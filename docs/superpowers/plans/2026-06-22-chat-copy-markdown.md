# Chat Copy-to-Markdown 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为聊天界面添加多层级 Markdown 复制功能（单条消息 / 段落级 / 多轮对话）。

**Architecture:** 底层是一个纯函数序列化引擎 `copy-markdown.ts`，负责将 `ChatMessage` 数据结构转为 Markdown 字符串。上层两个 Vue 组件 `MessageToolbar` 和 `CopyRoundsButton` 提供 UI 交互，调用引擎完成复制。

**Tech Stack:** Vue 3 + TypeScript, Element Plus (`el-popover`, `el-input-number`, `el-checkbox`, `el-button`), Clipboard API

**Spec:** `docs/superpowers/specs/2026-06-22-chat-copy-markdown-design.md`

---

## 文件清单

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| 新建 | `frontend/src/utils/copy-markdown.ts` | Markdown 序列化引擎（纯函数） |
| 新建 | `frontend/src/components/chat/MessageToolbar.vue` | 气泡底部工具栏组件 |
| 新建 | `frontend/src/components/chat/CopyRoundsButton.vue` | 右上角多轮复制按钮+面板 |
| 修改 | `frontend/src/views/ChatView.vue` | 集成上述两个组件 |
| 新建 | `frontend/scripts/check-copy-markdown-contract.mjs` | 契约测试脚本 |

---

### Task 1: Markdown 序列化引擎

**Files:**
- Create: `frontend/src/utils/copy-markdown.ts`
- Create: `frontend/scripts/check-copy-markdown-contract.mjs`

- [ ] **Step 1: 创建契约测试脚本**

契约测试检查 `copy-markdown.ts` 导出了所有必需的函数。在 `frontend/scripts/check-copy-markdown-contract.mjs` 中：

```javascript
import { readFileSync } from 'fs'
const src = readFileSync('src/utils/copy-markdown.ts', 'utf-8')

const required = [
  'messagesToMarkdown',
  'singleMessageToMarkdown',
  'extractThinking',
  'extractToolCalls',
  'extractAnswer',
]

const missing = required.filter(fn => !src.includes(`export function ${fn}`))
if (missing.length) {
  console.error('Missing exports:', missing)
  process.exit(1)
}

// 检查 CopyOptions 接口
if (!src.includes('interface CopyOptions')) {
  console.error('Missing CopyOptions interface')
  process.exit(1)
}

console.log('copy-markdown contract OK')
```

- [ ] **Step 2: 运行契约测试确认失败**

```bash
cd frontend && node scripts/check-copy-markdown-contract.mjs
```

预期：失败（文件不存在）。

- [ ] **Step 3: 实现 copy-markdown.ts**

创建 `frontend/src/utils/copy-markdown.ts`：

