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
      <button
        v-for="file in group.files"
        :key="file.file_path"
        class="rfc-file-row"
        type="button"
        :title="file.file_path"
        @click.stop="openFile(file)"
      >
        <span :class="['rfc-tag', `rfc-tag--${file.change_type}`]">{{ tagLabel(file.change_type) }}</span>
        <span class="rfc-file-name">{{ fileName(file.file_path) }}</span>
        <span class="rfc-file-dir">{{ fileDir(file.file_path) }}</span>
        <span class="rfc-line-stats">
          <span v-if="file.additions" class="rfc-additions">+{{ file.additions }}</span>
          <span v-if="file.deletions" class="rfc-deletions">-{{ file.deletions }}</span>
        </span>
      </button>
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

const props = defineProps<{ round: number }>()

const store = useFileChangesStore()

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
  store.selectedRound = props.round
  store.openDrawer()
}

function openFile(file: FileChangeItem) {
  store.selectedRound = props.round
  store.pendingOpenFile = file.file_path
  store.openDrawer()
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
  font-size: 12px;
  cursor: pointer;
  color: var(--el-text-color-regular);
}
.rfc-file-row:hover {
  background: var(--el-fill-color);
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
