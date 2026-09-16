<template>
  <aside class="left-sidebar" :class="{ collapsed }" :style="panelWidth !== undefined ? { width: panelWidth + 'px' } : {}">
    <div class="sidebar-header">
      <transition name="fade">
        <div v-if="!collapsed" class="sidebar-brand-wrap">
          <div v-if="isProjectMode" class="view-switch" role="tablist" aria-label="侧栏视图切换">
            <button
              type="button"
              role="tab"
              class="view-switch-btn"
              :class="{ active: sidebarView === 'chats' }"
              :aria-selected="sidebarView === 'chats'"
              @click="sidebarView = 'chats'"
            >
              <svg class="view-switch-icon" viewBox="0 0 16 16" aria-hidden="true">
                <path
                  d="M2.5 4.5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v4.5a2 2 0 0 1-2 2H7.5L4.5 13.5V11h0a2 2 0 0 1-2-2z"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.4"
                  stroke-linejoin="round"
                />
              </svg>
              <span>Chats</span>
            </button>
            <button
              type="button"
              role="tab"
              class="view-switch-btn"
              :class="{ active: sidebarView === 'files' }"
              :aria-selected="sidebarView === 'files'"
              @click="sidebarView = 'files'"
            >
              <svg class="view-switch-icon" viewBox="0 0 16 16" aria-hidden="true">
                <path
                  d="M1.8 4.2c0-.5.4-.9.9-.9h3.1l1.3 1.5h6.2c.5 0 .9.4.9.9v6.1c0 .5-.4.9-.9.9H2.7a.9.9 0 0 1-.9-.9z"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.4"
                  stroke-linejoin="round"
                />
              </svg>
              <span>文件</span>
            </button>
          </div>
          <span v-else class="sidebar-brand">Chats</span>
        </div>
      </transition>
      <div v-if="!collapsed" class="header-actions">
        <button v-if="sidebarView === 'chats'" class="action-btn" @click="toggleAllGroups" :title="allCollapsed ? '全部展开' : '全部折叠'">
          <span v-if="allCollapsed">⊞</span>
          <span v-else>⊟</span>
        </button>
        <button class="toggle-btn" @click="emit('toggleCollapse')" :title="collapsed ? '展开侧边栏' : '收起侧边栏'">
          <span class="toggle-icon" :class="{ flipped: collapsed }">«</span>
        </button>
      </div>
      <button v-else class="toggle-btn" @click="emit('toggleCollapse')" title="展开侧边栏">
        <span class="toggle-icon flipped">«</span>
      </button>
    </div>

    <div v-if="!collapsed && sidebarView === 'files'" class="sidebar-files">
      <FileTreePanel />
    </div>

    <div v-else-if="!collapsed" ref="sessionListRef" class="session-list">
      <div class="sidebar-search">
        <input
          v-model="searchQuery"
          class="sidebar-search-input"
          type="text"
          placeholder="搜索聊天标题"
        >
      </div>

      <div v-if="renderedGroups.length > 0" class="session-tree">
        <section
          v-for="group in renderedGroups"
          :key="group.agentId"
          class="agent-section"
          :class="[`agent-src-${group.agentSource}`, { 'is-active-agent': group.agentId === activeAgentId }]"
        >
          <button
            type="button"
            class="agent-section-header"
            @click="toggleGroup(group.agentName)"
          >
            <span class="agent-group-arrow" :class="{ collapsed: collapsedGroups.has(group.agentName) }">▶</span>
            <span class="agent-group-icon">{{ group.agentIcon }}</span>
            <span class="agent-group-name">{{ group.agentName }}</span>
            <span class="agent-section-actions">
              <span class="agent-card-count">{{ group.badgeText }}</span>
              <button
                type="button"
                class="agent-new-chat-btn"
                title="新建会话"
                @click.stop="emit('newChatForAgent', group.agentId)"
              >
                +
              </button>
            </span>
          </button>

          <div v-if="!collapsedGroups.has(group.agentName)" class="session-children">
            <div
              v-for="session in group.visibleSessions"
              :key="session.id"
              class="session-item"
              :class="{
                'is-active': session.id === sessionsStore.currentSessionId,
                'is-menu-open': openMenuSessionId === session.id,
              }"
              :data-session-id="session.id"
              @click="handleSessionSelect(session.id)"
            >
              <span v-if="session.is_pinned" class="session-pin-indicator">📌</span>
              <span
                v-if="chatStore.isSessionStreaming(session.id)"
                class="session-streaming-spinner"
                title="正在生成中"
              />
              <span
                v-else-if="sessionsStore.isCompletedUnseen(session.id)"
                class="session-completed-badge"
                title="已完成，尚未查看"
              >✓</span>
              <span class="session-item-title">{{ session.title || '新对话' }}</span>
              <div class="session-item-meta">
                <button
                  type="button"
                  class="session-action-btn"
                  title="会话操作"
                  @click.stop="toggleSessionMenu(session.id)"
                >
                  ⋯
                </button>
                <div v-if="openMenuSessionId === session.id" class="session-menu">
                  <button type="button" @click.stop="handleRename(session.id, session.title || '新对话')">重命名</button>
                  <button type="button" @click.stop="handleTogglePinned(session)">
                    {{ session.is_pinned ? '取消置顶' : '置顶' }}
                  </button>
                  <button type="button" @click.stop="handleDelete(session.id)">删除</button>
                </div>
              </div>
            </div>

            <button
              v-if="group.hiddenCount > 0"
              type="button"
              class="show-more-btn"
              @click="showMore(group.agentId)"
            >
              <span class="show-more-icon">↓</span>
              <span>显示更多</span>
              <span class="show-more-hint">还有 {{ group.hiddenCount }} 条</span>
            </button>
          </div>
        </section>
      </div>

      <div v-else class="empty-state">
        <span>{{ normalizedQuery ? '没有匹配的聊天标题' : '暂无聊天' }}</span>
      </div>
    </div>

    <div v-if="!collapsed" class="sidebar-footer">
      <el-dropdown trigger="click" placement="top-start" @command="handleSettingsCommand">
        <button type="button" class="settings-btn" title="设置">
          <span class="settings-icon">⚙️</span>
          <span class="settings-label">{{ authStore.user?.username || '设置' }}</span>
          <el-icon class="settings-arrow"><ArrowUp /></el-icon>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="change-password">修改密码</el-dropdown-item>
            <el-dropdown-item command="my-usage">我的用量</el-dropdown-item>
            <el-dropdown-item v-if="authStore.isAdmin" command="admin">管理后台</el-dropdown-item>
            <el-dropdown-item v-if="authStore.isAdmin" command="usage-admin">用量统计</el-dropdown-item>
            <el-dropdown-item v-if="authStore.isAdmin" command="cleanup">数据清理</el-dropdown-item>
            <el-dropdown-item divided command="logout">登出</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { ArrowUp } from '@element-plus/icons-vue'
