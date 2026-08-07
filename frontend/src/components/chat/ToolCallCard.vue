<template>
  <div v-if="!isDismissed" class="tool-call-card" :class="[toolCall.status, { 'is-collapsed': isCollapsed }]">
    <div class="tool-header" @click.stop="toggleCollapse">
      <span class="collapse-icon">{{ isCollapsed ? '▸' : '▾' }}</span>
      <el-icon v-if="toolCall.status === 'running'" class="spinning">
        <Loading />
      </el-icon>
      <el-icon v-else-if="toolCall.status === 'done'" style="color: var(--el-color-success)">
        <Check />
      </el-icon>
      <el-icon v-else-if="toolCall.status === 'error'" class="error-icon">
        <CircleCloseFilled />
      </el-icon>
      <span class="tool-kind">
        <el-icon><Tools /></el-icon>
        工具调用
      </span>
      <span class="tool-name">{{ toolCall.name }}</span>
      <el-tag size="small" :type="statusType">{{ statusLabel }}</el-tag>
      <span class="tool-meta" v-if="toolCall.status === 'done'">
        <span v-if="toolCall.duration" class="meta-item">⏱ {{ formatDuration(toolCall.duration) }}</span>
        <span v-if="toolCall.resultLength" class="meta-item">📦 {{ formatSize(toolCall.resultLength) }}<template v-if="tokenCount !== null"> | {{ formatTokenCount(tokenCount) }} tokens</template></span>
      </span>
      <span v-if="toolCall.pid && !processKilled && (toolCall.bgProcessRunning || toolCall.status === 'running')" class="process-info">
        <span class="pid-badge">PID {{ toolCall.pid }}</span>
        <button class="stop-btn" title="终止进程" @click.stop="killProcess" :disabled="killing">
          {{ killing ? '...' : '■ 停止' }}
        </button>
      </span>
      <button
        v-if="toolCall.status === 'error'"
        class="dismiss-btn"
        title="关闭此错误"
        aria-label="关闭此错误"
        @click.stop="isDismissed = true"
      >✕</button>
    </div>
    <div v-if="toolCall.args && Object.keys(toolCall.args).length > 0" class="tool-args">
      <div v-for="arg in formatArgs(toolCall.name, toolCall.args)" :key="arg.key" class="arg-row">
        <span class="arg-key">{{ arg.key }}:</span>
        <span class="arg-value">{{ arg.value }}</span>
      </div>
    </div>
    <template v-if="!isCollapsed">
    <div v-if="(toolCall.status === 'running' || toolCall.bgProcessRunning) && toolCall.streamingOutput" class="tool-result streaming">
      <div class="tool-result-rendered" v-html="renderedStreamingOutput" />
      <button class="fullscreen-btn" @click.stop="showModal = true" title="查看完整内容">⛶</button>
      <div v-if="pollPaused" class="poll-paused-bar">
        <span>输出刷新已暂停（5 分钟无操作）</span>
        <button class="resume-poll-btn" @click.stop="resumeBgPolling">▶ 继续刷新</button>
      </div>
    </div>
    <div v-else-if="toolCall.fileDiff" class="tool-result diff-result">
      <div class="diff-header clickable-path" @click.stop="openFileModal(toolCall.fileDiff!.file)" title="点击查看完整文件">{{ toolCall.fileDiff.file }}</div>
      <div class="diff-body" :class="{ collapsed: diffCollapsed && diffTotalLines > 30 }">
        <div v-for="(line, i) in diffLines" :key="i" class="diff-line" :class="line.type">
          <span class="diff-linenum">{{ line.num }}</span>
          <span class="diff-prefix">{{ line.prefix }}</span>
          <span class="diff-content">{{ line.text }}</span>
        </div>
      </div>
      <button v-if="diffTotalLines > 30" class="diff-expand-btn" @click="diffCollapsed = !diffCollapsed">
        {{ diffCollapsed ? `展开全部 (${diffTotalLines} 行)` : '折叠' }}
      </button>
    </div>
    <div v-else-if="toolCall.filePreview && !toolCall.fileDiff" class="tool-result diff-result">
      <div class="diff-header clickable-path" @click.stop="openFileModal(toolCall.filePreview!.file)" title="点击查看完整文件">{{ toolCall.filePreview.file }} ({{ toolCall.filePreview.mode === 'append' ? '追加' : '写入' }})</div>
      <div class="diff-body" :class="{ collapsed: diffCollapsed && toolCall.filePreview.total_lines > 30 }">
        <div v-for="(line, i) in displayPreviewLines" :key="i" class="diff-line added">
          <span class="diff-linenum">{{ (toolCall.filePreview.start_line || 1) + i }}</span>
          <span class="diff-prefix">+</span>
          <span class="diff-content">{{ line }}</span>
        </div>
        <div v-if="hasMorePreviewLines && !previewExpanded" class="diff-line context clickable-more" @click.stop="expandPreview">
          <span class="diff-linenum"></span>
          <span class="diff-prefix"></span>
          <span class="diff-content">{{ previewLoading ? '加载中...' : `... ${toolCall.filePreview.total_lines - previewLines.length} more lines (点击展开)` }}</span>
        </div>
      </div>
    </div>
    <div v-else-if="toolCall.result" class="tool-result">
      <div class="tool-result-rendered" v-html="renderedResult" />
      <button v-if="isLong" class="fullscreen-btn" @click.stop="showModal = true" title="查看完整内容">⛶</button>
    </div>
    </template>

    <teleport to="body">
      <div v-if="showModal" class="tool-modal-backdrop" @click="showModal = false">
        <div class="tool-modal" role="dialog" aria-modal="true" @click.stop>
          <div class="tool-modal-header">
            <div class="tool-modal-title-wrap">
              <span class="tool-modal-kicker">工具结果</span>
              <span class="tool-modal-title">{{ toolCall.name }}</span>
            </div>
            <div class="modal-actions">
              <button class="tool-modal-close" aria-label="关闭" @click="showModal = false">✕</button>
            </div>
          </div>
          <div class="tool-modal-toolbar">
            <input
              v-model="searchQuery"
              class="tool-search-input"
              type="text"
              placeholder="搜索关键字..."
              @keydown.enter.prevent="jumpToNextMatch"
            />
            <div class="tool-search-actions">
              <span v-if="searchQuery" class="tool-search-count">{{ activeMatchLabel }}</span>
              <button class="tool-search-btn" :disabled="!matchCount" @click="jumpToPrevMatch">↑</button>
              <button class="tool-search-btn" :disabled="!matchCount" @click="jumpToNextMatch">↓</button>
            </div>
          </div>
          <div class="tool-modal-content">
            <div ref="modalBodyRef" class="tool-modal-body rendered" v-html="modalRenderedResult" />
          </div>
        </div>
      </div>
    </teleport>

    <CodeBlockModal
      :visible="showFileModal"
      :code="fileModalCode"
      :language="fileModalLang"
      :title="fileModalPath"
      kicker="文件内容"
      @close="showFileModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { Loading, Check, Tools, CircleCloseFilled } from '@element-plus/icons-vue'
