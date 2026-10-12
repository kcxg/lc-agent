<template>
  <div class="chat-overview-panel">
    <div class="panel-section overview-section">
      <!-- 标题 + 总览卡整体吸附：向下滚动轮次列表时始终可见 -->
      <div class="overview-sticky">
        <div class="overview-header">
          <h4 class="overview-title">
            <span class="overview-title-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 16l4.5-5.5L11 14l4.5-7L20 12"/></svg>
            </span>
            聊天概览
          </h4>
          <div class="overview-header-right">
            <span class="overview-count">{{ rounds.length }} 轮</span>
            <button
              class="overview-refresh"
              :class="{ 'is-loading': loading }"
              type="button"
              title="刷新"
              @click="loadOverview"
            >
              <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-2.6-6.4"/><path d="M21 3v6h-6"/></svg>
            </button>
          </div>
        </div>

        <!-- 会话总览：深色渐变仪表盘，与下方轮次卡彻底拉开视觉 -->
        <div v-if="rounds.length > 0" class="overview-hero">
          <div class="hero-grid">
            <div class="hero-cell hero-cell-window">
              <span class="hero-cell-value">{{ formatToken(summary.windowInput) }}</span>
              <span class="hero-cell-label">当前窗口</span>
            </div>
            <div class="hero-cell">
              <span class="hero-cell-value">{{ formatToken(summary.totalInput) }}</span>
              <span class="hero-cell-label">总输入</span>
            </div>
            <div class="hero-cell">
              <span class="hero-cell-value">{{ formatToken(summary.totalOutput) }}</span>
              <span class="hero-cell-label">总输出</span>
            </div>
            <div class="hero-cell hero-cell-cached">
              <span class="hero-cell-value">{{ formatToken(summary.cacheRead) }}</span>
              <span class="hero-cell-label">总缓存</span>
            </div>
          </div>
          <div class="hero-foot">
            <span class="hero-foot-item" title="模型调用轮次">
              <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
              {{ summary.modelRounds }} 轮次
            </span>
            <span class="hero-foot-item" title="工具调用次数">
              <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a4.5 4.5 0 0 0-6 6L3 18l3 3 5.7-5.7a4.5 4.5 0 0 0 6-6L14 13l-3-3 3.7-3.7z"/></svg>
              {{ summary.toolCalls }} 工具
            </span>
            <span class="hero-foot-item hero-foot-time" title="总耗时">
              <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>
              {{ formatDuration(summary.durationMs) }}
            </span>
          </div>

          <!-- 会话深链：hash 路由 /c/:sessionId，浏览器打开即进入该会话 -->
          <div class="hero-share">
            <svg class="hero-share-icon" viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.07 0l3-3a5 5 0 0 0-7.07-7.07L11 4.9"/><path d="M14 11a5 5 0 0 0-7.07 0l-3 3a5 5 0 0 0 7.07 7.07L13 19.1"/></svg>
            <a
              v-if="sessionLink"
              class="hero-share-url"
              :href="sessionLink"
              :title="sessionLink"
              target="_blank"
              rel="noopener"
            >{{ sessionLink }}</a>
            <span v-else class="hero-share-url is-empty">会话保存后生成分享链接</span>
            <button
              v-if="sessionLink"
              class="hero-share-copy"
              type="button"
              @click="copySessionLink"
            >复制</button>
          </div>
        </div>
      </div>

      <div v-if="loading && rounds.length === 0" class="overview-state">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="loadError && rounds.length === 0" class="overview-state overview-error">
        <span class="overview-error-text">{{ loadError }}</span>
        <el-button size="small" type="primary" plain @click="loadOverview">重试</el-button>
      </div>

      <div v-else-if="rounds.length === 0" class="overview-state overview-empty">
        当前会话暂无消息
      </div>

      <!-- 每轮：6 色轮换的彩色轮次卡 -->
      <div v-if="rounds.length > 0" class="overview-timeline">
        <button
          v-for="round in rounds"
          :key="round.userMessageId"
          type="button"
          class="timeline-item"
          :class="accentClass(round.roundNumber)"
          :title="round.userText"
          @click="jumpToRound(round)"
        >
          <span class="timeline-card">
            <span class="timeline-head">
              <span class="timeline-badge">#{{ round.roundNumber }}</span>
              <span class="timeline-question">{{ round.userText || '（无文本）' }}</span>
              <span class="timeline-foot">
                <span class="timeline-foot-item" title="模型调用轮次">
                  <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
                  {{ round.modelRounds ?? '-' }}
                </span>
                <span class="timeline-foot-item" title="工具调用次数">
                  <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a4.5 4.5 0 0 0-6 6L3 18l3 3 5.7-5.7a4.5 4.5 0 0 0 6-6L14 13l-3-3 3.7-3.7z"/></svg>
                  {{ round.toolCallCount ?? '-' }}
                </span>
                <span class="timeline-foot-item" title="本轮耗时">
                  <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>
                  {{ formatDuration(round.durationMs) }}
                </span>
              </span>
            </span>
            <span class="timeline-metrics">
              <span class="timeline-metric" title="本轮当前窗口"><i>窗口</i><b>{{ formatToken(round.windowInput) }}</b></span>
              <span class="timeline-metric" title="本轮总输入"><i>输入</i><b>{{ formatToken(round.totalInput) }}</b></span>
              <span class="timeline-metric" title="本轮总输出"><i>输出</i><b>{{ formatToken(round.totalOutput) }}</b></span>
              <span class="timeline-metric metric-cached" title="本轮缓存读取"><i>缓存</i><b>{{ formatToken(round.cacheRead) }}</b></span>
            </span>
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useUiStore } from '@/stores/ui'
import { useSessionsStore } from '@/stores/sessions'
import { useChatStore } from '@/stores/chat'
import { normalizeHistoryMessages, type ChatMessage } from '@/stores/chat'
import { api } from '@/api/http'

