<template>
  <header class="app-header">
    <div class="header-left">
      <el-button
        class="mobile-sidebar-btn"
        :icon="Menu"
        circle
        size="small"
        aria-label="打开会话列表"
        @click="$emit('openMobileSidebar')"
      />
      <span class="logo">⚡ {{ appName }}</span>
    </div>
    <div class="header-center">
      <el-select
        class="agent-select"
        :model-value="agentsStore.currentAgentId"
        size="small"
        @change="$emit('changeAgent', $event)"
      >
        <el-option
          v-for="agent in agentsStore.agents"
          :key="agent.id"
          :label="agent.name"
          :value="agent.id"
        >
          <div class="agent-option">
            <span class="agent-option-name">{{ agent.name }}</span>
            <span v-if="agent.source === 'builtin'" class="source-badge badge-builtin">内置</span>
            <span v-else-if="agent.source === 'code'" class="source-badge badge-code">代码</span>
            <span v-else class="source-badge badge-user">自建</span>
          </div>
        </el-option>
      </el-select>
      <div class="header-actions desktop-only">
        <button class="header-btn btn-edit" @click="$emit('editAgent')" :disabled="agentsStore.isBuiltin">编辑</button>
        <button class="header-btn btn-new-agent" @click="$emit('newAgent')">+ 新Agent</button>
        <button class="header-btn btn-new-chat" @click="$emit('newChat')">+ 新对话</button>
        <CopyRoundsButton v-if="hasMessages" :messages="chatStore.messages" :model-name="sessionModel" />
      </div>
    </div>
    <div class="header-right">
      <button class="header-btn mobile-new-chat-btn" @click="$emit('newChat')">新对话</button>
      <span class="mobile-only">
        <CopyRoundsButton v-if="hasMessages" :messages="chatStore.messages" :model-name="sessionModel" />
      </span>
      <el-button
        class="mobile-tools-btn"
        :icon="Setting"
        circle
        size="small"
        aria-label="打开工具和状态面板"
        @click="$emit('openMobileTools')"
      />
      <span class="model-badge">{{ modelName }}</span>
      <span class="status-dot" :class="connected ? 'connected' : 'disconnected'" />
      <span class="status-text" :title="connected ? 'WebSocket 已连接' : 'WebSocket 未连接'">
        {{ connected ? '已连接' : '未连接' }}
      </span>
      <el-button :icon="RefreshRight" circle size="small" title="刷新页面" @click="reloadPage" />
      <el-button :icon="isDark ? Sunny : Moon" circle size="small" @click="toggleDark()" />
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAgentsStore } from '@/stores/agents'
import { useChatStore } from '@/stores/chat'
import { useToolsStore } from '@/stores/tools'
import { useTheme } from '@/composables/useTheme'
import { Sunny, Moon, Menu, Setting, RefreshRight } from '@element-plus/icons-vue'
import CopyRoundsButton from '@/components/chat/CopyRoundsButton.vue'

const agentsStore = useAgentsStore()
const chatStore = useChatStore()
const toolsStore = useToolsStore()
const { isDark, toggleDark } = useTheme()

function reloadPage() {
  window.location.reload()
}

const hasMessages = computed(() => chatStore.messages.length > 0)
const sessionModel = computed(() => {
  const model = toolsStore.currentModel || agentsStore.currentAgent?.default_model || ''
  if (!model) return ''
  const parts = model.split('/')
  return parts[parts.length - 1] || model
})

defineProps<{
  appName: string
  modelName: string
  connected: boolean
}>()

defineEmits<{
  editAgent: []
  newAgent: []
  newChat: []
  changeAgent: [id: string]
  openMobileSidebar: []
  openMobileTools: []
}>()
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  height: 52px;
  flex-shrink: 0;
  z-index: 100;
}

.logo {
  font-size: 16px;
  font-weight: 700;
  color: var(--el-color-primary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-center {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mobile-sidebar-btn,
.mobile-tools-btn,
.mobile-new-chat-btn,
.mobile-only {
  display: none;
}

.desktop-only {
  display: inline-flex;
}

.header-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex-wrap: nowrap;
}

.agent-select {
  width: 280px;
}

.agent-select :deep(.el-select__wrapper) {
  min-width: 0;
  min-height: 38px;
  padding: 0 36px 0 14px;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 24%, var(--el-border-color));
  background: linear-gradient(180deg, color-mix(in srgb, var(--el-bg-color-overlay) 96%, white 4%), color-mix(in srgb, var(--el-fill-color-light) 92%, var(--el-bg-color-overlay)));
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, transform 0.18s ease;
}

.agent-select :deep(.el-select__wrapper:hover) {
  border-color: color-mix(in srgb, var(--el-color-primary) 38%, var(--el-border-color));
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.1);
}

.agent-select :deep(.el-select__wrapper.is-focused) {
  border-color: color-mix(in srgb, var(--el-color-primary) 58%, var(--el-border-color));
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--el-color-primary) 14%, transparent), 0 12px 28px rgba(15, 23, 42, 0.12);
}

