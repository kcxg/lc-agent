<template>
  <ConfigProvider :theme="isDark ? 'dark' : 'light'">
    <router-view v-if="isPublicRoute" />
    <div v-else class="app-container">
    <AppHeader
      :app-name="appName"
      :model-name="agentsStore.isCodeAgent ? '代码内定义' : (toolsStore.currentModel || agentsStore.currentAgent?.default_model || 'N/A')"
      @manage-agents="openAgentManager"
      @new-chat="handleNewChat"
      @change-agent="handleAgentChange"
      @open-mobile-sidebar="openMobileLeft"
      @open-mobile-tools="openMobileRight"
    />

    <div
      v-if="mobileLeftOpen || mobileRightOpen"
      class="mobile-drawer-backdrop"
      @click="closeMobileDrawers"
    />

    <div
      class="app-body"
      :class="{
        'mobile-left-open': mobileLeftOpen,
        'mobile-right-open': mobileRightOpen,
      }"
    >
      <LeftSidebar
        class="mobile-left-panel"
        :class="{ 'is-mobile-open': mobileLeftOpen }"
        :collapsed="mobileLeftOpen ? false : sidebarCollapsed"
        :panel-width="sidebarWidth"
        @new-chat="handleNewChat"
        @new-chat-for-agent="handleAgentChange"
        @switch-session="handleSwitchSession"
        @close-session-tab="handleSessionDeleted"
        @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
        @open-settings="openCleanupDialog"
        @change-password="openChangePassword"
        @go-admin="goAdmin"
        @logout="handleLogout"
      />

      <div
        v-if="!sidebarCollapsed"
        class="resizer resizer-left"
        @mousedown="startResize('left', $event)"
      />

      <main class="chat-main">
        <SessionTabs
          v-if="isChatRoute"
          @activate="handleTabActivate"
          @close="handleTabClose"
        />
        <router-view />
      </main>

      <div
        v-if="!rightCollapsed"
        class="resizer resizer-right"
        @mousedown="startResize('right', $event)"
      />

      <RightPanel
        class="mobile-right-panel"
        :class="{ 'is-mobile-open': mobileRightOpen }"
        :collapsed="mobileRightOpen ? false : rightCollapsed"
        :panel-width="rightWidth"
        @toggle-collapse="rightCollapsed = !rightCollapsed"
        @open-automation="openAutomationDrawer"
      />
    </div>

    <AgentManagerDialog ref="agentManagerRef" />
    <CleanupDialog ref="cleanupDialogRef" @cleaned="handleCleanupDone" />
    <ChangePasswordDialog ref="changePasswordRef" />
    <AutomationDrawer ref="automationDrawerRef" />
    </div>
  </ConfigProvider>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ConfigProvider } from 'vue-element-plus-x'
import { useTheme } from '@/composables/useTheme'
import { usePanelResize } from '@/composables/usePanelResize'
import { api } from '@/api/http'
import { useChatStore } from '@/stores/chat'
import { useToolsStore } from '@/stores/tools'
import { useAgentsStore } from '@/stores/agents'
import { useSessionsStore } from '@/stores/sessions'
import type { Session } from '@/stores/sessions'
import { useSessionTabsStore } from '@/stores/session-tabs'
import { useOpenedFilesStore } from '@/stores/opened-files'
import { useChatUiStateStore } from '@/stores/chat-ui-state'
import { useFileChangesStore } from '@/stores/file-changes'
import AppHeader from '@/components/layout/AppHeader.vue'
import LeftSidebar from '@/components/layout/LeftSidebar.vue'
import RightPanel from '@/components/layout/RightPanel.vue'
import SessionTabs from '@/components/layout/SessionTabs.vue'
import AgentManagerDialog from '@/components/dialogs/AgentManagerDialog.vue'
import CleanupDialog from '@/components/dialogs/CleanupDialog.vue'
import ChangePasswordDialog from '@/components/dialogs/ChangePasswordDialog.vue'
import AutomationDrawer from '@/components/automation/AutomationDrawer.vue'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const { isDark } = useTheme()
const { leftWidth, rightWidth, startResize } = usePanelResize()

const sidebarWidth = computed(() => sidebarCollapsed.value ? 68 : leftWidth.value)

const router = useRouter()
const route = useRoute()
const chatStore = useChatStore()
const toolsStore = useToolsStore()
const agentsStore = useAgentsStore()
const sessionsStore = useSessionsStore()
const sessionTabsStore = useSessionTabsStore()
const openedFilesStore = useOpenedFilesStore()
const chatUiStateStore = useChatUiStateStore()
const authStore = useAuthStore()
const uiStore = useUiStore()
const agentManagerRef = ref<InstanceType<typeof AgentManagerDialog>>()
const cleanupDialogRef = ref<InstanceType<typeof CleanupDialog>>()
const changePasswordRef = ref<InstanceType<typeof ChangePasswordDialog>>()
const automationDrawerRef = ref<InstanceType<typeof AutomationDrawer>>()
const sidebarCollapsed = ref(false)
const rightCollapsed = ref(false)
const mobileLeftOpen = ref(false)
const mobileRightOpen = ref(false)
const appName = ref('lc_agent')

