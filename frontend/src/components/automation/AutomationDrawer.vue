<template>
  <el-drawer
    v-model="visible"
    title="自动化任务"
    direction="rtl"
    size="min(560px, 100vw)"
    class="automation-drawer"
    :show-close="false"
    :destroy-on-close="false"
    @close="handleDrawerClose"
  >
    <template #header>
      <div class="automation-drawer-header">
        <div>
          <h3>自动化任务</h3>
          <p>让 Agent 按计划自动执行任务</p>
        </div>
        <div class="automation-header-actions">
          <button class="create-task-btn" type="button" @click="startCreate">
            <el-icon><Plus /></el-icon>
            新建
          </button>
          <button class="drawer-close-btn" type="button" title="关闭自动化任务面板" aria-label="关闭自动化任务面板" @click="closeDrawer">
            <el-icon><Close /></el-icon>
            <span>关闭</span>
          </button>
        </div>
      </div>
    </template>

    <div class="automation-tabs" role="tablist">
      <button
        type="button"
        :class="{ active: activeTab === 'tasks' }"
        role="tab"
        :aria-selected="activeTab === 'tasks'"
        @click="activeTab = 'tasks'"
      >
        已配置
        <span class="tab-count">{{ automationStore.tasks.length }}</span>
      </button>
      <button
        type="button"
        :class="{ active: activeTab === 'runs' }"
        role="tab"
        :aria-selected="activeTab === 'runs'"
        @click="switchToRuns"
      >
        执行历史
        <span class="tab-count">{{ automationStore.runTotal }}</span>
      </button>
    </div>

    <div v-if="automationStore.error" class="automation-error">
      {{ automationStore.error }}
    </div>

    <form v-if="showForm" class="automation-form" @submit.prevent="saveTask">
      <div class="form-heading">
        <div>
          <span class="form-kicker">{{ editingTaskId ? '编辑任务' : '新建任务' }}</span>
          <h4>{{ editingTaskId ? form.name || '自动化任务' : '配置一个自动执行任务' }}</h4>
        </div>
        <button
          class="form-cancel-btn"
          type="button"
          :title="editingTaskId ? '取消编辑' : '取消创建'"
          :aria-label="editingTaskId ? '取消编辑' : '取消创建'"
          @click="cancelForm"
      >
          <el-icon><Close /></el-icon>
          <span>{{ editingTaskId ? '取消编辑' : '取消创建' }}</span>
        </button>
      </div>

      <label class="field-label" for="automation-task-name">任务名称</label>
      <el-input id="automation-task-name" v-model="form.name" maxlength="120" placeholder="例如：每日 AI 新闻" />

      <label class="field-label" for="automation-agent">选择 Agent</label>
      <el-select id="automation-agent" v-model="form.agent_id" class="full-control" filterable>
        <el-option
          v-for="agent in availableAgents"
          :key="agent.id"
          :label="agent.display_name || agent.name"
          :value="agent.id"
        >
          <div class="agent-option">
            <span>{{ agent.display_name || agent.name }}</span>
            <small>{{ agent.source === 'code' ? '代码 Agent' : agent.id }}</small>
          </div>
        </el-option>
      </el-select>

      <label class="field-label">执行周期</label>
      <el-select v-model="form.schedule_type" class="full-control" @change="resetScheduleDefaults">
        <el-option label="一次性" value="one_time" />
        <el-option label="每隔一段时间" value="interval" />
        <el-option label="每天指定时间" value="daily" />
        <el-option label="每周指定时间" value="weekly" />
      </el-select>

      <div v-if="form.schedule_type === 'one_time'" class="schedule-fields">
        <label class="field-label" for="automation-run-at">执行时间</label>
        <input id="automation-run-at" v-model="form.run_at" class="native-control" type="datetime-local" required />
      </div>

      <div v-else-if="form.schedule_type === 'interval'" class="schedule-fields interval-fields">
        <div>
          <label class="field-label" for="automation-interval-value">间隔</label>
          <el-input-number id="automation-interval-value" v-model="form.interval_value" :min="1" :max="99999" controls-position="right" />
        </div>
        <div>
          <label class="field-label">单位</label>
          <el-select v-model="form.interval_unit" class="full-control">
            <el-option label="分钟" value="minutes" />
            <el-option label="小时" value="hours" />
            <el-option label="天" value="days" />
          </el-select>
        </div>
        <div class="interval-start-field">
          <label class="field-label" for="automation-start-at">开始时间（可选）</label>
          <input id="automation-start-at" v-model="form.start_at" class="native-control" type="datetime-local" />
        </div>
      </div>

      <div v-else class="schedule-fields calendar-fields">
        <div v-if="form.schedule_type === 'weekly'">
          <label class="field-label">星期</label>
          <el-select v-model="form.day_of_week" class="full-control">
            <el-option v-for="day in WEEKDAYS" :key="day.value" :label="day.label" :value="day.value" />
          </el-select>
        </div>
        <div>
          <label class="field-label" for="automation-time">执行时间</label>
          <input id="automation-time" v-model="form.time" class="native-control" type="time" required />
        </div>
      </div>

      <div class="timezone-hint">
        <el-icon><Clock /></el-icon>
        使用后端运行环境时区{{ automationStore.timezone ? `（${automationStore.timezone}）` : '' }}
      </div>

      <label class="field-label" for="automation-prompt">任务内容</label>
      <el-input
        id="automation-prompt"
        v-model="form.prompt"
        type="textarea"
        :rows="7"
        maxlength="100000"
        show-word-limit
        resize="vertical"
        placeholder="请描述 Agent 需要自动完成的任务，以及期望的输出格式。"
      />

      <section class="notification-section" aria-label="群通知">
        <div class="notification-section-header">
          <div>
            <span class="form-kicker">群通知</span>
            <p>任务完成或失败后，发送结果到指定群。</p>
          </div>
          <button class="add-target-btn" type="button" @click="addNotificationTarget">
            <el-icon><Plus /></el-icon>
            添加群
          </button>
        </div>

        <div v-if="form.notification_targets.length === 0" class="notification-empty">
          未配置群通知
        </div>

        <article v-for="(target, index) in form.notification_targets" :key="index" class="notification-target">
          <div class="notification-target-header">
            <strong>通知目标 {{ index + 1 }}</strong>
            <button
              class="remove-target-btn"
              type="button"
              title="移除通知目标"
              :aria-label="`移除通知目标 ${index + 1}`"
              @click="removeNotificationTarget(index)"
            >
              <el-icon><Delete /></el-icon>
            </button>
          </div>
          <div class="notification-target-grid">
            <div>
              <label class="field-label" :for="`notification-platform-${index}`">平台</label>
              <el-select
                :id="`notification-platform-${index}`"
                v-model="target.platform"
                class="full-control"
                @change="clearUnusedTargetFields(target)"
              >
                <el-option label="企业微信" value="wecom" />
                <el-option label="飞书" value="feishu" />
                <el-option label="钉钉" value="dingtalk" />
              </el-select>
            </div>
            <div>
              <label class="field-label" :for="`notification-name-${index}`">群名称</label>
              <el-input :id="`notification-name-${index}`" v-model="target.name" maxlength="120" placeholder="例如：研发日报群" />
            </div>
            <div class="notification-target-wide">
              <label class="field-label" :for="`notification-webhook-${index}`">Webhook</label>
              <el-input
                :id="`notification-webhook-${index}`"
                v-model="target.webhook"
                maxlength="2000"
                placeholder="粘贴该群机器人的官方 Webhook 地址"
              />
            </div>
            <div v-if="target.platform === 'dingtalk'" class="notification-target-wide">
              <label class="field-label" :for="`notification-secret-${index}`">钉钉签名密钥（可选）</label>
              <el-input
                :id="`notification-secret-${index}`"
                v-model="target.dingtalk_secret"
                maxlength="1000"
                show-password
                placeholder="机器人启用签名校验时填写"
              />
            </div>
          </div>
          <div class="notification-target-actions">
            <button
              class="test-notification-btn"
              type="button"
              :disabled="testingTargetIndex === index || !canTestNotificationTarget(target)"
              @click="testNotificationTarget(target, index)"
            >
              <el-icon><Promotion /></el-icon>
              {{ testingTargetIndex === index ? '发送中...' : '测试发送' }}
            </button>
          </div>
        </article>
      </section>

      <div class="form-actions">
        <button class="secondary-btn" type="button" @click="cancelForm">取消</button>
        <button class="primary-btn" type="submit" :disabled="automationStore.saving || !canSave">
          {{ automationStore.saving ? '保存中...' : editingTaskId ? '保存修改' : '创建任务' }}
        </button>
      </div>
    </form>

    <template v-else-if="activeTab === 'tasks'">
      <div v-if="automationStore.loading" class="automation-loading">加载中...</div>
      <div v-else-if="automationStore.tasks.length === 0" class="automation-empty">
        <div class="empty-icon">
          <el-icon :size="25"><Clock /></el-icon>
        </div>
        <strong>还没有自动化任务</strong>
        <span>选择一个 Agent，让它按计划自动工作</span>
        <button class="primary-btn empty-create-btn" type="button" @click="startCreate">创建第一个任务</button>
      </div>
      <div v-else class="task-list">
        <article v-for="task in automationStore.tasks" :key="task.id" class="task-item">
          <div class="task-item-top">
            <div class="task-title-wrap">
              <span class="task-status-dot" :class="task.enabled ? 'enabled' : 'paused'"></span>
              <div>
                <h4>{{ task.name }}</h4>
                <p>{{ task.agent_name || task.agent_id }} · {{ formatSchedule(task) }}</p>
              </div>
            </div>
            <el-switch
              :model-value="task.enabled"
              size="small"
              :loading="actionTaskId === task.id && actionType === 'toggle'"
              @change="toggleTask(task)"
            />
          </div>
          <p class="task-prompt">{{ task.prompt }}</p>
          <div class="task-meta">
            <span :class="['run-status', task.last_status || 'none']">{{ statusLabel(task.last_status) }}</span>
            <span v-if="task.notification_targets.length">群通知 {{ task.notification_targets.length }} 个</span>
            <span v-if="task.next_run_at">下次 {{ formatDate(task.next_run_at) }}</span>
            <span v-else-if="!task.enabled">已暂停</span>
          </div>
          <div class="task-actions">
            <button class="run-action" type="button" title="立即执行" :disabled="actionTaskId === task.id" @click="runTask(task)">
              <el-icon><VideoPlay /></el-icon>
              {{ actionTaskId === task.id && actionType === 'run' ? '执行中...' : '立即执行' }}
            </button>
            <button class="edit-action" type="button" title="编辑任务" :disabled="actionTaskId === task.id" @click="startEdit(task)">
              <el-icon><EditPen /></el-icon>
              编辑
            </button>
            <button class="danger-action" type="button" title="删除任务" :disabled="actionTaskId === task.id" @click="deleteTask(task)">
              <el-icon><Delete /></el-icon>
              删除
            </button>
          </div>
        </article>
      </div>
    </template>

    <template v-else>
      <div v-if="automationStore.runs.length === 0" class="automation-empty history-empty">
        <strong>还没有执行记录</strong>
        <span>任务执行后，结果会出现在这里</span>
      </div>
      <div v-else class="run-list">
        <article v-for="run in automationStore.runs" :key="run.id" class="run-item">
          <div class="run-item-top">
            <div>
              <h4>{{ automationStore.getTaskName(run.task_id) }}</h4>
              <p>{{ formatDate(run.scheduled_at) }}</p>
            </div>
            <span :class="['run-status', run.status]">{{ statusLabel(run.status) }}</span>
          </div>
          <p v-if="run.error" class="run-error">{{ run.error }}</p>
          <p v-if="run.notification_status !== 'not_configured'" :class="['notification-result', run.notification_status]">
            {{ notificationStatusLabel(run.notification_status) }}
            <span v-if="run.notification_error">：{{ run.notification_error }}</span>
          </p>
          <div class="run-item-bottom">
            <span v-if="run.finished_at">完成于 {{ formatDate(run.finished_at) }}</span>
            <span v-else>执行中</span>
            <div class="run-actions">
              <button v-if="run.session_id" class="view-action" type="button" @click="openRunSession(run)">
                <el-icon><View /></el-icon>
                查看会话
              </button>
              <button v-if="run.status === 'failed'" class="rerun-action" type="button" :disabled="actionRunId === run.id" @click="rerun(run)">
                {{ actionRunId === run.id ? '重新执行中...' : '重新执行' }}
              </button>
            </div>
          </div>
        </article>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Clock, Close, Delete, EditPen, Plus, Promotion, VideoPlay, View } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useAgentsStore } from '@/stores/agents'
