<template>
  <div class="chat-input-wrapper">
    <div v-if="isEditing" class="edit-banner">
      <span>正在编辑上一条消息</span>
      <button type="button" class="cancel-edit-btn" @click="handleCancelEdit">取消</button>
    </div>
    <div class="textarea-shell" :class="{ 'is-disabled': isInputDisabled }">
      <textarea
        ref="textareaRef"
        v-model="messageText"
        class="chat-textarea"
        rows="1"
        placeholder="Send a message..."
        enterkeyhint="enter"
        :disabled="isInputDisabled"
        @input="resizeTextarea"
        @keydown="handleKeydown"
      />
      <div class="input-actions">
        <button
          v-if="isStreamingState"
          type="button"
          class="input-action-btn stop-btn animated-stop-btn"
          aria-label="停止生成"
          title="停止生成"
          @click="handleStop"
        >
          <span class="stop-spinner" aria-hidden="true">
            <span class="stop-square" />
          </span>
        </button>
        <button
          v-else-if="messageText"
          type="button"
          class="input-action-btn clear-btn"
          @click="clearInput"
        >
          清空
        </button>
        <button
          v-if="!isStreamingState"
          type="button"
          class="send-btn"
          :disabled="!canSend"
          @click="handleSubmit"
        >
          发送
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'

const props = defineProps<{
  isStreaming?: boolean
  editContent?: string
  isEditing?: boolean
}>()

const emit = defineEmits<{
  send: [content: string]
  stop: []
  cancelEdit: []
}>()

const chatStore = useChatStore()
const { isStreaming } = storeToRefs(chatStore)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const messageText = ref('')
const isStreamingState = computed(() => props.isStreaming ?? isStreaming.value)
const isInputDisabled = computed(() => isStreamingState.value)
const canSend = computed(() => Boolean(messageText.value.trim()) && !isInputDisabled.value)

watch(() => props.editContent, async (content) => {
  messageText.value = content || ''
  await nextTick()
  resizeTextarea()
  if (messageText.value) {
    focusTextarea('end')
  }
}, { immediate: true })

onMounted(async () => {
  await nextTick()
  resizeTextarea()
  if (!isInputDisabled.value) {
    focusTextarea('end')
  }
})

function resizeTextarea() {
  const textarea = textareaRef.value
  if (!textarea) return
  textarea.style.height = 'auto'
  const maxHeight = Math.floor(window.innerHeight * 0.4)
  const nextHeight = Math.min(textarea.scrollHeight, maxHeight)
  textarea.style.height = `${nextHeight}px`
  textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden'
}

function focusTextarea(position: 'start' | 'end' = 'end') {
  const textarea = textareaRef.value
  if (!textarea) return
  textarea.focus()
  const cursor = position === 'start' ? 0 : textarea.value.length
  textarea.setSelectionRange(cursor, cursor)
}

function clearInput() {
  messageText.value = ''
  nextTick(() => {
    resizeTextarea()
    focusTextarea('end')
  })
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' || (!event.ctrlKey && !event.metaKey) || event.isComposing) return
  event.preventDefault()
  handleSubmit()
}

function handleSubmit() {
  const text = messageText.value.trim()
  if (!text || isInputDisabled.value) return
  emit('send', text)
  clearInput()
}

function handleStop() {
  emit('stop')
}

function handleCancelEdit() {
  clearInput()
  emit('cancelEdit')
}
</script>

<style scoped>
.chat-input-wrapper {
  padding: 10px 20px 14px;
  border-top: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  box-sizing: border-box;
  flex-shrink: 0;
  position: relative;
  z-index: 120;
  width: 100%;
}

.textarea-shell {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  width: 100%;
  padding: 7px 8px 7px 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color-overlay);
  box-sizing: border-box;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.textarea-shell:focus-within {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--el-color-primary) 22%, transparent);
}

.textarea-shell.is-disabled {
  opacity: 0.78;
}

.chat-textarea {
  flex: 1;
  min-width: 0;
  min-height: 22px;
  max-height: 40vh;
  resize: none;
  border: none;
  outline: none;
  padding: 1px 0;
  background: transparent;
  color: var(--el-text-color-primary);
  font: inherit;
  font-size: 14px;
  line-height: 22px;
  overflow-y: hidden;
  scrollbar-width: thin;
}

.chat-textarea::placeholder {
  color: var(--el-text-color-placeholder);
}

.chat-textarea:disabled {
  cursor: not-allowed;
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  min-height: 24px;
}

.input-action-btn,
.send-btn {
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  line-height: 18px;
  padding: 4px 8px;
  transition: background 0.18s ease, color 0.18s ease, opacity 0.18s ease;
}

.input-action-btn {
  background: transparent;
  color: var(--el-text-color-secondary);
}

.input-action-btn:hover {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

.stop-btn {
  width: 28px;
  height: 28px;
  padding: 0;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--el-color-danger) 10%, transparent);
  color: var(--el-color-danger);
}

.stop-btn:hover {
  background: color-mix(in srgb, var(--el-color-danger) 16%, transparent);
  color: var(--el-color-danger);
}

.stop-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid color-mix(in srgb, var(--el-color-danger) 28%, transparent);
  border-top-color: var(--el-color-danger);
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  animation: stop-spin 0.9s linear infinite;
  box-sizing: border-box;
}

.stop-square {
  width: 6px;
  height: 6px;
  border-radius: 1px;
  background: var(--el-color-danger);
  display: block;
}

@keyframes stop-spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

.clear-btn {
  color: var(--el-text-color-secondary);
}

.send-btn {
  background: var(--el-color-primary);
  color: #fff;
  font-weight: 600;
}

.send-btn:hover:not(:disabled) {
  background: var(--el-color-primary-light-3);
}

.send-btn:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.edit-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
  padding: 7px 10px;
  border: 1px solid color-mix(in srgb, var(--el-color-success) 38%, var(--el-border-color));
  border-radius: 8px;
  background: color-mix(in srgb, var(--el-color-success) 12%, var(--el-bg-color-overlay));
  color: var(--el-text-color-primary);
  font-size: 12px;
}

.cancel-edit-btn {
  border: none;
  background: transparent;
  color: var(--el-color-success);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 4px;
}

.cancel-edit-btn:hover {
  color: var(--el-color-success-light-3);
}

@media (max-width: 520px) {
  .chat-input-wrapper {
    padding: 8px 10px 10px;
  }

  .textarea-shell {
    border-radius: 10px;
    padding: 7px 7px 7px 10px;
  }

  .input-action-btn,
  .send-btn {
    padding: 4px 7px;
  }
}
</style>
