# 聊天文件附件显示优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 聊天区域文本文件附件只显示文件图标和文件名（不显示完整内容），同时 LLM 仍然能收到文件名和完整文件内容。

**Architecture:** 新增 `text_file` content block 类型，前端和 DB 存储结构化的文件元数据，后端 engine.chat_stream 在传给 LangChain 前将 `text_file` block 转换为原生 `text` block。

**Tech Stack:** Python 3.12 / FastAPI / LangChain / Vue 3 / TypeScript / Element Plus / pytest

## Global Constraints

- Python 解释器: `D:\ProgramData\Miniconda3\envs\py312\python.exe`
- 项目早期阶段无历史包袱，不写兼容性迁移
- 禁止硬编码密码（如大模型 API key）
- 前端类型检查命令: `npm run build`（包含 `vue-tsc --noEmit`）
- 后端测试命令: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/<file> -v`
- 后端 lint 命令: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m ruff check lc_agent/`
- 代码中不添加注释（除非用户明确要求）

---

## File Structure

| 文件 | 职责 | 操作 |
|---|---|---|
| `lc_agent/core/engine.py` | 新增 `_convert_text_file_blocks` + `_convert_history_item` 模块函数，`chat_stream` 调用转换 | 修改 |
| `lc_agent/server/sse.py` | `_extract_text_from_blocks` 识别 `text_file` block 提取文件名 | 修改 |
| `frontend/src/utils/fileUpload.ts` | ContentBlock 类型新增 `text_file`，`buildContentBlocks` 生成 `text_file` block | 修改 |
| `frontend/src/views/ChatView.vue` | 渲染 `text_file` block 为图标+文件名，编辑恢复路径简化 | 修改 |
| `tests/test_engine_text_file_blocks.py` | 后端转换函数单元测试 | 新建 |

---

### Task 1: 后端转换函数 — _convert_text_file_blocks + _convert_history_item

**Files:**
- Create: `tests/test_engine_text_file_blocks.py`
- Modify: `lc_agent/core/engine.py` (在 `chat_stream` 方法之前添加模块函数)

**Interfaces:**
- Produces: `_convert_text_file_blocks(content: list[dict[str, Any]]) -> list[dict[str, Any]]` — 将 text_file block 转为 text block
- Produces: `_convert_history_item(item: dict[str, Any]) -> dict[str, Any]` — 转换历史消息中的 text_file block

- [ ] **Step 1: Write the failing test**

Create `tests/test_engine_text_file_blocks.py`:

```python
from lc_agent.core.engine import _convert_text_file_blocks, _convert_history_item


def test_convert_text_file_block_to_text():
    content = [
        {"type": "text", "text": "请检查这个文件"},
        {"type": "text_file", "name": "foo.py", "textContent": "print('hello')", "lang": "python"},
    ]
    result = _convert_text_file_blocks(content)
    assert len(result) == 2
    assert result[0] == {"type": "text", "text": "请检查这个文件"}
    assert result[1]["type"] == "text"
    assert result[1]["text"] == "📎 `foo.py`:\n```python\nprint('hello')\n```"


def test_convert_passes_through_text_and_image_blocks():
    content = [
        {"type": "text", "text": "hello"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}},
    ]
    result = _convert_text_file_blocks(content)
    assert result == content


def test_convert_text_file_block_empty_content():
    content = [{"type": "text_file", "name": "empty.txt", "textContent": "", "lang": ""}]
    result = _convert_text_file_blocks(content)
    assert result == [{"type": "text", "text": "📎 `empty.txt`:\n```\n\n```"}]


def test_convert_text_file_block_missing_fields():
    content = [{"type": "text_file"}]
    result = _convert_text_file_blocks(content)
    assert result == [{"type": "text", "text": "📎 ``:\n```\n\n```"}]


def test_convert_empty_list():
    assert _convert_text_file_blocks([]) == []


def test_convert_history_item_with_list_content():
    item = {
        "role": "user",
        "content": [
            {"type": "text", "text": "hi"},
            {"type": "text_file", "name": "a.py", "textContent": "x=1", "lang": "python"},
        ],
    }
    result = _convert_history_item(item)
    assert result["role"] == "user"
    assert result["content"][0] == {"type": "text", "text": "hi"}
    assert result["content"][1]["type"] == "text"
    assert "📎 `a.py`" in result["content"][1]["text"]


def test_convert_history_item_with_string_content():
    item = {"role": "assistant", "content": "hello world"}
    result = _convert_history_item(item)
    assert result == item


def test_convert_history_item_does_not_mutate_original():
    original = {"role": "user", "content": [{"type": "text_file", "name": "x.py", "textContent": "y", "lang": "python"}]}
    _convert_history_item(original)
    assert original["content"][0]["type"] == "text_file"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine_text_file_blocks.py -v`
