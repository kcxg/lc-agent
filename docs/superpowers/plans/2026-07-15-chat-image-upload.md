# 聊天图片与文件上传实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让聊天输入支持粘贴截图、拖拽文件、文件选择按钮上传图片和文本文件，采用 LangChain 原生 content blocks 格式透传给 LLM。

**Architecture:** user 消息 content 改为 LangChain content blocks list（`list[dict]`），DB content 列改为 JSON，engine 层零解析直接透传给 `astream_events`。assistant 消息 content 保持 string 不动（现有流式子系统不破坏）。前端 ChatInput 新增附件管理（粘贴/拖拽/文件选择 + 压缩 + 预览）。

**Tech Stack:** Python 3.12 + FastAPI + SQLModel + Alembic（后端）；Vue 3 + TypeScript + Element Plus（前端）；LangChain `create_agent`/`astream_events`（LLM 层）。

**Spec:** [2026-07-15-chat-image-upload-design.md](file:///d:\codes\lc-agent\docs\superpowers\specs\2026-07-15-chat-image-upload-design.md)

---

## 文件结构

### 后端（Python）
- **Modify:** `lc_agent/db/models.py:57` —— `ChatUiMessage.content` 从 `str` 改为 `list[dict]` JSON 列
- **Modify:** `lc_agent/db/repository.py:108-125` —— `ChatUiMessageRepository.create` 的 content 参数类型
- **Modify:** `lc_agent/server/persistence.py:132-162` —— `save_ui_message` 的 content 参数类型
- **Modify:** `lc_agent/server/sse.py:95-102` —— `RunStreamRequest.input` 类型
- **Modify:** `lc_agent/server/sse.py:248-273` —— `_send_stream` 的 content 处理
- **Modify:** `lc_agent/server/routes/sessions.py:156-170` —— `get_session_messages` 返回的 content（list 透传）
- **Modify:** `lc_agent/core/engine.py:900-925` —— `chat_stream` 的 message 参数类型
- **Modify:** `lc_agent/core/engine.py:941-958` —— `generate_title` 从 content blocks 提取文本
- **Create:** `lc_agent/db/migrations/versions/20260715_chat_content_to_json.py` —— Alembic 迁移（清空 + 改列类型）

### 前端（Vue/TS）
- **Create:** `frontend/src/utils/fileUpload.ts` —— 附件处理工具函数（压缩、读取、白名单、content blocks 构造）
- **Modify:** `frontend/src/components/chat/ChatInput.vue` —— 附件管理 UI + paste/drop/file-input 事件
- **Modify:** `frontend/src/stores/chat.ts` —— `ChatMessage.content` 类型、`sendMessage` 签名、历史消息归一化
- **Modify:** `frontend/src/api/sse-client.ts:85-107` —— `sendMessage` 的 content 类型
- **Modify:** `frontend/src/views/ChatView.vue` —— 用户消息渲染（content blocks 分支）、编辑/重放路径

---

## Task 1: 后端 DB 模型与迁移

**Files:**
- Modify: `lc_agent/db/models.py:57`
- Modify: `lc_agent/db/repository.py:108-125`
- Create: `lc_agent/db/migrations/versions/20260715_chat_content_to_json.py`

- [ ] **Step 1: 修改 ChatUiMessage.content 类型**

修改 `lc_agent/db/models.py` 第 57 行：

```python
# 之前
content: str = ""

# 之后
content: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
```

确保文件顶部已经导入 `Column`、`JSON`（检查现有 import，应该已经有，因为 `tool_calls` 字段用了）。

- [ ] **Step 2: 修改 ChatUiMessageRepository.create 的 content 参数类型**

修改 `lc_agent/db/repository.py` 第 108-125 行：

```python
# 之前
async def create(
    self,
    *,
    session_id: str,
    role: str,
    content: str = "",
    tool_calls: list[dict] | None = None,
    usage: dict | None = None,
    http_traces: list[dict] | None = None,
) -> ChatUiMessage:

# 之后
async def create(
    self,
    *,
    session_id: str,
    role: str,
    content: list[dict] | None = None,
    tool_calls: list[dict] | None = None,
    usage: dict | None = None,
    http_traces: list[dict] | None = None,
) -> ChatUiMessage:
    message = ChatUiMessage(
        session_id=session_id,
        role=role,
        content=content or [],
        tool_calls=tool_calls,
        usage=usage,
        http_traces=http_traces,
    )
```

- [ ] **Step 3: 创建 Alembic 迁移文件**

创建 `lc_agent/db/migrations/versions/20260715_chat_content_to_json.py`：

```python
"""change chat_ui_messages.content from str to JSON list

Revision ID: 20260715_content_json
Revises: 20260710_rename_builtin_ids
Create Date: 2026-07-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

revision = "20260715_content_json"
down_revision = "20260710_rename_builtin_ids"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 项目早期无历史包袱，直接清空老数据并改列类型
    op.execute("DELETE FROM chat_ui_messages")
    # SQLite 不支持 ALTER COLUMN，需要用 batch_alter_table 重建表
    with op.batch_alter_table("chat_ui_messages") as batch_op:
        batch_op.alter_column(
            "content",
            existing_type=sa.String(),
            type_=sa.JSON(),
            existing_nullable=False,
            server_default="[]",
        )


def downgrade() -> None:
    with op.batch_alter_table("chat_ui_messages") as batch_op:
        batch_op.alter_column(
            "content",
            existing_type=sa.JSON(),
            type_=sa.String(),
            existing_nullable=False,
            server_default="",
        )
```

- [ ] **Step 4: 运行迁移**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -m alembic -c lc_agent/db/migrations/alembic.ini upgrade head`

注意：检查 alembic.ini 位置。如果在项目根，用 `D:\ProgramData\Miniconda3\envs\py312\python.exe -m alembic upgrade head`（cwd=d:\codes\lc-agent）。

Expected: 输出 `Running upgrade 20260710_rename_builtin_ids -> 20260715_content_json, change chat_ui_messages.content from str to JSON list`

- [ ] **Step 5: 验证迁移成功**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -c "import sqlite3; conn = sqlite3.connect('lc_agent_data.db'); cur = conn.execute('PRAGMA table_info(chat_ui_messages)'); print([r for r in cur])"`

Expected: 输出表结构，content 列类型应为 JSON 或匹配现有 JSON 存储格式（SQLite 中 JSON 存为 TEXT 但 schema 为 JSON）。

- [ ] **Step 6: Commit**

```bash
git add lc_agent/db/models.py lc_agent/db/repository.py lc_agent/db/migrations/versions/20260715_chat_content_to_json.py
git commit -m "refactor(db): change ChatUiMessage.content to JSON list for multimodal support"
```

---

## Task 2: 后端持久化层与 API 入口

**Files:**
- Modify: `lc_agent/server/persistence.py:132-162`
- Modify: `lc_agent/server/sse.py:95-102`
- Modify: `lc_agent/server/sse.py:248-273`

- [ ] **Step 1: 修改 save_ui_message 签名**

修改 `lc_agent/server/persistence.py` 第 132-162 行：

```python
# 之前
async def save_ui_message(
    db_url: str,
    thread_id: str,
    role: str,
    content: str,
    *,
    tool_calls: list[dict[str, Any]] | None = None,
    usage: dict[str, Any] | None = None,
    http_traces: list[dict[str, Any]] | None = None,
) -> None:

# 之后
async def save_ui_message(
    db_url: str,
    thread_id: str,
    role: str,
    content: list[dict[str, Any]],
    *,
    tool_calls: list[dict[str, Any]] | None = None,
    usage: dict[str, Any] | None = None,
    http_traces: list[dict[str, Any]] | None = None,
) -> None:
```

实现部分（第 143-162 行）不变，因为 `repo.create` 已经适配了 list[dict]。

- [ ] **Step 2: 修改 RunStreamRequest.input 类型**

修改 `lc_agent/server/sse.py` 第 95-102 行：

```python
# 之前
class RunStreamRequest(BaseModel):
    input: str | None = None
    command: dict[str, Any] | None = None
    preset_id: str = "chat"
    model: str = ""
    llm_params: dict[str, Any] | None = None
    replace_from_message_id: str | None = None
    history: list[dict[str, Any]] | None = None

# 之后
class RunStreamRequest(BaseModel):
    input: list[dict[str, Any]] | None = None
    command: dict[str, Any] | None = None
    preset_id: str = "chat"
    model: str = ""
    llm_params: dict[str, Any] | None = None
    replace_from_message_id: str | None = None
    history: list[dict[str, Any]] | None = None
```

- [ ] **Step 3: 修改 _send_stream 的 content 处理**

修改 `lc_agent/server/sse.py` 第 248-273 行。关键是 content 现在是 list[dict]，预标题生成需要提取文本：

```python
async def _send_stream(thread_id: str, req: RunStreamRequest, request: Request):
    """Handle new message: save to DB, stream agent response as SSE."""
    engine = _get_engine()
    content = req.input or []
    preset_id = req.preset_id
    model_id = req.model
    llm_params = req.llm_params
    lock = _get_lock(thread_id)
    _cancel_flags[thread_id] = False
    user = await _authenticate_sse(request)

    try:
        msg_count = await persistence.get_session_message_count(_db_url, thread_id)
        is_first = msg_count == 0
        if is_first:
            # 从 content blocks 提取纯文本生成预标题
            preliminary_title = _extract_text_from_blocks(content)[:30].strip()
            await persistence.ensure_session(
                _db_url, thread_id, preliminary_title, preset_id, model_id,
                user_id=user.id if user else "",
            )

        if req.replace_from_message_id:
            await persistence.truncate_from_message(_db_url, thread_id, req.replace_from_message_id)
            await engine.reset_thread(thread_id)

        await persistence.save_ui_message(_db_url, thread_id, "user", content)
    except Exception as e:
        # ... 现有错误处理不变
```

在 `_send_stream` 之前（或文件顶部辅助函数区）添加：

```python
def _extract_text_from_blocks(content: list[dict[str, Any]]) -> str:
    """从 content blocks 提取纯文本（用于标题生成等场景）。"""
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return " ".join(parts)
```

- [ ] **Step 4: 验证 input 空校验**

在 `_send_stream` 开头（第 251 行后）添加空校验：

```python
content = req.input or []
if not content:
    async def error_stream():
        yield stream_utils.format_sse_event("error", {
            "title": "消息为空",
            "detail": "消息内容不能为空",
            "suggestions": ["请输入文本或附加图片/文件"],
            "error_code": "EMPTY_INPUT",
            "message": "Empty input",
        })
    return StreamingResponse(
        error_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
```

- [ ] **Step 5: 验证后端能启动**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -c "from lc_agent.server.sse import RunStreamRequest; r = RunStreamRequest(input=[{'type':'text','text':'hi'}]); print(r.input)"`

Expected: 输出 `[{'type': 'text', 'text': 'hi'}]`

- [ ] **Step 6: Commit**

```bash
git add lc_agent/server/persistence.py lc_agent/server/sse.py
git commit -m "refactor(server): change input/content to LangChain content blocks list"
```

---

## Task 3: 后端 engine 层

**Files:**
- Modify: `lc_agent/core/engine.py:900-925`
- Modify: `lc_agent/core/engine.py:941-958`

- [ ] **Step 1: 修改 chat_stream 签名**

修改 `lc_agent/core/engine.py` 第 900-925 行：

```python
# 之前
async def chat_stream(
    self,
    message: str,
    thread_id: str,
    preset_id: str = "chat",
    model_id: str = "",
    history: list[dict[str, str]] | None = None,
    llm_params: dict | None = None,
    user_id: str = "anonymous",
) -> AsyncIterator[dict]:
    """Stream chat responses as events."""
    agent = self._get_or_build_agent(preset_id, model_id, llm_params=llm_params)

    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": self.recursion_limit}
    input_messages = list(history or [])
    input_messages.append({"role": "user", "content": message})
    stream_kwargs: dict[str, Any] = {"config": config, "version": "v2"}
    if self._should_use_memory_context(preset_id):
        from lc_agent.core.memory import AgentRuntimeContext, normalize_memory_user_id

        stream_kwargs["context"] = AgentRuntimeContext(user_id=normalize_memory_user_id(user_id))
    async for event in agent.astream_events(
        {"messages": input_messages},
        **stream_kwargs,
    ):
        yield event

# 之后
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
    stream_kwargs: dict[str, Any] = {"config": config, "version": "v2"}
    if self._should_use_memory_context(preset_id):
        from lc_agent.core.memory import AgentRuntimeContext, normalize_memory_user_id

        stream_kwargs["context"] = AgentRuntimeContext(user_id=normalize_memory_user_id(user_id))
    async for event in agent.astream_events(
        {"messages": input_messages},
        **stream_kwargs,
    ):
        yield event
```

content blocks 直接作为 message content 透传，LangChain `create_agent` 原生支持。

- [ ] **Step 2: 修改 generate_title 适配 content blocks**

修改 `lc_agent/core/engine.py` 第 941-958 行。注意 `generate_title` 的 `user_message` 参数现在可能从 sse.py 传入提取后的纯文本字符串（参见 Task 2 Step 3 的 `_extract_text_from_blocks`），所以 `generate_title` 本身签名不变，仍是 `str`。但需要检查所有调用 `generate_title` 的地方，确保传入的是提取后的文本。

检查 `persistence.py` 中调用 `generate_title` 的地方（第 120-130 行附近）：

```python
# 查找类似这样的代码：
# first_message = ...  # 从 DB 取的 content
# return await engine.generate_title(first_message, model_id)
```

需要修改为从 content blocks 提取文本：

```python
# 之前（假设）
first_message_content = first_msg.content  # str
return await engine.generate_title(first_message_content, model_id)

# 之后
first_message_content = first_msg.content  # list[dict]
first_message_text = " ".join(
    block.get("text", "") for block in first_message_content
    if isinstance(block, dict) and block.get("type") == "text"
)
return await engine.generate_title(first_message_text, model_id)
```

用 Grep 搜索 `generate_title` 的所有调用点，逐一适配。

- [ ] **Step 3: 验证 engine 导入正常**

Run: `D:\ProgramData\Miniconda3\envs\py312\python.exe -c "from lc_agent.core.engine import AgentEngine; print('OK')"`

Expected: 输出 `OK`

- [ ] **Step 4: Commit**

```bash
git add lc_agent/core/engine.py lc_agent/server/persistence.py
git commit -m "refactor(engine): chat_stream accepts LangChain content blocks list"
```

---

## Task 4: 后端 get_session_messages 适配

**Files:**
- Modify: `lc_agent/server/routes/sessions.py:156-170`

- [ ] **Step 1: 检查 get_session_messages 的 content 返回**

读 `lc_agent/server/routes/sessions.py` 第 156-170 行，确认 `content` 字段直接透传（list[dict] → JSON 响应）：

```python
"messages": [
    {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,  # 现在是 list[dict]，FastAPI 自动序列化为 JSON
        "tool_calls": msg.tool_calls or [],
        ...
    }
]
```

如果现有代码就是这样直接透传 `msg.content`，则无需修改。FastAPI/Pydantic 会自动把 list[dict] 序列化为 JSON 数组。

- [ ] **Step 2: 验证 GET 消息接口返回 list**

启动后端后用 curl 测试（或写个 Python 脚本）：

```python
# 启动后端后，先 POST 一条带图片的消息（用前端或 curl），然后 GET 消息历史
# 验证返回的 content 是 list 而非 str
```

（此步骤依赖前端能发送消息，可在 Task 7 完成后统一验证。）

- [ ] **Step 3: Commit（如有改动）**

```bash
git add lc_agent/server/routes/sessions.py
git commit -m "fix(sessions): ensure content list is returned as JSON"
```

---

## Task 5: 前端 fileUpload.ts 工具函数

**Files:**
- Create: `frontend/src/utils/fileUpload.ts`

- [ ] **Step 1: 创建 fileUpload.ts**

```typescript
/**
 * 附件处理工具：图片压缩、文本文件读取、content blocks 构造
 */

export interface ContentBlock {
  type: 'text' | 'image_url'
  text?: string
  image_url?: { url: string }
}

export interface Attachment {
  id: string
  type: 'image' | 'text_file'
  name: string
  // image 专属
  dataUrl?: string
  // text_file 专属
  textContent?: string
}

/** 支持的文本文件扩展名白名单 */
export const TEXT_EXTENSIONS = [
  'txt', 'md', 'markdown', 'json', 'yaml', 'yml', 'csv', 'log', 'xml', 'html', 'htm',
  'js', 'ts', 'jsx', 'tsx', 'py', 'go', 'rs', 'java', 'c', 'cpp', 'h', 'hpp', 'sh', 'sql',
  'css', 'scss', 'less', 'vue', 'toml', 'ini', 'conf',
]

/** 扩展名到代码块语言的映射 */
const EXT_TO_LANG: Record<string, string> = {
  js: 'javascript', ts: 'typescript', jsx: 'jsx', tsx: 'tsx',
  py: 'python', go: 'go', rs: 'rust', java: 'java',
  c: 'c', cpp: 'cpp', h: 'c', hpp: 'cpp',
  sh: 'bash', sql: 'sql', css: 'css', scss: 'scss',
  less: 'less', vue: 'vue', html: 'html', htm: 'html',
  xml: 'xml', json: 'json', yaml: 'yaml', yml: 'yaml',
  toml: 'toml', ini: 'ini', conf: 'ini',
  md: 'markdown', markdown: 'markdown',
}

/** 图片上限（软提示） */
export const MAX_IMAGE_COUNT = 9

/** 图片压缩最长边 */
const MAX_IMAGE_EDGE = 1280

/** 生成简单 uuid */
function genId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

/** 获取文件扩展名（小写，无点） */
export function getExtension(filename: string): string {
  const parts = filename.split('.')
  return parts.length > 1 ? parts.pop()!.toLowerCase() : ''
}

/** 判断文件是否为图片 */
export function isImageFile(file: File): boolean {
  return file.type.startsWith('image/')
}

/** 判断文件是否为白名单文本文件 */
export function isTextFile(file: File): boolean {
  const ext = getExtension(file.name)
  return TEXT_EXTENSIONS.includes(ext)
}

/** 压缩图片：最长边 1280，保留原格式 */
export async function compressImage(file: File): Promise<string> {
  const bitmap = await createImageBitmap(file)
  let { width, height } = bitmap
  if (width > MAX_IMAGE_EDGE || height > MAX_IMAGE_EDGE) {
    const ratio = Math.min(MAX_IMAGE_EDGE / width, MAX_IMAGE_EDGE / height)
    width = Math.round(width * ratio)
    height = Math.round(height * ratio)
  }
  const canvas = new OffscreenCanvas(width, height)
  const ctx = canvas.getContext('bitmaprenderer')
  if (!ctx) throw new Error('Canvas 2D context unavailable')
  ctx.transferFromImageBitmap(bitmap)
  // 保留原格式：png 输出 png，jpeg 输出 jpeg
  const blob = await canvas.convertToBlob({ type: file.type, quality: 0.8 })
  return await blobToDataURL(blob)
}

function blobToDataURL(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error('Failed to read blob as data URL'))
    reader.readAsDataURL(blob)
  })
}

