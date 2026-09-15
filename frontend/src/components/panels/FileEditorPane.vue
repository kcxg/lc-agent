<template>
  <div class="file-editor-pane">
    <!-- 文件标签栏 -->
    <template v-if="store.files.length > 0">
      <div class="editor-tabbar">
        <div
          ref="tabsBarRef"
          class="editor-tabs"
          role="tablist"
          aria-label="打开的文件"
          @scroll.passive="syncTabScrollState"
          @wheel="onTabsWheel"
        >
          <div
            v-for="file in store.files"
            :key="file.path"
            class="editor-tab"
            :class="{ active: store.activePath === file.path }"
            :title="file.path"
            role="tab"
            :aria-selected="store.activePath === file.path"
            @click="store.activate(file.path)"
            @auxclick.middle.prevent="store.close(file.path)"
            @contextmenu.prevent="openTabMenu($event, file)"
          >
            <FileTypeIcon :name="file.name" :compact="true" />
            <svg v-if="file.pinned" class="editor-tab-pin" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z" fill="currentColor" />
            </svg>
            <span class="editor-tab-name">{{ file.name }}</span>
            <button
              class="editor-tab-close"
              type="button"
              :aria-label="`关闭 ${file.name}`"
              title="关闭标签"
              @click.stop="store.close(file.path)"
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
        <div class="editor-tabbar-actions">
          <button
            v-if="tabsOverflow"
            class="editor-icon-btn"
            type="button"
            title="向左滚动标签"
            :disabled="!canScrollLeft"
            @click="scrollTabs(-1)"
          >
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <button
            v-if="tabsOverflow"
            class="editor-icon-btn"
            type="button"
            title="向右滚动标签"
            :disabled="!canScrollRight"
            @click="scrollTabs(1)"
          >
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M6 3.5L10.5 8L6 12.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <button class="editor-icon-btn" type="button" title="刷新当前文件" :disabled="!store.activePath || content?.loading" @click="store.refresh(store.activePath)">
            <svg viewBox="0 0 16 16" :class="{ spinning: content?.loading }" aria-hidden="true">
              <path d="M13 8a5 5 0 1 1-1.5-3.6M13 2v3h-3" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <button class="editor-restore-btn" type="button" title="恢复已关闭的标签" @click="store.reopenClosed()">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9z"
                fill="currentColor"
              />
            </svg>
          </button>
          <button class="editor-icon-btn" type="button" title="关闭全部" @click="store.closeAll()">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M4 4l8 8m0-8l-8 8" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 标签右键菜单：与代码区菜单各用一套状态，避免互相顶掉 -->
      <teleport to="body">
        <div
          v-if="tabMenuVisible"
          ref="tabMenuEl"
          class="code-ctx-menu"
          :style="tabMenuStyle"
          role="menu"
          @contextmenu.prevent
        >
          <button class="code-ctx-item" role="menuitem" @click="toggleTabPin">
            {{ tabMenuFile?.pinned ? '取消固定' : '固定标签' }}
          </button>
          <button class="code-ctx-item" role="menuitem" @click="closeTabFromMenu">关闭</button>
          <button class="code-ctx-item" role="menuitem" @click="closeOtherTabs">关闭其他</button>
          <button class="code-ctx-item" role="menuitem" @click="closeTabsToRight">关闭右侧</button>
          <button class="code-ctx-item" role="menuitem" @click="closeAllTabs">关闭全部</button>
          <button class="code-ctx-item" role="menuitem" @click="copyTabPath">复制路径</button>
        </div>
      </teleport>
    </template>

    <!-- 空状态 -->
    <div v-if="store.files.length === 0" class="editor-empty">
      <div class="editor-empty-icon-wrap">
        <svg viewBox="0 0 48 48" aria-hidden="true">
          <path
            d="M10 12.5c0-1.4 1.1-2.5 2.5-2.5h9l3.5 4h10.5c1.4 0 2.5 1.1 2.5 2.5v3.5"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            d="M14 21h20a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H14a2 2 0 0 1-2-2V23a2 2 0 0 1 2-2z"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linejoin="round"
          />
          <path d="M17 27h14M17 32h9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
      </div>
      <p class="editor-empty-title">还没有打开的文件</p>
      <p class="editor-empty-hint">在左侧栏切到「文件」浏览项目目录</p>
      <p class="editor-empty-hint">或点击聊天中的文件链接，内容会在这里以标签打开</p>
    </div>

    <!-- 内容区 -->
    <template v-else-if="store.activeFile">
      <!-- 路径面包屑：位于标签栏与工具栏之间 -->
      <div class="editor-breadcrumb">
        <template v-for="(seg, i) in breadcrumbSegments" :key="seg.path">
          <span v-if="i > 0" class="editor-breadcrumb-sep">/</span>
          <button
            class="editor-breadcrumb-item"
            :class="{ 'is-last': i === breadcrumbSegments.length - 1 }"
            type="button"
            :title="seg.abs"
            @click="revealInTree(seg)"
          >
            {{ seg.label }}
          </button>
        </template>
      </div>

      <!-- 工具栏：搜索 + 复制。图片不参与搜索/复制，整条工具栏隐藏 -->
      <div v-if="!isImageFile" class="editor-toolbar">
        <input
          ref="searchInputRef"
          v-model="searchQuery"
          class="editor-search-input"
          type="text"
          placeholder="搜索关键字..."
          @keydown.enter.prevent="jumpToNextMatch"
        />
        <div class="editor-search-actions">
          <span v-if="searchQuery" class="editor-search-count">{{ activeMatchLabel }}</span>
          <button class="editor-search-btn" :disabled="!matchCount" @click="jumpToPrevMatch">↑</button>
          <button class="editor-search-btn" :disabled="!matchCount" @click="jumpToNextMatch">↓</button>
        </div>
        <button class="editor-copy-btn" type="button" @click="copyCode">{{ copyLabel }}</button>
        <button class="editor-locate-btn" type="button" title="在文件树中定位当前文件" @click="revealActiveInTree">
          <svg viewBox="0 0 16 16" aria-hidden="true">
            <path d="M2 3.5h5l1.2 1.5H14v7.5H2z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
            <circle cx="8" cy="8.5" r="2.4" fill="none" stroke="currentColor" stroke-width="1.4"/>
          </svg>
          <span>定位</span>
        </button>
      </div>

      <!-- 加载中 -->
      <div v-if="content?.loading" class="editor-status">
        <el-icon class="is-loading"><Loading /></el-icon>
        加载中
      </div>

      <!-- 错误 -->
      <div v-else-if="content?.error" class="editor-error">{{ content.error }}</div>

      <!-- 图片预览 -->
      <div v-else-if="content?.image && content?.imageDataUrl" class="editor-image">
        <img :src="content.imageDataUrl" :alt="store.activeFile.name" />
      </div>

      <!-- 图片过大：后端不下发数据，只能提示 -->
      <div v-else-if="content?.image && content?.imageTooLarge" class="editor-binary">
        <div class="editor-binary-icon">
          <svg viewBox="0 0 48 48" aria-hidden="true">
            <path d="M10 12h28v24H10z" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round" />
            <path d="M10 30l8-8 7 7 5-5 8 8" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round" />
            <circle cx="31" cy="18" r="3" fill="none" stroke="currentColor" stroke-width="2.4" />
          </svg>
        </div>
        <p class="editor-binary-title">图片过大，无法预览</p>
        <p class="editor-binary-hint">{{ store.activeFile.name }} 超过 8MB，超出预览上限，请用系统图片查看器打开</p>
      </div>

      <!-- 二进制文件：不渲染内容，给出提示 -->
      <div v-else-if="content?.binary" class="editor-binary">
        <div class="editor-binary-icon">
          <svg viewBox="0 0 48 48" aria-hidden="true">
            <path
              d="M28 6H14a3 3 0 0 0-3 3v30a3 3 0 0 0 3 3h20a3 3 0 0 0 3-3V15z"
              fill="none"
              stroke="currentColor"
              stroke-width="2.4"
              stroke-linejoin="round"
            />
            <path d="M28 6v9h9" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round" />
            <path d="M19 26l10 10M29 26L19 36" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" />
          </svg>
        </div>
        <p class="editor-binary-title">二进制文件，无法预览</p>
        <p class="editor-binary-hint">{{ store.activeFile.name }} 不是文本文件（如数据库、图片、压缩包等），请在对应工具中打开</p>
      </div>

      <!-- 内容 -->
      <div v-else-if="content" ref="contentWrapRef" class="editor-content" @scroll="closeMenu">
        <!-- 跳行高亮：绝对定位色带随滚动跟随该行，1.5s 后由定时器移除 -->
        <div
          v-if="jumpFlash"
          class="editor-jump-band"
          :style="{
            top: `${jumpLineTop}px`,
            left: `${jumpLineLeft}px`,
            width: `${jumpLineWidth}px`,
            height: `${jumpLineHeight}px`,
          }"
          aria-hidden="true"
        />
        <!-- Markdown 渲染 -->
        <div
          v-if="store.activeFile.asMarkdown"
          ref="renderRef"
          class="editor-markdown markdown-body"
          v-html="renderedHtml"
        />
        <!-- 代码 + 行号 -->
        <div v-else class="editor-code">
          <div class="editor-gutter" aria-hidden="true">{{ lineNumbers }}</div>
          <pre ref="renderRef" class="editor-pre hljs" v-html="renderedHtml" />
        </div>
      </div>

      <!-- 右键菜单 -->
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
          <template v-if="store.activeFile.sourcePath && !store.activeFile.asMarkdown">
            <button class="code-ctx-item" role="menuitem" @click="copyLineRef">复制行号</button>
            <button class="code-ctx-item" role="menuitem" @click="copyLineRefWithContent">复制行号和内容</button>
          </template>
        </div>
      </teleport>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import hljs from 'highlight.js'
