<template>
  <div class="tool-group-panel">
    <div v-for="group in groups" :key="group.id" class="group-item" :class="{ 'not-allowed': !(group as any).allowed && (group as any).allowed !== undefined }">
      <div class="group-header">
        <div class="group-title">
          <span class="group-name">{{ group.id }}{{ group.description ? `（${group.description}）` : '' }}</span>
          <span class="group-count">{{ group.tools.length }}</span>
        </div>
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
  padding: 11px;
  background: var(--el-fill-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.group-item:hover {
  border-color: var(--el-color-primary-light-7);
  background: color-mix(in srgb, var(--el-fill-color) 92%, var(--el-color-primary) 3%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  gap: 8px;
}

.group-title {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 6px;
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
  font-weight: 650;
  color: var(--el-text-color-primary);
}

.group-count {
  min-width: 18px;
  padding: 1px 5px;
  border-radius: 999px;
  background: var(--el-fill-color-dark);
  color: var(--el-text-color-secondary);
  font-size: 10px;
  font-weight: 700;
  line-height: 1.4;
  text-align: center;
}

.group-tools {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.group-tools :deep(.el-tag) {
  height: 21px;
  padding: 0 7px;
  border-color: color-mix(in srgb, var(--el-color-primary) 22%, var(--el-border-color));
  border-radius: 5px;
  background: color-mix(in srgb, var(--el-color-primary) 7%, var(--el-fill-color));
  color: var(--el-color-primary);
  font-family: Consolas, 'Courier New', monospace;
  font-size: 10px;
  line-height: 19px;
}

.group-tools :deep(.tool-tag-disabled) {
  border-color: var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
  color: var(--el-text-color-placeholder);
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