/** 读取文本文件内容 */
export function readTextFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error(`Failed to read ${file.name}`))
    reader.readAsText(file, 'utf-8')
  })
}

/** 把 File 转为 Attachment */
export async function fileToAttachment(file: File): Promise<Attachment | null> {
  if (isImageFile(file)) {
    try {
      const dataUrl = await compressImage(file)
      return {
        id: genId(),
        type: 'image',
        name: file.name || `image-${Date.now()}.png`,
        dataUrl,
      }
    } catch (e) {
      console.error('Image compression failed:', e)
      return null
    }
  }
  if (isTextFile(file)) {
    try {
      const textContent = await readTextFile(file)
      return {
        id: genId(),
        type: 'text_file',
        name: file.name,
        textContent,
      }
    } catch (e) {
      console.error('Text file read failed:', e)
      return null
    }
  }
  return null
}

/** 批量处理文件 */
export async function filesToAttachments(files: File[]): Promise<{ attachments: Attachment[]; rejected: string[] }> {
  const attachments: Attachment[] = []
  const rejected: string[] = []
  for (const file of files) {
    const att = await fileToAttachment(file)
    if (att) {
      attachments.push(att)
    } else {
      rejected.push(file.name)
    }
  }
  return { attachments, rejected }
}

/** 从剪贴板 items 提取图片文件（只取图片，忽略文本） */
export function imageFilesFromClipboard(items: DataTransferItemList): File[] {
  const files: File[] = []
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.kind === 'file' && item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) files.push(file)
    }
  }
  return files
}

