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
            <button
              class="overview-collapse"
              :class="{ 'is-collapsed': heroCollapsed }"
              type="button"
              :title="heroCollapsed ? '展开概览' : '折叠概览'"
              :aria-expanded="!heroCollapsed"
              @click="heroCollapsed = !heroCollapsed"
            >
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>
            </button>
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

        <!-- 会话总览：遥测仪表盘，中性底 + 点阵纹理；整个 Hero 可折叠，折叠后只留标题行 -->
        <div v-if="rounds.length > 0" v-show="!heroCollapsed" class="overview-hero">
          <!-- 两行 7 格：上排 token 四项，下排过程三项；色点把格子与下方对应折线绑起来 -->
          <div
            v-for="(row, rowIndex) in heroRows"
            :key="rowIndex"
            class="hero-grid"
            :class="{ 'is-3': row.length === 3 }"
          >
            <button
              v-for="cell in row"
              :key="cell.key"
              class="hero-cell"
              :class="{ 'is-muted': !isSeriesVisible(cell.key) }"
              type="button"
              :title="`${cell.title}（点击只看这一条，再点恢复全部）`"
              :aria-pressed="isSeriesVisible(cell.key)"
              @click="toggleSeries(cell.key)"
            >
              <span class="hero-cell-value" :class="{ 'is-accent': cell.accent }">{{ cell.value }}</span>
              <span class="hero-cell-label">
                <i class="series-dot" :class="cell.cls"></i>{{ cell.label }}
              </span>
            </button>
          </div>
          <!-- 批量显隐：两个按钮按当前状态禁用（都已经显示了，"显示全部"就没必要点） -->
          <div class="hero-chart-tip">
            <span v-if="chartHint" class="hero-chart-tip-count" :title="chartHintTitle">{{ chartHint }}</span>
            <button
              class="hero-chart-btn"
              type="button"
              :disabled="allShown"
              @click="showAllSeries"
            >显示全部</button>
            <button
              class="hero-chart-btn"
              type="button"
              :disabled="noneShown"
              @click="hideAllSeries"
            >隐藏全部</button>
          </div>
          <!-- 走势叠加图：每条线各自归一化，纵轴只表形状不表绝对大小 -->
          <div class="hero-chart-wrap">
            <svg
              class="hero-chart"
              :viewBox="`0 0 100 ${CHART_H}`"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
                <g v-for="series in visibleChartSeries" :key="series.key">
                  <polyline
                    v-for="(seg, segIndex) in series.segs"
                    :key="segIndex"
                    :class="series.cls"
                    :points="seg"
                    vector-effect="non-scaling-stroke"
                  />
                </g>
            </svg>
            <span v-if="chartEmptyText" class="hero-chart-empty">{{ chartEmptyText }}</span>
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

      <!-- 每轮：中性轮次卡，最新一轮左侧色条点亮 -->
      <div v-if="rounds.length > 0" class="overview-timeline">
        <button
          v-for="(round, idx) in rounds"
          :key="round.userMessageId"
          type="button"
          class="timeline-item"
          :class="{ 'is-latest': idx === rounds.length - 1 }"
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
            <span
              class="timeline-comp"
              :title="`缓存 ${formatToken(round.cacheRead)} · 输入 ${formatToken(round.totalInput)} · 输出 ${formatToken(round.totalOutput)}`"
            >
              <i class="comp-cache" :style="{ width: compOf(round).cache + '%' }"></i>
              <i class="comp-input" :style="{ width: compOf(round).input + '%' }"></i>
              <i class="comp-output" :style="{ width: compOf(round).output + '%' }"></i>
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

const uiStore = useUiStore()
const sessionsStore = useSessionsStore()
const chatStore = useChatStore()

const rounds = ref<OverviewRound[]>([])
const loading = ref(false)
const loadError = ref('')
// 会话切换/重试会并发触发加载，只让最后一次的结果落地
let loadToken = 0
let refreshTimer: ReturnType<typeof setTimeout> | null = null

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

type SparkMode = 'minmax' | 'zero'
type SeriesKey = 'window' | 'input' | 'output' | 'cache' | 'calls' | 'tools' | 'duration'

