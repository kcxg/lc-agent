<template>
  <teleport to="body">
    <div v-if="visible" class="code-modal-backdrop" @click="$emit('close')">
      <div class="code-modal" role="dialog" aria-modal="true" @click.stop>
        <div class="code-modal-header">
          <div class="code-modal-title-wrap">
            <span class="code-modal-kicker">{{ kicker || '源码' }}</span>
            <span class="code-modal-title">{{ title || language }}</span>
          </div>
          <div class="code-modal-actions">
            <button class="code-modal-action-btn" @click="copyCode">{{ copyLabel }}</button>
            <button class="code-modal-close" aria-label="关闭" @click="$emit('close')">✕</button>
          </div>
        </div>
        <div class="code-modal-toolbar">
          <input
            ref="searchInputRef"
            v-model="searchQuery"
            class="code-search-input"
            type="text"
            placeholder="搜索关键字..."
            @keydown.enter.prevent="jumpToNextMatch"
          />
          <div class="code-search-actions">
            <span v-if="searchQuery" class="code-search-count">{{ activeMatchLabel }}</span>
            <button class="code-search-btn" :disabled="!matchCount" @click="jumpToPrevMatch">↑</button>
            <button class="code-search-btn" :disabled="!matchCount" @click="jumpToNextMatch">↓</button>
          </div>
        </div>
        <div class="code-modal-content" @contextmenu="handleContextMenu" @scroll="closeMenu">
          <div v-if="!renderAsMarkdown" class="code-modal-code">
            <div class="code-gutter" aria-hidden="true">{{ lineNumbers }}</div>
            <pre ref="preRef" class="code-modal-pre hljs"><code ref="contentRef" class="hljs" /></pre>
          </div>
          <div v-else ref="contentRef" class="code-modal-markdown markdown-body" />
        </div>
      </div>
    </div>
  </teleport>

  <teleport to="body">
    <div
      v-if="menuVisible"
      ref="menuEl"
      class="code-ctx-menu"
      :style="menuStyle"
      role="menu"
      @contextmenu.prevent
    >
      <button class="code-ctx-item" role="menuitem" @click="copySelection">复制</button>
      <template v-if="hasSourcePath">
        <button class="code-ctx-item" role="menuitem" @click="copyLineRef">复制行号</button>
        <button class="code-ctx-item" role="menuitem" @click="copyLineRefWithContent">复制行号和内容</button>
      </template>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import hljs from 'highlight.js'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps<{
  visible: boolean
  code: string
  language: string
  title?: string
  kicker?: string
  renderAsMarkdown?: boolean
  // 文件绝对路径。提供后才显示「复制行号 / 复制行号和内容」。
  sourcePath?: string
}>()

defineEmits<{ close: [] }>()

const searchQuery = ref('')
const activeMatchIndex = ref(0)
const matchCount = ref(0)
const contentRef = ref<HTMLElement | null>(null)
const searchInputRef = ref<HTMLInputElement | null>(null)
const copyLabel = ref('复制')

// 行号栏只在代码（非 Markdown）渲染时出现
const lineNumbers = computed(() => {
  if (props.renderAsMarkdown) return ''
  const total = props.code.split('\n').length
  return Array.from({ length: total }, (_, i) => i + 1).join('\n')
})

// 复制行号需要真实文件路径，且仅在代码视图下行号可推算
const hasSourcePath = computed(() => !!props.sourcePath && !props.renderAsMarkdown)

const menuVisible = ref(false)
const menuX = ref(0)
const menuY = ref(0)
const menuEl = ref<HTMLElement | null>(null)

const menuStyle = computed(() => ({ left: `${menuX.value}px`, top: `${menuY.value}px` }))

function closeMenu() {
  menuVisible.value = false
}

