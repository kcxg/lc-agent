<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="500px"
    class="interrupt-dialog"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
  >
    <!-- ask_user 模式 -->
    <template v-if="isAskUser">
      <p class="ask-question">{{ askPayload?.question }}</p>
      <p v-if="askPayload?.allow_multiple && askPayload?.options?.length" class="multi-hint">（可多选）</p>

      <div v-if="askPayload?.options?.length" class="options-list">
        <el-button
          v-for="opt in askPayload.options"
          :key="opt.id"
          :type="isOptionSelected(opt.label) ? 'primary' : 'default'"
          class="option-btn"
          @click="selectOption(opt.label)"
        >
          <span class="option-id">{{ opt.id }}</span>
          {{ opt.label }}
        </el-button>
      </div>

      <el-input
        v-if="askPayload?.allow_free_input"
        v-model="freeInput"
        :placeholder="askPayload?.options?.length ? '或输入自定义回答...' : '请输入回答...'"
        class="free-input"
        @keyup.enter="canSubmitAskUser && submitAskUser()"
      />
    </template>

    <!-- 标准工具审批模式 -->
    <template v-else>
      <div v-for="(action, idx) in allActions" :key="idx" class="action-item" :class="{ compact: !showDetails }">
        <p>
          <strong>工具:</strong>
          <span class="tool-display-name">{{ action.display_name || action.name }}</span>
          <span v-if="action.display_name" class="tool-internal-name">({{ action.name }})</span>
        </p>
        <pre v-if="showDetails" class="action-args">{{ JSON.stringify(action.args ?? action.arguments, null, 2) }}</pre>
      </div>
      <el-button
        link
        :type="showDetails ? 'info' : 'primary'"
        class="expand-btn"
        @click="showDetails = !showDetails"
      >
        {{ showDetails ? '收起详情' : `展开详情（${allActions.length} 个工具调用）` }}
      </el-button>
    </template>

    <template #footer>
      <template v-if="isAskUser">
        <el-button type="primary" :disabled="!canSubmitAskUser" @click="submitAskUser">
          提交
        </el-button>
      </template>
      <template v-else>
        <el-button @click="reject">拒绝</el-button>
        <el-button type="success" @click="allowPermanently" :disabled="!firstToolName">永久允许此工具</el-button>
        <el-button type="primary" @click="approve">批准执行</el-button>
      </template>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { InterruptInfo } from '@/stores/chat'

interface AskUserPayload {
  type: 'ask_user'
  question: string
  options?: { id: string; label: string }[]
  allow_multiple?: boolean
  allow_free_input?: boolean
}

interface AskUserInterrupt {
  id?: string
  value: AskUserPayload
}

const props = defineProps<{ interrupt: InterruptInfo | null }>()
const emit = defineEmits<{
  decide: [decision: { type: string; message?: string }]
  resume: [value: any]
  'allow-permanently': [toolName: string]
}>()

const visible = computed({
  get: () => props.interrupt !== null,
  set: () => {},
})

const freeInput = ref('')
const selectedOption = ref<string | null>(null)
const selectedOptions = ref<string[]>([])
const showDetails = ref(false)

const allActions = computed(() => props.interrupt?.actionRequests ?? [])
const askUserInterrupt = computed<AskUserInterrupt | null>(() => {
  const item = props.interrupt?.data?.[0]
  if (item?.value && typeof item.value === 'object' && item.value.type === 'ask_user') {
    return item as AskUserInterrupt
  }
  return null
})

const askPayload = computed<AskUserPayload | null>(() => askUserInterrupt.value?.value ?? null)

const isAskUser = computed(() => askPayload.value !== null)

const dialogTitle = computed(() => isAskUser.value ? '💬 请回答' : '⚠️ 工具需要审批')

const firstToolName = computed<string | null>(() => {
  if (!props.interrupt) return null
  const reqs = props.interrupt.actionRequests
  if (reqs && reqs.length > 0) return reqs[0].name
  const data = props.interrupt.data
  if (data && data.length > 0) {
    const value = data[0]?.value
    if (typeof value === 'object' && value?.action_requests?.length > 0) {
      return value.action_requests[0].name
    }
  }
  return null
})

