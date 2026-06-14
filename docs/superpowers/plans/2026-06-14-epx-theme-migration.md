# Frontend EPX Theme Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace custom glassmorphism theme with Element Plus X component library and add light/dark theme switching.

**Architecture:** Wrap the app in EPX `<ConfigProvider>` for theme management. Replace hand-written chat components (ChatBubble, ChatInput, session list) with EPX equivalents (Bubble, BubbleList, XSender, Conversations). Remove all `--lc-*` CSS variables and use `--elx-*` tokens. Theme state managed by `@vueuse/core`'s `useDark`.

**Tech Stack:** Vue 3, Element Plus, vue-element-plus-x (v2), @vueuse/core, Pinia, Vue Router

---

## File Structure

| File | Role |
|------|------|
| `frontend/package.json` | Add vue-element-plus-x dependency |
| `frontend/src/main.ts` | Register EPX ConfigProvider, remove old dark CSS import |
| `frontend/index.html` | Remove hardcoded `class="dark"` |
| `frontend/src/App.vue` | Wrap in ConfigProvider, theme state |
| `frontend/src/composables/useTheme.ts` | NEW: Theme composable (useDark wrapper) |
| `frontend/src/style.css` | Gut all --lc-* variables, minimal global reset |
| `frontend/src/components/layout/AppHeader.vue` | Add theme toggle button |
| `frontend/src/components/layout/LeftSidebar.vue` | Replace session list with EPX Conversations |
| `frontend/src/components/chat/ChatBubble.vue` | REPLACE with EPX Bubble usage |
| `frontend/src/components/chat/ChatMessages.vue` | NEW: BubbleList wrapper |
| `frontend/src/components/chat/ChatInput.vue` | REPLACE with EPX XSender |
| `frontend/src/components/chat/ChatView.vue` | Integrate Welcome + BubbleList + Thinking |
| `frontend/src/components/chat/TokenUsagePanel.vue` | Restyle with EP tokens |
| `frontend/src/components/layout/RightSidebar.vue` | Restyle with EP tokens |

---

### Task 1: Install Dependencies and Base Configuration

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/main.ts`
- Modify: `frontend/index.html`
- Create: `frontend/src/composables/useTheme.ts`

- [ ] **Step 1: Install vue-element-plus-x**

```bash
cd frontend
npm install vue-element-plus-x@latest
```

Verify: `node_modules/vue-element-plus-x` exists. Check `package.json` has the dep listed.

- [ ] **Step 2: Remove hardcoded dark class from index.html**

Change `frontend/index.html`:
```html
<!-- Before -->
<html lang="zh-CN" class="dark">
<!-- After -->
<html lang="zh-CN">
```

- [ ] **Step 3: Update main.ts — remove old dark CSS, add EPX**

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')
```

Keep `element-plus/theme-chalk/dark/css-vars.css` (needed by EPX dark mode for el-* components). No registration needed for EPX components (tree-shakeable imports).

- [ ] **Step 4: Create theme composable**

Create `frontend/src/composables/useTheme.ts`:
```typescript
import { useDark, useToggle } from '@vueuse/core'

export function useTheme() {
  const isDark = useDark({
    selector: 'html',
    attribute: 'class',
    valueDark: 'dark',
    valueLight: '',
  })
  const toggleDark = useToggle(isDark)

  return { isDark, toggleDark }
}
```

- [ ] **Step 5: Wrap App.vue in ConfigProvider**

Modify `frontend/src/App.vue` `<script setup>`:
```typescript
import { ConfigProvider } from 'vue-element-plus-x'
import { useTheme } from '@/composables/useTheme'

const { isDark } = useTheme()
```

Modify template — wrap existing content:
```vue
<template>
  <ConfigProvider :theme="isDark ? 'dark' : 'light'">
    <div class="app-container">
      <!-- existing layout content -->
    </div>
  </ConfigProvider>
</template>
```

- [ ] **Step 6: Verify build compiles**

```bash
cd frontend && npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/index.html frontend/src/main.ts frontend/src/composables/useTheme.ts frontend/src/App.vue
git commit -m "feat(frontend): install EPX, add ConfigProvider and theme composable"
```

---

### Task 2: Theme Toggle in Header

**Files:**
- Modify: `frontend/src/components/layout/AppHeader.vue`

- [ ] **Step 1: Add theme toggle button to AppHeader**

In `AppHeader.vue` script:
```typescript
import { useTheme } from '@/composables/useTheme'
import { Sunny, Moon } from '@element-plus/icons-vue'

const { isDark, toggleDark } = useTheme()
```

In template (right section of header):
```vue
<el-button :icon="isDark ? Sunny : Moon" circle size="small" @click="toggleDark()" />
```

- [ ] **Step 2: Remove glassmorphism styles from AppHeader**

Replace the `<style scoped>` block. Remove all:
- `backdrop-filter` / `-webkit-backdrop-filter`
- `var(--lc-glass-*)` references
- hardcoded GitHub-dark hex colors