import { useSessionsStore, type Session } from '@/stores/sessions'
import { useAgentsStore } from '@/stores/agents'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import FileTreePanel from '@/components/panels/FileTreePanel.vue'

const props = defineProps<{ collapsed: boolean; panelWidth?: number }>()

const sessionsStore = useSessionsStore()
const agentsStore = useAgentsStore()
const chatStore = useChatStore()
const authStore = useAuthStore()
const emit = defineEmits<{
  newChat: []
  newChatForAgent: [agentId: string]
  switchSession: [id: string]
  closeSessionTab: [id: string]
  toggleCollapse: []
  openSettings: []
  changePassword: []
  goAdmin: []
  goUsageAdmin: []
  goMyUsage: []
  logout: []
}>()

// 侧栏视图：会话列表 / 项目文件树
const sidebarView = ref<'chats' | 'files'>('chats')
const isProjectMode = computed(() => agentsStore.currentAgent?.project_mode ?? false)

// 切到非项目模式 agent 时文件视图没有意义，自动回到会话列表
watch(isProjectMode, (projectMode) => {
  if (!projectMode && sidebarView.value === 'files') sidebarView.value = 'chats'
})

function handleSettingsCommand(command: string) {
  if (command === 'change-password') {
    emit('changePassword')
  } else if (command === 'admin') {
    emit('goAdmin')
  } else if (command === 'my-usage') {
    emit('goMyUsage')
  } else if (command === 'usage-admin') {
    emit('goUsageAdmin')
  } else if (command === 'cleanup') {
    emit('openSettings')
  } else if (command === 'logout') {
    emit('logout')
  }
}

