<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="520px"
    class="interrupt-dialog"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
  >
    <!-- ask_user 多问题模式 -->
    <template v-if="isAskUser && askPayload">
      <div class="questions-list">
        <div
          v-for="(q, idx) in askPayload.questions"
          :key="idx"
          class="question-block"
          :class="{ 'question-done': isAnswered(idx) }"
        >
          <div class="question-header">
            <span class="question-num">{{ idx + 1 }}</span>
            <span class="question-text">{{ q.question }}</span>
            <span v-if="q.required === false" class="optional-badge">可选</span>
          </div>

          <!-- multiple_choice -->
          <template v-if="q.type === 'multiple_choice'">
            <div class="choices-list">
              <button
                v-for="(choice, ci) in q.choices"
                :key="ci"
                class="choice-btn"
                :class="{ selected: isChoiceSelected(idx, choice) }"
                @click="toggleChoice(idx, choice, q.allow_multiple, false)"
              >
                <span class="choice-id">{{ String.fromCharCode(65 + ci) }}</span>
                {{ choice }}
              </button>
              <!-- Other option -->
              <button
                class="choice-btn choice-other"
                :class="{ selected: otherSelected[idx] }"
                @click="toggleOther(idx, q.allow_multiple)"
              >
                <span class="choice-id">…</span>自定义
              </button>
            </div>
            <el-input
              v-if="otherSelected[idx]"
              v-model="otherTexts[idx]"
              :placeholder="q.allow_multiple ? '追加自定义内容...' : '输入自定义回答...'"
              class="other-input"
              size="small"
              @keyup.enter.prevent
            />
          </template>

          <!-- text -->
          <template v-else>
            <el-input
              v-model="textAnswers[idx]"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 6 }"
              placeholder="请输入回答..."
              class="text-input"
            />
          </template>
        </div>
      </div>
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
        <el-button link @click="cancelAskUser">跳过</el-button>
        <el-button type="primary" :disabled="!canSubmit" @click="submitAskUser">
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

interface Question {
  question: string
  type: 'text' | 'multiple_choice'
  choices?: string[]
  required?: boolean
  allow_multiple?: boolean
}