Expected: FAIL with `ImportError: cannot import name '_convert_text_file_blocks'`

- [ ] **Step 3: Write minimal implementation**

In `lc_agent/core/engine.py`, add these module-level functions before the `AgentEngine` class (before the line `class AgentEngine`):

```python
def _convert_text_file_blocks(content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert text_file blocks to native text blocks for LangChain consumption."""
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

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine_text_file_blocks.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Lint check**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m ruff check lc_agent/core/engine.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add tests/test_engine_text_file_blocks.py lc_agent/core/engine.py
git commit -m "feat: add _convert_text_file_blocks and _convert_history_item to engine"
```

---

### Task 2: 后端 — chat_stream 集成转换逻辑

**Files:**
- Modify: `lc_agent/core/engine.py` (chat_stream 方法, 约 900-928 行)
- Test: `tests/test_engine_text_file_blocks.py` (追加集成测试)

**Interfaces:**
- Consumes: `_convert_text_file_blocks` + `_convert_history_item` from Task 1
- Produces: `chat_stream` 方法现在接受含 `text_file` block 的 message 和 history，内部自动转换

- [ ] **Step 1: Write the failing test**

Append to `tests/test_engine_text_file_blocks.py`:

```python
def test_chat_stream_converts_text_file_blocks(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock, patch
    from lc_agent.core.engine import AgentEngine

    captured_messages = []

    async def fake_astream_events(self, input, **kwargs):
        captured_messages.append(input)
        return iter([])

    engine = MagicMock(spec=AgentEngine)
    engine._get_or_build_agent = MagicMock(return_value=MagicMock())
    engine._should_use_memory_context = MagicMock(return_value=False)
    engine.recursion_limit = 25

    message = [
        {"type": "text", "text": "看下这个文件"},
        {"type": "text_file", "name": "foo.py", "textContent": "print('hi')", "lang": "python"},
    ]

    import asyncio
    from lc_agent.core.engine import AgentEngine as AE

    with patch.object(AE, 'chat_stream', AE.chat_stream.__get__(engine, AE)):
        with patch.object(type(engine._get_or_build_agent()), 'astream_events', fake_astream_events):
            async def run():
                async for _ in AE.chat_stream(engine, message, "thread-1"):
                    pass
            asyncio.run(run())

    assert len(captured_messages) == 1
    msgs = captured_messages[0]["messages"]
    user_msg = msgs[-1]
    assert user_msg["role"] == "user"
    blocks = user_msg["content"]
    assert all(b["type"] != "text_file" for b in blocks)
    assert any("📎 `foo.py`" in b.get("text", "") for b in blocks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine_text_file_blocks.py::test_chat_stream_converts_text_file_blocks -v`
Expected: FAIL (text_file block passes through unconverted)

- [ ] **Step 3: Modify chat_stream to call conversion functions**

In `lc_agent/core/engine.py`, modify the `chat_stream` method. Find these lines:

```python
    async def chat_stream(
        self,
        message: list[dict[str, Any]],
        thread_id: str,
        preset_id: str = "chat",
        model_id: str = "",
        history: list[dict[str, str]] | None = None,
        llm_params: dict | None = None,
        user_id: str = "anonymous",
    ) -> AsyncIterator[dict]:
        """Stream chat responses as events.

        message: LangChain content blocks list, e.g. [{"type":"text","text":"..."}, {"type":"image_url","image_url":{"url":"data:..."}}]
        """
        agent = self._get_or_build_agent(preset_id, model_id, llm_params=llm_params)

        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": self.recursion_limit}
        input_messages = list(history or [])
        input_messages.append({"role": "user", "content": message})
```

Replace the `input_messages` section with:

```python
        agent = self._get_or_build_agent(preset_id, model_id, llm_params=llm_params)

        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": self.recursion_limit}
        message = _convert_text_file_blocks(message)
        history = [_convert_history_item(item) for item in (history or [])]
        input_messages = list(history)
        input_messages.append({"role": "user", "content": message})
```

