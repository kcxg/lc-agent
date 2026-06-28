<template>
  <header class="app-header" :class="{ 'is-desktop': isDesktop }">
    <div class="header-left" :class="{ 'desktop-drag': isDesktop }">
      <el-button
        class="mobile-sidebar-btn"
        :icon="Menu"
        circle
        size="small"
        aria-label="打开会话列表"
        @click="$emit('openMobileSidebar')"
      />
      <span class="logo">⚡ lc_agent</span>
    </div>
    <div class="header-center" :class="{ 'desktop-no-drag': isDesktop }">
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
            <span>{{ agent.name }}</span>
            <span v-if="agent.source === 'builtin'" class="source-badge badge-builtin">内置</span>
            <span v-else-if="agent.source === 'code'" class="source-badge badge-code">代码</span>
            <span v-else class="source-badge badge-user">自建</span>
          </div>
        </el-option>
      </el-select>
      <button class="header-btn btn-edit" @click="$emit('editAgent')" :disabled="agentsStore.isBuiltin">编辑</button>
      <button class="header-btn btn-new-agent" @click="$emit('newAgent')">+ 新Agent</button>
      <button class="header-btn btn-new-chat" @click="$emit('newChat')">+ 新对话</button>
    </div>
    <div class="header-right" :class="{ 'desktop-no-drag': isDesktop }">
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
      <el-button :icon="isDark ? Sunny : Moon" circle size="small" @click="toggleDark()" />
      <div v-if="isDesktop" class="window-controls" aria-label="窗口控制">
        <button class="window-control" type="button" aria-label="最小化" @click="minimizeWindow">─</button>
        <button class="window-control" type="button" aria-label="全屏或还原" @click="toggleMaximizeWindow">□</button>
        <button class="window-control close" type="button" aria-label="关闭" @click="closeWindow">×</button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAgentsStore } from '@/stores/agents'
import { useTheme } from '@/composables/useTheme'
import { Sunny, Moon, Menu, Setting } from '@element-plus/icons-vue'

declare global {
  interface Window {
    pywebview?: {
      api?: {
        minimize?: () => void
        toggle_maximize?: () => void
        close?: () => void
      }
    }
  }
}

const agentsStore = useAgentsStore()
const { isDark, toggleDark } = useTheme()
const isDesktop = ref(false)

onMounted(() => {
  const params = new URLSearchParams(window.location.search)
  isDesktop.value = params.get('desktop') === '1' || Boolean(window.pywebview?.api)
})

function minimizeWindow() {
  window.pywebview?.api?.minimize?.()
}

function toggleMaximizeWindow() {
  window.pywebview?.api?.toggle_maximize?.()
}

function closeWindow() {
  window.pywebview?.api?.close?.()
}

defineProps<{
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

.app-header.is-desktop {
  padding-right: 0;
}

.logo {
  font-size: 16px;
  font-weight: 700;
  color: var(--el-color-primary);
}

.is-desktop .logo {
  pointer-events: auto;
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
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mobile-sidebar-btn,
.mobile-tools-btn {
  display: none;
}

.agent-select {
  width: 240px;
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
  width: 100%;
}

.source-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.badge-builtin {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border: 1px solid var(--el-color-primary-light-5);
}

.badge-code {
  background: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
  border: 1px solid var(--el-color-warning-light-5);
}

.badge-user {
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
  border: 1px solid var(--el-color-success-light-5);
}

.header-btn {
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: none;
}

.header-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-edit {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-regular);
  border: 1px solid var(--el-border-color);
}

.btn-edit:hover:not(:disabled) {
  background: var(--el-fill-color);
  color: var(--el-text-color-primary);
}

.btn-new-agent {
  background: var(--el-color-success);
  color: var(--el-color-white);
}

.btn-new-agent:hover {
  background: var(--el-color-success-light-3);
}

.btn-new-chat {
  background: var(--el-color-primary);
  color: var(--el-color-white);
  white-space: nowrap;
  flex-shrink: 0;
}

.btn-new-chat:hover {
  background: var(--el-color-primary-light-3);
}

.window-controls {
  display: flex;
  align-items: stretch;
  align-self: stretch;
  margin-left: 4px;
  border-left: 1px solid color-mix(in srgb, var(--el-border-color) 72%, transparent);
}

.window-control {
  width: 46px;
  height: 100%;
  border: none;
  background: transparent;
  color: var(--el-text-color-regular);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  transition: background 0.14s ease, color 0.14s ease;
}

.window-control:hover {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

.window-control.close {
  font-size: 18px;
}

.window-control.close:hover {
  background: #e81123;
  color: #fff;
}

@media (max-width: 900px) {
  .app-header {
    padding: 8px 0 8px 10px;
    gap: 8px;
  }

  .mobile-sidebar-btn,
  .mobile-tools-btn {
    display: inline-flex;
    flex-shrink: 0;
  }

  .header-left,
  .header-right {
    flex-shrink: 0;
  }

  .header-center {
    flex: 1;
    justify-content: flex-end;
  }

  .agent-select {
    width: min(42vw, 220px);
  }

  .btn-edit,
  .btn-new-agent,
  .model-badge {
    display: none;
  }
}

@media (max-width: 520px) {
  .logo {
    font-size: 14px;
  }

  .agent-select {
    width: min(40vw, 160px);
  }

  .status-text {
    display: none;
  }

  .btn-new-chat {
    padding: 5px 8px;
  }
}

@media (max-width: 420px) {
  .logo {
    display: none;
  }

  .agent-select {
    width: min(46vw, 170px);
  }
}
</style>

<style>
.app-header.is-desktop {
  -webkit-app-region: drag;
}
.desktop-drag {
  -webkit-app-region: drag;
}
.desktop-no-drag {
  -webkit-app-region: no-drag;
}
</style>