import { Loading } from '@element-plus/icons-vue'
import { renderMarkdown } from '@/utils/markdown'
import { useOpenedFilesStore } from '@/stores/opened-files'
import type { OpenedFile } from '@/stores/opened-files'
import { useProjectTreeStore } from '@/stores/project-tree'
import FileTypeIcon from '@/components/common/FileTypeIcon.vue'

const store = useOpenedFilesStore()
const treeStore = useProjectTreeStore()

const content = computed(() => store.activeContent)

// 图片不参与搜索与复制：既看扩展名（内容未到达前就能判断），也看后端识别结果
const isImageFile = computed(() =>
  !!store.activeFile && (store.isImagePath(store.activeFile.path) || !!content.value?.image),
)

// ---- 路径面包屑 ----
interface BreadcrumbSeg {
  label: string
  // 相对项目根的路径，文件树以此定位
  path: string
  // 完整路径，仅用于 title 提示
  abs: string
}

// 绝对路径转成相对项目根；不在项目内则原样返回
function toProjectRelative(p: string): string {
  const raw = (p || '').replace(/\\/g, '/')
  const root = (treeStore.projectRoot || '').replace(/\\/g, '/').replace(/\/+$/, '')
  if (root && (raw === root || raw.startsWith(root + '/'))) return raw.slice(root.length + 1)
  return raw
}

