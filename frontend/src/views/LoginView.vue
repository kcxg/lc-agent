<template>
  <main class="login-view">
    <canvas
      ref="canvasRef"
      class="login-canvas"
      aria-hidden="true"
    />

    <section class="login-panel" aria-labelledby="login-title">
      <div class="login-heading">
        <p class="login-brand" id="login-title">→ sreagent</p>
        <p class="login-subtitle">智能运维控制中心</p>
      </div>

      <div
        v-if="errorMessage"
        class="login-error"
        role="alert"
      >
        <span class="login-error-text">{{ errorMessage }}</span>
      </div>

      <el-form
        class="login-form"
        label-position="top"
        @submit.prevent="handleSubmit"
      >
        <el-form-item>
          <template #label>
            <span class="form-label">用户名</span>
          </template>
          <el-input
            v-model.trim="username"
            class="login-input"
            autocomplete="username"
            placeholder="请输入用户名"
            :disabled="isSubmitting"
          />
        </el-form-item>

        <el-form-item>
          <template #label>
            <span class="form-label">密码</span>
          </template>
          <el-input
            v-model="password"
            class="login-input"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            :disabled="isSubmitting"
            show-password
          />
        </el-form-item>

        <el-button
          class="login-submit"
          native-type="submit"
          :loading="isSubmitting"
        >
          {{ isSubmitting ? '验证中...' : '登录' }}
        </el-button>
      </el-form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const isSubmitting = ref(false)
const errorMessage = ref('')

const redirectPath = computed(() => {
  const redirect = route.query.redirect
  return typeof redirect === 'string' && redirect.startsWith('/') ? redirect : '/'
})

async function handleSubmit() {
  if (!username.value || !password.value) {
    errorMessage.value = '请输入用户名和密码'
    return
  }
  isSubmitting.value = true
  errorMessage.value = ''
  try {
    await authStore.login(username.value, password.value)
    await router.replace(redirectPath.value)
  } catch {
    errorMessage.value = '账号或密码错误，请重试'
  } finally {
    isSubmitting.value = false
  }
}

// ── Canvas 动画背景 ──────────────────────────────────

const canvasRef = ref<HTMLCanvasElement | null>(null)
let animFrameId = 0
let lastTime = 0
const FRAME_INTERVAL = 1000 / 30 // 30fps

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  r: number
  phase: number
  hue: number // 210-195 range, mapped to indigo-cyan
}

let particles: Particle[] = []
let mouseX = -9999
let mouseY = -9999
let canvasW = 0
let canvasH = 0
let isReducedMotion = false

function createParticles(count: number): Particle[] {
  const ps: Particle[] = []
  for (let i = 0; i < count; i++) {
    // bias toward left (0-0.7) and bottom (0.3-1.0)
    const xBias = Math.random() < 0.55 ? Math.random() * 0.6 : Math.random()
    const yBias = Math.random() < 0.55 ? 0.35 + Math.random() * 0.65 : Math.random()
    ps.push({
      x: xBias,
      y: yBias,
      vx: (Math.random() - 0.5) * 0.0003,
      vy: (Math.random() - 0.5) * 0.0003,
      r: 1.5 + Math.random() * 2.5,
      phase: Math.random() * Math.PI * 2,
      hue: 195 + Math.random() * 15, // 195-210 (cyan-indigo range)
    })
  }
  return ps
}

function resizeCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return
  const dpr = window.devicePixelRatio || 1
  canvasW = window.innerWidth
  canvasH = window.innerHeight
  canvas.width = canvasW * dpr
  canvas.height = canvasH * dpr
  canvas.style.width = `${canvasW}px`
  canvas.style.height = `${canvasH}px`
  const ctx = canvas.getContext('2d')
  if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function drawGrid(ctx: CanvasRenderingContext2D) {
  const spacing = 40
  ctx.strokeStyle = 'rgba(30, 41, 59, 0.4)' // #1e293b
  ctx.lineWidth = 0.5

  for (let x = spacing; x < canvasW; x += spacing) {
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, canvasH)
    ctx.stroke()
  }
  for (let y = spacing; y < canvasH; y += spacing) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(canvasW, y)
    ctx.stroke()
  }
}

