import asyncio
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from typing import TypedDict


class State(TypedDict):
    input: str
    result: str


def ask_node(state):
    answer = interrupt({"type": "ask_user", "question": "你好？"})
    return {"result": answer}


builder = StateGraph(State)
builder.add_node("ask", ask_node)
builder.set_entry_point("ask")
builder.set_finish_point("ask")

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)


async def main():
    config = {"configurable": {"thread_id": "t1"}}

    print("=== FIRST RUN (will hit interrupt) ===")
    async for event in graph.astream_events(
        {"input": "hi", "result": ""}, config=config, version="v2"
    ):
        print(f"  event={event['event']}, name={event.get('name', '')}")

    print("\n=== RESUME RUN ===")
    async for event in graph.astream_events(
        Command(resume="用户回答"), config=config, version="v2"
    ):
        print(f"  event={event['event']}, name={event.get('name', '')}")

    state = await graph.aget_state(config)
    print(f"\nFinal state: {state.values}")


asyncio.run(main())