/** 构造 content blocks list */
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

/** 统计图片数量 */
export function countImages(attachments: Attachment[]): number {
  return attachments.filter(a => a.type === 'image').length
}
```

- [ ] **Step 2: 验证 TypeScript 编译通过**

Run: `cd frontend && npx tsc --noEmit src/utils/fileUpload.ts`

Expected: 无错误输出。如果有 `OffscreenCanvas` 类型未定义，在 `frontend/src/types/` 或 `tsconfig.json` 的 `lib` 中添加 `DOM`（通常已有）。

- [ ] **Step 3: Commit**

```bash
cd frontend
git add src/utils/fileUpload.ts
git commit -m "feat(frontend): add fileUpload utils for image compression and text file reading"
```

---

## Task 6: 前端 ChatInput.vue 改造

**Files:**
- Modify: `frontend/src/components/chat/ChatInput.vue`

- [ ] **Step 1: 修改 script setup 部分**

替换 `frontend/src/components/chat/ChatInput.vue` 的 `<script setup lang="ts">` 整块（第 54-143 行）：

```typescript
<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import {
  type Attachment,
  type ContentBlock,
  buildContentBlocks,
  countImages,
  filesToAttachments,
  imageFilesFromClipboard,
  isImageFile,
  isTextFile,
  MAX_IMAGE_COUNT,
  fileToAttachment,
} from '@/utils/fileUpload'