interface OverviewRound {
  userMessageId: string
  roundNumber: number
  userText: string
  windowInput: number | null
  totalInput: number | null
  totalOutput: number | null
  cacheRead: number | null
  modelRounds: number | null
  toolCallCount: number | null
  durationMs: number | null
}

// 单页取到接口上限，尽量少次请求拉全；页数上限防御异常会话无限分页
const PAGE_LIMIT = 200
const MAX_PAGES = 60
// 自动刷新防抖：等后端落盘 + 合并一次提问里的多次状态翻转
const AUTO_REFRESH_DEBOUNCE_MS = 800
// 每轮主题色数量：按轮次号轮换，深浅主题下都清晰可辨
const ACCENT_COUNT = 6

const uiStore = useUiStore()
const sessionsStore = useSessionsStore()
const chatStore = useChatStore()

const rounds = ref<OverviewRound[]>([])
const loading = ref(false)
const loadError = ref('')
// 会话切换/重试会并发触发加载，只让最后一次的结果落地
let loadToken = 0
let refreshTimer: ReturnType<typeof setTimeout> | null = null

/** 每轮主题色：accent-0 ~ accent-5 轮换，样式里定义对应的 --accent */
function accentClass(roundNumber: number): string {
  return `accent-${(roundNumber - 1) % ACCENT_COUNT}`
}

/** 会话级汇总：tokens 求和，窗口取最后一轮的值 */
const summary = computed(() => {
  let totalInput: number | null = null
  let totalOutput: number | null = null
  let cacheRead: number | null = null
  let modelRounds = 0
  let hasModelRounds = false
  let toolCalls: number | null = null
  let durationMs: number | null = null
  let windowInput: number | null = null
  for (const r of rounds.value) {
    if (r.totalInput != null) totalInput = (totalInput ?? 0) + r.totalInput
    if (r.totalOutput != null) totalOutput = (totalOutput ?? 0) + r.totalOutput
    if (r.cacheRead != null) cacheRead = (cacheRead ?? 0) + r.cacheRead
    if (r.modelRounds != null) {
      modelRounds += r.modelRounds
      hasModelRounds = true
    }
    if (r.toolCallCount != null) toolCalls = (toolCalls ?? 0) + r.toolCallCount
    if (r.durationMs != null) durationMs = (durationMs ?? 0) + r.durationMs
    if (r.windowInput != null) windowInput = r.windowInput
  }
  return {
    windowInput,
    totalInput,
    totalOutput,
    cacheRead,
    modelRounds: hasModelRounds ? modelRounds : '-',
    toolCalls: toolCalls ?? '-',
    durationMs,
  }
})

