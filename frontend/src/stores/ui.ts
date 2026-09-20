import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { useAgentsStore } from '@/stores/agents'
import { useFileChangesStore } from '@/stores/file-changes'

export type RightPanelTab = 'model' | 'abilities' | 'changes' | 'editor' | 'tasks'

export const RIGHT_PANEL_TABS: RightPanelTab[] = ['model', 'abilities', 'changes', 'editor', 'tasks']

export type SidebarView = 'chats' | 'files'

const ACTIVE_TAB_KEY = 'lc-agent:right-panel:activeTab:v2'

function loadActiveTab(): RightPanelTab {
  try {
    const raw = localStorage.getItem(ACTIVE_TAB_KEY)
    if (raw && (RIGHT_PANEL_TABS as string[]).includes(raw)) return raw as RightPanelTab
  } catch { /* ignore */ }
  return 'model'
}

export const useUiStore = defineStore('ui', () => {
  const activeTab = ref<RightPanelTab>(loadActiveTab())
  // 收起状态下被请求切 tab 时，App.vue 依此展开右侧面板
  const rightPanelOpenRequest = ref(0)
  // 左侧栏视图：会话列表 / 项目文件树。编辑器「定位」、面包屑点击等外部入口也会切它
  const sidebarView = ref<SidebarView>('chats')
  // 侧栏收起时被请求切到文件树，App.vue 依此展开左侧面板
  const sidebarOpenRequest = ref(0)

  watch(activeTab, (tab) => {
    try {
      localStorage.setItem(ACTIVE_TAB_KEY, tab)
    } catch { /* ignore */ }
  })

  const agentsStore = useAgentsStore()
  watch(() => agentsStore.currentAgentId, () => {
    activeTab.value = 'model'
  })

  function setActiveTab(tab: RightPanelTab) {
    activeTab.value = tab
  }

  function setSidebarView(view: SidebarView) {
    sidebarView.value = view
  }

  // 跨组件入口：编辑器「定位」/ 面包屑点击 → 展示项目文件树（侧栏收起时一并展开）。
  // 非项目模式没有文件树可看，直接不动，否则会被 LeftSidebar 的守卫立刻弹回会话列表
  function requestFileTree() {
    if (!agentsStore.currentAgent?.project_mode) return
    sidebarView.value = 'files'
    sidebarOpenRequest.value += 1
  }

  // 跨组件入口：Header Badge / 轮次卡片 / 工具卡片 都通过它切到指定 tab
  function requestTab(tab: RightPanelTab, target?: { round?: number | null; filePath?: string }) {
    if (tab === 'changes' && target) {
      const fileChangesStore = useFileChangesStore()
      if (target.round !== undefined) fileChangesStore.selectedRound = target.round
      if (target.filePath) fileChangesStore.pendingOpenFile = target.filePath
    }
    activeTab.value = tab
    rightPanelOpenRequest.value += 1
  }

  return {
    activeTab,
    rightPanelOpenRequest,
    sidebarView,
    sidebarOpenRequest,
    setActiveTab,
    setSidebarView,
    requestFileTree,
    requestTab,
  }
})