- [ ] **Step 4: Run all engine text_file tests**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine_text_file_blocks.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Run existing engine tests to check no regression**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_engine.py tests/test_engine_subagents.py -v`
Expected: PASS (all existing tests still pass)

- [ ] **Step 6: Lint check**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m ruff check lc_agent/core/engine.py`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add tests/test_engine_text_file_blocks.py lc_agent/core/engine.py
git commit -m "feat: integrate text_file block conversion into chat_stream"
```

---

### Task 3: 后端 — sse.py _extract_text_from_blocks 适配

**Files:**
- Create: `tests/test_sse_text_file_blocks.py`
- Modify: `lc_agent/server/sse.py` (约 248-254 行)

**Interfaces:**
- Consumes: `_extract_text_from_blocks` function from sse.py
- Produces: `_extract_text_from_blocks` 现在识别 `text_file` block 并提取文件名

- [ ] **Step 1: Write the failing test**

Create `tests/test_sse_text_file_blocks.py`:

```python
from lc_agent.server.sse import _extract_text_from_blocks


def test_extract_text_from_plain_text_block():
    content = [{"type": "text", "text": "你好"}]
    assert _extract_text_from_blocks(content) == "你好"


def test_extract_text_from_text_file_block_returns_filename():
    content = [{"type": "text_file", "name": "foo.py", "textContent": "print('hello')", "lang": "python"}]
    assert _extract_text_from_blocks(content) == "foo.py"


def test_extract_text_mixed_blocks():
    content = [
        {"type": "text", "text": "请检查"},
        {"type": "text_file", "name": "foo.py", "textContent": "x=1", "lang": "python"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}},
    ]
    result = _extract_text_from_blocks(content)
    assert "请检查" in result
    assert "foo.py" in result
    assert "x=1" not in result


def test_extract_text_empty_content():
    assert _extract_text_from_blocks([]) == ""


def test_extract_text_file_block_missing_name():
    content = [{"type": "text_file", "textContent": "x=1", "lang": "python"}]
    assert _extract_text_from_blocks(content) == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_sse_text_file_blocks.py -v`
Expected: FAIL (text_file blocks not recognized, returns "" instead of filename)

- [ ] **Step 3: Modify _extract_text_from_blocks**

In `lc_agent/server/sse.py`, find the `_extract_text_from_blocks` function:

```python
def _extract_text_from_blocks(content: list[dict[str, Any]]) -> str:
    """从 content blocks 提取纯文本（用于标题生成等场景）。"""
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return " ".join(parts)
```

Replace with:

```python
def _extract_text_from_blocks(content: list[dict[str, Any]]) -> str:
    """从 content blocks 提取纯文本（用于标题生成等场景）。"""
    parts = []
    for block in content:
        if isinstance(block, dict):
            if block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif block.get("type") == "text_file":
                parts.append(block.get("name", ""))
    return " ".join(parts)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_sse_text_file_blocks.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Lint check**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m ruff check lc_agent/server/sse.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add tests/test_sse_text_file_blocks.py lc_agent/server/sse.py
