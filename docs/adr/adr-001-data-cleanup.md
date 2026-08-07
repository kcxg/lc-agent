# ADR-001: 数据清理 / 瘦身功能

- 状态：已批准（Approved）
- 日期：2026-08-06
- 作者：lc-agent 开发团队

## 1. 背景

lc-agent 运行一段时间后，两个 SQLite 数据库会持续增长：

- **data 数据库**（默认 `./lc_agent_data.db`）：存储会话元数据、消息内容、Agent 配置、提示词模板等。
- **checkpoints 数据库**（默认 `./lc_agent_checkpoints.db`）：LangGraph 用于持久化对话状态，包含 checkpoints 和 writes 表。

当用户消息量很大时，这两个文件可能占用数 GB 磁盘空间，且没有内置的清理机制。因此需要提供一个"数据清理 / 瘦身"功能，让用户可以按保留天数删除历史会话及其关联数据。

## 2. 目标

1. 按 **session（会话）** 为清理单位，删除 X 天之前的完整会话数据。
2. 用户可以在前端选择"保留最近 X 天"。
3. 清理后显著减小 data 和 checkpoints 数据库体积。
4. 不删除 Agent 配置、提示词模板等框架配置数据。

## 3. 数据库结构

### 3.1 data 数据库

表定义位于 `lc_agent/db/models.py`：

| 表名 | 说明 | 是否清理 |
|------|------|---------|
| `prompt_templates` | 提示词模板 | 否 |
| `agent_prompt_bindings` | Agent-提示词绑定 | 否 |
| `agent_presets` | Agent 预设配置 | 否 |
| `sessions` | 会话元数据，`id` 即 `thread_id` | **是** |
| `chat_ui_messages` | 消息内容，`session_id` 外键 | **是** |

`SessionMeta` 关键字段：

- `id`: UUID，主键，等于 checkpoints 库中的 `thread_id`。
- `created_at`: 会话创建时间。
- `updated_at`: 会话最后更新时间，作为清理判据。
- `is_pinned`: 是否置顶。
- `pinned_at`: 置顶时间。
- `parent_session_id`: 父会话 ID（子 Agent 委派场景）。

### 3.2 checkpoints 数据库

由 LangGraph 的 `AsyncSqliteSaver` 初始化（`lc_agent/app.py`），包含：

| 表名 | 说明 | 是否清理 |
|------|------|---------|
| `checkpoints` | 每个 thread 的 checkpoint 状态 | **是** |
| `writes` | checkpoint writes 数据 | **是** |

两张表均以 `thread_id` 为键，与 `sessions.id` 一一对应。

## 4. 清理流程

```
1. 用户输入 keep_days（默认 30）
2. 计算 cutoff_time = now() - keep_days days
3. 查询 sessions 表中 updated_at < cutoff_time 的 id 列表；列表
   - 可选：跳过 is_pinned = true 的会话
   - 可选：跳过当前活跃会话
4. 对每个 session_id：
   a. 调用 engine.reset_thread(session_id) 删除 checkpoints 库中该 thread 的数据
   b. 删除 chat_ui_messages 中 session_id = id 的消息
   c. 删除 sessions 中 id = id 的会话记录
5. 返回统计信息：
   - deleted_sessions: 删除的会话数
   - deleted_messages: 删除的消息数
   - deleted_threads: 删除的 checkpoint thread 数
```

### 4.1 删除顺序

必须先删除 checkpoints，再删除 data 库中的消息和会话。原因：

- 如果 data 库删除失败，checkpoints 还可以重新关联（虽然需要重建 session 元数据）。
- 如果先删 data 再删 checkpoints，checkpoints 可能留下孤立数据。

### 4.2 并发安全

- SQLite 写操作是串行的，清理任务和其他请求不会并发写冲突。
- 但如果用户正在某个待删除 session 上聊天，可能会出现"会话正在使用"的情况。
- 建议清理前检查该 session 是否在当前活跃会话列表中，若活跃则跳过。

## 5. API 设计

> 注：实际路由前缀为 `/api/admin/...`（`create_app` 中 `include_router(admin_router, prefix="/api")` + router 自身 `prefix="/admin"`）。

### 5.1 清理接口

```http
POST /admin/cleanup
Content-Type: application/json

{
  "keep_days": 30,
  "skip_pinned": true,
  "skip_active": true,
  "active_session_ids": ["<current-open-session-id>", ...]
}
```

响应：

```json
{
  "deleted_sessions": 47,
  "deleted_messages": 1256,
  "deleted_threads": 47,
  "kept_sessions": 12,
  "errors": []
}
```

### 5.2 预览接口

```http
POST /admin/cleanup/preview
Content-Type: application/json
```

请求体与清理接口相同。预览接口使用 POST 是因为 `active_session_ids` 是列表参数，GET 传 list 不便。

响应：

```json
{
  "would_delete_sessions": 47,
  "would_delete_messages": 1256,
  "would_delete_threads": 47,
  "affected_session_ids": ["..."]
}
```

> `would_delete_threads` 等于 `would_delete_sessions`，因为每个 session 对应一个 thread；保留该字段是为了与清理接口响应字段对称。

### 5.3 数据库压缩接口（VACUUM）

SQLite 删除数据后文件体积不会自动缩小，需要手动 `VACUUM` 重建数据库文件回收空间。

```http
POST /admin/vacuum
```

响应：

```json
{
  "data": { "success": true, "path": "...", "error": null },
  "checkpoints": { "success": true, "path": "...", "error": null }
}
```