const canSubmitAskUser = computed(() => {
  return selectedOption.value !== null || selectedOptions.value.length > 0 || freeInput.value.trim() !== ''
})

watch(() => props.interrupt, () => {
  freeInput.value = ''
  selectedOption.value = null
  selectedOptions.value = []
  showDetails.value = false
})

function isOptionSelected(label: string): boolean {
  const payload = askPayload.value
  if (payload?.allow_multiple) {
    return selectedOptions.value.includes(label)
  }
  return selectedOption.value === label
}

function selectOption(label: string) {
  const payload = askPayload.value
  if (payload?.allow_multiple) {
    const idx = selectedOptions.value.indexOf(label)
    if (idx >= 0) {
      selectedOptions.value.splice(idx, 1)
    } else {
      selectedOptions.value.push(label)
    }
    selectedOption.value = selectedOptions.value.length > 0 ? selectedOptions.value.join(', ') : null
  } else {
    selectedOption.value = label
    if (!payload?.allow_free_input) {
      submitAskUser()
    }
  }
}

function submitAskUser() {
  const parts: string[] = []
  if (askPayload.value?.allow_multiple && selectedOptions.value.length > 0) {
    parts.push(selectedOptions.value.join(', '))
  } else if (selectedOption.value) {
    parts.push(selectedOption.value)
  }
  if (freeInput.value.trim()) {
    parts.push(freeInput.value.trim())
  }
  const answer = parts.join('; ')
  if (!answer) return
  const interruptId = askUserInterrupt.value?.id
  if (!interruptId) {
    console.warn('[InterruptDialog] Missing LangGraph interrupt id')
    return
  }
  emit('resume', { [interruptId]: answer })
}

function allowPermanently() {
  const toolName = firstToolName.value
  if (toolName) {
    emit('allow-permanently', toolName)
  }
}

function approve() {
  emit('decide', { type: 'approve' })
}

function reject() {
  emit('decide', { type: 'reject', message: '用户拒绝了此操作' })
}
</script>

<style scoped>
.ask-question {
  font-size: 15px;
  margin-bottom: 16px;
  line-height: 1.6;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.option-btn {
  justify-content: flex-start;
  text-align: left;
  height: auto;
  padding: 10px 16px;
  white-space: normal;
}

.option-id {
  display: inline-block;
  width: 22px;
  height: 22px;
  line-height: 22px;
  text-align: center;
  border-radius: 4px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 600;
  font-size: 12px;
  margin-right: 10px;
  flex-shrink: 0;
}

.multi-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin: -8px 0 12px;
}

.free-input {
  margin-top: 8px;
  width: 100%;
}

.free-input :deep(.el-input__wrapper),
.free-input :deep(.el-textarea__inner) {
  box-sizing: border-box;
}

.tool-display-name {
  margin-left: 4px;
  font-weight: 500;
}
.tool-internal-name {
  margin-left: 6px;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}
.action-item {
  margin-bottom: 14px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
}

.action-item.compact {
  margin-bottom: 6px;
  padding: 8px 12px;
}

.action-args {
  background: var(--el-fill-color);
  padding: 10px;
  border-radius: 6px;
  font-size: 12px;
  overflow-x: auto;
  margin-top: 8px;
  border: 1px solid var(--el-border-color);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.expand-btn {
  margin-top: 4px;
}

.dialog-footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
  width: 100%;
}

:deep(.interrupt-dialog) {
  max-width: min(500px, calc(100vw - 24px));
}

@media (max-width: 768px) {
  .ask-question {
    font-size: 14px;
  }

  .action-item {
    padding: 10px;
  }

  .action-args {
    font-size: 11px;
    max-height: 40vh;
  }

  .dialog-footer-actions {
    flex-direction: column-reverse;
    align-items: stretch;
  }

  .dialog-footer-actions .el-button {
    width: 100%;
    margin-left: 0;
  }

  .option-btn {
    width: 100%;
    margin-left: 0;
  }
}
</style>
