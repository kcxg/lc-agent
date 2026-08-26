<template>
  <el-drawer
    v-model="store.isDrawerOpen"
    direction="rtl"
    :size="isMobile ? '100%' : '40%'"
    :modal="true"
    :append-to-body="true"
    :close-on-click-modal="true"
    :close-on-press-escape="true"
    class="file-changes-drawer"
  >
    <template #header>
      <div class="drawer-header">
        <h3 class="drawer-title">文件变更</h3>
        <div class="drawer-actions">
          <el-button
            v-if="store.gitBaseHash"
            size="small"
            type="primary"
            plain
            :loading="gitDiffLoading"
            @click="loadGitDiff"
          >
            Git Diff
          </el-button>
          <el-segmented
            v-model="diffMode"
            :options="[
              { label: 'Unified', value: 'unified' },
              { label: 'Side by Side', value: 'side-by-side' },
            ]"
            size="small"
          />
        </div>
      </div>
    </template>

    <div v-if="!store.hasChanges" class="empty-state">
      <p>当前会话没有文件变更</p>
    </div>

    <div v-else class="file-list">
      <div
        v-for="file in store.files"
        :key="file.file_path"
        class="file-item"
      >
        <div
          class="file-header"
          role="button"
          tabindex="0"
          :aria-expanded="expandedFiles.has(file.file_path)"
          @click="toggleExpand(file.file_path)"
          @keydown.enter="toggleExpand(file.file_path)"
          @keydown.space.prevent="toggleExpand(file.file_path)"
        >
          <span class="expand-icon">{{ expandedFiles.has(file.file_path) ? '▼' : '▶' }}</span>
          <span :class="['change-tag', `change-tag--${file.change_type}`]">
            {{ changeTypeLabels[file.change_type] || '?' }}
          </span>
          <span class="file-name" :title="file.file_path">
            {{ getFileName(file.file_path) }}
          </span>
          <span class="file-dir" :title="file.file_path">{{ getFileDir(file.file_path) }}</span>
          <el-tooltip content="复制路径" placement="top" :show-after="300">
            <button class="copy-path-btn" @click="copyPath(file.file_path, $event)" aria-label="复制文件路径">📋</button>
          </el-tooltip>
          <span v-if="file.edit_count > 1" class="edit-count">×{{ file.edit_count }}</span>
        </div>

        <div v-if="expandedFiles.has(file.file_path)" class="file-diff-container">
          <div v-if="loadingDiffs.has(file.file_path)" class="diff-loading">
            <el-icon class="is-loading"><Loading /></el-icon> 加载中...
          </div>
          <div
            v-else-if="fileDiffs[file.file_path]"
            class="diff-content"
            v-html="fileDiffs[file.file_path]"
          />
          <div v-else class="diff-empty">无法生成 diff</div>
        </div>
      </div>
    </div>

    <!-- Sub-agent summaries -->
    <div v-if="store.subSessions.length > 0" class="sub-agent-section">
      <div class="sub-agent-section-title">子 Agent 变更</div>
      <div
        v-for="sub in store.subSessions"
        :key="sub.sub_session_id"
        class="sub-agent-item"
      >
        <div
          class="sub-agent-header"
          role="button"
          tabindex="0"
          :aria-expanded="expandedSubSessions.has(sub.sub_session_id)"
          @click="toggleSubSession(sub.sub_session_id)"
          @keydown.enter="toggleSubSession(sub.sub_session_id)"
          @keydown.space.prevent="toggleSubSession(sub.sub_session_id)"
        >
          <span class="expand-icon">{{ expandedSubSessions.has(sub.sub_session_id) ? '▼' : '▶' }}</span>
          <span class="sub-agent-icon">🤖</span>
          <span class="sub-agent-title">{{ sub.title }}</span>
          <span class="sub-agent-badge">{{ sub.file_count }} 个文件</span>
        </div>
        <div v-if="expandedSubSessions.has(sub.sub_session_id)" class="sub-agent-files">
          <div
            v-for="file in sub.files"
            :key="file.file_path"
            class="file-item sub-file-item"
          >
            <div
              class="file-header"
              role="button"
              tabindex="0"
              :aria-expanded="expandedFiles.has(`${sub.sub_session_id}:${file.file_path}`)"
              @click="toggleExpandSubFile(sub.sub_session_id, file.file_path)"
              @keydown.enter="toggleExpandSubFile(sub.sub_session_id, file.file_path)"
              @keydown.space.prevent="toggleExpandSubFile(sub.sub_session_id, file.file_path)"
            >
              <span class="expand-icon">{{ expandedFiles.has(`${sub.sub_session_id}:${file.file_path}`) ? '▼' : '▶' }}</span>
              <span :class="['change-tag', `change-tag--${file.change_type}`]">
                {{ changeTypeLabels[file.change_type] || '?' }}
              </span>
              <span class="file-name" :title="file.file_path">{{ getFileName(file.file_path) }}</span>
              <span class="file-dir" :title="file.file_path">{{ getFileDir(file.file_path) }}</span>
              <el-tooltip content="复制路径" placement="top" :show-after="300">
                <button class="copy-path-btn" @click.stop="copyPath(file.file_path, $event)" aria-label="复制文件路径">📋</button>
              </el-tooltip>
            </div>
            <div v-if="expandedFiles.has(`${sub.sub_session_id}:${file.file_path}`)" class="file-diff-container">
              <div v-if="loadingDiffs.has(`${sub.sub_session_id}:${file.file_path}`)" class="diff-loading">
                <el-icon class="is-loading"><Loading /></el-icon> 加载中...
              </div>
              <div
                v-else-if="fileDiffs[`${sub.sub_session_id}:${file.file_path}`]"
                class="diff-content"
                v-html="fileDiffs[`${sub.sub_session_id}:${file.file_path}`]"
              />
              <div v-else class="diff-empty">无法生成 diff</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Git diff modal: load the file list first, then load one file on demand -->
    <el-dialog
      v-model="showGitDiff"
      title="Git Diff (完整变更)"
      width="80%"
      :append-to-body="true"
      destroy-on-close
      class="git-diff-dialog"
    >
      <div v-if="gitDiffLoading" class="diff-loading">
        <el-icon class="is-loading"><Loading /></el-icon> 加载文件列表...
      </div>
      <div v-else-if="gitDiffError" class="git-diff-error">{{ gitDiffError }}</div>
      <div v-else-if="gitDiffFiles.length === 0" class="diff-empty">没有可显示的文件变更</div>
      <div v-else class="git-diff-file-list">
        <div
          v-for="file in gitDiffFiles"
          :key="file.file_path"
          class="git-diff-file-item"
        >
          <div
            class="git-diff-file-header"
            role="button"
            tabindex="0"
            :aria-expanded="expandedGitFiles.has(file.file_path)"
            @click="toggleGitFile(file.file_path)"
            @keydown.enter="toggleGitFile(file.file_path)"
            @keydown.space.prevent="toggleGitFile(file.file_path)"
          >
            <span class="expand-icon">{{ expandedGitFiles.has(file.file_path) ? '▼' : '▶' }}</span>
            <span :class="['change-tag', `change-tag--${file.change_type}`]">
              {{ changeTypeLabels[file.change_type] || '?' }}
            </span>
            <span class="file-name" :title="file.file_path">{{ getFileName(file.file_path) }}</span>
            <span class="file-dir" :title="file.file_path">{{ getFileDir(file.file_path) }}</span>
          </div>
          <div v-if="expandedGitFiles.has(file.file_path)" class="file-diff-container">
            <div v-if="loadingGitFiles.has(file.file_path)" class="diff-loading">
              <el-icon class="is-loading"><Loading /></el-icon> 加载中...
            </div>
            <div
              v-else-if="gitFileDiffs[file.file_path]"
              class="diff-content"
              v-html="gitFileDiffs[file.file_path]"
            />
            <div v-else class="diff-empty">无法生成 diff</div>
          </div>
        </div>
      </div>
    </el-dialog>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, onBeforeUnmount } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { useFileChangesStore } from '@/stores/file-changes'
