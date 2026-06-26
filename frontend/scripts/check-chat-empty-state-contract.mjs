import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const chatView = readFileSync(join(root, 'src/views/ChatView.vue'), 'utf8')

const failures = []

function expectIncludes(expected) {
  if (!chatView.includes(expected)) {
    failures.push(`ChatView.vue 缺少: ${expected}`)
  }
}

function expectNotIncludes(unexpected) {
  if (chatView.includes(unexpected)) {
    failures.push(`ChatView.vue 不应再包含: ${unexpected}`)
  }
}

function expectMatch(pattern, message) {
  if (!pattern.test(chatView)) {
    failures.push(`ChatView.vue ${message}`)
  }
}

expectIncludes('class="chat-empty-state"')
expectIncludes('class="chat-empty-accent"')
expectIncludes('title="开始新的对话"')
expectIncludes('description="有什么想法、问题或任务，都可以直接告诉我。"')
expectNotIncludes('Start a conversation')
expectNotIncludes('Ask me anything')
expectMatch(/\.chat-empty-state\s*\{[\s\S]*display:\s*grid[\s\S]*place-items:\s*center/, '空态应有稳定居中布局')
expectMatch(/\.messages-container :deep\(\.elx-welcome\)\s*\{[\s\S]*border-radius:\s*8px/, '欢迎卡片圆角应控制在 8px')
expectMatch(/\.messages-container :deep\(\.elx-welcome__title\)\s*\{[\s\S]*font-size:\s*24px/, '空态标题应有明确层级')
expectMatch(/@media\s*\(max-width:\s*520px\)[\s\S]*\.chat-empty-state[\s\S]*padding:\s*20px 10px/, '手机端空态应收紧留白')

if (failures.length > 0) {
  console.error('聊天空态契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('聊天空态契约测试通过')