const DEFAULT_VISIBLE_COUNT = 5
const LOAD_MORE_COUNT = 20
const SIDEBAR_COLLAPSED_GROUPS_KEY = 'lc-agent:sidebar:collapsed-agent-groups'

const searchQuery = ref('')
const openMenuSessionId = ref<string | null>(null)
const visibleCountByAgent = ref<Record<string, number>>({})
const sessionListRef = ref<HTMLElement | null>(null)
// 首次渲染时按最近会话活动排序一次，之后冻结顺序，切换会话不再重排
const frozenOrder = ref<string[] | null>(null)

interface SidebarGroup {
  agentId: string
  agentName: string
  agentIcon: string
  agentSource: 'builtin' | 'code' | 'user' | 'deleted'
  isProjectMode: boolean
  lastActivityAt: number
  badgeText: string
  visibleSessions: Session[]
  hiddenCount: number
}

function getAgentIcon(agent: { id: string; source: string; project_mode?: boolean } | null): string {
  if (!agent) return '🤖'
  if (agent.project_mode) return '📁'
  if (agent.source === 'code') return '⚙️'
  if (agent.id === 'chat') return '💬'
  if (agent.id === 'empty') return '🧩'
  if (agent.source === 'builtin') return '✨'
  return '🤖'
}

function loadCollapsedGroups() {
  try {
    const raw = localStorage.getItem(SIDEBAR_COLLAPSED_GROUPS_KEY)
    const names = raw ? JSON.parse(raw) : []
    return new Set(Array.isArray(names) ? names.filter((name): name is string => typeof name === 'string') : [])
  } catch {
    return new Set<string>()
  }
}

function persistCollapsedGroups() {
  localStorage.setItem(SIDEBAR_COLLAPSED_GROUPS_KEY, JSON.stringify([...collapsedGroups.value]))
}

const collapsedGroups = ref<Set<string>>(loadCollapsedGroups())

const activeAgentId = computed(() => {
  const session = sessionsStore.sessions.find(s => s.id === sessionsStore.currentSessionId)
  return session?.agent_id || 'chat'
})

const normalizedQuery = computed(() => searchQuery.value.trim().toLowerCase())

const filteredSessions = computed(() => {
  const query = normalizedQuery.value
  if (!query) return sessionsStore.sessions.slice()
  return sessionsStore.sessions.filter(session =>
    (session.title || '新对话').toLowerCase().includes(query),
  )
})

function getVisibleCount(agentId: string) {
  return visibleCountByAgent.value[agentId] ?? DEFAULT_VISIBLE_COUNT
}

function compareSessions(a: Session, b: Session) {
  if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1

  const pinnedA = a.pinned_at ? new Date(a.pinned_at).getTime() : 0
  const pinnedB = b.pinned_at ? new Date(b.pinned_at).getTime() : 0
  if (pinnedA !== pinnedB) return pinnedB - pinnedA

  return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
}

