<template>
  <div class="tool-call-card" :class="toolCall.status">
    <div class="tool-header">
      <el-icon v-if="toolCall.status === 'running'" class="spinning">
        <Loading />
      </el-icon>
      <el-icon v-else-if="toolCall.status === 'done'" style="color: var(--lc-success)">
        <Check />
      </el-icon>
      <span class="tool-name">{{ toolCall.name }}</span>
      <el-tag size="small" :type="statusType">{{ statusLabel }}</el-tag>
    </div>
    <div v-if="toolCall.result" class="tool-result">
      <pre>{{ toolCall.result }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Loading, Check } from '@element-plus/icons-vue'
import type { ToolCall } from '@/stores/chat'

const props = defineProps<{ toolCall: ToolCall }>()

const statusType = computed(() => {
  switch (props.toolCall.status) {
    case 'running': return 'warning'
    case 'done': return 'success'
    case 'error': return 'danger'
    default: return 'info'
  }
})

const statusLabel = computed(() => {
  switch (props.toolCall.status) {
    case 'running': return '执行中'
    case 'done': return '完成'
    case 'error': return '错误'
    default: return '等待'
  }
})
</script>

<style scoped>
.tool-call-card {
  border: 1px solid var(--lc-glass-border);
  border-radius: var(--lc-radius-md);
  padding: 10px 14px;
  margin: 6px 0;
  background: var(--lc-glass-bg);
  border-left: 3px solid var(--lc-text-secondary);
  transition: border-color var(--lc-transition-normal), box-shadow var(--lc-transition-normal);
  animation: float-in var(--lc-transition-slow) ease both;
}

.tool-call-card.running {
  border-left-color: var(--lc-accent);
  box-shadow: 0 0 12px rgba(88, 166, 255, 0.08);
}

.tool-call-card.done {
  border-left-color: var(--lc-success);
}

.tool-call-card.error {
  border-left-color: var(--lc-danger);
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-name {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
  color: var(--lc-accent);
  font-weight: 500;
}

.tool-result {
  margin-top: 8px;
  padding: 8px 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--lc-radius-sm);
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--lc-glass-border);
}

.tool-result pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--lc-text-secondary);
}

.spinning {
  animation: spin 1s linear infinite;
  color: var(--lc-accent);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
