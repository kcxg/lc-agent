# lcagent_as_mcp 任务计划

> 目标：让 lc-agent 自己的服务端口同时是一个标准 MCP server，把指定 agent 暴露成 MCP 工具，  
> 使 Claude Code / Codex CLI / Cursor / Cline / Continue 等任意 MCP 客户端能直接调用 lc-agent 的 agent。
>
> 整理日期：2026-09-08（grill 讨论后定稿）  
> 状态：**首版已实现，后被双工具模式取代**（2026-09-09）。首版是 N 工具模式
> （每个 agent 一个 `lcagent__<slug>` 工具），现已改造为固定 2 个工具
> （目录 + 调用），见 `docs/tasks/lcagent_as_mcp_two_tools.md`。
> 本文保留设计依据与历史记录，§3.4 的工具生成规则、slug 化命名等
> 已不适用于当前代码；模块结构、挂载、服务用户、安全闸等仍有效。

---

## 0. 先说清最容易混淆的一件事

lc-agent 里已经有一套叫 "mcp" 的代码，它和本功能是**两回事**：

|    | 现有 `mcp` 代码                                     | 本功能 `lcagent_as_mcp`           |
| -- | ----------------------------------------------- | ------------------------------ |
| 位置 | `lc_agent/mcp/`、`lc_agent/server/routes/mcp.py` | `lc_agent/lcagent_as_mcp/`（新建） |
| 角色 | lc-agent 作为 **MCP 客户端**，去连别人的 MCP 服务器           | lc-agent 作为 **MCP 服务端**，给别人调用  |
| 端点 | `/api/mcp`、`/api/mcp/refresh` 等（管理接口）           | `/mcp`（协议端点）                   |
| 语义 | 管理"我连了哪些第三方工具"                                  | "别人可以把我的 agent 当工具用"           |

两者前缀不同，路由层面零冲突（已核实：`/mcp` 根路径当前未被占用）。  
**命名统一用 `lcagent_as_mcp`，代码、配置、文档一律不加 `mcp` 单独字样，避免和现有代码混。**

---

## 1. 目标与非目标

### 目标

- lc-agent 服务端口挂一个标准 MCP 端点（默认 `/mcp`），走 Streamable HTTP
- 被勾选 `can_be_subagent` 的 agent，各生成一个 MCP 工具
- 外部 MCP 客户端重连时，能拿到最新的 agent 工具列表（**服务不重启**）
- token 用量能正常记到用量看板里，不出现空白用户

### 非目标（本期不做）

- 不做实时推送：不实现 `tools/list_changed` 通知，客户端重连才更新
- 不做多轮会话：一次 `tools/call` = 一次独立运行
- 不做鉴权：MCP 端点不校验身份（依赖只监听 127.0.0.1）
- 不做 A2A：见 §2

---

## 2. 为什么先做 MCP 而不是 A2A

已核实的事实（2026-09-08 检索）：

- A2A 生产落地是实的：150+ 组织，Azure AI Foundry / Bedrock AgentCore / Vertex AI 原生支持，  
  LangGraph、CrewAI 已有原生集成，5 个官方 SDK，Linux Foundation 治理
- **但调用方是企业编排系统，不是 coding agent 客户端**。  
  Claude Code / Codex CLI / Cursor / Trae / WorkBuddy 全都只认 MCP，没有原生 A2A。  
  连 `a2abridge` 都是"把 A2A 包成一个 MCP server"IDE 才看得见

结论：A2A 对 lc-agent 是**标准合规门票**，不是"被别人调用"的通道。`docs/tasks/a2a.md` 保留不动。

补充定性：MCP 表达不了"长任务 + 中途要人确认 + 可中断恢复"，那是 A2A 任务状态机的强项。  
所以是**暂缓**，不是取消。

---

## 3. 设计决策

### 3.1 协议与实现层：官方 SDK 的 low-level Server

**不用 FastMCP。** 协议层面两者完全等价（FastMCP 输出的也是标准 MCP，客户端无感），  
分歧只在"谁来生成那些标准响应"：

- FastMCP 的核心价值是"从静态 Python 函数的签名 + docstring 自动生成 inputSchema"
- lc-agent 的工具是**数据库驱动的动态工具**，没有静态函数可以反射 → 该价值归零
- 所有动态工具参数统一（就一个 `prompt`），inputSchema 手写一次即可
- 反过来说，用 FastMCP 要在 preset 增删改的每个入口挂 `add_tool`/`remove_tool` 钩子，漏一处就不同步

