<template>
  <div class="chat-view">
    <div class="messages-area" ref="messagesRef">
      <div v-if="!messages.length" class="empty-state">
        <div class="empty-icon">⚡</div>
        <p>开始新的对话</p>
      </div>
      <TransitionGroup name="msg" tag="div">
        <ChatBubble v-for="msg in messages" :key="msg.id" :message="msg" />
      </TransitionGroup>
    </div>

    <ChatInput :is-streaming="isStreaming" @send="handleSend" />

    <InterruptDialog
      :interrupt="interrupt"
      @decide="handleInterruptDecide"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'
import { useAgentsStore } from '@/stores/agents'
import ChatBubble from '@/components/chat/ChatBubble.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import InterruptDialog from '@/components/chat/InterruptDialog.vue'

const chatStore = useChatStore()
const agentsStore = useAgentsStore()
const { messages, isStreaming, interrupt } = storeToRefs(chatStore)
const messagesRef = ref<HTMLElement>()

onMounted(() => {
  chatStore.connect()
})

function handleSend(content: string) {
  chatStore.sendMessage(content, agentsStore.currentAgentId)
}

function handleInterruptDecide(decision: { type: string }) {
  chatStore.respondToInterrupt(decision.type === 'approve', agentsStore.currentAgentId)
}

watch(messages, () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}, { deep: true })
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--lc-text-secondary);
  gap: 8px;
}

.empty-icon {
  font-size: 48px;
  opacity: 0.4;
}

.empty-state p {
  font-size: 16px;
  opacity: 0.6;
}

.msg-enter-active {
  animation: float-in var(--lc-transition-slow) ease both;
}
</style>
