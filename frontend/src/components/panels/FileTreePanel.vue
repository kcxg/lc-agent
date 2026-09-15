<template>
  <div class="file-tree-panel">
    <div class="panel-section tree-toolbar">
      <div class="tree-toolbar-row">
        <div class="tree-project" :title="store.projectRoot || '项目'">
          <el-icon class="tree-project-icon"><FolderOpened /></el-icon>
          <span class="tree-project-name">{{ rootLabel }}</span>
        </div>

        <span v-if="store.gitBranch" class="tree-branch" :title="`当前 git 分支：${store.gitBranch}`">
          <svg viewBox="0 0 16 16" aria-hidden="true">
            <path
              d="M5 3.5v6.2M5 12.5a2 2 0 1 0 0-.01M11 5.5a2 2 0 1 0 0-.01M11 5.5v1c0 1.4-1.1 2.5-2.5 2.5H5"
              fill="none"
              stroke="currentColor"
              stroke-width="1.4"
              stroke-linecap="round"
            />
            <circle cx="5" cy="12.4" r="2" fill="none" stroke="currentColor" stroke-width="1.4" />
            <circle cx="11" cy="3.6" r="2" fill="none" stroke="currentColor" stroke-width="1.4" />
          </svg>
          <span class="tree-branch-name">{{ store.gitBranch }}</span>
        </span>

        <button class="tree-icon-btn" type="button" title="刷新目录" :disabled="loading" @click="reload">
          <svg viewBox="0 0 16 16" :class="{ spinning: loading }" aria-hidden="true">
            <path
              d="M13 8a5 5 0 1 1-1.5-3.6M13 2v3h-3"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>
      </div>

      <div class="tree-search">
        <el-icon class="tree-search-icon"><Search /></el-icon>
        <input
          v-model="keyword"
          class="tree-search-input"
          type="text"
          placeholder="搜索项目内文件或目录"
          @keydown.esc="keyword = ''"
        />
        <button
          v-if="keyword"
          class="tree-search-clear"
          type="button"
          title="清空"
          @click="keyword = ''"
        >
          <svg viewBox="0 0 12 12" aria-hidden="true">
            <path
              d="M3.5 3.5l5 5m0-5l-5 5"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </svg>
        </button>
      </div>
    </div>

    <div v-if="error" class="tree-error">{{ error }}</div>

    <template v-else-if="searching || keyword">
      <div class="tree-scroll">
        <div v-if="searching" class="tree-status">
          <el-icon class="is-loading"><Loading /></el-icon>
          搜索中
        </div>
        <div v-else-if="searchError" class="tree-error tree-error-inline">{{ searchError }}</div>
        <template v-else-if="results.length > 0">
          <div class="tree-status tree-status-count">
            <span>{{ results.length }} 个匹配</span>
            <span v-if="searchTruncated" class="tree-truncated">已截断</span>
          </div>
          <div
            v-for="item in results"
            :key="item.path"
            class="result-item"
            :class="{ 'is-active': isActiveFile(item) }"
            role="button"
            tabindex="0"
            :title="item.path"
            @click="openResult(item)"
            @keydown.enter="openResult(item)"
            @keydown.space.prevent="openResult(item)"
          >
            <FileTypeIcon
              :name="item.type === 'dir' ? '' : item.name"
              :is-directory="item.type === 'dir'"
              :compact="true"
            />
            <span class="result-name">{{ item.name }}</span>
            <span class="result-path">{{ parentDir(item.path) }}</span>
          </div>
        </template>
        <div v-else class="tree-status">
          没有匹配「{{ keyword }}」的文件或目录
        </div>
      </div>
    </template>

    <template v-else>
      <div v-if="loading && rootEntries.length === 0" class="tree-status">
        <el-icon class="is-loading"><Loading /></el-icon>
        加载目录
      </div>

      <div v-else-if="rootEntries.length === 0" class="tree-status">目录为空</div>

      <div v-else class="tree-scroll">
        <FileTreeNode
          v-for="entry in rootEntries"
          :key="entry.path"
          :entry="entry"
          :depth="0"
        />
      </div>
    </template>

    <CodeBlockModal
      :visible="previewVisible"
      :code="previewCode"
      :language="previewLang"
      :title="previewPath"
      kicker="项目文件"
      :render-as-markdown="previewAsMarkdown"
      :source-path="previewSourcePath"
      @close="previewVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, provide, ref, watch } from 'vue'