import { AnsiUp } from 'ansi_up'
import type { ToolCall, FileDiffData, FilePreviewData } from '@/stores/chat'
import { fetchApi } from '@/api/http'
import CodeBlockModal from './CodeBlockModal.vue'

const EXT_LANG_MAP: Record<string, string> = {
  py: 'python', ts: 'typescript', tsx: 'typescript', js: 'javascript', jsx: 'javascript',
  vue: 'xml', yml: 'yaml', md: 'markdown', sh: 'bash', zsh: 'bash', ps1: 'powershell',
  rs: 'rust', rb: 'ruby', kt: 'kotlin', cs: 'csharp', h: 'c', hpp: 'cpp', cc: 'cpp',
}
function langFromPath(filePath: string): string {
  const ext = filePath.split('.').pop()?.toLowerCase() || ''
  return EXT_LANG_MAP[ext] || ext
}

// lazy-load js-tiktoken only when the first tool result arrives
let _encPromise: Promise<{ encode: (text: string) => ArrayLike<number> }> | null = null
function getTiktokenEnc() {
  if (!_encPromise) {
    _encPromise = import('js-tiktoken').then(({ getEncoding }) => getEncoding('cl100k_base'))
  }
  return _encPromise
}

const ansiUp = new AnsiUp()

const props = defineProps<{ toolCall: ToolCall; collapsed?: boolean }>()
const showModal = ref(false)
const isCollapsed = ref(props.collapsed ?? false)
const userToggled = ref(false)
const isDismissed = ref(false)
const searchQuery = ref('')
const activeMatchIndex = ref(0)
const modalBodyRef = ref<HTMLElement | null>(null)
const diffCollapsed = ref(true)