import {
  useAutomationStore,
  type AutomationNotificationTarget,
  type AutomationRun,
  type AutomationScheduleType,
  type AutomationTask,
} from '@/stores/automation'
import { useSessionsStore } from '@/stores/sessions'

const visible = ref(false)
const activeTab = ref<'tasks' | 'runs'>('tasks')
const formVisible = ref(false)
const editingTaskId = ref<string | null>(null)
const actionTaskId = ref<string | null>(null)
const actionType = ref<'run' | 'toggle' | null>(null)
const actionRunId = ref<string | null>(null)
const testingTargetIndex = ref<number | null>(null)

const agentsStore = useAgentsStore()
const automationStore = useAutomationStore()
const sessionsStore = useSessionsStore()
const router = useRouter()

const WEEKDAYS = [
  { value: 0, label: '星期一' },
  { value: 1, label: '星期二' },
  { value: 2, label: '星期三' },
  { value: 3, label: '星期四' },
  { value: 4, label: '星期五' },
  { value: 5, label: '星期六' },
  { value: 6, label: '星期日' },
]

const form = reactive({
  name: '',
  agent_id: '',
  prompt: '',
  schedule_type: 'daily' as AutomationScheduleType,
  run_at: '',
  interval_value: 1,
  interval_unit: 'hours',
  start_at: '',
  time: '09:00',
  day_of_week: 0,
  notification_targets: [] as AutomationNotificationTarget[],
})