实现用 `mcp.server.lowlevel.Server`（已确认本机 SDK 有 `@server.list_tools()` 装饰器  
`lowlevel/server.py:434`、`@server.call_tool()` `:492`）。协议正确性、能力协商、错误处理、  
JSON-RPC 封装全部由 SDK 保证，只手写两个 handler。

`mcp>=1.0` 已在依赖里（现在当客户端用），**不需要新增依赖**。

### 3.2 端点：1 个，默认 `/mcp`

Streamable HTTP 是单端点，三种 HTTP 方法：POST（请求）/ GET（SSE 流）/ DELETE（终止会话）。  
JSON-RPC 核心方法 3 个：`initialize`、`tools/list`、`tools/call`。

**三个已确认的实现坑：**

1. **路径重复**：`streamable_http_app()` 内部路由默认就是 `/mcp`（`fastmcp/server.py:166`），  
   直接 `app.mount("/mcp", ...)` 会变成 `/mcp/mcp`。用 low-level 自建则无此问题。
2. **子 app 的 lifespan 不会自动执行**（Starlette 行为）。`StreamableHTTPSessionManager` 必须在  
   lifespan 里 `run()`（源码注释 97-104 明说），所以要在 lc-agent 的 FastAPI lifespan 里手动跑。
3. **注册顺序**：`mount_static_files()` 是在 `create_app()` 返回之后调用的独立函数，mount 到 `/`  
   （`lc_agent/server/app.py:79`）。`/mcp` 必须注册在它**之前**，否则被静态文件吃掉，  
   表现为访问 `/mcp` 返回前端 HTML。

可用 `stateless_http=True`（不需要 SSE 长连接）。

### 3.3 刷新语义：每次 `tools/list` 实时查库

不做启动期快照，不做任何缓存。`list_tools` handler 每次被调用时查 `agent_presets` 表，  
返回当前可暴露的 agent。

因此：服务永不重启；客户端刷新重连 → 拿到最新能力。**不实现 `tools/list_changed` 通知。**

### 3.4 工具生成规则

| 项         | 规则                                                             |
| --------- | -------------------------------------------------------------- |
| 暴露条件      | `can_be_subagent == True` **且** 工具组不含 `file_write` / `command` |
| 工具名       | `lcagent__<slug>`。agent 名可能是中文，需 slug 化（MCP 工具名有字符集限制）         |
| 工具描述      | 复用 `default_delegation_description`                            |
| 输入 schema | 固定：`{"prompt": {"type": "string"}}`，`required: ["prompt"]`     |

**安全闸**：含 `file_write` / `command` 的 agent 不允许暴露。  
理由——勾 `can_be_subagent` 时用户心里的语义是"内部可委派"，  
不该顺带把本机文件和命令执行能力对外部开放。不满足条件时跳过并在日志明确打印原因。

### 3.5 执行身份：自动创建 `lcagent_as_mcp_user`

框架启动时自动确保存在一个服务用户，所有 MCP 调用归属它，用量记它头上。

| 字段              | 值                                     |
| --------------- | ------------------------------------- |
| `username`      | `lcagent_as_mcp_user`（可由配置覆盖）         |
| `role`          | `user`（**不是 admin**，避免 MCP 通道拿到管理员权限） |
| `password_hash` | 随机值，不可登录                              |

> ⚠️ **已核实的坑**：`UserAgentAccess` 是**白名单**机制。  
> `automation.py:284` 是 `if user.role == "admin" or agent_id == "chat": return True`，  
> 否则必须有 `UserAgentAccess` 记录；`agents.py:436` 也只返回已授权的 agent。  
> 所以服务用户作为普通 `user` 角色，**默认一个 agent 都调不动**。
>
> **处理办法（待你确认，见 §7）**：MCP 执行路径不查 `UserAgentAccess`，  
> 只按 §3.4 的两道过滤判定。理由：服务用户是系统内部账号不是真人，  
> 且 `can_be_subagent` 已经是明确的暴露条件，再叠加一层白名单只会让配置互相打架。

> 🔴 **角色必须是 `user`，永远不能是 `admin`。**
> MCP 端点本期不鉴权——如果服务用户是 admin，任何能访问 8001 的人就等于拿到了
> lc-agent 的管理员权限（所有 agent 可见、绕过所有访问控制）。这个组合是灾难性的。
> 即使将来给 MCP 加了鉴权也不应给 admin：MCP 通道只需要"能调用指定 agent"，不需要管理权限。

**管理界面里的处理**：该用户会出现在用户列表，需标记为"系统账号"、角色不可改、不可删除，
否则管理员手滑把它改成 admin 就会打开上面的口子。由 `docs/tasks/user_role_management.md` 统一处理。

