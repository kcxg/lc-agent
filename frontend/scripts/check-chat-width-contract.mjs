import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const chatView = readFileSync(join(root, 'src/views/ChatView.vue'), 'utf8')

// 工具卡片拆成多张后，窄屏保护要每张都有：头部可换行、标题可省略、小屏标题独占一行
const toolCards = [
  { name: 'ToolGenericCard.vue', title: '.tg-title', css: readFileSync(join(root, 'src/components/chat/tools/ToolGenericCard.vue'), 'utf8') },
  { name: 'ToolFileCard.vue', title: '.tf-title', css: readFileSync(join(root, 'src/components/chat/tools/ToolFileCard.vue'), 'utf8') },
  { name: 'ToolTerminalCard.vue', title: '.tt-title', css: readFileSync(join(root, 'src/components/chat/tools/ToolTerminalCard.vue'), 'utf8') },
]

const failures = []

function expectIncludes(expected) {
  if (!chatView.includes(expected)) {
    failures.push(`ChatView.vue 缺少: ${expected}`)
  }
}

function expectMatch(pattern, message) {
  if (!pattern.test(chatView)) {
    failures.push(`ChatView.vue ${message}`)
  }
}

function expectNotMatch(pattern, message) {
  if (pattern.test(chatView)) {
    failures.push(`ChatView.vue ${message}`)
  }
}

function expectToolIncludes(card, expected) {
  if (!card.css.includes(expected)) {
    failures.push(`${card.name} 缺少: ${expected}`)
  }
}

function expectToolMatch(card, pattern, message) {
  if (!pattern.test(card.css)) {
    failures.push(`${card.name} ${message}`)
  }
}

expectIncludes('.elx-bubble--start')
expectIncludes('.elx-bubble--end')
expectMatch(/\.elx-bubble__avatar[\s\S]*display:\s*none/, '两侧头像列应隐藏，身份标识收进顶部 header 行')
expectMatch(/\.elx-bubble--start[\s\S]*width:\s*100%\s*!important/, '桌面端 assistant 气泡应占满整行宽度')
expectMatch(/\.elx-bubble--start[\s\S]*align-self:\s*stretch/, 'assistant 气泡缺少整行拉伸对齐')
expectNotMatch(/\.elx-bubble--end\)\s*\{\s*width:\s*fit-content/, '桌面端 user 消息行仍是 fit-content，不能整体贴右')
expectMatch(/\.elx-bubble--end[\s\S]*width:\s*100%\s*!important/, '桌面端 user 消息行应占满宽度，方便整体靠右')
expectMatch(/\.elx-bubble--end[\s\S]*justify-content:\s*flex-end/, '桌面端 user 消息缺少贴右对齐')
expectMatch(/\.elx-bubble--end \.elx-bubble__content-wrapper[\s\S]*width:\s*fit-content/, 'user 气泡内容仍应保持紧凑宽度')
expectIncludes('.elx-bubble--start .elx-bubble__content-wrapper')
expectIncludes('.elx-bubble--start .elx-bubble__content')
expectMatch(/\.elx-bubble--end[\s\S]*align-self:\s*flex-end/, 'user 气泡缺少右侧紧凑对齐')
expectMatch(/@media\s*\(max-width:\s*960px\)[\s\S]*\.elx-bubble--start[\s\S]*width:\s*100%\s*!important[\s\S]*max-width:\s*100%\s*!important/, '移动端 assistant 气泡应占满可用宽度')
for (const card of toolCards) {
  expectToolIncludes(card, 'flex-wrap: wrap')
  expectToolMatch(card, new RegExp(`${card.title.replace('.', '\\.')}[\\s\\S]*min-width:\\s*0`), '工具名缺少 min-width: 0，移动端会把长工具名压成竖排')
  expectToolMatch(card, new RegExp(`${card.title.replace('.', '\\.')}[\\s\\S]*white-space:\\s*nowrap`), '工具名缺少 nowrap，移动端会逐字换行')
  expectToolMatch(card, new RegExp(`${card.title.replace('.', '\\.')}[\\s\\S]*text-overflow:\\s*ellipsis`), '工具名缺少省略策略，移动端会撑破或竖排')
  expectToolMatch(
    card,
    new RegExp(`@media\\s*\\(max-width:\\s*520px\\)[\\s\\S]*${card.title.replace('.', '\\.')}[\\s\\S]*flex-basis:\\s*100%`),
    '移动端工具名应独占一行，避免被状态和统计信息挤窄',
  )
}

if (failures.length > 0) {
  console.error('聊天气泡宽度契约测试失败:')
  for (const failure of failures) {
    console.error(`- ${failure}`)
  }
  process.exit(1)
}

console.log('聊天气泡宽度契约测试通过')