// 定位用路径：项目外的文件（如聊天里的绝对路径）在树里不存在，不发起定位
function toRevealPath(p: string): string {
  const rel = toProjectRelative(p)
  if (!rel || rel.startsWith('/') || /^[a-zA-Z]:/.test(rel)) return ''
  return rel
}

const breadcrumbSegments = computed<BreadcrumbSeg[]>(() => {
  const file = store.activeFile
  if (!file) return []
  const absPath = (file.sourcePath || file.path).replace(/\\/g, '/')
  const root = (treeStore.projectRoot || '').replace(/\\/g, '/').replace(/\/+$/, '')
  // 项目内文件用绝对路径还原各级（title 更好读）；项目外路径只有相对路径可用
  const inProject = !!root && (absPath === root || absPath.startsWith(root + '/'))
  const parts = toProjectRelative(inProject ? absPath : file.path).split('/').filter(Boolean)
  return parts.map((part, i) => {
    const rel = parts.slice(0, i + 1).join('/')
    return { label: part, path: rel, abs: inProject ? `${root}/${rel}` : rel }
  })
})

function revealInTree(seg: BreadcrumbSeg) {
  treeStore.reveal(seg.path)
}

// 「在树中显示」：把当前激活文件在文件树里展开定位（应对自动定位被手动滚动打断）
function revealActiveInTree() {
  const file = store.activeFile
  if (!file) return
  const rel = toRevealPath(file.path)
  if (rel) treeStore.reveal(rel)
}

// 切换标签时让文件树跟随定位（仅在激活项变化时触发，树内滚动不反向干扰编辑器）
watch(() => store.activePath, (path) => {
  if (!path) return
  const rel = toRevealPath(path)
  if (rel) treeStore.reveal(rel)
})

// ---- 渲染 ----
const renderRef = ref<HTMLElement | null>(null)
const contentWrapRef = ref<HTMLElement | null>(null)

const lineNumbers = computed(() => {
  if (!content.value || store.activeFile?.asMarkdown) return ''
  const total = content.value.code.split('\n').length
  return Array.from({ length: total }, (_, i) => i + 1).join('\n')
})

const renderedHtml = computed(() => {
  if (!content.value) return ''
  if (store.activeFile?.asMarkdown) return renderMarkdown(content.value.code)
  const lang = store.activeFile?.language?.toLowerCase() || ''
  if (lang && lang !== 'text' && hljs.getLanguage(lang)) {
    return hljs.highlight(content.value.code, { language: lang }).value
  }
  return escapeHtml(content.value.code)
})

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

