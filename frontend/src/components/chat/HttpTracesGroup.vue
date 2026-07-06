<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { HttpTrace, LlmRoundUsage } from '@/stores/chat'
import { api } from '@/api/http'
import HttpTraceBlock from './HttpTraceBlock.vue'

const props = defineProps<{
  traces?: HttpTrace[]
  tracesCount?: number
  sessionId?: string
  messageId?: string
  rounds?: LlmRoundUsage[]
}>()

const loadedTraces = ref<HttpTrace[]>([])
const loading = ref(false)
const loadError = ref(false)

const effectiveTraces = computed(() => props.traces?.length ? props.traces : loadedTraces.value)
const displayCount = computed(() => effectiveTraces.value.length || props.tracesCount || 0)

const totalDuration = computed(() => {
  if (!effectiveTraces.value.length) return ''
  const ms = effectiveTraces.value.reduce((sum, t) => sum + (t.durationMs || 0), 0)
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${ms}ms`
})

const errorCount = computed(() =>
  effectiveTraces.value.filter(t => Boolean(t.error) || t.response.ok === false).length,
)

const isOpen = ref(false)

watch(isOpen, async (open) => {
  if (!open) return
  if (effectiveTraces.value.length > 0) return
  if (!props.sessionId || !props.messageId) return

  loading.value = true
  loadError.value = false
  try {
    const resp = await api.getMessageTraces(props.sessionId, props.messageId)
    loadedTraces.value = resp.traces || []
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
})

function onToggle(e: Event) {
  isOpen.value = (e.target as HTMLDetailsElement).open
}
</script>

<template>
  <details class="http-traces-group" @toggle="onToggle">
    <summary class="http-group-summary">
      <span class="http-group-icon">🌐</span>
      <span class="http-group-label">HTTP 交互</span>
      <span class="http-group-stats">
        {{ displayCount }} 步<template v-if="totalDuration"> · {{ totalDuration }}</template>
      </span>
      <span v-if="errorCount > 0" class="http-group-errors">
        {{ errorCount }} 失败
      </span>
      <span class="http-group-toggle" />
    </summary>
    <div class="http-group-body">
      <div v-if="loading" class="http-loading">加载中...</div>
      <div v-else-if="loadError" class="http-load-error">加载失败</div>
      <template v-else>
        <HttpTraceBlock
          v-for="(trace, idx) in effectiveTraces"
          :key="trace.id"
          :trace="trace"
          :usage-round="rounds?.[idx]"
        />
      </template>
    </div>
  </details>
</template>

<style scoped>
.http-traces-group {
  margin: 8px 0;
  border: 1px solid var(--el-border-color-lighter);
  border-left: 3px solid var(--el-color-primary);
  border-radius: 8px;
  background: var(--el-fill-color-light);
  overflow: hidden;
}

.http-group-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  font-size: 13px;
  color: var(--el-text-color-regular);
}
.http-group-summary::-webkit-details-marker {
  display: none;
}

.http-group-icon {
  font-size: 14px;
}
.http-group-label {
  font-weight: 600;
}
.http-group-stats {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.http-group-errors {
  font-size: 12px;
  color: var(--el-color-danger);
  font-weight: 500;
}
.http-group-toggle {
  margin-left: auto;
  font-size: 11px;
  color: var(--el-text-color-secondary);
}
.http-traces-group[open] .http-group-toggle::before {
  content: '收起';
}
.http-traces-group:not([open]) .http-group-toggle::before {
  content: '展开';
}

.http-group-body {
  padding: 4px 8px 8px;
}
.http-loading, .http-load-error {
  padding: 12px;
  text-align: center;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.http-load-error {
  color: var(--el-color-danger);
}
</style>
