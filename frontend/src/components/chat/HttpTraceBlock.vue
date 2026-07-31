<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { HttpTrace, LlmRoundUsage } from '@/stores/chat'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps<{
  trace: HttpTrace
  usageRound?: LlmRoundUsage
}>()

const isSuccess = computed(() => props.trace.response.ok === true)
const isError = computed(() => Boolean(props.trace.error) || props.trace.response.ok === false)
const tagType = computed(() => (isError.value ? 'danger' : isSuccess.value ? 'success' : 'info'))

const statusText = computed(() => {
  if (props.trace.error) return '失败'
  const status = props.trace.response.status
  return status != null ? String(status) : '未返回'
})

const durationText = computed(() => {
  const ms = props.trace.durationMs
  if (ms == null) return '-'
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
})

const urlText = computed(() => props.trace.request.url || props.trace.model || '未采集')

function fmtTokens(n: number | undefined): string {
  if (n == null || n === 0) return ''
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

const tokenStats = computed(() => {
  const u = props.usageRound
  if (!u) return null
  const parts: { label: string; value: string; cls: string }[] = []
  if (u.inputTokens) parts.push({ label: '输入', value: fmtTokens(u.inputTokens), cls: 'tok-input' })
  if (u.cacheReadTokens) parts.push({ label: '缓存', value: fmtTokens(u.cacheReadTokens), cls: 'tok-cache' })
  if (u.outputTokens) parts.push({ label: '输出', value: fmtTokens(u.outputTokens), cls: 'tok-output' })
  if (u.reasoningTokens) parts.push({ label: '推理', value: fmtTokens(u.reasoningTokens), cls: 'tok-reason' })
  return parts.length > 0 ? parts : null
})

function formatBody(body: string | undefined) {
  if (!body) return '空'
  try {
    return JSON.stringify(JSON.parse(body), null, 2)
  } catch {
    return body
  }
}

const copiedField = ref<string | null>(null)
let copyTimer: ReturnType<typeof setTimeout> | undefined

async function copyField(fieldKey: string, text: string) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.setAttribute('readonly', 'true')
      textarea.style.position = 'fixed'
      textarea.style.left = '-9999px'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    copiedField.value = fieldKey
    clearTimeout(copyTimer)
    copyTimer = setTimeout(() => { copiedField.value = null }, 1400)
  } catch { /* silent */ }
}

const showModal = ref(false)
const modalTitle = ref('')
const modalContent = ref('')
const searchQuery = ref('')
const activeMatchIndex = ref(0)
const modalBodyRef = ref<HTMLElement | null>(null)

