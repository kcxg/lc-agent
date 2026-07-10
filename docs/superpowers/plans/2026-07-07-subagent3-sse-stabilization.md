# SubAgent3 SSE Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stabilize sub-agent SSE event semantics and state handling on the `subagent3` branch without changing the communication architecture or rewriting the UI.

**Architecture:** Keep `stream_utils.py` as the LangGraph raw-event to UIEvent converter. Add a focused backend `SubAgentRunTracker` that receives UIEvents, enriches sub-agent payloads, persists sub-session data, and is shared by `_send_stream` and `_resume_stream`. On the frontend, add explicit sub-agent SSE fields and extract reducer-style helpers from the existing Pinia callback logic while preserving current rendering behavior.

**Tech Stack:** Python 3.12 via `D:\ProgramData\Miniconda3\envs\py312\python.exe`, FastAPI SSE, LangGraph `astream_events(version="v2")`, pytest, Vue 3, Pinia, TypeScript, Vite, `vue-tsc`.

**Branch and git rule:** Work only on `subagent3`. Do not commit unless the user explicitly asks. Ignore the generic commit steps from standard planning practice for this task.

---

## Spec Reference

Design spec: `docs/superpowers/specs/2026-07-07-subagent3-sse-stabilization-design.md`

Critical decisions from the spec:

- Keep SSE; do not introduce WebSocket, MQTT, Redis Pub/Sub, Redis Streams, or EventBus in this round.
- Single-segment `tools:{id}` is not automatically a sub-agent internal event.
- Main agent calling a sub-agent is identified by `tool_name in subagent_tool_names`.
- Multi-segment namespace such as `tools:{id}|agent` identifies execution inside a nested graph.
- Existing pytest assertions that conflict with the above semantics are stale and should be updated.
- Preserve current UI behavior; only type and store organization should change.

---

## File Structure

### Backend

- Modify: `tests/test_stream_utils_subagents.py`
  - Update stale namespace tests.
  - Add explicit tests for single-segment vs multi-segment namespace behavior.
  - Add tests for sub-agent tool start/done with single-segment namespace.

- Create: `tests/test_subagent_run_tracker.py`
  - Unit-test the new tracker without running a real LangGraph agent.
  - Monkeypatch persistence and trace functions so tests are deterministic and fast.

- Create: `lc_agent/server/subagent_tracker.py`
  - Own sub-agent run state.
  - Enrich `subagent_start`, `tool_call` for sub-agent tools, and `subagent_done` payloads.
  - Accumulate sub-agent content/thinking/internal tool calls.
  - Persist sub-session creation, delegation message, and final assistant message.
  - Provide finalization for cancelled/error paths.

- Modify: `lc_agent/server/sse.py`
  - Replace inline `_sa_writers`, `_sa_create_tasks`, `_sa_finalize_tasks` logic with `SubAgentRunTracker`.
  - Use the same tracker path in `_send_stream` and `_resume_stream`.
  - Preserve main message persistence, usage, HTTP trace, title, interrupt, cancel, and lock behavior.

- Modify only if needed: `lc_agent/server/stream_utils.py`
  - Current implementation already mostly matches the intended namespace semantics.
  - Keep changes minimal; update comments only if they are misleading.

### Frontend

- Modify: `frontend/src/api/sse-client.ts`
  - Extend `SseMessage` with explicit sub-agent fields.

- Modify: `frontend/src/stores/chat.ts`
  - Export reducer helper functions near the existing type definitions.
  - Replace inline `subagent_*` callback logic with helper calls.
  - Reduce `(msg as any)` usage for sub-agent events.

- Create: `frontend/scripts/check-subagent-reducers-contract.mjs`
  - Static contract test that checks reducer helpers exist and key inline patterns were removed.
  - This repo currently uses Node-based contract scripts rather than a full frontend unit-test runner.

- Modify: `frontend/package.json`
  - Add script `test:subagent-reducers` pointing to the new contract script.

---

## Task 1: Update backend stream_utils sub-agent semantics tests

**Files:**
- Modify: `tests/test_stream_utils_subagents.py`
- Verify: `lc_agent/server/stream_utils.py`

- [ ] **Step 1: Replace stale tests with explicit namespace semantics**

Edit `tests/test_stream_utils_subagents.py` so it contains these tests:

```python
from lc_agent.server.stream_utils import (
    _extract_subagent_tool_call_id,
    _get_checkpoint_ns,
    convert_stream_event,
)


def _make_chunk(content="hello", reasoning=None):
    class Chunk:
        additional_kwargs = {}

    c = Chunk()
    c.content = content
    if reasoning:
        c.additional_kwargs = {"reasoning_content": reasoning}
    return c


def test_main_agent_token():
    event = {"event": "on_chat_model_stream", "metadata": {}, "data": {"chunk": _make_chunk("hi")}}
    results = convert_stream_event(event)
    assert results == [("token", {"content": "hi"})]


def test_single_segment_tools_namespace_is_not_subagent_internal_token():
    event = {
        "event": "on_chat_model_stream",
        "metadata": {"langgraph_checkpoint_ns": "tools:abc123"},
        "data": {"chunk": _make_chunk("main tool scoped text")},
    }
    results = convert_stream_event(event)
    assert results == [("token", {"content": "main tool scoped text"})]


def test_multi_segment_tools_namespace_is_subagent_internal_token():
    event = {
        "event": "on_chat_model_stream",
        "metadata": {"langgraph_checkpoint_ns": "tools:abc123|agent:model"},
        "data": {"chunk": _make_chunk("sub hi")},
    }
    results = convert_stream_event(event)
    assert results == [("subagent_token", {"tool_call_id": "abc123", "content": "sub hi"})]


def test_multi_segment_tools_namespace_is_subagent_internal_thinking():
    event = {
        "event": "on_chat_model_stream",
        "metadata": {"langgraph_checkpoint_ns": "tools:abc123|agent:model"},
        "data": {"chunk": _make_chunk("", reasoning="sub thought")},
    }
    results = convert_stream_event(event)
    assert results == [("subagent_thinking", {"tool_call_id": "abc123", "content": "sub thought"})]


def test_subagent_start_emitted_for_subagent_tools_with_single_segment_namespace():
    event = {
        "event": "on_tool_start",
        "name": "research_expert",
        "run_id": "run123",
        "metadata": {"langgraph_checkpoint_ns": "tools:task123"},
        "data": {"input": {"query": "quantum", "tool_call_id": "hidden"}},
    }
    results = convert_stream_event(event, subagent_tool_names={"research_expert"})
    assert results == [
        (
            "tool_call",
            {
                "name": "research_expert",
                "run_id": "task123",
                "args": {"query": "quantum"},
                "is_subagent": True,
            },
        ),
        (
            "subagent_start",
            {
                "name": "research_expert",
                "tool_call_id": "task123",
                "query": "quantum",
            },
        ),
    ]


def test_subagent_done_instead_of_tool_result_with_single_segment_namespace():
    event = {
        "event": "on_tool_end",
        "name": "research_expert",
        "run_id": "run123",
        "metadata": {"langgraph_checkpoint_ns": "tools:task123"},
        "data": {"output": "research result"},
    }
    results = convert_stream_event(event, subagent_tool_names={"research_expert"})
    assert results == [
        (
            "subagent_done",
            {
                "tool_call_id": "task123",
                "result_preview": "research result",
                "status": "done",
            },
        )
    ]


def test_subagent_internal_tool_call_and_result():
    start_event = {
        "event": "on_tool_start",
        "name": "web_search",
        "metadata": {"langgraph_checkpoint_ns": "tools:abc123|tools:inner456"},
        "data": {"input": {"q": "quantum"}},
    }
    end_event = {
        "event": "on_tool_end",
        "name": "web_search",
        "metadata": {"langgraph_checkpoint_ns": "tools:abc123|tools:inner456"},
        "data": {"output": "found"},
    }
    assert convert_stream_event(start_event, subagent_tool_names={"research_expert"}) == [
        ("subagent_tool_call", {"tool_call_id": "abc123", "name": "web_search", "args": {"q": "quantum"}})
    ]
    assert convert_stream_event(end_event, subagent_tool_names={"research_expert"}) == [
        ("subagent_tool_result", {"tool_call_id": "abc123", "name": "web_search", "result": "found"})
    ]


def test_extract_subagent_tool_call_id():
    assert _extract_subagent_tool_call_id("tools:abc123") is None
    assert _extract_subagent_tool_call_id("tools:abc123|model:def") == "abc123"
    assert _extract_subagent_tool_call_id("tools:abc123|tools:def456") == "abc123"
    assert _extract_subagent_tool_call_id("") is None


def test_get_checkpoint_ns():
    assert _get_checkpoint_ns({"metadata": {"langgraph_checkpoint_ns": "tools:abc"}}) == "tools:abc"
    assert _get_checkpoint_ns({"metadata": {}}) == ""
    assert _get_checkpoint_ns({}) == ""
```

- [ ] **Step 2: Run the focused tests and confirm current baseline**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_stream_utils_subagents.py -q
```

Expected:

```text
10 passed
```

If this fails, inspect only `lc_agent/server/stream_utils.py` and fix the smallest mismatch. Do not change broad SSE flow in this task.

---

## Task 2: Add backend SubAgentRunTracker tests first

**Files:**
- Create: `tests/test_subagent_run_tracker.py`
- Create later: `lc_agent/server/subagent_tracker.py`

- [ ] **Step 1: Write failing tracker tests**

Create `tests/test_subagent_run_tracker.py` with:

```python
import pytest


@pytest.mark.asyncio
async def test_tracker_start_token_done_persists_subsession(monkeypatch):
    from lc_agent.server import subagent_tracker
    from lc_agent.server.subagent_tracker import SubAgentRunTracker

    calls = []

    async def fake_create_subsession(db_url, sub_session_id, parent_session_id, tool_call_id, agent_id, title, user_id=""):
        calls.append(("create", db_url, sub_session_id, parent_session_id, tool_call_id, agent_id, title, user_id))

    async def fake_delegation(db_url, sub_session_id, query):
        calls.append(("delegation", db_url, sub_session_id, query))

    async def fake_finalize(db_url, sub_session_id, content, tool_calls=None, http_traces=None):
        calls.append(("finalize", db_url, sub_session_id, content, tool_calls, http_traces))

    monkeypatch.setattr(subagent_tracker.persistence, "create_subsession", fake_create_subsession)
    monkeypatch.setattr(subagent_tracker.persistence, "save_subsession_delegation_message", fake_delegation)
    monkeypatch.setattr(subagent_tracker.persistence, "finalize_subsession_message", fake_finalize)
    monkeypatch.setattr(subagent_tracker, "pop_subagent_traces", lambda sub_session_id: [{"id": "trace1"}])

    tool_calls = [{"name": "research_expert", "runId": "task123", "status": "running"}]
    tracker = SubAgentRunTracker(
        db_url="sqlite+aiosqlite:///test.db",
        parent_thread_id="parent1",
        user_id="user1",
        subagent_display_map={"research_expert": "研究专家"},
        tool_calls=tool_calls,
    )

    start_type, start_payload = tracker.handle_event("subagent_start", {
        "name": "research_expert",
        "tool_call_id": "task123",
        "query": "quantum",
    })
    assert start_type == "subagent_start"
    assert start_payload["name"] == "研究专家"
    assert start_payload["sub_session_id"] == "parent1--sa--task123"
    assert tool_calls[0]["is_subagent"] is True
    assert tool_calls[0]["sub_session_id"] == "parent1--sa--task123"
    assert tool_calls[0]["name"] == "研究专家"

    assert tracker.handle_event("subagent_token", {"tool_call_id": "task123", "content": "hello"}) == (
        "subagent_token",
        {"tool_call_id": "task123", "content": "hello"},
    )
    assert tracker.handle_event("subagent_token", {"tool_call_id": "task123", "content": " world"}) == (
        "subagent_token",
        {"tool_call_id": "task123", "content": " world"},
    )

    done_type, done_payload = tracker.handle_event("subagent_done", {
        "tool_call_id": "task123",
        "result_preview": "ignored fallback",
        "status": "done",
    })
    assert done_type == "subagent_done"
    assert done_payload["tool_call_id"] == "task123"
    assert done_payload["result_preview"] == "hello world"
    assert done_payload["status"] == "done"
    assert done_payload["token_count"] == 2
    assert done_payload["tool_count"] == 0
    assert done_payload["http_traces"] == [{"id": "trace1"}]

    await tracker.drain()
    assert calls[0] == (
        "create",
        "sqlite+aiosqlite:///test.db",
        "parent1--sa--task123",
        "parent1",
        "task123",
        "研究专家",
        "研究专家: quantum",
        "user1",
    )
    assert calls[1] == ("delegation", "sqlite+aiosqlite:///test.db", "parent1--sa--task123", "quantum")
    assert calls[2] == (
        "finalize",
        "sqlite+aiosqlite:///test.db",
        "parent1--sa--task123",
        "hello world",
        None,
        [{"id": "trace1"}],
    )