/** 走势图高度（viewBox 100xCHART_H） */
const CHART_H = 56

/** 逐轮序列 → SVG 折线段（viewBox 100x{height}）。
 *  - null 表示"该轮没有数据"：断开折线，且不参与极值计算（当 0 会把曲线砸出假坑）
 *  - mode='minmax'：按 [min, max] 拉伸，用于起点天然不为 0 的 token 类
 *  - mode='zero'：按 [0, max] 拉伸，用于 0 是真实最低位的计数/耗时类
 *  - x 一律按轮次下标定位，7 条线共享同一时间轴
 *  - 每条线**各自归一化**：7 个量量纲差 6 个数量级，共享尺度会让小量贴成直线，
 *    因此纵轴只表"形状"，不表绝对大小
 *  - 单点段补一个微小横段，保证"只有一轮"时也可见 */
function sparkSegments(values: Array<number | null>, mode: SparkMode, height: number): string[] {
  const n = values.length
  if (n === 0) return []
  const present = values.filter((v): v is number => v != null)
  if (present.length === 0) return []
  const max = Math.max(...present)
  const min = mode === 'zero' ? 0 : Math.min(...present)
  const span = max - min
  const padX = 2
  const padY = 3
  const w = 100 - padX * 2
  const h = height - padY * 2
  const segs: string[] = []
  let pts: Array<{ x: number; y: number }> = []
  const flush = () => {
    if (pts.length === 0) return
    if (pts.length === 1) {
      const p = pts[0]
      segs.push(`${p.x.toFixed(1)},${p.y.toFixed(1)} ${(p.x + 0.8).toFixed(1)},${p.y.toFixed(1)}`)
    } else {
      segs.push(pts.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' '))
    }
    pts = []
  }
  for (let i = 0; i < n; i++) {
    const v = values[i]
    if (v == null) {
      flush()
      continue
    }
    const x = n === 1 ? 50 : padX + (i / (n - 1)) * w
    // span 为 0 时没有可拉伸的范围：计数类全 0 要贴底（是"真的没有"，不是"有数据"），
    // 其余情况居中，表示"该项恒定"
    const y = span === 0
      ? (mode === 'zero' ? padY + h : padY + h / 2)
      : padY + (1 - (v - min) / span) * h
    pts.push({ x, y })
  }
  flush()
  return segs
}

/** 7 条线的元信息：key 同时决定颜色类 `series-<key>`，格子圆点与折线共用同一个色 */
const seriesMeta: Array<{ key: SeriesKey; cls: string }> = [
  { key: 'window', cls: 'series-window' },
  { key: 'input', cls: 'series-input' },
  { key: 'output', cls: 'series-output' },
  { key: 'cache', cls: 'series-cache' },
  { key: 'calls', cls: 'series-calls' },
  { key: 'tools', cls: 'series-tools' },
  { key: 'duration', cls: 'series-duration' },
]

/** 只有"有数据"的轮次才占 x 位置。
 *  整轮缺失（run 被取消或模型报错，一条都没落库）不占位：7 条线共享同一布局，
 *  于是"7 条线在同一 x 一起断开、看起来像两张图"自然消失，而且不伪造任何数据。
 *  注意：单条线内部残留的 null（某轮只有 token 没有耗时之类）仍照旧断开——那是真的稀疏。 */
const plotRounds = computed(() =>
  rounds.value.filter(
    r => r.totalInput != null || r.modelRounds != null || r.toolCallCount != null || r.durationMs != null,
  ),
)

/** 被跳过的轮数——形体干净了，但这个信息不能丢，要显式写出来 */
const skippedRounds = computed(() => rounds.value.length - plotRounds.value.length)

/** 7 条逐轮走势，叠加在同一张图上 */
const sparks = computed<Record<SeriesKey, string[]>>(() => ({
  window: sparkSegments(plotRounds.value.map(r => r.windowInput), 'minmax', CHART_H),
  input: sparkSegments(plotRounds.value.map(r => r.totalInput), 'minmax', CHART_H),
  output: sparkSegments(plotRounds.value.map(r => r.totalOutput), 'minmax', CHART_H),
  cache: sparkSegments(plotRounds.value.map(r => r.cacheRead), 'minmax', CHART_H),
  calls: sparkSegments(plotRounds.value.map(r => r.modelRounds), 'zero', CHART_H),
  tools: sparkSegments(plotRounds.value.map(r => r.toolCallCount), 'zero', CHART_H),
  duration: sparkSegments(plotRounds.value.map(r => r.durationMs), 'zero', CHART_H),
}))