// ---- 搜索 ----
const searchQuery = ref('')
const activeMatchIndex = ref(0)
const matchCount = ref(0)
const searchInputRef = ref<HTMLInputElement | null>(null)

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function applyMarks() {
  const el = renderRef.value
  if (!el) return
  // 代码模式下 v-html 已渲染，需要重新写入以清除旧 mark
  if (!store.activeFile?.asMarkdown) {
    el.innerHTML = renderedHtml.value
  }
  const query = searchQuery.value.trim()
  if (!query) { matchCount.value = 0; return }
  const regex = new RegExp(escapeRegExp(query), 'gi')
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)
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
  matchCount.value = el.querySelectorAll('mark.code-search-hit').length
  syncActive()
}

const activeMatchLabel = computed(() => {
  if (!matchCount.value) return searchQuery.value.trim() ? '0/0' : ''
  return `${activeMatchIndex.value + 1}/${matchCount.value}`
})

function syncActive() {
  const el = renderRef.value
  if (!el) return
  const marks = el.querySelectorAll('mark.code-search-hit')
  marks.forEach((m, i) => m.classList.toggle('is-active', i === activeMatchIndex.value))
  ;(marks[activeMatchIndex.value] as HTMLElement | undefined)?.scrollIntoView({ block: 'center', behavior: 'smooth' })
}

function jumpToNextMatch() {
  if (!matchCount.value) return
  activeMatchIndex.value = (activeMatchIndex.value + 1) % matchCount.value
}

function jumpToPrevMatch() {
  if (!matchCount.value) return
  activeMatchIndex.value = (activeMatchIndex.value - 1 + matchCount.value) % matchCount.value
}

watch(searchQuery, async () => { activeMatchIndex.value = 0; await nextTick(); applyMarks() })
watch(activeMatchIndex, () => syncActive())
watch(() => store.activePath, async () => {
  searchQuery.value = ''
  activeMatchIndex.value = 0
  matchCount.value = 0
  await nextTick()
  applyMarks()
  searchInputRef.value?.focus()
})
watch(() => content.value?.code, async () => { await nextTick(); applyMarks() })

// ---- 跳行定位 ----
const jumpFlash = ref(false)
const jumpLineTop = ref(0)
const jumpLineLeft = ref(0)
const jumpLineWidth = ref(0)
const jumpLineHeight = ref(0)
let jumpFlashTimer: ReturnType<typeof setTimeout> | undefined

async function applyJumpLine() {
  const line = store.jumpLine
  const c = content.value
  if (line <= 0 || !c?.code) return
  // Markdown 是渲染后的排版，行号与源码行不对应；图片/二进制无代码区，均只清空请求
  if (c.image || c.binary || store.activeFile?.asMarkdown) {
    store.consumeJumpLine()
    return
  }
  await nextTick()
  const wrap = contentWrapRef.value
  const pre = renderRef.value
  if (!wrap || !pre) return
  const cs = window.getComputedStyle(pre)
  const fontSize = parseFloat(cs.fontSize) || 12
  // 行高取真实计算值，'normal' 时回退到 CSS 里写的 1.65 倍字号
  const lh = cs.lineHeight === 'normal' ? fontSize * 1.65 : parseFloat(cs.lineHeight) || fontSize * 1.65
  const top = (parseFloat(cs.paddingTop) || 0) + (line - 1) * lh
  // 目标行居中显示，比顶对齐更容易看清上下文
  wrap.scrollTop = Math.max(0, top + pre.offsetTop - (wrap.clientHeight - lh) / 2)
  // .editor-content 是该 pre 的 offsetParent（已设为 relative），offset* 即内容坐标系下的位置
  jumpLineTop.value = top + pre.offsetTop
  jumpLineLeft.value = pre.offsetLeft
  jumpLineWidth.value = pre.offsetWidth
  jumpLineHeight.value = lh
  jumpFlash.value = true
  clearTimeout(jumpFlashTimer)
  jumpFlashTimer = setTimeout(() => { jumpFlash.value = false }, 1500)
  store.consumeJumpLine()
}

// 同时监听两个来源：先请求跳行后内容才到、内容已在立即跳行，两种情况都能覆盖
watch(
  [() => store.jumpLine, () => content.value?.code],
  () => { void applyJumpLine() },
)

// ---- 标签栏：溢出滚动 + 右键菜单 ----
const tabsBarRef = ref<HTMLElement | null>(null)
// 溢出状态：决定是否显示左右箭头；滚动位置决定箭头是否可用
const tabsOverflow = ref(false)
const canScrollLeft = ref(false)
const canScrollRight = ref(false)