### 3.6 鉴权：本期不做

MCP 端点不校验身份，依赖只监听 `127.0.0.1`。

已知风险：部署到局域网/公网等于把 agent 能力完全开放。**文档和日志里必须写清这个前提。**

后续若要鉴权：主流客户端都支持自定义 header（Cursor `.cursor/mcp.json` 的 `headers`、  
Claude Code `claude mcp add --header`、Cline / Continue / Windsurf / Gemini CLI 均支持），  
落地无障碍。但 lc-agent 现有 JWT 有过期时间，不适合写死在客户端配置里，届时应新增长期 API Key 表。

---

## 4. 模块结构（独立目录，不污染现有代码）

```
lc_agent/lcagent_as_mcp/
├── __init__.py          # 只对外暴露 setup_lcagent_as_mcp(app, config)
├── mounting.py          # 挂到 FastAPI：处理路径注册顺序 + lifespan 里跑 session manager
├── server.py            # low-level Server，实现 list_tools / call_tool 两个 handler
├── tool_builder.py      # 查库 → 工具列表（暴露过滤、slug 化、description、inputSchema）
├── runner.py            # 执行一次 agent run，返回最终文本
├── service_user.py      # 启动时确保 lcagent_as_mcp_user 存在
└── config.py            # 本功能的配置 schema 片段
```

边界约定：

- 本目录**不修改** `lc_agent/mcp/`（客户端）和 `lc_agent/server/routes/mcp.py`（管理接口）任何一行
- 与框架的接触点只有三处：`app.py` 里加一行挂载调用、lifespan 里加一行 `run()`、config schema 加一段
- `runner.py` 复用现有 agent 执行链路，不自己拼 LLM 调用

---

## 5. 配置项

```jsonc
{
  "lcagent_as_mcp": {
    "enabled": true,
    "path": "/mcp"
  }
}
```

服务用户名**不在本段**，在 `auth.service_username`（默认 `lcagent_as_mcp_user`）——
因为它是用户体系的一部分，角色管理功能也要读它（见 `docs/tasks/user_role_management.md` §2.2）。

---

## 6. 数据改动

**不新增表。** 只在启动时确保 `users` 表里有一条 `lcagent_as_mcp_user` 记录。  
`llm_usage.user_id` 填该用户 id，用量看板按用户聚合时是一个独立分组。

---

## 7. 实现步骤（按此顺序，每步可独立验证）

| 步 | 内容                            | 验证方式                                    |
| - | ----------------------------- | --------------------------------------- |
| 1 | 目录骨架 + 挂载到 `/mcp`，先返回空工具列表    | MCP 客户端能连上、握手成功、工具数为 0                  |
| 2 | `list_tools` 实时查库生成工具         | 客户端看到 `lcagent__*` 工具，改 preset 后重连能看到变化 |
| 3 | `call_tool` 跑一次 agent 并返回最终文本 | 客户端调用能拿到结果，用量看板出现记录                     |
| 4 | 服务用户 + 用量归属                   | 用量看板不出现空白用户                             |
| 5 | 危险工具组过滤                       | 开了 `command` 的 agent 不出现在工具列表，日志有原因     |
| 6 | 前端/文档提示：MCP 端点无鉴权，务必只监听本机     | —                                       |
| 7 | 修复：Starlette 1.2.1 `Mount("/mcp")` 匹配不到裸路径 `/mcp`（正则要求尾斜杠），请求落到静态文件兜底返回 405/404。`mounting.py` 改用 `Route` 精确匹配 | 重启 bfzs 后 curl `POST /mcp` initialize/tools/list 全通（2026-09-09）|

---

## 8. 待确认（我给了推荐值，你说改就改）

1. **服务用户是否绕过 `Use`*`rAgentAccess`****&#x20;— 推荐：绕过，只按 §3.4 两道过滤。见 §3.5 的红字*
   - *备选：建用户时给所有 `can_be_subagent` 的 agent 插 `UserAgentAccess`* 记录。  
     缺点：agent 是动态变的，新增 agent 时要同步维护，容易漏
2. **`auth.secret` 未配置（匿名 admin 模式）时怎么办** — 推荐：照常创建服务用户并归属，  
   MCP 端点行为不变。理由：MCP 本来就不鉴权，有没有 auth 不影响它
3. **每次调用是否新建会话** — 推荐：是，一次调用 = 一次独立运行。多轮以后再说
4. **是否暴露 `project_mode` 的 agent** — 推荐：先不特殊处理，同样按 `can_be_subagent` 判定