function resolveSessionId(): string {
  return sessionsStore.effectiveThreadId || sessionsStore.currentSessionId || ''
}

/** 会话深链：hash 路由 /c/:sessionId，浏览器打开即进入该会话。未落库的本地会话没有可分享地址 */
const sessionLink = computed(() => {
  const id = resolveSessionId()
  if (!id || sessionsStore.isLocalSession(id)) return ''
  const { origin, pathname } = window.location
  return `${origin}${pathname}#/c/${id}`
})

async function copySessionLink() {
  const url = sessionLink.value
  if (!url) return
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.warning('复制失败，请手动选择地址')
  }
}

async function fetchAllMessages(sessionId: string): Promise<ChatMessage[]> {
  const raw: any[] = []
  let offset = 0
  let total = Number.POSITIVE_INFINITY
  for (let page = 0; page < MAX_PAGES; page++) {
    const resp = await api.getSessionMessages(sessionId, { offset, limit: PAGE_LIMIT })
    const batch = resp?.messages ?? []
    total = resp?.total ?? raw.length + batch.length
    raw.push(...batch)
    if (batch.length === 0 || raw.length >= total) break
    // offset 显式传入时接口按最早在前返回，按已取条数递增即可续取
    offset += batch.length
  }
  return normalizeHistoryMessages(raw)
}

function userTextOf(msg: ChatMessage): string {
  const content = msg.content
  if (typeof content === 'string') return content
  const parts: string[] = []
  for (const block of content) {
    if (block.type === 'text' && block.text) parts.push(block.text)
    else if (block.type === 'image_url') parts.push('[图片]')
    else if (block.type === 'text_file') parts.push(`[文件: ${block.name || '附件'}]`)
  }
  return parts.join(' ').trim()
}

function buildRounds(messages: ChatMessage[]): OverviewRound[] {
  const result: OverviewRound[] = []
  let current: OverviewRound | null = null
  for (const msg of messages) {
    if (msg.role === 'user') {
      if (msg.isSystem) continue
      current = {
        userMessageId: msg.id,
        roundNumber: msg.roundNumber ?? result.length + 1,
        userText: userTextOf(msg),
        windowInput: null,
        totalInput: null,
        totalOutput: null,
        cacheRead: null,
        modelRounds: null,
        toolCallCount: null,
        durationMs: null,
      }
      result.push(current)
      continue
    }
    // 一次提问后可能有多条 assistant，累计它们的指标；无 usage 时整轮保持 null 显示 '-'
    if (msg.role !== 'assistant' || !current || !msg.usage) continue
    for (const r of msg.usage.rounds) {
      current.totalInput = (current.totalInput ?? 0) + (r.inputTokens || 0)
      current.totalOutput = (current.totalOutput ?? 0) + (r.outputTokens || 0)
      current.cacheRead = (current.cacheRead ?? 0) + (r.cacheReadTokens || 0)
      // 当前窗口即最后一轮模型调用的输入规模，随遍历自然覆盖为最新值
      current.windowInput = r.inputTokens || 0
    }
    if (msg.usage.rounds.length > 0) {
      current.modelRounds = (current.modelRounds ?? 0) + msg.usage.rounds.length
    }
    current.toolCallCount = (current.toolCallCount ?? 0) + (msg.usage.toolCallCount || 0)
    if (msg.usage.totalDuration != null) {
      current.durationMs = (current.durationMs ?? 0) + msg.usage.totalDuration
    }
  }
  return result
}

