# 自动化定时任务实现计划

> 状态：第一版已实现，待后续继续增强。
>
> 目的：持久化当前讨论结论，后续实现以本文档为准，避免上下文压缩后丢失产品边界或执行语义。

## 1. 已确认的产品方向

lc-agent 增加“自动化任务”能力。用户可以让某个 Agent 按指定时间或周期，自动执行一段任务指令。

第一版的核心心智模型是：

```text
自动化任务 = Agent + 调度规则 + 任务指令
```

自动化任务只选择 Agent，不让用户在任务表单里重复配置项目、Tools、MCP、Skills。Agent 是完整能力单元，执行时读取该 Agent 当前配置。

## 2. 用户入口与界面边界

### 2.1 入口位置

在右侧面板的“输入框动画”区域下面，增加独立的“自动化任务”区域：

```text
输入框动画
自动化任务
    创建定时任务
    已配置数量 / 最近一次 / 下次执行
```

右侧面板是快捷入口，因为这里天然对应当前 Agent 和当前工作上下文。

第一版不增加顶部一级导航，也不把任务配置放到 Tools、MCP 或 Skills 面板中。

### 2.2 入口与管理职责

右侧入口负责：

- 快速打开创建表单
- 默认带入当前 Agent
- 显示少量任务状态

自动化任务抽屉负责：

- 创建任务
- 查看已配置任务
- 启用或暂停任务
- 立即执行
- 查看执行历史
- 进入某次执行产生的会话

任务数量和执行历史增加后，可以在同一个抽屉中使用两个 Tab：

```text
已配置    执行历史
```

不在右侧面板中展示完整的任务表格，避免被模型、Markdown、Tools、MCP 等配置内容挤压。

### 2.3 创建表单

第一版只暴露以下字段：

```text
任务名称
选择 Agent
执行周期
任务内容
```

创建时默认选中当前 Agent，但允许切换到其他可用 Agent。

执行周期使用普通用户可理解的选项，不直接暴露 Cron 表达式：

```text
一次性
每隔一段时间
每天指定时间
每周指定时间
```

时间默认使用后端运行环境的本机时区。表单必须明确显示当前时区，避免用户误以为使用浏览器时区。

第一版不提供以下配置：

- 单独选择项目
- 单独选择 Tools
- 单独选择 MCP
- 单独选择 Skills
- Cron 表达式编辑器
- 自动重试次数
- 通知渠道
- 依赖任务编排
- Agent 配置快照选项

## 3. 领域对象与术语

### 3.1 自动化任务 AutomationTask

表示用户配置的一项长期任务，负责描述“哪个 Agent 在什么时间执行什么指令”。

建议字段：

```text
id
user_id
name
agent_id
prompt
schedule_type       one_time | interval | daily | weekly
schedule_config     JSON，保存对应周期的规范化参数
timezone
enabled
next_run_at
last_run_at
last_status
created_at
updated_at
```

`agent_id` 是引用关系，不复制 Agent 的模型、工具、MCP、Skills 或项目配置。

### 3.2 自动化执行 AutomationRun

表示自动化任务的一次实际触发，负责记录“这一次是否执行、执行结果是什么”。

建议字段：

```text
id
task_id
user_id
session_id
status              pending | running | success | failed | skipped
scheduled_at
started_at
finished_at
error
created_at
```

`AutomationTask` 是计划，`AutomationRun` 是一次事实记录。不能只在任务表上覆盖最后状态，否则无法查看历史、定位失败或重新执行。

### 3.3 执行会话 Execution Session

每次自动化执行都创建独立的 `SessionMeta` 会话，并通过 `AutomationRun.session_id` 关联。

会话标题建议为：

```text
[自动化] 每日 AI 新闻 · 2026-08-27 09:00
```

执行会话使用被绑定 Agent 的当前配置，但不复用当前聊天会话，也不把结果插入用户当前对话。

## 4. Agent 绑定语义

### 4.1 只保存 Agent ID

创建任务时保存 `agent_id`。触发执行时重新解析该 Agent，读取其当前模型、提示词、Tools、MCP、Skills、项目模式和 Graph 配置。

这样保持任务表单简单，并符合用户直觉：修改 Agent 后，绑定它的自动化任务也使用最新 Agent 行为。

### 4.2 Agent 删除或不可用

如果绑定的 Agent 被删除、代码 Agent 未注册，或项目路径已不可访问：

- 不静默改绑其他 Agent
- 本次执行不调用模型
- 任务标记为不可执行或记录 `failed`
- 前端显示明确原因
- 用户可以编辑任务重新选择 Agent

保存任务时应检查 Agent 是否存在；运行时仍需再次检查，因为 Agent 可能在保存后被删除或失效。

## 5. 后端执行架构

```text
FastAPI lifespan
        ↓
AutomationScheduler
        ↓ 触发到期任务
AutomationRunner
        ↓ 创建 AutomationRun 和独立 SessionMeta
AgentRunService
        ↓
AgentEngine.chat_stream(...)
        ↓
消息、工具调用、用量、HTTP trace、文件变更持久化
```

