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
  isHistoryLoading: Ref<boolean>

  // Streaming state
  isStreaming: Ref<boolean>
  /** 服务端是否仍在该会话上运行：本地没有流时（刷新过页面）靠轮询 /run-status 得知 */
  serverRunning: Ref<boolean>
  /** 正在请求停止（防止重复点击把状态反复改写） */
  cancelling: Ref<boolean>
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
    isHistoryLoading: ref(false),
    isStreaming: ref(false),
    serverRunning: ref(false),
    cancelling: ref(false),
    inThinking: false,
    streamStartTime: 0,
    currentRoundStart: 0,
    todos: ref([]),
    interrupt: ref(null),
    errorMessage: ref(null),
    client: null,
  }
}
