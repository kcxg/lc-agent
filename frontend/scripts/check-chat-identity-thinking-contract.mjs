import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))

function read(relativePath) {
  return readFileSync(join(root, relativePath), 'utf8')
}

const files = {
  chatView: read('src/views/ChatView.vue'),
  genericCard: read('src/components/chat/tools/ToolGenericCard.vue'),
  useToolCard: read('src/components/chat/tools/useToolCard.ts'),
  chatStore: read('src/stores/chat.ts'),
  sseClient: read('src/api/sse-client.ts'),
  chatInput: read('src/components/chat/ChatInput.vue'),
}

const failures = []

function expectIncludes(name, content, expected) {
  if (!content.includes(expected)) failures.push(`${name} 缺少: ${expected}`)
}

function expectMatch(name, content, pattern, message) {
  if (!pattern.test(content)) failures.push(`${name} ${message}`)
}

expectIncludes('ChatView.vue', files.chatView, '#header="{ item }"')
expectIncludes('ChatView.vue', files.chatView, 'class="role-avatar is-ai"')
expectIncludes('ChatView.vue', files.chatView, 'class="role-avatar is-user"')
expectIncludes('ChatView.vue', files.chatView, 'class="role-header is-ai"')
expectMatch('ChatView.vue', files.chatView, /v-else\s+class="role-header is-ai"/, '助手身份栏没有限制为仅助手消息展示')
expectIncludes('ChatView.vue', files.chatView, 'getAssistantLabel()')
expectIncludes('ChatView.vue', files.chatView, 'getModelLabel()')
expectIncludes('ChatView.vue', files.chatView, "type: 'thinking'")
expectIncludes('ChatView.vue', files.chatView, 'class="thinking-block"')
expectIncludes('ChatView.vue', files.chatView, 'class="thinking-unavailable"')
expectIncludes('ChatView.vue', files.chatView, 'shouldShowReasoningNotice(item)')
expectIncludes('ChatView.vue', files.chatView, 'getReasoningTokenTotal')
expectIncludes('ChatView.vue', files.chatView, '没有返回可展示的思考文字')
expectIncludes('ChatView.vue', files.chatView, 'class="thinking-summary"')
expectIncludes('ChatView.vue', files.chatView, 'hasStructuredSegments')
// THINK 标记（现为 THINK_START/THINK_END 常量）解析成 thinking segment
expectMatch('ChatView.vue', files.chatView, /THINK_START[\s\S]*type: inThinking \? 'thinking' : 'text'/, '没有把 THINK 标记解析成 thinking segment')
// 思考块流式输出中默认展开（isThinkingExpanded 兜底 isStreamingMessage === true），结束后可点"思考过程"展开
expectMatch('ChatView.vue', files.chatView, /class="thinking-block"[\s\S]*isThinkingExpanded[\s\S]*\?\? item\.isStreamingMessage === true/, '思考块流式期间没有默认展开，用户会看不到思考正文')
if (files.chatView.includes(':open="item.loading"')) {
  failures.push('ChatView.vue 思考块仍绑定 item.loading；thinking 一写入 content 后 loading 会变 false')
}

// 工具卡片（拆成多张卡后由 ToolGenericCard + useToolCard 承载这些行为）
expectIncludes('ToolGenericCard.vue', files.genericCard, 'badgeIcon')
expectIncludes('ToolGenericCard.vue', files.genericCard, "@element-plus/icons-vue")
expectIncludes('ToolGenericCard.vue', files.genericCard, 'label="工具"')
expectIncludes('ToolGenericCard.vue', files.genericCard, '@click.stop="toggleCollapse"')
expectIncludes('useToolCard.ts', files.useToolCard, 'userToggled')
expectMatch(
  'useToolCard.ts',
  files.useToolCard,
  /if \(userToggled\.value\) return/,
  '工具完成后会覆盖用户手动折叠的结果（用户点过之后就不该再自动折叠）',
)

expectIncludes('sse-client.ts', files.sseClient, 'reasoning_tokens?: number')
expectIncludes('chat.ts', files.chatStore, 'function mergeFinalUsageRounds')
expectIncludes('chat.ts', files.chatStore, 'reasoningTokens: msg.reasoning_tokens || 0')
expectIncludes('chat.ts', files.chatStore, 'mergeFinalUsageRounds(last.usage.rounds, usageData)')
expectIncludes('chat.ts', files.chatStore, 'client.sendMessage(content, presetId, modelId')
expectMatch(
  'ChatView.vue',
  files.chatView,
  /const modelOverride = agentsStore\.isCodeAgent \? '' : toolsStore\.currentModel[\s\S]*chatStore\.sendMessage\(\s*content,\s*agentsStore\.currentAgentId,\s*modelOverride/,
  '发送消息必须继续使用当前 Agent 和当前模型',
)
expectIncludes('ChatInput.vue', files.chatInput, "send: [content: ContentBlock[]]")
expectIncludes('ChatView.vue', files.chatView, '<span class="role-name">你</span>')
expectMatch(
  'ChatView.vue',
  files.chatView,
  /\.elx-bubble__avatar[\s\S]*display:\s*none/,
  '两侧头像列没有隐藏，身份标识应收进顶部 header 行',
)

if (failures.length > 0) {
  console.error('聊天身份与思考展示契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('聊天身份与思考展示契约测试通过')