const availableAgents = computed(() => agentsStore.agents)
const showForm = computed(() => formVisible.value)
const canSave = computed(() => {
  if (!form.name.trim() || !form.agent_id || !form.prompt.trim()) return false
  if (!form.notification_targets.every(canTestNotificationTarget)) return false
  if (form.schedule_type === 'one_time') return Boolean(form.run_at)
  if (form.schedule_type === 'interval') return form.interval_value > 0
  return Boolean(form.time)
})

function open() {
  visible.value = true
  activeTab.value = 'tasks' 
  automationStore.error = ''
  void automationStore.loadTasks()
  void automationStore.loadRuns()
  void automationStore.loadTimezone()
}

function resetForm() {
  editingTaskId.value = null
  form.name = ''
  form.agent_id = agentsStore.currentAgentId || availableAgents.value[0]?.id || ''
  form.prompt = ''
  form.schedule_type = 'daily'
  form.run_at = ''
  form.interval_value = 1
  form.interval_unit = 'hours'
  form.start_at = ''
  form.time = '09:00'
  form.day_of_week = 0
  form.notification_targets = []
}

function startCreate() {
  resetForm()
  formVisible.value = true
  activeTab.value = 'tasks'
}

function startEdit(task: AutomationTask) {
  formVisible.value = true
  editingTaskId.value = task.id
  form.name = task.name
  form.agent_id = task.agent_id
  form.prompt = task.prompt
  form.schedule_type = task.schedule_type
  form.run_at = String(task.schedule_config.run_at || '').slice(0, 16)
  form.interval_value = Number(task.schedule_config.value || 1)
  form.interval_unit = String(task.schedule_config.unit || 'hours')
  form.start_at = String(task.schedule_config.start_at || '').slice(0, 16)
  form.time = String(task.schedule_config.time || '09:00')
  form.day_of_week = Number(task.schedule_config.day_of_week || 0)
  form.notification_targets = (task.notification_targets || []).map(target => ({ ...target }))
}