/** 图表数据：每条线 + 颜色类 + 折线段 */
const chartSeries = computed(() =>
  seriesMeta.map(s => ({ ...s, segs: sparks.value[s.key] })),
)

interface HeroCell {
  key: SeriesKey
  label: string
  title: string
  /** 会话级数值（总量）；走势统一在下方那张叠加图里 */
  value: string
  accent?: boolean
  cls: string
}

const heroCells = computed<HeroCell[]>(() => {
  const m = summary.value
  return [
    { key: 'window', label: '当前窗口', title: '当前窗口：最后一次模型调用的输入规模', value: formatToken(m.windowInput), accent: true, cls: 'series-window' },
    { key: 'input', label: '总输入', title: '本会话所有模型调用的输入合计', value: formatToken(m.totalInput), cls: 'series-input' },
    { key: 'output', label: '总输出', title: '本会话所有模型调用的输出合计', value: formatToken(m.totalOutput), cls: 'series-output' },
    { key: 'cache', label: '总缓存', title: '本会话命中缓存的输入合计', value: formatToken(m.cacheRead), cls: 'series-cache' },
    { key: 'calls', label: '总模型调用', title: '本会话模型调用次数（一次提问内的工具循环会反复调用）', value: formatCount(m.modelRounds), cls: 'series-calls' },
    { key: 'tools', label: '总工具次数', title: '本会话工具调用次数', value: formatCount(m.toolCalls), cls: 'series-tools' },
    { key: 'duration', label: '总耗时', title: '本会话所有模型调用的耗时合计', value: formatDuration(m.durationMs), cls: 'series-duration' },
  ]
})

/** 两行布局：上排 4 个 token 指标，下排 3 个过程指标 */
const heroRows = computed(() => {
  const cells = heroCells.value
  return [cells.slice(0, 4), cells.slice(4)]
})

/** Hero 折叠：收起后只留标题行 */
const heroCollapsed = ref(false)

/** null = 全部显示；[] = 全部隐藏；非空数组 = 只画选中的这几条
 *  点格子：全部显示 → 只看这一条；已选中 → 取消（点掉最后一条回到全部显示）；
 *  未选中 → 追加进去；凑满 7 条等同全部显示 */
const soloKeys = ref<SeriesKey[] | null>(null)

const allShown = computed(() => soloKeys.value === null)
const noneShown = computed(() => soloKeys.value !== null && soloKeys.value.length === 0)
const visibleCount = computed(() =>
  soloKeys.value === null ? seriesMeta.length : soloKeys.value.length,
)

function isSeriesVisible(key: SeriesKey): boolean {
  return soloKeys.value === null || soloKeys.value.includes(key)
}

function toggleSeries(key: SeriesKey) {
  const cur = soloKeys.value
  if (cur === null) {
    soloKeys.value = [key]
    return
  }
  if (cur.includes(key)) {
    const next = cur.filter(k => k !== key)
    // 点掉最后一条 = 回到"全部显示"（与"再点它一下就恢复全部"保持一致）
    soloKeys.value = next.length === 0 ? null : next
    return
  }
  const next = [...cur, key]
  soloKeys.value = next.length === seriesMeta.length ? null : next
}

function showAllSeries() {
  soloKeys.value = null
}

function hideAllSeries() {
  soloKeys.value = []
}

/** 图上实际绘制的线（顺序仍按 seriesMeta） */
const visibleChartSeries = computed(() => chartSeries.value.filter(s => isSeriesVisible(s.key)))

/** 图表左上角那行小字：只在真有额外信息时才出现（没筛选、没跳轮就什么都不显示） */
const chartHint = computed(() => {
  const parts: string[] = []
  if (!allShown.value) parts.push(`已显示 ${visibleCount.value} / ${seriesMeta.length}`)
  if (skippedRounds.value > 0) parts.push(`${skippedRounds.value} 轮无数据`)
  return parts.join(' · ')
})

