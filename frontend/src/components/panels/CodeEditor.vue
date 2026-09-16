<template>
  <div ref="hostRef" class="code-editor-host" :class="{ 'is-readonly': !editable }" />
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { EditorState, type Extension } from '@codemirror/state'
import { EditorView } from '@codemirror/view'
import { basicSetup } from 'codemirror'
import { oneDark } from '@codemirror/theme-one-dark'
import { search as searchExt, SearchQuery, setSearchQuery, getSearchQuery } from '@codemirror/search'
import { python } from '@codemirror/lang-python'
import { javascript } from '@codemirror/lang-javascript'
import { json } from '@codemirror/lang-json'
import { markdown as langMarkdown } from '@codemirror/lang-markdown'
import { html } from '@codemirror/lang-html'
import { css } from '@codemirror/lang-css'
import { java } from '@codemirror/lang-java'
import { cpp } from '@codemirror/lang-cpp'
import { rust } from '@codemirror/lang-rust'

const props = defineProps<{
  code: string
  language: string
  editable: boolean
  /** 超大文件：关闭语法高亮，保证打开速度 */
  heavy?: boolean
}>()

const emit = defineEmits<{ (e: 'update:code', value: string): void }>()

const hostRef = ref<HTMLDivElement | null>(null)
let view: EditorView | null = null

function languageExtension(): Extension | null {
  if (props.heavy) return null
  switch (props.language) {
    case 'python': return python()
    case 'javascript': return javascript()
    case 'typescript': return javascript({ typescript: true })
    case 'json': return json()
    case 'markdown': return langMarkdown()
    case 'html': case 'xml': case 'vue': return html()
    case 'css': return css()
    case 'java': return java()
    case 'c': case 'cpp': return cpp()
    case 'rust': return rust()
    default: return null
  }
}

// 与原 hljs 代码区同一套深色视觉：底色跟随 --md-code-bg，字号/行高/字体保持一致
const themeExt = EditorView.theme({
  '&': {
    height: '100%',
    fontSize: '12px',
    backgroundColor: 'var(--md-code-bg, #0d1117)',
  },
  '.cm-scroller': {
    fontFamily: "'Cascadia Code', 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace",
    lineHeight: '1.65',
    overflow: 'auto',
  },
  '.cm-gutters': {
    backgroundColor: 'transparent',
    border: 'none',
    color: 'color-mix(in srgb, var(--md-code-text, #d8fff0) 34%, transparent)',
  },
  '.cm-activeLine': { backgroundColor: 'rgba(255, 255, 255, 0.045)' },
  '.cm-activeLineGutter': { backgroundColor: 'rgba(255, 255, 255, 0.06)' },
  '&.cm-focused': { outline: 'none' },
  '.cm-content': { paddingBottom: '28px', caretColor: '#34d399' },
  '.cm-selectionBackground': { backgroundColor: 'rgba(52, 211, 153, 0.22) !important' },
})

onMounted(() => {
  const langExt = languageExtension()
  const extensions: Extension[] = [
    basicSetup,
    // search 状态必须显式启用，setSearchQuery effect 才会生效
    searchExt(),
    ...(langExt ? [langExt] : []),
    oneDark,
    themeExt,
    EditorState.readOnly.of(!props.editable),
    EditorView.editable.of(props.editable),
    EditorView.updateListener.of((u) => {
      if (u.docChanged) emit('update:code', u.state.doc.toString())
    }),
  ]
  view = new EditorView({
    state: EditorState.create({ doc: props.code, extensions }),
    parent: hostRef.value!,
  })
})

onBeforeUnmount(() => {
  view?.destroy()
  view = null
})

// 外部内容变化（刷新/冲突后重载）同步进编辑器；自身输入回流时内容相同则跳过，避免死循环
watch(() => props.code, (next) => {
  if (!view) return
  const current = view.state.doc.toString()
  if (next !== current) {
    view.dispatch({ changes: { from: 0, to: current.length, insert: next } })
  }
})

function jumpToLine(line: number) {
  if (!view) return
  const total = view.state.doc.lines
  const target = Math.min(Math.max(1, line), total)
  const info = view.state.doc.line(target)
  view.dispatch({
    selection: { anchor: info.from },
    effects: EditorView.scrollIntoView(info.from, { y: 'center' }),
  })
  view.focus()
}