function cancelForm() {
  resetForm()
  formVisible.value = false
}

function closeDrawer() {
  visible.value = false
  handleDrawerClose()
}

function handleDrawerClose() {
  resetForm()
  formVisible.value = false
}

function resetScheduleDefaults() {
  if (form.schedule_type === 'daily' || form.schedule_type === 'weekly') {
    if (!form.time) form.time = '09:00'
  }
}

function buildScheduleConfig() {
  if (form.schedule_type === 'one_time') return { run_at: form.run_at }
  if (form.schedule_type === 'interval') {
    return {
      value: form.interval_value,
      unit: form.interval_unit,
      ...(form.start_at ? { start_at: form.start_at } : {}),
    }
  }
  if (form.schedule_type === 'weekly') return { day_of_week: form.day_of_week, time: form.time }
  return { time: form.time }
}

async function saveTask() {
  if (!canSave.value) return
  try {
    const payload = {
      name: form.name,
      agent_id: form.agent_id,
      prompt: form.prompt,
      schedule_type: form.schedule_type,
      schedule_config: buildScheduleConfig(),
      notification_targets: form.notification_targets.map(target => ({
        ...target,
        dingtalk_secret: target.dingtalk_secret || undefined,
      })),
    }
    if (editingTaskId.value) {
      await automationStore.updateTask(editingTaskId.value, payload)
      ElMessage.success('自动化任务已更新')
    } else {
      await automationStore.createTask(payload)
      ElMessage.success('自动化任务已创建')
    }
    resetForm()
    formVisible.value = false
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '保存自动化任务失败')
  }
}

function addNotificationTarget() {
  form.notification_targets.push({
    platform: 'wecom',
    name: '',
    webhook: '',
    dingtalk_secret: '',
  })
}

function removeNotificationTarget(index: number) {
  form.notification_targets.splice(index, 1)
}

function clearUnusedTargetFields(target: AutomationNotificationTarget) {
  if (target.platform !== 'dingtalk') target.dingtalk_secret = ''
}

function canTestNotificationTarget(target: AutomationNotificationTarget) {
  return Boolean(target.name.trim() && target.webhook.trim())
}