/** "无数据"要说清是什么原因，不能让读者自己猜 */
const chartHintTitle = computed(() =>
  skippedRounds.value > 0
    ? `${skippedRounds.value} 个轮次没有落库任何用量数据（运行被取消或模型报错），已从走势图中跳过`
    : '',
)

/** 图上什么都画不出来时的提示：全部隐藏，或这个会话还没有可用数据 */
const chartEmptyText = computed(() => {
  if (noneShown.value) return '已隐藏全部曲线 · 点上方指标可单独查看'
  if (plotRounds.value.length === 0) return '还没有可用的用量数据'
  return ''
})

/** 轮次构成条：缓存命中 / 新增输入 / 输出 三段百分比。
 *  注意 cacheRead 在多数厂商口径里是 inputTokens 的子集，所以输入段 = 输入 - 缓存，
 *  并 clamp 防脏数据（缓存 > 输入）出现负宽度。 */
function compOf(round: OverviewRound): { cache: number; input: number; output: number } {
  const input = Math.max(0, round.totalInput ?? 0)
  const cache = Math.min(Math.max(0, round.cacheRead ?? 0), input)
  const fresh = input - cache
  const output = Math.max(0, round.totalOutput ?? 0)
  const total = cache + fresh + output
  if (total <= 0) return { cache: 0, input: 0, output: 0 }
  return {
    cache: (cache / total) * 100,
    input: (fresh / total) * 100,
    output: (output / total) * 100,
  }
}

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

/** 次数类不做 k 缩写（90 次就是 90，不该显示成 0.1k） */
function formatCount(v: number | string | null): string {
  if (v == null) return '-'
  return String(v)
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
/* 暖色（轮次卡 token 构成条的输入侧用）：浅色主题加深一档、深色主题提亮一档。
   走势图那 7 条线各有自己的 --series 色（见 .series-*），与本变量无关 */
.overview-section {
  --comp-warm: #c97a12;
  --comp-warm-soft: rgb(201 122 18 / 30%);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

html.dark .overview-section {
  --comp-warm: #f0a94a;
  --comp-warm-soft: rgb(240 169 74 / 20%);
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

/* 标题小方标：发丝线 + 单强调色图标（原三色渐变改掉） */
.overview-title-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  color: var(--el-color-primary);
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 35%, transparent);
  background: color-mix(in srgb, var(--el-color-primary) 8%, transparent);
}

.overview-header-right {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

/* 计数胶囊：中性淡彩底 + 强调色数字（原双色渐变改掉） */
.overview-count {
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: var(--el-color-primary);
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 30%, transparent);
  background: color-mix(in srgb, var(--el-color-primary) 7%, transparent);
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

/* 折叠/展开 Hero：和刷新按钮同款的圆形按钮（原来是 11px 裸字形，太小看不出能点） */
.overview-collapse {
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
  transition: color 0.15s ease, border-color 0.15s ease, background 0.15s ease;
}

.overview-collapse svg {
  transition: transform 0.2s ease;
}

/* 折叠后箭头转向，按钮本身也带着状态 */
.overview-collapse.is-collapsed svg {
  transform: rotate(-90deg);
}

.overview-collapse:hover {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-5);
  background: color-mix(in srgb, var(--el-color-primary) 8%, transparent);
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

/* 遥测仪表盘：中性底 + 发丝线 + 顶部受光，深浅主题自动适配 */
.overview-hero {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  padding: 14px 14px 12px;
  color: var(--el-text-color-primary);
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 6%);
}

/* 工程点阵纹理：currentColor 低透明度，随主题自动反色；只铺上半部，底部渐隐不干扰文字 */
.overview-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image: radial-gradient(circle, currentColor 1px, transparent 1px);
  background-size: 18px 18px;
  opacity: 0.05;
  mask-image: linear-gradient(to bottom, #000 0%, transparent 70%);
  -webkit-mask-image: linear-gradient(to bottom, #000 0%, transparent 70%);
}

.hero-grid {
  position: relative;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
}

/* 第二行只有 3 格（过程指标）：列数跟着变，避免右侧留一个空列 */
.hero-grid.is-3 {
  grid-template-columns: repeat(3, 1fr);
}

.hero-grid + .hero-grid {
  margin-top: 10px;
}

/* 指标格同时是走势图的开关（点一下只看这条），所以是个 button */
.hero-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  min-width: 0;
  padding: 0;
  border: none;
  border-radius: 8px;
  background: transparent;
  font: inherit;
  color: inherit;
  cursor: pointer;
}

.hero-cell + .hero-cell {
  border-left: 1px solid var(--el-border-color-lighter);
}

/* 未选中的指标：整格变淡、色点变灰，表示"这条线现在不画" */
.hero-cell.is-muted .hero-cell-value,
.hero-cell.is-muted .hero-cell-label {
  color: var(--el-text-color-placeholder);
}

.hero-cell.is-muted .series-dot {
  background: var(--el-text-color-placeholder);
}

.hero-cell:hover .hero-cell-label,
.hero-cell:focus-visible .hero-cell-label {
  color: var(--el-color-primary);
}

.hero-cell:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--el-color-primary) 45%, transparent);
  outline-offset: 2px;
}