const props = defineProps<{
  isStreaming?: boolean
  editContent?: string  // 兼容老接口：纯文本回填
  editAttachments?: Attachment[]  // 新增：附件回填（编辑重放）
  isEditing?: boolean
}>()

const emit = defineEmits<{
  send: [content: ContentBlock[]]
  stop: []
  cancelEdit: []
}>()

const chatStore = useChatStore()
const { isStreaming } = storeToRefs(chatStore)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const messageText = ref('')
const attachments = ref<Attachment[]>([])
const isStreamingState = computed(() => props.isStreaming ?? isStreaming.value)
const isInputDisabled = computed(() => isStreamingState.value)
const canSend = computed(() =>
  (Boolean(messageText.value.trim()) || attachments.value.length > 0) && !isInputDisabled.value,
)

// 编辑回填：支持纯文本 + 附件
watch(() => [props.editContent, props.editAttachments] as const, async ([content, atts]) => {
  messageText.value = content || ''
  attachments.value = atts ? [...atts] : []
  await nextTick()
  resizeTextarea()
  if (messageText.value || attachments.value.length > 0) {
    focusTextarea('end')
  }
}, { immediate: true })

onMounted(async () => {
  await nextTick()
  resizeTextarea()
  if (!isInputDisabled.value) {
    focusTextarea('end')
  }
})

function resizeTextarea() {
  const textarea = textareaRef.value
  if (!textarea) return
  textarea.style.height = 'auto'
  const maxHeight = Math.floor(window.innerHeight * 0.4)
  const nextHeight = Math.min(textarea.scrollHeight, maxHeight)
  textarea.style.height = `${nextHeight}px`
  textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden'
}

function focusTextarea(position: 'start' | 'end' = 'end') {
  const textarea = textareaRef.value
  if (!textarea) return
  textarea.focus()
  const cursor = position === 'start' ? 0 : textarea.value.length
  textarea.setSelectionRange(cursor, cursor)
}

function clearInput() {
  messageText.value = ''
  attachments.value = []
  nextTick(() => {
    resizeTextarea()
    focusTextarea('end')
  })
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' || (!event.ctrlKey && !event.metaKey) || event.isComposing) return
  event.preventDefault()
  handleSubmit()
}

// 粘贴：检测剪贴板图片
function handlePaste(event: ClipboardEvent) {
  if (!event.clipboardData) return
  const imageFiles = imageFilesFromClipboard(event.clipboardData.items)
  if (imageFiles.length === 0) return  // 纯文本走原生 paste
  event.preventDefault()
  void addFiles(imageFiles)
}

// 拖拽
function handleDrop(event: DragEvent) {
  event.preventDefault()
  if (!event.dataTransfer?.files?.length) return
  void addFiles(Array.from(event.dataTransfer.files))
}

function handleDragover(event: DragEvent) {
  event.preventDefault()  // 允许 drop
}

// 文件选择按钮
function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileInputChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return
  void addFiles(Array.from(input.files))
  input.value = ''  // 清空，允许重复选择同一文件
}

async function addFiles(files: File[]) {
  const { attachments: newAtts, rejected } = await filesToAttachments(files)
  if (newAtts.length > 0) {
    attachments.value.push(...newAtts)
    // 图片数量软提示
    const imgCount = countImages(attachments.value)
    if (imgCount > MAX_IMAGE_COUNT) {
      ElMessage.warning(`图片较多（${imgCount} 张），可能影响响应速度`)
    }
  }
  for (const name of rejected) {
    ElMessage.error(`不支持的文件类型: ${name}，仅支持图片和文本文件`)
  }
  if (newAtts.length === 0 && rejected.length === files.length) {
    ElMessage.error('没有可处理的文件')
  }
}

function removeAttachment(id: string) {
  attachments.value = attachments.value.filter(a => a.id !== id)
}

function handleSubmit() {
  if (isInputDisabled.value) return
  const blocks = buildContentBlocks(messageText.value, attachments.value)
  if (blocks.length === 0) return
  emit('send', blocks)
  clearInput()
}

function handleStop() {
  emit('stop')
}

