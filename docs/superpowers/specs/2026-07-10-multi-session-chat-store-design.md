# Multi-Session Chat Store Design

**Date:** 2026-07-10  
**Status:** Approved  
**Scope:** Frontend only (`lc-agent` framework)

---

## 1. Problem

The current `chat.ts` Pinia store uses a single-session model: one SSE client, one `messages` array,
one `isStreaming` flag. When the user switches sessions while a stream is in progress, the store
calls `disconnect()` which aborts the underlying fetch, stopping the server-side generator before
it can save the AI response to the database.

This means:
- Switching away mid-stream silently discards the AI response.
- A user cannot start a long-running agent in session A, switch to session B to do other work,
  and return to A to see the result.
- The left sidebar cannot show which sessions are actively streaming.

---

## 2. Goals

- A user can have multiple sessions streaming simultaneously in the same browser.
- Switching sessions does not kill the SSE connection of the session being left.
- The left sidebar shows a visual indicator for each session that is actively streaming.
- When switching back to a session that was streaming in the background, the user sees all tokens
  accumulated so far plus new tokens as they arrive.
- Completed background sessions are automatically cleaned up to release memory.
- Components that use `useChatStore()` do not need to change (public API is preserved).

**Out of scope:**
- Backend changes (backend already supports concurrent SSE per thread).
- Streaming writes to DB (separate effort).
- Supporting more than one "primary" session rendering at the same time (multi-pane UI).

---

## 3. Architecture

### 3.1 Current Model (Single Session)

```
chatStore
  messages: Ref<Message[]>           ← global singleton
  isStreaming: Ref<boolean>          ← global singleton
  sseClient: ChatSseClient | null    ← global singleton
  activeSessionId: string | null

  switchSession():
    sseClient.disconnect()  ← kills server-side stream
    replace all state
    loadMessages + connect
```

### 3.2 New Model (Session Registry)

```
chatStore
  activeSessions: Map<sessionId, SessionState>  ← registry
  activeSessionId: Ref<string | null>

  // Public computed (API unchanged)
  messages       = computed → activeSessions[activeId].messages
  isStreaming    = computed → activeSessions[activeId].isStreaming
  todos          = computed → activeSessions[activeId].todos
  interrupt      = computed → activeSessions[activeId].interrupt
  errorMessage   = computed → activeSessions[activeId].errorMessage
  ...

  switchToSession(id):
    old = activeSessions[activeId]
    if old.isStreaming → keep in map (background stream continues)
    else               → delete from map (release memory)
    activeSessionId = id
    if id not in activeSessions → create SessionState, loadMessages, connect
    else                        → already loaded (was streaming in background), just switch
```

---

## 4. Data Structures

### 4.1 SessionState

Defined in `frontend/src/stores/chat-session-state.ts`:

```typescript
export interface SessionState {
  // Message data
  messages: Ref<Message[]>
  totalMessageCount: Ref<number>
  hasOlderMessages: Ref<boolean>
  loadingOlder: Ref<boolean>

  // Streaming state
  isStreaming: Ref<boolean>
  inThinking: boolean          // mutable internal flag, no Ref needed
  todos: Ref<string[]>
  interrupt: Ref<InterruptRequest | null>
  errorMessage: Ref<string | null>

  // SSE client
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
    todos: ref([]),
    interrupt: ref(null),
    errorMessage: ref(null),
    client: null,
  }
}
```

---

## 5. Key Algorithms

### 5.1 switchToSession(sessionId)

```
async function switchToSession(sessionId: string):
  if activeSessionId == sessionId: return  // already there

  // Handle departing session
  old = activeSessions.get(activeSessionId)
  if old:
    if old.isStreaming:
      // Keep in map; background SSE continues; sidebar shows indicator
      pass
    else:
      activeSessions.delete(activeSessionId)

  activeSessionId = sessionId

  // Handle arriving session
  if sessionId in activeSessions:
    // Was streaming in background — all buffered tokens already in state
    // No need to reload messages; just switch the active pointer
    return

  // New session: create state, load messages, connect SSE
  state = createSessionState()
  activeSessions.set(sessionId, state)
  await _loadMessages(sessionId, state)
  await _connect(sessionId, state)
```

### 5.2 Cleanup on Stream Done

Inside `_registerHandlers(client, state, sessionId)`, on receiving the `done` event:

```
// existing done handling (save message, refresh title) ...

// Auto-cleanup if this is a background session
if sessionId != activeSessionId:
  state.client?.disconnect()
  activeSessions.delete(sessionId)
```

This prevents orphaned sessions from consuming memory after their stream finishes.

### 5.3 sendMessage

```
async function sendMessage(content, presetId, modelId, options):
  state = activeSessions.get(activeSessionId)
  if not state or not state.client: return
  // ... existing logic using state.client
```

---

## 6. API Changes

### New public methods / properties on `useChatStore()`

| Name | Type | Purpose |
|---|---|---|
| `isSessionStreaming(id)` | `(id: string) => boolean` | Sidebar streaming indicator |
| `switchToSession(id)` | `async (id: string) => void` | Replace `connect` + `disconnect` + `loadMessages` calls |

### Removed (internal refactor, not public):
- `connect()` — replaced by `switchToSession` internals
- `disconnect()` — replaced by `switchToSession` internals
- `abandonStream()` — no longer needed (covered by switchToSession logic)

### Unchanged (public API preserved):
- `messages`, `isStreaming`, `todos`, `interrupt`, `errorMessage`, `threadId`
- `sendMessage`, `stopGeneration`, `respondToInterrupt`, `resumeInterrupt`
- `loadMessages`, `loadOlderMessages`, `clearMessages`, `truncateAfterMessage`

---

## 7. Files Affected

| File | Change Type | Notes |
|---|---|---|
| `frontend/src/stores/chat.ts` | Major refactor | Session registry, delegate computed props |
| `frontend/src/stores/chat-session-state.ts` | New file (~50 lines) | `SessionState` type + factory |
| `frontend/src/App.vue` | Minor | Replace disconnect/connect calls with `switchToSession` |
| `frontend/src/components/layout/LeftSidebar.vue` | Minor | Add streaming indicator per session |
| `frontend/src/api/sse-client.ts` | Remove `abandon()` | No longer needed |

---

## 8. Error Handling

- If `switchToSession` is called while another switch is in progress (race condition): guard with a
  `switching` flag; ignore the second call.
- If `loadMessages` fails for the arriving session: set `errorMessage` on that session's state,
  do not delete from map.
- If a background session's SSE connection errors out: log, set `errorMessage`, clean up from map.

---

## 9. Testing

- Unit: `chat.ts` is not straightforward to unit test (SSE is async); rely on E2E.
- Manual: open session A, trigger a 5-tool agent, switch to session B, watch sidebar indicator for A,
  switch back to A and verify all tokens are present.
- Verify cleanup: after A's stream finishes while in background, `activeSessions.size` returns to 0.
