import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export interface NavStackEntry {
  session_id: string
  label: string
}

const OPEN_TABS_KEY = 'lc-agent:session-tabs:open'
const ACTIVE_TAB_KEY = 'lc-agent:session-tabs:active'

function loadPersisted<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return fallback
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

function savePersisted(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* ignore */
  }
}

export const useSessionTabsStore = defineStore('sessionTabs', () => {
  const openTabIds = ref<string[]>(loadPersisted<string[]>(OPEN_TABS_KEY, []))
  const activeTabId = ref<string | null>(loadPersisted<string | null>(ACTIVE_TAB_KEY, null))

  // 子会话导航栈按标签隔离：切标签各自保留钻取深度，避免 A 标签显示 B 的子会话
  const navStacks = ref<Record<string, NavStackEntry[]>>({})

  // 只在用户显式 push/pop 子会话时自增。标签切换只是换 activeTabId，不自增，
  // 因此 ChatView 不会把「切回一个钻取中的标签」误判成新钻取而重新拉消息。
  const navStackRevision = ref(0)

  // 会话切换「数据加载完成」的信号，由 App 在 await switchToSession 之后自增。
  // ChatView 依此决定是恢复滚动位置、还是恢复子会话视图——比监听 currentSessionId
  // 可靠，因为后者会早于消息加载完成触发。
  const switchCompletionRevision = ref(0)

  const activeNavStack = computed<NavStackEntry[]>(() =>
    activeTabId.value ? (navStacks.value[activeTabId.value] ?? []) : [],
  )

  watch(openTabIds, (ids) => savePersisted(OPEN_TABS_KEY, ids), { deep: true })
  watch(activeTabId, (id) => savePersisted(ACTIVE_TAB_KEY, id))

  function isTabOpen(id: string): boolean {
    return openTabIds.value.includes(id)
  }

  function setActiveTab(id: string | null): void {
    activeTabId.value = id
  }

  /** 打开标签并激活；已打开则只激活（去重） */
  function openTab(id: string): void {
    if (!openTabIds.value.includes(id)) {
      openTabIds.value = [...openTabIds.value, id]
    }
    activeTabId.value = id
  }

  /**
   * 关闭标签，返回关闭后应激活的标签 id（右邻 → 左邻 → 最后一个）。
   * 关的不是当前标签时，激活项不变，返回当前激活项。
   */
  function closeTab(id: string): string | null {
    const idx = openTabIds.value.indexOf(id)
    if (idx < 0) return activeTabId.value

    const remaining = openTabIds.value.filter(item => item !== id)
    openTabIds.value = remaining
    delete navStacks.value[id]

    if (activeTabId.value !== id) return activeTabId.value
    if (remaining.length === 0) {
      activeTabId.value = null
      return null
    }
    const next = remaining[Math.min(idx, remaining.length - 1)]
    activeTabId.value = next
    return next
  }

  /** 会话被删除时移除标签与导航栈 */
  function removeTab(id: string): void {
    closeTab(id)
  }

  /**
   * 关闭除 keepId 外的全部标签，返回被关闭的 id 列表。
   * 只动标签不动会话数据；调用方需按返回列表释放各 store 的缓存。
   */
  function closeOthers(keepId: string): string[] {
    if (!openTabIds.value.includes(keepId)) return []
    const removed = openTabIds.value.filter(id => id !== keepId)
    if (removed.length === 0) return []
    openTabIds.value = [keepId]
    for (const id of removed) delete navStacks.value[id]
    activeTabId.value = keepId
    return removed
  }

  /** 关闭 keepId 右侧的全部标签，返回被关闭的 id 列表；激活项若被关则落到 keepId */
  function closeToRight(keepId: string): string[] {
    const idx = openTabIds.value.indexOf(keepId)
    if (idx < 0) return []
    const removed = openTabIds.value.slice(idx + 1)
    if (removed.length === 0) return []
    openTabIds.value = openTabIds.value.slice(0, idx + 1)
    for (const id of removed) delete navStacks.value[id]
    if (activeTabId.value && removed.includes(activeTabId.value)) {
      activeTabId.value = keepId
    }
    return removed
  }

  /** 关闭全部标签，返回被关闭的 id 列表；激活项置空（调用方负责回首页） */
  function closeAll(): string[] {
    const removed = [...openTabIds.value]
    if (removed.length === 0) return []
    openTabIds.value = []
    navStacks.value = {}
    activeTabId.value = null
    return removed
  }

  /**
   * 「新对话」落库后本地 id 会换成真实 id，标签、激活项、导航栈必须一起搬迁，
   * 否则标签会指向一个不存在的会话。
   */
  function renameTab(oldId: string, newId: string): void {
    if (oldId === newId) return
    openTabIds.value = openTabIds.value.map(item => (item === oldId ? newId : item))
    if (activeTabId.value === oldId) activeTabId.value = newId
    if (navStacks.value[oldId]) {
      navStacks.value[newId] = navStacks.value[oldId]
      delete navStacks.value[oldId]
    }
  }

  /** 启动时恢复持久化标签，剔除已被删除的会话 */
  function restoreTabs(validSessionIds: string[]): void {
    const valid = new Set(validSessionIds)
    const kept = openTabIds.value.filter(id => valid.has(id))
    openTabIds.value = kept
    if (activeTabId.value && !valid.has(activeTabId.value)) {
      activeTabId.value = kept.length > 0 ? kept[kept.length - 1] : null
    }
    const nextStacks: Record<string, NavStackEntry[]> = {}
    for (const id of kept) {
      if (navStacks.value[id]) nextStacks[id] = navStacks.value[id]
    }
    navStacks.value = nextStacks
  }

  function setActiveNavStack(stack: NavStackEntry[]): void {
    if (!activeTabId.value) return
    navStacks.value[activeTabId.value] = stack
  }

  function bumpNavRevision(): void {
    navStackRevision.value += 1
  }

  /** App 完成一次会话切换后调用，通知 ChatView 恢复该会话的视图状态 */
  function notifySwitchCompleted(): void {
    switchCompletionRevision.value += 1
  }

  return {
    openTabIds,
    activeTabId,
    activeNavStack,
    navStackRevision,
    switchCompletionRevision,
    isTabOpen,
    setActiveTab,
    openTab,
    closeTab,
    removeTab,
    closeOthers,
    closeToRight,
    closeAll,
    renameTab,
    restoreTabs,
    setActiveNavStack,
    bumpNavRevision,
    notifySwitchCompleted,
  }
})