function handleContextMenu(e: MouseEvent) {
  const sel = window.getSelection()
  // 无选中内容时不接管原生菜单
  if (!sel || sel.isCollapsed || !sel.toString().trim()) return

  e.preventDefault()
  const MENU_W = 176
  const MENU_H = hasSourcePath.value ? 116 : 44
  menuX.value = Math.min(e.clientX, window.innerWidth - MENU_W - 8)
  menuY.value = Math.min(e.clientY, window.innerHeight - MENU_H - 8)
  menuVisible.value = true
}

// 从选区反推覆盖的源码行号（highlight 不改变文本，故可按换行数计数）
function selectionLineRange(): { start: number; end: number } | null {
  const contentEl = contentRef.value
  const sel = window.getSelection()
  if (!contentEl || !sel || sel.rangeCount === 0) return null

  const range = sel.getRangeAt(0)
  if (!contentEl.contains(range.startContainer) || !contentEl.contains(range.endContainer)) return null

  const text = range.toString()
  if (!text.trim()) return null

  const probe = document.createRange()
  probe.selectNodeContents(contentEl)
  probe.setEnd(range.startContainer, range.startOffset)
  const start = (probe.toString().match(/\n/g)?.length ?? 0) + 1

  probe.setEnd(range.endContainer, range.endOffset)
  const covered = probe.toString()
  const newlines = covered.match(/\n/g)?.length ?? 0
  const end = Math.max(start, newlines + (text.endsWith('\n') ? 0 : 1))

  return { start, end }
}

function lineRefLabel(): string | null {
  const lines = selectionLineRange()
  if (!lines || !props.sourcePath) return null
  const span = lines.start === lines.end ? `L${lines.start}` : `L${lines.start}-${lines.end}`
  return `${props.sourcePath}#${span}`
}

function selectionText(): string {
  return window.getSelection()?.toString() ?? ''
}

async function copySelection() {
  const text = selectionText()
  if (text) await writeClipboard(text)
  closeMenu()
}

async function copyLineRef() {
  const label = lineRefLabel()
  if (label) await writeClipboard(label)
  closeMenu()
}

async function copyLineRefWithContent() {
  const label = lineRefLabel()
  const text = selectionText()
  if (label && text) await writeClipboard(`${label}\n\n${text}`)
  closeMenu()
}

async function writeClipboard(text: string) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.left = '-9999px'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
  } catch {
    // 剪贴板不可用时静默失败，避免打断阅读
  }
}

// 点击其他区域 / 按 Esc 关闭右键菜单
function onDocumentPointerDown(e: MouseEvent) {
  const menu = menuEl.value
  if (menu && e.target instanceof Node && menu.contains(e.target)) return
  closeMenu()
}

function onDocumentKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') closeMenu()
}

onMounted(() => {
  document.addEventListener('pointerdown', onDocumentPointerDown)
  document.addEventListener('keydown', onDocumentKeydown)
  window.addEventListener('resize', closeMenu)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocumentPointerDown)
  document.removeEventListener('keydown', onDocumentKeydown)
  window.removeEventListener('resize', closeMenu)
})

const renderedContent = computed(() => {
  if (props.renderAsMarkdown) return renderMarkdown(props.code)

  const lang = props.language.toLowerCase()
  if (lang && lang !== 'text' && hljs.getLanguage(lang)) {
    return hljs.highlight(props.code, { language: lang }).value
  }
  return escapeHtml(props.code)
})

const activeMatchLabel = computed(() => {
  if (!matchCount.value) return '0/0'
  return `${activeMatchIndex.value + 1}/${matchCount.value}`
})

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

async function copyCode() {
  if (!props.code) return
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(props.code)
    } else {
      const ta = document.createElement('textarea')
      ta.value = props.code
      ta.style.position = 'fixed'
      ta.style.left = '-9999px'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    copyLabel.value = '已复制'
  } catch {
    copyLabel.value = '复制失败'
  }
  setTimeout(() => { copyLabel.value = '复制' }, 1400)
}

