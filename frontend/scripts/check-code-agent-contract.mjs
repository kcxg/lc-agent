import fs from 'node:fs'
import path from 'node:path'

const root = process.cwd()
function read(rel) {
  return fs.readFileSync(path.join(root, rel), 'utf8')
}
function assertContains(file, needle, message) {
  const content = read(file)
  if (!content.includes(needle)) {
    console.error(`[code-agent-contract] ${message}`)
    console.error(`Missing in ${file}: ${needle}`)
    process.exit(1)
  }
}
function assertNotContains(file, needle, message) {
  const content = read(file)
  if (content.includes(needle)) {
    console.error(`[code-agent-contract] ${message}`)
    console.error(`Unexpected in ${file}: ${needle}`)
    process.exit(1)
  }
}

assertContains(
  'src/stores/agents.ts',
  'const isCodeAgent = computed(() => currentAgent.value?.source === \'code\')',
  'agents store must expose current code-agent state',
)
assertContains(
  'src/stores/agents.ts',
  'isCodeAgent,',
  'agents store must return isCodeAgent',
)
assertContains(
  'src/stores/tools.ts',
  "if (agentsStore.currentAgent?.source === 'code') {",
  'tools store must special-case code agents when syncing model',
)
assertContains(
  'src/stores/tools.ts',
  "currentModel.value = ''",
  'tools store must clear UI model for code agents',
)
assertNotContains(
  'src/stores/tools.ts',
  'currentModel.value = defaultModel\n      return',
  'tools store must not blindly set default_model=custom as runtime model',
)
console.log('[code-agent-contract] store checks passed')
