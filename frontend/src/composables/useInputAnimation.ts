import { computed, readonly, ref, watch } from 'vue'

export type InputAnimationType = 'rainbow-rod' | 'transparent-arc' | 'marquee'

export interface InputAnimationOption {
  id: InputAnimationType
  label: string
  description: string
}

export const INPUT_ANIMATION_OPTIONS: InputAnimationOption[] = [
  { id: 'rainbow-rod', label: '彩虹金箍棒', description: '满圈彩虹锥形渐变旋转' },
  { id: 'transparent-arc', label: '透明小光弧', description: '一小段彩色光弧绕圈旋转' },
  { id: 'marquee', label: '跑马灯', description: '围绕输入框上下左右流动的彩色灯带' },
]

const STORAGE_KEY = 'lc-agent:input-animation'
const DEFAULT_ANIMATION: InputAnimationType = 'marquee'
const validAnimationIds = new Set<InputAnimationType>(INPUT_ANIMATION_OPTIONS.map(option => option.id))
const inputAnimation = ref<InputAnimationType>(loadInitialAnimation())

function isInputAnimationType(value: string | null): value is InputAnimationType {
  return Boolean(value && validAnimationIds.has(value as InputAnimationType))
}

function loadInitialAnimation(): InputAnimationType {
  if (typeof window === 'undefined') return DEFAULT_ANIMATION
  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (isInputAnimationType(stored)) return stored
  // 兼容旧值 led-strip → transparent-arc
  if (stored === 'led-strip') return 'transparent-arc'
  return DEFAULT_ANIMATION
}

export function useInputAnimation() {
  const currentOption = computed(() => (
    INPUT_ANIMATION_OPTIONS.find(option => option.id === inputAnimation.value) || INPUT_ANIMATION_OPTIONS[0]
  ))

  function setInputAnimation(animation: InputAnimationType) {
    if (!validAnimationIds.has(animation)) return
    inputAnimation.value = animation
  }

  watch(inputAnimation, animation => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, animation)
    }
  })

  return {
    inputAnimation,
    inputAnimationOptions: readonly(INPUT_ANIMATION_OPTIONS),
    currentOption,
    setInputAnimation,
  }
}
