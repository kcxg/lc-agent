# Multi-Session Chat Store Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `chat.ts` from a single-session store into a session registry that allows multiple sessions to stream simultaneously, with sidebar streaming indicators and automatic cleanup.

**Architecture:** A `Map<sessionId, SessionState>` inside `useChatStore()` holds per-session reactive state and SSE clients. Computed properties delegate to the active session, so all existing component code is unchanged. `switchToSession(id)` replaces the previous `connect`/`disconnect`/`loadMessages` call sequence in `App.vue`.

**Tech Stack:** Vue 3 + Pinia, TypeScript, `ChatSseClient` (existing SSE abstraction)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `frontend/src/stores/chat-session-state.ts` | **Create** | `SessionState` interface + `createSessionState()` factory |
| `frontend/src/stores/chat.ts` | **Major refactor** | Session registry, delegate computed props, `switchToSession` |
| `frontend/src/api/sse-client.ts` | **Minor** | Remove `abandon()` (no longer needed) |
| `frontend/src/App.vue` | **Minor** | Replace disconnect/loadMessages/connect with `switchToSession` |
| `frontend/src/components/layout/LeftSidebar.vue` | **Minor** | Add streaming indicator per session |

---

## Task 1: Create `chat-session-state.ts`

**Files:**
- Create: `frontend/src/stores/chat-session-state.ts`

- [ ] **Step 1.1: Create the file**

```typescript
// frontend/src/stores/chat-session-state.ts
import { ref } from 'vue'
import type { Ref } from 'vue'
import type { ChatSseClient } from '@/api/sse-client'
import type { ChatMessage, InterruptInfo, ErrorInfo, TodoItem } from './chat'

export interface SessionState {
  // Message data
  messages: Ref<ChatMessage[]>
  totalMessageCount: Ref<number>
  hasOlderMessages: Ref<boolean>
  loadingOlder: Ref<boolean>

  // Streaming state
  isStreaming: Ref<boolean>
  inThinking: boolean           // mutable flag, intentionally not Ref
  streamStartTime: number       // mutable, not Ref
  currentRoundStart: number     // mutable, not Ref
  todos: Ref<TodoItem[]>
  interrupt: Ref<InterruptInfo | null>
  errorMessage: Ref<ErrorInfo | null>

  // SSE client (null until connect is called)
  client: ChatSseClient | null
}

export function createSessionState(): SessionState {
  return {
    messages: ref([]),
    totalMessageCount: ref(0),
    hasOlderMessages: ref(false),
    loadingOlder: ref(false),
    isStreaming: ref(false),
    inThinking: false,
    streamStartTime: 0,
    currentRoundStart: 0,
    todos: ref([]),
    interrupt: ref(null),
    errorMessage: ref(null),
    client: null,
  }
}
```

- [ ] **Step 1.2: Verify TypeScript compiles**

Run: `cd frontend && npx vue-tsc --noEmit`  
Expected: no errors related to `chat-session-state.ts`

- [ ] **Step 1.3: Commit**

```bash
git add frontend/src/stores/chat-session-state.ts
git commit -m "feat: add SessionState type and factory for multi-session chat store"
```

---

## Task 2: Add session registry to `chat.ts`

**Files:**
- Modify: `frontend/src/stores/chat.ts`

This task replaces all top-level reactive singletons (`messages`, `isStreaming`, etc.) with delegating computed properties backed by the session registry.

- [ ] **Step 2.1: Import `SessionState` and `createSessionState` at top of `chat.ts`**

Add after the existing imports:

```typescript
import { createSessionState } from './chat-session-state'
import type { SessionState } from './chat-session-state'
```

- [ ] **Step 2.2: Replace the singleton state declarations inside `defineStore`**

Find the block starting at line ~540:

```typescript
// REMOVE this block:
const messages = ref<ChatMessage[]>([])
const isStreaming = ref(false)
const isConnected = computed(() => !!threadId.value)
const threadId = ref<string | null>(null)
const interrupt = ref<InterruptInfo | null>(null)
let sseClient: ChatSseClient | null = null
const todos = ref<TodoItem[]>([])
const errorMessage = ref<ErrorInfo | null>(null)
const lastMessage = computed(() => messages.value[messages.value.length - 1])
let streamStartTime = 0
let currentRoundStart = 0
let inThinking = false
```