.hero-cell-value {
  font-size: 15px;
  font-weight: 800;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-variant-numeric: tabular-nums;
  color: var(--el-text-color-primary);
}

/* 当前窗口是 Hero 里唯一的"活指标"：强调色 + 略大字号 */
.hero-cell-value.is-accent {
  color: var(--el-color-primary);
  font-size: 17px;
}

.hero-cell-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: var(--el-text-color-secondary);
}

/* 色点：把格子里的数值与下方图表里对应的那条线绑起来 */
.series-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--series);
  flex-shrink: 0;
}

/* 批量显隐行：左边状态，右边两个按钮 */
.hero-chart-tip {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  margin-top: 10px;
}

.hero-chart-tip-count {
  margin-right: auto;
  font-size: 10px;
  color: var(--el-text-color-placeholder);
}

.hero-chart-btn {
  padding: 2px 9px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 30%, transparent);
  background: color-mix(in srgb, var(--el-color-primary) 7%, transparent);
  color: var(--el-color-primary);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.03em;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
}

.hero-chart-btn:hover:not(:disabled) {
  background: color-mix(in srgb, var(--el-color-primary) 14%, transparent);
}

/* 该动作已经是当前状态时置灰（已经全显示了，"显示全部"就点不动） */
.hero-chart-btn:disabled {
  color: var(--el-text-color-placeholder);
  border-color: var(--el-border-color-lighter);
  background: transparent;
  cursor: default;
}

/* 走势图容器：兼作"全部隐藏"时空状态提示的定位参照 */
.hero-chart-wrap {
  position: relative;
  margin-top: 10px;
}

/* 7 条逐轮走势叠加图 */
.hero-chart {
  display: block;
  width: 100%;
  height: 56px;
}

/* 全部隐藏时的占位提示（图还在，只是没线） */
.hero-chart-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: var(--el-text-color-placeholder);
  pointer-events: none;
}

.hero-chart polyline {
  fill: none;
  stroke: var(--series);
  stroke-width: 1.25;
  stroke-opacity: 0.85;
  stroke-linejoin: round;
  stroke-linecap: round;
}

/* 7 条线各自的颜色。叠加之后"位置"不再是区分手段，只能靠色相，
   所以这里必须每条一个颜色——这属于功能性用色（等同于图表图例），不是装饰性彩虹 */
