
# 🤖 AI 上下文阅读协议 (由 nb_ai_context 生成)

> **此文档生成时间**：2026-07-16 15:32:40
> **系统指令**：你正在解析一份由工具 **`nb_ai_context`** 自动生成的**结构化项目快照**。
> **文档性质**：这**不是**一份普通的面向人类的文档，而是专为 AI 大模型（LLM）设计的上下文数据流。它将项目文档、源代码和 AST 架构元数据进行了特殊的结构化合并，请开启"代码解析器"的心智模式。


## 🧠 AI 认知与解析准则

这份由 `nb_ai_context` 生成的文档是你的核心知识库。其中的内容是动态的——它可能包含完整的底层源码，也可能仅包含使用教程，或者是两者的混合。请严格遵循以下自适应阅读策略：

### 1. 信息的层级与冲突处理
*   **文档即意图**：将 `README`、教程文档和 Docstrings 视为项目设计的**最高意图**。如果生成器省略了对应源码，请完全信任文档逻辑，以此为基础推理。
*   **源码即事实**：遇到 `.py` 源码或 AST 元数据（类/函数签名）时，以此作为实现细节、类型约束和语法准确性的**最终事实标准**。
*   **冲突处理**：若文档与源码/AST 存在矛盾，请以源码为准，并在回答中向用户简要指出该差异。
*   **测试代码的忽略**：为优化 Token 长度，集成/单元测试及非核心 API 源码通常被隐藏。**绝对不要**因此推断或提醒用户“项目缺乏测试”或“代码未实现”。

### 2. 文件边界与架构感知
*   **上下文定界**：工具使用 `--- **start of file: <路径>** ---` 等标记严格界定文件。**在你的回复中，请使用标准 Markdown 代码块，切勿模仿使用此类系统定界符。**
*   **结构可视化**：利用“文件树 (File Tree)”章节建立项目的宏观架构认知。
*   **依赖关系**：利用“文件依赖分析”章节理清模块间的 import 数据流向。

### 3. 严格的代码生成与交互边界
*   **事实锚定 (Fact Anchoring)**：你生成的代码必须严格锚定在本文档范围内！API 调用必须基于**源码中的 AST 签名**或**文档中的演示示例**。
*   **严禁臆造 (Zero Fabrication)**：绝对禁止编造文档中未定义或未提及的类名、方法名或参数。
*   **越界拒绝**：如果用户询问的功能在当前提供的上下文中完全不存在，请明确告知“当前上下文中未包含该信息”，而不是试图凭空生成。

---
# markdown content namespace: lc_agent project summary 



- `lc-agent` 是基于 LangChain / LangGraph 的 AI Agent Web 应用框架。
- 提供 WebSocket 流式对话、工具调用、MCP 集成、Skill 系统、多 Agent Preset 管理等能力。
- 前端使用 Vue 3 + Element Plus + Vite，后端使用 FastAPI + LangGraph。
- 核心模块：
  - `lc_agent/app.py`: LcAgentApp — 应用编排入口，创建引擎、注册路由、启动服务
  - `lc_agent/core/engine.py`: AgentEngine — 核心引擎，管理 Agent 实例、Preset、工具组
  - `lc_agent/server/websocket.py`: ChatWebSocketHandler — WebSocket 流式事件转发
  - `lc_agent/mcp/manager.py`: McpManager — MCP 服务连接管理
  - `lc_agent/tools/registry.py`: ToolRegistry — 工具注册表
  - `lc_agent/skills/scanner.py`: SkillScanner — Skill 扫描与匹配
  - `lc_agent/db/`: SQLAlchemy 异步数据持久化
  - `frontend/src/`: Vue 3 前端界面
- 用户用法：`from lc_agent import LcAgentApp, load_config`


## 📋 lc_agent most core source files metadata (Entry Points)


以下是项目 lc_agent 最核心的入口文件的结构化元数据，帮助快速理解项目架构：



### the project lc_agent most core source code files as follows: 
- `lc_agent/__init__.py`
- `lc_agent/app.py`
- `lc_agent/core/engine.py`


### 📄 Python File Metadata: `lc_agent/__init__.py`

#### 📝 Module Docstring

`````
lc_agent — LangChain Agent framework with built-in Web UI.
`````

#### 📦 Imports

- `from importlib.metadata import version`
- `from importlib.metadata import PackageNotFoundError`
- `from lc_agent.app import LcAgentApp`
- `from lc_agent.config.loader import load_config`
- `from lc_agent.core.traced_llm import create_traced_chat_openai`
- `from lc_agent.core.traced_llm import create_traced_openai_http_client`
- `from lc_agent.tools.registry import ToolRegistry`
- `from lc_agent.tools.registry import tool`


---




### 📄 Python File Metadata: `lc_agent/app.py`

#### 📦 Imports

- `from contextlib import asynccontextmanager`
- `from pathlib import Path`
- `import uvicorn`
- `from fastapi import FastAPI`
- `from langchain_agentskills import SkillsToolkit`
- `from langchain_agentskills.loaders import CompositeSkillLoader`
- `from langchain_agentskills.loaders import DirectorySkillLoader`
- `from lc_agent.config.schema import MemoryConfig`
- `from lc_agent.core.auth import AuthService`
- `from lc_agent.core.engine import AgentEngine`
- `from lc_agent.core.memory import aclose_memory_store`
- `from lc_agent.core.memory import create_sqlite_memory_store`
- `from lc_agent.core.permissions import PermissionsService`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.engine import init_db`
- `from lc_agent.db.models_auth import User`
- `from lc_agent.mcp.manager import McpManager`
- `from lc_agent.server.app import create_app`
- `from lc_agent.server.app import mount_static_files`
- `from lc_agent.server import sse as sse_module`
- `from lc_agent.skills.filtered_loader import FilteredSkillLoader`
- `from lc_agent.skills.script_executor import patch_windows_script_executor`
- `from lc_agent.utils.loggers import app_logger`
- `from lc_agent.utils.loggers import mcp_logger`
- `import asyncio`
- `from lc_agent.db.models import SessionMeta`
- `from sqlalchemy import select`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.models import AgentPresetDB`
- `from lc_agent.core.models import AgentPreset`
- `from lc_agent.core.models import SubAgentLink`
- `from sqlalchemy import select`
- `from lc_agent.core.models import AgentPreset`
- `from lc_agent import __version__`
- `from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver`
- `import aiosqlite`

#### 🏛️ Classes (1)

##### 📌 `class LcAgentApp`
*Line: 56*

**Docstring:**
`````
Main application orchestrator — creates engine, server, and runs.
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, config: dict, host: str = '127.0.0.1', port: int = 8000)`
  - **Parameters:**
    - `self`
    - `config: dict`
    - `host: str = '127.0.0.1'`
    - `port: int = 8000`

**Public Methods (2):**
- `def add_agent(self, name: str, graph, description: str = '', delegation_description: str = '', display_name: str | None = None)`
  - **Docstring:**
  `````
  Register a pre-built CompiledStateGraph as a named agent.
  
  Args:
      name: Unique agent identifier (ASCII slug recommended)
      graph: A compiled LangGraph (must have ainvoke and astream_events)
      description: Human-readable description
      delegation_description: Default delegation guidance for parent agents
      display_name: Optional human-readable display name (can be non-ASCII)
  `````
- `def run(self)`
  - *Start the server (blocking).*


---




### 📄 Python File Metadata: `lc_agent/core/engine.py`


---



## 🔗 lc_agent Some File Dependencies Analysis

以下是项目文件之间的依赖关系，帮助 AI 理解代码结构：

### 📊 Internal Dependencies Graph

`````
Core Files (imported by other files, sorted by import count):
  ◆ lc_agent/__init__.py (imported by 1 files)
  ◆ lc_agent/app.py (imported by 1 files)
  ◆ lc_agent/core/engine.py (imported by 1 files)

`````

### 📋 Detailed Dependencies

#### `lc_agent/__init__.py`

**Imports from project:**
- `lc_agent/app.py`

**Imported by:**
- `lc_agent/app.py`

#### `lc_agent/app.py`

**Imports from project:**
- `lc_agent/__init__.py`
- `lc_agent/core/engine.py`

**Imported by:**
- `lc_agent/__init__.py`

#### `lc_agent/core/engine.py`

**Imported by:**
- `lc_agent/app.py`

### 📦 Third-party Dependencies

项目使用的第三方库：

- `aiosqlite`
- `fastapi`
- `langchain_agentskills`
- `langgraph`
- `sqlalchemy`
- `uvicorn`
- ......以及更多的第三方库......


---
# markdown content namespace: lc_agent Project Root Dir Some Files 


## lc_agent File Tree (relative dir: `.`)


`````

├── README.md
└── pyproject.toml

`````

---


## lc_agent (relative dir: `.`)  Included Files (total: 2 files)


- `README.md`

- `pyproject.toml`


---


--- **start of file: README.md** (project: lc_agent) --- 

`````markdown
# lc-agent

> Visual Agent Runtime Control Plane built on LangChain / LangGraph.
>
> 一个可视化、可热切换、可人在环路管控的 Agent 运行时控制平面。

[![PyPI package](https://img.shields.io/badge/pypi-lc--agent--app-blue)](https://pypi.org/project/lc-agent-app/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

`lc-agent` 既是可以直接使用的 Agent 工作台，也是可以被业务项目导入的 Python 框架。

它把 **模型、思考参数、Tools、MCP、Skills、子 Agent、长期记忆、知识库入口、Human-in-the-top 控制** 放进一个统一的 Web UI 里，并支持运行时热切换配置，无需重启代码。

演示项目：[lc-agent-bfzs](https://github.com/ydf0509/lc-agent-bfzs)

## 为什么是 lc-agent

很多 Agent 项目只解决其中一部分问题：有的只做聊天 UI，有的只做 MCP，有的只做工具调用，有的只做 LangGraph 编排。

`lc-agent` 的定位不是普通聊天网页，而是 **Agent Runtime Control Plane**：

- **运行时热切换**：模型、思考等级、工具组、MCP、Skills、Agent 默认态都可以在前端切换，无需重启服务
- **统一能力编排**：把 Tools、MCP、Skills、子 Agent、代码型 Graph 接入同一个执行入口
- **Human-in-the-top**：人站在最高控制层，可以审批、接管、切换配置、限制工具权限
- **可观测执行过程**：thinking、tool call、HTTP trace、token usage、子 Agent 执行过程都能看到
- **框架与产品一体**：既能开箱当工作台用，也能 `import lc_agent` 嵌入自己的业务项目

## 核心能力

| 能力 | 说明 |
| --- | --- |
| Agent Runtime | 内置 Chat / Empty / Power 预设，支持网页创建 Agent 与代码注册 Agent |
| Hot-swappable Config | 前端运行时切换模型、LLM 参数、工具、MCP、Skills，无需重启代码 |
| Tools | `@tool` 装饰器注册 Python 工具，支持分组展示与权限控制 |
| MCP | 支持 `stdio`、`SSE`、Streamable HTTP，自动适配 MCP 工具 schema |
| Skills | 扫描 `SKILL.md` 技能目录，支持渐进式发现与运行时开关 |
| Sub-agents | 支持子 Agent / 通用子 Agent 委派，并保留独立执行过程 |
| Human Control | 支持 Human-in-the-loop 审批与 Human-in-the-top 总控式调度 |
| AskUser | Agent 在信息不足、需求有歧义或关键动作前，可以主动询问用户确认 |
| Autonomous Planning | LLM 可用 TodoWrite 自主拆解任务步骤、维护执行计划、持续更新进度 |
| Memory | 支持会话持久化、历史消息、checkpoint 与长期上下文扩展 |
| Knowledge Base | 不内置强绑定 RAG，可通过 MCP 接入 [nbrag](https://github.com/ydf0509/nbrag) 等 agentic search 知识库 |
| Observability | HTTP trace、token 面板、工具调用卡片、子 Agent 过程可视化 |
| Auth & Permission | 支持登录认证、用户隔离、管理员能力、审批白名单 |

## 截图

说明：产品界面与实际有差异，实际界面更加美观，功能更加强大，截图时间太早了，后来持续增加了功能，以实际运行界面为准。

**桌面端：对话 + MCP / Skills 面板**

![桌面端对话界面](https://raw.githubusercontent.com/ydf0509/lc-agent/main/docs_pic/pc01.png)

**可观测性：HTTP 追踪 + Token 面板 + 工具调用**

![HTTP追踪与Token面板](https://raw.githubusercontent.com/ydf0509/lc-agent/main/docs_pic/pc02.png)

**工具调用详情**

![工具调用卡片](https://raw.githubusercontent.com/ydf0509/lc-agent/main/docs_pic/pc03.png)

**移动端**

![移动端界面](https://raw.githubusercontent.com/ydf0509/lc-agent/main/docs_pic/phone01.png)

## 快速开始

### 安装

PyPI 包名是 **`lc-agent-app`**，不是 `lc-agent`。

```bash
pip install lc-agent-app
```

如果你是从源码开发：

```bash
git clone https://github.com/ydf0509/lc-agent.git
cd lc-agent
pip install -e ".[dev,desktop]"
```

### 启动工作台

```bash
cp config.example.jsonc config.jsonc
# 编辑 config.jsonc，至少配置 provider、models、agent.default_model
lc-agent
# 打开 http://127.0.0.1:8000
```

如果配置里启用了 `auth.secret`，首次启动会进入登录流；默认会自动创建一个管理员账号：

- 用户名：`admin`
- 密码：`123456`

首次登录后建议立即修改密码。

## 作为框架使用

### 注册 Python 工具

```python
from lc_agent import LcAgentApp, load_config, tool

@tool(group="my_tools", group_description="我的工具")
def my_tool(query: str) -> str:
    """工具描述，会展示给 Agent 判断何时使用。"""
    return f"result: {query}"

config = load_config(config_path="./config.jsonc")
app = LcAgentApp(config, host="127.0.0.1", port=8001)
app.run()
```

### 注册代码型 Agent

你可以把自己写好的 LangGraph `CompiledStateGraph` 注册到 lc-agent，复用现成前端、会话、权限、审批和可观测能力。

```python
from lc_agent import LcAgentApp, load_config
from my_agents import build_my_agent

config = load_config("./config.jsonc")
app = LcAgentApp(config, host="127.0.0.1", port=8001)
app.add_agent("my_agent", build_my_agent(config), description="自定义 Agent")
app.run()
```

## 配置重点

大多数用户只需要关心这几个配置块：

- `provider`：模型提供商与模型列表
- `agent.default_model`：默认模型
- `skills`：Skills 目录
- `mcp_servers`：MCP 服务器配置
- `database`：会话与 checkpoint 存储
- `auth`：登录认证与管理员配置

配置文件使用 `config.jsonc`，支持：

- JSONC 注释
- `{env:VAR}` 环境变量替换
- `.env` 自动加载

## MCP、Skills 与知识库

`lc-agent` 不把知识库硬编码进框架，而是通过 MCP 解耦接入。

这意味着你可以把 [nbrag](https://github.com/ydf0509/nbrag)、文件检索、网页搜索、数据库查询、业务系统 API 等能力全部作为 MCP 或 tool 接入同一个 Agent 控制台。

推荐理解方式：

- **Tools**：项目内 Python 函数，适合业务工具和本地能力
- **MCP**：外部工具服务器，适合跨项目复用和进程隔离
- **Skills**：面向 Agent 的能力说明与工作流知识，适合渐进式触发
- **[nbrag](https://github.com/ydf0509/nbrag) / RAG**：作为 MCP 工具接入，保持知识库与 Agent 框架低耦合

## Human-in-the-top

`lc-agent` 支持的不只是传统 human-in-the-loop。

Human-in-the-loop 通常是 Agent 遇到危险动作时请求审批；而 lc-agent 更强调 **Human-in-the-top**：

- 人可以在运行时切换模型和思考参数
- 人可以随时打开或关闭 tool groups、MCP servers、Skills
- 人可以切换不同 Agent 默认态，避免工具能力张冠李戴
- 人可以审批危险工具，并把可信工具加入持久化白名单
- Agent 可以在信息不足、存在歧义或需要确认时主动 AskUser，而不是低质量猜测
- Agent 可以用 TodoWrite 自主拆解任务、维护计划、更新进度，让复杂任务可追踪
- 人可以查看 Agent 与子 Agent 的完整执行过程

## API 与通信方式

`lc-agent` 当前主要通过 **REST + SSE** 工作。

常用接口包括：

- `POST /api/threads/{thread_id}/runs/stream`：SSE 流式运行
- `POST /api/threads/{thread_id}/runs/cancel`：取消当前生成
- `GET /api/agents/available-subagents`：查询可选子 Agent
- `GET /api/sessions/{id}/messages`：分页读取会话消息
- `GET /api/sessions/{id}/messages/{message_id}/traces`：读取单条消息 trace
- `GET /api/permissions`、`POST /api/permissions/allow`、`POST /api/permissions/remove`：审批白名单管理
- `POST /api/auth/login`、`GET /api/auth/me`：登录与用户信息

## 和普通聊天网页的区别

如果只聊天，lc-agent 和普通聊天网页都能完成任务。

lc-agent 真正多出来的是：

- 你能看见 Agent 在做什么
- 你能控制 Agent 可以用什么
- 你能把多个能力源拼起来：Tools、MCP、Skills、子 Agent、自定义 Graph、知识库入口
- 你不需要自己再做前端、会话、审批、trace、调试面板

简化理解：

- **普通聊天网页**：更像对话产品
- **lc-agent**：更像可直接运行、也可二次开发的 Agent 工作台 / Runtime Control Plane

## 项目关系

| 项目 | 角色 |
| --- | --- |
| [lc-agent](https://github.com/ydf0509/lc-agent) | 框架与通用 Web UI |
| [lc-agent-bfzs](https://github.com/ydf0509/lc-agent-bfzs) | 基于 lc-agent 的演示应用 |
| [nbrag](https://github.com/ydf0509/nbrag) | 可通过 MCP 接入的 agentic search 知识库 |

## 登录和部署边界

lc-agent 已经支持登录认证、用户隔离、管理员能力。

但它的定位不是纯云端托管聊天站，而是一个可以接本地工具、MCP、脚本和执行环境的 Agent 框架。因此更适合：

- 单机部署
- 内网部署
- 用户自己可控的服务器或工作机

如果你给 Agent 接了文件系统、命令执行或自定义 MCP，它运行的仍然是**部署机器的权限边界**。

## 开发

后端开发：

```bash
pip install -e ".[dev]"
pytest
```

前端开发：

```bash
cd frontend
npm install
npm run dev
npm run build
```

常用前端契约测试：

```bash
cd frontend
npm run test:new-chat-right-panel
npm run test:session-route
npm run test:code-agent
```

## FAQ

### lc-agent 是否内置 RAG 知识库？

不强绑定内置知识库。

推荐通过 MCP 接入 [nbrag](https://github.com/ydf0509/nbrag) 这类 agentic search 知识库。这样知识库能力可以同时服务 lc-agent、OpenClaw、Claude Code、Codex、Trae、Cursor、WorkBuddy、Qoder 等不同 Agent 客户端，框架和知识库保持低耦合。

### lc-agent 是产品还是框架？

两者都是。

你可以直接把它当 Agent 工作台使用，也可以把它作为 Python 包导入业务项目，复用现成 Web UI、会话、审批、MCP、Skills、工具注册、可观测性和运行时配置能力。

### 切换配置需要重启吗？

大多数运行时配置不需要。

模型、思考参数、工具组、MCP、Skills、Agent 默认态都可以通过前端热切换。只有修改 Python 代码、安装新依赖或调整底层服务部署时才需要重启对应服务。

### lc-agent 能不能联网查询问题？

答： 你购买apikey后，模型厂商是不会自动送你联网功能的，联网实际是通过工具调用。
所以你可以配置mcp，市面上能联网的mcp有很多

例如配置 Open Web Search MCP，你在docker里面启动mcp服务，然后配置到config.jsonc里面的mcp_servers，agent可以勾选启用这个mcp，这样`agent`就能联网查询新闻了，而且可以启用web-search这个skill，引导ai何时联网，怎么高效使用这个mcp的各个工具。
```jsonc
{
    ...其他配置...
  "mcp_servers": {

    // Web 搜索 MCP
     // 实时网页搜索 MCP（SSE 方式）
      // Open Web Search（多引擎搜索 + 文章抓取，Docker 部署）
      // 启动: docker run -d --name web-search -p 3000:3000 -e ENABLE_CORS=true -e CORS_ORIGIN=* ghcr.io/aas-ee/open-web-search:latest
    "web-search": {
      "type": "http",
      "url": "http://localhost:3000/mcp",
      "enabled": true
    },
  }
}
```

## License

MIT

`````

--- **end of file: README.md** (project: lc_agent) --- 

---


--- **start of file: pyproject.toml** (project: lc_agent) --- 

`````text
[project]
name = "lc-agent-app"
version = "0.2.3"
description = "LangChain Agent framework with built-in Web UI"
requires-python = ">=3.12"
license = "MIT"
dependencies = [
    "langchain>=1.0",
    "langgraph>=0.4",
    "langchain-openai",
    "langchain-deepseek",
    "fastapi>=0.115",
    "uvicorn[standard]",
    "sqlmodel>=0.0.22",
    "aiosqlite>=0.20",
    "alembic>=1.13",
    "langgraph-checkpoint-sqlite>=3.0",
    "python-dotenv",
    "commentjson",
    "websockets",
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "langchain-agentskills>=0.4",
    "mcp>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "httpx",
    "ruff",
]
desktop = [
    "pywebview>=5.0",
]

[project.scripts]
lc-agent = "lc_agent.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["lc_agent"]

[tool.hatch.build.targets.sdist]
include = ["lc_agent/**", "README.md", "pyproject.toml", "LICENSE"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 120

`````

--- **end of file: pyproject.toml** (project: lc_agent) --- 

---

# markdown content namespace: lc_agent Python 后端源码 


## lc_agent File Tree (relative dir: `lc_agent`)


`````

└── lc_agent
    ├── __init__.py
    ├── __main__.py
    ├── app.py
    ├── config
    │   ├── __init__.py
    │   ├── loader.py
    │   └── schema.py
    ├── core
    │   ├── __init__.py
    │   ├── auth.py
    │   ├── chat_model.py
    │   ├── engine.py
    │   ├── http_trace.py
    │   ├── http_trace_httpx.py
    │   ├── memory.py
    │   ├── models.py
    │   ├── permissions.py
    │   └── traced_llm.py
    ├── db
    │   ├── __init__.py
    │   ├── engine.py
    │   ├── migrations
    │   │   ├── env.py
    │   │   └── versions
    │   │       ├── 20260623_add_http_traces_to_chat_ui_messages.py
    │   │       ├── 20260704_add_users.py
    │   │       ├── 20260704_drop_dangerous_tools.py
    │   │       ├── 20260706_add_llm_params.py
    │   │       ├── 20260707_add_subagent_fields.py
    │   │       ├── 20260708_add_general_purpose_subagent.py
    │   │       ├── 20260710_add_display_name.py
    │   │       ├── 20260710_rename_builtin_ids.py
    │   │       ├── 20260715_chat_content_to_json.py
    │   │       └── a342dc61a740_initial_schema.py
    │   ├── models.py
    │   ├── models_auth.py
    │   └── repository.py
    ├── desktop.py
    ├── main.py
    ├── mcp
    │   ├── __init__.py
    │   ├── manager.py
    │   └── tool_adapter.py
    ├── server
    │   ├── __init__.py
    │   ├── app.py
    │   ├── auth_middleware.py
    │   ├── dependencies.py
    │   ├── persistence.py
    │   ├── routes
    │   │   ├── __init__.py
    │   │   ├── admin.py
    │   │   ├── agents.py
    │   │   ├── auth.py
    │   │   ├── health.py
    │   │   ├── mcp.py
    │   │   ├── models.py
    │   │   ├── permissions.py
    │   │   ├── sessions.py
    │   │   ├── settings.py
    │   │   ├── skills.py
    │   │   └── tools.py
    │   ├── sse.py
    │   ├── stream_utils.py
    │   └── subagent_tracker.py
    ├── skills
    │   ├── __init__.py
    │   ├── filtered_loader.py
    │   ├── scanner.py
    │   └── script_executor.py
    ├── tools
    │   ├── __init__.py
    │   ├── builtin.py
    │   ├── contrib_tools
    │   │   ├── __init__.py
    │   │   ├── ask_user_tool.py
    │   │   └── get_time.py
    │   └── registry.py
    └── utils
        └── loggers.py

`````

---


## lc_agent (relative dir: `lc_agent`)  Included Files (total: 68 files)


- `lc_agent/app.py`

- `lc_agent/desktop.py`

- `lc_agent/main.py`

- `lc_agent/__init__.py`

- `lc_agent/__main__.py`

- `lc_agent/config/loader.py`

- `lc_agent/config/schema.py`

- `lc_agent/config/__init__.py`

- `lc_agent/core/auth.py`

- `lc_agent/core/chat_model.py`

- `lc_agent/core/engine.py`

- `lc_agent/core/http_trace.py`

- `lc_agent/core/http_trace_httpx.py`

- `lc_agent/core/memory.py`

- `lc_agent/core/models.py`

- `lc_agent/core/permissions.py`

- `lc_agent/core/traced_llm.py`

- `lc_agent/core/__init__.py`

- `lc_agent/db/engine.py`

- `lc_agent/db/models.py`

- `lc_agent/db/models_auth.py`

- `lc_agent/db/repository.py`

- `lc_agent/db/__init__.py`

- `lc_agent/db/migrations/env.py`

- `lc_agent/db/migrations/versions/20260623_add_http_traces_to_chat_ui_messages.py`

- `lc_agent/db/migrations/versions/20260704_add_users.py`

- `lc_agent/db/migrations/versions/20260704_drop_dangerous_tools.py`

- `lc_agent/db/migrations/versions/20260706_add_llm_params.py`

- `lc_agent/db/migrations/versions/20260707_add_subagent_fields.py`

- `lc_agent/db/migrations/versions/20260708_add_general_purpose_subagent.py`

- `lc_agent/db/migrations/versions/20260710_add_display_name.py`

- `lc_agent/db/migrations/versions/20260710_rename_builtin_ids.py`

- `lc_agent/db/migrations/versions/20260715_chat_content_to_json.py`

- `lc_agent/db/migrations/versions/a342dc61a740_initial_schema.py`

- `lc_agent/mcp/manager.py`

- `lc_agent/mcp/tool_adapter.py`

- `lc_agent/mcp/__init__.py`

- `lc_agent/server/app.py`

- `lc_agent/server/auth_middleware.py`

- `lc_agent/server/dependencies.py`

- `lc_agent/server/persistence.py`

- `lc_agent/server/sse.py`

- `lc_agent/server/stream_utils.py`

- `lc_agent/server/subagent_tracker.py`

- `lc_agent/server/__init__.py`

- `lc_agent/server/routes/admin.py`

- `lc_agent/server/routes/agents.py`

- `lc_agent/server/routes/auth.py`

- `lc_agent/server/routes/health.py`

- `lc_agent/server/routes/mcp.py`

- `lc_agent/server/routes/models.py`

- `lc_agent/server/routes/permissions.py`

- `lc_agent/server/routes/sessions.py`

- `lc_agent/server/routes/settings.py`

- `lc_agent/server/routes/skills.py`

- `lc_agent/server/routes/tools.py`

- `lc_agent/server/routes/__init__.py`

- `lc_agent/skills/filtered_loader.py`

- `lc_agent/skills/scanner.py`

- `lc_agent/skills/script_executor.py`

- `lc_agent/skills/__init__.py`

- `lc_agent/tools/builtin.py`

- `lc_agent/tools/registry.py`

- `lc_agent/tools/__init__.py`

- `lc_agent/tools/contrib_tools/ask_user_tool.py`

- `lc_agent/tools/contrib_tools/get_time.py`

- `lc_agent/tools/contrib_tools/__init__.py`

- `lc_agent/utils/loggers.py`


---


--- **start of file: lc_agent/app.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/app.py`

#### 📦 Imports

- `from contextlib import asynccontextmanager`
- `from pathlib import Path`
- `import uvicorn`
- `from fastapi import FastAPI`
- `from langchain_agentskills import SkillsToolkit`
- `from langchain_agentskills.loaders import CompositeSkillLoader`
- `from langchain_agentskills.loaders import DirectorySkillLoader`
- `from lc_agent.config.schema import MemoryConfig`
- `from lc_agent.core.auth import AuthService`
- `from lc_agent.core.engine import AgentEngine`
- `from lc_agent.core.memory import aclose_memory_store`
- `from lc_agent.core.memory import create_sqlite_memory_store`
- `from lc_agent.core.permissions import PermissionsService`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.engine import init_db`
- `from lc_agent.db.models_auth import User`
- `from lc_agent.mcp.manager import McpManager`
- `from lc_agent.server.app import create_app`
- `from lc_agent.server.app import mount_static_files`
- `from lc_agent.server import sse as sse_module`
- `from lc_agent.skills.filtered_loader import FilteredSkillLoader`
- `from lc_agent.skills.script_executor import patch_windows_script_executor`
- `from lc_agent.utils.loggers import app_logger`
- `from lc_agent.utils.loggers import mcp_logger`
- `import asyncio`
- `from lc_agent.db.models import SessionMeta`
- `from sqlalchemy import select`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.models import AgentPresetDB`
- `from lc_agent.core.models import AgentPreset`
- `from lc_agent.core.models import SubAgentLink`
- `from sqlalchemy import select`
- `from lc_agent.core.models import AgentPreset`
- `from lc_agent import __version__`
- `from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver`
- `import aiosqlite`

#### 🏛️ Classes (1)

##### 📌 `class LcAgentApp`
*Line: 56*

**Docstring:**
`````
Main application orchestrator — creates engine, server, and runs.
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, config: dict, host: str = '127.0.0.1', port: int = 8000)`
  - **Parameters:**
    - `self`
    - `config: dict`
    - `host: str = '127.0.0.1'`
    - `port: int = 8000`

**Public Methods (2):**
- `def add_agent(self, name: str, graph, description: str = '', delegation_description: str = '', display_name: str | None = None)`
  - **Docstring:**
  `````
  Register a pre-built CompiledStateGraph as a named agent.
  
  Args:
      name: Unique agent identifier (ASCII slug recommended)
      graph: A compiled LangGraph (must have ainvoke and astream_events)
      description: Human-readable description
      delegation_description: Default delegation guidance for parent agents
      display_name: Optional human-readable display name (can be non-ASCII)
  `````
- `def run(self)`
  - *Start the server (blocking).*


---

`````python
# lc_agent/app.py

from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from langchain_agentskills import SkillsToolkit
from langchain_agentskills.loaders import CompositeSkillLoader, DirectorySkillLoader

from lc_agent.config.schema import MemoryConfig
from lc_agent.core.auth import AuthService
from lc_agent.core.engine import AgentEngine
from lc_agent.core.memory import aclose_memory_store, create_sqlite_memory_store
from lc_agent.core.permissions import PermissionsService
from lc_agent.db.engine import get_async_session, init_db
from lc_agent.db.models_auth import User
from lc_agent.mcp.manager import McpManager
from lc_agent.server.app import create_app, mount_static_files
from lc_agent.server import sse as sse_module
from lc_agent.skills.filtered_loader import FilteredSkillLoader
from lc_agent.skills.script_executor import patch_windows_script_executor
from lc_agent.utils.loggers import app_logger, mcp_logger


def _resolve_sqlite_url(url: str, root: Path) -> str:
    prefixes = ("sqlite+aiosqlite:///", "sqlite:///")
    for prefix in prefixes:
        if not url.startswith(prefix):
            continue
        path_part = url[len(prefix):]
        if path_part in (":memory:", ""):
            return url
        path = Path(path_part)
        if path.is_absolute():
            return url
        return f"{prefix}{(root / path).resolve().as_posix()}"
    return url


def _resolve_file_path(path: str, root: Path) -> str:
    if path == ":memory:":
        return path
    file_path = Path(path)
    if file_path.is_absolute():
        return str(file_path)
    return str((root / file_path).resolve())


def _get_config_value(config, name: str, default=None):
    if isinstance(config, dict):
        return config.get(name, default)
    return getattr(config, name, default)


class LcAgentApp:
    """Main application orchestrator — creates engine, server, and runs."""

    def __init__(self, config: dict, host: str = "127.0.0.1", port: int = 8000):
        self.config = config
        project_root = Path(config.get("_project_root") or Path.cwd())
        database_config = self.config.setdefault("database", {})
        database_config["url"] = _resolve_sqlite_url(
            database_config.get("url", "sqlite+aiosqlite:///./lc_agent_data.db"),
            project_root,
        )
        database_config["checkpoint_path"] = _resolve_file_path(
            database_config.get("checkpoint_path", "./lc_agent_checkpoints.db"),
            project_root,
        )
        self.host = host
        self.port = port
        self._db_url = database_config["url"]
        self._checkpoint_path = database_config["checkpoint_path"]
        permissions_path = config.get("permissions", {}).get("path", "./permissions.jsonc")
        self._permissions_service = PermissionsService(permissions_path=Path(permissions_path))
        self.engine = AgentEngine(config)
        skills_dirs = config.get("skills", ["./skills"])
        existing_dirs = [d for d in skills_dirs if Path(d).is_dir()]
        if existing_dirs:
            inner_loaders = [DirectorySkillLoader(d) for d in existing_dirs]
            inner = inner_loaders[0] if len(inner_loaders) == 1 else CompositeSkillLoader(inner_loaders)
            self.filtered_loader = FilteredSkillLoader(inner)
            self.skills_toolkit = SkillsToolkit(loaders=[self.filtered_loader])
            patch_windows_script_executor(self.skills_toolkit)
        else:
            self.filtered_loader = None
            self.skills_toolkit = None
        mcp_config = config.get("mcp_servers", {})
        self.mcp_manager = McpManager(mcp_config, on_state_change=self._on_mcp_state_change)
        self.fastapi_app = create_app(config, lifespan=self._lifespan)
        self.fastapi_app.state.mcp_manager = self.mcp_manager
        self.fastapi_app.state.skills_toolkit = self.skills_toolkit
        self.fastapi_app.state.filtered_loader = self.filtered_loader
        self.engine._skills_toolkit = self.skills_toolkit
        self.engine._mcp_manager = self.mcp_manager
        self.fastapi_app.state.engine = self.engine
        self.fastapi_app.state.permissions = self._permissions_service
        self.engine._permissions_service = self._permissions_service
        sse_module.configure(self.engine, self._db_url)
        mount_static_files(self.fastapi_app)

    def _on_mcp_state_change(self):
        self.engine._mcp_generation += 1

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """FastAPI lifespan: startup and shutdown logic."""
        import asyncio

        memory_store = None
        try:
            await init_db(self._db_url)
            await self._init_auth(app)
            try:
                from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
                import aiosqlite
                conn = await aiosqlite.connect(self._checkpoint_path)
                saver = AsyncSqliteSaver(conn)
                await saver.setup()
                self.engine._checkpointer = saver
            except Exception:
                app_logger.exception("Checkpoint saver setup failed, using None")

            memory_config = self.config.get("memory")
            if memory_config is None:
                memory_config = MemoryConfig().model_dump()
            if _get_config_value(memory_config, "enabled", False):
                memory_type = _get_config_value(memory_config, "type", "sqlite")
                if memory_type != "sqlite":
                    raise ValueError("Only sqlite long-term memory is supported")
                memory_path = _resolve_file_path(
                    _get_config_value(memory_config, "path", "./lc_agent_memory.db"),
                    Path(self.config.get("_project_root") or Path.cwd()),
                )
                memory_store = await create_sqlite_memory_store(memory_path, memory_config=memory_config)
                self.engine._store = memory_store

            await self._load_presets_from_db()

            async def _connect_mcp_background():
                try:
                    await self.mcp_manager.connect_all()
                    connected = [s for s in self.mcp_manager.servers if s.status == "connected"]
                    if connected:
                        mcp_logger.info("Connected MCP servers: %s", [s.name for s in connected])
                except Exception:
                    mcp_logger.exception("Background MCP connection error")

            asyncio.create_task(_connect_mcp_background())
            yield
        finally:
            if memory_store is not None:
                await aclose_memory_store(memory_store)
                self.engine._store = None
            await self.mcp_manager.shutdown()

    async def _init_auth(self, app: FastAPI) -> None:
        """Initialize auth service and ensure at least one admin exists."""
        auth_config = self.config.get("auth", {})
        secret = auth_config.get("secret", "")
        if not secret:
            app_logger.warning("auth.secret not configured, authentication disabled")
            return
        if len(secret) < 16:
            raise ValueError("Auth secret must be at least 16 characters")

        token_expire_days = auth_config.get("token_expire_days", 7)
        auth_service = AuthService(secret=secret, token_expire_days=token_expire_days)
        app.state.auth_service = auth_service

        from lc_agent.db.models import SessionMeta
        from sqlalchemy import select

        db = get_async_session(self._db_url)
        try:
            result = await db.execute(select(User).where(User.role == "admin"))
            admin = result.scalar_one_or_none()
            if admin is None:
                password = "123456"
                admin = User(
                    username="admin",
                    password_hash=auth_service.hash_password(password),
                    role="admin",
                )
                db.add(admin)

                await db.execute(
                    SessionMeta.__table__.update().where(SessionMeta.user_id == "").values(user_id=admin.id)
                )

                await db.commit()
                app_logger.warning("Created initial admin user with default password; change it immediately")
            else:
                app_logger.info("Admin user exists: %s", admin.username)
        finally:
            await db.close()

    async def _load_presets_from_db(self):
        """Load user-created presets from database on startup."""
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.models import AgentPresetDB
        from lc_agent.core.models import AgentPreset, SubAgentLink
        from sqlalchemy import select

        session = get_async_session(self._db_url)
        try:
            stmt = select(AgentPresetDB)
            result = await session.execute(stmt)
            for row in result.scalars().all():
                preset = AgentPreset(
                    id=row.id,
                    name=row.name,
                    system_prompt=row.system_prompt,
                    default_model=row.default_model,
                    allowed_tool_groups=row.allowed_tool_groups,
                    allowed_mcp_servers=row.allowed_mcp_servers,
                    allowed_skills=row.allowed_skills,
                    llm_params=row.llm_params,
                    subagents=[SubAgentLink.model_validate(item) for item in row.subagents] if row.subagents else None,
                    enable_general_purpose_subagent=row.enable_general_purpose_subagent,
                )
                self.engine._presets[preset.id] = preset
            loaded = len(self.engine._presets)
            if loaded:
                app_logger.info("Loaded %s user presets from database", loaded)
        except Exception as e:
            app_logger.exception("Failed to load presets from DB")
        finally:
            await session.close()

    def add_agent(self, name: str, graph, description: str = "", delegation_description: str = "", display_name: str | None = None):
        """Register a pre-built CompiledStateGraph as a named agent.

        Args:
            name: Unique agent identifier (ASCII slug recommended)
            graph: A compiled LangGraph (must have ainvoke and astream_events)
            description: Human-readable description
            delegation_description: Default delegation guidance for parent agents
            display_name: Optional human-readable display name (can be non-ASCII)
        """
        if name in self.engine._agents:
            raise ValueError(f"Agent '{name}' already registered")

        from lc_agent.core.models import AgentPreset

        self.engine._agents[name] = graph
        self.engine._agent_mcp_gen[name] = self.engine._mcp_generation
        preset = AgentPreset(
            id=name,
            name=name,
            display_name=display_name,
            system_prompt=description or f"Custom agent: {name}",
            default_model="custom",
            default_delegation_description=delegation_description,
            allowed_tool_groups=[],
            allowed_mcp_servers=[],
            allowed_skills=[],
            source="code",
            default_enabled=False,
        )
        self.engine._custom_presets[name] = preset

    def run(self):
        """Start the server (blocking)."""
        from lc_agent import __version__

        app_logger.info("lc_agent v%s", __version__)
        app_logger.info("Web UI: http://%s:%s", self.host, self.port)
        app_logger.info("API Docs: http://%s:%s/api/docs", self.host, self.port)
        uvicorn.run(self.fastapi_app, host=self.host, port=self.port)

`````

--- **end of file: lc_agent/app.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/desktop.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/desktop.py`

#### 📦 Imports

- `import multiprocessing`
- `import socket`
- `import time`
- `from pathlib import Path`
- `import sys`
- `from lc_agent.utils.loggers import desktop_logger`
- `import os`
- `import time`
- `import os`
- `import argparse`
- `import ctypes`
- `from ctypes import wintypes`
- `import ctypes`
- `from ctypes import wintypes`
- `import ctypes`
- `from ctypes import wintypes`
- `import webview`

#### 🔧 Public Functions (5)

- `def wait_for_port(host: str, port: int, timeout: float = 30.0)`
  - *Line: 11*

- `def get_work_area() -> tuple[int, int, int, int]`
  - *Line: 23*

- `def get_webview_storage_path() -> str`
  - *Line: 36*

- `def launch_desktop(host: str, port: int, title: str = 'lc-agent') -> multiprocessing.Process | None`
  - *Line: 177*
  - **Docstring:**
  `````
  Launch a webview window in a subprocess pointing at the server.
  
  Returns the Process object (or None if the server is not reachable).
  The caller (uvicorn main process) keeps running regardless of whether
  the webview is open or closed.
  `````

- `def on_started()`
  - *Line: 170*


---

`````python

import multiprocessing
import socket
import time
from pathlib import Path
import sys

from lc_agent.utils.loggers import desktop_logger


def wait_for_port(host: str, port: int, timeout: float = 30.0):
    deadline = time.monotonic() + timeout
    connect_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((connect_host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def get_work_area() -> tuple[int, int, int, int]:
    try:
        import ctypes
        from ctypes import wintypes

        rect = wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
    except Exception:
        pass
    return 0, 0, 1400, 900


def get_webview_storage_path() -> str:
    path = Path.cwd() / ".tmp" / "webview2-data"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def _apply_dark_titlebar(title: str):
    """Set dark/themed title bar on Windows 10/11 via DWM API."""
    import os
    import time

    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        dwm = ctypes.windll.dwmapi

        dwm.DwmSetWindowAttribute.argtypes = [
            wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
        ]
        dwm.DwmSetWindowAttribute.restype = ctypes.HRESULT

        # Find the webview window by enumerating windows in this process
        pid = os.getpid()
        candidates: list[int] = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def _enum_cb(h, _lp):
            wpid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(h, ctypes.byref(wpid))
            if wpid.value == pid and user32.IsWindowVisible(h):
                candidates.append(h)
            return True

        for _ in range(20):
            candidates.clear()
            user32.EnumWindows(_enum_cb, 0)
            if candidates:
                break
            time.sleep(0.5)

        if not candidates:
            desktop_logger.warning("No visible window found in PID %s", pid)
            return

        for hwnd in candidates:
            dark = ctypes.c_int(1)
            # Try attribute 20 (Win10 20H1+), fallback to 19 (pre-20H1)
            hr = dwm.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), 4)
            if hr != 0:
                dwm.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(dark), 4)

            # DWMWA_CAPTION_COLOR = 35 (Windows 11+)
            # #141414 matches Element Plus dark --el-bg-color
            color = ctypes.c_uint(0x00141414)
            hr35 = dwm.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(color), 4)

            # Force non-client area redraw
            user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                0x0020 | 0x0001 | 0x0002 | 0x0004,  # FRAMECHANGED|NOSIZE|NOMOVE|NOZORDER
            )
            desktop_logger.info("Dark titlebar applied (hwnd=%s, caption_hr=%#x)", hwnd, hr35)

    except Exception:
        desktop_logger.exception("Failed to set dark titlebar")


def _apply_window_icon(title: str):
    """Set the window/taskbar icon to favicon.ico via Win32 API."""
    import os

    try:
        import ctypes
        from ctypes import wintypes

        ico_path = str(Path(__file__).parent / "web" / "dist" / "favicon.ico")
        if not Path(ico_path).exists():
            return

        user32 = ctypes.windll.user32
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010
        LR_DEFAULTSIZE = 0x0040
        WM_SETICON = 0x0080
        ICON_BIG = 1
        ICON_SMALL = 0

        pid = os.getpid()
        candidates: list[int] = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def _enum_cb(h, _lp):
            wpid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(h, ctypes.byref(wpid))
            if wpid.value == pid and user32.IsWindowVisible(h):
                candidates.append(h)
            return True

        user32.EnumWindows(_enum_cb, 0)

        for hwnd in candidates:
            big = user32.LoadImageW(0, ico_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
            small = user32.LoadImageW(0, ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
            if big:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, big)
            if small:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, small)
            desktop_logger.info("Window icon set (hwnd=%s)", hwnd)
    except Exception:
        desktop_logger.exception("Failed to set window icon")


def _webview_process(url: str, title: str):
    """Entry point for the webview subprocess."""
    try:
        import webview
    except ImportError:
        desktop_logger.warning("pywebview not installed, skipping desktop window")
        return

    x, y, width, height = get_work_area()
    webview.create_window(
        title=title,
        url=url,
        x=x,
        y=y,
        width=width,
        height=height,
        min_size=(800, 600),
        text_select=True,
    )

    def on_started():
        _apply_dark_titlebar(title)
        _apply_window_icon(title)

    webview.start(private_mode=False, storage_path=get_webview_storage_path(), func=on_started)


def launch_desktop(host: str, port: int, title: str = "lc-agent") -> multiprocessing.Process | None:
    """Launch a webview window in a subprocess pointing at the server.

    Returns the Process object (or None if the server is not reachable).
    The caller (uvicorn main process) keeps running regardless of whether
    the webview is open or closed.
    """
    url_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{url_host}:{port}/"
    if not wait_for_port(host, port, timeout=5.0):
        desktop_logger.error("Server %s:%s did not respond", host, port)
        sys.exit(1)
    _webview_process(url, title)

    # proc = multiprocessing.Process(
    #     target=_webview_process,
    #     args=(url, title),
    #     daemon=True,
    # )
    # proc.start()
    # return proc


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Open lc-agent desktop window")
    parser.add_argument("--url", default=None, help="Server URL to open")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--title", default="lc-agent", help="Window title")
    args = parser.parse_args()

    url = args.url or f"http://{args.host}:{args.port}/"
    desktop_logger.info("Opening %s", url)

    if not wait_for_port(args.host, args.port, timeout=5.0):
        desktop_logger.warning("Server at %s:%s not reachable, opening anyway", args.host, args.port)

    _webview_process(url, args.title)

`````

--- **end of file: lc_agent/desktop.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/main.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/main.py`

#### 📦 Imports

- `import argparse`
- `from lc_agent.config.loader import load_config`
- `from lc_agent.app import LcAgentApp`

#### 🔧 Public Functions (1)

- `def main()`
  - *Line: 5*


---

`````python
# lc_agent/main.py
import argparse


def main():
    parser = argparse.ArgumentParser(description="lc_agent - LangChain Agent with Web UI")
    parser.add_argument("--config", "-c", help="Path to config.jsonc")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--dotenv", help="Path to .env file")
    args = parser.parse_args()

    from lc_agent.config.loader import load_config

    config = load_config(config_path=args.config, dotenv_path=args.dotenv)

    from lc_agent.app import LcAgentApp

    app = LcAgentApp(config, host=args.host, port=args.port)
    app.run()


if __name__ == "__main__":
    main()

`````

--- **end of file: lc_agent/main.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/__init__.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/__init__.py`

#### 📝 Module Docstring

`````
lc_agent — LangChain Agent framework with built-in Web UI.
`````

#### 📦 Imports

- `from importlib.metadata import version`
- `from importlib.metadata import PackageNotFoundError`
- `from lc_agent.app import LcAgentApp`
- `from lc_agent.config.loader import load_config`
- `from lc_agent.core.traced_llm import create_traced_chat_openai`
- `from lc_agent.core.traced_llm import create_traced_openai_http_client`
- `from lc_agent.tools.registry import ToolRegistry`
- `from lc_agent.tools.registry import tool`


---

`````python
# lc_agent/__init__.py
"""lc_agent — LangChain Agent framework with built-in Web UI."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("lc-agent-app")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

from lc_agent.app import LcAgentApp
from lc_agent.config.loader import load_config
from lc_agent.core.traced_llm import (
    create_traced_chat_openai,
    create_traced_openai_http_client,
)
from lc_agent.tools.registry import ToolRegistry, tool

__all__ = [
    "LcAgentApp",
    "load_config",
    "create_traced_chat_openai",
    "create_traced_openai_http_client",
    "ToolRegistry",
    "tool",
    "__version__",
]

`````

--- **end of file: lc_agent/__init__.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/__main__.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/__main__.py`

#### 📦 Imports

- `from lc_agent.main import main`


---

`````python
from lc_agent.main import main

if __name__ == "__main__":
    main()

`````

--- **end of file: lc_agent/__main__.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/config/loader.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/config/loader.py`

#### 📦 Imports

- `import os`
- `import re`
- `from pathlib import Path`
- `from typing import Any`
- `import commentjson`
- `from dotenv import load_dotenv`

#### 🔧 Public Functions (4)

- `def substitute_env_vars(data: Any) -> Any`
  - *Line: 12*
  - *Recursively replace {env:VAR_NAME} patterns with environment variable values.*

- `def load_config_from_file(path: str) -> dict`
  - *Line: 36*
  - *Load a JSONC configuration file and apply env substitution.*

- `def load_config(config_path: str | None = None, dotenv_path: str | None = None) -> dict`
  - *Line: 48*
  - *Load configuration with priority: explicit path > ./config.jsonc > ~/.lc_agent/config.jsonc > defaults.*

- `def replacer(m)`
  - *Line: 22*


---

`````python
import os
import re
from pathlib import Path
from typing import Any

import commentjson
from dotenv import load_dotenv

ENV_PATTERN = re.compile(r"\{env:([^}]+)\}")


def substitute_env_vars(data: Any) -> Any:
    """Recursively replace {env:VAR_NAME} patterns with environment variable values."""
    if isinstance(data, str):
        match = ENV_PATTERN.fullmatch(data)
        if match:
            var_name = match.group(1)
            value = os.environ.get(var_name)
            if value is None:
                raise ValueError(f"Environment variable '{var_name}' not found")
            return value
        def replacer(m):
            var_name = m.group(1)
            value = os.environ.get(var_name)
            if value is None:
                raise ValueError(f"Environment variable '{var_name}' not found")
            return value
        return ENV_PATTERN.sub(replacer, data)
    elif isinstance(data, dict):
        return {k: substitute_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [substitute_env_vars(item) for item in data]
    return data


def load_config_from_file(path: str) -> dict:
    """Load a JSONC configuration file and apply env substitution."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(file_path, "r", encoding="utf-8") as f:
        raw = commentjson.load(f)

    return substitute_env_vars(raw)


def load_config(
    config_path: str | None = None,
    dotenv_path: str | None = None,
) -> dict:
    """Load configuration with priority: explicit path > ./config.jsonc > ~/.lc_agent/config.jsonc > defaults."""
    if dotenv_path:
        load_dotenv(dotenv_path)
    else:
        load_dotenv()

    search_paths = []
    if config_path:
        search_paths.append(Path(config_path))
    search_paths.append(Path.cwd() / "config.jsonc")
    search_paths.append(Path.home() / ".lc_agent" / "config.jsonc")

    for p in search_paths:
        if p.exists():
            config = load_config_from_file(str(p))
            config["_config_path"] = str(p)
            config["_project_root"] = str(p.parent)
            return config

    return {
        "provider": {},
        "agent": {
            "system_prompt": "You are a helpful assistant.",
            "default_model": "",
            "streaming": True,
        },
        "database": {
            "url": "sqlite+aiosqlite:///./lc_agent_data.db",
            "checkpoint_path": "./lc_agent_checkpoints.db",
        },
        "memory": {
            "enabled": True,
            "type": "sqlite",
            "path": "./lc_agent_memory.db",
            "save_policy": "explicit",
            "retrieval_policy": "manual",
            "semantic_search": {
                "enabled": True,
                "api_key": "{env:NBRAG_API_KEY}",
                "base_url": "https://api.siliconflow.cn/v1",
                "model": "BAAI/bge-m3",
                "dims": 1024,
            },
        },
        "skills": ["./skills"],
        "mcp_servers": {},
        "_config_path": None,
        "_project_root": str(Path.cwd()),
    }

`````

--- **end of file: lc_agent/config/loader.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/config/schema.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/config/schema.py`

#### 📦 Imports

- `from typing import Any`
- `from pydantic import BaseModel`
- `from pydantic import Field`
- `from pydantic import model_validator`

#### 🏛️ Classes (8)

##### 📌 `class ModelConfig(BaseModel)`
*Line: 6*

**Class Variables (3):**
- `id: str`
- `context_limit: int = 8000`
- `max_output_tokens: int = 65536`

##### 📌 `class ProviderConfig(BaseModel)`
*Line: 12*

**Class Variables (3):**
- `api_key: str = ''`
- `base_url: str = ''`
- `models: list[ModelConfig] = Field(default_factory=list)`

##### 📌 `class DatabaseConfig(BaseModel)`
*Line: 18*

**Class Variables (2):**
- `url: str = 'sqlite+aiosqlite:///./lc_agent_data.db'`
- `checkpoint_path: str = './lc_agent_checkpoints.db'`

##### 📌 `class MemorySemanticSearchConfig(BaseModel)`
*Line: 23*

**Class Variables (5):**
- `enabled: bool = True`
- `api_key: str = '{env:NBRAG_API_KEY}'`
- `base_url: str = 'https://api.siliconflow.cn/v1'`
- `model: str = 'BAAI/bge-m3'`
- `dims: int = 1024`

##### 📌 `class MemoryConfig(BaseModel)`
*Line: 31*

**Class Variables (6):**
- `enabled: bool = True`
- `type: str = 'sqlite'`
- `path: str = './lc_agent_memory.db'`
- `save_policy: str = 'explicit'`
- `retrieval_policy: str = 'manual'`
- `semantic_search: MemorySemanticSearchConfig = Field(default_factory=MemorySemanticSearchConfig)`

##### 📌 `class McpServerConfig(BaseModel)`
*Line: 40*

**Public Methods (1):**
- `def infer_http_type_from_url(cls, data: Any) -> Any` `model_validator(mode='before')` `classmethod`

**Class Variables (6):**
- `type: str = 'local'`
- `command: str | list[str] = ''`
- `args: list[str] = Field(default_factory=list)`
- `env: dict[str, str] = Field(default_factory=dict)`
- `url: str = ''`
- `enabled: bool = True`

##### 📌 `class AuthConfig(BaseModel)`
*Line: 56*

**Class Variables (2):**
- `secret: str = ''`
- `token_expire_days: int = 7`

##### 📌 `class AppConfig(BaseModel)`
*Line: 61*

**Docstring:**
`````
Application configuration schema.
`````

**Class Variables (10):**
- `provider: dict[str, ProviderConfig | dict] = Field(default_factory=dict)`
- `agent: dict = Field(default_factory=lambda : {'system_prompt': 'You are a helpful assistant.', 'default_model': '', 'streaming': True, 'recursion_limit': 100, 'max_subagent_depth': 2})`
- `mcp: dict = Field(default_factory=dict)`
- `database: DatabaseConfig = Field(default_factory=DatabaseConfig)`
- `memory: MemoryConfig = Field(default_factory=MemoryConfig)`
- `auth: AuthConfig = Field(default_factory=AuthConfig)`
- `session: dict = Field(default_factory=lambda : {'db_path': ''})`
- `ui: dict = Field(default_factory=dict)`
- `skills: list[str] = Field(default_factory=lambda : ['./skills'])`
- `mcp_servers: dict[str, McpServerConfig] = Field(default_factory=dict)`


---

`````python
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ModelConfig(BaseModel):
    id: str
    context_limit: int = 8000  # maps to LangChain profile["max_input_tokens"]
    max_output_tokens: int = 65536


class ProviderConfig(BaseModel):
    api_key: str = ""
    base_url: str = ""
    models: list[ModelConfig] = Field(default_factory=list)


class DatabaseConfig(BaseModel):
    url: str = "sqlite+aiosqlite:///./lc_agent_data.db"
    checkpoint_path: str = "./lc_agent_checkpoints.db"


class MemorySemanticSearchConfig(BaseModel):
    enabled: bool = True
    api_key: str = "{env:NBRAG_API_KEY}"
    base_url: str = "https://api.siliconflow.cn/v1"
    model: str = "BAAI/bge-m3"
    dims: int = 1024


class MemoryConfig(BaseModel):
    enabled: bool = True
    type: str = "sqlite"
    path: str = "./lc_agent_memory.db"
    save_policy: str = "explicit"
    retrieval_policy: str = "manual"
    semantic_search: MemorySemanticSearchConfig = Field(default_factory=MemorySemanticSearchConfig)


class McpServerConfig(BaseModel):
    type: str = "local"  # "local", "sse", "http"
    command: str | list[str] = ""
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    url: str = ""
    enabled: bool = True

    @model_validator(mode="before")
    @classmethod
    def infer_http_type_from_url(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("url") and not data.get("type"):
            return {**data, "type": "http"}
        return data


class AuthConfig(BaseModel):
    secret: str = ""
    token_expire_days: int = 7


class AppConfig(BaseModel):
    """Application configuration schema."""

    provider: dict[str, ProviderConfig | dict] = Field(default_factory=dict)
    agent: dict = Field(default_factory=lambda: {
        "system_prompt": "You are a helpful assistant.",
        "default_model": "",
        "streaming": True,
        "recursion_limit": 100,
        "max_subagent_depth": 2,
    })
    mcp: dict = Field(default_factory=dict)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    session: dict = Field(default_factory=lambda: {"db_path": ""})
    ui: dict = Field(default_factory=dict)
    skills: list[str] = Field(default_factory=lambda: ["./skills"])
    mcp_servers: dict[str, McpServerConfig] = Field(default_factory=dict)

`````

--- **end of file: lc_agent/config/schema.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/config/__init__.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/config/__init__.py`

#### 📦 Imports

- `from lc_agent.config.loader import load_config`
- `from lc_agent.config.loader import load_config_from_file`
- `from lc_agent.config.loader import substitute_env_vars`


---

`````python
from lc_agent.config.loader import load_config, load_config_from_file, substitute_env_vars

__all__ = ["load_config", "load_config_from_file", "substitute_env_vars"]

`````

--- **end of file: lc_agent/config/__init__.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/core/auth.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/core/auth.py`

#### 📦 Imports

- `import secrets`
- `from datetime import datetime`
- `from datetime import timedelta`
- `from datetime import timezone`
- `import bcrypt`
- `from jose import JWTError`
- `from jose import jwt`

#### 🏛️ Classes (1)

##### 📌 `class AuthService`
*Line: 8*

**🔧 Constructor (`__init__`):**
- `def __init__(self, secret: str, token_expire_days: int = 7)`
  - **Parameters:**
    - `self`
    - `secret: str`
    - `token_expire_days: int = 7`

**Public Methods (5):**
- `def hash_password(self, password: str) -> str`
- `def verify_password(self, plain: str, hashed: str) -> bool`
- `def create_token(self) -> str`
- `def decode_token(self, token: str) -> dict | None`
- `def generate_random_password(self, length: int = 16) -> str`


---

`````python
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt


class AuthService:
    def __init__(self, secret: str, token_expire_days: int = 7):
        if len(secret) < 16:
            raise ValueError("Auth secret must be at least 16 characters")
        self._secret = secret
        self._token_expire_days = token_expire_days

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

    def create_token(self, *, user_id: str, username: str, role: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=self._token_expire_days)
        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": expire,
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def decode_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(token, self._secret, algorithms=["HS256"])
            return payload
        except JWTError:
            return None

    def generate_random_password(self, length: int = 16) -> str:
        return secrets.token_urlsafe(length)[:length]

`````

--- **end of file: lc_agent/core/auth.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/core/chat_model.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/core/chat_model.py`

#### 📝 Module Docstring

`````
ChatOpenAI subclass that extracts reasoning_content from streaming deltas.

ChatOpenAI only supports official OpenAI API fields. Many providers (DeepSeek,
GLM, etc.) return a non-standard ``reasoning_content`` field in the streaming
delta for chain-of-thought / thinking content. This subclass captures it into
``additional_kwargs["reasoning_content"]`` so downstream handlers can display it.

For models that embed reasoning inside ``<think>...</think>`` tags within the
regular content stream (e.g. MiniMax-M3), those tags are detected, stripped,
and the enclosed text is likewise moved to ``reasoning_content``.
`````

#### 📦 Imports

- `import contextvars`
- `from typing import Any`
- `from typing import ClassVar`
- `from langchain_core.messages import AIMessageChunk`
- `from langchain_core.outputs import ChatGenerationChunk`
- `from langchain_openai import ChatOpenAI`

#### 🏛️ Classes (1)

##### 📌 `class ChatOpenAIReasoning(ChatOpenAI)`
*Line: 25*

**Docstring:**
`````
ChatOpenAI with reasoning_content extraction from streaming deltas.

Drop-in replacement for ChatOpenAI. Works with any provider that returns
``reasoning_content`` or ``reasoning`` in the streaming delta dict (e.g.
DeepSeek, GLM with thinking mode, OpenRouter).

Also detects ``<think>...</think>`` tags in the content stream and moves
the enclosed text to ``additional_kwargs["reasoning_content"]``.

Fixes the max_tokens / max_completion_tokens rename that ChatOpenAI applies
for the OpenAI API — non-OpenAI providers still expect ``max_tokens``.
`````

**Properties (1):**
- `@property _default_params -> dict[str, Any]`

**Class Variables (1):**
- `_think_mode: ClassVar[contextvars.ContextVar[bool]] = contextvars.ContextVar('ChatOpenAIReasoning__think_mode', default=False)`


---

`````python
"""ChatOpenAI subclass that extracts reasoning_content from streaming deltas.

ChatOpenAI only supports official OpenAI API fields. Many providers (DeepSeek,
GLM, etc.) return a non-standard ``reasoning_content`` field in the streaming
delta for chain-of-thought / thinking content. This subclass captures it into
``additional_kwargs["reasoning_content"]`` so downstream handlers can display it.

For models that embed reasoning inside ``<think>...</think>`` tags within the
regular content stream (e.g. MiniMax-M3), those tags are detected, stripped,
and the enclosed text is likewise moved to ``reasoning_content``.
"""


import contextvars
from typing import Any, ClassVar

from langchain_core.messages import AIMessageChunk
from langchain_core.outputs import ChatGenerationChunk
from langchain_openai import ChatOpenAI

_THINK_OPEN = "<think>"
_THINK_CLOSE = "</think>"


class ChatOpenAIReasoning(ChatOpenAI):
    """ChatOpenAI with reasoning_content extraction from streaming deltas.

    Drop-in replacement for ChatOpenAI. Works with any provider that returns
    ``reasoning_content`` or ``reasoning`` in the streaming delta dict (e.g.
    DeepSeek, GLM with thinking mode, OpenRouter).

    Also detects ``<think>...</think>`` tags in the content stream and moves
    the enclosed text to ``additional_kwargs["reasoning_content"]``.

    Fixes the max_tokens / max_completion_tokens rename that ChatOpenAI applies
    for the OpenAI API — non-OpenAI providers still expect ``max_tokens``.
    """

    _think_mode: ClassVar[contextvars.ContextVar[bool]] = contextvars.ContextVar(
        "ChatOpenAIReasoning__think_mode", default=False,
    )

    @property
    def _default_params(self) -> dict[str, Any]:
        params = super()._default_params
        if "max_completion_tokens" in params:
            params["max_tokens"] = params["max_completion_tokens"]
        return params

    def _get_request_payload(
        self,
        input_: Any,
        *,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> dict:
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        if "max_completion_tokens" in payload:
            payload["max_tokens"] = payload["max_completion_tokens"]
        return payload

    def _convert_chunk_to_generation_chunk(
        self,
        chunk: dict,
        default_chunk_class: type,
        base_generation_info: dict | None,
    ) -> ChatGenerationChunk | None:
        generation_chunk = super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info,
        )
        if generation_chunk is None:
            return None

        choices = chunk.get("choices") or chunk.get("chunk", {}).get("choices") or []
        if not choices:
            return generation_chunk

        delta = choices[0].get("delta") or {}
        if isinstance(generation_chunk.message, AIMessageChunk):
            reasoning = delta.get("reasoning_content")
            if reasoning is None:
                reasoning = delta.get("reasoning")
            if reasoning is not None:
                generation_chunk.message.additional_kwargs["reasoning_content"] = reasoning
            else:
                self._extract_think_tags(generation_chunk.message)

        return generation_chunk

    # ------------------------------------------------------------------
    # <think> tag extraction
    # ------------------------------------------------------------------

    def _extract_think_tags(self, message: AIMessageChunk) -> None:
        """Move ``<think>...</think>`` content to ``reasoning_content``."""
        content = message.content
        if not isinstance(content, str) or not content:
            return

        in_think = self._think_mode.get()

        if not in_think:
            idx = content.find(_THINK_OPEN)
            if idx == -1:
                return
            before = content[:idx]
            after = content[idx + len(_THINK_OPEN):]

            end_idx = after.find(_THINK_CLOSE)
            if end_idx != -1:
                reasoning_text = after[:end_idx]
                rest = after[end_idx + len(_THINK_CLOSE):]
                message.content = before + rest
                if reasoning_text:
                    message.additional_kwargs["reasoning_content"] = reasoning_text
            else:
                self._think_mode.set(True)
                message.content = before
                if after:
                    message.additional_kwargs["reasoning_content"] = after
        else:
            end_idx = content.find(_THINK_CLOSE)
            if end_idx != -1:
                reasoning_text = content[:end_idx]
                rest = content[end_idx + len(_THINK_CLOSE):]
                self._think_mode.set(False)
                message.content = rest
                if reasoning_text:
                    message.additional_kwargs["reasoning_content"] = reasoning_text
            else:
                message.additional_kwargs["reasoning_content"] = content
                message.content = ""

`````

--- **end of file: lc_agent/core/chat_model.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/core/engine.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/core/engine.py`


---

`````python
# lc_agent/core/engine.py
import logging
from dataclasses import dataclass
import re
from typing import Annotated, Any, AsyncIterator, Literal

from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain.agents.middleware.summarization import SummarizationMiddleware
from langchain.agents.middleware.todo import WRITE_TODOS_SYSTEM_PROMPT, WRITE_TODOS_TOOL_DESCRIPTION
try:
    from langchain.agents.middleware.types import AgentMiddleware as _AgentMiddlewareBase
    from langchain_core.messages import SystemMessage
    _HAS_MIDDLEWARE_BASE = True
except ImportError:
    _AgentMiddlewareBase = object  # type: ignore[misc,assignment]
    _HAS_MIDDLEWARE_BASE = False

from lc_agent.core.http_trace import (
    HttpTraceCollector,
    bind_http_trace_collector,
    get_http_trace_collector,
    register_subagent_collector,
    reset_http_trace_collector,
)
from lc_agent.core.http_trace_httpx import TracingAsyncClient
from lc_agent.core.models import AgentPreset, ModelInfo
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool as lc_tool
from pydantic import Field as _PydanticField

from lc_agent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

TODO_FINAL_ANSWER_GUARD = """## Final Answer Guard for `write_todos`

- Do not create todo items whose only purpose is to write, organize, summarize, or deliver the final answer.
- Before writing the substantive final answer to the user, make your last necessary `write_todos` call.
- After you start writing the substantive final answer, do not call `write_todos` again in the same turn.
- If the only remaining todo is about producing the final answer, do not call `write_todos` just to mark it complete. Deliver the final answer directly.
"""

TODO_SYSTEM_PROMPT = f"{WRITE_TODOS_SYSTEM_PROMPT}\n\n{TODO_FINAL_ANSWER_GUARD}"
TODO_TOOL_DESCRIPTION = f"{WRITE_TODOS_TOOL_DESCRIPTION}\n\n{TODO_FINAL_ANSWER_GUARD}"

_LOAD_SKILL_DESCRIPTION = (
    "Retrieve the full step-by-step instructions for a skill. "
    "This MUST be called before executing any task that matches a skill — "
    "the brief description in the system prompt is only a trigger hint, "
    "not the actual procedure. "
    "Returns the skill's markdown body, available resources, and scripts. "
    "Skill names are listed in the system prompt under '## Available Skills'."
)


class _SystemBlockMiddleware(_AgentMiddlewareBase):  # type: ignore[misc]
    """Injects a text block as a separate system message content block."""

    def __init__(self, text: str, middleware_name: str, *, prepend: bool = False) -> None:
        super().__init__()
        self._text = text
        self._middleware_name = middleware_name
        self._prepend = prepend

    @property
    def name(self) -> str:  # type: ignore[override]
        return self._middleware_name

    def _patched_system(self, existing: Any) -> Any:
        if self._prepend:
            new_block = {"type": "text", "text": self._text}
            new_content = [new_block, *(existing.content_blocks if existing is not None else [])]
        else:
            new_block = {"type": "text", "text": f"\n\n{self._text}"}
            new_content = [*(existing.content_blocks if existing is not None else []), new_block]
        return SystemMessage(content_blocks=new_content)  # type: ignore[call-arg]

    def wrap_model_call(self, request: Any, handler: Any) -> Any:
        return handler(request.override(system_message=self._patched_system(request.system_message)))

    async def awrap_model_call(self, request: Any, handler: Any) -> Any:
        return await handler(request.override(system_message=self._patched_system(request.system_message)))


# Keep old name as alias for backwards compatibility
_SkillsPromptMiddleware = _SystemBlockMiddleware

# --------------------------------------------------------------------------- #
# Subagent prompts
# --------------------------------------------------------------------------- #

SUBAGENT_DELEGATION_PROMPT = (
    "In order to complete the objective that the user asks of you, "
    "you have access to a number of standard tools.\n\n"
    "You receive a single task message and cannot ask for clarification or send follow-up messages. "
    "Complete the task entirely within this one invocation.\n\n"
    "Only your **last assistant message** is returned as the final output — "
    "every message you produce during tool use (including thoughts between tool calls) is discarded. "
    "After finishing all tool use, write a single complete answer in your final message. "
    "Do NOT say 'as shown above' or reference any intermediate tool output — "
    "your final message must be fully self-contained and contain the complete answer."
)

TASK_SYSTEM_PROMPT = """\
## task（子智能体调度器）

你拥有 `task` 工具，可以将独立任务委派给专用子智能体完成。\
这些子智能体是一次性的，仅在任务期间存在，完成后返回单一结果。

**每次子智能体调用都是无状态且单次往返（stateless, one-shot）**：子智能体看不到你的对话历史、记忆或上下文，\
你也无法向它追加消息。它只会收到你在 `description` 参数里写的内容，并在唯一一次回复中返回结果。\
因此，`description` 必须包含子智能体**独立完成任务**所需的全部背景和上下文，\
并明确说明它需要在唯一回复中返回什么内容（格式、语言、字数等）。

`description` 错误示例（子智能体无法访问你的对话历史）：
- ❌ "帮我查一下" （无背景、无上下文、无输出要求）
- ❌ "修复上面讨论的 bug" （子智能体没有"上面"的对话上下文）

**子智能体的返回结果对用户不可见**——它只返回给你。你有责任将结果整合后再呈现给用户，而不是直接转发原文。

子智能体的完整生命周期：
1. **派遣** → 在 `description` 里写明角色、任务、期望输出格式和语言
2. **执行** → 子智能体自主完成任务
3. **返回** → 子智能体以单条消息返回结果给你
4. **整合** → 你将结果融合到当前对话，呈现给用户

**重要：若有多个独立任务，必须在同一条消息中同时发起多个 `task` 调用并行执行，而不是逐一等待。**\
并行调用能显著减少用户等待时间，请务必利用：
- ❌ 错误：先调用 `task(A)`，等 A 返回后再调用 `task(B)`
- ✅ 正确：在同一条 assistant 消息里同时发出 `task(A)` 和 `task(B)` 两个工具调用
- ⚠️ 例外：若 B 依赖 A 的结果，则必须等 A 返回后才能发起 B

何时使用 `task`：
- 任务复杂、多步骤，且可以完整委派，不需要你参与中间过程
- 任务相互独立，可以并行启动以节省时间（例如：同时研究 A 话题和 B 话题）
- 任务需要大量工具调用或 token，委派可以避免你的上下文窗口被污染
- 你只关心子智能体的最终输出，不需要中间步骤

何时**不**使用 `task`：
- 任务简单（几次工具调用或快速查询即可）
- 你需要看到中间推理过程（task 工具会隐藏中间步骤）
- 委派的子任务过于简短，拆分只会增加延迟而没有收益
- 任务依赖你的当前上下文，无法独立表达为完整的委派描述"""


@dataclass(frozen=True)
class SubAgentDescriptor:
    subagent_type: str
    preset_id: str
    display_name: str
    description: str


_GENERAL_PURPOSE_DESCRIPTION = (
    "当你需要一个与当前智能体能力相近、但在隔离上下文中并行处理复杂任务的工作线程时调用它。"
)


def _extract_subagent_result(messages: list[Any]) -> str:
    """Extract the last non-empty AI message text from a subagent's message list.

    Iterates in reverse to skip any trailing empty messages that some providers
    (e.g. Anthropic Claude) may append after the final tool call.
    Returns the first non-empty AI text found — the subagent's conclusive answer.
    """
    for msg in reversed(messages):
        if getattr(msg, "type", None) != "ai":
            continue
        content = getattr(msg, "content", "")
        if isinstance(content, str):
            text = content.strip()
        elif isinstance(content, list):
            text = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            ).strip()
        else:
            text = str(content).strip()
        if text:
            return text
    return ""

try:
    from langchain_core.tools import InjectedToolCallId
    _HAS_INJECTED_TOOL_CALL_ID = True
except ImportError:
    InjectedToolCallId = None  # type: ignore[assignment,misc]
    _HAS_INJECTED_TOOL_CALL_ID = False


class AgentEngine:
    """Core agent engine wrapping langchain.agents.create_agent with middleware support."""

    def __init__(self, config: dict, checkpointer=None, store=None):
        self.config = config
        self.tool_registry = ToolRegistry()
        self._checkpointer = checkpointer
        self._store = store
        self._agents: dict[str, Any] = {}
        self._agent_subagent_tools: dict[str, set[str]] = {}
        self._agent_subagent_display_map: dict[str, dict[str, str]] = {}
        self._current_preset: AgentPreset | None = None
        self._models: list[ModelInfo] = self._parse_models(config)
        self._presets: dict[str, AgentPreset] = {}
        self._custom_presets: dict[str, AgentPreset] = {}
        self._agent_mcp_gen: dict[str, int] = {}
        self._mcp_generation: int = 0
        self.recursion_limit: int = config.get("agent", {}).get("recursion_limit", 100)

    def _memory_enabled(self) -> bool:
        memory_conf = self.config.get("memory", {})
        if isinstance(memory_conf, dict):
            return memory_conf.get("enabled", True)
        return getattr(memory_conf, "enabled", True)

    def _is_code_agent(self, preset_id: str) -> bool:
        preset = self._resolve_preset(preset_id)
        return preset.source == "code" or preset_id in self._custom_presets

    def _should_use_memory_context(self, preset_id: str) -> bool:
        return self._store is not None and self._memory_enabled() and not self._is_code_agent(preset_id)

    def _parse_models(self, config: dict) -> list[ModelInfo]:
        """Extract ModelInfo list from config."""
        models = []
        for provider_name, provider_conf in config.get("provider", {}).items():
            if isinstance(provider_conf, dict):
                for model_conf in provider_conf.get("models", []):
                    models.append(ModelInfo(
                        id=model_conf["id"],
                        provider=provider_name,
                        base_url=provider_conf.get("base_url", ""),
                        context_limit=model_conf.get("context_limit", 8000),
                        max_output_tokens=model_conf.get("max_output_tokens", 0),
                        api_key=provider_conf.get("api_key", ""),
                    ))
        return models

    def get_models(self) -> list[ModelInfo]:
        """Return available models."""
        return self._models

    BUILTIN_IDS = {"chat", "empty", "power"}

    def get_builtin_presets(self) -> list[AgentPreset]:
        """Return the three built-in agent presets."""
        agent_conf = self.config.get("agent", {})
        default_model = agent_conf.get("default_model", "")
        return [
            AgentPreset(
                id="chat",
                name="chat",
                display_name="Chat",
                system_prompt="You are a helpful assistant. Respond in the user's language.",
                default_model=default_model,
                allowed_tool_groups=[],
                allowed_mcp_servers=[],
                allowed_skills=[],
                source="builtin",
                default_enabled=False,
            ),
            AgentPreset(
                id="empty",
                name="empty",
                display_name="Empty",
                system_prompt=agent_conf.get("system_prompt", "You are a helpful assistant."),
                default_model=default_model,
                allowed_tool_groups=None,
                allowed_mcp_servers=None,
                allowed_skills=[],
                source="builtin",
                default_enabled=False,
            ),
            AgentPreset(
                id="power",
                name="power",
                display_name="Power",
                system_prompt=agent_conf.get("system_prompt", "You are a helpful assistant."),
                default_model=default_model,
                allowed_tool_groups=None,
                allowed_mcp_servers=None,
                allowed_skills=None,
                source="builtin",
                default_enabled=True,
            ),
        ]

    def get_default_preset(self) -> AgentPreset:
        """Return the default agent (Chat - safest)."""
        return self.get_builtin_presets()[0]

    def _preset_exists(self, preset_id: str) -> bool:
        """Return True if preset_id refers to a known preset."""
        return (
            preset_id in self.BUILTIN_IDS
            or preset_id in self._custom_presets
            or preset_id in self._presets
        )

    def _build_subagent_registry(
        self,
        preset: AgentPreset,
        depth: int,
        building_set: frozenset[str],
    ) -> dict[str, SubAgentDescriptor]:
        max_depth = self.config.get("agent", {}).get("max_subagent_depth", 2)
        if depth >= max_depth:
            return {}

        registry: dict[str, SubAgentDescriptor] = {}
        subagent_candidates: list[tuple[str, str]] = []
        if getattr(preset, "subagents", None):
            for subagent_link in preset.subagents:
                subagent_candidates.append((
                    subagent_link.agent_id,
                    (subagent_link.delegation_description or "").strip(),
                ))

        for subagent_id, relationship_description in subagent_candidates:
            if subagent_id in building_set:
                logger.warning("Subagent circular reference detected: %s — skipping", subagent_id)
                continue
            if not self._preset_exists(subagent_id):
                logger.warning("Subagent preset not found: %s — skipping", subagent_id)
                continue
            subagent_preset = self._resolve_preset(subagent_id)
            display_name = subagent_preset.display_name or subagent_preset.name
            subagent_type = subagent_preset.name
            suffix = 1
            while subagent_type in registry:
                suffix += 1
                subagent_type = f"{subagent_preset.name}-{suffix}"
            registry[subagent_type] = SubAgentDescriptor(
                subagent_type=subagent_type,
                preset_id=subagent_id,
                display_name=display_name,
                description=(
                    relationship_description
                    or (getattr(subagent_preset, "default_delegation_description", "") or "").strip()
                    or display_name
                ),
            )

        if getattr(preset, "enable_general_purpose_subagent", False):
            gp_id = f"__gp__:{preset.id}"
            gp_preset = preset.model_copy(update={
                "id": gp_id,
                "subagents": None,
                "enable_general_purpose_subagent": False,
            })
            self._presets[gp_id] = gp_preset
            registry["general-purpose"] = SubAgentDescriptor(
                subagent_type="general-purpose",
                preset_id=gp_id,
                display_name="通用助手",
                description=_GENERAL_PURPOSE_DESCRIPTION,
            )

        return registry

    def _make_task_tool(
        self,
        registry: dict[str, SubAgentDescriptor],
        depth: int,
        building_set: frozenset[str],
    ):
        async def _run_subagent(subagent_type: str, description: str, config: RunnableConfig, tool_call_id: str) -> str:
            descriptor = registry.get(subagent_type)
            if descriptor is None:
                available = ", ".join(sorted(registry))
                return f"[Sub-agent error: Unknown subagent_type '{subagent_type}'. Available: {available}]"

            try:
                sub_agent = self._get_or_build_agent(descriptor.preset_id, _depth=depth)
            except Exception as exc:
                logger.exception("Subagent %s failed to build: %s", descriptor.preset_id, exc)
                return f"[Sub-agent error: {exc}]"

            configurable = (config or {}).get("configurable", {})
            parent_tid = configurable.get("thread_id") or ""
            lg_ns = configurable.get("checkpoint_ns", "")
            tc_id = next(
                (seg.split(":", 1)[1] for seg in lg_ns.split("|") if seg.startswith("tools:")),
                tool_call_id,
            )
            sub_thread_id = f"{parent_tid}--sa--{tc_id}"
            sub_config = {
                **(config or {}),
                "configurable": {
                    **((config or {}).get("configurable") or {}),
                    "thread_id": sub_thread_id,
                    "sub_session_id": sub_thread_id,
                },
            }

            _sa_collector = HttpTraceCollector(provider=None, model=None)
            _trace_token = bind_http_trace_collector(_sa_collector)
            try:
                result = await sub_agent.ainvoke(
                    {"messages": [{"role": "user", "content": description}]},
                    config=sub_config,
                )
                msgs = result.get("messages", [])
                return _extract_subagent_result(msgs)
            except Exception as exc:
                logger.exception("Subagent %s failed: %s", descriptor.preset_id, exc)
                return f"[Sub-agent error: {exc}]"
            finally:
                reset_http_trace_collector(_trace_token)
                register_subagent_collector(sub_thread_id, _sa_collector)

        description_lines = [
            "Delegate a task to one configured sub-agent.",
            "",
            "Each call is **stateless and one-shot**: the sub-agent only sees what you put in",
            "the `description` argument. Therefore `description` must be fully self-contained:",
            "include ALL background, specify exactly what to return in the **final and only reply**",
            "(sections, format, language, length).",
            "",
            "**Good description example**:",
            "  \"The user is building a Python project using LangChain. Please research LangChain",
            "  v0.3's checkpointing mechanism, focusing on: (1) InMemorySaver vs SqliteSaver",
            "  differences, (2) per-user memory configuration. Return a detailed Chinese analysis",
            "  with code examples, in sections: Overview / Comparison / Recommendation.\"",
            "**Bad description examples**:",
            "  ❌ \"Research LangChain memory.\" (no context, no output format)",
            "  ❌ \"Fix the checkpoint bug we discussed above.\" (sub-agent has no 'above' context)",
            "",
            "Use the exact `subagent_type` value from the list below.",
            "Do not rename it, paraphrase it, translate it, or invent a new value.",
            "",
            "Available subagents:",
            "",
        ]
        for descriptor in registry.values():
            description_lines.extend([
                "====================",
                "",
                f"subagent_type: {descriptor.subagent_type}",
                "",
                "when_to_use:",
                descriptor.description,
                "",
            ])
        if description_lines and description_lines[-1] == "":
            description_lines.pop()
        task_description = "\n".join(description_lines)

        available_types = sorted(descriptor.subagent_type for descriptor in registry.values())
        subagent_type_field_desc = (
            f"The type of subagent to use. Must be exactly one of: "
            f"{', '.join(repr(t) for t in available_types)}. "
            "Do not translate or modify it."
        )
        description_field_desc = (
            "A detailed description of the task for the subagent to perform autonomously. "
            "Must include ALL necessary background and context — the subagent cannot access your "
            "conversation history and you cannot send follow-up messages. "
            "Specify exactly what the subagent must return in its final and only reply "
            "(sections, format, language, length)."
        )

        if _HAS_INJECTED_TOOL_CALL_ID:
            @lc_tool("task", description=task_description)
            async def task(
                subagent_type: Annotated[Literal[*available_types], _PydanticField(  # type: ignore[valid-type]
                    description=subagent_type_field_desc,
                )],
                description: Annotated[str, _PydanticField(description=description_field_desc)],
                tool_call_id: Annotated[str, InjectedToolCallId],
                config: RunnableConfig,
            ) -> str:
                return await _run_subagent(subagent_type, description, config, tool_call_id)
        else:
            @lc_tool("task", description=task_description)
            async def task(
                subagent_type: Annotated[Literal[*available_types], _PydanticField(  # type: ignore[valid-type]
                    description=subagent_type_field_desc,
                )],
                description: Annotated[str, _PydanticField(description=description_field_desc)],
                config: RunnableConfig,
            ) -> str:
                import uuid

                tool_call_id = ((config or {}).get("configurable") or {}).get("tool_call_id") or uuid.uuid4().hex
                return await _run_subagent(subagent_type, description, config, tool_call_id)

        return task
    def build_agent(
        self,
        preset: AgentPreset | None = None,
        cache_key: str | None = None,
        llm_params: dict | None = None,
        building_set: frozenset[str] | None = None,
        _depth: int = 0,
    ):
        """Build a LangGraph ReAct agent from preset."""
        if preset is None:
            preset = self.get_default_preset()
        self._current_preset = preset

        system_prompt = preset.system_prompt
        # Subagents need an explicit reminder that only the final message is returned to the caller
        if _depth > 0 and not _HAS_MIDDLEWARE_BASE:
            system_prompt = f"{system_prompt}\n\n{SUBAGENT_DELEGATION_PROMPT}"
        tools = self.tool_registry.get_filtered_tools(preset.allowed_tool_groups)

        _memory_middleware: _SystemBlockMiddleware | None = None
        _skills_middleware: _SystemBlockMiddleware | None = None
        if hasattr(self, '_skills_toolkit') and self._skills_toolkit:
            allowed = preset.allowed_skills
            if allowed is None or allowed:
                skill_tools = []
                for _t in self._skills_toolkit.get_tools():
                    if _t.name == "list_skills":
                        continue
                    if _t.name == "load_skill":
                        try:
                            _t = _t.model_copy(update={"description": _LOAD_SKILL_DESCRIPTION})
                        except Exception:
                            pass
                    skill_tools.append(_t)
                tools = tools + skill_tools
                loader = self._skills_toolkit._resolved_loader
                if loader:
                    all_skills = loader.list_skills()
                    if allowed is not None:
                        all_skills = [s for s in all_skills if s.name in allowed]
                    if all_skills and _HAS_MIDDLEWARE_BASE:
                        import json as _json
                        skill_entries = [
                            {
                                "skill_name": s.name,
                                "description": s.description.splitlines()[0],
                            }
                            for s in all_skills
                        ]
                        lines = [
                            "## Available Skills",
                            "",
                            "The descriptions below are **triggers** — they tell you WHEN a skill applies.",
                            "The actual step-by-step instructions, required tools, and constraints are INSIDE the skill.",
                            "",
                            "**MANDATORY RULE**: When the user's request matches a skill's description,",
                            "you MUST call `load_skill(skill_name=\"<skill_name>\")` FIRST to retrieve",
                            "the full instructions, then follow them exactly.",
                            "Do NOT skip this step and proceed with your default approach.",
                            "",
                            "```json",
                            _json.dumps(skill_entries, ensure_ascii=False, indent=2),
                            "```",
                            "",
                            "After loading a skill, you may also call `read_skill_resource` to fetch",
                            "its reference files or `run_skill_script` to execute its scripts.",
                        ]
                        _skills_middleware = _SystemBlockMiddleware("\n".join(lines), "SkillsPromptMiddleware")

        if hasattr(self, '_mcp_manager') and self._mcp_manager:
            mcp_tools = self._mcp_manager.get_filtered_langchain_tools(preset.allowed_mcp_servers)
            tools = tools + mcp_tools

        kwargs: dict[str, Any] = {}
        if self._checkpointer:
            kwargs["checkpointer"] = self._checkpointer

        if self._store is not None and self._memory_enabled():
            from lc_agent.core.memory import (
                AgentRuntimeContext,
                MEMORY_SYSTEM_PROMPT,
                build_memory_tools,
            )

            tools = tools + build_memory_tools()
            if _HAS_MIDDLEWARE_BASE:
                _memory_middleware = _SystemBlockMiddleware(MEMORY_SYSTEM_PROMPT, "MemoryPromptMiddleware")
            else:
                system_prompt = f"{system_prompt}\n\n{MEMORY_SYSTEM_PROMPT}"
            kwargs["store"] = self._store
            kwargs["context_schema"] = AgentRuntimeContext

        new_building = (building_set or frozenset()) | {preset.id}
        subagent_registry = self._build_subagent_registry(preset, depth=_depth, building_set=new_building)
        subagent_tool_names: set[str] = set()
        subagent_display_map: dict[str, str] = {}
        if subagent_registry:
            tools.append(self._make_task_tool(subagent_registry, _depth + 1, new_building))
            subagent_tool_names = {"task"}
            subagent_display_map = {
                descriptor.subagent_type: descriptor.display_name
                for descriptor in subagent_registry.values()
            }

        model_info = self._find_model(preset.default_model)
        effective_params = {**(preset.llm_params or {}), **(llm_params or {})}
        llm = self._create_llm(model_info, preset.default_model, llm_params=effective_params or None)

        middleware = []
        if _depth > 0 and _HAS_MIDDLEWARE_BASE:
            middleware.append(_SystemBlockMiddleware(
                SUBAGENT_DELEGATION_PROMPT, "SubagentDelegationMiddleware", prepend=True
            ))
        if _memory_middleware is not None:
            middleware.append(_memory_middleware)
        if _skills_middleware is not None:
            middleware.append(_skills_middleware)
        if _depth == 0 and subagent_registry:
            if _HAS_MIDDLEWARE_BASE:
                middleware.append(_SystemBlockMiddleware(TASK_SYSTEM_PROMPT, "TaskSystemPromptMiddleware"))
            else:
                system_prompt = f"{system_prompt}\n\n{TASK_SYSTEM_PROMPT}"
        if _depth == 0:
            middleware.append(TodoListMiddleware(
                system_prompt=TODO_SYSTEM_PROMPT,
                tool_description=TODO_TOOL_DESCRIPTION,
            ))
        middleware.extend(self._build_summarization_middleware(preset))

        # Only top-level agents need human-in-the-loop approval; sub-agents run autonomously
        if hasattr(self, '_permissions_service') and self._permissions_service and _depth == 0:
            from langchain.agents.middleware import HumanInTheLoopMiddleware
            interrupt_on = {
                tool.name: {
                    "allowed_decisions": ["approve", "reject"],
                    "when": self._permissions_service.should_interrupt,
                }
                for tool in tools
                if tool.name != "ask_user"
            }
            if interrupt_on:
                middleware.append(HumanInTheLoopMiddleware(interrupt_on=interrupt_on))

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
            middleware=middleware,
            **kwargs,
        )

        resolved_cache_key = cache_key or preset.id
        self._agents[resolved_cache_key] = agent
        self._agent_subagent_tools[resolved_cache_key] = subagent_tool_names
        self._agent_subagent_display_map[resolved_cache_key] = subagent_display_map
        return agent

    def _build_tracing_async_client(self, model_info: ModelInfo | None, model_id: str):
        provider = model_info.provider if model_info else None
        resolved_model = model_info.id if model_info else model_id
        base_url = model_info.base_url if model_info and model_info.base_url else None
        return TracingAsyncClient(
            collector_getter=get_http_trace_collector,
            provider=provider,
            model=resolved_model,
            base_url=base_url or "https://api.openai.com/v1",
            timeout=120,
        )

    def _create_llm(
        self,
        model_info: ModelInfo | None,
        model_id: str,
        llm_params: dict | None = None,
    ):
        """Create a chat model instance.

        Uses ChatOpenAIReasoning when base_url is set — extracts reasoning_content
        from any provider that returns it (DeepSeek, GLM, etc).
        Uses init_chat_model for standard providers (handles provider routing).
        """
        params = llm_params or {}
        temperature = params.get("temperature", 0.7)
        reasoning_effort = params.get("reasoning_effort")
        # passthrough: top_p, top_k, presence_penalty, frequency_penalty, max_tokens, etc.
        HANDLED_KEYS = {"temperature", "reasoning_effort"}
        extra_params = {k: v for k, v in params.items() if k not in HANDLED_KEYS and v is not None}

        if model_info and model_info.base_url:
            from lc_agent.core.chat_model import ChatOpenAIReasoning
            kwargs: dict[str, Any] = dict(
                model=model_info.id,
                base_url=model_info.base_url,
                api_key=model_info.api_key or "not-set",
                temperature=temperature,
                stream_usage=True,
                http_async_client=self._build_tracing_async_client(model_info, model_id),
                **extra_params,
            )
            if model_info.max_output_tokens > 0:
                kwargs["max_tokens"] = model_info.max_output_tokens
            if reasoning_effort:
                kwargs["reasoning_effort"] = reasoning_effort
            return ChatOpenAIReasoning(**kwargs)

        from langchain.chat_models import init_chat_model

        if model_info:
            model_str = f"{model_info.provider}:{model_info.id}" if model_info.provider else model_info.id
            kwargs: dict[str, Any] = dict(
                api_key=model_info.api_key or "not-set",
                temperature=temperature,
                stream_usage=True,
                **extra_params,
            )
            if reasoning_effort:
                kwargs["reasoning_effort"] = reasoning_effort
            return init_chat_model(model_str, **kwargs)

        kwargs: dict[str, Any] = dict(api_key="not-set", temperature=temperature, stream_usage=True, **extra_params)
        if reasoning_effort:
            kwargs["reasoning_effort"] = reasoning_effort
        return init_chat_model(model_id, **kwargs)

    def _find_model(self, model_id: str) -> ModelInfo | None:
        """Find model info by ID."""
        for m in self._models:
            if m.id == model_id:
                return m
        return None

    def _build_summarization_middleware(self, preset: AgentPreset) -> list:
        """Build SummarizationMiddleware based on config, returns empty list if disabled."""
        summ_conf = self.config.get("agent", {}).get("summarization", {})
        if not summ_conf.get("enabled", True):
            return []

        summ_model_id = summ_conf.get("default_model", "") or preset.default_model
        model_info = self._find_model(summ_model_id)
        llm = self._create_llm(model_info, summ_model_id)

        trigger = self._parse_context_size(summ_conf.get("trigger")) or ("fraction", 0.85)
        keep = self._parse_context_size(summ_conf.get("keep")) or ("fraction", 0.20)

        needs_profile = trigger[0] == "fraction" or keep[0] == "fraction"
        if needs_profile and model_info:
            llm.profile = {"max_input_tokens": model_info.context_limit}

        kwargs: dict[str, Any] = {"model": llm, "keep": keep, "trigger": trigger}

        try:
            mw = SummarizationMiddleware(**kwargs)
            logger.info("SummarizationMiddleware enabled: trigger=%s, keep=%s", trigger, keep)
            return [mw]
        except Exception:
            logger.exception("Failed to create SummarizationMiddleware")
            return []

    @staticmethod
    def _parse_context_size(value) -> tuple | None:
        """Parse a context size value from config (e.g. ["fraction", 0.85]) into a tuple."""
        if value is None:
            return None
        if isinstance(value, (list, tuple)) and len(value) == 2:
            kind, amount = value
            if kind in ("fraction", "tokens", "messages"):
                return (kind, amount)
        return None

    def _resolve_preset(self, preset_id: str) -> AgentPreset:
        """Resolve a preset ID to an AgentPreset object."""
        if preset_id in self.BUILTIN_IDS:
            for bp in self.get_builtin_presets():
                if bp.id == preset_id:
                    return bp
        if preset_id in self._custom_presets:
            return self._custom_presets[preset_id]
        if preset_id in self._presets:
            return self._presets[preset_id]
        return self.get_default_preset()

    def _get_agent_cache_key(
        self,
        preset_id: str,
        model_id: str = "",
        llm_params: dict | None = None,
        _depth: int = 0,
    ) -> str:
        key = f"{preset_id}::model::{model_id}" if model_id else preset_id
        if llm_params:
            import json
            key = f"{key}::llm::{json.dumps(llm_params, sort_keys=True)}"
        if _depth:
            key = f"{key}::depth::{_depth}"
        return key

    def get_subagent_tool_names(
        self,
        preset_id: str,
        model_id: str = "",
        llm_params: dict | None = None,
        _depth: int = 0,
    ) -> set[str]:
        """Return the set of tool names (not IDs) that are sub-agents for the given preset."""
        cache_key = self._get_agent_cache_key(
            preset_id,
            model_id if self._find_model(model_id) else "",
            llm_params=llm_params,
            _depth=_depth,
        )
        return self._agent_subagent_tools.get(cache_key, set())

    def get_subagent_display_name_map(
        self,
        preset_id: str,
        model_id: str = "",
        llm_params: dict | None = None,
        _depth: int = 0,
    ) -> dict[str, str]:
        """Return {tool_name: display_name} for sub-agents of the given preset."""
        cache_key = self._get_agent_cache_key(
            preset_id,
            model_id if self._find_model(model_id) else "",
            llm_params=llm_params,
            _depth=_depth,
        )
        return self._agent_subagent_display_map.get(cache_key, {})

    def invalidate_agent_cache(self, preset_id: str, keep_exact: bool = False) -> None:
        """Remove cached agents for a preset, including model/llm_params override variants."""
        prefix = f"{preset_id}::"
        keys = [
            key
            for key in self._agents
            if key.startswith(prefix) or (key == preset_id and not keep_exact)
        ]
        for key in keys:
            self._agents.pop(key, None)
            self._agent_mcp_gen.pop(key, None)
            self._agent_subagent_tools.pop(key, None)
            self._agent_subagent_display_map.pop(key, None)

    def invalidate_all_agents(self) -> None:
        """Remove all cached agents, forcing rebuild on next use."""
        self._agents.clear()
        self._agent_mcp_gen.clear()
        self._agent_subagent_tools.clear()
        self._agent_subagent_display_map.clear()

    def _resolve_preset_for_model(self, preset_id: str, model_id: str = "") -> AgentPreset:
        preset = self._resolve_preset(preset_id)
        if model_id and self._find_model(model_id):
            return preset.model_copy(update={"default_model": model_id})
        return preset

    def _get_or_build_agent(
        self,
        preset_id: str,
        model_id: str = "",
        llm_params: dict | None = None,
        _depth: int = 0,
    ):
        """Get cached agent or build a new one. Rebuilds preset agents if MCP state changed."""
        preset = self._resolve_preset(preset_id)
        if preset.source == "code" or preset_id in self._custom_presets:
            agent = self._agents.get(preset_id)
            if agent is None:
                raise ValueError(f"Code agent '{preset_id}' is registered without a graph")
            return agent

        if model_id and self._find_model(model_id):
            preset = preset.model_copy(update={"default_model": model_id})
        cache_key = self._get_agent_cache_key(
            preset_id,
            model_id if preset.default_model == model_id else "",
            llm_params=llm_params,
            _depth=_depth,
        )
        mcp_gen = getattr(self, '_mcp_generation', 0)
        cached = self._agents.get(cache_key)
        cached_gen = self._agent_mcp_gen.get(cache_key, -1)
        if cached is None or cached_gen != mcp_gen:
            agent = self.build_agent(preset, cache_key=cache_key, llm_params=llm_params, _depth=_depth)
            self._agent_mcp_gen[cache_key] = mcp_gen
            return agent
        return cached

    async def chat(
        self,
        message: str,
        thread_id: str,
        preset_id: str = "chat",
        model_id: str = "",
        user_id: str = "anonymous",
    ) -> str:
        """Send a message and get a response (non-streaming)."""
        agent = self._get_or_build_agent(preset_id, model_id)

        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": self.recursion_limit}
        invoke_kwargs: dict[str, Any] = {"config": config}
        if self._should_use_memory_context(preset_id):
            from lc_agent.core.memory import AgentRuntimeContext, normalize_memory_user_id

            invoke_kwargs["context"] = AgentRuntimeContext(user_id=normalize_memory_user_id(user_id))
        result = await agent.ainvoke({"messages": [{"role": "user", "content": message}]}, **invoke_kwargs)
        messages = result.get("messages", [])
        if messages:
            return messages[-1].content
        return ""

    async def chat_stream(
        self,
        message: list[dict[str, Any]],
        thread_id: str,
        preset_id: str = "chat",
        model_id: str = "",
        history: list[dict[str, str]] | None = None,
        llm_params: dict | None = None,
        user_id: str = "anonymous",
    ) -> AsyncIterator[dict]:
        """Stream chat responses as events.

        message: LangChain content blocks list, e.g. [{"type":"text","text":"..."}, {"type":"image_url","image_url":{"url":"data:..."}}]
        """
        agent = self._get_or_build_agent(preset_id, model_id, llm_params=llm_params)

        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": self.recursion_limit}
        input_messages = list(history or [])
        input_messages.append({"role": "user", "content": message})
        stream_kwargs: dict[str, Any] = {"config": config, "version": "v2"}
        if self._should_use_memory_context(preset_id):
            from lc_agent.core.memory import AgentRuntimeContext, normalize_memory_user_id

            stream_kwargs["context"] = AgentRuntimeContext(user_id=normalize_memory_user_id(user_id))
        async for event in agent.astream_events(
            {"messages": input_messages},
            **stream_kwargs,
        ):
            yield event

    async def reset_thread(self, thread_id: str) -> None:
        """Delete all checkpoints for a thread if the checkpointer supports it."""
        if not self._checkpointer:
            return

        deleter = getattr(self._checkpointer, "adelete_thread", None)
        if callable(deleter):
            await deleter(thread_id)
            return

        sync_deleter = getattr(self._checkpointer, "delete_thread", None)
        if callable(sync_deleter):
            sync_deleter(thread_id)

    async def generate_title(self, user_message: str, model_id: str = "") -> str:
        """Generate a short conversation title from the user's first message."""
        model_info = self._find_model(model_id) if model_id else None
        if model_info is None and self._models:
            model_info = self._models[0]
        if model_info is None:
            return user_message[:20]

        llm = self._create_llm(model_info, model_info.id)
        try:
            resp = await llm.ainvoke([
                {"role": "system", "content": "用10个字以内为这段对话生成一个简洁标题。只输出标题，不要标点符号和引号。"},
                {"role": "user", "content": user_message[:200]},
            ])
            title = resp.content.strip().strip('"\'""').strip()
            return title[:30] if title else user_message[:20]
        except Exception:
            return user_message[:20]

    def get_presets(self) -> list[AgentPreset]:
        """Return all agent presets (including default and custom)."""
        default = self.get_default_preset()
        return [default] + list(self._presets.values()) + list(self._custom_presets.values())

    def add_preset(self, preset: AgentPreset) -> AgentPreset:
        """Add a new agent preset."""
        self._presets[preset.id] = preset
        return preset

    def update_preset(self, preset_id: str, data: dict) -> AgentPreset | None:
        """Update an existing preset."""
        if preset_id not in self._presets:
            return None
        existing = self._presets[preset_id]
        updated = existing.model_copy(update=data)
        self._presets[preset_id] = updated
        return updated

    def delete_preset(self, preset_id: str) -> bool:
        """Delete a preset. Cannot delete builtin."""
        if preset_id in self.BUILTIN_IDS:
            return False
        return self._presets.pop(preset_id, None) is not None

`````

--- **end of file: lc_agent/core/engine.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/core/http_trace.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/core/http_trace.py`

#### 📦 Imports

- `import json`
- `import time`
- `from contextvars import ContextVar`
- `from contextvars import Token`
- `from dataclasses import dataclass`
- `from dataclasses import field`
- `from typing import Any`
- `from typing import TypedDict`

#### 🏛️ Classes (5)

##### 📌 `class HttpMessagePart(TypedDict)`
*Line: 10*

**Class Variables (5):**
- `method: str | None`
- `url: str | None`
- `headers: dict[str, str]`
- `body: str`
- `bodyFormat: str`

##### 📌 `class HttpResponsePart(TypedDict)`
*Line: 18*

**Class Variables (5):**
- `status: int | None`
- `headers: dict[str, str]`
- `body: str`
- `bodyFormat: str`
- `ok: bool | None`

##### 📌 `class HttpTrace(TypedDict)`
*Line: 26*

**Class Variables (10):**
- `id: str`
- `sequence: int`
- `kind: str`
- `provider: str | None`
- `model: str | None`
- `startedAt: int`
- `durationMs: int | None`
- `request: HttpMessagePart`
- `response: HttpResponsePart`
- `error: str | None`

##### 📌 `class _PendingTrace`
*Line: 114*

**Class Variables (17):**
- `id: str`
- `sequence: int`
- `provider: str | None`
- `model: str | None`
- `started_at: int`
- `request_method: str | None`
- `request_url: str | None`
- `request_headers: dict[str, str]`
- `request_body: str`
- `request_body_format: str`
- `response_status: int | None = None`
- `response_headers: dict[str, str] = field(default_factory=dict)`
- `response_body: str = '未返回'`
- `response_body_format: str = 'unknown'`
- `response_ok: bool | None = None`
- `duration_ms: int | None = None`
- `error: str | None = None`

##### 📌 `class HttpTraceCollector`
*Line: 134*

**🔧 Constructor (`__init__`):**
- `def __init__(self)`
  - **Parameters:**
    - `self`

**Public Methods (4):**
- `def start_request(self) -> str`
- `def finish_response(self, trace_id: str) -> None`
- `def fail_response(self, trace_id: str, error: str) -> None`
- `def snapshot(self) -> list[HttpTrace]`

#### 🔧 Public Functions (6)

- `def bind_http_trace_collector(collector: HttpTraceCollector) -> Token`
  - *Line: 219*

- `def reset_http_trace_collector(token: Token) -> None`
  - *Line: 223*

- `def get_http_trace_collector() -> HttpTraceCollector | None`
  - *Line: 227*

- `def init_subagent_collector_registry() -> None`
  - *Line: 236*
  - *No-op with the global-dict approach; kept for API compatibility.*

- `def register_subagent_collector(sub_thread_id: str, collector: 'HttpTraceCollector') -> None`
  - *Line: 240*
  - *Store completed sub-agent traces so SSE can retrieve them after ainvoke.*

- `def pop_subagent_traces(sub_thread_id: str) -> list`
  - *Line: 247*
  - *Return and remove the collected HTTP traces for a sub-agent session.*


---

`````python


import json
import time
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any, TypedDict


class HttpMessagePart(TypedDict):
    method: str | None
    url: str | None
    headers: dict[str, str]
    body: str
    bodyFormat: str


class HttpResponsePart(TypedDict):
    status: int | None
    headers: dict[str, str]
    body: str
    bodyFormat: str
    ok: bool | None


class HttpTrace(TypedDict):
    id: str
    sequence: int
    kind: str
    provider: str | None
    model: str | None
    startedAt: int
    durationMs: int | None
    request: HttpMessagePart
    response: HttpResponsePart
    error: str | None


_SENSITIVE_HEADERS = {
    "authorization",
    "api-key",
    "x-api-key",
    "cookie",
    "set-cookie",
}
_SENSITIVE_BODY_KEYS = {
    "api_key",
    "token",
    "password",
    "secret",
    "access_token",
    "refresh_token",
}
_CURRENT_COLLECTOR: 'ContextVar[HttpTraceCollector | None]' = ContextVar(
    "http_trace_collector",
    default=None,
)


def _now_ms() -> int:
    return int(time.time() * 1000)


def _mask_header(name: str, value: Any) -> str:
    text = "" if value is None else str(value)
    if name.lower() in _SENSITIVE_HEADERS:
        if text.lower().startswith("bearer "):
            return "Bearer ***"
        return "***"
    return text


def _mask_json_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            key: ("***" if key.lower() in _SENSITIVE_BODY_KEYS else _mask_json_obj(value))
            for key, value in obj.items()
        }
    if isinstance(obj, list):
        return [_mask_json_obj(item) for item in obj]
    return obj


def _normalize_headers(headers: dict[str, Any] | None) -> dict[str, str]:
    if not headers:
        return {}
    return {str(key): _mask_header(str(key), value) for key, value in headers.items()}


def _normalize_body(body: Any) -> tuple[str, str]:
    if body is None:
        return "空", "empty"
    if isinstance(body, (dict, list)):
        return json.dumps(_mask_json_obj(body), ensure_ascii=False, indent=2), "json"

    if isinstance(body, (bytes, bytearray)):
        text = body.decode("utf-8", errors="replace")
    else:
        text = str(body)

    text = text.strip()
    if not text:
        return "空", "empty"

    try:
        parsed = json.loads(text)
    except Exception:
        return text, "text"

    return json.dumps(_mask_json_obj(parsed), ensure_ascii=False, indent=2), "json"


@dataclass(slots=True)
class _PendingTrace:
    id: str
    sequence: int
    provider: str | None
    model: str | None
    started_at: int
    request_method: str | None
    request_url: str | None
    request_headers: dict[str, str]
    request_body: str
    request_body_format: str
    response_status: int | None = None
    response_headers: dict[str, str] = field(default_factory=dict)
    response_body: str = "未返回"
    response_body_format: str = "unknown"
    response_ok: bool | None = None
    duration_ms: int | None = None
    error: str | None = None


class HttpTraceCollector:
    def __init__(self, *, provider: str | None, model: str | None, seq_offset: int = 0):
        self.provider = provider
        self.model = model
        self._seq = seq_offset
        self._traces: list[_PendingTrace] = []

    def start_request(
        self,
        *,
        method: str | None,
        url: str | None,
        headers: dict[str, Any] | None,
        body: Any,
    ) -> str:
        self._seq += 1
        request_body, request_body_format = _normalize_body(body)
        trace = _PendingTrace(
            id=f"trace-{self._seq}",
            sequence=self._seq,
            provider=self.provider,
            model=self.model,
            started_at=_now_ms(),
            request_method=method,
            request_url=url,
            request_headers=_normalize_headers(headers),
            request_body=request_body,
            request_body_format=request_body_format,
        )
        self._traces.append(trace)
        return trace.id

    def finish_response(
        self,
        trace_id: str,
        *,
        status: int | None,
        headers: dict[str, Any] | None,
        body: Any,
        duration_ms: int | None,
    ) -> None:
        trace = next(item for item in self._traces if item.id == trace_id)
        response_body, response_body_format = _normalize_body(body)
        trace.response_status = status
        trace.response_headers = _normalize_headers(headers)
        trace.response_body = response_body
        trace.response_body_format = response_body_format
        trace.response_ok = bool(status is not None and 200 <= status < 400)
        trace.duration_ms = duration_ms

    def fail_response(self, trace_id: str, error: str) -> None:
        trace = next(item for item in self._traces if item.id == trace_id)
        trace.error = error
        trace.response_ok = False

    def snapshot(self) -> list[HttpTrace]:
        return [
            {
                "id": trace.id,
                "sequence": trace.sequence,
                "kind": "llm_http",
                "provider": trace.provider,
                "model": trace.model,
                "startedAt": trace.started_at,
                "durationMs": trace.duration_ms,
                "request": {
                    "method": trace.request_method,
                    "url": trace.request_url,
                    "headers": trace.request_headers,
                    "body": trace.request_body,
                    "bodyFormat": trace.request_body_format,
                },
                "response": {
                    "status": trace.response_status,
                    "headers": trace.response_headers,
                    "body": trace.response_body,
                    "bodyFormat": trace.response_body_format,
                    "ok": trace.response_ok,
                },
                "error": trace.error,
            }
            for trace in self._traces
        ]


def bind_http_trace_collector(collector: HttpTraceCollector) -> Token:
    return _CURRENT_COLLECTOR.set(collector)


def reset_http_trace_collector(token: Token) -> None:
    _CURRENT_COLLECTOR.reset(token)


def get_http_trace_collector() -> HttpTraceCollector | None:
    return _CURRENT_COLLECTOR.get()


# Sub-agent HTTP traces registry — keyed by sub_thread_id (globally unique per session+tool_call).
# Using a plain dict avoids ContextVar inheritance issues across asyncio task boundaries.
_SUBAGENT_TRACES_STORE: dict[str, list] = {}


def init_subagent_collector_registry() -> None:
    """No-op with the global-dict approach; kept for API compatibility."""


def register_subagent_collector(sub_thread_id: str, collector: "HttpTraceCollector") -> None:
    """Store completed sub-agent traces so SSE can retrieve them after ainvoke."""
    traces = collector.snapshot()
    if traces:
        _SUBAGENT_TRACES_STORE[sub_thread_id] = traces


def pop_subagent_traces(sub_thread_id: str) -> list:
    """Return and remove the collected HTTP traces for a sub-agent session."""
    return _SUBAGENT_TRACES_STORE.pop(sub_thread_id, [])

`````

--- **end of file: lc_agent/core/http_trace.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/core/http_trace_httpx.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/core/http_trace_httpx.py`

#### 📦 Imports

- `import time`
- `from collections.abc import Callable`
- `from typing import Any`
- `import httpx`
- `import openai`
- `from lc_agent.core.http_trace import HttpTraceCollector`

#### 🏛️ Classes (2)

##### 📌 `class _TracingAsyncByteStream(httpx.AsyncByteStream)`
*Line: 12*

**🔧 Constructor (`__init__`):**
- `def __init__(self, stream: httpx.AsyncByteStream, on_success: Callable[[bytes, int], None], on_error: Callable[[Exception], None])`
  - **Parameters:**
    - `self`
    - `stream: httpx.AsyncByteStream`
    - `on_success: Callable[[bytes, int], None]`
    - `on_error: Callable[[Exception], None]`

**Public Methods (1):**
- `async def aclose(self) -> None`

##### 📌 `class TracingAsyncClient(openai.DefaultAsyncHttpxClient)`
*Line: 59*

**🔧 Constructor (`__init__`):**
- `def __init__(self, **kwargs: Any)`
  - **Parameters:**
    - `self`
    - `**kwargs: Any`

**Public Methods (1):**
- `async def send(self, request: httpx.Request, *args: Any, **kwargs: Any) -> httpx.Response`


---

`````python

import time
from collections.abc import Callable
from typing import Any

import httpx
import openai

from lc_agent.core.http_trace import HttpTraceCollector


class _TracingAsyncByteStream(httpx.AsyncByteStream):
    def __init__(
        self,
        stream: httpx.AsyncByteStream,
        on_success: Callable[[bytes, int], None],
        on_error: Callable[[Exception], None],
    ):
        self._stream = stream
        self._on_success = on_success
        self._on_error = on_error
        self._chunks: list[bytes] = []
        self._finished = False
        self._started = time.time()

    async def __aiter__(self):
        try:
            async for chunk in self._stream:
                self._chunks.append(chunk)
                yield chunk
            self._finish_success()
        except Exception as exc:
            self._finish_error(exc)
            raise

    async def aclose(self) -> None:
        try:
            await self._stream.aclose()
        except Exception as exc:
            self._finish_error(exc)
            raise
        else:
            self._finish_success()

    def _finish_success(self) -> None:
        if self._finished:
            return
        self._finished = True
        duration_ms = int((time.time() - self._started) * 1000)
        self._on_success(b"".join(self._chunks), duration_ms)

    def _finish_error(self, exc: Exception) -> None:
        if self._finished:
            return
        self._finished = True
        self._on_error(exc)


class TracingAsyncClient(openai.DefaultAsyncHttpxClient):
    def __init__(
        self,
        *,
        collector_getter: Callable[[], HttpTraceCollector | None],
        provider: str | None,
        model: str | None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._collector_getter = collector_getter
        self.provider = provider
        self.model = model

    async def send(self, request: httpx.Request, *args: Any, **kwargs: Any) -> httpx.Response:
        collector = self._collector_getter()
        started = time.time()
        trace_id: str | None = None

        if collector is not None:
            trace_id = collector.start_request(
                method=request.method,
                url=str(request.url),
                headers=dict(request.headers),
                body=request.content,
            )

        try:
            response = await super().send(request, *args, **kwargs)
        except Exception as exc:
            if collector is not None and trace_id is not None:
                collector.fail_response(trace_id, exc.__class__.__name__)
            raise

        if collector is None or trace_id is None:
            return response

        if response.is_stream_consumed:
            body = getattr(response, "content", b"")
            collector.finish_response(
                trace_id,
                status=response.status_code,
                headers=dict(response.headers),
                body=body,
                duration_ms=int((time.time() - started) * 1000),
            )
            return response

        def _finish_success(body: bytes, duration_ms: int) -> None:
            collector.finish_response(
                trace_id,
                status=response.status_code,
                headers=dict(response.headers),
                body=body,
                duration_ms=duration_ms,
            )

        def _finish_error(exc: Exception) -> None:
            collector.fail_response(trace_id, exc.__class__.__name__)

        response.stream = _TracingAsyncByteStream(response.stream, _finish_success, _finish_error)
        return response

`````

--- **end of file: lc_agent/core/http_trace_httpx.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/core/memory.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/core/memory.py`

#### 📦 Imports

- `from collections.abc import Sequence`
- `from dataclasses import dataclass`
- `from typing import Annotated`
- `from typing import Any`
- `import aiosqlite`
- `import httpx`
- `from langchain.tools import ToolRuntime`
- `from langchain_core.tools import StructuredTool`
- `from langchain_core.tools.base import InjectedToolArg`
- `from langgraph.store.base import IndexConfig`
- `from langgraph.store.sqlite.aio import AsyncSqliteStore`
- `from pydantic import BaseModel`
- `from pydantic import ConfigDict`
- `from pydantic import Field`

#### 🏛️ Classes (6)

##### 📌 `class AgentRuntimeContext`
*Line: 24*

**Class Variables (1):**
- `user_id: str`

##### 📌 `class OpenAICompatibleEmbeddings`
*Line: 40*

**🔧 Constructor (`__init__`):**
- `def __init__(self)`
  - **Parameters:**
    - `self`

**Public Methods (4):**
- `def embed_documents(self, texts: list[str]) -> list[list[float]]`
- `async def aembed_documents(self, texts: list[str]) -> list[list[float]]`
- `def embed_query(self, text: str) -> list[float]`
- `async def aembed_query(self, text: str) -> list[float]`

##### 📌 `class _RuntimeArgs(BaseModel)`
*Line: 156*

**Class Variables (2):**
- `model_config = ConfigDict(arbitrary_types_allowed=True)`
- `runtime: Annotated[Any, InjectedToolArg()] = Field(description='Injected LangChain runtime')`

##### 📌 `class _KeyContentArgs(_RuntimeArgs)`
*Line: 161*

**Class Variables (2):**
- `key: str = Field(description='Memory key')`
- `content: str = Field(description='Memory content')`

##### 📌 `class _KeyArgs(_RuntimeArgs)`
*Line: 166*

**Class Variables (1):**
- `key: str = Field(description='Memory key')`

##### 📌 `class _SearchArgs(_RuntimeArgs)`
*Line: 170*

**Class Variables (2):**
- `query: str = Field(description='Search query')`
- `limit: int = Field(default=10, description='Maximum number of memories to return')`

#### 🔧 Public Functions (12)

- `def normalize_memory_user_id(user_id: str | None) -> str`
  - *Line: 28*

- `def memory_namespace(user_id: str | None, base_namespace: tuple[str, ...] = DEFAULT_MEMORY_NAMESPACE) -> tuple[str, ...]`
  - *Line: 33*

- `def build_store_index(memory_config: Any) -> IndexConfig | None`
  - *Line: 120*

- `async def create_sqlite_memory_store(path: str, memory_config: Any | None = None) -> AsyncSqliteStore`
  - *Line: 141*

- `async def aclose_memory_store(store: AsyncSqliteStore) -> None`
  - *Line: 152*

- `def build_memory_tools(namespace: tuple[str, ...] = DEFAULT_MEMORY_NAMESPACE) -> list[StructuredTool]`
  - *Line: 270*

- `async def insert_memory(key: str, content: str, runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str`
  - *Line: 273*

- `async def update_memory(key: str, content: str, runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str`
  - *Line: 276*

- `async def get_memory(key: str, runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str`
  - *Line: 279*

- `async def search_memories(query: str, runtime: ToolRuntime[AgentRuntimeContext, Any], limit: int = 10) -> str`
  - *Line: 282*

- `async def list_memories(runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str`
  - *Line: 289*

- `async def delete_memory(key: str, runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str`
  - *Line: 292*


---

`````python

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Any

import aiosqlite
import httpx
from langchain.tools import ToolRuntime
from langchain_core.tools import StructuredTool
from langchain_core.tools.base import InjectedToolArg
from langgraph.store.base import IndexConfig
from langgraph.store.sqlite.aio import AsyncSqliteStore
from pydantic import BaseModel, ConfigDict, Field


DEFAULT_MEMORY_NAMESPACE = ("lc-agent", "memories")

MEMORY_SYSTEM_PROMPT = """You may use the memory tools to store and retrieve durable user memories.
Only save stable, user-relevant preferences or facts when the user explicitly asks you to remember them
or when a memory is clearly useful for future conversations. Keep memory keys short and specific."""


@dataclass(frozen=True)
class AgentRuntimeContext:
    user_id: str


def normalize_memory_user_id(user_id: str | None) -> str:
    normalized = (user_id or "anonymous").strip()
    return normalized or "anonymous"


def memory_namespace(
    user_id: str | None,
    base_namespace: tuple[str, ...] = DEFAULT_MEMORY_NAMESPACE,
) -> tuple[str, ...]:
    return (*base_namespace, normalize_memory_user_id(user_id))


class OpenAICompatibleEmbeddings:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 60.0,
    ) -> None:
        if not api_key:
            raise ValueError("memory semantic_search.api_key is required when semantic search is enabled")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._aembed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]

    async def aembed_query(self, text: str) -> list[float]:
        return (await self._aembed([text]))[0]

    def __call__(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed(list(texts))

    async def _acall(self, texts: Sequence[str]) -> list[list[float]]:
        return await self._aembed(list(texts))

    def _payload(self, texts: list[str]) -> dict[str, Any]:
        return {
            "model": self.model,
            "input": texts,
            "encoding_format": "float",
        }

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _embed(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            f"{self.base_url}/embeddings",
            json=self._payload(texts),
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return _extract_embeddings(response.json())

    async def _aembed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                json=self._payload(texts),
                headers=self._headers(),
            )
            response.raise_for_status()
            return _extract_embeddings(response.json())


def _extract_embeddings(payload: dict[str, Any]) -> list[list[float]]:
    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("Embedding response missing data list")
    return [item["embedding"] for item in data]


def _get_config_value(config: Any, name: str, default: Any = None) -> Any:
    if config is None:
        return default
    if isinstance(config, dict):
        return config.get(name, default)
    return getattr(config, name, default)


def build_store_index(memory_config: Any) -> IndexConfig | None:
    semantic = _get_config_value(memory_config, "semantic_search")
    if semantic is None or not _get_config_value(semantic, "enabled", False):
        return None

    api_key = _get_config_value(semantic, "api_key", "")
    if not api_key:
        raise ValueError("memory.semantic_search.api_key is required when semantic search is enabled")

    embeddings = OpenAICompatibleEmbeddings(
        api_key=api_key,
        base_url=_get_config_value(semantic, "base_url", ""),
        model=_get_config_value(semantic, "model", ""),
    )
    return IndexConfig(
        embed=embeddings,
        dims=int(_get_config_value(semantic, "dims", 0)),
        fields=["content"],
    )


async def create_sqlite_memory_store(
    path: str,
    memory_config: Any | None = None,
) -> AsyncSqliteStore:
    index = build_store_index(memory_config) if memory_config is not None else None
    conn = await aiosqlite.connect(path, isolation_level=None)
    store = AsyncSqliteStore(conn, index=index)
    await store.setup()
    return store


async def aclose_memory_store(store: AsyncSqliteStore) -> None:
    await store.conn.close()


class _RuntimeArgs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    runtime: Annotated[Any, InjectedToolArg()] = Field(description="Injected LangChain runtime")


class _KeyContentArgs(_RuntimeArgs):
    key: str = Field(description="Memory key")
    content: str = Field(description="Memory content")


class _KeyArgs(_RuntimeArgs):
    key: str = Field(description="Memory key")


class _SearchArgs(_RuntimeArgs):
    query: str = Field(description="Search query")
    limit: int = Field(default=10, description="Maximum number of memories to return")


def _runtime_namespace(runtime: Any, namespace: tuple[str, ...]) -> tuple[str, ...]:
    context = getattr(runtime, "context", None)
    user_id = getattr(context, "user_id", None)
    if isinstance(context, dict):
        user_id = context.get("user_id", user_id)
    return memory_namespace(user_id, namespace)


def _format_memory_item(item: Any) -> str:
    value = getattr(item, "value", None)
    content = value.get("content") if isinstance(value, dict) else value
    key = getattr(item, "key", "")
    return f"{key}: {content}" if key else str(content)


async def _insert_memory(*, key: str, content: str, runtime: Any, namespace: tuple[str, ...]) -> str:
    store = runtime.store
    ns = _runtime_namespace(runtime, namespace)
    existing = await store.aget(ns, key)
    if existing is not None:
        return f"Memory key '{key}' already exists; conflict/duplicate insert ignored."
    await store.aput(ns, key, {"content": content})
    return f"Inserted memory '{key}'."


async def _update_memory(*, key: str, content: str, runtime: Any, namespace: tuple[str, ...]) -> str:
    store = runtime.store
    ns = _runtime_namespace(runtime, namespace)
    existing = await store.aget(ns, key)
    if existing is None:
        return f"Memory key '{key}' is missing/not found; update ignored."
    await store.aput(ns, key, {"content": content})
    return f"Updated memory '{key}'."


async def _get_memory(*, key: str, runtime: Any, namespace: tuple[str, ...]) -> str:
    item = await runtime.store.aget(_runtime_namespace(runtime, namespace), key)
    if item is None:
        return "Memory not found."
    return _format_memory_item(item)


async def _search_memories(
    *,
    query: str,
    runtime: Any,
    namespace: tuple[str, ...],
    limit: int = 10,
) -> str:
    results = await runtime.store.asearch(
        _runtime_namespace(runtime, namespace),
        query=query,
        limit=limit,
    )
    if not results:
        return "No memories found."
    return "\n".join(_format_memory_item(item) for item in results)


async def _list_memories(*, runtime: Any, namespace: tuple[str, ...]) -> str:
    results = await runtime.store.asearch(
        _runtime_namespace(runtime, namespace),
        limit=100,
    )
    if not results:
        return "No memories found."
    return "\n".join(_format_memory_item(item) for item in results)


async def _delete_memory(*, key: str, runtime: Any, namespace: tuple[str, ...]) -> str:
    store = runtime.store
    ns = _runtime_namespace(runtime, namespace)
    existing = await store.aget(ns, key)
    if existing is None:
        return f"Memory key '{key}' not found."
    await store.adelete(ns, key)
    return f"Deleted memory '{key}'."


def _tool_from_coroutine(
    *,
    name: str,
    description: str,
    args_schema: type[BaseModel],
    coroutine: Any,
) -> StructuredTool:
    return StructuredTool.from_function(
        func=None,
        coroutine=coroutine,
        name=name,
        description=description,
        args_schema=args_schema,
    )


def build_memory_tools(
    namespace: tuple[str, ...] = DEFAULT_MEMORY_NAMESPACE,
) -> list[StructuredTool]:
    async def insert_memory(key: str, content: str, runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str:
        return await _insert_memory(key=key, content=content, runtime=runtime, namespace=namespace)

    async def update_memory(key: str, content: str, runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str:
        return await _update_memory(key=key, content=content, runtime=runtime, namespace=namespace)

    async def get_memory(key: str, runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str:
        return await _get_memory(key=key, runtime=runtime, namespace=namespace)

    async def search_memories(
        query: str,
        runtime: ToolRuntime[AgentRuntimeContext, Any],
        limit: int = 10,
    ) -> str:
        return await _search_memories(query=query, runtime=runtime, namespace=namespace, limit=limit)

    async def list_memories(runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str:
        return await _list_memories(runtime=runtime, namespace=namespace)

    async def delete_memory(key: str, runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str:
        return await _delete_memory(key=key, runtime=runtime, namespace=namespace)

    return [
        _tool_from_coroutine(
            name="memory__insert_memory",
            description="Insert a new durable memory for the current user. Fails if the key already exists.",
            args_schema=_KeyContentArgs,
            coroutine=insert_memory,
        ),
        _tool_from_coroutine(
            name="memory__update_memory",
            description="Update an existing durable memory for the current user. Fails if the key is missing.",
            args_schema=_KeyContentArgs,
            coroutine=update_memory,
        ),
        _tool_from_coroutine(
            name="memory__get_memory",
            description="Get one durable memory by key for the current user.",
            args_schema=_KeyArgs,
            coroutine=get_memory,
        ),
        _tool_from_coroutine(
            name="memory__search_memories",
            description="Search durable memories for the current user.",
            args_schema=_SearchArgs,
            coroutine=search_memories,
        ),
        _tool_from_coroutine(
            name="memory__list_memories",
            description="List durable memories for the current user.",
            args_schema=_RuntimeArgs,
            coroutine=list_memories,
        ),
        _tool_from_coroutine(
            name="memory__delete_memory",
            description="Delete one durable memory by key for the current user.",
            args_schema=_KeyArgs,
            coroutine=delete_memory,
        ),
    ]

`````

--- **end of file: lc_agent/core/memory.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/core/models.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/core/models.py`

#### 📦 Imports

- `from pydantic import BaseModel`

#### 🏛️ Classes (3)

##### 📌 `class SubAgentLink(BaseModel)`
*Line: 5*

**Class Variables (2):**
- `agent_id: str`
- `delegation_description: str`

##### 📌 `class ModelInfo(BaseModel)`
*Line: 10*

**Docstring:**
`````
LLM model metadata.
`````

**Class Variables (6):**
- `id: str`
- `provider: str`
- `base_url: str`
- `context_limit: int = 8000`
- `max_output_tokens: int = 0`
- `api_key: str = ''`

##### 📌 `class AgentPreset(BaseModel)`
*Line: 21*

**Docstring:**
`````
Agent preset configuration (three-value semantics from nb_agent).

For allowed_* fields:
  None  = all allowed (default)
  []    = all disabled
  ["a"] = only specified items allowed

source: "builtin" | "code" | "user"
default_enabled: controls whether tools/MCP/skills default to ON or OFF in the UI
`````

**Class Variables (14):**
- `id: str`
- `name: str`
- `display_name: str | None = None`
- `system_prompt: str`
- `default_model: str`
- `default_delegation_description: str = ''`
- `allowed_tool_groups: list[str] | None = None`
- `allowed_mcp_servers: list[str] | None = None`
- `allowed_skills: list[str] | None = None`
- `llm_params: dict | None = None`
- `source: str = 'user'`
- `default_enabled: bool = True`
- `subagents: list[SubAgentLink] | None = None`
- `enable_general_purpose_subagent: bool = False`


---

`````python
# lc_agent/core/models.py
from pydantic import BaseModel


class SubAgentLink(BaseModel):
    agent_id: str
    delegation_description: str


class ModelInfo(BaseModel):
    """LLM model metadata."""

    id: str
    provider: str
    base_url: str
    context_limit: int = 8000
    max_output_tokens: int = 0
    api_key: str = ""


class AgentPreset(BaseModel):
    """Agent preset configuration (three-value semantics from nb_agent).

    For allowed_* fields:
      None  = all allowed (default)
      []    = all disabled
      ["a"] = only specified items allowed

    source: "builtin" | "code" | "user"
    default_enabled: controls whether tools/MCP/skills default to ON or OFF in the UI
    """

    id: str
    name: str
    display_name: str | None = None
    system_prompt: str
    default_model: str
    default_delegation_description: str = ""

    allowed_tool_groups: list[str] | None = None
    allowed_mcp_servers: list[str] | None = None
    allowed_skills: list[str] | None = None

    llm_params: dict | None = None

    source: str = "user"
    default_enabled: bool = True

    subagents: list[SubAgentLink] | None = None
    enable_general_purpose_subagent: bool = False

`````

--- **end of file: lc_agent/core/models.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/core/permissions.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/core/permissions.py`

#### 📦 Imports

- `import json`
- `import logging`
- `import re`
- `from pathlib import Path`
- `from typing import Any`

#### 🏛️ Classes (1)

##### 📌 `class PermissionsService`
*Line: 18*

**Docstring:**
`````
Manages tool permissions with JSONC file persistence.

All tools require approval by default. Tools listed in ``tool_allowlist``
skip the human-in-the-loop interrupt.
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, permissions_path: Path)`
  - **Parameters:**
    - `self`
    - `permissions_path: Path`

**Public Methods (6):**
- `def is_allowed(self, tool_name: str) -> bool`
- `def should_interrupt(self, request: Any) -> bool`
  - **Docstring:**
  `````
  ``when`` predicate for HumanInTheLoopMiddleware.
  
  Returns True to interrupt (tool NOT in allowlist).
  Returns False to auto-approve (tool IS in allowlist).
  `````
- `def allow_tool(self, tool_name: str) -> None`
- `def remove_tool(self, tool_name: str) -> None`
- `def get_allowlist(self) -> list[str]`
- `def set_allowlist(self, tools: list[str]) -> None`


---

`````python

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_JSONC_COMMENT_RE = re.compile(r"//.*?$|/\*.*?\*/", re.MULTILINE | re.DOTALL)


def _strip_jsonc_comments(text: str) -> str:
    """Remove // and /* */ comments from JSONC text."""
    return _JSONC_COMMENT_RE.sub("", text)


class PermissionsService:
    """Manages tool permissions with JSONC file persistence.

    All tools require approval by default. Tools listed in ``tool_allowlist``
    skip the human-in-the-loop interrupt.
    """

    def __init__(self, permissions_path: Path):
        self._path = Path(permissions_path)
        self._allowlist: set[str] = set()
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            self._allowlist = set()
            return
        try:
            raw = self._path.read_text(encoding="utf-8")
            cleaned = _strip_jsonc_comments(raw)
            data = json.loads(cleaned)
            tools = data.get("tool_allowlist", [])
            self._allowlist = set(tools) if isinstance(tools, list) else set()
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load permissions from %s: %s — using empty allowlist", self._path, e)
            self._allowlist = set()

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "tool_allowlist": sorted(self._allowlist),
        }
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._path)

    def is_allowed(self, tool_name: str) -> bool:
        return tool_name in self._allowlist

    def should_interrupt(self, request: Any) -> bool:
        """``when`` predicate for HumanInTheLoopMiddleware.

        Returns True to interrupt (tool NOT in allowlist).
        Returns False to auto-approve (tool IS in allowlist).
        """
        tool_name = request.tool_call["name"]
        return not self.is_allowed(tool_name)

    def allow_tool(self, tool_name: str) -> None:
        self._allowlist.add(tool_name)
        self._save()

    def remove_tool(self, tool_name: str) -> None:
        self._allowlist.discard(tool_name)
        self._save()

    def get_allowlist(self) -> list[str]:
        return sorted(self._allowlist)

    def set_allowlist(self, tools: list[str]) -> None:
        self._allowlist = set(tools)
        self._save()

`````

--- **end of file: lc_agent/core/permissions.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/core/traced_llm.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/core/traced_llm.py`

#### 📦 Imports

- `from typing import Any`
- `from lc_agent.core.chat_model import ChatOpenAIReasoning`
- `from lc_agent.core.http_trace import get_http_trace_collector`
- `from lc_agent.core.http_trace_httpx import TracingAsyncClient`

#### 🔧 Public Functions (2)

- `def create_traced_openai_http_client(**kwargs: Any) -> TracingAsyncClient`
  - *Line: 9*
  - *Create an OpenAI-compatible async HTTP client with lc-agent tracing enabled.*

- `def create_traced_chat_openai(**kwargs: Any) -> ChatOpenAIReasoning`
  - *Line: 28*
  - **Docstring:**
  `````
  Create a ChatOpenAIReasoning model that records HTTP request/response traces.
  
  This helper is intended for code-registered agents built with StateGraph,
  langchain.agents.create_agent(model=llm), deepagents, or any other
  LangChain-compatible graph where the application code owns LLM construction.
  `````


---

`````python

from typing import Any

from lc_agent.core.chat_model import ChatOpenAIReasoning
from lc_agent.core.http_trace import get_http_trace_collector
from lc_agent.core.http_trace_httpx import TracingAsyncClient


def create_traced_openai_http_client(
    *,
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    timeout: float = 120,
    **kwargs: Any,
) -> TracingAsyncClient:
    """Create an OpenAI-compatible async HTTP client with lc-agent tracing enabled."""
    return TracingAsyncClient(
        collector_getter=get_http_trace_collector,
        provider=provider,
        model=model,
        base_url=base_url or "https://api.openai.com/v1",
        timeout=timeout,
        **kwargs,
    )


def create_traced_chat_openai(
    *,
    model: str,
    base_url: str | None = None,
    api_key: str = "not-set",
    provider: str | None = None,
    timeout: float = 120,
    stream_usage: bool = True,
    **kwargs: Any,
) -> ChatOpenAIReasoning:
    """Create a ChatOpenAIReasoning model that records HTTP request/response traces.

    This helper is intended for code-registered agents built with StateGraph,
    langchain.agents.create_agent(model=llm), deepagents, or any other
    LangChain-compatible graph where the application code owns LLM construction.
    """
    return ChatOpenAIReasoning(
        model=model,
        base_url=base_url,
        api_key=api_key,
        stream_usage=stream_usage,
        http_async_client=create_traced_openai_http_client(
            provider=provider,
            model=model,
            base_url=base_url,
            timeout=timeout,
        ),
        **kwargs,
    )

`````

--- **end of file: lc_agent/core/traced_llm.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/core/__init__.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/core/__init__.py`

#### 📦 Imports

- `from lc_agent.core.engine import AgentEngine`
- `from lc_agent.core.models import AgentPreset`
- `from lc_agent.core.models import ModelInfo`


---

`````python
# lc_agent/core/__init__.py
from lc_agent.core.engine import AgentEngine
from lc_agent.core.models import AgentPreset, ModelInfo

__all__ = ["AgentEngine", "AgentPreset", "ModelInfo"]

`````

--- **end of file: lc_agent/core/__init__.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/engine.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/engine.py`

#### 📦 Imports

- `from pathlib import Path`
- `from sqlalchemy.ext.asyncio import create_async_engine`
- `from sqlalchemy.ext.asyncio import AsyncSession`
- `from sqlalchemy.orm import sessionmaker`
- `from sqlalchemy.pool import StaticPool`
- `from sqlmodel import SQLModel`
- `from lc_agent.utils.loggers import db_logger`
- `from sqlalchemy import inspect as sa_inspect`
- `from sqlalchemy import text`
- `import lc_agent.db.models`
- `from alembic.config import Config`
- `from alembic import command`
- `from alembic.script import ScriptDirectory`

#### 🔧 Public Functions (4)

- `def get_async_engine(url: str = 'sqlite+aiosqlite:///./lc_agent_data.db')`
  - *Line: 16*

- `def get_async_session(url: str = 'sqlite+aiosqlite:///./lc_agent_data.db') -> AsyncSession`
  - *Line: 30*

- `async def init_db(url: str = 'sqlite+aiosqlite:///./lc_agent_data.db')`
  - *Line: 75*
  - **Docstring:**
  `````
  Run Alembic migrations to create / update all tables.
  
  Falls back to SQLModel.metadata.create_all if alembic has no revisions yet.
  After create_all, inspects existing tables and adds any missing columns
  (handles the case where migrations failed but tables already exist).
  `````

- `def reset_engine()`
  - *Line: 113*
  - *Reset engine state (for testing).*


---

`````python
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from lc_agent.utils.loggers import db_logger

_engine = None
_async_session_factory = None

_MIGRATIONS_DIR = str(Path(__file__).parent / "migrations")


def get_async_engine(url: str = "sqlite+aiosqlite:///./lc_agent_data.db"):
    global _engine, _engine_url, _async_session_factory, _async_session_factory_url
    if _engine is None or _engine_url != url:
        _async_session_factory = None
        _async_session_factory_url = None
        engine_kwargs = {"echo": False}
        if url.endswith(":memory:"):
            engine_kwargs["poolclass"] = StaticPool
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        _engine = create_async_engine(url, **engine_kwargs)
        _engine_url = url
    return _engine


def get_async_session(url: str = "sqlite+aiosqlite:///./lc_agent_data.db") -> AsyncSession:
    global _async_session_factory, _async_session_factory_url
    if _async_session_factory is None or _async_session_factory_url != url:
        engine = get_async_engine(url)
        _async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        _async_session_factory_url = url
    return _async_session_factory()


def _to_sync_url(url: str) -> str:
    """Convert async DB URL to sync for Alembic."""
    if "+aiosqlite" in url:
        return url.replace("+aiosqlite", "")
    return url


def _add_missing_columns(connection):
    """Inspect existing tables and ALTER TABLE ADD COLUMN for any missing columns.

    Handles the gap where create_all skips existing tables but migrations
    that would have added new columns failed.
    SQLite-specific: uses PRAGMA table_info.
    """
    from sqlalchemy import inspect as sa_inspect, text

    inspector = sa_inspect(connection)
    for table in SQLModel.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue
        existing_cols = {col["name"] for col in inspector.get_columns(table.name)}
        for col in table.columns:
            if col.name not in existing_cols:
                col_type = col.type.compile(connection.dialect)
                nullable = "" if col.nullable else " NOT NULL"
                default = ""
                if col.server_default is not None:
                    default = f" DEFAULT {col.server_default.arg}"
                ddl = f"ALTER TABLE {table.name} ADD COLUMN {col.name} {col_type}{nullable}{default}"
                try:
                    connection.execute(text(ddl))
                    db_logger.info("Added missing column: %s.%s (%s)", table.name, col.name, col_type)
                except Exception:
                    db_logger.exception("Failed to add column %s.%s", table.name, col.name)


async def init_db(url: str = "sqlite+aiosqlite:///./lc_agent_data.db"):
    """Run Alembic migrations to create / update all tables.

    Falls back to SQLModel.metadata.create_all if alembic has no revisions yet.
    After create_all, inspects existing tables and adds any missing columns
    (handles the case where migrations failed but tables already exist).
    """
    import lc_agent.db.models  # noqa: F401 — ensure models are registered

    sync_url = _to_sync_url(url)

    try:
        from alembic.config import Config
        from alembic import command
        from alembic.script import ScriptDirectory

        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", _MIGRATIONS_DIR)
        alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

        script = ScriptDirectory.from_config(alembic_cfg)
        has_revisions = bool(list(script.walk_revisions()))

        if has_revisions:
            command.upgrade(alembic_cfg, "head")
            engine = get_async_engine(url)
            async with engine.begin() as conn:
                await conn.run_sync(_add_missing_columns)
            return
    except Exception as e:
        db_logger.exception("Alembic migration failed, falling back to create_all")

    engine = get_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.run_sync(_add_missing_columns)


def reset_engine():
    """Reset engine state (for testing)."""
    global _engine, _async_session_factory
    _engine = None
    _async_session_factory = None

`````

--- **end of file: lc_agent/db/engine.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/models.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/models.py`

#### 📦 Imports

- `import uuid`
- `from datetime import datetime`
- `from datetime import timezone`
- `from typing import Any`
- `from sqlmodel import SQLModel`
- `from sqlmodel import Field`
- `from sqlalchemy import Boolean`
- `from sqlalchemy import Column`
- `from sqlalchemy import JSON`
- `from sqlalchemy import false`

#### 🏛️ Classes (3)

##### 📌 `class AgentPresetDB(SQLModel)`
*Line: 13*

**Class Variables (14):**
- `__tablename__ = 'agent_presets'`
- `id: str = Field(default_factory=lambda : str(uuid.uuid4()), primary_key=True)`
- `name: str`
- `display_name: str | None = Field(default=None)`
- `system_prompt: str = ''`
- `default_model: str = ''`
- `allowed_tool_groups: list[str] | None = Field(default=None, sa_column=Column(JSON))`
- `allowed_mcp_servers: list[str] | None = Field(default=None, sa_column=Column(JSON))`
- `allowed_skills: list[str] | None = Field(default=None, sa_column=Column(JSON))`
- `subagents: list[dict[str, Any]] | None = Field(default=None, sa_column=Column(JSON))`
- `enable_general_purpose_subagent: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, server_default=false()))`
- `llm_params: dict | None = Field(default=None, sa_column=Column(JSON))`
- `created_at: datetime = Field(default_factory=utcnow)`
- `updated_at: datetime = Field(default_factory=utcnow)`

##### 📌 `class SessionMeta(SQLModel)`
*Line: 34*

**Class Variables (13):**
- `__tablename__ = 'sessions'`
- `id: str = Field(default_factory=lambda : str(uuid.uuid4()), primary_key=True)`
- `title: str = '新对话'`
- `agent_id: str = 'chat'`
- `model: str = ''`
- `user_id: str = Field(default='', index=True)`
- `parent_session_id: str | None = Field(default=None, index=True)`
- `tool_call_id: str | None = Field(default=None)`
- `message_count: int = 0`
- `is_pinned: bool = False`
- `pinned_at: datetime | None = None`
- `created_at: datetime = Field(default_factory=utcnow)`
- `updated_at: datetime = Field(default_factory=utcnow)`

##### 📌 `class ChatUiMessage(SQLModel)`
*Line: 51*

**Class Variables (9):**
- `__tablename__ = 'chat_ui_messages'`
- `id: str = Field(default_factory=lambda : str(uuid.uuid4()), primary_key=True)`
- `session_id: str = Field(index=True)`
- `role: str`
- `content: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))`
- `tool_calls: list[dict[str, Any]] | None = Field(default=None, sa_column=Column(JSON))`
- `usage: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))`
- `http_traces: list[dict[str, Any]] | None = Field(default=None, sa_column=Column(JSON))`
- `created_at: datetime = Field(default_factory=utcnow)`

#### 🔧 Public Functions (1)

- `def utcnow()`
  - *Line: 9*


---

`````python
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlmodel import SQLModel, Field
from sqlalchemy import Boolean, Column, JSON, false


def utcnow():
    return datetime.now(timezone.utc)


class AgentPresetDB(SQLModel, table=True):
    __tablename__ = "agent_presets"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    display_name: str | None = Field(default=None)
    system_prompt: str = ""
    default_model: str = ""
    allowed_tool_groups: list[str] | None = Field(default=None, sa_column=Column(JSON))
    allowed_mcp_servers: list[str] | None = Field(default=None, sa_column=Column(JSON))
    allowed_skills: list[str] | None = Field(default=None, sa_column=Column(JSON))
    subagents: list[dict[str, Any]] | None = Field(default=None, sa_column=Column(JSON))
    enable_general_purpose_subagent: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default=false()),
    )
    llm_params: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class SessionMeta(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str = "新对话"
    agent_id: str = "chat"
    model: str = ""
    user_id: str = Field(default="", index=True)
    parent_session_id: str | None = Field(default=None, index=True)
    tool_call_id: str | None = Field(default=None)
    message_count: int = 0
    is_pinned: bool = False
    pinned_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class ChatUiMessage(SQLModel, table=True):
    __tablename__ = "chat_ui_messages"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    session_id: str = Field(index=True)
    role: str
    content: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    tool_calls: list[dict[str, Any]] | None = Field(default=None, sa_column=Column(JSON))
    usage: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    http_traces: list[dict[str, Any]] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)

`````

--- **end of file: lc_agent/db/models.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/models_auth.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/models_auth.py`

#### 📦 Imports

- `import uuid`
- `from datetime import datetime`
- `from datetime import timezone`
- `from sqlmodel import SQLModel`
- `from sqlmodel import Field`

#### 🏛️ Classes (2)

##### 📌 `class User(SQLModel)`
*Line: 11*

**Class Variables (7):**
- `__tablename__ = 'users'`
- `id: str = Field(default_factory=lambda : str(uuid.uuid4()), primary_key=True)`
- `username: str = Field(index=True, unique=True)`
- `password_hash: str`
- `role: str = 'user'`
- `created_at: datetime = Field(default_factory=utcnow)`
- `updated_at: datetime = Field(default_factory=utcnow)`

##### 📌 `class UserAgentAccess(SQLModel)`
*Line: 22*

**Class Variables (3):**
- `__tablename__ = 'user_agent_access'`
- `user_id: str = Field(primary_key=True)`
- `agent_id: str = Field(primary_key=True)`

#### 🔧 Public Functions (1)

- `def utcnow()`
  - *Line: 7*


---

`````python
import uuid
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


def utcnow():
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    role: str = "user"  # "admin" or "user"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class UserAgentAccess(SQLModel, table=True):
    __tablename__ = "user_agent_access"

    user_id: str = Field(primary_key=True)
    agent_id: str = Field(primary_key=True)

`````

--- **end of file: lc_agent/db/models_auth.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/repository.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/repository.py`

#### 📦 Imports

- `from datetime import datetime`
- `from datetime import timezone`
- `from sqlalchemy import func`
- `from sqlalchemy import select`
- `from sqlalchemy.ext.asyncio import AsyncSession`
- `from lc_agent.db.models import AgentPresetDB`
- `from lc_agent.db.models import ChatUiMessage`
- `from lc_agent.db.models import SessionMeta`

#### 🏛️ Classes (3)

##### 📌 `class PresetRepository`
*Line: 9*

**🔧 Constructor (`__init__`):**
- `def __init__(self, session: AsyncSession)`
  - **Parameters:**
    - `self`
    - `session: AsyncSession`

**Public Methods (5):**
- `async def list_all(self) -> list[AgentPresetDB]`
- `async def get_by_id(self, preset_id: str) -> AgentPresetDB | None`
- `async def create(self, **kwargs) -> AgentPresetDB`
- `async def update(self, preset_id: str, **kwargs) -> AgentPresetDB | None`
- `async def delete(self, preset_id: str) -> bool`

##### 📌 `class SessionRepository`
*Line: 48*

**🔧 Constructor (`__init__`):**
- `def __init__(self, session: AsyncSession)`
  - **Parameters:**
    - `self`
    - `session: AsyncSession`

**Public Methods (6):**
- `async def list_all(self, limit: int = 50, user_id: str | None = None) -> list[SessionMeta]`
- `async def get_by_id(self, session_id: str) -> SessionMeta | None`
- `async def create(self, **kwargs) -> SessionMeta`
- `async def update(self, session_id: str, **kwargs) -> SessionMeta | None`
- `async def delete(self, session_id: str) -> bool`
- `async def increment_messages(self, session_id: str) -> None`

##### 📌 `class ChatUiMessageRepository`
*Line: 104*

**🔧 Constructor (`__init__`):**
- `def __init__(self, session: AsyncSession)`
  - **Parameters:**
    - `self`
    - `session: AsyncSession`

**Public Methods (6):**
- `async def create(self) -> ChatUiMessage`
- `async def list_by_session(self, session_id: str) -> list[ChatUiMessage]`
- `async def get_by_id(self, message_id: str) -> ChatUiMessage | None`
- `async def truncate_from_message(self, session_id: str, message_id: str) -> int`
- `async def get_last_assistant(self, session_id: str) -> ChatUiMessage | None`
- `async def count_by_session(self, session_id: str) -> int`


---

`````python
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lc_agent.db.models import AgentPresetDB, ChatUiMessage, SessionMeta


class PresetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> list[AgentPresetDB]:
        result = await self.session.execute(select(AgentPresetDB).order_by(AgentPresetDB.created_at))
        return list(result.scalars().all())

    async def get_by_id(self, preset_id: str) -> AgentPresetDB | None:
        return await self.session.get(AgentPresetDB, preset_id)

    async def create(self, **kwargs) -> AgentPresetDB:
        preset = AgentPresetDB(**kwargs)
        self.session.add(preset)
        await self.session.commit()
        await self.session.refresh(preset)
        return preset

    async def update(self, preset_id: str, **kwargs) -> AgentPresetDB | None:
        preset = await self.get_by_id(preset_id)
        if preset is None:
            return None
        for key, value in kwargs.items():
            if hasattr(preset, key):
                setattr(preset, key, value)
        preset.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(preset)
        return preset

    async def delete(self, preset_id: str) -> bool:
        preset = await self.get_by_id(preset_id)
        if preset is None:
            return False
        await self.session.delete(preset)
        await self.session.commit()
        return True


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self, limit: int = 50, user_id: str | None = None) -> list[SessionMeta]:
        stmt = select(SessionMeta).where(~SessionMeta.id.contains("--sa--"))
        if user_id:
            stmt = stmt.where(SessionMeta.user_id == user_id)
        stmt = stmt.order_by(SessionMeta.updated_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, session_id: str) -> SessionMeta | None:
        return await self.session.get(SessionMeta, session_id)

    async def create(self, **kwargs) -> SessionMeta:
        sess = SessionMeta(**kwargs)
        self.session.add(sess)
        await self.session.commit()
        await self.session.refresh(sess)
        return sess

    async def update(self, session_id: str, **kwargs) -> SessionMeta | None:
        sess = await self.get_by_id(session_id)
        if sess is None:
            return None

        if "is_pinned" in kwargs:
            is_pinned = bool(kwargs.pop("is_pinned"))
            sess.is_pinned = is_pinned
            sess.pinned_at = datetime.now(timezone.utc) if is_pinned else None

        for key, value in kwargs.items():
            if hasattr(sess, key):
                setattr(sess, key, value)
        sess.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(sess)
        return sess

    async def delete(self, session_id: str) -> bool:
        sess = await self.get_by_id(session_id)
        if sess is None:
            return False
        await self.session.delete(sess)
        await self.session.commit()
        return True

    async def increment_messages(self, session_id: str) -> None:
        sess = await self.get_by_id(session_id)
        if sess:
            sess.message_count += 1
            sess.updated_at = datetime.now(timezone.utc)
            await self.session.commit()


class ChatUiMessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        session_id: str,
        role: str,
        content: list[dict] | None = None,
        tool_calls: list[dict] | None = None,
        usage: dict | None = None,
        http_traces: list[dict] | None = None,
    ) -> ChatUiMessage:
        message = ChatUiMessage(
            session_id=session_id,
            role=role,
            content=content or [],
            tool_calls=tool_calls,
            usage=usage,
            http_traces=http_traces,
        )
        self.session.add(message)
        await self.session.commit()
        try:
            await self.session.refresh(message)
        except Exception:
            pass
        return message

    async def list_by_session(
        self,
        session_id: str,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[ChatUiMessage]:
        stmt = (
            select(ChatUiMessage)
            .where(ChatUiMessage.session_id == session_id)
            .order_by(ChatUiMessage.created_at, ChatUiMessage.id)
        )
        if offset > 0:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, message_id: str) -> ChatUiMessage | None:
        return await self.session.get(ChatUiMessage, message_id)

    async def truncate_from_message(self, session_id: str, message_id: str) -> int:
        anchor = await self.session.get(ChatUiMessage, message_id)
        if anchor is None or anchor.session_id != session_id:
            return 0

        result = await self.session.execute(
            select(ChatUiMessage)
            .where(ChatUiMessage.session_id == session_id)
            .order_by(ChatUiMessage.created_at, ChatUiMessage.id)
        )
        rows = list(result.scalars().all())
        start_idx = next((idx for idx, row in enumerate(rows) if row.id == anchor.id), -1)
        if start_idx < 0:
            return 0

        for row in rows[start_idx:]:
            await self.session.delete(row)
        await self.session.commit()
        return len(rows[start_idx:])

    async def get_last_assistant(self, session_id: str) -> ChatUiMessage | None:
        result = await self.session.execute(
            select(ChatUiMessage)
            .where(ChatUiMessage.session_id == session_id, ChatUiMessage.role == "assistant")
            .order_by(ChatUiMessage.created_at.desc(), ChatUiMessage.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_by_session(self, session_id: str) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(ChatUiMessage).where(ChatUiMessage.session_id == session_id)
        )
        return int(result.scalar_one())

`````

--- **end of file: lc_agent/db/repository.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/__init__.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/__init__.py`

#### 📦 Imports

- `from lc_agent.db.models import AgentPresetDB`
- `from lc_agent.db.models import SessionMeta`
- `from lc_agent.db.engine import get_async_engine`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.engine import init_db`
- `from lc_agent.db.repository import PresetRepository`
- `from lc_agent.db.repository import SessionRepository`


---

`````python
from lc_agent.db.models import AgentPresetDB, SessionMeta
from lc_agent.db.engine import get_async_engine, get_async_session, init_db
from lc_agent.db.repository import PresetRepository, SessionRepository

__all__ = [
    "AgentPresetDB",
    "SessionMeta",
    "get_async_engine",
    "get_async_session",
    "init_db",
    "PresetRepository",
    "SessionRepository",
]

`````

--- **end of file: lc_agent/db/__init__.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/migrations/env.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/migrations/env.py`

#### 📦 Imports

- `import os`
- `from logging.config import fileConfig`
- `from sqlalchemy import engine_from_config`
- `from sqlalchemy import pool`
- `from sqlmodel import SQLModel`
- `from alembic import context`
- `import lc_agent.db.models`
- `from lc_agent.db.models_auth import User`
- `from lc_agent.db.models_auth import UserAgentAccess`

#### 🔧 Public Functions (2)

- `def run_migrations_offline() -> None`
  - *Line: 38*

- `def run_migrations_online() -> None`
  - *Line: 50*


---

`````python
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from alembic import context

import lc_agent.db.models  # noqa: F401  — register all table models
from lc_agent.db.models_auth import User, UserAgentAccess  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def _resolve_url() -> str:
    """Return a *synchronous* database URL for Alembic to use.

    Priority: env-var > alembic -x db_url=... > alembic.ini sqlalchemy.url
    """
    url = (
        os.environ.get("LC_AGENT_DB_URL")
        or config.get_main_option("sqlalchemy.url", "")
    )
    cmd_opts = context.get_x_argument(as_dictionary=True)
    if "db_url" in cmd_opts:
        url = cmd_opts["db_url"]
    # Alembic CLI needs a sync driver; convert aiosqlite → pysqlite
    if "+aiosqlite" in url:
        url = url.replace("+aiosqlite", "")
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=_resolve_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = _resolve_url()

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

`````

--- **end of file: lc_agent/db/migrations/env.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/migrations/versions/20260623_add_http_traces_to_chat_ui_messages.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/migrations/versions/20260623_add_http_traces_to_chat_ui_messages.py`

#### 📝 Module Docstring

`````
add http_traces to chat_ui_messages

Revision ID: 20260623_http_traces
Revises: a342dc61a740
Create Date: 2026-06-23 00:10:00
`````

#### 📦 Imports

- `from typing import Sequence`
- `from typing import Union`
- `from alembic import op`
- `import sqlalchemy as sa`

#### 🔧 Public Functions (2)

- `def upgrade() -> None`
  - *Line: 18*

- `def downgrade() -> None`
  - *Line: 23*


---

`````python
"""add http_traces to chat_ui_messages

Revision ID: 20260623_http_traces
Revises: a342dc61a740
Create Date: 2026-06-23 00:10:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260623_http_traces"
down_revision: Union[str, Sequence[str], None] = "a342dc61a740"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("chat_ui_messages", schema=None) as batch_op:
        batch_op.add_column(sa.Column("http_traces", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("chat_ui_messages", schema=None) as batch_op:
        batch_op.drop_column("http_traces")

`````

--- **end of file: lc_agent/db/migrations/versions/20260623_add_http_traces_to_chat_ui_messages.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/migrations/versions/20260704_add_users.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/migrations/versions/20260704_add_users.py`

#### 📝 Module Docstring

`````
Add users table and user_id to sessions

Revision ID: 20260704_add_users
`````

#### 📦 Imports

- `from alembic import op`
- `import sqlalchemy as sa`

#### 🔧 Public Functions (2)

- `def upgrade() -> None`
  - *Line: 14*

- `def downgrade() -> None`
  - *Line: 37*


---

`````python
"""Add users table and user_id to sessions

Revision ID: 20260704_add_users
"""
from alembic import op
import sqlalchemy as sa

revision = "20260704_add_users"
down_revision = "20260704_drop_dangerous_tools"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "user_agent_access",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("agent_id", sa.String(), primary_key=True),
    )

    with op.batch_alter_table("sessions") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.String(), server_default="", nullable=False))
        batch_op.create_index("ix_sessions_user_id", ["user_id"])


def downgrade() -> None:
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.drop_index("ix_sessions_user_id")
        batch_op.drop_column("user_id")
    op.drop_table("user_agent_access")
    op.drop_index("ix_users_username", "users")
    op.drop_table("users")

`````

--- **end of file: lc_agent/db/migrations/versions/20260704_add_users.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/migrations/versions/20260704_drop_dangerous_tools.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/migrations/versions/20260704_drop_dangerous_tools.py`

#### 📝 Module Docstring

`````
drop dangerous_tools column

Revision ID: 20260704_drop_dangerous_tools
Revises: 20260623_http_traces
Create Date: 2026-07-04 00:00:00
`````

#### 📦 Imports

- `from typing import Sequence`
- `from typing import Union`
- `from alembic import op`
- `import sqlalchemy as sa`

#### 🔧 Public Functions (2)

- `def upgrade() -> None`
  - *Line: 18*

- `def downgrade() -> None`
  - *Line: 23*


---

`````python
"""drop dangerous_tools column

Revision ID: 20260704_drop_dangerous_tools
Revises: 20260623_http_traces
Create Date: 2026-07-04 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260704_drop_dangerous_tools"
down_revision: Union[str, Sequence[str], None] = "20260623_http_traces"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("agent_presets", schema=None) as batch_op:
        batch_op.drop_column("dangerous_tools")


def downgrade() -> None:
    with op.batch_alter_table("agent_presets", schema=None) as batch_op:
        batch_op.add_column(sa.Column("dangerous_tools", sa.JSON(), nullable=True))

`````

--- **end of file: lc_agent/db/migrations/versions/20260704_drop_dangerous_tools.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/migrations/versions/20260706_add_llm_params.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/migrations/versions/20260706_add_llm_params.py`

#### 📝 Module Docstring

`````
Add llm_params to agent_presets

Revision ID: 20260706_add_llm_params
`````

#### 📦 Imports

- `import sqlalchemy as sa`
- `from alembic import op`

#### 🔧 Public Functions (2)

- `def upgrade() -> None`
  - *Line: 14*

- `def downgrade() -> None`
  - *Line: 19*


---

`````python
"""Add llm_params to agent_presets

Revision ID: 20260706_add_llm_params
"""
import sqlalchemy as sa
from alembic import op

revision = "20260706_add_llm_params"
down_revision = "20260704_add_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.add_column(sa.Column("llm_params", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.drop_column("llm_params")

`````

--- **end of file: lc_agent/db/migrations/versions/20260706_add_llm_params.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/migrations/versions/20260707_add_subagent_fields.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/migrations/versions/20260707_add_subagent_fields.py`

#### 📝 Module Docstring

`````
Add subagent_ids and subsession fields

Revision ID: 20260707_subagent_fields
`````

#### 📦 Imports

- `import sqlalchemy as sa`
- `from alembic import op`

#### 🔧 Public Functions (2)

- `def upgrade() -> None`
  - *Line: 14*

- `def downgrade() -> None`
  - *Line: 24*


---

`````python
"""Add subagent_ids and subsession fields

Revision ID: 20260707_subagent_fields
"""
import sqlalchemy as sa
from alembic import op

revision = "20260707_subagent_fields"
down_revision = "20260706_add_llm_params"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.add_column(sa.Column("subagents", sa.JSON(), nullable=True))

    with op.batch_alter_table("sessions") as batch_op:
        batch_op.add_column(sa.Column("parent_session_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("tool_call_id", sa.String(), nullable=True))
        batch_op.create_index("ix_sessions_parent_session_id", ["parent_session_id"])


def downgrade() -> None:
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.drop_index("ix_sessions_parent_session_id")
        batch_op.drop_column("tool_call_id")
        batch_op.drop_column("parent_session_id")

    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.drop_column("subagent_ids")

`````

--- **end of file: lc_agent/db/migrations/versions/20260707_add_subagent_fields.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/migrations/versions/20260708_add_general_purpose_subagent.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/migrations/versions/20260708_add_general_purpose_subagent.py`

#### 📝 Module Docstring

`````
add general purpose subagent flag

Revision ID: 20260708_add_general_purpose_subagent
Revises: 20260707_subagent_fields
Create Date: 2026-07-08
`````

#### 📦 Imports

- `import sqlalchemy as sa`
- `from alembic import op`

#### 🔧 Public Functions (2)

- `def upgrade() -> None`
  - *Line: 18*

- `def downgrade() -> None`
  - *Line: 23*


---

`````python
"""add general purpose subagent flag

Revision ID: 20260708_add_general_purpose_subagent
Revises: 20260707_subagent_fields
Create Date: 2026-07-08
"""

import sqlalchemy as sa
from alembic import op


revision = "20260708_add_general_purpose_subagent"
down_revision = "20260707_subagent_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.add_column(sa.Column("enable_general_purpose_subagent", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.drop_column("enable_general_purpose_subagent")

`````

--- **end of file: lc_agent/db/migrations/versions/20260708_add_general_purpose_subagent.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/migrations/versions/20260710_add_display_name.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/migrations/versions/20260710_add_display_name.py`

#### 📝 Module Docstring

`````
add display_name to agent_presets

Revision ID: 20260710_add_display_name
Revises: 20260708_add_general_purpose_subagent
Create Date: 2026-07-10
`````

#### 📦 Imports

- `import sqlalchemy as sa`
- `from alembic import op`

#### 🔧 Public Functions (2)

- `def upgrade() -> None`
  - *Line: 18*

- `def downgrade() -> None`
  - *Line: 24*


---

`````python
"""add display_name to agent_presets

Revision ID: 20260710_add_display_name
Revises: 20260708_add_general_purpose_subagent
Create Date: 2026-07-10
"""

import sqlalchemy as sa
from alembic import op


revision = "20260710_add_display_name"
down_revision = "20260708_add_general_purpose_subagent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.add_column(sa.Column("display_name", sa.String(), nullable=True))
    op.execute("UPDATE agent_presets SET display_name = name WHERE display_name IS NULL")


def downgrade() -> None:
    with op.batch_alter_table("agent_presets") as batch_op:
        batch_op.drop_column("display_name")

`````

--- **end of file: lc_agent/db/migrations/versions/20260710_add_display_name.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/migrations/versions/20260710_rename_builtin_ids.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/migrations/versions/20260710_rename_builtin_ids.py`

#### 📝 Module Docstring

`````
rename builtin preset ids from __xxx__ to xxx

Revision ID: 20260710_rename_builtin_ids
Revises: 20260710_add_display_name
Create Date: 2026-07-10
`````

#### 📦 Imports

- `from alembic import op`

#### 🔧 Public Functions (2)

- `def upgrade() -> None`
  - *Line: 22*

- `def downgrade() -> None`
  - *Line: 32*


---

`````python
"""rename builtin preset ids from __xxx__ to xxx

Revision ID: 20260710_rename_builtin_ids
Revises: 20260710_add_display_name
Create Date: 2026-07-10
"""

from alembic import op

revision = "20260710_rename_builtin_ids"
down_revision = "20260710_add_display_name"
branch_labels = None
depends_on = None

_RENAME_MAP = [
    ("__chat__", "chat"),
    ("__empty__", "empty"),
    ("__power__", "power"),
]


def upgrade() -> None:
    for old_id, new_id in _RENAME_MAP:
        op.execute(
            f"UPDATE sessions SET agent_id = '{new_id}' WHERE agent_id = '{old_id}'"
        )
        op.execute(
            f"UPDATE user_agent_access SET agent_id = '{new_id}' WHERE agent_id = '{old_id}'"
        )


def downgrade() -> None:
    for old_id, new_id in _RENAME_MAP:
        op.execute(
            f"UPDATE sessions SET agent_id = '{old_id}' WHERE agent_id = '{new_id}'"
        )
        op.execute(
            f"UPDATE user_agent_access SET agent_id = '{old_id}' WHERE agent_id = '{new_id}'"
        )

`````

--- **end of file: lc_agent/db/migrations/versions/20260710_rename_builtin_ids.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/migrations/versions/20260715_chat_content_to_json.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/migrations/versions/20260715_chat_content_to_json.py`

#### 📝 Module Docstring

`````
change chat_ui_messages.content from str to JSON list

Revision ID: 20260715_content_json
Revises: 20260710_rename_builtin_ids
Create Date: 2026-07-15
`````

#### 📦 Imports

- `from alembic import op`
- `import sqlalchemy as sa`

#### 🔧 Public Functions (2)

- `def upgrade() -> None`
  - *Line: 17*

- `def downgrade() -> None`
  - *Line: 30*


---

`````python
"""change chat_ui_messages.content from str to JSON list

Revision ID: 20260715_content_json
Revises: 20260710_rename_builtin_ids
Create Date: 2026-07-15
"""

from alembic import op
import sqlalchemy as sa

revision = "20260715_content_json"
down_revision = "20260710_rename_builtin_ids"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 项目早期无历史包袱，用户已确认清空老数据
    op.execute("DELETE FROM chat_ui_messages")
    # SQLite 不支持 ALTER COLUMN，需要用 batch_alter_table 重建表
    with op.batch_alter_table("chat_ui_messages") as batch_op:
        batch_op.alter_column(
            "content",
            existing_type=sa.String(),
            type_=sa.JSON(),
            existing_nullable=False,
        )


def downgrade() -> None:
    # 降级时也清空数据（list[dict] 数据在 VARCHAR 列中不可读）
    op.execute("DELETE FROM chat_ui_messages")
    with op.batch_alter_table("chat_ui_messages") as batch_op:
        batch_op.alter_column(
            "content",
            existing_type=sa.JSON(),
            type_=sa.String(),
            existing_nullable=False,
        )

`````

--- **end of file: lc_agent/db/migrations/versions/20260715_chat_content_to_json.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/db/migrations/versions/a342dc61a740_initial_schema.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/db/migrations/versions/a342dc61a740_initial_schema.py`

#### 📝 Module Docstring

`````
initial schema

Revision ID: a342dc61a740
Revises: 
Create Date: 2026-06-22 13:55:07.737615
`````

#### 📦 Imports

- `from typing import Sequence`
- `from typing import Union`
- `from alembic import op`
- `import sqlalchemy as sa`
- `import sqlmodel`

#### 🔧 Public Functions (2)

- `def upgrade() -> None`
  - *Line: 22*
  - *Upgrade schema.*

- `def downgrade() -> None`
  - *Line: 66*
  - *Downgrade schema.*


---

`````python
"""initial schema

Revision ID: a342dc61a740
Revises: 
Create Date: 2026-06-22 13:55:07.737615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a342dc61a740'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('agent_presets',
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('system_prompt', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('default_model', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('allowed_tool_groups', sa.JSON(), nullable=True),
    sa.Column('allowed_mcp_servers', sa.JSON(), nullable=True),
    sa.Column('allowed_skills', sa.JSON(), nullable=True),
    sa.Column('dangerous_tools', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('chat_ui_messages',
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('session_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('role', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('tool_calls', sa.JSON(), nullable=True),
    sa.Column('usage', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('chat_ui_messages', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_chat_ui_messages_session_id'), ['session_id'], unique=False)

    op.create_table('sessions',
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('agent_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('model', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('message_count', sa.Integer(), nullable=False),
    sa.Column('is_pinned', sa.Boolean(), nullable=False),
    sa.Column('pinned_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('sessions')
    with op.batch_alter_table('chat_ui_messages', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_chat_ui_messages_session_id'))

    op.drop_table('chat_ui_messages')
    op.drop_table('agent_presets')
    # ### end Alembic commands ###

`````

--- **end of file: lc_agent/db/migrations/versions/a342dc61a740_initial_schema.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/mcp/manager.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/mcp/manager.py`

#### 📦 Imports

- `import asyncio`
- `import os`
- `from dataclasses import dataclass`
- `from dataclasses import field`
- `from typing import Any`
- `from typing import Callable`
- `from mcp import ClientSession`
- `from mcp import StdioServerParameters`
- `from mcp.client.stdio import stdio_client`
- `from mcp import ClientSession`
- `from mcp.client.sse import sse_client`
- `from mcp import ClientSession`
- `from mcp.client.streamable_http import streamable_http_client`
- `from lc_agent.mcp.tool_adapter import create_langchain_tools_from_schemas`
- `from lc_agent.mcp.tool_adapter import create_langchain_tools_from_schemas`

#### 🏛️ Classes (2)

##### 📌 `class McpServerStatus`
*Line: 9*

**Class Variables (9):**
- `name: str`
- `type: str = 'local'`
- `command: str = ''`
- `url: str = ''`
- `enabled: bool = True`
- `status: str = 'disconnected'`
- `tools: list[str] = field(default_factory=list)`
- `tool_schemas: list[dict] = field(default_factory=list)`
- `error: str | None = None`

##### 📌 `class McpManager`
*Line: 30*

**Docstring:**
`````
Manages persistent MCP server connections and tool invocation.
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, config: dict[str, dict], on_state_change: Callable[[], None] | None = None)`
  - **Parameters:**
    - `self`
    - `config: dict[str, dict]`
    - `on_state_change: Callable[[], None] | None = None`

**Public Methods (7):**
- `def get_server(self, name: str) -> McpServerStatus | None`
- `async def connect_all(self)`
  - *Connect to all configured MCP servers (persistent).*
- `async def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> str`
  - *Invoke a tool on a connected MCP server, reconnecting once if needed.*
- `def get_tools_for_server(self, server_name: str) -> list[str]`
  - *Get tool names for a given server.*
- `def get_langchain_tools(self) -> list`
  - *Get all connected MCP tools as LangChain StructuredTools.*
- `def get_filtered_langchain_tools(self, allowed_servers: list[str] | None) -> list`
  - *Get MCP tools filtered by allowed servers (three-value semantics).*
- `async def shutdown(self)`
  - *Clean up all persistent connections.*

**Properties (1):**
- `@property servers -> list[McpServerStatus]`


---

`````python

import asyncio
import os
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class McpServerStatus:
    name: str
    type: str = "local"
    command: str = ""
    url: str = ""
    enabled: bool = True
    status: str = "disconnected"
    tools: list[str] = field(default_factory=list)
    tool_schemas: list[dict] = field(default_factory=list)
    error: str | None = None


def _resolve_server_type(conf: dict) -> str:
    server_type = conf.get("type")
    if server_type:
        return server_type
    if conf.get("url"):
        return "http"
    return "local"


class McpManager:
    """Manages persistent MCP server connections and tool invocation."""

    def __init__(self, config: dict[str, dict], on_state_change: Callable[[], None] | None = None):
        self._config = config
        self._on_state_change = on_state_change
        self._servers: dict[str, McpServerStatus] = {}
        self._sessions: dict[str, Any] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._server_contexts: dict[str, tuple[Any, Any]] = {}

        for name, conf in config.items():
            enabled = conf.get("enabled", True)
            server_type = _resolve_server_type(conf)
            command = conf.get("command", "")
            if isinstance(command, list):
                command = " ".join(command)
            self._servers[name] = McpServerStatus(
                name=name,
                type=server_type,
                command=command,
                url=conf.get("url", ""),
                enabled=enabled,
            )

    @property
    def servers(self) -> list[McpServerStatus]:
        return list(self._servers.values())

    def get_server(self, name: str) -> McpServerStatus | None:
        return self._servers.get(name)

    def _notify_state_change(self) -> None:
        """Notify the owner that MCP state changed without coupling to the engine."""
        if self._on_state_change is None:
            return
        try:
            self._on_state_change()
        except Exception:
            pass

    def _set_server_error(self, name: str, error: str) -> None:
        server = self._servers.get(name)
        if server is None:
            return
        server.status = "error"
        server.error = error
        self._notify_state_change()

    async def _cleanup_server(self, name: str) -> None:
        """Close and forget a single server's persistent connection."""
        self._sessions.pop(name, None)
        self._locks.pop(name, None)
        contexts = self._server_contexts.pop(name, None)
        if contexts is None:
            return

        cm, session_cm = contexts
        try:
            await session_cm.__aexit__(None, None, None)
        except Exception:
            pass
        try:
            await cm.__aexit__(None, None, None)
        except Exception:
            pass

    async def _reconnect_server(self, name: str) -> bool:
        """Reconnect one enabled configured server after a persistent session fails."""
        server = self._servers.get(name)
        conf = self._config.get(name)
        if server is None or conf is None or not server.enabled:
            return False

        await self._cleanup_server(name)
        await self._connect_server(name, conf)
        return name in self._sessions and self._servers[name].status == "connected"

    async def connect_all(self):
        """Connect to all configured MCP servers (persistent)."""
        for name, conf in self._config.items():
            if not conf.get("enabled", True):
                self._servers[name].status = "disabled"
                continue
            await self._connect_server(name, conf)

    async def _connect_server(self, name: str, conf: dict):
        """Establish a persistent connection to a single MCP server."""
        server_type = _resolve_server_type(conf)
        self._servers[name].status = "connecting"

        try:
            if server_type == "sse":
                await self._connect_sse_persistent(name, conf)
            elif server_type == "http":
                await self._connect_http_persistent(name, conf)
            else:
                await self._connect_stdio_persistent(name, conf)
        except Exception as e:
            self._set_server_error(name, str(e))

    async def _connect_stdio_persistent(self, name: str, conf: dict):
        """Keep a stdio MCP server process alive."""
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        command_raw = conf.get("command", "")
        if isinstance(command_raw, list):
            cmd = command_raw[0]
            args = command_raw[1:]
        else:
            cmd = command_raw
            args = conf.get("args", [])

        env = {**os.environ, **conf.get("env", {})}
        params = StdioServerParameters(command=cmd, args=args, env=env)

        cm = stdio_client(params)
        transport = await cm.__aenter__()
        read, write = transport

        session_cm = ClientSession(read, write)
        session = await session_cm.__aenter__()
        await session.initialize()

        self._server_contexts[name] = (cm, session_cm)
        self._sessions[name] = session
        self._extract_tools(name, await session.list_tools())

    async def _connect_sse_persistent(self, name: str, conf: dict):
        """Keep an SSE MCP connection alive."""
        from mcp import ClientSession
        from mcp.client.sse import sse_client

        url = conf.get("url", "")
        if not url:
            raise ValueError(f"SSE server '{name}' requires a 'url' field")

        cm = sse_client(url=url)
        transport = await cm.__aenter__()
        read, write = transport

        session_cm = ClientSession(read, write)
        session = await session_cm.__aenter__()
        await session.initialize()

        self._server_contexts[name] = (cm, session_cm)
        self._sessions[name] = session
        self._extract_tools(name, await session.list_tools())

    async def _connect_http_persistent(self, name: str, conf: dict):
        """Keep a StreamableHTTP MCP connection alive."""
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        url = conf.get("url", "")
        if not url:
            raise ValueError(f"HTTP server '{name}' requires a 'url' field")

        cm = streamable_http_client(url=url)
        transport = await cm.__aenter__()
        read, write = transport[0], transport[1]

        session_cm = ClientSession(read, write)
        session = await session_cm.__aenter__()
        await session.initialize()

        self._server_contexts[name] = (cm, session_cm)
        self._sessions[name] = session
        self._extract_tools(name, await session.list_tools())

    def _extract_tools(self, name: str, tools_result):
        """Extract tool info from list_tools result."""
        tool_names = [t.name for t in tools_result.tools]
        tool_schemas = [
            {
                "name": t.name,
                "description": getattr(t, "description", "") or "",
                "input_schema": getattr(t, "inputSchema", {}) or {},
            }
            for t in tools_result.tools
        ]
        self._servers[name].status = "connected"
        self._servers[name].tools = tool_names
        self._servers[name].tool_schemas = tool_schemas
        self._servers[name].error = None
        self._locks[name] = asyncio.Lock()
        self._notify_state_change()

    async def _call_tool_once(self, server_name: str, tool_name: str, arguments: dict) -> str:
        session = self._sessions.get(server_name)
        if session is None:
            raise RuntimeError(f"MCP server '{server_name}' not connected")

        lock = self._locks.get(server_name)
        if lock:
            async with lock:
                result = await asyncio.wait_for(
                    session.call_tool(tool_name, arguments),
                    timeout=60.0,
                )
        else:
            result = await asyncio.wait_for(
                session.call_tool(tool_name, arguments),
                timeout=60.0,
            )

        parts = []
        for content in result.content:
            if hasattr(content, "text"):
                parts.append(content.text)
            else:
                parts.append(str(content))
        return "\n".join(parts) if parts else "(empty result)"

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> str:
        """Invoke a tool on a connected MCP server, reconnecting once if needed."""
        server = self._servers.get(server_name)
        if server is not None and not server.enabled:
            await self._cleanup_server(server_name)
            server.status = "disabled"
            return f"MCP server '{server_name}' is disabled"

        if self._sessions.get(server_name) is None:
            if server is not None and server_name in self._config:
                if await self._reconnect_server(server_name):
                    try:
                        return await self._call_tool_once(server_name, tool_name, arguments)
                    except Exception as e:
                        self._set_server_error(server_name, str(e))
                        await self._cleanup_server(server_name)
                        return f"MCP tool error after reconnect: {e}"
                reconnect_error = server.error or f"MCP server '{server_name}' not connected"
                return f"MCP server '{server_name}' reconnect failed: {reconnect_error}"
            return f"MCP server '{server_name}' not connected"

        try:
            return await self._call_tool_once(server_name, tool_name, arguments)
        except asyncio.TimeoutError:
            initial_error = f"MCP tool '{tool_name}' timed out after 60s"
        except Exception as e:
            initial_error = f"MCP tool error: {e}"

        self._set_server_error(server_name, initial_error)
        if not await self._reconnect_server(server_name):
            server = self._servers.get(server_name)
            reconnect_error = server.error if server and server.error else initial_error
            return f"MCP server '{server_name}' reconnect failed: {reconnect_error}"

        try:
            return await self._call_tool_once(server_name, tool_name, arguments)
        except asyncio.TimeoutError:
            final_error = f"MCP tool '{tool_name}' timed out after reconnect"
        except Exception as e:
            final_error = f"MCP tool error after reconnect: {e}"

        self._set_server_error(server_name, final_error)
        await self._cleanup_server(server_name)
        return final_error

    def get_tools_for_server(self, server_name: str) -> list[str]:
        """Get tool names for a given server."""
        server = self._servers.get(server_name)
        return server.tools if server else []

    def get_langchain_tools(self) -> list:
        """Get all connected MCP tools as LangChain StructuredTools."""
        from lc_agent.mcp.tool_adapter import create_langchain_tools_from_schemas

        all_tools = []
        for server in self._servers.values():
            if server.enabled and server.status == "connected" and server.tool_schemas:
                invoke_fn = self._make_invoke_fn(server.name)
                tools = create_langchain_tools_from_schemas(server.name, server.tool_schemas, invoke_fn)
                all_tools.extend(tools)
        return all_tools

    def get_filtered_langchain_tools(self, allowed_servers: list[str] | None) -> list:
        """Get MCP tools filtered by allowed servers (three-value semantics)."""
        from lc_agent.mcp.tool_adapter import create_langchain_tools_from_schemas

        all_tools = []
        for server in self._servers.values():
            if not server.enabled or server.status != "connected" or not server.tool_schemas:
                continue
            if allowed_servers is not None and server.name not in allowed_servers:
                continue
            invoke_fn = self._make_invoke_fn(server.name)
            tools = create_langchain_tools_from_schemas(server.name, server.tool_schemas, invoke_fn)
            all_tools.extend(tools)
        return all_tools

    def _make_invoke_fn(self, server_name: str):
        """Create an async invoke function bound to a specific server."""
        async def invoke(tool_name: str, arguments: dict) -> str:
            return await self.call_tool(server_name, tool_name, arguments)
        return invoke

    async def shutdown(self):
        """Clean up all persistent connections."""
        for name in list(self._server_contexts):
            await self._cleanup_server(name)

`````

--- **end of file: lc_agent/mcp/manager.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/mcp/tool_adapter.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/mcp/tool_adapter.py`

#### 📝 Module Docstring

`````
Converts MCP tool schemas into LangChain StructuredTool instances.
`````

#### 📦 Imports

- `from typing import Any`
- `from langchain_core.tools import StructuredTool`
- `from pydantic import BaseModel`
- `from pydantic import Field`
- `from pydantic import create_model`

#### 🔧 Public Functions (2)

- `def create_langchain_tools_from_schemas(server_name: str, tool_schemas: list[dict], invoke_fn: Any = None) -> list[StructuredTool]`
  - *Line: 43*
  - **Docstring:**
  `````
  Convert MCP tool schemas to LangChain StructuredTool list.
  
  Args:
      server_name: MCP server name for namespacing
      tool_schemas: List of {name, description, input_schema}
      invoke_fn: Optional async callable(tool_name, args) -> result
  `````

- `def mcp_tool_names_to_display(server_name: str, tool_names: list[str]) -> list[dict]`
  - *Line: 92*
  - *Convert MCP tool names to display format.*


---

`````python
"""Converts MCP tool schemas into LangChain StructuredTool instances."""

from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model


def _build_pydantic_model(tool_name: str, input_schema: dict) -> type[BaseModel]:
    """Dynamically create a Pydantic model from JSON Schema."""
    properties = input_schema.get("properties", {})
    required = set(input_schema.get("required", []))

    fields: dict[str, Any] = {}
    for prop_name, prop_def in properties.items():
        python_type = _json_type_to_python(prop_def.get("type", "string"))
        description = prop_def.get("description", "")
        if prop_name in required:
            fields[prop_name] = (python_type, Field(description=description))
        else:
            fields[prop_name] = (python_type | None, Field(default=None, description=description))

    if not fields:
        fields["placeholder"] = (str | None, Field(default=None, description="no params"))

    model_name = f"McpInput_{tool_name}"
    return create_model(model_name, **fields)


def _json_type_to_python(json_type: str) -> type:
    """Map JSON Schema type to Python type."""
    mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    return mapping.get(json_type, str)


def create_langchain_tools_from_schemas(
    server_name: str,
    tool_schemas: list[dict],
    invoke_fn: Any = None,
) -> list[StructuredTool]:
    """Convert MCP tool schemas to LangChain StructuredTool list.

    Args:
        server_name: MCP server name for namespacing
        tool_schemas: List of {name, description, input_schema}
        invoke_fn: Optional async callable(tool_name, args) -> result
    """
    tools = []
    for schema in tool_schemas:
        name = schema["name"]
        description = schema.get("description", "")
        input_schema = schema.get("input_schema", {"type": "object", "properties": {}})

        args_model = _build_pydantic_model(name, input_schema)
        full_name = f"mcp__{server_name}__{name}"

        if invoke_fn:
            async def _invoke(invoke=invoke_fn, tool_name=name, **kwargs):
                filtered = {k: v for k, v in kwargs.items() if v is not None}
                return await invoke(tool_name, filtered)

            tool = StructuredTool.from_function(
                func=None,
                coroutine=_invoke,
                name=full_name,
                description=f"[MCP:{server_name}] {description}",
                args_schema=args_model,
            )
        else:
            def _placeholder(full=full_name, **kwargs):
                return f"MCP tool {full} not connected"

            tool = StructuredTool.from_function(
                func=_placeholder,
                name=full_name,
                description=f"[MCP:{server_name}] {description}",
                args_schema=args_model,
            )

        tools.append(tool)

    return tools


def mcp_tool_names_to_display(server_name: str, tool_names: list[str]) -> list[dict]:
    """Convert MCP tool names to display format."""
    return [
        {"name": f"mcp__{server_name}__{name}", "group": f"mcp__{server_name}", "description": f"MCP tool: {name}"}
        for name in tool_names
    ]

`````

--- **end of file: lc_agent/mcp/tool_adapter.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/mcp/__init__.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/mcp/__init__.py`

#### 📦 Imports

- `from lc_agent.mcp.manager import McpManager`


---

`````python
from lc_agent.mcp.manager import McpManager

__all__ = ["McpManager"]

`````

--- **end of file: lc_agent/mcp/__init__.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/app.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/app.py`

#### 📦 Imports

- `import mimetypes`
- `from pathlib import Path`
- `from fastapi import FastAPI`
- `from fastapi.middleware.cors import CORSMiddleware`
- `from fastapi.staticfiles import StaticFiles`
- `from lc_agent import __version__`
- `from lc_agent.server.routes.health import router as health_router`
- `from lc_agent.server.routes.tools import router as tools_router`
- `from lc_agent.server.routes.models import router as models_router`
- `from lc_agent.server.routes.agents import router as agents_router`
- `from lc_agent.server.routes.sessions import router as sessions_router`
- `from lc_agent.server.routes.skills import router as skills_router`
- `from lc_agent.server.routes.mcp import router as mcp_router`
- `from lc_agent.server.routes.settings import router as settings_router`
- `from lc_agent.server.routes.permissions import router as permissions_router`
- `from lc_agent.server.routes.auth import router as auth_router`
- `from lc_agent.server.routes.admin import router as admin_router`
- `from lc_agent.server.sse import router as sse_router`

#### 🔧 Public Functions (2)

- `def create_app(config: dict, lifespan = None) -> FastAPI`
  - *Line: 27*
  - *Create and configure the FastAPI application.*

- `def mount_static_files(app: FastAPI)`
  - *Line: 63*
  - *Mount static files AFTER API routes are registered.*


---

`````python
# lc_agent/server/app.py
import mimetypes
from pathlib import Path

from fastapi import FastAPI

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from lc_agent import __version__
from lc_agent.server.routes.health import router as health_router
from lc_agent.server.routes.tools import router as tools_router
from lc_agent.server.routes.models import router as models_router
from lc_agent.server.routes.agents import router as agents_router
from lc_agent.server.routes.sessions import router as sessions_router
from lc_agent.server.routes.skills import router as skills_router
from lc_agent.server.routes.mcp import router as mcp_router
from lc_agent.server.routes.settings import router as settings_router
from lc_agent.server.routes.permissions import router as permissions_router
from lc_agent.server.routes.auth import router as auth_router
from lc_agent.server.routes.admin import router as admin_router
from lc_agent.server.sse import router as sse_router


def create_app(config: dict, lifespan=None) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="lc_agent",
        version=__version__,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.config = config

    app.include_router(health_router, prefix="/api")
    app.include_router(tools_router, prefix="/api")
    app.include_router(models_router, prefix="/api")
    app.include_router(agents_router, prefix="/api")
    app.include_router(sessions_router, prefix="/api")
    app.include_router(skills_router, prefix="/api")
    app.include_router(mcp_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(permissions_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    app.include_router(sse_router)

    return app


def mount_static_files(app: FastAPI):
    """Mount static files AFTER API routes are registered."""
    web_dist = Path(__file__).parent.parent / "web" / "dist"
    if web_dist.exists():
        app.mount("/", StaticFiles(directory=str(web_dist), html=True), name="frontend")

`````

--- **end of file: lc_agent/server/app.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/auth_middleware.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/auth_middleware.py`

#### 📦 Imports

- `from fastapi import Depends`
- `from fastapi import HTTPException`
- `from fastapi import Request`
- `from sqlalchemy import select`
- `from sqlalchemy.ext.asyncio import AsyncSession`
- `from lc_agent.core.auth import AuthService`
- `from lc_agent.db.models_auth import User`
- `from lc_agent.server.dependencies import get_db_session`

#### 🔧 Public Functions (3)

- `def get_auth_service(request: Request) -> AuthService`
  - *Line: 10*

- `async def get_current_user(request: Request, db: AsyncSession = Depends(get_db_session)) -> User`
  - *Line: 24*
  - *FastAPI dependency: extract and validate JWT, return User object.*

- `async def require_admin(user: User = Depends(get_current_user)) -> User`
  - *Line: 60*
  - *FastAPI dependency: require admin role.*


---

`````python
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lc_agent.core.auth import AuthService
from lc_agent.db.models_auth import User
from lc_agent.server.dependencies import get_db_session


def get_auth_service(request: Request) -> AuthService:
    svc = getattr(request.app.state, "auth_service", None)
    if svc is None:
        raise HTTPException(status_code=500, detail="Auth not configured")
    return svc


def _extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return request.query_params.get("token")


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """FastAPI dependency: extract and validate JWT, return User object."""
    auth_service: AuthService | None = getattr(request.app.state, "auth_service", None)
    if auth_service is None:
        anon = User(
            id="__anonymous__",
            username="anonymous",
            password_hash="",
            role="admin",
        )
        request.state.current_user = anon
        return anon

    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="认证失败")

    payload = auth_service.decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="认证失败")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="认证失败")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="认证失败")
    request.state.current_user = user
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency: require admin role."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    return user

`````

--- **end of file: lc_agent/server/auth_middleware.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/dependencies.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/dependencies.py`

#### 📦 Imports

- `from fastapi import Request`
- `from lc_agent.core.engine import AgentEngine`
- `from lc_agent.db.engine import get_async_session as _get_db_session`
- `from lc_agent.tools.registry import ToolRegistry`

#### 🔧 Public Functions (3)

- `def get_engine(request: Request) -> AgentEngine`
  - *Line: 9*
  - *Dependency to get the AgentEngine from app state.*

- `def get_registry(request: Request) -> ToolRegistry`
  - *Line: 14*
  - *Dependency to get the ToolRegistry singleton.*

- `async def get_db_session(request: Request)`
  - *Line: 19*
  - *Dependency to get an async DB session.*


---

`````python
# lc_agent/server/dependencies.py
from fastapi import Request

from lc_agent.core.engine import AgentEngine
from lc_agent.db.engine import get_async_session as _get_db_session
from lc_agent.tools.registry import ToolRegistry


def get_engine(request: Request) -> AgentEngine:
    """Dependency to get the AgentEngine from app state."""
    return request.app.state.engine


def get_registry(request: Request) -> ToolRegistry:
    """Dependency to get the ToolRegistry singleton."""
    return ToolRegistry()


async def get_db_session(request: Request):
    """Dependency to get an async DB session."""
    db_url = request.app.state.config.get("database", {}).get("url", "sqlite+aiosqlite:///./lc_agent_data.db")
    session = _get_db_session(db_url)
    try:
        yield session
    finally:
        await session.close()

`````

--- **end of file: lc_agent/server/dependencies.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/persistence.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/persistence.py`

#### 📝 Module Docstring

`````
Database persistence operations for chat sessions and messages.

All functions accept db_url as the first argument and are self-contained —
no dependency on the WebSocket handler class.
`````

#### 📦 Imports

- `import logging`
- `from typing import Any`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.repository import SessionRepository`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.repository import SessionRepository`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.repository import SessionRepository`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.repository import SessionRepository`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.repository import ChatUiMessageRepository`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.repository import ChatUiMessageRepository`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.repository import ChatUiMessageRepository`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.repository import ChatUiMessageRepository`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.models import SessionMeta`

#### 🔧 Public Functions (12)

- `async def get_session_message_count(db_url: str, thread_id: str) -> int`
  - *Line: 13*
  - *Get the current message count for a session. Returns 0 if not found.*

- `async def ensure_session(db_url: str, thread_id: str, title: str, agent_id: str, model: str, user_id: str = '') -> None`
  - *Line: 32*
  - *Create session metadata if not exists, or update if exists.*

- `async def increment_session_message_count(db_url: str, thread_id: str) -> None`
  - *Line: 72*
  - *Increment persisted session message count after a completed round.*

- `async def save_title(db_url: str, thread_id: str, title: str) -> None`
  - *Line: 88*
  - *Save title to DB.*

- `async def generate_title(engine: Any, thread_id: str, first_message: str, preset_id: str = 'chat', selected_model_id: str = '') -> str | None`
  - *Line: 104*
  - **Docstring:**
  `````
  Generate title from first message using the agent's model.
  
  Returns the generated title string, or None on failure.
  `````

- `async def save_ui_message(db_url: str, thread_id: str, role: str, content: list[dict[str, Any]]) -> None`
  - *Line: 132*
  - *Persist replay data for the web chat history.*

- `async def truncate_from_message(db_url: str, thread_id: str, message_id: str) -> None`
  - *Line: 165*
  - *Delete persisted UI messages from the edited anchor onward.*

- `async def load_resume_context(db_url: str, thread_id: str) -> tuple[list[dict[str, Any]], int]`
  - *Line: 182*
  - *Load tool_calls and http_traces count from the last assistant message for interrupt continuation.*

- `async def append_to_last_assistant_message(db_url: str, thread_id: str, content: str) -> None`
  - *Line: 201*
  - **Docstring:**
  `````
  Update the last assistant message after interrupt resume.
  
  ``all_tool_calls`` replaces the entire tool_calls array (it already
  contains both pre-interrupt tools with updated statuses and new tools).
  `````

- `async def create_subsession(db_url: str, sub_session_id: str, parent_session_id: str, tool_call_id: str, agent_id: str, title: str, user_id: str = '') -> None`
  - *Line: 255*
  - *Create a sub-session record linked to its parent session.*

- `async def save_subsession_delegation_message(db_url: str, sub_session_id: str, query: str) -> None`
  - *Line: 290*
  - *Insert the synthetic delegation message as the first message in a sub-session.*

- `async def finalize_subsession_message(db_url: str, sub_session_id: str, content: str, tool_calls: list[dict] | None = None, usage: dict | None = None, http_traces: list[dict] | None = None) -> None`
  - *Line: 301*
  - *Save the sub-agent's assistant message and increment message count.*


---

`````python
"""Database persistence operations for chat sessions and messages.

All functions accept db_url as the first argument and are self-contained —
no dependency on the WebSocket handler class.
"""
import logging
from typing import Any


logger = logging.getLogger(__name__)


async def get_session_message_count(db_url: str, thread_id: str) -> int:
    """Get the current message count for a session. Returns 0 if not found."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import SessionRepository

        session = get_async_session(db_url)
        try:
            repo = SessionRepository(session)
            existing = await repo.get_by_id(thread_id)
            if existing is None:
                return 0
            return existing.message_count or 0
        finally:
            await session.close()
    except Exception:
        return 0


async def ensure_session(
    db_url: str,
    thread_id: str,
    title: str,
    agent_id: str,
    model: str,
    user_id: str = "",
) -> None:
    """Create session metadata if not exists, or update if exists."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import SessionRepository

        session = get_async_session(db_url)
        try:
            repo = SessionRepository(session)
            existing = await repo.get_by_id(thread_id)
            if existing is None:
                await repo.create(
                    id=thread_id,
                    title=title or "新对话",
                    agent_id=agent_id,
                    model=model,
                    message_count=0,
                    user_id=user_id,
                )
            else:
                await repo.update(
                    thread_id,
                    title=title or existing.title,
                    agent_id=agent_id,
                    model=model or existing.model,
                )
        finally:
            await session.close()
    except Exception:
        logger.exception("Failed to ensure session %s", thread_id)
        raise


async def increment_session_message_count(db_url: str, thread_id: str) -> None:
    """Increment persisted session message count after a completed round."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import SessionRepository

        session = get_async_session(db_url)
        try:
            await SessionRepository(session).increment_messages(thread_id)
        finally:
            await session.close()
    except Exception:
        logger.exception("Failed to increment message count for session %s", thread_id)
        raise


async def save_title(db_url: str, thread_id: str, title: str) -> None:
    """Save title to DB."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import SessionRepository

        session = get_async_session(db_url)
        try:
            await SessionRepository(session).update(thread_id, title=title)
        finally:
            await session.close()
    except Exception:
        logger.exception("Failed to save title for session %s", thread_id)
        raise


async def generate_title(
    engine: Any,
    thread_id: str,
    first_message: str,
    preset_id: str = "chat",
    selected_model_id: str = "",
) -> str | None:
    """Generate title from first message using the agent's model.

    Returns the generated title string, or None on failure.
    """
    try:
        model_id = selected_model_id
        if preset_id in engine.BUILTIN_IDS:
            for bp in engine.get_builtin_presets():
                if bp.id == preset_id:
                    model_id = model_id or bp.default_model
                    break
        else:
            preset = engine._presets.get(preset_id) or engine._custom_presets.get(preset_id)
            if preset:
                model_id = model_id or preset.default_model
        return await engine.generate_title(first_message, model_id)
    except Exception:
        logger.exception("Title generation failed for session %s", thread_id)
        return None


async def save_ui_message(
    db_url: str,
    thread_id: str,
    role: str,
    content: list[dict[str, Any]],
    *,
    tool_calls: list[dict[str, Any]] | None = None,
    usage: dict[str, Any] | None = None,
    http_traces: list[dict[str, Any]] | None = None,
) -> None:
    """Persist replay data for the web chat history."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import ChatUiMessageRepository

        session = get_async_session(db_url)
        try:
            repo = ChatUiMessageRepository(session)
            await repo.create(
                session_id=thread_id,
                role=role,
                content=content,
                tool_calls=tool_calls,
                usage=usage,
                http_traces=http_traces,
            )
        finally:
            await session.close()
    except Exception:
        logger.exception("Failed to persist UI message for session %s", thread_id)
        raise


async def truncate_from_message(db_url: str, thread_id: str, message_id: str) -> None:
    """Delete persisted UI messages from the edited anchor onward."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import ChatUiMessageRepository

        session = get_async_session(db_url)
        try:
            repo = ChatUiMessageRepository(session)
            await repo.truncate_from_message(thread_id, message_id)
        finally:
            await session.close()
    except Exception:
        logger.exception("Failed to truncate UI messages for session %s", thread_id)
        raise


async def load_resume_context(db_url: str, thread_id: str) -> tuple[list[dict[str, Any]], int]:
    """Load tool_calls and http_traces count from the last assistant message for interrupt continuation."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import ChatUiMessageRepository

        session = get_async_session(db_url)
        try:
            repo = ChatUiMessageRepository(session)
            last_msg = await repo.get_last_assistant(thread_id)
            if last_msg is None:
                return [], 0
            return list(last_msg.tool_calls or []), len(last_msg.http_traces or [])
        finally:
            await session.close()
    except Exception:
        return [], 0


async def append_to_last_assistant_message(
    db_url: str,
    thread_id: str,
    content: str,
    *,
    all_tool_calls: list[dict[str, Any]] | None = None,
    usage_rounds: list[dict] | None = None,
    http_traces: list[dict[str, Any]] | None = None,
    resume_duration_ms: int = 0,
) -> None:
    """Update the last assistant message after interrupt resume.

    ``all_tool_calls`` replaces the entire tool_calls array (it already
    contains both pre-interrupt tools with updated statuses and new tools).
    """
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.repository import ChatUiMessageRepository

        session = get_async_session(db_url)
        try:
            repo = ChatUiMessageRepository(session)
            last_msg = await repo.get_last_assistant(thread_id)
            if last_msg is None:
                return

            if content:
                existing = list(last_msg.content) if isinstance(last_msg.content, list) else []
                if existing and isinstance(existing[-1], dict) and existing[-1].get("type") == "text":
                    existing[-1] = {**existing[-1], "text": (existing[-1].get("text") or "") + content}
                else:
                    existing.append({"type": "text", "text": content})
                last_msg.content = existing
            if all_tool_calls is not None:
                last_msg.tool_calls = all_tool_calls
            if usage_rounds:
                old = last_msg.usage or {}
                last_msg.usage = {
                    **old,
                    "rounds": (old.get("rounds") or []) + usage_rounds,
                    "tool_call_count": len(all_tool_calls or []),
                    "total_duration_ms": (old.get("total_duration_ms") or 0) + resume_duration_ms,
                }
            if http_traces:
                last_msg.http_traces = (last_msg.http_traces or []) + list(http_traces)
            session.add(last_msg)
            await session.commit()
        finally:
            await session.close()
    except Exception:
        logger.exception("Failed to update last assistant message for session %s", thread_id)
        raise


async def create_subsession(
    db_url: str,
    sub_session_id: str,
    parent_session_id: str,
    tool_call_id: str,
    agent_id: str,
    title: str,
    user_id: str = "",
) -> None:
    """Create a sub-session record linked to its parent session."""
    try:
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.models import SessionMeta

        session = get_async_session(db_url)
        try:
            new_session = SessionMeta(
                id=sub_session_id,
                title=title,
                agent_id=agent_id,
                model="",
                user_id=user_id,
                message_count=0,
                parent_session_id=parent_session_id,
                tool_call_id=tool_call_id,
            )
            session.add(new_session)
            await session.commit()
        finally:
            await session.close()
    except Exception:
        logger.exception("Failed to create sub-session %s", sub_session_id)
        raise


async def save_subsession_delegation_message(
    db_url: str,
    sub_session_id: str,
    query: str,
) -> None:
    """Insert the synthetic delegation message as the first message in a sub-session."""
    await save_ui_message(
        db_url, sub_session_id, "system", [{"type": "text", "text": f"委托任务: {query}"}],
    )


async def finalize_subsession_message(
    db_url: str,
    sub_session_id: str,
    content: str,
    tool_calls: list[dict] | None = None,
    usage: dict | None = None,
    http_traces: list[dict] | None = None,
) -> None:
    """Save the sub-agent's assistant message and increment message count."""
    await save_ui_message(
        db_url, sub_session_id, "assistant", [{"type": "text", "text": content}],
        tool_calls=tool_calls,
        usage=usage,
        http_traces=http_traces,
    )
    await increment_session_message_count(db_url, sub_session_id)

`````

--- **end of file: lc_agent/server/persistence.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/sse.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/sse.py`

#### 📝 Module Docstring

`````
SSE streaming endpoints for chat.

Replaces WebSocket communication with POST → SSE streaming + REST control endpoints.
API design aligns with LangGraph /threads/{id}/runs/stream pattern.
`````

#### 📦 Imports

- `import asyncio`
- `import logging`
- `import time`
- `import traceback`
- `from typing import Any`
- `from fastapi import APIRouter`
- `from fastapi import Request`
- `from fastapi.responses import JSONResponse`
- `from fastapi.responses import StreamingResponse`
- `from pydantic import BaseModel`
- `from lc_agent.core.engine import AgentEngine`
- `from lc_agent.core.http_trace import HttpTraceCollector`
- `from lc_agent.core.http_trace import bind_http_trace_collector`
- `from lc_agent.core.http_trace import init_subagent_collector_registry`
- `from lc_agent.core.http_trace import reset_http_trace_collector`
- `from lc_agent.server import persistence`
- `from lc_agent.server import stream_utils`
- `from lc_agent.server.subagent_tracker import SubAgentRunTracker`
- `from lc_agent.utils.loggers import server_logger`
- `from lc_agent.server.auth_middleware import _extract_token`
- `from lc_agent.db.models_auth import User`
- `from sqlalchemy import select`
- `from lc_agent.db.engine import get_async_session`
- `from lc_agent.db.engine import get_async_session as _get_session`
- `from lc_agent.db.models import SessionMeta`
- `from sqlalchemy import select as sa_select`
- `from langgraph.types import Command`
- `from lc_agent.core.memory import AgentRuntimeContext`
- `from lc_agent.core.memory import normalize_memory_user_id`

#### 🏛️ Classes (1)

##### 📌 `class RunStreamRequest(BaseModel)`
*Line: 95*

**Class Variables (7):**
- `input: list[dict[str, Any]] | None = None`
- `command: dict[str, Any] | None = None`
- `preset_id: str = 'chat'`
- `model: str = ''`
- `llm_params: dict[str, Any] | None = None`
- `replace_from_message_id: str | None = None`
- `history: list[dict[str, Any]] | None = None`

#### 🔧 Public Functions (9)

- `def configure(engine: AgentEngine, db_url: str) -> None`
  - *Line: 39*
  - *Initialize the SSE module with engine and DB URL. Called once at app startup.*

- `async def run_stream(thread_id: str, req: RunStreamRequest, request: Request)` `router.post('/{thread_id}/runs/stream')`
  - *Line: 171*
  - *Unified entry: send message or resume interrupt, returning SSE stream.*

- `async def cancel_run(thread_id: str, request: Request)` `router.post('/{thread_id}/runs/cancel')`
  - *Line: 206*
  - *Cancel the currently active run for this thread.*

- `async def get_thread_state(thread_id: str, request: Request, preset_id: str = 'chat', model: str = '')` `router.get('/{thread_id}/state')`
  - *Line: 218*
  - *Check thread state — primarily for pending interrupts.*

- `async def event_stream()`
  - *Line: 316*

- `async def event_stream()`
  - *Line: 542*

- `async def error_stream()`
  - *Line: 264*

- `async def error_stream()`
  - *Line: 304*

- `async def timeout_stream()`
  - *Line: 184*


---

`````python
"""SSE streaming endpoints for chat.

Replaces WebSocket communication with POST → SSE streaming + REST control endpoints.
API design aligns with LangGraph /threads/{id}/runs/stream pattern.
"""

import asyncio
import logging
import time
import traceback
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from lc_agent.core.engine import AgentEngine
from lc_agent.core.http_trace import (
    HttpTraceCollector,
    bind_http_trace_collector,
    init_subagent_collector_registry,
    reset_http_trace_collector,
)
from lc_agent.server import persistence, stream_utils
from lc_agent.server.subagent_tracker import SubAgentRunTracker
from lc_agent.utils.loggers import server_logger

router = APIRouter(prefix="/api/threads", tags=["chat-sse"])

logger = logging.getLogger(__name__)

_cancel_flags: dict[str, bool] = {}
_run_locks: dict[str, asyncio.Lock] = {}

_engine: AgentEngine | None = None
_db_url: str = "sqlite+aiosqlite:///./lc_agent_data.db"


def configure(engine: AgentEngine, db_url: str) -> None:
    """Initialize the SSE module with engine and DB URL. Called once at app startup."""
    global _engine, _db_url
    _engine = engine
    _db_url = db_url


def _get_engine() -> AgentEngine:
    if _engine is None:
        raise RuntimeError("SSE module not configured. Call sse.configure() first.")
    return _engine


def _extract_existing_subsession_ids(tool_calls: list[dict[str, Any]]) -> set[str]:
    return {
        sub_session_id
        for tool_call in tool_calls
        if isinstance((sub_session_id := tool_call.get("sub_session_id")), str) and sub_session_id
    }


def _mark_stale_running_subagent_tool_calls_interrupted(
    tool_calls: list[dict[str, Any]],
    active_subagent_tool_call_ids: set[str],
) -> None:
    for tool_call in tool_calls:
        if not tool_call.get("is_subagent"):
            continue
        if tool_call.get("status") != "running":
            continue
        run_id = tool_call.get("runId") or tool_call.get("run_id")
        if isinstance(run_id, str) and run_id in active_subagent_tool_call_ids:
            continue
        tool_call["status"] = "interrupted"


def _enrich_action_requests_display_names(
    action_requests: list[dict[str, Any]],
    subagent_display_map: dict[str, str],
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for action_request in action_requests:
        args = action_request.get("args")
        subagent_type = args.get("subagent_type") if isinstance(args, dict) else None
        if isinstance(subagent_type, str) and subagent_type in subagent_display_map:
            enriched.append({**action_request, "display_name": subagent_display_map[subagent_type]})
        elif action_request.get("name") in subagent_display_map:
            enriched.append({**action_request, "display_name": subagent_display_map[action_request["name"]]})
        else:
            enriched.append(action_request)
    return enriched


# --- Request Models ---


class RunStreamRequest(BaseModel):
    input: list[dict[str, Any]] | None = None
    command: dict[str, Any] | None = None
    preset_id: str = "chat"
    model: str = ""
    llm_params: dict[str, Any] | None = None
    replace_from_message_id: str | None = None
    history: list[dict[str, Any]] | None = None


# --- Endpoints ---


async def _authenticate_sse(request: Request):
    """Authenticate SSE request. Returns User or None. Returns None if auth not configured."""
    auth_service = getattr(request.app.state, "auth_service", None)
    if auth_service is None:
        return None  # Auth not configured, allow all (backward compat)

    from lc_agent.server.auth_middleware import _extract_token
    token = _extract_token(request)
    if not token:
        return None

    payload = auth_service.decode_token(token)
    if payload is None:
        return None

    from lc_agent.db.models_auth import User
    from sqlalchemy import select
    from lc_agent.db.engine import get_async_session
    db_url = request.app.state.config.get("database", {}).get("url", "sqlite+aiosqlite:///./lc_agent_data.db")
    db = get_async_session(db_url)
    try:
        result = await db.execute(select(User).where(User.id == payload["sub"]))
        return result.scalar_one_or_none()
    finally:
        await db.close()


async def _check_sse_auth(request: Request, thread_id: str) -> JSONResponse | None:
    """Return JSONResponse if access denied, None if allowed."""
    user = await _authenticate_sse(request)
    auth_service = getattr(request.app.state, "auth_service", None)
    if auth_service is not None and user is None:
        return JSONResponse(status_code=401, content={"detail": "认证失败"})

    if user is not None:
        from lc_agent.db.engine import get_async_session as _get_session
        from lc_agent.db.models import SessionMeta
        from sqlalchemy import select as sa_select
        db_url = request.app.state.config.get("database", {}).get("url", "sqlite+aiosqlite:///./lc_agent_data.db")
        _db = _get_session(db_url)
        try:
            result = await _db.execute(sa_select(SessionMeta).where(SessionMeta.id == thread_id))
            session_meta = result.scalar_one_or_none()
            if session_meta:
                # Deny if session has owner and it's not this user
                if session_meta.user_id and session_meta.user_id != user.id and user.role != "admin":
                    return JSONResponse(status_code=403, content={"detail": "权限不足"})
                # For sessions with no owner (user_id=""), only admin can access
                if not session_meta.user_id and user.role != "admin":
                    return JSONResponse(status_code=403, content={"detail": "权限不足"})
        finally:
            await _db.close()

    return None


def _get_lock(thread_id: str) -> asyncio.Lock:
    if thread_id not in _run_locks:
        _run_locks[thread_id] = asyncio.Lock()
    return _run_locks[thread_id]


@router.post("/{thread_id}/runs/stream")
async def run_stream(thread_id: str, req: RunStreamRequest, request: Request):
    """Unified entry: send message or resume interrupt, returning SSE stream."""
    auth_error = await _check_sse_auth(request, thread_id)
    if auth_error is not None:
        return auth_error

    lock = _get_lock(thread_id)
    if lock.locked():
        _cancel_flags[thread_id] = True
        try:
            await asyncio.wait_for(lock.acquire(), timeout=10)
            lock.release()
        except asyncio.TimeoutError:
            async def timeout_stream():
                yield stream_utils.format_sse_event("error", {
                    "title": "请求超时",
                    "detail": "等待前一个请求完成超时，请稍后重试。",
                    "suggestions": ["稍后再次发送消息"],
                    "error_code": "LOCK_TIMEOUT",
                    "tech_detail": "Timed out waiting for previous run to complete",
                    "message": "Timed out waiting for previous run to complete",
                })

            return StreamingResponse(
                timeout_stream(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
            )

    if req.command is not None:
        return await _resume_stream(thread_id, req, request)
    return await _send_stream(thread_id, req, request)


@router.post("/{thread_id}/runs/cancel")
async def cancel_run(thread_id: str, request: Request):
    """Cancel the currently active run for this thread."""
    user = await _authenticate_sse(request)
    auth_service = getattr(request.app.state, "auth_service", None)
    if auth_service is not None and user is None:
        return JSONResponse(status_code=401, content={"detail": "认证失败"})

    _cancel_flags[thread_id] = True
    return {"ok": True, "thread_id": thread_id}


@router.get("/{thread_id}/state")
async def get_thread_state(thread_id: str, request: Request, preset_id: str = "chat", model: str = ""):
    """Check thread state — primarily for pending interrupts."""
    auth_error = await _check_sse_auth(request, thread_id)
    if auth_error is not None:
        return auth_error

    engine = _get_engine()
    agent = engine._get_or_build_agent(preset_id, model)
    if agent is None:
        return {"has_interrupts": False, "error": "agent_not_found"}

    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": engine.recursion_limit}
    try:
        graph_state = await agent.aget_state(config)
        interrupts = []
        if graph_state.tasks:
            for task in graph_state.tasks:
                for intr in (task.interrupts or ()):
                    interrupts.append({
                        "value": intr.value,
                        "id": getattr(intr, "id", None),
                    })
        return {"has_interrupts": bool(interrupts), "interrupts": interrupts}
    except Exception as e:
        return {"has_interrupts": False, "error": str(e)}


# --- Internal Stream Implementations ---


def _extract_text_from_blocks(content: list[dict[str, Any]]) -> str:
    """从 content blocks 提取纯文本（用于标题生成等场景）。"""
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return " ".join(parts)


async def _send_stream(thread_id: str, req: RunStreamRequest, request: Request):
    """Handle new message: save to DB, stream agent response as SSE."""
    engine = _get_engine()
    content = req.input or []

    # 空输入校验
    if not content:
        async def error_stream():
            yield stream_utils.format_sse_event("error", {
                "title": "消息为空",
                "detail": "消息内容不能为空",
                "suggestions": ["请输入文本或附加图片/文件"],
                "error_code": "EMPTY_INPUT",
                "message": "Empty input",
            })

        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    preset_id = req.preset_id
    model_id = req.model
    llm_params = req.llm_params
    lock = _get_lock(thread_id)
    _cancel_flags[thread_id] = False
    user = await _authenticate_sse(request)

    try:
        msg_count = await persistence.get_session_message_count(_db_url, thread_id)
        is_first = msg_count == 0
        if is_first:
            preliminary_title = _extract_text_from_blocks(content)[:30].strip()
            await persistence.ensure_session(
                _db_url, thread_id, preliminary_title, preset_id, model_id,
                user_id=user.id if user else "",
            )

        if req.replace_from_message_id:
            await persistence.truncate_from_message(_db_url, thread_id, req.replace_from_message_id)
            await engine.reset_thread(thread_id)

        await persistence.save_ui_message(_db_url, thread_id, "user", content)
    except Exception as e:
        traceback.print_exc()

        async def error_stream():
            error_info = stream_utils.categorize_error(e)
            error_info["tech_detail"] = str(e)
            error_info["message"] = str(e)
            yield stream_utils.format_sse_event("error", error_info)

        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    async def event_stream():
        nonlocal is_first
        await lock.acquire()
        try:
            usage_rounds: list[dict] = []
            round_start_time = time.time()
            stream_start_time = time.time()
            content_parts: list[str] = []
            tool_calls: list[dict[str, Any]] = []
            in_thinking = False
            last_event_time = time.time()
            active_subagent_tool_call_ids: set[str] = set()
            # Ensure the agent is built (and subagent tools are cached) before streaming
            try:
                engine._get_or_build_agent(preset_id, model_id, llm_params=llm_params)
            except Exception as _e:
                logger.warning("Failed to pre-build agent for subagent tool name lookup: %s", _e)
            subagent_display_map = engine.get_subagent_display_name_map(
                preset_id, model_id=model_id or "", llm_params=llm_params,
            )
            subagent_tool_names = engine.get_subagent_tool_names(
                preset_id, model_id=model_id or "", llm_params=llm_params,
            )
            subagent_tracker = SubAgentRunTracker(
                db_url=_db_url,
                parent_thread_id=thread_id,
                user_id=user.id if user else "",
                subagent_display_map=subagent_display_map,
                tool_calls=tool_calls,
            )

            # Initialize sub-agent HTTP trace collector registry for this stream
            init_subagent_collector_registry()

            if is_first:
                preliminary_title = _extract_text_from_blocks(content)[:30].strip()
                yield stream_utils.format_sse_event("title_update", {
                    "thread_id": thread_id,
                    "title": preliminary_title,
                })

            stream_kwargs: dict[str, Any] = {}
            if model_id:
                stream_kwargs["model_id"] = model_id
            if llm_params:
                stream_kwargs["llm_params"] = llm_params
            if req.replace_from_message_id:
                stream_kwargs["history"] = req.history or []

            model_info = engine._find_model(model_id) if model_id else None
            provider = model_info.provider if model_info else None
            resolved_model = model_info.id if model_info else model_id
            trace_collector = HttpTraceCollector(provider=provider, model=resolved_model)
            trace_token = bind_http_trace_collector(trace_collector)

            try:
                stream = engine.chat_stream(
                    content,
                    thread_id,
                    preset_id,
                    user_id=user.id if user else "anonymous",
                    **stream_kwargs,
                )
                async for event in stream:
                    if _cancel_flags.get(thread_id):
                        for evt_type, evt_data in subagent_tracker.finalize_open_runs(status="cancelled"):
                            yield stream_utils.format_sse_event(evt_type, evt_data)
                        await subagent_tracker.drain()
                        yield stream_utils.format_sse_event("cancelled", {})
                        return

                    if await request.is_disconnected():
                        _cancel_flags[thread_id] = True
                        for evt_type, evt_data in subagent_tracker.finalize_open_runs(status="cancelled"):
                            yield stream_utils.format_sse_event(evt_type, evt_data)
                        await subagent_tracker.drain()
                        return

                    in_thinking = stream_utils.accumulate_display_state(
                        event, content_parts, tool_calls, in_thinking,
                        subagent_tool_names=subagent_tool_names,
                        thread_id=thread_id,
                        subagent_display_map=subagent_display_map,
                        active_subagent_tool_call_ids=active_subagent_tool_call_ids,
                    )

                    for evt_type, evt_data in stream_utils.convert_stream_event(
                        event,
                        subagent_tool_names=subagent_tool_names,
                        subagent_display_map=subagent_display_map,
                        active_subagent_tool_call_ids=active_subagent_tool_call_ids,
                    ):
                        if evt_type == "subagent_start":
                            tool_call_id = evt_data.get("tool_call_id")
                            if isinstance(tool_call_id, str):
                                active_subagent_tool_call_ids.add(tool_call_id)
                        elif evt_type == "subagent_done":
                            tool_call_id = evt_data.get("tool_call_id")
                            if isinstance(tool_call_id, str):
                                active_subagent_tool_call_ids.discard(tool_call_id)
                        evt_type, evt_data = subagent_tracker.handle_event(evt_type, evt_data)
                        yield stream_utils.format_sse_event(evt_type, evt_data)
                        last_event_time = time.time()

                    prev_len = len(usage_rounds)
                    stream_utils.accumulate_usage(event, usage_rounds)
                    if len(usage_rounds) > prev_len:
                        usage_rounds[-1]["duration_ms"] = int((time.time() - round_start_time) * 1000)
                        round_start_time = time.time()
                        yield stream_utils.format_sse_event("llm_usage", usage_rounds[-1])

                    if time.time() - last_event_time > 15:
                        yield stream_utils.SSE_HEARTBEAT
                        last_event_time = time.time()
            finally:
                if in_thinking:
                    content_parts.append("<!--THINK_END-->")
                reset_http_trace_collector(trace_token)

            interrupt_sent = False
            try:
                agent = engine._get_or_build_agent(preset_id, model_id, llm_params=llm_params)
                state_config = {"configurable": {"thread_id": thread_id}, "recursion_limit": engine.recursion_limit}
                graph_state = await agent.aget_state(state_config)
                if graph_state.tasks:
                    all_interrupts = []
                    for task in graph_state.tasks:
                        for intr in (task.interrupts or ()):
                            all_interrupts.append({
                                "value": intr.value,
                                "id": getattr(intr, "id", None),
                            })
                    if all_interrupts:
                        interrupt_payload: dict[str, Any] = {
                            "message": "Tool requires approval",
                            "data": all_interrupts,
                        }
                        first_value = all_interrupts[0].get("value")
                        if isinstance(first_value, dict):
                            if "action_requests" in first_value:
                                reqs = first_value["action_requests"]
                                # Enrich with display_name for sub-agent tools
                                if subagent_display_map:
                                    reqs = _enrich_action_requests_display_names(reqs, subagent_display_map)
                                interrupt_payload["action_requests"] = reqs
                            if "review_configs" in first_value:
                                interrupt_payload["review_configs"] = first_value["review_configs"]
                        yield stream_utils.format_sse_event("interrupt", interrupt_payload)
                        interrupt_sent = True
            except Exception:
                server_logger.exception("Failed to check interrupt state")

            http_traces = trace_collector.snapshot()
            if http_traces:
                for i in range(len(http_traces)):
                    marker = f"\n<!--HTTP:{i}-->\n"
                    content_parts.append(marker)
                    yield stream_utils.format_sse_event("content", {"content": marker})

            done_payload: dict[str, Any] = {}
            if usage_rounds:
                done_payload["usage"] = usage_rounds
            if http_traces:
                done_payload["http_traces"] = http_traces

            await subagent_tracker.drain()

            if content_parts or tool_calls or usage_rounds or http_traces:
                await persistence.save_ui_message(
                    _db_url, thread_id, "assistant",
                    [{"type": "text", "text": "".join(content_parts)}],
                    tool_calls=tool_calls or None,
                    usage={
                        "rounds": usage_rounds,
                        "tool_call_count": len(tool_calls),
                        "total_duration_ms": int((time.time() - stream_start_time) * 1000),
                    },
                    http_traces=http_traces or None,
                )

            yield stream_utils.format_sse_event("done", done_payload)

            asyncio.create_task(persistence.increment_session_message_count(_db_url, thread_id))

            if is_first:
                asyncio.create_task(
                    _generate_and_yield_title(thread_id, _extract_text_from_blocks(content), preset_id, model_id)
                )

        except Exception as e:
            traceback.print_exc()
            if "subagent_tracker" in locals():
                for evt_type, evt_data in subagent_tracker.finalize_open_runs(status="error"):
                    yield stream_utils.format_sse_event(evt_type, evt_data)
                await subagent_tracker.drain()
            error_info = stream_utils.categorize_error(e)
            error_info["tech_detail"] = str(e)
            error_info["message"] = str(e)
            yield stream_utils.format_sse_event("error", error_info)
        finally:
            lock.release()
            _cancel_flags.pop(thread_id, None)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _resume_stream(thread_id: str, req: RunStreamRequest, request: Request):
    """Handle interrupt resume: stream continued agent response as SSE."""
    engine = _get_engine()
    preset_id = req.preset_id
    model_id = req.model
    llm_params = req.llm_params
    lock = _get_lock(thread_id)
    _cancel_flags[thread_id] = False
    user = await _authenticate_sse(request)

    resume_value = req.command.get("resume", {}) if req.command else {}

    async def event_stream():
        await lock.acquire()
        try:
            usage_rounds: list[dict] = []
            round_start_time = time.time()
            stream_start_time = time.time()
            content_parts: list[str] = []
            in_thinking = False
            last_event_time = time.time()
            active_subagent_tool_call_ids: set[str] = set()

            existing_tool_calls, existing_trace_count = await persistence.load_resume_context(_db_url, thread_id)
            tool_calls: list[dict[str, Any]] = list(existing_tool_calls)
            # Ensure the agent is built (and subagent tools are cached) before streaming
            try:
                engine._get_or_build_agent(preset_id, model_id, llm_params=llm_params)
            except Exception as _e:
                logger.warning("Failed to pre-build agent for subagent tool name lookup: %s", _e)
            subagent_display_map = engine.get_subagent_display_name_map(
                preset_id, model_id=model_id or "", llm_params=llm_params,
            )
            subagent_tool_names = engine.get_subagent_tool_names(
                preset_id, model_id=model_id or "", llm_params=llm_params,
            )
            subagent_tracker = SubAgentRunTracker(
                db_url=_db_url,
                parent_thread_id=thread_id,
                user_id=user.id if user else "",
                subagent_display_map=subagent_display_map,
                tool_calls=tool_calls,
                existing_subsession_ids=_extract_existing_subsession_ids(tool_calls),
            )
            from langgraph.types import Command

            agent = engine._get_or_build_agent(preset_id, model_id, llm_params=llm_params)
            if agent is None:
                yield stream_utils.format_sse_event("error", {
                    "title": "缺少 AI 代理配置",
                    "detail": "没有找到用于恢复对话的 AI 代理配置，可能是配置已变更。",
                    "suggestions": ["刷新页面后重试", "重新选择 AI 助手并开始新对话"],
                    "error_code": "AGENT_NOT_FOUND",
                    "tech_detail": "No agent found for resume",
                })
                return

            config = {"configurable": {"thread_id": thread_id}, "recursion_limit": engine.recursion_limit}

            model_info = engine._find_model(model_id) if model_id else None
            provider = model_info.provider if model_info else None
            resolved_model = model_info.id if model_info else model_id
            trace_collector = HttpTraceCollector(
                provider=provider, model=resolved_model, seq_offset=existing_trace_count,
            )
            trace_token = bind_http_trace_collector(trace_collector)

            try:
                stream_kwargs: dict[str, Any] = {"config": config, "version": "v2"}
                if engine._should_use_memory_context(preset_id):
                    from lc_agent.core.memory import AgentRuntimeContext, normalize_memory_user_id

                    stream_kwargs["context"] = AgentRuntimeContext(
                        user_id=normalize_memory_user_id(user.id if user else "anonymous"),
                    )
                async for event in agent.astream_events(
                    Command(resume=resume_value),
                    **stream_kwargs,
                ):
                    if _cancel_flags.get(thread_id):
                        for evt_type, evt_data in subagent_tracker.finalize_open_runs(status="cancelled"):
                            yield stream_utils.format_sse_event(evt_type, evt_data)
                        await subagent_tracker.drain()
                        yield stream_utils.format_sse_event("cancelled", {})
                        return

                    if await request.is_disconnected():
                        _cancel_flags[thread_id] = True
                        for evt_type, evt_data in subagent_tracker.finalize_open_runs(status="cancelled"):
                            yield stream_utils.format_sse_event(evt_type, evt_data)
                        await subagent_tracker.drain()
                        return

                    in_thinking = stream_utils.accumulate_display_state(
                        event, content_parts, tool_calls, in_thinking,
                        subagent_tool_names=subagent_tool_names,
                        thread_id=thread_id,
                        subagent_display_map=subagent_display_map,
                        active_subagent_tool_call_ids=active_subagent_tool_call_ids,
                    )

                    for evt_type, evt_data in stream_utils.convert_stream_event(
                        event,
                        subagent_tool_names=subagent_tool_names,
                        subagent_display_map=subagent_display_map,
                        active_subagent_tool_call_ids=active_subagent_tool_call_ids,
                    ):
                        if evt_type == "subagent_start":
                            tool_call_id = evt_data.get("tool_call_id")
                            if isinstance(tool_call_id, str):
                                active_subagent_tool_call_ids.add(tool_call_id)
                        elif evt_type == "subagent_done":
                            tool_call_id = evt_data.get("tool_call_id")
                            if isinstance(tool_call_id, str):
                                active_subagent_tool_call_ids.discard(tool_call_id)
                        evt_type, evt_data = subagent_tracker.handle_event(evt_type, evt_data)
                        yield stream_utils.format_sse_event(evt_type, evt_data)
                        last_event_time = time.time()

                    prev_len = len(usage_rounds)
                    stream_utils.accumulate_usage(event, usage_rounds)
                    if len(usage_rounds) > prev_len:
                        usage_rounds[-1]["duration_ms"] = int((time.time() - round_start_time) * 1000)
                        round_start_time = time.time()
                        yield stream_utils.format_sse_event("llm_usage", usage_rounds[-1])

                    if time.time() - last_event_time > 15:
                        yield stream_utils.SSE_HEARTBEAT
                        last_event_time = time.time()
            finally:
                if in_thinking:
                    content_parts.append("<!--THINK_END-->")
                reset_http_trace_collector(trace_token)

            interrupt_sent = False
            try:
                graph_state = await agent.aget_state(config)
                if graph_state.tasks:
                    all_interrupts = []
                    for task in graph_state.tasks:
                        for intr in (task.interrupts or ()):
                            all_interrupts.append({
                                "value": intr.value,
                                "id": getattr(intr, "id", None),
                            })
                    if all_interrupts:
                        interrupt_payload: dict[str, Any] = {
                            "message": "Tool requires approval",
                            "data": all_interrupts,
                        }
                        first_value = all_interrupts[0].get("value")
                        if isinstance(first_value, dict):
                            if "action_requests" in first_value:
                                reqs = first_value["action_requests"]
                                if subagent_display_map:
                                    reqs = _enrich_action_requests_display_names(reqs, subagent_display_map)
                                interrupt_payload["action_requests"] = reqs
                            if "review_configs" in first_value:
                                interrupt_payload["review_configs"] = first_value["review_configs"]
                        yield stream_utils.format_sse_event("interrupt", interrupt_payload)
                        interrupt_sent = True
            except Exception as e:
                server_logger.exception("Failed to check interrupt state after resume")

            if isinstance(resume_value, dict):
                permanently_allow = resume_value.get("permanently_allow")
                if permanently_allow and hasattr(request.app.state, "permissions"):
                    # Only admin can permanently allow tools
                    if user and user.role == "admin":
                        request.app.state.permissions.allow_tool(permanently_allow)

            _mark_stale_running_subagent_tool_calls_interrupted(
                tool_calls,
                active_subagent_tool_call_ids,
            )

            http_traces = trace_collector.snapshot()
            if http_traces:
                for i in range(len(http_traces)):
                    marker = f"\n<!--HTTP:{existing_trace_count + i}-->\n"
                    content_parts.append(marker)
                    yield stream_utils.format_sse_event("content", {"content": marker})
            done_payload: dict[str, Any] = {"is_resume": True}
            if usage_rounds:
                done_payload["usage"] = usage_rounds
            if http_traces:
                done_payload["http_traces"] = http_traces

            await subagent_tracker.drain()

            new_content = "".join(content_parts)
            if new_content or tool_calls or usage_rounds or http_traces:
                await persistence.append_to_last_assistant_message(
                    _db_url, thread_id, new_content,
                    all_tool_calls=tool_calls or None,
                    usage_rounds=usage_rounds or None,
                    http_traces=http_traces or None,
                    resume_duration_ms=int((time.time() - stream_start_time) * 1000),
                )

            yield stream_utils.format_sse_event("done", done_payload)

        except Exception as e:
            traceback.print_exc()
            if "subagent_tracker" in locals():
                for evt_type, evt_data in subagent_tracker.finalize_open_runs(status="error"):
                    yield stream_utils.format_sse_event(evt_type, evt_data)
                await subagent_tracker.drain()
            error_info = stream_utils.categorize_error(e)
            error_info["tech_detail"] = str(e)
            error_info["message"] = str(e)
            yield stream_utils.format_sse_event("error", error_info)
        finally:
            lock.release()
            _cancel_flags.pop(thread_id, None)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _generate_and_yield_title(
    thread_id: str,
    first_message: str,
    preset_id: str,
    model_id: str,
) -> None:
    """Background task: generate title and save to DB.

    Note: since the SSE stream is already closed by the time this runs,
    the title update will be delivered on the next state query or page refresh.
    """
    engine = _get_engine()
    title = await persistence.generate_title(engine, thread_id, first_message, preset_id, model_id)
    if title:
        await persistence.save_title(_db_url, thread_id, title)

`````

--- **end of file: lc_agent/server/sse.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/stream_utils.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/stream_utils.py`

#### 📝 Module Docstring

`````
SSE stream event processing utilities.

Converts LangGraph astream_events v2 events into SSE-friendly tuples,
accumulates display state and token usage for persistence.
`````

#### 📦 Imports

- `import json`
- `import time`
- `from typing import Any`

#### 🔧 Public Functions (5)

- `def format_sse_event(event_type: str, data: dict) -> str`
  - *Line: 82*
  - **Docstring:**
  `````
  Format a single SSE event frame.
  
  Returns a string like:
      event: token
      data: {"type":"token","content":"hello"}
  `````

- `def convert_stream_event(event: dict, subagent_tool_names: set[str] | None = None, subagent_display_map: dict[str, str] | None = None, active_subagent_tool_call_ids: set[str] | None = None) -> list[tuple[str, dict]]`
  - *Line: 97*
  - **Docstring:**
  `````
  Convert an astream_events v2 event into SSE event tuples.
  
  Returns a list of (event_type, payload_dict) for each client-visible
  event produced by this single LangGraph event. May return an empty list
  if the event has no client-visible representation.
  `````

- `def accumulate_display_state(event: dict, content_parts: list[str], tool_calls: list[dict[str, Any]], in_thinking: bool, subagent_tool_names: set[str] | None = None, thread_id: str | None = None, subagent_display_map: dict[str, str] | None = None, active_subagent_tool_call_ids: set[str] | None = None) -> bool`
  - *Line: 241*
  - **Docstring:**
  `````
  Mirror the client display markers so history can replay the same layout.
  
  Mutates content_parts and tool_calls in place. Returns updated in_thinking flag.
  `````

- `def accumulate_usage(event: dict, usage_rounds: list[dict]) -> None`
  - *Line: 391*
  - **Docstring:**
  `````
  Extract token usage from on_chat_model_end events.
  
  Appends a usage dict to usage_rounds if the event is on_chat_model_end.
  Sub-agent LLM calls are skipped — they belong to the sub-session.
  `````

- `def categorize_error(error: Exception) -> dict`
  - *Line: 455*
  - *Categorize an exception into structured Chinese error info for the frontend.*


---

`````python
"""SSE stream event processing utilities.

Converts LangGraph astream_events v2 events into SSE-friendly tuples,
accumulates display state and token usage for persistence.
"""

import json
import time
from typing import Any


def _get_checkpoint_ns(event: dict) -> str:
    """Return the langgraph_checkpoint_ns metadata string (empty = main agent)."""
    return event.get("metadata", {}).get("langgraph_checkpoint_ns", "")


def _extract_subagent_tool_call_id(checkpoint_ns: str) -> str | None:
    """Return tool_call_id if this event is INSIDE a sub-agent's execution.

    Sub-agents inherit the parent's checkpoint_ns and append their own layers,
    producing a multi-segment namespace separated by "|":
      - Main agent tool execution:   "tools:{task_uuid}"          (single segment)
      - Sub-agent internal event:    "tools:{task_uuid}|agent"    (multiple segments)
      - Sub-agent internal tool:     "tools:{uuid}|...|tools:{uuid2}" (multiple segments)

    Returns None for single-segment namespaces (main-agent-level events).
    Returns the task_uuid from the first "tools:" segment when multi-segment.
    """
    segments = checkpoint_ns.split("|")
    if len(segments) <= 1:
        # Single segment: main-agent-level event — NOT inside a sub-agent
        return None
    # Multiple segments: we are executing inside a sub-agent graph
    for seg in segments:
        if seg.startswith("tools:"):
            return seg.split(":", 1)[1]
    return None


def _extract_tools_task_id(checkpoint_ns: str) -> str | None:
    """Extract the LangGraph task UUID from the first 'tools:{uuid}' segment.

    Unlike _extract_subagent_tool_call_id, this works for both single-segment
    (main-agent tool call) and multi-segment (sub-agent internal) namespaces.
    Used to build the sub_thread_id key that matches engine.py.
    """
    for seg in checkpoint_ns.split("|"):
        if seg.startswith("tools:"):
            return seg.split(":", 1)[1]
    return None


def _extract_task_subagent_type(tool_name: str, tool_input: Any, subagent_tool_names: set[str] | None) -> str | None:
    if not subagent_tool_names or tool_name not in subagent_tool_names:
        return None
    if tool_name != "task":
        return tool_name
    if not isinstance(tool_input, dict):
        return None
    subagent_type = tool_input.get("subagent_type")
    if not isinstance(subagent_type, str) or not subagent_type.strip():
        return None
    return subagent_type.strip()


def _is_subagent_tool_end(
    tool_name: str,
    tool_input: Any,
    subagent_tool_names: set[str] | None,
    active_subagent_tool_call_ids: set[str] | None,
    tool_call_id: str,
) -> bool:
    if not subagent_tool_names or tool_name not in subagent_tool_names:
        return False
    if tool_name != "task":
        return True
    if isinstance(tool_input, dict) and tool_input:
        return _extract_task_subagent_type(tool_name, tool_input, subagent_tool_names) is not None
    return bool(active_subagent_tool_call_ids and tool_call_id in active_subagent_tool_call_ids)


def format_sse_event(event_type: str, data: dict) -> str:
    """Format a single SSE event frame.

    Returns a string like:
        event: token
        data: {"type":"token","content":"hello"}

    """
    payload = json.dumps({"type": event_type, **data}, ensure_ascii=False)
    return f"event: {event_type}\ndata: {payload}\n\n"


SSE_HEARTBEAT = ": heartbeat\n\n"


def convert_stream_event(
    event: dict,
    subagent_tool_names: set[str] | None = None,
    subagent_display_map: dict[str, str] | None = None,
    active_subagent_tool_call_ids: set[str] | None = None,
) -> list[tuple[str, dict]]:
    """Convert an astream_events v2 event into SSE event tuples.

    Returns a list of (event_type, payload_dict) for each client-visible
    event produced by this single LangGraph event. May return an empty list
    if the event has no client-visible representation.
    """
    results: list[tuple[str, dict]] = []
    checkpoint_ns = _get_checkpoint_ns(event)
    sa_tool_call_id = _extract_subagent_tool_call_id(checkpoint_ns)
    is_in_subagent = sa_tool_call_id is not None
    kind = event.get("event", "")

    if kind == "on_chat_model_stream":
        chunk = event.get("data", {}).get("chunk")
        if chunk:
            additional = getattr(chunk, "additional_kwargs", None) or {}
            reasoning = additional.get("reasoning_content") or additional.get("reasoning")
            text = ""
            if hasattr(chunk, "content") and chunk.content:
                content = chunk.content
                if isinstance(content, list):
                    content = "".join(
                        p.get("text", "") if isinstance(p, dict) else str(p) for p in content
                    )
                text = content
            if is_in_subagent:
                if reasoning:
                    results.append(("subagent_thinking", {"tool_call_id": sa_tool_call_id, "content": reasoning}))
                if text:
                    results.append(("subagent_token", {"tool_call_id": sa_tool_call_id, "content": text}))
            else:
                if reasoning:
                    results.append(("thinking", {"content": reasoning}))
                if text:
                    results.append(("token", {"content": text}))

    elif kind == "on_tool_start":
        tool_name = event.get("name", "")
        tool_input = event.get("data", {}).get("input", {})
        if not isinstance(tool_input, (dict, list, str, int, float, bool, type(None))):
            tool_input = str(tool_input)
        # NOTE: LangGraph's ToolNode runs ALL tools inside "tools:{tc_id}" checkpoint_ns,
        # so is_in_subagent is True even for the main agent calling a sub-agent tool.
        # We MUST check by tool name first to correctly classify sub-agent invocations.
        subagent_type = _extract_task_subagent_type(tool_name, tool_input, subagent_tool_names)
        if subagent_type:
            # Main agent calling a sub-agent tool (is_in_subagent is False here
            # because the main-agent ToolNode has a single-segment checkpoint_ns).
            # Use _extract_tools_task_id (works for single-segment too) to get the
            # LangGraph task UUID, which matches the tc_id engine.py registers.
            tool_input_dict = tool_input if isinstance(tool_input, dict) else {}
            sa_tc_id = (
                _extract_tools_task_id(checkpoint_ns)  # LangGraph task UUID (single-segment OK)
                or event.get("run_id", "")             # fallback
            )
            display_args = (
                {k: v for k, v in tool_input_dict.items() if k != "tool_call_id"}
                if isinstance(tool_input, dict) else tool_input
            )
            display_name = (subagent_display_map or {}).get(subagent_type, subagent_type)
            query = ""
            if isinstance(tool_input_dict, dict):
                query = str(tool_input_dict.get("description") or tool_input_dict.get("query") or tool_input)
            else:
                query = str(tool_input)
            results.append(("tool_call", {
                "name": display_name,
                "run_id": sa_tc_id,
                "args": display_args,
                "is_subagent": True,
            }))
            start_payload = {
                "name": display_name,
                "tool_call_id": sa_tc_id,
                "query": query,
            }
            if subagent_type:
                start_payload["subagent_type"] = subagent_type
            results.append(("subagent_start", start_payload))
        elif is_in_subagent:
            # Sub-agent calling its own internal tool
            results.append(("subagent_tool_call", {
                "tool_call_id": sa_tool_call_id,
                "name": tool_name,
                "args": tool_input,
            }))
        else:
            # Regular main-agent tool call
            results.append(("tool_call", {
                "name": tool_name,
                "run_id": event.get("run_id", ""),
                "args": tool_input,
            }))

    elif kind == "on_tool_end":
        tool_name = event.get("name", "")
        tool_call_id = _extract_tools_task_id(checkpoint_ns) or event.get("run_id", "")
        output = event.get("data", {}).get("output", "")
        if hasattr(output, "content"):
            result_str = output.content if isinstance(output.content, str) else str(output.content)
        else:
            result_str = str(output)
        tool_input = event.get("data", {}).get("input", {})
        if _is_subagent_tool_end(tool_name, tool_input, subagent_tool_names, active_subagent_tool_call_ids, tool_call_id):
            # Main agent's sub-agent tool finished (single-segment checkpoint_ns)
            sa_tc_id_end = (
                _extract_tools_task_id(checkpoint_ns)  # LangGraph task UUID (matches on_tool_start)
                or event.get("run_id", "")             # fallback
            )
            is_error = result_str.startswith("[Sub-agent error:")
            status = "error" if is_error else "done"
            results.append(("subagent_done", {
                "tool_call_id": sa_tc_id_end,
                "result_preview": result_str[:150],
                "status": status,
                "is_error": is_error,
            }))
        elif is_in_subagent:
            # Sub-agent's internal tool finished
            is_error = result_str.startswith("[Tool error:") or result_str.startswith("Tool error:")
            status = "error" if is_error else "done"
            results.append(("subagent_tool_result", {
                "tool_call_id": sa_tool_call_id,
                "name": tool_name,
                "result": result_str,
                "status": status,
                "is_error": is_error,
            }))
        else:
            # Regular main-agent tool finished
            results.append(("tool_result", {
                "name": tool_name,
                "result": result_str,
            }))

    return results


def accumulate_display_state(
    event: dict,
    content_parts: list[str],
    tool_calls: list[dict[str, Any]],
    in_thinking: bool,
    subagent_tool_names: set[str] | None = None,
    thread_id: str | None = None,
    subagent_display_map: dict[str, str] | None = None,
    active_subagent_tool_call_ids: set[str] | None = None,
) -> bool:
    """Mirror the client display markers so history can replay the same layout.

    Mutates content_parts and tool_calls in place. Returns updated in_thinking flag.
    """
    kind = event.get("event", "")
    checkpoint_ns = _get_checkpoint_ns(event)
    sa_tool_call_id = _extract_subagent_tool_call_id(checkpoint_ns)
    is_in_subagent = sa_tool_call_id is not None

    if kind == "on_chat_model_stream":
        chunk = event.get("data", {}).get("chunk")
        if not chunk:
            return in_thinking

        if not is_in_subagent:
            additional = getattr(chunk, "additional_kwargs", None) or {}
            reasoning = additional.get("reasoning_content") or additional.get("reasoning")
            if reasoning:
                if not in_thinking:
                    content_parts.append("<!--THINK_START-->")
                    in_thinking = True
                content_parts.append(reasoning)

            if hasattr(chunk, "content") and chunk.content:
                if in_thinking:
                    content_parts.append("<!--THINK_END-->")
                    in_thinking = False
                text = chunk.content
                if isinstance(text, list):
                    text = "".join(
                        p.get("text", "") if isinstance(p, dict) else str(p) for p in text
                    )
                content_parts.append(text)

    elif kind == "on_tool_start":
        tool_name = event.get("name", "")
        # PRIORITY: check by name first — LangGraph's ToolNode sets checkpoint_ns to
        # "tools:{tc_id}" for ALL tool calls, so is_in_subagent would be True even for
        # the main agent calling a sub-agent tool.  Name-based detection is reliable.
        tool_input = event.get("data", {}).get("input", {})
        subagent_type = _extract_task_subagent_type(tool_name, tool_input, subagent_tool_names)
        if subagent_type:
            # Main agent calling a sub-agent tool (single-segment checkpoint_ns here)
            if in_thinking:
                content_parts.append("<!--THINK_END-->")
                in_thinking = False
            tool_input_dict = tool_input if isinstance(tool_input, dict) else {}
            sa_tc_id = (
                _extract_tools_task_id(checkpoint_ns)  # LangGraph task UUID (matches engine.py)
                or event.get("run_id", "")             # fallback
            )
            display_args = (
                {k: v for k, v in tool_input_dict.items() if k != "tool_call_id"}
                if isinstance(tool_input, dict) else tool_input
            )
            sub_session_id = f"{thread_id}--sa--{sa_tc_id}" if thread_id else ""
            display_name = (subagent_display_map or {}).get(subagent_type, subagent_type)
            tool_idx = len(tool_calls)
            tool_calls.append({
                "name": display_name,
                "runId": sa_tc_id,
                "args": display_args,
                "status": "running",
                "is_subagent": True,
                "sub_session_id": sub_session_id,
                "startTime": int(time.time() * 1000),
            })
            content_parts.append(f"\n<!--TOOL:{tool_idx}-->\n")
        elif not is_in_subagent:
            # Regular main-agent tool call (not a sub-agent tool)
            if in_thinking:
                content_parts.append("<!--THINK_END-->")
                in_thinking = False
            tool_idx = len(tool_calls)
            tool_input = event.get("data", {}).get("input", {})
            if not isinstance(tool_input, (dict, list, str, int, float, bool, type(None))):
                tool_input = str(tool_input)
            tool_calls.append({
                "name": tool_name,
                "runId": event.get("run_id", ""),
                "args": tool_input,
                "status": "running",
                "startTime": int(time.time() * 1000),
            })
            content_parts.append(f"\n<!--TOOL:{tool_idx}-->\n")
        # else: sub-agent's internal tool call (is_in_subagent=True, not a subagent tool) — skip

    elif kind == "on_tool_end":
        tool_name = event.get("name", "")
        tool_input = event.get("data", {}).get("input", {})
        tool_call_id = _extract_tools_task_id(checkpoint_ns) or event.get("run_id", "")
        if _is_subagent_tool_end(tool_name, tool_input, subagent_tool_names, active_subagent_tool_call_ids, tool_call_id):
            # Main agent's sub-agent tool finished
            raw_output = event.get("data", {}).get("output", "")
            if hasattr(raw_output, "content"):
                result_str = raw_output.content if isinstance(raw_output.content, str) else str(raw_output.content)
            else:
                result_str = str(raw_output)
            sa_tc_id = (
                _extract_tools_task_id(checkpoint_ns)  # LangGraph task UUID (matches on_tool_start)
                or event.get("run_id", "")             # fallback
            )
            for tc in tool_calls:
                if tc.get("runId") == sa_tc_id and tc.get("is_subagent"):
                    start_time = tc.get("startTime")
                    tc["status"] = "error" if result_str.startswith("[Sub-agent error:") else "done"
                    tc["result"] = result_str
                    tc["duration"] = int(time.time() * 1000) - start_time if start_time else None
                    tc["resultLength"] = len(result_str)
                    break
        elif not is_in_subagent:
            # Regular main-agent tool finished
            raw_output = event.get("data", {}).get("output", "")
            if hasattr(raw_output, "content"):
                result_str = raw_output.content if isinstance(raw_output.content, str) else str(raw_output.content)
            else:
                result_str = str(raw_output)
            run_id = event.get("run_id", "")
            name = event.get("name", "")
            tool_call = None
            if run_id:
                tool_call = next(
                    (tc for tc in tool_calls if tc.get("runId") == run_id), None,
                )
            if tool_call is None:
                tool_call = next(
                    (tc for tc in tool_calls if tc.get("name") == name and tc.get("status") == "running"),
                    None,
                )
            if tool_call:
                start_time = tool_call.get("startTime")
                tool_call["result"] = result_str
                tool_call["status"] = "done"
                tool_call["duration"] = int(time.time() * 1000) - start_time if start_time else None
                tool_call["resultLength"] = len(result_str)
        # else: sub-agent's internal tool result (is_in_subagent=True, not a subagent tool) — skip

    return in_thinking


def accumulate_usage(event: dict, usage_rounds: list[dict]) -> None:
    """Extract token usage from on_chat_model_end events.

    Appends a usage dict to usage_rounds if the event is on_chat_model_end.
    Sub-agent LLM calls are skipped — they belong to the sub-session.
    """
    kind = event.get("event", "")
    if kind != "on_chat_model_end":
        return

    # Skip sub-agent LLM calls (they run inside a nested checkpoint_ns)
    checkpoint_ns = _get_checkpoint_ns(event)
    if _extract_subagent_tool_call_id(checkpoint_ns) is not None:
        return

    output = event.get("data", {}).get("output")
    if not output:
        usage_rounds.append({"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cache_read_tokens": 0})
        return

    meta = getattr(output, "usage_metadata", None)
    if meta is None and hasattr(output, "response_metadata"):
        resp_meta = output.response_metadata or {}
        meta = resp_meta.get("token_usage") or resp_meta.get("usage")

    if meta:
        def _get(obj: Any, key: str, default: int = 0) -> int:
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        input_t = _get(meta, "input_tokens", 0) or _get(meta, "prompt_tokens", 0)
        output_t = _get(meta, "output_tokens", 0) or _get(meta, "completion_tokens", 0)
        total_t = _get(meta, "total_tokens", 0) or (input_t + output_t)

        cache_read = 0
        if isinstance(meta, dict):
            details = meta.get("input_token_details") or {}
            cache_read = details.get("cache_read", 0) if isinstance(details, dict) else getattr(details, "cache_read", 0)
        else:
            details = getattr(meta, "input_token_details", None)
            if details:
                cache_read = getattr(details, "cache_read", 0) if not isinstance(details, dict) else details.get("cache_read", 0)

        reasoning = 0
        if isinstance(meta, dict):
            out_details = meta.get("output_token_details") or {}
            reasoning = out_details.get("reasoning", 0) if isinstance(out_details, dict) else getattr(out_details, "reasoning", 0)
        else:
            out_details = getattr(meta, "output_token_details", None)
            if out_details:
                reasoning = getattr(out_details, "reasoning", 0) if not isinstance(out_details, dict) else out_details.get("reasoning", 0)

        usage_rounds.append({
            "input_tokens": input_t or 0,
            "output_tokens": output_t or 0,
            "total_tokens": total_t or 0,
            "cache_read_tokens": cache_read or 0,
            "reasoning_tokens": reasoning or 0,
        })
    else:
        usage_rounds.append({"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cache_read_tokens": 0})


def categorize_error(error: Exception) -> dict:
    """Categorize an exception into structured Chinese error info for the frontend."""
    msg = str(error)
    msg_lower = msg.lower()

    if any(k in msg_lower for k in (
        "401", "unauthorized", "authentication", "api key",
        "incorrect api", "invalid key", "auth failed", "credentials",
    )):
        return {
            "title": "API 密钥认证失败",
            "detail": "AI 模型的 API 密钥无效或未授权，请求被拒绝。",
            "suggestions": ["检查配置文件中的 API Key 是否正确", "确认 API Key 是否有对应模型的访问权限", "如已更换密钥，请更新配置后重试"],
            "error_code": "AUTH_FAILED",
        }

    if any(k in msg_lower for k in ("429", "rate limit", "too many requests", "rate_limit")):
        return {
            "title": "请求频率超限",
            "detail": "向 AI 模型的请求频率超过限制，已被暂时限流。",
            "suggestions": ["等待一段时间后重试", "降低请求并发数", "联系服务商提升配额"],
            "error_code": "RATE_LIMITED",
        }

    if any(k in msg_lower for k in ("model not found", "does not exist", "model `")):
        return {
            "title": "模型不存在或不可用",
            "detail": f"请求的 AI 模型不存在或当前不可用。\n{msg}",
            "suggestions": ["检查选择的模型名称是否正确", "确认该模型在 API 服务商处可用", "尝试切换其他模型"],
            "error_code": "MODEL_NOT_FOUND",
        }

    if any(k in msg_lower for k in (
        "connection refused", "connection error", "connection failed",
        "cannot connect", "connectionreset", "connection_reset",
        "connect failed", "no route to host", "name or service not known",
        "getaddrinfo failed",
    )):
        return {
            "title": "模型服务器连接失败",
            "detail": "无法连接到 AI 模型服务器，请检查网络或服务器状态。",
            "suggestions": ["检查服务器地址和端口是否正确", "确认 AI 模型网关服务是否在运行", "检查防火墙或网络代理设置"],
            "error_code": "CONNECTION_FAILED",
        }

    if any(k in msg_lower for k in ("timeout", "timed out", "deadline exceeded")):
        return {
            "title": "请求超时",
            "detail": "AI 模型响应超时，可能是模型负载过高或网络不稳定。",
            "suggestions": ["稍后重试", "尝试减少输入内容长度", "检查网络连接"],
            "error_code": "TIMEOUT",
        }

    if any(k in msg_lower for k in ("content filter", "content_filter", "safety", "blocked")):
        return {
            "title": "内容被安全策略拦截",
            "detail": "请求内容被 AI 模型的安全审查机制拦截。",
            "suggestions": ["修改输入内容后重试", "避免使用敏感或违规词汇"],
            "error_code": "CONTENT_FILTERED",
        }

    if any(k in msg_lower for k in ("insufficient", "quota", "balance", "billing", "payment")):
        return {
            "title": "账户配额不足",
            "detail": "API 账户配额或余额不足，无法继续请求。",
            "suggestions": ["检查 API 账户余额", "联系服务商增加配额"],
            "error_code": "INSUFFICIENT_QUOTA",
        }

    if any(k in msg_lower for k in ("500", "502", "503", "504", "service unavailable", "internal server error")):
        return {
            "title": "AI 模型服务暂时不可用",
            "detail": "AI 模型服务端返回错误，可能是服务负载过高或正在维护。",
            "suggestions": ["等待几秒后重试", "如持续不可用，联系服务商或管理员"],
            "error_code": "SERVER_UNAVAILABLE",
        }

    return {
        "title": "AI 模型接口请求失败",
        "detail": msg,
        "suggestions": ["请稍后重试，如问题持续请联系管理员"],
        "error_code": "UNKNOWN_ERROR",
    }

`````

--- **end of file: lc_agent/server/stream_utils.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/subagent_tracker.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/subagent_tracker.py`

#### 📝 Module Docstring

`````
Sub-agent stream run tracking for SSE events.
`````

#### 📦 Imports

- `import asyncio`
- `import time`
- `from dataclasses import dataclass`
- `from dataclasses import field`
- `from collections.abc import Awaitable`
- `from collections.abc import Callable`
- `from typing import Any`
- `from lc_agent.core.http_trace import pop_subagent_traces`
- `from lc_agent.server import persistence`

#### 🏛️ Classes (2)

##### 📌 `class _SubAgentRun`
*Line: 15*

**Class Variables (12):**
- `tool_call_id: str`
- `sub_session_id: str`
- `name: str`
- `query: str`
- `tokens: list[str] = field(default_factory=list)`
- `thinking: list[str] = field(default_factory=list)`
- `content_parts: list[str] = field(default_factory=list)`
- `inner_tool_calls: list[dict[str, Any]] = field(default_factory=list)`
- `start_time: float = field(default_factory=time.time)`
- `status: str = 'running'`
- `in_thinking: bool = False`
- `http_traces: list[dict[str, Any]] | None = None`

##### 📌 `class SubAgentRunTracker`
*Line: 30*

**🔧 Constructor (`__init__`):**
- `def __init__(self)`
  - **Parameters:**
    - `self`

**Public Methods (3):**
- `def handle_event(self, event_type: str, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]`
- `def finalize_open_runs(self, status: str = 'error') -> list[tuple[str, dict[str, Any]]]`
- `async def drain(self) -> None`


---

`````python
"""Sub-agent stream run tracking for SSE events."""


import asyncio
import time
from dataclasses import dataclass, field
from collections.abc import Awaitable, Callable
from typing import Any

from lc_agent.core.http_trace import pop_subagent_traces
from lc_agent.server import persistence


@dataclass
class _SubAgentRun:
    tool_call_id: str
    sub_session_id: str
    name: str
    query: str
    tokens: list[str] = field(default_factory=list)
    thinking: list[str] = field(default_factory=list)
    content_parts: list[str] = field(default_factory=list)
    inner_tool_calls: list[dict[str, Any]] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    status: str = "running"
    in_thinking: bool = False
    http_traces: list[dict[str, Any]] | None = None


class SubAgentRunTracker:
    def __init__(
        self,
        *,
        db_url: str,
        parent_thread_id: str,
        user_id: str,
        subagent_display_map: dict[str, str],
        tool_calls: list[dict[str, Any]],
        existing_subsession_ids: set[str] | None = None,
    ) -> None:
        self.db_url = db_url
        self.parent_thread_id = parent_thread_id
        self.user_id = user_id
        self.subagent_display_map = subagent_display_map
        self.tool_calls = tool_calls
        self.existing_subsession_ids = existing_subsession_ids or set()
        self._runs: dict[str, _SubAgentRun] = {}
        self._tasks: list[asyncio.Task[Any]] = []
        self._run_persistence_tasks: dict[str, asyncio.Task[Any]] = {}

    def handle_event(self, event_type: str, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        if event_type == "tool_call" and payload.get("is_subagent"):
            return event_type, self._enrich_subagent_tool_call(payload)
        if event_type == "subagent_start":
            return event_type, self._handle_start(payload)
        if event_type == "subagent_token":
            self._handle_token(payload)
            return event_type, payload
        if event_type == "subagent_thinking":
            self._handle_thinking(payload)
            return event_type, payload
        if event_type == "subagent_tool_call":
            self._handle_tool_call(payload)
            return event_type, payload
        if event_type == "subagent_tool_result":
            self._handle_tool_result(payload)
            return event_type, payload
        if event_type == "subagent_done":
            return event_type, self._handle_done(payload)
        return event_type, payload

    def finalize_open_runs(self, status: str = "error") -> list[tuple[str, dict[str, Any]]]:
        terminal_events: list[tuple[str, dict[str, Any]]] = []
        for tool_call_id in list(self._runs.keys()):
            terminal_events.append((
                "subagent_done",
                self._handle_done({"tool_call_id": tool_call_id, "status": status}),
            ))
        return terminal_events

    async def drain(self) -> None:
        while self._tasks:
            tasks = self._tasks
            self._tasks = []
            await asyncio.gather(*tasks)

    def _enqueue_persistence(self, tool_call_id: str, operation_factory: Callable[[], Awaitable[Any]]) -> None:
        previous_task = self._run_persistence_tasks.get(tool_call_id)

        async def run_ordered() -> None:
            if previous_task is not None:
                await previous_task
            try:
                await operation_factory()
            finally:
                if self._run_persistence_tasks.get(tool_call_id) is current_task:
                    self._run_persistence_tasks.pop(tool_call_id, None)

        current_task = asyncio.create_task(run_ordered())
        self._run_persistence_tasks[tool_call_id] = current_task
        self._tasks.append(current_task)

    def _handle_start(self, payload: dict[str, Any]) -> dict[str, Any]:
        tool_call_id = payload["tool_call_id"]
        subagent_type = payload.get("subagent_type")
        raw_name = payload.get("name") or subagent_type or "sub-agent"
        if subagent_type:
            display_name = self.subagent_display_map.get(subagent_type, raw_name)
        else:
            display_name = self.subagent_display_map.get(raw_name, raw_name)
        query = payload.get("query", "")
        sub_session_id = f"{self.parent_thread_id}--sa--{tool_call_id}"
        run = _SubAgentRun(
            tool_call_id=tool_call_id,
            sub_session_id=sub_session_id,
            name=display_name,
            query=query,
        )
        self._runs[tool_call_id] = run
        existed = sub_session_id in self.existing_subsession_ids
        self._mark_parent_tool_call(tool_call_id, display_name, sub_session_id)
        if not existed:
            self._enqueue_persistence(
                tool_call_id,
                lambda: persistence.create_subsession(
                    self.db_url,
                    sub_session_id,
                    self.parent_thread_id,
                    tool_call_id,
                    display_name,
                    f"{display_name}: {query}",
                    self.user_id,
                ),
            )
            self._enqueue_persistence(
                tool_call_id,
                lambda: persistence.save_subsession_delegation_message(
                    self.db_url,
                    sub_session_id,
                    query,
                ),
            )
        return {**payload, "name": display_name, "sub_session_id": sub_session_id}

    def _handle_token(self, payload: dict[str, Any]) -> None:
        run = self._runs.get(payload.get("tool_call_id"))
        if run is not None:
            content = payload.get("content", "")
            if run.in_thinking:
                run.content_parts.append("<!--THINK_END-->")
                run.in_thinking = False
            run.tokens.append(content)
            run.content_parts.append(content)

    def _handle_thinking(self, payload: dict[str, Any]) -> None:
        run = self._runs.get(payload.get("tool_call_id"))
        if run is not None:
            content = payload.get("content", "")
            if not run.in_thinking:
                run.content_parts.append("<!--THINK_START-->")
                run.in_thinking = True
            run.thinking.append(content)
            run.content_parts.append(content)

    def _handle_tool_call(self, payload: dict[str, Any]) -> None:
        run = self._runs.get(payload.get("tool_call_id"))
        if run is None:
            return
        tool_index = len(run.inner_tool_calls)
        run.inner_tool_calls.append({
            "name": payload.get("name", ""),
            "args": payload.get("args", {}),
            "status": "running",
            "startTime": int(time.time() * 1000),
        })
        if run.in_thinking:
            run.content_parts.append("<!--THINK_END-->")
            run.in_thinking = False
        run.content_parts.append(f"\n<!--TOOL:{tool_index}-->\n")

    def _handle_tool_result(self, payload: dict[str, Any]) -> None:
        run = self._runs.get(payload.get("tool_call_id"))
        if run is None:
            return
        tool_name = payload.get("name", "")
        for tool_call in reversed(run.inner_tool_calls):
            if tool_call.get("name") == tool_name and tool_call.get("status") == "running":
                result = payload.get("result", "")
                status = payload.get("status") or ("error" if payload.get("is_error") else "done")
                start_time = tool_call.get("startTime")
                tool_call["status"] = status
                tool_call["result"] = result
                tool_call["duration"] = int(time.time() * 1000) - start_time if start_time else None
                tool_call["resultLength"] = len(result)
                return

    def _handle_done(self, payload: dict[str, Any]) -> dict[str, Any]:
        tool_call_id = payload["tool_call_id"]
        run = self._runs.pop(tool_call_id, None)
        if run is None:
            return payload
        run.status = payload.get("status", "done")
        content = self._build_content(run)
        traces = pop_subagent_traces(run.sub_session_id) or None
        run.http_traces = traces
        self._enqueue_persistence(
            tool_call_id,
            lambda: persistence.finalize_subsession_message(
                self.db_url,
                run.sub_session_id,
                content,
                tool_calls=run.inner_tool_calls or None,
                http_traces=traces,
            ),
        )
        result_preview = content or payload.get("result_preview", "")
        done_payload = {
            **payload,
            "result_preview": result_preview[:150],
            "status": run.status,
            "duration": int((time.time() - run.start_time) * 1000),
            "tool_count": len(run.inner_tool_calls),
            "token_count": len(run.tokens),
        }
        if traces:
            done_payload["http_traces"] = traces
        return done_payload

    def _mark_parent_tool_call(self, tool_call_id: str, display_name: str, sub_session_id: str) -> None:
        for tool_call in self.tool_calls:
            if tool_call.get("runId") == tool_call_id or tool_call.get("run_id") == tool_call_id:
                tool_call["is_subagent"] = True
                tool_call["sub_session_id"] = sub_session_id
                tool_call["name"] = display_name
                return

    def _enrich_subagent_tool_call(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw_name = payload.get("name", "sub-agent")
        display_name = self.subagent_display_map.get(raw_name, raw_name)
        tool_call_id = payload.get("run_id") or payload.get("runId") or payload.get("tool_call_id")
        if not tool_call_id:
            return {**payload, "name": display_name}
        sub_session_id = f"{self.parent_thread_id}--sa--{tool_call_id}"
        self._mark_parent_tool_call(tool_call_id, display_name, sub_session_id)
        return {**payload, "name": display_name, "sub_session_id": sub_session_id}

    @staticmethod
    def _build_content(run: _SubAgentRun) -> str:
        parts = list(run.content_parts)
        if run.in_thinking:
            parts.append("<!--THINK_END-->")
        return "".join(parts)

`````

--- **end of file: lc_agent/server/subagent_tracker.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/__init__.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/__init__.py`

#### 📦 Imports

- `from lc_agent.server.app import create_app`


---

`````python
# lc_agent/server/__init__.py
from lc_agent.server.app import create_app

__all__ = ["create_app"]

`````

--- **end of file: lc_agent/server/__init__.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/routes/admin.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/routes/admin.py`

#### 📦 Imports

- `from datetime import datetime`
- `from datetime import timezone`
- `from fastapi import APIRouter`
- `from fastapi import Depends`
- `from fastapi import HTTPException`
- `from fastapi import Request`
- `from pydantic import BaseModel`
- `from sqlalchemy import delete`
- `from sqlalchemy import select`
- `from sqlalchemy.ext.asyncio import AsyncSession`
- `from lc_agent.db.models import ChatUiMessage`
- `from lc_agent.db.models import SessionMeta`
- `from lc_agent.db.models_auth import User`
- `from lc_agent.db.models_auth import UserAgentAccess`
- `from lc_agent.server.auth_middleware import get_auth_service`
- `from lc_agent.server.auth_middleware import require_admin`
- `from lc_agent.server.dependencies import get_db_session`
- `from sqlalchemy import delete as sa_delete`

#### 🏛️ Classes (2)

##### 📌 `class CreateUserRequest(BaseModel)`
*Line: 16*

**Class Variables (1):**
- `username: str`

##### 📌 `class SetAgentsRequest(BaseModel)`
*Line: 20*

**Class Variables (1):**
- `agent_ids: list[str]`

#### 🔧 Public Functions (6)

- `async def list_users(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db_session))` `router.get('/users')`
  - *Line: 25*

- `async def create_user(body: CreateUserRequest, request: Request, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db_session))` `router.post('/users', status_code=201)`
  - *Line: 38*

- `async def delete_user(user_id: str, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db_session))` `router.delete('/users/{user_id}', status_code=204)`
  - *Line: 68*

- `async def reset_password(user_id: str, request: Request, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db_session))` `router.put('/users/{user_id}/reset-password')`
  - *Line: 95*

- `async def get_user_agents(user_id: str, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db_session))` `router.get('/users/{user_id}/agents')`
  - *Line: 115*

- `async def set_user_agents(user_id: str, body: SetAgentsRequest, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db_session))` `router.put('/users/{user_id}/agents')`
  - *Line: 126*


---

`````python
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from lc_agent.db.models import ChatUiMessage, SessionMeta
from lc_agent.db.models_auth import User, UserAgentAccess
from lc_agent.server.auth_middleware import get_auth_service, require_admin
from lc_agent.server.dependencies import get_db_session

router = APIRouter(prefix="/admin", tags=["admin"])


class CreateUserRequest(BaseModel):
    username: str


class SetAgentsRequest(BaseModel):
    agent_ids: list[str]


@router.get("/users")
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(User).order_by(User.created_at))
    users = result.scalars().all()
    return [
        {"id": u.id, "username": u.username, "role": u.role, "created_at": u.created_at.isoformat()}
        for u in users
    ]


@router.post("/users", status_code=201)
async def create_user(
    body: CreateUserRequest,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    auth_service = get_auth_service(request)

    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="用户名已存在")

    password = auth_service.generate_random_password()
    user = User(
        username=body.username,
        password_hash=auth_service.hash_password(password),
        role="user",
    )
    db.add(user)

    access = UserAgentAccess(user_id=user.id, agent_id="chat")
    db.add(access)

    await db.commit()
    await db.refresh(user)

    return {"id": user.id, "username": user.username, "role": user.role, "password": password}


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    # Delete messages for user's sessions
    user_sessions = await db.execute(select(SessionMeta.id).where(SessionMeta.user_id == user_id))
    session_ids = [row[0] for row in user_sessions.all()]
    if session_ids:
        from sqlalchemy import delete as sa_delete
        await db.execute(sa_delete(ChatUiMessage).where(ChatUiMessage.session_id.in_(session_ids)))
        await db.execute(sa_delete(SessionMeta).where(SessionMeta.user_id == user_id))

    await db.execute(delete(UserAgentAccess).where(UserAgentAccess.user_id == user_id))
    await db.delete(user)
    await db.commit()


@router.put("/users/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    auth_service = get_auth_service(request)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    password = auth_service.generate_random_password()
    user.password_hash = auth_service.hash_password(password)
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"password": password}


@router.get("/users/{user_id}/agents")
async def get_user_agents(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(UserAgentAccess.agent_id).where(UserAgentAccess.user_id == user_id))
    agent_ids = [row[0] for row in result.all()]
    return {"agent_ids": agent_ids}


@router.put("/users/{user_id}/agents")
async def set_user_agents(
    user_id: str,
    body: SetAgentsRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    await db.execute(delete(UserAgentAccess).where(UserAgentAccess.user_id == user_id))
    for agent_id in body.agent_ids:
        db.add(UserAgentAccess(user_id=user_id, agent_id=agent_id))
    await db.commit()
    return {"agent_ids": body.agent_ids}

`````

--- **end of file: lc_agent/server/routes/admin.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/routes/agents.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/routes/agents.py`

#### 📦 Imports

- `import re`
- `import uuid`
- `from datetime import datetime`
- `from datetime import timezone`
- `from fastapi import APIRouter`
- `from fastapi import Depends`
- `from fastapi import HTTPException`
- `from fastapi import Request`
- `from fastapi import Response`
- `from pydantic import BaseModel`
- `from pydantic import ConfigDict`
- `from pydantic import field_validator`
- `from sqlalchemy import select`
- `from lc_agent.core.engine import AgentEngine`
- `from lc_agent.core.models import AgentPreset`
- `from lc_agent.core.models import SubAgentLink`
- `from lc_agent.db.engine import get_async_session as _get_db_session`
- `from lc_agent.db.models import AgentPresetDB`
- `from lc_agent.db.models_auth import User`
- `from lc_agent.db.models_auth import UserAgentAccess`
- `from lc_agent.server.auth_middleware import get_current_user`
- `from lc_agent.server.auth_middleware import require_admin`
- `from lc_agent.server.dependencies import get_engine`
- `from lc_agent.tools.registry import ToolRegistry`

#### 🏛️ Classes (2)

##### 📌 `class AgentCreateRequest(BaseModel)`
*Line: 36*

**Public Methods (2):**
- `def validate_name_ascii(cls, v: str) -> str` `field_validator('name')` `classmethod`
- `def validate_subagents(cls, value: list[SubAgentLink] | None) -> list[SubAgentLink] | None` `field_validator('subagents')` `classmethod`

**Class Variables (11):**
- `model_config = ConfigDict(extra='forbid')`
- `name: str`
- `display_name: str | None = None`
- `system_prompt: str`
- `default_model: str`
- `allowed_tool_groups: list[str] | None = None`
- `allowed_mcp_servers: list[str] | None = None`
- `allowed_skills: list[str] | None = None`
- `llm_params: dict | None = None`
- `subagents: list[SubAgentLink] | None = None`
- `enable_general_purpose_subagent: bool = False`

##### 📌 `class AgentUpdateRequest(BaseModel)`
*Line: 72*

**Public Methods (2):**
- `def validate_name_ascii(cls, v: str | None) -> str | None` `field_validator('name')` `classmethod`
- `def validate_subagents(cls, value: list[SubAgentLink] | None) -> list[SubAgentLink] | None` `field_validator('subagents')` `classmethod`

**Class Variables (11):**
- `model_config = ConfigDict(extra='forbid')`
- `name: str | None = None`
- `display_name: str | None = None`
- `system_prompt: str | None = None`
- `default_model: str | None = None`
- `allowed_tool_groups: list[str] | None = None`
- `allowed_mcp_servers: list[str] | None = None`
- `allowed_skills: list[str] | None = None`
- `llm_params: dict | None = None`
- `subagents: list[SubAgentLink] | None = None`
- `enable_general_purpose_subagent: bool | None = None`

#### 🔧 Public Functions (7)

- `async def get_db(request: Request)`
  - *Line: 20*

- `async def list_agents(engine: AgentEngine = Depends(get_engine), db = Depends(get_db), user: User = Depends(get_current_user))` `router.get('/agents')`
  - *Line: 133*
  - *List all agent presets (builtin + code + DB-persisted).*

- `async def create_agent(body: AgentCreateRequest, engine: AgentEngine = Depends(get_engine), db = Depends(get_db), admin: User = Depends(require_admin))` `router.post('/agents', status_code=201)`
  - *Line: 188*
  - *Create a new agent preset (persisted to DB).*

- `async def list_available_subagents(engine: AgentEngine = Depends(get_engine), db = Depends(get_db), admin: User = Depends(require_admin))` `router.get('/agents/available-subagents')`
  - *Line: 232*
  - **Docstring:**
  `````
  Return all presets that can be used as sub-agents.
  
  Excludes __chat__ builtin. Includes code agents and web presets.
  `````

- `async def update_agent(agent_id: str, body: AgentUpdateRequest, engine: AgentEngine = Depends(get_engine), db = Depends(get_db), admin: User = Depends(require_admin))` `router.put('/agents/{agent_id}')`
  - *Line: 278*
  - *Update an agent preset.*

- `async def delete_agent(agent_id: str, engine: AgentEngine = Depends(get_engine), db = Depends(get_db), admin: User = Depends(require_admin))` `router.delete('/agents/{agent_id}', status_code=204)`
  - *Line: 330*
  - *Delete an agent preset.*

- `def activate_agent(agent_id: str, request: Request, engine: AgentEngine = Depends(get_engine), admin: User = Depends(require_admin))` `router.post('/agents/{agent_id}/activate')`
  - *Line: 358*
  - **Docstring:**
  `````
  Apply an agent's default toggle state to MCP servers and tool groups.
  
  - Agents with default_enabled=False (Empty): disable all MCP + tool groups
  - Agents with default_enabled=True (Power): enable all MCP + tool groups
  - Chat agent (allowed=[]): no change needed (preset blocks everything)
  `````


---

`````python
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select

from lc_agent.core.engine import AgentEngine
from lc_agent.core.models import AgentPreset, SubAgentLink
from lc_agent.db.engine import get_async_session as _get_db_session
from lc_agent.db.models import AgentPresetDB
from lc_agent.db.models_auth import User, UserAgentAccess
from lc_agent.server.auth_middleware import get_current_user, require_admin
from lc_agent.server.dependencies import get_engine

router = APIRouter(tags=["agents"])


async def get_db(request: Request):
    db_url = request.app.state.config.get("database", {}).get("url", "sqlite+aiosqlite:///./lc_agent_data.db")
    session = _get_db_session(db_url)
    try:
        yield session
    finally:
        await session.close()


_AGENT_NAME_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]*$')
_AGENT_NAME_ERROR = (
    "Agent 名称只能使用英文字母、数字、连字符(-)和下划线(_)，"
    "且必须以字母开头，例如：code-assistant、researcher_v2"
)


class AgentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    display_name: str | None = None
    system_prompt: str
    default_model: str
    allowed_tool_groups: list[str] | None = None
    allowed_mcp_servers: list[str] | None = None
    allowed_skills: list[str] | None = None
    llm_params: dict | None = None
    subagents: list[SubAgentLink] | None = None
    enable_general_purpose_subagent: bool = False

    @field_validator("name")
    @classmethod
    def validate_name_ascii(cls, v: str) -> str:
        if not _AGENT_NAME_PATTERN.match(v):
            raise ValueError(_AGENT_NAME_ERROR)
        return v

    @field_validator("subagents")
    @classmethod
    def validate_subagents(cls, value: list[SubAgentLink] | None) -> list[SubAgentLink] | None:
        if value is None:
            return value
        seen_ids: set[str] = set()
        for item in value:
            if not item.delegation_description.strip():
                raise ValueError("delegation_description must not be blank")
            if item.agent_id in seen_ids:
                raise ValueError(f"duplicate subagent agent_id: {item.agent_id}")
            seen_ids.add(item.agent_id)
        return value


class AgentUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    display_name: str | None = None
    system_prompt: str | None = None
    default_model: str | None = None
    allowed_tool_groups: list[str] | None = None
    allowed_mcp_servers: list[str] | None = None
    allowed_skills: list[str] | None = None
    llm_params: dict | None = None
    subagents: list[SubAgentLink] | None = None
    enable_general_purpose_subagent: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name_ascii(cls, v: str | None) -> str | None:
        if v is not None and not _AGENT_NAME_PATTERN.match(v):
            raise ValueError(_AGENT_NAME_ERROR)
        return v

    @field_validator("subagents")
    @classmethod
    def validate_subagents(cls, value: list[SubAgentLink] | None) -> list[SubAgentLink] | None:
        if value is None:
            return value
        seen_ids: set[str] = set()
        for item in value:
            if not item.delegation_description.strip():
                raise ValueError("delegation_description must not be blank")
            if item.agent_id in seen_ids:
                raise ValueError(f"duplicate subagent agent_id: {item.agent_id}")
            seen_ids.add(item.agent_id)
        return value


def _preset_to_dict(p: AgentPreset) -> dict:
    data = p.model_dump()
    if data.get("subagents") is not None:
        data["subagents"] = [item.model_dump() if hasattr(item, "model_dump") else item for item in data["subagents"]]
    if p.source == "code":
        return {
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "system_prompt": p.system_prompt,
            "default_model": "custom",
            "allowed_tool_groups": [],
            "allowed_mcp_servers": [],
            "allowed_skills": [],
            "source": "code",
            "default_enabled": False,
            "subagents": data.get("subagents"),
            "enable_general_purpose_subagent": False,
        }
    data["source"] = p.source
    data["default_enabled"] = p.default_enabled
    return data


@router.get("/agents")
async def list_agents(
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all agent presets (builtin + code + DB-persisted)."""
    result = []

    for bp in engine.get_builtin_presets():
        result.append(_preset_to_dict(bp))

    for p in engine._custom_presets.values():
        result.append(_preset_to_dict(p))

    stmt = select(AgentPresetDB)
    rows = await db.execute(stmt)
    for row in rows.scalars().all():
        result.append({
            "id": row.id,
            "name": row.name,
            "display_name": row.display_name,
            "system_prompt": row.system_prompt,
            "default_model": row.default_model,
            "allowed_tool_groups": row.allowed_tool_groups,
            "allowed_mcp_servers": row.allowed_mcp_servers,
            "allowed_skills": row.allowed_skills,
            "llm_params": row.llm_params,
            "source": "user",
            "default_enabled": True,
            "subagents": row.subagents,
            "enable_general_purpose_subagent": row.enable_general_purpose_subagent,
        })

    if user.role != "admin":
        access_stmt = select(UserAgentAccess.agent_id).where(UserAgentAccess.user_id == user.id)
        access_rows = await db.execute(access_stmt)
        allowed_ids = set(access_rows.scalars().all())
        result = [a for a in result if a["id"] in allowed_ids]

    return result


def _validate_subagent_ids_exist(engine: AgentEngine, subagents: list[SubAgentLink] | None) -> None:
    """Validate that every subagent agent_id refers to a known preset."""
    if not subagents:
        return
    for link in subagents:
        if not engine._preset_exists(link.agent_id):
            raise HTTPException(
                status_code=422,
                detail=f"subagent agent_id not found: {link.agent_id}",
            )


@router.post("/agents", status_code=201)
async def create_agent(
    body: AgentCreateRequest,
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Create a new agent preset (persisted to DB)."""
    _validate_subagent_ids_exist(engine, body.subagents)
    preset_db = AgentPresetDB(
        id=str(uuid.uuid4()),
        name=body.name,
        display_name=body.display_name,
        system_prompt=body.system_prompt,
        default_model=body.default_model,
        allowed_tool_groups=body.allowed_tool_groups,
        allowed_mcp_servers=body.allowed_mcp_servers,
        allowed_skills=body.allowed_skills,
        llm_params=body.llm_params,
        subagents=[item.model_dump() for item in body.subagents] if body.subagents else None,
        enable_general_purpose_subagent=body.enable_general_purpose_subagent,
    )
    db.add(preset_db)
    await db.commit()
    await db.refresh(preset_db)

    preset = AgentPreset(
        id=preset_db.id,
        name=preset_db.name,
        display_name=preset_db.display_name,
        system_prompt=preset_db.system_prompt,
        default_model=preset_db.default_model,
        allowed_tool_groups=preset_db.allowed_tool_groups,
        allowed_mcp_servers=preset_db.allowed_mcp_servers,
        allowed_skills=preset_db.allowed_skills,
        llm_params=preset_db.llm_params,
        subagents=[SubAgentLink.model_validate(item) for item in preset_db.subagents] if preset_db.subagents else None,
        enable_general_purpose_subagent=preset_db.enable_general_purpose_subagent,
    )
    engine._presets[preset.id] = preset

    return _preset_to_dict(preset)


@router.get("/agents/available-subagents")
async def list_available_subagents(
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Return all presets that can be used as sub-agents.

    Excludes __chat__ builtin. Includes code agents and web presets.
    """
    result = []

    for p in engine._custom_presets.values():
        result.append({
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "source": "code",
            "description": p.default_delegation_description or "",
        })

    for bp in engine.get_builtin_presets():
        if bp.id == "chat":
            continue
        result.append({
            "id": bp.id,
            "name": bp.name,
            "display_name": bp.display_name,
            "source": "builtin",
            "description": bp.default_delegation_description or "",
        })

    stmt = select(AgentPresetDB)
    rows = await db.execute(stmt)
    for row in rows.scalars().all():
        result.append({
            "id": row.id,
            "name": row.name,
            "display_name": row.display_name,
            "source": "user",
            "description": "",
        })

    return result


@router.put("/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    body: AgentUpdateRequest,
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Update an agent preset."""
    if agent_id in engine.BUILTIN_IDS:
        raise HTTPException(status_code=400, detail="Cannot edit builtin agent")

    _validate_subagent_ids_exist(engine, body.subagents)
    update_data = body.model_dump(exclude_unset=True)

    if agent_id in engine._custom_presets:
        raise HTTPException(
            status_code=403,
            detail="Code agents are defined by their registered graph and cannot be edited from the UI",
        )

    stmt = select(AgentPresetDB).where(AgentPresetDB.id == agent_id)
    result = await db.execute(stmt)
    preset_db = result.scalar_one_or_none()
    if preset_db is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    for key, value in update_data.items():
        setattr(preset_db, key, value)
    preset_db.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(preset_db)

    preset = AgentPreset(
        id=preset_db.id,
        name=preset_db.name,
        display_name=preset_db.display_name,
        system_prompt=preset_db.system_prompt,
        default_model=preset_db.default_model,
        allowed_tool_groups=preset_db.allowed_tool_groups,
        allowed_mcp_servers=preset_db.allowed_mcp_servers,
        allowed_skills=preset_db.allowed_skills,
        llm_params=preset_db.llm_params,
        subagents=[SubAgentLink.model_validate(item) for item in preset_db.subagents] if preset_db.subagents else None,
        enable_general_purpose_subagent=preset_db.enable_general_purpose_subagent,
    )
    engine._presets[preset.id] = preset
    engine.invalidate_agent_cache(agent_id)

    return _preset_to_dict(preset)


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Delete an agent preset."""
    if agent_id in engine.BUILTIN_IDS:
        raise HTTPException(status_code=400, detail="Cannot delete builtin agent")
    if agent_id in engine._custom_presets:
        raise HTTPException(status_code=403, detail="Cannot delete code-registered agent")

    stmt = select(AgentPresetDB).where(AgentPresetDB.id == agent_id)
    result = await db.execute(stmt)
    preset_db = result.scalar_one_or_none()
    if preset_db is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    await db.delete(preset_db)
    await db.commit()

    engine._presets.pop(agent_id, None)
    engine.invalidate_agent_cache(agent_id)

    return Response(status_code=204)


@router.post("/agents/{agent_id}/activate")
def activate_agent(
    agent_id: str,
    request: Request,
    engine: AgentEngine = Depends(get_engine),
    admin: User = Depends(require_admin),
):
    """Apply an agent's default toggle state to MCP servers and tool groups.

    - Agents with default_enabled=False (Empty): disable all MCP + tool groups
    - Agents with default_enabled=True (Power): enable all MCP + tool groups
    - Chat agent (allowed=[]): no change needed (preset blocks everything)
    """
    from lc_agent.tools.registry import ToolRegistry

    preset = engine._resolve_preset(agent_id)
    if preset.source == "code" or agent_id in engine._custom_presets:
        return {
            "agent_id": agent_id,
            "action": "none",
            "reason": "code agent is controlled by its registered graph",
        }
    manager = getattr(request.app.state, "mcp_manager", None)
    loader = getattr(request.app.state, "filtered_loader", None)
    registry = ToolRegistry()

    if preset.allowed_tool_groups == [] and preset.allowed_mcp_servers == [] and preset.allowed_skills == []:
        return {"agent_id": agent_id, "action": "none", "reason": "preset blocks all"}

    target_enabled = preset.default_enabled

    changed_mcp = []
    if manager:
        for server in manager.servers:
            if server.enabled != target_enabled:
                server.enabled = target_enabled
                if not target_enabled:
                    server.status = "disabled"
                elif server.name in manager._sessions:
                    server.status = "connected"
                else:
                    server.status = "disconnected"
                changed_mcp.append(server.name)

    changed_groups = []
    for group in registry.get_group_names():
        is_disabled = group in registry._disabled_groups
        if target_enabled and is_disabled:
            registry._disabled_groups.discard(group)
            changed_groups.append(group)
        elif not target_enabled and not is_disabled:
            registry._disabled_groups.add(group)
            changed_groups.append(group)

    changed_skills = []
    if loader:
        all_skill_names = {skill.name for skill in loader.list_all_skills()}
        if preset.allowed_skills is None:
            target_skill_names = sorted(all_skill_names)
        else:
            target_skill_names = [name for name in preset.allowed_skills if name in all_skill_names]
        for skill_name in target_skill_names:
            is_disabled = skill_name in loader.disabled_skills
            if target_enabled and is_disabled:
                loader.disabled_skills.discard(skill_name)
                changed_skills.append(skill_name)
            elif not target_enabled and not is_disabled:
                loader.disabled_skills.add(skill_name)
                changed_skills.append(skill_name)

    if changed_mcp or changed_groups or changed_skills:
        engine._mcp_generation += 1

    return {
        "agent_id": agent_id,
        "default_enabled": target_enabled,
        "changed_mcp": changed_mcp,
        "changed_groups": changed_groups,
        "changed_skills": changed_skills,
    }

`````

--- **end of file: lc_agent/server/routes/agents.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/routes/auth.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/routes/auth.py`

#### 📦 Imports

- `from fastapi import APIRouter`
- `from fastapi import Depends`
- `from fastapi import HTTPException`
- `from fastapi import Request`
- `from pydantic import BaseModel`
- `from sqlalchemy import select`
- `from sqlalchemy.ext.asyncio import AsyncSession`
- `from lc_agent.db.models_auth import User`
- `from lc_agent.server.auth_middleware import get_auth_service`
- `from lc_agent.server.auth_middleware import get_current_user`
- `from lc_agent.server.dependencies import get_db_session`

#### 🏛️ Classes (2)

##### 📌 `class LoginRequest(BaseModel)`
*Line: 13*

**Class Variables (2):**
- `username: str`
- `password: str`

##### 📌 `class ChangePasswordRequest(BaseModel)`
*Line: 18*

**Class Variables (2):**
- `old_password: str`
- `new_password: str`

#### 🔧 Public Functions (3)

- `async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db_session))` `router.post('/login')`
  - *Line: 24*

- `async def me(user: User = Depends(get_current_user))` `router.get('/me')`
  - *Line: 43*

- `async def change_password(body: ChangePasswordRequest, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session))` `router.post('/change-password')`
  - *Line: 52*


---

`````python
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lc_agent.db.models_auth import User
from lc_agent.server.auth_middleware import get_auth_service, get_current_user
from lc_agent.server.dependencies import get_db_session

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/login")
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db_session)):
    auth_service = get_auth_service(request)
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if user is None or not auth_service.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="认证失败")

    token = auth_service.create_token(user_id=user.id, username=user.username, role=user.role)
    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
    }


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    auth_service = get_auth_service(request)
    if not auth_service.verify_password(body.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="旧密码错误")

    result = await db.execute(select(User).where(User.id == user.id))
    db_user = result.scalar_one()
    db_user.password_hash = auth_service.hash_password(body.new_password)
    await db.commit()
    return {"message": "密码修改成功"}

`````

--- **end of file: lc_agent/server/routes/auth.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/routes/health.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/routes/health.py`

#### 📦 Imports

- `from fastapi import APIRouter`
- `from fastapi import Request`
- `from lc_agent import __version__`

#### 🔧 Public Functions (1)

- `async def health(request: Request)` `router.get('/health')`
  - *Line: 10*
  - *Health check endpoint.*


---

`````python
# lc_agent/server/routes/health.py
from fastapi import APIRouter, Request

from lc_agent import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request):
    """Health check endpoint."""
    config = request.app.state.config
    auth_enabled = (
        hasattr(request.app.state, "auth_service")
        and request.app.state.auth_service is not None
    )
    return {
        "status": "ok",
        "version": __version__,
        "auth_enabled": auth_enabled,
        "config_loaded": config.get("_config_path") is not None,
        "app_name": config.get("ui", {}).get("app_name"),
    }

`````

--- **end of file: lc_agent/server/routes/health.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/routes/mcp.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/routes/mcp.py`

#### 📦 Imports

- `from fastapi import APIRouter`
- `from fastapi import Depends`
- `from fastapi import HTTPException`
- `from fastapi import Request`
- `from lc_agent.db.models_auth import User`
- `from lc_agent.server.auth_middleware import get_current_user`

#### 🔧 Public Functions (2)

- `def list_mcp_servers(request: Request, user: User = Depends(get_current_user))` `router.get('/mcp')`
  - *Line: 10*
  - *List MCP servers with their status.*

- `def toggle_mcp_server(name: str, request: Request, user: User = Depends(get_current_user))` `router.post('/mcp/{name}/toggle')`
  - *Line: 35*
  - *Toggle a MCP server's enabled state at runtime.*


---

`````python
from fastapi import APIRouter, Depends, HTTPException, Request

from lc_agent.db.models_auth import User
from lc_agent.server.auth_middleware import get_current_user

router = APIRouter(tags=["mcp"])


@router.get("/mcp")
def list_mcp_servers(
    request: Request,
    user: User = Depends(get_current_user),
):
    """List MCP servers with their status."""
    manager = getattr(request.app.state, "mcp_manager", None)
    if manager is None:
        return []
    return [
        {
            "name": s.name,
            "type": s.type,
            "command": s.command,
            "url": s.url,
            "enabled": s.enabled,
            "status": s.status,
            "tools": s.tools,
            "tool_schemas": s.tool_schemas if hasattr(s, 'tool_schemas') else [],
            "error": s.error,
        }
        for s in manager.servers
    ]


@router.post("/mcp/{name}/toggle")
def toggle_mcp_server(
    name: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Toggle a MCP server's enabled state at runtime."""
    manager = getattr(request.app.state, "mcp_manager", None)
    if manager is None:
        raise HTTPException(status_code=404, detail="MCP manager not found")
    server = manager.get_server(name)
    if server is None:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")
    server.enabled = not server.enabled
    if not server.enabled:
        server.status = "disabled"
    else:
        has_session = name in manager._sessions
        if has_session:
            server.status = "connected"
        else:
            server.status = "disconnected"
    engine = getattr(request.app.state, "engine", None)
    if engine:
        engine._mcp_generation += 1
    return {"name": name, "enabled": server.enabled, "status": server.status}

`````

--- **end of file: lc_agent/server/routes/mcp.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/routes/models.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/routes/models.py`

#### 📦 Imports

- `from fastapi import APIRouter`
- `from fastapi import Depends`
- `from lc_agent.core.engine import AgentEngine`
- `from lc_agent.db.models_auth import User`
- `from lc_agent.server.auth_middleware import get_current_user`
- `from lc_agent.server.dependencies import get_engine`

#### 🔧 Public Functions (1)

- `def list_models(user: User = Depends(get_current_user), engine: AgentEngine = Depends(get_engine))` `router.get('/models')`
  - *Line: 12*
  - *List all configured models.*


---

`````python
from fastapi import APIRouter, Depends

from lc_agent.core.engine import AgentEngine
from lc_agent.db.models_auth import User
from lc_agent.server.auth_middleware import get_current_user
from lc_agent.server.dependencies import get_engine

router = APIRouter(tags=["models"])


@router.get("/models")
def list_models(
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
):
    """List all configured models."""
    return [
        {
            "id": m.id,
            "provider": m.provider,
            "base_url": m.base_url,
            "context_limit": m.context_limit,
        }
        for m in engine.get_models()
    ]

`````

--- **end of file: lc_agent/server/routes/models.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/routes/permissions.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/routes/permissions.py`

#### 📦 Imports

- `from fastapi import APIRouter`
- `from fastapi import Depends`
- `from fastapi import Request`
- `from pydantic import BaseModel`
- `from lc_agent.core.permissions import PermissionsService`
- `from lc_agent.db.models_auth import User`
- `from lc_agent.server.auth_middleware import get_current_user`
- `from lc_agent.server.auth_middleware import require_admin`

#### 🏛️ Classes (2)

##### 📌 `class AllowToolRequest(BaseModel)`
*Line: 15*

**Class Variables (1):**
- `tool_name: str`

##### 📌 `class SetAllowlistRequest(BaseModel)`
*Line: 19*

**Class Variables (1):**
- `tool_allowlist: list[str]`

#### 🔧 Public Functions (4)

- `def get_permissions(request: Request, user: User = Depends(get_current_user))` `router.get('/permissions')`
  - *Line: 24*

- `def allow_tool(body: AllowToolRequest, request: Request, admin: User = Depends(require_admin))` `router.post('/permissions/allow')`
  - *Line: 33*

- `def remove_tool(body: AllowToolRequest, request: Request, admin: User = Depends(require_admin))` `router.post('/permissions/remove')`
  - *Line: 44*

- `def set_permissions(body: SetAllowlistRequest, request: Request, admin: User = Depends(require_admin))` `router.put('/permissions')`
  - *Line: 55*


---

`````python
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from lc_agent.core.permissions import PermissionsService
from lc_agent.db.models_auth import User
from lc_agent.server.auth_middleware import get_current_user, require_admin

router = APIRouter(tags=["permissions"])


def _get_permissions(request: Request) -> PermissionsService:
    return request.app.state.permissions


class AllowToolRequest(BaseModel):
    tool_name: str


class SetAllowlistRequest(BaseModel):
    tool_allowlist: list[str]


@router.get("/permissions")
def get_permissions(
    request: Request,
    user: User = Depends(get_current_user),
):
    svc = _get_permissions(request)
    return {"version": 1, "tool_allowlist": svc.get_allowlist()}


@router.post("/permissions/allow")
def allow_tool(
    body: AllowToolRequest,
    request: Request,
    admin: User = Depends(require_admin),
):
    svc = _get_permissions(request)
    svc.allow_tool(body.tool_name)
    return {"ok": True, "tool_allowlist": svc.get_allowlist()}


@router.post("/permissions/remove")
def remove_tool(
    body: AllowToolRequest,
    request: Request,
    admin: User = Depends(require_admin),
):
    svc = _get_permissions(request)
    svc.remove_tool(body.tool_name)
    return {"ok": True, "tool_allowlist": svc.get_allowlist()}


@router.put("/permissions")
def set_permissions(
    body: SetAllowlistRequest,
    request: Request,
    admin: User = Depends(require_admin),
):
    svc = _get_permissions(request)
    svc.set_allowlist(body.tool_allowlist)
    return {"ok": True, "tool_allowlist": svc.get_allowlist()}

`````

--- **end of file: lc_agent/server/routes/permissions.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/routes/sessions.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/routes/sessions.py`

#### 📦 Imports

- `from fastapi import APIRouter`
- `from fastapi import Depends`
- `from fastapi import HTTPException`
- `from fastapi import Query`
- `from fastapi import Request`
- `from fastapi import Response`
- `from pydantic import BaseModel`
- `from sqlalchemy.ext.asyncio import AsyncSession`
- `from lc_agent.db.models_auth import User`
- `from lc_agent.db.repository import ChatUiMessageRepository`
- `from lc_agent.db.repository import SessionRepository`
- `from lc_agent.server.auth_middleware import get_current_user`
- `from lc_agent.server.dependencies import get_db_session`
- `from lc_agent.utils.loggers import server_logger`
- `from lc_agent.db.models_auth import UserAgentAccess`
- `from sqlalchemy import select as sa_select`

#### 🏛️ Classes (2)

##### 📌 `class SessionCreateRequest(BaseModel)`
*Line: 14*

**Class Variables (3):**
- `title: str = '新对话'`
- `agent_id: str = 'chat'`
- `model: str = ''`

##### 📌 `class SessionUpdateRequest(BaseModel)`
*Line: 20*

**Class Variables (3):**
- `title: str | None = None`
- `model: str | None = None`
- `is_pinned: bool | None = None`

#### 🔧 Public Functions (7)

- `def serialize_session(s)`
  - *Line: 26*

- `async def list_sessions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session))` `router.get('/sessions')`
  - *Line: 46*

- `async def create_session(body: SessionCreateRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session))` `router.post('/sessions', status_code=201)`
  - *Line: 59*

- `async def update_session(session_id: str, body: SessionUpdateRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session))` `router.put('/sessions/{session_id}')`
  - *Line: 89*

- `async def delete_session(session_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session))` `router.delete('/sessions/{session_id}', status_code=204)`
  - *Line: 109*

- `async def get_session_messages(session_id: str, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session), limit: int = Query(default=50, ge=1, le=200), offset: int | None = Query(default=None, ge=0))` `router.get('/sessions/{session_id}/messages')`
  - *Line: 127*
  - **Docstring:**
  `````
  Retrieve message history for a session (paginated, without http_traces body).
  
  When offset is not provided, returns the LATEST `limit` messages (most recent).
  When offset is explicitly 0 or positive, returns from that position (oldest first).
  `````

- `async def get_message_traces(session_id: str, message_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session))` `router.get('/sessions/{session_id}/messages/{message_id}/traces')`
  - *Line: 225*
  - *Retrieve http_traces for a specific message (on-demand loading).*


---

`````python
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from lc_agent.db.models_auth import User
from lc_agent.db.repository import ChatUiMessageRepository, SessionRepository
from lc_agent.server.auth_middleware import get_current_user
from lc_agent.server.dependencies import get_db_session
from lc_agent.utils.loggers import server_logger

router = APIRouter(tags=["sessions"])


class SessionCreateRequest(BaseModel):
    title: str = "新对话"
    agent_id: str = "chat"
    model: str = ""


class SessionUpdateRequest(BaseModel):
    title: str | None = None
    model: str | None = None
    is_pinned: bool | None = None


def serialize_session(s):
    return {
        "id": s.id,
        "title": s.title,
        "agent_id": s.agent_id,
        "model": s.model,
        "message_count": s.message_count,
        "is_pinned": s.is_pinned,
        "pinned_at": s.pinned_at.isoformat() if s.pinned_at else None,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }


def _check_session_access(sess, user: User) -> None:
    if sess.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")


@router.get("/sessions")
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repo = SessionRepository(db)
    if user.role == "admin":
        sessions = await repo.list_all()
    else:
        sessions = await repo.list_all(user_id=user.id)
    return [serialize_session(s) for s in sessions]


@router.post("/sessions", status_code=201)
async def create_session(
    body: SessionCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repo = SessionRepository(db)

    # Validate agent access for non-admin
    if user.role != "admin" and body.agent_id != "chat":
        from lc_agent.db.models_auth import UserAgentAccess
        from sqlalchemy import select as sa_select
        result = await db.execute(
            sa_select(UserAgentAccess).where(
                UserAgentAccess.user_id == user.id,
                UserAgentAccess.agent_id == body.agent_id,
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=403, detail="无权使用此智能体")

    session = await repo.create(
        title=body.title,
        agent_id=body.agent_id,
        model=body.model,
        user_id=user.id,
    )
    return {"id": session.id, "title": session.title}


@router.put("/sessions/{session_id}")
async def update_session(
    session_id: str,
    body: SessionUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_session_access(sess, user)

    update_data = body.model_dump(exclude_unset=True)
    result = await repo.update(session_id, **update_data)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return serialize_session(result)


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_session_access(sess, user)

    deleted = await repo.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return Response(status_code=204)


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int | None = Query(default=None, ge=0),
):
    """Retrieve message history for a session (paginated, without http_traces body).

    When offset is not provided, returns the LATEST `limit` messages (most recent).
    When offset is explicitly 0 or positive, returns from that position (oldest first).
    """
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_session_access(sess, user)

    msg_repo = ChatUiMessageRepository(db)
    total = await msg_repo.count_by_session(session_id)

    if offset is None:
        effective_offset = max(0, total - limit)
    else:
        effective_offset = offset

    ui_messages = await msg_repo.list_by_session(session_id, limit=limit, offset=effective_offset)

    if ui_messages:
        return {
            "total": total,
            "offset": effective_offset,
            "limit": limit,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "tool_calls": msg.tool_calls or [],
                    "usage": msg.usage,
                    "http_traces_count": len(msg.http_traces) if msg.http_traces else 0,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in ui_messages
            ],
        }

    engine = request.app.state.engine
    checkpointer = engine._checkpointer
    if checkpointer is None:
        return {"total": 0, "offset": effective_offset, "limit": limit, "messages": []}

    try:
        config = {"configurable": {"thread_id": session_id}}
        checkpoint_tuple = await checkpointer.aget_tuple(config)
        if checkpoint_tuple is None:
            return {"total": 0, "offset": effective_offset, "limit": limit, "messages": []}

        checkpoint = checkpoint_tuple.checkpoint
        channel_values = checkpoint.get("channel_values", {})
        messages = channel_values.get("messages", [])

        result = []
        for msg in messages:
            msg_type = getattr(msg, "type", "unknown")
            content = getattr(msg, "content", "")
            tool_calls = getattr(msg, "tool_calls", None)

            role = msg_type
            if msg_type == "human":
                role = "user"
            elif msg_type == "ai":
                role = "assistant"

            item = {"role": role, "content": content}

            if tool_calls:
                item["tool_calls"] = [
                    {"name": tc.get("name", ""), "args": tc.get("args", {}), "id": tc.get("id", "")}
                    for tc in tool_calls
                ]

            if msg_type == "tool":
                item["tool_call_id"] = getattr(msg, "tool_call_id", "")
                item["name"] = getattr(msg, "name", "")

            result.append(item)

        checkpoint_offset = effective_offset if effective_offset < len(result) else max(0, len(result) - limit)
        paginated = result[checkpoint_offset:checkpoint_offset + limit]
        return {"total": len(result), "offset": checkpoint_offset, "limit": limit, "messages": paginated}
    except Exception as e:
        server_logger.exception("Failed to load messages for session %s", session_id)
        return {"total": 0, "offset": effective_offset, "limit": limit, "messages": []}


@router.get("/sessions/{session_id}/messages/{message_id}/traces")
async def get_message_traces(
    session_id: str,
    message_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Retrieve http_traces for a specific message (on-demand loading)."""
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_session_access(sess, user)

    msg_repo = ChatUiMessageRepository(db)
    msg = await msg_repo.get_by_id(message_id)
    if msg is None or msg.session_id != session_id:
        raise HTTPException(status_code=404, detail="Message not found")

    return {"traces": msg.http_traces or []}

`````

--- **end of file: lc_agent/server/routes/sessions.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/routes/settings.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/routes/settings.py`

#### 📦 Imports

- `from fastapi import APIRouter`
- `from fastapi import Depends`
- `from pydantic import BaseModel`
- `from lc_agent.core.engine import AgentEngine`
- `from lc_agent.db.models_auth import User`
- `from lc_agent.server.auth_middleware import get_current_user`
- `from lc_agent.server.dependencies import get_engine`

#### 🏛️ Classes (1)

##### 📌 `class SummarizationConfig(BaseModel)`
*Line: 12*

**Class Variables (4):**
- `enabled: bool = True`
- `default_model: str = ''`
- `trigger: list | None = None`
- `keep: list | None = None`

#### 🔧 Public Functions (2)

- `def get_summarization(user: User = Depends(get_current_user), engine: AgentEngine = Depends(get_engine))` `router.get('/settings/summarization')`
  - *Line: 20*
  - *Get current summarization configuration.*

- `def update_summarization(body: SummarizationConfig, user: User = Depends(get_current_user), engine: AgentEngine = Depends(get_engine))` `router.put('/settings/summarization')`
  - *Line: 35*
  - *Update summarization config at runtime (no restart needed).*


---

`````python
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from lc_agent.core.engine import AgentEngine
from lc_agent.db.models_auth import User
from lc_agent.server.auth_middleware import get_current_user
from lc_agent.server.dependencies import get_engine

router = APIRouter(tags=["settings"])


class SummarizationConfig(BaseModel):
    enabled: bool = True
    default_model: str = ""
    trigger: list | None = None
    keep: list | None = None


@router.get("/settings/summarization")
def get_summarization(
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
):
    """Get current summarization configuration."""
    conf = engine.config.get("agent", {}).get("summarization", {})
    return {
        "enabled": conf.get("enabled", True),
        "default_model": conf.get("default_model", ""),
        "trigger": conf.get("trigger"),
        "keep": conf.get("keep"),
    }


@router.put("/settings/summarization")
def update_summarization(
    body: SummarizationConfig,
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
):
    """Update summarization config at runtime (no restart needed)."""
    agent_conf = engine.config.setdefault("agent", {})
    summ_conf = agent_conf.setdefault("summarization", {})

    summ_conf["enabled"] = body.enabled
    summ_conf["default_model"] = body.default_model
    if body.trigger is not None:
        summ_conf["trigger"] = body.trigger
    if body.keep is not None:
        summ_conf["keep"] = body.keep

    engine.invalidate_all_agents()

    return {
        "enabled": summ_conf.get("enabled", True),
        "default_model": summ_conf.get("default_model", ""),
        "trigger": summ_conf.get("trigger"),
        "keep": summ_conf.get("keep"),
    }

`````

--- **end of file: lc_agent/server/routes/settings.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/routes/skills.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/routes/skills.py`

#### 📦 Imports

- `from fastapi import APIRouter`
- `from fastapi import Depends`
- `from fastapi import HTTPException`
- `from fastapi import Request`
- `from langchain_agentskills import SkillsToolkit`
- `from lc_agent.db.models_auth import User`
- `from lc_agent.server.auth_middleware import get_current_user`
- `from lc_agent.skills.filtered_loader import FilteredSkillLoader`

#### 🔧 Public Functions (4)

- `def list_skills(request: Request, user: User = Depends(get_current_user))` `router.get('/skills')`
  - *Line: 21*
  - *List all skills with their enabled state (tier 1 metadata).*

- `def toggle_skill(name: str, request: Request, user: User = Depends(get_current_user))` `router.post('/skills/{name}/toggle')`
  - *Line: 43*
  - *Toggle a skill's enabled state at runtime.*

- `def get_skill(name: str, request: Request, user: User = Depends(get_current_user))` `router.get('/skills/{name}')`
  - *Line: 63*
  - *Load a skill's full content (tier 2).*

- `def read_skill_resource(name: str, resource_name: str, request: Request, user: User = Depends(get_current_user))` `router.get('/skills/{name}/resources/{resource_name:path}')`
  - *Line: 86*
  - *Read a skill resource file (tier 3).*


---

`````python
from fastapi import APIRouter, Depends, HTTPException, Request

from langchain_agentskills import SkillsToolkit

from lc_agent.db.models_auth import User
from lc_agent.server.auth_middleware import get_current_user
from lc_agent.skills.filtered_loader import FilteredSkillLoader

router = APIRouter(tags=["skills"])


def _get_toolkit(request: Request) -> SkillsToolkit | None:
    return getattr(request.app.state, "skills_toolkit", None)


def _get_loader(request: Request) -> FilteredSkillLoader | None:
    return getattr(request.app.state, "filtered_loader", None)


@router.get("/skills")
def list_skills(
    request: Request,
    user: User = Depends(get_current_user),
):
    """List all skills with their enabled state (tier 1 metadata)."""
    loader = _get_loader(request)
    if loader is None:
        return []
    all_skills = loader.list_all_skills()
    return [
        {
            "name": s.name,
            "description": s.description,
            "source": s.source,
            "metadata": s.metadata,
            "enabled": s.name not in loader.disabled_skills,
        }
        for s in all_skills
    ]


@router.post("/skills/{name}/toggle")
def toggle_skill(
    name: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Toggle a skill's enabled state at runtime."""
    loader = _get_loader(request)
    if loader is None:
        raise HTTPException(status_code=404, detail="Skills not configured")
    all_names = {s.name for s in loader.list_all_skills()}
    if name not in all_names:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")
    enabled = loader.toggle(name)
    engine = getattr(request.app.state, "engine", None)
    if engine:
        engine._mcp_generation += 1
    return {"name": name, "enabled": enabled}


@router.get("/skills/{name}")
def get_skill(
    name: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Load a skill's full content (tier 2)."""
    loader = _get_loader(request)
    if loader is None:
        raise HTTPException(status_code=404, detail="Skills not configured")
    try:
        skill = loader.load_skill(name)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")
    return {
        "name": skill.metadata.name,
        "description": skill.metadata.description,
        "body": skill.body,
        "resources": skill.resources,
        "scripts": skill.scripts,
    }


@router.get("/skills/{name}/resources/{resource_name:path}")
def read_skill_resource(
    name: str,
    resource_name: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Read a skill resource file (tier 3)."""
    loader = _get_loader(request)
    if loader is None:
        raise HTTPException(status_code=404, detail="Skills not configured")
    try:
        content = loader.read_resource(name, resource_name)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Resource '{resource_name}' not found in skill '{name}'",
        )
    return {"skill": name, "resource": resource_name, "content": content}

`````

--- **end of file: lc_agent/server/routes/skills.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/routes/tools.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/routes/tools.py`

#### 📦 Imports

- `from fastapi import APIRouter`
- `from fastapi import Depends`
- `from fastapi import Request`
- `from lc_agent.core.engine import AgentEngine`
- `from lc_agent.db.models_auth import User`
- `from lc_agent.server.auth_middleware import get_current_user`
- `from lc_agent.server.dependencies import get_engine`
- `from lc_agent.server.dependencies import get_registry`
- `from lc_agent.tools.registry import ToolRegistry`

#### 🔧 Public Functions (3)

- `def list_tools(user: User = Depends(get_current_user), registry: ToolRegistry = Depends(get_registry))` `router.get('/tools')`
  - *Line: 13*
  - *List all registered tools.*

- `def list_tool_groups(user: User = Depends(get_current_user), registry: ToolRegistry = Depends(get_registry))` `router.get('/tools/groups')`
  - *Line: 31*
  - *List tool groups with their tools.*

- `def toggle_tool_group(group_id: str, user: User = Depends(get_current_user), registry: ToolRegistry = Depends(get_registry), engine: AgentEngine = Depends(get_engine))` `router.post('/tools/groups/{group_id}/toggle')`
  - *Line: 66*
  - *Toggle a tool group's enabled state.*


---

`````python
from fastapi import APIRouter, Depends, Request

from lc_agent.core.engine import AgentEngine
from lc_agent.db.models_auth import User
from lc_agent.server.auth_middleware import get_current_user
from lc_agent.server.dependencies import get_engine, get_registry
from lc_agent.tools.registry import ToolRegistry

router = APIRouter(tags=["tools"])


@router.get("/tools")
def list_tools(
    user: User = Depends(get_current_user),
    registry: ToolRegistry = Depends(get_registry),
):
    """List all registered tools."""
    tools = []
    for name, entry in registry._global_tools.items():
        group = entry["group"]
        tools.append({
            "name": name,
            "group": group,
            "group_description": registry._group_descriptions.get(group, group),
            "description": entry["tool"].description,
        })
    return tools


@router.get("/tools/groups")
def list_tool_groups(
    user: User = Depends(get_current_user),
    registry: ToolRegistry = Depends(get_registry),
):
    """List tool groups with their tools."""
    groups: dict[str, list] = {}
    for name, entry in registry._global_tools.items():
        group_name = entry["group"] or "__ungrouped__"
        if group_name not in groups:
            groups[group_name] = []
        tool_obj = entry["tool"]
        schema = None
        if hasattr(tool_obj, "args_schema") and tool_obj.args_schema:
            try:
                schema = tool_obj.args_schema.model_json_schema()
            except Exception:
                pass
        groups[group_name].append({
            "name": name,
            "description": tool_obj.description,
            "input_schema": schema,
        })
    disabled = registry._disabled_groups
    return [
        {
            "id": group,
            "description": registry._group_descriptions.get(group, group),
            "tools": tools,
            "enabled": group not in disabled,
        }
        for group, tools in sorted(groups.items())
    ]


@router.post("/tools/groups/{group_id}/toggle")
def toggle_tool_group(
    group_id: str,
    user: User = Depends(get_current_user),
    registry: ToolRegistry = Depends(get_registry),
    engine: AgentEngine = Depends(get_engine),
):
    """Toggle a tool group's enabled state."""
    if group_id in registry._disabled_groups:
        registry._disabled_groups.discard(group_id)
        enabled = True
    else:
        registry._disabled_groups.add(group_id)
        enabled = False
    engine._mcp_generation += 1
    return {"id": group_id, "enabled": enabled}

`````

--- **end of file: lc_agent/server/routes/tools.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/server/routes/__init__.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/server/routes/__init__.py`


---

`````python


`````

--- **end of file: lc_agent/server/routes/__init__.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/skills/filtered_loader.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/skills/filtered_loader.py`

#### 📝 Module Docstring

`````
Wrapper around SkillLoader that supports runtime enable/disable toggle.

All skills default to ON.  Disabled skills are tracked in a blacklist set.
`````

#### 📦 Imports

- `from pathlib import Path`
- `from langchain_agentskills.exceptions import SkillNotFoundError`
- `from langchain_agentskills.loaders.base import SkillLoader`
- `from langchain_agentskills.models import SkillContent`
- `from langchain_agentskills.models import SkillMetadata`

#### 🏛️ Classes (1)

##### 📌 `class FilteredSkillLoader(SkillLoader)`
*Line: 14*

**Docstring:**
`````
Delegates to an inner loader but hides disabled skills.

All skills are enabled by default.  Use :meth:`toggle` to flip a
skill's state at runtime.
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, inner: SkillLoader)`
  - **Parameters:**
    - `self`
    - `inner: SkillLoader`

**Public Methods (8):**
- `def is_enabled(self, name: str) -> bool`
- `def toggle(self, name: str) -> bool`
  - *Toggle a skill's enabled state.  Returns the new enabled state.*
- `def list_skills(self) -> list[SkillMetadata]`
- `def list_all_skills(self) -> list[SkillMetadata]`
  - *Return all skills including disabled ones (for UI display).*
- `def load_skill(self, name: str) -> SkillContent`
- `def read_resource(self, skill_name: str, resource_name: str) -> str`
- `def has_skill(self, name: str) -> bool`
- `def read_script(self, skill_name: str, script_name: str) -> Path`

**Properties (1):**
- `@property disabled_skills -> set[str]`


---

`````python
"""Wrapper around SkillLoader that supports runtime enable/disable toggle.

All skills default to ON.  Disabled skills are tracked in a blacklist set.
"""


from pathlib import Path

from langchain_agentskills.exceptions import SkillNotFoundError
from langchain_agentskills.loaders.base import SkillLoader
from langchain_agentskills.models import SkillContent, SkillMetadata


class FilteredSkillLoader(SkillLoader):
    """Delegates to an inner loader but hides disabled skills.

    All skills are enabled by default.  Use :meth:`toggle` to flip a
    skill's state at runtime.
    """

    def __init__(self, inner: SkillLoader) -> None:
        self._inner = inner
        self._disabled: set[str] = set()

    @property
    def disabled_skills(self) -> set[str]:
        return self._disabled

    def is_enabled(self, name: str) -> bool:
        return name not in self._disabled

    def toggle(self, name: str) -> bool:
        """Toggle a skill's enabled state.  Returns the new enabled state."""
        if name in self._disabled:
            self._disabled.discard(name)
            return True
        self._disabled.add(name)
        return False

    def list_skills(self) -> list[SkillMetadata]:
        return [s for s in self._inner.list_skills() if s.name not in self._disabled]

    def list_all_skills(self) -> list[SkillMetadata]:
        """Return all skills including disabled ones (for UI display)."""
        return self._inner.list_skills()

    def load_skill(self, name: str) -> SkillContent:
        if name in self._disabled:
            raise SkillNotFoundError(name)
        return self._inner.load_skill(name)

    def read_resource(self, skill_name: str, resource_name: str) -> str:
        if skill_name in self._disabled:
            raise SkillNotFoundError(skill_name)
        return self._inner.read_resource(skill_name, resource_name)

    def has_skill(self, name: str) -> bool:
        if name in self._disabled:
            return False
        return self._inner.has_skill(name)

    def read_script(self, skill_name: str, script_name: str) -> Path:
        if skill_name in self._disabled:
            raise SkillNotFoundError(skill_name)
        return self._inner.read_script(skill_name, script_name)

`````

--- **end of file: lc_agent/skills/filtered_loader.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/skills/scanner.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/skills/scanner.py`

#### 📦 Imports

- `import hashlib`
- `import re`
- `from dataclasses import dataclass`
- `from pathlib import Path`
- `import yaml`

#### 🏛️ Classes (2)

##### 📌 `class SkillInfo`
*Line: 11*

**Class Variables (6):**
- `name: str`
- `description: str`
- `content: str`
- `file_path: str`
- `group: str = ''`
- `metadata: dict = None`

##### 📌 `class SkillScanner`
*Line: 24*

**Docstring:**
`````
Discovers and parses SKILL.md files from a directory.
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, directories: list[str] | str = './skills')`
  - **Parameters:**
    - `self`
    - `directories: list[str] | str = './skills'`

**Public Methods (5):**
- `def scan(self) -> list[SkillInfo]`
  - **Docstring:**
  `````
  Scan all directories recursively for SKILL.md files.
  
  Increments ``generation`` whenever the scanned content differs from
  the previous scan, so callers can cheaply detect changes.
  `````
- `def get_by_name(self, name: str) -> SkillInfo | None`
  - *Get a skill by name.*
- `def get_filtered(self, allowed: list[str] | None) -> list[SkillInfo]`
  - **Docstring:**
  `````
  Filter skills by allowed list (three-value semantics).
  Also excludes runtime-disabled skills.
  `````
- `def get_groups(self) -> list[str]`
  - *Return unique skill group names.*
- `def get_by_group(self, group: str) -> list[SkillInfo]`
  - *Get all skills in a specific group.*

**Properties (1):**
- `@property skills -> list[SkillInfo]`


---

`````python

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class SkillInfo:
    name: str
    description: str
    content: str
    file_path: str
    group: str = ""
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SkillScanner:
    """Discovers and parses SKILL.md files from a directory."""

    def __init__(self, directories: list[str] | str = "./skills"):
        if isinstance(directories, str):
            directories = [directories]
        self.directories = [Path(d) for d in directories]
        self._skills: list[SkillInfo] = []
        self._disabled_skills: set[str] = set()
        self._content_hash: str = ""
        self.generation: int = 0

    @property
    def skills(self) -> list[SkillInfo]:
        return self._skills

    def scan(self) -> list[SkillInfo]:
        """Scan all directories recursively for SKILL.md files.

        Increments ``generation`` whenever the scanned content differs from
        the previous scan, so callers can cheaply detect changes.
        """
        self._skills = []
        seen_names: set[str] = set()

        for directory in self.directories:
            if not directory.exists():
                continue
            for skill_file in directory.rglob("SKILL.md"):
                skill = self._parse_skill(skill_file)
                if skill and skill.name not in seen_names:
                    self._skills.append(skill)
                    seen_names.add(skill.name)

        new_hash = hashlib.md5(
            "|".join(f"{s.name}:{s.content}" for s in self._skills).encode()
        ).hexdigest()
        if new_hash != self._content_hash:
            self._content_hash = new_hash
            self.generation += 1

        return self._skills

    def _parse_skill(self, path: Path) -> SkillInfo | None:
        """Parse a SKILL.md file with YAML frontmatter."""
        try:
            text = path.read_text(encoding="utf-8-sig")
            frontmatter, content = self._split_frontmatter(text)

            name = frontmatter.get("name", path.parent.name)
            description = frontmatter.get("description", "")
            metadata = frontmatter.get("metadata", {}) or {}
            group = metadata.get("group", "")

            return SkillInfo(
                name=name,
                description=description,
                content=content.strip(),
                file_path=str(path),
                group=group,
                metadata=metadata,
            )
        except Exception:
            return None

    def _split_frontmatter(self, text: str) -> tuple[dict, str]:
        """Split YAML frontmatter from markdown content."""
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
        if match:
            fm = yaml.safe_load(match.group(1)) or {}
            return fm, match.group(2)
        return {}, text

    def get_by_name(self, name: str) -> SkillInfo | None:
        """Get a skill by name."""
        for skill in self._skills:
            if skill.name == name:
                return skill
        return None

    def get_filtered(self, allowed: list[str] | None) -> list[SkillInfo]:
        """Filter skills by allowed list (three-value semantics).
        Also excludes runtime-disabled skills.
        """
        if allowed is None:
            skills = self._skills
        elif not allowed:
            return []
        else:
            skills = [s for s in self._skills if s.name in allowed]

        if self._disabled_skills:
            skills = [s for s in skills if s.name not in self._disabled_skills]
        return skills

    def get_groups(self) -> list[str]:
        """Return unique skill group names."""
        groups = set()
        for s in self._skills:
            if s.group:
                groups.add(s.group)
        return sorted(groups)

    def get_by_group(self, group: str) -> list[SkillInfo]:
        """Get all skills in a specific group."""
        return [s for s in self._skills if s.group == group]

`````

--- **end of file: lc_agent/skills/scanner.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/skills/script_executor.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/skills/script_executor.py`

#### 📦 Imports

- `import platform`
- `import shutil`
- `import subprocess`
- `import sys`
- `from pathlib import Path`
- `from langchain_agentskills import SkillsToolkit`
- `from langchain_agentskills.exceptions import SkillScriptExecutionError`
- `from langchain_agentskills.executor import ScriptExecutor`

#### 🏛️ Classes (1)

##### 📌 `class WindowsScriptExecutor(ScriptExecutor)`
*Line: 12*

**Docstring:**
`````
Run interpreter-based skill scripts with their required Windows runtime.
`````

**Public Methods (1):**
- `def run(self, script_path: Path, args: list[str] | None = None, timeout: int | None = None) -> str`

#### 🔧 Public Functions (1)

- `def patch_windows_script_executor(toolkit: SkillsToolkit) -> None`
  - *Line: 89*
  - *Replace the third-party default executor only for Windows processes.*


---

`````python
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from langchain_agentskills import SkillsToolkit
from langchain_agentskills.exceptions import SkillScriptExecutionError
from langchain_agentskills.executor import ScriptExecutor


class WindowsScriptExecutor(ScriptExecutor):
    """Run interpreter-based skill scripts with their required Windows runtime."""

    def run(
        self,
        script_path: Path,
        args: list[str] | None = None,
        timeout: int | None = None,
    ) -> str:
        effective_timeout = timeout if timeout is not None else self._timeout
        script_name = script_path.name

        if not script_path.is_file():
            raise SkillScriptExecutionError(f"Script not found: {script_path}")

        command = self._build_command(script_path)
        if args:
            command.extend(args)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=str(script_path.parent),
            )
        except subprocess.TimeoutExpired:
            raise SkillScriptExecutionError(
                f"Script '{script_name}' timed out after {effective_timeout}s"
            )
        except OSError as exc:
            raise SkillScriptExecutionError(f"Failed to execute script '{script_name}': {exc}")

        output = result.stdout
        if result.returncode != 0:
            output += f"\n[stderr]\n{result.stderr}" if result.stderr else ""
            raise SkillScriptExecutionError(
                f"Script '{script_name}' exited with code {result.returncode}:\n{output}"
            )

        return output

    @staticmethod
    def _build_command(script_path: Path) -> list[str]:
        suffix = script_path.suffix.lower()
        script = str(script_path)

        if suffix == ".py":
            return [sys.executable, script]
        if suffix == ".js":
            return [_find_runtime("node", script_path), script]
        if suffix == ".ps1":
            return [
                _find_runtime("powershell", script_path),
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                script,
            ]
        if suffix == ".sh":
            return [_find_runtime("bash", script_path), script]

        return [script]


def _find_runtime(name: str, script_path: Path) -> str:
    runtime = shutil.which(name)
    if runtime:
        return runtime
    raise SkillScriptExecutionError(
        f"Script '{script_path.name}' requires '{name}', but it was not found on PATH"
    )


def patch_windows_script_executor(toolkit: SkillsToolkit) -> None:
    """Replace the third-party default executor only for Windows processes."""
    if platform.system() != "Windows":
        return
    toolkit._executor = WindowsScriptExecutor(timeout=toolkit.script_timeout)

`````

--- **end of file: lc_agent/skills/script_executor.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/skills/__init__.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/skills/__init__.py`

#### 📦 Imports

- `from lc_agent.skills.scanner import SkillInfo`
- `from lc_agent.skills.scanner import SkillScanner`


---

`````python
from lc_agent.skills.scanner import SkillInfo, SkillScanner

__all__ = ["SkillInfo", "SkillScanner"]

`````

--- **end of file: lc_agent/skills/__init__.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/tools/builtin.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/tools/builtin.py`


---

`````python
# lc_agent/tools/builtin.py
# Tools migrated to lc_agent/tools/contrib_tools/

`````

--- **end of file: lc_agent/tools/builtin.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/tools/registry.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/tools/registry.py`

#### 📦 Imports

- `import asyncio`
- `import functools`
- `import inspect`
- `import re`
- `from typing import Any`
- `from typing import Callable`
- `from typing import Literal`
- `from typing import overload`
- `from langchain_core.runnables import Runnable`
- `from langchain_core.tools import BaseTool`
- `from langchain_core.tools import StructuredTool`
- `from langchain_core.tools.base import ArgsSchema`

#### 🏛️ Classes (1)

##### 📌 `class ToolRegistry`
*Line: 16*

**Docstring:**
`````
Central registry for all tools, supporting groups and filtering.
`````

**Public Methods (6):**
- `def get_all_tools(self) -> list[BaseTool]`
  - *Return all registered tools as LangChain BaseTool instances.*
- `def get_tools_by_groups(self, groups: list[str]) -> list[BaseTool]`
  - *Return tools belonging to specified groups.*
- `def get_filtered_tools(self, allowed_groups: list[str] | None) -> list[BaseTool]`
  - **Docstring:**
  `````
  Filter tools by allowed groups (three-value semantics).
  
  None = all allowed, [] = none allowed, ["a","b"] = only those groups.
  Also excludes runtime-disabled groups.
  `````
- `def get_group_names(self) -> list[str]`
  - *Return unique list of all registered group names.*
- `def get_group_info(self) -> list[dict[str, str]]`
  - *Return group id + description pairs.*
- `def register(self, func: Callable) -> BaseTool`
  - **Docstring:**
  `````
  Register a function as a tool.
  
  Accepts all official langchain_core @tool parameters plus lc-agent
  extensions (group, group_description).
  
  Args:
      func: The function to register.
      name: Explicit tool name.  Priority: name > group__func_name > func_name.
      group: ASCII group id for filtering.  Must match ^[a-zA-Z0-9_-]+$.
      group_description: Human-readable group label for the UI.
      description: Override tool description (otherwise uses docstring).
      return_direct: Return result directly without continuing agent loop.
      args_schema: Custom Pydantic schema for tool input.
      infer_schema: Infer schema from function signature.
      response_format: ``"content"`` or ``"content_and_artifact"``.
      parse_docstring: Parse param descriptions from Google-style docstring.
      error_on_invalid_docstring: Raise on bad docstring when parse_docstring=True.
      extras: Provider-specific extra fields (e.g. Anthropic cache_control).
  `````

**Class Variables (4):**
- `_instance: 'ToolRegistry | None' = None`
- `_global_tools: dict[str, dict[str, Any]] = {}`
- `_group_descriptions: dict[str, str] = {}`
- `_disabled_groups: set[str] = set()`

#### 🔧 Public Functions (7)

- `def tool() -> Callable` `overload`
  - *Line: 172*

- `def tool(name_or_callable: str) -> Callable[[Callable], Callable]` `overload`
  - *Line: 175*

- `def tool() -> Callable[[Callable], Callable]` `overload`
  - *Line: 191*

- `def tool(name_or_callable: str | Callable | None = None)`
  - *Line: 207*
  - **Docstring:**
  `````
  Register a function as an agent tool.
  
  Fully compatible with ``langchain_core.tools.convert.tool`` parameter
  names and calling conventions, with additional ``group`` / ``group_description``
  extensions for lc-agent's tool-group system.
  
  Supported calling patterns (same as official @tool)::
  
      @tool                                   # bare decorator
      def my_func(...): ...
  
      @tool("custom_name")                    # positional string → name
      def my_func(...): ...
  
      @tool(name="ask_user")                  # keyword name
      def ask_user_impl(...): ...
  
      @tool(description="...", parse_docstring=True)
      def my_func(...): ...
  
  lc-agent extensions::
  
      @tool(group="file_mgmt", group_description="文件管理")
      def my_func(...): ...
  
  Name resolution: name (kwarg) > name_or_callable (str) > group__func > func.
  `````

- `def decorator(fn: Callable) -> Callable`
  - *Line: 255*

- `def sync_wrapper(*args, **kwargs)` `functools.wraps(fn)`
  - *Line: 272*

- `async def async_wrapper(*args, **kwargs)` `functools.wraps(fn)`
  - *Line: 276*


---

`````python
# lc_agent/tools/registry.py

import asyncio
import functools
import inspect
import re
from typing import Any, Callable, Literal, overload

from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool, StructuredTool
from langchain_core.tools.base import ArgsSchema

_TOOL_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


class ToolRegistry:
    """Central registry for all tools, supporting groups and filtering."""

    _instance: 'ToolRegistry | None' = None
    _global_tools: dict[str, dict[str, Any]] = {}
    _group_descriptions: dict[str, str] = {}
    _disabled_groups: set[str] = set()

    def __new__(cls) -> 'ToolRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_all_tools(self) -> list[BaseTool]:
        """Return all registered tools as LangChain BaseTool instances."""
        return [entry["tool"] for entry in self._global_tools.values()]

    def get_tools_by_groups(self, groups: list[str]) -> list[BaseTool]:
        """Return tools belonging to specified groups."""
        return [
            entry["tool"]
            for entry in self._global_tools.values()
            if entry["group"] in groups
        ]

    def get_filtered_tools(self, allowed_groups: list[str] | None) -> list[BaseTool]:
        """Filter tools by allowed groups (three-value semantics).

        None = all allowed, [] = none allowed, ["a","b"] = only those groups.
        Also excludes runtime-disabled groups.
        """
        if allowed_groups is None:
            tools = self.get_all_tools()
        elif not allowed_groups:
            return []
        else:
            tools = self.get_tools_by_groups(allowed_groups)

        if self._disabled_groups:
            tools = [
                t for t in tools
                if self._global_tools.get(t.name, {}).get("group") not in self._disabled_groups
            ]
        return tools

    def get_group_names(self) -> list[str]:
        """Return unique list of all registered group names."""
        groups = set()
        for entry in self._global_tools.values():
            if entry["group"]:
                groups.add(entry["group"])
        return sorted(groups)

    def get_group_info(self) -> list[dict[str, str]]:
        """Return group id + description pairs."""
        groups = {}
        for entry in self._global_tools.values():
            g = entry["group"]
            if g and g not in groups:
                groups[g] = self._group_descriptions.get(g, g)
        return [{"id": gid, "description": desc} for gid, desc in sorted(groups.items())]

    def register(
        self,
        func: Callable,
        *,
        name: str = "",
        group: str = "",
        group_description: str = "",
        description: str | None = None,
        return_direct: bool = False,
        args_schema: ArgsSchema | None = None,
        infer_schema: bool = True,
        response_format: Literal["content", "content_and_artifact"] = "content",
        parse_docstring: bool = False,
        error_on_invalid_docstring: bool = True,
        extras: dict[str, Any] | None = None,
    ) -> BaseTool:
        """Register a function as a tool.

        Accepts all official langchain_core @tool parameters plus lc-agent
        extensions (group, group_description).

        Args:
            func: The function to register.
            name: Explicit tool name.  Priority: name > group__func_name > func_name.
            group: ASCII group id for filtering.  Must match ^[a-zA-Z0-9_-]+$.
            group_description: Human-readable group label for the UI.
            description: Override tool description (otherwise uses docstring).
            return_direct: Return result directly without continuing agent loop.
            args_schema: Custom Pydantic schema for tool input.
            infer_schema: Infer schema from function signature.
            response_format: ``"content"`` or ``"content_and_artifact"``.
            parse_docstring: Parse param descriptions from Google-style docstring.
            error_on_invalid_docstring: Raise on bad docstring when parse_docstring=True.
            extras: Provider-specific extra fields (e.g. Anthropic cache_control).
        """
        if group and not _TOOL_NAME_PATTERN.match(group):
            raise ValueError(
                f"Tool group '{group}' must match ^[a-zA-Z0-9_-]+$. "
                f"Use ASCII for 'group' and put display name in 'group_description'."
            )
        if name and not _TOOL_NAME_PATTERN.match(name):
            raise ValueError(
                f"Tool name '{name}' must match ^[a-zA-Z0-9_-]+$."
            )

        if name:
            resolved_name = name
        elif group:
            resolved_name = f"{group}__{func.__name__}"
        else:
            resolved_name = func.__name__

        if resolved_name in self._global_tools:
            existing = self._global_tools[resolved_name]["func"]
            raise ValueError(
                f"Tool name '{resolved_name}' already registered by "
                f"{existing.__module__}.{existing.__qualname__}. "
                f"Use a different name or group to avoid collision."
            )

        if group and group_description:
            self._group_descriptions[group] = group_description

        from_fn_kwargs: dict[str, Any] = {
            "name": resolved_name,
            "description": description or func.__doc__ or f"Tool: {resolved_name}",
            "return_direct": return_direct,
            "infer_schema": infer_schema,
            "response_format": response_format,
            "parse_docstring": parse_docstring,
            "error_on_invalid_docstring": error_on_invalid_docstring,
        }
        if args_schema is not None:
            from_fn_kwargs["args_schema"] = args_schema

        if inspect.iscoroutinefunction(func):
            from_fn_kwargs["coroutine"] = func
        else:
            from_fn_kwargs["func"] = func

        lc_tool = StructuredTool.from_function(**from_fn_kwargs)

        if extras:
            lc_tool.metadata = {**(lc_tool.metadata or {}), "extras": extras}

        self._global_tools[resolved_name] = {"tool": lc_tool, "group": group, "func": func}
        return lc_tool


# ---------------------------------------------------------------------------
# @tool decorator — fully compatible with langchain_core.tools.convert.tool
# ---------------------------------------------------------------------------

@overload
def tool(name_or_callable: Callable, /) -> Callable: ...

@overload
def tool(
    name_or_callable: str,
    *,
    description: str | None = ...,
    return_direct: bool = ...,
    args_schema: ArgsSchema | None = ...,
    infer_schema: bool = ...,
    response_format: Literal["content", "content_and_artifact"] = ...,
    parse_docstring: bool = ...,
    error_on_invalid_docstring: bool = ...,
    extras: dict[str, Any] | None = ...,
    group: str = ...,
    group_description: str = ...,
) -> Callable[[Callable], Callable]: ...

@overload
def tool(
    *,
    name: str = ...,
    description: str | None = ...,
    return_direct: bool = ...,
    args_schema: ArgsSchema | None = ...,
    infer_schema: bool = ...,
    response_format: Literal["content", "content_and_artifact"] = ...,
    parse_docstring: bool = ...,
    error_on_invalid_docstring: bool = ...,
    extras: dict[str, Any] | None = ...,
    group: str = ...,
    group_description: str = ...,
) -> Callable[[Callable], Callable]: ...


def tool(
    name_or_callable: str | Callable | None = None,
    *,
    name: str = "",
    description: str | None = None,
    return_direct: bool = False,
    args_schema: ArgsSchema | None = None,
    infer_schema: bool = True,
    response_format: Literal["content", "content_and_artifact"] = "content",
    parse_docstring: bool = False,
    error_on_invalid_docstring: bool = True,
    extras: dict[str, Any] | None = None,
    group: str = "",
    group_description: str = "",
):
    """Register a function as an agent tool.

    Fully compatible with ``langchain_core.tools.convert.tool`` parameter
    names and calling conventions, with additional ``group`` / ``group_description``
    extensions for lc-agent's tool-group system.

    Supported calling patterns (same as official @tool)::

        @tool                                   # bare decorator
        def my_func(...): ...

        @tool("custom_name")                    # positional string → name
        def my_func(...): ...

        @tool(name="ask_user")                  # keyword name
        def ask_user_impl(...): ...

        @tool(description="...", parse_docstring=True)
        def my_func(...): ...

    lc-agent extensions::

        @tool(group="file_mgmt", group_description="文件管理")
        def my_func(...): ...

    Name resolution: name (kwarg) > name_or_callable (str) > group__func > func.
    """
    registry = ToolRegistry()

    resolved_name = name
    if not resolved_name and isinstance(name_or_callable, str):
        resolved_name = name_or_callable

    def decorator(fn: Callable) -> Callable:
        registry.register(
            fn,
            name=resolved_name,
            group=group,
            group_description=group_description,
            description=description,
            return_direct=return_direct,
            args_schema=args_schema,
            infer_schema=infer_schema,
            response_format=response_format,
            parse_docstring=parse_docstring,
            error_on_invalid_docstring=error_on_invalid_docstring,
            extras=extras,
        )

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            return await fn(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(fn) else sync_wrapper

    if callable(name_or_callable):
        return decorator(name_or_callable)
    return decorator

`````

--- **end of file: lc_agent/tools/registry.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/tools/__init__.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/tools/__init__.py`

#### 📦 Imports

- `from lc_agent.tools.registry import ToolRegistry`
- `from lc_agent.tools.registry import tool`


---

`````python
# lc_agent/tools/__init__.py
from lc_agent.tools.registry import ToolRegistry, tool

__all__ = ["ToolRegistry", "tool"]

`````

--- **end of file: lc_agent/tools/__init__.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/tools/contrib_tools/ask_user_tool.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/tools/contrib_tools/ask_user_tool.py`

#### 📦 Imports

- `from typing import Annotated`
- `from langgraph.types import interrupt`
- `from lc_agent.tools.registry import tool`

#### 🔧 Public Functions (1)

- `def ask_user(question: Annotated[str, "向用户展示的问题文本。应清晰简洁，直接表达你需要用户提供的信息或做出的决定。示例：'您希望报告覆盖哪个时间段？' / '确认要删除这条记录吗？'"], options: Annotated[list[str] | None, "候选选项列表，将按 A/B/C/D 顺序展示给用户点选。仅在答案范围有限且可枚举时提供（建议 2~6 项）；若用户需要自由填写则不传。示例：['本月', '本季度', '自定义时间段']"] = None, allow_multiple: Annotated[bool, '是否允许用户同时勾选多个选项。True=多选，False=单选（默认）。仅在 options 不为空时有意义。场景示例：让用户勾选多个偏好标签时传 True。'] = False, allow_free_input: Annotated[bool, '是否允许用户在选项之外输入自定义文字。True（默认）=点选与自由输入均可；False=强制仅能从 options 中点选，适合需要受控输入的场景。'] = True) -> str` `tool(name='ask_user', group='utility', group_description='通用工具')`
  - *Line: 10*
  - **Docstring:**
  `````
  向用户提问并获取回答。
  
  当你需要以下情形时使用此工具：
  - 关键信息缺失，无法从上下文推断，必须由用户补充（自由输入，不传 options）
  - 需要用户从有限方案中做单选或多选（传 options）
  - 需要用户确认一个不可逆操作（如删除、发送）
  
  
  返回值：用户回答的原始文本；若传了 options，返回内容还会附带选项 ID 与文本的对照表（格式：A=选项文本）。
  `````


---

`````python
# lc_agent/tools/contrib_tools/ask_user_tool.py
from typing import Annotated

from langgraph.types import interrupt

from lc_agent.tools.registry import tool


@tool(name="ask_user", group="utility", group_description="通用工具")
def ask_user(
    question: Annotated[
        str,
        (
            "向用户展示的问题文本。应清晰简洁，直接表达你需要用户提供的信息或做出的决定。"
            "示例：'您希望报告覆盖哪个时间段？' / '确认要删除这条记录吗？'"
        ),
    ],
    options: Annotated[
        list[str] | None,
        (
            "候选选项列表，将按 A/B/C/D 顺序展示给用户点选。"
            "仅在答案范围有限且可枚举时提供（建议 2~6 项）；若用户需要自由填写则不传。"
            "示例：['本月', '本季度', '自定义时间段']"
        ),
    ] = None,
    allow_multiple: Annotated[
        bool,
        (
            "是否允许用户同时勾选多个选项。True=多选，False=单选（默认）。"
            "仅在 options 不为空时有意义。场景示例：让用户勾选多个偏好标签时传 True。"
        ),
    ] = False,
    allow_free_input: Annotated[
        bool,
        (
            "是否允许用户在选项之外输入自定义文字。True（默认）=点选与自由输入均可；"
            "False=强制仅能从 options 中点选，适合需要受控输入的场景。"
        ),
    ] = True,
) -> str:
    """向用户提问并获取回答。

    当你需要以下情形时使用此工具：
    - 关键信息缺失，无法从上下文推断，必须由用户补充（自由输入，不传 options）
    - 需要用户从有限方案中做单选或多选（传 options）
    - 需要用户确认一个不可逆操作（如删除、发送）


    返回值：用户回答的原始文本；若传了 options，返回内容还会附带选项 ID 与文本的对照表（格式：A=选项文本）。
    """
    payload: dict = {
        "type": "ask_user",
        "question": question,
        "allow_multiple": allow_multiple,
        "allow_free_input": allow_free_input,
    }
    option_map: dict[str, str] = {}
    if options:
        payload["options"] = [
            {"id": chr(65 + i), "label": opt}
            for i, opt in enumerate(options)
        ]
        option_map = {chr(65 + i): opt for i, opt in enumerate(options)}

    raw_answer: str = interrupt(payload)

    if not option_map:
        return raw_answer

    mapping_lines = "\n".join(f"{k}={v}" for k, v in option_map.items())
    return f"用户回答: {raw_answer}\n选项对照:\n{mapping_lines}"

`````

--- **end of file: lc_agent/tools/contrib_tools/ask_user_tool.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/tools/contrib_tools/get_time.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/tools/contrib_tools/get_time.py`

#### 📦 Imports

- `from datetime import datetime`
- `from typing import Annotated`
- `from zoneinfo import ZoneInfo`
- `from lc_agent.tools.registry import tool`

#### 🔧 Public Functions (1)

- `def get_current_time(timezone: Annotated[str, 'IANA 标准时区名称。示例：Asia/Shanghai（北京时间）、America/New_York（纽约）、Europe/London（伦敦）、UTC（协调世界时）。默认 Asia/Shanghai。'] = 'Asia/Shanghai') -> str` `tool(name='get_current_time', group='utility', group_description='通用工具', description="获取指定时区的当前实时日期和时间，返回格式为 'YYYY-MM-DD HH:MM:SS (时区名)'。当用户提问隐含或显含当前时间的情况下，必须先调用此工具获取准确时间后再回答，不可凭训练知识估算当前时间。触发场景示例：'现在几点' '今天几号' '今天星期几' '本月/这个月有什么' '今年/今天发生了什么' '最近/近期/当前的XX情况' '这周/本周计划' 以及任何需要知道当前日期才能正确作答的问题。")`
  - *Line: 20*


---

`````python
# lc_agent/tools/contrib_tools/get_time.py
from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from lc_agent.tools.registry import tool


@tool(
    name="get_current_time",
    group="utility",
    group_description="通用工具",
    description=(
        "获取指定时区的当前实时日期和时间，返回格式为 'YYYY-MM-DD HH:MM:SS (时区名)'。"
        "当用户提问隐含或显含当前时间的情况下，必须先调用此工具获取准确时间后再回答，不可凭训练知识估算当前时间。"
        "触发场景示例：'现在几点' '今天几号' '今天星期几' '本月/这个月有什么' '今年/今天发生了什么' "
        "'最近/近期/当前的XX情况' '这周/本周计划' 以及任何需要知道当前日期才能正确作答的问题。"
    ),
)
def get_current_time(
    timezone: Annotated[
        str,
        "IANA 标准时区名称。示例：Asia/Shanghai（北京时间）、America/New_York（纽约）、Europe/London（伦敦）、UTC（协调世界时）。默认 Asia/Shanghai。",
    ] = "Asia/Shanghai",
) -> str:
    try:
        tz = ZoneInfo(timezone)
    except (KeyError, ValueError):
        return f"错误: 无效的时区 '{timezone}'。请使用 IANA 时区格式，如 Asia/Shanghai、UTC。"
    now = datetime.now(tz)
    return f"{now.strftime('%Y-%m-%d %H:%M:%S')} ({timezone})"

`````

--- **end of file: lc_agent/tools/contrib_tools/get_time.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/tools/contrib_tools/__init__.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/tools/contrib_tools/__init__.py`

#### 📦 Imports

- `import lc_agent.tools.contrib_tools.ask_user_tool`
- `import lc_agent.tools.contrib_tools.get_time`


---

`````python
# lc_agent/tools/contrib_tools/__init__.py
import lc_agent.tools.contrib_tools.ask_user_tool  # noqa: F401
import lc_agent.tools.contrib_tools.get_time  # noqa: F401

`````

--- **end of file: lc_agent/tools/contrib_tools/__init__.py** (project: lc_agent) --- 

---


--- **start of file: lc_agent/utils/loggers.py** (project: lc_agent) --- 


### 📄 Python File Metadata: `lc_agent/utils/loggers.py`

#### 📦 Imports

- `import logging`


---

`````python
import logging

app_logger = logging.getLogger("lc_agent.app")
server_logger = logging.getLogger("lc_agent.server")
db_logger = logging.getLogger("lc_agent.db")
desktop_logger = logging.getLogger("lc_agent.desktop")
debug_logger = logging.getLogger("lc_agent.debug")
mcp_logger = logging.getLogger("lc_agent.mcp")
`````

--- **end of file: lc_agent/utils/loggers.py** (project: lc_agent) --- 

---

# markdown content namespace: lc_agent 前端源码 (Vue 3) 


## lc_agent File Tree (relative dir: `frontend/src`)


`````

└── frontend
    └── src
        ├── App.vue
        ├── api
        │   ├── auth.ts
        │   ├── http.ts
        │   ├── permissions.ts
        │   └── sse-client.ts
        ├── components
        │   ├── chat
        │   │   ├── ChatBubble.vue
        │   │   ├── ChatInput.vue
        │   │   ├── CodeBlockModal.vue
        │   │   ├── CopyRoundsButton.vue
        │   │   ├── HttpTraceBlock.vue
        │   │   ├── HttpTracesGroup.vue
        │   │   ├── InterruptDialog.vue
        │   │   ├── MessageToolbar.vue
        │   │   ├── SubAgentCard.vue
        │   │   ├── TodoProgressCard.vue
        │   │   ├── TokenUsagePanel.vue
        │   │   └── ToolCallCard.vue
        │   ├── dialogs
        │   │   ├── AgentEditorDialog.vue
        │   │   └── ChangePasswordDialog.vue
        │   ├── layout
        │   │   ├── AppHeader.vue
        │   │   ├── LeftSidebar.vue
        │   │   └── RightPanel.vue
        │   ├── panels
        │   │   ├── DetailModal.vue
        │   │   ├── ModelSelector.vue
        │   │   ├── TodoList.vue
        │   │   └── ToolGroupPanel.vue
        │   └── settings
        │       └── PermissionsPanel.vue
        ├── composables
        │   ├── useMarkdownTheme.ts
        │   └── useTheme.ts
        ├── main.ts
        ├── router
        │   └── index.ts
        ├── stores
        │   ├── agents.ts
        │   ├── auth.ts
        │   ├── chat-session-state.ts
        │   ├── chat.ts
        │   ├── sessions.ts
        │   └── tools.ts
        ├── utils
        │   ├── client-id.ts
        │   ├── copy-markdown.ts
        │   ├── fileUpload.ts
        │   └── markdown.ts
        └── views
            ├── AdminView.vue
            ├── ChatView.vue
            ├── LoginView.vue
            └── TestSegments.vue

`````

---


## lc_agent (relative dir: `frontend/src`)  Included Files (total: 45 files)


- `frontend/src/App.vue`

- `frontend/src/main.ts`

- `frontend/src/api/auth.ts`

- `frontend/src/api/http.ts`

- `frontend/src/api/permissions.ts`

- `frontend/src/api/sse-client.ts`

- `frontend/src/components/chat/ChatBubble.vue`

- `frontend/src/components/chat/ChatInput.vue`

- `frontend/src/components/chat/CodeBlockModal.vue`

- `frontend/src/components/chat/CopyRoundsButton.vue`

- `frontend/src/components/chat/HttpTraceBlock.vue`

- `frontend/src/components/chat/HttpTracesGroup.vue`

- `frontend/src/components/chat/InterruptDialog.vue`

- `frontend/src/components/chat/MessageToolbar.vue`

- `frontend/src/components/chat/SubAgentCard.vue`

- `frontend/src/components/chat/TodoProgressCard.vue`

- `frontend/src/components/chat/TokenUsagePanel.vue`

- `frontend/src/components/chat/ToolCallCard.vue`

- `frontend/src/components/dialogs/AgentEditorDialog.vue`

- `frontend/src/components/dialogs/ChangePasswordDialog.vue`

- `frontend/src/components/layout/AppHeader.vue`

- `frontend/src/components/layout/LeftSidebar.vue`

- `frontend/src/components/layout/RightPanel.vue`

- `frontend/src/components/panels/DetailModal.vue`

- `frontend/src/components/panels/ModelSelector.vue`

- `frontend/src/components/panels/TodoList.vue`

- `frontend/src/components/panels/ToolGroupPanel.vue`

- `frontend/src/components/settings/PermissionsPanel.vue`

- `frontend/src/composables/useMarkdownTheme.ts`

- `frontend/src/composables/useTheme.ts`

- `frontend/src/router/index.ts`

- `frontend/src/stores/agents.ts`

- `frontend/src/stores/auth.ts`

- `frontend/src/stores/chat-session-state.ts`

- `frontend/src/stores/chat.ts`

- `frontend/src/stores/sessions.ts`

- `frontend/src/stores/tools.ts`

- `frontend/src/utils/client-id.ts`

- `frontend/src/utils/copy-markdown.ts`

- `frontend/src/utils/fileUpload.ts`

- `frontend/src/utils/markdown.ts`

- `frontend/src/views/AdminView.vue`

- `frontend/src/views/ChatView.vue`

- `frontend/src/views/LoginView.vue`

- `frontend/src/views/TestSegments.vue`


---


--- **start of file: frontend/src/App.vue** (project: lc_agent) --- 

`````vue
<template>
  <ConfigProvider :theme="isDark ? 'dark' : 'light'">
    <router-view v-if="isPublicRoute" />
    <div v-else class="app-container">
    <AppHeader
      :app-name="appName"
      :model-name="agentsStore.isCodeAgent ? '代码内定义' : (toolsStore.currentModel || agentsStore.currentAgent?.default_model || 'N/A')"
      @edit-agent="editCurrentAgent"
      @new-agent="createNewAgent"
      @new-chat="handleNewChat"
      @change-agent="handleAgentChange"
      @open-mobile-sidebar="openMobileLeft"
      @open-mobile-tools="openMobileRight"
    />

    <div
      v-if="mobileLeftOpen || mobileRightOpen"
      class="mobile-drawer-backdrop"
      @click="closeMobileDrawers"
    />

    <div
      class="app-body"
      :class="{
        'mobile-left-open': mobileLeftOpen,
        'mobile-right-open': mobileRightOpen,
      }"
    >
      <LeftSidebar
        class="mobile-left-panel"
        :class="{ 'is-mobile-open': mobileLeftOpen }"
        :collapsed="mobileLeftOpen ? false : sidebarCollapsed"
        @new-chat="handleNewChat"
        @switch-session="handleSwitchSession"
        @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
      />

      <main class="chat-main">
        <router-view />
      </main>

      <RightPanel
        class="mobile-right-panel"
        :class="{ 'is-mobile-open': mobileRightOpen }"
      />
    </div>

    <AgentEditorDialog ref="agentEditorRef" />
    </div>
  </ConfigProvider>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ConfigProvider } from 'vue-element-plus-x'
import { useTheme } from '@/composables/useTheme'
import { api } from '@/api/http'
import { useChatStore } from '@/stores/chat'
import { useToolsStore } from '@/stores/tools'
import { useAgentsStore } from '@/stores/agents'
import { useSessionsStore } from '@/stores/sessions'
import AppHeader from '@/components/layout/AppHeader.vue'
import LeftSidebar from '@/components/layout/LeftSidebar.vue'
import RightPanel from '@/components/layout/RightPanel.vue'
import AgentEditorDialog from '@/components/dialogs/AgentEditorDialog.vue'

const { isDark } = useTheme()

const router = useRouter()
const route = useRoute()
const chatStore = useChatStore()
const toolsStore = useToolsStore()
const agentsStore = useAgentsStore()
const sessionsStore = useSessionsStore()
const agentEditorRef = ref<InstanceType<typeof AgentEditorDialog>>()
const sidebarCollapsed = ref(false)
const mobileLeftOpen = ref(false)
const mobileRightOpen = ref(false)
const appName = ref('lc_agent')

const isPublicRoute = computed(() => !!route.meta.public)
const appInitialized = ref(false)

async function initApp() {
  if (appInitialized.value || isPublicRoute.value) return
  appInitialized.value = true

  await Promise.all([
    toolsStore.init(),
    agentsStore.init(),
    sessionsStore.init(),
  ])

  try {
    const health = await api.health()
    if (health.app_name?.trim()) {
      appName.value = health.app_name.trim()
      document.title = health.app_name.trim()
    }
  } catch (e) {
    console.error('[App] Failed to fetch app name:', e)
  }

  const sessionId = route.params.sessionId as string
  if (sessionId) {
    await restoreSession(sessionId)
    return
  }

  const routeSessionId = typeof sessionId === 'string' ? sessionId : ''
  const agentQuery = route.query.agent as string
  if (routeSessionId && agentQuery && agentsStore.agents.find(a => a.id === agentQuery)) {
    const sessionModel = getSessionModelForAgent(agentQuery)
    sessionsStore.ensureLocalSession(routeSessionId, agentQuery, sessionModel)
    sessionsStore.selectSession(routeSessionId)
    if (agentQuery !== agentsStore.currentAgentId) {
      await agentsStore.selectAgent(agentQuery)
    }
    applySessionModel(sessionModel)
    return
  }

  if (agentQuery && agentsStore.agents.find(a => a.id === agentQuery)) {
    await agentsStore.selectAgent(agentQuery)
  }
}


function getSessionModelForAgent(agentId: string): string {
  const agent = agentsStore.agents.find(a => a.id === agentId)
  if (agent?.source === 'code') return ''
  return agent?.default_model || toolsStore.currentModel || ''
}

function getCurrentRightPanelModelForAgent(agentId: string): string {
  const agent = agentsStore.agents.find(a => a.id === agentId)
  if (agent?.source === 'code') return ''
  return toolsStore.currentModel || agent?.default_model || ''
}

function applySessionModel(model: string) {
  if (model) {
    toolsStore.setModel(model)
  }
}

onMounted(async () => {
  await initApp()
})

watch(isPublicRoute, async (isPublic) => {
  if (!isPublic) {
    appInitialized.value = false
    await initApp()
  }
})

watch(() => route.params.sessionId, (newId) => {
  if (newId && typeof newId === 'string') {
    restoreSession(newId)
  }
})

async function restoreSession(sessionId: string) {
  if (chatStore.threadId === sessionId && chatStore.isConnected) return
  const session = sessionsStore.sessions.find(s => s.id === sessionId)
  if (session) {
    sessionsStore.selectSession(sessionId)
    if (session.agent_id && session.agent_id !== agentsStore.currentAgentId) {
      await agentsStore.selectAgent(session.agent_id)
    }
    const sessionAgent = agentsStore.agents.find(a => a.id === session.agent_id)
    if (sessionAgent?.source === 'code') {
      toolsStore.syncModelWithAgentDefault()
    } else if (session.model) {
      toolsStore.setModel(session.model)
    }
    await chatStore.switchToSession(sessionId)
    return
  }

  const agentQuery = route.query.agent as string
  if (agentQuery && agentsStore.agents.find(a => a.id === agentQuery)) {
    const sessionModel = getSessionModelForAgent(agentQuery)
    sessionsStore.ensureLocalSession(sessionId, agentQuery, sessionModel)
    sessionsStore.selectSession(sessionId)
    if (agentQuery !== agentsStore.currentAgentId) {
      await agentsStore.selectAgent(agentQuery)
    }
    applySessionModel(sessionModel)
    await chatStore.switchToSession(sessionId)
  }
}

async function handleNewChat() {
  const sessionModel = getCurrentRightPanelModelForAgent(agentsStore.currentAgentId)
  const session = sessionsStore.createLocalSession(agentsStore.currentAgentId, sessionModel)
  const sameRouteSession = route.params.sessionId === session.id
  await chatStore.switchToSession(session.id)
  await router.push({ name: 'chat', params: { sessionId: session.id }, query: { agent: agentsStore.currentAgentId } })
  if (sameRouteSession) {
    await restoreSession(session.id)
  }
  closeMobileDrawers()
}

async function handleSwitchSession(sessionId: string) {
  if (chatStore.threadId === sessionId && chatStore.isConnected) {
    const session = sessionsStore.sessions.find(s => s.id === sessionId)
    const agentId = session?.agent_id || agentsStore.currentAgentId
    const sessionAgent = agentsStore.agents.find(a => a.id === agentId)
    if (sessionAgent?.source === 'code') {
      toolsStore.syncModelWithAgentDefault()
    } else if (session?.model) {
      toolsStore.setModel(session.model)
    }
    router.push({ name: 'chat', params: { sessionId }, query: { agent: agentId } })
    closeMobileDrawers()
    return
  }
  const session = sessionsStore.sessions.find(s => s.id === sessionId)
  sessionsStore.selectSession(sessionId)
  const agentId = session?.agent_id || agentsStore.currentAgentId
  const sessionAgent = agentsStore.agents.find(a => a.id === agentId)
  if (sessionAgent?.source === 'code') {
    toolsStore.syncModelWithAgentDefault()
  } else if (session?.model) {
    toolsStore.setModel(session.model)
  }
  await chatStore.switchToSession(sessionId)
  if (session?.agent_id && session.agent_id !== agentsStore.currentAgentId) {
    await agentsStore.selectAgent(session.agent_id)
  }
  router.push({ name: 'chat', params: { sessionId }, query: { agent: agentId } })
  closeMobileDrawers()
}

async function handleAgentChange(agentId: string) {
  await agentsStore.selectAgent(agentId)
  const sessionModel = getSessionModelForAgent(agentId)
  applySessionModel(sessionModel)
  const session = sessionsStore.createLocalSession(agentId, sessionModel)
  await chatStore.switchToSession(session.id)
  await router.push({ name: 'chat', params: { sessionId: session.id }, query: { agent: agentId } })
  closeMobileDrawers()
}

function editCurrentAgent() {
  agentEditorRef.value?.open(agentsStore.currentAgent)
}

function createNewAgent() {
  agentEditorRef.value?.open()
}

function openMobileLeft() {
  mobileLeftOpen.value = !mobileLeftOpen.value
  mobileRightOpen.value = false
}

function openMobileRight() {
  mobileRightOpen.value = !mobileRightOpen.value
  mobileLeftOpen.value = false
}

function closeMobileDrawers() {
  mobileLeftOpen.value = false
  mobileRightOpen.value = false
}
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  position: fixed;
  inset: 0;
  height: 100dvh;
  background: var(--el-bg-color-page);
  overflow: hidden;
}

.app-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.mobile-drawer-backdrop {
  display: none;
}

@media (max-width: 900px) {
  .app-body {
    position: relative;
  }

  .chat-main {
    width: 100%;
    min-width: 0;
  }

  .mobile-drawer-backdrop {
    display: block;
    position: fixed;
    inset: 52px 0 0;
    background: rgba(15, 23, 42, 0.35);
    backdrop-filter: blur(2px);
    z-index: 180;
  }

  .mobile-left-panel,
  .mobile-right-panel {
    position: fixed;
    top: 52px;
    bottom: 0;
    height: calc(100dvh - 52px);
    z-index: 200;
    pointer-events: none;
    box-shadow: 0 24px 60px rgba(15, 23, 42, 0.24);
    transition: transform 0.24s ease, box-shadow 0.24s ease;
  }

  .mobile-left-panel {
    left: 0;
    transform: translateX(-100%);
  }

  .mobile-right-panel {
    right: 0;
    transform: translateX(100%);
  }

  .app-body.mobile-left-open .mobile-left-panel,
  .app-body.mobile-right-open .mobile-right-panel,
  .mobile-left-panel.is-mobile-open,
  .mobile-right-panel.is-mobile-open {
    transform: translateX(0);
    pointer-events: auto;
  }
}

@media (prefers-reduced-motion: reduce) {
  .mobile-left-panel,
  .mobile-right-panel {
    transition: none;
  }
}
</style>

`````

--- **end of file: frontend/src/App.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/main.ts** (project: lc_agent) --- 

`````typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import App from './App.vue'
import router from './router'
import './style.css'
import './styles/markdown-theme.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')

`````

--- **end of file: frontend/src/main.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/api/auth.ts** (project: lc_agent) --- 

`````typescript
const BASE_URL = '/api/auth'

export interface LoginResponse {
  token: string
  user: { id: string; username: string; role: string }
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const resp = await fetch(`${BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!resp.ok) throw new Error('认证失败')
  return resp.json()
}

export async function getMe(token: string): Promise<{ id: string; username: string; role: string }> {
  const resp = await fetch(`${BASE_URL}/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!resp.ok) throw new Error('Token 无效')
  return resp.json()
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  const token = localStorage.getItem('token') || ''
  const resp = await fetch(`${BASE_URL}/change-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  })
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}))
    throw new Error(data.detail || '修改失败')
  }
}

`````

--- **end of file: frontend/src/api/auth.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/api/http.ts** (project: lc_agent) --- 

`````typescript
const BASE_URL = '/api'

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = localStorage.getItem('token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: getAuthHeaders(),
    ...options,
  })
  if (response.status === 401) {
    localStorage.removeItem('token')
    window.dispatchEvent(new CustomEvent('auth:expired'))
    throw new Error('认证已过期，请重新登录')
  }
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

export const api = {
  health: () => fetchApi<{ status: string; version: string; app_name?: string; config_loaded: boolean }>('/health'),

  getTools: () => fetchApi<{ name: string; group: string; group_description: string; description: string }[]>('/tools'),
  getToolGroups: () => fetchApi<{ id: string; description: string; tools: { name: string; description: string }[]; enabled: boolean }[]>('/tools/groups'),
  toggleToolGroup: (groupId: string) => fetchApi<{ id: string; enabled: boolean }>(`/tools/groups/${groupId}/toggle`, { method: 'POST' }),

  getModels: () => fetchApi<{ id: string; provider: string; base_url: string; context_limit: number }[]>('/models'),

  getMcpServers: () => fetchApi<any[]>('/mcp'),
  toggleMcpServer: (name: string) => fetchApi<{ name: string; enabled: boolean }>(`/mcp/${name}/toggle`, { method: 'POST' }),
  getSkills: () => fetchApi<any[]>('/skills'),
  getSkillDetail: (name: string) => fetchApi<any>(`/skills/${name}`),
  toggleSkill: (name: string) => fetchApi<{ name: string; enabled: boolean }>(`/skills/${name}/toggle`, { method: 'POST' }),

  getAgents: () => fetchApi<any[]>('/agents'),
  createAgent: (data: object) => fetchApi<any>('/agents', { method: 'POST', body: JSON.stringify(data) }),
  updateAgent: (id: string, data: object) => fetchApi<any>(`/agents/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteAgent: (id: string) => fetchApi<void>(`/agents/${id}`, { method: 'DELETE' }),
  activateAgent: (id: string) => fetchApi<any>(`/agents/${id}/activate`, { method: 'POST' }),

  getSessions: () => fetchApi<any[]>('/sessions'),
  createSession: (data: { title?: string; agent_id?: string; model?: string }) =>
    fetchApi<{ id: string; title: string }>('/sessions', { method: 'POST', body: JSON.stringify(data) }),
  updateSession: (id: string, data: { title?: string; model?: string; is_pinned?: boolean }) =>
    fetchApi<any>(`/sessions/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteSession: (id: string) =>
    fetchApi<void>(`/sessions/${id}`, { method: 'DELETE' }),
  getSessionMessages: (id: string, params?: { limit?: number; offset?: number }) => {
    const qs = new URLSearchParams()
    if (params?.limit !== undefined) qs.set('limit', String(params.limit))
    if (params?.offset !== undefined) qs.set('offset', String(params.offset))
    const query = qs.toString()
    return fetchApi<{ total: number; offset: number; limit: number; messages: any[] }>(
      `/sessions/${id}/messages${query ? '?' + query : ''}`
    )
  },
  getMessageTraces: (sessionId: string, messageId: string) =>
    fetchApi<{ traces: any[] }>(`/sessions/${sessionId}/messages/${messageId}/traces`),

  getSummarization: () => fetchApi<{ enabled: boolean; default_model: string; trigger: any; keep: any }>('/settings/summarization'),
  updateSummarization: (data: { enabled?: boolean; default_model?: string; trigger?: any; keep?: any }) =>
    fetchApi<any>('/settings/summarization', { method: 'PUT', body: JSON.stringify(data) }),
}

export async function fetchAvailableSubagents(): Promise<Array<{
  id: string
  name: string
  display_name: string | null
  source: string
  description: string
}>> {
  return fetchApi('/agents/available-subagents')
}

`````

--- **end of file: frontend/src/api/http.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/api/permissions.ts** (project: lc_agent) --- 

`````typescript
import { fetchApi } from './http'

export interface PermissionsConfig {
  version: number
  tool_allowlist: string[]
}

export async function getPermissions(): Promise<PermissionsConfig> {
  return fetchApi<PermissionsConfig>('/permissions')
}

export async function allowTool(toolName: string): Promise<PermissionsConfig> {
  return fetchApi<PermissionsConfig>('/permissions/allow', {
    method: 'POST',
    body: JSON.stringify({ tool_name: toolName }),
  })
}

export async function removeTool(toolName: string): Promise<PermissionsConfig> {
  return fetchApi<PermissionsConfig>('/permissions/remove', {
    method: 'POST',
    body: JSON.stringify({ tool_name: toolName }),
  })
}

export async function setPermissions(tools: string[]): Promise<PermissionsConfig> {
  return fetchApi<PermissionsConfig>('/permissions', {
    method: 'PUT',
    body: JSON.stringify({ tool_allowlist: tools }),
  })
}

`````

--- **end of file: frontend/src/api/permissions.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/api/sse-client.ts** (project: lc_agent) --- 

`````typescript
/**
 * SSE-based chat client. Drop-in replacement for ChatWebSocket.
 * Uses fetch + ReadableStream to consume server-sent events.
 */

import type { ContentBlock } from '@/utils/fileUpload'

export interface SseMessage {
  type: string
  content?: string
  thread_id?: string
  title?: string
  name?: string
  subagent_type?: string
  description?: string
  result?: string
  message?: string
  run_id?: string
  tool_call_id?: string
  sub_session_id?: string
  query?: string
  status?: 'running' | 'done' | 'error' | string
  result_preview?: string
  duration?: number
  tool_count?: number
  token_count?: number
  args?: Record<string, any>
  action_requests?: any[]
  review_configs?: any[]
  data?: any[]
  input_tokens?: number
  output_tokens?: number
  total_tokens?: number
  cache_read_tokens?: number
  reasoning_tokens?: number
  duration_ms?: number
  usage?: any[]
  http_traces?: any[]
  is_resume?: boolean
  is_subagent?: boolean
  is_error?: boolean
  // error fields
  error_code?: string
  detail?: string
  suggestions?: string[]
  tech_detail?: string
}

export type SseEventHandler = (msg: SseMessage) => void


function getSseAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = localStorage.getItem('token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

function appendTokenToUrl(url: string): string {
  const token = localStorage.getItem('token') || ''
  if (!token) return url
  const separator = url.includes('?') ? '&' : '?'
  return `${url}${separator}token=${encodeURIComponent(token)}`
}

export class ChatSseClient {
  private baseUrl: string
  private handlers: Map<string, SseEventHandler[]> = new Map()
  private _threadId: string | null = null
  private _abortController: AbortController | null = null
  private _streaming = false

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl || window.location.origin
  }

  get threadId() { return this._threadId }
  get connected() { return true }
  get streaming() { return this._streaming }

  setThreadId(threadId: string) {
    this._threadId = threadId
  }

  async sendMessage(
    content: ContentBlock[],
    presetId?: string,
    model?: string,
    options?: { replaceFromMessageId?: string; history?: any[]; llmParams?: Record<string, any> | null },
  ): Promise<void> {
    if (!this._threadId) throw new Error('threadId not set')

    const body: Record<string, any> = {
      input: content,
      preset_id: presetId || 'chat',
      model: model || '',
    }
    if (options?.replaceFromMessageId) {
      body.replace_from_message_id = options.replaceFromMessageId
      body.history = options.history || []
    }
    if (options?.llmParams && Object.keys(options.llmParams).length > 0) {
      body.llm_params = options.llmParams
    }

    await this._startStream(body)
  }

  async sendInterruptResponse(approved: boolean, presetId: string, model?: string): Promise<void> {
    const decisions = [{ type: approved ? 'approve' : 'reject' }]
    await this.sendInterruptResume({ decisions }, presetId, model)
  }

  async sendInterruptResume(
    resumeValue: any,
    presetId: string,
    model?: string,
    llmParams?: Record<string, any> | null,
  ): Promise<void> {
    if (!this._threadId) throw new Error('threadId not set')

    const body: Record<string, any> = {
      command: { resume: resumeValue },
      preset_id: presetId || 'chat',
      model: model || '',
    }
    if (llmParams && Object.keys(llmParams).length > 0) {
      body.llm_params = llmParams
    }

    await this._startStream(body)
  }

  async sendCancel(): Promise<void> {
    if (!this._threadId) return

    this._abortController?.abort()
    this._abortController = null
    this._streaming = false

    this.emit('cancelled', { type: 'cancelled' })

    try {
      const cancelUrl = appendTokenToUrl(`${this.baseUrl}/api/threads/${this._threadId}/runs/cancel`)
      await fetch(cancelUrl, {
        method: 'POST',
        headers: getSseAuthHeaders(),
        body: JSON.stringify({}),
      })
    } catch (e) {
      console.warn('[SSE] Cancel request failed:', e)
    }
  }

  async getState(): Promise<any> {
    if (!this._threadId) return { has_interrupts: false }
    const stateUrl = appendTokenToUrl(`${this.baseUrl}/api/threads/${this._threadId}/state`)
    const resp = await fetch(stateUrl, { headers: getSseAuthHeaders() })
    return resp.json()
  }

  on(event: string, handler: SseEventHandler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, [])
    }
    this.handlers.get(event)!.push(handler)
  }

  off(event: string, handler: SseEventHandler) {
    const handlers = this.handlers.get(event)
    if (handlers) {
      const idx = handlers.indexOf(handler)
      if (idx >= 0) handlers.splice(idx, 1)
    }
  }

  disconnect() {
    this._abortController?.abort()
    this._abortController = null
    this._streaming = false
    this._threadId = null
  }

  // --- Internal ---

  private async _startStream(body: Record<string, any>): Promise<void> {
    if (this._streaming) {
      console.warn('[SSE] Already streaming, aborting previous')
      this._abortController?.abort()
      if (this._threadId) {
        fetch(appendTokenToUrl(`${this.baseUrl}/api/threads/${this._threadId}/runs/cancel`), {
          method: 'POST',
          headers: getSseAuthHeaders(),
          body: JSON.stringify({}),
        }).catch(() => {})
      }
    }

    const controller = new AbortController()
    this._abortController = controller
    this._streaming = true

    const url = appendTokenToUrl(`${this.baseUrl}/api/threads/${this._threadId}/runs/stream`)

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: getSseAuthHeaders(),
        body: JSON.stringify(body),
        signal: controller.signal,
      })

      if (!response.ok) {
        if (response.status === 401) {
          window.dispatchEvent(new CustomEvent('auth:expired'))
          this.emit('error', { type: 'error', title: '认证已过期', detail: '请重新登录' })
          return
        }
        const text = await response.text()
        this.emit('error', {
          type: 'error',
          title: `HTTP ${response.status}`,
          detail: text,
          error_code: 'HTTP_ERROR',
        })
        return
      }

      const receivedTerminal = await this._consumeStream(response)
      if (!receivedTerminal && this._abortController === controller) {
        this.emit('done', { type: 'done' })
      }
    } catch (e: any) {
      if (e.name === 'AbortError') {
        return
      }
      this.emit('error', {
        type: 'error',
        title: '连接失败',
        detail: e.message || String(e),
        error_code: 'NETWORK_ERROR',
      })
    } finally {
      if (this._abortController === controller) {
        this._streaming = false
        this._abortController = null
      }
    }
  }

  private async _consumeStream(response: Response): Promise<boolean> {
    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let receivedTerminal = false
    const terminalTypes = new Set(['done', 'error', 'cancelled'])

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        const events = this._parseSSE(buffer)
        buffer = events.remaining

        for (const evt of events.parsed) {
          this.emit(evt.type, evt)
          if (terminalTypes.has(evt.type)) receivedTerminal = true
        }
      }

      if (buffer.trim()) {
        const events = this._parseSSE(buffer + '\n\n')
        for (const evt of events.parsed) {
          this.emit(evt.type, evt)
          if (terminalTypes.has(evt.type)) receivedTerminal = true
        }
      }
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        throw e
      }
    }

    return receivedTerminal
  }

  private _parseSSE(buffer: string): { parsed: SseMessage[]; remaining: string } {
    const parsed: SseMessage[] = []
    const blocks = buffer.split('\n\n')

    // The last element might be incomplete (no trailing \n\n)
    const remaining = blocks.pop() || ''

    for (const block of blocks) {
      if (!block.trim()) continue

      // Skip heartbeat comments
      if (block.trim().startsWith(':')) continue

      let data = ''
      for (const line of block.split('\n')) {
        if (line.startsWith('data: ')) {
          data += line.slice(6)
        } else if (line.startsWith('data:')) {
          data += line.slice(5)
        }
      }

      if (data) {
        try {
          const msg: SseMessage = JSON.parse(data)
          parsed.push(msg)
        } catch {
          console.warn('[SSE] Failed to parse event data:', data)
        }
      }
    }

    return { parsed, remaining }
  }

  private emit(event: string, msg: SseMessage) {
    const handlers = this.handlers.get(event) || []
    handlers.forEach(h => h(msg))
    const allHandlers = this.handlers.get('*') || []
    allHandlers.forEach(h => h(msg))
  }
}

`````

--- **end of file: frontend/src/api/sse-client.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/chat/ChatBubble.vue** (project: lc_agent) --- 

`````vue
<!-- @deprecated Use EPX BubbleList in ChatView instead. Kept for TestSegments.vue. -->
<template>
  <div class="chat-bubble" :class="[message.role, { streaming: message.isStreaming }]">
    <div class="bubble-avatar" :class="message.role">
      <span v-if="message.role === 'user'" class="avatar-icon">👨‍💻</span>
      <span v-else class="avatar-icon">🤖</span>
    </div>
    <div class="bubble-body">
      <div class="bubble-label">
        <span v-if="message.role === 'user'" class="role-name user-name">You</span>
        <span v-else class="role-name ai-name">{{ modelLabel }}</span>
        <button
          v-if="showEdit"
          class="edit-btn"
          title="编辑并重发"
          @click="$emit('edit')"
        >✏️</button>
      </div>
      <div class="bubble-content">
        <template v-if="message.role === 'assistant'">
          <template v-for="(seg, idx) in renderedSegments" :key="idx">
            <ToolCallCard v-if="seg.type === 'tool' && seg.toolCall && !shouldShowSubAgentCard(seg.toolCall)" :tool-call="seg.toolCall" :collapsed="true" />
            <SubAgentCard
              v-else-if="seg.type === 'tool' && seg.toolCall && shouldShowSubAgentCard(seg.toolCall)"
              :entry="getSubAgentEntryForTool(seg.toolCall)!"
              @enter="handleEnterSubAgent"
            />
            <div v-else-if="seg.type === 'text' && seg.html" :class="seg.cls">
              <div v-if="seg.cls === 'thinking-block'" class="thinking-header">
                <span class="thinking-icon">💭</span>
                <span class="thinking-label">思考中</span>
              </div>
              <div v-html="seg.html" class="markdown-body" />
            </div>
          </template>
        </template>
        <div v-else-if="message.role === 'user'" class="plain-text">{{ message.content }}</div>

        <span v-if="message.isStreaming" class="streaming-cursor">▊</span>

        <TokenUsagePanel v-if="message.role === 'assistant' && !message.isStreaming && message.usage" :usage="message.usage" :tool-calls="message.toolCalls" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/markdown'
import { useToolsStore } from '@/stores/tools'
import ToolCallCard from './ToolCallCard.vue'
import SubAgentCard from './SubAgentCard.vue'
import TokenUsagePanel from './TokenUsagePanel.vue'
import type { ChatMessage, ToolCall, SubAgentEntry } from '@/stores/chat'

interface RenderedSegment {
  type: 'text' | 'tool'
  html?: string
  cls?: string
  toolCall?: ToolCall
}

const props = defineProps<{
  message: ChatMessage
  showEdit?: boolean
}>()
defineEmits<{ edit: [] }>()
const toolsStore = useToolsStore()

const renderedSegments = computed((): RenderedSegment[] => {
  const content = props.message.content
  if (typeof content !== 'string' || !content) return []

  const toolCalls = props.message.toolCalls || []
  const markerRe = /<!--(?:TOOL:(\d+)|THINK_START|THINK_END)-->/g
  const parts: RenderedSegment[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null
  let lastToolSegIdx = -1
  let inThinking = false

  while ((match = markerRe.exec(content)) !== null) {
    const textBefore = content.slice(lastIndex, match.index).trim()
    const marker = match[0]

    if (marker === '<!--THINK_START-->') {
      if (textBefore) {
        parts.push({ type: 'text', html: renderMarkdown(textBefore), cls: 'content-block' })
      }
      inThinking = true
    } else if (marker === '<!--THINK_END-->') {
      if (textBefore) {
        parts.push({ type: 'text', html: renderMarkdown(textBefore), cls: 'thinking-block' })
      }
      inThinking = false
    } else {
      // TOOL marker
      if (textBefore) {
        parts.push({ type: 'text', html: renderMarkdown(textBefore), cls: inThinking ? 'thinking-block' : 'content-block' })
      }
      const tcIdx = parseInt(match[1], 10)
      if (toolCalls[tcIdx]) {
        lastToolSegIdx = parts.length
        parts.push({ type: 'tool', toolCall: toolCalls[tcIdx] })
      }
    }
    lastIndex = match.index + match[0].length
  }

  const remaining = content.slice(lastIndex).trim()
  if (remaining) {
    parts.push({ type: 'text', html: renderMarkdown(remaining), cls: inThinking ? 'thinking-block' : 'content-block' })
  }

  // If no explicit THINK markers, fall back to old heuristic: text before last tool = thinking
  const hasThinkMarkers = content.includes('<!--THINK_START-->')
  if (!hasThinkMarkers && lastToolSegIdx >= 0) {
    for (let i = 0; i < parts.length; i++) {
      if (parts[i].type === 'text') {
        parts[i].cls = i < lastToolSegIdx ? 'thinking-block' : 'content-block'
      }
    }
  }

  return parts
})

const modelLabel = computed(() => {
  const model = toolsStore.currentModel
  if (!model) return 'AI'
  const parts = model.split('/')
  return parts[parts.length - 1] || 'AI'
})

function shouldShowSubAgentCard(tc: ToolCall): boolean {
  return Boolean(tc.is_subagent && tc.runId && props.message.subAgents?.[tc.runId])
}

function getSubAgentEntryForTool(tc: ToolCall): SubAgentEntry | undefined {
  if (!tc.runId) return undefined
  return props.message.subAgents?.[tc.runId]
}

function handleEnterSubAgent(subSessionId: string, name: string) {
  console.log('enter', subSessionId, name)
}
</script>

<style scoped>
.chat-bubble {
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  margin-bottom: 12px;
  border: 1px solid transparent;
}

.chat-bubble.user {
  background: #0f2b1e;
  border-color: #1b4332;
}

.chat-bubble.assistant {
  background: var(--el-fill-color-light);
  border-color: var(--el-border-color);
}

.bubble-avatar {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  border-radius: 50%;
  flex-shrink: 0;
}

.bubble-avatar.user {
  background: linear-gradient(135deg, #2ea043, #238636);
  box-shadow: 0 2px 8px rgba(46, 160, 67, 0.3);
}

.bubble-avatar.assistant {
  background: var(--el-fill-color);
}

.bubble-body {
  flex: 1;
  min-width: 0;
}

.bubble-label {
  margin-bottom: 4px;
}

.role-name {
  font-size: 12px;
  font-weight: 600;
}

.user-name {
  color: #56d364;
}

.ai-name {
  color: var(--el-text-color-secondary);
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
}

.bubble-content {
  overflow-wrap: break-word;
  line-height: 1.7;
  font-size: 14px;
}

.streaming-cursor {
  animation: blink 1s infinite;
  color: var(--el-color-primary);
  font-size: 16px;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.thinking-block {
  background: rgba(234, 179, 8, 0.08);
  border: 1px solid rgba(234, 179, 8, 0.2);
  border-left: 3px solid rgba(234, 179, 8, 0.6);
  border-radius: 8px;
  padding: 10px 14px;
  margin: 8px 0;
  position: relative;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 2px 0 4px;
  user-select: none;
  border-bottom: 1px solid rgba(139, 148, 158, 0.1);
  margin-bottom: 6px;
}

.thinking-icon {
  font-size: 13px;
}

.thinking-label {
  font-size: 11px;
  color: #eab308;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.thinking-toggle {
  font-size: 10px;
  color: #6e7681;
  margin-left: auto;
}

.thinking-block :deep(.markdown-body) {
  font-size: 12.5px !important;
  color: #d4a017 !important;
  font-style: italic;
  line-height: 1.65;
  opacity: 0.9;
}

.thinking-block :deep(.markdown-body p) {
  color: #d4a017;
  margin: 4px 0;
}

.thinking-block :deep(.markdown-body code) {
  background: rgba(234, 179, 8, 0.12);
  color: #eab308;
}

.thinking-block :deep(.markdown-body strong) {
  color: #facc15;
  font-style: normal;
}

.content-block {
  margin: 4px 0;
}

.tool-calls {
  margin-bottom: 8px;
}

.edit-btn {
  margin-left: 8px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12px;
  padding: 2px 4px;
  border-radius: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.chat-bubble.user:hover .edit-btn {
  opacity: 0.7;
}

.edit-btn:hover {
  opacity: 1 !important;
  background: rgba(255, 255, 255, 0.1);
}
</style>

`````

--- **end of file: frontend/src/components/chat/ChatBubble.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/chat/ChatInput.vue** (project: lc_agent) --- 

`````vue
<template>
  <div class="chat-input-wrapper">
    <div v-if="isEditing" class="edit-banner">
      <span>正在编辑上一条消息</span>
      <button type="button" class="cancel-edit-btn" @click="handleCancelEdit">取消</button>
    </div>
    <div
      class="textarea-shell"
      :class="{ 'is-disabled': isInputDisabled }"
      @drop="handleDrop"
      @dragover="handleDragover"
    >
      <div v-if="attachments.length > 0" class="attachments-preview">
        <div
          v-for="att in attachments"
          :key="att.id"
          class="attachment-item"
        >
          <img
            v-if="att.type === 'image'"
            :src="att.dataUrl"
            class="attachment-image"
            :alt="att.name"
          />
          <div v-else class="attachment-file">
            <span class="file-icon">📄</span>
            <span class="file-name" :title="att.name">{{ att.name }}</span>
          </div>
          <button
            type="button"
            class="attachment-remove"
            @click="removeAttachment(att.id)"
          >×</button>
        </div>
      </div>

      <textarea
        ref="textareaRef"
        v-model="messageText"
        class="chat-textarea"
        rows="1"
        placeholder="Send a message... (可粘贴/拖拽图片或文本文件)"
        enterkeyhint="enter"
        :disabled="isInputDisabled"
        @input="resizeTextarea"
        @keydown="handleKeydown"
        @paste="handlePaste"
      />
      <div class="input-actions">
        <button
          v-if="!isStreamingState"
          type="button"
          class="input-action-btn attach-btn"
          aria-label="附加文件"
          title="附加图片或文本文件"
          :disabled="isInputDisabled"
          @click="triggerFileInput"
        >
          <span class="attach-icon">📎</span>
        </button>
        <input
          ref="fileInputRef"
          type="file"
          multiple
          class="hidden-file-input"
          accept="image/*,.txt,.md,.markdown,.json,.yaml,.yml,.csv,.log,.xml,.html,.htm,.js,.ts,.jsx,.tsx,.py,.go,.rs,.java,.c,.cpp,.h,.hpp,.sh,.sql,.css,.scss,.less,.vue,.toml,.ini,.conf"
          @change="handleFileInputChange"
        />
        <button
          v-if="isStreamingState"
          type="button"
          class="input-action-btn stop-btn animated-stop-btn"
          aria-label="停止生成"
          title="停止生成"
          @click="handleStop"
        >
          <span class="stop-spinner" aria-hidden="true">
            <span class="stop-square" />
          </span>
        </button>
        <button
          v-else-if="messageText || attachments.length > 0"
          type="button"
          class="input-action-btn clear-btn"
          @click="clearInput"
        >
          清空
        </button>
        <button
          v-if="!isStreamingState"
          type="button"
          class="send-btn"
          :disabled="!canSend"
          @click="handleSubmit"
        >
          发送
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import {
  type Attachment,
  type ContentBlock,
  buildContentBlocks,
  countImages,
  filesToAttachments,
  imageFilesFromClipboard,
  MAX_IMAGE_COUNT,
} from '@/utils/fileUpload'

const props = defineProps<{
  isStreaming?: boolean
  editContent?: string
  editAttachments?: Attachment[]
  isEditing?: boolean
}>()

const emit = defineEmits<{
  send: [content: ContentBlock[]]
  stop: []
  cancelEdit: []
}>()

const chatStore = useChatStore()
const { isStreaming } = storeToRefs(chatStore)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const messageText = ref('')
const attachments = ref<Attachment[]>([])
const isStreamingState = computed(() => props.isStreaming ?? isStreaming.value)
const isInputDisabled = computed(() => isStreamingState.value)
const canSend = computed(() =>
  (Boolean(messageText.value.trim()) || attachments.value.length > 0) && !isInputDisabled.value,
)

watch(() => [props.editContent, props.editAttachments] as const, async ([content, atts]) => {
  messageText.value = content || ''
  attachments.value = atts ? [...atts] : []
  await nextTick()
  resizeTextarea()
  if (messageText.value || attachments.value.length > 0) {
    focusTextarea('end')
  }
}, { immediate: true })

onMounted(async () => {
  await nextTick()
  resizeTextarea()
  if (!isInputDisabled.value) {
    focusTextarea('end')
  }
})

function resizeTextarea() {
  const textarea = textareaRef.value
  if (!textarea) return
  textarea.style.height = 'auto'
  const maxHeight = Math.floor(window.innerHeight * 0.4)
  const nextHeight = Math.min(textarea.scrollHeight, maxHeight)
  textarea.style.height = `${nextHeight}px`
  textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden'
}

function focusTextarea(position: 'start' | 'end' = 'end') {
  const textarea = textareaRef.value
  if (!textarea) return
  textarea.focus()
  const cursor = position === 'start' ? 0 : textarea.value.length
  textarea.setSelectionRange(cursor, cursor)
}

function clearInput() {
  messageText.value = ''
  attachments.value = []
  nextTick(() => {
    resizeTextarea()
    focusTextarea('end')
  })
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' || (!event.ctrlKey && !event.metaKey) || event.isComposing) return
  event.preventDefault()
  handleSubmit()
}

function handlePaste(event: ClipboardEvent) {
  if (!event.clipboardData) return
  const imageFiles = imageFilesFromClipboard(event.clipboardData.items)
  if (imageFiles.length === 0) return
  event.preventDefault()
  void addFiles(imageFiles)
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  if (!event.dataTransfer?.files?.length) return
  void addFiles(Array.from(event.dataTransfer.files))
}

function handleDragover(event: DragEvent) {
  event.preventDefault()
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileInputChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return
  void addFiles(Array.from(input.files))
  input.value = ''
}

async function addFiles(files: File[]) {
  const { attachments: newAtts, rejected } = await filesToAttachments(files)
  if (newAtts.length > 0) {
    attachments.value.push(...newAtts)
    const imgCount = countImages(attachments.value)
    if (imgCount > MAX_IMAGE_COUNT) {
      ElMessage.warning(`图片较多（${imgCount} 张），可能影响响应速度`)
    }
  }
  for (const name of rejected) {
    ElMessage.error(`不支持的文件类型: ${name}，仅支持图片和文本文件`)
  }
  if (newAtts.length === 0 && rejected.length === files.length) {
    ElMessage.error('没有可处理的文件')
  }
}

function removeAttachment(id: string) {
  attachments.value = attachments.value.filter(a => a.id !== id)
}

function handleSubmit() {
  if (isInputDisabled.value) return
  const blocks = buildContentBlocks(messageText.value, attachments.value)
  if (blocks.length === 0) return
  emit('send', blocks)
  clearInput()
}

function handleStop() {
  emit('stop')
}

function handleCancelEdit() {
  clearInput()
  emit('cancelEdit')
}
</script>

<style scoped>
.chat-input-wrapper {
  padding: 10px 20px 14px;
  border-top: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  box-sizing: border-box;
  flex-shrink: 0;
  position: relative;
  z-index: 120;
  width: 100%;
}

.textarea-shell {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 8px;
  width: 100%;
  padding: 7px 8px 7px 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color-overlay);
  box-sizing: border-box;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.textarea-shell:focus-within {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--el-color-primary) 22%, transparent);
}

.textarea-shell.is-disabled {
  opacity: 0.78;
}

.chat-textarea {
  flex: 1;
  min-width: 0;
  min-height: 22px;
  max-height: 40vh;
  resize: none;
  border: none;
  outline: none;
  padding: 1px 0;
  background: transparent;
  color: var(--el-text-color-primary);
  font: inherit;
  font-size: 14px;
  line-height: 22px;
  overflow-y: hidden;
  scrollbar-width: thin;
}

.chat-textarea::placeholder {
  color: var(--el-text-color-placeholder);
}

.chat-textarea:disabled {
  cursor: not-allowed;
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  min-height: 24px;
}

.input-action-btn,
.send-btn {
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  line-height: 18px;
  padding: 4px 8px;
  transition: background 0.18s ease, color 0.18s ease, opacity 0.18s ease;
}

.input-action-btn {
  background: transparent;
  color: var(--el-text-color-secondary);
}

.input-action-btn:hover {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

.stop-btn {
  width: 28px;
  height: 28px;
  padding: 0;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--el-color-danger) 10%, transparent);
  color: var(--el-color-danger);
}

.stop-btn:hover {
  background: color-mix(in srgb, var(--el-color-danger) 16%, transparent);
  color: var(--el-color-danger);
}

.stop-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid color-mix(in srgb, var(--el-color-danger) 28%, transparent);
  border-top-color: var(--el-color-danger);
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  animation: stop-spin 0.9s linear infinite;
  box-sizing: border-box;
}

.stop-square {
  width: 6px;
  height: 6px;
  border-radius: 1px;
  background: var(--el-color-danger);
  display: block;
}

@keyframes stop-spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

.clear-btn {
  color: var(--el-text-color-secondary);
}

.send-btn {
  background: var(--el-color-primary);
  color: #fff;
  font-weight: 600;
}

.send-btn:hover:not(:disabled) {
  background: var(--el-color-primary-light-3);
}

.send-btn:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.edit-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
  padding: 7px 10px;
  border: 1px solid color-mix(in srgb, var(--el-color-success) 38%, var(--el-border-color));
  border-radius: 8px;
  background: color-mix(in srgb, var(--el-color-success) 12%, var(--el-bg-color-overlay));
  color: var(--el-text-color-primary);
  font-size: 12px;
}

.cancel-edit-btn {
  border: none;
  background: transparent;
  color: var(--el-color-success);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 4px;
}

.cancel-edit-btn:hover {
  color: var(--el-color-success-light-3);
}

@media (max-width: 520px) {
  .chat-input-wrapper {
    padding: 8px 10px 10px;
  }

  .textarea-shell {
    border-radius: 10px;
    padding: 7px 7px 7px 10px;
  }

  .input-action-btn,
  .send-btn {
    padding: 4px 7px;
  }

  .attachment-item {
    width: 50px;
    height: 50px;
  }
}

.attachments-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 6px 4px 0;
  width: 100%;
}

.attachment-item {
  position: relative;
  width: 60px;
  height: 60px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  overflow: hidden;
  background: var(--el-fill-color-light);
  display: flex;
  align-items: center;
  justify-content: center;
}

.attachment-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.attachment-file {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.file-icon {
  font-size: 20px;
  line-height: 1;
}

.file-name {
  font-size: 9px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attachment-remove {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 16px;
  height: 16px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 12px;
  line-height: 14px;
  padding: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.attachment-remove:hover {
  background: rgba(0, 0, 0, 0.8);
}

.attach-btn {
  font-size: 16px;
  line-height: 1;
  padding: 4px 6px;
}

.attach-icon {
  display: inline-block;
}

.hidden-file-input {
  display: none;
}
</style>

`````

--- **end of file: frontend/src/components/chat/ChatInput.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/chat/CodeBlockModal.vue** (project: lc_agent) --- 

`````vue
<template>
  <teleport to="body">
    <div v-if="visible" class="code-modal-backdrop" @click="$emit('close')">
      <div class="code-modal" role="dialog" aria-modal="true" @click.stop>
        <div class="code-modal-header">
          <div class="code-modal-title-wrap">
            <span class="code-modal-kicker">源码</span>
            <span class="code-modal-title">{{ language }}</span>
          </div>
          <div class="code-modal-actions">
            <button class="code-modal-action-btn" @click="copyCode">{{ copyLabel }}</button>
            <button class="code-modal-close" aria-label="关闭" @click="$emit('close')">✕</button>
          </div>
        </div>
        <div class="code-modal-toolbar">
          <input
            ref="searchInputRef"
            v-model="searchQuery"
            class="code-search-input"
            type="text"
            placeholder="搜索关键字..."
            @keydown.enter.prevent="jumpToNextMatch"
          />
          <div class="code-search-actions">
            <span v-if="searchQuery" class="code-search-count">{{ activeMatchLabel }}</span>
            <button class="code-search-btn" :disabled="!matchCount" @click="jumpToPrevMatch">↑</button>
            <button class="code-search-btn" :disabled="!matchCount" @click="jumpToNextMatch">↓</button>
          </div>
        </div>
        <div class="code-modal-content">
          <pre ref="preRef" class="code-modal-pre hljs"><code ref="codeRef" class="hljs" /></pre>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import hljs from 'highlight.js'

const props = defineProps<{
  visible: boolean
  code: string
  language: string
}>()

defineEmits<{ close: [] }>()

const searchQuery = ref('')
const activeMatchIndex = ref(0)
const matchCount = ref(0)
const codeRef = ref<HTMLElement | null>(null)
const searchInputRef = ref<HTMLInputElement | null>(null)
const copyLabel = ref('复制')

const highlightedCode = computed(() => {
  const lang = props.language.toLowerCase()
  if (lang && lang !== 'text' && hljs.getLanguage(lang)) {
    return hljs.highlight(props.code, { language: lang }).value
  }
  return escapeHtml(props.code)
})

const activeMatchLabel = computed(() => {
  if (!matchCount.value) return '0/0'
  return `${activeMatchIndex.value + 1}/${matchCount.value}`
})

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

async function copyCode() {
  if (!props.code) return
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(props.code)
    } else {
      const ta = document.createElement('textarea')
      ta.value = props.code
      ta.style.position = 'fixed'
      ta.style.left = '-9999px'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    copyLabel.value = '已复制'
  } catch {
    copyLabel.value = '复制失败'
  }
  setTimeout(() => { copyLabel.value = '复制' }, 1400)
}

function applyMarks() {
  const codeEl = codeRef.value
  if (!codeEl) return

  codeEl.innerHTML = highlightedCode.value

  const query = searchQuery.value.trim()
  if (!query) {
    matchCount.value = 0
    return
  }

  const regex = new RegExp(escapeRegExp(query), 'gi')
  const walker = document.createTreeWalker(codeEl, NodeFilter.SHOW_TEXT)
  const textNodes: Text[] = []
  let n: Node | null
  while ((n = walker.nextNode())) textNodes.push(n as Text)

  for (const tn of textNodes) {
    const text = tn.textContent || ''
    regex.lastIndex = 0
    const hits: { s: number; e: number }[] = []
    let m: RegExpExecArray | null
    while ((m = regex.exec(text))) hits.push({ s: m.index, e: m.index + m[0].length })
    if (!hits.length) continue

    const frag = document.createDocumentFragment()
    let last = 0
    for (const h of hits) {
      if (h.s > last) frag.appendChild(document.createTextNode(text.slice(last, h.s)))
      const mark = document.createElement('mark')
      mark.className = 'code-search-hit'
      mark.textContent = text.slice(h.s, h.e)
      frag.appendChild(mark)
      last = h.e
    }
    if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)))
    tn.parentNode!.replaceChild(frag, tn)
  }

  const allMarks = codeEl.querySelectorAll('mark.code-search-hit')
  matchCount.value = allMarks.length
  syncActive()
}

function syncActive() {
  const codeEl = codeRef.value
  if (!codeEl) return
  const marks = codeEl.querySelectorAll('mark.code-search-hit')
  marks.forEach((m, i) => m.classList.toggle('is-active', i === activeMatchIndex.value))
  const active = marks[activeMatchIndex.value]
  active?.scrollIntoView({ block: 'center', behavior: 'smooth' })
}

function jumpToNextMatch() {
  if (!matchCount.value) return
  activeMatchIndex.value = (activeMatchIndex.value + 1) % matchCount.value
}

function jumpToPrevMatch() {
  if (!matchCount.value) return
  activeMatchIndex.value = (activeMatchIndex.value - 1 + matchCount.value) % matchCount.value
}

watch(() => props.visible, async (vis) => {
  if (!vis) return
  searchQuery.value = ''
  activeMatchIndex.value = 0
  matchCount.value = 0
  await nextTick()
  applyMarks()
  searchInputRef.value?.focus()
})

watch(searchQuery, async () => {
  activeMatchIndex.value = 0
  await nextTick()
  applyMarks()
})

watch(activeMatchIndex, () => {
  syncActive()
})
</script>

<style scoped>
.code-modal-backdrop {
  position: fixed;
  inset: 0;
  background: color-mix(in srgb, var(--el-bg-color-page) 70%, transparent);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.code-modal {
  width: min(960px, calc(100vw - 80px));
  max-height: min(85vh, 800px);
  min-height: 0;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 16px 48px color-mix(in srgb, var(--el-bg-color-page) 50%, transparent);
}

.code-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color);
  gap: 12px;
  flex: 0 0 auto;
}

.code-modal-title-wrap {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.code-modal-kicker {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.code-modal-title {
  font-family: 'JetBrains Mono', 'Cascadia Code', monospace;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-primary);
  text-transform: lowercase;
}

.code-modal-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.code-modal-action-btn {
  padding: 4px 12px;
  font-size: 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-fill-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: all 0.15s ease;
}

.code-modal-action-btn:hover {
  background: var(--el-fill-color-light);
  border-color: var(--el-color-primary-light-5);
  color: var(--el-color-primary);
}

.code-modal-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 16px;
  cursor: pointer;
}

.code-modal-close:hover {
  background: var(--el-fill-color);
  color: var(--el-text-color-primary);
}

.code-modal-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: color-mix(in srgb, var(--el-fill-color-light) 78%, transparent);
}

.code-search-input {
  flex: 1 1 auto;
  min-width: 0;
  height: 34px;
  padding: 0 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  font-size: 13px;
  outline: none;
}

.code-search-input:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 14%, transparent);
}

.code-search-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.code-search-count {
  min-width: 42px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: right;
}

.code-search-btn {
  width: 30px;
  height: 30px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.code-search-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.code-modal-content {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  background: var(--md-code-bg, #101b17);
}

.code-modal-pre {
  margin: 0;
  padding: 16px 20px;
  min-height: 100%;
  color: var(--md-code-text, #d8fff0);
  background: transparent;
  font-family: 'Cascadia Code', 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre;
  word-break: normal;
  overflow-wrap: normal;
  tab-size: 4;
}

.code-modal-pre :deep(.code-search-hit) {
  background: rgba(250, 204, 21, 0.35);
  color: inherit;
  padding: 1px 0;
  border-radius: 2px;
}

.code-modal-pre :deep(.code-search-hit.is-active) {
  background: rgba(245, 158, 11, 0.78);
}

@media (max-width: 520px) {
  .code-modal-backdrop {
    padding: max(8px, env(safe-area-inset-top)) max(8px, env(safe-area-inset-right)) max(8px, env(safe-area-inset-bottom)) max(8px, env(safe-area-inset-left));
    background: color-mix(in srgb, var(--el-bg-color-page) 88%, transparent);
  }

  .code-modal {
    width: 100%;
    max-height: none;
    height: 100%;
    border-radius: 12px;
  }

  .code-modal-header {
    position: sticky;
    top: 0;
    z-index: 1;
    padding: 10px 10px 9px;
    background: var(--el-bg-color);
    gap: 8px;
  }

  .code-modal-kicker {
    display: none;
  }

  .code-modal-title {
    font-size: 12px;
  }

  .code-modal-close {
    width: 34px;
    height: 34px;
    font-size: 18px;
  }

  .code-modal-toolbar {
    padding: 8px 10px;
    gap: 8px;
    flex-wrap: wrap;
  }

  .code-search-input {
    width: 100%;
    height: 36px;
  }

  .code-search-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .code-search-count {
    margin-right: auto;
    text-align: left;
  }

  .code-modal-pre {
    padding: 12px 10px;
    font-size: 12px;
    line-height: 1.6;
  }
}
</style>

`````

--- **end of file: frontend/src/components/chat/CodeBlockModal.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/chat/CopyRoundsButton.vue** (project: lc_agent) --- 

`````vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { copyRecentRounds, getRounds, copyToClipboard } from '@/utils/copy-markdown'
import type { ChatMessage } from '@/stores/chat'

const props = defineProps<{
  messages: ChatMessage[]
  modelName?: string
}>()

const visible = ref(false)
const roundCount = ref(3)
const includeThinking = ref(true)
const includeToolCalls = ref(true)
const copied = ref(false)

const totalRounds = computed(() => getRounds(props.messages).length)
const maxRounds = computed(() => Math.max(totalRounds.value, 1))

async function doCopy() {
  const md = copyRecentRounds(props.messages, roundCount.value, {
    includeThinking: includeThinking.value,
    includeToolCalls: includeToolCalls.value,
    modelName: props.modelName,
  })
  const ok = await copyToClipboard(md)
  if (ok) {
    copied.value = true
    setTimeout(() => {
      copied.value = false
      visible.value = false
    }, 1200)
  }
}
</script>

<template>
  <el-popover
    v-model:visible="visible"
    trigger="click"
    :width="260"
    placement="bottom-end"
  >
    <template #reference>
      <button class="copy-rounds-trigger"><span class="copy-icon">📋</span><span class="copy-text"> 复制对话</span></button>
    </template>

    <div class="copy-rounds-panel">
      <div class="panel-title">复制最近对话</div>

      <div class="panel-row">
        <span>轮数:</span>
        <el-input-number
          v-model="roundCount"
          :min="1"
          :max="maxRounds"
          size="small"
          controls-position="right"
          style="width: 100px"
        />
        <span class="hint">/ {{ totalRounds }}</span>
      </div>

      <div class="panel-row">
        <el-checkbox v-model="includeThinking">包含思考过程</el-checkbox>
      </div>
      <div class="panel-row">
        <el-checkbox v-model="includeToolCalls">包含工具调用</el-checkbox>
      </div>

      <el-button
        type="primary"
        size="small"
        style="width: 100%; margin-top: 8px"
        @click="doCopy"
      >
        {{ copied ? '已复制 ✓' : '复制到剪贴板' }}
      </el-button>
    </div>
  </el-popover>
</template>

<style scoped>
.copy-rounds-trigger {
  border: 1px solid color-mix(in srgb, var(--el-color-success) 36%, transparent);
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  background: color-mix(in srgb, var(--el-color-success) 18%, transparent);
  color: var(--el-color-success);
  white-space: nowrap;
}
.copy-rounds-trigger:hover {
  background: color-mix(in srgb, var(--el-color-success) 28%, transparent);
  border-color: color-mix(in srgb, var(--el-color-success) 50%, transparent);
}

@media (max-width: 900px) {
  .copy-rounds-trigger .copy-text {
    display: none;
  }
  .copy-rounds-trigger {
    padding: 6px 8px;
  }
}

.copy-rounds-panel {
  padding: 4px 0;
}
.panel-title {
  font-weight: 600;
  margin-bottom: 10px;
  font-size: 14px;
}
.panel-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.hint {
  color: var(--el-text-color-placeholder, #a8abb2);
  font-size: 12px;
}
</style>

`````

--- **end of file: frontend/src/components/chat/CopyRoundsButton.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/chat/HttpTraceBlock.vue** (project: lc_agent) --- 

`````vue
<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { HttpTrace, LlmRoundUsage } from '@/stores/chat'

const props = defineProps<{
  trace: HttpTrace
  usageRound?: LlmRoundUsage
}>()

const isSuccess = computed(() => props.trace.response.ok === true)
const isError = computed(() => Boolean(props.trace.error) || props.trace.response.ok === false)
const tagType = computed(() => (isError.value ? 'danger' : isSuccess.value ? 'success' : 'info'))

const statusText = computed(() => {
  if (props.trace.error) return '失败'
  const status = props.trace.response.status
  return status != null ? String(status) : '未返回'
})

const durationText = computed(() => {
  const ms = props.trace.durationMs
  if (ms == null) return '-'
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
})

const urlText = computed(() => props.trace.request.url || props.trace.model || '未采集')

function fmtTokens(n: number | undefined): string {
  if (n == null || n === 0) return ''
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

const tokenStats = computed(() => {
  const u = props.usageRound
  if (!u) return null
  const parts: { label: string; value: string; cls: string }[] = []
  if (u.inputTokens) parts.push({ label: '输入', value: fmtTokens(u.inputTokens), cls: 'tok-input' })
  if (u.cacheReadTokens) parts.push({ label: '缓存', value: fmtTokens(u.cacheReadTokens), cls: 'tok-cache' })
  if (u.outputTokens) parts.push({ label: '输出', value: fmtTokens(u.outputTokens), cls: 'tok-output' })
  if (u.reasoningTokens) parts.push({ label: '推理', value: fmtTokens(u.reasoningTokens), cls: 'tok-reason' })
  return parts.length > 0 ? parts : null
})

function formatBody(body: string | undefined) {
  if (!body) return '空'
  try {
    return JSON.stringify(JSON.parse(body), null, 2)
  } catch {
    return body
  }
}

const copiedField = ref<string | null>(null)
let copyTimer: ReturnType<typeof setTimeout> | undefined

async function copyField(fieldKey: string, text: string) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.setAttribute('readonly', 'true')
      textarea.style.position = 'fixed'
      textarea.style.left = '-9999px'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    copiedField.value = fieldKey
    clearTimeout(copyTimer)
    copyTimer = setTimeout(() => { copiedField.value = null }, 1400)
  } catch { /* silent */ }
}

const showModal = ref(false)
const modalTitle = ref('')
const modalContent = ref('')
const searchQuery = ref('')
const activeMatchIndex = ref(0)
const modalBodyRef = ref<HTMLElement | null>(null)

function openBodyModal(title: string, body: string) {
  modalTitle.value = title
  modalContent.value = formatBody(body)
  showModal.value = true
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function renderTextToHtml(value: string): string {
  return escapeHtml(value)
    .replace(/\n/g, '<br>')
    .replace(/ {2}/g, '&nbsp;&nbsp;')
}

const modalRenderedResult = computed(() => {
  const query = searchQuery.value.trim()
  if (!query) return renderTextToHtml(modalContent.value)

  const highlighted = modalContent.value.replace(
    new RegExp(escapeRegExp(query), 'gi'),
    (match) => `@@HIT_START@@${match}@@HIT_END@@`,
  )

  return renderTextToHtml(highlighted)
    .replace(/@@HIT_START@@/g, '<mark class="http-search-hit">')
    .replace(/@@HIT_END@@/g, '</mark>')
})

const matchCount = computed(() => {
  const query = searchQuery.value.trim()
  if (!query) return 0
  const matches = modalContent.value.match(new RegExp(escapeRegExp(query), 'gi'))
  return matches?.length || 0
})

const activeMatchLabel = computed(() => {
  if (!matchCount.value) return '0/0'
  return `${activeMatchIndex.value + 1}/${matchCount.value}`
})

async function syncSearchHighlights() {
  await nextTick()
  const container = modalBodyRef.value
  if (!container) return
  const hits = Array.from(container.querySelectorAll('mark.http-search-hit')) as HTMLElement[]
  hits.forEach((hit, index) => {
    hit.classList.toggle('is-active', index === activeMatchIndex.value)
  })
  if (hits.length > 0) {
    hits[activeMatchIndex.value]?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }
}

function jumpToNextMatch() {
  if (!matchCount.value) return
  activeMatchIndex.value = (activeMatchIndex.value + 1) % matchCount.value
}

function jumpToPrevMatch() {
  if (!matchCount.value) return
  activeMatchIndex.value = (activeMatchIndex.value - 1 + matchCount.value) % matchCount.value
}

watch(searchQuery, () => {
  activeMatchIndex.value = 0
  syncSearchHighlights()
})

watch(activeMatchIndex, () => {
  syncSearchHighlights()
})

watch(showModal, (visible) => {
  if (!visible) {
    searchQuery.value = ''
    activeMatchIndex.value = 0
    return
  }
  syncSearchHighlights()
})

const isReqBodyLong = computed(() => (props.trace.request.body?.length || 0) > 300)
const isRespBodyLong = computed(() => (props.trace.response.body?.length || 0) > 300)
</script>

<template>
  <details class="http-trace-block" :class="{ 'is-error': isError }">
    <summary class="http-summary">
      <span class="http-summary-icon">🌐</span>
      <span class="http-summary-title">HTTP 交互 #{{ trace.sequence }}</span>
      <el-tag size="small" :type="tagType" class="http-summary-tag">
        {{ trace.request.method || 'HTTP' }}
      </el-tag>
      <el-tag size="small" :type="tagType" class="http-summary-tag">
        {{ statusText }}
      </el-tag>
      <span class="http-summary-duration">{{ durationText }}</span>
      <span v-if="tokenStats" class="http-token-stats">
        <span v-for="stat in tokenStats" :key="stat.label" class="http-token-item" :class="stat.cls">
          {{ stat.label }} {{ stat.value }}
        </span>
      </span>
      <span class="http-summary-toggle" />
    </summary>

    <div class="http-body">
      <div class="http-row">
        <span class="http-label">URL</span>
        <div class="http-field-row">
          <code class="http-url">{{ urlText }}</code>
          <button class="http-copy-btn" @click.stop="copyField('url', urlText)" :title="copiedField === 'url' ? '已复制' : '复制'">
            {{ copiedField === 'url' ? '✓' : '📋' }}
          </button>
        </div>
      </div>
      <div v-if="trace.provider || trace.model" class="http-row">
        <span class="http-label">模型</span>
        <div class="http-field-row">
          <code>{{ [trace.provider, trace.model].filter(Boolean).join(' / ') }}</code>
          <button class="http-copy-btn" @click.stop="copyField('model', [trace.provider, trace.model].filter(Boolean).join(' / '))" :title="copiedField === 'model' ? '已复制' : '复制'">
            {{ copiedField === 'model' ? '✓' : '📋' }}
          </button>
        </div>
      </div>

      <details class="http-section">
        <summary class="http-section-title">
          <span>Request Headers</span>
          <button class="http-copy-btn" @click.stop="copyField('req-h', formatBody(JSON.stringify(trace.request.headers || {}, null, 2)))">
            {{ copiedField === 'req-h' ? '✓' : '📋' }}
          </button>
        </summary>
        <pre class="http-code">{{ formatBody(JSON.stringify(trace.request.headers || {}, null, 2)) }}</pre>
      </details>
      <details class="http-section">
        <summary class="http-section-title">
          <span>Request Body</span>
          <span class="http-section-actions">
            <button v-if="isReqBodyLong" class="http-expand-btn" @click.stop="openBodyModal('Request Body', trace.request.body)" title="全屏查看">⛶</button>
            <button class="http-copy-btn" @click.stop="copyField('req-b', formatBody(trace.request.body))">
              {{ copiedField === 'req-b' ? '✓' : '📋' }}
            </button>
          </span>
        </summary>
        <pre class="http-code">{{ formatBody(trace.request.body) }}</pre>
      </details>
      <details class="http-section">
        <summary class="http-section-title">
          <span>Response Headers</span>
          <button class="http-copy-btn" @click.stop="copyField('resp-h', formatBody(JSON.stringify(trace.response.headers || {}, null, 2)))">
            {{ copiedField === 'resp-h' ? '✓' : '📋' }}
          </button>
        </summary>
        <pre class="http-code">{{ formatBody(JSON.stringify(trace.response.headers || {}, null, 2)) }}</pre>
      </details>
      <details class="http-section">
        <summary class="http-section-title">
          <span>Response Body</span>
          <span class="http-section-actions">
            <button v-if="isRespBodyLong" class="http-expand-btn" @click.stop="openBodyModal('Response Body', trace.response.body)" title="全屏查看">⛶</button>
            <button class="http-copy-btn" @click.stop="copyField('resp-b', formatBody(trace.response.body))">
              {{ copiedField === 'resp-b' ? '✓' : '📋' }}
            </button>
          </span>
        </summary>
        <pre class="http-code">{{ formatBody(trace.response.body) }}</pre>
      </details>
      <div v-if="trace.error" class="http-error">请求失败：{{ trace.error }}</div>
    </div>
  </details>

  <teleport to="body">
    <div v-if="showModal" class="http-modal-backdrop" @click="showModal = false">
      <div class="http-modal" role="dialog" aria-modal="true" @click.stop>
        <div class="http-modal-header">
          <div class="http-modal-title-wrap">
            <span class="http-modal-kicker">HTTP #{{ trace.sequence }}</span>
            <span class="http-modal-title">{{ modalTitle }}</span>
          </div>
          <div class="http-modal-actions">
            <button class="http-copy-btn-lg" @click="copyField('modal', modalContent)">
              {{ copiedField === 'modal' ? '已复制 ✓' : '复制全部' }}
            </button>
            <button class="http-modal-close" aria-label="关闭" @click="showModal = false">✕</button>
          </div>
        </div>
        <div class="http-modal-toolbar">
          <input
            v-model="searchQuery"
            class="http-search-input"
            type="text"
            placeholder="搜索关键字..."
            @keydown.enter.prevent="jumpToNextMatch"
          />
          <div class="http-search-actions">
            <span v-if="searchQuery" class="http-search-count">{{ activeMatchLabel }}</span>
            <button class="http-search-btn" :disabled="!matchCount" @click="jumpToPrevMatch">↑</button>
            <button class="http-search-btn" :disabled="!matchCount" @click="jumpToNextMatch">↓</button>
          </div>
        </div>
        <div class="http-modal-content">
          <div ref="modalBodyRef" class="http-modal-body" v-html="modalRenderedResult" />
        </div>
      </div>
    </div>
  </teleport>
</template>

<style scoped>
.http-trace-block {
  margin: 8px 0;
  border: 1px solid var(--el-border-color-lighter);
  border-left: 3px solid var(--el-color-primary);
  border-radius: 8px;
  background: var(--el-fill-color-light);
  overflow: hidden;
}
.http-trace-block.is-error {
  border-left-color: var(--el-color-danger);
}

.http-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  cursor: pointer;
  user-select: none;
  font-size: 12px;
  color: var(--el-text-color-regular);
}
.http-summary::-webkit-details-marker {
  display: none;
}
.http-summary-icon {
  font-size: 13px;
}
.http-summary-title {
  font-weight: 600;
  white-space: nowrap;
}
.http-summary-tag {
  flex-shrink: 0;
}
.http-summary-duration {
  color: var(--el-text-color-secondary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.http-token-stats {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: 4px;
}
.http-token-item {
  font-size: 11px;
  padding: 0 5px;
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  white-space: nowrap;
}
.tok-input {
  color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
}
.tok-cache {
  color: var(--el-color-success);
  background: color-mix(in srgb, var(--el-color-success) 10%, transparent);
}
.tok-output {
  color: #c58f22;
  background: color-mix(in srgb, #c58f22 10%, transparent);
}
.tok-reason {
  color: var(--el-color-warning);
  background: color-mix(in srgb, var(--el-color-warning) 10%, transparent);
}
.http-summary-toggle {
  margin-left: auto;
  color: var(--el-text-color-secondary);
  font-size: 11px;
}
.http-trace-block[open] .http-summary-toggle::before {
  content: '收起';
}
.http-trace-block:not([open]) .http-summary-toggle::before {
  content: '展开';
}

.http-body {
  padding: 4px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.http-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
}
.http-label {
  color: var(--el-text-color-secondary);
  font-size: 11px;
}
.http-field-row {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}
.http-field-row code {
  flex: 1;
  min-width: 0;
}
.http-url {
  word-break: break-all;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.http-section {
  border-top: 1px solid var(--el-border-color-lighter);
  padding-top: 6px;
}
.http-section-title {
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-regular);
  padding: 2px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}
.http-section-actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
}
.http-copy-btn {
  flex-shrink: 0;
  padding: 1px 4px;
  font-size: 11px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  color: var(--el-text-color-secondary);
  opacity: 0.6;
  transition: all 0.15s ease;
}
.http-copy-btn:hover {
  opacity: 1;
  border-color: var(--el-border-color);
  background: var(--el-fill-color);
}
.http-expand-btn {
  flex-shrink: 0;
  padding: 1px 6px;
  font-size: 13px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  color: var(--el-color-primary);
  opacity: 0.7;
  transition: all 0.15s ease;
}
.http-expand-btn:hover {
  opacity: 1;
  border-color: var(--el-color-primary-light-5);
  background: var(--el-color-primary-light-9);
}
.http-code {
  margin: 4px 0 0;
  padding: 8px;
  border-radius: 6px;
  background: var(--el-fill-color);
  max-height: 220px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
}
.http-error {
  color: var(--el-color-danger);
  font-size: 12px;
  padding: 6px 8px;
  background: color-mix(in srgb, var(--el-color-danger) 10%, transparent);
  border-radius: 6px;
}

/* Modal */
.http-modal-backdrop {
  position: fixed;
  inset: 0;
  background: color-mix(in srgb, var(--el-bg-color-page) 70%, transparent);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}
.http-modal {
  width: min(900px, calc(100vw - 80px));
  max-height: min(80vh, 760px);
  min-height: 0;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 16px 48px color-mix(in srgb, var(--el-bg-color-page) 50%, transparent);
}
.http-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color);
  gap: 12px;
  flex: 0 0 auto;
}
.http-modal-title-wrap {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.http-modal-kicker {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}
.http-modal-title {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-primary);
}
.http-modal-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.http-copy-btn-lg {
  padding: 4px 10px;
  font-size: 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-fill-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: all 0.15s ease;
}
.http-copy-btn-lg:hover {
  background: var(--el-fill-color-light);
  border-color: var(--el-color-primary-light-5);
}
.http-modal-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 16px;
  cursor: pointer;
}
.http-modal-close:hover {
  background: var(--el-fill-color);
  color: var(--el-text-color-primary);
}
.http-modal-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: color-mix(in srgb, var(--el-fill-color-light) 78%, transparent);
}
.http-search-input {
  flex: 1 1 auto;
  min-width: 0;
  height: 34px;
  padding: 0 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  outline: none;
  font-size: 13px;
}
.http-search-input:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 14%, transparent);
}
.http-search-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.http-search-count {
  min-width: 42px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: right;
}
.http-search-btn {
  width: 30px;
  height: 30px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
}
.http-search-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.http-modal-content {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}
.http-modal-body {
  min-height: 100%;
  padding: 16px;
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
  color: var(--el-text-color-regular);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.http-modal-body :deep(.http-search-hit) {
  background: rgba(250, 204, 21, 0.35);
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
}
.http-modal-body :deep(.http-search-hit.is-active) {
  background: rgba(245, 158, 11, 0.78);
}

@media (max-width: 520px) {
  .http-summary {
    flex-wrap: wrap;
    gap: 4px 6px;
    padding: 8px 10px;
  }
  .http-summary-title {
    white-space: nowrap;
  }
  .http-summary-toggle {
    order: 10;
  }
  .http-token-stats {
    width: 100%;
    margin-left: 0;
    margin-top: 2px;
    flex-wrap: wrap;
  }
}

@media (max-width: 520px) {
  .http-modal-backdrop {
    align-items: stretch;
    justify-content: stretch;
    padding: max(8px, env(safe-area-inset-top)) max(8px, env(safe-area-inset-right)) max(8px, env(safe-area-inset-bottom)) max(8px, env(safe-area-inset-left));
    background: color-mix(in srgb, var(--el-bg-color-page) 88%, transparent);
  }
  .http-modal {
    width: 100%;
    max-height: none;
    height: 100%;
    border-radius: 12px;
    min-width: 0;
  }
  .http-modal-header {
    position: sticky;
    top: 0;
    z-index: 1;
    padding: 10px;
    background: var(--el-bg-color);
    gap: 8px;
  }
  .http-modal-kicker {
    display: none;
  }
  .http-modal-title {
    font-size: 12px;
  }
  .http-modal-close {
    width: 34px;
    height: 34px;
    font-size: 18px;
  }
  .http-modal-toolbar {
    padding: 8px 10px;
    gap: 8px;
    flex-wrap: wrap;
  }
  .http-search-input {
    width: 100%;
    height: 36px;
  }
  .http-search-actions {
    width: 100%;
    justify-content: flex-end;
  }
  .http-search-count {
    margin-right: auto;
    text-align: left;
  }
  .http-modal-body {
    padding: 12px 10px 18px;
    font-size: 12px;
    line-height: 1.65;
  }
}
</style>

`````

--- **end of file: frontend/src/components/chat/HttpTraceBlock.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/chat/HttpTracesGroup.vue** (project: lc_agent) --- 

`````vue
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { HttpTrace, LlmRoundUsage } from '@/stores/chat'
import { api } from '@/api/http'
import HttpTraceBlock from './HttpTraceBlock.vue'

const props = defineProps<{
  traces?: HttpTrace[]
  tracesCount?: number
  sessionId?: string
  messageId?: string
  rounds?: LlmRoundUsage[]
}>()

const loadedTraces = ref<HttpTrace[]>([])
const loading = ref(false)
const loadError = ref(false)

const effectiveTraces = computed(() => props.traces?.length ? props.traces : loadedTraces.value)
const displayCount = computed(() => effectiveTraces.value.length || props.tracesCount || 0)

const totalDuration = computed(() => {
  if (!effectiveTraces.value.length) return ''
  const ms = effectiveTraces.value.reduce((sum, t) => sum + (t.durationMs || 0), 0)
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${ms}ms`
})

const errorCount = computed(() =>
  effectiveTraces.value.filter(t => Boolean(t.error) || t.response.ok === false).length,
)

const isOpen = ref(false)

watch(isOpen, async (open) => {
  if (!open) return
  if (effectiveTraces.value.length > 0) return
  if (!props.sessionId || !props.messageId) return

  loading.value = true
  loadError.value = false
  try {
    const resp = await api.getMessageTraces(props.sessionId, props.messageId)
    loadedTraces.value = resp.traces || []
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
})

function onToggle(e: Event) {
  isOpen.value = (e.target as HTMLDetailsElement).open
}
</script>

<template>
  <details class="http-traces-group" @toggle="onToggle">
    <summary class="http-group-summary">
      <span class="http-group-icon">🌐</span>
      <span class="http-group-label">HTTP 交互</span>
      <span class="http-group-stats">
        {{ displayCount }} 步<template v-if="totalDuration"> · {{ totalDuration }}</template>
      </span>
      <span v-if="errorCount > 0" class="http-group-errors">
        {{ errorCount }} 失败
      </span>
      <span class="http-group-toggle" />
    </summary>
    <div class="http-group-body">
      <div v-if="loading" class="http-loading">加载中...</div>
      <div v-else-if="loadError" class="http-load-error">加载失败</div>
      <template v-else>
        <HttpTraceBlock
          v-for="(trace, idx) in effectiveTraces"
          :key="trace.id"
          :trace="trace"
          :usage-round="rounds?.[idx]"
        />
      </template>
    </div>
  </details>
</template>

<style scoped>
.http-traces-group {
  margin: 8px 0;
  border: 1px solid var(--el-border-color-lighter);
  border-left: 3px solid var(--el-color-primary);
  border-radius: 8px;
  background: var(--el-fill-color-light);
  overflow: hidden;
}

.http-group-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  font-size: 13px;
  color: var(--el-text-color-regular);
}
.http-group-summary::-webkit-details-marker {
  display: none;
}

.http-group-icon {
  font-size: 14px;
}
.http-group-label {
  font-weight: 600;
}
.http-group-stats {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.http-group-errors {
  font-size: 12px;
  color: var(--el-color-danger);
  font-weight: 500;
}
.http-group-toggle {
  margin-left: auto;
  font-size: 11px;
  color: var(--el-text-color-secondary);
}
.http-traces-group[open] .http-group-toggle::before {
  content: '收起';
}
.http-traces-group:not([open]) .http-group-toggle::before {
  content: '展开';
}

.http-group-body {
  padding: 4px 8px 8px;
}
.http-loading, .http-load-error {
  padding: 12px;
  text-align: center;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.http-load-error {
  color: var(--el-color-danger);
}
</style>

`````

--- **end of file: frontend/src/components/chat/HttpTracesGroup.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/chat/InterruptDialog.vue** (project: lc_agent) --- 

`````vue
<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="500px"
    class="interrupt-dialog"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
  >
    <!-- ask_user 模式 -->
    <template v-if="isAskUser">
      <p class="ask-question">{{ askPayload?.question }}</p>
      <p v-if="askPayload?.allow_multiple && askPayload?.options?.length" class="multi-hint">（可多选）</p>

      <div v-if="askPayload?.options?.length" class="options-list">
        <el-button
          v-for="opt in askPayload.options"
          :key="opt.id"
          :type="isOptionSelected(opt.label) ? 'primary' : 'default'"
          class="option-btn"
          @click="selectOption(opt.label)"
        >
          <span class="option-id">{{ opt.id }}</span>
          {{ opt.label }}
        </el-button>
      </div>

      <el-input
        v-if="askPayload?.allow_free_input"
        v-model="freeInput"
        :placeholder="askPayload?.options?.length ? '或输入自定义回答...' : '请输入回答...'"
        class="free-input"
        @keyup.enter="canSubmitAskUser && submitAskUser()"
      />
    </template>

    <!-- 标准工具审批模式 -->
    <template v-else>
      <div v-for="(action, idx) in allActions" :key="idx" class="action-item" :class="{ compact: !showDetails }">
        <p>
          <strong>工具:</strong>
          <span class="tool-display-name">{{ action.display_name || action.name }}</span>
          <span v-if="action.display_name" class="tool-internal-name">({{ action.name }})</span>
        </p>
        <pre v-if="showDetails" class="action-args">{{ JSON.stringify(action.args ?? action.arguments, null, 2) }}</pre>
      </div>
      <el-button
        link
        :type="showDetails ? 'info' : 'primary'"
        class="expand-btn"
        @click="showDetails = !showDetails"
      >
        {{ showDetails ? '收起详情' : `展开详情（${allActions.length} 个工具调用）` }}
      </el-button>
    </template>

    <template #footer>
      <template v-if="isAskUser">
        <el-button type="primary" :disabled="!canSubmitAskUser" @click="submitAskUser">
          提交
        </el-button>
      </template>
      <template v-else>
        <el-button @click="reject">拒绝</el-button>
        <el-button type="success" @click="allowPermanently" :disabled="!firstToolName">永久允许此工具</el-button>
        <el-button type="primary" @click="approve">批准执行</el-button>
      </template>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { InterruptInfo } from '@/stores/chat'

interface AskUserPayload {
  type: 'ask_user'
  question: string
  options?: { id: string; label: string }[]
  allow_multiple?: boolean
  allow_free_input?: boolean
}

const props = defineProps<{ interrupt: InterruptInfo | null }>()
const emit = defineEmits<{
  decide: [decision: { type: string; message?: string }]
  resume: [value: any]
  'allow-permanently': [toolName: string]
}>()

const visible = computed({
  get: () => props.interrupt !== null,
  set: () => {},
})

const freeInput = ref('')
const selectedOption = ref<string | null>(null)
const selectedOptions = ref<string[]>([])
const showDetails = ref(false)

const allActions = computed(() => props.interrupt?.actionRequests ?? [])
const askPayload = computed<AskUserPayload | null>(() => {
  if (!props.interrupt) return null
  const data = props.interrupt.data
  if (data && data.length > 0) {
    const value = data[0]?.value
    if (value && typeof value === 'object' && value.type === 'ask_user') {
      return value as AskUserPayload
    }
  }
  return null
})

const isAskUser = computed(() => askPayload.value !== null)

const dialogTitle = computed(() => isAskUser.value ? '💬 请回答' : '⚠️ 工具需要审批')

const firstToolName = computed<string | null>(() => {
  if (!props.interrupt) return null
  const reqs = props.interrupt.actionRequests
  if (reqs && reqs.length > 0) return reqs[0].name
  const data = props.interrupt.data
  if (data && data.length > 0) {
    const value = data[0]?.value
    if (typeof value === 'object' && value?.action_requests?.length > 0) {
      return value.action_requests[0].name
    }
  }
  return null
})

const canSubmitAskUser = computed(() => {
  return selectedOption.value !== null || selectedOptions.value.length > 0 || freeInput.value.trim() !== ''
})

watch(() => props.interrupt, () => {
  freeInput.value = ''
  selectedOption.value = null
  selectedOptions.value = []
  showDetails.value = false
})

function isOptionSelected(label: string): boolean {
  const payload = askPayload.value
  if (payload?.allow_multiple) {
    return selectedOptions.value.includes(label)
  }
  return selectedOption.value === label
}

function selectOption(label: string) {
  const payload = askPayload.value
  if (payload?.allow_multiple) {
    const idx = selectedOptions.value.indexOf(label)
    if (idx >= 0) {
      selectedOptions.value.splice(idx, 1)
    } else {
      selectedOptions.value.push(label)
    }
    selectedOption.value = selectedOptions.value.length > 0 ? selectedOptions.value.join(', ') : null
  } else {
    selectedOption.value = label
    if (!payload?.allow_free_input) {
      submitAskUser()
    }
  }
}

function submitAskUser() {
  const parts: string[] = []
  if (askPayload.value?.allow_multiple && selectedOptions.value.length > 0) {
    parts.push(selectedOptions.value.join(', '))
  } else if (selectedOption.value) {
    parts.push(selectedOption.value)
  }
  if (freeInput.value.trim()) {
    parts.push(freeInput.value.trim())
  }
  const answer = parts.join('; ')
  if (!answer) return
  emit('resume', answer)
}

function allowPermanently() {
  const toolName = firstToolName.value
  if (toolName) {
    emit('allow-permanently', toolName)
  }
}

function approve() {
  emit('decide', { type: 'approve' })
}

function reject() {
  emit('decide', { type: 'reject', message: '用户拒绝了此操作' })
}
</script>

<style scoped>
.ask-question {
  font-size: 15px;
  margin-bottom: 16px;
  line-height: 1.6;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.option-btn {
  justify-content: flex-start;
  text-align: left;
  height: auto;
  padding: 10px 16px;
  white-space: normal;
}

.option-id {
  display: inline-block;
  width: 22px;
  height: 22px;
  line-height: 22px;
  text-align: center;
  border-radius: 4px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 600;
  font-size: 12px;
  margin-right: 10px;
  flex-shrink: 0;
}

.multi-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin: -8px 0 12px;
}

.free-input {
  margin-top: 8px;
  width: 100%;
}

.free-input :deep(.el-input__wrapper),
.free-input :deep(.el-textarea__inner) {
  box-sizing: border-box;
}

.tool-display-name {
  margin-left: 4px;
  font-weight: 500;
}
.tool-internal-name {
  margin-left: 6px;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}
.action-item {
  margin-bottom: 14px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
}

.action-item.compact {
  margin-bottom: 6px;
  padding: 8px 12px;
}

.action-args {
  background: var(--el-fill-color);
  padding: 10px;
  border-radius: 6px;
  font-size: 12px;
  overflow-x: auto;
  margin-top: 8px;
  border: 1px solid var(--el-border-color);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.expand-btn {
  margin-top: 4px;
}

.dialog-footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
  width: 100%;
}

:deep(.interrupt-dialog) {
  max-width: min(500px, calc(100vw - 24px));
}

@media (max-width: 768px) {
  .ask-question {
    font-size: 14px;
  }

  .action-item {
    padding: 10px;
  }

  .action-args {
    font-size: 11px;
    max-height: 40vh;
  }

  .dialog-footer-actions {
    flex-direction: column-reverse;
    align-items: stretch;
  }

  .dialog-footer-actions .el-button {
    width: 100%;
    margin-left: 0;
  }

  .option-btn {
    width: 100%;
    margin-left: 0;
  }
}
</style>

`````

--- **end of file: frontend/src/components/chat/InterruptDialog.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/chat/MessageToolbar.vue** (project: lc_agent) --- 

`````vue
<script setup lang="ts">
import { ref } from 'vue'
import {
  singleMessageToMarkdown,
  extractThinking,
  extractToolCalls,
  extractAnswer,
  copyToClipboard,
} from '@/utils/copy-markdown'
import type { ChatMessage } from '@/stores/chat'

const props = defineProps<{
  message: ChatMessage
  modelName?: string
  hasThinking?: boolean
  hasToolCalls?: boolean
  hasAnswer?: boolean
}>()

const copiedKey = ref<string | null>(null)

async function doCopy(key: string, text: string) {
  if (!text) return
  const ok = await copyToClipboard(text)
  if (ok) {
    copiedKey.value = key
    setTimeout(() => (copiedKey.value = null), 1500)
  }
}

function copyAll() {
  doCopy('all', singleMessageToMarkdown(props.message, { modelName: props.modelName }))
}
function copyThinking() {
  doCopy('thinking', extractThinking(props.message))
}
function copyTools() {
  doCopy('tools', extractToolCalls(props.message))
}
function copyAnswer() {
  doCopy('answer', extractAnswer(props.message))
}
function copyUser() {
  const content = props.message.content
  const text = typeof content === 'string'
    ? content
    : content.find(b => b.type === 'text')?.text || ''
  doCopy('all', text)
}
</script>

<template>
  <div class="message-toolbar">
    <template v-if="message.role === 'user'">
      <button class="tb-btn" @click="copyUser">
        {{ copiedKey === 'all' ? '已复制 ✓' : '📋 复制' }}
      </button>
    </template>
    <template v-else>
      <button class="tb-btn" @click="copyAll">
        {{ copiedKey === 'all' ? '已复制 ✓' : '📋 复制全部' }}
      </button>
      <button v-if="hasThinking" class="tb-btn" @click="copyThinking">
        {{ copiedKey === 'thinking' ? '已复制 ✓' : '💭 复制思考' }}
      </button>
      <button v-if="hasToolCalls" class="tb-btn" @click="copyTools">
        {{ copiedKey === 'tools' ? '已复制 ✓' : '🔧 复制工具' }}
      </button>
      <button v-if="hasAnswer" class="tb-btn" @click="copyAnswer">
        {{ copiedKey === 'answer' ? '已复制 ✓' : '📝 复制回答' }}
      </button>
    </template>
  </div>
</template>

<style scoped>
.message-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
  opacity: 0.35;
  transition: opacity 0.2s;
}
.message-toolbar:hover {
  opacity: 1;
}

@media (max-width: 768px) {
  .message-toolbar {
    opacity: 1;
  }
}

.tb-btn {
  background: var(--el-fill-color-light, #f5f7fa);
  border: 1px solid var(--el-border-color-lighter, #e4e7ed);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
  color: var(--el-text-color-secondary, #909399);
  transition: all 0.15s;
}
.tb-btn:hover {
  background: var(--el-color-primary-light-9, #ecf5ff);
  border-color: var(--el-color-primary-light-7, #c6e2ff);
  color: var(--el-color-primary, #409eff);
}
.tb-btn:active {
  transform: scale(0.96);
}

@media (max-width: 768px) {
  .tb-btn {
    padding: 6px 12px;
    font-size: 13px;
    min-height: 36px;
  }
}
</style>

`````

--- **end of file: frontend/src/components/chat/MessageToolbar.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/chat/SubAgentCard.vue** (project: lc_agent) --- 

`````vue
<template>
  <div class="subagent-card" :class="statusClass">
    <!-- Header -->
    <div class="sa-header">
      <span class="sa-icon">🤖</span>
      <div class="sa-meta">
        <div class="sa-name">{{ entry.name }}</div>
        <div class="sa-submeta">
          <span v-if="entry.status === 'running'" class="sa-running-dot"></span>
          <span v-if="entry.status === 'running'">执行中</span>
          <span v-else-if="entry.status === 'done'">完成 ✓</span>
          <span v-else-if="entry.status === 'error'">失败</span>
          <span v-else-if="entry.status === 'cancelled'">已取消</span>
          <span v-else-if="entry.status === 'interrupted'">已中断</span>
          <template v-if="entry.toolCallCount > 0">
            · 🔧 {{ entry.toolCallCount }}次
          </template>
          <template v-if="entry.tokenCount > 0">
            · 💬 {{ entry.tokenCount }}
          </template>
          <template v-if="entry.duration">
            · ⏱ {{ formatDuration(entry.duration) }}
          </template>
        </div>
      </div>
      <button
        v-if="entry.sub_session_id"
        class="sa-enter-btn"
        title="进入子Agent查看详情"
        @click="$emit('enter', entry.sub_session_id, entry.name)"
      >
        ↗
      </button>
    </div>

    <!-- Body: always 200px scrollable window -->
    <div ref="bodyRef" class="sa-body">
      <div v-if="entry.query?.trim()" class="sa-query-block">
        <div class="sa-query-header">对子 Agent 的提问</div>
        <div class="sa-query-text">{{ entry.query }}</div>
      </div>
      <!-- Thinking block (only while running) -->
      <div v-if="entry.status === 'running' && entry.thinking?.trim()" class="sa-thinking-block">
        <div class="sa-thinking-header">
          <span class="sa-thinking-icon">💭</span>
          <span>思考中...</span>
        </div>
        <div class="sa-thinking-text">{{ entry.thinking }}</div>
      </div>

      <!-- Inner tool calls (only while running) -->
      <div v-if="entry.status === 'running' && entry.innerToolCalls.length" class="sa-inner-tools">
        <div v-for="(tc, i) in entry.innerToolCalls" :key="i" class="sa-inner-tool">
          <span class="sa-inner-status" :class="tc.status">●</span>
          🔧 <span class="sa-tool-name">{{ tc.name }}</span>
          <span v-if="tc.status === 'done'" class="sa-tool-done">✓</span>
          <span v-if="tc.status === 'running'" class="sa-tool-running-dot"></span>
        </div>
      </div>

      <!-- Streaming tokens (running) -->
      <div v-if="entry.status === 'running' && entry.tokens" class="sa-tokens">
        {{ entry.tokens }}<span class="sa-cursor">▋</span>
      </div>

      <!-- Empty running state -->
      <div v-if="entry.status === 'running' && !hasContent" class="sa-empty-running">
        <span class="sa-dots"><span>.</span><span>.</span><span>.</span></span>
      </div>

      <!-- Done/Error: markdown rendered full answer -->
      <div
        v-if="entry.status !== 'running' && bodyText"
        class="sa-md-body"
        v-html="renderMarkdown(bodyText)"
      />
      <div v-if="entry.status !== 'running' && !bodyText" class="sa-empty-done">
        (无回答内容)
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { SubAgentEntry } from '@/stores/chat'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps<{
  entry: SubAgentEntry
}>()

defineEmits<{
  enter: [sub_session_id: string, name: string]
}>()

const bodyRef = ref<HTMLElement | null>(null)

const statusClass = computed(() => {
  const status = props.entry.status

  return {
    'sa-running': status === 'running',
    'sa-done': status === 'done',
    'sa-error': status === 'error',
    'sa-cancelled': status === 'cancelled',
    'sa-interrupted': status === 'interrupted',
  }
})

/** Text shown in done state: prefer full in-memory tokens, fallback to DB tokenPreview */
const bodyText = computed(() => props.entry.tokens || props.entry.tokenPreview || '')

const hasContent = computed(() =>
  !!(props.entry.thinking?.trim() || props.entry.innerToolCalls.length || props.entry.tokens),
)

function formatDuration(ms: number) {
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`
}

function scrollToBottom() {
  nextTick(() => {
    const el = bodyRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

watch(() => props.entry.tokens, scrollToBottom)
watch(() => props.entry.innerToolCalls.length, scrollToBottom)
watch(() => props.entry.thinkCount, scrollToBottom)
watch(() => props.entry.status, (newStatus) => {
  if (newStatus !== 'running') scrollToBottom()
})
</script>

<style scoped>
.subagent-card {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
  margin: 6px 0;
  border-left: 3px solid var(--el-color-primary);
}
.sa-running { border-left-color: var(--el-color-primary); }
.sa-done { border-left-color: var(--el-color-success); }
.sa-error { border-left-color: var(--el-color-danger); }

.sa-header {
  background: var(--el-color-primary-light-9);
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid var(--el-color-primary-light-7);
}
.sa-icon { font-size: 16px; }
.sa-meta { flex: 1; min-width: 0; }
.sa-name { font-weight: 700; color: var(--el-color-primary-dark-2); font-size: 13px; }
.sa-submeta {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 1px;
}
.sa-running-dot {
  width: 7px;
  height: 7px;
  background: var(--el-color-primary);
  border-radius: 50%;
  animation: pulse 1s infinite;
  align-self: center;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.sa-enter-btn {
  background: none;
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 6px;
  padding: 3px 8px;
  color: var(--el-color-primary);
  cursor: pointer;
  font-size: 14px;
  flex-shrink: 0;
}
.sa-enter-btn:hover { background: var(--el-color-primary-light-9); }

/* Body: always 200px fixed scrollable window */
.sa-body {
  height: 200px;
  padding: 8px 12px;
  overflow-y: auto;
  scroll-behavior: smooth;
  box-sizing: border-box;
}

/* Query block */
.sa-query-block {
  margin-bottom: 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  background: var(--el-fill-color-light);
}

.sa-query-header {
  padding: 6px 8px 4px;
  font-size: 11px;
  font-weight: 700;
  color: var(--el-text-color-secondary);
}

.sa-query-text {
  padding: 0 8px 8px;
  color: var(--el-text-color-regular);
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-wrap: break-word;
}

/* Thinking block */
.sa-thinking-block {
  margin-bottom: 8px;
  border: 1px solid var(--el-color-warning-light-5);
  border-radius: 4px;
  background: var(--el-color-warning-light-9);
  font-size: 11px;
}
.sa-thinking-header {
  padding: 4px 8px;
  color: var(--el-color-warning-dark-2);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}
.sa-thinking-icon { font-size: 12px; }
.sa-thinking-text {
  padding: 4px 8px 6px;
  color: var(--el-text-color-secondary);
  white-space: pre-wrap;
  overflow-wrap: break-word;
  line-height: 1.5;
}

/* Tool calls */
.sa-inner-tools {
  margin-bottom: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.sa-inner-tool {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 0;
}
.sa-tool-name { flex: 1; }
.sa-inner-status { font-size: 8px; }
.sa-inner-status.running { color: var(--el-color-warning); }
.sa-inner-status.done { color: var(--el-color-success); }
.sa-tool-done { color: var(--el-color-success); font-size: 11px; }
.sa-tool-running-dot {
  width: 6px;
  height: 6px;
  background: var(--el-color-warning);
  border-radius: 50%;
  animation: pulse 0.8s infinite;
}

/* Response tokens */
.sa-tokens {
  color: var(--el-text-color-regular);
  font-size: 12px;
  line-height: 1.7;
  white-space: pre-wrap;
  overflow-wrap: break-word;
}
.sa-cursor { animation: blink 1s step-end infinite; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

/* Done state: markdown rendered full answer */
.sa-md-body {
  font-size: 12px;
  line-height: 1.7;
  color: var(--el-text-color-regular);
  overflow-wrap: break-word;
}
.sa-md-body :deep(p) { margin: 0 0 6px; }
.sa-md-body :deep(p:last-child) { margin-bottom: 0; }
.sa-md-body :deep(h1), .sa-md-body :deep(h2), .sa-md-body :deep(h3) {
  font-size: 13px;
  font-weight: 700;
  margin: 8px 0 4px;
}
.sa-md-body :deep(code) {
  background: var(--el-fill-color-light);
  border-radius: 3px;
  padding: 1px 4px;
  font-size: 11px;
  font-family: monospace;
}
.sa-md-body :deep(pre) {
  background: var(--el-fill-color-light);
  border-radius: 4px;
  padding: 8px;
  overflow-x: auto;
  margin: 4px 0;
}
.sa-md-body :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 11px;
}
.sa-md-body :deep(ul), .sa-md-body :deep(ol) {
  margin: 4px 0;
  padding-left: 16px;
}
.sa-md-body :deep(li) { margin: 2px 0; }
.sa-md-body :deep(blockquote) {
  border-left: 3px solid var(--el-border-color);
  margin: 4px 0;
  padding: 2px 8px;
  color: var(--el-text-color-secondary);
}
.sa-empty-done {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
  padding: 8px 0;
}

/* Empty running dots animation */
.sa-empty-running {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
  padding: 8px 0;
}
.sa-dots span {
  animation: dotbounce 1.2s infinite;
  display: inline-block;
  font-size: 18px;
  line-height: 0;
}
.sa-dots span:nth-child(2) { animation-delay: 0.2s; }
.sa-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotbounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-4px); }
}
</style>

`````

--- **end of file: frontend/src/components/chat/SubAgentCard.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/chat/TodoProgressCard.vue** (project: lc_agent) --- 

`````vue
<template>
  <div class="todo-progress-card" :class="{ expanded: isExpanded }" @click="isExpanded = !isExpanded">
    <div class="todo-compact">
      <span class="todo-status-icon" :class="{ spinning: hasInProgress }">
        {{ hasInProgress ? '◉' : allCompleted ? '✓' : '○' }}
      </span>
      <span class="todo-current-label">{{ currentLabel }}</span>
      <span class="todo-progress-badge">{{ completed }}/{{ totalCount }}</span>
      <div class="todo-mini-bar">
        <div class="todo-mini-fill" :style="{ width: percentage + '%' }" />
      </div>
      <span class="todo-expand-icon">{{ isExpanded ? '▾' : '▸' }}</span>
    </div>

    <ul v-if="isExpanded" class="todo-full-list" @click.stop>
      <li
        v-for="(todo, idx) in todoItems"
        :key="idx"
        class="todo-row"
        :class="'status-' + todo.status"
      >
        <span class="row-icon">{{ statusIcon(todo.status) }}</span>
        <span class="row-text">{{ todo.content }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ToolCall } from '@/stores/chat'

const props = defineProps<{ toolCall: ToolCall }>()

const isExpanded = ref(false)

interface TodoEntry {
  content: string
  status: 'pending' | 'in_progress' | 'completed'
}

const todoItems = computed((): TodoEntry[] => {
  const args = props.toolCall.args
  if (!args || !Array.isArray(args.todos)) return []
  return args.todos as TodoEntry[]
})

const totalCount = computed(() => todoItems.value.length)
const completed = computed(() => todoItems.value.filter(t => t.status === 'completed').length)
const hasInProgress = computed(() => todoItems.value.some(t => t.status === 'in_progress'))
const allCompleted = computed(() => totalCount.value > 0 && completed.value === totalCount.value)
const percentage = computed(() =>
  totalCount.value ? Math.round((completed.value / totalCount.value) * 100) : 0,
)

const currentLabel = computed(() => {
  const inProgress = todoItems.value.find(t => t.status === 'in_progress')
  if (inProgress) return inProgress.content
  if (allCompleted.value) return '全部完成'
  const nextPending = todoItems.value.find(t => t.status === 'pending')
  return nextPending?.content || '任务进度'
})

function statusIcon(status: string) {
  switch (status) {
    case 'completed': return '✓'
    case 'in_progress': return '◉'
    default: return '○'
  }
}
</script>

<style scoped>
.todo-progress-card {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  padding: 10px 14px;
  margin: 8px 0;
  background: var(--el-fill-color-blank);
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
  user-select: none;
}

.todo-progress-card:hover {
  border-color: var(--el-border-color);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.todo-progress-card.expanded {
  border-color: var(--el-color-primary-light-5);
}

.todo-compact {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.todo-status-icon {
  font-size: 14px;
  flex-shrink: 0;
  color: var(--el-color-warning);
}

.todo-status-icon.spinning {
  animation: pulse 1.5s ease-in-out infinite;
}

.todo-current-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.todo-progress-badge {
  flex-shrink: 0;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 9px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-secondary);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.todo-mini-bar {
  width: 48px;
  height: 4px;
  border-radius: 2px;
  background: var(--el-fill-color-light);
  overflow: hidden;
  flex-shrink: 0;
}

.todo-mini-fill {
  height: 100%;
  border-radius: 2px;
  background: var(--el-color-success);
  transition: width 0.4s ease;
}

.todo-expand-icon {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  flex-shrink: 0;
}

.todo-full-list {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  cursor: default;
}

.todo-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 5px 8px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.5;
  border: 1px solid transparent;
}

.row-icon {
  flex-shrink: 0;
  width: 16px;
  text-align: center;
  margin-top: 1px;
}

.row-text {
  flex: 1;
  word-break: break-word;
}

.status-pending {
  color: var(--el-text-color-secondary);
}
.status-pending .row-icon {
  color: var(--el-text-color-placeholder);
}

.status-in_progress {
  background: var(--el-color-warning-light-9);
  border-color: var(--el-color-warning-light-7);
  color: var(--el-color-warning-dark-2);
}
.status-in_progress .row-icon {
  color: var(--el-color-warning);
  animation: pulse 1.5s ease-in-out infinite;
}

.status-completed {
  color: var(--el-color-success-dark-2);
}
.status-completed .row-text {
  text-decoration: line-through;
  opacity: 0.7;
}
.status-completed .row-icon {
  color: var(--el-color-success);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>

`````

--- **end of file: frontend/src/components/chat/TodoProgressCard.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/chat/TokenUsagePanel.vue** (project: lc_agent) --- 

`````vue
<template>
  <div v-if="usage && (usage.rounds.length > 0 || usage.toolCallCount > 0 || usage.totalDuration)" class="token-usage-panel">
    <div class="usage-header" @click.stop="toggleRoundsDetails">
      <span class="usage-title">Token 用量</span>
      <div class="usage-badges">
        <span class="badge badge-rounds" @click.stop="toggleRoundsDetails">🔄 {{ usage.rounds.length }} Rounds</span>
        <span v-if="usage.toolCallCount" class="badge badge-tools" @click.stop="toggleToolsDetails">🔧 {{ usage.toolCallCount }} 工具</span>
        <span v-if="usage.totalDuration" class="badge badge-time">⏱ {{ formatDuration(usage.totalDuration) }}</span>
      </div>
    </div>

    <div v-if="usage.rounds.length > 0" class="usage-summary">
      <div class="summary-card summary-card-window">
        <div class="summary-value">{{ formatTokens(currentWindowInput) }}</div>
        <div class="summary-label">当前窗口</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ formatTokens(totalInput) }}</div>
        <div class="summary-label">总输入</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ formatTokens(totalOutput) }}</div>
        <div class="summary-label">总输出</div>
        <div v-if="totalReasoning > 0" class="summary-sub reasoning">Reasoning: {{ formatTokens(totalReasoning) }}</div>
      </div>
      <div class="summary-card card-cached">
        <div class="summary-value">{{ formatTokens(totalCached) }}</div>
        <div class="summary-label">总缓存</div>
        <div v-if="usage.totalDuration" class="summary-sub time">{{ formatDuration(usage.totalDuration) }}</div>
      </div>
    </div>
    <div v-else-if="usage.totalDuration" class="usage-summary-minimal">
      <span class="minimal-info">总耗时 {{ formatDuration(usage.totalDuration) }}</span>
      <span v-if="usage.toolCallCount" class="minimal-info">· {{ usage.toolCallCount }} 次工具调用</span>
    </div>

    <Transition name="usage-details">
    <div v-if="expanded && usage.rounds.length > 1" ref="usageDetailsRef" class="usage-details">
      <div class="details-header">
        <span class="detail-toggle" @click="toggleRoundsDetails">▾ Per-round Details</span>
        <span class="rounds-badge">{{ usage.rounds.length }} Rounds</span>
      </div>
      <table class="details-table">
        <thead>
          <tr>
            <th>#</th>
            <th>当前窗口</th>
            <th>总输入</th>
            <th>总输出</th>
            <th>总缓存</th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(round, i) in usage.rounds"
            :key="i"
            :class="{ 'row-window-drop': isWindowDrop(i) }"
          >
            <td class="col-num">{{ i + 1 }}</td>
            <td>
              {{ formatTokens(round.inputTokens) }}
              <span v-if="isWindowDrop(i)" class="drop-indicator">↓</span>
            </td>
            <td>{{ formatTokens(round.inputTokens) }}</td>
            <td>{{ formatTokens(round.outputTokens) }}</td>
            <td>{{ formatTokens(round.cacheReadTokens) }}</td>
            <td class="col-duration">{{ round.duration ? formatDuration(round.duration) : '-' }}</td>
          </tr>
          <tr class="row-sum">
            <td class="col-num">Sum</td>
            <td>{{ formatTokens(currentWindowInput) }}</td>
            <td>{{ formatTokens(totalInput) }}</td>
            <td>{{ formatTokens(totalOutput) }}</td>
            <td>{{ formatTokens(totalCached) }}</td>
            <td class="col-duration">{{ usage.totalDuration ? formatDuration(usage.totalDuration) : '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    </Transition>

    <Transition name="usage-details">
    <div v-if="toolsExpanded && toolCalls && toolCalls.length > 0" ref="toolsDetailsRef" class="tools-details">
      <div class="details-header">
        <span class="detail-toggle" @click="toggleToolsDetails">▾ Tool Calls</span>
        <span class="tools-badge">{{ toolCalls.length }} 工具</span>
      </div>
      <table class="details-table">
        <thead>
          <tr>
            <th>#</th>
            <th class="th-name">名称</th>
            <th>状态</th>
            <th>耗时</th>
            <th>返回长度</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(tc, i) in toolCalls" :key="i">
            <td class="col-num">{{ i + 1 }}</td>
            <td class="col-tool-name">{{ tc.name }}</td>
            <td><span class="status-dot" :class="tc.status" />{{ statusLabel(tc.status) }}</td>
            <td class="col-duration">{{ tc.duration ? formatDuration(tc.duration) : '-' }}</td>
            <td>{{ tc.resultLength ? formatSize(tc.resultLength) : '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import type { MessageUsage, ToolCall } from '@/stores/chat'

const props = defineProps<{
  usage: MessageUsage | undefined
  toolCalls?: ToolCall[]
}>()
const expanded = ref(false)
const toolsExpanded = ref(false)
const usageDetailsRef = ref<HTMLElement>()
const toolsDetailsRef = ref<HTMLElement>()

const totalInput = computed(() =>
  props.usage?.rounds.reduce((s, r) => s + r.inputTokens, 0) || 0
)
const totalOutput = computed(() =>
  props.usage?.rounds.reduce((s, r) => s + r.outputTokens, 0) || 0
)
const totalCached = computed(() =>
  props.usage?.rounds.reduce((s, r) => s + r.cacheReadTokens, 0) || 0
)
const totalReasoning = computed(() =>
  props.usage?.rounds.reduce((s, r) => s + (r.reasoningTokens || 0), 0) || 0
)
const currentWindowInput = computed(() => {
  const rounds = props.usage?.rounds || []
  return rounds.length > 0 ? rounds[rounds.length - 1].inputTokens : 0
})

function isWindowDrop(index: number): boolean {
  const rounds = props.usage?.rounds || []
  if (index <= 0 || index >= rounds.length) return false
  const previous = rounds[index - 1]?.inputTokens || 0
  const current = rounds[index]?.inputTokens || 0
  if (previous <= 0 || current <= 0) return false
  return current <= previous * 0.7
}

function formatTokens(n: number): string {
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

function formatDuration(ms: number): string {
  if (ms < 1000) return ms + 'ms'
  return (ms / 1000).toFixed(1) + 's'
}

function formatSize(len: number): string {
  if (len < 1024) return `${len} chars`
  return `${(len / 1024).toFixed(1)}K`
}

function statusLabel(status: string): string {
  switch (status) {
    case 'done': return '完成'
    case 'running': return '执行中'
    case 'error': return '错误'
    default: return '等待'
  }
}

async function scrollDetailsIntoView(target: typeof usageDetailsRef) {
  await nextTick()
  target.value?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
}

function toggleRoundsDetails() {
  expanded.value = !expanded.value
  if (expanded.value) {
    scrollDetailsIntoView(usageDetailsRef)
  }
}

function toggleToolsDetails() {
  toolsExpanded.value = !toolsExpanded.value
  if (toolsExpanded.value) {
    scrollDetailsIntoView(toolsDetailsRef)
  }
}
</script>

<style scoped>
.token-usage-panel {
  margin-top: 12px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 12px;
  font-size: 12px;
}

.usage-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  margin-bottom: 10px;
}

.usage-title {
  font-weight: 700;
  color: var(--el-text-color-primary);
  font-size: 13px;
}

.usage-badges {
  display: flex;
  gap: 8px;
}

.badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}

.badge-rounds {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border: 1px solid var(--el-color-primary-light-5);
}

.badge-tools {
  background: var(--el-fill-color);
  color: var(--el-text-color-primary);
  border: 1px solid var(--el-border-color);
}

.badge-time {
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
  border: 1px solid var(--el-color-success-light-5);
}

.usage-summary {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 8px;
}

.summary-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 10px 12px;
  text-align: center;
}

.summary-card-window {
  border-color: var(--el-color-primary-light-5);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--el-color-primary) 18%, transparent);
}

.summary-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  font-family: 'JetBrains Mono', monospace;
}

.summary-label {
  font-size: 12px;
  color: var(--el-text-color-primary);
  margin-top: 4px;
  font-weight: 600;
}

.summary-sub {
  margin-top: 4px;
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.summary-sub.reasoning {
  color: var(--el-color-warning-dark-2);
}

.summary-sub.time {
  color: var(--el-color-success);
}

.usage-summary-minimal {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  color: var(--el-text-color-secondary);
}

.minimal-info {
  font-size: 12px;
}

.usage-details,
.tools-details {
  margin-top: 12px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
}

.usage-details-enter-active,
.usage-details-leave-active {
  transition: all 0.18s ease;
}

.usage-details-enter-from,
.usage-details-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.usage-details-enter-to,
.usage-details-leave-from {
  opacity: 1;
  transform: translateY(0);
}

.details-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
}

.detail-toggle {
  font-weight: 600;
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.rounds-badge,
.tools-badge {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.details-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.details-table th,
.details-table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  text-align: left;
  vertical-align: middle;
}

.details-table th {
  color: var(--el-text-color-secondary);
  font-weight: 600;
  background: color-mix(in srgb, var(--el-fill-color-light) 70%, transparent);
}

.details-table tbody tr:last-child td {
  border-bottom: none;
}

.row-sum {
  font-weight: 700;
  background: color-mix(in srgb, var(--el-color-primary-light-9) 55%, transparent);
}

.row-window-drop {
  background: color-mix(in srgb, var(--el-color-warning-light-9) 70%, transparent);
}

.drop-indicator {
  margin-left: 4px;
  color: var(--el-color-warning-dark-2);
  font-weight: 700;
}

.col-num {
  width: 52px;
}

.col-duration {
  white-space: nowrap;
}

.th-name,
.col-tool-name {
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  margin-right: 6px;
  vertical-align: middle;
}

.status-dot.done {
  background: var(--el-color-success);
}

.status-dot.running {
  background: var(--el-color-primary);
}

.status-dot.error {
  background: var(--el-color-danger);
}

.status-dot.pending {
  background: var(--el-color-warning);
}

.card-cached .summary-value {
  color: var(--el-color-success-dark-2);
}

@media (max-width: 720px) {
  .usage-summary {
    grid-template-columns: 1fr 1fr;
  }

  .details-table {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }
}
</style>

`````

--- **end of file: frontend/src/components/chat/TokenUsagePanel.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/chat/ToolCallCard.vue** (project: lc_agent) --- 

`````vue
<template>
  <div class="tool-call-card" :class="[toolCall.status, { 'is-collapsed': isCollapsed }]">
    <div class="tool-header" @click.stop="toggleCollapse">
      <span class="collapse-icon">{{ isCollapsed ? '▸' : '▾' }}</span>
      <el-icon v-if="toolCall.status === 'running'" class="spinning">
        <Loading />
      </el-icon>
      <el-icon v-else-if="toolCall.status === 'done'" style="color: var(--el-color-success)">
        <Check />
      </el-icon>
      <span class="tool-kind">
        <el-icon><Tools /></el-icon>
        工具调用
      </span>
      <span class="tool-name">{{ toolCall.name }}</span>
      <el-tag size="small" :type="statusType">{{ statusLabel }}</el-tag>
      <span class="tool-meta" v-if="toolCall.status === 'done'">
        <span v-if="toolCall.duration" class="meta-item">⏱ {{ formatDuration(toolCall.duration) }}</span>
        <span v-if="toolCall.resultLength" class="meta-item">📦 {{ formatSize(toolCall.resultLength) }}</span>
      </span>
    </div>
    <template v-if="!isCollapsed">
    <div v-if="toolCall.args && Object.keys(toolCall.args).length > 0" class="tool-args">
      <div v-for="arg in formatArgs(toolCall.args)" :key="arg.key" class="arg-row">
        <span class="arg-key">{{ arg.key }}:</span>
        <span class="arg-value">{{ arg.value }}</span>
      </div>
    </div>
    <div v-if="toolCall.result" class="tool-result">
      <div class="tool-result-rendered" v-html="renderedResult" />
      <button v-if="isLong" class="fullscreen-btn" @click.stop="showModal = true" title="查看完整内容">⛶</button>
    </div>
    </template>

    <teleport to="body">
      <div v-if="showModal" class="tool-modal-backdrop" @click="showModal = false">
        <div class="tool-modal" role="dialog" aria-modal="true" @click.stop>
          <div class="tool-modal-header">
            <div class="tool-modal-title-wrap">
              <span class="tool-modal-kicker">工具结果</span>
              <span class="tool-modal-title">{{ toolCall.name }}</span>
            </div>
            <div class="modal-actions">
              <button class="tool-modal-close" aria-label="关闭" @click="showModal = false">✕</button>
            </div>
          </div>
          <div class="tool-modal-toolbar">
            <input
              v-model="searchQuery"
              class="tool-search-input"
              type="text"
              placeholder="搜索关键字..."
              @keydown.enter.prevent="jumpToNextMatch"
            />
            <div class="tool-search-actions">
              <span v-if="searchQuery" class="tool-search-count">{{ activeMatchLabel }}</span>
              <button class="tool-search-btn" :disabled="!matchCount" @click="jumpToPrevMatch">↑</button>
              <button class="tool-search-btn" :disabled="!matchCount" @click="jumpToNextMatch">↓</button>
            </div>
          </div>
          <div class="tool-modal-content">
            <div ref="modalBodyRef" class="tool-modal-body rendered" v-html="modalRenderedResult" />
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { Loading, Check, Tools } from '@element-plus/icons-vue'
import type { ToolCall } from '@/stores/chat'

const props = defineProps<{ toolCall: ToolCall; collapsed?: boolean }>()
const showModal = ref(false)
const isCollapsed = ref(props.collapsed ?? false)
const userToggled = ref(false)
const searchQuery = ref('')
const activeMatchIndex = ref(0)
const modalBodyRef = ref<HTMLElement | null>(null)

function toggleCollapse() {
  userToggled.value = true
  isCollapsed.value = !isCollapsed.value
}

watch(() => props.collapsed, (collapsed) => {
  if (userToggled.value || collapsed === undefined) return
  isCollapsed.value = collapsed
}, { immediate: true })

const isLong = computed(() => (props.toolCall.result?.length || 0) > 300)

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function normalizeResult(value?: string): string {
  if (!value) return ''
  return value
    .replace(/\\u3000/g, '　')
    .replace(/\\n/g, '\n')
}

function renderTextToHtml(value: string): string {
  return escapeHtml(value)
    .replace(/\n/g, '<br>')
    .replace(/ {2}/g, '&nbsp;&nbsp;')
}

const normalizedResult = computed(() => normalizeResult(props.toolCall.result))

const renderedResult = computed(() => renderTextToHtml(normalizedResult.value))

const modalRenderedResult = computed(() => {
  const query = searchQuery.value.trim()
  if (!query) return renderedResult.value

  const highlighted = normalizedResult.value.replace(
    new RegExp(escapeRegExp(query), 'gi'),
    (match) => `@@HIT_START@@${match}@@HIT_END@@`,
  )

  return renderTextToHtml(highlighted)
    .replace(/@@HIT_START@@/g, '<mark class="tool-search-hit">')
    .replace(/@@HIT_END@@/g, '</mark>')
})

const matchCount = computed(() => {
  const query = searchQuery.value.trim()
  if (!query) return 0
  const matches = normalizedResult.value.match(new RegExp(escapeRegExp(query), 'gi'))
  return matches?.length || 0
})

const activeMatchLabel = computed(() => {
  if (!matchCount.value) return '0/0'
  return `${activeMatchIndex.value + 1}/${matchCount.value}`
})

async function syncSearchHighlights() {
  await nextTick()
  const container = modalBodyRef.value
  if (!container) return
  const hits = Array.from(container.querySelectorAll('mark.tool-search-hit')) as HTMLElement[]
  hits.forEach((hit, index) => {
    hit.classList.toggle('is-active', index === activeMatchIndex.value)
  })
  if (hits.length > 0) {
    hits[activeMatchIndex.value]?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }
}

function jumpToNextMatch() {
  if (!matchCount.value) return
  activeMatchIndex.value = (activeMatchIndex.value + 1) % matchCount.value
}

function jumpToPrevMatch() {
  if (!matchCount.value) return
  activeMatchIndex.value = (activeMatchIndex.value - 1 + matchCount.value) % matchCount.value
}

watch(searchQuery, () => {
  activeMatchIndex.value = 0
  syncSearchHighlights()
})

watch(activeMatchIndex, () => {
  syncSearchHighlights()
})

watch(showModal, (visible) => {
  if (!visible) {
    searchQuery.value = ''
    activeMatchIndex.value = 0
    return
  }
  syncSearchHighlights()
})


function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function formatSize(len: number): string {
  if (len < 1024) return `${len} chars`
  return `${(len / 1024).toFixed(1)}K chars`
}

function formatArgs(args: Record<string, any>): { key: string; value: string }[] {
  return Object.entries(args).map(([k, v]) => {
    let val: string
    if (Array.isArray(v)) {
      val = v.map((item, i) => `${String.fromCharCode(65 + i)}. ${item}`).join('\n')
    } else if (typeof v === 'string') {
      val = v
    } else {
      val = JSON.stringify(v)
    }
    if (val.length > 200) val = val.slice(0, 200) + '...'
    return { key: k, value: val }
  })
}

const statusType = computed(() => {
  switch (props.toolCall.status) {
    case 'running': return 'warning'
    case 'done': return 'success'
    case 'error': return 'danger'
    default: return 'info'
  }
})

const statusLabel = computed(() => {
  switch (props.toolCall.status) {
    case 'running': return '执行中'
    case 'done': return '完成'
    case 'error': return '错误'
    default: return '等待'
  }
})
</script>

<style scoped>
.tool-call-card {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 10px 14px;
  margin: 6px 0;
  background: var(--el-fill-color-light);
  border-left: 3px solid var(--el-text-color-secondary);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.tool-call-card.running {
  border-left-color: var(--el-color-primary);
  box-shadow: 0 0 12px color-mix(in srgb, var(--el-color-primary) 8%, transparent);
}

.tool-call-card.done {
  border-left-color: var(--el-color-success);
}

.tool-call-card.error {
  border-left-color: var(--el-color-danger);
}

.tool-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.tool-header:hover {
  opacity: 0.85;
}

.collapse-icon {
  font-size: 10px;
  color: var(--el-text-color-secondary);
  width: 12px;
  flex-shrink: 0;
}

.is-collapsed {
  padding: 6px 14px;
}

.tool-name {
  flex: 1 1 180px;
  min-width: 0;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
  color: var(--el-color-primary);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-kind {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 7px;
  border-radius: 999px;
  color: var(--el-text-color-regular);
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.tool-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
  flex-shrink: 0;
}

.meta-item {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.tool-args {
  margin-top: 6px;
  padding: 5px 8px;
  background: var(--el-fill-color);
  border-radius: 4px;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
}

.arg-row {
  display: flex;
  gap: 6px;
  padding: 1px 0;
  line-height: 1.5;
}

.arg-key {
  color: var(--el-color-primary);
  flex-shrink: 0;
  font-weight: 500;
}

.arg-value {
  color: var(--el-text-color-regular);
  word-break: break-all;
  white-space: pre-wrap;
}

.tool-result {
  margin-top: 8px;
  padding: 8px 10px;
  background: var(--el-fill-color);
  border-radius: 6px;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--el-border-color);
  position: relative;
}

.tool-result-rendered {
  margin: 0;
  white-space: normal;
  word-break: break-word;
  overflow-wrap: anywhere;
  color: var(--el-text-color-secondary);
  line-height: 1.65;
}

.fullscreen-btn {
  position: sticky;
  bottom: 0;
  float: right;
  padding: 2px 8px;
  font-size: 14px;
  color: var(--el-color-primary);
  background: var(--el-bg-color);
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.fullscreen-btn:hover {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
}

.tool-modal-backdrop {
  position: fixed;
  inset: 0;
  background: color-mix(in srgb, var(--el-bg-color-page) 70%, transparent);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.tool-modal {
  width: min(900px, calc(100vw - 80px));
  max-height: min(80vh, 760px);
  min-height: 0;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 16px 48px color-mix(in srgb, var(--el-bg-color-page) 50%, transparent);
}

.tool-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color);
  gap: 12px;
  flex: 0 0 auto;
}

.tool-modal-title-wrap {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tool-modal-kicker {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.modal-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.modal-toggle-btn {
  padding: 4px 10px;
  font-size: 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-fill-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: all 0.15s ease;
}

.modal-toggle-btn:hover {
  background: var(--el-fill-color-light);
}

.modal-toggle-btn.active {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.tool-modal-title {
  min-width: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-modal-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 16px;
  cursor: pointer;
}

.tool-modal-close:hover {
  background: var(--el-fill-color);
  color: var(--el-text-color-primary);
}

.tool-modal-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: color-mix(in srgb, var(--el-fill-color-light) 78%, transparent);
}

.tool-search-input {
  flex: 1 1 auto;
  min-width: 0;
  height: 34px;
  padding: 0 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  outline: none;
}

.tool-search-input:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 14%, transparent);
}

.tool-search-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.tool-search-count {
  min-width: 42px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: right;
}

.tool-search-btn {
  width: 30px;
  height: 30px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
}

.tool-search-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.tool-modal-content {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}

.tool-modal-body {
  min-height: 100%;
  padding: 16px;
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
  color: var(--el-text-color-regular);
}

.tool-modal-body.rendered {
  white-space: normal;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}

.tool-modal-body :deep(.tool-search-hit),
.tool-modal-body.rendered :deep(.tool-search-hit) {
  background: rgba(250, 204, 21, 0.35);
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
}

.tool-modal-body :deep(.tool-search-hit.is-active),
.tool-modal-body.rendered :deep(.tool-search-hit.is-active) {
  background: rgba(245, 158, 11, 0.78);
}

.spinning {
  animation: spin 1s linear infinite;
  color: var(--el-color-primary);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 520px) {
  .tool-call-card {
    padding: 9px 10px;
  }

  .is-collapsed {
    padding: 7px 10px;
  }

  .tool-header {
    gap: 6px;
  }

  .tool-name {
    flex-basis: 100%;
    order: 10;
    padding-left: 24px;
    max-width: 100%;
  }

  .tool-meta {
    margin-left: 0;
    gap: 7px;
  }

  .tool-modal-backdrop {
    align-items: stretch;
    justify-content: stretch;
    padding: max(8px, env(safe-area-inset-top)) max(8px, env(safe-area-inset-right)) max(8px, env(safe-area-inset-bottom)) max(8px, env(safe-area-inset-left));
    background: color-mix(in srgb, var(--el-bg-color-page) 88%, transparent);
  }

  .tool-modal {
    width: 100%;
    max-height: none;
    height: 100%;
    border-radius: 12px;
    min-width: 0;
  }

  .tool-modal-header {
    position: sticky;
    top: 0;
    z-index: 1;
    padding: 10px 10px 9px;
    background: var(--el-bg-color);
    gap: 8px;
  }

  .tool-modal-title-wrap {
    flex: 1 1 auto;
  }

  .tool-modal-title {
    font-size: 12px;
  }

  .tool-modal-kicker {
    display: none;
  }

  .modal-actions {
    gap: 6px;
  }

  .modal-toggle-btn {
    padding: 5px 8px;
    font-size: 12px;
    white-space: nowrap;
  }

  .tool-modal-close {
    width: 34px;
    height: 34px;
    font-size: 18px;
  }

  .tool-modal-toolbar {
    padding: 8px 10px;
    gap: 8px;
    flex-wrap: wrap;
  }

  .tool-search-input {
    width: 100%;
    height: 36px;
  }

  .tool-search-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .tool-search-count {
    margin-right: auto;
    text-align: left;
  }

  .tool-modal-content {
    flex: 1 1 auto;
  }

  .tool-modal-body {
    padding: 12px 10px 18px;
    font-size: 12px;
    line-height: 1.65;
  }
}
</style>

`````

--- **end of file: frontend/src/components/chat/ToolCallCard.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/dialogs/AgentEditorDialog.vue** (project: lc_agent) --- 

`````vue
<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑 Agent' : '新建 Agent'"
    width="600px"
    class="agent-editor-dialog"
    :close-on-click-modal="false"
  >
    <el-alert v-if="isCodeAgent" type="warning" :closable="false" style="margin-bottom: 12px">
      此智能体由代码注册（CompiledGraph），工具、MCP、Skills、提示词和模型由代码中的 graph 决定。此处仅展示说明，不能修改框架级配置。
    </el-alert>

    <el-form v-if="!isCodeAgent" :model="form" label-width="100px" label-position="top">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="基本设置" name="basic">
      <el-form-item label="名称" required>
        <el-input v-model="form.name" :disabled="isCodeAgent" placeholder="例如：code-assistant、researcher" />
        <div class="form-hint">只能使用英文字母、数字、连字符(-)和下划线(_)，且必须以字母开头</div>
      </el-form-item>

      <el-form-item label="显示名称">
        <el-input v-model="form.display_name" :disabled="isCodeAgent" placeholder="可填中文，例如：代码助手（留空则显示名称字段）" />
      </el-form-item>

      <el-form-item label="模型">
        <el-select v-model="form.default_model" :disabled="isCodeAgent" filterable style="width:100%" placeholder="选择默认模型">
          <el-option
            v-for="model in toolsStore.models"
            :key="model.id"
            :label="`${model.id} (${model.provider})`"
            :value="model.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="Temperature">
        <div class="llm-param-item">
          <el-checkbox
            :model-value="form.llm_params?.temperature !== undefined"
            :disabled="isCodeAgent"
            @update:model-value="toggleTemperature"
          >为此预设固定温度值</el-checkbox>
          <div v-if="form.llm_params?.temperature !== undefined" class="temperature-preset-control">
            <el-slider
              :model-value="form.llm_params.temperature"
              :min="0"
              :max="2"
              :step="0.05"
              :disabled="isCodeAgent"
              class="temp-slider"
              @update:model-value="setTemperature"
            />
            <el-input-number
              :model-value="form.llm_params.temperature"
              :min="0"
              :max="2"
              :step="0.05"
              :precision="2"
              size="small"
              controls-position="right"
              :disabled="isCodeAgent"
              style="width: 80px"
              @update:model-value="setTemperature"
            />
          </div>
          <span v-else class="param-hint">留空时运行时默认 0.7</span>
        </div>
      </el-form-item>

      <el-form-item label="思考级别（reasoning_effort）">
        <div class="llm-param-item">
          <el-checkbox
            :model-value="form.llm_params?.reasoning_effort !== undefined"
            :disabled="isCodeAgent"
            @update:model-value="toggleReasoningEffort"
          >为此预设固定思考级别</el-checkbox>
          <el-select
            v-if="form.llm_params?.reasoning_effort !== undefined"
            :model-value="form.llm_params.reasoning_effort"
            size="small"
            :disabled="isCodeAgent"
            style="width: 140px; margin-top: 6px"
            @update:model-value="setReasoningEffort"
          >
            <el-option
              v-for="effort in REASONING_EFFORTS"
              :key="effort"
              :label="effort"
              :value="effort"
            />
          </el-select>
          <span v-else class="param-hint">留空时由模型决定</span>
        </div>
      </el-form-item>

      <el-form-item label="系统提示词">
        <el-input
          v-model="form.system_prompt"
          :disabled="isCodeAgent"
          type="textarea"
          :autosize="{ minRows: 4, maxRows: 12 }"
          placeholder="定义 Agent 的行为和角色..."
        />
      </el-form-item>

      <el-form-item label="允许的工具组">
        <div class="tool-group-select">
          <el-radio-group v-model="toolGroupMode" size="small">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="none">无</el-radio-button>
            <el-radio-button value="custom">自定义</el-radio-button>
          </el-radio-group>
          <div v-if="toolGroupMode === 'custom'" class="custom-groups">
            <el-checkbox-group v-model="selectedGroups">
              <el-checkbox
                v-for="group in toolsStore.groups"
                :key="group.id"
                :value="group.id"
              >
                {{ group.description || group.id }} ({{ group.tools.length }} tools)
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </div>
      </el-form-item>

      <el-form-item label="允许的 MCP 服务器">
        <div class="tool-group-select">
          <el-radio-group v-model="mcpMode" size="small">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="none">无</el-radio-button>
            <el-radio-button value="custom">自定义</el-radio-button>
          </el-radio-group>
          <div v-if="mcpMode === 'custom'" class="custom-groups">
            <el-checkbox-group v-model="selectedMcpServers">
              <el-checkbox
                v-for="server in toolsStore.mcpServers"
                :key="server.name"
                :value="server.name"
              >
                {{ server.name }}
                <el-tag size="small" :type="server.status === 'connected' ? 'success' : 'info'" style="margin-left:4px">
                  {{ server.tools?.length || 0 }} tools
                </el-tag>
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </div>
      </el-form-item>

      <el-form-item label="允许的 Skills">
        <div class="tool-group-select">
          <el-radio-group v-model="skillsMode" size="small">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="none">无</el-radio-button>
            <el-radio-button value="custom">自定义</el-radio-button>
          </el-radio-group>
          <div v-if="skillsMode === 'custom'" class="custom-groups">
            <el-checkbox-group v-model="selectedSkills">
              <el-checkbox
                v-for="skill in toolsStore.skills"
                :key="skill.name"
                :value="skill.name"
              >
                {{ skill.name }}
                <span class="skill-hint">{{ skill.description }}</span>
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </div>
      </el-form-item>
        </el-tab-pane>

        <el-tab-pane label="子Agent" name="subagents">
          <div class="subagent-picker">
            <div class="general-purpose-subagent">
              <el-checkbox v-model="form.enable_general_purpose_subagent">
                <span style="font-weight: 600;">启用通用子 Agent</span>
              </el-checkbox>
              <p class="picker-hint" style="font-size:12px; color: var(--el-text-color-secondary); margin: 4px 0 12px 24px;">
                让当前 Agent 可以把复杂任务委派给一个同能力的隔离 worker。该 worker 不会继续调用 task。
              </p>
            </div>
            <p class="picker-hint" style="font-size:12px; color: var(--el-text-color-secondary); margin-bottom: 12px;">
              选择专业子 Agent，并为每个子 Agent 填写委派说明。
            </p>
            <div class="subagent-list">
              <div
                v-for="sa in availableSubagents"
                :key="sa.id"
                class="subagent-item"
              >
                <el-checkbox
                  :model-value="isSubagentSelected(sa.id)"
                  @update:model-value="toggleSubagent(sa.id, $event)"
                >
                  <span class="sa-item-name" style="font-weight: 600;">{{ sa.display_name || sa.name }}</span>
                  <el-tag
                    size="small"
                    :type="sa.source === 'code' ? 'info' : sa.source === 'builtin' ? 'warning' : 'primary'"
                    style="margin-left: 6px;"
                  >
                    {{ sa.source }}
                  </el-tag>
                </el-checkbox>
                <span v-if="sa.description" class="sa-item-desc">
                  {{ sa.description }}
                </span>
                <div v-if="isSubagentSelected(sa.id)" class="subagent-delegation-section">
                  <p class="subagent-delegation-help">
                    填写该子 Agent 适合处理什么任务，以便主 Agent 能在正确、合适的时机触发调用它，作用类似 Skill 的 description；不能为空。
                  </p>
                  <el-input
                    :model-value="getSubagentDelegationDescription(sa.id)"
                    type="textarea"
                    :autosize="{ minRows: 2, maxRows: 4 }"
                    placeholder="例如：当对话涉及数据分析、报表生成时调用它"
                    class="subagent-delegation-input"
                    @update:model-value="setSubagentDelegationDescription(sa.id, $event)"
                  />
                </div>
              </div>
            </div>
            <el-empty
              v-if="availableSubagents.length === 0"
              description="暂无可用的子 Agent"
              :image-size="60"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-form>

    <div v-else class="code-agent-readonly">
      <div class="readonly-row">
        <span class="readonly-label">名称</span>
        <span class="readonly-value">{{ form.name }}</span>
      </div>
      <div class="readonly-row">
        <span class="readonly-label">说明</span>
        <span class="readonly-value">{{ form.system_prompt }}</span>
      </div>
      <div class="readonly-row">
        <span class="readonly-label">运行模型</span>
        <span class="readonly-value">由代码 graph 决定</span>
      </div>
      <div class="readonly-row">
        <span class="readonly-label">工具能力</span>
        <span class="readonly-value">由代码 graph 决定</span>
      </div>
    </div>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="danger" v-if="isEdit && !agentsStore.isAgentBuiltin(editingId!) && !isCodeAgent" @click="handleDelete">
        删除
      </el-button>
      <el-button v-if="!isCodeAgent" type="primary" :loading="saving" @click="handleSave">
        {{ isEdit ? '保存' : '创建' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchAvailableSubagents } from '@/api/http'
import { useToolsStore } from '@/stores/tools'
import { useAgentsStore, type AgentPreset, type AgentSubagentConfig } from '@/stores/agents'

const REASONING_EFFORTS = ['none', 'minimal', 'low', 'medium', 'high', 'xhigh']

const toolsStore = useToolsStore()
const agentsStore = useAgentsStore()

const visible = ref(false)
const saving = ref(false)
const activeTab = ref('basic')
const isEdit = ref(false)
const editingId = ref('')
const editingSource = ref<'builtin' | 'code' | 'user'>('user')
const toolGroupMode = ref<'all' | 'none' | 'custom'>('all')
const selectedGroups = ref<string[]>([])
const mcpMode = ref<'all' | 'none' | 'custom'>('all')
const selectedMcpServers = ref<string[]>([])
const skillsMode = ref<'all' | 'none' | 'custom'>('all')
const selectedSkills = ref<string[]>([])
const availableSubagents = ref<Array<{ id: string; name: string; display_name: string | null; source: string; description: string }>>([])

const isCodeAgent = ref(false)

const form = ref({
  name: '',
  display_name: '',
  system_prompt: '',
  default_model: '',
  llm_params: null as Record<string, any> | null,
  subagents: [] as AgentSubagentConfig[],
  enable_general_purpose_subagent: false,
})

async function open(agent?: AgentPreset) {
  activeTab.value = 'basic'
  const all = await fetchAvailableSubagents()
  availableSubagents.value = all.filter(sa => sa.id !== (agent?.id ?? ''))

  if (agent) {
    isEdit.value = true
    editingId.value = agent.id
    editingSource.value = agent.source || 'user'
    isCodeAgent.value = agent.source === 'code'
    form.value.name = agent.name
    form.value.display_name = agent.display_name ?? ''
    form.value.system_prompt = agent.system_prompt
    form.value.default_model = agent.default_model
    form.value.llm_params = agent.llm_params ?? null
    form.value.subagents = agent.subagents ? agent.subagents.map(item => ({ ...item })) : []
    form.value.enable_general_purpose_subagent = agent.enable_general_purpose_subagent ?? false

    if (agent.allowed_tool_groups === null) {
      toolGroupMode.value = 'all'
      selectedGroups.value = []
    } else if (agent.allowed_tool_groups.length === 0) {
      toolGroupMode.value = 'none'
      selectedGroups.value = []
    } else {
      toolGroupMode.value = 'custom'
      selectedGroups.value = [...agent.allowed_tool_groups]
    }

    if (agent.allowed_mcp_servers === null) {
      mcpMode.value = 'all'
      selectedMcpServers.value = []
    } else if (agent.allowed_mcp_servers.length === 0) {
      mcpMode.value = 'none'
      selectedMcpServers.value = []
    } else {
      mcpMode.value = 'custom'
      selectedMcpServers.value = [...agent.allowed_mcp_servers]
    }

    if (agent.allowed_skills === null) {
      skillsMode.value = 'all'
      selectedSkills.value = []
    } else if (agent.allowed_skills.length === 0) {
      skillsMode.value = 'none'
      selectedSkills.value = []
    } else {
      skillsMode.value = 'custom'
      selectedSkills.value = [...agent.allowed_skills]
    }
  } else {
    isEdit.value = false
    editingId.value = ''
    editingSource.value = 'user'
    isCodeAgent.value = false
    form.value = {
      name: '',
      display_name: '',
      system_prompt: '',
      default_model: toolsStore.currentModel,
      llm_params: null,
      subagents: [],
      enable_general_purpose_subagent: false,
    }
    toolGroupMode.value = 'none'
    selectedGroups.value = []
    mcpMode.value = 'none'
    selectedMcpServers.value = []
    skillsMode.value = 'none'
    selectedSkills.value = []
  }
  visible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    const namePattern = /^[a-zA-Z][a-zA-Z0-9_-]*$/
    if (!namePattern.test(form.value.name)) {
      ElMessage.error('名称只能使用英文字母、数字、连字符(-)和下划线(_)，且必须以字母开头')
      return
    }

    const allowed_tool_groups =
      toolGroupMode.value === 'all' ? null :
      toolGroupMode.value === 'none' ? [] :
      selectedGroups.value

    const allowed_mcp_servers =
      mcpMode.value === 'all' ? null :
      mcpMode.value === 'none' ? [] :
      selectedMcpServers.value

    const allowed_skills =
      skillsMode.value === 'all' ? null :
      skillsMode.value === 'none' ? [] :
      selectedSkills.value

    if (form.value.subagents.some(item => !item.delegation_description.trim())) {
      activeTab.value = 'subagents'
      ElMessage.error('每个已选择的子 Agent 都必须填写非空的委派说明')
      return
    }

    const normalizedSubagents = form.value.subagents.map(item => ({
      agent_id: item.agent_id,
      delegation_description: item.delegation_description.trim(),
    }))

    const data = {
      name: form.value.name,
      display_name: form.value.display_name || null,
      system_prompt: form.value.system_prompt,
      default_model: form.value.default_model,
      allowed_tool_groups,
      allowed_mcp_servers,
      allowed_skills,
      llm_params: form.value.llm_params || null,
      subagents: normalizedSubagents.length > 0 ? normalizedSubagents : null,
      enable_general_purpose_subagent: form.value.enable_general_purpose_subagent,
    }

    if (isEdit.value) {
      await agentsStore.updateAgent(editingId.value, data)
    } else {
      await agentsStore.createAgent(data as any)
    }
    visible.value = false
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  await agentsStore.deleteAgent(editingId.value)
  visible.value = false
}

function isSubagentSelected(agentId: string) {
  return form.value.subagents.some(item => item.agent_id === agentId)
}

function getSubagentDelegationDescription(agentId: string) {
  return form.value.subagents.find(item => item.agent_id === agentId)?.delegation_description || ''
}

function toggleSubagent(agentId: string, checked: boolean | string | number) {
  if (checked) {
    if (!isSubagentSelected(agentId)) {
      form.value.subagents.push({ agent_id: agentId, delegation_description: '' })
    }
    return
  }
  form.value.subagents = form.value.subagents.filter(item => item.agent_id !== agentId)
}

function setSubagentDelegationDescription(agentId: string, value: string | number) {
  const item = form.value.subagents.find(entry => entry.agent_id === agentId)
  if (!item) return
  item.delegation_description = String(value)
}

function _ensureLlmParams() {
  if (!form.value.llm_params) form.value.llm_params = {}
}

function _cleanLlmParams() {
  if (form.value.llm_params && !Object.keys(form.value.llm_params).length) {
    form.value.llm_params = null
  }
}

function toggleTemperature(v: boolean) {
  if (v) {
    _ensureLlmParams()
    form.value.llm_params!.temperature = 0.7
  } else {
    if (form.value.llm_params) {
      delete form.value.llm_params.temperature
      _cleanLlmParams()
    }
  }
}

function setTemperature(v: number | undefined) {
  if (v === undefined) return
  _ensureLlmParams()
  form.value.llm_params!.temperature = v
}

function toggleReasoningEffort(v: boolean) {
  if (v) {
    _ensureLlmParams()
    form.value.llm_params!.reasoning_effort = 'medium'
  } else {
    if (form.value.llm_params) {
      delete form.value.llm_params.reasoning_effort
      _cleanLlmParams()
    }
  }
}

function setReasoningEffort(v: string) {
  _ensureLlmParams()
  form.value.llm_params!.reasoning_effort = v
}

defineExpose({ open })
</script>

<style scoped>
.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.llm-param-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.temperature-preset-control {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.temp-slider {
  flex: 1;
}

.param-hint {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-left: 2px;
}

.tool-group-select {
  width: 100%;
}

.custom-groups {
  margin-top: 8px;
  padding: 10px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.custom-groups .el-checkbox {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.skill-hint {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  margin-left: 4px;
  opacity: 0.7;
}

.subagent-picker {
  width: 100%;
}

.subagent-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.subagent-item {
  display: flex;
  flex-direction: column;
  width: 100%;
  padding: 10px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-extra-light);
}

.subagent-item :deep(.el-checkbox) {
  display: flex;
  align-items: center;
  height: auto;
  width: 100%;
}

.sa-item-desc {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  margin-left: 22px;
  margin-top: 2px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.subagent-delegation-section {
  margin-top: 8px;
  margin-left: 22px;
  padding-right: 10px;
}

.subagent-delegation-help {
  margin-top: 0;
  margin-left: 0;
  margin-bottom: 6px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
}

.subagent-delegation-input {
  margin-top: 0;
  margin-left: 0;
}

.code-agent-readonly {
  padding: 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-light);
}

.readonly-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.readonly-row:last-child {
  border-bottom: none;
}

.readonly-label {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 600;
}

.readonly-value {
  color: var(--el-text-color-primary);
  font-size: 13px;
  text-align: right;
}

:deep(.agent-editor-dialog) {
  max-width: min(600px, calc(100vw - 24px));
}

@media (max-width: 768px) {
  .subagent-item {
    padding: 10px 8px;
  }

  .sa-item-desc {
    margin-left: 0;
  }

  .subagent-delegation-section {
    margin-left: 0;
    padding-right: 0;
  }

  .subagent-delegation-help {
    margin-left: 0;
  }

  .subagent-delegation-input {
    margin-left: 0;
    width: 100%;
  }
}

</style>

`````

--- **end of file: frontend/src/components/dialogs/AgentEditorDialog.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/dialogs/ChangePasswordDialog.vue** (project: lc_agent) --- 

`````vue
<template>
  <el-dialog v-model="visible" title="修改密码" width="420px" :close-on-click-modal="false" @closed="resetForm">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-form-item label="旧密码" prop="oldPassword">
        <el-input v-model="form.oldPassword" type="password" show-password autocomplete="current-password" />
      </el-form-item>
      <el-form-item label="新密码" prop="newPassword">
        <el-input v-model="form.newPassword" type="password" show-password autocomplete="new-password" />
      </el-form-item>
      <el-form-item label="确认密码" prop="confirmPassword">
        <el-input v-model="form.confirmPassword" type="password" show-password autocomplete="new-password" />
      </el-form-item>
    </el-form>

    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" style="margin-bottom: 12px" />

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">确认</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { changePassword } from '@/api/auth'

const visible = ref(false)
const loading = ref(false)
const error = ref('')
const formRef = ref<FormInstance>()

const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const rules: FormRules = {
  oldPassword: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

function open() {
  error.value = ''
  visible.value = true
}

function resetForm() {
  form.oldPassword = ''
  form.newPassword = ''
  form.confirmPassword = ''
  error.value = ''
  formRef.value?.resetFields()
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  error.value = ''
  try {
    await changePassword(form.oldPassword, form.newPassword)
    ElMessage.success('密码修改成功')
    visible.value = false
  } catch (e: any) {
    error.value = e.message || '修改失败'
  } finally {
    loading.value = false
  }
}

defineExpose({ open })
</script>

`````

--- **end of file: frontend/src/components/dialogs/ChangePasswordDialog.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/layout/AppHeader.vue** (project: lc_agent) --- 

`````vue
<template>
  <header class="app-header">
    <div class="header-left">
      <el-button
        class="mobile-sidebar-btn"
        :icon="Menu"
        circle
        size="small"
        aria-label="打开会话列表"
        @click="$emit('openMobileSidebar')"
      />
      <span class="logo">⚡ {{ appName }}</span>
    </div>
    <div class="header-center">
      <el-select
        class="agent-select"
        :model-value="agentsStore.currentAgentId"
        size="small"
        @change="$emit('changeAgent', $event)"
        :prefix-icon="MagicStick"
        placeholder="选择智能体"
        popper-class="agent-select-popper"
      >
        <el-option
          v-for="agent in agentsStore.agents"
          :key="agent.id"
          :label="agent.display_name || agent.name"
          :value="agent.id"
        >
          <div class="agent-option">
            <span class="agent-option-icon">{{ getAgentIcon(agent) }}</span>
            <div class="agent-option-content">
              <span class="agent-option-name">{{ agent.display_name || agent.name }}</span>
            </div>
            <span :class="['source-tag', `source-tag--${agent.source || 'user'}`]">
              {{ agent.source === 'builtin' ? '内置' : agent.source === 'code' ? '代码' : '自建' }}
            </span>
          </div>
        </el-option>
      </el-select>
      <div class="header-actions desktop-only">
        <button class="header-btn btn-edit" @click="$emit('editAgent')" :disabled="agentsStore.isBuiltin">编辑</button>
        <button class="header-btn btn-new-agent" @click="$emit('newAgent')">+ 新Agent</button>
        <button class="header-btn btn-new-chat" @click="$emit('newChat')">+ 新对话</button>
        <CopyRoundsButton v-if="hasMessages" :messages="chatStore.messages" :model-name="sessionModel" />
      </div>
    </div>
    <div class="header-right">
      <button class="header-btn mobile-new-chat-btn" @click="$emit('newChat')">
        <el-icon class="mobile-btn-icon"><Plus /></el-icon>
        <span class="mobile-btn-text">新对话</span>
      </button>
      <span class="mobile-only">
        <CopyRoundsButton v-if="hasMessages" :messages="chatStore.messages" :model-name="sessionModel" />
      </span>
      <el-dropdown trigger="click" @command="handleUserCommand">
        <span class="user-dropdown-trigger">
          <el-icon><UserFilled /></el-icon>
          <span class="username-text">{{ authStore.user?.username || '用户' }}</span>
          <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="change-password">修改密码</el-dropdown-item>
            <el-dropdown-item v-if="authStore.isAdmin" command="admin">管理后台</el-dropdown-item>
            <el-dropdown-item divided command="logout">登出</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button
        class="mobile-tools-btn"
        :icon="Setting"
        circle
        size="small"
        aria-label="打开工具和状态面板"
        @click="$emit('openMobileTools')"
      />
      <span class="model-badge">{{ modelName }}</span>
      <el-button :icon="RefreshRight" circle size="small" title="刷新页面" @click="reloadPage" />
      <el-button :icon="isDark ? Sunny : Moon" circle size="small" @click="toggleDark()" />
    </div>

    <ChangePasswordDialog ref="changePasswordRef" />
  </header>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAgentsStore } from '@/stores/agents'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useToolsStore } from '@/stores/tools'
import { useTheme } from '@/composables/useTheme'
import { Sunny, Moon, Menu, Setting, RefreshRight, MagicStick, UserFilled, ArrowDown, Plus } from '@element-plus/icons-vue'
import CopyRoundsButton from '@/components/chat/CopyRoundsButton.vue'
import ChangePasswordDialog from '@/components/dialogs/ChangePasswordDialog.vue'

const router = useRouter()
const agentsStore = useAgentsStore()
const authStore = useAuthStore()
const chatStore = useChatStore()
const toolsStore = useToolsStore()
const { isDark, toggleDark } = useTheme()
const changePasswordRef = ref<InstanceType<typeof ChangePasswordDialog>>()

function handleUserCommand(command: string) {
  if (command === 'change-password') {
    changePasswordRef.value?.open()
  } else if (command === 'admin') {
    router.push('/admin')
  } else if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}

function reloadPage() {
  window.location.reload()
}

function getAgentIcon(agent: any): string {
  if (agent.source === 'code') return '⚙️'
  if (agent.id === 'chat') return '💬'
  if (agent.id === 'empty') return '🧩'
  if (agent.source === 'builtin') return '✨'
  return '🤖'
}

const hasMessages = computed(() => chatStore.messages.length > 0)
const sessionModel = computed(() => {
  if (agentsStore.isCodeAgent) return '代码内定义'
  const model = toolsStore.currentModel || agentsStore.currentAgent?.default_model || ''
  if (!model) return ''
  const parts = model.split('/')
  return parts[parts.length - 1] || model
})

defineProps<{
  appName: string
  modelName: string
}>()

defineEmits<{
  editAgent: []
  newAgent: []
  newChat: []
  changeAgent: [id: string]
  openMobileSidebar: []
  openMobileTools: []
}>()
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  height: 52px;
  flex-shrink: 0;
  z-index: 100;
}

.logo {
  font-size: 16px;
  font-weight: 700;
  color: var(--el-color-primary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-center {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mobile-sidebar-btn,
.mobile-tools-btn,
.mobile-new-chat-btn,
.mobile-only {
  display: none;
}

.desktop-only {
  display: inline-flex;
}

.header-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex-wrap: nowrap;
}

.agent-select {
  width: 260px;
}

.agent-select :deep(.el-select__wrapper) {
  min-width: 0;
  min-height: 36px;
  padding: 0 32px 0 10px;
  border-radius: 12px;
  border: 1.5px solid var(--el-color-primary);
  background: var(--el-bg-color);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
  transition: all 0.2s ease;
}

.agent-select :deep(.el-select__wrapper:hover) {
  border-color: var(--el-color-primary);
  box-shadow: 0 4px 14px color-mix(in srgb, var(--el-color-primary) 16%, transparent);
}

.agent-select :deep(.el-select__wrapper.is-focused) {
  border-color: var(--el-color-primary);
  box-shadow:
    0 0 0 3px color-mix(in srgb, var(--el-color-primary) 12%, transparent),
    0 4px 14px color-mix(in srgb, var(--el-color-primary) 16%, transparent);
}

.agent-select :deep(.el-select__prefix) {
  color: var(--el-color-primary);
  margin-right: 4px;
}

.agent-select :deep(.el-select__selected-item) {
  min-width: 0;
  display: block;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: var(--el-text-color-primary);
}

.agent-select :deep(.el-select__caret) {
  color: var(--el-color-primary);
  font-size: 13px;
  opacity: 0.7;
  transition: opacity 0.2s, transform 0.2s;
}

.agent-select :deep(.el-select__wrapper:hover .el-select__caret) {
  opacity: 1;
}

:global(html.dark) .agent-select :deep(.el-select__wrapper) {
  background: rgba(15, 23, 42, 0.9);
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

:global(html.dark) .agent-select :deep(.el-select__wrapper:hover) {
  border-color: var(--el-color-primary);
  box-shadow: 0 4px 18px color-mix(in srgb, var(--el-color-primary) 24%, transparent);
}

:global(html.dark) .agent-select :deep(.el-select__wrapper.is-focused) {
  border-color: var(--el-color-primary);
  box-shadow:
    0 0 0 3px color-mix(in srgb, var(--el-color-primary) 16%, transparent),
    0 6px 20px color-mix(in srgb, var(--el-color-primary) 24%, transparent);
}

.model-badge {
  font-size: 12px;
  padding: 3px 10px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  color: var(--el-text-color-secondary);
}

.user-dropdown-trigger {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--el-border-color);
  background: var(--el-fill-color-light);
  cursor: pointer;
  font-size: 12px;
  color: var(--el-text-color-regular);
  transition: background 0.15s ease, border-color 0.15s ease;
}

.user-dropdown-trigger:hover {
  background: var(--el-fill-color);
  border-color: var(--el-color-primary-light-5);
}

.username-text {
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-arrow {
  font-size: 12px;
  opacity: 0.6;
}


.agent-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 2px 0;
}

.agent-option-icon {
  font-size: 16px;
  flex-shrink: 0;
  width: 22px;
  text-align: center;
}

.agent-option-content {
  flex: 1;
  min-width: 0;
}

.agent-option-name {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 500;
}

.source-tag {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 10px;
  font-weight: 600;
  flex-shrink: 0;
  letter-spacing: 0.02em;
}

.source-tag--builtin {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.1));
  color: #7c3aed;
  border: 1px solid rgba(124, 58, 237, 0.2);
}

.source-tag--code {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(6, 182, 212, 0.1));
  color: #059669;
  border: 1px solid rgba(5, 150, 105, 0.2);
}

.source-tag--user {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(249, 115, 22, 0.1));
  color: #d97706;
  border: 1px solid rgba(217, 119, 6, 0.2);
}

:global(html.dark) .source-tag--builtin {
  background: rgba(124, 58, 237, 0.15);
  color: #a78bfa;
  border-color: rgba(167, 139, 250, 0.25);
}

:global(html.dark) .source-tag--code {
  background: rgba(16, 185, 129, 0.15);
  color: #6ee7b7;
  border-color: rgba(110, 231, 183, 0.25);
}

:global(html.dark) .source-tag--user {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
  border-color: rgba(251, 191, 36, 0.25);
}

.header-btn {
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, border-color 0.18s ease, color 0.18s ease, opacity 0.18s ease;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
}

.header-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.header-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 5px 14px rgba(15, 23, 42, 0.10);
}

.header-btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in srgb, currentColor 18%, transparent), 0 8px 20px rgba(15, 23, 42, 0.12);
}

.btn-edit {
  color: #f5f3ff;
  background: linear-gradient(135deg, #5b4b8a, #475569);
  border-color: rgba(109, 91, 163, 0.42);
}

.btn-edit:hover:not(:disabled) {
  background: linear-gradient(135deg, #6d5fa8, #52627a);
  border-color: rgba(129, 111, 181, 0.5);
}

.btn-edit:disabled {
  opacity: 0.48;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-new-agent {
  color: #ffffff;
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  border-color: rgba(37, 99, 235, 0.42);
}

.btn-new-agent:hover {
  background: linear-gradient(135deg, #1d4ed8, #2563eb);
}

.btn-new-chat,
.mobile-new-chat-btn {
  color: #ffffff;
  background: linear-gradient(135deg, #059669, #10b981);
  border-color: rgba(5, 150, 105, 0.36);
}

.btn-new-chat:hover,
.mobile-new-chat-btn:hover {
  background: linear-gradient(135deg, #047857, #059669);
}

:deep(.copy-rounds-trigger) {
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
  background: linear-gradient(135deg, #ea580c, #f59e0b);
  color: #ffffff;
  border: 1px solid rgba(234, 88, 12, 0.34);
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}

:deep(.copy-rounds-trigger:hover) {
  transform: translateY(-1px);
  background: linear-gradient(135deg, #c2410c, #ea580c);
  border-color: rgba(194, 65, 12, 0.4);
}

:global(html.dark) .header-btn,
:global(html.dark) .copy-rounds-trigger {
  box-shadow: 0 10px 24px rgba(2, 6, 23, 0.34);
}

:global(html.dark) .btn-edit {
  color: #f5f3ff;
  background: linear-gradient(135deg, rgba(88, 70, 139, 0.98), rgba(51, 65, 85, 0.96));
  border-color: rgba(129, 111, 181, 0.3);
}

:global(html.dark) .btn-edit:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(109, 95, 168, 0.98), rgba(71, 85, 105, 0.98));
  border-color: rgba(167, 139, 250, 0.42);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

@media (max-width: 900px) {
  .app-header {
    padding: 8px 10px;
    gap: 6px;
  }

  .mobile-sidebar-btn,
  .mobile-tools-btn,
  .mobile-new-chat-btn,
  .mobile-only {
    display: inline-flex;
    flex-shrink: 0;
  }

  .desktop-only {
    display: none;
  }

  .header-left {
    flex-shrink: 0;
  }

  .logo {
    display: none;
  }

  .header-center {
    justify-content: flex-start;
    overflow: hidden;
  }

  .header-right {
    gap: 0;
  }

  .agent-select {
    display: inline-flex;
    flex: 1;
    width: auto;
    min-width: 0;
    max-width: none;
  }

  .agent-select :deep(.el-select__wrapper) {
    width: 100%;
    min-width: 0;
    padding-right: 24px;
  }

  .header-btn,
  .model-badge,
  .status-dot,
  .status-text {
    display: none;
  }

  .mobile-new-chat-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    min-height: 28px;
    min-width: 28px;
    padding: 0;
    white-space: nowrap;
    font-size: 12px;
    flex-shrink: 0;
    border-radius: 50%;
  }
  .mobile-new-chat-btn .mobile-btn-text {
    display: none;
  }
  .mobile-new-chat-btn .mobile-btn-icon {
    font-size: 14px;
  }

  .user-dropdown-trigger .username-text,
  .user-dropdown-trigger .dropdown-arrow {
    display: none;
  }
  .user-dropdown-trigger {
    width: 28px;
    height: 28px;
    padding: 0;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .header-right :deep(.el-button.is-circle) {
    width: 28px;
    height: 28px;
    --el-button-size: 28px;
    margin: 0;
  }

  .header-right :deep(.el-button + .el-button) {
    margin-left: 0;
  }

  :deep(.copy-rounds-trigger) {
    width: 28px;
    height: 28px;
    min-height: 28px;
    padding: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
  }
}
</style>

<style>
.agent-select-popper.el-popper {
  border-radius: 14px !important;
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 18%, var(--el-border-color-lighter)) !important;
  box-shadow:
    0 20px 48px rgba(15, 23, 42, 0.12),
    0 8px 20px rgba(15, 23, 42, 0.06) !important;
  overflow: hidden;
  padding: 6px !important;
}

.agent-select-popper .el-select-dropdown {
  max-height: 600px !important;
}

.agent-select-popper .el-select-dropdown__list {
  padding: 4px 0 !important;
}

.agent-select-popper .el-select-dropdown__item {
  border-radius: 8px;
  margin: 2px 0;
  padding: 10px 12px;
  height: auto;
  line-height: normal;
  transition: background 0.15s ease;
}

.agent-select-popper .el-select-dropdown__item.is-selected {
  background: linear-gradient(135deg, color-mix(in srgb, var(--el-color-primary) 10%, transparent), color-mix(in srgb, var(--el-color-primary) 6%, transparent));
  font-weight: 600;
}

.agent-select-popper .el-select-dropdown__item:hover {
  background: var(--el-fill-color-light);
}

html.dark .agent-select-popper.el-popper {
  border-color: rgba(148, 163, 184, 0.15) !important;
  box-shadow:
    0 24px 56px rgba(0, 0, 0, 0.4),
    0 10px 24px rgba(0, 0, 0, 0.2) !important;
}
</style>

`````

--- **end of file: frontend/src/components/layout/AppHeader.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/layout/LeftSidebar.vue** (project: lc_agent) --- 

`````vue
<template>
  <aside class="left-sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <transition name="fade">
        <div v-if="!collapsed" class="sidebar-brand-wrap">
          <span class="sidebar-brand mobile-only-brand">心有灵犀</span>
          <span class="sidebar-brand desktop-only-brand">Chats</span>
        </div>
      </transition>
      <div v-if="!collapsed" class="header-actions">
        <button class="action-btn" @click="toggleAllGroups" :title="allCollapsed ? '全部展开' : '全部折叠'">
          <span v-if="allCollapsed">⊞</span>
          <span v-else>⊟</span>
        </button>
        <button class="toggle-btn" @click="emit('toggleCollapse')" :title="collapsed ? '展开侧边栏' : '收起侧边栏'">
          <span class="toggle-icon" :class="{ flipped: collapsed }">«</span>
        </button>
      </div>
      <button v-else class="toggle-btn" @click="emit('toggleCollapse')" title="展开侧边栏">
        <span class="toggle-icon flipped">«</span>
      </button>
    </div>

    <div v-if="!collapsed" class="session-list">
      <div class="sidebar-search">
        <input
          v-model="searchQuery"
          class="sidebar-search-input"
          type="text"
          placeholder="搜索聊天标题"
        >
      </div>

      <div v-if="renderedGroups.length > 0" class="session-tree">
        <section
          v-for="group in renderedGroups"
          :key="group.agentId"
          class="agent-section"
          :class="{ 'is-active-agent': group.agentName === activeAgentName }"
        >
          <button
            type="button"
            class="agent-section-header"
            @click="toggleGroup(group.agentName)"
          >
            <span class="agent-group-arrow" :class="{ collapsed: collapsedGroups.has(group.agentName) }">▶</span>
            <span class="agent-group-name">{{ group.agentName }}</span>
            <span class="agent-card-count">{{ group.badgeText }}</span>
          </button>

          <div v-if="!collapsedGroups.has(group.agentName)" class="session-children">
            <div
              v-for="session in group.visibleSessions"
              :key="session.id"
              class="session-item"
              :class="{ 'is-active': session.id === sessionsStore.currentSessionId }"
              @click="handleSessionSelect(session.id)"
            >
              <span class="session-rail" aria-hidden="true"></span>
              <span v-if="session.is_pinned" class="session-pin-indicator">📌</span>
              <span
                v-if="chatStore.isSessionStreaming(session.id)"
                class="session-streaming-dot"
                title="正在生成中"
              />
              <span class="session-item-title">{{ session.title || '新对话' }}</span>
              <div class="session-item-meta">
                <button
                  type="button"
                  class="session-action-btn"
                  title="会话操作"
                  @click.stop="toggleSessionMenu(session.id)"
                >
                  ⋯
                </button>
                <div v-if="openMenuSessionId === session.id" class="session-menu">
                  <button type="button" @click.stop="handleRename(session.id, session.title || '新对话')">重命名</button>
                  <button type="button" @click.stop="handleTogglePinned(session)">
                    {{ session.is_pinned ? '取消置顶' : '置顶' }}
                  </button>
                  <button type="button" @click.stop="handleDelete(session.id)">删除</button>
                </div>
              </div>
            </div>

            <button
              v-if="group.hiddenCount > 0"
              type="button"
              class="show-more-btn"
              @click="showMore(group.agentId)"
            >
              <span>显示更多</span>
              <span class="show-more-hint">每次显示更多 20 条</span>
            </button>
          </div>
        </section>
      </div>

      <div v-else class="empty-state">
        <span>{{ normalizedQuery ? '没有匹配的聊天标题' : '暂无聊天' }}</span>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { useSessionsStore, type Session } from '@/stores/sessions'
import { useAgentsStore } from '@/stores/agents'
import { useChatStore } from '@/stores/chat'

const props = defineProps<{ collapsed: boolean }>()

const sessionsStore = useSessionsStore()
const agentsStore = useAgentsStore()
const chatStore = useChatStore()
const emit = defineEmits<{ newChat: []; switchSession: [id: string]; toggleCollapse: [] }>()

const DEFAULT_VISIBLE_COUNT = 5
const LOAD_MORE_COUNT = 20
const SIDEBAR_COLLAPSED_GROUPS_KEY = 'lc-agent:sidebar:collapsed-agent-groups'

const searchQuery = ref('')
const openMenuSessionId = ref<string | null>(null)
const visibleCountByAgent = ref<Record<string, number>>({})

interface SidebarGroup {
  agentId: string
  agentName: string
  badgeText: string
  visibleSessions: Session[]
  hiddenCount: number
}

function loadCollapsedGroups() {
  try {
    const raw = localStorage.getItem(SIDEBAR_COLLAPSED_GROUPS_KEY)
    const names = raw ? JSON.parse(raw) : []
    return new Set(Array.isArray(names) ? names.filter((name): name is string => typeof name === 'string') : [])
  } catch {
    return new Set<string>()
  }
}

function persistCollapsedGroups() {
  localStorage.setItem(SIDEBAR_COLLAPSED_GROUPS_KEY, JSON.stringify([...collapsedGroups.value]))
}

const collapsedGroups = ref<Set<string>>(loadCollapsedGroups())

const activeAgentName = computed(() => {
  const session = sessionsStore.sessions.find(s => s.id === sessionsStore.currentSessionId)
  return agentsStore.getAgentName(session?.agent_id || 'chat')
})

const normalizedQuery = computed(() => searchQuery.value.trim().toLowerCase())

const filteredSessions = computed(() => {
  const query = normalizedQuery.value
  if (!query) return sessionsStore.sessions.slice()
  return sessionsStore.sessions.filter(session =>
    (session.title || '新对话').toLowerCase().includes(query),
  )
})

function getVisibleCount(agentId: string) {
  return visibleCountByAgent.value[agentId] ?? DEFAULT_VISIBLE_COUNT
}

function compareSessions(a: Session, b: Session) {
  if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1

  const pinnedA = a.pinned_at ? new Date(a.pinned_at).getTime() : 0
  const pinnedB = b.pinned_at ? new Date(b.pinned_at).getTime() : 0
  if (pinnedA !== pinnedB) return pinnedB - pinnedA

  return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
}

const renderedGroups = computed<SidebarGroup[]>(() => {
  const buckets = new Map<string, Session[]>()

  for (const session of filteredSessions.value) {
    const agentId = session.agent_id || 'chat'
    const list = buckets.get(agentId) || []
    list.push(session)
    buckets.set(agentId, list)
  }

  return [...buckets.entries()]
    .map(([agentId, sessions]) => {
      const agentName = agentsStore.getAgentName(agentId)
      const sorted = sessions.slice().sort(compareSessions)
      const visibleCount = getVisibleCount(agentId)
      const totalCount = sessionsStore.sessions.filter(s => (s.agent_id || 'chat') === agentId).length
      return {
        agentId,
        agentName,
        badgeText: normalizedQuery.value ? `${sorted.length}/${totalCount}` : String(sorted.length),
        visibleSessions: sorted.slice(0, visibleCount),
        hiddenCount: Math.max(sorted.length - visibleCount, 0),
      }
    })
    .sort((a, b) => a.agentName.localeCompare(b.agentName, 'zh-CN'))
})

const allCollapsed = computed(() => {
  const groupNames = renderedGroups.value.map(group => group.agentName)
  return groupNames.length > 0 && groupNames.every(name => collapsedGroups.value.has(name))
})

watch(normalizedQuery, () => {
  visibleCountByAgent.value = {}
  openMenuSessionId.value = null
})

watch(renderedGroups, groups => {
  const groupNames = new Set(groups.map(group => group.agentName))
  const pruned = new Set([...collapsedGroups.value].filter(name => groupNames.has(name)))
  if (pruned.size !== collapsedGroups.value.size) {
    collapsedGroups.value = pruned
    persistCollapsedGroups()
  }
}, { immediate: true })

function toggleGroup(title: string) {
  const next = new Set(collapsedGroups.value)
  if (next.has(title)) {
    next.delete(title)
  } else {
    next.add(title)
  }
  collapsedGroups.value = next
  persistCollapsedGroups()
}

function toggleAllGroups() {
  const groupNames = renderedGroups.value.map(group => group.agentName)
  if (groupNames.length === 0) return

  if (allCollapsed.value) {
    collapsedGroups.value = new Set([...collapsedGroups.value].filter(name => !groupNames.includes(name)))
  } else {
    collapsedGroups.value = new Set([...collapsedGroups.value, ...groupNames])
  }
  persistCollapsedGroups()
}

function showMore(agentId: string) {
  visibleCountByAgent.value = {
    ...visibleCountByAgent.value,
    [agentId]: getVisibleCount(agentId) + LOAD_MORE_COUNT,
  }
}

function handleSessionSelect(id: string) {
  openMenuSessionId.value = null
  emit('switchSession', id)
}

function toggleSessionMenu(id: string) {
  openMenuSessionId.value = openMenuSessionId.value === id ? null : id
}

async function handleRename(id: string, title: string) {
  openMenuSessionId.value = null
  const result = await ElMessageBox.prompt('输入新的会话标题', '重命名会话', {
    inputValue: title,
    confirmButtonText: '保存',
    cancelButtonText: '取消',
  }).catch(() => null)

  if (!result) return
  const nextTitle = result.value.trim()
  if (!nextTitle) return
  await sessionsStore.updateTitle(id, nextTitle)
}

async function handleDelete(id: string) {
  openMenuSessionId.value = null
  const confirmed = await ElMessageBox.confirm('确认删除该会话吗？', '删除会话', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  }).catch(() => null)

  if (!confirmed) return
  await sessionsStore.deleteSession(id)
}

async function handleTogglePinned(session: Session) {
  openMenuSessionId.value = null
  await sessionsStore.setPinned(session.id, !session.is_pinned)
}

function handleDocumentClick(event: MouseEvent) {
  const target = event.target as HTMLElement | null
  if (!target?.closest('.session-item-meta')) {
    openMenuSessionId.value = null
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<style scoped>
.left-sidebar {
  width: 312px;
  --sidebar-agent-card-bg: color-mix(in srgb, var(--el-bg-color-overlay) 78%, var(--el-fill-color-light));
  --sidebar-agent-card-border: var(--el-border-color-lighter);
  --sidebar-agent-card-active-border: color-mix(in srgb, var(--el-color-primary) 62%, var(--el-border-color));
  --sidebar-agent-card-active-bg: color-mix(in srgb, var(--el-color-primary-light-9) 82%, var(--el-bg-color));
  --sidebar-agent-card-active-ring: color-mix(in srgb, var(--el-color-primary) 18%, transparent);
  --sidebar-agent-card-count-bg: var(--el-fill-color-light);
  --sidebar-agent-card-count-color: var(--el-text-color-secondary);
  --sidebar-session-hover-bg: color-mix(in srgb, var(--el-color-success) 16%, var(--el-bg-color-overlay));
  --sidebar-session-hover-color: var(--el-text-color-primary);
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:global(html.dark) .left-sidebar {
  --sidebar-agent-card-bg: color-mix(in srgb, var(--el-bg-color-overlay) 82%, white 4%);
  --sidebar-agent-card-border: color-mix(in srgb, var(--el-border-color) 76%, white 8%);
  --sidebar-agent-card-active-border: color-mix(in srgb, var(--el-color-primary) 72%, white 8%);
  --sidebar-agent-card-active-bg: color-mix(in srgb, var(--el-color-primary) 14%, var(--el-bg-color-overlay));
  --sidebar-agent-card-active-ring: color-mix(in srgb, var(--el-color-primary) 24%, transparent);
  --sidebar-agent-card-count-bg: color-mix(in srgb, var(--el-fill-color) 84%, white 8%);
  --sidebar-agent-card-count-color: var(--el-text-color-regular);
  --sidebar-session-hover-bg: color-mix(in srgb, var(--el-color-success) 30%, #10261d);
  --sidebar-session-hover-color: #f8fafc;
}

.left-sidebar.collapsed {
  width: 68px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--el-border-color);
}

.sidebar-brand-wrap {
  display: flex;
  align-items: center;
}

.sidebar-brand {
  font-size: 14px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  letter-spacing: 0.3px;
}

.mobile-only-brand {
  display: none;
}

.desktop-only-brand {
  display: inline;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn,
.toggle-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.15s ease;
}

.action-btn:hover,
.toggle-btn:hover {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

.toggle-icon {
  display: inline-block;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.toggle-icon.flipped {
  transform: rotate(180deg);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 8px 12px;
}

.sidebar-search {
  padding: 6px 4px 12px;
}

.sidebar-search-input {
  width: 100%;
  height: 34px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
  padding: 0 12px;
  outline: none;
}

.sidebar-search-input:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--el-color-primary) 18%, transparent);
}

.session-tree {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.agent-section {
  border: 1px solid var(--sidebar-agent-card-border);
  border-radius: 10px;
  background: var(--sidebar-agent-card-bg);
  overflow: visible;
  transition: border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
}

.agent-section.is-active-agent {
  border-color: var(--sidebar-agent-card-active-border);
  box-shadow: 0 0 0 1px var(--sidebar-agent-card-active-ring);
}

.agent-section-header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-weight: 700;
  color: var(--el-text-color-primary);
  text-align: left;
}

.agent-section-header:hover {
  background: var(--el-fill-color-lighter);
}

.agent-group-arrow {
  font-size: 9px;
  color: var(--el-text-color-secondary);
  transition: transform 0.2s ease;
  transform: rotate(90deg);
  flex-shrink: 0;
}

.agent-group-arrow.collapsed {
  transform: rotate(0deg);
}

.agent-group-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-card-count {
  font-size: 10px;
  font-weight: 600;
  color: var(--sidebar-agent-card-count-color);
  background: var(--sidebar-agent-card-count-bg);
  padding: 1px 6px;
  border-radius: 8px;
  flex-shrink: 0;
}

.session-children {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 2px;
  padding-right: 8px;
  padding-bottom: 10px;
  padding-left: 22px;
}

.session-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 7px 8px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--el-text-color-regular);
}

.session-item:hover {
  background: var(--sidebar-session-hover-bg);
  color: var(--sidebar-session-hover-color);
}

.session-item.is-active {
  background: var(--sidebar-agent-card-active-bg);
  color: var(--el-color-primary);
}

.session-rail {
  width: 8px;
  height: 1px;
  background: color-mix(in srgb, var(--el-border-color) 78%, transparent);
  flex-shrink: 0;
}

.session-pin-indicator {
  flex-shrink: 0;
  font-size: 12px;
}

.session-streaming-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--el-color-primary, #409eff);
  animation: streaming-pulse 1.2s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes streaming-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.session-item-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-item-meta {
  position: relative;
  flex-shrink: 0;
}

.session-action-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.session-action-btn:hover {
  background: color-mix(in srgb, var(--el-fill-color-light) 88%, transparent);
}

.session-menu {
  position: absolute;
  top: calc(100% - 4px);
  right: 0;
  z-index: 10;
  display: flex;
  flex-direction: column;
  min-width: 112px;
  padding: 6px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color-overlay);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
}

.session-menu button {
  border: none;
  background: transparent;
  color: var(--el-text-color-primary);
  text-align: left;
  padding: 7px 8px;
  border-radius: 6px;
  cursor: pointer;
}

.session-menu button:hover {
  background: var(--el-fill-color-light);
}

.show-more-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  margin-top: 2px;
  padding: 8px 8px 4px;
  border: none;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
}

.show-more-btn:hover {
  color: var(--el-text-color-primary);
}

.show-more-hint {
  font-size: 11px;
  opacity: 0.72;
}

.empty-state {
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 900px) {
  .left-sidebar,
  .left-sidebar.collapsed {
    width: min(86vw, 340px);
    max-width: 86vw;
    height: 100%;
  }

  .sidebar-header {
    padding: 10px 12px;
  }

  .mobile-only-brand {
    display: inline;
  }

  .desktop-only-brand {
    display: none;
  }

  .session-list {
    padding: 6px 6px 12px;
  }

  .session-tree {
    gap: 8px;
  }
}
</style>

`````

--- **end of file: frontend/src/components/layout/LeftSidebar.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/layout/RightPanel.vue** (project: lc_agent) --- 

`````vue
<template>
  <aside class="right-panel">
    <div class="right-panel-fixed">
      <template v-if="!agentsStore.isCodeAgent">
        <div class="panel-section">
          <h4>模型</h4>
          <ModelSelector
            :models="toolsStore.models"
            :current-model="toolsStore.currentModel"
            @change="toolsStore.setModel"
          />
          <div class="llm-params-controls">
            <div class="param-row">
              <div class="param-label-group">
                <span class="param-label">思考级别</span>
                <span v-if="reasoningFromPreset" class="param-source-hint">预设</span>
                <span v-else-if="hasReasoningOverride" class="param-source-hint override">覆盖</span>
              </div>
              <div class="param-control-group">
                <el-select
                  :model-value="effectiveReasoningEffort ?? 'default'"
                  size="small"
                  class="reasoning-effort-select"
                  @update:model-value="(v: string) => toolsStore.setLlmParam('reasoning_effort', v === 'default' ? null : v)"
                >
                  <el-option
                    v-for="effort in ['default', 'none', 'minimal', 'low', 'medium', 'high', 'xhigh']"
                    :key="effort"
                    :label="effort"
                    :value="effort"
                  />
                </el-select>
                <button
                  v-if="hasReasoningOverride"
                  class="param-reset-btn"
                  type="button"
                  title="清除覆盖，恢复预设/默认"
                  @click="toolsStore.setLlmParam('reasoning_effort', null)"
                >×</button>
              </div>
            </div>
            <div class="param-row param-row-slider">
              <div class="param-label-group">
                <span class="param-label">温度</span>
                <span v-if="temperatureFromPreset" class="param-source-hint">预设</span>
                <span v-else-if="hasTemperatureOverride" class="param-source-hint override">覆盖</span>
              </div>
              <div class="temperature-control">
                <el-slider
                  :model-value="effectiveTemperature"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  size="small"
                  class="temperature-slider"
                  @update:model-value="(v: number) => toolsStore.setLlmParam('temperature', v)"
                />
                <el-input-number
                  :model-value="effectiveTemperature"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  :precision="1"
                  size="small"
                  controls-position="right"
                  class="temperature-input"
                  @update:model-value="(v: number | undefined) => toolsStore.setLlmParam('temperature', v ?? null)"
                />
                <button
                  v-if="hasTemperatureOverride"
                  class="param-reset-btn"
                  type="button"
                  title="清除覆盖，恢复预设/默认"
                  @click="toolsStore.setLlmParam('temperature', null)"
                >×</button>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-section window-trim-section">
          <div class="window-trim-control">
            <h4>窗口裁剪模型</h4>
            <el-switch
              :model-value="summEnabled"
              size="small"
              @change="(val: boolean) => { summEnabled = val; updateSummarization({ enabled: val }) }"
            />
          </div>
          <el-select
            v-if="summEnabled"
            v-model="summModel"
            placeholder="默认同主模型"
            size="small"
            filterable
            clearable
            class="window-trim-select"
            @change="updateSummarization({ default_model: $event || '' })"
          >
            <el-option
              v-for="model in toolsStore.models"
              :key="model.id"
              :label="model.id"
              :value="model.id"
            />
          </el-select>
        </div>
      </template>

      <div class="panel-section markdown-theme-section">
        <div class="section-header compact-section-header">
          <h4>Markdown 风格</h4>
          <span class="theme-current">{{ currentOption.label }}</span>
        </div>
        <el-select
          v-model="markdownTheme"
          size="small"
          class="markdown-theme-select"
          @change="(value: MarkdownThemeId) => setMarkdownTheme(value)"
        >
          <el-option
            v-for="option in MARKDOWN_THEME_OPTIONS"
            :key="option.id"
            :label="option.label"
            :value="option.id"
          >
            <div class="theme-option-row">
              <span class="theme-option-dot" :style="{ background: option.accent }"></span>
              <div class="theme-option-copy">
                <span class="theme-option-name">{{ option.label }}</span>
                <span class="theme-option-desc">{{ option.description }}</span>
              </div>
            </div>
          </el-option>
        </el-select>
      </div>

      <div v-if="chatStore.todos.length > 0" class="panel-section">
        <TodoList :todos="chatStore.todos" />
      </div>
    </div>

    <div class="right-panel-scroll">
      <div v-if="agentsStore.isCodeAgent" class="panel-section code-agent-hint">
        <div class="hint-box code-agent-box">
          <span class="hint-icon">⚙️</span>
          <span class="hint-text">代码智能体</span>
          <span class="hint-sub">此智能体由代码注册，工具、MCP、Skills、提示词和模型由代码中的 graph 决定。当前面板的框架级配置不适用于它。</span>
        </div>
      </div>

      <template v-if="!agentsStore.isChatAgent && !agentsStore.isCodeAgent">
        <div class="panel-section">
          <h4>工具</h4>
          <ToolGroupPanel
            :groups="toolsStore.filteredGroups"
            @toggle="toolsStore.toggleGroup"
            @detail="(group) => openDetail('tool-group', group.description || group.id, group)"
          />
        </div>

        <div class="panel-section">
          <div class="section-header">
            <h4>MCP 服务器</h4>
            <button class="refresh-btn" type="button" :disabled="toolsStore.mcpRefreshing" @click="toolsStore.refreshMcpServers()">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                :class="{ spinning: toolsStore.mcpRefreshing }"
              >
                <path d="M21 2v6h-6" />
                <path d="M3 12a9 9 0 0 1 15.55-6.36L21 8" />
                <path d="M3 22v-6h6" />
                <path d="M21 12a9 9 0 0 1-15.55 6.36L3 16" />
              </svg>
              刷新
            </button>
          </div>
          <div v-for="server in toolsStore.filteredMcp" :key="server.name" class="mcp-item" :class="{ 'not-allowed': !server.allowed }">
            <div class="mcp-header">
              <div class="mcp-left">
                <el-switch
                  :model-value="server.enabled"
                  :disabled="!server.allowed"
                  size="small"
                  @change="toolsStore.toggleMcp(server.name)"
                />
                <span class="mcp-name">{{ server.name }}</span>
                <button class="detail-btn" type="button" @click="openDetail('mcp', server.name, server)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="16" x2="12" y2="12" />
                    <line x1="12" y1="8" x2="12.01" y2="8" />
                  </svg>
                  详情
                </button>
              </div>
              <el-tag size="small" :type="!server.allowed ? 'warning' : server.status === 'connected' ? 'success' : server.status === 'error' ? 'danger' : server.status === 'disabled' ? 'warning' : 'info'">
                {{ !server.allowed ? '未授权' : server.status === 'connected' ? '已连接' : server.status === 'error' ? '错误' : server.status === 'disabled' ? '已禁用' : '未连接' }}
              </el-tag>
            </div>
            <div v-if="server.error && server.allowed" class="mcp-error">{{ server.error }}</div>
            <div v-if="server.tools && server.tools.length && server.allowed" class="mcp-tools">
              <el-tag v-for="tool in server.tools.slice(0, 5)" :key="tool" size="small" :class="server.enabled ? 'tool-tag-enabled' : 'tool-tag-disabled'">{{ tool }}</el-tag>
              <el-tag v-if="server.tools.length > 5" size="small" :class="server.enabled ? 'tool-tag-enabled' : 'tool-tag-disabled'">+{{ server.tools.length - 5 }}</el-tag>
            </div>
          </div>
          <p v-if="!toolsStore.mcpServers.length" class="empty-hint">暂无 MCP 服务器</p>
        </div>

        <div class="panel-section">
          <h4>Skills</h4>
          <div v-for="skill in toolsStore.filteredSkills" :key="skill.name" class="skill-item" :class="{ 'not-allowed': !skill.allowed, 'skill-disabled': !skill.enabled }">
            <div class="skill-header">
              <el-switch
                :model-value="skill.enabled"
                :disabled="!skill.allowed"
                size="small"
                @change="toolsStore.toggleSkill(skill.name)"
              />
              <span class="skill-name" :class="{ dimmed: !skill.enabled }">{{ skill.name }}</span>
              <button class="detail-btn" type="button" @click="openDetail('skill', skill.name, skill)">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
                详情
              </button>
            </div>
            <span class="skill-desc">{{ skill.description }}</span>
          </div>
          <p v-if="!toolsStore.skills.length" class="empty-hint">暂无 Skills</p>
        </div>

        <div class="panel-section">
          <PermissionsPanel />
        </div>
      </template>

      <div v-if="agentsStore.isChatAgent" class="panel-section chat-only-hint">
        <div class="hint-box">
          <span class="hint-icon">💬</span>
          <span class="hint-text">Chat 模式：纯对话，无工具</span>
          <span class="hint-sub">切换至 Empty 或 Power 智能体以启用工具</span>
        </div>
      </div>

      <div v-if="chatStore.threadId" class="panel-section status-section">
        <h4>会话</h4>
        <div class="status-item">
          <span>Thread:</span>
          <code>{{ chatStore.threadId.slice(0, 8) }}...</code>
        </div>
      </div>
    </div>

    <DetailModal
      v-model:visible="detailModal.visible"
      :title="detailModal.title"
      :mode="detailModal.mode"
      :data="detailModal.data"
    />
  </aside>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { useToolsStore } from '@/stores/tools'
import { api } from '@/api/http'
import { useChatStore } from '@/stores/chat'
import { useAgentsStore } from '@/stores/agents'
import { useMarkdownTheme, MARKDOWN_THEME_OPTIONS, type MarkdownThemeId } from '@/composables/useMarkdownTheme'
import ModelSelector from '@/components/panels/ModelSelector.vue'
import ToolGroupPanel from '@/components/panels/ToolGroupPanel.vue'
import DetailModal from '@/components/panels/DetailModal.vue'
import TodoList from '@/components/panels/TodoList.vue'
import PermissionsPanel from '@/components/settings/PermissionsPanel.vue'

const toolsStore = useToolsStore()
const chatStore = useChatStore()
const agentsStore = useAgentsStore()

const presetLlmParams = computed(() => agentsStore.currentAgent?.llm_params ?? null)

const effectiveTemperature = computed(() =>
  toolsStore.llmParams?.temperature
    ?? presetLlmParams.value?.temperature
    ?? 0.7
)
const effectiveReasoningEffort = computed(() =>
  toolsStore.llmParams?.reasoning_effort
    ?? presetLlmParams.value?.reasoning_effort
    ?? null
)
const hasTemperatureOverride = computed(() => toolsStore.llmParams?.temperature !== undefined)
const hasReasoningOverride = computed(() => toolsStore.llmParams?.reasoning_effort !== undefined)
const temperatureFromPreset = computed(() =>
  !hasTemperatureOverride.value && presetLlmParams.value?.temperature !== undefined
)
const reasoningFromPreset = computed(() =>
  !hasReasoningOverride.value && presetLlmParams.value?.reasoning_effort !== undefined
)
const { markdownTheme, currentOption, setMarkdownTheme } = useMarkdownTheme()

const summEnabled = ref(true)
const summModel = ref('')

onMounted(async () => {
  try {
    const conf = await api.getSummarization()
    summEnabled.value = conf.enabled
    summModel.value = conf.default_model || ''
  } catch { /* ignore */ }
})

async function updateSummarization(data: { enabled?: boolean; default_model?: string }) {
  try {
    const res = await api.updateSummarization(data)
    summEnabled.value = res.enabled
    summModel.value = res.default_model || ''
  } catch { /* ignore */ }
}

const detailModal = reactive<{
  visible: boolean
  mode: 'tool-group' | 'mcp' | 'skill'
  title: string
  data: any
}>({
  visible: false,
  mode: 'tool-group',
  title: '',
  data: null,
})

async function openDetail(mode: 'tool-group' | 'mcp' | 'skill', title: string, data: any) {
  detailModal.mode = mode
  detailModal.title = title
  if (mode === 'skill' && data?.name && !data.body) {
    try {
      const detail = await api.getSkillDetail(data.name)
      detailModal.data = { ...data, ...detail }
    } catch {
      detailModal.data = data
    }
  } else {
    detailModal.data = data
  }
  detailModal.visible = true
}
</script>

<style scoped>
.right-panel {
  width: 350px;
  background: var(--el-bg-color);
  border-left: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.right-panel-fixed {
  flex-shrink: 0;
  padding: 16px 16px 0;
}

.right-panel-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 16px;
}

.panel-section {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
}

.markdown-theme-section {
  background: linear-gradient(180deg, color-mix(in srgb, var(--el-fill-color-light) 88%, var(--el-color-primary) 4%), var(--el-fill-color-light));
}

.window-trim-section,
.markdown-theme-section {
  margin-bottom: 14px;
}

.llm-params-controls {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.param-row-slider {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.param-label-group {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.param-label {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.param-source-hint {
  font-size: 10px;
  padding: 0 4px;
  border-radius: 3px;
  background: var(--el-fill-color);
  color: var(--el-text-color-placeholder);
  border: 1px solid var(--el-border-color-lighter);
  white-space: nowrap;
}

.param-source-hint.override {
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-7);
}

.param-control-group {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.reasoning-effort-select {
  width: 100%;
}

.param-reset-btn {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border: 1px solid var(--el-border-color);
  border-radius: 50%;
  background: var(--el-fill-color);
  color: var(--el-text-color-secondary);
  font-size: 11px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: all 0.15s ease;
}

.param-reset-btn:hover {
  background: var(--el-color-danger-light-8);
  border-color: var(--el-color-danger-light-5);
  color: var(--el-color-danger);
}

.temperature-control {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.temperature-slider {
  flex: 1;
}

.temperature-input {
  width: 68px;
  flex-shrink: 0;
}

.window-trim-control {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.window-trim-select {
  width: 100%;
}

.compact-section-header {
  margin-bottom: 8px;
  padding-bottom: 0;
  border-bottom: none;
}

.theme-current {
  max-width: 132px;
  overflow: hidden;
  color: var(--el-text-color-secondary);
  font-size: 11px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.markdown-theme-select {
  width: 100%;
}

.theme-option-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.theme-option-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  box-shadow: 0 0 0 3px color-mix(in srgb, currentColor 12%, transparent);
  flex-shrink: 0;
}

.theme-option-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.25;
}

.theme-option-name {
  color: var(--el-text-color-primary);
  font-size: 12px;
  font-weight: 700;
}

.theme-option-desc {
  overflow: hidden;
  color: var(--el-text-color-secondary);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.panel-section h4 {
  margin: 0;
  font-size: 11px;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.7px;
  font-weight: 600;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--el-border-color);
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border: 1px solid var(--el-border-color);
  border-radius: 10px;
  background: var(--el-bg-color);
  color: var(--el-text-color-secondary);
  font-size: 11px;
  line-height: 1;
  cursor: pointer;
  transition: all 0.18s ease;
}

.refresh-btn:hover:not(:disabled) {
  border-color: var(--el-color-primary-light-5);
  color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary) 6%, var(--el-bg-color));
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinning {
  animation: spin 0.9s linear infinite;
}

.empty-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin: 4px 0;
  opacity: 0.6;
}

.status-section .status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
}

.status-section code {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.mcp-item {
  margin-bottom: 8px;
  padding: 8px 10px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  transition: border-color 0.15s ease;
}

.mcp-item:hover {
  border-color: var(--el-color-primary-light-5);
}

.mcp-item:has(.el-switch:not(.is-checked)) {
  opacity: 0.75;
  border: 1px dashed var(--el-color-warning-light-5) !important;
  background: var(--el-color-warning-light-9) !important;
}

.mcp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mcp-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mcp-error {
  font-size: 11px;
  color: var(--el-color-danger);
  margin-top: 4px;
  word-break: break-all;
  opacity: 0.8;
}

.mcp-name {
  font-size: 13px;
  font-weight: 500;
}

.mcp-tools {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.skill-item {
  padding: 8px 10px;
  margin-bottom: 4px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  transition: border-color 0.15s ease;
}

.skill-item:hover {
  border-color: var(--el-color-primary-light-5);
}

.skill-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.detail-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 10px;
  background: color-mix(in srgb, var(--el-color-primary) 8%, transparent);
  font-size: 11px;
  color: var(--el-color-primary);
  cursor: pointer;
  line-height: 1;
  flex-shrink: 0;
  transition: all 0.18s ease;
  white-space: nowrap;
}

.detail-btn:hover {
  background: color-mix(in srgb, var(--el-color-primary) 15%, transparent);
  border-color: var(--el-color-primary-light-3);
  box-shadow: 0 1px 4px color-mix(in srgb, var(--el-color-primary) 12%, transparent);
}

.detail-btn:active {
  transform: scale(0.95);
  background: color-mix(in srgb, var(--el-color-primary) 20%, transparent);
}

.skill-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-color-primary);
  transition: color 0.15s ease, opacity 0.15s ease;
}

.code-agent-hint .hint-sub {
  line-height: 1.45;
}

.code-agent-box {
  border: 1px solid var(--el-color-primary-light-7);
  background: color-mix(in srgb, var(--el-color-primary) 7%, var(--el-fill-color-light));
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>

`````

--- **end of file: frontend/src/components/layout/RightPanel.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/panels/DetailModal.vue** (project: lc_agent) --- 

`````vue
<template>
  <teleport to="body">
    <div v-if="visible" class="detail-modal-backdrop" @click="close">
      <div class="detail-modal" role="dialog" aria-modal="true" @click.stop>
        <div class="detail-modal-header">
          <div class="detail-modal-title-wrap">
            <span class="detail-modal-kicker">{{ modeKicker }}</span>
            <span class="detail-modal-title">{{ title }}</span>
          </div>
          <button class="detail-modal-close" aria-label="关闭" @click="close">✕</button>
        </div>
        <div class="detail-modal-toolbar">
          <input
            v-model="searchQuery"
            class="detail-search-input"
            type="text"
            placeholder="搜索关键字..."
            @keydown.enter.prevent="jumpToNextMatch"
          />
          <div class="detail-search-actions">
            <span v-if="searchQuery" class="detail-search-count">{{ activeMatchLabel }}</span>
            <button class="detail-search-btn" :disabled="!matchCount" @click="jumpToPrevMatch">↑</button>
            <button class="detail-search-btn" :disabled="!matchCount" @click="jumpToNextMatch">↓</button>
          </div>
        </div>
        <div class="detail-modal-content">
          <div ref="modalBodyRef" class="detail-modal-body" v-html="displayHtml" />
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps<{
  visible: boolean
  title: string
  mode: 'tool-group' | 'mcp' | 'skill'
  data: any
}>()

const emit = defineEmits<{ 'update:visible': [value: boolean] }>()

const searchQuery = ref('')
const activeMatchIndex = ref(0)
const modalBodyRef = ref<HTMLElement | null>(null)

const modeKicker = computed(() => {
  switch (props.mode) {
    case 'tool-group': return '工具组'
    case 'mcp': return 'MCP 服务器'
    case 'skill': return 'Skill'
    default: return '详情'
  }
})

function close() {
  emit('update:visible', false)
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function highlightText(text: string, query: string): string {
  const escaped = escapeHtml(text)
  if (!query) return escaped
  const highlighted = text.replace(
    new RegExp(escapeRegExp(query), 'gi'),
    (match) => `@@HIT_START@@${match}@@HIT_END@@`,
  )
  return escapeHtml(highlighted)
    .replace(/@@HIT_START@@/g, '<mark class="detail-search-hit">')
    .replace(/@@HIT_END@@/g, '</mark>')
}

function buildToolGroupHtml(data: any, query: string): string {
  let html = ''
  if (data.description) {
    html += `<div class="detail-section-desc">${highlightText(data.description, query)}</div>`
  }
  for (const tool of data.tools || []) {
    html += '<div class="detail-tool-item">'
    html += `<div class="detail-tool-name">${highlightText(tool.name, query)}</div>`
    if (tool.description) {
      html += `<div class="detail-tool-desc">${highlightText(tool.description, query)}</div>`
    }
    if (tool.input_schema) {
      const schemaJson = JSON.stringify(tool.input_schema, null, 2)
      html += `<details class="detail-schema"><summary>参数 Schema</summary><pre class="detail-schema-pre">${highlightText(schemaJson, query)}</pre></details>`
    }
    html += '</div>'
  }
  return html
}

function buildMcpHtml(data: any, query: string): string {
  let html = '<div class="detail-info-grid">'
  html += `<div class="detail-info-row"><span class="detail-info-label">类型</span><span>${highlightText(data.type || '', query)}</span></div>`
  if (data.command) {
    html += `<div class="detail-info-row"><span class="detail-info-label">命令</span><span class="detail-mono">${highlightText(data.command, query)}</span></div>`
  }
  if (data.url) {
    html += `<div class="detail-info-row"><span class="detail-info-label">URL</span><span class="detail-mono">${highlightText(data.url, query)}</span></div>`
  }
  html += `<div class="detail-info-row"><span class="detail-info-label">状态</span><span>${highlightText(data.status || '', query)}</span></div>`
  if (data.error) {
    html += `<div class="detail-info-row detail-error"><span class="detail-info-label">错误</span><span>${highlightText(data.error, query)}</span></div>`
  }
  html += '</div>'

  const schemas = data.tool_schemas || []
  if (schemas.length > 0) {
    html += '<div class="detail-tools-section"><div class="detail-tools-heading">工具列表</div>'
    for (const tool of schemas) {
      html += '<div class="detail-tool-item">'
      html += `<div class="detail-tool-name">${highlightText(tool.name, query)}</div>`
      if (tool.description) {
        html += `<div class="detail-tool-desc">${highlightText(tool.description, query)}</div>`
      }
      if (tool.input_schema) {
        const schemaJson = JSON.stringify(tool.input_schema, null, 2)
        html += `<details class="detail-schema"><summary>参数 Schema</summary><pre class="detail-schema-pre">${highlightText(schemaJson, query)}</pre></details>`
      }
      html += '</div>'
    }
    html += '</div>'
  } else if (data.tools?.length) {
    html += '<div class="detail-tools-section"><div class="detail-tools-heading">工具列表</div><div class="detail-tool-tags">'
    for (const name of data.tools) {
      html += `<span class="detail-tool-tag">${highlightText(name, query)}</span>`
    }
    html += '</div></div>'
  }
  return html
}

function buildSkillHtml(data: any, query: string): string {
  let html = ''
  if (data.description) {
    html += `<div class="detail-section-desc">${highlightText(data.description, query)}</div>`
  }
  const body = data.body || data.content
  if (body) {
    const mdHtml = renderMarkdown(body)
    if (query) {
      const highlighted = body.replace(
        new RegExp(escapeRegExp(query), 'gi'),
        (match: string) => `@@HIT_START@@${match}@@HIT_END@@`,
      )
      const rendered = renderMarkdown(highlighted)
        .replace(/@@HIT_START@@/g, '<mark class="detail-search-hit">')
        .replace(/@@HIT_END@@/g, '</mark>')
      html += `<div class="detail-skill-content markdown-body">${rendered}</div>`
    } else {
      html += `<div class="detail-skill-content markdown-body">${mdHtml}</div>`
    }
  } else {
    html += `<div class="detail-section-desc" style="color:var(--el-text-color-secondary)">暂无详细内容</div>`
  }
  return html
}

const baseHtml = computed(() => {
  if (!props.data) return ''
  const query = searchQuery.value.trim()
  switch (props.mode) {
    case 'tool-group': return buildToolGroupHtml(props.data, query)
    case 'mcp': return buildMcpHtml(props.data, query)
    case 'skill': return buildSkillHtml(props.data, query)
    default: return ''
  }
})

const displayHtml = computed(() => baseHtml.value)

const searchableText = computed(() => {
  if (!props.data) return ''
  switch (props.mode) {
    case 'tool-group': {
      const parts = [props.data.description || '']
      for (const tool of props.data.tools || []) {
        parts.push(tool.name, tool.description || '')
        if (tool.input_schema) parts.push(JSON.stringify(tool.input_schema))
      }
      return parts.join('\n')
    }
    case 'mcp': {
      const parts = [props.data.type || '', props.data.command || '', props.data.url || '', props.data.status || '', props.data.error || '']
      for (const tool of props.data.tool_schemas || []) {
        parts.push(tool.name, tool.description || '')
        if (tool.input_schema) parts.push(JSON.stringify(tool.input_schema))
      }
      for (const name of props.data.tools || []) parts.push(name)
      return parts.join('\n')
    }
    case 'skill': {
      return [props.data.description || '', props.data.body || ''].join('\n')
    }
    default:
      return ''
  }
})

const matchCount = computed(() => {
  const query = searchQuery.value.trim()
  if (!query) return 0
  const matches = searchableText.value.match(new RegExp(escapeRegExp(query), 'gi'))
  return matches?.length || 0
})

const activeMatchLabel = computed(() => {
  if (!matchCount.value) return '0/0'
  return `${activeMatchIndex.value + 1}/${matchCount.value}`
})

async function syncSearchHighlights() {
  await nextTick()
  const container = modalBodyRef.value
  if (!container) return
  const hits = Array.from(container.querySelectorAll('mark.detail-search-hit')) as HTMLElement[]
  hits.forEach((hit, index) => {
    hit.classList.toggle('is-active', index === activeMatchIndex.value)
  })
  if (hits.length > 0) {
    hits[activeMatchIndex.value]?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }
}

function jumpToNextMatch() {
  if (!matchCount.value) return
  activeMatchIndex.value = (activeMatchIndex.value + 1) % matchCount.value
}

function jumpToPrevMatch() {
  if (!matchCount.value) return
  activeMatchIndex.value = (activeMatchIndex.value - 1 + matchCount.value) % matchCount.value
}

watch(searchQuery, () => {
  activeMatchIndex.value = 0
  syncSearchHighlights()
})

watch(activeMatchIndex, () => {
  syncSearchHighlights()
})

watch(() => props.visible, (visible) => {
  if (!visible) {
    searchQuery.value = ''
    activeMatchIndex.value = 0
    return
  }
  syncSearchHighlights()
})

watch(baseHtml, () => {
  syncSearchHighlights()
})
</script>

<style scoped>
.detail-modal-backdrop {
  position: fixed;
  inset: 0;
  background: color-mix(in srgb, var(--el-bg-color-page) 70%, transparent);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.detail-modal {
  width: min(900px, calc(100vw - 80px));
  max-height: min(80vh, 760px);
  min-height: 0;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 16px 48px color-mix(in srgb, var(--el-bg-color-page) 50%, transparent);
}

.detail-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color);
  gap: 12px;
  flex: 0 0 auto;
}

.detail-modal-title-wrap {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-modal-kicker {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.detail-modal-title {
  min-width: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-modal-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 16px;
  cursor: pointer;
  flex-shrink: 0;
}

.detail-modal-close:hover {
  background: var(--el-fill-color);
  color: var(--el-text-color-primary);
}

.detail-modal-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: color-mix(in srgb, var(--el-fill-color-light) 78%, transparent);
}

.detail-search-input {
  flex: 1 1 auto;
  min-width: 0;
  height: 34px;
  padding: 0 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  outline: none;
}

.detail-search-input:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 14%, transparent);
}

.detail-search-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.detail-search-count {
  min-width: 42px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: right;
}

.detail-search-btn {
  width: 30px;
  height: 30px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
}

.detail-search-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.detail-modal-content {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}

.detail-modal-body {
  min-height: 100%;
  padding: 16px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--el-text-color-regular);
}

.detail-modal-body :deep(.detail-section-desc) {
  margin-bottom: 12px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
}

.detail-modal-body :deep(.detail-tool-item) {
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.detail-modal-body :deep(.detail-tool-item:last-child) {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.detail-modal-body :deep(.detail-tool-name) {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 700;
  color: var(--el-color-primary);
  margin-bottom: 4px;
}

.detail-modal-body :deep(.detail-tool-desc) {
  font-size: 12px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  margin-bottom: 6px;
}

.detail-modal-body :deep(.detail-schema) {
  margin-top: 6px;
}

.detail-modal-body :deep(.detail-schema summary) {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  user-select: none;
}

.detail-modal-body :deep(.detail-schema-pre) {
  margin: 6px 0 0;
  padding: 10px 12px;
  background: var(--el-fill-color);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.detail-modal-body :deep(.detail-info-grid) {
  margin-bottom: 16px;
}

.detail-modal-body :deep(.detail-info-row) {
  display: flex;
  gap: 10px;
  padding: 4px 0;
  font-size: 12px;
  line-height: 1.5;
}

.detail-modal-body :deep(.detail-info-label) {
  flex-shrink: 0;
  min-width: 48px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

.detail-modal-body :deep(.detail-mono) {
  font-family: 'JetBrains Mono', monospace;
  word-break: break-all;
}

.detail-modal-body :deep(.detail-error) {
  color: var(--el-color-danger);
}

.detail-modal-body :deep(.detail-tools-section) {
  margin-top: 8px;
}

.detail-modal-body :deep(.detail-tools-heading) {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.detail-modal-body :deep(.detail-tool-tags) {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.detail-modal-body :deep(.detail-tool-tag) {
  padding: 2px 8px;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  background: var(--el-fill-color);
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
}

.detail-modal-body :deep(.detail-file-path) {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  margin-bottom: 10px;
  font-family: 'JetBrains Mono', monospace;
  word-break: break-all;
}

.detail-modal-body :deep(.detail-skill-content) {
  margin-top: 8px;
}

.detail-modal-body :deep(.detail-search-hit) {
  background: rgba(250, 204, 21, 0.35);
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
}

.detail-modal-body :deep(.detail-search-hit.is-active) {
  background: rgba(245, 158, 11, 0.78);
}

@media (max-width: 520px) {
  .detail-modal-backdrop {
    align-items: stretch;
    justify-content: stretch;
    padding: max(8px, env(safe-area-inset-top)) max(8px, env(safe-area-inset-right)) max(8px, env(safe-area-inset-bottom)) max(8px, env(safe-area-inset-left));
    background: color-mix(in srgb, var(--el-bg-color-page) 88%, transparent);
  }

  .detail-modal {
    width: 100%;
    max-height: none;
    height: 100%;
    border-radius: 12px;
    min-width: 0;
  }

  .detail-modal-header {
    padding: 10px 10px 9px;
    gap: 8px;
  }

  .detail-modal-kicker {
    display: none;
  }

  .detail-modal-toolbar {
    padding: 8px 10px;
    flex-wrap: wrap;
  }

  .detail-search-input {
    width: 100%;
    height: 36px;
  }

  .detail-search-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .detail-search-count {
    margin-right: auto;
    text-align: left;
  }

  .detail-modal-body {
    padding: 12px 10px 18px;
    font-size: 12px;
  }
}
</style>

`````

--- **end of file: frontend/src/components/panels/DetailModal.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/panels/ModelSelector.vue** (project: lc_agent) --- 

`````vue
<template>
  <div class="model-selector">
    <el-select
      :model-value="currentModel"
      placeholder="选择模型"
      size="small"
      filterable
      style="width: 100%"
      @change="$emit('change', $event)"
    >
      <el-option
        v-for="model in models"
        :key="model.id"
        :label="model.id"
        :value="model.id"
      >
        <span>{{ model.id }}</span>
        <span style="float:right; color:var(--el-text-color-secondary); font-size:11px">
          {{ model.provider }}
        </span>
      </el-option>
    </el-select>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  models: { id: string; provider: string; context_limit: number }[]
  currentModel: string
}>()
defineEmits<{ change: [modelId: string] }>()
</script>

<style scoped>
.model-selector {
  margin-bottom: 8px;
}
</style>

`````

--- **end of file: frontend/src/components/panels/ModelSelector.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/panels/TodoList.vue** (project: lc_agent) --- 

`````vue
<template>
  <div v-if="todos.length > 0" class="todo-panel">
    <div class="todo-header">
      <span class="todo-title">任务进度</span>
      <span class="todo-counter">{{ completed }}/{{ todos.length }}</span>
    </div>

    <div class="todo-progress-bar">
      <div class="todo-progress-fill" :style="{ width: percentage + '%' }" />
    </div>

    <ul class="todo-list">
      <li
        v-for="(todo, idx) in todos"
        :key="idx"
        class="todo-item"
        :class="'todo-' + todo.status"
      >
        <span class="todo-icon">{{ statusIcon(todo.status) }}</span>
        <span class="todo-content">{{ todo.content }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TodoItem } from '@/stores/chat'

const props = defineProps<{ todos: TodoItem[] }>()

const completed = computed(() => props.todos.filter(t => t.status === 'completed').length)
const percentage = computed(() =>
  props.todos.length ? Math.round((completed.value / props.todos.length) * 100) : 0,
)

function statusIcon(status: string) {
  switch (status) {
    case 'completed': return '✓'
    case 'in_progress': return '◉'
    default: return '○'
  }
}
</script>

<style scoped>
.todo-panel {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 12px;
  background: var(--el-bg-color);
}

.todo-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.todo-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.todo-counter {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.todo-progress-bar {
  height: 4px;
  border-radius: 2px;
  background: var(--el-fill-color-light);
  margin-bottom: 10px;
  overflow: hidden;
}

.todo-progress-fill {
  height: 100%;
  border-radius: 2px;
  background: var(--el-color-success);
  transition: width 0.4s ease;
}

.todo-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.todo-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.4;
  border: 1px solid transparent;
}

.todo-icon {
  flex-shrink: 0;
  width: 16px;
  text-align: center;
  margin-top: 1px;
}

.todo-content {
  flex: 1;
  word-break: break-word;
}

.todo-pending {
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-secondary);
}
.todo-pending .todo-icon {
  color: var(--el-text-color-placeholder);
}

.todo-in_progress {
  background: var(--el-color-warning-light-9);
  border-color: var(--el-color-warning-light-7);
  color: var(--el-color-warning-dark-2);
}
.todo-in_progress .todo-icon {
  color: var(--el-color-warning);
  animation: pulse 1.5s ease-in-out infinite;
}

.todo-completed {
  background: var(--el-color-success-light-9);
  border-color: var(--el-color-success-light-7);
  color: var(--el-color-success-dark-2);
}
.todo-completed .todo-content {
  text-decoration: line-through;
  opacity: 0.7;
}
.todo-completed .todo-icon {
  color: var(--el-color-success);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>

`````

--- **end of file: frontend/src/components/panels/TodoList.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/panels/ToolGroupPanel.vue** (project: lc_agent) --- 

`````vue
<template>
  <div class="tool-group-panel">
    <div v-for="group in groups" :key="group.id" class="group-item" :class="{ 'not-allowed': !(group as any).allowed && (group as any).allowed !== undefined }">
      <div class="group-header">
        <span class="group-name">{{ group.description || group.id }}</span>
        <div class="group-actions">
          <button class="detail-btn" type="button" @click="$emit('detail', group)">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            详情
          </button>
          <el-switch
            :model-value="group.enabled"
            :disabled="(group as any).allowed === false"
            size="small"
            @change="$emit('toggle', group.id)"
          />
        </div>
      </div>
      <div class="group-tools">
        <el-tag
          v-for="tool in group.tools"
          :key="tool.name"
          size="small"
          :class="group.enabled ? 'tool-tag-enabled' : 'tool-tag-disabled'"
        >
          {{ tool.name.split('__').pop() }}
        </el-tag>
      </div>
    </div>
    <p v-if="!groups.length" class="empty">暂无工具</p>
  </div>
</template>

<script setup lang="ts">
import type { ToolGroup } from '@/stores/tools'

defineProps<{ groups: ToolGroup[] }>()
defineEmits<{ toggle: [groupId: string]; detail: [group: ToolGroup] }>()
</script>

<style scoped>
.group-item {
  margin-bottom: 8px;
  padding: 10px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.group-item:hover {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-fill-color);
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  gap: 8px;
}

.group-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.detail-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 10px;
  background: color-mix(in srgb, var(--el-color-primary) 8%, transparent);
  font-size: 11px;
  color: var(--el-color-primary);
  cursor: pointer;
  line-height: 1;
  flex-shrink: 0;
  transition: all 0.18s ease;
  white-space: nowrap;
}

.detail-btn:hover {
  background: color-mix(in srgb, var(--el-color-primary) 15%, transparent);
  border-color: var(--el-color-primary-light-3);
  box-shadow: 0 1px 4px color-mix(in srgb, var(--el-color-primary) 12%, transparent);
}

.detail-btn:active {
  transform: scale(0.95);
  background: color-mix(in srgb, var(--el-color-primary) 20%, transparent);
}

.group-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.group-tools {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.empty {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  opacity: 0.6;
}

.not-allowed {
  opacity: 0.4;
  border-style: dashed;
  border-color: var(--el-border-color) !important;
}
</style>

`````

--- **end of file: frontend/src/components/panels/ToolGroupPanel.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/components/settings/PermissionsPanel.vue** (project: lc_agent) --- 

`````vue
<template>
  <div class="permissions-panel">
    <div class="panel-header">
      <h3>工具权限白名单</h3>
      <el-button link type="primary" @click="dialogVisible = true">
        详情（{{ allowlist.length }}）
      </el-button>
    </div>
    <p class="desc">白名单中的工具将跳过人工审批，自动执行。</p>

    <div class="allowlist">
      <el-tag
        v-for="tool in allowlist"
        :key="tool"
        class="tool-tag"
      >
        {{ tool }}
      </el-tag>
      <el-tag v-if="allowlist.length === 0" type="info">（空 — 所有工具需要审批）</el-tag>
    </div>

    <el-dialog v-model="dialogVisible" title="工具权限白名单详情" width="600px">
      <el-input
        v-model="searchQuery"
        placeholder="搜索已添加的工具..."
        clearable
        class="dialog-search"
      />
      <el-table :data="filteredTableData" style="width: 100%" max-height="300">
        <el-table-column prop="name" label="工具名称" />
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button link type="danger" @click="handleRemove(row.name)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="dialog-add-row">
        <el-input
          v-model="newTool"
          placeholder="输入工具名添加到白名单"
          @keyup.enter="handleAdd"
        />
        <el-button type="primary" :disabled="!newTool.trim()" @click="handleAdd">添加</el-button>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button v-if="allowlist.length > 0" type="danger" plain @click="handleClearAll">清空全部</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { getPermissions, allowTool, removeTool, setPermissions } from '@/api/permissions'
import { useChatStore } from '@/stores/chat'
import { ElMessage } from 'element-plus'

const allowlist = ref<string[]>([])
const newTool = ref('')
const dialogVisible = ref(false)
const searchQuery = ref('')
const chatStore = useChatStore()

const tableData = computed(() => allowlist.value.map(name => ({ name })))
const filteredTableData = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return tableData.value
  return tableData.value.filter(row => row.name.toLowerCase().includes(q))
})

async function fetchList() {
  try {
    const data = await getPermissions()
    allowlist.value = data.tool_allowlist
  } catch (e) {
    console.error('Failed to load permissions:', e)
  }
}

onMounted(fetchList)

watch(() => chatStore.isStreaming, (streaming, prev) => {
  if (prev && !streaming) {
    fetchList()
  }
})

async function handleAdd() {
  const name = newTool.value.trim()
  if (!name) return
  try {
    const data = await allowTool(name)
    allowlist.value = data.tool_allowlist
    newTool.value = ''
    ElMessage.success(`已添加 ${name} 到白名单`)
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function handleRemove(name: string) {
  try {
    const data = await removeTool(name)
    allowlist.value = data.tool_allowlist
    ElMessage.info(`已从白名单移除 ${name}`)
  } catch (e) {
    ElMessage.error('移除失败')
  }
}

async function handleClearAll() {
  try {
    const data = await setPermissions([])
    allowlist.value = data.tool_allowlist
    ElMessage.warning('已清空全部白名单')
  } catch (e) {
    ElMessage.error('清空失败')
  }
}
</script>

<style scoped>
.permissions-panel {
  padding: 16px 0;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.panel-header h3 {
  margin: 0;
}
.desc {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin-bottom: 16px;
}
.allowlist {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  min-height: 32px;
}
.tool-tag {
  font-family: 'JetBrains Mono', monospace;
}
.dialog-search {
  margin-bottom: 12px;
}
.dialog-add-row {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}
</style>

`````

--- **end of file: frontend/src/components/settings/PermissionsPanel.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/composables/useMarkdownTheme.ts** (project: lc_agent) --- 

`````typescript
import { computed, readonly, ref, watch } from 'vue'

export type MarkdownThemeId = 'github' | 'notion' | 'aurora' | 'neon' | 'obsidian' | 'paper' | 'lime' | 'sky' | 'candy' | 'solar'

export interface MarkdownThemeOption {
  id: MarkdownThemeId
  label: string
  description: string
  accent: string
}

export const MARKDOWN_THEME_OPTIONS: MarkdownThemeOption[] = [
  { id: 'github', label: 'Arctic Blue', description: '冰蓝银白的冷调高级风', accent: '#38bdf8' },
  { id: 'notion', label: 'Cyber Mint', description: '薄荷青绿的玻璃科技风', accent: '#2dd4bf' },
  { id: 'aurora', label: 'Aurora Blast', description: '亮紫电蓝的极光炫彩风', accent: '#a855f7' },
  { id: 'neon', label: 'Neon Future', description: '高亮霓虹科技演示风', accent: '#22d3ee' },
  { id: 'obsidian', label: 'Sunset Chrome', description: '橙红玫瑰金的暖色金属风', accent: '#fb7185' },
  { id: 'paper', label: 'Paper Luxe', description: '高级纸张阅读器风', accent: '#b7791f' },
  { id: 'lime', label: 'Lime Surge', description: '电光青柠的能量科技风', accent: '#a3e635' },
  { id: 'sky', label: 'Prism White', description: '银白棱镜的高亮彩光风', accent: '#c4b5fd' },
  { id: 'candy', label: 'Lava Pulse', description: '黑红熔岩的高能冲击风', accent: '#ef4444' },
  { id: 'solar', label: 'Solar Flare', description: '太阳耀斑的亮黄橙金风', accent: '#facc15' },
]

const STORAGE_KEY = 'lc-agent:markdown-theme'
const DEFAULT_THEME: MarkdownThemeId = 'aurora'
const validThemeIds = new Set<MarkdownThemeId>(MARKDOWN_THEME_OPTIONS.map(option => option.id))
const markdownTheme = ref<MarkdownThemeId>(loadInitialTheme())

function isMarkdownThemeId(value: string | null): value is MarkdownThemeId {
  return Boolean(value && validThemeIds.has(value as MarkdownThemeId))
}

function loadInitialTheme(): MarkdownThemeId {
  if (typeof window === 'undefined') return DEFAULT_THEME
  const stored = window.localStorage.getItem(STORAGE_KEY)
  return isMarkdownThemeId(stored) ? stored : DEFAULT_THEME
}

function applyMarkdownTheme(theme: MarkdownThemeId) {
  if (typeof document === 'undefined') return
  document.documentElement.dataset.mdTheme = theme
}

export function useMarkdownTheme() {
  const currentOption = computed(() => (
    MARKDOWN_THEME_OPTIONS.find(option => option.id === markdownTheme.value) || MARKDOWN_THEME_OPTIONS[0]
  ))

  function setMarkdownTheme(theme: MarkdownThemeId) {
    if (!validThemeIds.has(theme)) return
    markdownTheme.value = theme
  }

  watch(markdownTheme, theme => {
    applyMarkdownTheme(theme)
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, theme)
    }
  }, { immediate: true })

  return {
    markdownTheme,
    markdownThemeOptions: readonly(MARKDOWN_THEME_OPTIONS),
    currentOption,
    setMarkdownTheme,
  }
}

`````

--- **end of file: frontend/src/composables/useMarkdownTheme.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/composables/useTheme.ts** (project: lc_agent) --- 

`````typescript
import { useDark, useToggle } from '@vueuse/core'

export function useTheme() {
  const isDark = useDark({
    selector: 'html',
    attribute: 'class',
    valueDark: 'dark',
    valueLight: '',
  })
  const toggleDark = useToggle(isDark)

  return { isDark, toggleDark }
}

`````

--- **end of file: frontend/src/composables/useTheme.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/router/index.ts** (project: lc_agent) --- 

`````typescript
import { createRouter, createWebHashHistory } from 'vue-router'
import ChatView from '@/views/ChatView.vue'
import LoginView from '@/views/LoginView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
    { path: '/', name: 'home', component: ChatView },
    { path: '/c/:sessionId', name: 'chat', component: ChatView, props: true },
    { path: '/admin', name: 'admin', component: () => import('@/views/AdminView.vue'), meta: { requiresAdmin: true } },
    { path: '/test-segments', name: 'test-segments', component: () => import('@/views/TestSegments.vue') },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  const authStore = useAuthStore()

  if (authStore.authRequired === null) {
    await authStore.checkBackendAuth()
  }

  if (!authStore.authRequired) return true

  if (!authStore.isAuthenticated) {
    const valid = await authStore.checkAuth()
    if (!valid) return { name: 'login' }
  }
  if (to.meta.requiresAdmin && !authStore.isAdmin) return { name: 'home' }
  return true
})

export default router

`````

--- **end of file: frontend/src/router/index.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/stores/agents.ts** (project: lc_agent) --- 

`````typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/http'

export interface AgentSubagentConfig {
  agent_id: string
  delegation_description: string
}

export interface AgentPreset {
  id: string
  name: string
  display_name: string | null
  system_prompt: string
  default_model: string
  allowed_tool_groups: string[] | null
  allowed_mcp_servers: string[] | null
  allowed_skills: string[] | null
  llm_params: Record<string, any> | null
  subagents: AgentSubagentConfig[] | null
  enable_general_purpose_subagent: boolean
  source: 'builtin' | 'code' | 'user'
  default_enabled: boolean
}

const BUILTIN_IDS = new Set(['chat', 'empty', 'power'])

export const useAgentsStore = defineStore('agents', () => {
  const agents = ref<AgentPreset[]>([])
  const currentAgentId = ref('chat')

  const currentAgent = computed(() =>
    agents.value.find(a => a.id === currentAgentId.value) || agents.value[0]
  )

  const isBuiltin = computed(() => BUILTIN_IDS.has(currentAgentId.value))

  const isChatAgent = computed(() => currentAgentId.value === 'chat')

  const isCodeAgent = computed(() => currentAgent.value?.source === 'code')

  async function init() {
    try {
      agents.value = await api.getAgents()
    } catch (e) {
      console.error('[AgentsStore] Failed to fetch:', e)
    }
  }

  async function createAgent(data: Omit<AgentPreset, 'id'>) {
    const created = await api.createAgent(data)
    agents.value.push(created)
    return created
  }

  async function updateAgent(id: string, data: Partial<AgentPreset>) {
    const updated = await api.updateAgent(id, data)
    const idx = agents.value.findIndex(a => a.id === id)
    if (idx >= 0) agents.value[idx] = updated
    return updated
  }

  async function deleteAgent(id: string) {
    if (BUILTIN_IDS.has(id)) return
    await api.deleteAgent(id)
    agents.value = agents.value.filter(a => a.id !== id)
    if (currentAgentId.value === id) currentAgentId.value = 'chat'
  }

  async function selectAgent(id: string) {
    await api.activateAgent(id)
    currentAgentId.value = id
  }

  function getAgentName(agentId: string): string {
    const agent = agents.value.find(a => a.id === agentId)
    return agent?.display_name || agent?.name || agentId
  }

  function isAgentBuiltin(id: string): boolean {
    return BUILTIN_IDS.has(id)
  }

  return {
    agents,
    currentAgentId,
    currentAgent,
    isBuiltin,
    isChatAgent,
    isCodeAgent,
    init,
    createAgent,
    updateAgent,
    deleteAgent,
    selectAgent,
    getAgentName,
    isAgentBuiltin,
  }
})

`````

--- **end of file: frontend/src/stores/agents.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/stores/auth.ts** (project: lc_agent) --- 

`````typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, getMe } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<{ id: string; username: string; role: string } | null>(null)
  const authRequired = ref<boolean | null>(null)
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function checkBackendAuth(): Promise<boolean> {
    try {
      const resp = await fetch('/api/health')
      const data = await resp.json()
      const enabled = data.auth_enabled ?? false
      authRequired.value = enabled
      return enabled
    } catch {
      authRequired.value = false
      return false
    }
  }

  async function login(username: string, password: string) {
    const resp = await apiLogin(username, password)
    token.value = resp.token
    user.value = resp.user
    localStorage.setItem('token', resp.token)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  async function checkAuth(): Promise<boolean> {
    if (!token.value) return false
    try {
      user.value = await getMe(token.value)
      return true
    } catch {
      logout()
      return false
    }
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('auth:expired', () => {
      logout()
      window.location.hash = '#/login'
    })
  }

  return {
    token,
    user,
    authRequired,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    checkAuth,
    checkBackendAuth,
  }
})

`````

--- **end of file: frontend/src/stores/auth.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/stores/chat-session-state.ts** (project: lc_agent) --- 

`````typescript
import { ref } from 'vue'
import type { Ref } from 'vue'
import type { ChatSseClient } from '@/api/sse-client'
import type { ChatMessage, InterruptInfo, ErrorInfo, TodoItem } from './chat'

export interface SessionState {
  // Message data
  messages: Ref<ChatMessage[]>
  totalMessageCount: Ref<number>
  hasOlderMessages: Ref<boolean>
  loadingOlder: Ref<boolean>

  // Streaming state
  isStreaming: Ref<boolean>
  inThinking: boolean       // mutable flag, intentionally not Ref
  streamStartTime: number   // mutable, not Ref
  currentRoundStart: number // mutable, not Ref
  todos: Ref<TodoItem[]>
  interrupt: Ref<InterruptInfo | null>
  errorMessage: Ref<ErrorInfo | null>

  // SSE client (null until connect is called)
  client: ChatSseClient | null
}

export function createSessionState(): SessionState {
  return {
    messages: ref([]),
    totalMessageCount: ref(0),
    hasOlderMessages: ref(false),
    loadingOlder: ref(false),
    isStreaming: ref(false),
    inThinking: false,
    streamStartTime: 0,
    currentRoundStart: 0,
    todos: ref([]),
    interrupt: ref(null),
    errorMessage: ref(null),
    client: null,
  }
}

`````

--- **end of file: frontend/src/stores/chat-session-state.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/stores/chat.ts** (project: lc_agent) --- 

`````typescript
import { defineStore } from 'pinia'
import { ref, computed, shallowReactive } from 'vue'
import { ChatSseClient, type SseMessage } from '@/api/sse-client'
import { useSessionsStore } from '@/stores/sessions'
import { api } from '@/api/http'
import { createClientId } from '@/utils/client-id'
import { createSessionState } from './chat-session-state'
import type { SessionState } from './chat-session-state'
import type { ContentBlock } from '@/utils/fileUpload'

const INITIAL_MESSAGE_LIMIT = 6

export interface LlmRoundUsage {
  inputTokens: number
  outputTokens: number
  totalTokens: number
  cacheReadTokens: number
  reasoningTokens: number
  duration?: number
}

export interface MessageUsage {
  rounds: LlmRoundUsage[]
  toolCallCount: number
  totalDuration?: number
}

export interface HttpTraceMessagePart {
  method?: string
  url?: string
  headers: Record<string, string>
  body: string
  bodyFormat?: 'json' | 'text' | 'empty' | 'unknown'
}

export interface HttpTraceResponsePart {
  status?: number
  headers: Record<string, string>
  body: string
  bodyFormat?: 'json' | 'text' | 'empty' | 'unknown'
  ok?: boolean
}

export interface HttpTrace {
  id: string
  sequence: number
  kind: 'llm_http'
  provider?: string
  model?: string
  startedAt: number
  durationMs?: number
  request: HttpTraceMessagePart
  response: HttpTraceResponsePart
  error?: string | null
}

export interface ErrorInfo {
  title: string
  detail: string
  suggestions?: string[]
  techDetail?: string
  errorCode?: string
}

export interface ContentSegment {
  type: 'text' | 'tool'
  text?: string
  toolCall?: ToolCall
}

export interface SubAgentEntry {
  tool_call_id: string
  name: string
  sub_session_id: string
  query: string
  status: 'running' | 'done' | 'error' | 'cancelled' | 'interrupted'
  tokenPreview: string
  toolCallCount: number
  tokenCount: number
  tokens: string
  thinking: string
  thinkCount: number
  innerToolCalls: Array<{ name: string; status: string; args?: unknown; result?: string }>
  duration?: number
  httpTraces?: HttpTrace[]
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content: string | ContentBlock[]
  timestamp: number
  toolCalls?: ToolCall[]
  segments?: ContentSegment[]
  subAgents?: Record<string, SubAgentEntry>
  isStreaming?: boolean
  isSystem?: boolean
  usage?: MessageUsage
  httpTraces?: HttpTrace[]
  httpTracesCount?: number
}

export interface ToolCall {
  name: string
  runId?: string
  args?: Record<string, any>
  result?: string
  status: 'pending' | 'running' | 'done' | 'error' | 'cancelled' | 'interrupted'
  startTime?: number
  duration?: number
  resultLength?: number
  is_subagent?: boolean
  sub_session_id?: string
}

export interface InterruptInfo {
  actionRequests: any[]
  reviewConfigs: any[]
  data: any[]
}

export interface ReplayMessage {
  role: 'user' | 'assistant'
  content: string | ContentBlock[]
}

export interface SendMessageOptions {
  replaceFromMessageId?: string
  history?: ReplayMessage[]
  llmParams?: Record<string, any> | null
}

function normalizeToolStatus(status: any): ToolCall['status'] {
  if (status === 'pending' || status === 'running' || status === 'done' || status === 'error') {
    return status
  }
  if (status === 'cancelled' || status === 'interrupted') return status
  if (status === 'success') return 'done'
  return 'done'
}

function normalizeSubAgentDoneStatus(status: any): SubAgentEntry['status'] {
  if (status === 'error' || status === 'cancelled' || status === 'interrupted') return status
  return 'done'
}

function ensureToolMarkers(content: string, toolCalls?: ToolCall[]): string {
  if (!toolCalls?.length) return content
  const missingIndexes = toolCalls
    .map((_, idx) => idx)
    .filter(idx => !content.includes(`<!--TOOL:${idx}-->`))
  if (missingIndexes.length === 0) return content
  return `${content}\n${missingIndexes.map(idx => `<!--TOOL:${idx}-->`).join('\n')}\n`
}

function ensureHttpMarkers(content: string, traceCount: number): string {
  if (traceCount <= 0) return content
  const missing = Array.from({ length: traceCount }, (_, i) => i)
    .filter(i => !content.includes(`<!--HTTP:${i}-->`))
  if (missing.length === 0) return content
  return `${content}\n${missing.map(i => `<!--HTTP:${i}-->`).join('\n')}\n`
}

function normalizeHistoryUsage(rawUsage: any): MessageUsage | undefined {
  if (!rawUsage) return undefined
  const rounds = (rawUsage.rounds || []).map((round: any) => ({
    inputTokens: round.inputTokens ?? round.input_tokens ?? 0,
    outputTokens: round.outputTokens ?? round.output_tokens ?? 0,
    totalTokens: round.totalTokens ?? round.total_tokens ?? 0,
    cacheReadTokens: round.cacheReadTokens ?? round.cache_read_tokens ?? 0,
    reasoningTokens: round.reasoningTokens ?? round.reasoning_tokens ?? 0,
    duration: round.duration ?? round.duration_ms,
  }))
  return {
    rounds,
    toolCallCount: rawUsage.toolCallCount ?? rawUsage.tool_call_count ?? 0,
    totalDuration: rawUsage.totalDuration ?? rawUsage.total_duration_ms,
  }
}

function normalizeHttpTrace(raw: any): HttpTrace {
  return {
    id: raw.id || createClientId(),
    sequence: raw.sequence ?? 0,
    kind: 'llm_http',
    provider: raw.provider || undefined,
    model: raw.model || undefined,
    startedAt: raw.startedAt ?? raw.started_at ?? Date.now(),
    durationMs: raw.durationMs ?? raw.duration_ms,
    request: {
      method: raw.request?.method || undefined,
      url: raw.request?.url || undefined,
      headers: raw.request?.headers || {},
      body: raw.request?.body || '空',
      bodyFormat: raw.request?.bodyFormat ?? raw.request?.body_format ?? 'unknown',
    },
    response: {
      status: raw.response?.status,
      headers: raw.response?.headers || {},
      body: raw.response?.body || '未返回',
      bodyFormat: raw.response?.bodyFormat ?? raw.response?.body_format ?? 'unknown',
      ok: raw.response?.ok,
    },
    error: raw.error ?? null,
  }
}

function normalizeHttpTraces(raw: any): HttpTrace[] | undefined {
  if (!Array.isArray(raw) || raw.length === 0) return undefined
  return raw.map(normalizeHttpTrace)
}

function normalizeHistoryMessage(msg: any): ChatMessage | null {
  if (msg.role === 'system') {
    const rawContent = msg.content
    let content = ''
    if (Array.isArray(rawContent)) {
      content = rawContent.find((b: any) => b.type === 'text')?.text || ''
    } else {
      content = rawContent || ''
    }
    return {
      id: msg.id || createClientId(),
      role: 'user',
      content,
      timestamp: msg.created_at ? new Date(msg.created_at).getTime() : Date.now(),
      isSystem: true,
    }
  }

  const role = msg.role === 'human' ? 'user' : msg.role === 'ai' ? 'assistant' : msg.role
  if (!['user', 'assistant', 'tool'].includes(role)) return null

  const toolCalls = (msg.tool_calls || msg.toolCalls || []).map((tc: any) => ({
    name: tc.name || '',
    runId: tc.runId || tc.run_id || tc.id,
    args: tc.args || {},
    result: tc.result,
    status: normalizeToolStatus(tc.status),
    startTime: tc.startTime ?? tc.start_time,
    duration: tc.duration,
    resultLength: tc.resultLength ?? tc.result_length ?? tc.result?.length,
    is_subagent: tc.is_subagent || false,
    sub_session_id: tc.sub_session_id || '',
  }))
  const usage = normalizeHistoryUsage(msg.usage)
  if (usage && toolCalls.length > usage.toolCallCount) {
    usage.toolCallCount = toolCalls.length
  }

  const subAgents: Record<string, SubAgentEntry> = {}
  for (const tc of toolCalls) {
    if (tc.is_subagent && tc.runId) {
      subAgents[tc.runId] = {
        tool_call_id: tc.runId,
        name: tc.name,
        sub_session_id: tc.sub_session_id || '',
        query: typeof tc.args === 'object' ? (tc.args?.query || '') : '',
        status: tc.status === 'running' ? 'running' : normalizeSubAgentDoneStatus(tc.status),
        tokenPreview: tc.result || '',
        toolCallCount: 0,
        tokenCount: 0,
        tokens: '',
        thinking: '',
        thinkCount: 0,
        innerToolCalls: [],
        duration: tc.duration,
      }
    }
  }

  const httpTraces = normalizeHttpTraces(msg.http_traces || msg.httpTraces)
  const httpTracesCount = msg.http_traces_count ?? msg.httpTracesCount ?? httpTraces?.length ?? 0
  let content: string | ContentBlock[]
  if (role === 'user') {
    content = Array.isArray(msg.content)
      ? msg.content
      : [{ type: 'text', text: String(msg.content || '') }]
  } else {
    const rawContent = msg.content
    let textContent = ''
    if (Array.isArray(rawContent)) {
      textContent = rawContent.find((b: any) => b.type === 'text')?.text || ''
    } else {
      textContent = rawContent || ''
    }
    textContent = ensureToolMarkers(textContent, toolCalls)
    if (httpTracesCount > 0) {
      textContent = ensureHttpMarkers(textContent, httpTracesCount)
    }
    content = textContent
  }

  return {
    id: msg.id || createClientId(),
    role,
    content,
    timestamp: msg.created_at ? new Date(msg.created_at).getTime() : Date.now(),
    toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
    subAgents: Object.keys(subAgents).length > 0 ? subAgents : undefined,
    usage,
    httpTraces,
    httpTracesCount,
  }
}

function normalizeHistoryMessages(rawMessages: any[]): ChatMessage[] {
  const loaded: ChatMessage[] = []
  for (const msg of rawMessages) {
    const chatMsg = normalizeHistoryMessage(msg)
    if (!chatMsg) continue
    if (chatMsg.role === 'tool') {
      const lastAssistant = [...loaded].reverse().find(m => m.role === 'assistant')
      if (lastAssistant?.toolCalls) {
        const tc = lastAssistant.toolCalls.find(t => t.name === msg.name && !t.result)
        if (tc) {
          const resultStr = typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)
          tc.result = resultStr
          tc.status = 'done'
          tc.resultLength = resultStr.length
        }
      }
      continue
    }
    loaded.push(chatMsg)
  }
  return loaded
}

function mergeFinalUsageRounds(targetRounds: LlmRoundUsage[], rawRounds: any[]) {
  rawRounds.forEach((round: any, idx: number) => {
    const normalized = {
      inputTokens: round.input_tokens || 0,
      outputTokens: round.output_tokens || 0,
      totalTokens: round.total_tokens || 0,
      cacheReadTokens: round.cache_read_tokens || 0,
      reasoningTokens: round.reasoning_tokens || 0,
      duration: round.duration_ms || undefined,
    }
    if (targetRounds[idx]) {
      Object.assign(targetRounds[idx], normalized)
    } else {
      targetRounds.push(normalized)
    }
  })
}

export interface SubAgentReducerResult {
  changed: boolean
  shouldRefresh: boolean
}

const SUBAGENT_UNCHANGED: SubAgentReducerResult = { changed: false, shouldRefresh: false }

type SubAgentReducer = (
  message: ChatMessage | undefined,
  msg: SseMessage,
  parentThreadId?: string | null,
) => SubAgentReducerResult

function getSubAgentToolCallId(msg: SseMessage): string {
  return msg.tool_call_id || msg.run_id || ''
}

function findSubAgentMessage(
  messages: ChatMessage[],
  toolCallId: string,
  allowLastAssistantFallback = false,
): ChatMessage | undefined {
  if (!toolCallId) return undefined
  let lastAssistant: ChatMessage | undefined
  for (let i = messages.length - 1; i >= 0; i--) {
    const message = messages[i]
    if (message.role !== 'assistant') continue
    if (allowLastAssistantFallback && message.role === 'assistant' && !lastAssistant) {
      lastAssistant = message
    }
    if (message.subAgents?.[toolCallId]) return message
    if (message.toolCalls?.some(t => t.runId === toolCallId)) return message
  }
  return allowLastAssistantFallback ? lastAssistant : undefined
}

export function applySubAgentEventToMessages(
  messages: ChatMessage[],
  msg: SseMessage,
  reducer: SubAgentReducer,
  parentThreadId?: string | null,
): SubAgentReducerResult {
  const toolCallId = getSubAgentToolCallId(msg)
  const message = findSubAgentMessage(messages, toolCallId, msg.type === 'subagent_start')
  return reducer(message, msg, parentThreadId)
}

export function applySubAgentStart(
  message: ChatMessage | undefined,
  msg: SseMessage,
  parentThreadId?: string | null,
): SubAgentReducerResult {
  if (!message || message.role !== 'assistant') return SUBAGENT_UNCHANGED

  const toolCallId = msg.tool_call_id || msg.run_id || ''
  if (!toolCallId) return SUBAGENT_UNCHANGED
  const subSessionId = msg.sub_session_id
    || (parentThreadId ? `${parentThreadId}--sa--${toolCallId}` : '')

  const existing = message.subAgents?.[toolCallId]
  const entry: SubAgentEntry = {
    tool_call_id: toolCallId,
    name: msg.name || msg.subagent_type || existing?.name || '子 Agent',
    sub_session_id: subSessionId || existing?.sub_session_id || '',
    query: msg.query || msg.description || existing?.query || '',
    status: 'running',
    tokenPreview: existing?.tokenPreview || '',
    toolCallCount: existing?.toolCallCount || 0,
    tokenCount: existing?.tokenCount || 0,
    tokens: existing?.tokens || '',
    thinking: existing?.thinking || '',
    thinkCount: existing?.thinkCount || 0,
    innerToolCalls: existing?.innerToolCalls || [],
    duration: existing?.duration,
    httpTraces: existing?.httpTraces,
  }
  if (!message.subAgents) {
    message.subAgents = {}
  }
  message.subAgents[toolCallId] = entry

  let tc = message.toolCalls?.find(t => t.runId === toolCallId)
  if (!tc) {
    message.toolCalls = message.toolCalls || []
    tc = {
      name: 'task',
      runId: toolCallId,
      args: msg.description ? { description: msg.description } : undefined,
      status: 'running',
      startTime: Date.now(),
      is_subagent: true,
      sub_session_id: subSessionId,
    }
    message.toolCalls.push(tc)
  }
  tc.is_subagent = true
  tc.sub_session_id = subSessionId
  return { changed: true, shouldRefresh: true }
}

export function applySubAgentToken(
  message: ChatMessage | undefined,
  msg: SseMessage,
): SubAgentReducerResult {
  if (!message?.subAgents) return SUBAGENT_UNCHANGED
  const toolCallId = msg.tool_call_id
  if (!toolCallId) return SUBAGENT_UNCHANGED
  const sa = message.subAgents[toolCallId]
  if (!sa) return SUBAGENT_UNCHANGED

  const newCount = sa.tokenCount + 1
  message.subAgents[toolCallId] = { ...sa, tokens: sa.tokens + (msg.content || ''), tokenCount: newCount }
  return { changed: true, shouldRefresh: newCount % 3 === 0 }
}

export function applySubAgentThinking(
  message: ChatMessage | undefined,
  msg: SseMessage,
): SubAgentReducerResult {
  if (!message?.subAgents) return SUBAGENT_UNCHANGED
  const toolCallId = msg.tool_call_id
  if (!toolCallId) return SUBAGENT_UNCHANGED
  const sa = message.subAgents[toolCallId]
  if (!sa) return SUBAGENT_UNCHANGED

  const newThinkCount = sa.thinkCount + 1
  message.subAgents[toolCallId] = {
    ...sa,
    thinking: sa.thinking + (msg.content || ''),
    thinkCount: newThinkCount,
  }
  return { changed: true, shouldRefresh: newThinkCount % 5 === 0 }
}

export function applySubAgentToolCall(
  message: ChatMessage | undefined,
  msg: SseMessage,
): SubAgentReducerResult {
  if (!message?.subAgents) return SUBAGENT_UNCHANGED
  const toolCallId = msg.tool_call_id
  if (!toolCallId) return SUBAGENT_UNCHANGED
  const sa = message.subAgents[toolCallId]
  if (!sa) return SUBAGENT_UNCHANGED

  message.subAgents[toolCallId] = {
    ...sa,
    innerToolCalls: [...sa.innerToolCalls, {
      name: msg.name || '',
      status: 'running',
      args: msg.args,
    }],
    toolCallCount: sa.toolCallCount + 1,
  }
  return { changed: true, shouldRefresh: true }
}

export function applySubAgentToolResult(
  message: ChatMessage | undefined,
  msg: SseMessage,
): SubAgentReducerResult {
  if (!message?.subAgents) return SUBAGENT_UNCHANGED
  const toolCallId = msg.tool_call_id
  if (!toolCallId) return SUBAGENT_UNCHANGED
  const sa = message.subAgents[toolCallId]
  if (!sa) return SUBAGENT_UNCHANGED

  const updatedCalls = [...sa.innerToolCalls]
  const idx = [...updatedCalls].reverse().findIndex(
    t => t.name === msg.name && t.status === 'running',
  )
  if (idx === -1) return SUBAGENT_UNCHANGED

  const resultStatus = msg.status === 'error' || msg.is_error ? 'error' : 'done'
  const realIdx = updatedCalls.length - 1 - idx
  updatedCalls[realIdx] = { ...updatedCalls[realIdx], result: msg.result, status: resultStatus }
  message.subAgents[toolCallId] = { ...sa, innerToolCalls: updatedCalls }
  return { changed: true, shouldRefresh: true }
}

export function applySubAgentDone(
  message: ChatMessage | undefined,
  msg: SseMessage,
): SubAgentReducerResult {
  if (!message) return SUBAGENT_UNCHANGED
  const toolCallId = msg.tool_call_id
  if (!toolCallId) return SUBAGENT_UNCHANGED
  const sa = message.subAgents?.[toolCallId]
  const rawHttpTraces = msg.http_traces
  const saHttpTraces = rawHttpTraces?.length ? normalizeHttpTraces(rawHttpTraces) : undefined
  const doneStatus = normalizeSubAgentDoneStatus(msg.status)
  if (sa) {
    message.subAgents![toolCallId] = {
      ...sa,
      status: doneStatus,
      tokens: sa.tokens,
      tokenPreview: sa.tokens || msg.result_preview || '',
      duration: msg.duration ?? sa.duration,
      httpTraces: saHttpTraces,
    }
  }
  const tc = message.toolCalls?.find(t => t.runId === toolCallId)
  if (tc) {
    tc.status = doneStatus
    tc.result = sa?.tokens || msg.result_preview || ''
    tc.duration = tc.startTime ? Date.now() - tc.startTime : msg.duration
    tc.resultLength = (tc.result || '').length
  }
  return { changed: !!sa || !!tc, shouldRefresh: true }
}

export interface TodoItem {
  content: string
  status: 'pending' | 'in_progress' | 'completed'
}

export const useChatStore = defineStore('chat', () => {
  // --- Session Registry ---
  // shallowReactive() makes Map.get/set/delete/has reactive (so sidebar streaming
  // indicators update automatically) without deep-unwrapping the Ref fields
  // inside SessionState.
  const activeSessions = shallowReactive(new Map<string, SessionState>())
  const activeSessionId = ref<string | null>(null)
  const sessionOffsets = new Map<string, number>()

  // --- Computed delegates to active session (API unchanged for components) ---
  const _active = (): SessionState | undefined =>
    activeSessionId.value ? activeSessions.get(activeSessionId.value) : undefined

  const messages = computed<ChatMessage[]>(() => _active()?.messages.value ?? [])
  const isStreaming = computed(() => _active()?.isStreaming.value ?? false)
  const interrupt = computed(() => _active()?.interrupt.value ?? null)
  const todos = computed(() => _active()?.todos.value ?? [])
  const errorMessage = computed(() => _active()?.errorMessage.value ?? null)
  const totalMessageCount = computed(() => _active()?.totalMessageCount.value ?? 0)
  const hasOlderMessages = computed(() => _active()?.hasOlderMessages.value ?? false)
  const loadingOlder = computed(() => _active()?.loadingOlder.value ?? false)
  const isConnected = computed(() => !!activeSessionId.value)
  const threadId = computed(() => activeSessionId.value)
  const lastMessage = computed(() => {
    const msgs = messages.value
    return msgs[msgs.length - 1] ?? null
  })

  function _createClientForSession(state: SessionState, sessionId: string): ChatSseClient {
    const client = new ChatSseClient()
    state.client = client
    _registerHandlers(client, state, sessionId)
    return client
  }

  function _releaseBackgroundSession(sessionId: string, state: SessionState): void {
    state.client?.disconnect()
    state.client = null
    sessionOffsets.delete(sessionId)
    activeSessions.delete(sessionId)
  }

  function _registerHandlers(client: ChatSseClient, state: SessionState, sessionId: string) {
    client.on('thinking', (msg: SseMessage) => {
      if (!state.isStreaming.value) {
        state.isStreaming.value = true
        state.streamStartTime = Date.now()
        state.currentRoundStart = Date.now()
        state.messages.value.push({
          id: createClientId(),
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          isStreaming: true,
          usage: { rounds: [], toolCallCount: 0 },
        })
      }
      const last = state.messages.value[state.messages.value.length - 1]
      if (last && last.role === 'assistant') {
        if (!state.inThinking) {
          state.inThinking = true
          last.content = (last.content as string) + '<!--THINK_START-->'
        }
        last.content = (last.content as string) + (msg.content || '')
      }
    })

    client.on('token', (msg: SseMessage) => {
      if (!state.isStreaming.value) {
        state.isStreaming.value = true
        state.streamStartTime = Date.now()
        state.currentRoundStart = Date.now()
        state.messages.value.push({
          id: createClientId(),
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          isStreaming: true,
          usage: { rounds: [], toolCallCount: 0 },
        })
      }
      const last = state.messages.value[state.messages.value.length - 1]
      if (last && last.role === 'assistant') {
        if (state.inThinking) {
          state.inThinking = false
          last.content = (last.content as string) + '<!--THINK_END-->'
        }
        last.content = (last.content as string) + (msg.content || '')
      }
    })

    client.on('content', (msg: SseMessage) => {
      const last = state.messages.value[state.messages.value.length - 1]
      if (last && last.role === 'assistant') {
        last.content = (last.content as string) + (msg.content || '')
      }
    })

    client.on('llm_usage', (msg: SseMessage) => {
      const last = state.messages.value[state.messages.value.length - 1]
      if (last?.usage) {
        const roundDuration = state.currentRoundStart ? Date.now() - state.currentRoundStart : undefined
        last.usage.rounds.push({
          inputTokens: msg.input_tokens || 0,
          outputTokens: msg.output_tokens || 0,
          totalTokens: msg.total_tokens || 0,
          cacheReadTokens: msg.cache_read_tokens || 0,
          reasoningTokens: msg.reasoning_tokens || 0,
          duration: roundDuration,
        })
        state.currentRoundStart = Date.now()
      }
    })

    client.on('tool_call', (msg: SseMessage) => {
      if (!state.isStreaming.value) {
        state.isStreaming.value = true
        state.streamStartTime = Date.now()
        state.currentRoundStart = Date.now()
        state.messages.value.push({
          id: createClientId(),
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          isStreaming: true,
          usage: { rounds: [], toolCallCount: 0 },
        })
      }
      const last = state.messages.value[state.messages.value.length - 1]
      if (last && last.role === 'assistant') {
        if (state.inThinking) {
          state.inThinking = false
          last.content = (last.content as string) + '<!--THINK_END-->'
        }
        if (!last.toolCalls) last.toolCalls = []

        const existingByRunId = last.toolCalls.find(t => t.runId === msg.run_id)
        if (existingByRunId) {
          return
        }

        const tcIdx = last.toolCalls.length
        const tc: ToolCall = {
          name: msg.name || '',
          runId: msg.run_id,
          args: msg.args,
          status: 'running',
          startTime: Date.now(),
          is_subagent: msg.is_subagent,
          sub_session_id: msg.sub_session_id,
        }
        last.toolCalls.push(tc)
        last.content = (last.content as string) + `\n<!--TOOL:${tcIdx}-->\n`
        if (last.usage) {
          last.usage.toolCallCount++
        }
        if (msg.name === 'write_todos' && msg.args?.todos) {
          state.todos.value = msg.args.todos as TodoItem[]
        }
      }
    })

    client.on('tool_result', (msg: SseMessage) => {
      const last = state.messages.value[state.messages.value.length - 1]
      if (last?.toolCalls) {
        const tc = last.toolCalls.find(t => t.name === msg.name && t.status === 'running')
        if (tc) {
          tc.result = msg.result
          tc.status = 'done'
          tc.duration = tc.startTime ? Date.now() - tc.startTime : undefined
          tc.resultLength = msg.result?.length || 0
        }
      }
    })

    client.on('subagent_start', (msg: SseMessage) => {
      const result = applySubAgentEventToMessages(state.messages.value, msg, applySubAgentStart, sessionId)
      if (result.shouldRefresh) {
        state.messages.value = [...state.messages.value]
      }
    })

    client.on('subagent_token', (msg: SseMessage) => {
      const result = applySubAgentEventToMessages(state.messages.value, msg, applySubAgentToken, sessionId)
      if (result.shouldRefresh) {
        state.messages.value = [...state.messages.value]
      }
    })

    client.on('subagent_thinking', (msg: SseMessage) => {
      const result = applySubAgentEventToMessages(state.messages.value, msg, applySubAgentThinking, sessionId)
      if (result.shouldRefresh) {
        state.messages.value = [...state.messages.value]
      }
    })

    client.on('subagent_tool_call', (msg: SseMessage) => {
      const result = applySubAgentEventToMessages(state.messages.value, msg, applySubAgentToolCall, sessionId)
      if (result.shouldRefresh) {
        state.messages.value = [...state.messages.value]
      }
    })

    client.on('subagent_tool_result', (msg: SseMessage) => {
      const result = applySubAgentEventToMessages(state.messages.value, msg, applySubAgentToolResult, sessionId)
      if (result.shouldRefresh) {
        state.messages.value = [...state.messages.value]
      }
    })

    client.on('subagent_done', (msg: SseMessage) => {
      const result = applySubAgentEventToMessages(state.messages.value, msg, applySubAgentDone, sessionId)
      if (result.shouldRefresh) {
        state.messages.value = [...state.messages.value]
      }
    })

    client.on('interrupt', (msg: SseMessage) => {
      state.interrupt.value = {
        actionRequests: msg.action_requests || [],
        reviewConfigs: msg.review_configs || [],
        data: msg.data || [],
      }
    })

    client.on('done', (msg: SseMessage) => {
      state.errorMessage.value = null
      state.isStreaming.value = false
      state.inThinking = false
      const last = state.messages.value[state.messages.value.length - 1]
      if (last) {
        last.isStreaming = false
        const isResume = !!msg.is_resume
        const usageData = msg.usage as any[] | undefined
        if (usageData && usageData.length > 0) {
          if (last.usage && state.streamStartTime) {
            last.usage.totalDuration = Date.now() - state.streamStartTime
          }
          if (last.usage) {
            if (isResume) {
              const offset = last.usage.rounds.length - usageData.length
              usageData.forEach((round: any, idx: number) => {
                const normalized = {
                  inputTokens: round.input_tokens || 0,
                  outputTokens: round.output_tokens || 0,
                  totalTokens: round.total_tokens || 0,
                  cacheReadTokens: round.cache_read_tokens || 0,
                  reasoningTokens: round.reasoning_tokens || 0,
                  duration: round.duration_ms || undefined,
                }
                const targetIdx = offset + idx
                if (targetIdx >= 0 && last.usage!.rounds[targetIdx]) {
                  Object.assign(last.usage!.rounds[targetIdx], normalized)
                } else {
                  last.usage!.rounds.push(normalized)
                }
              })
            } else {
              mergeFinalUsageRounds(last.usage.rounds, usageData)
            }
          }
        }
        const rawTraces = (msg as any).http_traces || (msg as any).httpTraces
        if (rawTraces) {
          const newTraces = normalizeHttpTraces(rawTraces) || []
          if (isResume && newTraces.length) {
            last.httpTraces = [...(last.httpTraces || []), ...newTraces]
          } else if (newTraces.length) {
            last.httpTraces = newTraces
          }
          if (last.httpTraces?.length) {
            last.content = ensureHttpMarkers(last.content as string, last.httpTraces.length)
          }
        }
      }
      setTimeout(() => {
        const sessionsStore = useSessionsStore()
        sessionsStore.refreshSessionTitle(sessionId)
      }, 3000)
      // Auto-cleanup: if this session is no longer the active one, release resources
      if (sessionId !== activeSessionId.value) {
        _releaseBackgroundSession(sessionId, state)
      }
    })

    client.on('cancelled', () => {
      state.errorMessage.value = null
      state.isStreaming.value = false
      state.inThinking = false
      const last = state.messages.value[state.messages.value.length - 1]
      if (last) last.isStreaming = false
      // Auto-cleanup: if this session is no longer the active one, release resources
      if (sessionId !== activeSessionId.value) {
        _releaseBackgroundSession(sessionId, state)
      }
    })

    client.on('error', (msg: SseMessage) => {
      state.isStreaming.value = false
      if (state.inThinking) {
        const last = state.messages.value[state.messages.value.length - 1]
        if (last && last.role === 'assistant') {
          last.content = (last.content as string) + '<!--THINK_END-->'
        }
        state.inThinking = false
      }
      const lastMsg = state.messages.value[state.messages.value.length - 1]
      if (lastMsg && lastMsg.role === 'assistant') {
        lastMsg.isStreaming = false
      }
      if (msg.title) {
        state.errorMessage.value = {
          title: msg.title,
          detail: msg.detail || '',
          suggestions: msg.suggestions,
          techDetail: msg.tech_detail,
          errorCode: msg.error_code,
        }
      } else {
        state.errorMessage.value = {
          title: 'AI 模型接口请求失败',
          detail: msg.message || '',
          suggestions: ['请稍后重试，如问题持续请联系管理员'],
          errorCode: 'UNKNOWN',
        }
      }
      console.error('[Chat] Error:', msg.message || msg.title)
      // Auto-cleanup: if this session is no longer the active one, release resources
      if (sessionId !== activeSessionId.value) {
        _releaseBackgroundSession(sessionId, state)
      }
    })

    client.on('title_update', (msg: SseMessage) => {
      if (msg.thread_id && msg.title) {
        const sessionsStore = useSessionsStore()
        sessionsStore.updateTitleLocal(msg.thread_id, msg.title)
      }
    })
  }

  /**
   * Switch the active session. If the departing session is streaming, it stays
   * in the registry and continues in the background. If it is idle, it is
   * released immediately. The arriving session is loaded from DB unless it is
   * already in the registry (was streaming in background).
   */
  async function switchToSession(sessionId: string): Promise<void> {
    if (activeSessionId.value === sessionId) return

    // Departing session
    const oldId = activeSessionId.value
    if (oldId) {
      const old = activeSessions.get(oldId)
      if (old && !old.isStreaming.value) {
        _releaseBackgroundSession(oldId, old)
      }
      // Streaming session: keep in map — SSE continues in background
    }

    activeSessionId.value = sessionId

    // Arriving session: already in registry means it was streaming in background
    if (activeSessions.has(sessionId)) return

    // New session: create state, load messages, connect client
    const state = createSessionState()
    activeSessions.set(sessionId, state)
    await _loadMessagesIntoState(sessionId, state)

    // Stale switch guard: verify this is still the current state object for
    // this session. Catches the A→B→A rapid-switch case where a second
    // switchToSession(A) created a new state and replaced ours in the map.
    // Only return — do NOT delete from the map (that would evict the
    // replacement state that is still loading).
    if (activeSessions.get(sessionId) !== state) {
      return
    }

    const client = _createClientForSession(state, sessionId)
    client.setThreadId(sessionId)
  }

  /** Expose session streaming state for sidebar indicators */
  function isSessionStreaming(sessionId: string): boolean {
    return activeSessions.get(sessionId)?.isStreaming.value ?? false
  }

  function getStreamingSessionIds(): string[] {
    return [...activeSessions.keys()].filter(id =>
      activeSessions.get(id)?.isStreaming.value
    )
  }

  async function sendMessage(
    content: ContentBlock[],
    presetId: string = 'chat',
    modelId: string = '',
    options: SendMessageOptions = {},
  ) {
    if (!content.length) return

    const sessionsStore = useSessionsStore()
    const sessionId = sessionsStore.currentSessionId
    if (sessionId && sessionsStore.isLocalSession(sessionId)) {
      const isFirstMessage = sessionsStore.currentSession?.message_count === 0
      const realId = await sessionsStore.persistSession(sessionId, modelId)
      await switchToSession(realId)
      if (isFirstMessage) {
        const firstText = content.find(b => b.type === 'text')?.text || ''
        sessionsStore.updateTitleLocal(realId, firstText.slice(0, 30))
      }
    } else if (!activeSessionId.value) {
      if (sessionId) await switchToSession(sessionId)
    }

    const state = activeSessionId.value ? activeSessions.get(activeSessionId.value) : undefined
    if (!state?.client) return

    state.errorMessage.value = null

    state.messages.value.push({
      id: createClientId(),
      role: 'user',
      content,
      timestamp: Date.now(),
    })

    state.client.sendMessage(content, presetId, modelId, {
      replaceFromMessageId: options.replaceFromMessageId,
      history: options.history,
      llmParams: options.llmParams,
    })
  }

  function respondToInterrupt(
    approved: boolean,
    presetId: string = 'chat',
    permanentlyAllow?: string,
    llmParams?: Record<string, any> | null,
  ) {
    const state = _active()
    if (!state?.client) return
    const count = state.interrupt.value?.actionRequests?.length || 1
    const decisions = Array.from({ length: count }, () => ({
      type: approved ? 'approve' : 'reject',
    }))
    const resumePayload: Record<string, any> = { decisions }
    if (permanentlyAllow) {
      resumePayload.permanently_allow = permanentlyAllow
    }
    state.client.sendInterruptResume(resumePayload, presetId, undefined, llmParams)
    state.interrupt.value = null
    state.isStreaming.value = true
    state.currentRoundStart = Date.now()
    const last = state.messages.value[state.messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.isStreaming = true
    }
  }

  function resumeInterrupt(
    resumeValue: any,
    presetId: string = 'chat',
    model?: string,
    llmParams?: Record<string, any> | null,
  ) {
    const state = _active()
    if (!state?.client) return
    state.client.sendInterruptResume(resumeValue, presetId, model, llmParams)
    state.interrupt.value = null
    state.isStreaming.value = true
    state.currentRoundStart = Date.now()
    const last = state.messages.value[state.messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.isStreaming = true
    }
  }

  async function _loadMessagesIntoState(sessionId: string, state: SessionState): Promise<void> {
    const sessionsStore = useSessionsStore()
    if (sessionsStore.isLocalSession(sessionId)) {
      state.totalMessageCount.value = 0
      sessionOffsets.set(sessionId, 0)
      state.messages.value = []
      state.hasOlderMessages.value = false
      return
    }
    try {
      const resp = await api.getSessionMessages(sessionId, { limit: INITIAL_MESSAGE_LIMIT })
      const total = resp?.total ?? 0
      const rawMessages = resp?.messages ?? resp
      state.totalMessageCount.value = total
      sessionOffsets.set(sessionId, resp?.offset ?? 0)

      // Always set messages on API success — this ensures session switches always
      // replace the current messages, even when the target session returns empty.
      state.messages.value = normalizeHistoryMessages(
        Array.isArray(rawMessages) ? rawMessages : []
      )
      state.hasOlderMessages.value = total > state.messages.value.length
    } catch (e) {
      // On API failure keep current messages (graceful degradation)
      console.error('[Chat] Failed to load messages:', e)
    }
  }

  async function loadMessages(sessionId: string): Promise<void> {
    // If the target session is in the registry, load into its own state.
    // Otherwise fall back to the currently active session — this supports
    // temporary display of sub-session messages without a full session switch.
    const targetState = activeSessions.get(sessionId) ?? _active()
    if (targetState) {
      await _loadMessagesIntoState(sessionId, targetState)
    }
  }

  async function loadOlderMessages(sessionId: string) {
    const state = _active()
    if (!state) return
    const currentOffset = sessionOffsets.get(sessionId) ?? 0
    if (!state.hasOlderMessages.value || state.loadingOlder.value || currentOffset <= 0) return
    state.loadingOlder.value = true
    try {
      const olderPageSize = INITIAL_MESSAGE_LIMIT
      const newOffset = Math.max(0, currentOffset - olderPageSize)
      const newLimit = currentOffset - newOffset
      if (newLimit <= 0) return

      const resp = await api.getSessionMessages(sessionId, { limit: newLimit, offset: newOffset })
      const olderRaw = resp?.messages ?? []
      if (olderRaw.length === 0) return

      sessionOffsets.set(sessionId, newOffset)
      const olderNormalized = normalizeHistoryMessages(olderRaw)
      state.messages.value = [...olderNormalized, ...state.messages.value]
      state.hasOlderMessages.value = state.totalMessageCount.value > state.messages.value.length
    } catch (e) {
      console.error('[Chat] Failed to load older messages:', e)
    } finally {
      state.loadingOlder.value = false
    }
  }

  function stopGeneration() {
    const state = _active()
    if (state?.client && state.isStreaming.value) {
      state.client.sendCancel()
    }
  }

  function clearMessages() {
    const state = _active()
    if (state) {
      state.messages.value = []
      state.todos.value = []
      state.interrupt.value = null
      state.errorMessage.value = null
    }
  }

  function truncateAfterMessage(messageId: string) {
    const state = _active()
    if (!state) return
    const idx = state.messages.value.findIndex(m => m.id === messageId)
    if (idx < 0) return
    state.messages.value = state.messages.value.slice(0, idx)
  }

  return {
    messages,
    isStreaming,
    isConnected,
    threadId,
    interrupt,
    lastMessage,
    todos,
    errorMessage,
    totalMessageCount,
    hasOlderMessages,
    loadingOlder,
    switchToSession,
    isSessionStreaming,
    getStreamingSessionIds,
    loadMessages,
    loadOlderMessages,
    sendMessage,
    stopGeneration,
    respondToInterrupt,
    resumeInterrupt,
    clearMessages,
    truncateAfterMessage,
  }
})

`````

--- **end of file: frontend/src/stores/chat.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/stores/sessions.ts** (project: lc_agent) --- 

`````typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/http'
import { useAgentsStore } from '@/stores/agents'
import { createClientId } from '@/utils/client-id'

export interface Session {
  id: string
  title: string
  agent_id: string
  model: string
  message_count: number
  is_pinned: boolean
  pinned_at: string | null
  created_at: string
  updated_at: string
}

export const useSessionsStore = defineStore('sessions', () => {
  const sessions = ref<Session[]>([])
  const currentSessionId = ref<string | null>(null)
  const localSessionIds = ref<Set<string>>(new Set())

  const currentSession = computed(() =>
    sessions.value.find(s => s.id === currentSessionId.value)
  )

  const sessionNavStack = ref<Array<{ session_id: string; label: string }>>([])

  const effectiveThreadId = computed(() => {
    const stack = sessionNavStack.value
    return stack.length > 0 ? stack[stack.length - 1].session_id : currentSessionId.value
  })

  function pushSubSession(sub_session_id: string, label: string) {
    const last = sessionNavStack.value[sessionNavStack.value.length - 1]
    if (last?.session_id === sub_session_id) return  // prevent duplicate push on repeated clicks
    sessionNavStack.value.push({ session_id: sub_session_id, label })
  }

  function popSubSession() {
    sessionNavStack.value.pop()
  }

  function popToRoot() {
    sessionNavStack.value = []
  }

  function isLocalSession(id: string): boolean {
    return localSessionIds.value.has(id)
  }

  async function init() {
    try {
      sessions.value = await api.getSessions()
    } catch (e) {
      console.error('[SessionsStore] Failed to fetch:', e)
    }
  }

  function createLocalSession(agentId: string = 'chat', model: string = ''): Session {
    const existing = sessions.value.find(
      s => s.agent_id === agentId && s.message_count === 0 && localSessionIds.value.has(s.id)
    )
    if (existing) {
      existing.model = model || existing.model
      currentSessionId.value = existing.id
      return existing
    }

    const id = createClientId()
    return ensureLocalSession(id, agentId, model)
  }

  function ensureLocalSession(id: string, agentId: string = 'chat', model: string = ''): Session {
    const existing = sessions.value.find(s => s.id === id)
    if (existing) {
      existing.agent_id = agentId
      existing.model = model || existing.model
      currentSessionId.value = existing.id
      localSessionIds.value.add(existing.id)
      return existing
    }

    const session: Session = {
      id,
      title: '新对话',
      agent_id: agentId,
      model,
      message_count: 0,
      is_pinned: false,
      pinned_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    sessions.value.unshift(session)
    localSessionIds.value.add(id)
    currentSessionId.value = id
    return session
  }

  async function persistSession(id: string, model: string = ''): Promise<string> {
    if (!localSessionIds.value.has(id)) return id
    const session = sessions.value.find(s => s.id === id)
    if (!session) return id

    const created = await api.createSession({
      agent_id: session.agent_id,
      model: model || session.model,
    })
    localSessionIds.value.delete(id)
    const newId = created.id || id
    const idx = sessions.value.findIndex(s => s.id === id)
    if (idx >= 0) {
      sessions.value[idx] = { ...sessions.value[idx], ...created, id: newId }
    }
    if (currentSessionId.value === id) {
      currentSessionId.value = newId
    }
    return newId
  }

  async function createSession(agentId: string = 'chat', model: string = '') {
    const created = await api.createSession({ agent_id: agentId, model })
    sessions.value.unshift({
      ...created,
      agent_id: agentId,
      model,
      message_count: 0,
      is_pinned: false,
      pinned_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    currentSessionId.value = created.id
    return created
  }

  async function deleteSession(id: string) {
    if (!localSessionIds.value.has(id)) {
      await api.deleteSession(id)
    } else {
      localSessionIds.value.delete(id)
    }
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (currentSessionId.value === id) {
      currentSessionId.value = sessions.value[0]?.id || null
    }
  }

  async function updateTitle(id: string, title: string) {
    if (!localSessionIds.value.has(id)) {
      await api.updateSession(id, { title })
    }
    const sess = sessions.value.find(s => s.id === id)
    if (sess) sess.title = title
  }

  function updateTitleLocal(id: string, title: string) {
    const sess = sessions.value.find(s => s.id === id)
    if (sess) sess.title = title
  }

  async function refreshSessionTitle(id: string) {
    try {
      const allSessions = await api.getSessions()
      const fresh = allSessions.find((s: any) => s.id === id)
      if (fresh) {
        const sess = sessions.value.find(s => s.id === id)
        if (sess && fresh.title && fresh.title !== sess.title) {
          sess.title = fresh.title
        }
      }
    } catch { /* ignore */ }
  }

  async function updateModel(id: string, model: string) {
    const sess = sessions.value.find(s => s.id === id)
    if (sess) sess.model = model
    if (!localSessionIds.value.has(id)) {
      await api.updateSession(id, { model })
    }
  }

  function updateModelLocal(id: string, model: string) {
    const sess = sessions.value.find(s => s.id === id)
    if (sess) sess.model = model
  }

  async function setPinned(id: string, isPinned: boolean) {
    if (!localSessionIds.value.has(id)) {
      const updated = await api.updateSession(id, { is_pinned: isPinned })
      const idx = sessions.value.findIndex(s => s.id === id)
      if (idx >= 0) {
        sessions.value[idx] = { ...sessions.value[idx], ...updated }
      }
      return
    }

    const sess = sessions.value.find(s => s.id === id)
    if (sess) {
      sess.is_pinned = isPinned
      sess.pinned_at = isPinned ? new Date().toISOString() : null
    }
  }

  const groupedByAgent = computed(() => {
    const agentsStore = useAgentsStore()
    const groups: Record<string, { agentName: string; agentSource: string; sessions: Session[] }> = {}
    for (const s of sessions.value) {
      const key = s.agent_id || 'chat'
      if (!groups[key]) {
        const agent = agentsStore.agents.find(a => a.id === key)
        groups[key] = {
          agentName: agentsStore.getAgentName(key),
          agentSource: agent?.source || 'user',
          sessions: [],
        }
      }
      groups[key].sessions.push(s)
    }
    return Object.entries(groups).map(([agentId, data]) => ({
      agentId,
      agentName: data.agentName,
      agentSource: data.agentSource,
      sessions: data.sessions,
    }))
  })

  function selectSession(id: string) {
    sessionNavStack.value = []
    currentSessionId.value = id
  }

  return { sessions, currentSessionId, currentSession, sessionNavStack, effectiveThreadId, pushSubSession, popSubSession, popToRoot, groupedByAgent, init, createSession, createLocalSession, ensureLocalSession, persistSession, isLocalSession, deleteSession, updateTitle, updateTitleLocal, refreshSessionTitle, updateModel, updateModelLocal, setPinned, selectSession }
})

`````

--- **end of file: frontend/src/stores/sessions.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/stores/tools.ts** (project: lc_agent) --- 

`````typescript
import { defineStore } from 'pinia'
import { ref, computed, watch, reactive } from 'vue'
import { api } from '@/api/http'
import { useAgentsStore } from '@/stores/agents'
import { useSessionsStore } from '@/stores/sessions'

export interface ToolItem {
  name: string
  description: string
  input_schema?: any
}

export interface ToolGroup {
  id: string
  description: string
  tools: ToolItem[]
  enabled: boolean
}

export interface McpToolSchema {
  name: string
  description: string
  input_schema: any
}

export interface McpServer {
  name: string
  type: string
  command?: string
  url?: string
  enabled: boolean
  status: string
  tools: string[]
  tool_schemas?: McpToolSchema[]
  error?: string
}

export interface Skill {
  name: string
  description: string
  source?: string
  metadata?: Record<string, any>
  enabled: boolean
}

export interface ModelInfo {
  id: string
  provider: string
  base_url: string
  context_limit: number
}

export const useToolsStore = defineStore('tools', () => {
  const groups = ref<ToolGroup[]>([])
  const models = ref<ModelInfo[]>([])
  const mcpServers = ref<McpServer[]>([])
  const skills = ref<Skill[]>([])
  const currentModel = ref('')
  const llmParams = ref<Record<string, any> | null>(null)
  const mcpRefreshing = ref(false)

  const localOverrides = reactive<Record<string, boolean>>({})

  function _effectiveEnabled(key: string, serverEnabled: boolean): boolean {
    const agentsStore = useAgentsStore()
    const agent = agentsStore.currentAgent
    if (!agent) return serverEnabled
    if (key in localOverrides) return localOverrides[key]
    return agent.default_enabled ? serverEnabled : false
  }

  const filteredGroups = computed(() => {
    const agentsStore = useAgentsStore()
    const agent = agentsStore.currentAgent
    if (!agent) return groups.value
    const allowed = agent.allowed_tool_groups
    return groups.value.map(g => ({
      ...g,
      enabled: _effectiveEnabled(`group:${g.id}`, g.enabled) && (allowed === null || allowed.includes(g.id)),
      allowed: allowed === null || allowed.includes(g.id),
    }))
  })

  const filteredMcp = computed(() => {
    const agentsStore = useAgentsStore()
    const agent = agentsStore.currentAgent
    if (!agent) return mcpServers.value
    const allowed = agent.allowed_mcp_servers
    return mcpServers.value.map((s: any) => ({
      ...s,
      enabled: _effectiveEnabled(`mcp:${s.name}`, s.enabled) && (allowed === null || allowed.includes(s.name)),
      allowed: allowed === null || allowed.includes(s.name),
    }))
  })

  const filteredSkills = computed(() => {
    const agentsStore = useAgentsStore()
    const agent = agentsStore.currentAgent
    if (!agent) return skills.value
    const allowed = agent.allowed_skills
    return skills.value.map((s: any) => ({
      ...s,
      enabled: _effectiveEnabled(`skill:${s.name}`, s.enabled !== false) && (allowed === null || allowed.includes(s.name)),
      allowed: allowed === null || allowed.includes(s.name),
    }))
  })

  function syncModelWithAgentDefault() {
    const agentsStore = useAgentsStore()
    if (agentsStore.currentAgent?.source === 'code') {
      currentModel.value = ''
      return
    }
    const defaultModel = agentsStore.currentAgent?.default_model
    if (defaultModel && defaultModel !== 'custom') {
      currentModel.value = defaultModel
      return
    }
    if (models.value.length > 0 && !currentModel.value) {
      currentModel.value = models.value[0].id
    }
  }

  function _clearOverrides() {
    for (const key of Object.keys(localOverrides)) {
      delete localOverrides[key]
    }
  }

  function setLlmParam(key: string, value: any) {
    if (value === null || value === undefined || value === '') {
      if (llmParams.value) {
        delete llmParams.value[key]
        if (Object.keys(llmParams.value).length === 0) llmParams.value = null
      }
    } else {
      if (!llmParams.value) llmParams.value = {}
      llmParams.value[key] = value
    }
  }

  function resetLlmParams() {
    llmParams.value = null
  }

  async function refreshMcpServers() {
    mcpRefreshing.value = true
    try {
      mcpServers.value = await api.getMcpServers()
    } catch (e) {
      console.error('[ToolsStore] Failed to refresh MCP servers:', e)
    } finally {
      mcpRefreshing.value = false
    }
  }

  async function refreshRuntimeToggles() {
    try {
      const [groupsData, mcpData, skillsData] = await Promise.all([
        api.getToolGroups(),
        api.getMcpServers(),
        api.getSkills(),
      ])
      groups.value = groupsData
      mcpServers.value = mcpData
      skills.value = skillsData
    } catch (e) {
      console.error('[ToolsStore] Failed to refresh runtime toggles:', e)
    }
  }

  async function init() {
    try {
      const [groupsData, modelsData, mcpData, skillsData] = await Promise.all([
        api.getToolGroups(),
        api.getModels(),
        api.getMcpServers(),
        api.getSkills(),
      ])
      groups.value = groupsData
      models.value = modelsData
      mcpServers.value = mcpData
      skills.value = skillsData
      syncModelWithAgentDefault()

      const agentsStore = useAgentsStore()
      watch(() => agentsStore.currentAgentId, () => {
        _clearOverrides()
        syncModelWithAgentDefault()
        resetLlmParams()
        refreshRuntimeToggles()
      })
    } catch (e) {
      console.error('[ToolsStore] Failed to fetch:', e)
    }
  }

  async function toggleGroup(groupId: string) {
    const key = `group:${groupId}`
    const current = _effectiveEnabled(key, groups.value.find(g => g.id === groupId)?.enabled ?? true)
    localOverrides[key] = !current
    try {
      await api.toggleToolGroup(groupId)
      const group = groups.value.find(g => g.id === groupId)
      if (group) group.enabled = !group.enabled
    } catch (e) {
      localOverrides[key] = current
      console.error('[ToolsStore] Toggle group failed:', e)
    }
  }

  async function toggleMcp(serverName: string) {
    const key = `mcp:${serverName}`
    const server = mcpServers.value.find((s: any) => s.name === serverName)
    const current = _effectiveEnabled(key, server?.enabled ?? true)
    localOverrides[key] = !current
    try {
      const result = await api.toggleMcpServer(serverName)
      if (server) {
        server.enabled = !server.enabled
        server.status = result.enabled ? (server.status === 'disabled' ? 'disconnected' : server.status) : 'disabled'
      }
    } catch (e) {
      localOverrides[key] = current
      console.error('[ToolsStore] Toggle MCP failed:', e)
    }
  }

  async function toggleSkill(skillName: string) {
    const key = `skill:${skillName}`
    const skill = skills.value.find((s: any) => s.name === skillName)
    const current = _effectiveEnabled(key, skill?.enabled !== false)
    localOverrides[key] = !current
    try {
      await api.toggleSkill(skillName)
      if (skill) skill.enabled = !skill.enabled
    } catch (e) {
      localOverrides[key] = current
      console.error('[ToolsStore] Toggle skill failed:', e)
    }
  }

  function setModel(modelId: string) {
    currentModel.value = modelId
    const sessionsStore = useSessionsStore()
    const sessionId = sessionsStore.currentSessionId
    if (sessionId) {
      sessionsStore.updateModel(sessionId, modelId).catch((e) => {
        console.error('[ToolsStore] Failed to update session model:', e)
      })
    }
  }

  return {
    groups, models, mcpServers, skills, currentModel, llmParams, mcpRefreshing,
    filteredGroups, filteredMcp, filteredSkills,
    init, refreshMcpServers, refreshRuntimeToggles, toggleGroup, toggleMcp, toggleSkill,
    setModel, setLlmParam, resetLlmParams, syncModelWithAgentDefault,
  }
})

`````

--- **end of file: frontend/src/stores/tools.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/utils/client-id.ts** (project: lc_agent) --- 

`````typescript
function randomHex(bytes: Uint8Array): string {
  return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('')
}

function getCrypto(): Crypto {
  if (!globalThis.crypto?.getRandomValues) {
    throw new Error('crypto.getRandomValues is required to create client IDs')
  }

  return globalThis.crypto
}

export function createClientId(): string {
  const bytes = new Uint8Array(16)
  getCrypto().getRandomValues(bytes)
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80

  const hex = randomHex(bytes)
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

`````

--- **end of file: frontend/src/utils/client-id.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/utils/copy-markdown.ts** (project: lc_agent) --- 

`````typescript
import type { HttpTrace, LlmRoundUsage } from '@/stores/chat'
import type { ContentBlock } from '@/utils/fileUpload'

export interface CopyOptions {
  includeThinking?: boolean
  includeToolCalls?: boolean
  includeHttpTraces?: boolean
  modelName?: string
}

interface ToolCallLike {
  name: string
  args?: Record<string, any>
  result?: string
  status?: string
  duration?: number
  resultLength?: number
}

interface MessageLike {
  role: 'user' | 'assistant' | 'tool'
  content: string | ContentBlock[]
  toolCalls?: ToolCallLike[]
  httpTraces?: HttpTrace[]
  usage?: { rounds: LlmRoundUsage[] }
}

function contentToString(content: string | ContentBlock[]): string {
  if (typeof content === 'string') return content
  return content.find(b => b.type === 'text')?.text || ''
}

const THINK_START = '<!--THINK_START-->'
const THINK_END = '<!--THINK_END-->'
const TOOL_RE = /<!--TOOL:(\d+)-->/
const HTTP_RE = /<!--HTTP:(\d+)-->/

interface Segment {
  type: 'text' | 'thinking' | 'tool' | 'http'
  content: string
  toolIndex?: number
  httpIndex?: number
}

function parseSegments(content: string): Segment[] {
  const segments: Segment[] = []
  let remaining = content
  let inThinking = false

  while (remaining.length > 0) {
    if (!inThinking) {
      const thinkStart = remaining.indexOf(THINK_START)
      const toolMatch = TOOL_RE.exec(remaining)
      const httpMatch = HTTP_RE.exec(remaining)

      const nextThink = thinkStart >= 0 ? thinkStart : Infinity
      const nextTool = toolMatch ? toolMatch.index : Infinity
      const nextHttp = httpMatch ? httpMatch.index : Infinity

      if (nextThink === Infinity && nextTool === Infinity && nextHttp === Infinity) {
        const trimmed = remaining.trim()
        if (trimmed) segments.push({ type: 'text', content: trimmed })
        break
      }

      const nextMarker = Math.min(nextThink, nextTool, nextHttp)
      const before = remaining.slice(0, nextMarker).trim()
      if (before) segments.push({ type: 'text', content: before })

      if (nextThink <= nextTool && nextThink <= nextHttp) {
        remaining = remaining.slice(thinkStart + THINK_START.length)
        inThinking = true
      } else if (nextTool <= nextHttp) {
        const idx = parseInt(toolMatch![1], 10)
        segments.push({ type: 'tool', content: '', toolIndex: idx })
        remaining = remaining.slice(toolMatch!.index + toolMatch![0].length)
      } else {
        const idx = parseInt(httpMatch![1], 10)
        segments.push({ type: 'http', content: '', httpIndex: idx })
        remaining = remaining.slice(httpMatch!.index + httpMatch![0].length)
      }
    } else {
      const thinkEnd = remaining.indexOf(THINK_END)
      if (thinkEnd >= 0) {
        const thinking = remaining.slice(0, thinkEnd).trim()
        if (thinking) segments.push({ type: 'thinking', content: thinking })
        remaining = remaining.slice(thinkEnd + THINK_END.length)
        inThinking = false
      } else {
        const thinking = remaining.trim()
        if (thinking) segments.push({ type: 'thinking', content: thinking })
        break
      }
    }
  }
  return segments
}

function toolCallToMarkdown(tc: ToolCallLike): string {
  const lines: string[] = []
  const meta = tc.duration ? ` (${(tc.duration / 1000).toFixed(1)}s)` : ''
  lines.push(`<details><summary>🔧 工具调用: ${tc.name}${meta}</summary>`)
  lines.push('')

  if (tc.args && Object.keys(tc.args).length > 0) {
    lines.push('**参数:**')
    for (const [k, v] of Object.entries(tc.args)) {
      const val = typeof v === 'string' ? v : JSON.stringify(v)
      const display = val.length > 200 ? val.slice(0, 200) + '...' : val
      lines.push(`- \`${k}\`: \`${display}\``)
    }
    lines.push('')
  }

  if (tc.result) {
    lines.push('**结果:**')
    lines.push('```')
    lines.push(tc.result)
    lines.push('```')
    lines.push('')
  }

  lines.push('</details>')
  return lines.join('\n')
}

function fmtTokens(n: number | undefined): string {
  if (n == null || n === 0) return ''
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

function httpTraceToMarkdown(trace: HttpTrace, usageRound?: LlmRoundUsage): string {
  const method = trace.request.method || 'HTTP'
  const status = trace.error ? '❌ 失败' : `${trace.response.status ?? '?'}`
  const duration = trace.durationMs != null
    ? (trace.durationMs >= 1000 ? `${(trace.durationMs / 1000).toFixed(1)}s` : `${trace.durationMs}ms`)
    : '-'

  const tokenParts: string[] = []
  if (usageRound) {
    if (usageRound.inputTokens) tokenParts.push(`输入 ${fmtTokens(usageRound.inputTokens)}`)
    if (usageRound.cacheReadTokens) tokenParts.push(`缓存 ${fmtTokens(usageRound.cacheReadTokens)}`)
    if (usageRound.outputTokens) tokenParts.push(`输出 ${fmtTokens(usageRound.outputTokens)}`)
    if (usageRound.reasoningTokens) tokenParts.push(`推理 ${fmtTokens(usageRound.reasoningTokens)}`)
  }
  const tokenStr = tokenParts.length > 0 ? tokenParts.join(' ') : ''

  const model = [trace.provider, trace.model].filter(Boolean).join(' / ')
  const url = trace.request.url || '未采集'

  const lines: string[] = []
  lines.push('| 项目 | 值 |')
  lines.push('| :-- | :-- |')
  lines.push(`| 🌐 HTTP | **#${trace.sequence}** \`${method}\` **${status}** ${duration} |`)
  if (tokenStr) lines.push(`| Tokens | ${tokenStr} |`)
  lines.push(`| URL | \`${url}\` |`)
  if (model) lines.push(`| 模型 | ${model} |`)
  if (trace.error) lines.push(`| 错误 | ${trace.error} |`)

  return lines.join('\n')
}

export function singleMessageToMarkdown(
  msg: MessageLike,
  options?: CopyOptions,
): string {
  const opts = { includeThinking: true, includeToolCalls: true, includeHttpTraces: true, ...options }

  if (msg.role === 'user') {
    return `## User\n\n${contentToString(msg.content).trim()}`
  }

  const modelSuffix = opts.modelName ? ` (${opts.modelName})` : ''
  const lines: string[] = [`## Assistant${modelSuffix}`, '']
  const segments = parseSegments(contentToString(msg.content))

  for (const seg of segments) {
    if (seg.type === 'thinking' && opts.includeThinking) {
      lines.push('<details><summary>💭 思考过程</summary>')
      lines.push('')
      lines.push(seg.content)
      lines.push('')
      lines.push('</details>')
      lines.push('')
    } else if (seg.type === 'tool' && opts.includeToolCalls) {
      const tc = msg.toolCalls?.[seg.toolIndex!]
      if (tc) {
        lines.push(toolCallToMarkdown(tc))
        lines.push('')
      }
    } else if (seg.type === 'http' && opts.includeHttpTraces) {
      const trace = msg.httpTraces?.[seg.httpIndex!]
      if (trace) {
        const usageRound = msg.usage?.rounds?.[seg.httpIndex!]
        lines.push(httpTraceToMarkdown(trace, usageRound))
        lines.push('')
      }
    } else if (seg.type === 'text') {
      lines.push(seg.content)
      lines.push('')
    }
  }

  return lines.join('\n').trimEnd()
}

export function messagesToMarkdown(
  messages: MessageLike[],
  options?: CopyOptions,
): string {
  return messages
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .map(m => singleMessageToMarkdown(m, options))
    .join('\n\n---\n\n')
}

export function extractThinking(msg: MessageLike): string {
  return parseSegments(contentToString(msg.content))
    .filter(s => s.type === 'thinking')
    .map(s => s.content)
    .join('\n\n')
}

export function extractToolCalls(msg: MessageLike): string {
  const segments = parseSegments(contentToString(msg.content))
  return segments
    .filter(s => s.type === 'tool')
    .map(s => {
      const tc = msg.toolCalls?.[s.toolIndex!]
      return tc ? toolCallToMarkdown(tc) : ''
    })
    .filter(Boolean)
    .join('\n\n')
}

export function extractAnswer(msg: MessageLike): string {
  return parseSegments(contentToString(msg.content))
    .filter(s => s.type === 'text')
    .map(s => s.content)
    .join('\n\n')
}

export function getRounds(messages: MessageLike[]): MessageLike[][] {
  const rounds: MessageLike[][] = []
  let current: MessageLike[] = []

  for (const msg of messages) {
    if (msg.role === 'user') {
      if (current.length > 0) rounds.push(current)
      current = [msg]
    } else if (msg.role === 'assistant') {
      current.push(msg)
    }
  }
  if (current.length > 0) rounds.push(current)
  return rounds
}

export function copyRecentRounds(
  messages: MessageLike[],
  n: number,
  options?: CopyOptions,
): string {
  const rounds = getRounds(messages)
  const recent = rounds.slice(-n)
  return recent
    .map(round => round.map(m => singleMessageToMarkdown(m, options)).join('\n\n'))
    .join('\n\n---\n\n')
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(textarea)
    return ok
  }
}

`````

--- **end of file: frontend/src/utils/copy-markdown.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/utils/fileUpload.ts** (project: lc_agent) --- 

`````typescript
/**
 * 附件处理工具：图片压缩、文本文件读取、content blocks 构造
 */

export interface ContentBlock {
  type: 'text' | 'image_url'
  text?: string
  image_url?: { url: string }
}

export interface Attachment {
  id: string
  type: 'image' | 'text_file'
  name: string
  // image 专属
  dataUrl?: string
  // text_file 专属
  textContent?: string
}

/** 支持的文本文件扩展名白名单 */
export const TEXT_EXTENSIONS = [
  'txt', 'md', 'markdown', 'json', 'yaml', 'yml', 'csv', 'log', 'xml', 'html', 'htm',
  'js', 'ts', 'jsx', 'tsx', 'py', 'go', 'rs', 'java', 'c', 'cpp', 'h', 'hpp', 'sh', 'sql',
  'css', 'scss', 'less', 'vue', 'toml', 'ini', 'conf',
]

/** 扩展名到代码块语言的映射 */
const EXT_TO_LANG: Record<string, string> = {
  js: 'javascript', ts: 'typescript', jsx: 'jsx', tsx: 'tsx',
  py: 'python', go: 'go', rs: 'rust', java: 'java',
  c: 'c', cpp: 'cpp', h: 'c', hpp: 'cpp',
  sh: 'bash', sql: 'sql', css: 'css', scss: 'scss',
  less: 'less', vue: 'vue', html: 'html', htm: 'html',
  xml: 'xml', json: 'json', yaml: 'yaml', yml: 'yaml',
  toml: 'toml', ini: 'ini', conf: 'ini',
  md: 'markdown', markdown: 'markdown',
}

/** 图片上限（软提示） */
export const MAX_IMAGE_COUNT = 9

/** 图片压缩最长边 */
const MAX_IMAGE_EDGE = 1280

/** 生成简单 uuid */
function genId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

/** 获取文件扩展名（小写，无点） */
export function getExtension(filename: string): string {
  const parts = filename.split('.')
  return parts.length > 1 ? parts.pop()!.toLowerCase() : ''
}

/** 判断文件是否为图片 */
export function isImageFile(file: File): boolean {
  return file.type.startsWith('image/')
}

/** 判断文件是否为白名单文本文件 */
export function isTextFile(file: File): boolean {
  const ext = getExtension(file.name)
  return TEXT_EXTENSIONS.includes(ext)
}

/** 压缩图片：最长边 1280，保留原格式 */
export async function compressImage(file: File): Promise<string> {
  const bitmap = await createImageBitmap(file)
  let { width, height } = bitmap
  if (width > MAX_IMAGE_EDGE || height > MAX_IMAGE_EDGE) {
    const ratio = Math.min(MAX_IMAGE_EDGE / width, MAX_IMAGE_EDGE / height)
    width = Math.round(width * ratio)
    height = Math.round(height * ratio)
  }
  const canvas = new OffscreenCanvas(width, height)
  const ctx = canvas.getContext('bitmaprenderer')
  if (!ctx) throw new Error('Canvas 2D context unavailable')
  ctx.transferFromImageBitmap(bitmap)
  // 保留原格式：png 输出 png，jpeg 输出 jpeg
  const blob = await canvas.convertToBlob({ type: file.type, quality: 0.8 })
  return await blobToDataURL(blob)
}

function blobToDataURL(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error('Failed to read blob as data URL'))
    reader.readAsDataURL(blob)
  })
}

/** 读取文本文件内容 */
export function readTextFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error(`Failed to read ${file.name}`))
    reader.readAsText(file, 'utf-8')
  })
}

/** 把 File 转为 Attachment */
export async function fileToAttachment(file: File): Promise<Attachment | null> {
  if (isImageFile(file)) {
    try {
      const dataUrl = await compressImage(file)
      return {
        id: genId(),
        type: 'image',
        name: file.name || `image-${Date.now()}.png`,
        dataUrl,
      }
    } catch (e) {
      console.error('Image compression failed:', e)
      return null
    }
  }
  if (isTextFile(file)) {
    try {
      const textContent = await readTextFile(file)
      return {
        id: genId(),
        type: 'text_file',
        name: file.name,
        textContent,
      }
    } catch (e) {
      console.error('Text file read failed:', e)
      return null
    }
  }
  return null
}

/** 批量处理文件 */
export async function filesToAttachments(files: File[]): Promise<{ attachments: Attachment[]; rejected: string[] }> {
  const attachments: Attachment[] = []
  const rejected: string[] = []
  for (const file of files) {
    const att = await fileToAttachment(file)
    if (att) {
      attachments.push(att)
    } else {
      rejected.push(file.name)
    }
  }
  return { attachments, rejected }
}

/** 从剪贴板 items 提取图片文件（只取图片，忽略文本） */
export function imageFilesFromClipboard(items: DataTransferItemList): File[] {
  const files: File[] = []
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.kind === 'file' && item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) files.push(file)
    }
  }
  return files
}

/** 构造 content blocks list */
export function buildContentBlocks(text: string, attachments: Attachment[]): ContentBlock[] {
  const blocks: ContentBlock[] = []
  const trimmed = text.trim()
  if (trimmed) {
    blocks.push({ type: 'text', text: trimmed })
  }
  for (const att of attachments) {
    if (att.type === 'image' && att.dataUrl) {
      blocks.push({ type: 'image_url', image_url: { url: att.dataUrl } })
    } else if (att.type === 'text_file' && att.textContent !== undefined) {
      const ext = getExtension(att.name)
      const lang = EXT_TO_LANG[ext] || ''
      blocks.push({
        type: 'text',
        text: `📎 \`${att.name}\`:\n\`\`\`${lang}\n${att.textContent}\n\`\`\``,
      })
    }
  }
  return blocks
}

/** 统计图片数量 */
export function countImages(attachments: Attachment[]): number {
  return attachments.filter(a => a.type === 'image').length
}

`````

--- **end of file: frontend/src/utils/fileUpload.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/utils/markdown.ts** (project: lc_agent) --- 

`````typescript
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

function escapeAttr(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function normalizeLanguage(lang: string): string {
  return lang.trim().split(/\s+/)[0]?.toLowerCase() || ''
}

function renderCodeBlock(source: string, lang: string): string {
  const language = normalizeLanguage(lang)
  const knownLanguage = language && hljs.getLanguage(language)
  const highlighted = knownLanguage
    ? hljs.highlight(source, { language }).value
    : md.utils.escapeHtml(source)
  const label = language || 'text'
  const languageClass = language ? ` language-${escapeAttr(language)}` : ''
  const encodedSource = escapeAttr(encodeURIComponent(source))

  return [
    `<div class="markdown-code-block" data-language="${escapeAttr(label)}">`,
    '<div class="markdown-code-toolbar">',
    '<span class="markdown-code-window" aria-hidden="true"><i></i><i></i><i></i></span>',
    `<span class="markdown-code-language">${escapeAttr(label)}</span>`,
    `<button class="markdown-code-expand" type="button" data-code="${encodedSource}" data-lang="${escapeAttr(label)}" aria-label="展开源码">⛶</button>`,
    `<button class="markdown-code-copy" type="button" data-code="${encodedSource}" aria-label="复制代码">复制</button>`,
    '</div>',
    `<pre class="hljs"><code class="hljs${languageClass}">${highlighted}</code></pre>`,
    '</div>',
  ].join('')
}

const md: MarkdownIt = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  highlight(str: string, lang: string): string {
    try {
      return renderCodeBlock(str, lang)
    } catch {
      return renderCodeBlock(str, '')
    }
  },
})

export function renderMarkdown(text: string): string {
  return md.render(text)
}

`````

--- **end of file: frontend/src/utils/markdown.ts** (project: lc_agent) --- 

---


--- **start of file: frontend/src/views/AdminView.vue** (project: lc_agent) --- 

`````vue
<template>
  <div class="admin-page">
    <el-card shadow="never">
      <template #header>
        <div class="admin-header">
          <h2>用户管理</h2>
          <div class="admin-actions">
            <el-button @click="router.push('/')">返回首页</el-button>
            <el-button type="primary" @click="openCreateDialog">创建用户</el-button>
          </div>
        </div>
      </template>

      <el-table v-loading="loading" :data="users" stripe style="width: 100%">
        <el-table-column prop="username" label="用户名" min-width="140" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
              {{ row.role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openAgentsDialog(row)">Agent 授权</el-button>
            <el-button size="small" type="warning" @click="handleResetPassword(row)">重置密码</el-button>
            <el-button
              size="small"
              type="danger"
              :disabled="row.role === 'admin'"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create user dialog -->
    <el-dialog v-model="createVisible" title="创建用户" width="420px" :close-on-click-modal="false">
      <el-form @submit.prevent="handleCreate">
        <el-form-item label="用户名">
          <el-input v-model="newUsername" placeholder="输入用户名" autocomplete="off" />
        </el-form-item>
      </el-form>
      <el-alert v-if="createError" :title="createError" type="error" show-icon :closable="false" style="margin-bottom: 12px" />
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- Generated password dialog -->
    <el-dialog v-model="passwordVisible" title="生成的密码" width="420px" :close-on-click-modal="false">
      <p class="password-hint">请妥善保存以下密码，关闭后将无法再次查看：</p>
      <el-input :model-value="generatedPassword" readonly>
        <template #append>
          <el-button @click="copyPassword">复制</el-button>
        </template>
      </el-input>
      <template #footer>
        <el-button type="primary" @click="passwordVisible = false">已保存</el-button>
      </template>
    </el-dialog>

    <!-- Agent authorization dialog -->
    <el-dialog
      v-model="agentsVisible"
      :title="`Agent 授权 — ${selectedUser?.username || ''}`"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-checkbox-group v-model="selectedAgentIds" class="agent-checkboxes">
        <el-checkbox v-for="agent in agents" :key="agent.id" :value="agent.id" :label="agent.id">
          {{ agent.display_name || agent.name }}
          <el-tag size="small" style="margin-left: 6px">{{ agent.source || 'user' }}</el-tag>
        </el-checkbox>
      </el-checkbox-group>
      <el-alert v-if="agentsError" :title="agentsError" type="error" show-icon :closable="false" style="margin-top: 12px" />
      <template #footer>
        <el-button @click="agentsVisible = false">取消</el-button>
        <el-button type="primary" :loading="agentsLoading" @click="handleSaveAgents">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchApi, api } from '@/api/http'

interface AdminUser {
  id: string
  username: string
  role: string
  created_at: string
}

interface AgentItem {
  id: string
  name: string
  display_name?: string | null
  source?: string
}

const router = useRouter()
const users = ref<AdminUser[]>([])
const agents = ref<AgentItem[]>([])
const loading = ref(false)

const createVisible = ref(false)
const createLoading = ref(false)
const createError = ref('')
const newUsername = ref('')

const passwordVisible = ref(false)
const generatedPassword = ref('')

const agentsVisible = ref(false)
const agentsLoading = ref(false)
const agentsError = ref('')
const selectedUser = ref<AdminUser | null>(null)
const selectedAgentIds = ref<string[]>([])

onMounted(async () => {
  await Promise.all([loadUsers(), loadAgents()])
})

async function loadUsers() {
  loading.value = true
  try {
    users.value = await fetchApi<AdminUser[]>('/admin/users')
  } catch (e: any) {
    ElMessage.error(e.message || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

async function loadAgents() {
  try {
    agents.value = await api.getAgents()
  } catch (e: any) {
    ElMessage.error(e.message || '加载 Agent 列表失败')
  }
}

function formatDate(iso: string): string {
  if (!iso) return '-'
  try {
    return new Date(iso).toLocaleString('zh-CN')
  } catch {
    return iso
  }
}

function openCreateDialog() {
  newUsername.value = ''
  createError.value = ''
  createVisible.value = true
}

async function handleCreate() {
  const username = newUsername.value.trim()
  if (!username) {
    createError.value = '请输入用户名'
    return
  }

  createLoading.value = true
  createError.value = ''
  try {
    const result = await fetchApi<{ password: string }>('/admin/users', {
      method: 'POST',
      body: JSON.stringify({ username }),
    })
    createVisible.value = false
    generatedPassword.value = result.password
    passwordVisible.value = true
    await loadUsers()
    ElMessage.success('用户创建成功')
  } catch (e: any) {
    createError.value = e.message || '创建失败'
  } finally {
    createLoading.value = false
  }
}

async function handleDelete(user: AdminUser) {
  try {
    await ElMessageBox.confirm(`确定删除用户「${user.username}」？`, '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await fetchApi<void>(`/admin/users/${user.id}`, { method: 'DELETE' })
    ElMessage.success('用户已删除')
    await loadUsers()
  } catch (e: any) {
    if (e !== 'cancel' && e?.message !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

async function handleResetPassword(user: AdminUser) {
  try {
    await ElMessageBox.confirm(`确定重置用户「${user.username}」的密码？`, '确认重置', {
      type: 'warning',
      confirmButtonText: '重置',
      cancelButtonText: '取消',
    })
    const result = await fetchApi<{ password: string }>(`/admin/users/${user.id}/reset-password`, {
      method: 'PUT',
    })
    generatedPassword.value = result.password
    passwordVisible.value = true
  } catch (e: any) {
    if (e !== 'cancel' && e?.message !== 'cancel') {
      ElMessage.error(e.message || '重置失败')
    }
  }
}

async function openAgentsDialog(user: AdminUser) {
  selectedUser.value = user
  agentsError.value = ''
  agentsVisible.value = true
  agentsLoading.value = true
  try {
    const result = await fetchApi<{ agent_ids: string[] }>(`/admin/users/${user.id}/agents`)
    selectedAgentIds.value = result.agent_ids
  } catch (e: any) {
    agentsError.value = e.message || '加载授权失败'
    selectedAgentIds.value = []
  } finally {
    agentsLoading.value = false
  }
}

async function handleSaveAgents() {
  if (!selectedUser.value) return

  agentsLoading.value = true
  agentsError.value = ''
  try {
    await fetchApi(`/admin/users/${selectedUser.value.id}/agents`, {
      method: 'PUT',
      body: JSON.stringify({ agent_ids: selectedAgentIds.value }),
    })
    ElMessage.success('Agent 授权已保存')
    agentsVisible.value = false
  } catch (e: any) {
    agentsError.value = e.message || '保存失败'
  } finally {
    agentsLoading.value = false
  }
}

function copyPassword() {
  navigator.clipboard.writeText(generatedPassword.value).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.warning('复制失败，请手动复制')
  })
}
</script>

<style scoped>
.admin-page {
  padding: 20px;
  overflow: auto;
  height: 100%;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.admin-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.admin-actions {
  display: flex;
  gap: 8px;
}

.password-hint {
  margin: 0 0 12px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.agent-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  overflow-y: auto;
}
</style>

`````

--- **end of file: frontend/src/views/AdminView.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/views/ChatView.vue** (project: lc_agent) --- 

`````vue
<template>
  <div class="chat-view">
    <div
      v-if="sessionsStore.sessionNavStack.length > 0"
      class="subagent-breadcrumb"
    >
      <button class="breadcrumb-back" @click="sessionsStore.popSubSession()">
        ← 返回
      </button>
      <span
        class="breadcrumb-home"
        @click="sessionsStore.popToRoot()"
      >
        主对话
      </span>
      <template
        v-for="(nav, i) in sessionsStore.sessionNavStack"
        :key="i"
      >
        <span class="breadcrumb-sep"> / </span>
        <span class="breadcrumb-item" :class="{ 'breadcrumb-active': i === sessionsStore.sessionNavStack.length - 1 }">
          {{ nav.label }}
        </span>
      </template>
    </div>
    <div ref="messagesContainerRef" class="messages-container">
      <Welcome
        v-if="messages.length === 0 && !isLoading"
        title="Start a conversation"
        description="Ask me anything"
        variant="borderless"
      />
      <template v-else>
        <BubbleList
          :list="bubbleList"
          max-height="100%"
          :auto-scroll="isStreaming"
          :virtual="false"
        >
        <template #item="{ item }">
          <div
            v-if="item.itemType === 'load-older'"
            class="load-older-messages is-inline"
          >
            <el-button
              :loading="loadingOlder"
              size="small"
              text
              @click="handleLoadOlderMessages"
            >
              {{ loadingOlder ? '加载中...' : '加载更早的消息' }}
            </el-button>
          </div>
        </template>
        <template #avatar="{ item }">
          <div
            v-if="item.isSystem"
            class="role-avatar is-system"
            title="委托任务"
            aria-label="委托任务"
          >
            <span class="system-avatar-icon">📋</span>
          </div>
          <div
            v-else
            class="role-avatar"
            :class="item.role === 'user' ? 'is-user' : 'is-ai'"
            :title="item.role === 'user' ? '你' : getAssistantLabel()"
            :aria-label="item.role === 'user' ? '你' : getAssistantLabel()"
          >
            <el-icon>
              <User v-if="item.role === 'user'" />
              <Cpu v-else />
            </el-icon>
          </div>
        </template>
        <template #header="{ item }">
          <div v-if="item.isSystem" class="role-header is-system">
            <span class="role-name">委托任务</span>
          </div>
          <div v-else-if="item.role === 'user'" class="role-header is-user">
            <button
              v-if="canEditMessage(item)"
              class="message-edit-btn"
              type="button"
              title="编辑并重新发送"
              @click.stop="startEditMessage(item)"
            >
              编辑
            </button>
          </div>
          <div v-else class="role-header is-ai">
            <span class="role-header-icon" aria-hidden="true">
              <el-icon><Cpu /></el-icon>
            </span>
            <span class="role-name">{{ getAssistantLabel() }}</span>
            <span class="role-model">{{ getModelLabel() }}</span>
          </div>
        </template>
        <template #content="{ item }">
          <div class="bubble-content-wrap" :class="{ 'is-system-delegation': item.isSystem }">
            <div v-if="item.isSystem" class="system-delegation-msg">
              <div class="markdown-body" v-html="renderMarkdown(item.content || '')" />
            </div>
            <template v-else-if="item.segments && item.segments.length > 0">
              <template v-for="(seg, segIdx) in item.segments" :key="segIdx">
                <div
                  v-if="seg.type === 'text' && seg.text"
                  class="markdown-body"
                  v-html="renderMarkdown(seg.text)"
                />
                <details
                  v-else-if="seg.type === 'thinking' && seg.text"
                  class="thinking-block"
                  :open="isThinkingExpanded(item)"
                >
                  <summary class="thinking-summary">
                    <el-icon><Cpu /></el-icon>
                    <span>思考过程</span>
                  </summary>
                  <div class="markdown-body thinking-body" v-html="renderMarkdown(seg.text)" />
                </details>
                <div v-else-if="seg.type === 'tool' && item.toolCalls && seg.toolIndex != null" class="tool-call-inline">
                  <TodoProgressCard
                    v-if="item.toolCalls[seg.toolIndex!]?.name === 'write_todos'"
                    :tool-call="item.toolCalls[seg.toolIndex!]"
                  />
                  <SubAgentCard
                    v-else-if="item.toolCalls[seg.toolIndex!]?.is_subagent"
                    :entry="getSubAgentEntry(item, seg.toolIndex!) || makeFallbackSubAgentEntry(item, seg.toolIndex!)"
                    @enter="handleEnterSubAgent"
                  />
                  <ToolCallCard
                    v-else
                    :tool-call="item.toolCalls[seg.toolIndex!]"
                    :collapsed="item.toolCalls[seg.toolIndex!]?.status === 'done'"
                  />
                </div>
              </template>
              <HttpTracesGroup
                v-if="item.httpTraces?.length || item.httpTracesCount"
                :traces="item.httpTraces"
                :traces-count="item.httpTracesCount"
                :session-id="sessionsStore.effectiveThreadId || undefined"
                :message-id="item.messageId"
                :rounds="item.usage?.rounds"
              />
            </template>
            <template v-else>
              <div v-if="item.role === 'user' && item.contentBlocks" class="user-content-blocks">
                <template v-for="(block, i) in item.contentBlocks" :key="i">
                  <span v-if="block.type === 'text'" class="user-text-block">{{ block.text }}</span>
                  <img
                    v-else-if="block.type === 'image_url' && block.image_url"
                    :src="block.image_url.url"
                    class="user-image-block"
                    @click="previewImage(block.image_url.url)"
                  />
                </template>
              </div>
              <span v-else-if="item.role === 'user'" class="user-plain-text">{{ item.content }}</span>
              <div
                v-else
                class="markdown-body"
                v-html="renderMarkdown(stripThinkingMarkers(item.content || ''))"
              />
            </template>
            <div
              v-if="!item.isSystem && shouldShowReasoningNotice(item)"
              class="thinking-unavailable"
            >
              <el-icon><Cpu /></el-icon>
              <div class="thinking-unavailable-text">
                <strong>模型进行了内部推理</strong>
                <span>
                  本轮消耗 {{ formatCompactTokens(getReasoningTokenTotal(item.usage)) }} reasoning tokens，
                  但供应商没有返回可展示的思考文字。
                </span>
              </div>
            </div>
            <MessageToolbar
              v-if="!item.isSystem && getOriginalMessage(item.messageId) && !item.loading"
              :message="getOriginalMessage(item.messageId)!"
              :model-name="sessionModel"
              :has-thinking="item.hasThinking"
              :has-tool-calls="item.hasToolCalls"
              :has-answer="item.hasAnswer"
            />
            <TokenUsagePanel
              v-if="item.usage"
              :usage="item.usage"
              :tool-calls="item.toolCalls"
            />
          </div>
        </template>
      </BubbleList>
      </template>
      <Thinking
        v-if="isLoading && !isStreaming && !errorMessage"
        status="thinking"
        content=""
      />
    </div>

    <div v-if="sessionsStore.sessionNavStack.length > 0" class="subagent-readonly-bar">
      <span class="subagent-readonly-icon">👁</span>
      <span>子 Agent 查看模式 — 如需停止或继续输入，请返回主对话</span>
      <button class="subagent-readonly-back" @click="sessionsStore.popToRoot()">返回主对话</button>
    </div>
    <ChatInput
      v-else
      :is-streaming="isStreaming"
      :edit-content="editingContent"
      :edit-attachments="editingAttachments"
      :is-editing="Boolean(editingMessageId)"
      @send="handleSend"
      @stop="handleStop"
      @cancel-edit="cancelEdit"
    />

    <InterruptDialog
      :interrupt="interrupt"
      @decide="handleInterruptDecide"
      @resume="handleInterruptResume"
      @allow-permanently="handleAllowPermanently"
    />

    <CodeBlockModal
      :visible="codeModalVisible"
      :code="codeModalSource"
      :language="codeModalLanguage"
      @close="codeModalVisible = false"
    />

    <el-image-viewer
      v-if="imageViewerVisible"
      :url-list="[imageViewerUrl]"
      @close="imageViewerVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
// Workaround: avoid '<!--' directly in string literals (Rolldown WASM parser bug with HTML comment-like strings)
const C = '\x3c!--'  // '<' + '!--' = '<!--'
const THINK_START = `${C}THINK_START-->`
const THINK_END = `${C}THINK_END-->`
const HTTP_MARKER = `${C}HTTP:`
const TOOL_MARKER = `${C}TOOL:`

import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { BubbleList, Thinking, Welcome } from 'vue-element-plus-x'
import type { BubbleListItemProps } from 'vue-element-plus-x/types/BubbleList'
import { Cpu, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import { useSessionsStore } from '@/stores/sessions'
import type { ToolCall, MessageUsage, ReplayMessage, HttpTrace, ErrorInfo, SubAgentEntry } from '@/stores/chat'
import type { ContentBlock, Attachment } from '@/utils/fileUpload'
import { useAgentsStore } from '@/stores/agents'
import { useToolsStore } from '@/stores/tools'
import { renderMarkdown } from '@/utils/markdown'
import ChatInput from '@/components/chat/ChatInput.vue'
import InterruptDialog from '@/components/chat/InterruptDialog.vue'
import ToolCallCard from '@/components/chat/ToolCallCard.vue'
import SubAgentCard from '@/components/chat/SubAgentCard.vue'
import TodoProgressCard from '@/components/chat/TodoProgressCard.vue'
import HttpTracesGroup from '@/components/chat/HttpTracesGroup.vue'
import TokenUsagePanel from '@/components/chat/TokenUsagePanel.vue'
import MessageToolbar from '@/components/chat/MessageToolbar.vue'
import CodeBlockModal from '@/components/chat/CodeBlockModal.vue'

const LOAD_OLDER_REVEAL_THRESHOLD = 24

interface ContentSegment {
  type: 'text' | 'thinking' | 'tool' | 'http'
  text?: string
  toolIndex?: number
  httpIndex?: number
}

type MessageBubbleItem = BubbleListItemProps & {
  role: 'user' | 'ai'
  messageId: string
  content: string
  contentBlocks?: ContentBlock[]
  isMarkdown?: boolean
  isSystem?: boolean
  toolCalls?: ToolCall[]
  segments?: ContentSegment[]
  usage?: MessageUsage
  hasThinking?: boolean
  hasToolCalls?: boolean
  hasAnswer?: boolean
  httpTraces?: HttpTrace[]
  httpTracesCount?: number
  isStreamingMessage?: boolean
}

type LoadOlderBubbleItem = BubbleListItemProps & {
  key: string
  type: 'load-older'
  itemType: 'load-older'
  role: 'ai'
  messageId: string
  content: string
  isMarkdown?: boolean
  isSystem?: boolean
  toolCalls?: ToolCall[]
  segments?: ContentSegment[]
  usage?: MessageUsage
  hasThinking?: boolean
  hasToolCalls?: boolean
  hasAnswer?: boolean
  httpTraces?: HttpTrace[]
  httpTracesCount?: number
  isStreamingMessage?: boolean
}

type ChatBubbleItem = MessageBubbleItem | LoadOlderBubbleItem

const chatStore = useChatStore()
const sessionsStore = useSessionsStore()
const agentsStore = useAgentsStore()
const toolsStore = useToolsStore()
const { messages, isStreaming, interrupt, errorMessage, hasOlderMessages, loadingOlder } = storeToRefs(chatStore)
const editingMessageId = ref<string | null>(null)
const editingContent = ref('')
const editingAttachments = ref<Attachment[]>([])
const messagesContainerRef = ref<HTMLElement | null>(null)
const showLoadOlderMessages = ref(false)
const codeModalVisible = ref(false)
const codeModalSource = ref('')
const codeModalLanguage = ref('')
const imageViewerVisible = ref(false)
const imageViewerUrl = ref('')

// Sub-session live mode: when navigating into a sub-session while streaming,
// we stay connected to the main SSE and render from SubAgentEntry in the store.
const subLiveToolCallId = ref<string | null>(null)

const subLiveEntry = computed((): SubAgentEntry | null => {
  if (!subLiveToolCallId.value) return null
  for (const msg of messages.value) {
    const entry = msg.subAgents?.[subLiveToolCallId.value]
    if (entry) return entry
  }
  return null
})

const subLiveBubbleList = computed((): ChatBubbleItem[] => {
  const entry = subLiveEntry.value
  if (!entry) return []
  const items: ChatBubbleItem[] = []

  // User message: the delegation query
  if (entry.query) {
    items.push({
      key: 'sub-query',
      messageId: 'sub-query',
      role: 'user',
      placement: 'end',
      content: entry.query,
      shape: 'corner',
      variant: 'outlined',
      isMarkdown: false,
      isSystem: false,
      hasThinking: false,
      hasToolCalls: false,
      hasAnswer: true,
      isStreamingMessage: false,
      loading: false,
      avatarSize: '28px',
      avatarGap: '8px',
    })
  }

  // Build assistant content with embedded markers
  let content = ''
  if (entry.thinking?.trim()) {
    content += `<!--THINK_START-->${entry.thinking}<!--THINK_END-->`
  }
  const toolCalls: ToolCall[] = entry.innerToolCalls.map((tc, i) => {
    content += `\n<!--TOOL:${i}-->\n`
    return {
      name: tc.name,
      runId: `sub-tc-${i}`,
      args: (typeof tc.args === 'object' && tc.args !== null) ? tc.args as Record<string, unknown> : {},
      result: tc.result,
      status: tc.status as ToolCall['status'],
      startTime: undefined,
      duration: undefined,
      resultLength: tc.result?.length,
    }
  })
  if (entry.tokens) {
    content += entry.tokens
  }

  const streamingNow = entry.status === 'running'
  const hasContent = !!(entry.thinking?.trim() || toolCalls.length || entry.tokens)
  const segs = hasStructuredSegments(content, toolCalls) ? parseSegments(content, toolCalls) : undefined

  items.push({
    key: 'sub-response',
    messageId: 'sub-response',
    role: 'ai',
    placement: 'start',
    content: streamingNow && entry.tokens ? content + '▋' : content,
    shape: 'corner',
    variant: 'filled',
    isMarkdown: true,
    isSystem: false,
    isStreamingMessage: streamingNow,
    loading: streamingNow && !hasContent,
    toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
    segments: segs,
    hasThinking: !!entry.thinking?.trim(),
    hasToolCalls: toolCalls.length > 0,
    hasAnswer: !!entry.tokens?.trim(),
    avatarSize: '28px',
    avatarGap: '8px',
    httpTraces: entry.httpTraces?.length ? entry.httpTraces : undefined,
    httpTracesCount: entry.httpTraces?.length || 0,
  })

  return items
})

const isLoading = computed(() => {
  const msgs = messages.value
  if (msgs.length === 0) return false
  const last = msgs[msgs.length - 1]
  return last.role === 'user' && !isStreaming.value
})

function createLoadOlderItem(): LoadOlderBubbleItem {
  return {
    key: 'load-older-messages',
    type: 'load-older',
    itemType: 'load-older',
    role: 'ai',
    messageId: '__load_older_messages__',
    content: '加载更早的消息',
  }
}

const bubbleList = computed((): ChatBubbleItem[] => {
  // When in live sub-session mode, render from SubAgentEntry without touching main SSE
  if (subLiveToolCallId.value !== null) return subLiveBubbleList.value

  const items = messages.value
    .filter(msg => msg.role === 'user' || msg.role === 'assistant')
    .map((msg, idx, arr): MessageBubbleItem => {
      const msgContent = typeof msg.content === 'string'
        ? msg.content
        : msg.content.find(b => b.type === 'text')?.text || ''
      const segs = msg.role === 'assistant' && hasStructuredSegments(msgContent, msg.toolCalls)
        ? parseSegments(msgContent, msg.toolCalls)
        : undefined
      const isStreamingMessage =
        msg.role === 'assistant'
        && idx === arr.length - 1
        && isStreaming.value
      return {
        key: msg.id,
        messageId: msg.id,
        role: msg.role === 'assistant' ? 'ai' : 'user',
        placement: msg.role === 'user' ? 'end' : 'start',
        content: msgContent,
        contentBlocks: msg.role === 'user' && Array.isArray(msg.content) ? msg.content : undefined,
        shape: 'corner' as const,
        variant: (msg.role === 'user' ? 'outlined' : 'filled') as 'outlined' | 'filled',
        isMarkdown: msg.role !== 'user' && !msg.isSystem,
        isSystem: msg.isSystem,
        toolCalls: msg.toolCalls,
        usage: msg.usage,
        segments: segs,
        httpTraces: msg.role === 'assistant' ? msg.httpTraces : undefined,
        httpTracesCount: msg.role === 'assistant' ? (msg.httpTracesCount || 0) : 0,
        hasThinking: segs?.some(s => s.type === 'thinking' && s.text?.trim()) ?? false,
        hasToolCalls: segs?.some(s => s.type === 'tool') ?? false,
        hasAnswer: segs?.some(s => s.type === 'text' && s.text?.trim()) ?? false,
        isStreamingMessage,
        loading:
          isStreamingMessage
          && !msgContent,
        avatarSize: '28px',
        avatarGap: '8px',
      }
    })

  if (hasOlderMessages.value) items.unshift(createLoadOlderItem())
  return items
})

const lastUserMessage = computed(() =>
  [...messages.value].reverse().find(msg => msg.role === 'user'),
)

const sessionModel = computed(() => getModelLabel())

function getOriginalMessage(messageId: string) {
  return messages.value.find(m => m.id === messageId)
}

function getSubAgentEntry(item: ChatBubbleItem, toolIndex: number): SubAgentEntry | undefined {
  const msg = getOriginalMessage(item.messageId)
  const tc = item.toolCalls?.[toolIndex]
  if (!msg?.subAgents || !tc?.runId) return undefined
  return msg.subAgents[tc.runId]
}

function makeFallbackSubAgentEntry(item: ChatBubbleItem, toolIndex: number): SubAgentEntry {
  const tc = item.toolCalls?.[toolIndex]
  return {
    tool_call_id: tc?.runId || '',
    name: tc?.name || '子Agent',
    sub_session_id: tc?.sub_session_id || '',
    query: typeof tc?.args === 'object' ? String((tc.args as Record<string, unknown>)?.query || (tc.args as Record<string, unknown>)?.description || '') : '',
    status: (tc?.status === 'done'
      ? 'done'
      : tc?.status === 'error'
        ? 'error'
        : tc?.status === 'cancelled'
          ? 'cancelled'
          : tc?.status === 'interrupted'
            ? 'interrupted'
            : 'running') as 'running' | 'done' | 'error' | 'cancelled' | 'interrupted',
    tokenPreview: tc?.result || '',
    toolCallCount: 0,
    tokenCount: 0,
    tokens: '',
    thinking: '',
    thinkCount: 0,
    innerToolCalls: [],
    duration: tc?.duration,
  }
}

function getLiveToolCallIdFromSubSession(subSessionId: string): string | null {
  const parts = subSessionId.split('--sa--')
  if (parts.length < 2) return null
  return parts.slice(1).join('--sa--')
}

function hasLiveSubAgentEntry(toolCallId: string): boolean {
  return messages.value.some(msg => Boolean(msg.subAgents?.[toolCallId]))
}

function handleEnterSubAgent(subSessionId: string, name: string) {
  if (chatStore.isStreaming) {
    if (subLiveToolCallId.value !== null) return
    const toolCallId = getLiveToolCallIdFromSubSession(subSessionId)
    if (toolCallId && !hasLiveSubAgentEntry(toolCallId)) return
  }
  sessionsStore.pushSubSession(subSessionId, name)
}

function getAssistantLabel(): string {
  const stack = sessionsStore.sessionNavStack
  if (stack.length > 0) {
    return stack[stack.length - 1].label || 'AI'
  }
  return agentsStore.currentAgent?.name || 'AI'
}

function getModelLabel(): string {
  if (sessionsStore.sessionNavStack.length > 0) {
    // In sub-session view, model info is not available; show nothing
    return ''
  }
  if (agentsStore.isCodeAgent) return '代码内定义'
  const model = toolsStore.currentModel || agentsStore.currentAgent?.default_model || ''
  if (!model) return '模型未选择'
  const parts = model.split('/')
  return parts[parts.length - 1] || model
}

function isThinkingExpanded(item: ChatBubbleItem): boolean {
  return item.isStreamingMessage === true
}

function canEditMessage(item: ChatBubbleItem) {
  return item.role === 'user'
    && !item.isSystem
    && lastUserMessage.value?.id === item.messageId
    && !isStreaming.value
    && sessionsStore.sessionNavStack.length === 0
}

function startEditMessage(item: ChatBubbleItem) {
  if (!canEditMessage(item)) return
  editingMessageId.value = item.messageId
  const blocks = 'contentBlocks' in item ? item.contentBlocks : undefined
  if (blocks && blocks.length > 0) {
    const textParts: string[] = []
    const restoredAtts: Attachment[] = []
    let attIdx = 0
    for (const block of blocks) {
      if (block.type === 'text') {
        const fileMatch = block.text?.match(/^📎 `([^`]+)`:\n```(\w*)\n([\s\S]*?)\n```$/)
        if (fileMatch) {
          const [, name, , content] = fileMatch
          restoredAtts.push({
            id: `restore-${attIdx++}`,
            type: 'text_file',
            name,
            textContent: content,
          })
        } else if (block.text) {
          textParts.push(block.text)
        }
      } else if (block.type === 'image_url' && block.image_url) {
        restoredAtts.push({
          id: `restore-${attIdx++}`,
          type: 'image',
          name: `image-${attIdx}.png`,
          dataUrl: block.image_url.url,
        })
      }
    }
    editingContent.value = textParts.join('\n')
    editingAttachments.value = restoredAtts
  } else {
    editingContent.value = item.content || ''
    editingAttachments.value = []
  }
}

function cancelEdit() {
  editingMessageId.value = null
  editingContent.value = ''
  editingAttachments.value = []
}

function previewImage(url: string) {
  imageViewerUrl.value = url
  imageViewerVisible.value = true
}

function hasStructuredSegments(content: string, toolCalls?: ToolCall[]): boolean {
  return Boolean(
    toolCalls?.length
    || content.includes(THINK_START)
    || content.includes(THINK_END)
    || content.includes(HTTP_MARKER),
  )
}

function getReasoningTokenTotal(usage?: MessageUsage): number {
  return usage?.rounds.reduce((total, round) => total + (round.reasoningTokens || 0), 0) || 0
}

function hasThinkingSegment(segments?: ContentSegment[]): boolean {
  return Boolean(segments?.some(seg => seg.type === 'thinking' && seg.text?.trim()))
}

function shouldShowReasoningNotice(item: ChatBubbleItem): boolean {
  return item.role === 'ai'
    && getReasoningTokenTotal(item.usage) > 0
    && !hasThinkingSegment(item.segments)
}

function formatCompactTokens(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

function stripThinkingMarkers(content: string): string {
  return content.replace(/<!--(?:THINK_START|THINK_END)-->/g, '').trim()
}

function stripUiMarkers(content: string): string {
  return stripThinkingMarkers(content).replace(/<!--TOOL:\d+-->/g, '').replace(/<!--HTTP:\d+-->/g, '').trim()
}

function getReplayHistory(beforeMessageId: string): ReplayMessage[] {
  const idx = messages.value.findIndex(msg => msg.id === beforeMessageId)
  if (idx < 0) return []

  return messages.value
    .slice(0, idx)
    .filter((msg): msg is typeof msg & { role: 'user' | 'assistant' } =>
      msg.role === 'user' || msg.role === 'assistant',
    )
    .map(msg => {
      if (msg.role === 'user' && Array.isArray(msg.content)) {
        return { role: msg.role, content: msg.content }
      }
      const text = typeof msg.content === 'string' ? msg.content : ''
      return { role: msg.role, content: stripUiMarkers(text) }
    })
    .filter(msg =>
      Array.isArray(msg.content) ? msg.content.length > 0 : msg.content.trim().length > 0,
    )
}

function parseSegments(content: string, toolCalls?: ToolCall[]): ContentSegment[] {
  const segments: ContentSegment[] = []
  const pattern = /<!--(?:TOOL:(\d+)|HTTP:(\d+)|THINK_START|THINK_END)-->/g
  let lastIndex = 0
  let match: RegExpExecArray | null
  let inThinking = false

  while ((match = pattern.exec(content)) !== null) {
    const textBefore = content.slice(lastIndex, match.index).trim()
    const marker = match[0]

    if (marker === THINK_START) {
      if (textBefore) {
        segments.push({ type: inThinking ? 'thinking' : 'text', text: stripThinkingMarkers(textBefore) })
      }
      inThinking = true
      lastIndex = match.index + match[0].length
      continue
    }

    if (marker === THINK_END) {
      if (textBefore) {
        segments.push({ type: 'thinking', text: stripThinkingMarkers(textBefore) })
      }
      inThinking = false
      lastIndex = match.index + match[0].length
      continue
    }

    if (match[2] != null) {
      if (textBefore) {
        segments.push({ type: inThinking ? 'thinking' : 'text', text: stripThinkingMarkers(textBefore) })
      }
      segments.push({ type: 'http', httpIndex: parseInt(match[2], 10) })
      lastIndex = match.index + match[0].length
      continue
    }

    if (textBefore) {
      segments.push({ type: inThinking ? 'thinking' : 'text', text: stripThinkingMarkers(textBefore) })
    }
    const toolIdx = parseInt(match[1], 10)
    if (toolCalls && toolIdx < toolCalls.length) {
      segments.push({ type: 'tool', toolIndex: toolIdx })
    }
    lastIndex = match.index + match[0].length
  }

  const remaining = content.slice(lastIndex).trim()
  if (remaining) {
    segments.push({ type: inThinking ? 'thinking' : 'text', text: stripThinkingMarkers(remaining) })
  }

  return segments
}

function handleSend(content: ContentBlock[]) {
  const editMessageId = editingMessageId.value
  const history = editMessageId ? getReplayHistory(editMessageId) : undefined
  const modelOverride = agentsStore.isCodeAgent ? '' : toolsStore.currentModel
  if (editingMessageId.value) {
    chatStore.truncateAfterMessage(editingMessageId.value)
    cancelEdit()
  }
  chatStore.sendMessage(content, agentsStore.currentAgentId, modelOverride, {
    replaceFromMessageId: editMessageId || undefined,
    history,
    llmParams: toolsStore.llmParams,
  })
}

function handleStop() {
  chatStore.stopGeneration()
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

let lastNotificationId: ReturnType<typeof ElMessage> | null = null

function showErrorNotification(error: ErrorInfo) {
  if (lastNotificationId) {
    lastNotificationId.close()
    lastNotificationId = null
  }

  const t = escapeHtml(error.title)
  const d = escapeHtml(error.detail)
  const suggestions = error.suggestions?.map(s => `<li>${escapeHtml(s)}</li>`).join('') || ''
  const tech = error.techDetail ? escapeHtml(error.techDetail) : ''

  lastNotificationId = ElMessage({
    type: 'error',
    dangerouslyUseHTMLString: true,
    showClose: true,
    duration: 0,
    grouping: true,
    message: `<div style="line-height:1.5;max-width:420px">
      <strong style="font-size:15px">${t}</strong>
      <div style="margin:6px 0 10px;font-size:13px;color:var(--el-text-color-regular)">${d}</div>
      ${suggestions ? `<div style="font-size:12px;color:var(--el-text-color-secondary)">
        <strong>建议：</strong>
        <ul style="margin:4px 0 0;padding-left:18px;line-height:1.6">${suggestions}</ul></div>` : ''}
      ${tech ? `<details style="margin-top:10px;font-size:11px;color:var(--el-text-color-placeholder)">
        <summary style="cursor:pointer">技术详情</summary>
        <pre style="margin:6px 0 0;padding:8px;background:var(--el-fill-color-light);border-radius:4px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:11px;overflow-x:auto;white-space:pre-wrap;word-break:break-word;max-height:150px;overflow-y:auto">${tech}</pre>
      </details>` : ''}
    </div>`,
    onClose: () => { lastNotificationId = null },
  })
}

watch(errorMessage, (newError) => {
  if (newError) {
    showErrorNotification(newError)
  }
})

watch(
  () => sessionsStore.sessionNavStack.length,
  async (newLen, oldLen) => {
    if (newLen === 0 && oldLen === 0) return
    const newId = sessionsStore.effectiveThreadId
    if (!newId) return

    if (newLen > 0) {
      if (chatStore.isStreaming) {
        const toolCallId = getLiveToolCallIdFromSubSession(newId)
        if (toolCallId && hasLiveSubAgentEntry(toolCallId)) {
          subLiveToolCallId.value = toolCallId
          return
        }
        sessionsStore.popSubSession()
        return
      }
      // Historical mode: load sub-session from DB
      chatStore.clearMessages()
      await chatStore.loadMessages(newId)
    } else {
      // Returning to root
      if (subLiveToolCallId.value !== null) {
        // Returning from live mode: just clear live state; main messages are still intact
        subLiveToolCallId.value = null
        return
      }
      // Returning from historical mode: reload main session messages
      await chatStore.loadMessages(newId)
    }
  },
)

// When streaming ends while in live sub-session, auto-switch to historical mode
watch(isStreaming, async (newVal, oldVal) => {
  if (!newVal && oldVal && subLiveToolCallId.value !== null && sessionsStore.sessionNavStack.length > 0) {
    const subSessionId = sessionsStore.effectiveThreadId
    // Give backend a moment to persist the sub-session messages
    await new Promise(resolve => setTimeout(resolve, 600))
    subLiveToolCallId.value = null
    if (subSessionId) {
      chatStore.clearMessages()
      await chatStore.loadMessages(subSessionId)
    }
  }
})

watch(() => messages.value[messages.value.length - 1]?.id, () => {
  scrollMessagesToBottom()
}, { flush: 'post' })

function handleAllowPermanently(toolName: string) {
  chatStore.respondToInterrupt(true, agentsStore.currentAgentId, toolName, toolsStore.llmParams)
}

function handleInterruptDecide(decision: { type: string }) {
  chatStore.respondToInterrupt(decision.type === 'approve', agentsStore.currentAgentId, undefined, toolsStore.llmParams)
}

function handleInterruptResume(value: any) {
  chatStore.resumeInterrupt(value, agentsStore.currentAgentId, toolsStore.currentModel, toolsStore.llmParams)
}

function getCodeToCopy(button: HTMLButtonElement): string {
  const encoded = button.dataset.code
  if (encoded) {
    try {
      return decodeURIComponent(encoded)
    } catch {
      return encoded
    }
  }
  return button.closest('.markdown-code-block')?.querySelector('code')?.textContent ?? ''
}

function fallbackCopy(text: string) {
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', 'true')
  textarea.style.position = 'fixed'
  textarea.style.left = '-9999px'
  document.body.appendChild(textarea)
  textarea.select()
  document.execCommand('copy')
  document.body.removeChild(textarea)
}

async function copyMarkdownCode(button: HTMLButtonElement) {
  const text = getCodeToCopy(button)
  if (!text) return

  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
  } else {
    fallbackCopy(text)
  }

  const previousText = button.textContent || '复制'
  button.textContent = '已复制'
  button.classList.add('copied')
  window.setTimeout(() => {
    button.textContent = previousText
    button.classList.remove('copied')
  }, 1400)
}

function getMessagesScroller() {
  return messagesContainerRef.value?.querySelector('.elx-bubble-list') as HTMLElement | null
}

function handleMessagesScroll() {
  const scroller = getMessagesScroller()
  if (!scroller) {
    showLoadOlderMessages.value = false
    return
  }
  const canRevealLoadOlderMessages = scroller.scrollHeight > scroller.clientHeight + LOAD_OLDER_REVEAL_THRESHOLD
  showLoadOlderMessages.value = canRevealLoadOlderMessages && scroller.scrollTop <= LOAD_OLDER_REVEAL_THRESHOLD
}

async function scrollMessagesToBottom() {
  await nextTick()
  const container = getMessagesScroller()
  if (!container) return
  container.scrollTop = container.scrollHeight
  handleMessagesScroll()
}

async function handleLoadOlderMessages() {
  if (loadingOlder.value) return
  const sessionId = chatStore.threadId
  const scroller = getMessagesScroller()
  if (!sessionId || !scroller) return

  const distanceFromBottom = scroller.scrollHeight - scroller.scrollTop
  await chatStore.loadOlderMessages(sessionId)
  await nextTick()
  scroller.scrollTop = scroller.scrollHeight - distanceFromBottom
  handleMessagesScroll()
}

function handleMarkdownClick(event: MouseEvent) {
  const target = event.target as HTMLElement | null

  const expandBtn = target?.closest?.('.markdown-code-expand') as HTMLButtonElement | null
  if (expandBtn) {
    event.preventDefault()
    const encoded = expandBtn.dataset.code || ''
    const lang = expandBtn.dataset.lang || 'text'
    try {
      codeModalSource.value = decodeURIComponent(encoded)
    } catch {
      codeModalSource.value = encoded
    }
    codeModalLanguage.value = lang
    codeModalVisible.value = true
    return
  }

  const button = target?.closest?.('.markdown-code-copy') as HTMLButtonElement | null
  if (!button) return
  event.preventDefault()
  copyMarkdownCode(button).catch(() => {
    button.textContent = '复制失败'
    window.setTimeout(() => {
      button.textContent = '复制'
    }, 1400)
  })
}

onMounted(() => {
  document.addEventListener('click', handleMarkdownClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleMarkdownClick)
})
</script>

<style scoped>
.chat-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  min-height: 0;
}

.subagent-breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: var(--el-color-primary-light-9);
  border-bottom: 1px solid var(--el-color-primary-light-7);
  font-size: 12px;
  flex-shrink: 0;
}
.breadcrumb-back {
  padding: 3px 9px;
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 6px;
  background: white;
  color: var(--el-color-primary);
  cursor: pointer;
  font-size: 12px;
}
.breadcrumb-back:hover {
  background: var(--el-color-primary-light-9);
}
.breadcrumb-home {
  color: var(--el-color-primary);
  cursor: pointer;
}
.breadcrumb-home:hover {
  text-decoration: underline;
}
.breadcrumb-sep {
  color: var(--el-text-color-disabled);
}
.breadcrumb-item {
  color: var(--el-text-color-secondary);
}
.breadcrumb-active {
  font-weight: 600;
  color: var(--el-text-color-primary);
  cursor: default;
}

.subagent-readonly-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: var(--el-color-info-light-9);
  border-top: 1px solid var(--el-color-info-light-5);
  font-size: 13px;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}
.subagent-readonly-icon {
  font-size: 15px;
}
.subagent-readonly-back {
  margin-left: auto;
  padding: 4px 12px;
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 6px;
  background: var(--el-bg-color);
  color: var(--el-color-primary);
  cursor: pointer;
  font-size: 12px;
}
.subagent-readonly-back:hover {
  background: var(--el-color-primary-light-9);
}

.messages-container {
  --chat-assistant-bubble-width: min(85%, 920px);
  --chat-user-bubble-max-width: min(78%, 720px);
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
  background: var(--el-bg-color-page);
  min-width: 0;
  min-height: 0;
}

.messages-container :deep(.elx-bubble-list) {
  width: 100%;
  flex: 1;
  min-height: 0;
}

.messages-container :deep(.elx-bubble-list__list) {
  height: 100%;
  overflow-y: auto;
  overscroll-behavior-y: contain;
  -webkit-overflow-scrolling: touch;
}

.messages-container :deep(.elx-bubble-list__content) {
  min-height: 100%;
}

.load-older-messages.is-inline {
  display: flex;
  justify-content: center;
  width: 100%;
  padding: 4px 0 8px;
}

.messages-container :deep(.elx-bubble) {
  max-width: 100% !important;
}

.messages-container :deep(.elx-bubble--start) {
  width: var(--chat-assistant-bubble-width) !important;
  max-width: var(--chat-assistant-bubble-width) !important;
  align-self: flex-start;
}

.messages-container :deep(.elx-bubble--end) {
  width: 100% !important;
  max-width: 100% !important;
  align-self: flex-end;
  justify-content: flex-end;
}

.messages-container :deep(.elx-bubble--end .elx-bubble__avatar) {
  margin-top: 2px;
}

.messages-container :deep(.elx-bubble--end .elx-bubble__header) {
  display: flex;
  justify-content: flex-end;
  min-height: 22px;
  margin-bottom: 4px;
}

.messages-container :deep(.elx-bubble--start),
.messages-container :deep(.elx-bubble--end) {
  padding-inline: 0 !important;
}

.messages-container :deep(.elx-bubble--end .elx-bubble__content-wrapper) {
  width: fit-content;
  max-width: var(--chat-user-bubble-max-width) !important;
}

.messages-container :deep(.elx-bubble__content) {
  max-width: none !important;
  min-width: 0;
}

.messages-container :deep(.elx-bubble--start .elx-bubble__content-wrapper),
.messages-container :deep(.elx-bubble--start .elx-bubble__content) {
  width: 100%;
  max-width: 100% !important;
}

.messages-container :deep(.elx-bubble--end .elx-bubble__content-wrapper),
.messages-container :deep(.elx-bubble--end .elx-bubble__content) {
  max-width: 100% !important;
}

.role-avatar {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--el-border-color);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.18);
}

.role-header.is-user {
  display: flex;
  justify-content: flex-end;
  width: 100%;
}

.message-edit-btn {
  border: 1px solid color-mix(in srgb, var(--el-color-success) 34%, var(--el-border-color));
  border-radius: 999px;
  background: color-mix(in srgb, var(--el-color-success) 12%, var(--el-bg-color-overlay));
  color: var(--el-color-success);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  opacity: 0;
  padding: 5px 9px;
  transform: translateY(2px);
  transition: opacity 0.16s ease, transform 0.16s ease, background 0.16s ease;
}

.messages-container :deep(.elx-bubble--end:hover) .message-edit-btn,
.message-edit-btn:focus-visible {
  opacity: 1;
  transform: translateY(0);
}

.message-edit-btn:hover {
  background: color-mix(in srgb, var(--el-color-success) 22%, var(--el-bg-color-overlay));
}

.role-avatar.is-user {
  color: #f7fee7;
  background: linear-gradient(135deg, #2ea043, #1f7a3a);
  border-color: rgba(74, 222, 128, 0.45);
}

.role-avatar.is-ai {
  color: #d8f3dc;
  background: linear-gradient(135deg, #15382a, #0b2119);
  border-color: rgba(74, 222, 128, 0.32);
}

.role-avatar.is-system {
  background: color-mix(in srgb, var(--el-color-info) 14%, var(--el-bg-color));
  border-color: color-mix(in srgb, var(--el-color-info) 35%, var(--el-border-color));
}

.system-avatar-icon {
  font-size: 14px;
  line-height: 1;
}

.role-header.is-system {
  color: var(--el-color-info);
  font-weight: 600;
}

.system-delegation-msg {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px dashed color-mix(in srgb, var(--el-color-info) 40%, var(--el-border-color));
  background: color-mix(in srgb, var(--el-color-info) 8%, var(--el-bg-color));
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.bubble-content-wrap.is-system-delegation {
  max-width: 100%;
}

.role-header {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 7px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.role-header.is-ai {
  min-height: 24px;
}

.role-header-icon {
  display: none;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  color: #d8f3dc;
  background: linear-gradient(135deg, #15382a, #0b2119);
  border: 1px solid rgba(74, 222, 128, 0.32);
}

.role-name {
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.role-model {
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 2px 8px;
  border-radius: 999px;
  color: var(--el-text-color-secondary);
  background: color-mix(in srgb, var(--el-fill-color-light) 82%, transparent);
  border: 1px solid color-mix(in srgb, var(--el-border-color-lighter) 78%, transparent);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
}

.bubble-content-wrap {
  width: 100%;
  min-width: 0;
  overflow-wrap: anywhere;
}

.user-plain-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.user-content-blocks {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 100%;
}

.user-text-block {
  white-space: pre-wrap;
  word-break: break-word;
}

.user-image-block {
  max-width: 240px;
  max-height: 240px;
  border-radius: 6px;
  cursor: zoom-in;
  border: 1px solid var(--el-border-color);
}

.tool-call-inline {
  margin: 8px 0;
  position: relative;
  z-index: 1;
  pointer-events: auto !important;
  max-width: 100%;
  overflow-x: auto;
}

.thinking-block {
  margin: 8px 0 10px;
  border-radius: 12px;
  border: 1px solid rgba(234, 179, 8, 0.22);
  border-left: 3px solid rgba(234, 179, 8, 0.72);
  background: rgba(234, 179, 8, 0.08);
  overflow: hidden;
}

.thinking-summary {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 8px 11px;
  cursor: pointer;
  user-select: none;
  color: #d69e2e;
  font-size: 12px;
  font-weight: 700;
}

.thinking-summary::-webkit-details-marker {
  display: none;
}

.thinking-summary::after {
  content: '展开';
  margin-left: auto;
  color: var(--el-text-color-secondary);
  font-weight: 500;
  font-size: 11px;
}

.thinking-block[open] .thinking-summary::after {
  content: '收起';
}

.thinking-body {
  padding: 0 12px 10px;
  color: #c58f22;
  font-size: 13px;
  opacity: 0.92;
}

.thinking-unavailable {
  display: flex;
  gap: 9px;
  align-items: flex-start;
  margin: 8px 0 10px;
  padding: 9px 11px;
  border-radius: 12px;
  color: var(--el-text-color-secondary);
  background: color-mix(in srgb, var(--el-fill-color-light) 82%, var(--el-color-warning) 8%);
  border: 1px dashed color-mix(in srgb, var(--el-color-warning) 36%, var(--el-border-color));
  font-size: 12px;
  line-height: 1.55;
}

.thinking-unavailable .el-icon {
  color: var(--el-color-warning);
  margin-top: 2px;
  flex-shrink: 0;
}

.thinking-unavailable-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.thinking-unavailable-text strong {
  color: var(--el-text-color-primary);
  font-size: 12px;
}

.messages-container :deep([style*="pointer-events"]) .tool-call-inline,
.messages-container :deep(.tool-call-card) {
  pointer-events: auto !important;
  cursor: pointer;
}

.messages-container :deep(.markdown-body) {
  max-width: 100%;
}

.messages-container :deep(.markdown-code-block),
.messages-container :deep(.markdown-body pre),
.messages-container :deep(.markdown-body table),
.messages-container :deep(.tool-call-card) {
  max-width: 100%;
  overflow-x: auto;
}

.messages-container :deep(.markdown-body code) {
  overflow-wrap: anywhere;
}

.messages-container :deep(.elx-welcome) {
  background: var(--el-bg-color-overlay) !important;
  border: 1px solid var(--el-border-color-lighter) !important;
  border-radius: 12px;
  color: var(--el-text-color-primary);
}

.messages-container :deep(.elx-welcome__title) {
  color: var(--el-text-color-primary) !important;
}

@media (max-width: 960px) {
  .messages-container {
    padding: 6px 0;
    overscroll-behavior-y: contain;
  }

  .messages-container :deep(.elx-bubble--start),
  .messages-container :deep(.elx-bubble--end) {
    width: 100% !important;
    max-width: 100% !important;
    padding-inline: 0 !important;
  }

  .messages-container :deep(.elx-bubble--start .elx-bubble__content-wrapper),
  .messages-container :deep(.elx-bubble--start .elx-bubble__content),
  .messages-container :deep(.elx-bubble--end .elx-bubble__content-wrapper),
  .messages-container :deep(.elx-bubble--end .elx-bubble__content),
  .messages-container :deep(.elx-bubble__content) {
    width: 100%;
    max-width: 100% !important;
  }

  .messages-container :deep(.markdown-body),
  .messages-container :deep(.markdown-body > *:first-child),
  .messages-container :deep(.markdown-body > *:last-child) {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }

  .messages-container :deep(.markdown-code-block),
  .messages-container :deep(.markdown-body pre),
  .messages-container :deep(.markdown-body table),
  .messages-container :deep(.tool-call-card) {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }

  .thinking-summary {
    padding: 8px 8px;
  }

  .thinking-body {
    padding: 0 8px 10px;
  }

  .thinking-unavailable {
    padding: 8px 8px;
  }

  .messages-container :deep(.elx-bubble__avatar) {
    display: none !important;
  }

  .role-header {
    gap: 6px;
    margin-bottom: 5px;
  }

  .role-header-icon {
    display: inline-flex;
  }

  .role-model {
    max-width: 42vw;
  }
}

@media (max-width: 560px) {
  .messages-container {
    padding: 4px 0;
  }

  .messages-container :deep(.elx-bubble-list__content) {
    gap: 0 !important;
  }

  .messages-container :deep(.elx-bubble-list) {
    overscroll-behavior: contain;
  }

  .messages-container :deep(.elx-bubble--start),
  .messages-container :deep(.elx-bubble--end) {
    padding-inline: 0 !important;
    margin-inline: 0 !important;
  }

  .messages-container :deep(.elx-bubble__content) {
    padding-left: 6px !important;
    padding-right: 6px !important;
  }

  .messages-container :deep(.elx-bubble) {
    gap: 0 !important;
  }

  .messages-container :deep(.elx-bubble--start .elx-bubble__content-wrapper),
  .messages-container :deep(.elx-bubble--start .elx-bubble__content),
  .messages-container :deep(.elx-bubble--end .elx-bubble__content-wrapper),
  .messages-container :deep(.elx-bubble--end .elx-bubble__content),
  .messages-container :deep(.elx-bubble__content),
  .messages-container :deep(.markdown-body),
  .messages-container :deep(.tool-call-card) {
    width: 100%;
    max-width: 100% !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
  }

  .messages-container :deep(.markdown-code-block),
  .messages-container :deep(.markdown-body pre),
  .messages-container :deep(.markdown-body table) {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }

  .messages-container :deep(.markdown-body > p),
  .messages-container :deep(.markdown-body > ul),
  .messages-container :deep(.markdown-body > ol),
  .messages-container :deep(.markdown-body > blockquote),
  .messages-container :deep(.markdown-body > h1),
  .messages-container :deep(.markdown-body > h2),
  .messages-container :deep(.markdown-body > h3),
  .messages-container :deep(.markdown-body > h4),
  .messages-container :deep(.markdown-body > h5),
  .messages-container :deep(.markdown-body > h6) {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }

  .thinking-summary {
    padding: 7px 6px;
  }

  .thinking-body {
    padding: 0 6px 9px;
  }

  .thinking-unavailable {
    padding: 7px 6px;
  }

  .role-model {
    max-width: 46vw;
  }

  .role-header {
    font-size: 11px;
  }

  .message-edit-btn {
    opacity: 1;
    transform: none;
    padding: 4px 8px;
  }

  .thinking-summary,
  .thinking-body,
  .thinking-unavailable,
  .thinking-unavailable-text strong {
    font-size: 12px;
  }
}

</style>

`````

--- **end of file: frontend/src/views/ChatView.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/views/LoginView.vue** (project: lc_agent) --- 

`````vue
<template>
  <div class="login-page">
    <el-card class="login-card" shadow="hover">
      <template #header>
        <div class="login-header">
          <span class="login-logo">⚡</span>
          <h1>登录</h1>
        </div>
      </template>

      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            autocomplete="current-password"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" style="margin-bottom: 16px" />

        <el-button type="primary" size="large" :loading="loading" style="width: 100%" @click="handleLogin">
          登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  if (authStore.authRequired === null) {
    await authStore.checkBackendAuth()
  }
  if (!authStore.authRequired) {
    await router.push('/')
  }
})

async function handleLogin() {
  if (!username.value.trim() || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  error.value = ''
  try {
    await authStore.login(username.value.trim(), password.value)
    await router.push('/')
  } catch (e: any) {
    error.value = e.message || '认证失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100dvh;
  background: var(--el-bg-color-page);
  padding: 24px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  border-radius: 16px;
}

.login-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.login-logo {
  font-size: 24px;
}

.login-header h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
</style>

`````

--- **end of file: frontend/src/views/LoginView.vue** (project: lc_agent) --- 

---


--- **start of file: frontend/src/views/TestSegments.vue** (project: lc_agent) --- 

`````vue
<template>
  <div style="padding:20px; background:var(--el-bg-color-page); min-height:100vh; color:var(--el-text-color-regular);">
    <h2>Segments Rendering Test</h2>
    <button @click="simulateStream" style="padding:8px 16px; margin:10px 0;">
      Simulate Stream (think → tool → answer)
    </button>
    <button @click="resetMsg" style="padding:8px 16px; margin:10px;">Reset</button>
    <div style="margin:10px 0; font-size:12px; color:var(--el-text-color-secondary);">
      Segments: {{ msg.segments?.length || 0 }} | Content length: {{ msg.content.length }}
    </div>
    <ChatBubble :message="msg" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ChatBubble from '@/components/chat/ChatBubble.vue'
import type { ChatMessage, ToolCall } from '@/stores/chat'

const msg = ref<ChatMessage>({
  id: 'test-1',
  role: 'assistant',
  content: '',
  timestamp: Date.now(),
  isStreaming: false,
  usage: { rounds: [], toolCallCount: 0 },
})

function resetMsg() {
  msg.value = {
    id: 'test-' + Date.now(),
    role: 'assistant',
    content: '',
    timestamp: Date.now(),
    isStreaming: false,
    usage: { rounds: [], toolCallCount: 0 },
  }
}

async function simulateStream() {
  resetMsg()
  msg.value.isStreaming = true
  
  const addToken = (text: string) => {
    msg.value.content += text
    const segs = msg.value.segments!
    const last = segs[segs.length - 1]
    if (last && last.type === 'text') {
      last.text = (last.text || '') + text
    } else {
      segs.push({ type: 'text', text })
    }
  }
  
  const addTool = (name: string) => {
    const tc: ToolCall = { name, args: { query: 'test' }, status: 'running' }
    if (!msg.value.toolCalls) msg.value.toolCalls = []
    const tcIdx = msg.value.toolCalls.length
    msg.value.toolCalls.push(tc)
    msg.value.content += `\n<!--TOOL:${tcIdx}-->\n`
    msg.value.usage!.toolCallCount++
  }
  
  const finishTool = (name: string) => {
    const tc = msg.value.toolCalls?.find(t => t.name === name && t.status === 'running')
    if (tc) {
      tc.status = 'done'
      tc.result = 'Some result data...'
      tc.duration = 1234
    }
  }
  
  const delay = (ms: number) => new Promise(r => setTimeout(r, ms))
  
  // Phase 1: thinking text
  for (const char of '我来查询相关文档...\n') {
    addToken(char)
    await delay(30)
  }
  
  // Phase 2: tool call
  await delay(200)
  addTool('mcp__docs__search')
  await delay(1000)
  finishTool('mcp__docs__search')
  
  // Phase 3: more thinking
  await delay(200)
  for (const char of '继续查找更多资料...\n') {
    addToken(char)
    await delay(30)
  }
  
  // Phase 4: another tool
  await delay(200)
  addTool('mcp__reference__get_symbol')
  await delay(800)
  finishTool('mcp__reference__get_symbol')
  
  // Phase 5: final answer
  await delay(200)
  for (const char of '## 最终答案\n\n这是一个总结性回答。') {
    addToken(char)
    await delay(20)
  }
  
  msg.value.isStreaming = false
  msg.value.usage!.totalDuration = 5000
}
</script>

`````

--- **end of file: frontend/src/views/TestSegments.vue** (project: lc_agent) --- 

---

