<template>
  <div class="tool-group-panel">
    <div v-for="group in groups" :key="group.id" class="group-item" :class="{ 'not-allowed': !(group as any).allowed && (group as any).allowed !== undefined }">
      <div class="group-header">
        <span class="group-name">{{ group.description || group.id }}</span>
        <el-switch
          :model-value="group.enabled"
          :disabled="(group as any).allowed === false"
          size="small"
          @change="$emit('toggle', group.id)"
        />
      </div>
      <div class="group-tools">
        <el-tag
          v-for="tool in group.tools"
          :key="tool.name"
          size="small"
          :class="group.enabled ? 'tool-tag-enabled' : 'tool-tag-disabled'"
        >
          {{ tool.name.split('__').pop() }}
        </el-tag>
      </div>
    </div>
    <p v-if="!groups.length" class="empty">暂无工具</p>
  </div>
</template>

<script setup lang="ts">
import type { ToolGroup } from '@/stores/tools'

defineProps<{ groups: ToolGroup[] }>()
defineEmits<{ toggle: [groupId: string] }>()
</script>

<style scoped>
.group-item {
  margin-bottom: 8px;
  padding: 10px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.group-item:hover {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-fill-color);
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.group-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.group-tools {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.empty {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  opacity: 0.6;
}

.not-allowed {
  opacity: 0.4;
  border-style: dashed;
  border-color: var(--el-border-color) !important;
}
</style>
