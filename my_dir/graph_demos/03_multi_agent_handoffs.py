"""
多 Agent Handoffs — LangGraph 官方教程忠实实现

官方教程: Handoffs (Complete example: Sales and support with handoffs)
文档来源: langchain_ai_codes_and_docs → multi-agent/handoffs.mdx

图结构:
    START ──条件──→ sales_agent ──┐
                   ↕               ├─条件→ END
               support_agent ──────┘

节点:
  1. sales_agent   — 销售 Agent，处理价格、购买、套餐等问题
  2. support_agent — 支持 Agent，处理技术问题、故障排查等

两个 Agent 通过 handoff 工具互相跳转。
使用 Command.PARENT 在父图层级切换节点。

关键机制:
- Handoff 工具返回 Command(goto=..., update=..., graph=Command.PARENT)
- 路由函数 route_after_agent 检查最后一条消息是否有 tool_calls 来判断是否结束
- active_agent 状态字段跟踪当前活跃的 Agent

运行: python 03_multi_agent_handoffs.py
"""

from typing import Literal

from langchain.agents import AgentState, create_agent
from langchain.messages import AIMessage, ToolMessage
from langchain.tools import tool, ToolRuntime
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from typing_extensions import NotRequired

# ───────────────────────── 配置 ─────────────────────────
BASE_URL = "http://localhost:4000/v1"
MODEL = "ark-deepseek-v4-flash"
API_KEY = "sk-fake-key-not-needed"

llm = ChatOpenAI(
    model=MODEL,
    base_url=BASE_URL,
    api_key=API_KEY,
    temperature=0.5,
)

# ───────────────────────── 1. 状态定义（官方教程原文） ─────────────────────────
#
# class MultiAgentState(AgentState):
#     active_agent: NotRequired[str]


class MultiAgentState(AgentState):
    active_agent: NotRequired[str]


# ───────────────────────── 2. Handoff 工具（官方教程原文） ─────────────────────────
#
# @tool
# def transfer_to_sales(runtime: ToolRuntime) -> Command:
#     last_ai_message = next(
#         msg for msg in reversed(runtime.state["messages"]) if isinstance(msg, AIMessage)
#     )
#     transfer_message = ToolMessage(
#         content="Transferred to sales agent from support agent",
#         tool_call_id=runtime.tool_call_id,
#     )
#     return Command(
#         goto="sales_agent",
#         update={
#             "active_agent": "sales_agent",
#             "messages": [last_ai_message, transfer_message],
#         },
#         graph=Command.PARENT,
#     )


@tool
def transfer_to_sales(
    runtime: ToolRuntime,
) -> Command:
    """Transfer to the sales agent."""
    last_ai_message = next(  # [!code highlight]
        msg for msg in reversed(runtime.state["messages"]) if isinstance(msg, AIMessage)  # [!code highlight]
    )  # [!code highlight]
    transfer_message = ToolMessage(  # [!code highlight]
        content="Transferred to sales agent from support agent",  # [!code highlight]
        tool_call_id=runtime.tool_call_id,  # [!code highlight]
    )  # [!code highlight]
    return Command(
        goto="sales_agent",
        update={
            "active_agent": "sales_agent",
            "messages": [last_ai_message, transfer_message],  # [!code highlight]
        },
        graph=Command.PARENT,
    )


@tool
def transfer_to_support(
    runtime: ToolRuntime,
) -> Command:
    """Transfer to the support agent."""
    last_ai_message = next(  # [!code highlight]
        msg for msg in reversed(runtime.state["messages"]) if isinstance(msg, AIMessage)  # [!code highlight]
    )  # [!code highlight]
    transfer_message = ToolMessage(  # [!code highlight]
        content="Transferred to support agent from sales agent",  # [!code highlight]
        tool_call_id=runtime.tool_call_id,  # [!code highlight]
    )  # [!code highlight]
    return Command(
        goto="support_agent",
        update={
            "active_agent": "support_agent",
            "messages": [last_ai_message, transfer_message],  # [!code highlight]
        },
        graph=Command.PARENT,
    )


# ───────────────────────── 3. 创建 Agent（官方教程原文） ─────────────────────────
#
# sales_agent = create_agent(
#     model="google_genai:gemini-3.5-flash",
#     tools=[transfer_to_support],
#     system_prompt="You are a sales agent...",
# )
#
# support_agent = create_agent(
#     model="google_genai:gemini-3.5-flash",
#     tools=[transfer_to_sales],
#     system_prompt="You are a support agent...",
# )

sales_agent = create_agent(
    model=llm,
    tools=[transfer_to_support],
    system_prompt=(
        "You are a sales agent. Help with sales inquiries. "
        "If asked about technical issues or support, transfer to the support agent."
    ),
)

