# 去掉 `db_url` 层层传递：统一走全局业务库会话

> 痛点：`db_url` 从 `LcAgentApp` → `sse.configure()` → 30+ 处 `persistence.*(db_url, …)` →
> `SubAgentRunTracker(db_url=…)` → `persistence`，另有 `AutomationScheduler/Runner`、
> `AgentRunService` 各自存一份 `self.db_url` 再往下传，最深 4 层。
> 目标：业务库访问全部改为无参 `get_business_async_session()`，删除所有 `db_url` 形参、
> 成员与模块全局快照。
>
> 状态：已实施（2026-09-09，全量 405 passed）。§7 三个问题按文档内建议执行：
> 不改名、保留 `app.state.db_url`、不加额外友好错误。

---

## 0. 目标与非目标

**做**

- 删除业务库 `db_url` 的全部显式传递：`persistence.py`（13 个函数首参）、
  `usage_recorder.record_usage` 首参、`SubAgentRunTracker` 构造参、
  `sse._db_url` 模块全局、`AutomationRunner/Scheduler.self.db_url`、
  `AgentRunService.self.db_url`。
- 统一收口到 `lc_agent/db/engine.py:39 get_business_async_session()`（无参，读全局配置）。
- 合并 `routes/agents.py:23`、`routes/prompts.py:18` 各自的私有 `get_db()` 到
  `server/dependencies.py:20 get_db_session`（三者行为完全一致，都是
  `get_async_session(get_database_url())`）。
- 测试迁移到 `set_config({"database": {"url": tmp}})` 注入隔离库（已有先例，见 §3）。

**明确不做**

- 不碰 checkpoint 通道（见 §1，它本来就是独立的，没有 `db_url` 可删）。
- 不保留 `db_url=None` 兼容形参：直接改签名（项目无历史包袱；`bfzs` 零调用，见 §4 Step 0）。
- 不改 `app.py` 启动路径的 `self._db_url`（`init_db`、`_init_auth`、`_load_presets_from_db`
  是启动时一次性使用，不属于"层层传递"）和 `app.state.db_url`（`routes/admin.py:415`
  vacuum 运维接口在用）。
- 不改 `db/migrations/env.py` 的 `db_url`（Alembic CLI 通道，无关）。

---

## 1. 先回答：`db_url` 全部指业务库，不可能是 checkpoint

命名即答案：`get_business_async_session` 里的 "business" 就是相对 checkpoint 而言的。
实证（`rg "db_url|checkpoint" lc_agent --type py` 全量结果分类）：

| 通道 | 来源配置 | 消费方式 | 经过 `db_url` 参数？ |
|------|----------|----------|----------------------|
| 业务库（sessions / chat_ui_messages / presets / llm_usage / users / automation…） | `database.url`（`config/schema.py:20`） | `get_async_session(db_url)` → SQLAlchemy AsyncSession → SQLModel 表 | **是，全部** |
| checkpoint（LangGraph 线程状态） | `database.checkpoint_path` / `database.checkpoint_url`（`config/schema.py:21-25`） | `app.py:151 build_checkpointer(self._checkpoint_url)` → `AsyncSqliteSaver` / `AsyncPostgresSaver`（`core/checkpointer.py:57`） | **否，零交集** |

- `app.py:82-90` 把两者存成两个独立成员 `self._db_url` / `self._checkpoint_url`，
  从源头就没有混用。
- 全仓库唯一的交集是 `routes/admin.py:415-438` 的 vacuum 运维接口，同时读
  `app.state.db_url` 和 `app.state.checkpoint_path` 做清理展示——读 state，不参与传递链。
- 所以放心删：要删的 `db_url` 参数**语义单一**，全是"业务库 URL"。

---

## 2. `db_url` 传递链全景（现状）

源头：`LcAgentApp.__init__` 从 config 读 `database.url`，经 `_resolve_sqlite_url`
（相对路径按 `project_root` 解析为绝对）存 `self._db_url`（`app.py:82`），再分三路：