New styles use EPX tokens:
```css
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  background: var(--elx-bg-surface);
  border-bottom: 1px solid var(--elx-border-color);
  height: 52px;
  z-index: 100;
}
```

- [ ] **Step 3: Verify toggle works**

```bash
cd frontend && npm run build
```

Start dev server, click toggle button in browser — html class should switch between "" and "dark". Element Plus components should follow.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/layout/AppHeader.vue
git commit -m "feat(frontend): add light/dark theme toggle in header"
```

---

### Task 3: Gut style.css — Remove Glassmorphism

**Files:**
- Modify: `frontend/src/style.css`

- [ ] **Step 1: Replace style.css with minimal global reset**

Remove all `--lc-*` variables, glass classes, gradient backgrounds, and Element Plus overrides. Replace with:

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--elx-bg-page);
  color: var(--elx-text-color-primary);
  transition: background 0.3s, color 0.3s;
}

a {
  color: var(--elx-color-primary);
  text-decoration: none;
}

::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-thumb {
  background: var(--elx-border-color);
  border-radius: 3px;
}
```

- [ ] **Step 2: Verify build compiles**

```bash
cd frontend && npm run build
```

Expected: Build succeeds. Some components may look broken until restyled (expected).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/style.css
git commit -m "refactor(frontend): remove glassmorphism CSS, use EPX tokens"
```

---

### Task 4: Migrate LeftSidebar → EPX Conversations

**Files:**
- Modify: `frontend/src/components/layout/LeftSidebar.vue`

- [ ] **Step 1: Replace session list rendering with EPX Conversations**

Import and use:
```typescript
import { Conversations } from 'vue-element-plus-x'
import type { ConversationItem } from 'vue-element-plus-x/types/Conversations'
```

Convert `sessionsStore.sessions` to EPX `ConversationItem[]` format:
```typescript
const conversationItems = computed<ConversationItem[]>(() =>
  sessionsStore.sessions.map(s => ({
    id: s.id,
    label: s.title || 'New Chat',
    group: getTimeGroup(s.created_at),
  }))
)
```

Template:
```vue
<Conversations
  v-model:active="sessionsStore.currentSessionId"
  :items="conversationItems"
  :label-max-width="180"
  :show-tooltip="true"
  row-key="id"
  @change="handleSessionChange"
