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
        :prefix-icon="MagicStick"
        placeholder="选择智能体"
        popper-class="agent-select-popper"
      >
        <el-option
          v-for="agent in agentsStore.agents"
          :key="agent.id"
          :label="agent.name"
          :value="agent.id"
        >
          <div class="agent-option">
            <span class="agent-option-icon">{{ getAgentIcon(agent) }}</span>
            <div class="agent-option-content">
              <span class="agent-option-name">{{ agent.name }}</span>
            </div>
            <span :class="['source-tag', `source-tag--${agent.source || 'user'}`]">
              {{ agent.source === 'builtin' ? '内置' : agent.source === 'code' ? '代码' : '自建' }}
            </span>
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
      <button class="header-btn mobile-new-chat-btn" @click="$emit('newChat')">
        <el-icon class="mobile-btn-icon"><Plus /></el-icon>
        <span class="mobile-btn-text">新对话</span>
      </button>
      <span class="mobile-only">
        <CopyRoundsButton v-if="hasMessages" :messages="chatStore.messages" :model-name="sessionModel" />
      </span>
      <el-dropdown trigger="click" @command="handleUserCommand">
        <span class="user-dropdown-trigger">
          <el-icon><UserFilled /></el-icon>
          <span class="username-text">{{ authStore.user?.username || '用户' }}</span>
          <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="change-password">修改密码</el-dropdown-item>
            <el-dropdown-item v-if="authStore.isAdmin" command="admin">管理后台</el-dropdown-item>
            <el-dropdown-item divided command="logout">登出</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button
        class="mobile-tools-btn"
        :icon="Setting"
        circle
        size="small"
        aria-label="打开工具和状态面板"
        @click="$emit('openMobileTools')"
      />
      <span class="model-badge">{{ modelName }}</span>
      <el-button :icon="RefreshRight" circle size="small" title="刷新页面" @click="reloadPage" />
      <el-button :icon="isDark ? Sunny : Moon" circle size="small" @click="toggleDark()" />
    </div>

    <ChangePasswordDialog ref="changePasswordRef" />
  </header>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAgentsStore } from '@/stores/agents'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useToolsStore } from '@/stores/tools'
import { useTheme } from '@/composables/useTheme'
import { Sunny, Moon, Menu, Setting, RefreshRight, MagicStick, UserFilled, ArrowDown, Plus } from '@element-plus/icons-vue'
import CopyRoundsButton from '@/components/chat/CopyRoundsButton.vue'
import ChangePasswordDialog from '@/components/dialogs/ChangePasswordDialog.vue'

const router = useRouter()
const agentsStore = useAgentsStore()
const authStore = useAuthStore()
const chatStore = useChatStore()
const toolsStore = useToolsStore()
const { isDark, toggleDark } = useTheme()
const changePasswordRef = ref<InstanceType<typeof ChangePasswordDialog>>()

function handleUserCommand(command: string) {
  if (command === 'change-password') {
    changePasswordRef.value?.open()
  } else if (command === 'admin') {
    router.push('/admin')
  } else if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}

function reloadPage() {
  window.location.reload()
}

function getAgentIcon(agent: any): string {
  if (agent.source === 'code') return '⚙️'
  if (agent.id === '__chat__') return '💬'
  if (agent.id === '__empty__') return '🧩'
  if (agent.source === 'builtin') return '✨'
  return '🤖'
}

const hasMessages = computed(() => chatStore.messages.length > 0)
const sessionModel = computed(() => {
  if (agentsStore.isCodeAgent) return '代码内定义'
  const model = toolsStore.currentModel || agentsStore.currentAgent?.default_model || ''
  if (!model) return ''
  const parts = model.split('/')
  return parts[parts.length - 1] || model
})

defineProps<{
  appName: string
  modelName: string
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
  width: 260px;
}

.agent-select :deep(.el-select__wrapper) {
  min-width: 0;
  min-height: 36px;
  padding: 0 32px 0 10px;
  border-radius: 12px;
  border: 1.5px solid var(--el-color-primary);
  background: var(--el-bg-color);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
  transition: all 0.2s ease;
}

.agent-select :deep(.el-select__wrapper:hover) {
  border-color: var(--el-color-primary);
  box-shadow: 0 4px 14px color-mix(in srgb, var(--el-color-primary) 16%, transparent);
}

.agent-select :deep(.el-select__wrapper.is-focused) {
  border-color: var(--el-color-primary);
  box-shadow:
    0 0 0 3px color-mix(in srgb, var(--el-color-primary) 12%, transparent),
    0 4px 14px color-mix(in srgb, var(--el-color-primary) 16%, transparent);
}

.agent-select :deep(.el-select__prefix) {
  color: var(--el-color-primary);
  margin-right: 4px;
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
  letter-spacing: 0.01em;
  color: var(--el-text-color-primary);
}

.agent-select :deep(.el-select__caret) {
  color: var(--el-color-primary);
  font-size: 13px;
  opacity: 0.7;
  transition: opacity 0.2s, transform 0.2s;
}

.agent-select :deep(.el-select__wrapper:hover .el-select__caret) {
  opacity: 1;
}

