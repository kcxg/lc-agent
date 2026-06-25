import type { ToolCall, HttpTrace } from '@/stores/chat'

export interface ContentSegment {
  type: 'text' | 'thinking' | 'tool' | 'http'
  text?: string
  toolIndex?: number
  httpIndex?: number
}

const THINK_START = '<!--THINK_START-->'
const THINK_END = '<!--THINK_END-->'
const TOOL_RE = /<!--TOOL:(\d+)-->/g
const HTTP_RE = /<!--HTTP:(\d+)-->/g
const ANY_MARKER = /<!--(?:TOOL:(\d+)|HTTP:(\d+)|THINK_START|THINK_END)-->/g

/**
 * Parse message content into structured segments.
 * Shared by ChatView.vue, ChatBubble.vue, and copy-markdown.ts.
 */
export function parseSegments(
  content: string,
): ContentSegment[] {
  const segments: ContentSegment[] = []
  if (!content) return segments

  const pattern = ANY_MARKER
  let lastIndex = 0
  let match: RegExpExecArray | null
  let inThinking = false
  // We need a fresh regex each call since it's stateful with lastIndex
  const re = new RegExp(ANY_MARKER.source, 'g')

  while ((match = re.exec(content)) !== null) {
    const textBefore = content.slice(lastIndex, match.index)
    const trimmed = textBefore.trim()
    const marker = match[0]

    if (marker === THINK_START) {
      if (trimmed) {
        segments.push({ type: inThinking ? 'thinking' : 'text', text: trimmed })
      }
      inThinking = true
      lastIndex = match.index + marker.length
      continue
    }

    if (marker === THINK_END) {
      if (trimmed) {
        segments.push({ type: 'thinking', text: trimmed })
      }
      inThinking = false
      lastIndex = match.index + marker.length
      continue
    }

    // TOOL or HTTP marker
    if (trimmed) {
      segments.push({ type: inThinking ? 'thinking' : 'text', text: trimmed })
    }

    if (match[2] != null) {
      // HTTP marker (group 2)
      segments.push({ type: 'http', httpIndex: parseInt(match[2], 10) })
    } else if (match[1] != null) {
      // TOOL marker (group 1)
      segments.push({ type: 'tool', toolIndex: parseInt(match[1], 10) })
    }

    lastIndex = match.index + marker.length
  }

  const remaining = content.slice(lastIndex).trim()
  if (remaining) {
    segments.push({ type: inThinking ? 'thinking' : 'text', text: remaining })
  }

  return segments
}

/**
 * Check if content has structured segments (thinking markers, tool calls, HTTP traces).
 */
export function hasStructuredSegments(
  content: string,
  toolCalls?: ToolCall[],
): boolean {
  return Boolean(
    toolCalls?.length
    || content.includes(THINK_START)
    || content.includes(THINK_END)
    || content.includes('<!--HTTP:'),
  )
}

/**
 * Strip all UI markers from content, returning plain text.
 */
export function stripUiMarkers(content: string): string {
  return content
    .replace(/<!--(?:THINK_START|THINK_END)-->/g, '')
    .replace(/<!--TOOL:\d+-->/g, '')
    .replace(/<!--HTTP:\d+-->/g, '')
    .trim()
}

/**
 * Get total reasoning token count from usage data.
 */
export function getReasoningTokenTotal(
  usage?: { rounds: { reasoningTokens: number }[] },
): number {
  return usage?.rounds.reduce((total, round) => total + (round.reasoningTokens || 0), 0) || 0
}
