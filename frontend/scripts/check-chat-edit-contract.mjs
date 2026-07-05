import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))

function read(relativePath) {
  return readFileSync(join(root, relativePath), 'utf8')
}

const files = {
  chatView: read('src/views/ChatView.vue'),
  chatInput: read('src/components/chat/ChatInput.vue'),
  chatStore: read('src/stores/chat.ts'),
  sseClient: read('src/api/sse-client.ts'),
  http: read('src/api/http.ts'),
  rightPanel: read('src/components/layout/RightPanel.vue'),
  toolsStore: read('src/stores/tools.ts'),
  sseServer: read('../lc_agent/server/sse.py'),
  engine: read('../lc_agent/core/engine.py'),
}

const failures = []

function expectIncludes(name, content, expected) {
  if (!content.includes(expected)) failures.push(`${name} 缺少: ${expected}`)
}

function expectMatch(name, content, pattern, message) {
  if (!pattern.test(content)) failures.push(`${name} ${message}`)
}

expectIncludes('ChatView.vue', files.chatView, 'canEditMessage(item)')
expectIncludes('ChatView.vue', files.chatView, 'class="message-edit-btn"')
expectIncludes('ChatView.vue', files.chatView, 'title="编辑并重新发送"')
expectIncludes('ChatView.vue', files.chatView, '@click.stop="startEditMessage(item)"')
expectIncludes('ChatView.vue', files.chatView, 'const editingMessageId = ref<string | null>(null)')
expectIncludes('ChatView.vue', files.chatView, 'const editingContent = ref(\'\')')
expectIncludes('ChatView.vue', files.chatView, ':edit-content="editingContent"')
expectIncludes('ChatView.vue', files.chatView, ':is-editing="Boolean(editingMessageId)"')
expectIncludes('ChatView.vue', files.chatView, '@cancel-edit="cancelEdit"')
expectIncludes('ChatView.vue', files.chatView, 'function getReplayHistory(beforeMessageId: string): ReplayMessage[]')
expectIncludes('ChatView.vue', files.chatView, 'replaceFromMessageId: editMessageId || undefined')
expectIncludes('ChatView.vue', files.chatView, 'history,')
expectIncludes('ChatView.vue', files.chatView, 'reasoningEffort: toolsStore.reasoningEffort,')
expectMatch(
  'ChatView.vue',
  files.chatView,
  /function canEditMessage\(item: ChatBubbleItem\)[\s\S]*item\.role === 'user'[\s\S]*lastUserMessage\.value\?\.id === item\.messageId[\s\S]*!isStreaming\.value/,
  '编辑入口必须限制为最后一条用户消息且非流式输出中',
)
expectMatch(
  'ChatView.vue',
  files.chatView,
  /function handleSend\(content: string\)[\s\S]*getReplayHistory\(editMessageId\)[\s\S]*chatStore\.truncateAfterMessage\(editingMessageId\.value\)[\s\S]*cancelEdit\(\)[\s\S]*chatStore\.sendMessage/,
  '编辑提交必须保留编辑点之前的历史、截断旧回复，再重新发送',
)
expectIncludes('ChatInput.vue', files.chatInput, 'isEditing?: boolean')
expectIncludes('ChatInput.vue', files.chatInput, 'watch(() => props.editContent')
expectIncludes('ChatInput.vue', files.chatInput, 'ref="textareaRef"')
expectIncludes('ChatInput.vue', files.chatInput, 'v-model="messageText"')
expectIncludes('ChatInput.vue', files.chatInput, 'function resizeTextarea()')
expectIncludes('ChatInput.vue', files.chatInput, 'function handleKeydown(event: KeyboardEvent)')
expectIncludes('ChatInput.vue', files.chatInput, 'if (event.key !== \'Enter\' || (!event.ctrlKey && !event.metaKey) || event.isComposing) return')
expectIncludes('ChatInput.vue', files.chatInput, 'class="stop-spinner"')
expectIncludes('ChatInput.vue', files.chatInput, 'class="stop-square"')
expectIncludes('ChatInput.vue', files.chatInput, '@keyframes stop-spin')
expectIncludes('ChatInput.vue', files.chatInput, 'class="edit-banner"')
expectIncludes('ChatInput.vue', files.chatInput, '@click="handleCancelEdit"')
expectIncludes('chat.ts', files.chatStore, 'function truncateAfterMessage(messageId: string)')
expectIncludes('chat.ts', files.chatStore, 'messages.value = messages.value.slice(0, idx)')
expectIncludes('chat.ts', files.chatStore, 'truncateAfterMessage')
expectIncludes('chat.ts', files.chatStore, 'export interface ReplayMessage')
expectIncludes('chat.ts', files.chatStore, 'export interface SendMessageOptions')
expectIncludes('chat.ts', files.chatStore, 'replaceFromMessageId: options.replaceFromMessageId')
expectIncludes('sse-client.ts', files.sseClient, "export type ReasoningEffort = 'default' | 'none' | 'minimal' | 'low' | 'medium' | 'high' | 'xhigh'")
expectIncludes('sse-client.ts', files.sseClient, 'reasoningEffort?: ReasoningEffort')
expectIncludes('sse-client.ts', files.sseClient, "if (options?.reasoningEffort && options.reasoningEffort !== 'default') {")
expectIncludes('sse-client.ts', files.sseClient, 'body.reasoning_effort = options.reasoningEffort')
expectIncludes('sse-client.ts', files.sseClient, 'replace_from_message_id = options.replaceFromMessageId')
expectIncludes('chat.ts', files.chatStore, 'history: options.history')
expectIncludes('chat.ts', files.chatStore, 'const INITIAL_MESSAGE_LIMIT = 6')
expectIncludes('chat.ts', files.chatStore, 'await api.getSessionMessages(sessionId, { limit: INITIAL_MESSAGE_LIMIT })')
expectIncludes('chat.ts', files.chatStore, 'const olderPageSize = INITIAL_MESSAGE_LIMIT')
expectIncludes('ChatView.vue', files.chatView, 'ref="messagesContainerRef"')
expectIncludes('ChatView.vue', files.chatView, 'function scrollMessagesToBottom()')
expectIncludes('ChatView.vue', files.chatView, 'scrollMessagesToBottom()')
expectIncludes('ChatView.vue', files.chatView, 'watch(() => messages.value[messages.value.length - 1]?.id')
expectIncludes('ChatView.vue', files.chatView, 'type LoadOlderBubbleItem = BubbleListItemProps & {')
expectIncludes('ChatView.vue', files.chatView, "itemType: 'load-older'")
expectIncludes('ChatView.vue', files.chatView, "if (hasOlderMessages.value) items.unshift(createLoadOlderItem())")
expectIncludes('ChatView.vue', files.chatView, '<template #item="{ item }">')
expectIncludes('ChatView.vue', files.chatView, "v-if=\"item.itemType === 'load-older'\"")
expectIncludes('ChatView.vue', files.chatView, 'class="load-older-messages is-inline"')
expectIncludes('ChatView.vue', files.chatView, 'function createLoadOlderItem(): LoadOlderBubbleItem')
expectIncludes('ChatView.vue', files.chatView, 'function getMessagesScroller()')
expectIncludes('ChatView.vue', files.chatView, '.elx-bubble-list__list')
expectIncludes('ChatView.vue', files.chatView, 'async function handleLoadOlderMessages()')
expectIncludes('ChatView.vue', files.chatView, 'const distanceFromBottom = scroller.scrollHeight - scroller.scrollTop')
expectIncludes('ChatView.vue', files.chatView, 'scroller.scrollTop = scroller.scrollHeight - distanceFromBottom')
expectIncludes('ChatView.vue', files.chatView, 'if (loadingOlder.value) return')
expectIncludes('ChatView.vue', files.chatView, '@click="handleLoadOlderMessages"')
expectMatch(
  'ChatView.vue',
  files.chatView,
  /<BubbleList[\s\S]*:list="bubbleList"[\s\S]*<template #item="\{ item \}">[\s\S]*item\.itemType === 'load-older'[\s\S]*@click="handleLoadOlderMessages"/,
  '加载更早入口必须作为 BubbleList 内联自定义第一项渲染',
)
expectMatch(
  'ChatView.vue',
  files.chatView,
  /const bubbleList = computed\(\(\): ChatBubbleItem\[\] =>[\s\S]*const items = messages\.value[\s\S]*if \(hasOlderMessages\.value\) items\.unshift\(createLoadOlderItem\(\)\)[\s\S]*return items/,
  'bubbleList 必须在还有更早消息时把加载入口插入为第一项',
)
expectIncludes('http.ts', files.http, 'if (params?.offset !== undefined)')

if (failures.length > 0) {
  console.error('聊天编辑并重发契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('聊天编辑并重发契约测试通过')