interface DiffLine {
  type: 'context' | 'removed' | 'added'
  num: string
  prefix: string
  text: string
}

const diffLines = computed<DiffLine[]>(() => {
  const diff = props.toolCall.fileDiff
  if (!diff) return []
  const lines: DiffLine[] = []
  let lineNum = diff.start_line

  for (const line of diff.context_before) {
    lines.push({ type: 'context', num: String(lineNum++), prefix: ' ', text: line })
  }
  for (const line of diff.removed) {
    lines.push({ type: 'removed', num: String(lineNum++), prefix: '-', text: line })
  }
  lineNum = diff.start_line + diff.context_before.length
  for (const line of diff.added) {
    lines.push({ type: 'added', num: String(lineNum++), prefix: '+', text: line })
  }
  for (const line of diff.context_after) {
    lines.push({ type: 'context', num: String(lineNum++), prefix: ' ', text: line })
  }
  return lines
})

const diffTotalLines = computed(() => diffLines.value.length)

const previewLines = computed<string[]>(() => {
  return props.toolCall.filePreview?.preview_lines || []
})

const previewExpanded = ref(false)
const previewExpandedLines = ref<string[]>([])
const previewLoading = ref(false)

const hasMorePreviewLines = computed(() => {
  const fp = props.toolCall.filePreview
  return fp && fp.total_lines > previewLines.value.length
})

const displayPreviewLines = computed(() => {
  return previewExpanded.value ? previewExpandedLines.value : previewLines.value
})

async function expandPreview() {
  const fp = props.toolCall.filePreview
  if (!fp || previewLoading.value) return
  previewLoading.value = true
  try {
    const data = await fetchApi<{ lines: string[]; error?: string }>(`/tools/file/read?path=${encodeURIComponent(fp.file)}&max_lines=500`)
    if (data.error) {
      console.warn('Failed to expand preview:', data.error)
      return
    }
    previewExpandedLines.value = data.lines
    previewExpanded.value = true
  } catch (e) {
    console.error('Failed to expand preview:', e)
  } finally {
    previewLoading.value = false
  }
}

const showFileModal = ref(false)
const fileModalCode = ref('')
const fileModalLang = ref('')
const fileModalPath = ref('')

async function openFileModal(filePath: string) {
  try {
    const data = await fetchApi<{ lines: string[]; truncated?: boolean; error?: string }>(
      `/tools/file/read?path=${encodeURIComponent(filePath)}&max_lines=2000`,
    )
    fileModalPath.value = filePath
    fileModalLang.value = langFromPath(filePath)
    if (data.error) {
      fileModalCode.value = `Error: ${data.error}`
      fileModalLang.value = 'text'
    } else {
      let code = data.lines.join('\n')
      if (data.truncated) code += '\n\n// … 文件过大，仅显示前 2000 行'
      fileModalCode.value = code
    }
    showFileModal.value = true
  } catch (e) {
    fileModalPath.value = filePath
    fileModalCode.value = `Failed to load file: ${e}`
    fileModalLang.value = 'text'
    showFileModal.value = true
  }
}

function toggleCollapse() {
  userToggled.value = true
  isCollapsed.value = !isCollapsed.value
}

const killing = ref(false)
const processKilled = ref(false)

async function killProcess() {
  if (!props.toolCall.pid || killing.value) return
  killing.value = true
  try {
    const res = await fetchApi<{ success: boolean }>(`/tools/process/${props.toolCall.pid}/kill`, { method: 'POST' })
    if (res.success) {
      processKilled.value = true
      stopBgPolling()
    }
  } catch (e) {
    console.error('Failed to kill process:', e)
  } finally {
    killing.value = false
  }
}

