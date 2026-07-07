from lc_agent.server.stream_utils import (
    convert_stream_event,
    _get_checkpoint_ns,
    _extract_subagent_tool_call_id,
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


def test_subagent_token():
    event = {
        "event": "on_chat_model_stream",
        "metadata": {"langgraph_checkpoint_ns": "tools:abc123"},
        "data": {"chunk": _make_chunk("sub hi")},
    }
    results = convert_stream_event(event)
    assert results == [("subagent_token", {"tool_call_id": "abc123", "content": "sub hi"})]


def test_subagent_start_emitted_for_subagent_tools():
    event = {
        "event": "on_tool_start",
        "name": "research_expert",
        "run_id": "run123",
        "metadata": {},
        "data": {"input": {"query": "quantum"}},
    }
    results = convert_stream_event(event, subagent_tool_names={"research_expert"})
    types = [r[0] for r in results]
    assert "subagent_start" in types
    assert "tool_call" in types
    tc = next(r[1] for r in results if r[0] == "tool_call")
    assert tc["is_subagent"] is True


def test_subagent_done_instead_of_tool_result():
    event = {
        "event": "on_tool_end",
        "name": "research_expert",
        "run_id": "run123",
        "metadata": {},
        "data": {"output": "research result"},
    }
    results = convert_stream_event(event, subagent_tool_names={"research_expert"})
    assert results[0][0] == "subagent_done"
    assert "tool_result" not in [r[0] for r in results]


def test_extract_subagent_tool_call_id():
    assert _extract_subagent_tool_call_id("tools:abc123") == "abc123"
    assert _extract_subagent_tool_call_id("tools:abc123|model:def") == "abc123"
    assert _extract_subagent_tool_call_id("") is None