async function testNotificationTarget(target: AutomationNotificationTarget, index: number) {
  if (!canTestNotificationTarget(target)) return
  testingTargetIndex.value = index
  try {
    const result = await automationStore.testNotificationTarget({
      ...target,
      dingtalk_secret: target.dingtalk_secret || undefined,
    })
    if (result.status === 'sent') ElMessage.success(`已发送测试消息到“${target.name}”`)
    else ElMessage.error(result.error || '测试消息发送失败')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '测试消息发送失败')
  } finally {
    testingTargetIndex.value = null
  }
}

async function toggleTask(task: AutomationTask) {
  actionTaskId.value = task.id
  actionType.value = 'toggle'
  try {
    if (task.enabled) await automationStore.pauseTask(task.id)
    else await automationStore.resumeTask(task.id)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '更新任务状态失败')
  } finally {
    actionTaskId.value = null
    actionType.value = null
  }
}

async function runTask(task: AutomationTask) {
  actionTaskId.value = task.id
  actionType.value = 'run'
  try {
    const run = await automationStore.runTask(task.id)
    if (run.status === 'failed') {
      ElMessage.error(run.error || '任务执行失败')
    } else {
      ElMessage.success('任务执行完成')
    }
    activeTab.value = 'runs'
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '任务执行失败')
    await automationStore.loadRuns()
  } finally {
    actionTaskId.value = null
    actionType.value = null
  }
}

async function deleteTask(task: AutomationTask) {
  try {
    await ElMessageBox.confirm(`确定删除“${task.name}”吗？执行历史会保留。`, '删除自动化任务', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await automationStore.deleteTask(task.id)
    ElMessage.success('自动化任务已删除')
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') ElMessage.error(e instanceof Error ? e.message : '删除任务失败')
  }
}

async function switchToRuns() {
  activeTab.value = 'runs'
  await automationStore.loadRuns()
}

async function rerun(run: AutomationRun) {
  actionRunId.value = run.id
  try {
    await automationStore.rerun(run.id)
    ElMessage.success('已重新执行任务')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '重新执行失败')
  } finally {
    actionRunId.value = null
  }
}

async function openRunSession(run: AutomationRun) {
  if (!run.session_id) return
  await sessionsStore.init()
  await router.push({ name: 'chat', params: { sessionId: run.session_id } })
  visible.value = false
}

function formatSchedule(task: AutomationTask) {
  const config = task.schedule_config || {}
  if (task.schedule_type === 'one_time') return `一次性 ${formatDate(String(config.run_at || ''))}`
  if (task.schedule_type === 'interval') {
    const unit = { minutes: '分钟', hours: '小时', days: '天' }[String(config.unit)] || String(config.unit)
    return `每 ${config.value || 1} ${unit}`
  }
  if (task.schedule_type === 'weekly') return `每${WEEKDAYS[Number(config.day_of_week) || 0]?.label.replace('星期', '周') || '周一'} ${config.time || ''}`
  return `每天 ${config.time || ''}`
}

function formatDate(value: string) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(date)
}

function statusLabel(status: string | null) {
  return {
    pending: '等待执行',
    running: '执行中',
    success: '成功',
    failed: '失败',
    skipped: '已跳过',
    none: '尚未执行',
  }[status || 'none'] || status || '尚未执行'
}

function notificationStatusLabel(status: string) {
  return {
    not_sent: '未推送（任务已跳过）',
    sent: '群通知已发送',
    partial_failed: '群通知部分失败',
    failed: '群通知发送失败',
  }[status] || '未配置群通知'
}

defineExpose({ open })
</script>

<style>
/* 按操作语义分配实心底色：运行=绿、修改=橙、删除=红、中止=青、主行动/查看=蓝。
   底色统一与 #000 混合压深，保证白色文字在亮色与暗色主题下都有足够对比度
   （Element Plus 的 *-dark-2 / *-light-3 在两个主题下明暗方向相反，不能直接用作实心底）。 */
