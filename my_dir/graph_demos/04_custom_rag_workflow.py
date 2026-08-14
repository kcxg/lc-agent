"""
自定义 RAG 工作流 — LangGraph 官方教程忠实实现

官方教程: Custom workflows → Example: RAG pipeline
文档来源: langchain_ai_codes_and_docs → multi-agent/custom-workflow.mdx

图结构:
    START → rewrite → retrieve → agent → END

展示三种不同类型的节点（官方教程原文）:
  1. Model node (Rewrite)     — 模型节点: 用 LLM 结构化输出重写查询
  2. Deterministic node (Retrieve) — 确定性节点: 向量检索，无 LLM
  3. Agent node (Agent)       — Agent 节点: 带工具的 agent 进行推理并生成答案

运行: python 04_custom_rag_workflow.py
"""

from typing import TypedDict

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

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

# ───────────────────────── 状态定义（官方教程原文） ─────────────────────────
#
# class State(TypedDict):
#     question: str
#     rewritten_query: str
#     documents: list[str]
#     answer: str


class State(TypedDict):
    question: str
    rewritten_query: str
    documents: list[str]
    answer: str


# ───────────────────────── 知识库 & 检索（官方教程用 InMemoryVectorStore） ─────────────────────────
# 官方教程用 OpenAIEmbeddings + InMemoryVectorStore 做真正的向量检索。
# 这里用简单关键词匹配代替，保持检索逻辑一致，避免依赖 embeddings API。

WNBA_KNOWLEDGE = [
    # Rosters
    "New York Liberty 2024 roster: Breanna Stewart, Sabrina Ionescu, Jonquel Jones, Courtney Vandersloot.",
    "Las Vegas Aces 2024 roster: A'ja Wilson, Kelsey Plum, Jackie Young, Chelsea Gray.",
    "Indiana Fever 2024 roster: Caitlin Clark, Aliyah Boston, Kelsey Mitchell, NaLyssa Smith.",
    # Game results
    "2024 WNBA Finals: New York Liberty defeated Minnesota Lynx 3-2 to win the championship.",
    "June 15, 2024: Indiana Fever 85, Chicago Sky 79. Caitlin Clark had 23 points and 8 assists.",
    "August 20, 2024: Las Vegas Aces 92, Phoenix Mercury 84. A'ja Wilson scored 35 points.",
    # Player stats
    "A'ja Wilson 2024 season stats: 26.9 PPG, 11.9 RPG, 2.6 BPG. Won MVP award.",
    "Caitlin Clark 2024 rookie stats: 19.2 PPG, 8.4 APG, 5.7 RPG. Won Rookie of the Year.",
    "Breanna Stewart 2024 stats: 20.4 PPG, 8.5 RPG, 3.5 APG.",
]


def simple_retrieve(query: str, top_k: int = 5) -> list[str]:
    """简单关键词检索（模拟 InMemoryVectorStore 的相似度检索）。"""
    query_words = set(query.lower().split())
    scored = []
    for doc in WNBA_KNOWLEDGE:
        doc_words = set(doc.lower().split())
        score = len(query_words & doc_words)
        scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in scored[:top_k] if score > 0]


# ───────────────────────── 工具 & Agent（官方教程原文） ─────────────────────────
#
# @tool
# def get_latest_news(query: str) -> str:
#     """Get the latest WNBA news and updates."""
#     return "Latest: The WNBA announced expanded playoff format for 2025..."
#
# agent = create_agent(model="openai:gpt-5.4", tools=[get_latest_news])


@tool
def get_latest_news(query: str) -> str:
    """Get the latest WNBA news and updates."""
    # Your news API here
    return "Latest: The WNBA announced expanded playoff format for 2025..."


agent = create_agent(
    model=model,
    tools=[get_latest_news],
)


# ───────────────────────── 节点 1: Model node — Rewrite（官方教程原文） ─────────────────────────
#
# class RewrittenQuery(BaseModel):
#     query: str
#
# def rewrite_query(state: State) -> dict:
#     """Rewrite the user query for better retrieval."""
#     system_prompt = """Rewrite this query to retrieve relevant WNBA information.
#     The knowledge base contains: team rosters, game results with scores, and player statistics (PPG, RPG, APG).
#     Focus on specific player names, team names, or stat categories mentioned."""
#     response = model.with_structured_output(RewrittenQuery).invoke([
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": state["question"]}
#     ])
#     return {"rewritten_query": response.query}
#
# 注: 官方教程用 with_structured_output，但 DeepSeek 推理模型不支持 tool_choice。
# 这里用普通 LLM 调用 + 手动提取关键词代替，保持"模型节点"的语义一致。