```typescript
export interface CopyOptions {
  includeThinking?: boolean
  includeToolCalls?: boolean
  modelName?: string
}

interface ToolCallLike {
  name: string
  args?: Record<string, any>
  result?: string
  status?: string
  duration?: number
  resultLength?: number
}

interface MessageLike {
  role: 'user' | 'assistant' | 'tool'
  content: string
  toolCalls?: ToolCallLike[]
}

const THINK_START = '<!--THINK_START-->'
const THINK_END = '<!--THINK_END-->'
const TOOL_RE = /<!--TOOL:(\d+)-->/g

interface Segment {
  type: 'text' | 'thinking' | 'tool'
  content: string
  toolIndex?: number
}

function parseSegments(content: string): Segment[] {
  const segments: Segment[] = []
  let remaining = content
  let inThinking = false

  while (remaining.length > 0) {
    if (!inThinking) {
      const thinkStart = remaining.indexOf(THINK_START)
      const toolMatch = TOOL_RE.exec(remaining)
      TOOL_RE.lastIndex = 0

      const nextThink = thinkStart >= 0 ? thinkStart : Infinity
      const nextTool = toolMatch ? toolMatch.index : Infinity

      if (nextThink === Infinity && nextTool === Infinity) {
        const trimmed = remaining.trim()
        if (trimmed) segments.push({ type: 'text', content: trimmed })
        break
      }

      const nextMarker = Math.min(nextThink, nextTool)
      const before = remaining.slice(0, nextMarker).trim()
      if (before) segments.push({ type: 'text', content: before })

      if (nextThink < nextTool) {
        remaining = remaining.slice(thinkStart + THINK_START.length)
        inThinking = true
      } else {
        const idx = parseInt(toolMatch![1], 10)
        segments.push({ type: 'tool', content: '', toolIndex: idx })
        remaining = remaining.slice(toolMatch!.index + toolMatch![0].length)
      }
    } else {
      const thinkEnd = remaining.indexOf(THINK_END)
      if (thinkEnd >= 0) {
        const thinking = remaining.slice(0, thinkEnd).trim()
        if (thinking) segments.push({ type: 'thinking', content: thinking })
        remaining = remaining.slice(thinkEnd + THINK_END.length)
        inThinking = false
      } else {
        const thinking = remaining.trim()
        if (thinking) segments.push({ type: 'thinking', content: thinking })
        break
      }
    }
  }
  return segments
}

function toolCallToMarkdown(tc: ToolCallLike): string {
  const lines: string[] = []
  const meta = tc.duration ? ` (${(tc.duration / 1000).toFixed(1)}s)` : ''
  lines.push(`<details><summary>🔧 工具调用: ${tc.name}${meta}</summary>`)
  lines.push('')

  if (tc.args && Object.keys(tc.args).length > 0) {
    lines.push('**参数:**')
    for (const [k, v] of Object.entries(tc.args)) {
      const val = typeof v === 'string' ? v : JSON.stringify(v)
      const display = val.length > 200 ? val.slice(0, 200) + '...' : val
      lines.push(`- \`${k}\`: \`${display}\``)
    }
    lines.push('')
  }

  if (tc.result) {
    lines.push('**结果:**')
    lines.push('```')
    lines.push(tc.result)
    lines.push('```')
    lines.push('')
  }

  lines.push('</details>')
  return lines.join('\n')
}

export function singleMessageToMarkdown(
  msg: MessageLike,
  options?: CopyOptions,
): string {
  const opts = { includeThinking: true, includeToolCalls: true, ...options }

  if (msg.role === 'user') {
    return `## User\n\n${msg.content.trim()}`
  }

  const modelSuffix = opts.modelName ? ` (${opts.modelName})` : ''
  const lines: string[] = [`## Assistant${modelSuffix}`, '']
  const segments = parseSegments(msg.content)

  for (const seg of segments) {
    if (seg.type === 'thinking' && opts.includeThinking) {
      lines.push('<details><summary>💭 思考过程</summary>')
      lines.push('')
      lines.push(seg.content)
      lines.push('')
      lines.push('</details>')
      lines.push('')
    } else if (seg.type === 'tool' && opts.includeToolCalls) {
      const tc = msg.toolCalls?.[seg.toolIndex!]
      if (tc) {
        lines.push(toolCallToMarkdown(tc))
        lines.push('')
      }
    } else if (seg.type === 'text') {
      lines.push(seg.content)
      lines.push('')
    }
  }

  return lines.join('\n').trimEnd()
}

export function messagesToMarkdown(
  messages: MessageLike[],
  options?: CopyOptions,
): string {
  return messages
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .map(m => singleMessageToMarkdown(m, options))
    .join('\n\n---\n\n')
}

export function extractThinking(msg: MessageLike): string {
  return parseSegments(msg.content)
    .filter(s => s.type === 'thinking')
    .map(s => s.content)
    .join('\n\n')
}

