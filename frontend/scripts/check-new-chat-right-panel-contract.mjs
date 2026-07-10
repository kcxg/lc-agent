import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const app = readFileSync(join(root, 'src/App.vue'), 'utf8')
const tools = readFileSync(join(root, 'src/stores/tools.ts'), 'utf8')
const agents = readFileSync(join(root, 'src/stores/agents.ts'), 'utf8')

const failures = []

function expectMatch(name, content, pattern, message) {
  if (!pattern.test(content)) failures.push(`${name} ${message}`)
}

function expectIncludes(name, content, expected) {
  if (!content.includes(expected)) failures.push(`${name} 缺少: ${expected}`)
}

expectMatch(
  'App.vue',
  app,
  /async function handleNewChat\(\)[\s\S]*const sessionModel = getCurrentRightPanelModelForAgent\(agentsStore\.currentAgentId\)[\s\S]*sessionsStore\.createLocalSession\(agentsStore\.currentAgentId, sessionModel\)/,
  '新建对话必须继承右侧当前模型，而不是回到 agent 默认模型',
)

expectMatch(
  'App.vue',
  app,
  /function getCurrentRightPanelModelForAgent\(agentId: string\): string \{[\s\S]*if \(agent\?\.source === 'code'\) return ''[\s\S]*return toolsStore\.currentModel \|\| agent\?\.default_model \|\| ''[\s\S]*\}/,
  '缺少新建对话专用的右侧模型继承 helper',
)

expectMatch(
  'App.vue',
  app,
  /async function handleAgentChange\(agentId: string\)[\s\S]*const sessionModel = getSessionModelForAgent\(agentId\)/,
  '切换 agent 仍应使用 agent 默认设置创建会话',
)

expectIncludes('tools.ts', tools, '_clearOverrides()')
expectIncludes('tools.ts', tools, 'resetLlmParams()')
expectMatch(
  'tools.ts',
  tools,
  /watch\(\(\) => agentsStore\.currentAgentId,[\s\S]*_clearOverrides\(\)[\s\S]*syncModelWithAgentDefault\(\)[\s\S]*resetLlmParams\(\)/,
  '右侧工具/skills/思考等级覆盖只应在切换 agent 时重置',
)

if (failures.length > 0) {
  console.error('新建对话右侧临时设置契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('新建对话右侧临时设置契约测试通过')