// --- Background process output polling ---
let bgPollTimer: ReturnType<typeof setInterval> | null = null
let bgPollOffset = 0
let bgPollStartTime = 0
let pollInFlight = false
const BG_POLL_DURATION_MS = 5 * 60 * 1000
const pollPaused = ref(false)

function startBgPolling() {
  if (bgPollTimer) return
  const tc = props.toolCall
  bgPollOffset = (tc.streamingOutput || '').length
  bgPollStartTime = Date.now()
  pollPaused.value = false
  bgPollTimer = setInterval(pollProcessOutput, 1000)
  pollProcessOutput()
}

function stopBgPolling() {
  if (bgPollTimer) {
    clearInterval(bgPollTimer)
    bgPollTimer = null
  }
  pollInFlight = false
  const tc = props.toolCall
  if (tc.bgProcessRunning) {
    tc.bgProcessRunning = false
    if (tc.streamingOutput) {
      tc.result = (tc.result ? tc.result + '\n' : '') + tc.streamingOutput
      tc.resultLength = tc.result.length
      delete tc.streamingOutput
    }
  }
}

function pauseBgPolling() {
  if (bgPollTimer) {
    clearInterval(bgPollTimer)
    bgPollTimer = null
  }
  pollPaused.value = true
}

function resumeBgPolling() {
  if (bgPollTimer) {
    clearInterval(bgPollTimer)
    bgPollTimer = null
  }
  bgPollStartTime = Date.now()
  pollPaused.value = false
  bgPollTimer = setInterval(pollProcessOutput, 1000)
  pollProcessOutput()
}

async function pollProcessOutput() {
  const tc = props.toolCall
  if (!tc.pid) { stopBgPolling(); return }
  if (pollInFlight) return

  if (Date.now() - bgPollStartTime > BG_POLL_DURATION_MS) {
    pauseBgPolling()
    return
  }

  pollInFlight = true
  try {
    const data = await fetchApi<{
      pid: number
      status: string
      output: string
      offset: number
    }>(`/tools/process/${tc.pid}/output?offset=${bgPollOffset}`)

    if (!tc.bgProcessRunning) return

    if (data.output) {
      tc.streamingOutput = (tc.streamingOutput || '') + data.output
      bgPollOffset = data.offset
    }

    if (!data.status.startsWith('running')) {
      stopBgPolling()
    }
  } catch {
    // Transient error — don't stop, just skip this tick
  } finally {
    pollInFlight = false
  }
}

watch(() => props.toolCall.bgProcessRunning, (val) => {
  if (val) startBgPolling()
  else stopBgPolling()
}, { immediate: true })

onBeforeUnmount(() => {
  stopBgPolling()
})

watch(() => props.collapsed, (collapsed) => {
  if (userToggled.value || collapsed === undefined) return
  isCollapsed.value = collapsed
}, { immediate: true })

const isLong = computed(() => (props.toolCall.result?.length || 0) > 300)

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function normalizeResult(value?: string): string {
  if (!value) return ''
  return value
    .replace(/\\u3000/g, '　')
    .replace(/\\n/g, '\n')
}

function renderTextToHtml(value: string): string {
  return escapeHtml(value)
    .replace(/\n/g, '<br>')
    .replace(/ {2}/g, '&nbsp;&nbsp;')
}

const isCommandTool = computed(() => props.toolCall.name.startsWith('command__'))

function renderAnsiToHtml(value: string): string {
  return ansiUp.ansi_to_html(value)
    .replace(/\n/g, '<br>')
    .replace(/ {2}/g, '&nbsp;&nbsp;')
}

const normalizedResult = computed(() => normalizeResult(props.toolCall.result))

const renderedResult = computed(() => {
  const text = normalizedResult.value
  return isCommandTool.value ? renderAnsiToHtml(text) : renderTextToHtml(text)
})

const renderedStreamingOutput = computed(() => {
  const raw = props.toolCall.streamingOutput || ''
  const tail = raw.length > 100000 ? raw.slice(-100000) : raw
  return isCommandTool.value ? renderAnsiToHtml(tail) : renderTextToHtml(tail)
})

