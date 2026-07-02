"""Test what astream_events emits on interrupt resume."""
import asyncio

from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.types import Command, interrupt


@tool
def ask_user(question: str) -> str:
    """Ask user a question."""
    return interrupt({"type": "ask_user", "question": question})


def agent_node(state):
    result = ask_user.invoke({"question": "hello?"})
    return {"answer": result}


builder = StateGraph(dict)
builder.add_node("agent", agent_node)
builder.set_entry_point("agent")
builder.set_finish_point("agent")
graph = builder.compile(checkpointer=MemorySaver())

INTERESTING = {
    "on_tool_start",
    "on_tool_end",
    "on_chat_model_stream",
    "on_chat_model_end",
    "on_chain_end",
}


async def collect_events(label, input_val, config):
    events = []
    async for event in graph.astream_events(input_val, config=config, version="v2"):
        kind = event.get("event", "")
        if kind in INTERESTING:
            name = event.get("name", "")
            run_id = str(event.get("run_id", ""))[:8]
            extra = ""
            if kind == "on_tool_end":
                extra = repr(event.get("data", {}).get("output"))[:120]
            elif kind == "on_chain_end" and name == "LangGraph":
                extra = repr(event.get("data", {}).get("output"))[:120]
            print(f"  [{label}] {kind:25} name={name!r:20} run_id={run_id}... {extra}")
        events.append(event)
    return events


async def main():
    config = {"configurable": {"thread_id": "t1"}, "recursion_limit": 10}

    print("=== Phase 1: initial run until interrupt ===")
    e1 = await collect_events("phase1", {"input": "hi"}, config)
    print(f"Phase1 unique events: {sorted(set(e.get('event') for e in e1))}")

    state = await graph.aget_state(config)
    print(f"State next: {state.next}, tasks: {len(state.tasks or [])}")

    print()
    print("=== Phase 2: resume with user answer ===")
    e2 = await collect_events("phase2", Command(resume="user answer"), config)
    print(f"Phase2 unique events: {sorted(set(e.get('event') for e in e2))}")

    tool_starts = [e for e in e2 if e.get("event") == "on_tool_start"]
    tool_ends = [e for e in e2 if e.get("event") == "on_tool_end"]
    print(f"Phase2 on_tool_start count: {len(tool_starts)}")
    print(f"Phase2 on_tool_end count: {len(tool_ends)}")


asyncio.run(main())
