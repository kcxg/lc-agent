import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const domSearch = readFileSync(join(root, 'src/composables/useDomSearch.ts'), 'utf8')
const chatView = readFileSync(join(root, 'src/views/ChatView.vue'), 'utf8')

const failures = []

function expectMatch(name, content, pattern, message) {
  if (!pattern.test(content)) failures.push(`${name} ${message}`)
}

function expectNotMatch(name, content, pattern, message) {
  if (pattern.test(content)) failures.push(`${name} ${message}`)
}

// 1) 命中跳转必须即时滚动：smooth 是异步的，连点 ↑/↓ 互相打断，视图追不上高亮项
expectMatch(
  'useDomSearch.ts',
  domSearch,
  /scrollIntoView\(\{[^}]*behavior:\s*'auto'[^}]*\}\)/,
  "命中跳转必须用 behavior: 'auto' 即时滚动（连点 smooth 会互相打断，视图不动）",
)
expectNotMatch(
  'useDomSearch.ts',
  domSearch,
  /scrollIntoView\(\{[^}]*behavior:\s*'smooth'/,
  "命中跳转不允许再用 behavior: 'smooth'",
)

// 2) 拆掉高亮后必须合并命中处相邻文本节点，否则逐节点匹配再也匹配不到被切开的整词
expectMatch(
  'useDomSearch.ts',
  domSearch,
  /function clearHits\([^)]*\)\s*\{[\s\S]*?appendData/,
  'clearHits 缺少相邻文本节点合并（appendData），还原后被切开的整词会漏匹配',
)

// 3) 聊天区滚动容器必须是 BubbleList 内部列表；外层 .elx-bubble-list 不滚动
expectMatch(
  'ChatView.vue',
  chatView,
  /function getMessagesScroller\(\)\s*\{[^}]*querySelector\(['"]\.elx-bubble-list__list['"]\)/,
  'getMessagesScroller 必须取 .elx-bubble-list__list（外层 .elx-bubble-list 不滚动）',
)
expectNotMatch(
  'ChatView.vue',
  chatView,
  /function getMessagesScroller\(\)\s*\{[^}]*querySelector\(['"]\.elx-bubble-list['"]\)/,
  'getMessagesScroller 仍取外层 .elx-bubble-list，回到底部/滚动位置记忆都会失效',
)

if (failures.length > 0) {
  console.error('聊天区查找契约测试失败:')
  for (const failure of failures) {
    console.error(`- ${failure}`)
  }
  process.exit(1)
}

console.log('聊天区查找契约测试通过')