Replace with:

```typescript
// --- Session Registry ---
const activeSessions = new Map<string, SessionState>()
const activeSessionId = ref<string | null>(null)

// --- Computed delegates to active session (API unchanged for components) ---
const _active = (): SessionState | undefined =>
  activeSessionId.value ? activeSessions.get(activeSessionId.value) : undefined

const messages = computed(() => _active()?.messages.value ?? [])
const isStreaming = computed(() => _active()?.isStreaming.value ?? false)
const interrupt = computed(() => _active()?.interrupt.value ?? null)
const todos = computed(() => _active()?.todos.value ?? [])
const errorMessage = computed(() => _active()?.errorMessage.value ?? null)
const totalMessageCount = computed(() => _active()?.totalMessageCount.value ?? 0)
const hasOlderMessages = computed(() => _active()?.hasOlderMessages.value ?? false)
const loadingOlder = computed(() => _active()?.loadingOlder.value ?? false)
const isConnected = computed(() => !!activeSessionId.value)
const threadId = computed(() => activeSessionId.value)
const lastMessage = computed(() => {
  const msgs = messages.value
  return msgs[msgs.length - 1] ?? null
})
```

- [ ] **Step 2.3: Run TypeScript check**

Run: `cd frontend && npx vue-tsc --noEmit`  
Expected: errors about `sseClient` and reactive state not found — these will be fixed in later tasks. At this step, the goal is to confirm the computed structure itself is correct. If TypeScript errors are only about missing variables used later in the file, proceed.

- [ ] **Step 2.4: Commit**

```bash
git add frontend/src/stores/chat.ts
git commit -m "refactor(chat): add session registry Map and delegate computed properties"
```

---

## Task 3: Refactor `_registerHandlers` and `_ensureClient`

**Files:**
- Modify: `frontend/src/stores/chat.ts`

The `_registerHandlers(client)` function currently reads/writes global reactive singletons. It must become `_registerHandlers(client, state, sessionId)` that operates on a `SessionState`.

- [ ] **Step 3.1: Remove `_ensureClient` and update `_registerHandlers` signature**

Replace:

```typescript
function _ensureClient(): ChatSseClient {
  if (!sseClient) {
    sseClient = new ChatSseClient()
    _registerHandlers(sseClient)
  }
  return sseClient
}

function _registerHandlers(client: ChatSseClient) {
```

With:

```typescript
function _createClientForSession(state: SessionState, sessionId: string): ChatSseClient {
  const client = new ChatSseClient()
  state.client = client
  _registerHandlers(client, state, sessionId)
  return client
}

function _registerHandlers(client: ChatSseClient, state: SessionState, sessionId: string) {
```

- [ ] **Step 3.2: Update every reactive variable access inside `_registerHandlers`**

This is a mechanical find-and-replace within the `_registerHandlers` function body (~260 lines, up to the closing `}`):

| Old | New |
|---|---|
| `isStreaming.value` | `state.isStreaming.value` |
| `messages.value` | `state.messages.value` |
| `inThinking` | `state.inThinking` |
| `streamStartTime` | `state.streamStartTime` |
| `currentRoundStart` | `state.currentRoundStart` |
| `todos.value` | `state.todos.value` |
| `interrupt.value` | `state.interrupt.value` |
| `errorMessage.value` | `state.errorMessage.value` |
| `threadId.value` (used in `applySubAgentEventToMessages` calls and title refresh) | `sessionId` |

- [ ] **Step 3.3: Add auto-cleanup at the end of the `done` handler**

Inside `client.on('done', (msg) => { ... })`, after the existing logic (the `setTimeout` for refreshSessionTitle), add:

```typescript
// Auto-cleanup: if this session is no longer the active one, release resources
if (sessionId !== activeSessionId.value) {
  state.client?.disconnect()
  state.client = null
  activeSessions.delete(sessionId)
}
```

- [ ] **Step 3.4: Add same cleanup to `cancelled` and `error` handlers**

Inside `client.on('cancelled', ...)` and `client.on('error', ...)`, after all existing logic, add the same 4-line cleanup block.