function syncTabScrollState() {
  const bar = tabsBarRef.value
  if (!bar) {
    tabsOverflow.value = false
    canScrollLeft.value = false
    canScrollRight.value = false
    return
  }
  // 留 1px 容差，避免亚像素误差让箭头一直亮着
  tabsOverflow.value = bar.scrollWidth > bar.clientWidth + 1
  canScrollLeft.value = bar.scrollLeft > 1
  canScrollRight.value = bar.scrollLeft + bar.clientWidth < bar.scrollWidth - 1
}

/** 点击左右箭头按一屏的 2/3 滚动 */
function scrollTabs(direction: 1 | -1) {
  const bar = tabsBarRef.value
  if (!bar) return
  bar.scrollBy({ left: direction * bar.clientWidth * (2 / 3), behavior: 'smooth' })
}

/** 滚轮在标签栏上默认竖向滚动页面；这里转换为横向滚动标签 */
function onTabsWheel(e: WheelEvent) {
  const bar = tabsBarRef.value
  if (!bar || !tabsOverflow.value) return
  // 触摸板横向手势本身已有 deltaX，无需干预
  if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) return
  e.preventDefault()
  bar.scrollLeft += e.deltaY
}

const tabMenuVisible = ref(false)
const tabMenuX = ref(0)
const tabMenuY = ref(0)
const tabMenuPath = ref('')
const tabMenuEl = ref<HTMLElement | null>(null)
const tabMenuFile = computed(() => store.files.find(f => f.path === tabMenuPath.value) ?? null)
const tabMenuStyle = computed(() => ({ left: `${tabMenuX.value}px`, top: `${tabMenuY.value}px` }))

function closeTabMenu() { tabMenuVisible.value = false }

function openTabMenu(e: MouseEvent, file: OpenedFile) {
  const MENU_W = 176
  // 6 个菜单项，与 .code-ctx-item 的行高一致
  const MENU_H = 6 * 31 + 8
  tabMenuPath.value = file.path
  tabMenuX.value = Math.min(e.clientX, window.innerWidth - MENU_W - 8)
  tabMenuY.value = Math.min(e.clientY, window.innerHeight - MENU_H - 8)
  tabMenuVisible.value = true
}

function toggleTabPin() { const p = tabMenuPath.value; closeTabMenu(); if (p) store.togglePin(p) }
function closeTabFromMenu() { const p = tabMenuPath.value; closeTabMenu(); if (p) store.close(p) }
function closeOtherTabs() { const p = tabMenuPath.value; closeTabMenu(); if (p) store.closeOthers(p) }
function closeTabsToRight() { const p = tabMenuPath.value; closeTabMenu(); if (p) store.closeToRight(p) }
function closeAllTabs() { closeTabMenu(); store.closeAll() }
function copyTabPath() {
  const f = tabMenuFile.value
  closeTabMenu()
  if (f) void writeClipboard(f.sourcePath || f.path)
}

// 激活标签变化后滚进可见区，避免被其他标签挤出视野
watch(() => store.activePath, async () => {
  await nextTick()
  const bar = tabsBarRef.value
  if (!bar) return
  const el = bar.querySelector<HTMLElement>('.editor-tab.active')
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

// ---- 复制 ----
const copyLabel = ref('复制')
async function copyCode() {
  if (!content.value?.code) return
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(content.value.code)
    } else {
      const ta = document.createElement('textarea')
      ta.value = content.value.code
      ta.style.position = 'fixed'; ta.style.left = '-9999px'
      document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta)
    }
    copyLabel.value = '已复制'
  } catch { copyLabel.value = '复制失败' }
  setTimeout(() => { copyLabel.value = '复制' }, 1400)
}

// ---- 右键菜单 ----
const menuVisible = ref(false)
const menuX = ref(0)
const menuY = ref(0)
const menuEl = ref<HTMLElement | null>(null)
const menuStyle = computed(() => ({ left: `${menuX.value}px`, top: `${menuY.value}px` }))

function closeMenu() { menuVisible.value = false }

function handleContextMenu(e: MouseEvent) {
  const sel = window.getSelection()
  if (!sel || sel.isCollapsed || !sel.toString().trim()) return
  e.preventDefault()
  const MENU_W = 176
  const MENU_H = store.activeFile?.sourcePath && !store.activeFile?.asMarkdown ? 116 : 44
  menuX.value = Math.min(e.clientX, window.innerWidth - MENU_W - 8)
  menuY.value = Math.min(e.clientY, window.innerHeight - MENU_H - 8)
  menuVisible.value = true
}