export function extractToolCalls(msg: MessageLike): string {
  const segments = parseSegments(msg.content)
  return segments
    .filter(s => s.type === 'tool')
    .map(s => {
      const tc = msg.toolCalls?.[s.toolIndex!]
      return tc ? toolCallToMarkdown(tc) : ''
    })
    .filter(Boolean)
    .join('\n\n')
}

export function extractAnswer(msg: MessageLike): string {
  return parseSegments(msg.content)
    .filter(s => s.type === 'text')
    .map(s => s.content)
    .join('\n\n')
}

export function getRounds(messages: MessageLike[]): MessageLike[][] {
  const rounds: MessageLike[][] = []
  let current: MessageLike[] = []

  for (const msg of messages) {
    if (msg.role === 'user') {
      if (current.length > 0) rounds.push(current)
      current = [msg]
    } else if (msg.role === 'assistant') {
      current.push(msg)
    }
  }
  if (current.length > 0) rounds.push(current)
  return rounds
}

export function copyRecentRounds(
  messages: MessageLike[],
  n: number,
  options?: CopyOptions,
): string {
  const rounds = getRounds(messages)
  const recent = rounds.slice(-n)
  return recent
    .map(round => round.map(m => singleMessageToMarkdown(m, options)).join('\n\n'))
    .join('\n\n---\n\n')
}
```

- [ ] **Step 4: 运行契约测试确认通过**

```bash
cd frontend && node scripts/check-copy-markdown-contract.mjs
```

预期：`copy-markdown contract OK`

- [ ] **Step 5: 提交**

```bash
git add frontend/src/utils/copy-markdown.ts frontend/scripts/check-copy-markdown-contract.mjs
git commit -m "feat: add Markdown serialization engine for chat copy"
```

---

### Task 2: 剪贴板工具函数

**Files:**
- Modify: `frontend/src/utils/copy-markdown.ts`（在底部追加）

- [ ] **Step 1: 追加 copyToClipboard 函数**

在 `copy-markdown.ts` 文件底部追加：

```typescript
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(textarea)
    return ok
  }
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/utils/copy-markdown.ts
git commit -m "feat: add clipboard helper with fallback"
```

---

### Task 3: MessageToolbar 组件

**Files:**
- Create: `frontend/src/components/chat/MessageToolbar.vue`

- [ ] **Step 1: 创建 MessageToolbar.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import {
  singleMessageToMarkdown,
  extractThinking,
  extractToolCalls,
  extractAnswer,
  copyToClipboard,
} from '@/utils/copy-markdown'
import type { ChatMessage } from '@/stores/chat'

const props = defineProps<{
  message: ChatMessage
  modelName?: string
  hasThinking?: boolean
  hasToolCalls?: boolean
  hasAnswer?: boolean
}>()

const copiedKey = ref<string | null>(null)

async function doCopy(key: string, text: string) {
  if (!text) return
  const ok = await copyToClipboard(text)
  if (ok) {
    copiedKey.value = key
    setTimeout(() => (copiedKey.value = null), 1500)
  }
}

function copyAll() {
  doCopy('all', singleMessageToMarkdown(props.message, { modelName: props.modelName }))
}
function copyThinking() {
  doCopy('thinking', extractThinking(props.message))
}
function copyTools() {
  doCopy('tools', extractToolCalls(props.message))
}
function copyAnswer() {
  doCopy('answer', extractAnswer(props.message))
}
function copyUser() {
  doCopy('all', props.message.content)
}
</script>

<template>
  <div class="message-toolbar">
    <template v-if="message.role === 'user'">
      <button class="tb-btn" @click="copyUser">
        {{ copiedKey === 'all' ? '已复制 ✓' : '📋 复制' }}
      </button>
    </template>
    <template v-else>
      <button class="tb-btn" @click="copyAll">
        {{ copiedKey === 'all' ? '已复制 ✓' : '📋 复制全部' }}
      </button>
      <button v-if="hasThinking" class="tb-btn" @click="copyThinking">
        {{ copiedKey === 'thinking' ? '已复制 ✓' : '💭 复制思考' }}
      </button>
      <button v-if="hasToolCalls" class="tb-btn" @click="copyTools">
        {{ copiedKey === 'tools' ? '已复制 ✓' : '🔧 复制工具' }}
      </button>
      <button v-if="hasAnswer" class="tb-btn" @click="copyAnswer">
        {{ copiedKey === 'answer' ? '已复制 ✓' : '📝 复制回答' }}
      </button>
    </template>
  </div>
</template>

<style scoped>
.message-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
  opacity: 0.35;
  transition: opacity 0.2s;
}

/* 桌面端 hover 显示 */
:deep(.bubble-item):hover .message-toolbar,
.message-toolbar:hover {
  opacity: 1;
}

/* 手机端始终可见 */
@media (max-width: 768px) {
  .message-toolbar {
    opacity: 1;
  }
}

.tb-btn {
  background: var(--el-fill-color-light, #f5f7fa);
  border: 1px solid var(--el-border-color-lighter, #e4e7ed);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
  color: var(--el-text-color-secondary, #909399);
  transition: all 0.15s;
}
.tb-btn:hover {
  background: var(--el-color-primary-light-9, #ecf5ff);
  border-color: var(--el-color-primary-light-7, #c6e2ff);
  color: var(--el-color-primary, #409eff);
}
.tb-btn:active {
  transform: scale(0.96);
}

@media (max-width: 768px) {
  .tb-btn {
    padding: 6px 12px;
    font-size: 13px;
    min-height: 36px;
  }
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/chat/MessageToolbar.vue
git commit -m "feat: add MessageToolbar component for per-bubble copy"
```