import { useSessionsStore } from '@/stores/sessions'
import { api } from '@/api/http'
import { html as diff2htmlHtml } from 'diff2html'
import 'diff2html/bundles/css/diff2html.min.css'

const store = useFileChangesStore()
const sessionsStore = useSessionsStore()

const diffMode = ref<'unified' | 'side-by-side'>('unified')
const expandedFiles = reactive(new Set<string>())
const expandedSubSessions = reactive(new Set<string>())
const loadingDiffs = reactive(new Set<string>())
const fileDiffs = reactive<Record<string, string>>({})

const gitDiffLoading = ref(false)
const showGitDiff = ref(false)
const gitDiffError = ref('')
const gitDiffFiles = ref<Array<{
  file_path: string
  change_type: string
  additions: number
  deletions: number
}>>([])
const expandedGitFiles = reactive(new Set<string>())
const loadingGitFiles = reactive(new Set<string>())
const gitFileDiffs = reactive<Record<string, string>>({})
const gitRawFileDiffs = reactive<Record<string, string>>({})

const isMobile = ref(window.innerWidth <= 900)
const handleResize = () => { isMobile.value = window.innerWidth <= 900 }
onMounted(() => { window.addEventListener('resize', handleResize) })
onBeforeUnmount(() => { window.removeEventListener('resize', handleResize) })