import { Document as _Document, Folder as _Folder, Loading, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api/http'
import { useAgentsStore } from '@/stores/agents'
import { useProjectTreeStore, type ProjectTreeEntry } from '@/stores/project-tree'
import { useUiStore } from '@/stores/ui'
import FileTreeNode from '@/components/panels/FileTreeNode.vue'
import CodeBlockModal from '@/components/chat/CodeBlockModal.vue'

const store = useProjectTreeStore()
const agentsStore = useAgentsStore()
const uiStore = useUiStore()

const error = ref('')

const rootEntries = computed(() => store.entriesOf(''))
const loading = computed(() => store.isLoading(''))

const rootLabel = computed(() => {
  const root = store.projectRoot
  if (!root) return '项目'
  return root.split(/[\\/]/).filter(Boolean).pop() || root
})

async function loadRoot() {
  const agentId = agentsStore.currentAgentId
  if (!agentId) return
  error.value = ''
  const result = await store.load(agentId, '')
  error.value = result.error || ''
}

function reload() {
  store.clear()
  keyword.value = ''
  void loadRoot()
}

// ---- 全项目搜索（覆盖未展开的目录）----
const keyword = ref('')
const results = ref<ProjectTreeEntry[]>([])
const searching = ref(false)
const searchError = ref('')
const searchTruncated = ref(false)
let searchToken = 0
let searchTimer: ReturnType<typeof setTimeout> | null = null

function isActiveFile(item: ProjectTreeEntry): boolean {
  return item.type !== 'dir' && activeFile.value === item.path
}

function parentDir(path: string): string {
  const idx = path.lastIndexOf('/')
  return idx === -1 ? '' : path.slice(0, idx)
}

async function runSearch() {
  const agentId = agentsStore.currentAgentId
  const q = keyword.value.trim()
  if (!agentId || !q) {
    results.value = []
    searchError.value = ''
    searchTruncated.value = false
    searching.value = false
    return
  }

  const token = ++searchToken
  searching.value = true
  searchError.value = ''
  try {
    const data = await api.searchProjectFiles(agentId, q)
    if (token !== searchToken) return
    if (data.error) {
      searchError.value = data.error
      results.value = []
      return
    }
    store.projectRoot = data.project_root || store.projectRoot
    if (data.git_branch !== undefined) store.gitBranch = data.git_branch ?? null
    results.value = data.results || []
    searchTruncated.value = !!data.truncated
  } catch (e: any) {
    if (token !== searchToken) return
    searchError.value = e.message || '搜索失败'
    results.value = []
  } finally {
    if (token === searchToken) searching.value = false
  }
}

watch(keyword, () => {
  if (searchTimer) clearTimeout(searchTimer)
  if (!keyword.value.trim()) {
    searchToken += 1
    results.value = []
    searchError.value = ''
    searching.value = false
    return
  }
  searching.value = true
  searchTimer = setTimeout(() => { void runSearch() }, 260)
})

async function openResult(item: ProjectTreeEntry) {
  if (item.type === 'dir') {
    keyword.value = ''
    await store.load(agentsStore.currentAgentId, item.path)
    return
  }
  await openFile(item.path)
}

watch(
  () => [uiStore.activeTab, agentsStore.currentAgentId] as const,
  ([tab, agentId]) => {
    if (tab !== 'files' || !agentId) return
    if (store.agentId !== agentId) {
      store.clear()
      keyword.value = ''
    }
    void loadRoot()
  },
  { immediate: true },
)

const previewVisible = ref(false)
const previewCode = ref('')
const previewLang = ref('text')
const previewPath = ref('')
const previewAsMarkdown = ref(false)
// 当前预览的文件路径，供列表/树节点高亮
const activeFile = ref('')

// 复制行号需要绝对路径：项目根 + 项目内相对路径
const previewSourcePath = computed(() => {
  const root = store.projectRoot
  if (!root || !previewPath.value) return ''
  const sep = root.includes('\\') ? '\\' : '/'
  const base = root.replace(/[\\/]+$/, '')
  return `${base}${sep}${previewPath.value.replace(/\//g, sep)}`
})

provide('openFile', (path: string) => { void openFile(path) })
provide('activeFile', activeFile)

const EXT_LANG_MAP: Record<string, string> = {
  py: 'python', ts: 'typescript', tsx: 'typescript', js: 'javascript', jsx: 'javascript',
  vue: 'xml', yml: 'yaml', md: 'markdown', sh: 'bash', zsh: 'bash', ps1: 'powershell',
  rs: 'rust', rb: 'ruby', kt: 'kotlin', cs: 'csharp', h: 'c', hpp: 'cpp', cc: 'cpp',
}

async function openFile(path: string) {
  const agentId = agentsStore.currentAgentId
  if (!agentId) return
  try {
    const data = await api.readFile(path, 2000, agentId)
    if (data.error) {
      ElMessage.error(`无法读取 ${path}: ${data.error}`)
      return
    }
    previewCode.value = (data.lines || []).join('\n') + (data.truncated ? '\n\n... (内容已截断)' : '')
    const ext = path.split('.').pop()?.toLowerCase() || ''
    previewLang.value = EXT_LANG_MAP[ext] || ext
    previewAsMarkdown.value = ext === 'md'
    previewPath.value = path
    activeFile.value = path
    previewVisible.value = true
  } catch (e: any) {
    ElMessage.error(e.message || '读取文件失败')
  }
}
</script>

<style scoped>
.file-tree-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.tree-toolbar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tree-toolbar-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.tree-project {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
  max-width: 50%;
  min-width: 0;
  color: var(--el-text-color-primary);
  font-size: 12.5px;
  font-weight: 700;
}

.tree-project-icon {
  flex-shrink: 0;
  color: #d9a441;
  font-size: 15px;
}

.tree-project-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 分支胶囊：内容自适应，不撑满整行 */
.tree-branch {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 1;
  min-width: 0;
  max-width: 46%;
  padding: 2px 8px;
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 32%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--el-color-primary) 9%, transparent);
  color: var(--el-color-primary);
  font-size: 11px;
  font-weight: 600;
  line-height: 1.5;
}