/** 设置搜索词并返回匹配总数；后续用 gotoMatchIndex 在匹配间跳转 */
function search(query: string): number {
  if (!view) return 0
  const q = new SearchQuery({ search: query, caseSensitive: false })
  view.dispatch({ effects: setSearchQuery.of(q) })
  const total = countMatches(view, q)
  // 命中时先把视图落到第一个匹配上，计数与光标位置保持一致
  if (total > 0) matchIndexAt(view, 0)
  return total
}

/** 统计当前文档里该查询的匹配总数 */
function countMatches(target: EditorView, query: SearchQuery): number {
  let count = 0
  const cursor = query.getCursor(target.state)
  let step = cursor.next()
  while (!step.done) {
    count++
    step = cursor.next()
  }
  return count
}

/** 把视图落到第 index 个匹配（0 起），返回匹配总数；越界或查询非法返回 0 */
function matchIndexAt(target: EditorView, index: number): number {
  const query = getSearchQuery(target.state)
  if (!query.valid) return 0
  const total = countMatches(target, query)
  if (!total || index < 0 || index >= total) return 0
  const cursor = query.getCursor(target.state)
  for (let i = 0, step = cursor.next(); !step.done; step = cursor.next(), i++) {
    if (i !== index) continue
    const { from, to } = step.value
    target.dispatch({
      selection: { anchor: from, head: to },
      effects: EditorView.scrollIntoView(from, { y: 'center' }),
    })
    return total
  }
  return 0
}

/**
 * 跳到第 index 个匹配（0 起），返回 { found, total }。
 * 环绕由调用方计算，这样「1/2」的计数与视图共用同一个下标。
 */
function gotoMatchIndex(index: number): { found: boolean; total: number } {
  if (!view) return { found: false, total: 0 }
  const total = matchIndexAt(view, index)
  return { found: total > 0, total }
}

/** 当前选区信息：文本与首尾行号（1 起）。无选区或全空白返回 null */
function getSelectionInfo(): { text: string; startLine: number; endLine: number } | null {
  if (!view) return null
  const sel = view.state.selection.main
  if (sel.empty) return null
  const text = view.state.sliceDoc(sel.from, sel.to)
  if (!text.trim()) return null
  const startLine = view.state.doc.lineAt(sel.from).number
  let endLine = view.state.doc.lineAt(sel.to).number
  // 选区恰好停在末行行首（选中了整行含换行符）时，不该把下一行算进来
  if (endLine > startLine && view.state.doc.lineAt(sel.to).from === sel.to) endLine--
  return { text, startLine, endLine }
}

defineExpose({
  jumpToLine,
  search,
  gotoMatchIndex,
  getSelectionInfo,
  focus: () => view?.focus(),
})
</script>

<style scoped>
.code-editor-host {
  height: 100%;
  min-height: 0;
}

/* 只读文件整体降一点亮度，与可编辑状态形成区分 */
.code-editor-host.is-readonly :deep(.cm-content) {
  color: color-mix(in srgb, var(--md-code-text, #d8fff0) 80%, transparent);
}

/* 深色代码底上全局灰色滚动条几乎不可见，改用明亮天蓝色（滚动容器是 .cm-scroller） */
.code-editor-host :deep(.cm-scroller) {
  scrollbar-color: #38bdf8 rgba(56, 189, 248, 0.1);
}

.code-editor-host :deep(.cm-scroller)::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.code-editor-host :deep(.cm-scroller)::-webkit-scrollbar-track {
  background: rgba(56, 189, 248, 0.1);
  border-radius: 999px;
}

.code-editor-host :deep(.cm-scroller)::-webkit-scrollbar-thumb {
  background: #38bdf8;
  border-radius: 999px;
  min-height: 40px;
}

.code-editor-host :deep(.cm-scroller)::-webkit-scrollbar-thumb:hover {
  background: #7dd3fc;
}

.code-editor-host :deep(.cm-scroller)::-webkit-scrollbar-thumb:active {
  background: #0ea5e9;
}

.code-editor-host :deep(.cm-scroller)::-webkit-scrollbar-corner {
  background: transparent;
}
</style>
