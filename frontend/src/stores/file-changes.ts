import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/http'

export interface FileChangeItem {
  file_path: string
  change_type: 'edit' | 'create' | 'append' | 'delete' | 'move'
  edit_count: number
  last_change_at: string
  move_destination?: string
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

export const useFileChangesStore = defineStore('fileChanges', () => {
  const files = ref<FileChangeItem[]>([])
  const subSessions = ref<SubSessionChanges[]>([])
  const rounds = ref<RoundGroup[]>([])
  const selectedRound = ref<number | null>(null) // null = 全部轮次
  const gitBaseHash = ref<string | null>(null)
  const isDrawerOpen = ref(false)
  const loadedSessionId = ref<string | null>(null)

  const displayFiles = computed(() => {
    if (selectedRound.value == null) return files.value
    return rounds.value.find(r => r.round_number === selectedRound.value)?.files || []
  })
  const displaySubSessions = computed(() => {
    if (selectedRound.value == null) return subSessions.value
    return rounds.value.find(r => r.round_number === selectedRound.value)?.sub_sessions || []
  })

  const fileCount = computed(() => {
    const subFileCount = subSessions.value.reduce((sum, s) => sum + s.file_count, 0)
    return files.value.length + subFileCount
  })
  const hasChanges = computed(() => files.value.length > 0 || subSessions.value.length > 0)

  function openDrawer() {
    isDrawerOpen.value = true
  }

  function closeDrawer() {
    isDrawerOpen.value = false
  }

  function mergeIntoFileList(list: FileChangeItem[], change: {
    file_path: string
    change_type: string
    move_destination?: string
  }) {
    const existing = list.find(f => f.file_path === change.file_path)
    if (existing) {
      existing.edit_count += 1
      existing.last_change_at = new Date().toISOString()
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
      })
    }
  }

  function addFileChange(change: {
    file_path: string
    change_type: string
    move_destination?: string
    round_number?: number | null
  }) {
    mergeIntoFileList(files.value, change)
    if (change.round_number != null) {
      let round = rounds.value.find(r => r.round_number === change.round_number)
      if (!round) {
        round = { round_number: change.round_number, files: [], sub_sessions: [] }
        rounds.value.push(round)
        rounds.value.sort((a, b) => a.round_number - b.round_number)
      }
      mergeIntoFileList(round.files, change)
    }
  }

  async function fetchFileChanges(sessionId: string) {
    try {
      const data = await api.getFileChanges(sessionId)
      files.value = data.files || []
      subSessions.value = (data as any).sub_sessions || []
      rounds.value = ((data as any).rounds || []).map((r: any) => ({
        round_number: r.round_number,
        files: r.files || [],
        sub_sessions: r.sub_sessions || [],
      }))
      selectedRound.value = null
      gitBaseHash.value = data.git_base_hash || null
      loadedSessionId.value = sessionId
    } catch {
      // Silently fail — may be old session without file changes
    }
  }

  function reset() {
    files.value = []
    subSessions.value = []
    rounds.value = []
    selectedRound.value = null
    gitBaseHash.value = null
    isDrawerOpen.value = false
    loadedSessionId.value = null
  }

  return {
    files,
    subSessions,
    rounds,
    selectedRound,
    gitBaseHash,
    isDrawerOpen,
    loadedSessionId,
    displayFiles,
    displaySubSessions,
    fileCount,
    hasChanges,
    openDrawer,
    closeDrawer,
    addFileChange,
    fetchFileChanges,
    reset,
  }
})
