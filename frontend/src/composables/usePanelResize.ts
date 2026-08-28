import { ref, onMounted, onBeforeUnmount } from 'vue'

const STORAGE_KEY_LEFT = 'lc-agent:layout:leftWidth'
const STORAGE_KEY_RIGHT = 'lc-agent:layout:rightWidth'

const DEFAULT_LEFT_WIDTH = 312
const DEFAULT_RIGHT_WIDTH = 350
const MIN_WIDTH = 200
const MAX_LEFT_WIDTH = 600
const MAX_RIGHT_WIDTH = 700

function loadWidth(key: string, fallback: number): number {
  try {
    const v = localStorage.getItem(key)
    if (v !== null) {
      const n = parseInt(v, 10)
      if (!isNaN(n) && n >= MIN_WIDTH) return n
    }
  } catch { /* ignore */ }
  return fallback
}

function saveWidth(key: string, value: number) {
  try {
    localStorage.setItem(key, String(Math.round(value)))
  } catch { /* ignore */ }
}

export function usePanelResize() {
  const leftWidth = ref(loadWidth(STORAGE_KEY_LEFT, DEFAULT_LEFT_WIDTH))
  const rightWidth = ref(loadWidth(STORAGE_KEY_RIGHT, DEFAULT_RIGHT_WIDTH))

  let dragging: 'left' | 'right' | null = null
  let startX = 0
  let startWidth = 0

  function onMouseMove(e: MouseEvent) {
    if (!dragging) return
    const delta = e.clientX - startX
    if (dragging === 'left') {
      const next = Math.min(MAX_LEFT_WIDTH, Math.max(MIN_WIDTH, startWidth + delta))
      leftWidth.value = next
      saveWidth(STORAGE_KEY_LEFT, next)
    } else {
      const next = Math.min(MAX_RIGHT_WIDTH, Math.max(MIN_WIDTH, startWidth - delta))
      rightWidth.value = next
      saveWidth(STORAGE_KEY_RIGHT, next)
    }
  }

  function onMouseUp() {
    if (!dragging) return
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    dragging = null
  }

  function startResize(side: 'left' | 'right', e: MouseEvent) {
    e.preventDefault()
    dragging = side
    startX = e.clientX
    startWidth = side === 'left' ? leftWidth.value : rightWidth.value
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }

  onMounted(() => {
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
  })

  onBeforeUnmount(() => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  })

  return {
    leftWidth,
    rightWidth,
    startResize,
  }
}