function handleCancelEdit() {
  clearInput()
  emit('cancelEdit')
}
</script>
```

- [ ] **Step 2: 修改 template 部分**

替换 `<template>` 整块（第 1-52 行）：

```vue
<template>
  <div class="chat-input-wrapper">
    <div v-if="isEditing" class="edit-banner">
      <span>正在编辑上一条消息</span>
      <button type="button" class="cancel-edit-btn" @click="handleCancelEdit">取消</button>
    </div>
    <div
      class="textarea-shell"
      :class="{ 'is-disabled': isInputDisabled }"
      @drop="handleDrop"
      @dragover="handleDragover"
    >
      <!-- 附件预览区 -->
      <div v-if="attachments.length > 0" class="attachments-preview">
        <div
          v-for="att in attachments"
          :key="att.id"
          class="attachment-item"
        >
          <img
            v-if="att.type === 'image'"
            :src="att.dataUrl"
            class="attachment-image"
            :alt="att.name"
          />
          <div v-else class="attachment-file">
            <span class="file-icon">📄</span>
            <span class="file-name" :title="att.name">{{ att.name }}</span>
          </div>
          <button
            type="button"
            class="attachment-remove"
            @click="removeAttachment(att.id)"
          >×</button>
        </div>
      </div>

      <textarea
        ref="textareaRef"
        v-model="messageText"
        class="chat-textarea"
        rows="1"
        placeholder="Send a message... (可粘贴/拖拽图片或文本文件)"
        enterkeyhint="enter"
        :disabled="isInputDisabled"
        @input="resizeTextarea"
        @keydown="handleKeydown"
        @paste="handlePaste"
      />
      <div class="input-actions">
        <!-- 文件选择按钮 -->
        <button
          v-if="!isStreamingState"
          type="button"
          class="input-action-btn attach-btn"
          aria-label="附加文件"
          title="附加图片或文本文件"
          :disabled="isInputDisabled"
          @click="triggerFileInput"
        >
          <span class="attach-icon">📎</span>
        </button>
        <input
          ref="fileInputRef"
          type="file"
          multiple
          class="hidden-file-input"
          accept="image/*,.txt,.md,.markdown,.json,.yaml,.yml,.csv,.log,.xml,.html,.htm,.js,.ts,.jsx,.tsx,.py,.go,.rs,.java,.c,.cpp,.h,.hpp,.sh,.sql,.css,.scss,.less,.vue,.toml,.ini,.conf"
          @change="handleFileInputChange"
        />
        <button
          v-if="isStreamingState"
          type="button"
          class="input-action-btn stop-btn animated-stop-btn"
          aria-label="停止生成"
          title="停止生成"
          @click="handleStop"
        >
          <span class="stop-spinner" aria-hidden="true">
            <span class="stop-square" />
          </span>
        </button>
        <button
          v-else-if="messageText || attachments.length > 0"
          type="button"
          class="input-action-btn clear-btn"
          @click="clearInput"
        >
          清空
        </button>
        <button
          v-if="!isStreamingState"
          type="button"
          class="send-btn"
          :disabled="!canSend"
          @click="handleSubmit"
        >
          发送
        </button>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: 追加新增样式**

在 `<style scoped>` 末尾（第 343 行 `}` 之后）追加：

```css
.attachments-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 6px 4px 0;
  width: 100%;
}

.attachment-item {
  position: relative;
  width: 60px;
  height: 60px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  overflow: hidden;
  background: var(--el-fill-color-light);
  display: flex;
  align-items: center;
  justify-content: center;
}

.attachment-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.attachment-file {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.file-icon {
  font-size: 20px;
  line-height: 1;
}

.file-name {
  font-size: 9px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attachment-remove {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 16px;
  height: 16px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 12px;
  line-height: 14px;
  padding: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.attachment-remove:hover {
  background: rgba(0, 0, 0, 0.8);
}

.attach-btn {
  font-size: 16px;
  line-height: 1;
  padding: 4px 6px;
}

.attach-icon {
  display: inline-block;
}

.hidden-file-input {
  display: none;
}

.textarea-shell {
  flex-wrap: wrap;
}

@media (max-width: 520px) {
  .attachment-item {
    width: 50px;
    height: 50px;
  }
}
```

注意：现有的 `.textarea-shell` 已经有 `display: flex; align-items: flex-end;`，新增 `flex-wrap: wrap` 让附件预览区能占满整行。

- [ ] **Step 4: 验证 TypeScript 编译**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: 无错误。如果 `editAttachments` prop 未被现有 ChatView 使用，会有警告但不阻塞——ChatView 会在 Task 8 中适配。

- [ ] **Step 5: Commit**

```bash
cd frontend
git add src/components/chat/ChatInput.vue
git commit -m "feat(chat-input): support paste/drop/file-select for images and text files"
```

---

## Task 7: 前端 sse-client.ts 改造

**Files:**
- Modify: `frontend/src/api/sse-client.ts:85-107`

- [ ] **Step 1: 修改 sendMessage 签名**

修改 `frontend/src/api/sse-client.ts` 第 85-107 行：

```typescript
// 之前
async sendMessage(
  content: string,
  presetId?: string,
  model?: string,
  options?: { replaceFromMessageId?: string; history?: any[]; llmParams?: Record<string, any> | null },
): Promise<void> {
  if (!this._threadId) throw new Error('threadId not set')

  const body: Record<string, any> = {
    input: content,
    preset_id: presetId || 'chat',
    model: model || '',
  }
  if (options?.replaceFromMessageId) {
    body.replace_from_message_id = options.replaceFromMessageId
    body.history = options.history || []
  }
  if (options?.llmParams && Object.keys(options.llmParams).length > 0) {
    body.llm_params = options.llmParams
  }

  await this._startStream(body)
}

// 之后
async sendMessage(
  content: ContentBlock[],
  presetId?: string,
  model?: string,
  options?: { replaceFromMessageId?: string; history?: any[]; llmParams?: Record<string, any> | null },
): Promise<void> {
  if (!this._threadId) throw new Error('threadId not set')

  const body: Record<string, any> = {
    input: content,
    preset_id: presetId || 'chat',
    model: model || '',
  }
  if (options?.replaceFromMessageId) {
    body.replace_from_message_id = options.replaceFromMessageId
    body.history = options.history || []
  }
  if (options?.llmParams && Object.keys(options.llmParams).length > 0) {
    body.llm_params = options.llmParams
  }

  await this._startStream(body)
}
```

在文件顶部 import 中添加：

```typescript
import type { ContentBlock } from '@/utils/fileUpload'
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: 无错误。

- [ ] **Step 3: Commit**

```bash
cd frontend
git add src/api/sse-client.ts
git commit -m "refactor(sse-client): sendMessage accepts ContentBlock[] instead of string"
```

---

## Task 8: 前端 chat.ts store 改造

**Files:**
- Modify: `frontend/src/stores/chat.ts`

- [ ] **Step 1: 修改 ChatMessage 和 ReplayMessage 类型**

修改 `frontend/src/stores/chat.ts`：

第 87-100 行 `ChatMessage`：

```typescript
// 之前
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content: string
  timestamp: number
  toolCalls?: ToolCall[]
  segments?: ContentSegment[]
  subAgents?: Record<string, SubAgentEntry>
  isStreaming?: boolean
  isSystem?: boolean
  usage?: MessageUsage
  httpTraces?: HttpTrace[]
  httpTracesCount?: number
}