.series-window { --series: #4a9eff; }
.series-input { --series: #f0a94a; }
.series-output { --series: #67c23a; }
.series-cache { --series: #b06ae0; }
.series-calls { --series: #e36d8a; }
.series-tools { --series: #2fb8ad; }
.series-duration { --series: #8d97a5; }

/* 会话深链行 */
.hero-share {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 9px;
  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
  font-size: 11px;
  color: var(--el-text-color-secondary);
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
  color: var(--el-color-primary);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  text-decoration: none;
}

.hero-share-url:hover {
  text-decoration: underline;
}

.hero-share-url.is-empty {
  color: var(--el-text-color-secondary);
  font-family: inherit;
}

.hero-share-copy {
  flex-shrink: 0;
  padding: 1px 8px;
  border-radius: 999px;
  border: 1px solid var(--el-border-color);
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 10px;
  font-weight: 700;
  cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease, background 0.15s ease;
}

.hero-share-copy:hover {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-5);
  background: color-mix(in srgb, var(--el-color-primary) 8%, transparent);
}

/* 轮次卡：中性底，区分度交给左轨色条与构成条 */
.overview-timeline {
  display: flex;
  flex-direction: column;
}

.timeline-item {
  width: 100%;
  padding: 0;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
}

.timeline-item:focus-visible {
  outline: 2px solid var(--el-color-primary-light-3);
  outline-offset: 1px;
  border-radius: 10px;
}

.timeline-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin: 4px 0 10px;
  padding: 11px 12px 11px 14px; /* 左侧多留 2px 给色条 */
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  background: var(--el-bg-color);
  transition: border-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
}

/* 左轨：历史轮浅灰，最新一轮点亮（全面板唯一的彩色信号） */
.timeline-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10px;
  bottom: 10px;
  width: 2px;
  border-radius: 2px;
  background: color-mix(in srgb, var(--el-text-color-primary) 14%, transparent);
  transition: background 0.18s ease, box-shadow 0.18s ease;
}

.timeline-item.is-latest .timeline-card::before {
  background: var(--el-color-primary);
  box-shadow: 0 0 8px color-mix(in srgb, var(--el-color-primary) 55%, transparent);
}

.timeline-item:hover .timeline-card {
  border-color: var(--el-border-color);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgb(0 0 0 / 18%);
}

/* 卡片首行：轮次徽章 + 提问文本 */
.timeline-head {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  min-width: 0;
}

.timeline-badge {
  flex-shrink: 0;
  margin-top: 1px;
  padding: 0 7px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--el-text-color-primary) 8%, transparent);
  color: var(--el-text-color-secondary);
  font-size: 10px;
  font-weight: 800;
  line-height: 17px;
  white-space: nowrap;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.timeline-item.is-latest .timeline-badge {
  color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
}

.timeline-question {
  flex: 1;
  min-width: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: var(--el-text-color-primary);
  font-size: 12px;
  font-weight: 700;
  line-height: 1.5;
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
  color: var(--el-text-color-secondary);
}

.timeline-foot-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* 指标行：淡中性底盒，标签次要色、数值主色 */
.timeline-metrics {
  display: flex;
  background: color-mix(in srgb, var(--el-text-color-primary) 4%, transparent);
  border: 1px solid color-mix(in srgb, var(--el-text-color-primary) 7%, transparent);
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
  border-left: 1px solid var(--el-border-color-lighter);
}

.timeline-metric i {
  font-style: normal;
  font-size: 10px;
  color: var(--el-text-color-secondary);
}

.timeline-metric b {
  font-weight: 800;
  font-size: 12px;
  color: var(--el-text-color-primary);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-variant-numeric: tabular-nums;
}

/* token 构成条：缓存命中（淡暖底 + 45° 斜纹，弱化）/ 未命中输入（实心暖色）/ 输出（绿）。
   5px 高度是斜纹可辨的最低要求；缓存段靠「纹理」而非「第三个色相」区分 */
.timeline-comp {
  display: flex;
  height: 5px;
  border-radius: 3px;
  overflow: hidden;
  gap: 1px;
  background: color-mix(in srgb, var(--el-text-color-primary) 6%, transparent);
}

.timeline-comp i {
  display: block;
  height: 100%;
  min-width: 0;
  transition: width 0.3s ease;
}

.timeline-comp .comp-cache {
  background-color: var(--comp-warm-soft);
  background-image: repeating-linear-gradient(
    45deg,
    color-mix(in srgb, var(--comp-warm) 70%, transparent) 0 1px,
    transparent 1px 6px
  );
}

.timeline-comp .comp-input {
  background: var(--comp-warm);
}

.timeline-comp .comp-output {
  background: var(--el-color-success);
}

/* 尊重系统的「减少动态效果」偏好 */
@media (prefers-reduced-motion: reduce) {
  .overview-refresh.is-loading svg {
    animation: none;
  }
  .timeline-card,
  .timeline-card::before,
  .timeline-comp i {
    transition: none;
  }
}
</style>
