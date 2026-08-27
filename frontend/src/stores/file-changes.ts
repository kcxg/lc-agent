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

export const useFileChangesStore = defineStore('fileChanges', () => {
  const files = ref<FileChangeItem[]>([])
  const subSessions = ref<SubSessionChanges[]>([])
  const gitBaseHash = ref<string | null>(null)
  const isDrawerOpen = ref(false)
  const loadedSessionId = ref<string | null>(null)

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

  function addFileChange(change: {
    file_path: string
    change_type: string
    move_destination?: string
  }) {
    const existing = files.value.find(f => f.file_path === change.file_path)
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
      files.value.push({
        file_path: change.file_path,
        change_type: change.change_type as FileChangeItem['change_type'],
        edit_count: 1,
        last_change_at: new Date().toISOString(),
        move_destination: change.move_destination,
      })
    }
  }

  async function fetchFileChanges(sessionId: string) {
    try {
      const data = await api.getFileChanges(sessionId)
      files.value = data.files || []
      subSessions.value = (data as any).sub_sessions || []
      gitBaseHash.value = data.git_base_hash || null
      loadedSessionId.value = sessionId
    } catch {
      // Silently fail — may be old session without file changes
    }
  }

  function reset() {
    files.value = []
    subSessions.value = []
    gitBaseHash.value = null
    isDrawerOpen.value = false
    loadedSessionId.value = null
  }

  return {
    files,
    subSessions,
    gitBaseHash,
    isDrawerOpen,
    loadedSessionId,
    fileCount,
    hasChanges,
    openDrawer,
    closeDrawer,
    addFileChange,
    fetchFileChanges,
    reset,
  }
})