const renderedGroups = computed<SidebarGroup[]>(() => {
  const buckets = new Map<string, Session[]>()

  for (const session of filteredSessions.value) {
    const agentId = session.agent_id || 'chat'
    const list = buckets.get(agentId) || []
    list.push(session)
    buckets.set(agentId, list)
  }

  const groups = [...buckets.entries()]
    .map(([agentId, sessions]) => {
      const agentInfo = agentsStore.agents.find(a => a.id === agentId)
      const agentName = agentsStore.getAgentName(agentId)
      const sorted = sessions.slice().sort(compareSessions)
      const visibleCount = getVisibleCount(agentId)
      const totalCount = sessionsStore.sessions.filter(s => (s.agent_id || 'chat') === agentId).length
      const lastActivityAt = sorted.length > 0 ? new Date(sorted[0].updated_at).getTime() : 0
      return {
        agentId,
        agentName,
        agentIcon: getAgentIcon(agentInfo ?? null),
        agentSource: (agentInfo?.source ?? 'deleted') as SidebarGroup['agentSource'],
        isProjectMode: agentInfo?.project_mode ?? false,
        lastActivityAt,
        badgeText: normalizedQuery.value ? `${sorted.length}/${totalCount}` : String(sorted.length),
        visibleSessions: sorted.slice(0, visibleCount),
        hiddenCount: Math.max(sorted.length - visibleCount, 0),
      }
    })

  if (frozenOrder.value === null && groups.length > 0) {
    frozenOrder.value = groups
      .slice()
      .sort((a, b) => {
        if (a.lastActivityAt !== b.lastActivityAt) return b.lastActivityAt - a.lastActivityAt
        return a.agentName.localeCompare(b.agentName, 'zh-CN')
      })
      .map(group => group.agentId)
  }

  const order = frozenOrder.value ?? []
  return groups.slice().sort((a, b) => {
    const ia = order.indexOf(a.agentId)
    const ib = order.indexOf(b.agentId)
    if (ia === -1 && ib === -1) return a.agentName.localeCompare(b.agentName, 'zh-CN')
    if (ia === -1) return 1
    if (ib === -1) return -1
    return ia - ib
  })
})

const allCollapsed = computed(() => {
  const groupNames = renderedGroups.value.map(group => group.agentName)
  return groupNames.length > 0 && groupNames.every(name => collapsedGroups.value.has(name))
})

const collapseDefaultsApplied = ref(false)

watch(normalizedQuery, () => {
  visibleCountByAgent.value = {}
  openMenuSessionId.value = null
})

watch(renderedGroups, groups => {
  const groupNames = new Set(groups.map(group => group.agentName))
  const next = new Set([...collapsedGroups.value].filter(name => groupNames.has(name)))
  if (!collapseDefaultsApplied.value && groups.length > 0) {
    for (const group of groups) {
      if (group.agentId === activeAgentId.value) next.delete(group.agentName)
      else next.add(group.agentName)
    }
    collapseDefaultsApplied.value = true
  }
  if (next.size !== collapsedGroups.value.size || [...next].some(name => !collapsedGroups.value.has(name))) {
    collapsedGroups.value = next
    persistCollapsedGroups()
  }
}, { immediate: true })

watch(() => sessionsStore.currentSessionId, async (sessionId) => {
  if (!sessionId || props.collapsed) return
  const session = sessionsStore.sessions.find(item => item.id === sessionId)
  if (!session) return

  if (normalizedQuery.value) {
    searchQuery.value = ''
  }

  const agentName = agentsStore.getAgentName(session.agent_id || 'chat')
  const nextCollapsedGroups = new Set(collapsedGroups.value)
  nextCollapsedGroups.delete(agentName)
  collapsedGroups.value = nextCollapsedGroups
  persistCollapsedGroups()

  const sortedSessions = sessionsStore.sessions
    .filter(item => (item.agent_id || 'chat') === (session.agent_id || 'chat'))
    .sort(compareSessions)
  const sessionIndex = sortedSessions.findIndex(item => item.id === sessionId)
  if (sessionIndex >= getVisibleCount(session.agent_id || 'chat')) {
    visibleCountByAgent.value = {
      ...visibleCountByAgent.value,
      [session.agent_id || 'chat']: sessionIndex + 1,
    }
  }

  await nextTick()
  const target = sessionListRef.value?.querySelector<HTMLElement>(`[data-session-id="${sessionId}"]`)
  target?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
})

function toggleGroup(title: string) {
  const next = new Set(collapsedGroups.value)
  if (next.has(title)) {
    next.delete(title)
  } else {
    next.add(title)
  }
  collapsedGroups.value = next
  persistCollapsedGroups()
}

function toggleAllGroups() {
  const groupNames = renderedGroups.value.map(group => group.agentName)
  if (groupNames.length === 0) return

  if (allCollapsed.value) {
    collapsedGroups.value = new Set([...collapsedGroups.value].filter(name => !groupNames.includes(name)))
  } else {
    collapsedGroups.value = new Set([...collapsedGroups.value, ...groupNames])
  }
  persistCollapsedGroups()
}