@pytest.mark.asyncio
async def test_tracker_records_thinking_and_internal_tools(monkeypatch):
    from lc_agent.server import subagent_tracker
    from lc_agent.server.subagent_tracker import SubAgentRunTracker

    finalized = []

    async def fake_noop(*args, **kwargs):
        return None

    async def fake_finalize(db_url, sub_session_id, content, tool_calls=None, http_traces=None):
        finalized.append((content, tool_calls, http_traces))

    monkeypatch.setattr(subagent_tracker.persistence, "create_subsession", fake_noop)
    monkeypatch.setattr(subagent_tracker.persistence, "save_subsession_delegation_message", fake_noop)
    monkeypatch.setattr(subagent_tracker.persistence, "finalize_subsession_message", fake_finalize)
    monkeypatch.setattr(subagent_tracker, "pop_subagent_traces", lambda sub_session_id: None)

    tracker = SubAgentRunTracker(
        db_url="db",
        parent_thread_id="parent1",
        user_id="",
        subagent_display_map={},
        tool_calls=[],
    )
    tracker.handle_event("subagent_start", {"name": "research_expert", "tool_call_id": "task123", "query": "q"})
    tracker.handle_event("subagent_thinking", {"tool_call_id": "task123", "content": "think"})
    tracker.handle_event("subagent_token", {"tool_call_id": "task123", "content": "answer"})
    tracker.handle_event("subagent_tool_call", {"tool_call_id": "task123", "name": "search", "args": {"q": "x"}})
    tracker.handle_event("subagent_tool_result", {"tool_call_id": "task123", "name": "search", "result": "result"})
    _, done_payload = tracker.handle_event("subagent_done", {"tool_call_id": "task123", "status": "done"})

    assert done_payload["tool_count"] == 1
    assert done_payload["token_count"] == 1
    await tracker.drain()

    assert finalized[0][0] == "<!--THINK_START-->think<!--THINK_END-->answer\n<!--TOOL:0-->\n"
    assert finalized[0][1][0]["name"] == "search"
    assert finalized[0][1][0]["status"] == "done"
    assert finalized[0][1][0]["result"] == "result"


@pytest.mark.asyncio
async def test_tracker_finalize_open_runs_marks_error(monkeypatch):
    from lc_agent.server import subagent_tracker
    from lc_agent.server.subagent_tracker import SubAgentRunTracker

    finalized = []

    async def fake_noop(*args, **kwargs):
        return None

    async def fake_finalize(db_url, sub_session_id, content, tool_calls=None, http_traces=None):
        finalized.append((sub_session_id, content, tool_calls, http_traces))

    monkeypatch.setattr(subagent_tracker.persistence, "create_subsession", fake_noop)
    monkeypatch.setattr(subagent_tracker.persistence, "save_subsession_delegation_message", fake_noop)
    monkeypatch.setattr(subagent_tracker.persistence, "finalize_subsession_message", fake_finalize)
    monkeypatch.setattr(subagent_tracker, "pop_subagent_traces", lambda sub_session_id: None)

    tracker = SubAgentRunTracker(
        db_url="db",
        parent_thread_id="parent1",
        user_id="",
        subagent_display_map={},
        tool_calls=[],
    )
    tracker.handle_event("subagent_start", {"name": "research_expert", "tool_call_id": "task123", "query": "q"})
    tracker.handle_event("subagent_token", {"tool_call_id": "task123", "content": "partial"})

    terminal_events = tracker.finalize_open_runs(status="error")
    assert terminal_events == [
        (
            "subagent_done",
            {
                "tool_call_id": "task123",
                "result_preview": "partial",
                "status": "error",
                "duration": terminal_events[0][1]["duration"],
                "tool_count": 0,
                "token_count": 1,
            },
        )
    ]
    await tracker.drain()
    assert finalized[0][0] == "parent1--sa--task123"
    assert finalized[0][1] == "partial"
```

- [ ] **Step 2: Run tracker tests and verify they fail because module does not exist yet**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_subagent_run_tracker.py -q
```

Expected before implementation:

```text
FAILED ... ModuleNotFoundError: No module named 'lc_agent.server.subagent_tracker'
```