function drawParticles(ctx: CanvasRenderingContext2D, timestamp: number) {
  const t = timestamp * 0.001

  // Update & draw particles
  for (const p of particles) {
    // Sinusoidal deviation
    p.x += p.vx + Math.sin(t * 0.5 + p.phase) * 0.0001
    p.y += p.vy + Math.cos(t * 0.4 + p.phase) * 0.0001

    // Mouse repulsion
    const mx = mouseX / canvasW
    const my = mouseY / canvasH
    const dx = p.x - mx
    const dy = p.y - my
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist < 0.1) {
      const force = (0.1 - dist) * 0.002
      p.x += (dx / dist) * force
      p.y += (dy / dist) * force
    }

    // Wrap around edges
    if (p.x < -0.05) p.x = 1.05
    if (p.x > 1.05) p.x = -0.05
    if (p.y < -0.05) p.y = 1.05
    if (p.y > 1.05) p.y = -0.05

    // Draw
    const px = p.x * canvasW
    const py = p.y * canvasH
    ctx.beginPath()
    ctx.arc(px, py, p.r, 0, Math.PI * 2)
    ctx.fillStyle = `hsla(${p.hue}, 70%, 70%, 0.6)`
    ctx.fill()
  }

  // Draw connections
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const a = particles[i]
      const b = particles[j]
      const ax = a.x * canvasW
      const ay = a.y * canvasH
      const bx = b.x * canvasW
      const by = b.y * canvasH
      const d = Math.hypot(bx - ax, by - ay)
      if (d < 120) {
        const alpha = (1 - d / 120) * 0.15
        ctx.beginPath()
        ctx.moveTo(ax, ay)
        ctx.lineTo(bx, by)
        ctx.strokeStyle = `rgba(129, 140, 248, ${alpha})`
        ctx.lineWidth = 0.5
        ctx.stroke()
      }
    }
  }
}

function animate(timestamp: number) {
  if (timestamp - lastTime < FRAME_INTERVAL) {
    animFrameId = requestAnimationFrame(animate)
    return
  }
  lastTime = timestamp

  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, canvasW, canvasH)
  drawGrid(ctx)
  drawParticles(ctx, timestamp)

  animFrameId = requestAnimationFrame(animate)
}

function onMouseMove(e: MouseEvent) {
  mouseX = e.clientX
  mouseY = e.clientY
}

function drawStaticFrame() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.clearRect(0, 0, canvasW, canvasH)
  drawGrid(ctx)
  for (const p of particles) {
    const px = p.x * canvasW
    const py = p.y * canvasH
    ctx.beginPath()
    ctx.arc(px, py, p.r, 0, Math.PI * 2)
    ctx.fillStyle = `hsla(${p.hue}, 70%, 70%, 0.4)`
    ctx.fill()
  }
}

function handleResizeReduced() {
  resizeCanvas()
  drawStaticFrame()
}

function handleVisibility() {
  if (isReducedMotion) return
  if (document.hidden) {
    cancelAnimationFrame(animFrameId)
  } else {
    lastTime = 0
    animFrameId = requestAnimationFrame(animate)
  }
}

function startCanvas() {
  isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  particles = createParticles(40)
  resizeCanvas()

  if (isReducedMotion) {
    // Static frame + resize redraw; no animation, no mouse tracking
    drawStaticFrame()
    window.addEventListener('resize', handleResizeReduced)
    return
  }

  window.addEventListener('resize', resizeCanvas)
  window.addEventListener('mousemove', onMouseMove)
  document.addEventListener('visibilitychange', handleVisibility)
  animFrameId = requestAnimationFrame(animate)
}

function stopCanvas() {
  cancelAnimationFrame(animFrameId)
  window.removeEventListener('resize', resizeCanvas)
  window.removeEventListener('resize', handleResizeReduced)
  window.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('visibilitychange', handleVisibility)
  particles = []
}

