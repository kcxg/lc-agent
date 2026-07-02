"""Realistic test: ToolNode + interrupt tool, then resume."""
import asyncio

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt


@tool
def ask_user(question: str) -> str:
    """Ask user a question and wait for answer."""
    return interrupt({"type": "ask_user", "question": question})


tools = [ask_user]
tool_node = ToolNode(tools)


def call_model(state: MessagesState):
    # Simulate LLM deciding to call ask_user
    from langchain_core.messages import AIMessage
    msg = AIMessage(
        content="",
        tool_calls=[{"name": "ask_user", "args": {"question": "hello?"}, "id": "tc1", "type": "tool_call"}],
    )
    return {"messages": [msg]}


def should_continue(state: MessagesState):
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


builder = StateGraph(MessagesState)
builder.add_node("agent", call_model)
builder.add_node("tools", tool_node)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")
graph = builder.compile(checkpointer=MemorySaver())

INTERESTING = {"on_tool_start", "on_tool_end", "on_chat_model_stream", "on_chat_model_end"}


async def print_events(label, input_val, config):
    async for event in graph.astream_events(input_val, config=config, version="v2"):
        kind = event.get("event", "")
        if kind in INTERESTING:
            name = event.get("name", "")
            extra = ""
            if kind == "on_tool_end":
                out = event.get("data", {}).get("output")
                extra = repr(getattr(out, "content", out))[:80]
            print(f"  [{label}] {kind:25} name={name!r} {extra}")


async def main():
    config = {"configurable": {"thread_id": "t2"}, "recursion_limit": 10}

    print("=== Phase 1 ===")
    await print_events("p1", {"messages": [HumanMessage(content="hi")]}, config)

    print("\n=== Phase 2: resume ===")
    await print_events("p2", Command(resume="my answer"), config)


asyncio.run(main())
