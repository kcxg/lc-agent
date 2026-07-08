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


def test_regular_tool_with_single_segment_namespace_emits_normal_tool_events():
    start_event = {
        "event": "on_tool_start",
        "name": "calculator",
        "run_id": "run-tool-123",
        "metadata": {"langgraph_checkpoint_ns": "tools:regular-task-123"},
        "data": {"input": {"expression": "1 + 1"}},
    }
    end_event = {
        "event": "on_tool_end",
        "name": "calculator",
        "run_id": "run-tool-123",
        "metadata": {"langgraph_checkpoint_ns": "tools:regular-task-123"},
        "data": {"output": "2"},
    }
    assert convert_stream_event(start_event, subagent_tool_names={"research_expert"}) == [
        ("tool_call", {"name": "calculator", "run_id": "run-tool-123", "args": {"expression": "1 + 1"}})
    ]
    assert convert_stream_event(end_event, subagent_tool_names={"research_expert"}) == [
        ("tool_result", {"name": "calculator", "result": "2"})
    ]


def test_subagent_tool_without_namespace_falls_back_to_run_id():
    start_event = {
        "event": "on_tool_start",
        "name": "research_expert",
        "run_id": "run123",
        "metadata": {},
        "data": {"input": {"query": "quantum", "tool_call_id": "hidden"}},
    }
    end_event = {
        "event": "on_tool_end",
        "name": "research_expert",
        "run_id": "run123",
        "metadata": {},
        "data": {"output": "research result"},
    }
    assert convert_stream_event(start_event, subagent_tool_names={"research_expert"}) == [
        (
            "tool_call",
            {
                "name": "research_expert",
                "run_id": "run123",
                "args": {"query": "quantum"},
                "is_subagent": True,
            },
        ),
        (
            "subagent_start",
            {
                "name": "research_expert",
                "tool_call_id": "run123",
                "query": "quantum",
            },
        ),
    ]
    assert convert_stream_event(end_event, subagent_tool_names={"research_expert"}) == [
        (
            "subagent_done",
            {
                "tool_call_id": "run123",
                "result_preview": "research result",
                "status": "done",
            },
        )
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
