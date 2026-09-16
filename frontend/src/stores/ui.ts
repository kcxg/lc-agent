import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { useAgentsStore } from '@/stores/agents'
import { useFileChangesStore } from '@/stores/file-changes'

export type RightPanelTab = 'model' | 'abilities' | 'changes' | 'editor' | 'tasks'

export const RIGHT_PANEL_TABS: RightPanelTab[] = ['model', 'abilities', 'changes', 'editor', 'tasks']

const ACTIVE_TAB_KEY = 'lc-agent:right-panel:activeTab'

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
    setActiveTab,
    requestTab,
  }
})
