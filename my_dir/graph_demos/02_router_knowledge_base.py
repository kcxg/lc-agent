"""
多源知识库 Router — LangGraph 官方教程忠实实现

官方教程: Build a multi-source knowledge base with routing
文档来源: langchain_ai_codes_and_docs → multi-agent/router-knowledge-base.mdx

图结构 (Map-Reduce 扇出扇入):
         ┌── github ──┐
START → classify ──┼── notion ──┼→ synthesize → END
                   └──  slack ──┘

节点:
  1. classify   — 分类查询，确定需要查询哪些数据源 + 生成针对性子问题
  2. github     — GitHub Agent（搜索代码、Issue、PR）
  3. notion     — Notion Agent（搜索内部文档和 Wiki）
  4. slack      — Slack Agent（搜索消息和讨论）
  5. synthesize — 综合所有来源的结果生成最终答案

使用 Send API 实现并行执行（Map-Reduce 模式）。

运行: python 02_router_knowledge_base.py
"""

from typing import Annotated, Literal, TypedDict

import operator
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

# ───────────────────────── 配置 ─────────────────────────
BASE_URL = "http://localhost:4000/v1"
MODEL = "ark-deepseek-v4-flash"
API_KEY = "sk-fake-key-not-needed"

model = ChatOpenAI(
    model=MODEL,
    base_url=BASE_URL,
    api_key=API_KEY,
    temperature=0,
)

router_llm = ChatOpenAI(
    model=MODEL,
    base_url=BASE_URL,
    api_key=API_KEY,
    temperature=0,
)

# ───────────────────────── 1. 状态定义（官方教程原文） ─────────────────────────
#
# class AgentInput(TypedDict):
#     query: str
#
# class AgentOutput(TypedDict):
#     source: str
#     result: str
#
# class Classification(TypedDict):
#     source: Literal["github", "notion", "slack"]
#     query: str
#
# class RouterState(TypedDict):
#     query: str
#     classifications: list[Classification]
#     results: Annotated[list[AgentOutput], operator.add]
#     final_answer: str


class AgentInput(TypedDict):
    """Simple input state for each subagent."""
    query: str


class AgentOutput(TypedDict):
    """Output from each subagent."""
    source: str
    result: str


class Classification(TypedDict):
    """A single routing decision: which agent to call with what query."""
    source: Literal["github", "notion", "slack"]
    query: str


class RouterState(TypedDict):
    query: str
    classifications: list[Classification]
    results: Annotated[list[AgentOutput], operator.add]  # Reducer collects parallel results
    final_answer: str


# ───────────────────────── 2. 各垂直领域工具（官方教程原文） ─────────────────────────
# 官方教程定义了 7 个工具，分布在 3 个垂直领域：
#   GitHub: search_code, search_issues, search_prs
#   Notion: search_notion, get_page
#   Slack:  search_slack, get_thread


@tool
def search_code(query: str, repo: str = "main") -> str:
    """Search code in GitHub repositories."""
    return f"Found code matching '{query}' in {repo}: authentication middleware in src/auth.py"


@tool
def search_issues(query: str) -> str:
    """Search GitHub issues and pull requests."""
    return f"Found 3 issues matching '{query}': #142 (API auth docs), #89 (OAuth flow), #203 (token refresh)"


@tool
def search_prs(query: str) -> str:
    """Search pull requests for implementation details."""
    return f"PR #156 added JWT authentication, PR #178 updated OAuth scopes"


@tool
def search_notion(query: str) -> str:
    """Search Notion workspace for documentation."""
    return f"Found documentation: 'API Authentication Guide' - covers OAuth2 flow, API keys, and JWT tokens"


@tool
def get_page(page_id: str) -> str:
    """Get a specific Notion page by ID."""
    return f"Page content: Step-by-step authentication setup instructions"