const isPublicRoute = computed(() => !!route.meta.public)
// 标签栏只管聊天会话：Admin / Usage 等整页路由不产生标签，也不该显示标签栏
const isChatRoute = computed(() => ['home', 'chat'].includes(String(route.name || '')))
const appInitialized = ref(false)

const RIGHT_COLLAPSED_KEY = 'lc-agent:layout:rightCollapsed'
function loadRightCollapsed(): boolean {
  try {
    return localStorage.getItem(RIGHT_COLLAPSED_KEY) === '1'
  } catch { return false }
}
rightCollapsed.value = loadRightCollapsed()
watch(rightCollapsed, (v) => {
  try {
    localStorage.setItem(RIGHT_COLLAPSED_KEY, v ? '1' : '0')
  } catch { /* ignore */ }
})

// 跨组件请求切 tab：收起状态下自动展开右侧面板（移动端则打开右侧抽屉）
watch(() => uiStore.rightPanelOpenRequest, () => {
  if (window.innerWidth <= 900) {
    mobileLeftOpen.value = false
    mobileRightOpen.value = true
    return
  }
  rightCollapsed.value = false
})

async function initApp() {
  if (appInitialized.value || isPublicRoute.value) return
  appInitialized.value = true

  const initialSessionId = typeof route.params.sessionId === 'string' ? route.params.sessionId : undefined
  await Promise.all([
    toolsStore.init(),
    agentsStore.init(),
    sessionsStore.init(initialSessionId),
  ])

  // 恢复上次的标签集合，剔除已删除的会话；本地（未落库）会话 id 也算有效
  sessionTabsStore.restoreTabs([
    ...sessionsStore.sessions.map(s => s.id),
    ...(initialSessionId ? [initialSessionId] : []),
  ])

  // 恢复当前 agent 上次打开的文件标签（localStorage）
  openedFilesStore.restoreForCurrentAgent()

  try {
    const health = await api.health()
    if (health.app_name?.trim()) {
      appName.value = health.app_name.trim()
      document.title = health.app_name.trim()
    }
  } catch (e) {
    console.error('[App] Failed to fetch app name:', e)
  }

  const sessionId = route.params.sessionId as string
  if (sessionId) {
    await restoreSession(sessionId)
    return
  }

  // URL 停在首页但上次有激活标签：直接恢复到那个会话。
  // 仅在聊天路由上做，否则直接打开 /admin 会被劫持回聊天页。
  if (isChatRoute.value && sessionTabsStore.activeTabId) {
    await handleSwitchSession(sessionTabsStore.activeTabId)
    return
  }

  const routeSessionId = typeof sessionId === 'string' ? sessionId : ''
  const agentQuery = route.query.agent as string
  if (routeSessionId && agentQuery && agentsStore.agents.find(a => a.id === agentQuery)) {
    const sessionModel = getSessionModelForAgent(agentQuery)
    sessionsStore.ensureLocalSession(routeSessionId, agentQuery, sessionModel)
    sessionsStore.selectSession(routeSessionId)
    if (agentQuery !== agentsStore.currentAgentId) {
      await agentsStore.selectAgent(agentQuery)
    }
    applySessionModel(sessionModel)
    return
  }

  if (agentQuery && agentsStore.agents.find(a => a.id === agentQuery)) {
    await agentsStore.selectAgent(agentQuery)
  }
}


function getSessionModelForAgent(agentId: string): string {
  const agent = agentsStore.agents.find(a => a.id === agentId)
  if (agent?.source === 'code') return ''
  return agent?.default_model || toolsStore.currentModel || ''
}

function getCurrentRightPanelModelForAgent(agentId: string): string {
  const agent = agentsStore.agents.find(a => a.id === agentId)
  if (agent?.source === 'code') return ''
  return toolsStore.currentModel || agent?.default_model || ''
}

function applySessionModel(model: string) {
  if (model) {
    toolsStore.applyModel(model)
  }
}

onMounted(async () => {
  await initApp()
})

watch(isPublicRoute, async (isPublic) => {
  if (!isPublic) {
    appInitialized.value = false
    await initApp()
  }
})

watch(() => route.params.sessionId, (newId) => {
  if (newId && typeof newId === 'string') {
    restoreSession(newId)
  }
})

