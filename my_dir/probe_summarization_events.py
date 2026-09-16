"""Probe: does dispatch_custom_event inside SummarizationMiddleware.before_model
surface as on_custom_event in agent.astream_events(version=v2)?

Also records every on_chat_model_end to see if the summarization LLM call
leaks into the usage stream.
"""

import asyncio

from langchain.agents import create_agent
from langchain_core.callbacks import adispatch_custom_event, dispatch_custom_event
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage

from lc_agent.middlewares.summarization_events import NotifyingSummarizationMiddleware


async def main() -> None:
    main_llm = FakeListChatModel(responses=["main answer"])
    summ_llm = FakeListChatModel(responses=["probe summary text"])
    mw = NotifyingSummarizationMiddleware(
        model=summ_llm,
        trigger=("messages", 3),
        keep=("messages", 1),
    )
    agent = create_agent(model=main_llm, tools=[], middleware=[mw])

    history = [HumanMessage(content=f"history message number {i}") for i in range(6)]

    custom_events: list[tuple[str, dict]] = []
    chat_model_ends: list[str] = []
    summary_end_meta: dict = {}
    async for event in agent.astream_events({"messages": history}, version="v2"):
        kind = event.get("event", "")
        if kind == "on_custom_event":
            custom_events.append((event.get("name", ""), dict(event.get("data", {}) or {})))
        elif kind == "on_chat_model_end":
            output = event.get("data", {}).get("output")
            content = getattr(output, "content", "") if output else ""
            chat_model_ends.append(str(content)[:60])
            if "probe summary" in str(content):
                summary_end_meta = {
                    "metadata": event.get("metadata"),
                    "tags": event.get("tags"),
                    "name": event.get("name"),
                }

    print("=== on_custom_event seen ===")
    for name, data in custom_events:
        print(f"  {name}: {data}")
    print("=== on_chat_model_end outputs ===")
    for c in chat_model_ends:
        print(f"  {c!r}")

    print("=== summary on_chat_model_end meta ===")
    import json as _json
    print(_json.dumps(summary_end_meta, default=str, ensure_ascii=False, indent=2)[:2000])

    names = [n for n, _ in custom_events]
    assert "summarization_start" in names, "summarization_start NOT surfaced!"
    assert "summarization_done" in names, "summarization_done NOT surfaced!"

    # 验证 stream_utils 侧：摘要 LLM 事件被隔离，不进正文；用量记 source="summarize"
    from lc_agent.server import stream_utils as _su

    content_parts: list[str] = []
    tool_calls: list[dict] = []
    usage_rounds: list[dict] = []
    main_tokens: list[str] = []
    async for event in agent.astream_events({"messages": history}, version="v2"):
        kind = event.get("event", "")
        if kind == "on_chat_model_stream":
            for evt_type, evt_data in _su.convert_stream_event(event):
                if evt_type == "token":
                    main_tokens.append(evt_data.get("content", ""))
        _su.accumulate_display_state(event, content_parts, tool_calls, False)
        _su.accumulate_usage(event, usage_rounds, default_model_id="test-model")

    joined = "".join(content_parts)
    assert "probe summary text" not in joined, f"summary leaked into content: {joined!r}"
    assert "main answer" in joined, f"main answer missing: {joined!r}"
    assert "<!--SUMMARIZE:" in joined, f"summary marker missing: {joined!r}"
    summarize_rows = [r for r in usage_rounds if r.get("source") == "summarize"]
    main_rows = [r for r in usage_rounds if r.get("source") != "summarize"]
    assert len(summarize_rows) == 1, f"expected 1 summarize row, got {usage_rounds}"
    assert len(main_rows) >= 1, f"expected main rows, got {usage_rounds}"
    print("PROBE OK: events surface, summary isolated, usage split, marker persisted")


if __name__ == "__main__":
    asyncio.run(main())
