# 聊天图片与文件上传设计

**日期**: 2026-07-15
**状态**: 已确认，待实现规划

## 背景与目标

当前 lc-agent 聊天输入只支持纯文本（[ChatInput.vue](file:///d:\codes\lc-agent\frontend\src\components\chat\ChatInput.vue) 单个 textarea），整条链路（前端 → SSE → engine → DB）都是纯字符串。

本设计目标是支持：
1. **粘贴截图**（Ctrl+V 剪贴板图片）
2. **拖拽文件**到输入框
3. **文件选择按钮**上传
4. 支持**图片**和**文本文件**两种附件
5. 一条消息可附多张图片/多个文件
6. 带附件的消息可编辑重放

## 设计方案

采用 **LangChain 原生 content blocks 方案**：消息 content 统一用 LangChain 的多模态 content blocks list 格式，engine 层零解析直接透传给 `create_agent`/`astream_events`，最贴近 LangChain 最佳实践。

项目处于早期阶段无历史包袱（AGENTS.md 明确），老数据直接清空，content 类型统一为 list，不保留 str 兼容形式。

---

## 1. 数据模型与 API Schema

### DB Schema 改动

[models.py](file:///d:\codes\lc-agent\lc_agent\db\models.py) 的 `ChatUiMessage.content`：

```python
# 之前
content: str = ""

# 之后
content: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
```

content 统一为 LangChain content blocks list，不再支持 str 形式。

### content blocks 格式

只用 LangChain 原生两种 block 类型：

```python
# 纯文本消息
content = [{"type": "text", "text": "你好"}]

# 带 2 张图和 1 个代码文件的消息
content = [
    {"type": "text", "text": "看下这两张图和这个文件"},
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,/9j/4AAQ..."}},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBORw0KG..."}},
    {"type": "text", "text": "📎 `foo.py`:\n```python\nimport os\nprint('hello')\n```"},
]
```

- `{"type":"text","text":"..."}` —— 文本和文本文件（文件内容包在代码块里带文件名标记）
- `{"type":"image_url","image_url":{"url":"data:..."}}` —— 图片（base64 data URL）

这正是 LangChain `HumanMessage.content` 的多模态格式，[block_translators/openai.py](file:///D:\ProgramData\miniconda3\envs\py312\Lib\site-packages\langchain_core\messages\block_translators\openai.py) 会自动转成 OpenAI API 格式透传给本机 LiteLLM 代理。

### API Schema 改动

[sse.py](file:///d:\codes\lc-agent\lc_agent\server\sse.py) 的 `RunStreamRequest.input`：

```python
# 之前
class RunStreamRequest(BaseModel):
    input: str | None = None

# 之后
class RunStreamRequest(BaseModel):
    input: list[dict] | None = None  # LangChain content blocks
```

### 老数据处理

直接清空老数据（重建表或 TRUNCATE `chat_ui_messages`），不做迁移。

---

## 2. 前端交互

### ChatInput.vue 改造

现在只有单个 textarea，改造后新增附件管理。

**附件状态**：

```ts
interface Attachment {
  id: string          // 前端生成的 uuid
  type: 'image' | 'text_file'
  name: string        // 文件名（图片也保留，如 "screenshot.png"）
  // image 专属
  dataUrl?: string    // 压缩后的 base64 data URL
  // text_file 专属
  textContent?: string // 读取出的文本内容
}
const attachments = ref<Attachment[]>([])
```

**三种输入方式**：

1. **粘贴**——textarea 加 `@paste="handlePaste"`，检测 `clipboardData.items` 里的 image 类型，转成 Attachment。剪贴板同时有图片和文本时只取图片，纯文本走原生 paste 行为。
2. **拖拽**——整个输入区域加 `@drop="handleDrop"` `@dragover.prevent`，遍历 `dataTransfer.files` 按类型分流。
3. **文件选择按钮**——textarea 左下角加图标按钮，隐藏 `<input type="file" multiple accept="image/*,.txt,.md,...">`。

**图片压缩**（保留原格式）：

```ts
async function compressImage(file: File): Promise<string> {
  const bitmap = await createImageBitmap(file)
  const maxEdge = 1280
  let {width, height} = bitmap
  if (width > maxEdge || height > maxEdge) {
    const ratio = Math.min(maxEdge / width, maxEdge / height)
    width = Math.round(width * ratio)
    height = Math.round(height * ratio)
  }
  const canvas = new OffscreenCanvas(width, height)
  canvas.getContext('bitmaprenderer').transferFromImageBitmap(bitmap)
  // 保留原格式：png 输出 png，jpeg 输出 jpeg
  const blob = await canvas.convertToBlob({type: file.type, quality: 0.8})
  return await blobToDataURL(blob)  // "data:image/png;base64,..."
}
```

- 最长边 > 1280px 时等比缩放到 1280
- 保留原格式（PNG 透明背景保留）
- JPEG quality 0.8

**文本文件读取**：

- 用 `FileReader.readAsText`，编码默认 utf-8
- 不限制大小
- 调用前先过扩展名白名单

**扩展名白名单**：

```ts
const TEXT_EXTENSIONS = [
  'txt','md','markdown','json','yaml','yml','csv','log','xml','html','htm',
  'js','ts','jsx','tsx','py','go','rs','java','c','cpp','h','hpp','sh','sql',
  'css','scss','less','vue','toml','ini','conf'
]
```

**预览区**：

textarea 上方显示附件列表：
- 图片：80x80 缩略图 + 右上角 × 删除按钮
- 文本文件：文件图标 + 文件名 + × 删除按钮
- 支持点击 × 删除单个附件

**send 事件改造**：

```ts
function buildContentBlocks(): ContentBlock[] {
  const blocks: ContentBlock[] = []
  if (messageText.value.trim()) {
    blocks.push({type: 'text', text: messageText.value.trim()})
  }
  for (const att of attachments.value) {
    if (att.type === 'image') {
      blocks.push({type: 'image_url', image_url: {url: att.dataUrl!}})
    } else {
      const ext = att.name.split('.').pop() || ''
      const lang = EXT_TO_LANG[ext] || ''
      blocks.push({type: 'text', text: `📎 \`${att.name}\`:\n\`\`\`${lang}\n${att.textContent}\n\`\`\``})
    }
  }
  return blocks
}
emit('send', buildContentBlocks())
```

### 非法文件处理

拖入非白名单文件（如 .pdf .docx .exe）时：前端 toast 提示"不支持的文件类型: xxx.pdf，仅支持图片和文本文件"，不加入 attachments。

---

## 3. 前端 store 与历史渲染

### chat.ts store 改造

```ts
interface ContentBlock {
  type: 'text' | 'image_url'
  text?: string
  image_url?: { url: string }
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string | ContentBlock[]   // user 消息是 ContentBlock[]，assistant 消息保持 string
  ...
}
```

**范围限定**：只有 user 消息的 content 改为 `ContentBlock[]`（支持图片/文件块）。assistant 消息的 content 保持 `string`，因为现有流式子系统（token 拼接、THINK_START/THINK_END 标记、TOOL:N 标记、HTTP:N 标记）都基于字符串，改为 list 会需要重做整个流式渲染——超出图片上传的范围。

后端 DB 层 `ChatUiMessage.content` 统一为 `list[dict]`（user 消息存 content blocks，assistant 消息存 `[{type:"text", text:"<markdown 文本>"}]` 单元素 list），但前端 store 在加载历史时把 assistant 消息的 content 自动展开为字符串（取第一个 text block 的 text）。

**sendMessage 签名**：

```ts
// 之前: async function sendMessage(content: string, ...)
// 之后: async function sendMessage(content: ContentBlock[], ...)
```

用户消息 push 时直接存 content blocks。

### sse-client.ts 改造

```ts
// 之前: sendMessage(content: string, ...)
// 之后: sendMessage(content: ContentBlock[], ...)

