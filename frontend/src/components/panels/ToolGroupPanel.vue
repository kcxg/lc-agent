<template>
  <div class="tool-group-panel">
    <div v-for="group in groups" :key="group.id" class="group-item" :class="{ 'not-allowed': !(group as any).allowed && (group as any).allowed !== undefined }">
      <div class="group-header">
        <span class="group-name">{{ group.description || group.id }}</span>
        <div class="group-actions">
          <button class="detail-btn" type="button" @click="$emit('detail', group)">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            详情
          </button>
          <el-switch
            :model-value="group.enabled"
            :disabled="(group as any).allowed === false"
            size="small"
            @change="$emit('toggle', group.id)"
          />
        </div>
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
defineEmits<{ toggle: [groupId: string]; detail: [group: ToolGroup] }>()
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
  gap: 8px;
}

.group-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.detail-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 10px;
  background: color-mix(in srgb, var(--el-color-primary) 8%, transparent);
  font-size: 11px;
  color: var(--el-color-primary);
  cursor: pointer;
  line-height: 1;
  flex-shrink: 0;
  transition: all 0.18s ease;
  white-space: nowrap;
}

.detail-btn:hover {
  background: color-mix(in srgb, var(--el-color-primary) 15%, transparent);
  border-color: var(--el-color-primary-light-3);
  box-shadow: 0 1px 4px color-mix(in srgb, var(--el-color-primary) 12%, transparent);
}

.detail-btn:active {
  transform: scale(0.95);
  background: color-mix(in srgb, var(--el-color-primary) 20%, transparent);
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
