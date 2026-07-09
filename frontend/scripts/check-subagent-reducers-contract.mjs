import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const read = (relativePath) => readFileSync(join(root, relativePath), 'utf8')

const chatStore = read('src/stores/chat.ts')
const failures = []

function expectIncludes(name, content, expected) {
  if (!content.includes(expected)) failures.push(`${name} 缺少: ${expected}`)
}

function expectMatches(name, content, pattern, message) {
  if (!pattern.test(content)) failures.push(`${name} ${message}`)
}

function expectNotMatches(name, content, pattern, message) {
  if (pattern.test(content)) failures.push(`${name} ${message}`)
}

function sliceBetween(content, start, end) {
  const startIndex = content.indexOf(start)
  const endIndex = content.indexOf(end)
  if (startIndex === -1 || endIndex === -1 || endIndex <= startIndex) return ''
  return content.slice(startIndex, endIndex)
}

const reducers = [
  ['subagent_start', 'applySubAgentStart'],
  ['subagent_token', 'applySubAgentToken'],
  ['subagent_thinking', 'applySubAgentThinking'],
  ['subagent_tool_call', 'applySubAgentToolCall'],
  ['subagent_tool_result', 'applySubAgentToolResult'],
  ['subagent_done', 'applySubAgentDone'],
]

expectIncludes('chat.ts', chatStore, 'export interface SubAgentReducerResult')
expectIncludes('chat.ts', chatStore, 'changed: boolean')
expectIncludes('chat.ts', chatStore, 'shouldRefresh: boolean')
expectIncludes('chat.ts', chatStore, 'const SUBAGENT_UNCHANGED: SubAgentReducerResult = { changed: false, shouldRefresh: false }')

const sseClient = read('src/api/sse-client.ts')
const subAgentCard = read('src/components/chat/SubAgentCard.vue')
const requiredSnippets = [
  'subagent_start',
  'is_subagent',
  'sub_session_id',
  'tool_call_id',
]

for (const snippet of requiredSnippets) {
  expectIncludes('chat.ts', chatStore, snippet)
}

for (const snippet of ['subagent_type', 'query', 'description']) {
  expectIncludes('sse-client.ts', sseClient, snippet)
}

const taskModeSubagentStart = {
  type: 'subagent_start',
  name: 'funboost教程查询智能体',
  subagent_type: 'funboost教程查询智能体',
  tool_call_id: 'task123',
  query: '查询定时任务',
}

expectIncludes('chat.ts', chatStore, 'name: msg.name || msg.subagent_type ||')
expectIncludes('chat.ts', chatStore, 'query: msg.query || msg.description ||')
expectMatches(
  'SubAgentCard.vue',
  subAgentCard,
  /\{\{\s*entry\.name\s*\}\}/,
  '必须使用 subagent_start 提供的 display name 渲染标题',
)
expectNotMatches(
  'SubAgentCard.vue',
  subAgentCard,
  /toolCall\.name|args\?\.name|args\?\.subagent_type/,
  '不得从原始 task tool call 或 args 派生子 Agent 标题',
)
if (taskModeSubagentStart.name !== 'funboost教程查询智能体' || taskModeSubagentStart.tool_call_id !== 'task123') {
  failures.push('task-mode subagent_start fixture 无效')
}

for (const [eventName, reducerName] of reducers) {
  expectIncludes('chat.ts', chatStore, `export function ${reducerName}(`)
  expectIncludes('chat.ts', chatStore, `client.on('${eventName}', (msg: SseMessage) => {`)
  expectIncludes('chat.ts', chatStore, `const result = applySubAgentEventToMessages(messages.value, msg, ${reducerName}, threadId.value)`)
  expectMatches(
    'chat.ts',
    chatStore,
    new RegExp(`const result = applySubAgentEventToMessages\\(messages\\.value, msg, ${reducerName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}, threadId\\.value\\)[\\s\\S]*?if \\(result\\.shouldRefresh\\) \\{\\s*messages\\.value = \\[\\.\\.\\.messages\\.value\\]\\s*\\}`, 'm'),
    `必须在 ${eventName} 处理器中按 tool_call_id 定位消息后再按 shouldRefresh 刷新 messages.value`,
  )
}