:global(html.dark) .agent-select :deep(.el-select__wrapper) {
  background: rgba(15, 23, 42, 0.9);
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

:global(html.dark) .agent-select :deep(.el-select__wrapper:hover) {
  border-color: var(--el-color-primary);
  box-shadow: 0 4px 18px color-mix(in srgb, var(--el-color-primary) 24%, transparent);
}

:global(html.dark) .agent-select :deep(.el-select__wrapper.is-focused) {
  border-color: var(--el-color-primary);
  box-shadow:
    0 0 0 3px color-mix(in srgb, var(--el-color-primary) 16%, transparent),
    0 6px 20px color-mix(in srgb, var(--el-color-primary) 24%, transparent);
}

.model-badge {
  font-size: 12px;
  padding: 3px 10px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  color: var(--el-text-color-secondary);
}

.user-dropdown-trigger {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--el-border-color);
  background: var(--el-fill-color-light);
  cursor: pointer;
  font-size: 12px;
  color: var(--el-text-color-regular);
  transition: background 0.15s ease, border-color 0.15s ease;
}

.user-dropdown-trigger:hover {
  background: var(--el-fill-color);
  border-color: var(--el-color-primary-light-5);
}

.username-text {
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-arrow {
  font-size: 12px;
  opacity: 0.6;
}


.agent-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 2px 0;
}

.agent-option-icon {
  font-size: 16px;
  flex-shrink: 0;
  width: 22px;
  text-align: center;
}

.agent-option-content {
  flex: 1;
  min-width: 0;
}

.agent-option-name {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 500;
}

.source-tag {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 10px;
  font-weight: 600;
  flex-shrink: 0;
  letter-spacing: 0.02em;
}

.source-tag--builtin {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.1));
  color: #7c3aed;
  border: 1px solid rgba(124, 58, 237, 0.2);
}

.source-tag--code {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(6, 182, 212, 0.1));
  color: #059669;
  border: 1px solid rgba(5, 150, 105, 0.2);
}

.source-tag--user {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(249, 115, 22, 0.1));
  color: #d97706;
  border: 1px solid rgba(217, 119, 6, 0.2);
}

:global(html.dark) .source-tag--builtin {
  background: rgba(124, 58, 237, 0.15);
  color: #a78bfa;
  border-color: rgba(167, 139, 250, 0.25);
}

:global(html.dark) .source-tag--code {
  background: rgba(16, 185, 129, 0.15);
  color: #6ee7b7;
  border-color: rgba(110, 231, 183, 0.25);
}

:global(html.dark) .source-tag--user {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
  border-color: rgba(251, 191, 36, 0.25);
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
    gap: 0;
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
    width: 28px;
    height: 28px;
    min-height: 28px;
    min-width: 28px;
    padding: 0;
    white-space: nowrap;
    font-size: 12px;
    flex-shrink: 0;
    border-radius: 50%;
  }
  .mobile-new-chat-btn .mobile-btn-text {
    display: none;
  }
  .mobile-new-chat-btn .mobile-btn-icon {
    font-size: 14px;
  }

  .user-dropdown-trigger .username-text,
  .user-dropdown-trigger .dropdown-arrow {
    display: none;
  }
  .user-dropdown-trigger {
    width: 28px;
    height: 28px;
    padding: 0;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .header-right :deep(.el-button.is-circle) {
    width: 28px;
    height: 28px;
    --el-button-size: 28px;
    margin: 0;
  }

  .header-right :deep(.el-button + .el-button) {
    margin-left: 0;
  }

  :deep(.copy-rounds-trigger) {
    width: 28px;
    height: 28px;
    min-height: 28px;
    padding: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
  }
}
</style>

<style>
.agent-select-popper.el-popper {
  border-radius: 14px !important;
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 18%, var(--el-border-color-lighter)) !important;
  box-shadow:
    0 20px 48px rgba(15, 23, 42, 0.12),
    0 8px 20px rgba(15, 23, 42, 0.06) !important;
  overflow: hidden;
  padding: 6px !important;
}

.agent-select-popper .el-select-dropdown {
  max-height: 600px !important;
}

.agent-select-popper .el-select-dropdown__list {
  padding: 4px 0 !important;
}

.agent-select-popper .el-select-dropdown__item {
  border-radius: 8px;
  margin: 2px 0;
  padding: 10px 12px;
  height: auto;
  line-height: normal;
  transition: background 0.15s ease;
}

.agent-select-popper .el-select-dropdown__item.is-selected {
  background: linear-gradient(135deg, color-mix(in srgb, var(--el-color-primary) 10%, transparent), color-mix(in srgb, var(--el-color-primary) 6%, transparent));
  font-weight: 600;
}

.agent-select-popper .el-select-dropdown__item:hover {
  background: var(--el-fill-color-light);
}

html.dark .agent-select-popper.el-popper {
  border-color: rgba(148, 163, 184, 0.15) !important;
  box-shadow:
    0 24px 56px rgba(0, 0, 0, 0.4),
    0 10px 24px rgba(0, 0, 0, 0.2) !important;
}
</style>
