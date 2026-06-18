<template>
  <ConfigProvider :theme="isDark ? 'dark' : 'light'">
  <div class="app-container">
    <AppHeader
      :model-name="toolsStore.currentModel || agentsStore.currentAgent?.default_model || 'N/A'"
      :connected="chatStore.isConnected"
      @edit-agent="editCurrentAgent"
      @new-agent="createNewAgent"
      @new-chat="handleNewChat"
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
        :collapsed="mobileLeftOpen ? false : sidebarCollapsed"
        @new-chat="handleNewChat"
        @switch-session="handleSwitchSession"
        @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
      />

      <main class="chat-main">
        <router-view />
      </main>

      <RightPanel class="mobile-right-panel" />
    </div>

    <AgentEditorDialog ref="agentEditorRef" />
  </div>
  </ConfigProvider>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ConfigProvider } from 'vue-element-plus-x'
import { useTheme } from '@/composables/useTheme'
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
let skipAgentWatch = false

onMounted(async () => {
  await Promise.all([
    toolsStore.init(),
    agentsStore.init(),
    sessionsStore.init(),
  ])

  const agentQuery = route.query.agent as string
  if (agentQuery && agentsStore.agents.find(a => a.id === agentQuery)) {
    agentsStore.selectAgent(agentQuery)
  }

  const sessionId = route.params.sessionId as string
  if (sessionId) {
    restoreSession(sessionId)
  }
})

watch(() => route.params.sessionId, (newId) => {
  if (newId && typeof newId === 'string') {
    restoreSession(newId)
  }
})

async function restoreSession(sessionId: string) {
  if (chatStore.threadId === sessionId) return
  const session = sessionsStore.sessions.find(s => s.id === sessionId)
  if (session) {
    sessionsStore.selectSession(sessionId)
    if (session.agent_id && session.agent_id !== agentsStore.currentAgentId) {
      skipAgentWatch = true
      agentsStore.selectAgent(session.agent_id)
    }
    chatStore.clearMessages()
    chatStore.disconnect()
    await chatStore.loadMessages(sessionId)
    chatStore.connect(sessionId)
  }
}

function handleNewChat() {
  const session = sessionsStore.createLocalSession(agentsStore.currentAgentId)
  chatStore.clearMessages()
  chatStore.disconnect()
  router.push({ name: 'chat', params: { sessionId: session.id }, query: { agent: agentsStore.currentAgentId } })
  closeMobileDrawers()
}

async function handleSwitchSession(sessionId: string) {
  if (chatStore.threadId === sessionId) {
    const session = sessionsStore.sessions.find(s => s.id === sessionId)
    const agentId = session?.agent_id || agentsStore.currentAgentId
    router.push({ name: 'chat', params: { sessionId }, query: { agent: agentId } })
    closeMobileDrawers()
    return
  }
  const session = sessionsStore.sessions.find(s => s.id === sessionId)
  sessionsStore.selectSession(sessionId)
  chatStore.clearMessages()
  chatStore.disconnect()
  await chatStore.loadMessages(sessionId)
  chatStore.connect(sessionId)
  const agentId = session?.agent_id || agentsStore.currentAgentId
  if (session?.agent_id && session.agent_id !== agentsStore.currentAgentId) {
    skipAgentWatch = true
    agentsStore.selectAgent(session.agent_id)
  }
  router.push({ name: 'chat', params: { sessionId }, query: { agent: agentId } })
  closeMobileDrawers()
}

watch(() => agentsStore.currentAgentId, (newAgentId) => {
  if (skipAgentWatch) {
    skipAgentWatch = false
    return
  }
  if (route.name === 'home' || route.name === 'chat') {
    const session = sessionsStore.createLocalSession(newAgentId)
    chatStore.clearMessages()
    chatStore.disconnect()
    router.push({ name: 'chat', params: { sessionId: session.id }, query: { agent: newAgentId } })
    closeMobileDrawers()
  }
})

function editCurrentAgent() {
  agentEditorRef.value?.open(agentsStore.currentAgent)
}

function createNewAgent() {
  agentEditorRef.value?.open()
}

function openMobileLeft() {
  mobileLeftOpen.value = true
  mobileRightOpen.value = false
}

function openMobileRight() {
  mobileRightOpen.value = true
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
  height: 100vh;
  background: var(--el-bg-color-page);
  position: relative;
  overflow: hidden;
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
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
  .app-body.mobile-right-open .mobile-right-panel {
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
