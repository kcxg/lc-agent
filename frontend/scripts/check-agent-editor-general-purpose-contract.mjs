import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const editor = readFileSync(resolve(root, 'src/components/dialogs/AgentEditorDialog.vue'), 'utf8')
const agentsStore = readFileSync(resolve(root, 'src/stores/agents.ts'), 'utf8')

const checks = [
  ['AgentPreset type exposes subagents relation config', agentsStore.includes('subagents: AgentSubagentConfig[] | null')],
  ['AgentPreset type exposes delegation description item', agentsStore.includes('delegation_description: string')],
  ['editor form tracks subagents relation array', editor.includes('subagents: [] as AgentSubagentConfig[]')],
  ['editor renders delegation description input', editor.includes('delegation_description')],
  ['editor trims delegation description before save', editor.includes("delegation_description: item.delegation_description.trim()")],
  ['editor rejects empty trimmed delegation description', editor.includes('some(item => !item.delegation_description.trim())')],
  ['save payload includes subagents relation config', editor.includes('subagents: normalizedSubagents.length > 0 ? normalizedSubagents : null')],
  ['AgentPreset type still exposes enable_general_purpose_subagent', agentsStore.includes('enable_general_purpose_subagent: boolean')],
  ['editor form tracks enable_general_purpose_subagent', editor.includes('enable_general_purpose_subagent')],
]

const failed = checks.filter(([, ok]) => !ok)
if (failed.length) {
  for (const [name] of failed) console.error(`FAIL ${name}`)
  process.exit(1)
}

for (const [name] of checks) console.log(`PASS ${name}`)