function showMore(agentId: string) {
  visibleCountByAgent.value = {
    ...visibleCountByAgent.value,
    [agentId]: getVisibleCount(agentId) + LOAD_MORE_COUNT,
  }
}

function handleSessionSelect(id: string) {
  openMenuSessionId.value = null
  emit('switchSession', id)
}

function toggleSessionMenu(id: string) {
  openMenuSessionId.value = openMenuSessionId.value === id ? null : id
}

async function handleRename(id: string, title: string) {
  openMenuSessionId.value = null
  const result = await ElMessageBox.prompt('输入新的会话标题', '重命名会话', {
    inputValue: title,
    confirmButtonText: '保存',
    cancelButtonText: '取消',
  }).catch(() => null)

  if (!result) return
  const nextTitle = result.value.trim()
  if (!nextTitle) return
  await sessionsStore.updateTitle(id, nextTitle)
}

async function handleDelete(id: string) {
  openMenuSessionId.value = null
  const confirmed = await ElMessageBox.confirm('确认删除该会话吗？', '删除会话', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  }).catch(() => null)

  if (!confirmed) return
  await sessionsStore.deleteSession(id)
  // 会话已删：若它正是主区打开的标签，交由 App 切到相邻标签或回首页
  emit('closeSessionTab', id)
}

async function handleTogglePinned(session: Session) {
  openMenuSessionId.value = null
  await sessionsStore.setPinned(session.id, !session.is_pinned)
}

