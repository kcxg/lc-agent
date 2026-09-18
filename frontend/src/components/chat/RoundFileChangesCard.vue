<template>
  <div v-if="group && (group.files.length > 0 || group.sub_sessions.length > 0)" class="round-file-changes-card">
    <div class="rfc-header">
      <span class="rfc-icon" aria-hidden="true">📄</span>
      <span class="rfc-title">{{ group.files.length }} 个文件已更改</span>
      <span v-if="totalAdditions" class="rfc-additions">+{{ totalAdditions }}</span>
      <span v-if="totalDeletions" class="rfc-deletions">-{{ totalDeletions }}</span>
      <button
        class="rfc-open-btn"
        type="button"
        title="查看本轮文件变更"
        @click.stop="openRoundDrawer"
      >
        <el-icon><TopRight /></el-icon>
      </button>
    </div>
    <div class="rfc-file-list">
      <div
        v-for="file in group.files"
        :key="file.file_path"
        class="rfc-file-row"
        role="button"
        tabindex="0"
        :title="file.file_path"
        @click.stop="openInChanges(file)"
        @keydown.enter.stop="openInChanges(file)"
        @keydown.space.prevent.stop="openInChanges(file)"
      >
        <span :class="['rfc-tag', `rfc-tag--${file.change_type}`]">{{ tagLabel(file.change_type) }}</span>
        <span class="rfc-file-name">{{ fileName(file.file_path) }}</span>
        <span class="rfc-file-dir">{{ fileDir(file.file_path) }}</span>
        <span class="rfc-line-stats">
          <span v-if="file.additions" class="rfc-additions">+{{ file.additions }}</span>
          <span v-if="file.deletions" class="rfc-deletions">-{{ file.deletions }}</span>
        </span>
        <span class="rfc-actions">
          <button
            type="button"
            class="rfc-jump-btn rfc-jump-changes"
            title="跳到变更面板看 diff"
            @click.stop="openInChanges(file)"
          ><svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2 3.2h8M2 6h5.2M2 8.8h8" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" /></svg>变更</button>
          <button
            v-if="canOpenInFile(file)"
            type="button"
            class="rfc-jump-btn rfc-jump-file"
            title="跳到文件面板看全文"
            @click.stop="openInFile(file)"
          ><svg viewBox="0 0 12 12" aria-hidden="true"><path d="M3.2 1.5h3.9L9.8 4.2v6.3H3.2z" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round" /><path d="M7 1.5v2.8h2.8" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round" /></svg>文件</button>
        </span>
      </div>
      <button
        v-for="sub in group.sub_sessions"
        :key="sub.sub_session_id"
        class="rfc-file-row rfc-sub-row"
        type="button"
        @click.stop="openRoundDrawer"
      >
        <span class="rfc-tag rfc-tag--sub">🤖</span>
        <span class="rfc-file-name">子 Agent：{{ sub.title }}</span>
        <span class="rfc-file-dir">{{ sub.file_count }} 个文件</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { TopRight } from '@element-plus/icons-vue'
import { useFileChangesStore, type FileChangeItem } from '@/stores/file-changes'
import { useOpenedFilesStore } from '@/stores/opened-files'
import { useUiStore } from '@/stores/ui'

const props = defineProps<{ round: number }>()

const store = useFileChangesStore()
const uiStore = useUiStore()

const group = computed(() => store.rounds.find(r => r.round_number === props.round) || null)

const totalAdditions = computed(() =>
  (group.value?.files || []).reduce((sum, f) => sum + (f.additions || 0), 0),
)
const totalDeletions = computed(() =>
  (group.value?.files || []).reduce((sum, f) => sum + (f.deletions || 0), 0),
)

function tagLabel(type: string): string {
  switch (type) {
    case 'create': return '新'
    case 'delete': return '删'
    case 'move': return '移'
    case 'append': return '追'
    default: return '改'
  }
}

function fileName(path: string): string {
  const idx = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'))
  return idx >= 0 ? path.slice(idx + 1) : path
}