const changeTypeLabels: Record<string, string> = {
  edit: 'M',
  create: 'A',
  append: 'M',
  delete: 'D',
  move: 'R',
}

function getFileName(path: string): string {
  return path.split(/[\\/]/).pop() || path
}

function getFileDir(path: string): string {
  const parts = path.split(/[\\/]/)
  if (parts.length <= 1) return ''
  parts.pop()
  return parts.join('/')
}

async function copyPath(path: string, event: Event) {
  event.stopPropagation()
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(path)
      return
    } catch {
      // fall through to fallback
    }
  }
  const textarea = document.createElement('textarea')
  textarea.value = path
  textarea.setAttribute('readonly', 'true')
  textarea.style.position = 'fixed'
  textarea.style.left = '-9999px'
  document.body.appendChild(textarea)
  textarea.select()
  try {
    document.execCommand('copy')
  } catch {
    // ignore
  } finally {
    document.body.removeChild(textarea)
  }
}

async function toggleExpand(filePath: string) {
  if (expandedFiles.has(filePath)) {
    expandedFiles.delete(filePath)
    return
  }

  expandedFiles.add(filePath)

  if (fileDiffs[filePath]) return

  const sessionId = sessionsStore.currentSessionId
  if (!sessionId) return

  loadingDiffs.add(filePath)
  try {
    const data = await api.getFileDiff(sessionId, filePath)
    fileDiffs[filePath] = renderDiff(data, filePath)
  } catch {
    fileDiffs[filePath] = '<div class="diff-error">加载失败</div>'
  } finally {
    loadingDiffs.delete(filePath)
  }
}

function renderUnifiedDiff(unifiedDiff: string, filePath: string): string {
  try {
    return diff2htmlHtml(unifiedDiff, {
      outputFormat: diffMode.value === 'side-by-side' ? 'side-by-side' : 'line-by-line',
      drawFileList: false,
    })
  } catch {
    return `<pre class="diff-fallback">${unifiedDiff}</pre>`
  }
}

function renderDiff(data: any, filePath: string): string {
  if (data.unified_diff) {
    return renderUnifiedDiff(data.unified_diff, filePath)
  }

  const hunks = data.hunks || []
  if (hunks.length === 0) return '<div class="diff-empty">无变更内容</div>'

  const unifiedLines: string[] = []
  unifiedLines.push(`--- a/${getFileName(filePath)}`)
  unifiedLines.push(`+++ b/${getFileName(filePath)}`)

  for (const hunk of hunks) {
    if (hunk.type === 'edit') {
      const removed = hunk.removed || []
      const added = hunk.added || []
      unifiedLines.push(`@@ -1,${removed.length} +1,${added.length} @@`)
      for (const line of removed) unifiedLines.push(`-${line}`)
      for (const line of added) unifiedLines.push(`+${line}`)
    } else if (hunk.type === 'create' || hunk.type === 'append') {
      const added = hunk.added || []
      unifiedLines.push(`@@ -0,0 +1,${added.length} @@`)
      for (const line of added) unifiedLines.push(`+${line}`)
    } else if (hunk.type === 'delete') {
      unifiedLines.push(`@@ -1,1 +0,0 @@`)
      unifiedLines.push(`-[file deleted]`)
    } else if (hunk.type === 'move') {
      unifiedLines.push(`@@ @@`)
      unifiedLines.push(`-[moved to: ${hunk.destination || '?'}]`)
    }
  }

  const diffText = unifiedLines.join('\n')
  try {
    return diff2htmlHtml(diffText, {
      outputFormat: diffMode.value === 'side-by-side' ? 'side-by-side' : 'line-by-line',
      drawFileList: false,
    })
  } catch {
    return `<pre class="diff-fallback">${diffText}</pre>`
  }
}