async function loadOverview() {
  const sessionId = resolveSessionId()
  const token = ++loadToken
  loadError.value = ''
  if (!sessionId || sessionsStore.isLocalSession(sessionId)) {
    rounds.value = []
    loading.value = false
    return
  }
  loading.value = true
  try {
    const messages = await fetchAllMessages(sessionId)
    if (token !== loadToken) return
    rounds.value = buildRounds(messages)
  } catch (e) {
    if (token !== loadToken) return
    loadError.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    if (token === loadToken) loading.value = false
  }
}

/** 仅概览可见时自动刷新：后台切走不浪费全量分页请求 */
function scheduleAutoRefresh() {
  if (uiStore.activeTab !== 'overview') return
  if (refreshTimer) clearTimeout(refreshTimer)
  refreshTimer = setTimeout(() => {
    refreshTimer = null
    void loadOverview()
  }, AUTO_REFRESH_DEBOUNCE_MS)
}

onUnmounted(() => {
  if (refreshTimer) clearTimeout(refreshTimer)
})

function jumpToRound(round: OverviewRound) {
  // 带上轮次号：最新几轮在前端是本地生成的 id，与库里 uuid 对不上，靠轮次号兜底定位
  chatStore.requestJumpToMessage(round.userMessageId, round.roundNumber)
}

function formatToken(n: number | null): string {
  if (n == null) return '-'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

function formatDuration(ms: number | null): string {
  if (ms == null) return '-'
  if (ms < 1000) return ms + 'ms'
  return (ms / 1000).toFixed(1) + 's'
}

watch(
  [() => uiStore.activeTab, () => sessionsStore.effectiveThreadId || sessionsStore.currentSessionId],
  ([tab]) => {
    if (tab === 'overview') void loadOverview()
  },
  { immediate: true },
)

// 本轮流式结束（落盘后）自动刷新一次
watch(
  () => chatStore.isStreaming,
  (streaming, prev) => {
    if (prev && !streaming) scheduleAutoRefresh()
  },
)

// 用户发出新提问时也刷新，把新轮次第一时间列出来
watch(
  () => chatStore.messages.length,
  (len, prevLen) => {
    if (len > prevLen) scheduleAutoRefresh()
  },
)
</script>

<style scoped>
.overview-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 标题栏：这块是独立组件，吃不到 RightPanel 的 scoped 标题样式，这里自带一套 */
.overview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.overview-title {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--el-text-color-primary);
}

/* 与仪表盘同色系的小方标，让标题和下方极光卡连成一体 */
.overview-title-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  color: #fff;
  background: linear-gradient(135deg, #38bdf8 0%, #6366f1 60%, #a855f7 100%);
  box-shadow: 0 2px 8px rgb(99 102 241 / 40%);
}