const modalRenderedResult = computed(() => {
  const source = props.toolCall.streamingOutput || normalizedResult.value
  const query = searchQuery.value.trim()
  const base = isCommandTool.value ? renderAnsiToHtml(source) : renderTextToHtml(source)
  if (!query) return base

  const highlighted = source.replace(
    new RegExp(escapeRegExp(query), 'gi'),
    (match) => `@@HIT_START@@${match}@@HIT_END@@`,
  )

  const rendered = isCommandTool.value ? renderAnsiToHtml(highlighted) : renderTextToHtml(highlighted)
  return rendered
    .replace(/@@HIT_START@@/g, '<mark class="tool-search-hit">')
    .replace(/@@HIT_END@@/g, '</mark>')
})

const matchCount = computed(() => {
  const query = searchQuery.value.trim()
  if (!query) return 0
  const matches = normalizedResult.value.match(new RegExp(escapeRegExp(query), 'gi'))
  return matches?.length || 0
})

const activeMatchLabel = computed(() => {
  if (!matchCount.value) return '0/0'
  return `${activeMatchIndex.value + 1}/${matchCount.value}`
})

async function syncSearchHighlights() {
  await nextTick()
  const container = modalBodyRef.value
  if (!container) return
  const hits = Array.from(container.querySelectorAll('mark.tool-search-hit')) as HTMLElement[]
  hits.forEach((hit, index) => {
    hit.classList.toggle('is-active', index === activeMatchIndex.value)
  })
  if (hits.length > 0) {
    hits[activeMatchIndex.value]?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }
}

function jumpToNextMatch() {
  if (!matchCount.value) return
  activeMatchIndex.value = (activeMatchIndex.value + 1) % matchCount.value
}

function jumpToPrevMatch() {
  if (!matchCount.value) return
  activeMatchIndex.value = (activeMatchIndex.value - 1 + matchCount.value) % matchCount.value
}

watch(searchQuery, () => {
  activeMatchIndex.value = 0
  syncSearchHighlights()
})

watch(activeMatchIndex, () => {
  syncSearchHighlights()
})

watch(showModal, (visible) => {
  if (!visible) {
    searchQuery.value = ''
    activeMatchIndex.value = 0
    return
  }
  syncSearchHighlights()
})


function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function formatSize(len: number): string {
  if (len < 1024) return `${len} chars`
  return `${(len / 1024).toFixed(1)}K chars`
}

function formatArgs(name: string, args: Record<string, unknown>): { key: string; value: string }[] {
  return Object.entries(args).map(([key, value]) => {
    let formatted: string
    if (name.endsWith('ask_user') && key === 'questions' && Array.isArray(value)) {
      formatted = (value as any[]).map((q: any, idx: number) => {
        if (!q || typeof q !== 'object') return `${idx + 1}. ${String(q)}`
        const header = `${idx + 1}. ${q.question ?? '?'}`
        if (q.type === 'multiple_choice' && Array.isArray(q.choices)) {
          const choiceLines = q.choices.map((c: string, ci: number) => `  ${String.fromCharCode(65 + ci)}. ${c}`).join('\n')
          return `${header}\n${choiceLines}`
        }
        return header
      }).join('\n\n')
    } else if (typeof value === 'string') {
      formatted = value
    } else {
      try {
        formatted = JSON.stringify(value) ?? String(value)
      } catch {
        formatted = String(value)
      }
    }
    if (formatted.length > 200) formatted = `${formatted.slice(0, 200)}...`
    return { key, value: formatted }
  })
}

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

const tokenCount = ref<number | null>(null)

watch(
  [() => props.toolCall.result, () => props.toolCall.status],
  async ([result, status]) => {
    if (!result || status !== 'done' || result.length > 500_000) {
      tokenCount.value = null
      return
    }
    try {
      const enc = await getTiktokenEnc()
      tokenCount.value = enc.encode(result).length
    } catch {
      tokenCount.value = null
    }
  },
  { immediate: true }
)

function formatTokenCount(count: number): string {
  if (count < 1000) return `~${count}`
  return `~${(count / 1000).toFixed(1)}K`
}
</script>