**A. sse 链（最粗）** — `app.py:126 sse.configure(engine, db_url)` → 模块全局
`sse.py:39 _db_url` → 20+ 处 `persistence.*(_db_url, …)`、`record_usage(_db_url, …)`，
以及 `SubAgentRunTracker(db_url=_db_url)`（`sse.py:399,727`）→ tracker 内部再调
`persistence.create_subsession / save_subsession_delegation_message / finalize_subsession_message`
（`subagent_tracker.py:126,138,209`）。另有 3 个鉴权函数每次现场读全局
（`sse.py:129,149,176`：`get_async_session(get_database_url())`，与 business 版等价）。

**B. automation 链** — `app.py:127 AutomationScheduler(engine, db_url, app)` →
`automation.py:239,530` 两级构造存 `self.db_url` → 17 处 `get_async_session(self.db_url)`
（`automation.py:253,277,301,324,345,355,381,413,449,459,473,508,519,544,583,596,603,620`）。

**C. agent_runner 链** — `AgentRunService.__init__` 构造时读一次全局
（`agent_runner.py:33 self.db_url = get_database_url()`），之后 8 处往
`persistence` / `record_usage` / `SubAgentRunTracker` 传（`agent_runner.py:61,66,75,122,137,162,172,184,202`）。
`lcagent_as_mcp/runner.py:49` 调的正是这个 service。

**D. 路由层（伪传递，可直接合并）** — 大部分路由用 `dependencies.get_db_session`
（内部 `get_async_session(get_database_url())`）；只有 `routes/agents.py:23` 和
`routes/prompts.py:18` 各自复制了一份同名私有 `get_db()`，行为一字不差。

**已是无参模式的孤岛**（不动）：`lcagent_as_mcp/tool_builder.py:42`、
`lcagent_as_mcp/runner.py:29` 直接用 `get_business_async_session()`——证明无参模式在
生产/MCP 路径已跑通。

---

## 3. 当初为什么传参，现在为什么能删

- 传参的唯一实质理由是**测试隔离**：各测试用 `tmp_path` 建临时库、`:memory:` 库，
  靠显式传参互不干扰。
- 但隔离已有不靠传参的成熟模式：`tests/test_automation.py:15-22` 的 `db_url` fixture
  做法是 `reset_engine()` + `set_config({"database": {"url": tmp_url}})` + `init_db(url)`，
  之后被测代码无论显式还是全局拿到的都是同一隔离库。`test_lcagent_as_mcp.py:44` 同款。
  改造只是把这个模式推广为唯一模式。
- 生产侧恒等：`LcAgentApp.__init__` 就地修改全局 config 同一 dict 引用
 （`set_config` 持有同一引用，`test_config.py:272` 有断言），App 创建后
  `get_database_url()` 返回的就是 resolved 后的绝对 URL，与 `self._db_url` 相同值。
  因此生产行为不变（§6 有一条行为差异说明，属变好）。

---

## 4. 实施步骤

### Step 0 — 开工前确认（只读，不改代码）

1. `rg "SubAgentRunTracker\(|AutomationScheduler\(|AutomationRunner\(|AgentRunService\(|sse\.configure\(" lc_agent tests`
   确认构造调用点全集（本文档基于 2026-09-09 的 grep，实施时以实测为准）。
2. 确认 `bfzs` 无直接调用：已查 `rg persistence|record_usage|AutomationScheduler|AgentRunService|SubAgentRunTracker`
   在 `D:\codes\lc-agent-bfzs` 为零命中，开工时重跑一遍即可。

### Step 1 — `server/persistence.py`：删所有 `db_url` 首参（核心）

- 13 个函数：`get_session_message_count`、`get_session_user_message_count`、
  `ensure_session`、`increment_session_message_count`、`save_title`、`save_ui_message`、
  `truncate_from_message`、`load_resume_context`、`append_to_last_assistant_message`、
  `create_subsession`、`save_subsession_delegation_message`、`save_file_change`、
  `save_git_base_hash`、`finalize_subsession_message`（含经由它透传的两个）。