@tool
def search_slack(query: str) -> str:
    """Search Slack messages and threads."""
    return f"Found discussion in #engineering: 'Use Bearer tokens for API auth, see docs for refresh flow'"


@tool
def get_thread(thread_id: str) -> str:
    """Get a specific Slack thread."""
    return f"Thread discusses best practices for API key rotation"


# ───────────────────────── 3. 专业化 Agent（官方教程原文） ─────────────────────────
#
# github_agent = create_agent(model, tools=[search_code, search_issues, search_prs], system_prompt=...)
# notion_agent = create_agent(model, tools=[search_notion, get_page], system_prompt=...)
# slack_agent  = create_agent(model, tools=[search_slack, get_thread], system_prompt=...)

github_agent = create_agent(
    model,
    tools=[search_code, search_issues, search_prs],
    system_prompt=(
        "You are a GitHub expert. Answer questions about code, "
        "API references, and implementation details by searching "
        "repositories, issues, and pull requests."
    ),
)

notion_agent = create_agent(
    model,
    tools=[search_notion, get_page],
    system_prompt=(
        "You are a Notion expert. Answer questions about internal "
        "processes, policies, and team documentation by searching "
        "the organization's Notion workspace."
    ),
)

slack_agent = create_agent(
    model,
    tools=[search_slack, get_thread],
    system_prompt=(
        "You are a Slack expert. Answer questions by searching "
        "relevant threads and discussions where team members have "
        "shared knowledge and solutions."
    ),
)


# ───────────────────────── 4. Router 工作流节点（官方教程原文） ─────────────────────────


def classify_query(state: RouterState) -> dict:
    """Classify query and determine which agents to invoke.

    官方教程用 with_structured_output(ClassificationResult) 做结构化输出。
    由于 DeepSeek 推理模型不支持 tool_choice，这里用普通 LLM 调用 + 手动解析代替，
    保持分类逻辑一致。
    """
    system_prompt = """Analyze this query and determine which knowledge bases to consult.
For each relevant source, generate a targeted sub-question optimized for that source.

Available sources:
- github: Code, API references, implementation details, issues, pull requests
- notion: Internal documentation, processes, policies, team wikis
- slack: Team discussions, informal knowledge sharing, recent conversations

Return ONLY the relevant sources, one per line, in this format:
source: sub-question

For example, for "How do I authenticate API requests?":
github: What authentication code exists? Search for auth middleware, JWT handling
notion: What authentication documentation exists? Look for API auth guides

Do NOT include sources that are not relevant. Respond with only the classifications, nothing else."""

    response = router_llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state["query"]},
    ])

    # 手动解析输出
    classifications: list[Classification] = []
    for line in response.content.strip().split("\n"):
        line = line.strip()
        if ":" in line:
            source, query = line.split(":", 1)
            source = source.strip().lower()
            query = query.strip()
            if source in ("github", "notion", "slack"):
                classifications.append({"source": source, "query": query})  # type: ignore

    if not classifications:
        # 兜底：三个都查
        classifications = [
            {"source": "github", "query": state["query"]},
            {"source": "notion", "query": state["query"]},
            {"source": "slack", "query": state["query"]},
        ]

    print(f"[分类] 将查询以下来源:")
    for c in classifications:
        print(f"  - {c['source']}: {c['query']}")

    return {"classifications": classifications}


def route_to_agents(state: RouterState) -> list[Send]:
    """Fan out to agents based on classifications.

    官方教程原文:
    return [Send(c["source"], {"query": c["query"]}) for c in state["classifications"]]
    """
    return [
        Send(c["source"], {"query": c["query"]})
        for c in state["classifications"]
    ]


def query_github(state: AgentInput) -> dict:
    """Query the GitHub agent.

    官方教程原文:
    result = github_agent.invoke({"messages": [{"role": "user", "content": state["query"]}]})
    return {"results": [{"source": "github", "result": result["messages"][-1].content}]}
    """
    print("[GitHub Agent] 查询中...")
    result = github_agent.invoke({
        "messages": [{"role": "user", "content": state["query"]}]
    })
    return {"results": [{"source": "github", "result": result["messages"][-1].content}]}