.tree-branch svg {
  flex-shrink: 0;
  width: 11px;
  height: 11px;
}

.tree-branch-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  margin-left: auto;
  padding: 0;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  transition: all 0.16s ease;
}

.tree-icon-btn svg {
  width: 13px;
  height: 13px;
}

.tree-icon-btn:hover:not(:disabled) {
  border-color: color-mix(in srgb, var(--el-color-primary) 40%, transparent);
  background: color-mix(in srgb, var(--el-color-primary) 8%, transparent);
  color: var(--el-color-primary);
}

.tree-icon-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.tree-icon-btn .spinning {
  animation: spin 0.9s linear infinite;
}

.tree-search {
  position: relative;
  display: flex;
  align-items: center;
}

.tree-search-icon {
  position: absolute;
  left: 9px;
  color: var(--el-text-color-placeholder);
  font-size: 13px;
  pointer-events: none;
}

.tree-search-input {
  width: 100%;
  height: 30px;
  padding: 0 28px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  outline: none;
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-primary);
  font-size: 12px;
  transition: border-color 0.16s ease, box-shadow 0.16s ease;
}

.tree-search-input::placeholder {
  color: var(--el-text-color-placeholder);
}

.tree-search-input:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 13%, transparent);
}

.tree-search-clear {
  position: absolute;
  right: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: var(--el-fill-color-dark);
  color: var(--el-text-color-secondary);
  cursor: pointer;
  transition: background 0.16s ease, color 0.16s ease;
}

.tree-search-clear svg {
  width: 10px;
  height: 10px;
}

.tree-search-clear:hover {
  background: var(--el-text-color-placeholder);
  color: var(--el-bg-color);
}

.tree-scroll {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 2px;
}

/* 搜索结果 */
.result-item {
  display: flex;
  align-items: center;
  gap: 7px;
  min-height: 26px;
  padding: 2px 7px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.14s ease;
}

.result-item:hover {
  background: var(--el-fill-color-light);
}

.result-item.is-active {
  background: color-mix(in srgb, var(--el-color-primary) 13%, transparent);
  box-shadow: inset 2px 0 0 var(--el-color-primary);
}

.result-name {
  flex-shrink: 0;
  max-width: 58%;
  overflow: hidden;
  color: var(--el-text-color-primary);
  font-size: 12.5px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-path {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: var(--el-text-color-placeholder);
  font-size: 11px;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
  direction: rtl;
}

.tree-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 20px 12px;
  color: var(--el-text-color-placeholder);
  font-size: 12px;
  text-align: center;
}

.tree-status-count {
  justify-content: flex-start;
  padding: 4px 6px 8px;
  color: var(--el-text-color-secondary);
  font-size: 11px;
}

.tree-truncated {
  padding: 1px 6px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--el-color-warning) 16%, transparent);
  color: var(--el-color-warning);
  font-size: 10px;
}

.tree-error {
  padding: 14px 10px;
  color: var(--el-color-danger);
  font-size: 12px;
  word-break: break-all;
}

.tree-error-inline {
  padding: 14px 4px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .tree-icon-btn .spinning {
    animation: none;
  }
}
</style>
