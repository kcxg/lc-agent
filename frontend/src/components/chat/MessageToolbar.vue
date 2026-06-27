<script setup lang="ts">
import { ref } from 'vue'
import {
  singleMessageToMarkdown,
  extractThinking,
  extractToolCalls,
  extractAnswer,
  copyToClipboard,
} from '@/utils/copy-markdown'
import type { ChatMessage } from '@/stores/chat'

const props = defineProps<{
  message: ChatMessage
  modelName?: string
  hasThinking?: boolean
  hasToolCalls?: boolean
  hasAnswer?: boolean
}>()

const copiedKey = ref<string | null>(null)

async function doCopy(key: string, text: string) {
  if (!text) return
  const ok = await copyToClipboard(text)
  if (ok) {
    copiedKey.value = key
    setTimeout(() => (copiedKey.value = null), 1500)
  }
}

function copyAll() {
  doCopy('all', singleMessageToMarkdown(props.message, { modelName: props.modelName }))
}
function copyThinking() {
  doCopy('thinking', extractThinking(props.message))
}
function copyTools() {
  doCopy('tools', extractToolCalls(props.message))
}
function copyAnswer() {
  doCopy('answer', extractAnswer(props.message))
}
function copyUser() {
  doCopy('all', props.message.content)
}
</script>

<template>
  <div class="message-toolbar">
    <template v-if="message.role === 'user'">
      <button class="tb-btn" @click="copyUser">
        {{ copiedKey === 'all' ? '已复制 ✓' : '📋 复制' }}
      </button>
    </template>
    <template v-else>
      <button class="tb-btn" @click="copyAll">
        {{ copiedKey === 'all' ? '已复制 ✓' : '📋 复制全部' }}
      </button>
      <button v-if="hasThinking" class="tb-btn" @click="copyThinking">
        {{ copiedKey === 'thinking' ? '已复制 ✓' : '💭 复制思考' }}
      </button>
      <button v-if="hasToolCalls" class="tb-btn" @click="copyTools">
        {{ copiedKey === 'tools' ? '已复制 ✓' : '🔧 复制工具' }}
      </button>
      <button v-if="hasAnswer" class="tb-btn" @click="copyAnswer">
        {{ copiedKey === 'answer' ? '已复制 ✓' : '📝 复制回答' }}
      </button>
    </template>
  </div>
</template>

<style scoped>
.message-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
  opacity: 0.35;
  transition: opacity 0.2s;
}
.message-toolbar:hover {
  opacity: 1;
}

@media (max-width: 768px) {
  .message-toolbar {
    opacity: 1;
  }
}

.tb-btn {
  background: var(--el-fill-color-light, #f5f7fa);
  border: 1px solid var(--el-border-color-lighter, #e4e7ed);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
  color: var(--el-text-color-secondary, #909399);
  transition: all 0.15s;
}
.tb-btn:hover {
  background: var(--el-color-primary-light-9, #ecf5ff);
  border-color: var(--el-color-primary-light-7, #c6e2ff);
  color: var(--el-color-primary, #409eff);
}
.tb-btn:active {
  transform: scale(0.96);
}

@media (max-width: 768px) {
  .tb-btn {
    padding: 6px 12px;
    font-size: 13px;
    min-height: 36px;
  }
}
</style>
