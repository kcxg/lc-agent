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
assertContains(
  "src/components/dialogs/AgentEditorDialog.vue",
  "\u6b64\u667a\u80fd\u4f53\u7531\u4ee3\u7801\u6ce8\u518c\uff08CompiledGraph\uff09\uff0c\u5de5\u5177\u3001MCP\u3001Skills\u3001\u63d0\u793a\u8bcd\u548c\u6a21\u578b\u7531\u4ee3\u7801\u4e2d\u7684 graph \u51b3\u5b9a\u3002",
  "editor must explain that code-agent framework fields are graph-owned",
)
assertContains(
  "src/components/dialogs/AgentEditorDialog.vue",
  "<el-form v-if=\"!isCodeAgent\"",
  "editor must hide normal editable form for code agents",
)
assertContains(
  "src/components/dialogs/AgentEditorDialog.vue",
  "v-if=\"!isCodeAgent\"",
  "editor save button must be hidden for code agents",
)
assertNotContains(
  "src/components/dialogs/AgentEditorDialog.vue",
  "\u4ec5\u53ef\u4fee\u6539\u8fd0\u884c\u65f6\u914d\u7f6e\uff08\u5de5\u5177/MCP/Skills\uff09",
  "editor must not claim code-agent runtime framework config is editable",
)
assertContains(
  "src/views/ChatView.vue",
  "const modelOverride = agentsStore.isCodeAgent ? '' : toolsStore.currentModel",
  "chat send must clear model override for code agents",
)
assertContains(
  "src/views/ChatView.vue",
  "chatStore.sendMessage(content, agentsStore.currentAgentId, modelOverride, {",
  "chat send must use code-agent-aware model override",
)
assertContains(
  "src/App.vue",
  "function getSessionModelForAgent(agentId: string): string {",
  "app must centralize code-agent-aware session model selection",
)
assertContains(
  "src/App.vue",
  "if (agent?.source === 'code') return ''",
  "app session model helper must return empty model for code agents",
)
assertContains(
  "src/App.vue",
  "const sessionModel = getSessionModelForAgent(agentId)",
  "new chats must use code-agent-aware session model",
)
assertContains(
  "src/App.vue",
  ":model-name=\"agentsStore.isCodeAgent ? '\u4ee3\u7801\u5185\u5b9a\u4e49'",
  "app header model prop must show graph-defined text for code agents",
)
assertContains(
  "src/components/layout/AppHeader.vue",
  "if (agentsStore.isCodeAgent) return '\u4ee3\u7801\u5185\u5b9a\u4e49'",
  "header model helper must show graph-defined text for code agents",
)
assertContains(
  "src/views/ChatView.vue",
  "if (agentsStore.isCodeAgent) return '\u4ee3\u7801\u5185\u5b9a\u4e49'",
  "chat message model label must show graph-defined text for code agents",
)
assertContains(
  "src/App.vue",
  "if (sessionAgent?.source === 'code') {",
  "session restore must special-case code-agent stored model",
)
assertContains(
  "src/App.vue",
  "toolsStore.syncModelWithAgentDefault()",
  "session restore must clear UI model for code agents",
)

console.log('[code-agent-contract] store checks passed')
