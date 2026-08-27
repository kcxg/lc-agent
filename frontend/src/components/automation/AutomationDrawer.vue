<template>
  <el-drawer
    v-model="visible"
    title="自动化任务"
    direction="rtl"
    size="min(560px, 100vw)"
    class="automation-drawer"
    :destroy-on-close="false"
  >
    <template #header>
      <div class="automation-drawer-header">
        <div>
          <h3>自动化任务</h3>
          <p>让 Agent 按计划自动执行任务</p>
        </div>
        <button class="create-task-btn" type="button" @click="startCreate">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M12 5v14M5 12h14" />
          </svg>
          新建
        </button>
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
        <span class="tab-count">{{ automationStore.runs.length }}</span>
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
        <button class="icon-close-btn" type="button" title="关闭表单" aria-label="关闭表单" @click="cancelForm">×</button>
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
        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" />
        </svg>
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
          <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" />
          </svg>
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
            <span v-if="task.next_run_at">下次 {{ formatDate(task.next_run_at) }}</span>
            <span v-else-if="!task.enabled">已暂停</span>
          </div>
          <div class="task-actions">
            <button type="button" title="立即执行" :disabled="actionTaskId === task.id" @click="runTask(task)">
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 3 14 9-14 9V3z" /></svg>
              {{ actionTaskId === task.id && actionType === 'run' ? '执行中...' : '立即执行' }}
            </button>
            <button type="button" title="编辑任务" :disabled="actionTaskId === task.id" @click="startEdit(task)">
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20h9" /><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" /></svg>
              编辑
            </button>
            <button class="danger-action" type="button" title="删除任务" :disabled="actionTaskId === task.id" @click="deleteTask(task)">
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
          <div class="run-item-bottom">
            <span v-if="run.finished_at">完成于 {{ formatDate(run.finished_at) }}</span>
            <span v-else>执行中</span>
            <div class="run-actions">
              <button v-if="run.session_id" type="button" @click="openRunSession(run)">查看会话</button>
              <button v-if="run.status === 'failed'" type="button" :disabled="actionRunId === run.id" @click="rerun(run)">
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
import { useRouter } from 'vue-router'
import { useAgentsStore } from '@/stores/agents'
import { useAutomationStore, type AutomationRun, type AutomationScheduleType, type AutomationTask } from '@/stores/automation'
import { useSessionsStore } from '@/stores/sessions'

const visible = ref(false)
const activeTab = ref<'tasks' | 'runs'>('tasks')
const formVisible = ref(false)
const editingTaskId = ref<string | null>(null)
const actionTaskId = ref<string | null>(null)
const actionType = ref<'run' | 'toggle' | null>(null)
const actionRunId = ref<string | null>(null)

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
})

const availableAgents = computed(() => agentsStore.agents)
const showForm = computed(() => formVisible.value)
const canSave = computed(() => {
  if (!form.name.trim() || !form.agent_id || !form.prompt.trim()) return false
  if (form.schedule_type === 'one_time') return Boolean(form.run_at)
  if (form.schedule_type === 'interval') return form.interval_value > 0
  return Boolean(form.time)
})

function open() {
  visible.value = true
  activeTab.value = 'tasks'
  automationStore.error = ''
  void automationStore.loadTasks()
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
}

function cancelForm() {
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

defineExpose({ open })
</script>

<style>
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
  border: 1px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: border-color .15s, background .15s, color .15s, opacity .15s;
}

.create-task-btn {
  min-height: 30px;
  padding: 0 11px;
  background: var(--el-color-primary);
  color: #fff;
  font-size: 12px;
}

.create-task-btn:hover,
.primary-btn:hover:not(:disabled) {
  background: var(--el-color-primary-dark-2);
}

.automation-tabs {
  display: flex;
  gap: 20px;
  height: 48px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.automation-tabs button {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 2px;
  border: 0;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  cursor: pointer;
}

.automation-tabs button.active {
  color: var(--el-color-primary);
  font-weight: 600;
}

.automation-tabs button.active::after {
  content: '';
  position: absolute;
  right: 0;
  bottom: -1px;
  left: 0;
  height: 2px;
  background: var(--el-color-primary);
}

.tab-count {
  min-width: 17px;
  padding: 1px 5px;
  border-radius: 10px;
  background: var(--el-fill-color);
  font-size: 11px;
  text-align: center;
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

.icon-close-btn {
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: 5px;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 21px;
  line-height: 1;
  cursor: pointer;
}

.icon-close-btn:hover {
  background: var(--el-fill-color);
  color: var(--el-text-color-primary);
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
  background: var(--el-color-primary);
  color: #fff;
}

.secondary-btn {
  border-color: var(--el-border-color);
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-regular);
}

.secondary-btn:hover:not(:disabled) {
  border-color: var(--el-color-primary-light-3);
  color: var(--el-color-primary);
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
  border-color: var(--el-border-color);
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-regular);
  font-size: 11px;
}

.task-actions button:hover:not(:disabled),
.run-actions button:hover:not(:disabled) {
  border-color: var(--el-color-primary-light-3);
  color: var(--el-color-primary);
}

.task-actions .danger-action {
  margin-left: auto;
  border-color: transparent;
  background: transparent;
  color: var(--el-color-danger);
}

.task-actions .danger-action:hover:not(:disabled) {
  background: var(--el-color-danger-light-9);
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

.run-error {
  margin: 10px 0 0;
  color: var(--el-color-danger);
  font-size: 11px;
  line-height: 1.5;
}

@media (max-width: 520px) {
  .automation-drawer .el-drawer__body {
    padding-right: 16px;
    padding-left: 16px;
  }

  .interval-fields,
  .calendar-fields {
    grid-template-columns: 1fr;
  }

  .interval-start-field {
    grid-column: auto;
  }

  .task-actions {
    flex-wrap: wrap;
  }
}
</style>
