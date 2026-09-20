<template>
  <button
    ref="triggerRef"
    class="tab-menu-trigger"
    :class="{ 'is-open': panelVisible }"
    :style="triggerStyle"
    type="button"
    :disabled="items.length === 0"
    :title="triggerLabel"
    :aria-label="triggerLabel"
    :aria-expanded="panelVisible"
    @click="togglePanel"
  >
    <svg class="tab-menu-chevron" viewBox="0 0 16 16" aria-hidden="true">
      <path
        d="M4 6.5L8 10.5L12 6.5"
        fill="none"
        stroke="currentColor"
        stroke-width="1.6"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
    <span class="tab-menu-count">{{ items.length }}</span>
  </button>

  <teleport to="body">
    <div
      v-if="panelVisible"
      ref="panelEl"
      class="tab-menu-panel"
      :style="panelStyle"
      role="listbox"
      :aria-label="`已打开的${label}`"
      @contextmenu.prevent
    >
      <div class="tab-menu-head">
        <span>已打开的{{ label }}</span>
        <span class="tab-menu-head-count">{{ items.length }}</span>
      </div>

      <div ref="listEl" class="tab-menu-list">
        <div
          v-for="item in items"
          :key="item.key"
          class="tab-menu-item"
          :class="{ 'is-active': item.active }"
          role="option"
          :aria-selected="item.active"
          tabindex="0"
          :title="item.hint || item.title"
          @click="selectItem(item)"
          @keydown.enter.prevent="selectItem(item)"
        >
          <span class="tab-menu-mark">
            <slot name="mark" :item="item" />
          </span>
          <span class="tab-menu-title">{{ item.title }}</span>
          <span class="tab-menu-extra">
            <slot name="extra" :item="item" />
          </span>
          <button
            class="tab-menu-close"
            type="button"
            :aria-label="`关闭 ${item.title}`"
            title="关闭"
            @click.stop="removeItem(item)"
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
    </div>
  </teleport>
</template>

<script setup lang="ts" generic="T extends { key: string; title: string; active: boolean; hint?: string }">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

const props = withDefaults(defineProps<{
  /** 逐个映射已打开的标签；调用方须直接沿用标签栏的数组顺序，不要另行排序 */
  items: T[]
  /** 列表对象的中文名，用于按钮提示与面板表头，如「会话」「文件」 */
  label: string
  /** 强调色：会话区靛蓝 / 文件区翠绿 */
  tone?: 'indigo' | 'green'
  /** 面板宽度 */
  width?: number
}>(), {
  tone: 'indigo',
  width: 268,
})

defineSlots<{
  /** 标题左侧的状态标记（icon / 图标 / 转圈等） */
  mark?: (props: { item: T }) => any
  /** 标题右侧的补充标记（脏点、外部改动等） */
  extra?: (props: { item: T }) => any
}>()

const emit = defineEmits<{
  select: [key: string]
  close: [key: string]
}>()

const TONE_COLORS: Record<'indigo' | 'green', string> = {
  indigo: '#4f46e5',
  green: '#059669',
}

const toneColor = computed(() => TONE_COLORS[props.tone])
const triggerLabel = computed(() => `展开已打开的${props.label}列表`)

const triggerRef = ref<HTMLButtonElement | null>(null)
const panelEl = ref<HTMLElement | null>(null)
const listEl = ref<HTMLElement | null>(null)
const panelVisible = ref(false)
const panelLeft = ref(0)
const panelTop = ref(0)

// 自定义属性用显式 Record 传，避免内联对象字面量在 vue-tsc 下对 CSS 变量键的类型报错
const triggerStyle = computed<Record<string, string>>(() => ({
  '--tab-menu-tone': toneColor.value,
}))

const panelStyle = computed<Record<string, string>>(() => ({
  left: `${panelLeft.value}px`,
  top: `${panelTop.value}px`,
  width: `${props.width}px`,
  '--tab-menu-tone': toneColor.value,
}))

const PANEL_GAP = 6
const VIEWPORT_MARGIN = 8

/**
 * 按触发按钮的位置定位面板。
 * 标签栏本身是 overflow 滚动容器，就地绝对定位会被裁切，所以这里固定定位到 body；
 * 每次调用都拿一次实时 rect，面板高度变化（首次渲染、内容增删）后重新调用即可纠正。
 */
function placePanel() {
  const trigger = triggerRef.value
  if (!trigger) return
  const rect = trigger.getBoundingClientRect()
  const panelHeight = panelEl.value?.offsetHeight ?? 0

  const maxLeft = window.innerWidth - props.width - VIEWPORT_MARGIN
  panelLeft.value = Math.max(VIEWPORT_MARGIN, Math.min(rect.left, maxLeft))

  const below = rect.bottom + PANEL_GAP
  // 下方放不下就翻到按钮上方，避免面板被视口底部切掉
  panelTop.value = panelHeight > 0 && below + panelHeight > window.innerHeight - VIEWPORT_MARGIN
    ? Math.max(VIEWPORT_MARGIN, rect.top - PANEL_GAP - panelHeight)
    : below
}

/** 打开列表时把当前激活项滚进可视区，标签多时不用手动找 */
function scrollActiveIntoView() {
  const list = listEl.value
  if (!list) return
  const active = list.querySelector<HTMLElement>('.tab-menu-item.is-active')
  if (!active) return
  const listRect = list.getBoundingClientRect()
  const itemRect = active.getBoundingClientRect()
  if (itemRect.top < listRect.top) {
    list.scrollTop -= listRect.top - itemRect.top
  } else if (itemRect.bottom > listRect.bottom) {
    list.scrollTop += itemRect.bottom - listRect.bottom
  }
}

