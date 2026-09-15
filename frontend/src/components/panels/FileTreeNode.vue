<template>
  <div class="tree-node">
    <div
      class="tree-row"
      :class="{ 'is-dir': isDir, 'is-open': isDir && isOpen, 'is-active': isActive }"
      :style="{ paddingLeft: 6 + depth * 14 + 'px' }"
      role="button"
      tabindex="0"
      :title="entry.path"
      @click="handleClick"
      @keydown.enter="handleClick"
      @keydown.space.prevent="handleClick"
    >
      <span class="tree-caret" :class="{ 'is-open': isOpen }">
        <svg v-if="isDir" viewBox="0 0 12 12" aria-hidden="true">
          <path
            d="M4.5 2.5 8 6l-3.5 3.5"
            fill="none"
            stroke="currentColor"
            stroke-width="1.6"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </span>

      <FileTypeIcon
        :name="isDir ? '' : entry.name"
        :is-directory="isDir"
        :compact="true"
      />

      <span class="tree-name">{{ entry.name }}</span>

      <span v-if="isDir && dirCount !== null" class="tree-count">{{ dirCount }}</span>
    </div>

    <template v-if="isDir && isOpen">
      <div v-if="loading" class="tree-hint" :style="{ paddingLeft: 6 + (depth + 1) * 14 + 18 + 'px' }">
        <el-icon class="is-loading"><Loading /></el-icon>
        加载中
      </div>
      <div
        v-else-if="loadError"
        class="tree-hint tree-hint-error"
        :style="{ paddingLeft: 6 + (depth + 1) * 14 + 18 + 'px' }"
      >
        {{ loadError }}
      </div>
      <template v-else>
        <FileTreeNode
          v-for="child in children"
          :key="child.path"
          :entry="child"
          :depth="depth + 1"
        />
        <div
          v-if="children.length === 0"
          class="tree-hint"
          :style="{ paddingLeft: 6 + (depth + 1) * 14 + 18 + 'px' }"
        >
          空目录
        </div>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, ref, type Ref } from 'vue'
import {
  Coin,
  Document,
  Folder,
  FolderOpened,
  Loading,
  Lock,
  Memo,
  Picture,
  Setting,
  Tickets,
} from '@element-plus/icons-vue'
import { useAgentsStore } from '@/stores/agents'
import { useProjectTreeStore } from '@/stores/project-tree'
import type { ProjectTreeEntry } from '@/stores/project-tree'

defineOptions({ name: 'FileTreeNode' })

const props = defineProps<{
  entry: ProjectTreeEntry
  depth: number
}>()

const store = useProjectTreeStore()
const agentsStore = useAgentsStore()

// 由 FileTreePanel 提供：点击文件时打开预览弹层
const openFile = inject<(path: string) => void>('openFile', () => {})
// 由 FileTreePanel 提供：当前预览中的文件路径
const activeFile = inject<Ref<string>>('activeFile', ref(''))

const isDir = computed(() => props.entry.type === 'dir')
const isOpen = ref(false)
const loadError = ref('')

const loading = computed(() => store.isLoading(props.entry.path))
const children = computed(() => (isOpen.value ? store.entriesOf(props.entry.path) : []))
const dirCount = computed(() => (isDir.value && store.isLoaded(props.entry.path) ? children.value.length : null))
const isActive = computed(() => !isDir.value && activeFile.value === props.entry.path)

async function handleClick() {
  if (!isDir.value) {
    activeFile.value = props.entry.path
    openFile(props.entry.path)
    return
  }

  if (isOpen.value) {
    isOpen.value = false
    return
  }

  isOpen.value = true
  if (store.isLoaded(props.entry.path)) return

  loadError.value = ''
  const result = await store.load(agentsStore.currentAgentId, props.entry.path)
  if (result.error) loadError.value = result.error
}
</script>

<style scoped>
.tree-node {
  user-select: none;
}

.tree-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 26px;
  padding-right: 6px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.14s ease;
}

.tree-row:hover {
  background: var(--el-fill-color-light);
}

.tree-row.is-active {
  background: color-mix(in srgb, var(--el-color-primary) 13%, transparent);
  box-shadow: inset 2px 0 0 var(--el-color-primary);
}

.tree-caret {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  color: var(--el-text-color-placeholder);
  transition: transform 0.16s ease, color 0.16s ease;
}

.tree-caret.is-open {
  transform: rotate(90deg);
  color: var(--el-text-color-secondary);
}

.tree-caret svg {
  width: 12px;
  height: 12px;
}

.tree-row:hover .tree-caret {
  color: var(--el-text-color-secondary);
}

.tree-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: var(--el-text-color-regular);
  font-size: 12.5px;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-row.is-dir .tree-name {
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.tree-count {
  flex-shrink: 0;
  min-width: 16px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--el-fill-color);
  color: var(--el-text-color-secondary);
  font-size: 10px;
  line-height: 15px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.tree-hint {
  display: flex;
  align-items: center;
  gap: 5px;
  padding-top: 3px;
  padding-bottom: 3px;
  color: var(--el-text-color-placeholder);
  font-size: 11px;
}

.tree-hint-error {
  color: var(--el-color-danger);
  word-break: break-all;
}
</style>
