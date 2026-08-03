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
          <span v-else-if="entry.status === 'done'">完成 ✓</span>
          <span v-else-if="entry.status === 'error'">失败</span>
          <span v-else-if="entry.status === 'cancelled'">已取消</span>
          <span v-else-if="entry.status === 'interrupted'">已中断</span>
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
        title="进入子Agent查看详情"
        @click="$emit('enter', entry.sub_session_id, entry.name)"
      >
        ↗
      </button>
    </div>

    <!-- Body: always 200px scrollable window -->
    <div ref="bodyRef" class="sa-body">
      <!-- Thinking block (only while running) -->
      <div v-if="entry.status === 'running' && entry.thinking?.trim()" class="sa-thinking-block">
        <div class="sa-thinking-header">
          <span class="sa-thinking-icon">💭</span>
          <span>思考中...</span>
        </div>
        <div class="sa-thinking-text">{{ entry.thinking }}</div>
      </div>

      <!-- Inner tool calls (only while running) -->
      <div v-if="entry.status === 'running' && entry.innerToolCalls.length" class="sa-inner-tools">
        <div v-for="(tc, i) in entry.innerToolCalls" :key="i" class="sa-inner-tool">
          <span class="sa-inner-status" :class="tc.status">●</span>
          🔧 <span class="sa-tool-name">{{ tc.name }}</span>
          <span v-if="tc.status === 'done'" class="sa-tool-done">✓</span>
          <span v-if="tc.status === 'running'" class="sa-tool-running-dot"></span>
        </div>
      </div>

      <!-- Streaming tokens (running) -->
      <div v-if="entry.status === 'running' && entry.tokens" class="sa-tokens">
        {{ entry.tokens }}<span class="sa-cursor">▋</span>
      </div>

      <!-- Empty running state -->
      <div v-if="entry.status === 'running' && !hasContent" class="sa-empty-running">
        <span class="sa-dots"><span>.</span><span>.</span><span>.</span></span>
      </div>

      <!-- Done/Error: markdown rendered full answer -->
      <div
        v-if="entry.status !== 'running' && bodyText"
        class="sa-md-body"
        v-html="renderMarkdown(bodyText)"
      />
      <div v-if="entry.status !== 'running' && !bodyText" class="sa-empty-done">
        (无回答内容)
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { SubAgentEntry } from '@/stores/chat'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps<{
  entry: SubAgentEntry
}>()

defineEmits<{
  enter: [sub_session_id: string, name: string]
}>()

const bodyRef = ref<HTMLElement | null>(null)

const statusClass = computed(() => {
  const status = props.entry.status

  return {
    'sa-running': status === 'running',
    'sa-done': status === 'done',
    'sa-error': status === 'error',
    'sa-cancelled': status === 'cancelled',
    'sa-interrupted': status === 'interrupted',
  }
})

/** Text shown in done state: prefer full in-memory tokens, fallback to DB tokenPreview */
const bodyText = computed(() => props.entry.tokens || props.entry.tokenPreview || '')

const hasContent = computed(() =>
  !!(props.entry.thinking?.trim() || props.entry.innerToolCalls.length || props.entry.tokens),
)

