# 聊天文件附件显示优化设计

**日期**: 2026-07-16
**状态**: 已确认，待实现规划

## 背景与目标

当前聊天输入框上传文本文件后，聊天区域直接显示完整的文件内容（一大段文字），因为文本文件内容被嵌入到一个 `text` 类型的 ContentBlock 中（格式为 `📎 \`文件名\`:\n\`\`\`语言\n<完整内容>\n\`\`\``），聊天区把所有 `text` 块当成纯文本显示。

**目标**：
1. 聊天区域只显示文件图标和文件名，不显示完整文件内容
2. LLM 仍然能知道文件名和完整文件内容
3. 采用最佳实践架构，不依赖 regex 解析

## 设计方案

采用**新增 `text_file` block 类型 + 后端转换**方案：前端和 DB 使用新的 `text_file` block 类型存储文件元数据（文件名、内容、语言），后端在传给 LangChain 前将其转换为原生 `text` block。

---

## 1. 架构与数据流

### ContentBlock 类型定义（三种）

```typescript
// 纯文本（用户输入的文字）
{ type: 'text', text: '你好' }

// 图片（base64 data URL）
{ type: 'image_url', image_url: { url: 'data:image/png;base64,...' } }

// 文本文件附件（新增）
{ type: 'text_file', name: 'foo.py', textContent: 'import os\n...', lang: 'python' }
```

### 完整数据流

```
用户上传文件
    ↓
ChatInput.vue: 生成 text_file block { type, name, textContent, lang }
    ↓
SSE 发送 content blocks（含 text_file）到后端
    ↓
后端 DB: 存储原始 content blocks（text_file 原样存入 JSON 列）
    ↓
后端 engine: 转换 text_file → text block 后传给 LangChain
    转换格式: { type: 'text', text: '📎 `foo.py`:\n```python\n<content>\n```' }
    ↓
LangChain create_agent: 只见到原生 text + image_url block，零兼容风险
    ↓
前端加载历史: 从 DB 读到 text_file block → 渲染为文件图标+文件名
```

### 转换边界

转换只发生在**后端 engine 入口**，是唯一需要解析 content blocks 的地方：

```
[前端] text_file block  →  [DB] text_file block  →  [engine 转换] text block  →  [LangChain]
```

DB 存储和前端显示全程保持 `text_file` 原始结构，只有传给 LangChain 的瞬间做转换。

---

## 2. 前端改动

### 2.1 fileUpload.ts — ContentBlock 类型与构建逻辑

[fileUpload.ts](file:///d:\codes\lc-agent\frontend\src\utils\fileUpload.ts) ContentBlock 类型新增 `text_file`：

```typescript
export interface ContentBlock {
  type: 'text' | 'image_url' | 'text_file'  // 新增 text_file
  text?: string
  image_url?: { url: string }
  // text_file 专属
  name?: string
  textContent?: string
  lang?: string
}
```

`buildContentBlocks` 改动：文本文件不再嵌入 text block，而是生成独立的 `text_file` block：

```typescript
// 之前：把文件内容嵌入 text block
blocks.push({ type: 'text', text: `📎 \`${att.name}\`:\n\`\`\`${lang}\n${att.textContent}\n\`\`\`` })

// 之后：生成独立的 text_file block
blocks.push({ type: 'text_file', name: att.name, textContent: att.textContent, lang })
```

### 2.2 ChatView.vue — 渲染 text_file block

[ChatView.vue:150-159](file:///d:\codes\lc-agent\frontend\src\views\ChatView.vue#L150-L159) 用户消息渲染新增 `text_file` 分支：

```vue
<div v-if="item.role === 'user' && item.contentBlocks" class="user-content-blocks">
  <template v-for="(block, i) in item.contentBlocks" :key="i">
    <span v-if="block.type === 'text'" class="user-text-block">{{ block.text }}</span>
    <img v-else-if="block.type === 'image_url' && block.image_url"
         :src="block.image_url.url" class="user-image-block"
         @click="previewImage(block.image_url.url)" />
    <!-- 新增：文本文件渲染为图标+文件名 -->
    <div v-else-if="block.type === 'text_file'" class="user-file-block">
      <span class="file-icon">📄</span>
      <span class="file-name" :title="block.name">{{ block.name }}</span>
    </div>
  </template>