function applyMarks() {
  const contentEl = contentRef.value
  if (!contentEl) return

  contentEl.innerHTML = renderedContent.value

  const query = searchQuery.value.trim()
  if (!query) {
    matchCount.value = 0
    return
  }

  const regex = new RegExp(escapeRegExp(query), 'gi')
  const walker = document.createTreeWalker(contentEl, NodeFilter.SHOW_TEXT)
  const textNodes: Text[] = []
  let n: Node | null
  while ((n = walker.nextNode())) textNodes.push(n as Text)

  for (const tn of textNodes) {
    const text = tn.textContent || ''
    regex.lastIndex = 0
    const hits: { s: number; e: number }[] = []
    let m: RegExpExecArray | null
    while ((m = regex.exec(text))) hits.push({ s: m.index, e: m.index + m[0].length })
    if (!hits.length) continue

    const frag = document.createDocumentFragment()
    let last = 0
    for (const h of hits) {
      if (h.s > last) frag.appendChild(document.createTextNode(text.slice(last, h.s)))
      const mark = document.createElement('mark')
      mark.className = 'code-search-hit'
      mark.textContent = text.slice(h.s, h.e)
      frag.appendChild(mark)
      last = h.e
    }
    if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)))
    tn.parentNode!.replaceChild(frag, tn)
  }

  const allMarks = contentEl.querySelectorAll('mark.code-search-hit')
  matchCount.value = allMarks.length
  syncActive()
}

function syncActive() {
  const contentEl = contentRef.value
  if (!contentEl) return
  const marks = contentEl.querySelectorAll('mark.code-search-hit')
  marks.forEach((m, i) => m.classList.toggle('is-active', i === activeMatchIndex.value))
  const active = marks[activeMatchIndex.value]
  active?.scrollIntoView({ block: 'center', behavior: 'smooth' })
}

function jumpToNextMatch() {
  if (!matchCount.value) return
  activeMatchIndex.value = (activeMatchIndex.value + 1) % matchCount.value
}

function jumpToPrevMatch() {
  if (!matchCount.value) return
  activeMatchIndex.value = (activeMatchIndex.value - 1 + matchCount.value) % matchCount.value
}

watch(() => props.visible, async (vis) => {
  if (!vis) return
  searchQuery.value = ''
  activeMatchIndex.value = 0
  matchCount.value = 0
  await nextTick()
  applyMarks()
  searchInputRef.value?.focus()
})

watch([() => props.code, () => props.renderAsMarkdown], async () => {
  if (!props.visible) return
  await nextTick()
  applyMarks()
})

watch(searchQuery, async () => {
  activeMatchIndex.value = 0
  await nextTick()
  applyMarks()
})

watch(activeMatchIndex, () => {
  syncActive()
})
</script>

<style scoped>
.code-modal-backdrop {
  position: fixed;
  inset: 0;
  background: color-mix(in srgb, var(--el-bg-color-page) 70%, transparent);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.code-modal {
  width: min(960px, calc(100vw - 80px));
  max-height: min(85vh, 800px);
  min-height: 0;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 16px 48px color-mix(in srgb, var(--el-bg-color-page) 50%, transparent);
}

.code-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color);
  gap: 12px;
  flex: 0 0 auto;
}

.code-modal-title-wrap {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.code-modal-kicker {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.code-modal-title {
  font-family: 'JetBrains Mono', 'Cascadia Code', monospace;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.code-modal-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.code-modal-action-btn {
  padding: 4px 12px;
  font-size: 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-fill-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: all 0.15s ease;
}

.code-modal-action-btn:hover {
  background: var(--el-fill-color-light);
  border-color: var(--el-color-primary-light-5);
  color: var(--el-color-primary);
}

.code-modal-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 16px;
  cursor: pointer;
}

.code-modal-close:hover {
  background: var(--el-fill-color);
  color: var(--el-text-color-primary);
}

.code-modal-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: color-mix(in srgb, var(--el-fill-color-light) 78%, transparent);
}

.code-search-input {
  flex: 1 1 auto;
  min-width: 0;
  height: 34px;
  padding: 0 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  font-size: 13px;
  outline: none;
}

.code-search-input:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 14%, transparent);
}