async function openPanel() {
  if (panelVisible.value || props.items.length === 0) return
  panelVisible.value = true
  await nextTick()
  placePanel()
  scrollActiveIntoView()
}

function closePanel() {
  panelVisible.value = false
}

function togglePanel() {
  if (panelVisible.value) closePanel()
  else void openPanel()
}

function selectItem(item: T) {
  closePanel()
  // 已激活项只收起面板：否则会触发一次多余的会话切换/文件重载
  if (!item.active) emit('select', item.key)
}

function removeItem(item: T) {
  // 关闭后不收起面板，方便连续清理多个标签
  emit('close', item.key)
}

function onDocumentPointerDown(e: MouseEvent) {
  const target = e.target
  if (!(target instanceof Node)) return
  if (panelEl.value?.contains(target) || triggerRef.value?.contains(target)) return
  closePanel()
}

function onDocumentKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') closePanel()
}

// 触发按钮所在的容器可能随窗口滚动/缩放移位，固定定位不再跟随，直接收起比错位更可靠
function onDocumentScroll(e: Event) {
  const target = e.target
  if (target instanceof Node && panelEl.value?.contains(target)) return
  closePanel()
}

function onWindowResize() {
  closePanel()
}

onMounted(() => {
  document.addEventListener('pointerdown', onDocumentPointerDown)
  document.addEventListener('keydown', onDocumentKeydown)
  document.addEventListener('scroll', onDocumentScroll, { capture: true, passive: true })
  window.addEventListener('resize', onWindowResize)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocumentPointerDown)
  document.removeEventListener('keydown', onDocumentKeydown)
  document.removeEventListener('scroll', onDocumentScroll, { capture: true })
  window.removeEventListener('resize', onWindowResize)
})
</script>

<style scoped>
.tab-menu-trigger {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  /* 30px：与会话标签胶囊等高，也不会矮于文件标签栏的可视高度 */
  height: 30px;
  padding: 0 9px 0 7px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 999px;
  background: color-mix(in srgb, var(--el-fill-color) 90%, var(--el-bg-color) 10%);
  color: var(--el-text-color-secondary);
  cursor: pointer;
  transition: background 0.16s ease, color 0.16s ease, border-color 0.16s ease;
}

.tab-menu-trigger:hover:not(:disabled) {
  background: var(--el-fill-color);
  color: var(--el-text-color-primary);
}

.tab-menu-trigger.is-open {
  border-color: color-mix(in srgb, var(--tab-menu-tone) 55%, transparent);
  background: color-mix(in srgb, var(--tab-menu-tone) 14%, transparent);
  color: var(--tab-menu-tone);
}

.tab-menu-trigger:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.tab-menu-chevron {
  flex-shrink: 0;
  width: 12px;
  height: 12px;
  transition: transform 0.18s ease;
}

.tab-menu-trigger.is-open .tab-menu-chevron {
  transform: rotate(180deg);
}

.tab-menu-count {
  min-width: 11px;
  font-size: 11px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  text-align: center;
}

.tab-menu-panel {
  position: fixed;
  z-index: 10002;
  display: flex;
  flex-direction: column;
  /* 标签多时尽量一屏放完：窗口不高再退回按视口比例限高 */
  max-height: min(620px, 76vh);
  padding: 6px;
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  background: var(--el-bg-color-overlay);
  box-shadow: 0 8px 24px color-mix(in srgb, var(--el-bg-color-page) 55%, transparent);
}

.tab-menu-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-shrink: 0;
  padding: 4px 9px 8px;
  color: var(--el-text-color-placeholder);
  font-size: 11px;
}

.tab-menu-head-count {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.tab-menu-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-height: 0;
  overflow-y: auto;
  scrollbar-width: thin;
}

.tab-menu-list::-webkit-scrollbar {
  width: 6px;
}

.tab-menu-list::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: var(--el-border-color);
}

.tab-menu-item {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-shrink: 0;
  /* 行高比标签胶囊略高，下拉里读起来更舒展 */
  padding: 7px 6px 7px 9px;
  border: 1px solid transparent;
  border-radius: 9px;
  color: var(--el-text-color-regular);
  font-size: 12px;
  cursor: pointer;
  user-select: none;
  transition: background 0.14s ease, color 0.14s ease;
}

.tab-menu-item:hover {
  background: var(--el-fill-color-light);
}

.tab-menu-item.is-active {
  background: color-mix(in srgb, var(--tab-menu-tone) 12%, transparent);
  border-color: color-mix(in srgb, var(--tab-menu-tone) 34%, transparent);
  color: var(--tab-menu-tone);
  font-weight: 600;
}

/* 用 min-width 而非固定宽度：文件区要放 22px 的类型徽标，会话区只有 11px 图标 */
.tab-menu-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  min-width: 14px;
  min-height: 14px;
}

.tab-menu-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tab-menu-extra {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.tab-menu-close {
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
  opacity: 0.5;
  transition: background 0.15s ease, opacity 0.15s ease;
}

.tab-menu-close svg {
  width: 10px;
  height: 10px;
}

.tab-menu-item:hover .tab-menu-close {
  opacity: 0.85;
}

.tab-menu-close:hover {
  background: color-mix(in srgb, currentColor 22%, transparent);
  opacity: 1;
}
</style>