.agent-select :deep(.el-select__selected-item) {
  min-width: 0;
  display: block;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.agent-select :deep(.el-select__caret) {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

:global(html.dark) .agent-select :deep(.el-select__wrapper) {
  border-color: rgba(148, 163, 184, 0.22);
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.96), rgba(15, 23, 42, 0.94));
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.34);
}

:global(html.dark) .agent-select :deep(.el-select__wrapper:hover) {
  border-color: color-mix(in srgb, var(--el-color-primary) 50%, rgba(148, 163, 184, 0.22));
}

:global(html.dark) .agent-select :deep(.el-select__wrapper.is-focused) {
  border-color: color-mix(in srgb, var(--el-color-primary) 64%, rgba(148, 163, 184, 0.22));
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--el-color-primary) 18%, transparent), 0 14px 30px rgba(2, 6, 23, 0.38);
}

.model-badge {
  font-size: 12px;
  padding: 3px 10px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  color: var(--el-text-color-secondary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.connected {
  background: var(--el-color-success);
  animation: pulse 2s infinite;
}

.status-dot.disconnected {
  background: var(--el-color-danger);
}

.status-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.agent-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
}

.agent-option-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 500;
  flex-shrink: 0;
}

.badge-builtin {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border: 1px solid var(--el-color-primary-light-5);
}

.badge-code {
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
  border: 1px solid var(--el-color-success-light-5);
}

.badge-user {
  background: var(--el-color-warning-light-9);
  color: var(--el-color-warning-dark-2);
  border: 1px solid var(--el-color-warning-light-5);
}

.header-btn {
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, border-color 0.18s ease, color 0.18s ease, opacity 0.18s ease;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
}

.header-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.header-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 5px 14px rgba(15, 23, 42, 0.10);
}

.header-btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in srgb, currentColor 18%, transparent), 0 8px 20px rgba(15, 23, 42, 0.12);
}

.btn-edit {
  color: #f5f3ff;
  background: linear-gradient(135deg, #5b4b8a, #475569);
  border-color: rgba(109, 91, 163, 0.42);
}

.btn-edit:hover:not(:disabled) {
  background: linear-gradient(135deg, #6d5fa8, #52627a);
  border-color: rgba(129, 111, 181, 0.5);
}

.btn-edit:disabled {
  opacity: 0.48;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-new-agent {
  color: #ffffff;
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  border-color: rgba(37, 99, 235, 0.42);
}

.btn-new-agent:hover {
  background: linear-gradient(135deg, #1d4ed8, #2563eb);
}

.btn-new-chat,
.mobile-new-chat-btn {
  color: #ffffff;
  background: linear-gradient(135deg, #059669, #10b981);
  border-color: rgba(5, 150, 105, 0.36);
}

.btn-new-chat:hover,
.mobile-new-chat-btn:hover {
  background: linear-gradient(135deg, #047857, #059669);
}

:deep(.copy-rounds-trigger) {
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
  background: linear-gradient(135deg, #ea580c, #f59e0b);
  color: #ffffff;
  border: 1px solid rgba(234, 88, 12, 0.34);
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}

:deep(.copy-rounds-trigger:hover) {
  transform: translateY(-1px);
  background: linear-gradient(135deg, #c2410c, #ea580c);
  border-color: rgba(194, 65, 12, 0.4);
}

:global(html.dark) .header-btn,
:global(html.dark) .copy-rounds-trigger {
  box-shadow: 0 10px 24px rgba(2, 6, 23, 0.34);
}

:global(html.dark) .btn-edit {
  color: #f5f3ff;
  background: linear-gradient(135deg, rgba(88, 70, 139, 0.98), rgba(51, 65, 85, 0.96));
  border-color: rgba(129, 111, 181, 0.3);
}

:global(html.dark) .btn-edit:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(109, 95, 168, 0.98), rgba(71, 85, 105, 0.98));
  border-color: rgba(167, 139, 250, 0.42);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

@media (max-width: 900px) {
  .app-header {
    padding: 8px 10px;
    gap: 6px;
  }

  .mobile-sidebar-btn,
  .mobile-tools-btn,
  .mobile-new-chat-btn,
  .mobile-only {
    display: inline-flex;
    flex-shrink: 0;
  }

  .desktop-only {
    display: none;
  }

  .header-left {
    flex-shrink: 0;
  }

  .logo {
    display: none;
  }

  .header-center {
    justify-content: flex-start;
    overflow: hidden;
  }

  .header-right {
    gap: 4px;
  }

  .agent-select {
    display: inline-flex;
    flex: 1;
    width: auto;
    min-width: 0;
    max-width: none;
  }

  .agent-select :deep(.el-select__wrapper) {
    width: 100%;
    min-width: 0;
    padding-right: 24px;
  }

  .header-btn,
  .model-badge,
  .status-dot,
  .status-text {
    display: none;
  }

  .mobile-new-chat-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 34px;
    padding: 0 10px;
    white-space: nowrap;
    font-size: 12px;
    flex-shrink: 0;
    border-radius: 999px;
  }

  :deep(.copy-rounds-trigger) {
    min-height: 34px;
    padding: 0 10px;
  }
}
</style>