// 之后
import type { ContentBlock, Attachment } from '@/utils/fileUpload'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content: string | ContentBlock[]  // user 消息是 ContentBlock[]，assistant 保持 string
  timestamp: number
  toolCalls?: ToolCall[]
  segments?: ContentSegment[]
  subAgents?: Record<string, SubAgentEntry>
  isStreaming?: boolean
  isSystem?: boolean
  usage?: MessageUsage
  httpTraces?: HttpTrace[]
  httpTracesCount?: number
  // 编辑重放时回填到 ChatInput 的附件（仅 user 消息）
  attachments?: Attachment[]
}
```

第 121-124 行 `ReplayMessage`：

```typescript
// 之前
export interface ReplayMessage {
  role: 'user' | 'assistant'
  content: string
}

// 之后
export interface ReplayMessage {
  role: 'user' | 'assistant'
  content: string | ContentBlock[]
}
```

- [ ] **Step 2: 修改 normalizeHistoryMessage 适配 content list**

修改 `frontend/src/stores/chat.ts` 第 212-283 行 `normalizeHistoryMessage`：

关键改动：assistant 消息的 content 现在从 DB 返回的是 `list[dict]`（后端统一存 list），需要展开为字符串；user 消息的 content 保持 list。

```typescript
function normalizeHistoryMessage(msg: any): ChatMessage | null {
  if (msg.role === 'system') {
    // system 消息 content 统一为 string
    const rawContent = msg.content
    const content = Array.isArray(rawContent)
      ? (rawContent.find((b: any) => b.type === 'text')?.text || '')
      : (rawContent || '')
    return {
      id: msg.id || createClientId(),
      role: 'user',
      content,
      timestamp: msg.created_at ? new Date(msg.created_at).getTime() : Date.now(),
      isSystem: true,
    }
  }

  const role = msg.role === 'human' ? 'user' : msg.role === 'ai' ? 'assistant' : msg.role
  if (!['user', 'assistant', 'tool'].includes(role)) return null

  const toolCalls = (msg.tool_calls || msg.toolCalls || []).map((tc: any) => ({
    name: tc.name || '',
    runId: tc.runId || tc.run_id || tc.id,
    args: tc.args || {},
    result: tc.result,
    status: normalizeToolStatus(tc.status),
    startTime: tc.startTime ?? tc.start_time,
    duration: tc.duration,
    resultLength: tc.resultLength ?? tc.result_length ?? tc.result?.length,
    is_subagent: tc.is_subagent || false,
    sub_session_id: tc.sub_session_id || '',
  }))
  const usage = normalizeHistoryUsage(msg.usage)
  if (usage && toolCalls.length > usage.toolCallCount) {
    usage.toolCallCount = toolCalls.length
  }

  const subAgents: Record<string, SubAgentEntry> = {}
  for (const tc of toolCalls) {
    if (tc.is_subagent && tc.runId) {
      subAgents[tc.runId] = {
        tool_call_id: tc.runId,
        name: tc.name,
        sub_session_id: tc.sub_session_id || '',
        query: typeof tc.args === 'object' ? (tc.args?.query || '') : '',
        status: tc.status === 'running' ? 'running' : normalizeSubAgentDoneStatus(tc.status),
        tokenPreview: tc.result || '',
        toolCallCount: 0,
        tokenCount: 0,
        tokens: '',
        thinking: '',
        thinkCount: 0,
        innerToolCalls: [],
        duration: tc.duration,
      }
    }
  }

  const httpTraces = normalizeHttpTraces(msg.http_traces || msg.httpTraces)
  const httpTracesCount = msg.http_traces_count ?? msg.httpTracesCount ?? httpTraces?.length ?? 0

  // content 处理：user 保持 list[dict]，assistant 展开为 string
  let content: string | ContentBlock[]
  if (role === 'user') {
    content = Array.isArray(msg.content) ? msg.content : [{ type: 'text', text: String(msg.content || '') }]
  } else {
    // assistant: 从 list[dict] 取第一个 text block 的 text，保持现有 string 流式逻辑
    const rawContent = msg.content
    let textContent = ''
    if (Array.isArray(rawContent)) {
      textContent = rawContent.find((b: any) => b.type === 'text')?.text || ''
    } else {
      textContent = rawContent || ''
    }
    // 重新应用 tool/http 标记
    textContent = ensureToolMarkers(textContent, toolCalls)
    if (httpTracesCount > 0) {
      textContent = ensureHttpMarkers(textContent, httpTracesCount)
    }
    content = textContent
  }

  return {
    id: msg.id || createClientId(),
    role,
    content,
    timestamp: msg.created_at ? new Date(msg.created_at).getTime() : Date.now(),
    toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
    subAgents: Object.keys(subAgents).length > 0 ? subAgents : undefined,
    usage,
    httpTraces,
    httpTracesCount,
  }
}
```

- [ ] **Step 3: 修改 sendMessage 签名和用户消息 push**

修改 `frontend/src/stores/chat.ts` 第 935-973 行：

```typescript
// 之前
async function sendMessage(
  content: string,
  presetId: string = 'chat',
  modelId: string = '',
  options: SendMessageOptions = {},
) {
  if (!content.trim()) return
  // ...
  state.messages.value.push({
    id: createClientId(),
    role: 'user',
    content: content.trim(),
    timestamp: Date.now(),
  })
  state.client.sendMessage(content.trim(), presetId, modelId, {
    replaceFromMessageId: options.replaceFromMessageId,
    history: options.history,
    llmParams: options.llmParams,
  })
}

// 之后
async function sendMessage(
  content: ContentBlock[],
  presetId: string = 'chat',
  modelId: string = '',
  options: SendMessageOptions = {},
) {
  if (!content.length) return
  // ...
  state.messages.value.push({
    id: createClientId(),
    role: 'user',
    content,
    timestamp: Date.now(),
  })
  state.client.sendMessage(content, presetId, modelId, {
    replaceFromMessageId: options.replaceFromMessageId,
    history: options.history,
    llmParams: options.llmParams,
  })
}
```

注意：`sessionsStore.updateTitleLocal(realId, content.trim().slice(0, 30))` 这一行需要改为从 content blocks 提取文本：

```typescript
// 之前
if (isFirstMessage) {
  sessionsStore.updateTitleLocal(realId, content.trim().slice(0, 30))
}

// 之后
if (isFirstMessage) {
  const firstText = content.find(b => b.type === 'text')?.text || ''
  sessionsStore.updateTitleLocal(realId, firstText.slice(0, 30))
}
```

- [ ] **Step 4: 修改 getReplayHistory 适配 content list**

在 `frontend/src/views/ChatView.vue` 第 612-626 行 `getReplayHistory`：

```typescript
// 之前
function getReplayHistory(beforeMessageId: string): ReplayMessage[] {
  const idx = messages.value.findIndex(msg => msg.id === beforeMessageId)
  if (idx < 0) return []

  return messages.value
    .slice(0, idx)
    .filter((msg): msg is typeof msg & { role: 'user' | 'assistant' } =>
      msg.role === 'user' || msg.role === 'assistant',
    )
    .map(msg => ({
      role: msg.role,
      content: stripUiMarkers(msg.content || ''),
    }))
    .filter(msg => msg.content.trim())
}

