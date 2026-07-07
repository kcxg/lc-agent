import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ChatSseClient, type SseMessage } from '@/api/sse-client'
import { useSessionsStore } from '@/stores/sessions'
import { api } from '@/api/http'
import { createClientId } from '@/utils/client-id'

const INITIAL_MESSAGE_LIMIT = 6

export interface LlmRoundUsage {
  inputTokens: number
  outputTokens: number
  totalTokens: number
  cacheReadTokens: number
  reasoningTokens: number
  duration?: number
}

export interface MessageUsage {
  rounds: LlmRoundUsage[]
  toolCallCount: number
  totalDuration?: number
}

export interface HttpTraceMessagePart {
  method?: string
  url?: string
  headers: Record<string, string>
  body: string
  bodyFormat?: 'json' | 'text' | 'empty' | 'unknown'
}

export interface HttpTraceResponsePart {
  status?: number
  headers: Record<string, string>
  body: string
  bodyFormat?: 'json' | 'text' | 'empty' | 'unknown'
  ok?: boolean
}

export interface HttpTrace {
  id: string
  sequence: number
  kind: 'llm_http'
  provider?: string
  model?: string
  startedAt: number
  durationMs?: number
  request: HttpTraceMessagePart
  response: HttpTraceResponsePart
  error?: string | null
}

export interface ErrorInfo {
  title: string
  detail: string
  suggestions?: string[]
  techDetail?: string
  errorCode?: string
}

export interface ContentSegment {
  type: 'text' | 'tool'
  text?: string
  toolCall?: ToolCall
}

export interface SubAgentEntry {
  tool_call_id: string
  name: string
  sub_session_id: string
  query: string
  status: 'running' | 'done' | 'error'
  tokenPreview: string
  toolCallCount: number
  tokenCount: number
  tokens: string
  innerToolCalls: Array<{ name: string; status: string; args?: unknown; result?: string }>
  duration?: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content: string
  timestamp: number
  toolCalls?: ToolCall[]
  segments?: ContentSegment[]
  subAgents?: Record<string, SubAgentEntry>
  isStreaming?: boolean
  isSystem?: boolean
  usage?: MessageUsage
  httpTraces?: HttpTrace[]
  httpTracesCount?: number
}

export interface ToolCall {
  name: string
  runId?: string
  args?: Record<string, any>
  result?: string
  status: 'pending' | 'running' | 'done' | 'error'
  startTime?: number
  duration?: number
  resultLength?: number
  is_subagent?: boolean
  sub_session_id?: string
}

export interface InterruptInfo {
  actionRequests: any[]
  reviewConfigs: any[]
  data: any[]
}

export interface ReplayMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface SendMessageOptions {
  replaceFromMessageId?: string
  history?: ReplayMessage[]
  llmParams?: Record<string, any> | null
}

function normalizeToolStatus(status: any): ToolCall['status'] {
  if (status === 'pending' || status === 'running' || status === 'done' || status === 'error') {
    return status
  }
  if (status === 'success') return 'done'
  return 'done'
}

function ensureToolMarkers(content: string, toolCalls?: ToolCall[]): string {
  if (!toolCalls?.length) return content
  const missingIndexes = toolCalls
    .map((_, idx) => idx)
    .filter(idx => !content.includes(`<!--TOOL:${idx}-->`))
  if (missingIndexes.length === 0) return content
  return `${content}\n${missingIndexes.map(idx => `<!--TOOL:${idx}-->`).join('\n')}\n`
}

function ensureHttpMarkers(content: string, traceCount: number): string {
  if (traceCount <= 0) return content
  const missing = Array.from({ length: traceCount }, (_, i) => i)
    .filter(i => !content.includes(`<!--HTTP:${i}-->`))
  if (missing.length === 0) return content
  return `${content}\n${missing.map(i => `<!--HTTP:${i}-->`).join('\n')}\n`
}

function normalizeHistoryUsage(rawUsage: any): MessageUsage | undefined {
  if (!rawUsage) return undefined
  const rounds = (rawUsage.rounds || []).map((round: any) => ({
    inputTokens: round.inputTokens ?? round.input_tokens ?? 0,
    outputTokens: round.outputTokens ?? round.output_tokens ?? 0,
    totalTokens: round.totalTokens ?? round.total_tokens ?? 0,
    cacheReadTokens: round.cacheReadTokens ?? round.cache_read_tokens ?? 0,
    reasoningTokens: round.reasoningTokens ?? round.reasoning_tokens ?? 0,
    duration: round.duration ?? round.duration_ms,
  }))
  return {
    rounds,
    toolCallCount: rawUsage.toolCallCount ?? rawUsage.tool_call_count ?? 0,
    totalDuration: rawUsage.totalDuration ?? rawUsage.total_duration_ms,
  }
}

