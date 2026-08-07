import { computed, readonly, ref, watch } from 'vue'

export type MarkdownThemeId = 'mist-blue' | 'sage' | 'graphite' | 'warm-gray' | 'rosewood' | 'paper' | 'sepia' | 'slate' | 'ocean-ink' | 'night-ink'

export interface MarkdownThemeOption {
  id: MarkdownThemeId
  label: string
  description: string
  accent: string
}

export const MARKDOWN_THEME_OPTIONS: MarkdownThemeOption[] = [
  { id: 'mist-blue', label: 'Mist Blue', description: '低饱和雾蓝的清爽阅读', accent: '#6d8ca2' },
  { id: 'sage', label: 'Sage', description: '柔和鼠尾草绿的长文阅读', accent: '#718a78' },
  { id: 'graphite', label: 'Graphite', description: '中性石墨灰的通用默认', accent: '#687b89' },
  { id: 'warm-gray', label: 'Warm Gray', description: '暖灰与浅褐的低刺激层次', accent: '#8c7e70' },
  { id: 'rosewood', label: 'Rosewood', description: '低饱和玫瑰木与灰粉', accent: '#97727a' },
  { id: 'paper', label: 'Paper', description: '自然纸张与柔和墨色', accent: '#9a876a' },
  { id: 'sepia', label: 'Sepia', description: '克制棕褐的纸本阅读', accent: '#9a7757' },
  { id: 'slate', label: 'Slate', description: '冷静石板蓝灰', accent: '#71849a' },
  { id: 'ocean-ink', label: 'Ocean Ink', description: '深海墨蓝与青灰', accent: '#5f8893' },
  { id: 'night-ink', label: 'Night Ink', description: '低亮度夜墨蓝灰', accent: '#6f8190' },
]

const STORAGE_KEY = 'lc-agent:markdown-theme'
const DEFAULT_THEME: MarkdownThemeId = 'graphite'
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