// 之后
function getReplayHistory(beforeMessageId: string): ReplayMessage[] {
  const idx = messages.value.findIndex(msg => msg.id === beforeMessageId)
  if (idx < 0) return []

  return messages.value
    .slice(0, idx)
    .filter((msg): msg is typeof msg & { role: 'user' | 'assistant' } =>
      msg.role === 'user' || msg.role === 'assistant',
    )
    .map(msg => {
      if (msg.role === 'user' && Array.isArray(msg.content)) {
        // user 消息直接传 content blocks
        return { role: msg.role, content: msg.content }
      }
      // assistant 消息或老格式 user：传字符串
      const text = typeof msg.content === 'string' ? msg.content : ''
      return { role: msg.role, content: stripUiMarkers(text) }
    })
    .filter(msg => {
      if (Array.isArray(msg.content)) return msg.content.length > 0
      return msg.content.trim()
    })
}
```

- [ ] **Step 5: 验证 TypeScript 编译**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: 无错误。可能有少量"content 类型不兼容"的警告，需要逐一修复（如其他地方读取 `msg.content` 假定是 string 的代码）。

- [ ] **Step 6: Commit**

```bash
cd frontend
git add src/stores/chat.ts src/views/ChatView.vue
git commit -m "refactor(chat-store): ChatMessage.content supports ContentBlock[] for user messages"
```

---

## Task 9: 前端 ChatView.vue 渲染改造

**Files:**
- Modify: `frontend/src/views/ChatView.vue`

- [ ] **Step 1: 修改 ChatBubbleItem 和 computed items**

在 `frontend/src/views/ChatView.vue` 中找到 `ChatBubbleItem` 类型定义（搜索 `interface ChatBubbleItem` 或 `type ChatBubbleItem`），把 `content: string` 改为 `content: string | ContentBlock[]`。

修改 `createBubbleItem` 函数（约第 435-464 行），保持 `content: msg.content` 直接透传（不再强制 string）。

- [ ] **Step 2: 修改用户消息渲染模板**

修改 `frontend/src/views/ChatView.vue` 第 149-156 行：

```vue
<!-- 之前 -->
<template v-else>
  <div
    v-if="item.isMarkdown"
    class="markdown-body"
    v-html="renderMarkdown(stripThinkingMarkers(item.content || ''))"
  />
  <span v-else class="user-plain-text">{{ item.content }}</span>
</template>

<!-- 之后 -->
<template v-else>
  <!-- user 消息且 content 是 ContentBlock[] -->
  <div v-if="item.role === 'user' && Array.isArray(item.content)" class="user-content-blocks">
    <template v-for="(block, i) in item.content" :key="i">
      <span v-if="block.type === 'text'" class="user-text-block">{{ block.text }}</span>
      <img
        v-else-if="block.type === 'image_url'"
        :src="block.image_url.url"
        class="user-image-block"
        @click="previewImage(block.image_url.url)"
      />
    </template>
  </div>
  <!-- user 消息且 content 是 string（老格式回退） -->
  <span v-else-if="item.role === 'user'" class="user-plain-text">{{ item.content }}</span>
  <!-- assistant 消息（保持现有 markdown 渲染） -->
  <div
    v-else
    class="markdown-body"
    v-html="renderMarkdown(stripThinkingMarkers(String(item.content || '')))"
  />
</template>
```

- [ ] **Step 3: 添加 previewImage 函数和 el-image-viewer**

在 `frontend/src/views/ChatView.vue` 的 `<script setup>` 中添加（如果还没有引入 el-image-viewer）：

```typescript
import { ElImageViewer } from 'element-plus'

const imageViewerVisible = ref(false)
const imageViewerUrl = ref('')

function previewImage(url: string) {
  imageViewerUrl.value = url
  imageViewerVisible.value = true
}
```

在 template 末尾（InterruptDialog 附近）添加：

```vue
<el-image-viewer
  v-if="imageViewerVisible"
  :url-list="[imageViewerUrl]"
  @close="imageViewerVisible = false"
/>
```

- [ ] **Step 4: 添加用户消息渲染样式**

在 `<style scoped>` 中追加：

```css
.user-content-blocks {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 100%;
}

.user-text-block {
  white-space: pre-wrap;
  word-break: break-word;
}

.user-image-block {
  max-width: 240px;
  max-height: 240px;
  border-radius: 6px;
  cursor: zoom-in;
  border: 1px solid var(--el-border-color);
}
```

- [ ] **Step 5: 修改 startEditMessage 支持附件回填**

修改 `frontend/src/views/ChatView.vue` 第 565-569 行 `startEditMessage`：

```typescript
// 之前
function startEditMessage(item: ChatBubbleItem) {
  if (!canEditMessage(item)) return
  editingMessageId.value = item.messageId
  editingContent.value = item.content || ''
}