function selectionLineRange(): { start: number; end: number } | null {
  const el = renderRef.value
  const sel = window.getSelection()
  if (!el || !sel || sel.rangeCount === 0) return null
  const range = sel.getRangeAt(0)
  if (!el.contains(range.startContainer) || !el.contains(range.endContainer)) return null
  const text = range.toString()
  if (!text.trim()) return null
  const probe = document.createRange()
  probe.selectNodeContents(el)
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
  const sp = store.activeFile?.sourcePath
  if (!lines || !sp) return null
  const span = lines.start === lines.end ? `L${lines.start}` : `L${lines.start}-${lines.end}`
  return `${sp}#${span}`
}

async function writeClipboard(text: string) {
  try {
    if (navigator.clipboard?.writeText) { await navigator.clipboard.writeText(text) }
    else {
      const ta = document.createElement('textarea')
      ta.value = text; ta.style.position = 'fixed'; ta.style.left = '-9999px'
      document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta)
    }
  } catch { /* 静默 */ }
}

async function copySelection() { const t = window.getSelection()?.toString() ?? ''; if (t) await writeClipboard(t); closeMenu() }
async function copyLineRef() { const l = lineRefLabel(); if (l) await writeClipboard(l); closeMenu() }
async function copyLineRefWithContent() {
  const l = lineRefLabel(); const t = window.getSelection()?.toString() ?? ''
  if (l && t) await writeClipboard(`${l}\n\n${t}`); closeMenu()
}

function onDocumentPointerDown(e: MouseEvent) {
  const target = e.target
  const insideCodeMenu = !!menuEl.value && target instanceof Node && menuEl.value.contains(target)
  if (!insideCodeMenu) closeMenu()
  // 两套菜单各自判断，避免其中一个命中就漏关另一个
  const insideTabMenu = !!tabMenuEl.value && target instanceof Node && tabMenuEl.value.contains(target)
  if (!insideTabMenu) closeTabMenu()
}
function onDocumentKeydown(e: KeyboardEvent) {
  // Ctrl/Cmd+Shift+T：恢复最近关闭的标签（与浏览器/VS Code 习惯一致）
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'T' || e.key === 't')) {
    if (store.files.length === 0) return
    e.preventDefault()
    store.reopenClosed()
    return
  }
  if (e.key !== 'Escape') return
  closeMenu()
  closeTabMenu()
}

function onWindowResize() { closeMenu(); closeTabMenu(); syncTabScrollState() }

onMounted(() => {
  document.addEventListener('pointerdown', onDocumentPointerDown)
  document.addEventListener('keydown', onDocumentKeydown)
  window.addEventListener('resize', onWindowResize)
  contentWrapRef.value?.addEventListener('contextmenu', handleContextMenu)
  void nextTick(syncTabScrollState)
})
onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocumentPointerDown)
  document.removeEventListener('keydown', onDocumentKeydown)
  window.removeEventListener('resize', onWindowResize)
  contentWrapRef.value?.removeEventListener('contextmenu', handleContextMenu)
  clearTimeout(jumpFlashTimer)
})

// 标签增减或面板宽度变化都会改变是否溢出，需重新判定箭头显隐
watch(() => store.files.length, () => { void nextTick(syncTabScrollState) })
watch(() => store.activePath, () => { void nextTick(syncTabScrollState) })

watch(contentWrapRef, (el, prev) => {
  prev?.removeEventListener('contextmenu', handleContextMenu)
  el?.addEventListener('contextmenu', handleContextMenu)
})
</script>

<style scoped>
.file-editor-pane {
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
}

/* 标签栏：与会话标签同一套胶囊设计语言 */
.editor-tabbar {
  display: flex;
  align-items: center;
  gap: 6px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
  flex-shrink: 0;
  min-width: 0;
  padding: 6px 8px;
}

.editor-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  min-width: 0;
  padding: 3px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  background: color-mix(in srgb, var(--el-fill-color) 90%, var(--el-bg-color) 10%);
  overflow-x: auto;
  overflow-y: hidden;
  /* 标签溢出时必须能看到/拖到横向滚动条，否则被挤出去的标签无法访问 */
  scrollbar-width: thin;
  scrollbar-color: var(--el-border-color) transparent;
}

.editor-tabs::-webkit-scrollbar {
  height: 6px;
}

.editor-tabs::-webkit-scrollbar-track {
  background: transparent;
}

.editor-tabs::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: var(--el-border-color);
}

.editor-tabs::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-dark);
}

.editor-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 5px 3px 8px;
  border: 1px solid transparent;
  border-radius: 999px;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  background: transparent;
  transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
  user-select: none;
}

