import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '@/api/http'

export type AutomationScheduleType = 'one_time' | 'interval' | 'daily' | 'weekly'
export type AutomationRunStatus = 'pending' | 'running' | 'success' | 'failed' | 'skipped'
export type AutomationNotificationPlatform = 'wecom' | 'feishu' | 'dingtalk'
export type AutomationNotificationStatus = 'not_configured' | 'not_sent' | 'sent' | 'partial_failed' | 'failed'

export interface AutomationNotificationTarget {
  platform: AutomationNotificationPlatform
  name: string
  webhook: string
  dingtalk_secret?: string
}

export interface AutomationTask {
  id: string
  user_id: string
  name: string
  agent_id: string
  agent_name?: string
  prompt: string
  schedule_type: AutomationScheduleType
  schedule_config: Record<string, unknown>
  notification_targets: AutomationNotificationTarget[]
  timezone: string
  enabled: boolean
  next_run_at: string | null
  last_run_at: string | null
  last_status: AutomationRunStatus | null
  created_at: string
  updated_at: string
}

export interface AutomationRun {
  id: string
  task_id: string
  user_id: string
  session_id: string | null
  status: AutomationRunStatus
  scheduled_at: string
  started_at: string | null
  finished_at: string | null
  error: string | null
  notification_status: AutomationNotificationStatus
  notification_error: string | null
  created_at: string
}

export const useAutomationStore = defineStore('automation', () => {
  const tasks = ref<AutomationTask[]>([])
  const runs = ref<AutomationRun[]>([])
  const runTotal = ref(0)
  const loading = ref(false)
  const error = ref('')
  const saving = ref(false)
  const timezone = ref('')
  const taskCount = computed(() => tasks.value.length)

  async function loadTasks() {
    loading.value = true
    error.value = ''
    try {
      tasks.value = await api.getAutomationTasks()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载自动化任务失败'
    } finally {
      loading.value = false
    }
  }

  async function loadRuns() {
    try {
      const response = await api.getAutomationRuns()
      runs.value = response.items
      runTotal.value = response.total
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载执行历史失败'
    }
  }

  async function loadTimezone() {
    try {
      timezone.value = (await api.getAutomationTimezone()).timezone
    } catch {
      timezone.value = ''
    }
  }

  async function createTask(data: object) {
    saving.value = true
    try {
      const created = await api.createAutomationTask(data)
      tasks.value = [created, ...tasks.value]
      return created as AutomationTask
    } finally {
      saving.value = false
    }
  }

  async function updateTask(id: string, data: object) {
    const updated = await api.updateAutomationTask(id, data)
    const index = tasks.value.findIndex(task => task.id === id)
    if (index >= 0) tasks.value[index] = updated
    return updated as AutomationTask
  }

  async function deleteTask(id: string) {
    await api.deleteAutomationTask(id)
    tasks.value = tasks.value.filter(task => task.id !== id)
  }

  async function pauseTask(id: string) {
    const updated = await api.pauseAutomationTask(id)
    replaceTask(updated)
    return updated as AutomationTask
  }

  async function resumeTask(id: string) {
    const updated = await api.resumeAutomationTask(id)
    replaceTask(updated)
    return updated as AutomationTask
  }

  async function runTask(id: string) {
    const run = await api.runAutomationTask(id)
    await loadTasks()
    await loadRuns()
    return run as AutomationRun
  }

  async function rerun(runId: string) {
    const run = await api.rerunAutomation(runId)
    await loadTasks()
    await loadRuns()
    return run as AutomationRun
  }

  async function testNotificationTarget(target: AutomationNotificationTarget) {
    return api.testAutomationNotification(target)
  }

  function replaceTask(updated: AutomationTask) {
    const index = tasks.value.findIndex(task => task.id === updated.id)
    if (index >= 0) tasks.value[index] = updated
  }

  function getTaskName(id: string) {
    return tasks.value.find(task => task.id === id)?.name || id
  }

  return {
    tasks,
    runs,
    runTotal,
    loading,
    error,
    saving,
    timezone,
    taskCount,
    loadTasks,
    loadRuns,
    loadTimezone,
    createTask,
    updateTask,
    deleteTask,
    pauseTask,
    resumeTask,
    runTask,
    rerun,
    testNotificationTarget,
    getTaskName,
  }
})