function normalizeHttpTrace(raw: any): HttpTrace {
  return {
    id: raw.id || createClientId(),
    sequence: raw.sequence ?? 0,
    kind: 'llm_http',
    provider: raw.provider || undefined,
    model: raw.model || undefined,
    startedAt: raw.startedAt ?? raw.started_at ?? Date.now(),
    durationMs: raw.durationMs ?? raw.duration_ms,
    request: {
      method: raw.request?.method || undefined,
      url: raw.request?.url || undefined,
      headers: raw.request?.headers || {},
      body: raw.request?.body || '空',
      bodyFormat: raw.request?.bodyFormat ?? raw.request?.body_format ?? 'unknown',
    },
    response: {
      status: raw.response?.status,
      headers: raw.response?.headers || {},
      body: raw.response?.body || '未返回',
      bodyFormat: raw.response?.bodyFormat ?? raw.response?.body_format ?? 'unknown',
      ok: raw.response?.ok,
    },
    error: raw.error ?? null,
  }
}

function normalizeHttpTraces(raw: any): HttpTrace[] | undefined {
  if (!Array.isArray(raw) || raw.length === 0) return undefined
  return raw.map(normalizeHttpTrace)
}

function normalizeHistoryMessage(msg: any): ChatMessage | null {
  if (msg.role === 'system') {
    const content = msg.content || ''
    return {
      id: msg.id || createClientId(),
      role: 'user',
      content,
      timestamp: msg.created_at ? new Date(msg.created_at).getTime() : Date.now(),
      isSystem: true,
    }
  }

  const role = msg.role === 'human' ? 'user' : msg.role === 'ai' ? 'assistant' : msg.role
  if (!['user', 'assistant', 'tool'].includes(role)) return null

  const toolCalls = (msg.tool_calls || msg.toolCalls || []).map((tc: any) => ({
    name: tc.name || '',
    runId: tc.runId || tc.run_id || tc.id,
    args: tc.args || {},
    result: tc.result,
    status: normalizeToolStatus(tc.status),
    startTime: tc.startTime ?? tc.start_time,
    duration: tc.duration,
    resultLength: tc.resultLength ?? tc.result_length ?? tc.result?.length,
    is_subagent: tc.is_subagent || false,
    sub_session_id: tc.sub_session_id || '',
  }))
  const usage = normalizeHistoryUsage(msg.usage)
  if (usage && toolCalls.length > usage.toolCallCount) {
    usage.toolCallCount = toolCalls.length
  }

  const subAgents: Record<string, SubAgentEntry> = {}
  for (const tc of toolCalls) {
    if (tc.is_subagent && tc.runId) {
      subAgents[tc.runId] = {
        tool_call_id: tc.runId,
        name: tc.name,
        sub_session_id: tc.sub_session_id || '',
        query: typeof tc.args === 'object' ? (tc.args?.query || '') : '',
        status: tc.status === 'running' ? 'running' : (tc.status === 'error' ? 'error' : 'done'),
        tokenPreview: tc.result ? tc.result.slice(0, 150) : '',
        toolCallCount: 0,
        tokenCount: 0,
        tokens: '',
        innerToolCalls: [],
        duration: tc.duration,
      }
    }
  }

  const httpTraces = normalizeHttpTraces(msg.http_traces || msg.httpTraces)
  const httpTracesCount = msg.http_traces_count ?? msg.httpTracesCount ?? httpTraces?.length ?? 0
  let content = role === 'assistant' ? ensureToolMarkers(msg.content || '', toolCalls) : msg.content || ''
  if (role === 'assistant' && httpTracesCount > 0) {
    content = ensureHttpMarkers(content, httpTracesCount)
  }

  return {
    id: msg.id || createClientId(),
    role,
    content,
    timestamp: msg.created_at ? new Date(msg.created_at).getTime() : Date.now(),
    toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
    subAgents: Object.keys(subAgents).length > 0 ? subAgents : undefined,
    usage,
    httpTraces,
    httpTracesCount,
  }
}