// 之后
function startEditMessage(item: ChatBubbleItem) {
  if (!canEditMessage(item)) return
  editingMessageId.value = item.messageId
  // 从 content blocks 还原到 ChatInput：文本块拼回 textarea，图片/文件块还原到 attachments
  if (Array.isArray(item.content)) {
    const textParts: string[] = []
    const restoredAtts: Attachment[] = []
    let attIdx = 0
    for (const block of item.content) {
      if (block.type === 'text') {
        // 文本文件块格式: "📎 `xxx.py`:\n```python\n...\n```"
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

在 `<script setup>` 顶部添加：

```typescript
import type { Attachment } from '@/utils/fileUpload'
const editingAttachments = ref<Attachment[]>([])
```

修改 `cancelEdit` 第 571-574 行：

```typescript
// 之前
function cancelEdit() {
  editingMessageId.value = null
  editingContent.value = ''
}

// 之后
function cancelEdit() {
  editingMessageId.value = null
  editingContent.value = ''
  editingAttachments.value = []
}
```

- [ ] **Step 6: 修改 ChatInput 的 props 传递**

修改 `frontend/src/views/ChatView.vue` 第 199-207 行：

```vue
<!-- 之前 -->
<ChatInput
  v-else
  :is-streaming="isStreaming"
  :edit-content="editingContent"
  :is-editing="Boolean(editingMessageId)"
  @send="handleSend"
  @stop="handleStop"
  @cancel-edit="cancelEdit"
/>

<!-- 之后 -->
<ChatInput
  v-else
  :is-streaming="isStreaming"
  :edit-content="editingContent"
  :edit-attachments="editingAttachments"
  :is-editing="Boolean(editingMessageId)"
  @send="handleSend"
  @stop="handleStop"
  @cancel-edit="cancelEdit"
/>
```

- [ ] **Step 7: 修改 handleSend 签名**

修改 `frontend/src/views/ChatView.vue` 第 684-697 行：

```typescript
// 之前
function handleSend(content: string) {
  const editMessageId = editingMessageId.value
  const history = editMessageId ? getReplayHistory(editMessageId) : undefined
  const modelOverride = agentsStore.isCodeAgent ? '' : toolsStore.currentModel
  if (editingMessageId.value) {
    chatStore.truncateAfterMessage(editingMessageId.value)
    cancelEdit()
  }
  chatStore.sendMessage(content, agentsStore.currentAgentId, modelOverride, {
    replaceFromMessageId: editMessageId || undefined,
    history,
    llmParams: toolsStore.llmParams,
  })
}

// 之后
function handleSend(content: ContentBlock[]) {
  const editMessageId = editingMessageId.value
  const history = editMessageId ? getReplayHistory(editMessageId) : undefined
  const modelOverride = agentsStore.isCodeAgent ? '' : toolsStore.currentModel
  if (editingMessageId.value) {
    chatStore.truncateAfterMessage(editingMessageId.value)
    cancelEdit()
  }
  chatStore.sendMessage(content, agentsStore.currentAgentId, modelOverride, {
    replaceFromMessageId: editMessageId || undefined,
    history,
    llmParams: toolsStore.llmParams,
  })
}
```

在 `<script setup>` 顶部添加 import：

```typescript
import type { ContentBlock } from '@/utils/fileUpload'
```

- [ ] **Step 8: 修改 canEditMessage 允许 user 消息编辑**

搜索 `canEditMessage` 函数定义，确认它允许 user 消息编辑（应该已经允许，因为现有功能就支持编辑 user 消息）。如果 `canEditMessage` 检查的是 `item.role === 'user'`，则无需修改。

- [ ] **Step 9: 验证 TypeScript 编译**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: 无错误。

- [ ] **Step 10: Commit**

```bash
cd frontend
git add src/views/ChatView.vue
git commit -m "feat(chat-view): render user content blocks and support image preview + edit replay"
```

---

## Task 10: 端到端验证

**Files:**
- 无修改，仅验证

- [ ] **Step 1: 启动后端**

Run: `cd d:\codes\lc-agent-bfzs && D:\ProgramData\Miniconda3\envs\py312\python.exe bfzs\main.py`

Expected: 服务启动无错误，监听端口正常。

- [ ] **Step 2: 启动前端**

Run: `cd d:\codes\lc-agent\frontend && npm run dev`

Expected: Vite dev server 启动，无编译错误。

- [ ] **Step 3: 验证纯文本消息**

在浏览器打开前端，发送一条纯文本消息"你好"。

Expected:
- 消息正常发送，AI 正常回复
- 用户气泡显示文本（纯文本，不 markdown）
- assistant 消息正常 markdown 渲染
- 历史消息刷新后仍正常显示

- [ ] **Step 4: 验证粘贴截图**

用截图工具截图（Win+Shift+S），在输入框 Ctrl+V 粘贴。

Expected:
- 输入框上方显示缩略图
- 点击 × 可删除
- 发送后用户气泡显示图片
- AI 能识别图片内容并回复
- 点击图片可全屏预览

- [ ] **Step 5: 验证拖拽文件**

把一个 `.py` 文件拖到输入框区域。

Expected:
- 输入框上方显示文件名标签
- 发送后用户气泡显示 `📎 foo.py:` 和代码内容（纯文本）
- AI 能理解文件内容

- [ ] **Step 6: 验证文件选择按钮**

点击 📎 按钮，选择一张图片。

Expected: 图片加入附件预览区。

- [ ] **Step 7: 验证非法文件**

拖一个 `.pdf` 文件到输入框。

Expected: toast 提示"不支持的文件类型: xxx.pdf，仅支持图片和文本文件"，不加入附件。

- [ ] **Step 8: 验证多图**

粘贴 3 张截图，发送。

Expected: 3 张图片都显示在用户气泡，AI 能看到所有图片。

- [ ] **Step 9: 验证编辑重放**

发送一条带图片的消息，等 AI 回复后点击编辑按钮。

Expected:
- ChatInput 回填文本和图片附件
- 可修改后重新发送
- 历史被截断并重新生成

- [ ] **Step 10: 验证刷新后历史**

发送几条带图片/文件的消息后刷新页面。

Expected: 历史消息正常加载，图片和文件内容正确显示。

- [ ] **Step 11: Commit（如有修复）**

```bash
git add -A
git commit -m "fix: end-to-end verification adjustments"
```

---

## Self-Review 检查

### Spec 覆盖

| Spec 章节 | 覆盖任务 |
|----------|---------|
| 1. DB Schema | Task 1 |
| 1. API Schema | Task 2 |
| 1. 老数据处理 | Task 1 (TRUNCATE) |
| 2. ChatInput 三种输入 | Task 6 |
| 2. 图片压缩 | Task 5 (compressImage) |
| 2. 文本文件读取 | Task 5 (readTextFile) |
| 2. 扩展名白名单 | Task 5 (TEXT_EXTENSIONS) |
| 2. 预览区 | Task 6 (template) |
| 2. send 事件改造 | Task 5 (buildContentBlocks) + Task 6 |
| 2. 非法文件处理 | Task 5 + Task 6 (toast) |
| 3. ChatMessage 类型 | Task 8 |
| 3. sendMessage 签名 | Task 7 (sse-client) + Task 8 (store) |
| 3. 历史消息加载 | Task 8 (normalizeHistoryMessage) |
| 3. ChatView 渲染 | Task 9 |
| 3. 编辑/重放 | Task 8 (getReplayHistory) + Task 9 (startEditMessage) |
| 4. sse.py 改造 | Task 2 |
| 4. engine.py 改造 | Task 3 |
| 4. 持久化层 | Task 1 (models) + Task 2 (persistence) |
| 4. 标题生成 | Task 2 (_extract_text_from_blocks) + Task 3 |
| 4. get_session_messages | Task 4 |
| 5. 前端错误处理 | Task 5 + Task 6 |
| 5. 后端错误处理 | Task 2 (空校验) |
| 5. 图片数量上限 | Task 5 (MAX_IMAGE_COUNT) + Task 6 (软提示) |

### 类型一致性

- `ContentBlock` 类型在 Task 5 定义，Task 7/8/9 引用，签名一致
- `Attachment` 类型在 Task 5 定义，Task 6/8/9 引用，签名一致
- `buildContentBlocks(text: string, attachments: Attachment[]): ContentBlock[]` 在 Task 5 定义，Task 6 调用，签名一致
- `sendMessage(content: ContentBlock[])` 在 Task 7 (sse-client) 和 Task 8 (store) 中一致
- `ChatMessage.content: string | ContentBlock[]` 在 Task 8 定义，Task 9 使用一致

无类型不一致问题。