git commit -m "feat: extract filename from text_file blocks for title generation"
```

---

### Task 4: 前端 — fileUpload.ts ContentBlock 类型 + buildContentBlocks

**Files:**
- Modify: `frontend/src/utils/fileUpload.ts` (ContentBlock 接口 + buildContentBlocks 函数)

**Interfaces:**
- Produces: `ContentBlock` type 新增 `text_file` 类型
- Produces: `buildContentBlocks` 现在生成 `{ type: 'text_file', name, textContent, lang }` block

- [ ] **Step 1: Update ContentBlock interface**

In `frontend/src/utils/fileUpload.ts`, find the ContentBlock interface:

```typescript
export interface ContentBlock {
  type: 'text' | 'image_url'
  text?: string
  image_url?: { url: string }
}
```

Replace with:

```typescript
export interface ContentBlock {
  type: 'text' | 'image_url' | 'text_file'
  text?: string
  image_url?: { url: string }
  name?: string
  textContent?: string
  lang?: string
}
```

- [ ] **Step 2: Update buildContentBlocks function**

In `frontend/src/utils/fileUpload.ts`, find the `buildContentBlocks` function:

```typescript
export function buildContentBlocks(text: string, attachments: Attachment[]): ContentBlock[] {
  const blocks: ContentBlock[] = []
  const trimmed = text.trim()
  if (trimmed) {
    blocks.push({ type: 'text', text: trimmed })
  }
  for (const att of attachments) {
    if (att.type === 'image' && att.dataUrl) {
      blocks.push({ type: 'image_url', image_url: { url: att.dataUrl } })
    } else if (att.type === 'text_file' && att.textContent !== undefined) {
      const ext = getExtension(att.name)
      const lang = EXT_TO_LANG[ext] || ''
      blocks.push({
        type: 'text',
        text: `📎 \`${att.name}\`:\n\`\`\`${lang}\n${att.textContent}\n\`\`\``,
      })
    }
  }
  return blocks
}
```

Replace with:

```typescript
export function buildContentBlocks(text: string, attachments: Attachment[]): ContentBlock[] {
  const blocks: ContentBlock[] = []
  const trimmed = text.trim()
  if (trimmed) {
    blocks.push({ type: 'text', text: trimmed })
  }
  for (const att of attachments) {
    if (att.type === 'image' && att.dataUrl) {
      blocks.push({ type: 'image_url', image_url: { url: att.dataUrl } })
    } else if (att.type === 'text_file' && att.textContent !== undefined) {
      const ext = getExtension(att.name)
      const lang = EXT_TO_LANG[ext] || ''
      blocks.push({
        type: 'text_file',
        name: att.name,
        textContent: att.textContent,
        lang,
      })
    }
  }
  return blocks
}
```

- [ ] **Step 3: Type check**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no TypeScript errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/utils/fileUpload.ts
git commit -m "feat: generate text_file content blocks instead of embedding file content in text"
```

---

### Task 5: 前端 — ChatView.vue 渲染 text_file block

**Files:**
- Modify: `frontend/src/views/ChatView.vue` (用户消息渲染模板 + 样式)

**Interfaces:**
- Consumes: `ContentBlock` with `type: 'text_file'` from Task 4
- Produces: `text_file` block 渲染为文件图标 + 文件名的卡片

- [ ] **Step 1: Add text_file rendering branch to template**

In `frontend/src/views/ChatView.vue`, find the user content blocks rendering section (around line 150-160):

```vue
              <div v-if="item.role === 'user' && item.contentBlocks" class="user-content-blocks">
                <template v-for="(block, i) in item.contentBlocks" :key="i">
                  <span v-if="block.type === 'text'" class="user-text-block">{{ block.text }}</span>
                  <img
                    v-else-if="block.type === 'image_url' && block.image_url"
                    :src="block.image_url.url"
                    class="user-image-block"
                    @click="previewImage(block.image_url.url)"
                  />
                </template>
              </div>
```

Replace with:

```vue
              <div v-if="item.role === 'user' && item.contentBlocks" class="user-content-blocks">
                <template v-for="(block, i) in item.contentBlocks" :key="i">
                  <span v-if="block.type === 'text'" class="user-text-block">{{ block.text }}</span>
                  <img
                    v-else-if="block.type === 'image_url' && block.image_url"
                    :src="block.image_url.url"
                    class="user-image-block"
                    @click="previewImage(block.image_url.url)"
                  />
                  <div v-else-if="block.type === 'text_file'" class="user-file-block">
                    <span class="file-icon">📄</span>
                    <span class="file-name" :title="block.name">{{ block.name }}</span>
                  </div>
                </template>
              </div>
```

- [ ] **Step 2: Add CSS styles**

In `frontend/src/views/ChatView.vue`, find the `.user-image-block` style (around line 1322-1328):

```css
.user-image-block {
  max-width: 240px;
  max-height: 240px;
  border-radius: 6px;
  cursor: zoom-in;
  border: 1px solid var(--el-border-color);
}
```

Add after it:

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

.user-file-block .file-icon {
  font-size: 16px;
  line-height: 1;
}

.user-file-block .file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-primary);
}
```

- [ ] **Step 3: Type check + build**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no TypeScript errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/ChatView.vue
git commit -m "feat: render text_file blocks as file icon + filename in chat area"
```

---

### Task 6: 前端 — ChatView.vue 编辑/恢复路径简化