function normalizeHistoryMessages(rawMessages: any[]): ChatMessage[] {
  const loaded: ChatMessage[] = []
  for (const msg of rawMessages) {
    const chatMsg = normalizeHistoryMessage(msg)
    if (!chatMsg) continue
    if (chatMsg.role === 'tool') {
      const lastAssistant = [...loaded].reverse().find(m => m.role === 'assistant')
      if (lastAssistant?.toolCalls) {
        const tc = lastAssistant.toolCalls.find(t => t.name === msg.name && !t.result)
        if (tc) {
          const resultStr = typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)
          tc.result = resultStr
          tc.status = 'done'
          tc.resultLength = resultStr.length
        }
      }
      continue
    }
    loaded.push(chatMsg)
  }
  return loaded
}

function mergeFinalUsageRounds(targetRounds: LlmRoundUsage[], rawRounds: any[]) {
  rawRounds.forEach((round: any, idx: number) => {
    const normalized = {
      inputTokens: round.input_tokens || 0,
      outputTokens: round.output_tokens || 0,
      totalTokens: round.total_tokens || 0,
      cacheReadTokens: round.cache_read_tokens || 0,
      reasoningTokens: round.reasoning_tokens || 0,
      duration: round.duration_ms || undefined,
    }
    if (targetRounds[idx]) {
      Object.assign(targetRounds[idx], normalized)
    } else {
      targetRounds.push(normalized)
    }
  })
}

export interface TodoItem {
  content: string
  status: 'pending' | 'in_progress' | 'completed'
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const isStreaming = ref(false)
  const isConnected = computed(() => !!threadId.value)
  const threadId = ref<string | null>(null)
  const interrupt = ref<InterruptInfo | null>(null)
  let sseClient: ChatSseClient | null = null
  const todos = ref<TodoItem[]>([])
  const errorMessage = ref<ErrorInfo | null>(null)

  const lastMessage = computed(() => messages.value[messages.value.length - 1])

  let streamStartTime = 0
  let currentRoundStart = 0
  let inThinking = false

  function _ensureClient(): ChatSseClient {
    if (!sseClient) {
      sseClient = new ChatSseClient()
      _registerHandlers(sseClient)
    }
    return sseClient
  }

  function _registerHandlers(client: ChatSseClient) {
    client.on('thinking', (msg: SseMessage) => {
      if (!isStreaming.value) {
        isStreaming.value = true
        streamStartTime = Date.now()
        currentRoundStart = Date.now()
        messages.value.push({
          id: createClientId(),
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          isStreaming: true,
          usage: { rounds: [], toolCallCount: 0 },
        })
      }
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'assistant') {
        if (!inThinking) {
          inThinking = true
          last.content += '<!--THINK_START-->'
        }
        last.content += msg.content || ''
      }
    })