.automation-drawer {
  --automation-run-bg: color-mix(in srgb, var(--el-color-success) 74%, #000);
  --automation-run-bg-hover: color-mix(in srgb, var(--el-color-success) 90%, #000);
  --automation-edit-bg: color-mix(in srgb, var(--el-color-warning) 72%, #000);
  --automation-edit-bg-hover: color-mix(in srgb, var(--el-color-warning) 88%, #000);
  --automation-danger-bg: color-mix(in srgb, var(--el-color-danger) 82%, #000);
  --automation-danger-bg-hover: var(--el-color-danger);
  --automation-cancel-bg: #0e7490;
  --automation-cancel-bg-hover: #0891b2;
}

.automation-drawer .el-drawer__header {
  margin-bottom: 0;
  padding: 20px 22px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.automation-drawer .el-drawer__body {
  padding: 0 22px 24px;
  background: var(--el-bg-color);
}

.automation-drawer-header {
  width: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.automation-header-actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  gap: 8px;
}

.automation-drawer-header h3 {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 20px;
}

.automation-drawer-header p {
  margin: 5px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.create-task-btn,
.primary-btn,
.secondary-btn,
.task-actions button,
.run-actions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: border-color .15s, background .15s, color .15s, box-shadow .15s, opacity .15s;
}

.create-task-btn {
  min-height: 30px;
  padding: 0 11px;
  border-color: var(--el-color-primary);
  background: var(--el-color-primary);
  color: #fff;
  font-size: 12px;
  box-shadow: 0 2px 6px color-mix(in srgb, var(--el-color-primary) 24%, transparent);
}

.drawer-close-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  min-height: 30px;
  padding: 0 11px;
  border: 1px solid var(--el-color-danger);
  border-radius: 6px;
  background: var(--el-color-danger);
  color: #fff;
  white-space: nowrap;
  cursor: pointer;
  font-size: 12px;
  box-shadow: 0 2px 6px color-mix(in srgb, var(--el-color-danger) 30%, transparent);
  transition: border-color .15s, background .15s, color .15s, box-shadow .15s;
}

.drawer-close-btn:hover {
  border-color: var(--el-color-danger-dark-2);
  background: var(--el-color-danger-dark-2);
}

.form-cancel-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  min-height: 30px;
  padding: 0 11px;
  border: 1px solid var(--automation-cancel-bg);
  border-radius: 6px;
  background: var(--automation-cancel-bg);
  color: #fff;
  white-space: nowrap;
  cursor: pointer;
  font-size: 12px;
  box-shadow: 0 2px 6px color-mix(in srgb, var(--automation-cancel-bg) 30%, transparent);
  transition: border-color .15s, background .15s, color .15s, box-shadow .15s;
}

.form-cancel-btn:hover {
  border-color: var(--automation-cancel-bg-hover);
  background: var(--automation-cancel-bg-hover);
}

.drawer-close-btn:active,
.form-cancel-btn:active,
.secondary-btn:active,
.task-actions button:active,
.run-actions button:active {
  transform: translateY(1px);
}

.create-task-btn:hover,
.primary-btn:hover:not(:disabled) {
  border-color: var(--el-color-primary-dark-2);
  background: var(--el-color-primary-dark-2);
}

.create-task-btn:active,
.primary-btn:active:not(:disabled) {
  transform: translateY(1px);
  box-shadow: none;
}

.automation-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px;
  min-height: 42px;
  padding: 4px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-light);
}

.automation-tabs button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  min-height: 32px;
  gap: 6px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 5px;
  background: var(--el-fill-color);
  color: var(--el-text-color-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: border-color .15s, background .15s, color .15s, box-shadow .15s;
}

.automation-tabs button:hover:not(.active) {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-primary);
}

.automation-tabs button.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 1px 4px color-mix(in srgb, var(--el-color-primary) 24%, transparent);
}

.tab-count {
  min-width: 17px;
  padding: 1px 5px;
  border-radius: 10px;
  background: var(--el-fill-color);
  font-size: 11px;
  text-align: center;
}

.automation-tabs button.active .tab-count {
  background: var(--el-color-primary-dark-2);
  color: #fff;
}

.automation-error {
  margin-top: 14px;
  padding: 9px 10px;
  border: 1px solid var(--el-color-danger-light-5);
  border-radius: 6px;
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
  font-size: 12px;
  line-height: 1.5;
}

.automation-form {
  padding-top: 18px;
}

.form-heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.form-kicker {
  color: var(--el-color-primary);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .04em;
}

.form-heading h4 {
  margin: 4px 0 0;
  color: var(--el-text-color-primary);
  font-size: 16px;
}

.field-label {
  display: block;
  margin: 14px 0 6px;
  color: var(--el-text-color-regular);
  font-size: 12px;
  font-weight: 600;
}

.full-control {
  width: 100%;
}

.agent-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.agent-option small {
  color: var(--el-text-color-secondary);
  font-size: 11px;
}

.native-control {
  width: 100%;
  box-sizing: border-box;
  min-height: 32px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  outline: none;
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-regular);
  font: inherit;
  font-size: 13px;
}

.native-control:focus {
  border-color: var(--el-color-primary);
}

.schedule-fields {
  margin-top: 2px;
}

