# LangGraph 多节点编排示例（官方教程忠实实现）

LangGraph 官方最经典的 4 个手写多节点编排示例，全部忠实于官方教程原文。
模型使用 DeepSeek（通过 LiteLLM 代理）。

## 环境配置

所有示例共用以下配置（在每个文件顶部修改）:

```python
BASE_URL = "http://localhost:4000/v1"   # LiteLLM 代理地址
MODEL = "ark-deepseek-v4-flash"          # 模型 ID
API_KEY = "sk-fake-key-not-needed"       # 随便填，LiteLLM 未配置 API Key 校验

# 使用 OpenAI 兼容客户端 (ChatOpenAI)
# llm = ChatOpenAI(model=MODEL, base_url=BASE_URL, api_key=API_KEY)
```

## 示例列表

### 01 — Agentic RAG（4 节点 + 条件边 + 循环）⭐ 最经典

**官方教程**: Build a custom RAG agent with LangGraph (`agentic-rag.mdx`)

**文件**: `01_agentic_rag.py`

**图结构**:
```
START → generate_query_or_respond ──条件──→ retrieve → grade_documents ──条件──→ generate_answer → END
                    ↑                                                                   │
                    │                                                             rewrite_question
                    └─────────────────────────────────────────────────────────────────┘
```

**节点**（对应官方教程章节）:
1. `generate_query_or_respond` — 调用 LLM + bind_tools，决定检索或直接回答（§3）
2. `retrieve` — `ToolNode` 调用检索工具（langgraph 预构建节点）
3. `grade_documents` — 评估文档相关性，作为条件边路由函数（§4）
4. `rewrite_question` — 文档不相关时重写问题（§5）
5. `generate_answer` — 基于检索文档生成最终答案（§6）

**核心知识点**: `add_node`、`add_edge`、`add_conditional_edges`、`ToolNode`、循环回流

**运行**:
```bash
python 01_agentic_rag.py
```

---

### 02 — 多源知识库 Router（5 节点 + Map-Reduce 并行）

**官方教程**: Build a multi-source knowledge base with routing (`multi-agent/router-knowledge-base.mdx`)

**文件**: `02_router_knowledge_base.py`

**图结构**:
```
         ┌── github ──┐
START → classify ──┼── notion ──┼→ synthesize → END
                   └──  slack ──┘
```

**节点**（对应官方教程章节）:
1. `classify` — 用 LLM 分类查询，生成各来源的针对性子问题（§4）
2. `github` — GitHub Agent，带 search_code / search_issues / search_prs 工具（§3）
3. `notion` — Notion Agent，带 search_notion / get_page 工具（§3）
4. `slack` — Slack Agent，带 search_slack / get_thread 工具（§3）
5. `synthesize` — 综合所有来源结果生成最终答案（§4）

**核心知识点**: `Send` API 实现并行扇出（Map-Reduce）、`Annotated` + `operator.add` 累加状态、专业化 Agent

**运行**:
```bash
python 02_router_knowledge_base.py
```

---

### 03 — 多 Agent Handoffs（2 节点 + 互相跳转）

**官方教程**: Handoffs → Complete example: Sales and support with handoffs (`multi-agent/handoffs.mdx`)

**文件**: `03_multi_agent_handoffs.py`

**图结构**:
```
START ──条件──→ sales_agent ──┐
               ↕               ├─条件→ END
           support_agent ──────┘
```

**节点**（对应官方教程章节）:
1. `sales_agent` — 销售 Agent，带 `transfer_to_support` handoff 工具（§Multiple agent subgraphs）
2. `support_agent` — 支持 Agent，带 `transfer_to_sales` handoff 工具

**关键机制**:
- Handoff 工具返回 `Command(goto=..., update=..., graph=Command.PARENT)`
- `route_after_agent` 检查最后一条消息是否有 `tool_calls` 来判断是否结束
- `active_agent` 状态字段跟踪当前活跃的 Agent

**核心知识点**: `Command.PARENT` 实现节点跳转、Handoff 模式、`AgentState`、工具驱动的状态转移

**运行**:
```bash
python 03_multi_agent_handoffs.py
```

---

### 04 — 自定义 RAG 工作流（3 节点顺序执行）

**官方教程**: Custom workflows → Example: RAG pipeline (`multi-agent/custom-workflow.mdx`)

**文件**: `04_custom_rag_workflow.py`

**图结构**:
```
START → rewrite → retrieve → agent → END
```

**三种节点类型**（官方教程原文）:
1. **Model node** (Rewrite) — 模型节点: 用 LLM 重写查询（结构化输出）
2. **Deterministic node** (Retrieve) — 确定性节点: 向量检索，无 LLM 调用
3. **Agent node** (Agent) — Agent 节点: 带工具的完整 Agent，自主推理

**核心知识点**: 三种节点类型对比、`create_agent` 集成到 LangGraph 节点

**运行**:
```bash
python 04_custom_rag_workflow.py
```

---

## 核心 API 速查

| API | 作用 |
|---|---|
| `StateGraph(State)` | 创建带状态的图构建器 |
| `.add_node(name, func)` | 添加节点（函数名自动推断，或显式指定） |
| `.add_edge(start, end)` | 添加普通有向边 |
| `.add_conditional_edges(source, path, path_map)` | 添加条件边 |
| `.add_sequence([n1, n2, n3])` | 顺序添加一组节点（简写） |
| `Send(node_name, state_patch)` | 条件边中返回，实现并行扇出 |
| `Command(goto=..., update=..., graph=PARENT)` | 从节点内部控制路由跳转 |
| `ToolNode([tool1, tool2])` | 预构建的工具调用节点 |
| `.compile()` | 编译图，返回 `CompiledGraph` |
| `graph.invoke(initial_state)` | 同步运行图 |
| `graph.stream(initial_state)` | 流式输出每一步 |

## 与官方教程的差异说明

由于本示例使用 `ark-deepseek-v4-flash`（通过 OpenAI 兼容接口访问 LiteLLM 代理），以下地方做了适配：

1. **`with_structured_output`**: DeepSeek 推理模型（thinking mode）不支持 `tool_choice`，因此官方教程中使用结构化输出的地方（grade_documents、classify_query、rewrite_query）改用普通 LLM 调用 + 手动解析。**图结构、节点逻辑、路由方式完全忠实于官方**。

2. **向量检索**: 官方教程用 `OpenAIEmbeddings + InMemoryVectorStore`，这里用简单关键词匹配代替，避免额外依赖 embeddings API。**节点职责和数据流完全一致**。

3. **模型初始化**: 官方用 `init_chat_model("gpt-5.4")`，这里用 `ChatOpenAI(model=..., base_url=...)` 通过 OpenAI 兼容接口访问 LiteLLM 代理。**使用方式完全兼容**。

## 依赖安装

```bash
pip install langgraph langchain langchain_deepseek pydantic
```