### 5.1 调度器

调度器运行在后端应用生命周期内，浏览器关闭不影响任务。第一版的前提是后端 Python 进程仍然运行；暂不做 Windows 系统服务、云端 Runner 或分布式调度。

调度器必须满足：

- 启动时从数据库加载所有启用任务
- 计算并注册下一次触发时间
- 创建任务、更新任务、暂停任务后立即刷新调度状态
- 应用关闭时停止调度并清理后台任务
- 不依赖前端页面或 SSE 连接保持运行
- 不把任务实现成“定时模拟点击前端发送按钮”

调度实现优先使用成熟的异步调度器，不手写 Cron 解析和时区/DST 规则。实现阶段需要根据当前 Python 环境验证所选库的 API；任务数据仍以 SQLite 为事实来源，不依赖调度器内存状态恢复。

第一版按单 Python 进程设计。使用多个 Uvicorn worker 时必须明确禁止或防止多个 scheduler 同时执行同一任务；不能默认假设进程内锁可以解决跨进程重复执行。

### 5.2 Runner

Runner 负责一次完整的生命周期：

1. 校验任务仍然启用。
2. 校验 Agent 存在且可构建。
3. 以原子方式声明本次执行，避免同一任务被重复领取。
4. 创建独立执行会话和 `AutomationRun`。
5. 调用公共 Agent 执行服务。
6. 持久化用户消息、助手消息、工具调用、用量、HTTP trace 和文件变更。
7. 更新 `AutomationRun.status` 与任务的最近状态/下一次时间。

Runner 不应伪造 REST 请求，也不应通过 HTTP 回调本机 SSE。应抽取或复用后端内部的公共执行服务，让 SSE 聊天和自动化任务共享 Agent 执行、事件分类和持久化语义。

第一版已新增 `AgentRunService` 供自动化 Runner 使用，聊天 SSE 暂时保留原有流式路径；两者复用了同一套 Agent Engine、事件分类和持久化底层函数，后续可以在低风险时再把聊天入口也收敛到该服务。

### 5.3 并发语义

同一个自动化任务同时只允许一个运行实例。

如果上一次运行仍未结束，下一次触发：

- 不排队
- 不并发执行
- 创建一条 `skipped` 执行记录
- 计算下一次正常触发时间

第一版需要同时考虑进程内锁和数据库领取条件。仅使用 `asyncio.Lock` 不能覆盖多 worker 或进程重启场景。

### 5.4 失败语义

第一版不自动重试。失败时记录：

- 错误类型
- 面向用户的错误消息
- 技术错误详情或日志关联信息
- 开始和结束时间
- 对应执行会话（如果会话已经创建）

历史页面提供“重新执行”操作。重新执行应创建新的 `AutomationRun` 和新的执行会话，不覆盖原失败记录。

自动重试暂缓到后续版本，原因是任务可能修改文件、发送请求或产生外部副作用，无法默认假设操作幂等。

## 6. 持久化与数据库

建议在 `lc_agent/db/models.py` 增加两张表：

```text
automation_tasks
automation_runs
```

不删除现有 SQLite 数据，不重建现有表，不把任务数据塞进 `sessions` 或 `chat_ui_messages` 的 JSON 字段。

迁移要求：

- 新增 Alembic migration
- 保留已有 sessions、presets、messages、checkpoints 数据
- 新表字段包含创建时间和更新时间
- `user_id` 建索引
- `task_id`、`session_id` 建索引
- 运行历史按创建时间或计划时间倒序查询

现有 `SessionMeta` 不需要为了自动化强行增加任务字段，执行归属由 `AutomationRun.session_id` 负责关联。这样可以最大程度复用已有会话和消息展示逻辑。

## 7. REST API 草案

路由统一放在新的 `lc_agent/server/routes/automation.py`：

```text
GET    /api/automation/tasks
POST   /api/automation/tasks
GET    /api/automation/tasks/{task_id}
PUT    /api/automation/tasks/{task_id}
DELETE /api/automation/tasks/{task_id}
POST   /api/automation/tasks/{task_id}/pause
POST   /api/automation/tasks/{task_id}/resume
POST   /api/automation/tasks/{task_id}/run
GET    /api/automation/tasks/{task_id}/runs
GET    /api/automation/runs
POST   /api/automation/runs/{run_id}/rerun
```

API 必须执行用户隔离：普通用户只能读取、修改和执行自己的任务；管理员可以按现有权限规则管理全部任务。

创建任务的请求不接受 `tools`、`mcp`、`skills`、`project_root` 等重复配置字段，避免前后端逐渐形成第二套 Agent 配置系统。

## 8. 前端实现边界

预计新增或修改：

```text
frontend/src/components/layout/RightPanel.vue
frontend/src/components/automation/AutomationSection.vue
frontend/src/components/automation/AutomationDrawer.vue
frontend/src/stores/automation.ts
frontend/src/api/http.ts
frontend/src/App.vue（仅在需要挂载全局抽屉时修改）
```

