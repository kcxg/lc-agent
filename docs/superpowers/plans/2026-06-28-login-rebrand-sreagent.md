# sreagent 登录页品牌重塑实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `LoginView.vue` 从 "lc-agent" 品牌转型为 "sreagent"，全面升级视觉效果：Canvas 动态背景 + 暗色靛紫配色 + 半透明毛玻璃面板

**Architecture:** 单文件修改 — `frontend/src/views/LoginView.vue`。Canvas 动画逻辑封装在组件内的 `onMounted`/`onUnmounted` 生命周期中，不抽离为独立文件（避免过度工程化）。动态背景为 Canvas 元素，通过 `position: fixed` 置于最底层，登录面板叠加其上。

**Tech Stack:** Vue 3 + TypeScript + Element Plus + Canvas 2D API（无额外依赖）

## Global Constraints

- 不引入新的 npm 依赖
- 登录接口 `/api/auth/login` 保持不变，script 逻辑仅微调文案变量
- 品牌名称统一为 `sreagent`
- `prefers-reduced-motion` 时禁用 Canvas 动画，仅保留静态网格
- 页面不可见时暂停动画（`visibilitychange`）
- 动画帧率限制 30fps
- 不支持旧版 IE

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `frontend/src/views/LoginView.vue` | 修改 | 登录页面：Canvas 动态背景 + 登录面板 + 表单交互 |

---

### Task 1: 模板结构重写

**Files:**
- Modify: `frontend/src/views/LoginView.vue:1-54`

**Interfaces:**
- Produces: `<canvas ref="canvasRef">` 作为背景层，登录面板 DOM 结构包含品牌名 `→ sreagent`、副标题、表单

- [ ] **Step 1: 替换 `<template>` 块**

 将现有模板整体替换为新结构：

```vue
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
```

关键变化：
- 新增 `<canvas>` 元素，`ref="canvasRef"` 供脚本操作
- 标题从 `<h1>登录 lc-agent</h1>` 变为 `<p class="login-brand">→ sreagent</p>` + 副标题 `<p class="login-subtitle">智能运维控制中心</p>`
- `el-alert` 替换为自定义错误横幅 `div.login-error`，用 `role="alert"` 保证可访问性
- 按钮文字动态切换："登录" → "验证中..."
- 移除 `el-button` 的 `type="primary"`（样式全自定义）
- 输入框添加 `class="login-input"` 用于深度样式覆盖
- Label 通过 `#label` 插槽控制，添加 `class="form-label"`

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/LoginView.vue
git commit -m "feat: rebrand login template to sreagent with canvas background"
```

---

### Task 2: Canvas 动画逻辑

**Files:**
- Modify: `frontend/src/views/LoginView.vue:56-92`

**Interfaces:**
- Consumes: 模板中的 `canvasRef` ref
- Produces: `startCanvas()`, `stopCanvas()` 在 `onMounted`/`onUnmounted` 中管理生命周期

- [ ] **Step 1: 替换 `<script setup>` 块**

```typescript
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

function handleVisibility() {
  if (document.hidden) {
    cancelAnimationFrame(animFrameId)
  } else {
    lastTime = 0
    animFrameId = requestAnimationFrame(animate)
  }
}

function startCanvas() {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  particles = createParticles(40)
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
  window.addEventListener('mousemove', onMouseMove)
  document.addEventListener('visibilitychange', handleVisibility)

  if (prefersReduced) {
    // Draw static frame only
    const canvas = canvasRef.value
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    drawGrid(ctx)
    for (const p of particles) {
      const px = p.x * canvasW
      const py = p.y * canvasH
      ctx.beginPath()
      ctx.arc(px, py, p.r, 0, Math.PI * 2)
      ctx.fillStyle = `hsla(${p.hue}, 70%, 70%, 0.4)`
      ctx.fill()
    }
    return
  }

  animFrameId = requestAnimationFrame(animate)
}

function stopCanvas() {
  cancelAnimationFrame(animFrameId)
  window.removeEventListener('resize', resizeCanvas)
  window.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('visibilitychange', handleVisibility)
  particles = []
}

onMounted(startCanvas)
onUnmounted(stopCanvas)
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/LoginView.vue
git commit -m "feat: add canvas dynamic background with grid and particles to login"
```

---

### Task 3: 样式全面升级

**Files:**
- Modify: `frontend/src/views/LoginView.vue:94-142`

**Interfaces:**
- Consumes: Task 1 的 DOM 结构（`.login-brand`、`.login-subtitle`、`.login-error`、`.login-input`、`.form-label` 等 class）
- Consumes: Task 2 的 `.login-canvas` Canvas 元素

- [ ] **Step 1: 替换 `<style scoped>` 块**

```css
<style scoped>
/* ── Canvas 背景 ──────────────────────────────── */
.login-canvas {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/LoginView.vue
git commit -m "feat: overhaul login page visual design with sreagent brand theme"
```

---

### Task 4: 验证构建

**Files:**
- No code changes — 构建验证

- [ ] **Step 1: 构建前端，确认无编译错误**

```bash
cd /Users/cuiyukun/code/py/lc-agent/frontend && npm run build
```

Expected: Build 成功，无 TypeScript 错误或 CSS 警告。

- [ ] **Step 2: 检查构建产物中登录页面内容**

```bash
grep -c 'sreagent' /Users/cuiyukun/code/py/lc-agent/lc_agent/web/dist/assets/LoginView-*.js
```

Expected: 至少匹配到 1 次（品牌名已嵌入 bundle）。

- [ ] **Step 3: Commit（如有构建产物变化）**

```bash
git add lc_agent/web/dist/
git commit -m "chore: update dist with sreagent login rebrand"
```

---

### 完整性复查清单

| 设计需求 | 覆盖 |
|----------|------|
| 品牌名 `→ sreagent` | Task 1 模板 |
| 副标题"智能运维控制中心" | Task 1 模板 |
| 配色 `#090d1a` / `#818cf8` 等 | Task 3 样式 |
| 终端网格动态背景 | Task 2 Canvas `drawGrid()` |
| AI 神经元光点 + 连线 | Task 2 Canvas `drawParticles()` |
| 鼠标排斥交互 | Task 2 `onMouseMove` + repulsion |
| 毛玻璃面板 `backdrop-filter` | Task 3 `.login-panel` |
| 错误横幅样式（琥珀色左边框） | Task 3 `.login-error` |
| 按钮 hover 光晕 + active scale | Task 3 `.login-submit` |
| 按钮 loading "验证中..." | Task 1 模板 |
| 焦点环可访问性 | Task 3 focus-visible |
| 30fps 帧率限制 | Task 2 `FRAME_INTERVAL` |
| `prefers-reduced-motion` | Task 2 `startCanvas()` + Task 3 media query |
| `visibilitychange` 暂停 | Task 2 `handleVisibility()` |
| 不引入新依赖 | ✅ 全部使用 Canvas 2D API |
| 响应式移动端 | Task 3 `@media (max-width: 400px)` |