- 函数体内惰性导入由 `from lc_agent.db.engine import get_async_session` 改为
  `get_business_async_session`，`get_async_session(db_url)` 改为无参调用。
- 模块 docstring "All functions accept db_url as the first argument…" 同步改写。

### Step 2 — `server/usage_recorder.py`：`record_usage` 删 `db_url` 首参

- 两处 `get_async_session(db_url)`（`:78` 子会话反查、`:98` 批量 insert）改无参。

### Step 3 — `server/subagent_tracker.py`：删构造参 `db_url`

- `__init__` 删 `db_url` kwarg 及 `self.db_url`；三处 `persistence.*(self.db_url, …)`
  去掉首参。调用方（`sse.py:399,727`、`agent_runner.py:75`）同步删 `db_url=`。

### Step 4 — `server/sse.py`：删 `_db_url` 全局

- 删 `_db_url`、`configure(engine, db_url)` 的 `db_url` 形参（保留 `engine`）；
  20+ 处 `_db_url` 引用同步（全是传给 persistence/record_usage/tracker 的首参，删即可）。
- 3 个鉴权函数（`:129,149,176`）的 `get_async_session(get_database_url())`
  改为 `get_business_async_session()`；`DEFAULT_DATABASE_URL` import 不再需要则删。

### Step 5 — `server/automation.py`：删两级 `db_url`

- `AutomationRunner.__init__`、`AutomationScheduler.__init__` 删 `db_url` 形参及成员；
  17 处 `get_async_session(self.db_url)` 改无参。`app.py:127` 构造调用同步。

### Step 6 — `server/agent_runner.py`：删 `self.db_url`

- 删 `:33` 及 8 处传递。注意 `runner.py`（lcagent_as_mcp）调 `AgentRunService(engine)`
  构造不变。

### Step 7 — 路由层收敛

- `dependencies.get_db_session` 内部改 `get_business_async_session()`。
- 删除 `routes/agents.py:23`、`routes/prompts.py:18` 私有 `get_db()`，
  改为 `Depends(get_db_session)`（与 sessions/usage/file_changes/auth 等路由一致）。

### Step 8 — `app.py` 调用点更新（保留启动路径）

- `sse.configure(self.engine)`、`AutomationScheduler(self.engine, self.fastapi_app)`。
- `self._db_url`、`app.state.db_url`、`init_db`、`_init_auth`、`_load_presets_from_db`
  保持不动（启动/运维用途，非传递链）。

### Step 9 — 顺手删死代码（可选，同 PR）

- `lcagent_as_mcp/config.py:21 database_url()` 全仓库零调用，删除。

### Step 10 — 测试迁移

- 通用模式（照抄 `test_automation.py:15-22`）：fixture 内
  `reset_engine()` → 建 tmp 库 → `set_config({"database": {"url": url}})` →
  `await init_db(url)`；teardown `reset_engine()` + `reset_config()`。
  把该模式推广到所有自建 `db_url` fixture 的测试文件（`test_db.py:9`、
  `test_usage_stats.py:113` 等），并删掉显式传参。
- `tests/test_persistence_errors.py`：`monkeypatch.setattr(db_engine, "get_async_session", …)`
  改为 patch `get_business_async_session`；parametrize 里的 `"db"` 首参全部删除。
- `tests/conftest.py:40 setup_test_auth(app, db_url, …)`：删 `db_url` 形参，
  内部改无参（调用方改为依赖已注入全局配置的 fixture）。
- 注意基线 fixture `conftest.py:9 set_config({})` 下 `get_database_url()` 会回退
  `DEFAULT_DATABASE_URL`（`./lc_agent_data.db`，相对 cwd！）：改造后任何忘记注入
  `database.url` 的测试会写到 cwd 真实文件。建议在基线 fixture 中直接
  `set_config({"database": {"url": "sqlite+aiosqlite:///:memory:"}})` 兜底，
  并加一条断言/检查确保没有测试产生 `./lc_agent_data.db` 写操作。