interface AskUserPayload {
  type: 'ask_user'
  questions: Question[]
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

// Per-question answer state
const textAnswers = ref<string[]>([])       // for type='text'
const selectedChoices = ref<string[][]>([]) // for type='multiple_choice', selected options
const otherSelected = ref<boolean[]>([])    // whether "Other" is active per question
const otherTexts = ref<string[]>([])        // custom text for "Other"

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

// Reset state when interrupt changes
watch(() => props.interrupt, () => {
  const qs = askPayload.value?.questions ?? []
  textAnswers.value = qs.map(() => '')
  selectedChoices.value = qs.map(() => [])
  otherSelected.value = qs.map(() => false)
  otherTexts.value = qs.map(() => '')
  showDetails.value = false
})

function isChoiceSelected(qIdx: number, choice: string): boolean {
  return (selectedChoices.value[qIdx] ?? []).includes(choice)
}

function toggleChoice(qIdx: number, choice: string, allowMultiple: boolean | undefined, _isOther: boolean) {
  const current = selectedChoices.value[qIdx] ?? []
  const pos = current.indexOf(choice)
  if (allowMultiple) {
    if (pos >= 0) {
      selectedChoices.value[qIdx] = current.filter(c => c !== choice)
    } else {
      selectedChoices.value[qIdx] = [...current, choice]
    }
  } else {
    // Single select: clear Other when a regular choice is selected
    otherSelected.value[qIdx] = false
    otherTexts.value[qIdx] = ''
    selectedChoices.value[qIdx] = pos >= 0 ? [] : [choice]
  }
}

function toggleOther(qIdx: number, allowMultiple: boolean | undefined) {
  const next = !otherSelected.value[qIdx]
  otherSelected.value[qIdx] = next
  if (!next) {
    otherTexts.value[qIdx] = ''
  } else if (!allowMultiple) {
    // Single select: deselect all regular choices when Other is selected
    selectedChoices.value[qIdx] = []
  }
}

function isAnswered(qIdx: number): boolean {
  const q = askPayload.value?.questions[qIdx]
  if (!q) return false
  if (q.required === false) return true
  if (q.type === 'text') return (textAnswers.value[qIdx] ?? '').trim().length > 0
  const choices = selectedChoices.value[qIdx] ?? []
  const other = otherSelected.value[qIdx] && (otherTexts.value[qIdx] ?? '').trim().length > 0
  return choices.length > 0 || other
}

const canSubmit = computed(() => {
  const qs = askPayload.value?.questions ?? []
  return qs.every((q, i) => q.required === false || isAnswered(i))
})

function buildAnswer(qIdx: number, q: Question): string {
  if (q.type === 'text') {
    return (textAnswers.value[qIdx] ?? '').trim()
  }
  const parts: string[] = [...(selectedChoices.value[qIdx] ?? [])]
  if (otherSelected.value[qIdx] && (otherTexts.value[qIdx] ?? '').trim()) {
    parts.push((otherTexts.value[qIdx] ?? '').trim())
  }
  return parts.join(', ')
}

function submitAskUser() {
  if (!canSubmit.value) return
  const qs = askPayload.value?.questions ?? []
  const answers = qs.map((q, i) => buildAnswer(i, q))
  const interruptId = askUserInterrupt.value?.id
  if (!interruptId) {
    console.error('[InterruptDialog] Missing LangGraph interrupt id — cannot resume')
    return
  }
  emit('resume', { [interruptId]: { status: 'answered', answers } })
}

function cancelAskUser() {
  const interruptId = askUserInterrupt.value?.id
  if (!interruptId) return
  emit('resume', { [interruptId]: { status: 'cancelled' } })
}

function allowPermanently() {
  const toolName = firstToolName.value
  if (toolName) emit('allow-permanently', toolName)
}

function approve() {
  emit('decide', { type: 'approve' })
}

function reject() {
  emit('decide', { type: 'reject', message: '用户拒绝了此操作' })
}
</script>

<style scoped>
.questions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-block {
  border: 1px solid var(--el-border-color);
  border-radius: 10px;
  padding: 14px 16px;
  background: var(--el-fill-color-lighter);
  transition: border-color 0.2s, background 0.2s;
}

.question-block.question-done {
  border-color: var(--el-color-success-light-5);
  background: color-mix(in srgb, var(--el-color-success) 6%, transparent);
}

.question-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
}

.question-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--el-color-primary-light-8);
  color: var(--el-color-primary);
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 1px;
}

.question-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--el-text-color-primary);
  flex: 1;
}

.optional-badge {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 1px 6px;
  flex-shrink: 0;
}

.choices-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.choice-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
  padding: 9px 14px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color);
  cursor: pointer;
  font-size: 13px;
  color: var(--el-text-color-primary);
  transition: all 0.15s;
  width: 100%;
}

.choice-btn:hover {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-color-primary-light-9);
}

.choice-btn.selected {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 500;
}

.choice-btn.choice-other {
  color: var(--el-text-color-secondary);
  border-style: dashed;
}

.choice-id {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  background: var(--el-fill-color);
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
  transition: background 0.15s, color 0.15s;
}

.choice-btn.selected .choice-id {
  background: var(--el-color-primary);
  color: #fff;
}

.other-input {
  margin-top: 8px;
}

.text-input {
  width: 100%;
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

:deep(.interrupt-dialog) {
  max-width: min(520px, calc(100vw - 24px));
}

@media (max-width: 768px) {
  .question-text {
    font-size: 13px;
  }

  .choice-btn {
    padding: 8px 12px;
    font-size: 12px;
  }

  .action-item {
    padding: 10px;
  }

  .action-args {
    font-size: 11px;
    max-height: 40vh;
  }
}
</style>
