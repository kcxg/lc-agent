<template>
  <el-dialog
    v-model="visible"
    title="数据清理 / 瘦身"
    width="520px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-alert
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
    >
      <template #title>不可逆操作</template>
      删除后无法恢复，将清理 data 与 checkpoints 两个数据库中超过保留天数的会话（含子会话、消息、checkpoint）。请先预览影响范围。
    </el-alert>

    <el-form label-width="120px" label-position="right">
      <el-form-item label="保留最近">
        <el-input-number v-model="form.keep_days" :min="1" :max="3650" controls-position="right" style="width: 140px" />
        <span style="margin-left: 8px; color: var(--el-text-color-secondary)">天</span>
      </el-form-item>
      <el-form-item label="跳过置顶会话">
        <el-checkbox v-model="form.skip_pinned">置顶会话保留不删</el-checkbox>
      </el-form-item>
      <el-form-item label="跳过活跃会话">
        <el-checkbox v-model="form.skip_active">当前打开的会话保留不删</el-checkbox>
      </el-form-item>
    </el-form>

    <!-- 预览结果 -->
    <div v-if="preview" class="preview-box">
      <div class="preview-title">预览影响范围：</div>
      <div class="preview-row">
        <span>将删除会话数</span>
        <strong>{{ preview.would_delete_sessions }}</strong>
      </div>
      <div class="preview-row">
        <span>将删除消息数</span>
        <strong>{{ preview.would_delete_messages }}</strong>
      </div>
      <div class="preview-row">
        <span>将删除 checkpoint</span>
        <strong>{{ preview.would_delete_threads }}</strong>
      </div>
      <div v-if="preview.would_delete_sessions === 0" class="preview-empty">
        没有符合条件的会话需要清理
      </div>
    </div>

    <!-- 执行结果 -->
    <div v-if="result" class="result-box" :class="{ 'has-errors': result.errors.length > 0 }">
      <div class="result-title">清理完成：</div>
      <div class="result-row">已删除会话 <strong>{{ result.deleted_sessions }}</strong></div>
      <div class="result-row">已删除消息 <strong>{{ result.deleted_messages }}</strong></div>
      <div class="result-row">已删除 checkpoint <strong>{{ result.deleted_threads }}</strong></div>
      <div class="result-row">剩余会话 <strong>{{ result.kept_sessions }}</strong></div>
      <div v-if="result.errors.length > 0" class="result-errors">
        <div>部分错误（{{ result.errors.length }}）：</div>
        <ul>
          <li v-for="(err, idx) in result.errors.slice(0, 5)" :key="idx">
            <span v-if="err.session_id">[{{ err.session_id.slice(0, 8) }}]</span>
            {{ err.phase }}: {{ err.error }}
          </li>
        </ul>
      </div>
    </div>

    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" style="margin-top: 12px" />

    <!-- 数据库压缩结果 -->
    <div v-if="vacuumResult" class="vacuum-box">
      <div class="vacuum-title">数据库压缩结果：</div>
      <div class="vacuum-row">
        <span>data 数据库</span>
        <span :class="vacuumResult.data.success ? 'vacuum-ok' : 'vacuum-fail'">
          {{ vacuumResult.data.success ? '成功' : vacuumResult.data.error || '失败' }}
        </span>
      </div>
      <div class="vacuum-row">
        <span>checkpoints 数据库</span>
        <span :class="vacuumResult.checkpoints.success ? 'vacuum-ok' : 'vacuum-fail'">
          {{ vacuumResult.checkpoints.success ? '成功' : vacuumResult.checkpoints.error || '失败' }}
        </span>
      </div>
    </div>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
      <el-button :loading="previewing" @click="handlePreview">预览影响范围</el-button>
      <el-button
        type="danger"
        :loading="cleaning"
        :disabled="!canExecute"
        @click="handleExecute"
      >
        执行清理
      </el-button>
      <el-button
        type="warning"
        plain
        :loading="vacuuming"
        @click="handleVacuum"
      >
        压缩数据库
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api/http'
import { useSessionsStore } from '@/stores/sessions'

const visible = ref(false)
const previewing = ref(false)
const cleaning = ref(false)
const error = ref('')
const preview = ref<{
  would_delete_sessions: number
  would_delete_messages: number
  would_delete_threads: number
  affected_session_ids: string[]
} | null>(null)
const result = ref<{
  deleted_sessions: number
  deleted_messages: number
  deleted_threads: number
  kept_sessions: number
  errors: Array<{ session_id?: string; phase: string; error: string }>
} | null>(null)
const vacuumResult = ref<{
  data: { success: boolean; path: string; error: string | null }
  checkpoints: { success: boolean; path: string; error: string | null }
} | null>(null)
const vacuuming = ref(false)

const sessionsStore = useSessionsStore()
const emit = defineEmits<{ cleaned: [] }>()

const form = reactive({
  keep_days: 30,
  skip_pinned: true,
  skip_active: true,
})

