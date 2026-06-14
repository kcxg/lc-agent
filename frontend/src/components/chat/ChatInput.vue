<template>
  <div class="chat-input-wrapper">
    <XSender
      ref="senderRef"
      :loading="isStreaming"
      :disabled="!isConnected"
      placeholder="Send a message..."
      submit-type="enter"
      clearable
      auto-focus
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { XSender } from 'vue-element-plus-x'
import { useChatStore } from '@/stores/chat'

defineProps<{
  isStreaming?: boolean
  editContent?: string
}>()

const emit = defineEmits<{
  send: [content: string]
  stop: []
  cancelEdit: []
}>()

const chatStore = useChatStore()
const { isStreaming, isConnected } = storeToRefs(chatStore)
const senderRef = ref<InstanceType<typeof XSender>>()

function handleSubmit() {
  const model = senderRef.value?.getModelValue()
  const text = model?.text ?? ''
  if (!text.trim()) return
  emit('send', text.trim())
  senderRef.value?.clear()
}
</script>

<style scoped>
.chat-input-wrapper {
  padding: 10px 20px 14px;
  border-top: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
}

.chat-input-wrapper :deep(.elx-x-sender) {
  background: var(--el-bg-color-overlay) !important;
  border-color: var(--el-border-color) !important;
  border-radius: 8px;
}

.chat-input-wrapper :deep(.chat-rich-text) {
  background: transparent !important;
}

.chat-input-wrapper :deep([contenteditable="true"]) {
  color: var(--el-text-color-primary) !important;
}

.chat-input-wrapper :deep([contenteditable="true"] p),
.chat-input-wrapper :deep([contenteditable="true"] span) {
  color: inherit !important;
}

.chat-input-wrapper :deep(.elx-x-sender__chat) {
  background: transparent !important;
}

.chat-input-wrapper :deep(.chat-grid-wrap) {
  color: var(--el-text-color-primary) !important;
}
</style>