function handleDocumentClick(event: MouseEvent) {
  const target = event.target as HTMLElement | null
  if (!target?.closest('.session-item-meta')) {
    openMenuSessionId.value = null
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<style scoped>
.left-sidebar {
  width: 312px;
  --sidebar-agent-card-bg: color-mix(in srgb, var(--el-bg-color-overlay) 78%, var(--el-fill-color-light));
  --sidebar-agent-card-border: var(--el-border-color-lighter);
  --sidebar-agent-card-active-border: color-mix(in srgb, var(--el-color-primary) 62%, var(--el-border-color));
  --sidebar-agent-card-active-bg: color-mix(in srgb, var(--el-color-primary-light-9) 82%, var(--el-bg-color));
  --sidebar-agent-card-active-ring: color-mix(in srgb, var(--el-color-primary) 18%, transparent);
  --sidebar-agent-card-count-bg: var(--el-fill-color-light);
  --sidebar-agent-card-count-color: var(--el-text-color-secondary);
  --sidebar-session-hover-bg: color-mix(in srgb, var(--el-color-success) 16%, var(--el-bg-color-overlay));
  --sidebar-session-hover-color: var(--el-text-color-primary);
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:global(html.dark) .left-sidebar {
  --sidebar-agent-card-bg: color-mix(in srgb, var(--el-bg-color-overlay) 82%, white 4%);
  --sidebar-agent-card-border: color-mix(in srgb, var(--el-border-color) 76%, white 8%);
  --sidebar-agent-card-active-border: color-mix(in srgb, var(--el-color-primary) 72%, white 8%);
  --sidebar-agent-card-active-bg: color-mix(in srgb, var(--el-color-primary) 14%, var(--el-bg-color-overlay));
  --sidebar-agent-card-active-ring: color-mix(in srgb, var(--el-color-primary) 24%, transparent);
  --sidebar-agent-card-count-bg: color-mix(in srgb, var(--el-fill-color) 84%, white 8%);
  --sidebar-agent-card-count-color: var(--el-text-color-regular);
  --sidebar-session-hover-bg: color-mix(in srgb, var(--el-color-success) 30%, #10261d);
  --sidebar-session-hover-color: #f8fafc;
}

.left-sidebar.collapsed {
  width: 68px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--el-border-color);
}

.sidebar-brand-wrap {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.sidebar-brand {
  font-size: 14px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  letter-spacing: 0.3px;
}

/* Chats / 文件 视图切换：与右侧面板 tab 同一套渐变胶囊设计语言 */
.view-switch {
  display: flex;
  width: 100%;
  min-width: 0;
  gap: 3px;
  padding: 3px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 14px;
  background: color-mix(in srgb, var(--el-fill-color) 90%, var(--el-bg-color) 10%);
}

.view-switch-btn {
  flex: 1;
  min-width: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  min-height: 28px;
  padding: 4px 8px;
  border: 1px solid transparent;
  border-radius: 11px;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.2px;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.view-switch-btn:hover:not(.active) {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
  transform: translateY(-1px);
}

/* 视图切换区域色相：天蓝，与面板 tab 紫色、文件标签翠绿区分 */
.view-switch-btn.active {
  background: linear-gradient(135deg, #0ea5e9, #06b6d4);
  color: #fff;
  border-color: rgba(14, 165, 233, 0.6);
  box-shadow: 0 2px 10px rgba(14, 165, 233, 0.35);
}

.view-switch-icon {
  flex-shrink: 0;
  width: 13px;
  height: 13px;
}

.sidebar-files {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 10px 8px 12px;
}

/* 嵌入侧栏的文件树：去掉卡片外壳，与 Chats 视图的搜索框风格对齐 */
.sidebar-files :deep(.file-tree-panel .panel-section) {
  margin-bottom: 10px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
}

.sidebar-files :deep(.file-tree-panel .tree-toolbar-row) {
  padding: 0 2px;
  margin-bottom: 2px;
}

.sidebar-files :deep(.file-tree-panel .tree-search-input) {
  height: 34px;
  border-radius: 8px;
}

.sidebar-files :deep(.file-tree-panel .tree-search-input:focus) {
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--el-color-primary) 18%, transparent);
}

.sidebar-files :deep(.file-tree-panel .tree-scroll) {
  padding: 0;
}

.mobile-only-brand {
  display: none;
}

.desktop-only-brand {
  display: inline;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn,
.toggle-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.15s ease;
}

.action-btn:hover,
.toggle-btn:hover {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

.toggle-icon {
  display: inline-block;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.toggle-icon.flipped {
  transform: rotate(180deg);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 6px 12px;
}

.sidebar-search {
  padding: 6px 4px 12px;
}

.sidebar-search-input {
  width: 100%;
  height: 34px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
  padding: 0 12px;
  outline: none;
}

.sidebar-search-input:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--el-color-primary) 18%, transparent);
}

.session-tree {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.agent-section {
  border: 1px solid var(--sidebar-agent-card-border);
  border-left: 3px solid var(--sidebar-agent-card-border);
  border-radius: 10px;
  background: var(--sidebar-agent-card-bg);
  overflow: visible;
  transition: border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
}

/* Source-based left accent color */
.agent-src-user    { border-left-color: var(--el-color-primary-light-4); }
.agent-src-code    { border-left-color: var(--el-color-warning-light-3); }
.agent-src-builtin { border-left-color: var(--el-color-success-light-4); }
.agent-src-deleted { border-left-color: var(--el-text-color-placeholder); opacity: 0.8; }

.agent-section.is-active-agent {
  border-color: var(--sidebar-agent-card-active-border);
  border-left-color: var(--el-color-primary);
  box-shadow: 0 0 0 1px var(--sidebar-agent-card-active-ring);
  background: var(--sidebar-agent-card-active-bg);
}

.agent-section-header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 10px;
  border: none;
  border-radius: 8px 8px 0 0;
  background: transparent;
  cursor: pointer;
  font-weight: 700;
  color: var(--el-text-color-primary);
  text-align: left;
  transition: background 0.13s;
}

.agent-section-header:hover {
  background: color-mix(in srgb, var(--el-fill-color-light) 60%, transparent);
}

.is-active-agent .agent-section-header {
  color: var(--el-color-primary);
}

.is-active-agent .agent-group-name {
  color: var(--el-color-primary);
}

.agent-group-arrow {
  font-size: 9px;
  color: var(--el-text-color-secondary);
  transition: transform 0.2s ease;
  transform: rotate(90deg);
  flex-shrink: 0;
}

.agent-group-arrow.collapsed {
  transform: rotate(0deg);
}

.agent-group-icon {
  font-size: 13px;
  flex-shrink: 0;
  line-height: 1;
}

.agent-group-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}


.agent-card-count {
  font-size: 10px;
  font-weight: 600;
  line-height: 15px;
  color: var(--sidebar-agent-card-count-color);
  background: var(--sidebar-agent-card-count-bg);
  padding: 0 5px;
  border-radius: 8px;
  flex-shrink: 0;
}

/* 数量徽标与「+」紧贴在一起，避免名字被右侧动作区挤掉 */
.agent-section-actions {
  position: relative;
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

/* 「+」只在悬停时出现，因此不该常驻占位：绝对定位贴到数量徽标左侧 */
.agent-new-chat-btn {
  position: absolute;
  top: 50%;
  right: calc(100% + 3px);
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.13s ease, background 0.13s ease, color 0.13s ease;
}

.agent-section-header:hover .agent-new-chat-btn,
.agent-section-header:focus-within .agent-new-chat-btn {
  opacity: 1;
  pointer-events: auto;
}

/* 「+」浮在名字末尾，把滑到它下方的文字渐隐，避免压字 */
.agent-section-header:hover .agent-group-name,
.agent-section-header:focus-within .agent-group-name {
  -webkit-mask-image: linear-gradient(to right, #000 calc(100% - 22px), transparent);
  mask-image: linear-gradient(to right, #000 calc(100% - 22px), transparent);
}

.agent-new-chat-btn:hover {
  background: var(--el-fill-color);
  color: var(--el-color-primary);
}

.agent-section.is-active-agent .agent-new-chat-btn:hover {
  color: var(--el-color-primary);
}

/* 触摸屏没有 hover：「+」回到文档流常驻，否则新建会话点不出来 */
@media (hover: none) {
  .agent-section-actions {
    gap: 4px;
  }

  .agent-new-chat-btn {
    position: static;
    transform: none;
    opacity: 1;
    pointer-events: auto;
  }

  .agent-section-header .agent-group-name {
    -webkit-mask-image: none;
    mask-image: none;
  }
}

.session-children {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 2px;
  padding-right: 6px;
  padding-bottom: 10px;
  padding-left: 12px;
}

.session-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 6px 6px 6px 8px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--el-text-color-regular);
  font-size: 12px;
}

.session-item:hover {
  background: var(--sidebar-session-hover-bg);
  color: var(--sidebar-session-hover-color);
}

.session-item.is-active {
  background: var(--sidebar-agent-card-active-bg);
  color: var(--el-color-primary);
  font-weight: 600;
}

.session-item.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 4px;
  bottom: 4px;
  width: 3px;
  border-radius: 2px;
  background: var(--el-color-primary);
}

.session-pin-indicator {
  flex-shrink: 0;
  font-size: 12px;
}

/* 运行中指示器：带彗尾的旋转弧，比原来的小圆点更醒目 */
.session-streaming-spinner {
  position: relative;
  flex-shrink: 0;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  /* 外发光放在父层：弧线那层会被 mask 裁掉发光，不能放一起 */
  background: radial-gradient(
    circle,
    color-mix(in srgb, var(--el-color-primary) 38%, transparent) 0%,
    transparent 70%
  );
}

.session-streaming-spinner::after {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  /* 缺口留在右上方，旋转起来像高速甩动的彗尾 */
  background: conic-gradient(
    from 0deg,
    transparent 0deg,
    color-mix(in srgb, var(--el-color-primary) 40%, transparent) 110deg,
    var(--el-color-primary) 300deg,
    var(--el-color-primary) 360deg
  );
  /* 挖空中心，只留约 2.5px 宽的弧线 */
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 2.5px), #000 calc(100% - 2.5px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 2.5px), #000 calc(100% - 2.5px));
  content: '';
  animation: streaming-spinner-rotate 0.6s linear infinite;
}

@keyframes streaming-spinner-rotate {
  to { transform: rotate(360deg); }
}

.session-completed-badge {
  display: grid;
  width: 15px;
  height: 15px;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--el-color-success) 72%, var(--el-border-color));
  border-radius: 50%;
  background: color-mix(in srgb, var(--el-color-success) 18%, transparent);
  box-shadow: 0 0 12px color-mix(in srgb, var(--el-color-success) 56%, transparent);
  color: var(--el-color-success);
  font-size: 10px;
  font-weight: 800;
  flex-shrink: 0;
  animation: completed-badge-arrival 0.9s ease-out both;
}

