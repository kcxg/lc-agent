import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const chatStore = readFileSync(join(root, 'src/stores/chat.ts'), 'utf8')
const chatView = readFileSync(join(root, 'src/views/ChatView.vue'), 'utf8')
const sessionState = readFileSync(join(root, 'src/stores/chat-session-state.ts'), 'utf8')
const failures = []

// 1) 后端下发轮次号 → 前端订阅并回填到直播消息上
if (!chatStore.includes("client.on('conversation_round'")) {
  failures.push("chat.ts 未订阅 conversation_round 事件")
}
if (!chatStore.includes('state.currentRoundNumber = roundNumber')) {
  failures.push('chat.ts 未记录当前轮次号')
}
if (!chatStore.includes('m.roundNumber = roundNumber')) {
  failures.push('chat.ts 未把轮次号回填到直播 user 消息')
}
if (!sessionState.includes('currentRoundNumber')) {
  failures.push('chat-session-state.ts 缺少 currentRoundNumber')
}

// 2) 轮次推导只允许一份实现（两份就是这次错位的温床）
const derivations = chatView.split('let round = 0').length - 1
if (derivations !== 1) {
  failures.push(`ChatView.vue 里轮次推导应只有一份，实际 ${derivations} 份`)
}
if (!chatView.includes('const { lastAssistantOfRound } = messageRounds.value')) {
  failures.push('roundFileCards 应复用 messageRounds 的轮次口径')
}
if (!chatView.includes('const roundOfMessage = computed<Map<string, number>>(() => messageRounds.value.byMessage)')) {
  failures.push('roundOfMessage 应从 messageRounds 派生')
}
if (chatView.includes('lastAiIdByRound')) {
  failures.push('ChatView.vue 仍残留旧的 lastAiIdByRound 推导')
}

if (failures.length > 0) {
  console.error('轮次-文件变更卡片契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('轮次-文件变更卡片契约测试通过')
