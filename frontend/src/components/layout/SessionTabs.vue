<template>
  <div v-if="tabs.length > 0" class="session-tabs">
    <div ref="barRef" class="session-tabs-bar" role="tablist" aria-label="已打开的会话">
      <div
        v-for="tab in tabs"
        :key="tab.id"
        class="session-tab"
        :class="{ 'is-active': tab.id === activeTabId }"
        role="tab"
        :aria-selected="tab.id === activeTabId"
        :title="tab.title"
        @click="emit('activate', tab.id)"
        @auxclick.middle.prevent="emit('close', tab.id)"
        @contextmenu.prevent="openTabMenu($event, tab.id)"
      >
        <span
          v-if="tab.streaming"
          class="session-tab-spinner"
          title="正在生成中"
        />
        <span
          v-else-if="tab.unseen"
          class="session-tab-dot is-unseen"
          title="已完成，尚未查看"
        />
        <!-- 置顶标识：与侧边栏的置顶状态同源，便于在标签栏直接看出哪些已置顶 -->
        <svg v-if="tab.pinned" class="session-tab-pin" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z" fill="currentColor" />
        </svg>
        <span class="session-tab-title">{{ tab.title }}</span>
        <button
          type="button"
          class="session-tab-close"
          :aria-label="`关闭 ${tab.title}`"
          title="关闭标签"
          @click.stop="emit('close', tab.id)"
        >
          <svg viewBox="0 0 12 12" aria-hidden="true">
            <path
              d="M3.2 3.2l5.6 5.6M8.8 3.2l-5.6 5.6"
              fill="none"
              stroke="currentColor"
              stroke-width="1.6"
              stroke-linecap="round"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- 标签右键菜单：teleport 到 body，复用全局 .code-ctx-menu 样式 -->
    <teleport to="body">
      <div
        v-if="menuVisible"
        ref="menuEl"
        class="code-ctx-menu"
        :style="menuStyle"
        role="menu"
        @contextmenu.prevent
      >
        <button class="code-ctx-item" role="menuitem" @click="menuClose">关闭</button>
        <button class="code-ctx-item" role="menuitem" @click="menuCloseOthers">关闭其他</button>
        <button class="code-ctx-item" role="menuitem" @click="menuCloseToRight">关闭右侧</button>
        <button class="code-ctx-item" role="menuitem" @click="menuCloseAll">关闭全部</button>
        <button class="code-ctx-item" role="menuitem" @click="menuTogglePin">
          {{ menuTab?.pinned ? '取消置顶' : '置顶' }}
        </button>
        <button class="code-ctx-item" role="menuitem" @click="menuRename">重命名</button>
        <button class="code-ctx-item is-danger" role="menuitem" @click="menuDelete">删除</button>
      </div>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import { useSessionsStore } from '@/stores/sessions'
import { useSessionTabsStore } from '@/stores/session-tabs'

interface TabView {
  id: string
  title: string
  streaming: boolean
  unseen: boolean
  pinned: boolean
}

const emit = defineEmits<{
  activate: [id: string]
  close: [id: string]
  // 批量关闭只上报意图，由 App 统一做标签与资源释放，避免绕过缓存清理
  closeOthers: [id: string]
  closeToRight: [id: string]
  closeAll: []
  // 会话已删除，交由 App 善后主区（与侧边栏删除同一入口）
  delete: [id: string]
}>()

const chatStore = useChatStore()
const sessionsStore = useSessionsStore()
const tabsStore = useSessionTabsStore()

const activeTabId = computed(() => tabsStore.activeTabId)
const barRef = ref<HTMLElement | null>(null)

const tabs = computed<TabView[]>(() =>
  tabsStore.openTabIds.map((id) => {
    const session = sessionsStore.sessions.find(s => s.id === id)
    return {
      id,
      title: session?.title || '新对话',
      streaming: chatStore.isSessionStreaming(id),
      unseen: sessionsStore.isCompletedUnseen(id),
      pinned: !!session?.is_pinned,
    }
  }),
)

// ---- 右键菜单 ----
const menuVisible = ref(false)
const menuX = ref(0)
const menuY = ref(0)
// 用 id 而非对象快照，菜单项始终读最新会话状态（置顶文案要跟着变）
const menuTabId = ref('')
const menuEl = ref<HTMLElement | null>(null)

const menuTab = computed(() => tabs.value.find(t => t.id === menuTabId.value) ?? null)
const menuStyle = computed(() => ({ left: `${menuX.value}px`, top: `${menuY.value}px` }))

function openTabMenu(e: MouseEvent, id: string) {
  const MENU_W = 176
  // 7 个菜单项，与 .code-ctx-item 的行高一致
  const MENU_H = 7 * 31 + 8
  menuTabId.value = id
  menuX.value = Math.min(e.clientX, window.innerWidth - MENU_W - 8)
  menuY.value = Math.min(e.clientY, window.innerHeight - MENU_H - 8)
  menuVisible.value = true
}

function closeTabMenu() {
  menuVisible.value = false
}

// 动作统一先取走 id 并关菜单，避免异步确认框期间菜单残留
function menuClose() {
  const id = menuTabId.value
  closeTabMenu()
  if (id) emit('close', id)
}

function menuCloseOthers() {
  const id = menuTabId.value
  closeTabMenu()
  if (id) emit('closeOthers', id)
}

function menuCloseToRight() {
  const id = menuTabId.value
  closeTabMenu()
  if (id) emit('closeToRight', id)
}

function menuCloseAll() {
  closeTabMenu()
  emit('closeAll')
}

