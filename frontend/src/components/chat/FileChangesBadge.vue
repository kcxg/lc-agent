<template>
  <el-tooltip
    v-if="store.hasChanges"
    :content="tooltipContent"
    placement="bottom"
    raw-content
    :show-after="300"
  >
    <button
      class="file-changes-badge"
      :aria-label="`查看 ${store.fileCount} 个文件变更`"
      @click="store.openDrawer()"
    >
      <span class="badge-icon">👁️</span>
      <span class="badge-count">{{ store.fileCount }}</span>
    </button>
  </el-tooltip>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useFileChangesStore } from '@/stores/file-changes'

const store = useFileChangesStore()

const changeTypeLabel: Record<string, string> = {
  edit: 'M',
  create: 'A',
  delete: 'D',
  move: 'R',
  append: 'M',
}

const tooltipContent = computed(() => {
  if (!store.hasChanges) return ''
  const lines = store.files.slice(0, 10).map(f => {
    const label = changeTypeLabel[f.change_type] || '?'
    const name = f.file_path.split(/[\\/]/).pop() || f.file_path
    return `<div style="display:flex;gap:6px;align-items:center;padding:1px 0">
      <span style="font-weight:700;color:${label === 'A' ? '#10b981' : label === 'D' ? '#ef4444' : '#f59e0b'};width:14px">${label}</span>
      <span style="opacity:0.85">${name}</span>
    </div>`
  })
  if (store.files.length > 10) {
    lines.push(`<div style="opacity:0.6;padding-top:2px">...and ${store.files.length - 10} more</div>`)
  }
  return `<div style="font-size:12px;line-height:1.6">${lines.join('')}</div>`
})
</script>

<style scoped>
.file-changes-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--el-border-color);
  background: var(--el-fill-color-light);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  transition: all 0.2s ease;
  white-space: nowrap;
  height: 28px;
}

.file-changes-badge:hover {
  border-color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary) 8%, var(--el-fill-color-light));
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.badge-icon {
  font-size: 13px;
}

.badge-count {
  color: var(--el-color-primary);
  font-weight: 700;
}
</style>