---

## Task 3: Implement SubAgentRunTracker

**Files:**
- Create: `lc_agent/server/subagent_tracker.py`
- Test: `tests/test_subagent_run_tracker.py`

- [ ] **Step 1: Create tracker implementation**

Create `lc_agent/server/subagent_tracker.py` with:

```python
import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from lc_agent.core.http_trace import pop_subagent_traces
from lc_agent.server import persistence


@dataclass
class SubAgentRunState:
    tool_call_id: str
    sub_session_id: str
    name: str
    query: str
    content_parts: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    token_count: int = 0
    in_thinking: bool = False
    start_time: float = field(default_factory=time.time)
    status: str = "running"


class SubAgentRunTracker:
    def __init__(
        self,
        *,
        db_url: str,
        parent_thread_id: str,
        user_id: str,
        subagent_display_map: dict[str, str],
        tool_calls: list[dict[str, Any]],
    ) -> None:
        self.db_url = db_url
        self.parent_thread_id = parent_thread_id
        self.user_id = user_id
        self.subagent_display_map = subagent_display_map
        self.parent_tool_calls = tool_calls
        self._runs: dict[str, SubAgentRunState] = {}
        self._tasks: list[asyncio.Task] = []

    def handle_event(self, event_type: str, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        if event_type == "tool_call" and payload.get("is_subagent"):
            return event_type, self._enrich_subagent_tool_call(payload)
        if event_type == "subagent_start":
            return event_type, self._handle_start(payload)
        if event_type == "subagent_thinking":
            self._handle_thinking(payload)
            return event_type, payload
        if event_type == "subagent_token":
            self._handle_token(payload)
            return event_type, payload
        if event_type == "subagent_tool_call":
            self._handle_tool_call(payload)
            return event_type, payload
        if event_type == "subagent_tool_result":
            self._handle_tool_result(payload)
            return event_type, payload
        if event_type == "subagent_done":
            return event_type, self._handle_done(payload)
        return event_type, payload

    def finalize_open_runs(self, *, status: str) -> list[tuple[str, dict[str, Any]]]:
        events: list[tuple[str, dict[str, Any]]] = []
        for tool_call_id in list(self._runs.keys()):
            events.append(("subagent_done", self._handle_done({"tool_call_id": tool_call_id, "status": status})))
        return events

    async def drain(self) -> None:
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

    def _display_name(self, name: str) -> str:
        return self.subagent_display_map.get(name) or name

    def _sub_session_id(self, tool_call_id: str) -> str:
        return f"{self.parent_thread_id}--sa--{tool_call_id}"

    def _enrich_subagent_tool_call(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw_name = payload.get("name", "")
        enriched = {**payload, "name": self._display_name(raw_name)}
        run_id = enriched.get("run_id")
        if run_id and not enriched.get("sub_session_id"):
            enriched["sub_session_id"] = self._sub_session_id(str(run_id))
        return enriched

    def _handle_start(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw_name = payload.get("name", "sub-agent")
        display_name = self._display_name(raw_name)
        tool_call_id = str(payload.get("tool_call_id") or payload.get("run_id") or "")
        sub_session_id = payload.get("sub_session_id") or self._sub_session_id(tool_call_id)
        query = str(payload.get("query") or "")

        state = SubAgentRunState(
            tool_call_id=tool_call_id,
            sub_session_id=sub_session_id,
            name=display_name,
            query=query,
        )
        self._runs[tool_call_id] = state
        self._mark_parent_tool_call(tool_call_id, display_name, sub_session_id)

        self._tasks.append(asyncio.create_task(persistence.create_subsession(
            self.db_url,
            sub_session_id,
            self.parent_thread_id,
            tool_call_id,
            agent_id=display_name,
            title=f"{display_name}: {query[:30]}",
            user_id=self.user_id,
        )))
        self._tasks.append(asyncio.create_task(persistence.save_subsession_delegation_message(
            self.db_url,
            sub_session_id,
            query,
        )))

        return {
            **payload,
            "name": display_name,
            "tool_call_id": tool_call_id,
            "sub_session_id": sub_session_id,
            "query": query,
        }

    def _mark_parent_tool_call(self, tool_call_id: str, display_name: str, sub_session_id: str) -> None:
        for tool_call in self.parent_tool_calls:
            if tool_call.get("runId") == tool_call_id or tool_call.get("run_id") == tool_call_id:
                tool_call["is_subagent"] = True
                tool_call["sub_session_id"] = sub_session_id
                tool_call["name"] = display_name
                break

    def _handle_thinking(self, payload: dict[str, Any]) -> None:
        state = self._runs.get(str(payload.get("tool_call_id") or ""))
        if state is None:
            return
        if not state.in_thinking:
            state.content_parts.append("<!--THINK_START-->")
            state.in_thinking = True
        state.content_parts.append(str(payload.get("content") or ""))

    def _handle_token(self, payload: dict[str, Any]) -> None:
        state = self._runs.get(str(payload.get("tool_call_id") or ""))
        if state is None:
            return
        if state.in_thinking:
            state.content_parts.append("<!--THINK_END-->")
            state.in_thinking = False
        state.content_parts.append(str(payload.get("content") or ""))
        state.token_count += 1

    def _handle_tool_call(self, payload: dict[str, Any]) -> None:
        state = self._runs.get(str(payload.get("tool_call_id") or ""))
        if state is None:
            return
        if state.in_thinking:
            state.content_parts.append("<!--THINK_END-->")
            state.in_thinking = False
        tool_idx = len(state.tool_calls)
        state.content_parts.append(f"\n<!--TOOL:{tool_idx}-->\n")
        state.tool_calls.append({
            "name": payload.get("name", ""),
            "args": payload.get("args"),
            "status": "running",
            "startTime": int(time.time() * 1000),
        })

    def _handle_tool_result(self, payload: dict[str, Any]) -> None:
        state = self._runs.get(str(payload.get("tool_call_id") or ""))
        if state is None:
            return
        name = payload.get("name", "")
        now_ms = int(time.time() * 1000)
        for tool_call in reversed(state.tool_calls):
            if tool_call.get("name") == name and tool_call.get("status") == "running":
                tool_call["result"] = payload.get("result")
                tool_call["status"] = "done"
                tool_call["duration"] = now_ms - tool_call.get("startTime", now_ms)
                break

    def _handle_done(self, payload: dict[str, Any]) -> dict[str, Any]:
        tool_call_id = str(payload.get("tool_call_id") or "")
        state = self._runs.pop(tool_call_id, None)
        if state is None:
            return payload

        if state.in_thinking:
            state.content_parts.append("<!--THINK_END-->")
            state.in_thinking = False

        status = str(payload.get("status") or "done")
        state.status = status
        content = "".join(state.content_parts)
        http_traces = pop_subagent_traces(state.sub_session_id) or None
        self._tasks.append(asyncio.create_task(persistence.finalize_subsession_message(
            self.db_url,
            state.sub_session_id,
            content,
            tool_calls=state.tool_calls or None,
            http_traces=http_traces,
        )))

        duration = int((time.time() - state.start_time) * 1000)
        enriched = {
            **payload,
            "tool_call_id": tool_call_id,
            "result_preview": content or payload.get("result_preview", ""),
            "status": status,
            "duration": duration,
            "tool_count": len(state.tool_calls),
            "token_count": state.token_count,
        }
        if http_traces:
            enriched["http_traces"] = http_traces
        return enriched
```