import re


def rewrite_query(state: State) -> dict:
    """Rewrite the user query for better retrieval.

    这是一个「模型节点」——调用 LLM 提取检索关键词。
    官方教程用 with_structured_output(RewrittenQuery) 做结构化输出。
    """
    system_prompt = (
        "Rewrite this query to retrieve relevant WNBA information.\n"
        "The knowledge base contains: team rosters, game results with scores, "
        "and player statistics (PPG, RPG, APG).\n"
        "Focus on specific player names, team names, or stat categories mentioned.\n"
        "Respond with ONLY the rewritten query keywords in English, nothing else."
    )
    response = model.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state["question"]},
    ])
    # 提取英文关键词
    words = re.findall(r"[a-zA-Z'\-]+", response.content)
    rewritten = " ".join(words[:8]) if words else state["question"]
    print(f"[重写查询] {state['question']}  →  {rewritten}")
    return {"rewritten_query": rewritten}


# ───────────────────────── 节点 2: Deterministic node — Retrieve（官方教程原文） ─────────────────────────
#
# def retrieve(state: State) -> dict:
#     """Retrieve documents based on the rewritten query."""
#     docs = retriever.invoke(state["rewritten_query"])
#     return {"documents": [doc.page_content for doc in docs]}


def retrieve(state: State) -> dict:
    """Retrieve documents based on the rewritten query.

    这是一个「确定性节点」——纯检索逻辑，不调用 LLM。
    """
    docs = simple_retrieve(state["rewritten_query"], top_k=5)
    print(f"[检索] 找到 {len(docs)} 条相关文档")
    for i, doc in enumerate(docs):
        print(f"  {i + 1}. {doc[:60]}...")
    return {"documents": docs}


# ───────────────────────── 节点 3: Agent node — Agent（官方教程原文） ─────────────────────────
#
# def call_agent(state: State) -> dict:
#     """Generate answer using retrieved context."""
#     context = "\n\n".join(state["documents"])
#     prompt = f"Context:\n{context}\n\nQuestion: {state['question']}"
#     response = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
#     return {"answer": response["messages"][-1].content_blocks}
#
# 注: 官方教程用 content_blocks，这里用 content 代替（不同消息格式版本差异）。


def call_agent(state: State) -> dict:
    """Generate answer using retrieved context.

    这是一个「Agent 节点」——内部是一个带工具的完整 Agent，可以自主决定是否调用工具。
    """
    print("[Agent] 正在生成答案...")
    if state["documents"]:
        context = "\n\n".join(state["documents"])
        prompt = f"Context:\n{context}\n\nQuestion: {state['question']}"
    else:
        prompt = f"Question: {state['question']}\n\nNo documents found. Answer from your knowledge, or use the news tool."

    response = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    return {"answer": response["messages"][-1].content}


# ───────────────────────── 构建图（官方教程原文） ─────────────────────────
#
# workflow = (
#     StateGraph(State)
#     .add_node("rewrite", rewrite_query)
#     .add_node("retrieve", retrieve)
#     .add_node("agent", call_agent)
#     .add_edge(START, "rewrite")
#     .add_edge("rewrite", "retrieve")
#     .add_edge("retrieve", "agent")
#     .add_edge("agent", END)
#     .compile()
# )

workflow = (
    StateGraph(State)
    .add_node("rewrite", rewrite_query)   # 节点1: 模型节点
    .add_node("retrieve", retrieve)       # 节点2: 确定性节点
    .add_node("agent", call_agent)        # 节点3: Agent 节点
    .add_edge(START, "rewrite")
    .add_edge("rewrite", "retrieve")
    .add_edge("retrieve", "agent")
    .add_edge("agent", END)
    .compile()
)


# ───────────────────────── 运行演示 ─────────────────────────

def run_demo(question: str):
    print("=" * 60)
    print(f"用户问题: {question}")
    print("=" * 60)
    print()

    result = workflow.invoke({"question": question})

    print()
    print("=" * 60)
    print("最终答案:")
    print("=" * 60)
    print(result["answer"])
    print()


if __name__ == "__main__":
    # 示例 1: 关于比赛结果的问题
    run_demo("Who won the 2024 WNBA Championship?")

    # 示例 2: 关于球员数据的问题
    # run_demo("What are A'ja Wilson's 2024 season stats?")

    # 示例 3: 关于新秀的问题
    # run_demo("Tell me about Caitlin Clark's rookie season stats")
