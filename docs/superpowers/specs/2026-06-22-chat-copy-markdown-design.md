# Chat Copy-to-Markdown 设计文档

> 日期: 2026-06-22
> 状态: 待实现

## 1. 概述

为聊天界面添加多层级 Markdown 复制功能，允许用户将对话内容（含思考过程、工具调用、AI回答）以结构化 Markdown 格式复制到剪贴板。

**核心需求：**
- 单条消息复制（user / assistant）
- 段落级复制（思考 / 工具调用 / 文本回答 分别可复制）
- 多轮对话复制（复制最近 N 轮）
- 输出格式为 Markdown
- 兼容桌面和手机浏览器

## 2. 架构

```
┌─────────────────────────────────────────────┐
│                 ChatView.vue                │
│  ┌───────────────────────────────────┐      │
│  │  CopyRoundsButton (右上角)        │      │
│  │  → popover: 轮数输入 + 选项 + 复制 │      │
│  └───────────────────────────────────┘      │
│                                             │
│  ┌─ BubbleList ──────────────────────┐      │
│  │                                   │      │
│  │  ┌─ user bubble ───────────────┐  │      │
│  │  │  消息内容                    │  │      │
│  │  │  MessageToolbar [📋 复制]   │  │      │
│  │  └─────────────────────────────┘  │      │
│  │                                   │      │
│  │  ┌─ assistant bubble ──────────┐  │      │
│  │  │  思考 / 工具调用 / 回答      │  │      │
│  │  │  MessageToolbar             │  │      │
│  │  │  [复制全部][思考][工具][回答] │  │      │
│  │  └─────────────────────────────┘  │      │
│  │                                   │      │
│  └───────────────────────────────────┘      │
│                                             │
│  ┌───────────────────────────────────┐      │
│  │  ChatInput                        │      │
│  └───────────────────────────────────┘      │
└─────────────────────────────────────────────┘

底层共用:
  utils/copy-markdown.ts  →  toMarkdown() 序列化引擎
```

## 3. Markdown 序列化引擎 (`utils/copy-markdown.ts`)

### 3.1 接口设计

```typescript
interface CopyOptions {
  includeThinking?: boolean   // default: true
  includeToolCalls?: boolean  // default: true
  modelName?: string          // 在 Assistant 标题后显示模型名
}

// 多条消息 → Markdown（用于多轮复制）
function messagesToMarkdown(
  messages: ChatMessage[],
  options?: CopyOptions,
): string

// 单条消息 → Markdown
function singleMessageToMarkdown(
  msg: ChatMessage,
  options?: CopyOptions,
): string

// 提取单条 assistant 消息的指定段落
function extractThinking(msg: ChatMessage): string
function extractToolCalls(msg: ChatMessage): string
function extractAnswer(msg: ChatMessage): string
```

### 3.2 输出格式规范

**User 消息：**
```markdown
## User

请帮我分析一下这段代码
```

**Assistant 消息（含模型名）：**
```markdown
## Assistant (deepseek-v4-flash)

<details><summary>💭 思考过程</summary>

让我先看看代码结构...
需要关注性能热点...

</details>

<details><summary>🔧 工具调用: read_file</summary>

**参数:**
- `path`: `src/utils/parser.ts`

**结果:**
```
export function parse(input: string) { ... }
```

</details>

根据分析，这段代码有以下性能问题：
1. 每次调用都重新编译正则表达式
2. 数组操作未使用惰性求值
```

**多轮之间：** 用 `\n---\n\n` 分隔。

**格式规则：**
- 每轮以 `## User` / `## Assistant (model)` 为标题
- 思考过程：`<details><summary>💭 思考过程</summary>\n\n{content}\n\n</details>`
- 工具调用：`<details><summary>🔧 工具调用: {name}</summary>\n\n` + 参数列表 + 结果 + `\n\n</details>`
- 工具参数以 Markdown 列表展示：`- \`key\`: \`value\``
- 工具结果用 fenced code block 包裹
- 没有思考 / 工具调用时，对应块不生成

### 3.3 实现要点

