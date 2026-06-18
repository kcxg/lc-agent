import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const chatStore = readFileSync(join(root, 'src/stores/chat.ts'), 'utf8')
const failures = []

function expectIncludes(expected) {
  if (!chatStore.includes(expected)) failures.push(`chat.ts 缺少: ${expected}`)
}

expectIncludes('function normalizeHistoryMessage')
expectIncludes('function normalizeHistoryMessages')
expectIncludes('function ensureToolMarkers')
expectIncludes('tool_calls')
expectIncludes('runId: tc.runId || tc.run_id || tc.id')
expectIncludes('const usage = normalizeHistoryUsage(msg.usage)')
expectIncludes('<!--TOOL:${idx}-->')

if (failures.length > 0) {
  console.error('聊天历史恢复契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('聊天历史恢复契约测试通过')