expectIncludes('chat.ts', chatStore, 'export function applySubAgentEventToMessages(')
expectIncludes('chat.ts', chatStore, 'findSubAgentMessage(messages, toolCallId, msg.type === \'subagent_start\')')
expectIncludes('chat.ts', chatStore, 'let lastAssistant: ChatMessage | undefined')
expectIncludes('chat.ts', chatStore, 'if (allowLastAssistantFallback && message.role === \'assistant\' && !lastAssistant)')
expectNotMatches(
  'chat.ts',
  chatStore,
  /applySubAgent(?:Start|Token|Thinking|ToolCall|ToolResult|Done)\(messages\.value\[messages\.value\.length - 1\]/,
  'subagent 事件处理器不得只更新最后一条 assistant 消息',
)

expectIncludes('chat.ts', chatStore, 'const toolCallId = msg.tool_call_id || msg.run_id || \'\'')
expectIncludes('chat.ts', chatStore, 'const subSessionId = msg.sub_session_id')
expectIncludes('chat.ts', chatStore, '|| (parentThreadId ? `${parentThreadId}--sa--${toolCallId}` : \'\')')
expectIncludes('chat.ts', chatStore, 'const existing = message.subAgents?.[toolCallId]')
expectIncludes('chat.ts', chatStore, 'tokenPreview: existing?.tokenPreview || \'\'')
expectIncludes('chat.ts', chatStore, 'innerToolCalls: existing?.innerToolCalls || []')
expectIncludes('chat.ts', chatStore, 'httpTraces: existing?.httpTraces')
expectIncludes('chat.ts', chatStore, 'tc.is_subagent = true')
expectIncludes('chat.ts', chatStore, 'message.toolCalls = message.toolCalls || []')
expectIncludes('chat.ts', chatStore, 'message.toolCalls.push(tc)')
expectIncludes('chat.ts', chatStore, "status: 'running'")
expectIncludes('chat.ts', chatStore, 'tc.sub_session_id = subSessionId')
expectIncludes('chat.ts', chatStore, 'return { changed: true, shouldRefresh: newCount % 3 === 0 }')
expectIncludes('chat.ts', chatStore, 'return { changed: true, shouldRefresh: newThinkCount % 5 === 0 }')
expectIncludes('chat.ts', chatStore, 'innerToolCalls: [...sa.innerToolCalls, {')
expectIncludes('chat.ts', chatStore, 'const idx = [...updatedCalls].reverse().findIndex(')
expectIncludes('chat.ts', chatStore, "const resultStatus = msg.status === 'error' || msg.is_error ? 'error' : 'done'")
expectIncludes('chat.ts', chatStore, 'status: resultStatus')
expectIncludes('chat.ts', chatStore, "status: 'running' | 'done' | 'error' | 'cancelled' | 'interrupted'")
expectIncludes('chat.ts', chatStore, "status === 'cancelled' || status === 'interrupted'")
expectIncludes('chat.ts', chatStore, 'normalizeSubAgentDoneStatus(msg.status)')
expectIncludes('chat.ts', chatStore, 'const rawHttpTraces = msg.http_traces')
expectIncludes('chat.ts', chatStore, 'httpTraces: saHttpTraces')
expectIncludes('chat.ts', chatStore, 'tc.result = sa?.tokens || msg.result_preview || \'\'')

const subAgentRegion = sliceBetween(
  chatStore,
  'export function applySubAgentStart(',
  "client.on('interrupt', (msg: SseMessage) => {",
)
if (!subAgentRegion) {
  failures.push('chat.ts 无法定位 subagent reducer/helper 与 callback 区域')
} else {
  expectNotMatches(
    'chat.ts',
    subAgentRegion,
    /\(msg as any\)\.(tool_call_id|sub_session_id|query|http_traces|status|result_preview|duration|is_subagent)/,
    'subagent reducer/helper 区域不得对 SseMessage 已声明字段使用 (msg as any) 强转',
  )
}

if (failures.length > 0) {
  console.error('子 Agent reducer 契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('子 Agent reducer 契约测试通过')