function openBodyModal(title: string, body: string) {
  modalTitle.value = title
  modalContent.value = formatBody(body)
  showModal.value = true
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function renderTextToHtml(value: string): string {
  return escapeHtml(value)
    .replace(/\n/g, '<br>')
    .replace(/ {2}/g, '&nbsp;&nbsp;')
}

const modalRenderedResult = computed(() => {
  const query = searchQuery.value.trim()
  if (!query) return renderTextToHtml(modalContent.value)

  const highlighted = modalContent.value.replace(
    new RegExp(escapeRegExp(query), 'gi'),
    (match) => `@@HIT_START@@${match}@@HIT_END@@`,
  )

  return renderTextToHtml(highlighted)
    .replace(/@@HIT_START@@/g, '<mark class="http-search-hit">')
    .replace(/@@HIT_END@@/g, '</mark>')
})

const matchCount = computed(() => {
  const query = searchQuery.value.trim()
  if (!query) return 0
  const matches = modalContent.value.match(new RegExp(escapeRegExp(query), 'gi'))
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
  const hits = Array.from(container.querySelectorAll('mark.http-search-hit')) as HTMLElement[]
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

const isReqBodyLong = computed(() => (props.trace.request.body?.length || 0) > 300)
const isRespBodyLong = computed(() => (props.trace.response.body?.length || 0) > 300)

// ===== Request Analysis =====
interface SystemBlock { index: number; chars: number; preview: string; fullText: string }
interface ToolEntry { name: string; description: string; fullDescription: string }
interface AnalyzeResult {
  messageCounts: { total: number; system: number; user: number; assistant: number; tool: number }
  systemBlocks: SystemBlock[]
  tools: ToolEntry[]
}

const showAnalyzeModal = ref(false)
const analyzeResult = ref<AnalyzeResult | null>(null)
const analyzeBlockViews = ref<Record<number, 'md' | 'raw'>>({})
const analyzeToolViews = ref<Record<number, 'md' | 'raw'>>({})
const analyzeErrorMsg = ref('')

watch(showAnalyzeModal, (visible) => {
  if (!visible) {
    analyzeResult.value = null
    analyzeBlockViews.value = {}
    analyzeToolViews.value = {}
    analyzeErrorMsg.value = ''
  }
})

function analyzeRequest() {
  let parsed: any
  try {
    parsed = JSON.parse(props.trace.request.body || '{}')
  } catch {
    analyzeErrorMsg.value = '请求体不是有效 JSON，无法解析。'
    analyzeResult.value = null
    showAnalyzeModal.value = true
    return
  }

  // P1-G: structural validation — must look like an LLM API call
  if (!Array.isArray(parsed.messages) && typeof parsed.system !== 'string' && !Array.isArray(parsed.tools)) {
    analyzeErrorMsg.value = '未找到 messages / system / tools 字段，可能不是标准 LLM 调用格式。'
    analyzeResult.value = null
    showAnalyzeModal.value = true
    return
  }

  const messages: any[] = Array.isArray(parsed.messages) ? parsed.messages : []
  const tools: any[] = Array.isArray(parsed.tools) ? parsed.tools : []

  const messageCounts = {
    total: messages.length,
    system: messages.filter((m: any) => m.role === 'system' || m.role === 'developer').length,
    user: messages.filter((m: any) => m.role === 'user').length,
    assistant: messages.filter((m: any) => m.role === 'assistant').length,
    tool: messages.filter((m: any) => m.role === 'tool').length,
  }

  // P2-D: also handle top-level `system` string (Anthropic format)
  // P2-C: include `developer` role alongside `system`
  // P1-A: filter blocks with missing/invalid text field
  const rawBlocks: string[] = [
    ...(typeof parsed.system === 'string' ? [parsed.system] : []),
    ...messages
      .filter((m: any) => m.role === 'system' || m.role === 'developer')
      .flatMap((m: any) => {
        if (typeof m.content === 'string') return [m.content]
        if (Array.isArray(m.content)) {
          return (m.content as any[])
            .filter(b => b?.type === 'text' && typeof b.text === 'string')
            .map((b: any) => b.text as string)
        }
        return []
      }),
  ]

  const systemBlocks: SystemBlock[] = rawBlocks.map((text, i) => ({
    index: i,
    chars: text.length,
    preview: text.slice(0, 160).replace(/\n/g, ' ').trim(),
    fullText: text,
  }))

  const toolEntries: ToolEntry[] = tools.map((t: any) => {
      const full = t.function?.description ?? t.description ?? ''
      return {
        name: t.function?.name ?? t.name ?? '(unnamed)',
        description: full.split('\n')[0].slice(0, 120),
        fullDescription: full,
      }
    })

  analyzeErrorMsg.value = ''
  analyzeResult.value = { messageCounts, systemBlocks, tools: toolEntries }
  analyzeBlockViews.value = {}
  analyzeToolViews.value = {}
  showAnalyzeModal.value = true
}

function setBlockView(i: number, mode: 'md' | 'raw') {
  if (analyzeBlockViews.value[i] === mode) {
    const next = { ...analyzeBlockViews.value }
    delete next[i]
    analyzeBlockViews.value = next
  } else {
    analyzeBlockViews.value = { ...analyzeBlockViews.value, [i]: mode }
  }
}

function setToolView(i: number, mode: 'md' | 'raw') {
  if (analyzeToolViews.value[i] === mode) {
    const next = { ...analyzeToolViews.value }
    delete next[i]
    analyzeToolViews.value = next
  } else {
    analyzeToolViews.value = { ...analyzeToolViews.value, [i]: mode }
  }
}

function estimateTokens(chars: number): string {
  const t = Math.round(chars / 4)
  return t >= 1000 ? `~${(t / 1000).toFixed(1)}k` : `~${t}`
}
</script>

<template>
  <details class="http-trace-block" :class="{ 'is-error': isError }">
    <summary class="http-summary">
      <span class="http-summary-icon">🌐</span>
      <span class="http-summary-title">HTTP 交互 #{{ trace.sequence }}</span>
      <el-tag size="small" :type="tagType" class="http-summary-tag">
        {{ trace.request.method || 'HTTP' }}
      </el-tag>
      <el-tag size="small" :type="tagType" class="http-summary-tag">
        {{ statusText }}
      </el-tag>
      <span class="http-summary-duration">{{ durationText }}</span>
      <span v-if="tokenStats" class="http-token-stats">
        <span v-for="stat in tokenStats" :key="stat.label" class="http-token-item" :class="stat.cls">
          {{ stat.label }} {{ stat.value }}
        </span>
      </span>
      <button v-if="trace.request.body" class="http-analyze-inline-btn" title="分析提示词 & 工具" @click.stop="analyzeRequest()">🔍 分析</button>
      <span class="http-summary-toggle" />
    </summary>

    <div class="http-body">
      <div class="http-row">
        <span class="http-label">URL</span>
        <div class="http-field-row">
          <code class="http-url">{{ urlText }}</code>
          <button class="http-copy-btn" @click.stop="copyField('url', urlText)" :title="copiedField === 'url' ? '已复制' : '复制'">
            {{ copiedField === 'url' ? '✓' : '📋' }}
          </button>
        </div>
      </div>
      <div v-if="trace.provider || trace.model" class="http-row">
        <span class="http-label">模型</span>
        <div class="http-field-row">
          <code>{{ [trace.provider, trace.model].filter(Boolean).join(' / ') }}</code>
          <button class="http-copy-btn" @click.stop="copyField('model', [trace.provider, trace.model].filter(Boolean).join(' / '))" :title="copiedField === 'model' ? '已复制' : '复制'">
            {{ copiedField === 'model' ? '✓' : '📋' }}
          </button>
        </div>
      </div>

      <details class="http-section">
        <summary class="http-section-title">
          <span>Request Headers</span>
          <button class="http-copy-btn" @click.stop="copyField('req-h', formatBody(JSON.stringify(trace.request.headers || {}, null, 2)))">
            {{ copiedField === 'req-h' ? '✓' : '📋' }}
          </button>
        </summary>
        <pre class="http-code">{{ formatBody(JSON.stringify(trace.request.headers || {}, null, 2)) }}</pre>
      </details>
      <details class="http-section">
        <summary class="http-section-title">
          <span>Request Body</span>
          <span class="http-section-actions">
            <button v-if="isReqBodyLong" class="http-expand-btn" @click.stop="openBodyModal('Request Body', trace.request.body)" title="全屏查看">⛶</button>
            <button class="http-copy-btn" @click.stop="copyField('req-b', formatBody(trace.request.body))">
              {{ copiedField === 'req-b' ? '✓' : '📋' }}
            </button>
          </span>
        </summary>
        <pre class="http-code">{{ formatBody(trace.request.body) }}</pre>
      </details>
      <details class="http-section">
        <summary class="http-section-title">
          <span>Response Headers</span>
          <button class="http-copy-btn" @click.stop="copyField('resp-h', formatBody(JSON.stringify(trace.response.headers || {}, null, 2)))">
            {{ copiedField === 'resp-h' ? '✓' : '📋' }}
          </button>
        </summary>
        <pre class="http-code">{{ formatBody(JSON.stringify(trace.response.headers || {}, null, 2)) }}</pre>
      </details>
      <details class="http-section">
        <summary class="http-section-title">
          <span>Response Body</span>
          <span class="http-section-actions">
            <button v-if="isRespBodyLong" class="http-expand-btn" @click.stop="openBodyModal('Response Body', trace.response.body)" title="全屏查看">⛶</button>
            <button class="http-copy-btn" @click.stop="copyField('resp-b', formatBody(trace.response.body))">
              {{ copiedField === 'resp-b' ? '✓' : '📋' }}
            </button>
          </span>
        </summary>
        <pre class="http-code">{{ formatBody(trace.response.body) }}</pre>
      </details>
      <div v-if="trace.error" class="http-error">请求失败：{{ trace.error }}</div>
    </div>
  </details>

  <teleport to="body">
    <div v-if="showAnalyzeModal" class="http-modal-backdrop" @click="showAnalyzeModal = false">
      <div class="http-modal" role="dialog" aria-modal="true" @click.stop>
        <div class="http-modal-header">
          <div class="http-modal-title-wrap">
            <span class="http-modal-kicker">HTTP #{{ trace.sequence }}</span>
            <span class="http-modal-title">提示词 & 工具分析</span>
          </div>
          <button class="http-modal-close" aria-label="关闭" @click="showAnalyzeModal = false">✕</button>
        </div>
        <div class="http-modal-content">
          <div v-if="!analyzeResult" class="analyze-error">
            <span class="analyze-error-icon">⚠️</span>
            {{ analyzeErrorMsg || '解析失败' }}
          </div>
          <template v-else>
            <!-- Message counts -->
            <div class="analyze-section analyze-section--stats">
              <div class="analyze-section-label">MESSAGES</div>
              <div class="analyze-stat-row">
                <div class="analyze-stat-card analyze-stat-total">
                  <span class="analyze-stat-num">{{ analyzeResult.messageCounts.total }}</span>
                  <span class="analyze-stat-name">total</span>
                </div>
                <div class="analyze-stat-divider" />
                <div v-if="analyzeResult.messageCounts.system" class="analyze-stat-card analyze-stat-system">
                  <span class="analyze-stat-num">{{ analyzeResult.messageCounts.system }}</span>
                  <span class="analyze-stat-name">system</span>
                </div>
                <div v-if="analyzeResult.messageCounts.user" class="analyze-stat-card analyze-stat-user">
                  <span class="analyze-stat-num">{{ analyzeResult.messageCounts.user }}</span>
                  <span class="analyze-stat-name">user</span>
                </div>
                <div v-if="analyzeResult.messageCounts.assistant" class="analyze-stat-card analyze-stat-assistant">
                  <span class="analyze-stat-num">{{ analyzeResult.messageCounts.assistant }}</span>
                  <span class="analyze-stat-name">assistant</span>
                </div>
                <div v-if="analyzeResult.messageCounts.tool" class="analyze-stat-card analyze-stat-tool">
                  <span class="analyze-stat-num">{{ analyzeResult.messageCounts.tool }}</span>
                  <span class="analyze-stat-name">tool</span>
                </div>
              </div>
            </div>

            <!-- System prompt blocks -->
            <div class="analyze-section">
              <div class="analyze-section-label">
                SYSTEM PROMPT
                <span class="analyze-section-badge">{{ analyzeResult.systemBlocks.length }} blocks</span>
              </div>
              <div v-if="analyzeResult.systemBlocks.length === 0" class="analyze-empty">无系统提示词</div>
              <div v-for="block in analyzeResult.systemBlocks" :key="block.index" class="analyze-block" :class="{ 'is-open': analyzeBlockViews[block.index] }">
                <div class="analyze-block-header">
                  <span class="analyze-block-index">#{{ block.index + 1 }}</span>
                  <div class="analyze-block-meta">
                    <span class="analyze-block-chars">{{ block.chars.toLocaleString() }} chars</span>
                    <span class="analyze-block-sep">·</span>
                    <span class="analyze-block-tokens">{{ estimateTokens(block.chars) }} tokens</span>
                  </div>
                  <div class="analyze-block-actions">
                    <div class="analyze-seg-ctrl">
                      <button type="button" class="analyze-seg-opt" :class="{ active: analyzeBlockViews[block.index] === 'md' }" @click="setBlockView(block.index, 'md')">MD</button>
                      <button type="button" class="analyze-seg-opt" :class="{ active: analyzeBlockViews[block.index] === 'raw' }" @click="setBlockView(block.index, 'raw')">原始</button>
                    </div>
                    <button type="button" class="analyze-copy-btn" :title="copiedField === `block-${block.index}` ? '已复制' : '复制'" @click="copyField(`block-${block.index}`, block.fullText)">{{ copiedField === `block-${block.index}` ? '✓' : '📋' }}</button>
                  </div>
                </div>
                <div v-if="!analyzeBlockViews[block.index]" class="analyze-block-preview">{{ block.preview }}{{ block.chars > 160 ? '…' : '' }}</div>
                <div v-else-if="analyzeBlockViews[block.index] === 'md'" class="analyze-block-rendered markdown-body" v-html="renderMarkdown(block.fullText)" />
                <pre v-else class="analyze-block-full">{{ block.fullText }}</pre>
              </div>
            </div>

            <!-- Tools -->
            <div class="analyze-section">
              <div class="analyze-section-label">
                TOOLS
                <span class="analyze-section-badge">{{ analyzeResult.tools.length }}</span>
              </div>
              <div v-if="analyzeResult.tools.length === 0" class="analyze-empty">无 Tools</div>
              <div v-for="(tool, i) in analyzeResult.tools" :key="i" class="analyze-block analyze-block--tool" :class="{ 'is-open': analyzeToolViews[i] }">
                <div class="analyze-block-header">
                  <code class="analyze-tool-name">{{ tool.name }}</code>
                  <div class="analyze-block-actions">
                    <div class="analyze-seg-ctrl">
                      <button type="button" class="analyze-seg-opt" :class="{ active: analyzeToolViews[i] === 'md' }" @click="setToolView(i, 'md')">MD</button>
                      <button type="button" class="analyze-seg-opt" :class="{ active: analyzeToolViews[i] === 'raw' }" @click="setToolView(i, 'raw')">原始</button>
                    </div>
                    <button type="button" class="analyze-copy-btn" :title="copiedField === `tool-${i}` ? '已复制' : '复制'" @click="copyField(`tool-${i}`, tool.fullDescription)">{{ copiedField === `tool-${i}` ? '✓' : '📋' }}</button>
                  </div>
                </div>
                <div v-if="!analyzeToolViews[i] && tool.description" class="analyze-block-preview">{{ tool.description }}{{ tool.fullDescription.length > 120 || tool.fullDescription.includes('\n') ? '…' : '' }}</div>
                <div v-else-if="analyzeToolViews[i] === 'md'" class="analyze-block-rendered markdown-body" v-html="renderMarkdown(tool.fullDescription)" />
                <pre v-else-if="analyzeToolViews[i] === 'raw'" class="analyze-block-full">{{ tool.fullDescription }}</pre>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </teleport>

  <teleport to="body">
    <div v-if="showModal" class="http-modal-backdrop" @click="showModal = false">
      <div class="http-modal" role="dialog" aria-modal="true" @click.stop>
        <div class="http-modal-header">
          <div class="http-modal-title-wrap">
            <span class="http-modal-kicker">HTTP #{{ trace.sequence }}</span>
            <span class="http-modal-title">{{ modalTitle }}</span>
          </div>
          <div class="http-modal-actions">
            <button class="http-copy-btn-lg" @click="copyField('modal', modalContent)">
              {{ copiedField === 'modal' ? '已复制 ✓' : '复制全部' }}
            </button>
            <button class="http-modal-close" aria-label="关闭" @click="showModal = false">✕</button>
          </div>
        </div>
        <div class="http-modal-toolbar">
          <input
            v-model="searchQuery"
            class="http-search-input"
            type="text"
            placeholder="搜索关键字..."
            @keydown.enter.prevent="jumpToNextMatch"
          />
          <div class="http-search-actions">
            <span v-if="searchQuery" class="http-search-count">{{ activeMatchLabel }}</span>
            <button class="http-search-btn" :disabled="!matchCount" @click="jumpToPrevMatch">↑</button>
            <button class="http-search-btn" :disabled="!matchCount" @click="jumpToNextMatch">↓</button>
          </div>
        </div>
        <div class="http-modal-content">
          <div ref="modalBodyRef" class="http-modal-body" v-html="modalRenderedResult" />
        </div>
      </div>
    </div>
  </teleport>
</template>

<style scoped>
.http-trace-block {
  margin: 8px 0;
  border: 1px solid var(--el-border-color-lighter);
  border-left: 3px solid var(--el-color-primary);
  border-radius: 8px;
  background: var(--el-fill-color-light);
  overflow: hidden;
}
.http-trace-block.is-error {
  border-left-color: var(--el-color-danger);
}

.http-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  cursor: pointer;
  user-select: none;
  font-size: 12px;
  color: var(--el-text-color-regular);
}
.http-summary::-webkit-details-marker {
  display: none;
}
.http-summary-icon {
  font-size: 13px;
}
.http-summary-title {
  font-weight: 600;
  white-space: nowrap;
}
.http-summary-tag {
  flex-shrink: 0;
}
.http-summary-duration {
  color: var(--el-text-color-secondary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.http-token-stats {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: 4px;
}
.http-token-item {
  font-size: 11px;
  padding: 0 5px;
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  white-space: nowrap;
}
.tok-input {
  color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
}
.tok-cache {
  color: var(--el-color-success);
  background: color-mix(in srgb, var(--el-color-success) 10%, transparent);
}
.tok-output {
  color: #c58f22;
  background: color-mix(in srgb, #c58f22 10%, transparent);
}
.tok-reason {
  color: var(--el-color-warning);
  background: color-mix(in srgb, var(--el-color-warning) 10%, transparent);
}
.http-summary-toggle {
  margin-left: auto;
  color: var(--el-text-color-secondary);
  font-size: 11px;
}
.http-trace-block[open] .http-summary-toggle::before {
  content: '收起';
}
.http-trace-block:not([open]) .http-summary-toggle::before {
  content: '展开';
}

.http-body {
  padding: 4px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.http-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
}
.http-label {
  color: var(--el-text-color-secondary);
  font-size: 11px;
}
.http-field-row {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}
.http-field-row code {
  flex: 1;
  min-width: 0;
}
.http-url {
  word-break: break-all;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.http-section {
  border-top: 1px solid var(--el-border-color-lighter);
  padding-top: 6px;
}
.http-section-title {
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-regular);
  padding: 2px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}
.http-section-actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
}
.http-copy-btn {
  flex-shrink: 0;
  padding: 1px 4px;
  font-size: 11px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  color: var(--el-text-color-secondary);
  opacity: 0.6;
  transition: all 0.15s ease;
}
.http-copy-btn:hover {
  opacity: 1;
  border-color: var(--el-border-color);
  background: var(--el-fill-color);
}
.http-expand-btn {
  flex-shrink: 0;
  padding: 1px 6px;
  font-size: 13px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  color: var(--el-color-primary);
  opacity: 0.7;
  transition: all 0.15s ease;
}
.http-expand-btn:hover {
  opacity: 1;
  border-color: var(--el-color-primary-light-5);
  background: var(--el-color-primary-light-9);
}
.http-code {
  margin: 4px 0 0;
  padding: 8px;
  border-radius: 6px;
  background: var(--el-fill-color);
  max-height: 220px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
}
.http-error {
  color: var(--el-color-danger);
  font-size: 12px;
  padding: 6px 8px;
  background: color-mix(in srgb, var(--el-color-danger) 10%, transparent);
  border-radius: 6px;
}

/* Analyze inline button in summary row */
.http-analyze-inline-btn {
  flex-shrink: 0;
  padding: 2px 7px;
  font-size: 11px;
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 5px;
  background: color-mix(in srgb, var(--el-color-primary) 7%, transparent);
  color: var(--el-color-primary);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
  line-height: 1.4;
}
.http-analyze-inline-btn:hover {
  background: color-mix(in srgb, var(--el-color-primary) 14%, transparent);
  border-color: var(--el-color-primary-light-3);
}

/* ===== Analyze Modal ===== */
.analyze-error {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 24px 20px;
  color: var(--el-color-danger);
  font-size: 13px;
}
.analyze-error-icon { font-size: 18px; flex-shrink: 0; }

/* Sections */
.analyze-section {
  padding: 14px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.analyze-section:last-child { border-bottom: none; }

.analyze-section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--el-text-color-placeholder);
  margin-bottom: 10px;
}
.analyze-section-badge {
  padding: 1px 6px;
  border-radius: 10px;
  background: var(--el-fill-color-dark);
  color: var(--el-text-color-secondary);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: none;
}

/* Stats row (Messages section) */
.analyze-section--stats { padding-bottom: 16px; }
.analyze-stat-row {
  display: flex;
  align-items: center;
  gap: 0;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  overflow: hidden;
}
.analyze-stat-divider {
  width: 1px;
  align-self: stretch;
  background: var(--el-border-color-lighter);
  flex-shrink: 0;
  margin: 8px 0;
}
.analyze-stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 16px;
  gap: 2px;
  flex: 1;
  min-width: 0;
  transition: background 0.15s;
}
.analyze-stat-card:not(.analyze-stat-total):hover { background: var(--el-fill-color); }
.analyze-stat-num {
  font-size: 20px;
  font-weight: 800;
  line-height: 1;
  font-family: ui-monospace, Consolas, monospace;
}
.analyze-stat-name {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.7;
}
.analyze-stat-total .analyze-stat-num { color: var(--el-text-color-primary); }
.analyze-stat-total .analyze-stat-name { color: var(--el-text-color-secondary); }
.analyze-stat-system .analyze-stat-num { color: var(--el-color-primary); }
.analyze-stat-system .analyze-stat-name { color: var(--el-color-primary-light-3); }
.analyze-stat-user .analyze-stat-num { color: var(--el-color-success); }
.analyze-stat-user .analyze-stat-name { color: var(--el-color-success-light-3); }
.analyze-stat-assistant .analyze-stat-num { color: #c58f22; }
.analyze-stat-assistant .analyze-stat-name { color: #d9a83c; }
.analyze-stat-tool .analyze-stat-num { color: var(--el-color-warning-dark-2); }
.analyze-stat-tool .analyze-stat-name { color: var(--el-color-warning); }

/* Block items */
.analyze-block {
  margin-bottom: 6px;
  border: 1px solid var(--el-border-color-lighter);
  border-left: 3px solid var(--el-border-color-light);
  border-radius: 7px;
  overflow: hidden;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.analyze-block:last-child { margin-bottom: 0; }
.analyze-block:hover { border-left-color: var(--el-color-primary-light-5); }
.analyze-block.is-open {
  border-left-color: var(--el-color-primary);
  box-shadow: 0 2px 8px color-mix(in srgb, var(--el-color-primary) 8%, transparent);
}
.analyze-block--tool .analyze-block-header { background: color-mix(in srgb, var(--el-fill-color-light) 80%, var(--el-bg-color) 20%); }

.analyze-block-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px 7px 12px;
  background: var(--el-fill-color-light);
}
.analyze-block-index {
  font-size: 10px;
  font-weight: 800;
  color: var(--el-color-primary);
  font-family: ui-monospace, Consolas, monospace;
  flex-shrink: 0;
  opacity: 0.8;
}
.analyze-block-meta {
  display: flex;
  align-items: center;
  gap: 5px;
  flex: 1;
  min-width: 0;
}
.analyze-block-chars {
  font-size: 11px;
  color: var(--el-text-color-regular);
  font-family: ui-monospace, Consolas, monospace;
  font-weight: 600;
}
.analyze-block-sep {
  font-size: 10px;
  color: var(--el-text-color-placeholder);
}
.analyze-block-tokens {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  font-family: ui-monospace, Consolas, monospace;
}
.analyze-block-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

/* Segmented control */
.analyze-seg-ctrl {
  display: inline-flex;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  overflow: hidden;
  background: var(--el-bg-color);
}
.analyze-seg-opt {
  padding: 2px 9px;
  font-size: 11px;
  font-weight: 600;
  border: none;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  transition: all 0.12s ease;
  line-height: 1.6;
  white-space: nowrap;
}
.analyze-seg-opt:first-child { border-right: 1px solid var(--el-border-color-lighter); }
.analyze-seg-opt:hover:not(.active) { background: var(--el-fill-color-light); color: var(--el-text-color-regular); }
.analyze-seg-opt.active { background: var(--el-color-primary); color: #fff; }

.analyze-copy-btn {
  flex-shrink: 0;
  padding: 2px 6px;
  font-size: 11px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  color: var(--el-text-color-placeholder);
  transition: all 0.15s ease;
}
.analyze-copy-btn:hover {
  color: var(--el-text-color-secondary);
  border-color: var(--el-border-color);
  background: var(--el-fill-color);
}

/* Block content areas */
.analyze-block-preview {
  padding: 7px 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: ui-monospace, Consolas, monospace;
  border-top: 1px solid var(--el-border-color-extra-light);
}
.analyze-block-full {
  margin: 0;
  padding: 10px 12px;
  font-size: 12px;
  line-height: 1.65;
  max-height: 320px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, Consolas, monospace;
  background: var(--el-fill-color);
  border-top: 1px solid var(--el-border-color-lighter);
}
.analyze-block-rendered {
  padding: 12px 14px;
  font-size: 13px;
  line-height: 1.65;
  max-height: 400px;
  overflow: auto;
  background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-lighter);
}
.analyze-block-rendered :deep(p) { margin: 0 0 8px; }
.analyze-block-rendered :deep(pre) { max-height: 200px; overflow: auto; }
.analyze-block-rendered :deep(code) { font-size: 12px; }
.analyze-block-rendered :deep(h1), .analyze-block-rendered :deep(h2),
.analyze-block-rendered :deep(h3), .analyze-block-rendered :deep(h4) { margin: 10px 0 6px; }

.analyze-empty {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  padding: 4px 0;
  font-style: italic;
}
.analyze-tool-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--el-color-primary);
  font-family: ui-monospace, Consolas, monospace;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Modal */
.http-modal-backdrop {
  position: fixed;
  inset: 0;
  background: color-mix(in srgb, var(--el-bg-color-page) 70%, transparent);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}
.http-modal {
  width: min(900px, calc(100vw - 80px));
  max-height: min(80vh, 760px);
  min-height: 0;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 16px 48px color-mix(in srgb, var(--el-bg-color-page) 50%, transparent);
}
.http-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color);
  gap: 12px;
  flex: 0 0 auto;
}
.http-modal-title-wrap {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.http-modal-kicker {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}
.http-modal-title {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-primary);
}
.http-modal-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.http-copy-btn-lg {
  padding: 4px 10px;
  font-size: 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-fill-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: all 0.15s ease;
}
.http-copy-btn-lg:hover {
  background: var(--el-fill-color-light);
  border-color: var(--el-color-primary-light-5);
}
.http-modal-close {
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
.http-modal-close:hover {
  background: var(--el-fill-color);
  color: var(--el-text-color-primary);
}
.http-modal-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: color-mix(in srgb, var(--el-fill-color-light) 78%, transparent);
}
.http-search-input {
  flex: 1 1 auto;
  min-width: 0;
  height: 34px;
  padding: 0 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  outline: none;
  font-size: 13px;
}
.http-search-input:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 14%, transparent);
}
.http-search-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.http-search-count {
  min-width: 42px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: right;
}
.http-search-btn {
  width: 30px;
  height: 30px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
}
.http-search-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.http-modal-content {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}
.http-modal-body {
  min-height: 100%;
  padding: 16px;
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
  color: var(--el-text-color-regular);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.http-modal-body :deep(.http-search-hit) {
  background: rgba(250, 204, 21, 0.35);
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
}
.http-modal-body :deep(.http-search-hit.is-active) {
  background: rgba(245, 158, 11, 0.78);
}

@media (max-width: 520px) {
  .http-summary {
    flex-wrap: wrap;
    gap: 4px 6px;
    padding: 8px 10px;
  }
  .http-summary-title {
    white-space: nowrap;
  }
  .http-summary-toggle {
    order: 10;
  }
  .http-token-stats {
    width: 100%;
    margin-left: 0;
    margin-top: 2px;
    flex-wrap: wrap;
  }
}

@media (max-width: 520px) {
  .http-modal-backdrop {
    align-items: stretch;
    justify-content: stretch;
    padding: max(8px, env(safe-area-inset-top)) max(8px, env(safe-area-inset-right)) max(8px, env(safe-area-inset-bottom)) max(8px, env(safe-area-inset-left));
    background: color-mix(in srgb, var(--el-bg-color-page) 88%, transparent);
  }
  .http-modal {
    width: 100%;
    max-height: none;
    height: 100%;
    border-radius: 12px;
    min-width: 0;
  }
  .http-modal-header {
    position: sticky;
    top: 0;
    z-index: 1;
    padding: 10px;
    background: var(--el-bg-color);
    gap: 8px;
  }
  .http-modal-kicker {
    display: none;
  }
  .http-modal-title {
    font-size: 12px;
  }
  .http-modal-close {
    width: 34px;
    height: 34px;
    font-size: 18px;
  }
  .http-modal-toolbar {
    padding: 8px 10px;
    gap: 8px;
    flex-wrap: wrap;
  }
  .http-search-input {
    width: 100%;
    height: 36px;
  }
  .http-search-actions {
    width: 100%;
    justify-content: flex-end;
  }
  .http-search-count {
    margin-right: auto;
    text-align: left;
  }
  .http-modal-body {
    padding: 12px 10px 18px;
    font-size: 12px;
    line-height: 1.65;
  }
}
</style>
