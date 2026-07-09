# lc-agent

基于 LangChain / LangGraph 的 Agent 框架，自带可直接使用的 Web UI。

**lc-agent 既是产品，也是框架。**

- 想直接用：配好模型、MCP、Skills，就能把它当成一个可观测、可审批、可扩展的 Agent 工作台
- 想二次开发：`import lc_agent`，把你自己的工具、MCP、Skills、`CompiledStateGraph` Agent 接进来，复用现成前端和运行时

> 演示项目：[lc-agent-bfzs](https://github.com/ydf0509/lc-agent-bfzs)

## 它适合什么场景

lc-agent 适合这三类需求：

1. 你想要一个比普通聊天网页更强的 Agent UI
2. 你已经在用 LangChain / LangGraph，不想自己再做前端、会话、审批、可观测性
3. 你要把 MCP、Skills、自定义工具和自定义 Agent 编排到一个统一界面里

如果你只是想要一个纯聊天网页，它也能用；但它真正的优势在于 **Agent 执行过程可见、工具调用可控、能力组合灵活**。

## 核心能力

### 1. Agent 运行时
- 内置三套预设：`Chat`、`Empty`、`Power`
- 页面直接创建和编辑 Agent
- 运行时切换模型、工具组、MCP、Skills，无需重启
- 支持固定 LLM 参数，如 `temperature`、`reasoning_effort`
- 支持注册代码型 `CompiledStateGraph` Agent：`app.add_agent(...)`

### 2. 子 Agent / 任务委派
- 一个 Agent 可以配置多个子 Agent
- 支持为每个子 Agent 写委派说明，控制何时触发
- 支持“通用子 Agent”，把复杂任务委派给隔离 worker
- 子 Agent 有独立小窗口，能看到提问、思考、工具调用和结果
- 可进入子会话查看完整执行过程

### 3. 工具、Skills、MCP
- `@tool` 装饰器注册工具，支持分组展示
- 扫描 `SKILL.md` 技能目录，按规则注入能力
- MCP 支持 `stdio / SSE / Streamable HTTP`
- MCP JSON Schema 自动适配为 LangChain 工具
- 工具、MCP、Skills 都支持 Agent 级权限控制

### 4. 可观测性
- 每轮 LLM 请求/响应支持 HTTP trace
- Token 面板展示 input / output / cache / reasoning 用量
- 工具调用卡片显示参数、耗时、结果、状态
- 历史消息支持按需加载单条 trace
- 子 Agent 的过程信息也会保留

### 5. 审批与安全控制
- 危险工具支持 Human-in-the-loop 审批
- 支持“永久允许此工具”，白名单持久化保存
- 支持登录认证、用户隔离、Agent 授权
- 管理员可以管理用户与权限

### 6. 对话体验
- 基于 **SSE** 的流式输出
- 支持 thinking / tool call / answer 交替渲染
- 支持中断生成
- 支持编辑历史消息并重新生成
- 自动生成会话标题
- 会话支持固定、分组、搜索、深链路
- 支持本地临时会话，首轮发送后自动持久化

## 截图
说明： 产品界面与实际有差异，实际界面更加美观，功能更加强大，截图时间太早了，后来持续增加了功能，以实际运行界面为准。

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
pip install -e .
```

### 作为现成 Agent 工作台使用

```bash
cp config.example.jsonc config.jsonc
# 编辑 config.jsonc，至少配置 provider、models、agent.default_model
lc-agent
# 打开 http://127.0.0.1:8000
```

如果你在配置里启用了 `auth.secret`，首次启动会进入登录流；默认会自动创建一个管理员账号：

- 用户名：`admin`
- 密码：`123456`

首次登录后建议立即修改密码。

### 作为框架接入你的项目

```python
from lc_agent import LcAgentApp, load_config, tool

@tool(group="my_tools", group_description="我的工具")
def my_tool(query: str) -> str:
    """工具描述"""
    return f"result: {query}"

config = load_config(config_path="./config.jsonc")
app = LcAgentApp(config, host="127.0.0.1", port=8001)
app.run()
```

### 注册你自己的代码型 Agent

```python
from lc_agent import LcAgentApp, load_config
from my_agents import build_my_agent

config = load_config("./config.jsonc")
app = LcAgentApp(config, host="127.0.0.1", port=8001)
app.add_agent("my_agent", build_my_agent(config), description="自定义 Agent")
app.run()
```

## 配置什么最重要

大多数用户只需要关心这几个配置块：

- `provider`：模型提供商与模型列表
- `agent.default_model`：默认模型
- `skills`：Skills 目录
- `mcp_servers`：MCP 配置
- `database`：会话与 checkpoint 存储

配置文件使用 `config.jsonc`，支持：
- 注释
- `{env:VAR}` 环境变量替换
- `.env` 自动加载

## API / 通信方式

lc-agent 当前主要通过 **REST + SSE** 工作，不是旧版 WebSocket 架构。

常用接口包括：
- `POST /api/threads/{thread_id}/runs/stream`：SSE 流式运行
- `POST /api/threads/{thread_id}/runs/cancel`：取消当前生成
- `GET /api/agents/available-subagents`：查询可选子 Agent
- `GET /api/sessions/{id}/messages`：分页读取会话消息
- `GET /api/sessions/{id}/messages/{message_id}/traces`：读取单条消息 trace
- `GET /api/permissions`、`POST /api/permissions/allow`、`POST /api/permissions/remove`：审批白名单管理
- `POST /api/auth/login` / `GET /api/auth/me`：登录与用户信息

## 和普通聊天网页的区别

如果只聊天，lc-agent 和普通聊天网页都能完成任务。

lc-agent 真正多出来的是：
- 你能看见 Agent 在做什么
- 你能控制 Agent 可以用什么
- 你能把多个能力源拼起来：工具、MCP、Skills、子 Agent、自定义 Graph
- 你不需要自己再做前端、会话、审批、trace、调试面板

简化理解：
- **普通聊天网页**：更像对话产品
- **lc-agent**：更像可直接运行、也可二次开发的 Agent 工作台

## 登录和部署边界

lc-agent 已经支持登录认证、用户隔离、管理员能力。

但它的定位不是纯云端托管聊天站，而是一个可以接本地工具、MCP、脚本和执行环境的 Agent 框架。因此更适合：
- 单机部署
- 内网部署
- 用户自己可控的服务器或工作机

如果你给 Agent 接了文件系统、命令执行或自定义 MCP，它运行的仍然是**部署机器的权限边界**。

## README 没展开但你可能会关心的点

- 代码型 Agent 也可以显示 HTTP traces，建议用 `create_traced_chat_openai()` 包装底层 LLM
- 子 Agent 的展示和主 Agent 一样会进入会话历史
- 审批白名单是持久化的，不是本次会话临时状态
- Agent 编辑器支持基础配置、权限配置、LLM 参数、子 Agent 配置、通用子 Agent 开关

## 开发

```bash
pip install -e ".[dev]"
pytest
```

前端：

```bash
cd frontend
npm install
npm run dev
npm run build
```

如果你是基于这个框架做业务项目，建议直接参考：
- [lc-agent-bfzs](https://github.com/ydf0509/lc-agent-bfzs)

## 快问快答 
### 1 lc-agent 是否有rag知识库功能
答：lc-agent 不内置自带知识库，nbrag也是本人开发，将nbrag mcp配置到mcpservers里面即可，这样更解耦，因为这种知识库是agentic serach的，并且能接入到任何agent中，例如 openclaw claudecode codex trae cursor workbuddy qoder 中等等。

## License

MIT
