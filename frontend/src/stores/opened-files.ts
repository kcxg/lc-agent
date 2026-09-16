import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import { api } from '@/api/http'
import { useAgentsStore } from '@/stores/agents'
import { useProjectTreeStore } from '@/stores/project-tree'
import { useUiStore } from '@/stores/ui'

export interface OpenedFile {
  // 读取内容用的路径：文件树传项目内相对路径，聊天区文件链接传绝对路径
  path: string
  name: string
  // 绝对路径，供「复制行号」使用
  sourcePath: string
  language: string
  asMarkdown: boolean
  // 固定标签：关闭其他/关闭全部时保留，排序时置前
  pinned: boolean
}

interface FileContent {
  code: string
  truncated: boolean
  loading: boolean
  error: string
  loaded: boolean
  // 二进制文件（.db 等）：不渲染内容，展示提示
  binary: boolean
  // 图片文件：渲染 imageDataUrl
  image: boolean
  imageDataUrl: string
  imageTooLarge: boolean
  // ---- 编辑支持 ----
  // 相对未保存修改
  dirty: boolean
  // 保存中锁：防止重复提交
  saving: boolean
  // 读取时的 mtime，保存时做乐观锁
  mtime: number
  // 原文件换行符与 BOM，写回时原样保留
  newline: 'lf' | 'crlf'
  hasBom: boolean
  // 后端判定是否允许编辑（UTF-8 无损且未截断）；不可编辑时给出原因
  editable: boolean
  readonlyReason: string
  // 保存失败的错误（与加载错误 error 分开，不互相覆盖）
  saveError: string
  // 最近一次保存/加载时的内容基线，与 code 比较判断脏状态
  savedCode: string
}

const IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'ico', 'avif']

const EXT_LANG_MAP: Record<string, string> = {
  py: 'python', ts: 'typescript', tsx: 'typescript', js: 'javascript', jsx: 'javascript',
  vue: 'xml', yml: 'yaml', md: 'markdown', sh: 'bash', zsh: 'bash', ps1: 'powershell',
  rs: 'rust', rb: 'ruby', kt: 'kotlin', cs: 'csharp', h: 'c', hpp: 'cpp', cc: 'cpp',
}

function extOf(path: string): string {
  return path.split('.').pop()?.toLowerCase() || ''
}

function langOf(path: string): string {
  const ext = extOf(path)
  return EXT_LANG_MAP[ext] || ext || 'text'
}

function nameOf(path: string): string {
  return path.split(/[\\/]/).filter(Boolean).pop() || path
}

function isImagePath(path: string): boolean {
  return IMAGE_EXTENSIONS.includes(extOf(path))
}

// 项目根 + 相对路径 → 绝对路径（分隔符跟随项目根风格）
function toAbsolute(relative: string): string {
  const treeStore = useProjectTreeStore()
  if (/^[a-zA-Z]:[\\/]/.test(relative) || relative.startsWith('/')) return relative
  const root = treeStore.projectRoot || useAgentsStore().currentAgent?.project_root?.trim() || ''
  if (!root) return relative
  const sep = root.includes('\\') ? '\\' : '/'
  return `${root.replace(/[\\/]+$/, '')}${sep}${relative.replace(/\//g, sep)}`
}

// 文件标签按 agent 持久化到 localStorage，刷新后恢复；与会话标签同一套模式
const OPENED_FILES_KEY_PREFIX = 'lc-agent:opened-files:'

interface PersistedFilesState {
  files: OpenedFile[]
  activePath: string
}

function loadPersistedState(agentId: string): PersistedFilesState | null {
  try {
    const raw = localStorage.getItem(OPENED_FILES_KEY_PREFIX + agentId)
    if (!raw) return null
    const parsed = JSON.parse(raw) as PersistedFilesState
    if (!Array.isArray(parsed.files)) return null
    return parsed
  } catch {
    return null
  }
}

function savePersistedState(agentId: string, state: PersistedFilesState): void {
  try {
    localStorage.setItem(OPENED_FILES_KEY_PREFIX + agentId, JSON.stringify(state))
  } catch {
    /* ignore */
  }
}

