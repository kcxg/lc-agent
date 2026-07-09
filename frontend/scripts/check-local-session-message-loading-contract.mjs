import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const chatStore = readFileSync(resolve(root, 'src/stores/chat.ts'), 'utf8')

const failures = []

function expectIncludes(label, source, snippet) {
  if (!source.includes(snippet)) {
    failures.push(`${label} 缺少片段: ${snippet}`)
  }
}

expectIncludes(
  'chat.ts',
  chatStore,
  'const sessionsStore = useSessionsStore()'
)
expectIncludes(
  'chat.ts',
  chatStore,
  'if (sessionsStore.isLocalSession(sessionId)) {'
)
expectIncludes(
  'chat.ts',
  chatStore,
  'messages.value = []'
)
expectIncludes(
  'chat.ts',
  chatStore,
  'return'
)

if (failures.length) {
  console.error('check-local-session-message-loading-contract failed:')
  for (const failure of failures) {
    console.error(`- ${failure}`)
  }
  process.exit(1)
}

console.log('check-local-session-message-loading-contract passed')
