import { computed, readonly, ref, watch } from 'vue'

export type MarkdownLayoutId =
  | 'github-docs'
  | 'notion-editorial'
  | 'obsidian-reading'
  | 'typora-paper'
  | 'gitbook-guides'
  | 'vitepress-technical'
  | 'docusaurus-docs'
  | 'hackmd-collaboration'
  | 'stackedit-focus'
  | 'joplin-notes'

export interface MarkdownLayoutOption {
  id: MarkdownLayoutId
  label: string
  description: string
}

export const MARKDOWN_LAYOUT_OPTIONS: MarkdownLayoutOption[] = [
  { id: 'github-docs', label: 'GitHub Docs', description: '紧凑清晰的文档站层级' },
  { id: 'notion-editorial', label: 'Notion Editorial', description: '字体与页宽优先的块级阅读' },
  { id: 'obsidian-reading', label: 'Obsidian Reading', description: 'CSS 变量驱动的舒展长文阅读' },
  { id: 'typora-paper', label: 'Typora Paper', description: '克制干净的纸面排版' },
  { id: 'gitbook-guides', label: 'GitBook Guides', description: '字体与代码面板分离的知识库阅读' },
  { id: 'vitepress-technical', label: 'VitePress Technical', description: 'Inter 回退栈下的紧凑技术文档' },
  { id: 'docusaurus-docs', label: 'Docusaurus Docs', description: '桌面与移动断点明确的说明阅读' },
  { id: 'hackmd-collaboration', label: 'HackMD Collaboration', description: '受协作 Markdown 工作流启发的节奏' },
  { id: 'stackedit-focus', label: 'StackEdit Focus', description: '受双栏编辑预览启发的聚焦阅读' },
  { id: 'joplin-notes', label: 'Joplin Notes', description: '可定制 Markdown 笔记本式层级' },
]

const STORAGE_KEY = 'lc-agent:markdown-layout'
const DEFAULT_LAYOUT: MarkdownLayoutId = 'notion-editorial'
const validLayoutIds = new Set<MarkdownLayoutId>(MARKDOWN_LAYOUT_OPTIONS.map(option => option.id))
const markdownLayout = ref<MarkdownLayoutId>(loadInitialLayout())

function isMarkdownLayoutId(value: string | null): value is MarkdownLayoutId {
  return Boolean(value && validLayoutIds.has(value as MarkdownLayoutId))
}

function loadInitialLayout(): MarkdownLayoutId {
  if (typeof window === 'undefined') return DEFAULT_LAYOUT
  const stored = window.localStorage.getItem(STORAGE_KEY)
  return isMarkdownLayoutId(stored) ? stored : DEFAULT_LAYOUT
}

function applyMarkdownLayout(layout: MarkdownLayoutId) {
  if (typeof document === 'undefined') return
  document.documentElement.dataset.mdLayout = layout
}

export function useMarkdownLayout() {
  const currentLayoutOption = computed(() => (
    MARKDOWN_LAYOUT_OPTIONS.find(option => option.id === markdownLayout.value) || MARKDOWN_LAYOUT_OPTIONS[0]
  ))

  function setMarkdownLayout(layout: MarkdownLayoutId) {
    if (!validLayoutIds.has(layout)) return
    markdownLayout.value = layout
  }

  watch(markdownLayout, layout => {
    applyMarkdownLayout(layout)
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, layout)
    }
  }, { immediate: true })

  return {
    markdownLayout,
    markdownLayoutOptions: readonly(MARKDOWN_LAYOUT_OPTIONS),
    currentLayoutOption,
    setMarkdownLayout,
  }
}
