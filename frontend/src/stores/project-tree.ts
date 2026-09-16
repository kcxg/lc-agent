import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/http'

export interface ProjectTreeEntry {
  name: string
  path: string
  type: 'dir' | 'file'
}

export const useProjectTreeStore = defineStore('projectTree', () => {
  // 已展开目录的下一层内容，key 为相对项目根的目录路径（根目录用空串）
  const children = ref<Record<string, ProjectTreeEntry[]>>({})
  const loading = ref<Record<string, boolean>>({})
  const error = ref<Record<string, string>>({})
  const projectRoot = ref('')
  // 当前 git 分支；项目不是 git 仓库时为 null
  const gitBranch = ref<string | null>(null)
  const agentId = ref<string | null>(null)
  // 待定位的文件路径：「在树中显示」/切换标签时写入，由 FileTreeNode 递归消费
  const revealPath = ref('')

  function entriesOf(path: string): ProjectTreeEntry[] {
    return children.value[path] ?? []
  }

  function isLoading(path: string): boolean {
    return !!loading.value[path]
  }

  function isLoaded(path: string): boolean {
    return path in children.value
  }

  async function load(id: string, path: string = '') {
    loading.value = { ...loading.value, [path]: true }
    const { [path]: _e, ...restErrors } = error.value
    error.value = restErrors
    try {
      const data = await api.getProjectTree(id, path)
      agentId.value = id
      if (data.error) {
        return { error: data.error }
      }
      projectRoot.value = data.project_root || projectRoot.value
      if (data.git_branch !== undefined) gitBranch.value = data.git_branch ?? null
      children.value = { ...children.value, [path]: data.entries || [] }
      return {}
    } catch (e: any) {
      return { error: e.message || '加载目录失败' }
    } finally {
      const { [path]: _l, ...restLoading } = loading.value
      loading.value = restLoading
    }
  }

  function clear() {
    children.value = {}
    loading.value = {}
    error.value = {}
    gitBranch.value = null
    agentId.value = null
    revealPath.value = ''
  }

  /** 请求在树中展开并滚动定位到某个文件/目录 */
  function reveal(path: string) {
    revealPath.value = ''
    revealPath.value = path
  }

  return {
    children,
    loading,
    error,
    projectRoot,
    gitBranch,
    agentId,
    revealPath,
    entriesOf,
    isLoading,
    isLoaded,
    load,
    clear,
    reveal,
  }
})