/** 置顶/取消置顶：复用侧边栏同一入口，状态两边同源 */
async function menuTogglePin() {
  const tab = menuTab.value
  closeTabMenu()
  if (!tab) return
  await sessionsStore.setPinned(tab.id, !tab.pinned)
}

async function menuRename() {
  const tab = menuTab.value
  closeTabMenu()
  if (!tab) return
  const result = await ElMessageBox.prompt('输入新的会话标题', '重命名会话', {
    inputValue: tab.title,
    confirmButtonText: '保存',
    cancelButtonText: '取消',
  }).catch(() => null)
  if (!result) return
  const nextTitle = result.value.trim()
  if (!nextTitle) return
  await sessionsStore.updateTitle(tab.id, nextTitle)
}

/** 删除会话：与侧边栏一致，warning 二次确认后删除 */
async function menuDelete() {
  const tab = menuTab.value
  closeTabMenu()
  if (!tab) return
  const confirmed = await ElMessageBox.confirm('确认删除该会话吗？', '删除会话', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  }).catch(() => null)
  if (!confirmed) return
  // deleteSession 内部已摘除标签，随后上报让 App 释放缓存并切换主区
  await sessionsStore.deleteSession(tab.id)
  emit('delete', tab.id)
}

function onDocumentPointerDown(e: MouseEvent) {
  const target = e.target
  if (menuEl.value && target instanceof Node && menuEl.value.contains(target)) return
  closeTabMenu()
}

function onDocumentKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') closeTabMenu()
}

function onWindowResize() {
  closeTabMenu()
}

onMounted(() => {
  document.addEventListener('pointerdown', onDocumentPointerDown)
  document.addEventListener('keydown', onDocumentKeydown)
  window.addEventListener('resize', onWindowResize)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocumentPointerDown)
  document.removeEventListener('keydown', onDocumentKeydown)
  window.removeEventListener('resize', onWindowResize)
})

/** 激活标签变化时滚进可视区，避免激活的标签被挤在可视范围外 */
watch(activeTabId, async () => {
  await nextTick()
  const bar = barRef.value
  if (!bar) return
  const el = bar.querySelector<HTMLElement>('.session-tab.is-active')
  if (!el) return
  const left = el.offsetLeft
  const right = left + el.offsetWidth
  const viewLeft = bar.scrollLeft
  const viewRight = viewLeft + bar.clientWidth
  if (left < viewLeft) {
    bar.scrollLeft = left
  } else if (right > viewRight) {
    bar.scrollLeft = right - bar.clientWidth
  }
})
</script>

<style scoped>
.session-tabs {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  padding: 6px 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
}

.session-tabs-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
  padding: 4px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 14px;
  background: color-mix(in srgb, var(--el-fill-color) 90%, var(--el-bg-color) 10%);
  overflow-x: auto;
  scrollbar-width: thin;
}

.session-tabs-bar::-webkit-scrollbar {
  height: 6px;
}

.session-tabs-bar::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: var(--el-border-color);
}

.session-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  max-width: 220px;
  min-height: 30px;
  padding: 4px 6px 4px 10px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
}

.session-tab:hover:not(.is-active) {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

/* 会话标签区域色相：靛蓝（与顶栏 Agents管理 一致），与文件标签翠绿、面板 tab 紫色区分 */
.session-tab.is-active {
  background: linear-gradient(135deg, #4f46e5, #6366f1);
  color: #fff;
  border-color: rgba(79, 70, 229, 0.6);
  box-shadow: 0 2px 10px rgba(79, 70, 229, 0.35);
}

.session-tab-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-tab-dot {
  flex-shrink: 0;
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

/* 置顶标识：与文件标签的图钉同一造型，激活态继承白色 */
.session-tab-pin {
  flex-shrink: 0;
  width: 11px;
  height: 11px;
  opacity: 0.85;
}

/* 与侧边栏一致：带彗尾的旋转弧。固定用 success 绿，
   因为在非激活标签上是浅底、在激活标签上是蓝色渐变底，两种底色都要能看清 */
.session-tab-spinner {
  position: relative;
  flex-shrink: 0;
  width: 11px;
  height: 11px;
  border-radius: 50%;
  color: var(--el-color-success);
  background: radial-gradient(circle, color-mix(in srgb, currentColor 34%, transparent) 0%, transparent 70%);
}

.session-tab-spinner::after {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: conic-gradient(
    from 0deg,
    transparent 0deg,
    color-mix(in srgb, currentColor 40%, transparent) 110deg,
    currentColor 300deg,
    currentColor 360deg
  );
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 2px), #000 calc(100% - 2px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 2px), #000 calc(100% - 2px));
  content: '';
  animation: session-tab-spin 0.6s linear infinite;
}

@keyframes session-tab-spin {
  to { transform: rotate(360deg); }
}

.session-tab-dot.is-unseen {
  background: var(--el-color-warning);
}

@media (prefers-reduced-motion: reduce) {
  .session-tab-spinner::after { animation: none; }
}

.session-tab-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: inherit;
  cursor: pointer;
  opacity: 0.6;
  transition: background 0.15s ease, opacity 0.15s ease;
}

.session-tab-close svg {
  width: 11px;
  height: 11px;
}

.session-tab-close:hover {
  background: color-mix(in srgb, currentColor 22%, transparent);
  opacity: 1;
}
</style>

<style>
/* 右键菜单 teleport 到 body，菜单容器样式来自 FileEditorPane 的全局 .code-ctx-*；
   这里只补「删除」这类危险项的颜色变体 */
.code-ctx-item.is-danger {
  color: var(--el-color-danger);
}

.code-ctx-item.is-danger:hover {
  background: color-mix(in srgb, var(--el-color-danger) 12%, transparent);
  color: var(--el-color-danger);
}
</style>