---

## 5. 文件级改动清单（预估）

| 文件 | 改动 |
|------|------|
| `lc_agent/server/persistence.py` | 13+ 函数删首参，换无参 session |
| `lc_agent/server/usage_recorder.py` | `record_usage` 删首参 |
| `lc_agent/server/subagent_tracker.py` | 删构造参 |
| `lc_agent/server/sse.py` | 删 `_db_url` 全局 + `configure` 形参，~25 处 |
| `lc_agent/server/automation.py` | 删两级 `db_url`，17 处 |
| `lc_agent/server/agent_runner.py` | 删 `self.db_url`，8 处 |
| `lc_agent/server/dependencies.py` | 换 business 版 |
| `lc_agent/server/routes/agents.py`、`routes/prompts.py` | 删私有 `get_db`，用公共依赖 |
| `lc_agent/app.py` | 2 处构造调用 |
| `lc_agent/lcagent_as_mcp/config.py` | 删死函数（可选） |
| `tests/` | fixture 模式统一 + `test_persistence_errors.py` + `conftest.setup_test_auth` |

---

## 6. 风险与对策

1. **全局配置未就绪就访问 DB**：改造后 DB 访问隐式依赖 `get_config()`。
   生产由 `set_config_path` + `LcAgentApp` 保证（`lcagent_as_mcp` 已是此模式，无新增风险）；
   测试由 Step 10 的 fixture 保证。 sober 检查：`rg get_business_async_session` 确认新增调用点
   均在请求/任务上下文内，无模块顶层调用。
2. **快照变实时**：现在 `sse._db_url` 是 `configure()` 时的快照，改造后每次读实时全局。
   生产两者同值（§3）；若运行时有人改配置，新行为（实时生效）比旧行为（快照过期）更合理。
   反向风险无。
3. **`:memory:` 串扰**：engine 缓存以 URL 为 key，多测试共用 `:memory:` + `StaticPool`
   会串数据。对策：隔离库一律用 `tmp_path` 文件库（现有 fixture 皆如此），`:memory:` 只做基线兜底；
   保留 `reset_engine()` 的 fixture 调用。
4. **破坏性签名**：`persistence.*`、`record_usage`、`SubAgentRunTracker`、
   `AutomationScheduler/Runner`、`sse.configure`、`setup_test_auth` 全部变签。
   已确认 `bfzs` 零调用；框架内调用点在 Step 0 全集确认后一次性改完，不做过渡期兼容。

---

## 7. 待定问题（评审时定）

1. `get_business_async_session` 是否趁机改名（如 `get_db_session`）？建议**不改**：
   改名要动已有的两处 MCP 调用 + 所有新调用点，零收益，"business" 恰好 self-documenting
   了"这是业务库、不是 checkpoint"。
2. `app.state.db_url` 是否保留？建议保留（admin vacuum 要解析 sqlite 文件路径做
   `VACUUM`，需要 URL→路径，删了就得重构 vacuum）。
3. 是否给无参会话加一个"配置未就绪时 raise 友好错误"？`get_config()` 现在是
   `load_config` 失败直接 raise RuntimeError，信息尚可，可不做。

---

## 8. 验证标准

- `D:\ProgramData\Miniconda3\envs\py312\python.exe -m pytest tests/ -v` 看到 `N passed`
  汇总行（exit 0 不算数，见 dev-guide §5）。
- `rg "db_url" lc_agent --type py` 残留仅限：`app.py`（启动/state）、`routes/admin.py`
  （vacuum）、`db/migrations/env.py`（alembic）、`db/engine.py`（定义处）。
- `rg "get_async_session\(" lc_agent/server` 残留仅限 `app.py` 启动路径；
  其余全部为 `get_business_async_session()`。
- bfzs 冒烟：`cd D:\codes\lc-agent-bfzs` 启动 `--port 8001`，发一轮对话 + 触发一次
  子 agent + 跑一次定时任务（覆盖 A/B/C 三链），无 `TypeError: missing db_url` 类错误。