右侧区域需要处理：

- 当前 Agent 改变后，创建表单默认 Agent 跟随当前 Agent
- 当前 Agent 为代码 Agent 时，仍可选择其他可用 Agent；若代码 Agent 可以被任务执行，需要后端明确其生命周期和可用性
- 任务加载失败时显示错误状态，不阻塞聊天
- 任务执行状态刷新不能影响右侧其他配置
- 移动端右侧面板打开时入口仍可用

任务抽屉需要处理：

- 空状态
- 创建中、保存中、删除中、立即执行中
- 已暂停、执行中、成功、失败、跳过、Agent 不可用
- 长 Prompt 展开/收起
- 执行历史进入独立会话
- 删除确认

## 9. 分阶段实现顺序

### 阶段 1：领域模型和数据库

- [x] 增加 `AutomationTask` 与 `AutomationRun` 模型
- [x] 增加数据库 repository
- [x] 增加 Alembic migration
- [x] 测试任务、执行记录、用户归属和索引查询

### 阶段 2：内部执行服务

- [x] 梳理 `sse.py` 当前 Agent 执行与持久化流程
- [x] 抽取独立执行所需的 `AgentRunService`
- [x] 支持独立 thread/session 执行
- [x] 覆盖成功、异常、Agent 不存在、项目不可用
- [x] 确认工具调用、用量、HTTP trace、文件变更的持久化一致性

### 阶段 3：调度器和 Runner

- [x] 启动时加载启用任务
- [x] 支持一次性、间隔、每天、每周
- [x] 支持暂停、恢复和任务修改后重新调度
- [x] 实现同任务单实例约束
- [x] 记录 skipped，不做第一版自动重试
- [x] 应用关闭时停止调度器

### 阶段 4：REST API

- [x] 增加任务 CRUD
- [x] 增加立即执行、暂停、恢复
- [x] 增加任务执行历史
- [x] 增加失败执行重新执行
- [x] 增加用户权限隔离和 Agent 存在性校验

### 阶段 5：前端入口和抽屉

- [x] 在右侧“输入框动画”下面增加自动化入口
- [x] 创建表单默认当前 Agent
- [x] 增加已配置任务列表
- [x] 增加执行历史和跳转执行会话
- [x] 增加加载、空状态、错误、暂停和执行中状态
- [x] 检查桌面端、窄窗口和移动端布局

### 阶段 6：验证和运行检查

- [x] Python 3.12 编译检查
- [x] 自动化 repository/API/runner/scheduler 测试
- [x] 前端 typecheck/build
- [x] 验证关闭浏览器后任务仍可执行（后端生命周期接入）
- [x] 验证后端重启后启用任务可以恢复
- [x] 验证同一任务不会重复执行（单进程锁和 active run 检查）
- [x] 验证失败重执行不会覆盖历史
- [x] 验证不删除现有 SQLite 数据

## 10. 验收标准

功能完成必须满足：

1. 用户可以从右侧面板打开自动化创建入口。
2. 创建任务只需要选择 Agent、填写任务指令和周期。
3. 用户不需要重复选择项目、Tools、MCP、Skills。
4. 浏览器关闭后，只要后端进程仍在，任务仍会按计划触发。
5. 每次执行都有独立会话和独立运行记录。
6. 当前聊天不会被自动化结果污染。
7. 任务执行时使用绑定 Agent 的当前配置。
8. Agent 不存在时不会静默换绑其他 Agent。
9. 同一个任务不会重叠执行，重叠触发会记录 `skipped`。
10. 第一版失败不自动重试，但可以手动重新执行。
11. 普通用户不能读取或操作其他用户的自动化任务。
12. 后端重启后启用任务可以重新加载。

## 11. 暂缓事项

以下能力不进入第一版实现范围：

- Cron 表达式
- 分布式 scheduler
- Windows 系统服务安装器
- 云端任务执行器
- 邮件、Webhook、桌面推送等通知渠道
- 自动重试和死信队列
- 任务依赖、DAG 编排
- Agent 配置快照或版本锁定
- 多 Agent 协作任务

这些功能需要先有稳定的任务模型、执行历史和失败语义，再单独讨论。

## 12. 第一版验证记录

- 定向自动化、路由、Agent、Session、Skills 测试：`37 passed`
- 前端 `vue-tsc --noEmit && vite build`：通过
- 完整测试集：`300 passed, 4 failed`；4 个失败为仓库原有 middleware 顺序、MCP generation 和 contrib `print` 扫描测试，不涉及自动化功能
- Python 3.12 编译检查、Ruff、`git diff --check`：通过
- 演示服务已在 `http://127.0.0.1:8001` 启动，健康检查返回 200；自动化接口在认证开启时未登录返回认证失败
- Alembic 当前仍存在历史多 head，初始化会安全回退到 `SQLModel.metadata.create_all()`；本次没有合并可能触碰现有聊天数据的历史 migration，也没有删除 SQLite 数据