<style scoped>
.tool-call-card {
  position: relative;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 10px 14px;
  margin: 6px 0;
  background: var(--el-fill-color-light);
  border-left: 3px solid var(--el-text-color-secondary);
  overflow: hidden;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.tool-call-card.running {
  border-left-color: var(--el-color-primary);
  box-shadow: 0 0 16px color-mix(in srgb, var(--el-color-primary) 18%, transparent);
}

.tool-call-card.running::before {
  position: absolute;
  left: -45%;
  top: 0;
  width: 45%;
  height: 100%;
  background: linear-gradient(
    to right,
    transparent 0%,
    color-mix(in srgb, var(--el-color-primary) 22%, transparent) 30%,
    color-mix(in srgb, var(--el-color-primary) 55%, transparent) 50%,
    color-mix(in srgb, var(--el-color-primary) 22%, transparent) 70%,
    transparent 100%
  );
  content: '';
  opacity: 0.65;
  animation: tool-scan 1.7s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  pointer-events: none;
  z-index: 0;
}

.tool-call-card.done {
  border-left-color: var(--el-color-success);
  animation: tool-complete-glow 0.8s ease-out both;
}

.tool-call-card.done::after {
  position: absolute;
  inset: 0 auto 0 -45%;
  width: 38%;
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--el-color-success) 32%, transparent), transparent);
  content: '';
  pointer-events: none;
  transform: skewX(-18deg);
  animation: tool-complete-sweep 0.8s ease-out both;
}

.tool-call-card.error {
  border-left-color: var(--el-color-danger);
}

.tool-header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.tool-header:hover {
  opacity: 0.85;
}

.tool-header:hover .dismiss-btn {
  opacity: 1;
}

.collapse-icon {
  font-size: 10px;
  color: var(--el-text-color-secondary);
  width: 12px;
  flex-shrink: 0;
}

.is-collapsed {
  padding: 6px 14px;
}