- [ ] **Step 2: Run tracker tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_subagent_run_tracker.py -q
```

Expected:

```text
3 passed
```

- [ ] **Step 3: Run stream_utils tests again**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_stream_utils_subagents.py -q
```

Expected:

```text
10 passed
```

---

## Task 4: Refactor `_send_stream` to use SubAgentRunTracker

**Files:**
- Modify: `lc_agent/server/sse.py`
- Test: `tests/test_subagent_run_tracker.py`, `tests/test_stream_utils_subagents.py`, `tests/test_engine_subagents.py`

- [ ] **Step 1: Add import**

In `lc_agent/server/sse.py`, add this import near the existing server imports:

```python
from lc_agent.server.subagent_tracker import SubAgentRunTracker
```

- [ ] **Step 2: Replace `_send_stream` local sub-agent writer variables**

Inside `_send_stream.event_stream()`, replace:

```python
            _sa_writers: dict[str, dict] = {}
            _sa_finalize_tasks: list[asyncio.Task] = []
            _sa_create_tasks: list[asyncio.Task] = []
```

with:

```python
            subagent_tracker = SubAgentRunTracker(
                db_url=_db_url,
                parent_thread_id=thread_id,
                user_id=user.id if user else "",
                subagent_display_map=subagent_display_map,
                tool_calls=tool_calls,
            )
```

- [ ] **Step 3: Replace inline event enrichment and writer updates in `_send_stream`**

In the loop over `convert_stream_event`, replace the whole sub-agent-specific block from the first `if evt_type == "subagent_start":` through the final `elif evt_type == "subagent_done": pass` with:

```python
                        evt_type, evt_data = subagent_tracker.handle_event(evt_type, evt_data)
                        yield stream_utils.format_sse_event(evt_type, evt_data)
                        last_event_time = time.time()
```

The resulting section should look like:

```python
                    for evt_type, evt_data in stream_utils.convert_stream_event(
                        event, subagent_tool_names=subagent_tool_names,
                    ):
                        evt_type, evt_data = subagent_tracker.handle_event(evt_type, evt_data)
                        yield stream_utils.format_sse_event(evt_type, evt_data)
                        last_event_time = time.time()
```

- [ ] **Step 4: Finalize open sub-agent runs on cancel in `_send_stream`**

Replace the cancel branch:

```python
                    if _cancel_flags.get(thread_id):
                        yield stream_utils.format_sse_event("cancelled", {})
                        return
```

with:

```python
                    if _cancel_flags.get(thread_id):
                        for evt_type, evt_data in subagent_tracker.finalize_open_runs(status="error"):
                            yield stream_utils.format_sse_event(evt_type, evt_data)
                        await subagent_tracker.drain()
                        yield stream_utils.format_sse_event("cancelled", {})
                        return
```

- [ ] **Step 5: Finalize open sub-agent runs on disconnect in `_send_stream`**

Replace:

```python
                    if await request.is_disconnected():
                        _cancel_flags[thread_id] = True
                        return
```

with:

```python
                    if await request.is_disconnected():
                        _cancel_flags[thread_id] = True
                        for evt_type, evt_data in subagent_tracker.finalize_open_runs(status="error"):
                            yield stream_utils.format_sse_event(evt_type, evt_data)
                        await subagent_tracker.drain()
                        return
```

- [ ] **Step 6: Replace sub-agent task gather before main message persistence**

Replace:

```python
            # Ensure all sub-agent create/finalize tasks complete before persisting main message
            all_sa_tasks = _sa_create_tasks + _sa_finalize_tasks
            if all_sa_tasks:
                await asyncio.gather(*all_sa_tasks, return_exceptions=True)
```

with:

```python
            await subagent_tracker.drain()
```

- [ ] **Step 7: Finalize open sub-agent runs in exception path**

Inside `_send_stream.event_stream()` exception handler, before yielding the error event, add:

```python
            for evt_type, evt_data in subagent_tracker.finalize_open_runs(status="error"):
                yield stream_utils.format_sse_event(evt_type, evt_data)
            await subagent_tracker.drain()
```

The exception handler should become:

```python
        except Exception as e:
            traceback.print_exc()
            for evt_type, evt_data in subagent_tracker.finalize_open_runs(status="error"):
                yield stream_utils.format_sse_event(evt_type, evt_data)
            await subagent_tracker.drain()
            error_info = stream_utils.categorize_error(e)
            error_info["tech_detail"] = str(e)
            error_info["message"] = str(e)
            yield stream_utils.format_sse_event("error", error_info)
```

- [ ] **Step 8: Run backend focused tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_stream_utils_subagents.py tests/test_subagent_run_tracker.py tests/test_engine_subagents.py -q
```

Expected:

```text
15 passed
```

The exact number may be higher if more tests are added, but there should be no failures.

---

## Task 5: Refactor `_resume_stream` to share SubAgentRunTracker

**Files:**
- Modify: `lc_agent/server/sse.py`
- Test: backend focused tests

- [ ] **Step 1: Initialize tracker in `_resume_stream.event_stream()` after `tool_calls` and display map exist**

After:

```python
            subagent_display_map = engine.get_subagent_display_name_map(
                preset_id, model_id=model_id or "", llm_params=llm_params,
            )
            subagent_tool_names = set(subagent_display_map.keys())
```

add:

```python
            subagent_tracker = SubAgentRunTracker(
                db_url=_db_url,
                parent_thread_id=thread_id,
                user_id=user.id if user else "",
                subagent_display_map=subagent_display_map,
                tool_calls=tool_calls,
            )
```

- [ ] **Step 2: Replace `_resume_stream` event enrichment with tracker**

Replace:

```python
                    for evt_type, evt_data in stream_utils.convert_stream_event(
                        event, subagent_tool_names=subagent_tool_names,
                    ):
                        if evt_type == "subagent_start":
                            tool_name = evt_data.get("name", "")
                            display_name = subagent_display_map.get(tool_name) or tool_name
                            sa_tid_pre = evt_data["tool_call_id"]
                            evt_data = {
                                **evt_data,
                                "name": display_name,
                                "sub_session_id": f"{thread_id}--sa--{sa_tid_pre}",
                            }
                        yield stream_utils.format_sse_event(evt_type, evt_data)
                        last_event_time = time.time()
```

with:

```python
                    for evt_type, evt_data in stream_utils.convert_stream_event(
                        event, subagent_tool_names=subagent_tool_names,
                    ):
                        evt_type, evt_data = subagent_tracker.handle_event(evt_type, evt_data)
                        yield stream_utils.format_sse_event(evt_type, evt_data)
                        last_event_time = time.time()
```

- [ ] **Step 3: Finalize open sub-agent runs on cancel and disconnect in `_resume_stream`**

Replace the cancel branch with:

```python
                    if _cancel_flags.get(thread_id):
                        for evt_type, evt_data in subagent_tracker.finalize_open_runs(status="error"):
                            yield stream_utils.format_sse_event(evt_type, evt_data)
                        await subagent_tracker.drain()
                        yield stream_utils.format_sse_event("cancelled", {})
                        return
```

Replace the disconnect branch with:

```python
                    if await request.is_disconnected():
                        _cancel_flags[thread_id] = True
                        for evt_type, evt_data in subagent_tracker.finalize_open_runs(status="error"):
                            yield stream_utils.format_sse_event(evt_type, evt_data)
                        await subagent_tracker.drain()
                        return
```

- [ ] **Step 4: Drain tracker before appending resume content**

Before:

```python
            new_content = "".join(content_parts)
```

add:

```python
            await subagent_tracker.drain()
```

- [ ] **Step 5: Finalize open sub-agent runs in `_resume_stream` exception path**

Inside `_resume_stream.event_stream()` exception handler, before yielding the error event, add the same pattern:

```python
            for evt_type, evt_data in subagent_tracker.finalize_open_runs(status="error"):
                yield stream_utils.format_sse_event(evt_type, evt_data)
            await subagent_tracker.drain()
```

If Python scope complains that `subagent_tracker` may be undefined before initialization, initialize it to `None` near the top of `event_stream()` and guard the exception path:

```python
            if subagent_tracker is not None:
                for evt_type, evt_data in subagent_tracker.finalize_open_runs(status="error"):
                    yield stream_utils.format_sse_event(evt_type, evt_data)
                await subagent_tracker.drain()
```

- [ ] **Step 6: Run backend focused tests**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_stream_utils_subagents.py tests/test_subagent_run_tracker.py tests/test_engine_subagents.py -q
```

Expected: all pass.

---

## Task 6: Add frontend sub-agent SSE fields

**Files:**
- Modify: `frontend/src/api/sse-client.ts`

- [ ] **Step 1: Extend `SseMessage`**

In `frontend/src/api/sse-client.ts`, extend the `SseMessage` interface by adding these optional fields after `run_id?: string`:

```typescript
  tool_call_id?: string
  sub_session_id?: string
  query?: string
  status?: 'running' | 'done' | 'error' | string
  result_preview?: string
  duration?: number
  tool_count?: number
  token_count?: number
```

Keep the existing `http_traces?: any[]` field as-is.

- [ ] **Step 2: Run frontend type/build check**

Run:

```powershell
npm run build
```

Working directory:

```text
D:\codes\lc-agent\frontend
```

Expected: `vue-tsc --noEmit` and `vite build` complete successfully.

---

## Task 7: Extract frontend sub-agent reducer helpers

**Files:**
- Modify: `frontend/src/stores/chat.ts`

- [ ] **Step 1: Add helper functions after `normalizeHttpTraces`**

In `frontend/src/stores/chat.ts`, after `normalizeHttpTraces`, add:

```typescript
export function applySubAgentStart(message: ChatMessage, msg: SseMessage, fallbackThreadId?: string | null): boolean {
  if (message.role !== 'assistant') return false
  const toolCallId = msg.tool_call_id || msg.run_id || ''
  if (!toolCallId) return false
  const subSessionId = msg.sub_session_id || (fallbackThreadId ? `${fallbackThreadId}--sa--${toolCallId}` : '')
  const entry: SubAgentEntry = {
    tool_call_id: toolCallId,
    name: msg.name || '',
    sub_session_id: subSessionId,
    query: msg.query || '',
    status: 'running',
    tokenPreview: '',
    toolCallCount: 0,
    tokenCount: 0,
    tokens: '',
    thinking: '',
    thinkCount: 0,
    innerToolCalls: [],
  }
  if (!message.subAgents) {
    message.subAgents = {}
  }
  message.subAgents[toolCallId] = entry
  const tc = message.toolCalls?.find(t => t.runId === toolCallId)
  if (tc) {
    tc.is_subagent = true
    tc.sub_session_id = subSessionId
  }
  return true
}

export function applySubAgentToken(message: ChatMessage, msg: SseMessage): number | null {
  if (!message.subAgents || !msg.tool_call_id) return null
  const sa = message.subAgents[msg.tool_call_id]
  if (!sa) return null
  const newCount = sa.tokenCount + 1
  message.subAgents[msg.tool_call_id] = {
    ...sa,
    tokens: sa.tokens + (msg.content || ''),
    tokenCount: newCount,
  }
  return newCount
}

export function applySubAgentThinking(message: ChatMessage, msg: SseMessage): number | null {
  if (!message.subAgents || !msg.tool_call_id) return null
  const sa = message.subAgents[msg.tool_call_id]
  if (!sa) return null
  const newThinkCount = sa.thinkCount + 1
  message.subAgents[msg.tool_call_id] = {
    ...sa,
    thinking: sa.thinking + (msg.content || ''),
    thinkCount: newThinkCount,
  }
  return newThinkCount
}

export function applySubAgentToolCall(message: ChatMessage, msg: SseMessage): boolean {
  if (!message.subAgents || !msg.tool_call_id) return false
  const sa = message.subAgents[msg.tool_call_id]
  if (!sa) return false
  message.subAgents[msg.tool_call_id] = {
    ...sa,
    innerToolCalls: [...sa.innerToolCalls, {
      name: msg.name || '',
      status: 'running',
      args: msg.args,
    }],
    toolCallCount: sa.toolCallCount + 1,
  }
  return true
}

export function applySubAgentToolResult(message: ChatMessage, msg: SseMessage): boolean {
  if (!message.subAgents || !msg.tool_call_id) return false
  const sa = message.subAgents[msg.tool_call_id]
  if (!sa) return false
  const updatedCalls = [...sa.innerToolCalls]
  const idx = [...updatedCalls].reverse().findIndex(
    t => t.name === msg.name && t.status === 'running',
  )
  if (idx === -1) return false
  const realIdx = updatedCalls.length - 1 - idx
  updatedCalls[realIdx] = { ...updatedCalls[realIdx], result: msg.result, status: 'done' }
  message.subAgents[msg.tool_call_id] = { ...sa, innerToolCalls: updatedCalls }
  return true
}

export function applySubAgentDone(message: ChatMessage, msg: SseMessage): boolean {
  if (!msg.tool_call_id) return false
  const sa = message.subAgents?.[msg.tool_call_id]
  const saHttpTraces = msg.http_traces?.length ? normalizeHttpTraces(msg.http_traces) : undefined
  if (sa && message.subAgents) {
    message.subAgents[msg.tool_call_id] = {
      ...sa,
      status: msg.status === 'error' ? 'error' : 'done',
      tokens: sa.tokens,
      tokenPreview: sa.tokens || msg.result_preview || '',
      duration: msg.duration ?? sa.duration,
      httpTraces: saHttpTraces,
    }
  }
  const tc = message.toolCalls?.find(t => t.runId === msg.tool_call_id)
  if (tc) {
    tc.status = msg.status === 'error' ? 'error' : 'done'
    tc.result = sa?.tokens || msg.result_preview || ''
    tc.duration = tc.startTime ? Date.now() - tc.startTime : msg.duration
    tc.resultLength = (tc.result || '').length
  }
  return !!sa || !!tc
}
```

- [ ] **Step 2: Replace `subagent_start` callback body**

Replace the current `client.on('subagent_start', ...)` body with:

```typescript
    client.on('subagent_start', (msg: SseMessage) => {
      const last = messages.value[messages.value.length - 1]
      if (!last) return
      if (applySubAgentStart(last, msg, threadId.value)) {
        messages.value = [...messages.value]
      }
    })
```

- [ ] **Step 3: Replace `subagent_token` callback body**

Replace with:

```typescript
    client.on('subagent_token', (msg: SseMessage) => {
      const last = messages.value[messages.value.length - 1]
      if (!last) return
      const newCount = applySubAgentToken(last, msg)
      if (newCount !== null && newCount % 3 === 0) {
        messages.value = [...messages.value]
      }
    })
```

- [ ] **Step 4: Replace `subagent_thinking` callback body**

Replace with:

```typescript
    client.on('subagent_thinking', (msg: SseMessage) => {
      const last = messages.value[messages.value.length - 1]
      if (!last) return
      const newThinkCount = applySubAgentThinking(last, msg)
      if (newThinkCount !== null && newThinkCount % 5 === 0) {
        messages.value = [...messages.value]
      }
    })
```

- [ ] **Step 5: Replace `subagent_tool_call` callback body**

Replace with:

```typescript
    client.on('subagent_tool_call', (msg: SseMessage) => {
      const last = messages.value[messages.value.length - 1]
      if (!last) return
      if (applySubAgentToolCall(last, msg)) {
        messages.value = [...messages.value]
      }
    })
```