export const useOpenedFilesStore = defineStore('openedFiles', () => {
  const agentsStore = useAgentsStore()
  const files = ref<OpenedFile[]>([])
  const activePath = ref('')
  const contents = ref<Record<string, FileContent>>({})
  // 待跳转的行号：内容加载完成后由 FileEditorPane 消费并清空
  const jumpLine = ref(0)
  // 已关闭标签栈，供「恢复已关闭的标签」使用（仅当前 agent 会话内有效）
  const closedStack = ref<OpenedFile[]>([])

  const activeFile = computed(() => files.value.find(f => f.path === activePath.value) ?? null)
  const activeContent = computed(() => contents.value[activePath.value] ?? null)

  function contentOf(path: string): FileContent | null {
    return contents.value[path] ?? null
  }

  // 固定标签永远排在未固定标签之前，保持各自相对顺序
  function normalizeOrder(list: OpenedFile[]): OpenedFile[] {
    const pinned = list.filter(f => f.pinned)
    const rest = list.filter(f => !f.pinned)
    return [...pinned, ...rest]
  }

  function emptyContent(overrides: Partial<FileContent> = {}): FileContent {
    return {
      code: '', truncated: false, loading: false, error: '', loaded: false,
      binary: false, image: false, imageDataUrl: '', imageTooLarge: false,
      dirty: false, saving: false, mtime: 0, newline: 'lf', hasBom: false,
      editable: false, readonlyReason: '', saveError: '', savedCode: '',
      ...overrides,
    }
  }

  // 刷新后启动恢复：从 localStorage 读回当前 agent 的文件标签（在 agentsStore 完成初始化后由 App 触发）
  function restoreForCurrentAgent() {
    const agentId = agentsStore.currentAgentId
    if (!agentId || files.value.length > 0) return
    const persisted = loadPersistedState(agentId)
    if (persisted && persisted.files.length > 0) {
      // 兼容早期存档：pinned 字段可能缺失
      files.value = normalizeOrder(persisted.files.map(f => ({ ...f, pinned: !!f.pinned })))
      activePath.value = persisted.activePath
      const file = files.value.find(f => f.path === activePath.value)
      if (file) void loadContent(file)
    }
  }

  async function loadContent(file: OpenedFile) {
    const current = contents.value[file.path]
    if (current?.loading || current?.loaded) return
    contents.value[file.path] = emptyContent({ loading: true })
    const agentsStore = useAgentsStore()
    try {
      // 相对路径需要 agent_id 才能定位项目根；绝对路径后端直接读
      const isRelative = !/^[a-zA-Z]:[\\/]/.test(file.path) && !file.path.startsWith('/')
      // 请求大行数，配合 CodeMirror 虚拟滚动可打开大文件
      const data = await api.readFile(file.path, 200000, isRelative ? agentsStore.currentAgentId : undefined)
      if (data.error) {
        contents.value[file.path] = emptyContent({ error: data.error, loaded: true })
        return
      }
      if (data.image) {
        contents.value[file.path] = emptyContent({
          loaded: true,
          image: true,
          imageDataUrl: data.data_url || '',
          imageTooLarge: !!data.image_too_large,
        })
        return
      }
      if (data.binary) {
        contents.value[file.path] = emptyContent({ loaded: true, binary: true })
        return
      }
      contents.value[file.path] = emptyContent({
        code: (data.lines || []).join('\n'),
        truncated: !!data.truncated,
        loaded: true,
        mtime: data.mtime ?? 0,
        newline: data.newline === 'crlf' ? 'crlf' : 'lf',
        hasBom: !!data.has_bom,
        editable: !!data.editable,
        readonlyReason: data.readonly_reason || '',
        savedCode: (data.lines || []).join('\n'),
      })
    } catch (e: any) {
      contents.value[file.path] = emptyContent({ error: e.message || '读取文件失败', loaded: true })
    }
  }

  function open(path: string, options?: { name?: string; sourcePath?: string; line?: number }) {
    if (!path) return
    const existing = files.value.find(f => f.path === path)
    if (!existing) {
      files.value = normalizeOrder([...files.value, {
        path,
        name: options?.name || nameOf(path),
        sourcePath: options?.sourcePath || toAbsolute(path),
        language: langOf(path),
        asMarkdown: path.toLowerCase().endsWith('.md'),
        pinned: false,
      }])
    }
    activePath.value = path
    jumpLine.value = options?.line ?? 0
    const file = files.value.find(f => f.path === path)!
    void loadContent(file)
    useUiStore().requestTab('editor')
  }

  function activate(path: string) {
    if (!files.value.some(f => f.path === path)) return
    activePath.value = path
    jumpLine.value = 0
    const file = files.value.find(f => f.path === path)!
    void loadContent(file)
  }

  /** 请求滚动到指定行；内容已加载时 FileEditorPane 会立刻消费 */
  function requestJumpToLine(line: number) {
    jumpLine.value = line
  }

  function consumeJumpLine() {
    jumpLine.value = 0
  }

  function close(path: string) {
    const idx = files.value.findIndex(f => f.path === path)
    if (idx === -1) return
    const closing = files.value[idx]
    if (!closing.pinned) {
      closedStack.value = [...closedStack.value, closing].slice(-20)
    }
    const next = [...files.value]
    next.splice(idx, 1)
    files.value = next
    delete contents.value[path]
    if (activePath.value === path) {
      const fallback = next[idx] || next[idx - 1] || null
      activePath.value = fallback ? fallback.path : ''
      if (fallback) void loadContent(fallback)
    }
  }

  /** 关闭除指定标签外的全部（固定标签保留） */
  function closeOthers(keepPath: string) {
    const kept = files.value.filter(f => f.pinned || f.path === keepPath)
    const removed = files.value.filter(f => !f.pinned && f.path !== keepPath)
    if (removed.length === 0) return
    closedStack.value = [...closedStack.value, ...removed].slice(-20)
    files.value = normalizeOrder(kept)
    for (const f of removed) delete contents.value[f.path]
    if (!kept.some(f => f.path === activePath.value)) {
      activePath.value = kept.length > 0 ? kept[kept.length - 1].path : ''
    }
  }

  /** 关闭指定标签右侧的全部（固定标签保留） */
  function closeToRight(path: string) {
    const idx = files.value.findIndex(f => f.path === path)
    if (idx === -1) return
    const left = files.value.slice(0, idx + 1)
    const right = files.value.slice(idx + 1)
    const removed = right.filter(f => !f.pinned)
    const kept = normalizeOrder([...left, ...right.filter(f => f.pinned)])
    if (removed.length === 0) return
    closedStack.value = [...closedStack.value, ...removed].slice(-20)
    files.value = kept
    for (const f of removed) delete contents.value[f.path]
    if (!kept.some(f => f.path === activePath.value)) {
      activePath.value = path
    }
  }

  /** 固定/取消固定标签；固定后自动置前 */
  function togglePin(path: string) {
    const file = files.value.find(f => f.path === path)
    if (!file) return
    files.value = normalizeOrder(
      files.value.map(f => (f.path === path ? { ...f, pinned: !f.pinned } : f)),
    )
  }

  /** 恢复最近关闭的标签 */
  function reopenClosed() {
    const stack = [...closedStack.value]
    const last = stack.pop()
    if (!last) return
    closedStack.value = stack
    if (!files.value.some(f => f.path === last.path)) {
      files.value = normalizeOrder([...files.value, last])
    }
    activePath.value = last.path
    void loadContent(last)
    useUiStore().requestTab('editor')
  }

  function closeAll() {
    // 固定标签在「关闭全部」时保留
    const pinned = files.value.filter(f => f.pinned)
    const removed = files.value.filter(f => !f.pinned)
    closedStack.value = [...closedStack.value, ...removed].slice(-20)
    for (const f of removed) delete contents.value[f.path]
    files.value = pinned
    activePath.value = pinned.length > 0 ? pinned[0].path : ''
  }

  /** 重命名/删除后同步标签路径（含激活项、固定状态、内容缓存） */
  function renamePath(oldPath: string, newPath: string, newName: string) {
    const file = files.value.find(f => f.path === oldPath)
    if (!file) return
    files.value = files.value.map(f =>
      f.path === oldPath
        ? { ...f, path: newPath, name: newName, sourcePath: toAbsolute(newPath), language: langOf(newPath), asMarkdown: newPath.toLowerCase().endsWith('.md') }
        : f,
    )
    if (contents.value[oldPath]) {
      contents.value[newPath] = contents.value[oldPath]
      delete contents.value[oldPath]
    }
    if (activePath.value === oldPath) activePath.value = newPath
  }

  /** 删除文件/目录后关闭受影响的标签（目录下所有文件一并关闭） */
  function closeUnderPath(targetPath: string) {
    const prefix = targetPath.replace(/[\\/]+$/, '')
    const affected = files.value.filter(
      f => f.path === targetPath || f.path.startsWith(prefix + '/') || f.path.startsWith(prefix + '\\'),
    )
    for (const f of affected) close(f.path)
  }

  /** 文件树/重命名后局部失效：清掉该目录缓存并重新拉取 */
  function invalidateTree(path: string) {
    const treeStore = useProjectTreeStore()
    delete treeStore.children[path]
  }

  // 切换 agent 时：把旧 agent 的标签集存档，载入新 agent 的标签集；
  // 新 agent 没有存档则清空。各 agent 的文件标签互不串扰。
  function switchAgent(previousId: string, nextId: string) {
    if (previousId) {
      savePersistedState(previousId, { files: files.value, activePath: activePath.value })
    }
    files.value = []
    contents.value = {}
    activePath.value = ''
    closedStack.value = []
    const persisted = nextId ? loadPersistedState(nextId) : null
    if (persisted && persisted.files.length > 0) {
      files.value = normalizeOrder(persisted.files.map(f => ({ ...f, pinned: !!f.pinned })))
      activePath.value = persisted.activePath
      const file = files.value.find(f => f.path === activePath.value)
      if (file) void loadContent(file)
    }
  }

  watch(() => agentsStore.currentAgentId, (nextId, previousId) => {
    switchAgent(previousId ?? '', nextId)
  })

  // 标签集或激活项变化时持久化到当前 agent 名下
  watch([files, activePath], () => {
    if (agentsStore.currentAgentId) {
      savePersistedState(agentsStore.currentAgentId, { files: files.value, activePath: activePath.value })
    }
  }, { deep: true })

  function refresh(path: string) {
    const file = files.value.find(f => f.path === path)
    if (!file) return
    delete contents.value[path]
    void loadContent(file)
  }

  /** 编辑器内容变化时调用：与保存基线比较维护脏状态 */
  function markDirty(path: string, nextCode: string) {
    const c = contents.value[path]
    if (!c || !c.loaded) return
    c.code = nextCode
    c.dirty = nextCode !== c.savedCode
  }

  /** 保存当前文件；成功后更新 mtime 并清除脏标记 */
  async function save(path: string): Promise<{ ok?: boolean; error?: string; conflict?: boolean }> {
    const c = contents.value[path]
    if (!c || !c.loaded || !c.editable) return { error: '文件不可编辑' }
    if (c.saving) return {}
    c.saving = true
    c.saveError = ''
    const agentsStore = useAgentsStore()
    const agentId = agentsStore.currentAgentId
    try {
      if (!agentId) return { error: '无活跃 Agent' }
      const result = await api.saveFile(agentId, path, c.code, {
        mtime: c.mtime, newline: c.newline, hasBom: c.hasBom,
      })
      if (result.error) {
        c.saveError = result.error
        if (result.conflict) {
          // 冲突后刷新 mtime，用户重载后才能再保存
          c.mtime = result.mtime ?? c.mtime
        }
        return result
      }
      c.mtime = result.mtime ?? c.mtime
      c.dirty = false
      c.savedCode = c.code
      return { ok: true }
    } catch (e: any) {
      c.saveError = e.message || '保存失败'
      return { error: c.saveError }
    } finally {
      c.saving = false
    }
  }

  return {
    files,
    activePath,
    activeFile,
    activeContent,
    jumpLine,
    contentOf,
    isImagePath,
    open,
    activate,
    close,
    closeOthers,
    closeToRight,
    closeAll,
    togglePin,
    reopenClosed,
    renamePath,
    closeUnderPath,
    invalidateTree,
    restoreForCurrentAgent,
    requestJumpToLine,
    consumeJumpLine,
    refresh,
    markDirty,
    save,
  }
})