support_agent = create_agent(
    model=llm,
    tools=[transfer_to_sales],
    system_prompt=(
        "You are a support agent. Help with technical issues. "
        "If asked about pricing or purchasing, transfer to the sales agent."
    ),
)


# ───────────────────────── 4. Agent 节点（官方教程原文） ─────────────────────────
#
# def call_sales_agent(state: MultiAgentState) -> Command:
#     response = sales_agent.invoke(state)
#     return response
#
# def call_support_agent(state: MultiAgentState) -> Command:
#     response = support_agent.invoke(state)
#     return response


def call_sales_agent(state: MultiAgentState) -> Command:
    """Node that calls the sales agent."""
    print("[销售 Agent] 正在处理...")
    response = sales_agent.invoke(state)
    return response


def call_support_agent(state: MultiAgentState) -> Command:
    """Node that calls the support agent."""
    print("[技术支持 Agent] 正在处理...")
    response = support_agent.invoke(state)
    return response


# ───────────────────────── 5. 路由函数（官方教程原文） ─────────────────────────
#
# def route_after_agent(state) -> Literal["sales_agent", "support_agent", "__end__"]:
#     messages = state.get("messages", [])
#     if messages:
#         last_msg = messages[-1]
#         if isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
#             return "__end__"
#     active = state.get("active_agent", "sales_agent")
#     return active if active else "sales_agent"
#
# def route_initial(state) -> Literal["sales_agent", "support_agent"]:
#     return state.get("active_agent") or "sales_agent"


def route_initial(
    state: MultiAgentState,
) -> Literal["sales_agent", "support_agent"]:
    """Route to the active agent based on state, default to sales agent."""
    return state.get("active_agent") or "sales_agent"


def route_after_agent(
    state: MultiAgentState,
) -> Literal["sales_agent", "support_agent", "__end__"]:
    """Route based on active_agent, or END if the agent finished without handoff.

    官方教程的核心逻辑：
    - 如果最后一条消息是 AIMessage 且没有 tool_calls，说明 Agent 已给出最终回答，结束
    - 否则根据 active_agent 跳转到对应的 Agent（可能发生了 handoff）
    """
    messages = state.get("messages", [])

    # Check the last message - if it's an AIMessage without tool calls, we're done
    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, AIMessage) and not last_msg.tool_calls:  # [!code highlight]
            return "__end__"  # [!code highlight]

    # Otherwise route to the active agent
    active = state.get("active_agent", "sales_agent")
    return active if active else "sales_agent"


# ───────────────────────── 6. 构建图（官方教程原文） ─────────────────────────
#
# builder = StateGraph(MultiAgentState)
# builder.add_node("sales_agent", call_sales_agent)
# builder.add_node("support_agent", call_support_agent)
# builder.add_conditional_edges(START, route_initial, ["sales_agent", "support_agent"])
# builder.add_conditional_edges(
#     "sales_agent", route_after_agent, ["sales_agent", "support_agent", END]
# )
# builder.add_conditional_edges(
#     "support_agent", route_after_agent, ["sales_agent", "support_agent", END]
# )
# graph = builder.compile()

builder = StateGraph(MultiAgentState)
builder.add_node("sales_agent", call_sales_agent)
builder.add_node("support_agent", call_support_agent)

# Start with conditional routing based on initial active_agent
builder.add_conditional_edges(START, route_initial, ["sales_agent", "support_agent"])

# After each agent, check if we should end or route to another agent
builder.add_conditional_edges(
    "sales_agent", route_after_agent, ["sales_agent", "support_agent", END]
)
builder.add_conditional_edges(
    "support_agent", route_after_agent, ["sales_agent", "support_agent", END]
)

graph = builder.compile()


# ───────────────────────── 运行演示 ─────────────────────────

def run_demo(question: str, start_agent: str = "sales_agent"):
    print("=" * 60)
    print(f"用户问题: {question}")
    print(f"起始 Agent: {start_agent}")
    print("=" * 60)
    print()

    result = graph.invoke(
        {
            "messages": [{"role": "user", "content": question}],
            "active_agent": start_agent,
        },
        config={"recursion_limit": 10},
    )

    print()
    print("=" * 60)
    print("最终回答:")
    print("=" * 60)
    # 打印最后一条 AI 消息
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            print(msg.content)
            break
    print()


if __name__ == "__main__":
    # 示例 1: 销售问题（从销售 Agent 开始，直接回答）
    run_demo("How much does your professional plan cost?", start_agent="sales_agent")

    # 示例 2: 技术问题（从销售开始，会自动转移到支持）
    # run_demo("I can't log in to my account, can you help?", start_agent="sales_agent")

    # 示例 3: 从技术支持开始，遇到销售问题转移
    # run_demo("What are the pricing tiers for enterprise?", start_agent="support_agent")