function fileDir(path: string): string {
  const idx = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'))
  return idx >= 0 ? path.slice(0, idx) : ''
}

function openRoundDrawer() {
  uiStore.requestTab('changes', { round: props.round })
}

/** 跳到变更面板并定位到该文件看 diff（行点击默认也是这个动作） */
function openInChanges(file: FileChangeItem) {
  uiStore.requestTab('changes', { round: props.round, filePath: file.file_path })
}

/** 移动过的文件原路径已不存在，打开它的新位置 */
function editorPathOf(file: FileChangeItem): string {
  if (file.change_type === 'move' && file.move_destination) return file.move_destination
  return file.file_path
}

/** 删除的文件磁盘上已经没有了，不给文件按钮 */
function canOpenInFile(file: FileChangeItem): boolean {
  return file.change_type !== 'delete'
}

/** 跳到右侧文件面板看全文，可编辑 */
function openInFile(file: FileChangeItem) {
  useOpenedFilesStore().open(editorPathOf(file))
}
</script>

<style scoped>
.round-file-changes-card {
  margin-top: 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-light);
  overflow: hidden;
  width: 100%;
}
.rfc-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 13px;
}
.rfc-icon {
  font-size: 14px;
}
.rfc-title {
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.rfc-additions {
  color: var(--el-color-success);
  font-family: monospace;
  font-size: 12px;
}
.rfc-deletions {
  color: var(--el-color-danger);
  font-family: monospace;
  font-size: 12px;
}
.rfc-open-btn {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  border: none;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
}
.rfc-open-btn:hover {
  color: var(--el-color-primary);
  background: var(--el-fill-color);
}
.rfc-file-list {
  display: flex;
  flex-direction: column;
}
.rfc-file-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 5px 12px;
  border: none;
  background: transparent;
  text-align: left;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
  color: var(--el-text-color-regular);
  box-sizing: border-box;
}
.rfc-file-row:hover {
  background: var(--el-fill-color);
}
.rfc-file-row:focus-visible {
  outline: 2px solid var(--el-color-primary);
  outline-offset: -2px;
}
.rfc-actions {
  flex: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: 4px;
}
.rfc-jump-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 9px 2px 7px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  font-size: 11px;
  line-height: 16px;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  white-space: nowrap;
  transition: transform 0.12s ease, box-shadow 0.12s ease, filter 0.12s ease;
}
.rfc-jump-btn svg {
  width: 11px;
  height: 11px;
  flex: none;
}
.rfc-jump-changes {
  background: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%);
  box-shadow: 0 1px 8px rgba(217, 70, 239, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
.rfc-jump-changes:hover {
  filter: brightness(1.12);
  transform: translateY(-1px);
  box-shadow: 0 3px 12px rgba(217, 70, 239, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
.rfc-jump-file {
  background: linear-gradient(135deg, #10b981 0%, #0ea5e9 100%);
  box-shadow: 0 1px 8px rgba(14, 165, 233, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
.rfc-jump-file:hover {
  filter: brightness(1.12);
  transform: translateY(-1px);
  box-shadow: 0 3px 12px rgba(14, 165, 233, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
.rfc-jump-btn:active {
  transform: translateY(0);
}
.rfc-file-row + .rfc-file-row {
  border-top: 1px solid var(--el-border-color-extra-light);
}
.rfc-tag {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 3px;
  border-radius: 4px;
  font-size: 11px;
  color: #fff;
  background: var(--el-color-info);
}
.rfc-tag--create { background: var(--el-color-success); }
.rfc-tag--delete { background: var(--el-color-danger); }
.rfc-tag--append { background: var(--el-color-primary); }
.rfc-tag--move { background: var(--el-color-warning); }
.rfc-tag--sub { background: transparent; }
.rfc-file-name {
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}
.rfc-file-dir {
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  direction: ltr;
}
.rfc-line-stats {
  margin-left: auto;
  flex: none;
  display: inline-flex;
  gap: 6px;
}
.rfc-sub-row .rfc-file-name {
  font-weight: 500;
}
</style>