function formatDuration(ms: number) {
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`
}

function scrollToBottom() {
  nextTick(() => {
    const el = bodyRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

watch(() => props.entry.tokens, scrollToBottom)
watch(() => props.entry.innerToolCalls.length, scrollToBottom)
watch(() => props.entry.thinkCount, scrollToBottom)
watch(() => props.entry.status, (newStatus) => {
  if (newStatus !== 'running') scrollToBottom()
})
</script>

<style scoped>
.subagent-card {
  position: relative;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
  margin: 6px 0;
  border-left: 3px solid var(--el-color-primary);
}
.sa-running {
  border-left-color: var(--el-color-primary);
  box-shadow: 0 0 17px color-mix(in srgb, var(--el-color-primary) 20%, transparent);
}
.sa-running::before {
  position: absolute;
  z-index: 2;
  inset: 0 auto auto -42%;
  width: 36%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--el-color-primary), transparent);
  box-shadow: 0 0 12px var(--el-color-primary);
  content: '';
  animation: subagent-energy-flow 1s linear infinite;
}
.sa-done {
  border-left-color: var(--el-color-success);
  animation: subagent-complete-glow 0.8s ease-out both;
}
.sa-done::after {
  position: absolute;
  z-index: 2;
  inset: 0 auto 0 -45%;
  width: 38%;
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--el-color-success) 32%, transparent), transparent);
  content: '';
  pointer-events: none;
  transform: skewX(-18deg);
  animation: subagent-complete-sweep 0.8s ease-out both;
}
.sa-error { border-left-color: var(--el-color-danger); }

@keyframes subagent-energy-flow {
  to { transform: translateX(430%); }
}

@keyframes subagent-complete-sweep {
  0% { transform: translateX(0) skewX(-18deg); opacity: 0; }
  18% { opacity: 1; }
  100% { transform: translateX(390%) skewX(-18deg); opacity: 0; }
}

@keyframes subagent-complete-glow {
  0% { box-shadow: 0 0 0 color-mix(in srgb, var(--el-color-success) 0%, transparent); }
  35% { box-shadow: 0 0 24px color-mix(in srgb, var(--el-color-success) 34%, transparent); }
  100% { box-shadow: 0 0 0 color-mix(in srgb, var(--el-color-success) 0%, transparent); }
}

@media (prefers-reduced-motion: reduce) {
  .sa-running::before,
  .sa-done,
  .sa-done::after {
    animation: none;
  }
}

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

/* Body: always 200px fixed scrollable window */
.sa-body {
  height: 200px;
  padding: 8px 12px;
  overflow-y: auto;
  scroll-behavior: smooth;
  box-sizing: border-box;
}

/* Thinking block */
.sa-thinking-block {
  margin-bottom: 8px;
  border: 1px solid var(--el-color-warning-light-5);
  border-radius: 4px;
  background: var(--el-color-warning-light-9);
  font-size: 11px;
}
.sa-thinking-header {
  padding: 4px 8px;
  color: var(--el-color-warning-dark-2);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}
.sa-thinking-icon { font-size: 12px; }
.sa-thinking-text {
  padding: 4px 8px 6px;
  color: var(--el-text-color-secondary);
  white-space: pre-wrap;
  overflow-wrap: break-word;
  line-height: 1.5;
}

/* Tool calls */
.sa-inner-tools {
  margin-bottom: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.sa-inner-tool {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 0;
}
.sa-tool-name { flex: 1; }
.sa-inner-status { font-size: 8px; }
.sa-inner-status.running { color: var(--el-color-warning); }
.sa-inner-status.done { color: var(--el-color-success); }
.sa-tool-done { color: var(--el-color-success); font-size: 11px; }
.sa-tool-running-dot {
  width: 6px;
  height: 6px;
  background: var(--el-color-warning);
  border-radius: 50%;
  animation: pulse 0.8s infinite;
}

/* Response tokens */
.sa-tokens {
  color: var(--el-text-color-regular);
  font-size: 12px;
  line-height: 1.7;
  white-space: pre-wrap;
  overflow-wrap: break-word;
}
.sa-cursor { animation: blink 1s step-end infinite; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

/* Done state: markdown rendered full answer */
.sa-md-body {
  font-size: 12px;
  line-height: 1.7;
  color: var(--el-text-color-regular);
  overflow-wrap: break-word;
}
.sa-md-body :deep(p) { margin: 0 0 6px; }
.sa-md-body :deep(p:last-child) { margin-bottom: 0; }
.sa-md-body :deep(h1), .sa-md-body :deep(h2), .sa-md-body :deep(h3) {
  font-size: 13px;
  font-weight: 700;
  margin: 8px 0 4px;
}
.sa-md-body :deep(code) {
  background: var(--el-fill-color-light);
  border-radius: 3px;
  padding: 1px 4px;
  font-size: 11px;
  font-family: monospace;
}
.sa-md-body :deep(pre) {
  background: var(--el-fill-color-light);
  border-radius: 4px;
  padding: 8px;
  overflow-x: auto;
  margin: 4px 0;
}
.sa-md-body :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 11px;
}
.sa-md-body :deep(ul), .sa-md-body :deep(ol) {
  margin: 4px 0;
  padding-left: 16px;
}
.sa-md-body :deep(li) { margin: 2px 0; }
.sa-md-body :deep(blockquote) {
  border-left: 3px solid var(--el-border-color);
  margin: 4px 0;
  padding: 2px 8px;
  color: var(--el-text-color-secondary);
}
.sa-empty-done {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
  padding: 8px 0;
}

/* Empty running dots animation */
.sa-empty-running {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
  padding: 8px 0;
}
.sa-dots span {
  animation: dotbounce 1.2s infinite;
  display: inline-block;
  font-size: 18px;
  line-height: 0;
}
.sa-dots span:nth-child(2) { animation-delay: 0.2s; }
.sa-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotbounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-4px); }
}
</style>
