# Project Folder Mode — 设计规格

> 日期: 2026-07-30
> 状态: **已实现**（2026-07-30 完成后端 + 前端全部改动）

## 概述

为 lc-agent 新增"项目模式"：用户在现有 Preset 上勾选"项目模式"并指定 `project_root` 路径，即可将该目录作为 AI Agent 的工作上下文。类似 Cursor / Codex / Trae Workspace 的体验。

---

## 设计决策

### 1. 项目与 Preset 的关系

**结论**: 扩展现有 Preset 数据模型，新增 `project_mode: bool` + `project_root: str | None` 字段。

- `project_mode = false` → 传统模式（`project_root` 字段被忽略）
- `project_mode = true` + `project_root` 有效路径 → 项目文件夹模式

> **⚠️ 与初始设计的变更**：原设计为"填写 `project_root` 即激活项目模式"（无独立开关）。
> 实现时增加了显式的 `project_mode` 布尔字段作为总开关，原因是：
> 1. 语义更清晰：用户明确知道自己打开了某个特殊模式
> 2. 防止误激活：不会因为遗留的 `project_root` 字段无意中进入项目模式
> 3. 方便以后扩展：可以在项目模式下增加更多配置项

不引入新的"项目"概念，避免增加认知负担。

---

### 2. AGENTS.md 加载时机

**结论**: Session 创建时读取一次 `{project_root}/AGENTS.md`，对话中途不重新加载。

- 用户修改 AGENTS.md 后需开新 Session 生效
- 避免每轮文件 I/O 和 KV cache 失效
- 与 Skills / MCP 加载时机一致（都是 Session 级别）

---

### 3. AGENTS.md 注入方式

**结论**: 作为 system message 的 `content` 数组中的一个元素。

```json
{
  "role": "system",
  "content": [
    {"type": "text", "text": "Preset 人设 system_prompt..."},
    {"type": "text", "text": "--- Project Rules (AGENTS.md) ---\n..."}
  ]
}
```

不拼接字符串，不增加额外 message，结构清晰。

---

### 4. 文件工具作用域

**结论**: 默认限定 `project_root` + 手动可扩展。

- 当 Preset 有 `project_root` 时，`allowed_directories` 自动包含该路径
- Preset 配置中可额外追加其他目录（如 `/tmp`、数据目录）
- AI 不能访问未声明的外部路径

---

### 5. 命令执行 CWD

**结论**: `run_command` / `start_background_process` 的默认 CWD = `project_root`。

- 工具仍提供 `cwd` 参数供 AI 手动指定其他目录
- 减少 AI 每次 `cd xxx && ...` 的无效操作

---

### 6. .gitignore 处理

**结论**: 不做 .gitignore 过滤，显示全部文件（与 Cursor 行为一致）。

- `list_directory` 只硬编码排除 `.git/` 目录
- `search_files` 走 ripgrep（默认 respect .gitignore，这是 ripgrep 自身行为）
- 不额外实现 gitignore 解析逻辑

---

### 7. 项目级 Skills

**结论**: 与全局 Skills 合并，同名时项目级优先。

- `{project_root}/.agents/skills/` 下的 Skill 文件会被扫描
- 加载时机：Session 创建时加载一次（不热加载）
- 全局通用 Skills 仍然可用

---

### 8. 项目级 MCP

**结论**: 自动与全局 MCP 合并。

- `{project_root}/.agents/mcp.json` 中声明的 MCP server 会被启动
- 启动时机：首次对话时（惰性加载）
- 同名时项目级覆盖全局
- 不做安全审批（个人/小团队工具，不存在不可信项目风险）

---

### 9. 项目级 config.jsonc

**结论**: 不支持。

- 工具权限只通过全局 `config.jsonc` + Preset 配置控制
- 项目目录不能影响 `blocked_commands` / `blocked_extensions` 等安全设置
- 保持权限配置的单一来源

---

### 10. 前端交互

**结论**: 在现有 Preset 编辑页面新增"项目模式"勾选框 + 条件展示的路径输入框。

- 未勾选 = 传统模式
- 勾选 + 填写路径 = 项目文件夹模式
- Agent 选择器中项目模式 agent 显示蓝色"项目"标签（替代"自建"标签）
- 勾选但未填路径 → 保存时前端校验报错
- 不新增页面或概念

---

### 11. project_root 无效时的行为

**结论**: 报错拒绝工作。

- Session 创建时检查 `project_root` 是否存在且可访问
- 如果无效，返回错误消息，不允许开始对话
- 用户必须修正路径或清空 `project_root` 字段

---

## 涉及的模块

| 模块 | 改动 |
|------|------|
| `lc_agent/core/models.py` | `AgentPreset` 加 `project_mode: bool` + `project_root` + `project_extra_dirs` 字段 |
| `lc_agent/db/models.py` | `AgentPresetDB` 加 `project_mode` 列（SQLite `BOOLEAN NOT NULL DEFAULT 0`） |
| `lc_agent/core/engine.py` | `_build_project_context_text`、`_TimeInjectionMiddleware`；`build_agent` 按 `project_mode` gate；`chat`/`chat_stream` 项目激活；异步 git 快照 |
| `lc_agent/tools/system_tools/_config.py` | 改用 `ContextVar` 替代全局变量，消除并发竞态；`allowed_directories` 自动包含 project_root |
| `lc_agent/tools/system_tools/command_tools.py` | 默认 CWD 读取 project_root（通过 `get_active_project_root()`） |
| `lc_agent/skills/filtered_loader.py` | Session 创建时扫描项目 Skills |
| `lc_agent/mcp/manager.py` | 首次对话时加载项目 MCP |
| `lc_agent/server/routes/agents.py` | Preset CRUD 接口支持 `project_mode` + `project_root` |
| `frontend/src/stores/agents.ts` | `AgentPreset` 接口加 `project_mode?: boolean` |
| `frontend/src/components/dialogs/AgentEditorDialog.vue` | 项目模式勾选框 + 条件路径输入框 + 保存时前端校验 |
| `frontend/src/components/layout/AppHeader.vue` | 项目 agent 在下拉和选中态显示蓝色"项目"标签 |

---

## 系统上下文注入（实现细节）

项目模式开启后，以下内容自动注入 system message（agent build 时一次性计算）：

```markdown
## Project Context

**Root**: /path/to/project
**OS**: Windows (cmd)
**Branch**: main
**Last Commit**: abc1234 fix: some bug
**Git Status** (snapshot at session start):
```
M src/foo.py
?? src/bar.py
```

> Git status is a snapshot. Run `run_command` to refresh if needed.
```

另外，所有 agent（不限于项目模式）的每条用户消息前都会注入当前时间：
```
[Current Time: 2026-07-30 17:31 (CST)]
```

时间注入在用户消息（不在 system message），不会影响 KV cache。

---

## 不做的事情

- 不引入"项目"新概念（复用 Preset）
- 不支持项目级 config 覆盖全局安全设置
- 不做 Skills 热加载（仅 Session 创建时加载）
- 不做 MCP 配置审批（信任本地项目）
- 不做多条 system message（用 content 数组 / middleware 追加）
