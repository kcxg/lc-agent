export interface CopyOptions {
  includeThinking?: boolean
  includeToolCalls?: boolean
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
}

const THINK_START = '<!--THINK_START-->'
const THINK_END = '<!--THINK_END-->'
const TOOL_RE = /<!--TOOL:(\d+)-->/

interface Segment {
  type: 'text' | 'thinking' | 'tool'
  content: string
  toolIndex?: number
}

function parseSegments(content: string): Segment[] {
  const segments: Segment[] = []
  let remaining = content
  let inThinking = false

  while (remaining.length > 0) {
    if (!inThinking) {
      const thinkStart = remaining.indexOf(THINK_START)
      const toolMatch = TOOL_RE.exec(remaining)

      const nextThink = thinkStart >= 0 ? thinkStart : Infinity
      const nextTool = toolMatch ? toolMatch.index : Infinity

      if (nextThink === Infinity && nextTool === Infinity) {
        const trimmed = remaining.trim()
        if (trimmed) segments.push({ type: 'text', content: trimmed })
        break
      }

      const nextMarker = Math.min(nextThink, nextTool)
      const before = remaining.slice(0, nextMarker).trim()
      if (before) segments.push({ type: 'text', content: before })

      if (nextThink < nextTool) {
        remaining = remaining.slice(thinkStart + THINK_START.length)
        inThinking = true
      } else {
        const idx = parseInt(toolMatch![1], 10)
        segments.push({ type: 'tool', content: '', toolIndex: idx })
        remaining = remaining.slice(toolMatch!.index + toolMatch![0].length)
      }
    } else {
      const thinkEnd = remaining.indexOf(THINK_END)
      if (thinkEnd >= 0) {
        const thinking = remaining.slice(0, thinkEnd).trim()
        if (thinking) segments.push({ type: 'thinking', content: thinking })
        remaining = remaining.slice(thinkEnd + THINK_END.length)
        inThinking = false
      } else {
        const thinking = remaining.trim()
        if (thinking) segments.push({ type: 'thinking', content: thinking })
        break
      }
    }
  }
  return segments
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

export function singleMessageToMarkdown(
  msg: MessageLike,
  options?: CopyOptions,
): string {
  const opts = { includeThinking: true, includeToolCalls: true, ...options }

  if (msg.role === 'user') {
    return `## User\n\n${msg.content.trim()}`
  }

  const modelSuffix = opts.modelName ? ` (${opts.modelName})` : ''
  const lines: string[] = [`## Assistant${modelSuffix}`, '']
  const segments = parseSegments(msg.content)

  for (const seg of segments) {
    if (seg.type === 'thinking' && opts.includeThinking) {
      lines.push('<details><summary>💭 思考过程</summary>')
      lines.push('')
      lines.push(seg.content)
      lines.push('')
      lines.push('</details>')
      lines.push('')
    } else if (seg.type === 'tool' && opts.includeToolCalls) {
      const tc = msg.toolCalls?.[seg.toolIndex!]
      if (tc) {
        lines.push(toolCallToMarkdown(tc))
        lines.push('')
      }
    } else if (seg.type === 'text') {
      lines.push(seg.content)
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
  return parseSegments(msg.content)
    .filter(s => s.type === 'thinking')
    .map(s => s.content)
    .join('\n\n')
}

export function extractToolCalls(msg: MessageLike): string {
  const segments = parseSegments(msg.content)
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
  return parseSegments(msg.content)
    .filter(s => s.type === 'text')
    .map(s => s.content)
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