.interval-fields {
  display: grid;
  grid-template-columns: minmax(110px, 1fr) minmax(110px, 1fr);
  gap: 10px;
}

.interval-start-field {
  grid-column: 1 / -1;
}

.calendar-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.timezone-hint {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 12px;
  color: var(--el-text-color-secondary);
  font-size: 11px;
}

.notification-section {
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.notification-section-header,
.notification-target-header,
.notification-target-actions {
  display: flex;
  align-items: center;
}

.notification-section-header {
  justify-content: space-between;
  gap: 12px;
}

.notification-section-header p {
  margin: 4px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 11px;
}

.add-target-btn,
.test-notification-btn,
.remove-target-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  border-radius: 5px;
  color: #fff;
  cursor: pointer;
  font-size: 12px;
  transition: border-color .15s, background .15s, box-shadow .15s, opacity .15s;
}

.add-target-btn {
  min-height: 30px;
  padding: 0 10px;
  border: 1px solid var(--el-color-primary);
  background: var(--el-color-primary);
  box-shadow: 0 2px 5px color-mix(in srgb, var(--el-color-primary) 20%, transparent);
}

.add-target-btn:hover {
  border-color: var(--el-color-primary-dark-2);
  background: var(--el-color-primary-dark-2);
}

.notification-empty {
  margin-top: 10px;
  padding: 10px 11px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.notification-target {
  margin-top: 10px;
  padding: 11px;
  border: 1px solid var(--el-border-color);
  border-radius: 7px;
  background: var(--el-fill-color-extra-light);
}

.notification-target-header {
  justify-content: space-between;
  gap: 10px;
}

.notification-target-header strong {
  color: var(--el-text-color-primary);
  font-size: 12px;
}

.remove-target-btn {
  width: 28px;
  min-width: 28px;
  height: 28px;
  border: 1px solid var(--el-color-danger);
  background: var(--el-color-danger);
  box-shadow: 0 2px 5px color-mix(in srgb, var(--el-color-danger) 20%, transparent);
}

.remove-target-btn:hover {
  border-color: var(--el-color-danger-dark-2);
  background: var(--el-color-danger-dark-2);
}

.notification-target-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 0 10px;
}

.notification-target-grid .field-label {
  margin-top: 11px;
}

.notification-target-wide {
  grid-column: 1 / -1;
}

.notification-target-actions {
  justify-content: flex-end;
  margin-top: 12px;
}

.test-notification-btn {
  min-height: 29px;
  padding: 0 10px;
  border: 1px solid var(--el-color-success);
  background: var(--el-color-success);
  box-shadow: 0 2px 5px color-mix(in srgb, var(--el-color-success) 20%, transparent);
}

.test-notification-btn:hover:not(:disabled) {
  border-color: var(--el-color-success-dark-2);
  background: var(--el-color-success-dark-2);
}

.test-notification-btn:disabled {
  cursor: not-allowed;
  opacity: .55;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.primary-btn,
.secondary-btn {
  min-height: 32px;
  padding: 0 13px;
  font-size: 12px;
}

.primary-btn {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary);
  color: #fff;
  box-shadow: 0 2px 6px color-mix(in srgb, var(--el-color-primary) 20%, transparent);
}

.secondary-btn {
  border-color: var(--automation-cancel-bg);
  background: var(--automation-cancel-bg);
  color: #fff;
  box-shadow: 0 2px 6px color-mix(in srgb, var(--automation-cancel-bg) 26%, transparent);
}

.secondary-btn:hover:not(:disabled) {
  border-color: var(--automation-cancel-bg-hover);
  background: var(--automation-cancel-bg-hover);
}

.secondary-btn:active:not(:disabled) {
  box-shadow: none;
}

.automation-drawer button:focus-visible {
  outline: 2px solid var(--el-color-primary-light-3);
  outline-offset: 2px;
}

.primary-btn:disabled,
.secondary-btn:disabled,
.create-task-btn:disabled,
.task-actions button:disabled,
.run-actions button:disabled {
  cursor: not-allowed;
  opacity: .55;
}

.automation-loading,
.automation-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 9px;
  min-height: 260px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  text-align: center;
}

.automation-empty strong {
  color: var(--el-text-color-primary);
  font-size: 14px;
}

.empty-icon {
  display: grid;
  width: 52px;
  height: 52px;
  place-items: center;
  margin-bottom: 3px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 50%;
  color: var(--el-color-primary);
  background: var(--el-fill-color-extra-light);
}

.empty-create-btn {
  margin-top: 8px;
}

.task-list,
.run-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 16px;
}