const body = {
  input: content,   // 直接传 content blocks
  preset_id: presetId || 'chat',
  model: model || '',
}
```

无需格式转换。

### 历史消息加载

后端 GET 消息时 `content` 字段返回 `list[dict]`（content blocks），store 直接存入，无需转换。

### ChatView.vue 渲染改造

现在 [ChatView.vue:149-156](file:///d:\codes\lc-agent\frontend\src\views\ChatView.vue#L149-L156) 用户消息走纯文本 span。改为：

```vue
<!-- 用户消息渲染（content 是 ContentBlock[]） -->
<div v-if="item.role === 'user' && Array.isArray(item.content)" class="user-content-blocks">
  <template v-for="(block, i) in item.content" :key="i">
    <span v-if="block.type === 'text'" class="user-text-block">{{ block.text }}</span>
    <img v-else-if="block.type === 'image_url'"
         :src="block.image_url.url"
         class="user-image-block"
         @click="previewImage(block.image_url.url)" />
  </template>
</div>
<!-- 用户消息渲染（content 是 string，老格式回退） -->
<span v-else-if="item.role === 'user'" class="user-plain-text">{{ item.content }}</span>
<!-- assistant 消息渲染（content 是 string，保持现有 markdown 渲染不动） -->
<div v-else class="markdown-body" v-html="renderMarkdown(stripThinkingMarkers(item.content || ''))" />
```

**渲染规则**：
- 用户文本块：纯文本显示（不 markdown 解析，```符号原样显示）
- 用户图片块：`<img>` 缩略图 + el-image-viewer 点击全屏预览（支持缩放/旋转）
- assistant 消息：保持现有 markdown 渲染不变