.overview-header-right {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

/* 计数胶囊：跟轮次卡呼应的双色渐变 */
.overview-count {
  padding: 2px 9px;
  border-radius: 999px;
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.04em;
  background: linear-gradient(135deg, #6366f1, #06b6d4);
  box-shadow: 0 2px 8px rgb(99 102 241 / 32%);
}

.overview-refresh {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: 1px solid var(--el-border-color);
  border-radius: 999px;
  background: var(--el-bg-color);
  color: var(--el-text-color-secondary);
  cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease, background 0.15s ease, transform 0.3s ease;
}

.overview-refresh:hover {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-5);
  background: color-mix(in srgb, var(--el-color-primary) 8%, transparent);
  transform: rotate(90deg);
}

.overview-refresh.is-loading svg {
  animation: overviewSpin 0.9s linear infinite;
}

@keyframes overviewSpin {
  to { transform: rotate(360deg); }
}

.overview-state {
  padding: 4px 0;
}

.overview-error {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
}

.overview-error-text {
  color: var(--el-color-danger);
  font-size: 12px;
  word-break: break-all;
}

.overview-empty {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  text-align: center;
  padding: 12px 0;
}

/* 标题 + 总览卡整体吸附在面板顶部。滚动容器是 .right-panel-scroll，
   该 tab 下容器顶部不留内边距（见 RightPanel 的 .is-overview），
   由这里的 padding 提供呼吸缝，吸附时自己被底色完全遮住 */
.overview-sticky {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 0 0;
  background: var(--el-bg-color);
}

/* 总览仪表盘：深色渐变，与下方轮次卡彻底区分；深浅主题下都保持深底白字 */
.overview-hero {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  padding: 14px 14px 12px;
  color: #f8fafc;
  border: 1px solid rgb(255 255 255 / 14%);
  background:
    radial-gradient(115% 85% at 100% 0%, rgb(34 211 238 / 55%) 0%, transparent 52%),
    radial-gradient(115% 100% at 0% 100%, rgb(168 85 247 / 58%) 0%, transparent 52%),
    radial-gradient(90% 80% at 50% 130%, rgb(244 114 182 / 45%) 0%, transparent 58%),
    linear-gradient(135deg, #1e1b4b 0%, #4c1d95 48%, #0e7490 100%);
  background-size: 180% 180%;
  box-shadow:
    0 6px 22px rgb(76 29 149 / 40%),
    inset 0 1px 0 rgb(255 255 255 / 18%);
  animation: heroAurora 16s ease-in-out infinite;
}

/* 仪表盘上掠过的流光：让极光渐变缓慢流动 */
.overview-hero::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(
    115deg,
    transparent 40%,
    rgb(255 255 255 / 12%) 48%,
    rgb(255 255 255 / 22%) 52%,
    transparent 60%
  );
  background-size: 260% 100%;
  background-repeat: no-repeat;
  animation: heroSheen 7s linear infinite;
}

@keyframes heroAurora {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

@keyframes heroSheen {
  0% { background-position: 140% 0; }
  100% { background-position: -40% 0; }
}

.hero-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
}

.hero-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  min-width: 0;
}

.hero-cell + .hero-cell {
  border-left: 1px solid rgb(255 255 255 / 12%);
}

