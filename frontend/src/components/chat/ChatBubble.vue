<template>
  <div class="chat-bubble" :class="[message.role, { streaming: message.isStreaming }]">
    <div class="bubble-avatar">
      {{ message.role === 'user' ? '👤' : '🤖' }}
    </div>
    <div class="bubble-content">
      <div v-if="message.role === 'assistant'" class="markdown-body" v-html="renderedContent" />
      <div v-else class="plain-text">{{ message.content }}</div>

      <div v-if="message.toolCalls?.length" class="tool-calls">
        <ToolCallCard
          v-for="(tc, idx) in message.toolCalls"
          :key="idx"
          :tool-call="tc"
        />
      </div>

      <span v-if="message.isStreaming" class="streaming-cursor">▊</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/markdown'
import ToolCallCard from './ToolCallCard.vue'
import type { ChatMessage } from '@/stores/chat'

const props = defineProps<{ message: ChatMessage }>()

const renderedContent = computed(() => renderMarkdown(props.message.content))
</script>

<style scoped>
.chat-bubble {
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--lc-radius-lg);
  margin-bottom: 10px;
  border: 1px solid transparent;
  transition: background var(--lc-transition-fast);
}

.chat-bubble.user {
  background: var(--lc-gradient-user-bubble);
  border-color: rgba(88, 166, 255, 0.15);
  margin-left: 40px;
  border-radius: 14px 14px 4px 14px;
}

.chat-bubble.assistant {
  background: var(--lc-glass-bg);
  border-color: var(--lc-glass-border);
  margin-right: 40px;
  border-radius: 14px 14px 14px 4px;
}

.bubble-avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  background: var(--lc-glass-bg-hover);
  border-radius: 50%;
  flex-shrink: 0;
}

.bubble-content {
  flex: 1;
  overflow-wrap: break-word;
  line-height: 1.7;
  font-size: 14px;
}

.streaming-cursor {
  animation: blink 1s infinite;
  color: var(--lc-accent);
  font-size: 16px;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.tool-calls {
  margin-top: 10px;
}
</style>