@keyframes streaming-status-ring {
  0% { transform: scale(0.42); opacity: 0.95; }
  75%, 100% { transform: scale(1.35); opacity: 0; }
}

@keyframes completed-badge-arrival {
  0% { transform: scale(0.35) rotate(-20deg); opacity: 0; }
  60% { transform: scale(1.18) rotate(4deg); opacity: 1; }
  100% { transform: scale(1) rotate(0); opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
  .session-streaming-spinner::after,
  .session-completed-badge {
    animation: none;
  }
}

.session-item-title {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-item-meta {
  position: absolute;
  top: 50%;
  right: 4px;
  z-index: 1;
  display: flex;
  align-items: center;
  opacity: 0;
  pointer-events: none;
  transform: translateY(-50%);
  transition: opacity 0.13s ease;
}

.session-item:hover .session-item-meta,
.session-item.is-menu-open .session-item-meta,
.session-item:focus-within .session-item-meta {
  opacity: 1;
  pointer-events: auto;
}

/* 按钮浮在行尾，把滑到它下方的标题文字渐隐，避免压字 */
.session-item:hover .session-item-title,
.session-item.is-menu-open .session-item-title,
.session-item:focus-within .session-item-title {
  -webkit-mask-image: linear-gradient(to right, #000 calc(100% - 34px), transparent);
  mask-image: linear-gradient(to right, #000 calc(100% - 34px), transparent);
}

/* 触摸屏没有 hover，按钮需常驻，否则会话操作无法触发 */
@media (hover: none) {
  .session-item-meta {
    opacity: 1;
    pointer-events: auto;
  }

  .session-item-title {
    -webkit-mask-image: linear-gradient(to right, #000 calc(100% - 34px), transparent);
    mask-image: linear-gradient(to right, #000 calc(100% - 34px), transparent);
  }
}

.session-action-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.session-action-btn:hover {
  background: color-mix(in srgb, var(--el-fill-color-light) 88%, transparent);
}

.session-menu {
  position: absolute;
  top: calc(100% - 4px);
  right: 0;
  z-index: 10;
  display: flex;
  flex-direction: column;
  min-width: 112px;
  padding: 6px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color-overlay);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
}

.session-menu button {
  border: none;
  background: transparent;
  color: var(--el-text-color-primary);
  text-align: left;
  padding: 7px 8px;
  border-radius: 6px;
  cursor: pointer;
}

.session-menu button:hover {
  background: var(--el-fill-color-light);
}

.show-more-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 4px;
  padding: 5px 10px;
  border: 1px dashed var(--el-border-color-lighter);
  border-radius: 6px;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  font-size: 12px;
  width: 100%;
  transition: all 0.15s;
}

.show-more-btn:hover {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
  border-color: var(--el-border-color-light);
}

.show-more-icon {
  font-size: 11px;
  opacity: 0.7;
}

.show-more-hint {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-left: auto;
}

.empty-state {
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.sidebar-footer {
  flex-shrink: 0;
  padding: 6px 12px 10px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.settings-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.settings-btn:hover {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

.settings-icon {
  font-size: 14px;
  line-height: 1;
}

.settings-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.settings-arrow {
  font-size: 12px;
  opacity: 0.55;
  flex-shrink: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 900px) {
  .left-sidebar,
  .left-sidebar.collapsed {
    width: min(86vw, 340px);
    max-width: 86vw;
    height: 100%;
  }

  .sidebar-header {
    padding: 10px 12px;
  }

  .mobile-only-brand {
    display: inline;
  }

  .desktop-only-brand {
    display: none;
  }

  .session-list {
    padding: 6px 6px 12px;
  }

  .session-tree {
    gap: 8px;
  }
}
</style>
