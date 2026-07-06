<template>
  <ConfigProvider :theme="isDark ? 'dark' : 'light'">
    <router-view v-if="isPublicRoute" />
    <div v-else class="app-container">
    <AppHeader
      :app-name="appName"
      :model-name="agentsStore.isCodeAgent ? '代码内定义' : (toolsStore.currentModel || agentsStore.currentAgent?.default_model || 'N/A')"
      @edit-agent="editCurrentAgent"
      @new-agent="createNewAgent"
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
        @new-chat="handleNewChat"
        @switch-session="handleSwitchSession"
        @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
      />

      <main class="chat-main">
        <router-view />
      </main>

      <RightPanel
        class="mobile-right-panel"
        :class="{ 'is-mobile-open': mobileRightOpen }"
      />
    </div>

    <AgentEditorDialog ref="agentEditorRef" />
    </div>
  </ConfigProvider>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ConfigProvider } from 'vue-element-plus-x'
import { useTheme } from '@/composables/useTheme'
import { api } from '@/api/http'
import { useChatStore } from '@/stores/chat'
import { useToolsStore } from '@/stores/tools'
import { useAgentsStore } from '@/stores/agents'
import { useSessionsStore } from '@/stores/sessions'
import AppHeader from '@/components/layout/AppHeader.vue'
import LeftSidebar from '@/components/layout/LeftSidebar.vue'
import RightPanel from '@/components/layout/RightPanel.vue'
import AgentEditorDialog from '@/components/dialogs/AgentEditorDialog.vue'

const { isDark } = useTheme()

const router = useRouter()
const route = useRoute()
const chatStore = useChatStore()
const toolsStore = useToolsStore()
const agentsStore = useAgentsStore()
const sessionsStore = useSessionsStore()
const agentEditorRef = ref<InstanceType<typeof AgentEditorDialog>>()
const sidebarCollapsed = ref(false)
const mobileLeftOpen = ref(false)
const mobileRightOpen = ref(false)
const appName = ref('lc_agent')

const isPublicRoute = computed(() => !!route.meta.public)
const appInitialized = ref(false)

async function initApp() {
  if (appInitialized.value || isPublicRoute.value) return
  appInitialized.value = true

  await Promise.all([
    toolsStore.init(),
    agentsStore.init(),
    sessionsStore.init(),
  ])

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

function applySessionModel(model: string) {
  if (model) {
    toolsStore.setModel(model)
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
  if (chatStore.threadId === sessionId && chatStore.isConnected) return
  const session = sessionsStore.sessions.find(s => s.id === sessionId)
  if (session) {
    sessionsStore.selectSession(sessionId)
    if (session.agent_id && session.agent_id !== agentsStore.currentAgentId) {
      await agentsStore.selectAgent(session.agent_id)
    }
    const sessionAgent = agentsStore.agents.find(a => a.id === session.agent_id)
    if (sessionAgent?.source === 'code') {
      toolsStore.syncModelWithAgentDefault()
    } else if (session.model) {
      toolsStore.setModel(session.model)
    }
    chatStore.clearMessages()
    chatStore.disconnect()
    await chatStore.loadMessages(sessionId)
    await chatStore.connect(sessionId)
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
    chatStore.clearMessages()
    chatStore.disconnect()
  }
}

async function handleNewChat() {
  const sessionModel = getSessionModelForAgent(agentsStore.currentAgentId)
  const session = sessionsStore.createLocalSession(agentsStore.currentAgentId, sessionModel)
  const sameRouteSession = route.params.sessionId === session.id
  chatStore.clearMessages()
  chatStore.disconnect()
  await router.push({ name: 'chat', params: { sessionId: session.id }, query: { agent: agentsStore.currentAgentId } })
  if (sameRouteSession) {
    await restoreSession(session.id)
  }
  closeMobileDrawers()
}

async function handleSwitchSession(sessionId: string) {
  if (chatStore.threadId === sessionId && chatStore.isConnected) {
    const session = sessionsStore.sessions.find(s => s.id === sessionId)
    const agentId = session?.agent_id || agentsStore.currentAgentId
    const sessionAgent = agentsStore.agents.find(a => a.id === agentId)
    if (sessionAgent?.source === 'code') {
      toolsStore.syncModelWithAgentDefault()
    } else if (session?.model) {
      toolsStore.setModel(session.model)
    }
    router.push({ name: 'chat', params: { sessionId }, query: { agent: agentId } })
    closeMobileDrawers()
    return
  }
  const session = sessionsStore.sessions.find(s => s.id === sessionId)
  sessionsStore.selectSession(sessionId)
  const agentId = session?.agent_id || agentsStore.currentAgentId
  const sessionAgent = agentsStore.agents.find(a => a.id === agentId)
  if (sessionAgent?.source === 'code') {
    toolsStore.syncModelWithAgentDefault()
  } else if (session?.model) {
    toolsStore.setModel(session.model)
  }
  chatStore.clearMessages()
  chatStore.disconnect()
  await chatStore.loadMessages(sessionId)
  await chatStore.connect(sessionId)
  if (session?.agent_id && session.agent_id !== agentsStore.currentAgentId) {
    await agentsStore.selectAgent(session.agent_id)
  }
  router.push({ name: 'chat', params: { sessionId }, query: { agent: agentId } })
  closeMobileDrawers()
}

async function handleAgentChange(agentId: string) {
  await agentsStore.selectAgent(agentId)
  const sessionModel = getSessionModelForAgent(agentId)
  applySessionModel(sessionModel)
  const session = sessionsStore.createLocalSession(agentId, sessionModel)
  chatStore.clearMessages()
  chatStore.disconnect()
  await router.push({ name: 'chat', params: { sessionId: session.id }, query: { agent: agentId } })
  closeMobileDrawers()
}

function editCurrentAgent() {
  agentEditorRef.value?.open(agentsStore.currentAgent)
}

function createNewAgent() {
  agentEditorRef.value?.open()
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
  overflow: hidden;
}

.mobile-drawer-backdrop {
  display: none;
}

@media (max-width: 900px) {
  .app-body {
    position: relative;
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