解析 `ChatMessage.content` 中的标记：
- `<!--THINK_START-->` ~ `<!--THINK_END-->` → 思考段落
- `<!--TOOL:N-->` → 工具调用位置，从 `msg.toolCalls[N]` 取数据
- 其余文本 → 回答段落

模型名来源优先级：
1. `CopyOptions.modelName`（传入时使用）
2. 从 chat store 的 session 级 `model` 字段读取

## 4. 气泡工具栏组件 (`MessageToolbar.vue`)

### 4.1 Props

```typescript
interface Props {
  message: ChatMessage
  modelName?: string
  hasThinking?: boolean    // 是否存在思考段落
  hasToolCalls?: boolean   // 是否存在工具调用
  hasAnswer?: boolean      // 是否存在文本回答
}
```

### 4.2 按钮

**User 消息：**
| 按钮 | 行为 |
|------|------|
| 📋 复制 | `singleMessageToMarkdown(msg)` → 剪贴板 |

**Assistant 消息：**
| 按钮 | 条件 | 行为 |
|------|------|------|
| 📋 复制全部 | 始终显示 | `singleMessageToMarkdown(msg, {modelName})` |
| 💭 复制思考 | `hasThinking` | `extractThinking(msg)` |
| 🔧 复制工具调用 | `hasToolCalls` | `extractToolCalls(msg)` |
| 📝 复制回答 | `hasAnswer` | `extractAnswer(msg)` |

### 4.3 反馈

点击后按钮文字变为 "已复制 ✓"，1.5 秒后恢复原始文字。使用 `el-message` 或按钮自身状态实现。

### 4.4 响应式

| 屏幕 | 行为 |
|------|------|
| 桌面 (>768px) | 工具栏默认 `opacity: 0.3`，hover 气泡时 `opacity: 1`；按钮紧凑排列 |
| 手机 (≤768px) | 工具栏始终 `opacity: 1`；按钮稍大（min-height 36px, padding 增大）适配触摸 |

按钮使用文字 + 小图标，不使用纯图标（避免歧义）。

## 5. 多轮复制 (`CopyRoundsButton.vue`)

### 5.1 位置

聊天区域右上角，与现有的 header 按钮一排。

### 5.2 交互

点击 `📋 复制对话` 按钮 → 展开 `el-popover` 面板：

```
┌────────────────────────────┐
│  复制最近对话               │
│                            │
│  轮数: [ 3 ]  (1~总轮数)   │
│                            │
│  ☑ 包含思考过程            │
│  ☑ 包含工具调用            │
│                            │
│  [ 复制到剪贴板 ]           │
└────────────────────────────┘
```

### 5.3 "一轮"的定义

从 `messages` 数组中，一轮 = 一个 `user` 消息 + 紧随其后的所有 `assistant` 消息（通常就是一条）。

取最近 N 轮 = 从末尾倒数 N 个 user 消息，每个 user 消息及其后续 assistant 消息一起取出。

### 5.4 响应式

| 屏幕 | 行为 |
|------|------|
| 桌面 | `el-popover` 在按钮下方弹出 |
| 手机 | 改用 `el-drawer` 从底部弹出，输入区域更大更易操作 |

## 6. 新增文件清单

| 文件 | 类型 | 职责 |
|------|------|------|
| `frontend/src/utils/copy-markdown.ts` | 工具函数 | Markdown 序列化引擎 |
| `frontend/src/components/chat/MessageToolbar.vue` | 组件 | 气泡底部工具栏 |
| `frontend/src/components/chat/CopyRoundsButton.vue` | 组件 | 右上角多轮复制按钮+面板 |

**修改文件：**
| 文件 | 变更 |
|------|------|
| `frontend/src/views/ChatView.vue` | 引入 MessageToolbar 和 CopyRoundsButton，传入数据 |

## 7. 测试要点

- 纯文本 user 消息复制
- 含思考 + 工具调用 + 回答的 assistant 消息复制
- 多轮复制（N=1, N=3, N=全部）
- 段落级复制（只复制思考 / 只复制工具调用 / 只复制回答）
- 没有思考过程时对应按钮不显示
- 手机端触摸操作
- 剪贴板写入成功反馈