async function restoreSession(sessionId: string) {
  // 深链 / 前进后退进入某个会话时，同样把它纳入标签栏（已打开则去重激活）
  sessionTabsStore.openTab(sessionId)
  if (chatStore.threadId === sessionId && chatStore.isConnected) return
  if (!sessionsStore.isLoaded) return

  const session = sessionsStore.sessions.find(s => s.id === sessionId)
  if (session) {
    sessionsStore.selectSession(sessionId)
    await applySessionContext(session)
    await chatStore.switchToSession(sessionId)
    sessionTabsStore.notifySwitchCompleted()
    return
  }

  if (sessionsStore.lastLoadFailed) {
    sessionsStore.selectSession(sessionId)
    await chatStore.switchToSession(sessionId)
    sessionTabsStore.notifySwitchCompleted()
    return
  }

  const agentQuery = route.query.agent as string
  if (agentQuery && agentsStore.agents.find(a => a.id === agentQuery)) {
    const sessionModel = getSessionModelForAgent(agentQuery)
    sessionsStore.ensureLocalSession(sessionId, agentQuery, sessionModel)
    sessionsStore.selectSession(sessionId)
    if (agentQuery !== agentsStore.currentAgentId) {
      await agentsStore.selectAgent(agentQuery)
    }
    applySessionModel(sessionModel)
    await chatStore.switchToSession(sessionId)
    sessionTabsStore.notifySwitchCompleted()
  }
}

async function handleNewChat() {
  const sessionModel = getCurrentRightPanelModelForAgent(agentsStore.currentAgentId)
  const session = sessionsStore.createLocalSession(agentsStore.currentAgentId, sessionModel)
  sessionTabsStore.openTab(session.id)
  const sameRouteSession = route.params.sessionId === session.id
  await chatStore.switchToSession(session.id)
  await router.push({ name: 'chat', params: { sessionId: session.id }, query: { agent: agentsStore.currentAgentId } })
  sessionTabsStore.notifySwitchCompleted()
  if (sameRouteSession) {
    await restoreSession(session.id)
  }
  closeMobileDrawers()
}

/**
 * 切到某会话时对齐 agent 上下文：R3-Q1 选了跨 agent 全局标签栏，
 * 激活别的 agent 的标签必须先把 agent 切过去，否则右侧面板/项目树/模型全是旧的。
 * 先切 agent 再同步模型——反过来会拿旧 agent 的 source 去判断，模型会错。
 */
async function applySessionContext(session: Session | undefined) {
  if (session?.agent_id && session.agent_id !== agentsStore.currentAgentId) {
    await agentsStore.selectAgent(session.agent_id)
  }
  if (agentsStore.currentAgent?.source === 'code') {
    toolsStore.syncModelWithAgentDefault()
  } else if (session?.model) {
    toolsStore.applyModel(session.model)
  }
}

async function handleSwitchSession(sessionId: string) {
  // 点击侧边栏会话 = 打开标签（已打开则去重激活）
  sessionTabsStore.openTab(sessionId)
  const session = sessionsStore.sessions.find(s => s.id === sessionId)

  if (chatStore.threadId === sessionId && chatStore.isConnected) {
    await applySessionContext(session)
    // 会话已在内存：仍需恢复其滚动位置（用户可能滚动过再切走）
    useFileChangesStore().switchToSession(sessionId)
    sessionTabsStore.notifySwitchCompleted()
    router.push({ name: 'chat', params: { sessionId }, query: { agent: agentsStore.currentAgentId } })
    closeMobileDrawers()
    return
  }

  sessionsStore.selectSession(sessionId)
  await applySessionContext(session)
  await chatStore.switchToSession(sessionId)
  // 数据加载完成，通知 ChatView 恢复该标签的滚动位置/子会话视图
  sessionTabsStore.notifySwitchCompleted()
  router.push({ name: 'chat', params: { sessionId }, query: { agent: agentsStore.currentAgentId } })
  closeMobileDrawers()
}

/** 点击标签：切过去，跨 agent 时自动切 agent（R3-Q1 选了全局一个标签栏） */
async function handleTabActivate(sessionId: string) {
  sessionTabsStore.setActiveTab(sessionId)
  await handleSwitchSession(sessionId)
}

/** 关闭标签：断开该会话的管线并释放缓存，再激活关闭后的目标标签 */
async function handleTabClose(sessionId: string) {
  const nextId = sessionTabsStore.closeTab(sessionId)
  chatStore.releaseSession(sessionId)
  chatUiStateStore.clearSession(sessionId)
  useFileChangesStore().dropSession(sessionId)

  // 关掉的不是当前标签，主区内容不受影响
  if (chatStore.threadId !== sessionId) return
  if (!nextId) {
    // 最后一个标签被关：回首页空态。会话本身仍在侧边栏列表里，未被删除
    await router.push({ name: 'home' })
    return
  }
  await handleSwitchSession(nextId)
}