watch(diffMode, () => {
  for (const key of expandedFiles) {
    if (!fileDiffs[key]) continue
    const isSubKey = key.includes('--sa--') && key.includes(':')
    const sessionId = isSubKey
      ? key.slice(0, key.indexOf(':', key.indexOf('--sa--')))
      : sessionsStore.currentSessionId
    const filePath = isSubKey
      ? key.slice(key.indexOf(':', key.indexOf('--sa--')) + 1)
      : key
    if (!sessionId) continue
    loadingDiffs.add(key)
    api.getFileDiff(sessionId, filePath).then(data => {
      fileDiffs[key] = renderDiff(data, filePath)
    }).catch(() => {}).finally(() => loadingDiffs.delete(key))
  }

  for (const filePath of expandedGitFiles) {
    const rawDiff = gitRawFileDiffs[filePath]
    if (rawDiff) gitFileDiffs[filePath] = renderUnifiedDiff(rawDiff, filePath)
  }
})

async function loadGitDiff() {
  const sessionId = sessionsStore.currentSessionId
  if (!sessionId) return

  gitDiffLoading.value = true
  gitDiffError.value = ''
  gitDiffFiles.value = []
  expandedGitFiles.clear()
  Object.keys(gitFileDiffs).forEach(key => delete gitFileDiffs[key])
  Object.keys(gitRawFileDiffs).forEach(key => delete gitRawFileDiffs[key])

  try {
    const data = await api.getGitDiffFiles(sessionId)
    if (data.available && data.files) {
      gitDiffFiles.value = data.files
      showGitDiff.value = true
    } else {
      gitDiffError.value = data.reason || '无法获取 Git Diff 文件列表'
      showGitDiff.value = true
    }
  } catch (e: any) {
    gitDiffError.value = e.message || '请求失败'
    showGitDiff.value = true
  } finally {
    gitDiffLoading.value = false
  }
}

async function toggleGitFile(filePath: string) {
  if (expandedGitFiles.has(filePath)) {
    expandedGitFiles.delete(filePath)
    delete gitFileDiffs[filePath]
    delete gitRawFileDiffs[filePath]
    return
  }

  expandedGitFiles.add(filePath)
  if (gitFileDiffs[filePath]) return

  const sessionId = sessionsStore.currentSessionId
  if (!sessionId) return
  loadingGitFiles.add(filePath)
  try {
    const data = await api.getGitFileDiff(sessionId, filePath)
    if (data.available && data.diff) {
      gitRawFileDiffs[filePath] = data.diff
      gitFileDiffs[filePath] = renderUnifiedDiff(data.diff, filePath)
    } else {
      gitFileDiffs[filePath] = `<div class="diff-error">${data.reason || '无法生成 diff'}</div>`
    }
  } catch (e: any) {
    gitFileDiffs[filePath] = `<div class="diff-error">${e.message || '加载失败'}</div>`
  } finally {
    loadingGitFiles.delete(filePath)
  }
}

function toggleSubSession(subSessionId: string) {
  if (expandedSubSessions.has(subSessionId)) {
    expandedSubSessions.delete(subSessionId)
  } else {
    expandedSubSessions.add(subSessionId)
  }
}

async function toggleExpandSubFile(subSessionId: string, filePath: string) {
  const key = `${subSessionId}:${filePath}`
  if (expandedFiles.has(key)) {
    expandedFiles.delete(key)
    return
  }
  expandedFiles.add(key)
  if (fileDiffs[key]) return

  loadingDiffs.add(key)
  try {
    const data = await api.getFileDiff(subSessionId, filePath)
    fileDiffs[key] = renderDiff(data, filePath)
  } catch {
    fileDiffs[key] = '<div class="diff-error">加载失败</div>'
  } finally {
    loadingDiffs.delete(key)
  }
}

watch(() => store.loadedSessionId, () => {
  expandedFiles.clear()
  expandedSubSessions.clear()
  loadingDiffs.clear()
  Object.keys(fileDiffs).forEach(k => delete fileDiffs[k])
  expandedGitFiles.clear()
  loadingGitFiles.clear()
  Object.keys(gitFileDiffs).forEach(k => delete gitFileDiffs[k])
  Object.keys(gitRawFileDiffs).forEach(k => delete gitRawFileDiffs[k])
})

watch(() => store.isDrawerOpen, async (open) => {
  if (open) {
    const sessionId = sessionsStore.currentSessionId
    if (sessionId && sessionId !== store.loadedSessionId) {
      await store.fetchFileChanges(sessionId)
    }
  }
})
</script>

<style scoped>
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.drawer-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.drawer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--el-text-color-secondary);
}