.task-item,
.run-item {
  padding: 13px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 7px;
  background: var(--el-fill-color-extra-light);
}

.task-item-top,
.run-item-top,
.run-item-bottom,
.task-meta,
.task-actions {
  display: flex;
  align-items: center;
}

.task-item-top,
.run-item-top {
  justify-content: space-between;
  gap: 10px;
}

.task-title-wrap {
  display: flex;
  align-items: flex-start;
  min-width: 0;
  gap: 8px;
}

.task-status-dot {
  width: 7px;
  height: 7px;
  flex: 0 0 7px;
  margin-top: 5px;
  border-radius: 50%;
  background: var(--el-text-color-placeholder);
}

.task-status-dot.enabled {
  background: var(--el-color-success);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--el-color-success) 14%, transparent);
}

.task-title-wrap h4,
.run-item-top h4 {
  overflow: hidden;
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 13px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-title-wrap p,
.run-item-top p {
  margin: 4px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 11px;
}

.task-prompt {
  display: -webkit-box;
  overflow: hidden;
  margin: 12px 0 9px;
  color: var(--el-text-color-regular);
  font-size: 12px;
  line-height: 1.5;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.task-meta,
.run-item-bottom {
  justify-content: space-between;
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 11px;
}

.run-status {
  color: var(--el-text-color-secondary);
}

.run-status.success { color: var(--el-color-success); }
.run-status.failed { color: var(--el-color-danger); }
.run-status.running { color: var(--el-color-primary); }
.run-status.skipped { color: var(--el-color-warning); }

.task-actions {
  gap: 7px;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.task-actions button,
.run-actions button {
  padding: 3px 7px;
  color: #fff;
  font-size: 11px;
}

.task-actions .run-action,
.run-actions .rerun-action {
  border-color: var(--automation-run-bg);
  background: var(--automation-run-bg);
  box-shadow: 0 2px 6px color-mix(in srgb, var(--automation-run-bg) 30%, transparent);
}

.task-actions .run-action:hover:not(:disabled),
.run-actions .rerun-action:hover:not(:disabled) {
  border-color: var(--automation-run-bg-hover);
  background: var(--automation-run-bg-hover);
}

.task-actions .edit-action {
  border-color: var(--automation-edit-bg);
  background: var(--automation-edit-bg);
  box-shadow: 0 2px 6px color-mix(in srgb, var(--automation-edit-bg) 30%, transparent);
}

.task-actions .edit-action:hover:not(:disabled) {
  border-color: var(--automation-edit-bg-hover);
  background: var(--automation-edit-bg-hover);
}

.run-actions .view-action {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary);
  box-shadow: 0 2px 6px color-mix(in srgb, var(--el-color-primary) 26%, transparent);
}

.run-actions .view-action:hover:not(:disabled) {
  border-color: var(--el-color-primary-dark-2);
  background: var(--el-color-primary-dark-2);
}

.task-actions .danger-action {
  margin-left: auto;
  border-color: var(--automation-danger-bg);
  background: var(--automation-danger-bg);
  box-shadow: 0 2px 6px color-mix(in srgb, var(--el-color-danger) 26%, transparent);
}

.task-actions .danger-action:hover:not(:disabled) {
  border-color: var(--automation-danger-bg-hover);
  background: var(--automation-danger-bg-hover);
}

.task-actions button:active:not(:disabled),
.run-actions button:active:not(:disabled) {
  box-shadow: none;
}

.run-list {
  padding-top: 16px;
}

.run-item-bottom {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.run-actions {
  display: flex;
  gap: 7px;
}

.run-actions button {
  min-height: 26px;
}

.run-error {
  margin: 10px 0 0;
  color: var(--el-color-danger);
  font-size: 11px;
  line-height: 1.5;
}

.notification-result {
  margin: 10px 0 0;
  font-size: 11px;
  line-height: 1.5;
}

.notification-result.sent {
  color: var(--el-color-success);
}

.notification-result.partial_failed {
  color: var(--el-color-warning);
}

.notification-result.failed {
  color: var(--el-color-danger);
}

@media (max-width: 520px) {
  .automation-drawer .el-drawer__body {
    padding-right: 16px;
    padding-left: 16px;
  }

  .interval-fields,
  .calendar-fields,
  .notification-target-grid {
    grid-template-columns: 1fr;
  }

  .interval-start-field,
  .notification-target-wide {
    grid-column: auto;
  }

  .task-actions {
    flex-wrap: wrap;
  }

  .automation-header-actions {
    gap: 6px;
  }

  .drawer-close-btn,
  .create-task-btn {
    padding-right: 9px;
    padding-left: 9px;
  }
}
</style>