.hero-cell-value {
  font-size: 13px;
  font-weight: 800;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.hero-cell-window .hero-cell-value {
  color: #67e8f9;
}

.hero-cell-cached .hero-cell-value {
  color: #6ee7b7;
}

.hero-cell-label {
  font-size: 10px;
  color: rgb(224 242 254 / 65%);
}

.hero-foot {
  display: flex;
  gap: 14px;
  margin-top: 9px;
  font-size: 11px;
  font-weight: 600;
  color: rgb(224 242 254 / 80%);
}

.hero-foot-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* 总耗时与轮次/工具同排，用薄荷色区分 */
.hero-foot-time {
  color: #a7f3d0;
}

/* 会话深链行 */
.hero-share {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 9px;
  padding-top: 8px;
  border-top: 1px solid rgb(255 255 255 / 14%);
  font-size: 11px;
  color: rgb(224 242 254 / 85%);
}

.hero-share-icon {
  flex-shrink: 0;
  opacity: 0.85;
}

.hero-share-url {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #a5f3fc;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  text-decoration: none;
}

.hero-share-url:hover {
  color: #cffafe;
  text-decoration: underline;
}

.hero-share-url.is-empty {
  color: rgb(224 242 254 / 55%);
  font-family: inherit;
}

.hero-share-copy {
  flex-shrink: 0;
  padding: 1px 8px;
  border-radius: 999px;
  border: 1px solid rgb(255 255 255 / 22%);
  background: rgb(255 255 255 / 14%);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s ease;
}

.hero-share-copy:hover {
  background: rgb(255 255 255 / 28%);
}

/* 轮次卡：每轮按轮次号轮换 6 种主题色，徽章 / 图标统一跟随 */
.overview-timeline {
  display: flex;
  flex-direction: column;
}

.timeline-item {
  --accent-a: #38bdf8;
  --accent-b: #1d4ed8;
  width: 100%;
  padding: 0;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
}

.timeline-item.accent-1 { --accent-a: #a78bfa; --accent-b: #6d28d9; }
.timeline-item.accent-2 { --accent-a: #34d399; --accent-b: #047857; }
.timeline-item.accent-3 { --accent-a: #fbbf24; --accent-b: #b45309; }
.timeline-item.accent-4 { --accent-a: #f472b6; --accent-b: #be123c; }
.timeline-item.accent-5 { --accent-a: #22d3ee; --accent-b: #0e7490; }

.timeline-item:focus-visible {
  outline: 2px solid var(--el-color-primary-light-3);
  outline-offset: 1px;
  border-radius: 10px;
}

/* 卡片首行：轮次徽章 + 提问文本 */
.timeline-head {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  min-width: 0;
}

/* 白底徽章：在彩色卡面上最跳，也和仪表盘左边缘严格对齐 */
.timeline-badge {
  flex-shrink: 0;
  margin-top: 1px;
  padding: 0 7px;
  border-radius: 999px;
  background: rgb(255 255 255 / 92%);
  color: color-mix(in srgb, var(--accent-b) 80%, #000);
  font-size: 10px;
  font-weight: 800;
  line-height: 17px;
  white-space: nowrap;
  box-shadow: 0 1px 5px rgb(0 0 0 / 22%);
  transition: transform 0.18s ease;
}

.timeline-item:hover .timeline-badge {
  transform: translateY(-1px);
}

.timeline-card {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin: 4px 0 10px;
  padding: 11px 12px;
  border: 1px solid rgb(255 255 255 / 20%);
  border-radius: 12px;
  background:
    radial-gradient(130% 150% at 0% 0%, rgb(255 255 255 / 20%) 0%, transparent 42%),
    linear-gradient(135deg, var(--accent-a) 0%, var(--accent-b) 100%);
  box-shadow: 0 4px 14px color-mix(in srgb, var(--accent-b) 42%, transparent);
  transition: box-shadow 0.18s ease, transform 0.18s ease;
}

/* 悬停时滑过卡面的高光 */
.timeline-card::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(
    115deg,
    transparent 42%,
    rgb(255 255 255 / 20%) 50%,
    transparent 58%
  );
  background-size: 240% 100%;
  background-repeat: no-repeat;
  background-position: 150% 0;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.timeline-item:hover .timeline-card::after {
  opacity: 1;
  animation: cardSheen 0.9s ease-out;
}

@keyframes cardSheen {
  0% { background-position: 150% 0; }
  100% { background-position: -50% 0; }
}

.timeline-item:hover .timeline-card {
  box-shadow: 0 8px 22px color-mix(in srgb, var(--accent-b) 58%, transparent);
  transform: translateY(-2px);
}

.timeline-question {
  flex: 1;
  min-width: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.5;
  text-shadow: 0 1px 3px rgb(0 0 0 / 28%);
}

.timeline-metrics {
  display: flex;
  background: rgb(255 255 255 / 16%);
  border: 1px solid rgb(255 255 255 / 16%);
  border-radius: 8px;
  padding: 7px 4px;
}

.timeline-metric {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  white-space: nowrap;
}

.timeline-metric + .timeline-metric {
  border-left: 1px solid rgb(255 255 255 / 22%);
}

.timeline-metric i {
  font-style: normal;
  font-size: 10px;
  color: rgb(255 255 255 / 78%);
}

.timeline-metric b {
  font-weight: 800;
  font-size: 12px;
  color: #fff;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  text-shadow: 0 1px 2px rgb(0 0 0 / 22%);
}

.metric-cached b {
  color: #d1fae5;
}

/* 轮次/工具/耗时：跟在用户问题右侧，与问题首行齐平 */
.timeline-foot {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  gap: 10px;
  margin-top: 2px;
  font-size: 11px;
  font-weight: 600;
  color: rgb(255 255 255 / 90%);
}

.timeline-foot-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.timeline-foot-item svg {
  color: rgb(255 255 255 / 95%);
}

/* 尊重系统的「减少动态效果」偏好：关掉极光流动、流光与刷新转圈 */
@media (prefers-reduced-motion: reduce) {
  .overview-hero,
  .overview-hero::after,
  .timeline-item:hover .timeline-card::after,
  .overview-refresh.is-loading svg {
    animation: none;
  }
}
</style>