.file-list {
  display: flex;
  flex-direction: column;
}

.file-item {
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.file-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s;
  user-select: none;
}

.file-header:hover {
  background: var(--el-fill-color-light);
}

.expand-icon {
  font-size: 10px;
  width: 14px;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.change-tag {
  font-size: 11px;
  font-weight: 700;
  width: 18px;
  text-align: center;
  flex-shrink: 0;
  border-radius: 3px;
  padding: 1px 0;
}

.change-tag--edit,
.change-tag--append {
  color: #f59e0b;
}

.change-tag--create {
  color: #10b981;
}

.change-tag--delete {
  color: #ef4444;
}

.change-tag--move {
  color: #6366f1;
}

.file-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-dir {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

.copy-path-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  border-radius: 4px;
  flex-shrink: 0;
  opacity: 0.5;
  transition: opacity 0.15s, background 0.15s;
}

.file-header:hover .copy-path-btn {
  display: inline-flex;
}

.copy-path-btn:hover {
  opacity: 1;
  background: var(--el-fill-color);
}

.edit-count {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color);
  padding: 1px 6px;
  border-radius: 10px;
  flex-shrink: 0;
}

.file-diff-container {
  padding: 0 12px 12px;
}

.diff-loading {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.diff-content {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
}

.diff-content :deep(.d2h-wrapper) {
  font-size: 12px;
}

.diff-content :deep(.d2h-file-header) {
  display: none;
}

.diff-content :deep(.d2h-code-linenumber) {
  position: static !important;
  display: table-cell !important;
  width: 40px !important;
  min-width: 40px !important;
  padding: 0 4px !important;
  box-sizing: border-box !important;
}

.diff-content :deep(.d2h-code-line) {
  padding: 0 8px !important;
  width: auto !important;
}

.diff-content :deep(.d2h-code-line-ctn) {
  white-space: pre-wrap !important;
  word-break: break-all !important;
}

.diff-content :deep(.d2h-code-side-linenumber) {
  position: static !important;
  display: table-cell !important;
  width: 40px !important;
  min-width: 40px !important;
  padding: 0 4px !important;
  box-sizing: border-box !important;
}

.diff-content :deep(.d2h-code-side-line) {
  padding: 0 8px !important;
  width: auto !important;
}

.diff-content :deep(.d2h-code-side-line-ctn) {
  white-space: pre-wrap !important;
  word-break: break-all !important;
}

.diff-empty {
  padding: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  text-align: center;
}

.diff-error {
  padding: 12px;
  color: var(--el-color-danger);
  font-size: 13px;
}

.diff-fallback {
  padding: 12px;
  font-size: 12px;
  font-family: monospace;
  overflow-x: auto;
  white-space: pre;
  background: var(--el-fill-color-lighter);
  border-radius: 6px;
}

.git-diff-file-list {
  max-height: 70vh;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
}

.git-diff-file-item {
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.git-diff-file-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s;
  user-select: none;
}

.git-diff-file-header:hover {
  background: var(--el-fill-color-light);
}

.git-diff-file-list .file-diff-container {
  padding-bottom: 12px;
}

.git-diff-file-list .diff-content {
  max-height: 60vh;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
}

.git-diff-file-list .diff-content :deep(.d2h-wrapper) {
  font-size: 12px;
}

.git-diff-file-list .diff-content :deep(.d2h-file-header) {
  display: none;
}

.git-diff-file-list .diff-content :deep(.d2h-diff-table) {
  table-layout: fixed;
  width: 100%;
}

.git-diff-file-list .diff-content :deep(.d2h-code-linenumber) {
  position: static !important;
  display: table-cell !important;
  width: 40px !important;
  min-width: 40px !important;
  padding: 0 4px !important;
  box-sizing: border-box !important;
}

.git-diff-file-list .diff-content :deep(.d2h-code-line) {
  padding: 0 8px !important;
  width: auto !important;
}

.git-diff-file-list .diff-content :deep(.d2h-code-line-ctn) {
  white-space: pre-wrap !important;
  word-break: break-all !important;
}

.git-diff-file-list .diff-content :deep(.d2h-code-side-linenumber) {
  position: static !important;
  display: table-cell !important;
  width: 40px !important;
  min-width: 40px !important;
  padding: 0 4px !important;
  box-sizing: border-box !important;
}

.git-diff-file-list .diff-content :deep(.d2h-code-side-line) {
  padding: 0 8px !important;
  width: auto !important;
}

.git-diff-file-list .diff-content :deep(.d2h-code-side-line-ctn) {
  white-space: pre-wrap !important;
  word-break: break-all !important;
}

.git-diff-dialog :deep(.el-dialog__body) {
  padding-top: 0;
}


.sub-agent-section {
  border-top: 2px solid var(--el-border-color);
  margin-top: 4px;
}

.sub-agent-section-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--el-text-color-secondary);
  padding: 10px 12px 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.sub-agent-item {
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.sub-agent-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s;
  user-select: none;
}