**Files:**
- Modify: `frontend/src/views/ChatView.vue` (startEditMessage 函数, 约 593-630 行)

**Interfaces:**
- Consumes: `ContentBlock` with `type: 'text_file'` from Task 4
- Produces: `startEditMessage` 直接读 `text_file` block 字段还原 attachments，不再需要 regex

- [ ] **Step 1: Update startEditMessage function**

In `frontend/src/views/ChatView.vue`, find the `startEditMessage` function. Look for the block parsing logic:

```typescript
function startEditMessage(item: ChatBubbleItem) {
  if (!canEditMessage(item)) return
  editingMessageId.value = item.messageId
  const blocks = 'contentBlocks' in item ? item.contentBlocks : undefined
  if (blocks && blocks.length > 0) {
    const textParts: string[] = []
    const restoredAtts: Attachment[] = []
    let attIdx = 0
    for (const block of blocks) {
      if (block.type === 'text') {
        const fileMatch = block.text?.match(/^📎 `([^`]+)`:\n```(\w*)\n([\s\S]*?)\n```$/)
        if (fileMatch) {
          const [, name, , content] = fileMatch
          restoredAtts.push({
            id: `restore-${attIdx++}`,
            type: 'text_file',
            name,
            textContent: content,
          })
        } else if (block.text) {
          textParts.push(block.text)
        }
      } else if (block.type === 'image_url' && block.image_url) {
        restoredAtts.push({
          id: `restore-${attIdx++}`,
          type: 'image',
          name: `image-${attIdx}.png`,
          dataUrl: block.image_url.url,
        })
      }
    }
    editingContent.value = textParts.join('\n')
    editingAttachments.value = restoredAtts
  } else {
    editingContent.value = item.content || ''
    editingAttachments.value = []
  }
}
```

Replace with:

```typescript
function startEditMessage(item: ChatBubbleItem) {
  if (!canEditMessage(item)) return
  editingMessageId.value = item.messageId
  const blocks = 'contentBlocks' in item ? item.contentBlocks : undefined
  if (blocks && blocks.length > 0) {
    const textParts: string[] = []
    const restoredAtts: Attachment[] = []
    let attIdx = 0
    for (const block of blocks) {
      if (block.type === 'text' && block.text) {
        textParts.push(block.text)
      } else if (block.type === 'text_file') {
        restoredAtts.push({
          id: `restore-${attIdx++}`,
          type: 'text_file',
          name: block.name || `file-${attIdx}.txt`,
          textContent: block.textContent || '',
        })
      } else if (block.type === 'image_url' && block.image_url) {
        restoredAtts.push({
          id: `restore-${attIdx++}`,
          type: 'image',
          name: `image-${attIdx}.png`,
          dataUrl: block.image_url.url,
        })
      }
    }
    editingContent.value = textParts.join('\n')
    editingAttachments.value = restoredAtts
  } else {
    editingContent.value = item.content || ''
    editingAttachments.value = []
  }
}
```

- [ ] **Step 2: Type check + build**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no TypeScript errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/ChatView.vue
git commit -m "refactor: simplify edit/restore path to read text_file blocks directly"
```

---

## Self-Review

**Spec coverage:**
- ✅ Section 1 (架构与数据流): Task 1-2 implement backend conversion, Task 4-5 implement frontend rendering
- ✅ Section 2.1 (ContentBlock 类型 + buildContentBlocks): Task 4
- ✅ Section 2.2 (ChatView 渲染 text_file): Task 5
- ✅ Section 2.3 (编辑/恢复路径简化): Task 6
- ✅ Section 2.4 (chat.ts 无需改动): Confirmed, no task needed
- ✅ Section 3.1 (engine.py 转换): Task 1-2
- ✅ Section 3.2 (sse.py 标题提取): Task 3
- ✅ Section 3.3-3.4 (无需改动部分): Confirmed, no task needed
- ✅ Section 4 (边界处理): Covered by test cases in Task 1 and Task 3

**Placeholder scan:** No TBD, TODO, or vague references found. All code blocks contain complete implementation.

**Type consistency:** `ContentBlock.type` is `'text' | 'image_url' | 'text_file'` consistently across fileUpload.ts and ChatView.vue. `_convert_text_file_blocks` and `_convert_history_item` signatures match between definition (Task 1) and usage (Task 2). Field names `name`, `textContent`, `lang` consistent across frontend and backend.