.tool-name {
  flex: 1 1 180px;
  min-width: 0;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
  color: var(--el-color-primary);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-kind {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 7px;
  border-radius: 999px;
  color: var(--el-text-color-regular);
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.tool-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
  flex-shrink: 0;
}

.meta-item {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.tool-args {
  position: relative;
  z-index: 1;
  margin-top: 6px;
  padding: 5px 8px;
  background: var(--el-fill-color);
  border-radius: 4px;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
}

.arg-row {
  display: flex;
  gap: 6px;
  padding: 1px 0;
  line-height: 1.5;
}

.arg-key {
  color: var(--el-color-primary);
  flex-shrink: 0;
  font-weight: 500;
}

.arg-value {
  color: var(--el-text-color-regular);
  word-break: break-all;
  white-space: pre-wrap;
}

.tool-result {
  z-index: 1;
  margin-top: 8px;
  padding: 8px 10px;
  background: #0d1117;
  border-radius: 6px;
  font-size: 12px;
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--el-border-color);
  position: relative;
}

@keyframes tool-scan {
  0% {
    left: -45%;
    opacity: 0;
  }
  12% {
    opacity: 0.65;
  }
  88% {
    opacity: 0.65;
  }
  100% {
    left: 100%;
    opacity: 0;
  }
}

@keyframes tool-complete-sweep {
  0% { transform: translateX(0) skewX(-18deg); opacity: 0; }
  18% { opacity: 1; }
  100% { transform: translateX(390%) skewX(-18deg); opacity: 0; }
}

@keyframes tool-complete-glow {
  0% { box-shadow: 0 0 0 color-mix(in srgb, var(--el-color-success) 0%, transparent); }
  35% { box-shadow: 0 0 24px color-mix(in srgb, var(--el-color-success) 34%, transparent); }
  100% { box-shadow: 0 0 0 color-mix(in srgb, var(--el-color-success) 0%, transparent); }
}

@media (prefers-reduced-motion: reduce) {
  .tool-call-card.running::before,
  .tool-call-card.done,
  .tool-call-card.done::after {
    animation: none;
  }
}

.tool-result,
.diff-body,
.tool-result :deep(pre.hljs) {
  scrollbar-width: thin;
}

.tool-result::-webkit-scrollbar,
.diff-body::-webkit-scrollbar,
.tool-result :deep(pre.hljs::-webkit-scrollbar) {
  width: 4px;
  height: 4px;
}

.tool-result::-webkit-scrollbar-thumb,
.diff-body::-webkit-scrollbar-thumb,
.tool-result :deep(pre.hljs::-webkit-scrollbar-thumb) {
  border-radius: 2px;
}

.diff-result {
  padding: 0;
  overflow: hidden;
}

.diff-header {
  padding: 6px 12px;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  color: #8b949e;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.diff-header.clickable-path {
  cursor: pointer;
  transition: color 0.15s;
}
.diff-header.clickable-path:hover {
  color: #58a6ff;
  text-decoration: underline;
}

.clickable-more {
  cursor: pointer;
  transition: background 0.15s;
}
.clickable-more:hover {
  background: rgba(88, 166, 255, 0.08);
}
.clickable-more .diff-content {
  color: #58a6ff;
}

.diff-body {
  overflow-y: auto;
  max-height: 380px;
}

.diff-body.collapsed {
  max-height: 200px;
}

.diff-line {
  display: flex;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
  line-height: 1.7;
  padding: 0 8px;
}

.diff-line.context {
  color: #8b949e;
}

.diff-line.removed {
  background: rgba(248, 81, 73, 0.1);
  color: #f85149;
}

.diff-line.added {
  background: rgba(63, 185, 80, 0.1);
  color: #3fb950;
}

.diff-linenum {
  width: 36px;
  flex-shrink: 0;
  text-align: right;
  padding-right: 8px;
  color: #484f58;
  user-select: none;
}

.diff-prefix {
  width: 14px;
  flex-shrink: 0;
  text-align: center;
  font-weight: 700;
}

.diff-content {
  flex: 1;
  min-width: 0;
  white-space: pre;
  overflow: hidden;
  text-overflow: ellipsis;
}

.diff-expand-btn {
  width: 100%;
  padding: 4px 0;
  border: none;
  border-top: 1px solid #30363d;
  background: #161b22;
  color: var(--el-color-primary);
  font-size: 11px;
  cursor: pointer;
}

.diff-expand-btn:hover {
  background: #1c2128;
}

.tool-result.streaming {
  border-color: var(--el-color-primary-light-5);
  background: #0d1117;
}

.poll-paused-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 6px 0;
  margin-top: 6px;
  border-top: 1px solid var(--el-border-color-lighter);
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.resume-poll-btn {
  padding: 3px 10px;
  font-size: 11px;
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 4px;
  background: transparent;
  color: var(--el-color-primary);
  cursor: pointer;
  transition: all 0.15s;
}

.resume-poll-btn:hover {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
}

.process-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  flex-shrink: 0;
}

.pid-badge {
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color);
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 1px 6px;
}

.stop-btn {
  font-size: 11px;
  padding: 2px 8px;
  border: 1px solid var(--el-color-danger-light-5);
  border-radius: 4px;
  background: transparent;
  color: var(--el-color-danger);
  cursor: pointer;
  transition: all 0.15s;
}

.stop-btn:hover {
  background: var(--el-color-danger-light-9);
  border-color: var(--el-color-danger);
}

.tool-result-rendered {
  margin: 0;
  white-space: normal;
  word-break: break-word;
  overflow-wrap: anywhere;
  color: #c9d1d9;
  line-height: 1.65;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
}

.fullscreen-btn {
  position: sticky;
  bottom: 0;
  float: right;
  padding: 2px 8px;
  font-size: 14px;
  color: var(--el-color-primary);
  background: var(--el-bg-color);
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.fullscreen-btn:hover {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
}

.tool-modal-backdrop {
  position: fixed;
  inset: 0;
  background: color-mix(in srgb, var(--el-bg-color-page) 70%, transparent);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.tool-modal {
  width: min(1300px, calc(100vw - 40px));
  max-height: min(92vh, 960px);
  min-height: 0;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 16px 48px color-mix(in srgb, var(--el-bg-color-page) 50%, transparent);
}

.tool-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color);
  gap: 12px;
  flex: 0 0 auto;
}