def query_notion(state: AgentInput) -> dict:
    """Query the Notion agent."""
    print("[Notion Agent] 查询中...")
    result = notion_agent.invoke({
        "messages": [{"role": "user", "content": state["query"]}]
    })
    return {"results": [{"source": "notion", "result": result["messages"][-1].content}]}


def query_slack(state: AgentInput) -> dict:
    """Query the Slack agent."""
    print("[Slack Agent] 查询中...")
    result = slack_agent.invoke({
        "messages": [{"role": "user", "content": state["query"]}]
    })
    return {"results": [{"source": "slack", "result": result["messages"][-1].content}]}


def synthesize_results(state: RouterState) -> dict:
    """Combine results from all agents into a coherent answer.

    官方教程原文:
    synthesis_response = router_llm.invoke([
        {"role": "system", "content": f"Synthesize these search results..."},
        {"role": "user", "content": "\n\n".join(formatted)}
    ])
    return {"final_answer": synthesis_response.content}
    """
    if not state["results"]:
        return {"final_answer": "No results found from any knowledge source."}

    formatted = [
        f"**From {r['source'].title()}:**\n{r['result']}"
        for r in state["results"]
    ]

    synthesis_response = router_llm.invoke([
        {
            "role": "system",
            "content": f"""Synthesize these search results to answer the original question: "{state['query']}"

- Combine information from multiple sources without redundancy
- Highlight the most relevant and actionable information
- Note any discrepancies between sources
- Keep the response concise and well-organized""",
        },
        {"role": "user", "content": "\n\n".join(formatted)},
    ])

    return {"final_answer": synthesis_response.content}


# ───────────────────────── 5. 编译工作流（官方教程原文） ─────────────────────────
#
# workflow = (
#     StateGraph(RouterState)
#     .add_node("classify", classify_query)
#     .add_node("github", query_github)
#     .add_node("notion", query_notion)
#     .add_node("slack", query_slack)
#     .add_node("synthesize", synthesize_results)
#     .add_edge(START, "classify")
#     .add_conditional_edges("classify", route_to_agents, ["github", "notion", "slack"])
#     .add_edge("github", "synthesize")
#     .add_edge("notion", "synthesize")
#     .add_edge("slack", "synthesize")
#     .add_edge("synthesize", END)
#     .compile()
# )

workflow = (
    StateGraph(RouterState)
    .add_node("classify", classify_query)
    .add_node("github", query_github)
    .add_node("notion", query_notion)
    .add_node("slack", query_slack)
    .add_node("synthesize", synthesize_results)
    .add_edge(START, "classify")
    .add_conditional_edges("classify", route_to_agents, ["github", "notion", "slack"])
    .add_edge("github", "synthesize")
    .add_edge("notion", "synthesize")
    .add_edge("slack", "synthesize")
    .add_edge("synthesize", END)
    .compile()
)


# ───────────────────────── 运行演示 ─────────────────────────

def run_demo(question: str):
    print("=" * 60)
    print(f"用户问题: {question}")
    print("=" * 60)
    print()

    result = workflow.invoke({"query": question})

    print()
    print("=" * 60)
    print("分类结果:")
    print("=" * 60)
    for c in result["classifications"]:
        print(f"  {c['source']}: {c['query']}")

    print()
    print("=" * 60)
    print("最终答案:")
    print("=" * 60)
    print(result["final_answer"])
    print()


if __name__ == "__main__":
    # 示例 1: 涉及多个来源的技术问题
    run_demo("How do I authenticate API requests?")

    # 示例 2: 只涉及单个来源
    # run_demo("How do I search GitHub issues?")

    # 示例 3: 涉及 Slack 的讨论类问题
    # run_demo("What does the team think about API key rotation?")