- [ ] **Step 6: Replace `subagent_tool_result` callback body**

Replace with:

```typescript
    client.on('subagent_tool_result', (msg: SseMessage) => {
      const last = messages.value[messages.value.length - 1]
      if (!last) return
      if (applySubAgentToolResult(last, msg)) {
        messages.value = [...messages.value]
      }
    })
```

- [ ] **Step 7: Replace `subagent_done` callback body**

Replace with:

```typescript
    client.on('subagent_done', (msg: SseMessage) => {
      const last = messages.value[messages.value.length - 1]
      if (!last) return
      if (applySubAgentDone(last, msg)) {
        messages.value = [...messages.value]
      }
    })
```

- [ ] **Step 8: Run frontend build**

Run in `D:\codes\lc-agent\frontend`:

```powershell
npm run build
```

Expected: success.

---

## Task 8: Add frontend reducer contract script

**Files:**
- Create: `frontend/scripts/check-subagent-reducers-contract.mjs`
- Modify: `frontend/package.json`
- Test: `frontend/src/stores/chat.ts`

- [ ] **Step 1: Create contract script**

Create `frontend/scripts/check-subagent-reducers-contract.mjs` with:

```javascript
import fs from 'node:fs'
import path from 'node:path'

const repoRoot = process.cwd()
const chatPath = path.join(repoRoot, 'src', 'stores', 'chat.ts')
const content = fs.readFileSync(chatPath, 'utf8')

const requiredExports = [
  'export function applySubAgentStart',
  'export function applySubAgentToken',
  'export function applySubAgentThinking',
  'export function applySubAgentToolCall',
  'export function applySubAgentToolResult',
  'export function applySubAgentDone',
]

for (const marker of requiredExports) {
  if (!content.includes(marker)) {
    throw new Error(`Missing reducer helper: ${marker}`)
  }
}

const callbackExpectations = [
  "client.on('subagent_start'",
  'applySubAgentStart(last, msg, threadId.value)',
  "client.on('subagent_token'",
  'applySubAgentToken(last, msg)',
  "client.on('subagent_thinking'",
  'applySubAgentThinking(last, msg)',
  "client.on('subagent_tool_call'",
  'applySubAgentToolCall(last, msg)',
  "client.on('subagent_tool_result'",
  'applySubAgentToolResult(last, msg)',
  "client.on('subagent_done'",
  'applySubAgentDone(last, msg)',
]

for (const marker of callbackExpectations) {
  if (!content.includes(marker)) {
    throw new Error(`Missing callback usage: ${marker}`)
  }
}

const subagentCallbackRegion = content.slice(
  content.indexOf("client.on('subagent_start'"),
  content.indexOf("client.on('interrupt'"),
)

if (subagentCallbackRegion.includes('(msg as any).tool_call_id')) {
  throw new Error('Sub-agent callbacks still cast tool_call_id through any')
}

console.log('Sub-agent reducer contract passed')
```

- [ ] **Step 2: Add npm script**

In `frontend/package.json`, add a script entry after `test:chat-http-ui`:

```json
"test:subagent-reducers": "node scripts/check-subagent-reducers-contract.mjs",
```

Ensure JSON commas remain valid.

- [ ] **Step 3: Run contract script**

Run in `D:\codes\lc-agent\frontend`:

```powershell
npm run test:subagent-reducers
```

Expected:

```text
Sub-agent reducer contract passed
```

- [ ] **Step 4: Run frontend build again**

Run:

```powershell
npm run build
```

Expected: success.

---

## Task 9: Full focused verification

**Files:**
- Backend tests
- Frontend scripts/build

- [ ] **Step 1: Run backend focused test set**

Run in `D:\codes\lc-agent`:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/test_stream_utils_subagents.py tests/test_subagent_run_tracker.py tests/test_engine_subagents.py -q
```

Expected: all pass.

- [ ] **Step 2: Run broader backend tests if focused tests pass**

Run:

```powershell
D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/ -q
```

Expected: all relevant current tests pass. If unrelated stale tests fail, report them separately with file/test names and do not silently change unrelated code.

- [ ] **Step 3: Run frontend reducer contract**

Run in `D:\codes\lc-agent\frontend`:

```powershell
npm run test:subagent-reducers
```

Expected: pass.

- [ ] **Step 4: Run frontend build/typecheck**

Run in `D:\codes\lc-agent\frontend`:

```powershell
npm run build
```

Expected: pass.

- [ ] **Step 5: Inspect working tree without committing**

Run in `D:\codes\lc-agent`:

```powershell
git status --short
```

Expected changed files:

```text
 M frontend/package.json
 M frontend/src/api/sse-client.ts
 M frontend/src/stores/chat.ts
 M lc_agent/server/sse.py
 M tests/test_stream_utils_subagents.py
?? frontend/scripts/check-subagent-reducers-contract.mjs
?? lc_agent/server/subagent_tracker.py
?? tests/test_subagent_run_tracker.py
```

Also expect the already-created spec/plan docs to appear if they are not tracked yet.

---

## Plan Self-Review

- Spec coverage: The plan covers backend event semantics, tracker extraction, `_send_stream`/`_resume_stream` convergence, frontend type additions, frontend reducer helper extraction, and test strategy.
- Placeholder scan: No TBD/TODO placeholders are used as implementation instructions. Each code-changing step includes exact target files and concrete code blocks.
- Type consistency: Backend uses `tool_call_id`, `sub_session_id`, `result_preview`, `tool_count`, `token_count`, and `duration` consistently. Frontend `SseMessage` fields match reducer helper usage.
- Scope check: The plan does not migrate SSE, add Redis/MQTT/WebSocket, rewrite UI components, or change database schema.
- User constraint check: The plan explicitly avoids git commits and uses the Python 3.12 conda interpreter for backend verification.