    client.on('token', (msg: SseMessage) => {
      if (!isStreaming.value) {
        isStreaming.value = true
        streamStartTime = Date.now()
        currentRoundStart = Date.now()
        messages.value.push({
          id: createClientId(),
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          isStreaming: true,
          usage: { rounds: [], toolCallCount: 0 },
        })
      }
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'assistant') {
        if (inThinking) {
          inThinking = false
          last.content += '<!--THINK_END-->'
        }
        last.content += msg.content || ''
      }
    })

    client.on('content', (msg: SseMessage) => {
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'assistant') {
        last.content += msg.content || ''
      }
    })

    client.on('llm_usage', (msg: SseMessage) => {
      const last = messages.value[messages.value.length - 1]
      if (last?.usage) {
        const roundDuration = currentRoundStart ? Date.now() - currentRoundStart : undefined
        last.usage.rounds.push({
          inputTokens: msg.input_tokens || 0,
          outputTokens: msg.output_tokens || 0,
          totalTokens: msg.total_tokens || 0,
          cacheReadTokens: msg.cache_read_tokens || 0,
          reasoningTokens: msg.reasoning_tokens || 0,
          duration: roundDuration,
        })
        currentRoundStart = Date.now()
      }
    })

    client.on('tool_call', (msg: SseMessage) => {
      if (!isStreaming.value) {
        isStreaming.value = true
        streamStartTime = Date.now()
        currentRoundStart = Date.now()
        messages.value.push({
          id: createClientId(),
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          isStreaming: true,
          usage: { rounds: [], toolCallCount: 0 },
        })
      }
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'assistant') {
        if (inThinking) {
          inThinking = false
          last.content += '<!--THINK_END-->'
        }
        if (!last.toolCalls) last.toolCalls = []

        const existingByRunId = last.toolCalls.find(t => t.runId === msg.run_id)
        if (existingByRunId) {
          return
        }

        const tcIdx = last.toolCalls.length
        const tc: ToolCall = {
          name: msg.name || '',
          runId: msg.run_id,
          args: msg.args,
          status: 'running',
          startTime: Date.now(),
          is_subagent: (msg as any).is_subagent,
          sub_session_id: (msg as any).sub_session_id,
        }
        last.toolCalls.push(tc)
        last.content += `\n<!--TOOL:${tcIdx}-->\n`
        if (last.usage) {
          last.usage.toolCallCount++
        }
        if (msg.name === 'write_todos' && msg.args?.todos) {
          todos.value = msg.args.todos as TodoItem[]
        }
      }
    })

    client.on('tool_result', (msg: SseMessage) => {
      const last = messages.value[messages.value.length - 1]
      if (last?.toolCalls) {
        const tc = last.toolCalls.find(t => t.name === msg.name && t.status === 'running')
        if (tc) {
          tc.result = msg.result
          tc.status = 'done'
          tc.duration = tc.startTime ? Date.now() - tc.startTime : undefined
          tc.resultLength = msg.result?.length || 0
        }
      }
    })

    client.on('subagent_start', (msg: SseMessage) => {
      const last = messages.value[messages.value.length - 1]
      if (!last || last.role !== 'assistant') return

      const toolCallId = (msg as any).tool_call_id || msg.run_id || ''
      const subSessionId = (msg as any).sub_session_id
        || (threadId.value ? `${threadId.value}/sa/${toolCallId}` : '')

      const entry: SubAgentEntry = {
        tool_call_id: toolCallId,
        name: msg.name || '',
        sub_session_id: subSessionId,
        query: (msg as any).query || '',
        status: 'running',
        tokenPreview: '',
        toolCallCount: 0,
        tokenCount: 0,
        tokens: '',
        innerToolCalls: [],
      }
      if (!last.subAgents) {
        last.subAgents = {}
      }
      last.subAgents[toolCallId] = entry

      const tc = last.toolCalls?.find(t => t.runId === toolCallId)
      if (tc) {
        tc.is_subagent = true
        tc.sub_session_id = subSessionId
      }
      // Force Vue to detect the subAgents addition so SubAgentCard renders immediately
      messages.value = [...messages.value]
    })

    client.on('subagent_token', (msg: SseMessage) => {
      const last = messages.value[messages.value.length - 1]
      if (!last?.subAgents) return
      const toolCallId = (msg as any).tool_call_id
      const sa = last.subAgents[toolCallId]
      if (sa) {
        sa.tokens += msg.content || ''
        sa.tokenCount++
      }
    })

    client.on('subagent_thinking', (msg: SseMessage) => {
      // Thinking content is not displayed in SubAgentCard for now.
      void msg
    })

    client.on('subagent_tool_call', (msg: SseMessage) => {
      const last = messages.value[messages.value.length - 1]
      if (!last?.subAgents) return
      const toolCallId = (msg as any).tool_call_id
      const sa = last.subAgents[toolCallId]
      if (sa) {
        sa.innerToolCalls.push({
          name: msg.name || '',
          status: 'running',
          args: msg.args,
        })
        sa.toolCallCount++
      }
    })

    client.on('subagent_tool_result', (msg: SseMessage) => {
      const last = messages.value[messages.value.length - 1]
      if (!last?.subAgents) return
      const toolCallId = (msg as any).tool_call_id
      const sa = last.subAgents[toolCallId]
      if (sa) {
        const tc = [...sa.innerToolCalls].reverse().find(
          t => t.name === msg.name && t.status === 'running',
        )
        if (tc) {
          tc.result = msg.result
          tc.status = 'done'
        }
      }
    })

    client.on('subagent_done', (msg: SseMessage) => {
      const last = messages.value[messages.value.length - 1]
      if (!last) return
      const toolCallId = (msg as any).tool_call_id
      const sa = last.subAgents?.[toolCallId]
      if (sa) {
        sa.status = (msg as any).status === 'error' ? 'error' : 'done'
        sa.tokenPreview = (msg as any).result_preview || ''
        if ((msg as any).duration) sa.duration = (msg as any).duration
      }
      const tc = last.toolCalls?.find(t => t.runId === toolCallId)
      if (tc) {
        tc.status = (msg as any).status === 'error' ? 'error' : 'done'
        tc.result = (msg as any).result_preview
        tc.duration = tc.startTime ? Date.now() - tc.startTime : (msg as any).duration
        tc.resultLength = ((msg as any).result_preview || '').length
      }
    })

    client.on('interrupt', (msg: SseMessage) => {
      interrupt.value = {
        actionRequests: msg.action_requests || [],
        reviewConfigs: msg.review_configs || [],
        data: msg.data || [],
      }
    })

    client.on('done', (msg: SseMessage) => {
      errorMessage.value = null
      isStreaming.value = false
      inThinking = false
      const last = messages.value[messages.value.length - 1]
      if (last) {
        last.isStreaming = false
        const isResume = !!msg.is_resume
        const usageData = msg.usage as any[] | undefined
        if (usageData && usageData.length > 0) {
          if (last.usage && streamStartTime) {
            last.usage.totalDuration = Date.now() - streamStartTime
          }
          if (last.usage) {
            if (isResume) {
              const offset = last.usage.rounds.length - usageData.length
              usageData.forEach((round: any, idx: number) => {
                const normalized = {
                  inputTokens: round.input_tokens || 0,
                  outputTokens: round.output_tokens || 0,
                  totalTokens: round.total_tokens || 0,
                  cacheReadTokens: round.cache_read_tokens || 0,
                  reasoningTokens: round.reasoning_tokens || 0,
                  duration: round.duration_ms || undefined,
                }
                const targetIdx = offset + idx
                if (targetIdx >= 0 && last.usage!.rounds[targetIdx]) {
                  Object.assign(last.usage!.rounds[targetIdx], normalized)
                } else {
                  last.usage!.rounds.push(normalized)
                }
              })
            } else {
              mergeFinalUsageRounds(last.usage.rounds, usageData)
            }
          }
        }
        const rawTraces = (msg as any).http_traces || (msg as any).httpTraces
        if (rawTraces) {
          const newTraces = normalizeHttpTraces(rawTraces) || []
          if (isResume && newTraces.length) {
            last.httpTraces = [...(last.httpTraces || []), ...newTraces]
          } else if (newTraces.length) {
            last.httpTraces = newTraces
          }
          if (last.httpTraces?.length) {
            last.content = ensureHttpMarkers(last.content, last.httpTraces.length)
          }
        }
      }
      if (threadId.value) {
        setTimeout(() => {
          const sessionsStore = useSessionsStore()
          sessionsStore.refreshSessionTitle(threadId.value!)
        }, 3000)
      }
    })

    client.on('cancelled', () => {
      errorMessage.value = null
      isStreaming.value = false
      inThinking = false
      const last = messages.value[messages.value.length - 1]
      if (last) last.isStreaming = false
    })

    client.on('error', (msg: SseMessage) => {
      isStreaming.value = false
      if (inThinking) {
        const last = messages.value[messages.value.length - 1]
        if (last && last.role === 'assistant') {
          last.content += '<!--THINK_END-->'
        }
        inThinking = false
      }
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg && lastMsg.role === 'assistant') {
        lastMsg.isStreaming = false
      }
      if (msg.title) {
        errorMessage.value = {
          title: msg.title,
          detail: msg.detail || '',
          suggestions: msg.suggestions,
          techDetail: msg.tech_detail,
          errorCode: msg.error_code,
        }
      } else {
        errorMessage.value = {
          title: 'AI 模型接口请求失败',
          detail: msg.message || '',
          suggestions: ['请稍后重试，如问题持续请联系管理员'],
          errorCode: 'UNKNOWN',
        }
      }
      console.error('[Chat] Error:', msg.message || msg.title)
    })

    client.on('title_update', (msg: SseMessage) => {
      if (msg.thread_id && msg.title) {
        const sessionsStore = useSessionsStore()
        sessionsStore.updateTitleLocal(msg.thread_id, msg.title)
      }
    })
  }

  async function connect(existingThreadId?: string) {
    const client = _ensureClient()
    if (existingThreadId) {
      client.setThreadId(existingThreadId)
      threadId.value = existingThreadId
    }
  }

  async function sendMessage(
    content: string,
    presetId: string = '__chat__',
    modelId: string = '',
    options: SendMessageOptions = {},
  ) {
    if (!content.trim()) return

    errorMessage.value = null
    const sessionsStore = useSessionsStore()
    const sessionId = sessionsStore.currentSessionId
    if (sessionId && sessionsStore.isLocalSession(sessionId)) {
      const isFirstMessage = sessionsStore.currentSession?.message_count === 0
      const realId = await sessionsStore.persistSession(sessionId, modelId)
      await connect(realId)
      if (isFirstMessage) {
        sessionsStore.updateTitleLocal(realId, content.trim().slice(0, 30))
      }
    } else if (!threadId.value) {
      if (sessionId) await connect(sessionId)
    }

    const client = _ensureClient()
    if (!threadId.value) return

    messages.value.push({
      id: createClientId(),
      role: 'user',
      content: content.trim(),
      timestamp: Date.now(),
    })

    client.sendMessage(content.trim(), presetId, modelId, {
      replaceFromMessageId: options.replaceFromMessageId,
      history: options.history,
      llmParams: options.llmParams,
    })
  }

  function respondToInterrupt(
    approved: boolean,
    presetId: string = '__chat__',
    permanentlyAllow?: string,
    llmParams?: Record<string, any> | null,
  ) {
    const client = _ensureClient()
    const count = interrupt.value?.actionRequests?.length || 1
    const decisions = Array.from({ length: count }, () => ({
      type: approved ? 'approve' : 'reject',
    }))
    const resumePayload: Record<string, any> = { decisions }
    if (permanentlyAllow) {
      resumePayload.permanently_allow = permanentlyAllow
    }
    client.sendInterruptResume(resumePayload, presetId, undefined, llmParams)
    interrupt.value = null
    isStreaming.value = true
    currentRoundStart = Date.now()
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.isStreaming = true
    }
  }

  function resumeInterrupt(
    resumeValue: any,
    presetId: string = '__chat__',
    model?: string,
    llmParams?: Record<string, any> | null,
  ) {
    const client = _ensureClient()
    client.sendInterruptResume(resumeValue, presetId, model, llmParams)
    interrupt.value = null
    isStreaming.value = true
    currentRoundStart = Date.now()
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.isStreaming = true
    }
  }

  const totalMessageCount = ref(0)
  const hasOlderMessages = computed(() => {
    const loaded = messages.value.length
    return totalMessageCount.value > loaded
  })
  const loadingOlder = ref(false)
  let _currentOffset = 0

  async function loadMessages(sessionId: string) {
    try {
      const resp = await api.getSessionMessages(sessionId, { limit: INITIAL_MESSAGE_LIMIT })
      const total = resp?.total ?? 0
      const rawMessages = resp?.messages ?? resp
      totalMessageCount.value = total
      _currentOffset = resp?.offset ?? 0

      if (!rawMessages || rawMessages.length === 0) return

      messages.value = normalizeHistoryMessages(
        Array.isArray(rawMessages) ? rawMessages : []
      )
    } catch (e) {
      console.error('[Chat] Failed to load messages:', e)
    }
  }

  async function loadOlderMessages(sessionId: string) {
    if (!hasOlderMessages.value || loadingOlder.value || _currentOffset <= 0) return
    loadingOlder.value = true
    try {
      const olderPageSize = INITIAL_MESSAGE_LIMIT
      const newOffset = Math.max(0, _currentOffset - olderPageSize)
      const newLimit = _currentOffset - newOffset
      if (newLimit <= 0) return

      const resp = await api.getSessionMessages(sessionId, { limit: newLimit, offset: newOffset })
      const olderRaw = resp?.messages ?? []
      if (olderRaw.length === 0) return

      _currentOffset = newOffset
      const olderNormalized = normalizeHistoryMessages(olderRaw)
      messages.value = [...olderNormalized, ...messages.value]
    } catch (e) {
      console.error('[Chat] Failed to load older messages:', e)
    } finally {
      loadingOlder.value = false
    }
  }

  function stopGeneration() {
    if (sseClient && isStreaming.value) {
      sseClient.sendCancel()
    }
  }

  function clearMessages() {
    messages.value = []
    todos.value = []
  }

  function truncateAfterMessage(messageId: string) {
    const idx = messages.value.findIndex(m => m.id === messageId)
    if (idx < 0) return
    messages.value = messages.value.slice(0, idx)
  }

  function disconnect() {
    sseClient?.disconnect()
    sseClient = null
    errorMessage.value = null
    isStreaming.value = false
    threadId.value = null
    todos.value = []
    inThinking = false
  }

  return {
    messages,
    isStreaming,
    isConnected,
    threadId,
    interrupt,
    lastMessage,
    todos,
    errorMessage,
    totalMessageCount,
    hasOlderMessages,
    loadingOlder,
    connect,
    loadMessages,
    loadOlderMessages,
    sendMessage,
    stopGeneration,
    respondToInterrupt,
    resumeInterrupt,
    clearMessages,
    truncateAfterMessage,
    disconnect,
  }
})