.code-search-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.code-search-count {
  min-width: 42px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: right;
}

.code-search-btn {
  width: 30px;
  height: 30px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.code-search-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.code-modal-content {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  background: var(--md-code-bg, #101b17);
}

.code-modal-code {
  display: flex;
  align-items: stretch;
  width: max-content;
  min-width: 100%;
  min-height: 100%;
}

.code-gutter {
  position: sticky;
  left: 0;
  z-index: 1;
  flex-shrink: 0;
  padding: 16px 10px 16px 20px;
  border-right: 1px solid color-mix(in srgb, var(--md-code-text, #d8fff0) 12%, transparent);
  background: var(--md-code-bg, #101b17);
  color: color-mix(in srgb, var(--md-code-text, #d8fff0) 34%, transparent);
  font-family: 'Cascadia Code', 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
  font-size: 13px;
  line-height: 1.7;
  text-align: right;
  white-space: pre;
  user-select: none;
  font-variant-numeric: tabular-nums;
}

.code-modal-pre {
  margin: 0;
  padding: 16px 20px;
  min-height: 100%;
  color: var(--md-code-text, #d8fff0);
  background: transparent;
  font-family: 'Cascadia Code', 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre;
  word-break: normal;
  overflow-wrap: normal;
  tab-size: 4;
}

/* 选中文本后右键唤起的自定义菜单 */
.code-ctx-menu {
  position: fixed;
  z-index: 10001;
  min-width: 176px;
  padding: 4px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color-overlay);
  box-shadow: 0 8px 24px color-mix(in srgb, var(--el-bg-color-page) 55%, transparent);
}

.code-ctx-item {
  display: block;
  width: 100%;
  padding: 7px 10px;
  border: none;
  border-radius: 5px;
  background: transparent;
  color: var(--el-text-color-regular);
  font-size: 12.5px;
  text-align: left;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.14s ease, color 0.14s ease;
}

.code-ctx-item:hover {
  background: color-mix(in srgb, var(--el-color-primary) 12%, transparent);
  color: var(--el-color-primary);
}

.code-modal-markdown {
  min-height: 100%;
  padding: 16px 20px;
  color: var(--md-text, var(--el-text-color-primary));
}

.code-modal-pre :deep(.code-search-hit),
.code-modal-markdown :deep(.code-search-hit) {
  background: rgba(250, 204, 21, 0.35);
  color: inherit;
  padding: 1px 0;
  border-radius: 2px;
}

.code-modal-pre :deep(.code-search-hit.is-active),
.code-modal-markdown :deep(.code-search-hit.is-active) {
  background: rgba(245, 158, 11, 0.78);
}

@media (max-width: 520px) {
  .code-modal-backdrop {
    padding: max(8px, env(safe-area-inset-top)) max(8px, env(safe-area-inset-right)) max(8px, env(safe-area-inset-bottom)) max(8px, env(safe-area-inset-left));
    background: color-mix(in srgb, var(--el-bg-color-page) 88%, transparent);
  }

  .code-modal {
    width: 100%;
    max-height: none;
    height: 100%;
    border-radius: 12px;
  }

  .code-modal-header {
    position: sticky;
    top: 0;
    z-index: 1;
    padding: 10px 10px 9px;
    background: var(--el-bg-color);
    gap: 8px;
  }

  .code-modal-kicker {
    display: none;
  }

  .code-modal-title {
    font-size: 12px;
  }

  .code-modal-close {
    width: 34px;
    height: 34px;
    font-size: 18px;
  }

  .code-modal-toolbar {
    padding: 8px 10px;
    gap: 8px;
    flex-wrap: wrap;
  }

  .code-search-input {
    width: 100%;
    height: 36px;
  }

  .code-search-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .code-search-count {
    margin-right: auto;
    text-align: left;
  }

  .code-modal-pre {
    padding: 12px 10px;
    font-size: 12px;
    line-height: 1.6;
  }

  .code-modal-markdown {
    padding: 12px 10px;
  }
}
</style>