// 必须先预览、且预览有删除项，才允许执行
const canExecute = computed(() => preview.value !== null && preview.value.would_delete_sessions > 0)

function buildPayload() {
  return {
    keep_days: form.keep_days,
    skip_pinned: form.skip_pinned,
    skip_active: form.skip_active,
    active_session_ids: form.skip_active && sessionsStore.currentSessionId
      ? [sessionsStore.currentSessionId]
      : [],
  }
}

function resetForm() {
  preview.value = null
  result.value = null
  vacuumResult.value = null
  error.value = ''
  form.keep_days = 30
  form.skip_pinned = true
  form.skip_active = true
}

async function handlePreview() {
  previewing.value = true
  error.value = ''
  preview.value = null
  result.value = null
  try {
    preview.value = await api.previewCleanup(buildPayload())
  } catch (e: any) {
    error.value = e.message || '预览失败'
  } finally {
    previewing.value = false
  }
}

async function handleExecute() {
  if (!preview.value || preview.value.would_delete_sessions === 0) return

  try {
    await ElMessageBox.confirm(
      `确认删除 ${preview.value.would_delete_sessions} 个会话（${preview.value.would_delete_messages} 条消息）？\n此操作不可恢复！`,
      '危险操作确认',
      {
        type: 'error',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger',
      },
    )
  } catch {
    return
  }

  cleaning.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await api.cleanupData(buildPayload())
    ElMessage.success(`已清理 ${result.value.deleted_sessions} 个会话`)
    // 清理后刷新会话列表，移除已删除的会话
    await sessionsStore.init()
    // 通知父组件：清理完成，可能需要处理当前会话被删的善后
    emit('cleaned')
    preview.value = null
  } catch (e: any) {
    error.value = e.message || '清理失败'
  } finally {
    cleaning.value = false
  }
}

async function handleVacuum() {
  try {
    await ElMessageBox.confirm(
      '压缩数据库会重建 SQLite 文件以回收删除后的磁盘空间。\n大文件可能耗时数秒到数分钟，期间数据库会被锁定，确认继续？',
      '压缩数据库确认',
      {
        type: 'warning',
        confirmButtonText: '确认压缩',
        cancelButtonText: '取消',
      },
    )
  } catch {
    return
  }

  vacuuming.value = true
  error.value = ''
  vacuumResult.value = null
  try {
    vacuumResult.value = await api.vacuumDatabases()
    const ok = vacuumResult.value.data.success && vacuumResult.value.checkpoints.success
    ElMessage[ok ? 'success' : 'error'](ok ? '数据库压缩完成' : '数据库压缩部分失败')
  } catch (e: any) {
    error.value = e.message || '压缩失败'
  } finally {
    vacuuming.value = false
  }
}

function open() {
  resetForm()
  visible.value = true
}

defineExpose({ open })
</script>

<style scoped>
.preview-box,
.result-box {
  margin-top: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  background: var(--el-fill-color-light);
  font-size: 13px;
}

.preview-box {
  border-color: color-mix(in srgb, var(--el-color-warning) 50%, var(--el-border-color));
  background: color-mix(in srgb, var(--el-color-warning-light-9) 40%, var(--el-fill-color-light));
}

.result-box {
  border-color: color-mix(in srgb, var(--el-color-success) 50%, var(--el-border-color));
  background: color-mix(in srgb, var(--el-color-success-light-9) 40%, var(--el-fill-color-light));
}

.result-box.has-errors {
  border-color: color-mix(in srgb, var(--el-color-danger) 50%, var(--el-border-color));
  background: color-mix(in srgb, var(--el-color-danger-light-9) 40%, var(--el-fill-color-light));
}

.preview-title,
.result-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
}

.preview-row,
.result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 3px 0;
  color: var(--el-text-color-regular);
}

.preview-row strong,
.result-row strong {
  color: var(--el-text-color-primary);
  font-variant-numeric: tabular-nums;
}

.preview-empty {
  margin-top: 6px;
  color: var(--el-text-color-secondary);
  font-style: italic;
}

.result-errors {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--el-border-color);
  color: var(--el-color-danger);
  font-size: 12px;
}

.result-errors ul {
  margin: 4px 0 0;
  padding-left: 18px;
}

.result-errors li {
  margin: 2px 0;
  word-break: break-all;
}

.vacuum-box {
  margin-top: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid color-mix(in srgb, var(--el-color-warning) 50%, var(--el-border-color));
  background: color-mix(in srgb, var(--el-color-warning-light-9) 40%, var(--el-fill-color-light));
  font-size: 13px;
}

.vacuum-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
}

.vacuum-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 3px 0;
  color: var(--el-text-color-regular);
}

.vacuum-ok {
  color: var(--el-color-success);
  font-weight: 600;
}

.vacuum-fail {
  color: var(--el-color-danger);
  font-weight: 600;
}
</style>