.tool-modal-title-wrap {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tool-modal-kicker {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.modal-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.modal-toggle-btn {
  padding: 4px 10px;
  font-size: 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-fill-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: all 0.15s ease;
}

.modal-toggle-btn:hover {
  background: var(--el-fill-color-light);
}

.modal-toggle-btn.active {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.tool-modal-title {
  min-width: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-modal-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 16px;
  cursor: pointer;
}

.tool-modal-close:hover {
  background: var(--el-fill-color);
  color: var(--el-text-color-primary);
}

.tool-modal-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: color-mix(in srgb, var(--el-fill-color-light) 78%, transparent);
}

.tool-search-input {
  flex: 1 1 auto;
  min-width: 0;
  height: 34px;
  padding: 0 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  outline: none;
}

.tool-search-input:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 14%, transparent);
}

.tool-search-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.tool-search-count {
  min-width: 42px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: right;
}

.tool-search-btn {
  width: 30px;
  height: 30px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
}

.tool-search-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.tool-modal-content {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}

.tool-modal-body {
  min-height: 100%;
  padding: 20px;
  margin: 0;
  font-size: 15px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
  color: var(--el-text-color-regular);
}

.tool-modal-body.rendered {
  white-space: normal;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}

.tool-modal-body :deep(.tool-search-hit),
.tool-modal-body.rendered :deep(.tool-search-hit) {
  background: rgba(250, 204, 21, 0.35);
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
}

.tool-modal-body :deep(.tool-search-hit.is-active),
.tool-modal-body.rendered :deep(.tool-search-hit.is-active) {
  background: rgba(245, 158, 11, 0.78);
}

.error-icon {
  color: var(--el-color-danger);
  flex-shrink: 0;
}

.dismiss-btn {
  margin-left: auto;
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  transition: background 0.15s, color 0.15s;
}

.dismiss-btn:hover {
  background: var(--el-color-danger-light-8);
  color: var(--el-color-danger);
}

.spinning {
  animation: spin 1s linear infinite;
  color: var(--el-color-primary);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 520px) {
  .tool-call-card {
    padding: 9px 10px;
  }

  .is-collapsed {
    padding: 7px 10px;
  }

  .tool-header {
    gap: 6px;
  }

  .tool-name {
    flex-basis: 100%;
    order: 10;
    padding-left: 24px;
    max-width: 100%;
  }

  .tool-meta {
    margin-left: 0;
    gap: 7px;
  }

  .tool-modal-backdrop {
    align-items: stretch;
    justify-content: stretch;
    padding: max(8px, env(safe-area-inset-top)) max(8px, env(safe-area-inset-right)) max(8px, env(safe-area-inset-bottom)) max(8px, env(safe-area-inset-left));
    background: color-mix(in srgb, var(--el-bg-color-page) 88%, transparent);
  }

  .tool-modal {
    width: 100%;
    max-height: none;
    height: 100%;
    border-radius: 12px;
    min-width: 0;
  }

  .tool-modal-header {
    position: sticky;
    top: 0;
    z-index: 1;
    padding: 10px 10px 9px;
    background: var(--el-bg-color);
    gap: 8px;
  }

  .tool-modal-title-wrap {
    flex: 1 1 auto;
  }

  .tool-modal-title {
    font-size: 12px;
  }

  .tool-modal-kicker {
    display: none;
  }

  .modal-actions {
    gap: 6px;
  }

  .modal-toggle-btn {
    padding: 5px 8px;
    font-size: 12px;
    white-space: nowrap;
  }

  .tool-modal-close {
    width: 34px;
    height: 34px;
    font-size: 18px;
  }

  .tool-modal-toolbar {
    padding: 8px 10px;
    gap: 8px;
    flex-wrap: wrap;
  }

  .tool-search-input {
    width: 100%;
    height: 36px;
  }

  .tool-search-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .tool-search-count {
    margin-right: auto;
    text-align: left;
  }

  .tool-modal-content {
    flex: 1 1 auto;
  }

  .tool-modal-body {
    padding: 12px 10px 18px;
    font-size: 12px;
    line-height: 1.65;
  }
}
</style>