.sub-agent-header:hover {
  background: var(--el-fill-color-light);
}

.sub-agent-icon {
  font-size: 14px;
}

.sub-agent-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.sub-agent-badge {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color);
  padding: 1px 8px;
  border-radius: 10px;
  margin-left: auto;
}

.sub-agent-files {
  padding-left: 16px;
}

.sub-file-item {
  border-bottom: none;
  border-top: 1px solid var(--el-border-color-extra-light);
}
</style>

<style>
/* diff2html dark mode — must be unscoped to override global diff2html.min.css */
html.dark .d2h-wrapper {
  background: #1e1e2e !important;
  color: #cdd6f4 !important;
}

html.dark .d2h-file-wrapper {
  border-color: #45475a !important;
}

html.dark .d2h-file-header {
  background: #313244 !important;
  border-color: #45475a !important;
  color: #cdd6f4 !important;
}

html.dark .d2h-diff-table {
  color: #cdd6f4 !important;
  border-collapse: collapse !important;
}

html.dark .d2h-diff-tbody > tr > td {
  color: #cdd6f4 !important;
  background: #1e1e2e !important;
}

html.dark .d2h-code-linenumber,
html.dark .d2h-code-side-linenumber {
  background: #1e1e2e !important;
  color: #6c7086 !important;
  border-color: #313244 !important;
}

html.dark .d2h-code-line,
html.dark .d2h-code-side-line {
  background: #1e1e2e !important;
  color: #cdd6f4 !important;
}

html.dark .d2h-code-line-prefix,
html.dark .d2h-code-line-ctn,
html.dark .d2h-code-side-line-prefix,
html.dark .d2h-code-side-line-ctn {
  color: #cdd6f4 !important;
  background: transparent !important;
}

html.dark td.d2h-ins,
html.dark .d2h-ins.d2h-change {
  background: rgba(166, 227, 161, 0.12) !important;
  border-color: rgba(166, 227, 161, 0.2) !important;
}

html.dark .d2h-ins .d2h-code-line-ctn {
  color: #a6e3a1 !important;
}

html.dark .d2h-ins.d2h-code-linenumber,
html.dark .d2h-ins.d2h-code-side-linenumber {
  background: rgba(166, 227, 161, 0.08) !important;
  color: #a6e3a1 !important;
  border-color: rgba(166, 227, 161, 0.15) !important;
}

html.dark .d2h-code-line-ctn ins,
html.dark ins.d2h-change {
  background: rgba(166, 227, 161, 0.28) !important;
  color: #a6e3a1 !important;
  text-decoration: none !important;
}

html.dark td.d2h-del,
html.dark .d2h-del.d2h-change {
  background: rgba(243, 139, 168, 0.12) !important;
  border-color: rgba(243, 139, 168, 0.2) !important;
}

html.dark .d2h-del .d2h-code-line-ctn {
  color: #f38ba8 !important;
}

html.dark .d2h-del.d2h-code-linenumber,
html.dark .d2h-del.d2h-code-side-linenumber {
  background: rgba(243, 139, 168, 0.08) !important;
  color: #f38ba8 !important;
  border-color: rgba(243, 139, 168, 0.15) !important;
}

html.dark .d2h-code-line-ctn del,
html.dark del.d2h-change {
  background: rgba(243, 139, 168, 0.28) !important;
  color: #f38ba8 !important;
  text-decoration: line-through !important;
}

html.dark .d2h-info {
  background: #313244 !important;
  color: #89b4fa !important;
  border-color: #45475a !important;
}

html.dark .d2h-file-list-wrapper {
  background: #1e1e2e !important;
  border-color: #45475a !important;
}

html.dark .d2h-file-list-line a {
  color: #89b4fa !important;
}

html.dark .d2h-diff-table {
  border-collapse: collapse !important;
}

html.dark .d2h-diff-tbody tr {
  border-color: #313244 !important;
}

html.dark .d2h-emptyplaceholder {
  background: #181825 !important;
  border-color: #313244 !important;
}
</style>