---

### Task 4: CopyRoundsButton 组件

**Files:**
- Create: `frontend/src/components/chat/CopyRoundsButton.vue`

- [ ] **Step 1: 创建 CopyRoundsButton.vue**

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { copyRecentRounds, getRounds, copyToClipboard } from '@/utils/copy-markdown'
import type { ChatMessage } from '@/stores/chat'

const props = defineProps<{
  messages: ChatMessage[]
  modelName?: string
}>()

const visible = ref(false)
const roundCount = ref(3)
const includeThinking = ref(true)
const includeToolCalls = ref(true)
const copied = ref(false)

const totalRounds = computed(() => getRounds(props.messages).length)
const maxRounds = computed(() => Math.max(totalRounds.value, 1))

async function doCopy() {
  const md = copyRecentRounds(props.messages, roundCount.value, {
    includeThinking: includeThinking.value,
    includeToolCalls: includeToolCalls.value,
    modelName: props.modelName,
  })
  const ok = await copyToClipboard(md)
  if (ok) {
    copied.value = true
    setTimeout(() => {
      copied.value = false
      visible.value = false
    }, 1200)
  }
}
</script>

<template>
  <el-popover
    v-model:visible="visible"
    trigger="click"
    :width="260"
    placement="bottom-end"
  >
    <template #reference>
      <el-button size="small" :icon="undefined" text>
        📋 复制对话
      </el-button>
    </template>

    <div class="copy-rounds-panel">
      <div class="panel-title">复制最近对话</div>

      <div class="panel-row">
        <span>轮数:</span>
        <el-input-number
          v-model="roundCount"
          :min="1"
          :max="maxRounds"
          size="small"
          controls-position="right"
          style="width: 100px"
        />
        <span class="hint">/ {{ totalRounds }}</span>
      </div>

      <div class="panel-row">
        <el-checkbox v-model="includeThinking">包含思考过程</el-checkbox>
      </div>
      <div class="panel-row">
        <el-checkbox v-model="includeToolCalls">包含工具调用</el-checkbox>
      </div>

      <el-button
        type="primary"
        size="small"
        style="width: 100%; margin-top: 8px"
        @click="doCopy"
      >
        {{ copied ? '已复制 ✓' : '复制到剪贴板' }}
      </el-button>
    </div>
  </el-popover>
