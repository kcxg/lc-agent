<template>
  <div class="subagent-card" :class="statusClass">
    <!-- Header -->
    <div class="sa-header">
      <span class="sa-icon">🤖</span>
      <div class="sa-meta">
        <div class="sa-name">{{ entry.name }}</div>
        <div class="sa-submeta">
          <span v-if="entry.status === 'running'" class="sa-running-dot"></span>
          <span v-if="entry.status === 'running'">执行中</span>
          <span v-if="entry.status === 'done'">完成 ✓</span>
          <span v-if="entry.status === 'error'">失败</span>
          <template v-if="entry.toolCallCount > 0">
            · 🔧 {{ entry.toolCallCount }}次
          </template>
          <template v-if="entry.tokenCount > 0">
            · 💬 {{ entry.tokenCount }}
          </template>
          <template v-if="entry.duration">
            · ⏱ {{ formatDuration(entry.duration) }}
          </template>
        </div>
      </div>
      <button
        v-if="entry.sub_session_id"
        class="sa-enter-btn"
        @click="$emit('enter', entry.sub_session_id, entry.name)"
      >
        ↗
      </button>
    </div>
    <!-- Body: running state shows streaming tokens -->
    <div class="sa-body">
      <div v-if="entry.status === 'running' && entry.tokens" class="sa-tokens">
        {{ entry.tokens }}▋
      </div>
      <div v-else-if="entry.status === 'done' && entry.tokenPreview" class="sa-preview">
        {{ entry.tokenPreview }}
      </div>
      <!-- Inner tool calls (compact) -->
      <div v-if="entry.innerToolCalls.length" class="sa-inner-tools">
        <div v-for="(tc, i) in entry.innerToolCalls" :key="i" class="sa-inner-tool">
          <span class="sa-inner-status" :class="tc.status">●</span>
          🔧 {{ tc.name }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SubAgentEntry } from '@/stores/chat'

const props = defineProps<{
  entry: SubAgentEntry
}>()

defineEmits<{
  enter: [sub_session_id: string, name: string]
}>()

const statusClass = computed(() => ({
  'sa-running': props.entry.status === 'running',
  'sa-done': props.entry.status === 'done',
  'sa-error': props.entry.status === 'error',
}))

function formatDuration(ms: number) {
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`
}
</script>

<style scoped>
.subagent-card {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
  margin: 6px 0;
  border-left: 3px solid var(--el-color-primary);
}
.sa-running { border-left-color: var(--el-color-primary); }
.sa-done { border-left-color: var(--el-color-success); }
.sa-error { border-left-color: var(--el-color-danger); }

.sa-header {
  background: var(--el-color-primary-light-9);
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid var(--el-color-primary-light-7);
}
.sa-icon { font-size: 16px; }
.sa-meta { flex: 1; min-width: 0; }
.sa-name { font-weight: 700; color: var(--el-color-primary-dark-2); font-size: 13px; }
.sa-submeta {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 1px;
}
.sa-running-dot {
  width: 7px;
  height: 7px;
  background: var(--el-color-primary);
  border-radius: 50%;
  animation: pulse 1s infinite;
  align-self: center;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.sa-enter-btn {
  background: none;
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 6px;
  padding: 3px 8px;
  color: var(--el-color-primary);
  cursor: pointer;
  font-size: 14px;
  flex-shrink: 0;
}
.sa-enter-btn:hover { background: var(--el-color-primary-light-9); }
.sa-body { padding: 8px 12px; }
.sa-tokens { color: var(--el-text-color-regular); font-size: 12px; line-height: 1.6; }
.sa-preview { color: var(--el-text-color-secondary); font-size: 12px; line-height: 1.5; }
.sa-inner-tools { margin-top: 6px; display: flex; flex-direction: column; gap: 3px; }
.sa-inner-tool {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  display: flex;
  align-items: center;
  gap: 5px;
}
.sa-inner-status { font-size: 8px; }
.sa-inner-status.running { color: var(--el-color-warning); }
.sa-inner-status.done { color: var(--el-color-success); }
</style>