</div>
```

样式（与 ChatInput 附件预览风格一致）：

```css
.user-file-block {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-fill-color-light);
  font-size: 13px;
  max-width: 100%;
}
.user-file-block .file-icon { font-size: 16px; }
.user-file-block .file-name {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  color: var(--el-text-color-primary);
}
```

### 2.3 ChatView.vue — 编辑/恢复路径简化

[ChatView.vue:593-630](file:///d:\codes\lc-agent\frontend\src\views\ChatView.vue#L593-L630) `startEditMessage` 不再需要 regex 解析，直接读 `text_file` block 字段：

```typescript
// 之前：regex 匹配 📎 `name`:\n```lang\ncontent\n```
const fileMatch = block.text?.match(/^📎 `([^`]+)`:\n```(\w*)\n([\s\S]*?)\n```$/)

// 之后：直接判断 block 类型
if (block.type === 'text_file') {
  restoredAtts.push({
    id: `restore-${attIdx++}`,
    type: 'text_file',
    name: block.name,
    textContent: block.textContent,
  })
}
```

### 2.4 chat.ts store — 无需改动

[chat.ts:275-278](file:///d:\codes\lc-agent\frontend\src\stores\chat.ts#L275-L278) 用户消息的 content 已经是 `ContentBlock[]`，`text_file` block 作为数组元素自动保留，无需特殊处理。

### 2.5 不需要改的前端部分

- **ChatInput.vue** — 附件预览区已正确显示文件图标+文件名，无需改动
- **sse-client.ts** — `sendMessage` 直接传 content blocks 数组，`text_file` block 自动透传

---

## 3. 后端改动

### 3.1 engine.py — chat_stream 新增转换逻辑

[engine.py:900-928](file:///d:\codes\lc-agent\lc_agent\core\engine.py#L900-L928) 的 `chat_stream` 是传给 LangChain 的唯一入口。在传入 `astream_events` 前，把 `text_file` block 转换为原生 `text` block：

```python
def _convert_text_file_blocks(content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert text_file blocks to native text blocks for LangChain."""
    converted = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text_file":
            name = block.get("name", "")
            text_content = block.get("textContent", "")
            lang = block.get("lang", "")
            converted.append({
                "type": "text",
                "text": f"📎 `{name}`:\n```{lang}\n{text_content}\n```",
            })
        else:
            converted.append(block)
    return converted


def _convert_history_item(item: dict[str, Any]) -> dict[str, Any]:
    """Convert text_file blocks in a history message's content."""
    content = item.get("content")
    if isinstance(content, list):
        return {**item, "content": _convert_text_file_blocks(content)}
    return item
```

`chat_stream` 方法改动：

```python
async def chat_stream(self, message, thread_id, ...):
    agent = self._get_or_build_agent(...)
    # 转换 text_file → text，LangChain 只见到原生 block
    message = _convert_text_file_blocks(message)
    history = [_convert_history_item(item) for item in (history or [])]
    input_messages = list(history)
    input_messages.append({"role": "user", "content": message})
    ...
```

### 3.2 sse.py — _extract_text_from_blocks 适配

[sse.py:248-254](file:///d:\codes\lc-agent\lc_agent\server\sse.py#L248-L254) 标题提取函数识别 `text_file` block，提取文件名（不提取文件内容，避免标题被大段代码污染）：

```python
def _extract_text_from_blocks(content: list[dict[str, Any]]) -> str:
    parts = []
    for block in content:
        if isinstance(block, dict):
            if block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif block.get("type") == "text_file":
                parts.append(block.get("name", ""))  # 只取文件名
    return " ".join(parts)
```

效果：用户发"请检查这个文件"+ 上传 `foo.py`，标题是"请检查这个文件 foo.py"而不是大段代码。

### 3.3 sse.py — _send_stream 无需改动

- `content = req.input` — 原样接收含 `text_file` block 的 content
- `persistence.save_ui_message(..., content)` — 原样存入 DB（JSON 列自动序列化）
- `engine.chat_stream(content, ...)` — engine 内部做转换

SSE 层零改动，content blocks 原样透传到 DB 和 engine。

### 3.4 不需要改的后端部分

- **persistence.py** — `save_ui_message` 接收 `content: list[dict]`，JSON 列存储任意结构
- **models.py** — `ChatUiMessage.content` 是 `list[dict]` JSON 列，自动兼容
- **chat_model.py** — LLM 客户端层，转换后只收到原生 `text` block
- **create_agent / astream_events** — LangChain 原生支持 content blocks
- **stream_utils.py** — 只处理 assistant 响应事件，不涉及 user content

---

## 4. 边界处理

### 4.1 后端边界

**空 text_file block**：`textContent` 为空字符串 → 转换生成 `📎 \`name\`:\n\`\`\`lang\n\n\`\`\``，LLM 能看到文件名但内容为空，不报错。

**lang 字段缺失**：`lang` 为空 → 代码块标记为 ` ```\n`（无语言标记），markdown 仍能正常渲染。

**历史消息中的 text_file block**：编辑消息重放历史时，`_convert_history_item` 遍历每条历史消息的 content，转换其中的 `text_file` block。历史中的 assistant 消息 content 是 string，不受影响。

**text_file block 字段缺失**：`name` 或 `textContent` 缺失 → 用空字符串，`.get()` 安全取值不抛异常。

### 4.2 前端边界

**加载历史消息**：DB 返回的 content 数组含 `text_file` block → `normalizeHistoryMessage` 已透传数组，`text_file` block 自动保留，ChatView 渲染时识别 `block.type === 'text_file'` 渲染文件卡片。

**编辑消息恢复附件**：`startEditMessage` 遍历 contentBlocks，遇到 `text_file` block 直接读 `name` 和 `textContent` 字段还原到 attachments，不再需要 regex。

**图片消息不受影响**：`image_url` block 渲染逻辑不变。

**混合消息**：一条消息同时有 text + image_url + text_file → 每种 block 独立处理，互不干扰。

---

## 关键设计决策

1. **新增 `text_file` block 类型**——语义清晰，每个 block 类型有明确含义，不依赖 regex
2. **后端转换而非前端转换**——DB 保存结构化的 `text_file` block，前端加载历史时能直接渲染文件卡片
3. **转换只在 engine.chat_stream**——单一转换入口，LangChain 只见到原生 `text` + `image_url` block
4. **标题提取只取文件名**——避免大段文件内容污染会话标题
5. **编辑恢复路径简化**——直接读 block 字段，移除 regex 匹配

## 影响范围

| 层 | 文件 | 改动 |
|---|---|---|
| 前端工具 | `frontend/src/utils/fileUpload.ts` | ContentBlock 类型 + buildContentBlocks |
| 前端视图 | `frontend/src/views/ChatView.vue` | 渲染 text_file block + 编辑恢复路径 |
| 后端引擎 | `lc_agent/core/engine.py` | chat_stream 转换 + _convert_text_file_blocks |
| 后端 SSE | `lc_agent/server/sse.py` | _extract_text_from_blocks 提取文件名 |
| 前端 store | `frontend/src/stores/chat.ts` | 无需改动（已透传数组） |
| 后端持久化 | `lc_agent/server/persistence.py` | 无需改动（JSON 列） |
| DB schema | `lc_agent/db/models.py` | 无需改动（JSON 列） |