- [ ] **Step 3.5: Verify TypeScript**

Run: `cd frontend && npx vue-tsc --noEmit`  
Expected: errors should now be only about callers of `_ensureClient` (removed) and the old `connect`/`disconnect` — fixed in the next task.

- [ ] **Step 3.6: Commit**

```bash
git add frontend/src/stores/chat.ts
git commit -m "refactor(chat): make _registerHandlers session-aware"
```

---

## Task 4: Add `switchToSession` and replace `connect`/`disconnect`

**Files:**
- Modify: `frontend/src/stores/chat.ts`

- [ ] **Step 4.1: Replace `connect`, `disconnect`, `abandonStream` with `switchToSession`**

Find and remove:

```typescript
async function connect(existingThreadId?: string) { ... }
function disconnect() { ... }
function abandonStream() { ... }
```

Add `switchToSession` in their place:

```typescript
/**
 * Switch the active session. If the departing session is streaming, it stays
 * in the registry and continues in the background. If it is idle, it is
 * released immediately. The arriving session is loaded from DB unless it is
 * already in the registry (was streaming in background).
 */
async function switchToSession(sessionId: string): Promise<void> {
  if (activeSessionId.value === sessionId) return

  // Departing session
  const oldId = activeSessionId.value
  if (oldId) {
    const old = activeSessions.get(oldId)
    if (old && !old.isStreaming.value) {
      old.client?.disconnect()
      old.client = null
      activeSessions.delete(oldId)
    }
    // Streaming session: keep in map — SSE continues in background
  }

  activeSessionId.value = sessionId

  // Arriving session: already in registry means it was streaming in background
  if (activeSessions.has(sessionId)) return

  // New session: create state, load messages, connect client
  const state = createSessionState()
  activeSessions.set(sessionId, state)
  await _loadMessagesIntoState(sessionId, state)
  const client = _createClientForSession(state, sessionId)
  client.setThreadId(sessionId)
}

/** Expose session streaming state for sidebar indicators */
function isSessionStreaming(sessionId: string): boolean {
  return activeSessions.get(sessionId)?.isStreaming.value ?? false
}
```

- [ ] **Step 4.2: Also expose `activeSessionIds` for sidebar badge count**

Add inside the store (after `isSessionStreaming`):

```typescript
function getStreamingSessionIds(): string[] {
  return [...activeSessions.keys()].filter(id =>
    activeSessions.get(id)?.isStreaming.value
  )
}
```

- [ ] **Step 4.3: Update the `return` statement at the end of `defineStore`**

Remove `connect`, `disconnect`, `abandonStream` from the returned object.  
Add `switchToSession`, `isSessionStreaming`, `getStreamingSessionIds`.

- [ ] **Step 4.4: Verify TypeScript**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: errors in `App.vue` and other callers that still use `connect`/`disconnect`. These are fixed in Task 6.

- [ ] **Step 4.5: Commit**

```bash
git add frontend/src/stores/chat.ts
git commit -m "feat(chat): add switchToSession, isSessionStreaming; remove connect/disconnect"
```

---

## Task 5: Update `sendMessage` and other methods to use session state

**Files:**
- Modify: `frontend/src/stores/chat.ts`

Several methods read/write reactive state directly. They need to look up the active `SessionState`.

- [ ] **Step 5.1: Update `sendMessage`**

Find `async function sendMessage(...)`. At the start of the function body, add:

```typescript
const state = activeSessionId.value ? activeSessions.get(activeSessionId.value) : undefined
if (!state) return
const client = state.client
if (!client) return
```

Then replace all direct reactive accesses inside `sendMessage` with their `state.xxx` counterparts (same mapping table as Task 3.2).

Replace `_ensureClient()` calls with just `client` (already obtained above).

- [ ] **Step 5.2: Update `stopGeneration`**

Find `function stopGeneration()`. Replace:

```typescript
if (sseClient && isStreaming.value) {
  sseClient.sendCancel()
```

With:

```typescript
const state = activeSessionId.value ? activeSessions.get(activeSessionId.value) : undefined
if (state?.client && state.isStreaming.value) {
  state.client.sendCancel()
```

- [ ] **Step 5.3: Update `clearMessages`**

