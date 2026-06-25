import type { HttpTrace, LlmRoundUsage } from '@/stores/chat'
import { parseSegments as parseContentSegments } from './parse-segments'
import type { ContentSegment } from './parse-segments'

export interface CopyOptions {
  includeThinking?: boolean
  includeToolCalls?: boolean
  includeHttpTraces?: boolean
  modelName?: string
}

interface ToolCallLike {
  name: string
  args?: Record<string, any>
  result?: string
  status?: string
  duration?: number
  resultLength?: number
}

interface MessageLike {
  role: 'user' | 'assistant' | 'tool'
  content: string
  toolCalls?: ToolCallLike[]
  httpTraces?: HttpTrace[]
  usage?: { rounds: LlmRoundUsage[] }
}

function toolCallToMarkdown(tc: ToolCallLike): string {
  const lines: string[] = []
  const meta = tc.duration ? ` (${(tc.duration / 1000).toFixed(1)}s)` : ''
  lines.push(`<details><summary>🔧 工具调用: ${tc.name}${meta}</summary>`)
  lines.push('')

  if (tc.args && Object.keys(tc.args).length > 0) {
    lines.push('**参数:**')
    for (const [k, v] of Object.entries(tc.args)) {
      const val = typeof v === 'string' ? v : JSON.stringify(v)
      const display = val.length > 200 ? val.slice(0, 200) + '...' : val
      lines.push(`- \`${k}\`: \`${display}\``)
    }
    lines.push('')
  }

  if (tc.result) {
    lines.push('**结果:**')
    lines.push('```')
    lines.push(tc.result)
    lines.push('```')
    lines.push('')
  }

  lines.push('</details>')
  return lines.join('\n')
}

function fmtTokens(n: number | undefined): string {
  if (n == null || n === 0) return ''
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

function httpTraceToMarkdown(trace: HttpTrace, usageRound?: LlmRoundUsage): string {
  const method = trace.request.method || 'HTTP'
  const status = trace.error ? '❌ 失败' : `${trace.response.status ?? '?'}`
  const duration = trace.durationMs != null
    ? (trace.durationMs >= 1000 ? `${(trace.durationMs / 1000).toFixed(1)}s` : `${trace.durationMs}ms`)
    : '-'

  const tokenParts: string[] = []
  if (usageRound) {
    if (usageRound.inputTokens) tokenParts.push(`输入 ${fmtTokens(usageRound.inputTokens)}`)
    if (usageRound.cacheReadTokens) tokenParts.push(`缓存 ${fmtTokens(usageRound.cacheReadTokens)}`)
    if (usageRound.outputTokens) tokenParts.push(`输出 ${fmtTokens(usageRound.outputTokens)}`)
    if (usageRound.reasoningTokens) tokenParts.push(`推理 ${fmtTokens(usageRound.reasoningTokens)}`)
  }
  const tokenStr = tokenParts.length > 0 ? tokenParts.join(' ') : ''

  const model = [trace.provider, trace.model].filter(Boolean).join(' / ')
  const url = trace.request.url || '未采集'

  const lines: string[] = []
  lines.push('| 项目 | 值 |')
  lines.push('| :-- | :-- |')
  lines.push(`| 🌐 HTTP | **#${trace.sequence}** \`${method}\` **${status}** ${duration} |`)
  if (tokenStr) lines.push(`| Tokens | ${tokenStr} |`)
  lines.push(`| URL | \`${url}\` |`)
  if (model) lines.push(`| 模型 | ${model} |`)
  if (trace.error) lines.push(`| 错误 | ${trace.error} |`)

  return lines.join('\n')
}

export function singleMessageToMarkdown(
  msg: MessageLike,
  options?: CopyOptions,
): string {
  const opts = { includeThinking: true, includeToolCalls: true, includeHttpTraces: true, ...options }

  if (msg.role === 'user') {
    return `## User\n\n${msg.content.trim()}`
  }

  const modelSuffix = opts.modelName ? ` (${opts.modelName})` : ''
  const lines: string[] = [`## Assistant${modelSuffix}`, '']
  const segments = parseContentSegments(msg.content)

  for (const seg of segments) {
    const segText = seg.text || ''
    if (seg.type === 'thinking' && opts.includeThinking) {
      lines.push('<details><summary>💭 思考过程</summary>')
      lines.push('')
      lines.push(segText)
      lines.push('')
      lines.push('</details>')
      lines.push('')
    } else if (seg.type === 'tool' && opts.includeToolCalls) {
      const tc = msg.toolCalls?.[seg.toolIndex!]
      if (tc) {
        lines.push(toolCallToMarkdown(tc))
        lines.push('')
      }
    } else if (seg.type === 'http' && opts.includeHttpTraces) {
      const trace = msg.httpTraces?.[seg.httpIndex!]
      if (trace) {
        const usageRound = msg.usage?.rounds?.[seg.httpIndex!]
        lines.push(httpTraceToMarkdown(trace, usageRound))
        lines.push('')
      }
    } else if (seg.type === 'text') {
      lines.push(segText)
      lines.push('')
    }
  }

  return lines.join('\n').trimEnd()
}

export function messagesToMarkdown(
  messages: MessageLike[],
  options?: CopyOptions,
): string {
  return messages
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .map(m => singleMessageToMarkdown(m, options))
    .join('\n\n---\n\n')
}

export function extractThinking(msg: MessageLike): string {
  return parseContentSegments(msg.content)
    .filter(s => s.type === 'thinking')
    .map(s => s.text || '')
    .join('\n\n')
}

export function extractToolCalls(msg: MessageLike): string {
  const segments = parseContentSegments(msg.content)
  return segments
    .filter(s => s.type === 'tool')
    .map(s => {
      const tc = msg.toolCalls?.[s.toolIndex!]
      return tc ? toolCallToMarkdown(tc) : ''
    })
    .filter(Boolean)
    .join('\n\n')
}

export function extractAnswer(msg: MessageLike): string {
  return parseContentSegments(msg.content)
    .filter(s => s.type === 'text')
    .map(s => s.text || '')
    .join('\n\n')
}

export function getRounds(messages: MessageLike[]): MessageLike[][] {
  const rounds: MessageLike[][] = []
  let current: MessageLike[] = []

  for (const msg of messages) {
    if (msg.role === 'user') {
      if (current.length > 0) rounds.push(current)
      current = [msg]
    } else if (msg.role === 'assistant') {
      current.push(msg)
    }
  }
  if (current.length > 0) rounds.push(current)
  return rounds
}

export function copyRecentRounds(
  messages: MessageLike[],
  n: number,
  options?: CopyOptions,
): string {
  const rounds = getRounds(messages)
  const recent = rounds.slice(-n)
  return recent
    .map(round => round.map(m => singleMessageToMarkdown(m, options)).join('\n\n'))
    .join('\n\n---\n\n')
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(textarea)
    return ok
  }
}
