import { computed, readonly, ref, watch } from 'vue'

export type MarkdownThemeId = 'github' | 'notion' | 'aurora' | 'neon' | 'obsidian' | 'paper' | 'lime' | 'sky' | 'candy' | 'solar'

export interface MarkdownThemeOption {
  id: MarkdownThemeId
  label: string
  description: string
  accent: string
}

export const MARKDOWN_THEME_OPTIONS: MarkdownThemeOption[] = [
  { id: 'github', label: 'Arctic Blue', description: '冰蓝银白的冷调高级风', accent: '#38bdf8' },
  { id: 'notion', label: 'Cyber Mint', description: '薄荷青绿的玻璃科技风', accent: '#2dd4bf' },
  { id: 'aurora', label: 'Aurora Blast', description: '亮紫电蓝的极光炫彩风', accent: '#a855f7' },
  { id: 'neon', label: 'Neon Future', description: '高亮霓虹科技演示风', accent: '#22d3ee' },
  { id: 'obsidian', label: 'Sunset Chrome', description: '橙红玫瑰金的暖色金属风', accent: '#fb7185' },
  { id: 'paper', label: 'Paper Luxe', description: '高级纸张阅读器风', accent: '#b7791f' },
  { id: 'lime', label: 'Lime Surge', description: '电光青柠的能量科技风', accent: '#a3e635' },
  { id: 'sky', label: 'Prism White', description: '银白棱镜的高亮彩光风', accent: '#c4b5fd' },
  { id: 'candy', label: 'Lava Pulse', description: '黑红熔岩的高能冲击风', accent: '#ef4444' },
  { id: 'solar', label: 'Solar Flare', description: '太阳耀斑的亮黄橙金风', accent: '#facc15' },
]

const STORAGE_KEY = 'lc-agent:markdown-theme'
const DEFAULT_THEME: MarkdownThemeId = 'aurora'
const validThemeIds = new Set<MarkdownThemeId>(MARKDOWN_THEME_OPTIONS.map(option => option.id))
const markdownTheme = ref<MarkdownThemeId>(loadInitialTheme())

function isMarkdownThemeId(value: string | null): value is MarkdownThemeId {
  return Boolean(value && validThemeIds.has(value as MarkdownThemeId))
}

function loadInitialTheme(): MarkdownThemeId {
  if (typeof window === 'undefined') return DEFAULT_THEME
  const stored = window.localStorage.getItem(STORAGE_KEY)
  return isMarkdownThemeId(stored) ? stored : DEFAULT_THEME
}

function applyMarkdownTheme(theme: MarkdownThemeId) {
  if (typeof document === 'undefined') return
  document.documentElement.dataset.mdTheme = theme
}

export function useMarkdownTheme() {
  const currentOption = computed(() => (
    MARKDOWN_THEME_OPTIONS.find(option => option.id === markdownTheme.value) || MARKDOWN_THEME_OPTIONS[0]
  ))

  function setMarkdownTheme(theme: MarkdownThemeId) {
    if (!validThemeIds.has(theme)) return
    markdownTheme.value = theme
  }

  watch(markdownTheme, theme => {
    applyMarkdownTheme(theme)
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, theme)
    }
  }, { immediate: true })

  return {
    markdownTheme,
    markdownThemeOptions: readonly(MARKDOWN_THEME_OPTIONS),
    currentOption,
    setMarkdownTheme,
  }
}