Find `function clearMessages()`. Replace body with:

```typescript
const state = activeSessionId.value ? activeSessions.get(activeSessionId.value) : undefined
if (state) {
  state.messages.value = []
  state.todos.value = []
  state.interrupt.value = null
  state.errorMessage.value = null
}
```

- [ ] **Step 5.4: Update `truncateAfterMessage`**

Find `function truncateAfterMessage(messageId: string)`. Replace `messages.value` with:

```typescript
const state = activeSessionId.value ? activeSessions.get(activeSessionId.value) : undefined
if (!state) return
// use state.messages.value instead of messages.value for truncation
```

- [ ] **Step 5.5: Update `respondToInterrupt` and `resumeInterrupt`**

These use `sseClient` and `threadId.value`. Replace:
- `sseClient` → `state?.client`
- `threadId.value` → `activeSessionId.value`

Add a guard at the start: `const state = activeSessionId.value ? activeSessions.get(activeSessionId.value) : undefined; if (!state?.client) return`

- [ ] **Step 5.6: Update `_loadMessagesIntoState` (previously `loadMessages`)**

The existing `loadMessages(sessionId)` function reads/writes `messages.value`, `totalMessageCount.value`, etc. It needs to be split into:

1. Keep `loadMessages(sessionId)` as the **public** method (so callers that already pass sessionId still work):

```typescript
async function loadMessages(sessionId: string): Promise<void> {
  const state = activeSessions.get(sessionId)
  if (state) {
    await _loadMessagesIntoState(sessionId, state)
  }
}
```

2. Extract `_loadMessagesIntoState(sessionId, state)` as the **private** method that takes a `SessionState`:

```typescript
async function _loadMessagesIntoState(sessionId: string, state: SessionState): Promise<void> {
  // existing loadMessages body, but replace:
  //   messages.value → state.messages.value
  //   totalMessageCount.value → state.totalMessageCount.value
  //   hasOlderMessages.value → state.hasOlderMessages.value
  //   loadingOlder.value → state.loadingOlder.value
}
```

- [ ] **Step 5.7: Update `loadOlderMessages`**

Similar to above: look up active session state and operate on `state.xxx.value`.

- [ ] **Step 5.8: Verify TypeScript**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: errors only in `App.vue` (still uses old API). If there are errors in `chat.ts` itself, fix them now.

- [ ] **Step 5.9: Commit**

```bash
git add frontend/src/stores/chat.ts
git commit -m "refactor(chat): update sendMessage and state-mutating methods to use SessionState"
```

---

## Task 6: Update `App.vue`

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 6.1: Find `restoreSession` in `App.vue`**

Locate the function (currently calls `chatStore.clearMessages()`, `chatStore.disconnect()`, `chatStore.loadMessages()`, `chatStore.connect()`).

- [ ] **Step 6.2: Replace the call sequence**

Replace all `chatStore.clearMessages()` / `chatStore.disconnect()` / `chatStore.abandonStream()` / `chatStore.loadMessages(sessionId)` / `chatStore.connect(sessionId)` sequences with:

```typescript
await chatStore.switchToSession(sessionId)
```

There may be multiple call sites in `restoreSession` (for different code paths). Apply the same replacement to each. Example — current pattern:

```typescript
chatStore.clearMessages()
// If a stream is in progress, abandon ...
if (chatStore.isStreaming) {
  chatStore.abandonStream()
} else {
  chatStore.disconnect()
}
await chatStore.loadMessages(sessionId)
await chatStore.connect(sessionId)
return
```

Becomes:

```typescript
await chatStore.switchToSession(sessionId)
return
```

- [ ] **Step 6.3: Also update any `chatStore.connect(sessionId)` calls outside `restoreSession`**

Search `App.vue` for any remaining `chatStore.connect` / `chatStore.disconnect` / `chatStore.abandonStream` calls and replace appropriately.

- [ ] **Step 6.4: Verify TypeScript**

Run: `cd frontend && npx vue-tsc --noEmit`  
Expected: no errors in `App.vue`.

- [ ] **Step 6.5: Commit**

```bash
git add frontend/src/App.vue
git commit -m "refactor(App.vue): replace connect/disconnect with switchToSession"
```