/** 会话被删除：标签已由 sessionsStore 内的 removeTab 摘掉，这里只负责善后主区 */
async function handleSessionDeleted(sessionId: string) {
  chatStore.releaseSession(sessionId)
  chatUiStateStore.clearSession(sessionId)
  useFileChangesStore().dropSession(sessionId)

  if (chatStore.threadId !== sessionId) return
  const nextId = sessionTabsStore.activeTabId
  if (!nextId) {
    await router.push({ name: 'home' })
    return
  }
  await handleSwitchSession(nextId)
}

async function handleAgentChange(agentId: string) {
  await agentsStore.selectAgent(agentId)
  const sessionModel = getSessionModelForAgent(agentId)
  applySessionModel(sessionModel)
  const session = sessionsStore.createLocalSession(agentId, sessionModel)
  sessionTabsStore.openTab(session.id)
  await chatStore.switchToSession(session.id)
  await router.push({ name: 'chat', params: { sessionId: session.id }, query: { agent: agentId } })
  closeMobileDrawers()
}

function openAgentManager() {
  agentManagerRef.value?.open(agentsStore.currentAgentId)
}

function openAutomationDrawer() {
  automationDrawerRef.value?.open()
}

function openCleanupDialog() {
  cleanupDialogRef.value?.open()
}

function openChangePassword() {
  changePasswordRef.value?.open()
}

function goAdmin() {
  router.push('/admin')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function handleCleanupDone() {
  // 清理后当前会话可能已被删除（用户取消"跳过活跃"勾选时），需要善后
  // 标签集合已在 init/删除路径里同步，这里只看主区是否还指着一个不存在的会话
  const currentId = chatStore.threadId
  const stillExists = currentId ? sessionsStore.sessions.some(s => s.id === currentId) : false
  if (stillExists) return
  // 当前会话已删：优先切到激活标签，其次第一个会话，都无则新建
  const nextId = sessionTabsStore.activeTabId || sessionsStore.sessions[0]?.id
  if (nextId) {
    handleSwitchSession(nextId)
  } else {
    handleNewChat()
  }
}

function openMobileLeft() {
  mobileLeftOpen.value = !mobileLeftOpen.value
  mobileRightOpen.value = false
}

function openMobileRight() {
  mobileRightOpen.value = !mobileRightOpen.value
  mobileLeftOpen.value = false
}

function closeMobileDrawers() {
  mobileLeftOpen.value = false
  mobileRightOpen.value = false
}
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  position: fixed;
  inset: 0;
  height: 100dvh;
  background: var(--el-bg-color-page);
  overflow: hidden;
}

.app-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}

.resizer {
  width: 5px;
  flex-shrink: 0;
  cursor: col-resize;
  background: transparent;
  transition: background 0.15s;
  position: relative;
  z-index: 10;
}

.resizer:hover,
.resizer:active {
  background: var(--el-color-primary);
}

.resizer-left {
  border-right: 1px solid var(--el-border-color-lighter);
}

.resizer-right {
  border-left: 1px solid var(--el-border-color-lighter);
}

.mobile-drawer-backdrop {
  display: none;
}

@media (max-width: 900px) {
  .resizer {
    display: none;
  }

  .chat-main {
    width: 100%;
    min-width: 0;
  }

  .mobile-drawer-backdrop {
    display: block;
    position: fixed;
    inset: 52px 0 0;
    background: rgba(15, 23, 42, 0.35);
    backdrop-filter: blur(2px);
    z-index: 180;
  }

  .mobile-left-panel,
  .mobile-right-panel {
    position: fixed;
    top: 52px;
    bottom: 0;
    height: calc(100dvh - 52px);
    z-index: 200;
    pointer-events: none;
    box-shadow: 0 24px 60px rgba(15, 23, 42, 0.24);
    transition: transform 0.24s ease, box-shadow 0.24s ease;
  }

  .mobile-left-panel {
    left: 0;
    transform: translateX(-100%);
  }

  .mobile-right-panel {
    right: 0;
    transform: translateX(100%);
  }

  .app-body.mobile-left-open .mobile-left-panel,
  .app-body.mobile-right-open .mobile-right-panel,
  .mobile-left-panel.is-mobile-open,
  .mobile-right-panel.is-mobile-open {
    transform: translateX(0);
    pointer-events: auto;
  }
}

@media (prefers-reduced-motion: reduce) {
  .mobile-left-panel,
  .mobile-right-panel {
    transition: none;
  }
}
</style>
