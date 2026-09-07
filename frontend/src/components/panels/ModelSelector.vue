<template>
  <div class="model-selector">
    <el-select
      :model-value="currentModel"
      placeholder="选择模型"
      size="small"
      filterable
      style="width: 100%"
      @change="$emit('change', $event)"
    >
      <el-option
        v-for="model in models"
        :key="model.model_id"
        :label="model.model_id"
        :value="model.model_id"
      >
        <span>{{ model.model_id }}</span>
        <span style="float:right; color:var(--el-text-color-secondary); font-size:11px">
          {{ model.provider }}
        </span>
      </el-option>
    </el-select>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  models: { model_id: string; provider: string; context_limit: number }[]
  currentModel: string
}>()
defineEmits<{ change: [modelId: string] }>()
</script>

<style scoped>
.model-selector {
  margin-bottom: 8px;
}
</style>