- 对 data 和 checkpoints 两个 SQLite 文件分别执行 `VACUUM`
- 使用独立连接，不依赖当前 SQLAlchemy/aiosqlite 连接池
- 大文件可能耗时较长，作为独立手动操作暴露，由用户确认后执行

## 6. UI 设计

### 6.1 入口

在左侧栏底部增加一个「设置」（齿轮图标）按钮。

点击后弹出菜单，包含：

- 数据清理
- 导出全部会话（预留）
- 导入会话（预留）

### 6.2 数据清理页面

- 输入框：保留最近 X 天（默认 30，最小 1）
- 复选框：跳过置顶会话（默认勾选）
- 复选框：跳过当前活跃会话（默认勾选）
- 按钮：预览影响范围
- 按钮：执行清理（红色危险按钮）
- 按钮：压缩数据库（黄色按钮，独立确认）：执行 SQLite VACUUM 回收删除后的磁盘空间
- 二次确认弹窗：显示将删除的会话数、消息数，并明确告知"不可恢复"

## 7. 决策确认（2026-08-06）

| 问题 | 决策 |
|------|------|
| 置顶会话是否跳过？ | **是**，默认跳过 `is_pinned = true` 的会话 |
| 子会话如何处理？ | **按各自 `updated_at` 独立判断**，不特殊处理、不强制级联父会话 |
| 活跃会话是否保护？ | **是**，默认跳过当前打开的会话（前端传入 `active_session_ids`） |
| 是否自动备份？ | **否**，仅前端二次确认警告 |
| 是否支持定时自动清理？ | **首期只做手动按钮**，定时清理作为后续扩展项 |
| 权限控制？ | **仅 admin 用户可见入口按钮**；后端接口校验 admin 角色 |
| 清理时是否阻塞前端？ | **显示 loading**，接口同步返回最终统计；大清理可能耗时数秒 |

## 8. 风险与注意事项

1. **不可逆操作**：删除后无法恢复，必须强二次确认。
2. **跨库一致性**：data 和 checkpoints 是两个独立 SQLite 文件，无法跨库事务。若中间失败可能出现 data 已删但 checkpoints 残留，或相反。
3. **大清理耗时**：如果消息很多，删除操作可能耗时数秒，需要前端 loading 反馈。
4. **外键约束**：SQLite 默认未启用外键约束，但删除顺序仍需谨慎。
5. **子 Agent 会话**：`parent_session_id` 关联的子会话也是普通 session，按创建时间清理即可，不强制级联父会话。

## 9. 后续可扩展

- 定时自动清理（启动时检查 / cron 任务）
- 按 Agent 筛选清理
- 导出旧会话后再删除
- 数据库 VACUUM 压缩（SQLite 删除后文件不会自动缩小）

## 10. 相关代码位置

- `lc_agent/db/models.py` — data 库表模型
- `lc_agent/db/engine.py` — data 库引擎初始化
- `lc_agent/app.py` — checkpoints 数据库初始化
- `lc_agent/core/engine.py:845-858` — `reset_thread()` 删除单个 thread 的 checkpoints（调用 `AsyncSqliteSaver.adelete_thread`）
- `lc_agent/server/auth_middleware.py:60-64` — `require_admin` 依赖
- `lc_agent/server/routes/admin.py:82-87` — 批量删 session 消息的 SQL 参考模式
- `frontend/src/components/layout/LeftSidebar.vue` — 左侧栏设置按钮入口
- `frontend/src/stores/auth.ts:10` — `isAdmin` computed

## 11. 实现备注（调研确认）

1. **checkpoints 删除**：`engine.reset_thread(thread_id)` 优先调用异步的 `adelete_thread`，AsyncSqliteSaver 已支持，无需直接操作底层 aiosqlite 连接。
2. **子会话处理**：清理查询**不应排除** `--sa--` 子会话（注意 `SessionRepository.list_all` 默认排除了它们，清理功能需自己写查询）。子会话作为独立 SessionMeta 行，按 `updated_at` 独立判断，符合 ADR 决策。
3. **ChatUiMessage 清理**：现有 `DELETE /sessions/{id}` 路由（`sessions.py:108-123`）仅删 SessionMeta，未级联删 ChatUiMessage。清理功能必须显式执行 `delete(ChatUiMessage).where(session_id.in_(ids))`，避免留下孤儿消息。
4. **时区**：`SessionMeta.updated_at` 使用 `datetime.now(timezone.utc)`（带时区），查询 cutoff 时也必须用带时区的 datetime 比较，否则会触发 SQLAlchemy 时区警告。
5. **删除顺序与事务**：先 `reset_thread` 删 checkpoints（独立操作，跨库无法事务化），再在同一事务内删 ChatUiMessage 和 SessionMeta（同属 data 库，合并事务避免孤儿消息）。checkpoints 与 data 分属不同 SQLite 文件，中途失败已删的 checkpoints 不回滚（符合 ADR 风险章节"跨库一致性"说明）。
6. **权限**：使用 `Depends(require_admin)`，未配置 auth 时 `get_current_user` 返回 role="admin" 的匿名用户，本地单用户场景默认放行，符合预期。
7. **前端入口**：LeftSidebar 当前无底部 footer，需新增 `.sidebar-footer` 容器放置设置按钮；用 `authStore.isAdmin` 控制按钮显隐；点击后 emit 事件给 App.vue，由 App.vue 打开清理 Dialog。