onMounted(startCanvas)
onUnmounted(stopCanvas)
</script>

<style scoped>
/* ── Canvas 背景 ──────────────────────────────── */
.login-canvas {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  mask-image: radial-gradient(ellipse at center, black 50%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 50%, transparent 80%);
}

/* ── 主容器 ──────────────────────────────── */
.login-view {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: #090d1a;
  position: relative;
}

/* ── 登录面板 ──────────────────────────────── */
.login-panel {
  position: relative;
  z-index: 1;
  width: min(100% - 32px, 380px);
  padding: 32px;
  border: 1px solid rgba(129, 140, 248, 0.2);
  border-radius: 12px;
  background: rgba(17, 24, 39, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

@media (max-width: 400px) {
  .login-panel {
    width: 100%;
    border-radius: 8px;
    padding: 24px;
  }
}

/* ── 标题区 ──────────────────────────────── */
.login-heading {
  margin-bottom: 28px;
}

.login-brand {
  margin: 0 0 4px;
  font-family: 'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace;
  font-size: 20px;
  font-weight: 600;
  color: #f1f5f9;
  letter-spacing: 0.02em;
}

.login-subtitle {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

/* ── 错误提示 ──────────────────────────────── */
.login-error {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding: 10px 14px;
  border-left: 3px solid #f59e0b;
  background: rgba(245, 158, 11, 0.1);
  border-radius: 0 6px 6px 0;
  animation: error-slide-in 200ms ease;
}

.login-error-text {
  font-size: 13px;
  color: #fbbf24;
}

@keyframes error-slide-in {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── 表单 ──────────────────────────────── */
.login-form {
  display: flex;
  flex-direction: column;
}

.form-label {
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
}

/* ── 输入框深度样式 ────────────────────────── */
:deep(.login-input .el-input__wrapper) {
  background: #0f172a;
  border: 1px solid rgba(100, 116, 139, 0.3);
  border-radius: 8px;
  box-shadow: none;
  transition: border-color 200ms ease;
}

:deep(.login-input .el-input__wrapper:hover) {
  border-color: rgba(129, 140, 248, 0.4);
}

:deep(.login-input .el-input__wrapper.is-focus) {
  border-color: #818cf8;
  box-shadow: 0 0 0 1px rgba(129, 140, 248, 0.25);
}

:deep(.login-input .el-input__inner) {
  color: #f1f5f9;
  font-size: 14px;
}

:deep(.login-input .el-input__inner::placeholder) {
  color: #475569;
}

:deep(.login-input.is-disabled .el-input__wrapper) {
  opacity: 0.5;
}

/* 密码可见切换按钮 */
:deep(.login-input .el-input__suffix-inner .el-icon) {
  color: #64748b;
}

/* ── 提交按钮 ──────────────────────────────── */
.login-submit {
  width: 100%;
  height: 42px;
  margin-top: 8px;
  border: none;
  border-radius: 8px;
  background: #818cf8;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  transition: background 200ms ease, box-shadow 200ms ease, transform 200ms ease;
}

.login-submit:hover {
  background: #6366f1;
  box-shadow: 0 0 20px rgba(129, 140, 248, 0.3);
}

.login-submit:active {
  transform: scale(0.985);
}

.login-submit.is-loading {
  background: #6366f1;
}

/* 覆盖 Element Plus 按钮默认样式 */
:deep(.login-submit .el-button__loading-icon) {
  color: rgba(255, 255, 255, 0.8);
}

/* ── 焦点环 ──────────────────────────────── */
:deep(.login-input .el-input__wrapper:focus-within) {
  outline: 2px solid rgba(129, 140, 248, 0.5);
  outline-offset: 2px;
}

.login-submit:focus-visible {
  outline: 2px solid rgba(129, 140, 248, 0.5);
  outline-offset: 2px;
}

/* ── reduced-motion ─────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .login-error {
    animation: none;
  }

  .login-submit {
    transition: none;
  }
}
</style>
