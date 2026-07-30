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

**ai coding 执行用户代码，流式打字机效果**
![ai coding 执行用户代码，流式打字机效果](https://raw.githubusercontent.com/ydf0509/lc-agent/main/docs_pic/ai_coding_run.png)

**ai coding 编辑用户代码，类似cursor codex的代码变动 diff 红绿渲染**
![ai coding 编辑用户代码，类似cursor codex的代码变动 diff 红绿渲染](https://raw.githubusercontent.com/ydf0509/lc-agent/main/docs_pic/aicoding_edit.png)

**子 agent 效果，可委派给子 agent 执行，并流式打字机显示和保留独立执行过程**
![子 agent 效果，可委派给子 agent 执行，并流式打字机显示和保留独立执行过程](https://raw.githubusercontent.com/ydf0509/lc-agent/main/docs_pic/subagent.png)

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

除了 `openwebsearch` mcp另外推荐一个更好更稳定更适合agent联网的mcp，`anysearch`，每天免费1000次，我在联网搜索某些技术文档时候，实测比deepseek 豆包官网的联网搜索更强。

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

## lc-agent 能不能作为aicoding 工具来使用？

答：完全可以，而且编程效果和体验都很好。

方案A:
可以，你可以搭配serena mcp全套来编程。但是这个因为是第三方mcp，对于edit文件 和 执行命令，lc-agent的前端界面没有精细化适配，例如文件变更diff、执行命令的流式打字机效果等，对serena没支持。

方案B：
开启lc-agent 内置赠送的工具组， 用户开启`file_read` `file_write` `command` 三个工具组，大约20个工具，足以编程了。另外你还可以搭配 nbrag 或者codegraph mcp，使代码语义和符号检索更强大。
lc-agent前端对代码改动和代码执行的渲染，达到了 traework codex-gui 的体验效果。


lc-agent 既可以作为 你的private gpt纯聊天页面来使用，也可以作为 通用agent来使用，ai coding只是能力之一。


## License

MIT
