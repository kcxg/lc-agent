<template>
  <FileEditCard v-if="kind === 'edit'" :tool-call="toolCall" :collapsed="collapsed" :round="round" />
  <FileWriteCard v-else-if="kind === 'write'" :tool-call="toolCall" :collapsed="collapsed" :round="round" />
  <TerminalCard v-else-if="kind === 'terminal'" :tool-call="toolCall" :collapsed="collapsed" />
  <GenericToolCard v-else :tool-call="toolCall" :collapsed="collapsed" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ToolCall } from '@/stores/chat'
import { resolveToolCardKind } from './toolCardRouter'
import FileEditCard from './ToolFileEditCard.vue'
import FileWriteCard from './ToolFileWriteCard.vue'
import TerminalCard from './ToolTerminalCard.vue'
import GenericToolCard from './ToolGenericCard.vue'

const props = defineProps<{
  toolCall: ToolCall
  collapsed?: boolean
  /** 该工具调用所在的对话轮次，透传给文件卡片做变更面板定位 */
  round?: number | null
}>()

const kind = computed(() => {
  const base = resolveToolCardKind(props.toolCall.name || '')
  // P0 只拆 edit / write / terminal，其余（read/directory/search/info/fileOp）暂时走通用卡
  if (base === 'edit' || base === 'write' || base === 'terminal') return base
  return 'generic'
})
</script>