/>
```

- [ ] **Step 2: Keep "New Chat" button and agent selector above Conversations**

Preserve existing new-chat button and agent dropdown. Only the session LIST gets replaced.

- [ ] **Step 3: Remove all glassmorphism styles from LeftSidebar**

Replace `backdrop-filter`, `--lc-*` vars, hardcoded hex with:
```css
.left-sidebar {
  width: 260px;
  background: var(--elx-bg-surface);
  border-right: 1px solid var(--elx-border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
```

- [ ] **Step 4: Remove old context menu styles (unscoped <style>)**

The old unscoped context menu with hardcoded colors — replace with EP's `el-dropdown` or restyle with `--elx-*`.

- [ ] **Step 5: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/layout/LeftSidebar.vue
git commit -m "feat(frontend): replace session list with EPX Conversations"
```

---

### Task 5: Migrate Chat Messages → EPX BubbleList

**Files:**
- Modify: `frontend/src/components/chat/ChatView.vue`
- Remove: `frontend/src/components/chat/ChatBubble.vue` (or gut contents)

- [ ] **Step 1: Create BubbleList integration in ChatView**

Import:
```typescript
import { BubbleList, Thinking, Welcome } from 'vue-element-plus-x'
import type { BubbleListItemProps } from 'vue-element-plus-x/types/BubbleList'
```

Convert `chatStore.messages` to BubbleList format:
```typescript
const bubbleList = computed(() =>
  chatStore.messages.map((msg, idx) => ({
    key: idx,
    role: msg.role as 'user' | 'ai',
    placement: msg.role === 'user' ? 'end' : 'start',
    content: msg.content,
    shape: 'corner' as const,
    variant: msg.role === 'user' ? 'outlined' : 'filled',
    avatar: msg.role === 'user' ? undefined : '/ai-avatar.png',
    avatarSize: '28px',
    avatarGap: '8px',
    isMarkdown: msg.role !== 'user',
    typing: msg.role !== 'user' && idx === chatStore.messages.length - 1 && chatStore.isStreaming,
  }))
)
```

Template:
```vue
<template>
  <div class="chat-view">
    <Welcome
      v-if="chatStore.messages.length === 0"
      title="Start a conversation"
      description="Ask me anything"
    />
    <BubbleList
      v-else
      :list="bubbleList"
      max-height="100%"
    />
    <Thinking
      v-if="chatStore.isLoading && !chatStore.isStreaming"
      status="thinking"
      content=""
    />
  </div>
</template>
```

- [ ] **Step 2: Handle markdown rendering in Bubble**

EPX v2 removed built-in Typewriter for Markdown. Use `x-markdown-vue` or keep existing `markdown-it` via Bubble's `#content` slot:
```vue
<!-- Inside BubbleList item slot if needed -->
<template #content="{ item }">
  <div v-if="item.isMarkdown" v-html="renderMarkdown(item.content)" />
  <span v-else>{{ item.content }}</span>
</template>
```

- [ ] **Step 3: Remove old ChatBubble.vue styles**

Clear out all glassmorphism from ChatBubble.vue (or delete the file if fully replaced by BubbleList).

- [ ] **Step 4: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/chat/
git commit -m "feat(frontend): replace chat messages with EPX BubbleList"
```

---

### Task 6: Migrate ChatInput → EPX XSender

**Files:**
- Modify: `frontend/src/components/chat/ChatInput.vue`

- [ ] **Step 1: Replace textarea with XSender**

Import:
```typescript
import { XSender } from 'vue-element-plus-x'
```

Template:
```vue
<template>
  <div class="chat-input-wrapper">
    <XSender
      ref="senderRef"
      :loading="chatStore.isStreaming"
      :disabled="!chatStore.isConnected"
      placeholder="Send a message..."
      submit-type="enter"
      clearable
      auto-focus
      @submit="handleSubmit"
    />
  </div>
</template>
```

Script:
```typescript
const senderRef = ref()

function handleSubmit() {
  const value = senderRef.value?.getModelValue()
  if (!value?.trim()) return
  chatStore.sendMessage(value)
  senderRef.value?.clear()
}
```

- [ ] **Step 2: Remove all old ChatInput styles**

Replace glassmorphism styles with:
```css
.chat-input-wrapper {
  padding: 10px 20px 14px;
  border-top: 1px solid var(--elx-border-color);
  background: var(--elx-bg-surface);
}
```

- [ ] **Step 3: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/chat/ChatInput.vue
git commit -m "feat(frontend): replace ChatInput with EPX XSender"
```

---

### Task 7: Restyle Right Sidebar

**Files:**
- Modify: `frontend/src/components/layout/RightSidebar.vue`
- Modify: `frontend/src/components/chat/TokenUsagePanel.vue`

- [ ] **Step 1: Replace glassmorphism in RightSidebar**

Remove all `backdrop-filter`, `--lc-glass-*`, hardcoded hex. Use:
```css
.right-sidebar {
  width: 300px;
  background: var(--elx-bg-surface);
  border-left: 1px solid var(--elx-border-color);
  padding: 16px;
  overflow-y: auto;
}
```

- [ ] **Step 2: Restyle TokenUsagePanel**

Replace hardcoded colors with `--elx-*` tokens:
```css
.token-panel {
  background: var(--elx-fill-color-light);
  border: 1px solid var(--elx-border-color);
  border-radius: var(--elx-border-radius);
  padding: var(--elx-padding-md);
}
```

- [ ] **Step 3: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/layout/RightSidebar.vue frontend/src/components/chat/TokenUsagePanel.vue
git commit -m "refactor(frontend): restyle sidebars with EPX tokens"
```

---

### Task 8: Final Cleanup and Integration Test

**Files:**
- Various: all component files
- Modify: `frontend/src/utils/markdown.ts` (if kept)

- [ ] **Step 1: Search and remove any remaining --lc-* or glass references**

```bash
cd frontend && grep -r "lc-glass\|lc-gradient\|lc-bg-\|lc-border\|lc-text-\|lc-accent\|backdrop-filter\|#0d1117\|#161b22\|#21262d\|#30363d" src/
```

Fix any remaining references by replacing with `--elx-*` equivalents.

- [ ] **Step 2: Remove unused highlight.js dark theme import**

In `frontend/src/utils/markdown.ts`, if it imports `highlight.js/styles/github-dark.css`, change to a theme that works in both modes or remove (EPX Bubble may handle code highlighting).

- [ ] **Step 3: Full build + check**

```bash
cd frontend && npm run build
```

Expected: Clean build, no warnings about missing CSS vars.

- [ ] **Step 4: Manual visual test**

Open `http://127.0.0.1:8001` in browser:
1. Default should be light theme
2. Click toggle → should switch to dark
3. Refresh page → should remember choice (localStorage)
4. Conversations list should render sessions
5. Send a message → BubbleList should show user/AI bubbles
6. Streaming → typing indicator should appear

- [ ] **Step 5: Build for production and deploy**

```bash
cd frontend && npm run build
```

Copy `frontend/dist/` to `lc_agent/web/dist/`.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat(frontend): complete EPX migration with light/dark theme"
```

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| EPX BubbleList doesn't support custom markdown rendering | Use `#content` slot with existing markdown-it |
| XSender submit API differs from current WebSocket flow | Adapt: get value from ref, call chatStore.sendMessage |
| Conversations component missing context menu (rename/delete) | Use EPX's built-in menu slot or `el-dropdown` overlay |
| Token usage panel has no EPX equivalent | Keep custom component, just restyle with `--elx-*` tokens |
| highlight.js theme doesn't match light mode | Use `github.css` for light, `github-dark.css` for dark (dynamic import) |