.editor-tab:hover:not(.active) {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

.editor-tab.active {
  /* 文件标签区域色相：翠绿（与顶栏 新对话 一致），与会话标签靛蓝、面板 tab 紫色区分 */
  background: linear-gradient(135deg, #059669, #10b981);
  color: #fff;
  border-color: rgba(5, 150, 105, 0.6);
  box-shadow: 0 2px 10px rgba(5, 150, 105, 0.35);
}

.editor-tab-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 固定标签的图钉标记 */
.editor-tab-pin {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
  opacity: 0.85;
}

.editor-tab-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: inherit;
  cursor: pointer;
  flex-shrink: 0;
  opacity: 0.6;
  transition: background 0.15s ease, opacity 0.15s ease;
  padding: 0;
  line-height: 1;
}

.editor-tab-close svg {
  width: 10px;
  height: 10px;
}

.editor-tab:hover .editor-tab-close,
.editor-tab.active .editor-tab-close { opacity: 1; }
.editor-tab-close:hover { background: color-mix(in srgb, currentColor 22%, transparent); }

/* 激活标签是渐变底，文件类型徽标改用半透明白底，避免彩色块压在蓝底上显脏 */
.editor-tab.active :deep(.ft-badge) {
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
}

.editor-tabbar-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 0 2px;
  flex-shrink: 0;
}

/* 恢复已关闭标签：翠绿实底，与文件区色相一致（禁止灰底/透明底） */
.editor-restore-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 24px;
  padding: 0 8px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #059669, #10b981);
  color: #fff;
  cursor: pointer;
  transition: filter 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease;
  box-shadow: 0 1px 6px rgba(5, 150, 105, 0.3);
}

.editor-restore-btn svg { width: 12px; height: 12px; }
.editor-restore-btn:hover { filter: brightness(1.08); box-shadow: 0 3px 12px rgba(5, 150, 105, 0.45); }
.editor-restore-btn:active { transform: translateY(1px); }

.editor-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  padding: 0;
  transition: background 0.13s, color 0.13s;
}
.editor-icon-btn svg { width: 12px; height: 12px; }
.editor-icon-btn:hover:not(:disabled) { background: var(--el-fill-color); color: var(--el-text-color-primary); }
.editor-icon-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.editor-icon-btn .spinning { animation: spin 0.9s linear infinite; }

/* 空状态 */
.editor-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 48px 24px;
  font-size: 13px;
  flex: 1;
}

.editor-empty-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  margin-bottom: 8px;
  border-radius: 20px;
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--el-color-primary) 12%, transparent),
    color-mix(in srgb, var(--el-color-info) 12%, transparent)
  );
  color: var(--el-color-primary);
}

.editor-empty-icon-wrap svg {
  width: 34px;
  height: 34px;
}

.editor-empty-title {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.editor-empty-hint {
  margin: 0;
  color: var(--el-text-color-placeholder);
  text-align: center;
}

/* 二进制文件提示：与空状态同一套设计语言 */
.editor-binary {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 48px 24px;
  flex: 1;
}

.editor-binary-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  margin-bottom: 8px;
  border-radius: 20px;
  background: linear-gradient(
    135deg,
    rgba(245, 158, 11, 0.14),
    rgba(249, 115, 22, 0.14)
  );
  color: #f59e0b;
}

.editor-binary-icon svg {
  width: 34px;
  height: 34px;
}

.editor-binary-title {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.editor-binary-hint {
  margin: 0;
  max-width: 420px;
  color: var(--el-text-color-placeholder);
  text-align: center;
}

/* 路径面包屑 */
.editor-breadcrumb {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
  font-size: 11.5px;
  overflow: hidden;
  white-space: nowrap;
  flex-shrink: 0;
}

.editor-breadcrumb-item {
  max-width: 180px;
  padding: 1px 4px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: inherit;
  font-family: inherit;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.editor-breadcrumb-item:hover {
  background: rgba(5, 150, 105, 0.12);
  color: #059669;
}

.editor-breadcrumb-item.is-last {
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.editor-breadcrumb-sep {
  flex-shrink: 0;
  color: var(--el-text-color-placeholder);
  opacity: 0.7;
}

/* 工具栏 */
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
  flex-shrink: 0;
}

.editor-search-input {
  flex: 1;
  min-width: 0;
  height: 26px;
  padding: 0 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 5px;
  outline: none;
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-primary);
  font-size: 12px;
  transition: border-color 0.14s;
}
.editor-search-input:focus { border-color: var(--el-color-primary); }
.editor-search-input::placeholder { color: var(--el-text-color-placeholder); }

.editor-search-actions {
  display: flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
}
.editor-search-count { min-width: 32px; font-size: 11px; color: var(--el-text-color-secondary); text-align: right; }
.editor-search-btn {
  width: 22px; height: 22px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  font-size: 11px;
  display: flex; align-items: center; justify-content: center;
  padding: 0;
  transition: background 0.12s;
}
.editor-search-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.editor-search-btn:hover:not(:disabled) { background: var(--el-fill-color); }

.editor-copy-btn {
  padding: 2px 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 11px;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background 0.12s, color 0.12s;
}
.editor-copy-btn:hover { background: var(--el-fill-color); color: var(--el-text-color-primary); }

/* 「定位」按钮：带彩色底的胶囊，与文件区翠绿色系一致 */
.editor-locate-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  padding: 3px 9px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #059669, #10b981);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  box-shadow: 0 1px 6px rgba(5, 150, 105, 0.32);
  transition: filter 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}

