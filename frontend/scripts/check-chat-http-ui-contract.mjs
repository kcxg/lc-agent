import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const read = (relativePath) => readFileSync(join(root, relativePath), 'utf8')

const toolbar = read('src/components/chat/MessageToolbar.vue')
const traceBlock = read('src/components/chat/HttpTraceBlock.vue')
const chatView = read('src/views/ChatView.vue')
const failures = []

function expectIncludes(name, content, expected) {
  if (!content.includes(expected)) failures.push(`${name} 缺少: ${expected}`)
}

// HttpTraceBlock.vue
expectIncludes('HttpTraceBlock.vue', traceBlock, 'props')
expectIncludes('HttpTraceBlock.vue', traceBlock, 'trace: HttpTrace')
expectIncludes('HttpTraceBlock.vue', traceBlock, 'HTTP 交互 #')
expectIncludes('HttpTraceBlock.vue', traceBlock, 'trace.sequence')
expectIncludes('HttpTraceBlock.vue', traceBlock, 'trace.request.method')
expectIncludes('HttpTraceBlock.vue', traceBlock, 'Request Headers')
expectIncludes('HttpTraceBlock.vue', traceBlock, 'Request Body')
expectIncludes('HttpTraceBlock.vue', traceBlock, 'Response Headers')
expectIncludes('HttpTraceBlock.vue', traceBlock, 'Response Body')

// MessageToolbar.vue — must NOT have HTTP buttons
if (toolbar.includes('请求 HTTP')) failures.push('MessageToolbar.vue 不应再包含 请求 HTTP 按钮')
if (toolbar.includes('响应 HTTP')) failures.push('MessageToolbar.vue 不应再包含 响应 HTTP 按钮')
if (toolbar.includes('HttpTracePopover')) failures.push('MessageToolbar.vue 不应再引入 HttpTracePopover')

// ChatView.vue — HTTP 交互以结构化 httpTraces 经 HttpTracesGroup 独立块渲染（内部仍用 HttpTraceBlock）
expectIncludes('ChatView.vue', chatView, 'import HttpTracesGroup')
expectIncludes('ChatView.vue', chatView, '<HttpTracesGroup')
expectIncludes('ChatView.vue', chatView, ':traces="item.httpTraces"')
expectIncludes('ChatView.vue', chatView, 'httpTracesCount')

if (failures.length > 0) {
  console.error('聊天 HTTP UI 契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('聊天 HTTP UI 契约测试通过')