</template>

<style scoped>
.copy-rounds-panel {
  padding: 4px 0;
}
.panel-title {
  font-weight: 600;
  margin-bottom: 10px;
  font-size: 14px;
}
.panel-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.hint {
  color: var(--el-text-color-placeholder, #a8abb2);
  font-size: 12px;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/chat/CopyRoundsButton.vue
git commit -m "feat: add CopyRoundsButton for multi-round copy"
```

---

### Task 5: 集成到 ChatView

**Files:**
- Modify: `frontend/src/views/ChatView.vue`

- [ ] **Step 1: 分析 ChatView 当前结构**

阅读 `frontend/src/views/ChatView.vue`，定位：
1. `BubbleList` 的 `#content` slot 模板（消息渲染区域）
2. 聊天区域顶部 header 位置
3. `parseSegments` 函数和 `bubbleList` computed

- [ ] **Step 2: 导入新组件**

在 `ChatView.vue` 的 `<script setup>` 中添加导入：

```typescript
import MessageToolbar from '@/components/chat/MessageToolbar.vue'
import CopyRoundsButton from '@/components/chat/CopyRoundsButton.vue'
```

- [ ] **Step 3: 计算辅助属性**

在 `bubbleList` computed 中，为每个 assistant 消息计算 `hasThinking`、`hasToolCalls`、`hasAnswer`：

对每个 assistant 类型的 item，在映射时添加三个布尔字段：
- `hasThinking`：segments 中存在 `type === 'thinking'` 的段
- `hasToolCalls`：segments 中存在 `type === 'tool'` 的段
- `hasAnswer`：segments 中存在 `type === 'text'` 的段

- [ ] **Step 4: 在 #content slot 中插入 MessageToolbar**

在每个消息气泡的内容渲染之后（`#content` slot 末尾），添加：

```html
<MessageToolbar
  :message="originalMsg"
  :model-name="sessionModel"
  :has-thinking="item.hasThinking"
  :has-tool-calls="item.hasToolCalls"
  :has-answer="item.hasAnswer"
/>
```

其中 `originalMsg` 是从 store 的 `messages` 数组中通过 `item.messageId` 找到的原始 `ChatMessage` 对象，`sessionModel` 是当前 session 的 model 名称。

- [ ] **Step 5: 在聊天区域顶部添加 CopyRoundsButton**

在 ChatView 模板中，聊天区域上方合适的位置添加：

```html
<CopyRoundsButton
  :messages="messages"
  :model-name="sessionModel"
/>
```

- [ ] **Step 6: 构建验证**

```bash
cd frontend && npm run build
```

预期：构建成功，无 TypeScript 错误。

- [ ] **Step 7: 提交**

```bash
git add frontend/src/views/ChatView.vue
git commit -m "feat: integrate copy-markdown components into ChatView"
```

---

### Task 6: 手动验证与微调

- [ ] **Step 1: 启动服务器**

```bash
d:\codes\lc-agent\.agents\skills\restart-bfzs\scripts\restart.ps1
```

- [ ] **Step 2: 浏览器测试**

打开 http://127.0.0.1:8001，进入一个有对话的 session：

1. hover assistant 消息 → 确认工具栏出现
2. 点击 "复制全部" → 粘贴到文本编辑器验证 Markdown 格式
3. 点击 "复制思考" / "复制工具" / "复制回答" → 分别验证
4. 点击 user 消息的 "复制" → 验证
5. 点击右上角 "复制对话" → 设置轮数 → 复制 → 验证多轮 Markdown
6. 调整浏览器为移动端宽度 → 确认工具栏始终可见、按钮可触摸

- [ ] **Step 3: 修复发现的问题**

根据测试结果修复样式或逻辑问题。

- [ ] **Step 4: 最终提交**

```bash
git add -A
git commit -m "feat: complete chat copy-to-markdown feature"
```