### 编辑/重放路径改造

[ChatView.vue:612-626](file:///d:\codes\lc-agent\frontend\src\views\ChatView.vue#L612-L626) 的 `getReplayHistory` 改为：
- 历史消息的 content 直接作为 history 传给后端（content blocks 透传）
- 编辑消息时，把原消息的 content blocks 还原到 ChatInput（文本块拼回 textarea，图片/文件块还原到 attachments）

---

## 4. 后端管道改造

### sse.py 改造

**请求 schema**：

```python
class RunStreamRequest(BaseModel):
    input: list[dict] | None = None  # LangChain content blocks
    command: dict[str, Any] | None = None
    preset_id: str = "chat"
    model: str = ""
    llm_params: dict[str, Any] | None = None
    replace_from_message_id: str | None = None
    history: list[dict[str, Any]] | None = None
```

**_send_stream 改造**：

```python
content = req.input or []
# content 是 list[dict]，直接存 DB、传给 engine
await persistence.save_ui_message(_db_url, thread_id, "user", content)
async for event in engine.chat_stream(content, ...):
    ...
```

### engine.py 改造

[engine.py:900-925](file:///d:\codes\lc-agent\lc_agent\core\engine.py#L900-L925) 的 `chat_stream`：

```python
async def chat_stream(
    self,
    message: list[dict],   # LangChain content blocks
    ...
):
    input_messages = list(history or [])
    input_messages.append({"role": "user", "content": message})  # list[dict] 直接透传
    ...
    async for event in agent.astream_events({"messages": input_messages}, ...):
        ...
```

**零解析、零转换**——content blocks 直接作为 message content 透传给 `astream_events`，LangChain 的 `create_agent` 原生支持。

### 持久化层改造

**models.py**：

```python
class ChatUiMessage(SQLModel, table=True):
    ...
    content: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    ...
```

**persistence.py save_ui_message**：

签名和实现把 str 换成 list[dict]，SQLModel 自动 JSON 序列化。

**消息读取**：

读取时返回 content 字段直接是 list[dict]，无需转换。

### 标题生成改造

[engine.py:941-958](file:///d:\codes\lc-agent\lc_agent\core\engine.py#L941-L958) 的 `generate_title`：

```python
def _extract_text(content: list[dict]) -> str:
    parts = []
    for block in content:
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
    return " ".join(parts)

title = await self.generate_title(_extract_text(message))
```

图片不参与标题生成，只提取 text 块。

### 不需要改的部分

- **LLM 客户端层**（[chat_model.py](file:///d:\codes\lc-agent\lc_agent\core\chat_model.py)）——`ChatOpenAIReasoning` 继承 `ChatOpenAI`，多模态 content blocks 自动透传
- **create_agent**（[engine.py:633-639](file:///d:\codes\lc-agent\lc_agent\core\engine.py#L633-L639)）——原生支持多模态消息
- **SSE 事件流协议**——响应事件格式不变，只是 input 变了

---

## 5. 错误处理与边界

### 前端错误处理

**图片处理失败**：
- `createImageBitmap` 失败（文件损坏/不支持格式）→ toast "图片解析失败: xxx.png"，跳过
- `canvas.convertToBlob` 失败 → toast "图片压缩失败: xxx.png"，跳过
- 不阻塞其他附件处理

**文本文件读取失败**：
- `FileReader.readAsText` 失败或读到二进制乱码 → toast "文件读取失败: xxx，仅支持文本文件"，跳过
- 扩展名不在白名单 → toast "不支持的文件类型: xxx，仅支持图片和文本文件"

**拖拽多文件**：
- 遍历每个 file 独立处理，单个失败不阻塞其他
- 全部失败时 toast "没有可处理的文件"

**粘贴混合内容**：
- 剪贴板同时有图片和文本 → 只取图片，文本忽略
- 剪贴板只有文本 → 走原生 paste 行为插入 textarea（不拦截）

**空消息保护**：
- attachments 为空且 textarea 为空 → 不发送
- attachments 非空但 textarea 为空 → 允许发送（只有图片/文件也是合法消息）

**图片数量**：
- 上限 9 张，超过时 toast 提示"图片较多可能影响响应速度"（软提示不硬阻）

### 后端错误处理

**input 验证**：
- `req.input` 为空 list 或 None → 返回 400 "消息内容不能为空"
- `req.input` 不是 list → Pydantic 自动 422 校验失败
- content blocks 格式不合法（缺 type 字段等）→ 在 `_send_stream` 入口校验，返回 400 "消息格式无效"

**DB 持久化失败**：
- `save_ui_message` 异常 → 沿用现有错误处理（向上抛出，SSE 流返回 error 事件）

**LLM 不支持多模态**：
- 用户选了纯文本模型（如 DeepSeek V4 Flash）但发了图片 → LiteLLM 代理返回 400 错误 → SSE 流返回 error 事件，前端显示 "当前模型不支持图片输入"
- 不在框架层做模型能力检测，让 LLM 自己报错

**历史消息含图片但模型不支持**：
- 切换模型后重放历史 → 不做特殊处理，让 LLM 报错，用户自己换模型

---

## 关键设计决策

1. **方案 B（input 升级为结构化内容）**——最贴近 LangChain 原生 content blocks 格式，engine 层零改动直接透传
2. **content 统一为 list**——不保留 str 兼容形式，老数据直接清空（项目早期无包袱）
3. **base64 内联**——图片以 data URL 形式存 DB 和传 LLM，本机 LiteLLM 代理场景无需公网 URL
4. **前端压缩**——最长边 1280px，保留原格式（PNG 透明背景保留），JPEG quality 0.8
5. **文本文件作为 text block**——不单独发明附件类型，文件内容包在代码块里带文件名标记
6. **图片上限 9 张（软提示）**——防止滥用但不硬阻
7. **不在框架层做模型能力检测**——让 LLM 自己报错，避免过度工程

## 影响范围

### 前端
- [ChatInput.vue](file:///d:\codes\lc-agent\frontend\src\components\chat\ChatInput.vue) —— 主要改造（附件管理、压缩、预览、send）
- [chat.ts](file:///d:\codes\lc-agent\frontend\src\stores\chat.ts) —— ChatMessage 类型、sendMessage 签名
- [sse-client.ts](file:///d:\codes\lc-agent\frontend\src\api\sse-client.ts) —— sendMessage body.input 类型
- [ChatView.vue](file:///d:\codes\lc-agent\frontend\src\views\ChatView.vue) —— 用户消息渲染、编辑/重放路径

### 后端
- [sse.py](file:///d:\codes\lc-agent\lc_agent\server\sse.py) —— RunStreamRequest.input 类型、_send_stream
- [engine.py](file:///d:\codes\lc-agent\lc_agent\core\engine.py) —— chat_stream 签名、generate_title 提取文本
- [models.py](file:///d:\codes\lc-agent\lc_agent\db\models.py) —— ChatUiMessage.content 类型
- [persistence.py](file:///d:\codes\lc-agent\lc_agent\db\persistence.py) —— save_ui_message 签名
- 新增 Alembic 迁移 —— 清空老数据 + 改列类型

### 不需要改
- [chat_model.py](file:///d:\codes\lc-agent\lc_agent\core\chat_model.py) —— LLM 客户端层天然支持多模态
- create_agent / astream_events —— LangChain 原生支持 content blocks
- SSE 事件流协议 —— 响应格式不变
