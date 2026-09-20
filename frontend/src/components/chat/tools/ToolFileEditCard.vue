<template>
  <ToolFileCard :tool-call="toolCall" :collapsed="collapsed" :round="round" variant="edit" />
</template>

<script setup lang="ts">
import type { ToolCall } from '@/stores/chat'
import ToolFileCard from './ToolFileCard.vue'

defineProps<{
  toolCall: ToolCall
  collapsed?: boolean
  round?: number | null
}>()
</script>