.editor-locate-btn svg {
  width: 12px;
  height: 12px;
}

.editor-locate-btn:hover {
  filter: brightness(1.06);
  box-shadow: 0 2px 10px rgba(5, 150, 105, 0.44);
  transform: translateY(-1px);
}

.editor-locate-btn:active {
  transform: translateY(0);
}

/* 状态 */
.editor-status {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 24px; color: var(--el-text-color-placeholder); font-size: 12px; flex: 1;
}
.editor-error {
  padding: 16px; color: var(--el-color-danger); font-size: 12px; flex: 1; word-break: break-all;
}

/* 内容区 */
.editor-content {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  background: var(--md-code-bg, #0d1117);
}

/* 跳行高亮：色带随内容一起滚动，1.5s 后由定时器摘除 */
.editor-jump-band {
  position: absolute;
  /* 低于行号列的 sticky 层级，横向滚动时行号列仍压住色带 */
  z-index: 0;
  pointer-events: none;
  background: linear-gradient(
    90deg,
    rgba(16, 185, 129, 0.28),
    rgba(16, 185, 129, 0.08)
  );
  box-shadow: inset 2px 0 0 #059669;
  animation: jump-band-fade 1.5s ease forwards;
}

@keyframes jump-band-fade {
  0% { opacity: 0; }
  12% { opacity: 1; }
  72% { opacity: 1; }
  100% { opacity: 0; }
}

@media (prefers-reduced-motion: reduce) {
  .editor-jump-band { animation: none; opacity: 0.85; }
}

/* 图片预览：棋盘格底衬托透明图 */
.editor-image {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 0;
  padding: 12px;
  overflow: auto;
  background-color: var(--el-fill-color-light);
  background-image:
    repeating-conic-gradient(
      color-mix(in srgb, var(--el-text-color-primary) 8%, transparent) 0% 25%,
      transparent 0% 50%
    );
  background-size: 16px 16px;
}

.editor-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 6px 22px color-mix(in srgb, var(--el-text-color-primary) 16%, transparent);
}

.editor-code {
  display: flex;
  align-items: stretch;
  width: max-content;
  min-width: 100%;
  min-height: 100%;
}

.editor-gutter {
  position: sticky;
  left: 0;
  z-index: 1;
  flex-shrink: 0;
  padding: 10px 8px 10px 12px;
  border-right: 1px solid color-mix(in srgb, var(--md-code-text, #d8fff0) 12%, transparent);
  background: var(--md-code-bg, #0d1117);
  color: color-mix(in srgb, var(--md-code-text, #d8fff0) 34%, transparent);
  font-family: 'Cascadia Code', 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
  font-size: 12px;
  line-height: 1.65;
  text-align: right;
  white-space: pre;
  user-select: none;
  font-variant-numeric: tabular-nums;
}

.editor-pre {
  margin: 0;
  padding: 10px 14px;
  min-height: 100%;
  color: var(--md-code-text, #d8fff0);
  background: transparent;
  font-family: 'Cascadia Code', 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
  font-size: 12px;
  line-height: 1.65;
  white-space: pre;
  word-break: normal;
  overflow-wrap: normal;
  tab-size: 4;
}

.editor-markdown {
  min-height: 100%;
  padding: 12px 14px;
  color: var(--md-text, var(--el-text-color-primary));
  font-size: 13px;
  line-height: 1.7;
}

.editor-pre :deep(.code-search-hit),
.editor-markdown :deep(.code-search-hit) {
  background: rgba(250, 204, 21, 0.35);
  color: inherit;
  padding: 1px 0;
  border-radius: 2px;
}
.editor-pre :deep(.code-search-hit.is-active),
.editor-markdown :deep(.code-search-hit.is-active) {
  background: rgba(245, 158, 11, 0.78);
}

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .editor-icon-btn .spinning { animation: none; } }
</style>

<style>
/* 右键菜单需要全局样式（teleport 到 body）*/
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
</style>
