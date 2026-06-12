<template>
  <aside class="left-sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <transition name="fade">
        <span v-if="!collapsed" class="sidebar-brand">Chats</span>
      </transition>
      <button class="toggle-btn" @click="emit('toggleCollapse')" :title="collapsed ? '展开侧边栏' : '收起侧边栏'">
        <span class="toggle-icon" :class="{ flipped: collapsed }">«</span>
      </button>
    </div>

    <button class="new-chat-btn" :class="{ 'icon-only': collapsed }" @click="emit('newChat')" title="新对话">
      <span class="btn-icon">+</span>
      <transition name="fade">
        <span v-if="!collapsed" class="btn-text">新对话</span>
      </transition>
    </button>

    <div v-if="!collapsed" class="session-scroll">
      <div v-for="group in sessionsStore.groupedByAgent" :key="group.agentId" class="agent-group">
        <div class="agent-group-header" @click="toggleGroup(group.agentId)">
          <span class="chevron" :class="{ expanded: !collapsedGroups[group.agentId] }">›</span>
          <span class="agent-dot" :class="`dot-${group.agentSource}`" />
          <span class="agent-name">{{ group.agentName }}</span>
          <span class="source-tag" :class="`tag-${group.agentSource}`">
            {{ group.agentSource === 'builtin' ? '内置' : group.agentSource === 'code' ? '代码' : '自建' }}
          </span>
          <span class="session-count">{{ group.sessions.length }}</span>
        </div>
        <transition name="slide">
          <div v-show="!collapsedGroups[group.agentId]" class="agent-group-body">
            <div
              v-for="session in group.sessions"
              :key="session.id"
              class="session-item"
              :class="{ active: session.id === sessionsStore.currentSessionId }"
              @click="emit('switchSession', session.id)"
              @contextmenu.prevent="openMenu($event, session)"
            >
              <template v-if="renaming === session.id">
                <input
                  class="rename-input"
                  v-model="renameInput"
                  @keyup.enter="confirmRename(session.id)"
                  @keyup.escape="cancelRename"
                  @blur="confirmRename(session.id)"
                />
              </template>
              <template v-else>
                <span class="session-title">{{ session.title }}</span>
                <span class="session-time">{{ formatTime(session.updated_at) }}</span>
              </template>
            </div>
          </div>
        </transition>
      </div>

      <div v-if="!sessionsStore.sessions.length" class="empty-state">
        <span class="empty-icon">💬</span>
        <span class="empty-text">暂无会话</span>
      </div>
    </div>

    <teleport to="body">
      <div v-if="menuVisible" class="menu-backdrop" @click="closeMenu" />
      <div
        v-if="menuVisible"
        class="context-menu"
        :style="{ left: menuPosition.x + 'px', top: menuPosition.y + 'px' }"
      >
        <div class="menu-item" @click="startRename">
          <span class="menu-icon">✏️</span> 重命名
        </div>
        <div class="menu-divider" />
        <div class="menu-item menu-item-danger" @click="deleteTarget">
          <span class="menu-icon">🗑️</span> 删除
        </div>
      </div>
    </teleport>
  </aside>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from 'vue'
import { useSessionsStore, type Session } from '@/stores/sessions'

defineProps<{ collapsed: boolean }>()

const sessionsStore = useSessionsStore()
const emit = defineEmits<{ newChat: []; switchSession: [id: string]; toggleCollapse: [] }>()

const collapsedGroups = reactive<Record<string, boolean>>({})
const menuVisible = ref(false)
const menuPosition = ref({ x: 0, y: 0 })
const menuTarget = ref<Session | null>(null)
const renaming = ref<string | null>(null)
const renameInput = ref('')

function toggleGroup(agentId: string) {
  collapsedGroups[agentId] = !collapsedGroups[agentId]
}

function openMenu(event: MouseEvent, session: Session) {
  menuTarget.value = session
  menuPosition.value = { x: event.clientX, y: event.clientY }
  menuVisible.value = true
}

function closeMenu() {
  menuVisible.value = false
  menuTarget.value = null
}

function startRename() {
  if (!menuTarget.value) return
  renaming.value = menuTarget.value.id
  renameInput.value = menuTarget.value.title
  closeMenu()
  nextTick(() => {
    const input = document.querySelector('.rename-input') as HTMLInputElement
    input?.focus()
    input?.select()
  })
}

async function confirmRename(sessionId: string) {
  if (renameInput.value.trim()) {
    await sessionsStore.updateTitle(sessionId, renameInput.value.trim())
  }
  renaming.value = null
}

function cancelRename() {
  renaming.value = null
}

async function deleteTarget() {
  if (!menuTarget.value) return
  const id = menuTarget.value.id
  const wasCurrent = id === sessionsStore.currentSessionId
  closeMenu()
  await sessionsStore.deleteSession(id)
  if (wasCurrent) {
    if (sessionsStore.sessions.length > 0) {
      emit('switchSession', sessionsStore.sessions[0].id)
    } else {
      emit('newChat')
    }
  }
}

function formatTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}天前`
  return new Date(iso).toLocaleDateString()
}
</script>

<style scoped>
.left-sidebar {
  width: 270px;
  background: linear-gradient(180deg, rgba(15, 20, 30, 0.85) 0%, rgba(10, 14, 22, 0.92) 100%);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.left-sidebar.collapsed {
  width: 56px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 14px 8px;
  flex-shrink: 0;
}

.sidebar-brand {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.5px;
  background: linear-gradient(135deg, #58a6ff 0%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.toggle-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--lc-text-secondary);
  cursor: pointer;
  font-size: 16px;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--lc-text-primary);
}

.toggle-icon {
  display: inline-block;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.toggle-icon.flipped {
  transform: rotate(180deg);
}

.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 4px 12px 16px;
  padding: 10px 16px;
  border: 1px solid rgba(88, 166, 255, 0.25);
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(88, 166, 255, 0.1) 0%, rgba(167, 139, 250, 0.08) 100%);
  color: #7ec8ff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
  flex-shrink: 0;
}

.new-chat-btn:hover {
  background: linear-gradient(135deg, rgba(88, 166, 255, 0.18) 0%, rgba(167, 139, 250, 0.14) 100%);
  border-color: rgba(88, 166, 255, 0.4);
  box-shadow: 0 0 16px rgba(88, 166, 255, 0.15);
  transform: translateY(-1px);
}

.new-chat-btn.icon-only {
  margin: 4px 8px 16px;
  padding: 10px;
  border-radius: 12px;
}

.btn-icon {
  font-size: 16px;
  font-weight: 300;
  line-height: 1;
}

.btn-text {
  white-space: nowrap;
}

.session-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 12px;
}

.agent-group {
  margin-bottom: 6px;
}

.agent-group-header {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 10px;
  transition: all 0.2s ease;
  user-select: none;
  background: linear-gradient(135deg, rgba(88, 166, 255, 0.08) 0%, rgba(167, 139, 250, 0.06) 100%);
  border: 1px solid rgba(88, 166, 255, 0.15);
  margin-bottom: 4px;
}

.agent-group-header:hover {
  background: linear-gradient(135deg, rgba(88, 166, 255, 0.14) 0%, rgba(167, 139, 250, 0.1) 100%);
  border-color: rgba(88, 166, 255, 0.25);
  box-shadow: 0 2px 12px rgba(88, 166, 255, 0.08);
}

.chevron {
  font-size: 13px;
  color: rgba(167, 139, 250, 0.7);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  width: 14px;
  text-align: center;
}

.chevron.expanded {
  transform: rotate(90deg);
}

.agent-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-builtin {
  background: linear-gradient(135deg, #58a6ff, #a78bfa);
  box-shadow: 0 0 6px rgba(88, 166, 255, 0.4);
}

.dot-code {
  background: linear-gradient(135deg, #ffb832, #ff8c00);
  box-shadow: 0 0 6px rgba(255, 180, 50, 0.4);
}

.dot-user {
  background: linear-gradient(135deg, #6ee77a, #3fb950);
  box-shadow: 0 0 6px rgba(63, 185, 80, 0.4);
}

.source-tag {
  font-size: 9px;
  padding: 1px 5px;
  border-radius: 4px;
  font-weight: 500;
  flex-shrink: 0;
}

.tag-builtin {
  background: rgba(88, 166, 255, 0.12);
  color: #58a6ff;
}

.tag-code {
  background: rgba(255, 180, 50, 0.12);
  color: #ffb832;
}

.tag-user {
  background: rgba(63, 185, 80, 0.12);
  color: #6ee77a;
}

.agent-name {
  font-size: 12px;
  font-weight: 600;
  background: linear-gradient(135deg, #a0d2ff 0%, #c4b5fd 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  flex: 1;
}

.session-count {
  font-size: 10px;
  color: rgba(167, 139, 250, 0.8);
  background: rgba(167, 139, 250, 0.1);
  border: 1px solid rgba(167, 139, 250, 0.2);
  padding: 2px 7px;
  border-radius: 10px;
  font-weight: 500;
}

.agent-group-body {
  padding-left: 6px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 9px 12px;
  margin: 2px 0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
  transition: all 0.2s ease;
  border: 1px solid transparent;
  position: relative;
  background: rgba(255, 255, 255, 0.02);
}

.session-item:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.08);
  color: var(--lc-text-primary);
}

.session-item.active {
  background: rgba(56, 189, 248, 0.08);
  border-color: rgba(56, 189, 248, 0.2);
  color: var(--lc-text-primary);
}

.session-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  border-radius: 0 3px 3px 0;
  background: linear-gradient(180deg, #38bdf8, #a78bfa);
}

.session-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 8px;
  line-height: 1.3;
}

.session-time {
  font-size: 10px;
  color: var(--lc-text-secondary);
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.session-item:hover .session-time {
  opacity: 1;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 16px;
  opacity: 0.5;
}

.empty-icon {
  font-size: 28px;
}

.empty-text {
  font-size: 12px;
  color: var(--lc-text-secondary);
}

.rename-input {
  width: 100%;
  padding: 5px 10px;
  font-size: 13px;
  border: 1px solid rgba(88, 166, 255, 0.4);
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.4);
  color: var(--lc-text-primary);
  outline: none;
  box-shadow: 0 0 12px rgba(88, 166, 255, 0.1);
}

.rename-input:focus {
  border-color: rgba(88, 166, 255, 0.6);
  box-shadow: 0 0 16px rgba(88, 166, 255, 0.2);
}

.slide-enter-active, .slide-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
.slide-enter-from, .slide-leave-to {
  max-height: 0;
  opacity: 0;
}
.slide-enter-to, .slide-leave-from {
  max-height: 500px;
  opacity: 1;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>

<style>
.context-menu {
  position: fixed;
  z-index: 9999;
  background: rgba(18, 22, 30, 0.96);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), 0 0 1px rgba(255, 255, 255, 0.1);
  padding: 5px;
  min-width: 140px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 13px;
  border-radius: 6px;
  cursor: pointer;
  color: var(--lc-text-primary);
  transition: background 0.15s ease;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.menu-item-danger {
  color: #f87171;
}

.menu-item-danger:hover {
  background: rgba(248, 113, 113, 0.1);
}

.menu-icon {
  font-size: 14px;
}

.menu-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.06);
  margin: 3px 8px;
}

.menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9998;
}
</style>