---

## Task 7: Add streaming indicator to `LeftSidebar.vue`

**Files:**
- Modify: `frontend/src/components/layout/LeftSidebar.vue`

- [ ] **Step 7.1: Import `useChatStore` in `LeftSidebar.vue` if not already imported**

```typescript
import { useChatStore } from '@/stores/chat'
const chatStore = useChatStore()
```

- [ ] **Step 7.2: Add streaming dot to each session item in the template**

Find the element that renders each session item in the list. Add a conditional streaming indicator:

```vue
<span
  v-if="chatStore.isSessionStreaming(session.id)"
  class="session-streaming-dot"
  title="正在生成中"
/>
```

- [ ] **Step 7.3: Add CSS for the streaming dot**

In the `<style>` section of `LeftSidebar.vue`, add:

```css
.session-streaming-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary-color, #409eff);
  animation: pulse 1.2s ease-in-out infinite;
  margin-left: 4px;
  vertical-align: middle;
  flex-shrink: 0;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
```

- [ ] **Step 7.4: Verify TypeScript**

Run: `cd frontend && npx vue-tsc --noEmit`  
Expected: no errors.

- [ ] **Step 7.5: Commit**

```bash
git add frontend/src/components/layout/LeftSidebar.vue
git commit -m "feat(LeftSidebar): add streaming indicator dot for background sessions"
```

---

## Task 8: Remove `abandon()` from `sse-client.ts`

**Files:**
- Modify: `frontend/src/api/sse-client.ts`

- [ ] **Step 8.1: Remove the `abandon()` method**

Delete the `abandon()` method added in a previous session (it was a workaround that is now superseded by `switchToSession`):

```typescript
// DELETE this entire method:
abandon(): void {
  this.handlers.clear()
  this._streaming = false
  this._threadId = null
  // Intentionally NOT aborting _abortController ...
}
```

- [ ] **Step 8.2: Verify TypeScript**

Run: `cd frontend && npx vue-tsc --noEmit`  
Expected: no errors (no callers remain after Tasks 4+6).

- [ ] **Step 8.3: Full build check**

Run: `cd frontend && npm run build`  
Expected: exit code 0.

- [ ] **Step 8.4: Commit**

```bash
git add frontend/src/api/sse-client.ts
git commit -m "refactor(sse-client): remove abandon() superseded by switchToSession"
```

---

## Task 9: Manual verification

- [ ] **Step 9.1: Restart bfzs**

Follow the restart procedure in the dev-guide skill.

- [ ] **Step 9.2: Open session A, trigger a multi-tool agent**

Send a message that requires 3+ tool calls (e.g., ask the power agent to research something).

- [ ] **Step 9.3: Switch to session B mid-stream**

While session A is streaming, click session B in the sidebar.  
Expected:
- Session A's streaming dot appears in the left sidebar.
- Session B loads normally.
- No JavaScript errors in browser console.

- [ ] **Step 9.4: Switch back to session A**

Expected:
- All tokens generated while in the background are visible.
- If the stream has completed, the response is complete. If still streaming, new tokens continue to appear.

- [ ] **Step 9.5: After stream completes, verify cleanup**

Open browser DevTools → Application → (if using Vue DevTools) check Pinia store.  
Expected: `activeSessions` map size returns to 1 (only the currently selected session) after session A's stream finishes.

---

## Self-Review Checklist

- **Spec section 2 (Goals)**: All 5 goals covered: ✅ multi-session streaming (Tasks 2-5), ✅ no disconnect on leave (Task 4), ✅ sidebar indicator (Task 7), ✅ buffered tokens on return (Task 3-4), ✅ auto-cleanup (Task 3.3).
- **Spec section 6 (API changes)**: `isSessionStreaming` (Task 4), `switchToSession` (Task 4), `connect/disconnect/abandonStream` removed (Tasks 4, 8). Public read-only API preserved via computed delegates (Task 2).
- **Placeholder scan**: No TBDs. Every step has exact code or exact commands.
- **Type consistency**: `SessionState` defined in Task 1, used in Tasks 2-5. `createSessionState()` called in Task 4. `_createClientForSession(state, sessionId)` defined in Task 3, called in Task 4.
