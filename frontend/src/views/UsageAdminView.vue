<template>
  <div class="usage-admin usage-page">
    <div class="page-header">
      <div class="page-title">
        <h2>Token 用量统计</h2>
        <span class="page-subtitle">按人 / Agent / 模型统计 token 消耗与费用</span>
      </div>
      <div class="page-actions">
        <el-button
          type="primary"
          data-test="open-pricing"
          @click="pricingOpen = true"
        >
          <span class="btn-icon">¥</span>
          单价设置
          <el-badge
            v-if="unpricedModels.length > 0"
            :value="`${unpricedModels.length} 个模型未设置价格`"
            class="pricing-badge"
          />
        </el-button>
        <el-button @click="$router.push('/admin')">返回管理后台</el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-date-picker
        v-model="range"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        :clearable="false"
        class="f-date"
        @change="loadAll"
      />
      <el-select v-model="granularity" class="f-gran" @change="loadAll">
        <el-option label="按天" value="day" />
        <el-option label="按月" value="month" />
      </el-select>
      <el-select v-model="groupBy" multiple collapse-tags class="f-group" placeholder="分组维度" @change="loadAll">
        <el-option label="用户" value="user" />
        <el-option label="Agent" value="agent" />
        <el-option label="时间桶" value="bucket" />
      </el-select>
      <el-checkbox v-model="includeSub" @change="loadAll">含子 Agent</el-checkbox>
      <el-button type="primary" :loading="loading" @click="loadAll">查询</el-button>
      <el-button :loading="exporting" @click="handleExport">导出 CSV</el-button>
    </div>

    <!-- 未设置价格警告：费用算不出来时第一时间提示 -->
    <el-alert
      v-if="unpricedModels.length > 0"
      type="warning"
      :closable="false"
      class="unpriced-alert"
    >
      <template #title>
        以下模型还没有设置价格，费用暂时无法统计：
        <el-tag
          v-for="m in unpricedModels.slice(0, 6)"
          :key="m"
          size="small"
          class="unpriced-tag"
        >{{ m }}</el-tag>
        <span v-if="unpricedModels.length > 6" class="unpriced-more">
          等 {{ unpricedModels.length }} 个
        </span>
        <el-button link type="primary" @click="pricingOpen = true">去设置价格 →</el-button>
      </template>
    </el-alert>

    <!-- 顶部卡片 -->
    <div class="cards">
      <div class="stat-card stat-card--cost">
        <div class="stat-label">总消耗（元）</div>
        <div class="stat-value">{{ fmtCost(totals?.cost) }}</div>
      </div>
      <div class="stat-card stat-card--tokens">
        <div class="stat-label">总 Token</div>
        <div class="stat-value">{{ fmtNum(totalTokens) }}</div>
      </div>
      <div class="stat-card stat-card--users">
        <div class="stat-label">活跃人数</div>
        <div class="stat-value">{{ totals?.active_users ?? '—' }}</div>
      </div>
      <div class="stat-card stat-card--calls">
        <div class="stat-label">调用次数</div>
        <div class="stat-value">{{ fmtNum(totals?.calls ?? 0) }}</div>
      </div>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="汇总" name="summary">
        <el-table v-loading="loading" :data="rows" stripe border max-height="560">
          <el-table-column
            v-for="dim in displayDims"
            :key="dim"
            :prop="dim"
            :label="dimLabel(dim)"
            min-width="110"
          />
          <el-table-column prop="model_id" label="模型" min-width="150" />
          <el-table-column label="输入" min-width="100" align="right">
            <template #default="{ row }">{{ fmtNum(row.input_tokens) }}</template>
          </el-table-column>
          <el-table-column label="命中缓存" min-width="100" align="right">
            <template #default="{ row }">{{ fmtNum(row.cache_read_tokens) }}</template>
          </el-table-column>
          <el-table-column label="写入缓存" min-width="90" align="right">
            <template #default="{ row }">{{ fmtNum(row.cache_write_tokens) }}</template>
          </el-table-column>
          <el-table-column label="输出" min-width="100" align="right">
            <template #default="{ row }">{{ fmtNum(row.output_tokens) }}</template>
          </el-table-column>
          <el-table-column prop="calls" label="调用" width="80" align="right" />
          <el-table-column label="金额（元）" min-width="110" align="right" fixed="right">
            <template #default="{ row }">
              <span :class="{ unpriced: row.cost === null }">{{ fmtCost(row.cost) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="消费最高的会话" name="sessions">
        <el-table v-loading="sessionsLoading" :data="topSessions" stripe border max-height="560">
          <el-table-column prop="title" label="会话" min-width="220" />
          <el-table-column prop="username" label="用户" min-width="110" />
          <el-table-column prop="agent_name" label="Agent" min-width="110" />
          <el-table-column prop="model_id" label="模型" min-width="140" />
          <el-table-column label="输入" min-width="100" align="right">
            <template #default="{ row }">{{ fmtNum(row.input_tokens) }}</template>
          </el-table-column>
          <el-table-column label="命中缓存" min-width="100" align="right">
            <template #default="{ row }">{{ fmtNum(row.cache_read_tokens) }}</template>
          </el-table-column>
          <el-table-column label="写入缓存" min-width="100" align="right">
            <template #default="{ row }">{{ fmtNum(row.cache_write_tokens) }}</template>
          </el-table-column>
          <el-table-column label="输出" min-width="100" align="right">
            <template #default="{ row }">{{ fmtNum(row.output_tokens) }}</template>
          </el-table-column>
          <el-table-column prop="calls" label="调用" width="80" align="right" />
          <el-table-column label="金额" width="110" align="right">
            <template #default="{ row }">
              <span :class="{ 'cost-strong': row.cost != null }">{{ fmtCost(row.cost) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDetail(row)">明细</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 会话明细弹窗 -->
    <el-dialog v-model="detailVisible" :title="detailTitle" width="1040px">
      <el-table v-loading="detailLoading" :data="detailRows" stripe border max-height="480" size="small">
        <el-table-column prop="ts" label="时间" min-width="160">
          <template #default="{ row }">{{ fmtTime(row.ts) }}</template>
        </el-table-column>
        <el-table-column prop="model_id" label="模型" min-width="140" />
        <el-table-column prop="role" label="角色" width="70" />
        <el-table-column prop="source" label="来源" width="90" />
        <el-table-column label="输入" width="90" align="right">
          <template #default="{ row }">{{ fmtNum(row.input_tokens) }}</template>
        </el-table-column>
        <el-table-column label="命中缓存" width="90" align="right">
          <template #default="{ row }">{{ fmtNum(row.cache_read_tokens) }}</template>
        </el-table-column>
        <el-table-column label="写入缓存" width="90" align="right">
          <template #default="{ row }">{{ fmtNum(row.cache_write_tokens) }}</template>
        </el-table-column>
        <el-table-column label="输出" width="90" align="right">
          <template #default="{ row }">{{ fmtNum(row.output_tokens) }}</template>
        </el-table-column>
        <el-table-column label="耗时" width="90" align="right">
          <template #default="{ row }">{{ (row.duration_ms / 1000).toFixed(1) }}s</template>
        </el-table-column>
        <el-table-column label="金额" width="100" align="right">
          <template #default="{ row }">{{ fmtCost(row.cost) }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 单价设置：居中大窗 -->
    <el-dialog
      v-model="pricingOpen"
      title="单价设置"
      width="1100px"
      top="6vh"
      class="usage-page pricing-dialog"
    >
      <div class="pricing-drawer-body">
        <div v-if="unpricedModels.length > 0" class="unpriced-in-drawer">
          <p class="unpriced-in-drawer-title">以下 {{ unpricedModels.length }} 个模型还没有设置价格，点名称直接添加：</p>
          <div class="unpriced-in-drawer-tags">
            <el-tag
              v-for="m in unpricedModels"
              :key="m"
              class="unpriced-in-drawer-tag"
              @click="openPriceDialog(m)"
            >{{ m }}</el-tag>
          </div>
        </div>
        <div class="pricing-callout">
          <p class="pricing-callout-title">价格说明</p>
          <p>
            每个模型需要设置输入、输出等价格后，才能统计出费用；没设置的模型费用会显示为「—」。
            单位是「元 / 百万 tokens」，调整价格就新增一条更晚生效的记录，历史账单不受影响。
          </p>
        </div>

        <div class="pricing-toolbar">
          <el-button type="primary" @click="openPriceDialog()">添加价格</el-button>
          <span v-if="prices.length === 0 && !pricingLoading" class="pricing-empty-hint">
            还没有设置任何价格，点「添加价格」开始
          </span>
        </div>

        <!-- 按模型合并：一个模型一行，三档价格并列 -->
        <el-table v-loading="pricingLoading" :data="priceGroups" stripe max-height="520">
          <el-table-column prop="model" label="模型" min-width="200">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ row.model }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="输入（未命中缓存）" width="150" align="right">
            <template #default="{ row }">{{ fmtPrice(row.input) }}</template>
          </el-table-column>
          <el-table-column label="命中缓存" width="110" align="right">
            <template #default="{ row }">{{ fmtPrice(row.cache_read) }}</template>
          </el-table-column>
          <el-table-column label="输出" width="110" align="right">
            <template #default="{ row }">{{ fmtPrice(row.output) }}</template>
          </el-table-column>
          <el-table-column label="写入缓存" width="110" align="right">
            <template #default="{ row }">{{ row.cache_write ?? '—' }}</template>
          </el-table-column>
          <el-table-column prop="effective_from" label="生效日期" width="115" />
          <el-table-column prop="note" label="备注" min-width="170" show-overflow-tooltip />
        </el-table>
        <p class="pricing-unit-hint">表中价格单位均为「元 / 百万 tokens」</p>
      </div>
      <template #footer>
        <el-button @click="pricingOpen = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 添加价格弹窗：三档价格一行录完 -->
    <el-dialog v-model="priceVisible" title="添加价格" width="560px" append-to-body class="usage-page">
      <el-form label-width="88px">
        <el-form-item label="模型">
          <el-select
            v-model="priceForm.model"
            filterable
            allow-create
            default-first-option
            placeholder="选择模型"
            style="width: 100%"
          >
            <el-option v-for="m in modelKeyOptions.models" :key="m" :value="m" :label="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="价格">
          <div class="price-grid">
            <div class="price-cell">
              <span class="price-cell-label">输入（未命中缓存）</span>
              <el-input-number v-model="priceForm.input" :min="0" :precision="4" :controls="false" style="width: 100%" />
            </div>
            <div class="price-cell">
              <span class="price-cell-label">命中缓存</span>
              <el-input-number v-model="priceForm.cache_read" :min="0" :precision="4" :controls="false" style="width: 100%" />
            </div>
            <div class="price-cell">
              <span class="price-cell-label">输出</span>
              <el-input-number v-model="priceForm.output" :min="0" :precision="4" :controls="false" style="width: 100%" />
            </div>
            <div class="price-cell">
              <span class="price-cell-label">写入缓存（选填）</span>
              <el-input-number
                v-model="priceForm.cache_write"
                :min="0"
                :precision="4"
                :controls="false"
                placeholder="—"
                style="width: 100%"
              />
            </div>
          </div>
          <div class="form-unit-hint">单位：元 / 百万 tokens（美元渠道请先换算成人民币）</div>
        </el-form-item>
        <el-form-item label="生效日期">
          <el-date-picker v-model="priceForm.effective_from" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="priceForm.note" placeholder="如：美元价 $5，汇率 7.1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="priceVisible = false">取消</el-button>
        <el-button type="primary" :loading="priceSaving" @click="handleAddPrice">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  api, downloadUsageCsv,
  type PriceRow, type UsageCallRow, type UsageSessionRow, type UsageSummaryRow, type UsageTotals,
} from '@/api/http'

const today = new Date().toISOString().slice(0, 10)
const monthStart = today.slice(0, 8) + '01'

const range = ref<[string, string]>([monthStart, today])
const granularity = ref<'day' | 'month'>('day')
const groupBy = ref<string[]>(['user', 'bucket'])
const includeSub = ref(true)
const activeTab = ref('summary')

const loading = ref(false)
const rows = ref<UsageSummaryRow[]>([])
const totals = ref<UsageTotals | null>(null)

const sessionsLoading = ref(false)
const topSessions = ref<UsageSessionRow[]>([])

const pricingLoading = ref(false)
const prices = ref<PriceRow[]>([])
const pricingOpen = ref(false)

const detailVisible = ref(false)
const detailLoading = ref(false)
const detailTitle = ref('')
const detailRows = ref<UsageCallRow[]>([])

const priceVisible = ref(false)
const priceSaving = ref(false)
// 一个模型一次录齐三档价格（写入缓存选填），保存时拆成多条记录
const priceForm = ref({
  model: '',
  input: 0,
  cache_read: 0,
  output: 0,
  cache_write: undefined as number | undefined,
  effective_from: today,
  note: '',
})

// 模型下拉选项：来自 /models 的 model_id
const modelKeyOptions = ref<{ models: string[] }>({ models: [] })

const exporting = ref(false)

const displayDims = computed(() => {
  // '时间'列在汇总表固定显示（时间桶是每行的天然属性，不该被筛选藏掉）
  const dims = groupBy.value.filter((d) => d !== 'bucket')
  return ['bucket', ...dims]
})
const totalTokens = computed(() =>
  // input_tokens 已含命中/写入缓存明细（langchain 口径），直接相加会重复统计
  (totals.value?.input_tokens ?? 0) + (totals.value?.output_tokens ?? 0)
)

// 汇总行里金额为 null 的模型 = 没设置价格（按模型名去重）
const unpricedModels = computed(() => {
  const names = new Set<string>()
  for (const row of rows.value) {
    if (row.cost === null && row.model_id) names.add(row.model_id)
  }
  return [...names]
})

function dimLabel(dim: string): string {
  const labels: Record<string, string> = {
    user: '用户', agent: 'Agent', model_id: '模型', raw_model_id: '底层模型', bucket: '时间',
  }
  return labels[dim] || dim
}

// 按模型合并：一个模型一行，三档价格并列展示
interface PriceGroupRow {
  model: string
  input?: number
  cache_read?: number
  output?: number
  cache_write?: number
  effective_from: string
  note: string
}
const priceGroups = computed<PriceGroupRow[]>(() => {
  // 按（模型 × 生效日期）合并：同一模型的不同生效版本各占一行，
  // 否则旧版本价格被新版本覆盖、日期却还显示旧的，误导
  const map = new Map<string, PriceGroupRow>()
  for (const p of prices.value) {
    const key = `${p.model}|${p.effective_from ?? ''}`
    let g = map.get(key)
    if (!g) {
      g = { model: p.model, effective_from: p.effective_from ?? '', note: p.note ?? '' }
      map.set(key, g)
    }
    if (p.kind === 'input' || p.kind === 'cache_read' || p.kind === 'output' || p.kind === 'cache_write') {
      g[p.kind] = p.price_per_1m
    }
  }
  return [...map.values()]
})

function fmtPrice(n: number | undefined): string {
  return n === undefined ? '—' : String(n)
}

function fmtNum(n: number | undefined): string {
  return (n ?? 0).toLocaleString('zh-CN')
}

function fmtCost(c: number | null | undefined): string {
  if (c === null || c === undefined) return '—'
  // 后端保留 4 位小数；小额费用 2 位会显示 ¥0.00，智能提升精度
  return `¥${c < 0.01 && c > 0 ? c.toFixed(4) : c.toFixed(2)}`
}

function fmtTime(ts: string | null): string {
  if (!ts) return '—'
  try {
    return new Date(ts).toLocaleString('zh-CN')
  } catch {
    return ts
  }
}

async function loadSummary() {
  loading.value = true
  try {
    const [from, to] = range.value
    const result = await api.getUsageSummary({
      from, to, group_by: groupBy.value.join(',') || 'bucket',
      granularity: granularity.value, include_sub: includeSub.value,
    })
    rows.value = result.rows
    totals.value = await api.getUsageTotals({
      from, to, include_sub: includeSub.value,
    })
  } catch (e: any) {
    ElMessage.error(e.message || '加载用量失败')
  } finally {
    loading.value = false
  }
}

async function loadSessions() {
  sessionsLoading.value = true
  try {
    const [from, to] = range.value
    const result = await api.getUsageTopSessions({ from, to, include_sub: includeSub.value })
    topSessions.value = result.rows
  } catch (e: any) {
    ElMessage.error(e.message || '加载会话列表失败')
  } finally {
    sessionsLoading.value = false
  }
}

async function loadPricing() {
  pricingLoading.value = true
  try {
    prices.value = (await api.getPricing()).rows
  } catch (e: any) {
    ElMessage.error(e.message || '加载价格失败')
  } finally {
    pricingLoading.value = false
  }
}

async function loadModelKeys() {
  try {
    const models = await api.getModels()
    const ids = new Set<string>()
    for (const m of models) {
      if (m.model_id) ids.add(m.model_id)
    }
    modelKeyOptions.value = { models: [...ids] }
  } catch {
    // 下拉选项加载失败不阻塞页面，弹窗里仍可手输
  }
}

async function loadAll() {
  await Promise.all([loadSummary(), loadSessions(), loadPricing(), loadModelKeys()])
}

function openDetail(row: UsageSessionRow) {
  detailTitle.value = `会话明细：${row.title}`
  detailVisible.value = true
  detailLoading.value = true
  api.getUsageSessionDetail(row.session_id)
    .then((r) => { detailRows.value = r.rows })
    .catch((e: any) => ElMessage.error(e.message || '加载明细失败'))
    .finally(() => { detailLoading.value = false })
}

function openPriceDialog(model?: unknown) {
  priceForm.value = {
    model: typeof model === 'string' ? model : '',
    input: 0,
    cache_read: 0,
    output: 0,
    cache_write: undefined,
    effective_from: today,
    note: '',
  }
  priceVisible.value = true
}

async function handleAddPrice() {
  if (!priceForm.value.model.trim()) {
    ElMessage.warning('请选择模型')
    return
  }
  priceSaving.value = true
  try {
    const base = {
      model: priceForm.value.model.trim(),
      effective_from: priceForm.value.effective_from,
      note: priceForm.value.note,
    }
    const rows = [
      { ...base, kind: 'input', price_per_1m: priceForm.value.input },
      { ...base, kind: 'cache_read', price_per_1m: priceForm.value.cache_read },
      { ...base, kind: 'output', price_per_1m: priceForm.value.output },
    ]
    if (priceForm.value.cache_write !== undefined && priceForm.value.cache_write > 0) {
      rows.push({ ...base, kind: 'cache_write', price_per_1m: priceForm.value.cache_write })
    }
    for (const row of rows) {
      await api.addPricing(row)
    }
    ElMessage.success('价格已保存')
    priceVisible.value = false
    await Promise.all([loadPricing(), loadSummary()])
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    priceSaving.value = false
  }
}

async function handleExport() {
  exporting.value = true
  try {
    const [from, to] = range.value
    await downloadUsageCsv({
      from, to, group_by: groupBy.value.join(',') || 'bucket',
      granularity: granularity.value, include_sub: includeSub.value,
    })
  } catch (e: any) {
    ElMessage.error(e.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.usage-admin {
  padding: 20px 28px;
  max-width: 1280px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}
.page-title h2 {
  margin: 0 0 4px;
}
.page-subtitle {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.page-actions {
  display: flex;
  gap: 0;
  align-items: center;
}
.btn-icon {
  margin-right: 4px;
  font-weight: 700;
}
.pricing-badge {
  margin-left: 8px;
  vertical-align: middle;
}
.unpriced-alert {
  margin-bottom: 14px;
}
.unpriced-tag {
  margin: 0 4px;
}
.unpriced-more {
  margin-right: 4px;
}
.filter-bar {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 16px;
  padding: 12px 14px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  background: var(--el-bg-color);
}
/* 筛选控件：定宽紧凑排列，禁止被拉伸通栏 */
.usage-page .filter-bar .el-date-editor,
.usage-page .filter-bar .el-select {
  flex: none;
}
.usage-page .f-date {
  width: 300px;
}
.usage-page .f-gran {
  width: 104px;
}
.usage-page .f-group {
  min-width: 230px;
  max-width: 280px;
}
/* 输入框/选择框：圆角 + 深色底 + 靛蓝描边，聚焦变亮 */
.usage-page .filter-bar .el-input__wrapper,
.usage-page .filter-bar .el-select__wrapper {
  border-radius: 8px;
  background: var(--el-fill-color-light);
  box-shadow: 0 0 0 1px color-mix(in srgb, #818cf8 28%, var(--el-border-color)) inset;
}
.usage-page .filter-bar .el-input__wrapper:hover,
.usage-page .filter-bar .el-select__wrapper:hover {
  box-shadow: 0 0 0 1px color-mix(in srgb, #818cf8 55%, var(--el-border-color)) inset;
}
.usage-page .filter-bar .el-input__wrapper.is-focus,
.usage-page .filter-bar .el-select__wrapper.is-focused {
  box-shadow: 0 0 0 1px #818cf8 inset;
}
.cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 18px;
}
.stat-card {
  position: relative;
  padding: 14px 18px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-bg-color);
  overflow: hidden;
}
.stat-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--card-accent, var(--el-color-primary));
}
.stat-card--cost {
  --card-accent: #6366f1;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), transparent 65%);
  border-color: rgba(99, 102, 241, 0.35);
}
.stat-card--cost .stat-value {
  color: #818cf8;
  font-size: 26px;
}
.cost-strong {
  color: #818cf8;
  font-weight: 600;
}
.stat-card--tokens {
  --card-accent: #06b6d4;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.10), transparent 65%);
  border-color: rgba(6, 182, 212, 0.30);
}
.stat-card--tokens .stat-value {
  color: #22d3ee;
}
.stat-card--users {
  --card-accent: #f59e0b;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.10), transparent 65%);
  border-color: rgba(245, 158, 11, 0.30);
}
.stat-card--users .stat-value {
  color: #fbbf24;
}
.stat-card--calls {
  --card-accent: #10b981;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.10), transparent 65%);
  border-color: rgba(16, 185, 129, 0.30);
}
.stat-card--calls .stat-value {
  color: #34d399;
}
/* 主操作按钮：彩色渐变背景，暗色主题下也要醒目。
   放在非 scoped 块：抽屉/弹窗会 teleport 到 body 外，scoped :deep 够不到，
   统一用 .usage-page 类圈定作用范围（页面根节点 + drawer/dialog class）。 */
.usage-page .el-button--primary:not(.is-link) {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  color: #fff;
  font-weight: 500;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(99, 102, 241, 0.35);
}
.usage-page .el-button--primary:not(.is-link):hover {
  background: linear-gradient(135deg, #818cf8, #a78bfa);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.5);
  color: #fff;
}
.usage-page .el-button--primary:not(.is-link):active {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
}
/* 次级按钮：彩色渐变底（青蓝系），与主按钮区分但不再是灰底 */
.usage-page .el-button:not(.el-button--primary):not(.is-link) {
  background: linear-gradient(135deg, #0ea5e9, #06b6d4);
  border: none;
  color: #fff;
  font-weight: 500;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(14, 165, 233, 0.3);
}
.usage-page .el-button:not(.el-button--primary):not(.is-link):hover {
  background: linear-gradient(135deg, #38bdf8, #22d3ee);
  box-shadow: 0 4px 16px rgba(14, 165, 233, 0.45);
  color: #fff;
}
.usage-page .el-button:not(.el-button--primary):not(.is-link):active {
  background: linear-gradient(135deg, #0284c7, #0891b2);
}
.usage-page .el-button:not(.el-button--primary):not(.is-link):focus-visible {
  outline: 2px solid #38bdf8;
  outline-offset: 1px;
}
/* 添加价格：三档价格一行并列 */
.usage-page .price-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px 14px;
  width: 100%;
}
.usage-page .price-cell-label {
  display: block;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}
.usage-page .form-unit-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 6px;
}
.usage-page .pricing-unit-hint {
  margin: 8px 2px 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>

<style scoped>
.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 6px;
}
.stat-value {
  font-size: 22px;
  font-weight: 600;
}
.unpriced {
  color: var(--el-text-color-secondary);
}
.pricing-drawer-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.unpriced-in-drawer {
  padding: 12px 14px;
  border: 1px solid var(--el-color-warning-light-5);
  border-left: 3px solid var(--el-color-warning);
  border-radius: 6px;
  background: var(--el-color-warning-light-9);
}
.unpriced-in-drawer-title {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}
.unpriced-in-drawer-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.unpriced-in-drawer-tag {
  cursor: pointer;
  font-size: 13px;
}
.unpriced-in-drawer-tag:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}
.pricing-callout {
  padding: 12px 14px;
  border: 1px solid var(--el-border-color-light);
  border-left: 3px solid var(--el-color-primary);
  border-radius: 6px;
  background: var(--el-fill-color-light);
  font-size: 13px;
  line-height: 1.7;
}
.pricing-callout p {
  margin: 0;
}
.pricing-callout-title {
  font-weight: 600;
  margin-bottom: 4px;
}
.pricing-callout-hint {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.pricing-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}
.pricing-empty-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
