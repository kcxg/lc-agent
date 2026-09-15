<template>
  <span
    v-if="isDirectory"
    class="ft-badge ft-badge--dir"
    :style="dirStyle"
    aria-hidden="true"
  >
    <svg viewBox="0 0 16 16">
      <path
        d="M1.8 4.2c0-.5.4-.9.9-.9h3.1l1.3 1.5h6.2c.5 0 .9.4.9.9v6.1c0 .5-.4.9-.9.9H2.7a.9.9 0 0 1-.9-.9z"
        fill="currentColor"
      />
    </svg>
  </span>

  <span
    v-else
    class="ft-badge"
    :class="{ 'is-compact': compact }"
    :style="fileStyle"
    aria-hidden="true"
  >
    {{ meta.label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { fileTypeMeta } from '@/utils/file-type'

const props = withDefaults(defineProps<{
  /** 文件名或路径，含后缀 */
  name: string
  /** 目录时显示文件夹图标 */
  isDirectory?: boolean
  /** 紧凑模式：字号与宽度更小，用于密集列表 */
  compact?: boolean
}>(), {
  isDirectory: false,
  compact: false,
})

const meta = computed(() => fileTypeMeta(props.name))

const dirStyle = computed(() => ({ color: '#d9a441' }))

const fileStyle = computed(() => ({
  color: meta.value.color,
  background: `color-mix(in srgb, ${meta.value.color} 16%, transparent)`,
}))
</script>

<style scoped>
.ft-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 26px;
  height: 18px;
  border-radius: 4px;
  font-family: 'Cascadia Code', 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: -0.2px;
  line-height: 1;
  text-align: center;
}

.ft-badge.is-compact {
  width: 22px;
  height: 16px;
  font-size: 8px;
}

.ft-badge--dir {
  background: transparent;
}

.ft-badge--dir svg {
  width: 15px;
  height: 15px;
}
</style>
