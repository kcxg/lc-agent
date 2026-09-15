import { defineStore } from 'pinia'
import { ref, computed, reactive } from 'vue'
import { api } from '@/api/http'

export interface FileChangeItem {
  file_path: string
  change_type: 'edit' | 'create' | 'append' | 'delete' | 'move'
  edit_count: number
  last_change_at: string
  move_destination?: string
  additions: number
  deletions: number
}

export interface SubSessionChanges {
  sub_session_id: string
  title: string
  file_count: number
  files: FileChangeItem[]
}

export interface RoundGroup {
  round_number: number
  files: FileChangeItem[]
  sub_sessions: SubSessionChanges[]
}

/** 单个会话的文件变更数据 */
interface SessionChangesState {
  files: FileChangeItem[]
  subSessions: SubSessionChanges[]
  rounds: RoundGroup[]
  selectedRound: number | null
  gitBaseHash: string | null
  gitAvailable: boolean
  loaded: boolean
}

function createSessionChangesState(): SessionChangesState {
  return {
    files: [],
    subSessions: [],
    rounds: [],
    selectedRound: null,
    gitBaseHash: null,
    gitAvailable: false,
    loaded: false,
  }
}

function countLines(text?: string | null): number {
  return text ? text.split('\n').length : 0
}

export const useFileChangesStore = defineStore('fileChanges', () => {
  // 按 sessionId 分桶：切标签时保留各会话的变更数据与轮次选择，切回不重拉
  const bySession = reactive(new Map<string, SessionChangesState>())
  const activeSessionId = ref<string | null>(null)
  // 待定位展开的文件：卡片点击后由变更面板消费（展开 diff 并滚动定位）
  const pendingOpenFile = ref<string | null>(null)

  function _bucket(sessionId: string): SessionChangesState {
    let state = bySession.get(sessionId)
    if (!state) {
      state = createSessionChangesState()
      bySession.set(sessionId, state)
    }
    return state
  }

  const _active = computed<SessionChangesState | null>(() =>
    activeSessionId.value ? (bySession.get(activeSessionId.value) ?? null) : null,
  )

  const files = computed(() => _active.value?.files ?? [])
  const subSessions = computed(() => _active.value?.subSessions ?? [])
  const rounds = computed(() => _active.value?.rounds ?? [])
  const gitBaseHash = computed(() => _active.value?.gitBaseHash ?? null)
  const gitAvailable = computed(() => _active.value?.gitAvailable ?? false)
  const loadedSessionId = computed(() => (_active.value?.loaded ? activeSessionId.value : null))

  const selectedRound = computed({
    get: () => _active.value?.selectedRound ?? null,
    set: (value: number | null) => {
      if (_active.value) _active.value.selectedRound = value
    },
  })

  const displayFiles = computed(() => {
    const state = _active.value
    if (!state) return []
    if (state.selectedRound == null) return state.files
    return state.rounds.find(r => r.round_number === state.selectedRound)?.files || []
  })
  const displaySubSessions = computed(() => {
    const state = _active.value
    if (!state) return []
    if (state.selectedRound == null) return state.subSessions
    return state.rounds.find(r => r.round_number === state.selectedRound)?.sub_sessions || []
  })

  const fileCount = computed(() => {
    const state = _active.value
    if (!state) return 0
    const subFileCount = state.subSessions.reduce((sum, s) => sum + s.file_count, 0)
    return state.files.length + subFileCount
  })
  const hasChanges = computed(() => {
    const state = _active.value
    if (!state) return false
    return state.files.length > 0 || state.subSessions.length > 0
  })

  function mergeIntoFileList(list: FileChangeItem[], change: {
    file_path: string
    change_type: string
    move_destination?: string
    old_string?: string | null
    new_string?: string | null
  }) {
    const additions = change.change_type === 'edit'
      ? countLines(change.new_string)
      : (change.change_type === 'create' || change.change_type === 'append') ? countLines(change.new_string) : 0
    const deletions = change.change_type === 'edit' ? countLines(change.old_string) : 0
    const existing = list.find(f => f.file_path === change.file_path)
    if (existing) {
      existing.edit_count += 1
      existing.last_change_at = new Date().toISOString()
      existing.additions += additions
      existing.deletions += deletions
      if (change.change_type === 'delete') {
        existing.change_type = 'delete'
      } else if (change.change_type === 'move') {
        existing.change_type = 'move'
        existing.move_destination = change.move_destination
      } else if (existing.change_type !== 'create' && existing.change_type !== 'delete') {
        existing.change_type = change.change_type as FileChangeItem['change_type']
      }
    } else {
      list.push({
        file_path: change.file_path,
        change_type: change.change_type as FileChangeItem['change_type'],
        edit_count: 1,
        last_change_at: new Date().toISOString(),
        move_destination: change.move_destination,
        additions,
        deletions,
      })
    }
  }

  /** 实时 SSE 事件：写入事件所属会话的桶（不一定是当前激活会话） */
  function addFileChange(change: {
    file_path: string
    change_type: string
    move_destination?: string
    round_number?: number | null
    old_string?: string | null
    new_string?: string | null
  }, sessionId?: string) {
    const targetId = sessionId || activeSessionId.value
    if (!targetId) return
    const state = _bucket(targetId)
    mergeIntoFileList(state.files, change)
    if (change.round_number != null) {
      let round = state.rounds.find(r => r.round_number === change.round_number)
      if (!round) {
        round = { round_number: change.round_number, files: [], sub_sessions: [] }
        state.rounds.push(round)
        state.rounds.sort((a, b) => a.round_number - b.round_number)
      }
      mergeIntoFileList(round.files, change)
    }
  }

  /** 切换激活会话：命中缓存则直接复用，不再请求 */
  function switchToSession(sessionId: string): void {
    activeSessionId.value = sessionId
    const state = bySession.get(sessionId)
    if (!state?.loaded) void fetchFileChanges(sessionId)
  }

  async function fetchFileChanges(sessionId: string) {
    try {
      const data = await api.getFileChanges(sessionId)
      const state = _bucket(sessionId)
      state.files = data.files || []
      state.subSessions = (data as any).sub_sessions || []
      state.rounds = ((data as any).rounds || []).map((r: any) => ({
        round_number: r.round_number,
        files: r.files || [],
        sub_sessions: r.sub_sessions || [],
      }))
      state.selectedRound = null
      state.gitBaseHash = data.git_base_hash || null
      state.gitAvailable = Boolean((data as any).git_available)
      state.loaded = true
    } catch {
      // Silently fail — may be old session without file changes
    }
  }

  /** 关闭标签时丢弃该会话的变更缓存 */
  function dropSession(sessionId: string): void {
    bySession.delete(sessionId)
    if (activeSessionId.value === sessionId) activeSessionId.value = null
  }

  /** SSE 快照事件写入指定会话的基准哈希 */
  function setGitBaseHash(sessionId: string, hash: string): void {
    _bucket(sessionId).gitBaseHash = hash
  }

  /** 会话 id 改写（本地 id → 真实 id）时搬迁缓存 */
  function renameSession(oldId: string, newId: string): void {
    if (oldId === newId) return
    const state = bySession.get(oldId)
    if (state) {
      bySession.set(newId, state)
      bySession.delete(oldId)
    }
    if (activeSessionId.value === oldId) activeSessionId.value = newId
  }

  function reset() {
    activeSessionId.value = null
    pendingOpenFile.value = null
  }

  return {
    files,
    subSessions,
    rounds,
    selectedRound,
    gitBaseHash,
    gitAvailable,
    loadedSessionId,
    pendingOpenFile,
    displayFiles,
    displaySubSessions,
    fileCount,
    hasChanges,
    addFileChange,
    switchToSession,
    fetchFileChanges,
    setGitBaseHash,
    dropSession,
    renameSession,
    reset,
  }
})
