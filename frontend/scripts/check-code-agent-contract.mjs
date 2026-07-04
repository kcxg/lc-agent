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
  "src/stores/agents.ts",
  "const isCodeAgent = computed(() => currentAgent.value?.source === 'code')",
  "agents store must expose current code-agent state",
)
assertContains(
  "src/stores/agents.ts",
  "isCodeAgent,",
  "agents store must return isCodeAgent",
)
assertContains(
  "src/stores/tools.ts",
  "if (agentsStore.currentAgent?.source === 'code') {",
  "tools store must special-case code agents when syncing model",
)
assertContains(
  "src/stores/tools.ts",
  "currentModel.value = ''",
  "tools store must clear UI model for code agents",
)
assertNotContains(
  "src/stores/tools.ts",
  "currentModel.value = defaultModel\n      return",
  "tools store must not blindly set default_model=custom as runtime model",
)
assertContains(
  "src/components/layout/RightPanel.vue",
  "v-if=\"!agentsStore.isCodeAgent\"",
  "right panel must hide fixed model/summarization controls for code agents",
)
assertContains(
  "src/components/layout/RightPanel.vue",
  "v-if=\"agentsStore.isCodeAgent\"",
  "right panel must render a code-agent explanation branch",
)
assertContains(
  "src/components/layout/RightPanel.vue",
  "\u4ee3\u7801\u667a\u80fd\u4f53",
  "right panel must label code-agent informational card",
)
assertContains(
  "src/components/layout/RightPanel.vue",
  "\u5de5\u5177\u3001MCP\u3001Skills\u3001\u63d0\u793a\u8bcd\u548c\u6a21\u578b\u7531\u4ee3\u7801\u4e2d\u7684 graph \u51b3\u5b9a",
  "right panel must explain code graph ownership",
)
assertContains(
  "src/components/layout/RightPanel.vue",
  "v-if=\"!agentsStore.isChatAgent && !agentsStore.isCodeAgent\"",
  "right panel must hide configurable tools for code agents",
)

console.log('[code-agent-contract] store checks passed')
