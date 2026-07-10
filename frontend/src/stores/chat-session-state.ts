import { ref } from 'vue'
import type { Ref } from 'vue'
import type { ChatSseClient } from '@/api/sse-client'
import type { ChatMessage, InterruptInfo, ErrorInfo, TodoItem } from './chat'

export interface SessionState {
  // Message data
  messages: Ref<ChatMessage[]>
  totalMessageCount: Ref<number>
  hasOlderMessages: Ref<boolean>
  loadingOlder: Ref<boolean>

  // Streaming state
  isStreaming: Ref<boolean>
  inThinking: boolean       // mutable flag, intentionally not Ref
  streamStartTime: number   // mutable, not Ref
  currentRoundStart: number // mutable, not Ref
  todos: Ref<TodoItem[]>
  interrupt: Ref<InterruptInfo | null>
  errorMessage: Ref<ErrorInfo | null>

  // SSE client (null until connect is called)
  client: ChatSseClient | null
}

export function createSessionState(): SessionState {
  return {
    messages: ref([]),
    totalMessageCount: ref(0),
    hasOlderMessages: ref(false),
    loadingOlder: ref(false),
    isStreaming: ref(false),
    inThinking: false,
    streamStartTime: 0,
    currentRoundStart: 0,
    todos: ref([]),
    interrupt: ref(null),
    errorMessage: ref(null),
    client: null,
  }
}
