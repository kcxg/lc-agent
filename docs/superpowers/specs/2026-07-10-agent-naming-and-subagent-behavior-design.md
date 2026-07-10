# Agent 双语命名与子 Agent 行为优化设计

> 设计时间：2026-07-10
> 背景来源：deepagents 官方实现调研（见 `research/2026-07-09-deepagents-subagent-prompts.md`）
> 状态：设计讨论中，未开始实现

---

## 1. 问题背景

### 1.1 Agent 名称的双重用途导致矛盾

当前 `AgentPreset.name` 字段同时承担两个职责：
- **LLM 填参数时的 key**（`subagent_type` 参数）：需要 ASCII，LLM 不会拼错中文
- **界面展示名**：用户希望能填中文（"代码助手"、"研究员"）

这两个需求互相冲突，目前的实现（`subagent_type = preset.name`）在用户填中文名时会导致 LLM 调用 `task` 工具时拼错参数。

### 1.2 子 Agent 行为缺陷

调研 deepagents 官方实现发现，lc-agent 子 Agent 有以下行为缺陷：

| 问题 | 根因 |
|------|------|
| 子 Agent 答案零散在多轮输出 | 子 Agent 不知道"只有最后一条消息被主 Agent 看到"，用对话习惯回答 |
| 主 Agent 委派描述不完整 | 主 Agent 没有被提示"子 Agent 是无状态的，看不到你的对话历史" |
| 提示词用"主 Agent/子 Agent"等框架术语 | LLM 不理解框架概念，用第一人称行为描述效果更好 |

---

## 2. 命名字段设计方案

### 2.1 新增 `display_name` 字段

| 字段 | 类型 | 约束 | 用途 |
|------|------|------|------|
| `name` | `str` | `^[a-zA-Z][a-zA-Z0-9_-]*$` | task 工具的 `subagent_type` key；代码逻辑标识符 |
| `display_name` | `str` (optional) | 无限制 | 界面展示；可为中文；不填时降级显示 `name` |

### 2.2 设计决策

**决策 1：ASCII 校验范围**
- `source="user"` 的 preset（网页创建）：`name` 必须符合 `^[a-zA-Z][a-zA-Z0-9_-]*$`
- `source="builtin"` 的内置 preset：`name` 也需要遵守（同时从 `__chat__` 等 `__` 前缀改为普通 ASCII 名，如 `chat`、`empty`、`power`）
- `source="code"` 的用户代码创建：`name` 建议 ASCII，但框架不强制（用户自己负责）

**决策 2：`display_name` 为可选**
- `display_name` 不填时，界面显示 `name`
- 不影响现有数据（老数据 `display_name` 为 null，显示 `name`）

**决策 3：代码创建 API**
```python
# 目前
app.add_agent(name="code-assistant", graph=..., description="...")

# 新 API（display_name 可选）
app.add_agent(
    name="code-assistant",           # ASCII
    display_name="代码助手",         # 可选，界面展示
    graph=...,
    description="...",
)
```

**决策 4：`_build_subagent_registry` 中的映射**
```python
subagent_type = subagent_preset.name          # 用 ASCII name 作为 key
display_name  = subagent_preset.display_name or subagent_preset.name  # 用于展示
```

### 2.3 内置 Preset 重命名

| 旧 `id`/`name` | 新 `name`（ASCII） | `display_name` |
|----------------|-------------------|----------------|
| `__chat__` | `chat` | 普通对话 |
| `__empty__` | `empty` | 空模板 |
| `__power__` | `power` | 全功能 |

> **注意**：内置 preset 的 ID（UUID 或特殊标识）和 `name` 的关系需要在实现时确认，不要破坏现有的路由和会话恢复逻辑。

---

## 3. 子 Agent 行为改善方案

### 3.1 子 Agent 注入"委派提示词"

参考 deepagents 的 `DEFAULT_SUBAGENT_PROMPT`，子 Agent 需要一个简短的系统提示词前缀，告知它：
- 自己是被委派完成一个具体任务的
- 只有最后一条 AI 消息对委托方可见
- 必须把完整答案集中在最后一条消息里

**原文（英文）：**
```
In order to complete the objective that the user asks of you, you have access to a number of standard tools.

The calling agent only sees your final assistant message, not your intermediate work, tool results, or status tracking. Ensure your final
response contains the complete answer.
```

**适配思路：**
- 不一定要翻译成中文，这段提示词的语义 LLM 无论中英文都能理解
- 关键是语义：**"calling agent"**（不是"主 Agent"这种框架术语）、**"final assistant message"**（具体的概念，不是抽象的"最后一条回复"）
- `build_agent(_depth > 0)` 时在 preset 的 `system_prompt` 前拼入这段提示词，不是注入到 middleware

**实现位置：** `engine.py` 的 `build_agent` 方法，在 `system_prompt = preset.system_prompt` 之后，`_depth > 0` 时前缀：
```python
if _depth > 0:
    system_prompt = f"{SUBAGENT_DELEGATION_PROMPT}\n\n{system_prompt}"
```

### 3.2 主 Agent system 注入 task 工具使用指南

参考 deepagents 的 `TASK_SYSTEM_PROMPT`，主 Agent 需要知道：
- 何时用 / 何时不用 `task` 工具
- 子 Agent 是**无状态**的（stateless），不共享对话历史
- 因此 `description` 参数必须包含所有必要背景

**实现方式：**
- 参考 `_SystemBlockMiddleware` 的模式，在 `_depth == 0` 且有子 Agent 时，通过 middleware 注入 task 使用指南作为独立 content block
- 或者直接注入到主 Agent 的 `system_prompt` 字符串（更简单，不需要新 middleware）

### 3.3 task 工具 description 强化

现有 task 工具的 `description` 可以加入：
- `stateless` 关键词（"Each invocation is stateless..."）
- 参数级 description 强调"Include all necessary context"

### 3.4 不向子 Agent 注入 TodoListMiddleware（已实现）

已在 `engine.py` 的 `build_agent` 中实现：`_depth > 0` 时不加 `TodoListMiddleware`。

---

## 4. 实现影响范围

### 4.1 需要修改的文件

**命名双字段：**
- `lc_agent/core/models.py`：`AgentPreset` 加 `display_name: str | None = None`
- `lc_agent/db/models.py`：`AgentPresetDB` 加 `display_name` 列
- `lc_agent/server/routes/agents.py`：请求 model 加 `display_name` 字段
- `lc_agent/app.py`：`add_agent()` 接口加 `display_name` 参数
- `lc_agent/core/engine.py`：`_build_subagent_registry` 用 `name` 作 key，`display_name` 作展示
- `frontend/src/components/dialogs/AgentEditorDialog.vue`：表单加 `display_name` 输入框
- 内置 preset 的 `name` 字段从 `__xxx__` 改为普通 ASCII

**子 Agent 委派提示词：**
- `lc_agent/core/engine.py`：加 `SUBAGENT_DELEGATION_PROMPT` 常量，`_depth > 0` 时前缀到 `system_prompt`

**task 使用指南注入：**
- `lc_agent/core/engine.py`：有子 Agent 时注入 `TASK_SYSTEM_PROMPT`（待定 middleware or 字符串）

### 4.2 数据库

- 新增 `display_name` 列（nullable），Alembic 自动迁移
- 内置 preset name 改变不涉及数据库（hardcoded）
- 已有用户 preset 的 `name` 如果含中文，迁移时不修改数据（破坏性变更，用户需手动更新）

### 4.3 暂不处理

- `AgentPreset.id`（UUID）保持不变，不作为 `subagent_type`
- 内置 preset 的 session/会话历史通过 preset_id 关联，改名时只改 `name`，不改 `id`

---

## 5. 待决策问题

1. **`SUBAGENT_DELEGATION_PROMPT` 语言**：不需要特别规定，英文即可。这是技术性指令，子 Agent 回复的语言由主 Agent 传入的 `description` 内容自然决定，与指令语言无关。

2. **`TASK_SYSTEM_PROMPT` 注入方式**：使用 content block 注入（通过 `_SystemBlockMiddleware`），命名为 `"TaskSystemPromptMiddleware"`。只在有子 Agent 时注入（`subagent_registry` 非空时才创建 middleware 实例）。

3. **内置 preset `name` 改成什么**：`chat`、`empty`、`power`。不需要兼容旧会话恢复数据。

---

## 6. 遗留疑问（已确认）

**疑问 1：内置 preset 的 `id` 字段**
→ **确认：`id` 和 `name` 都改**，同时更新前端 hardcode 的地方。`__chat__` → id=`chat` name=`chat`，以此类推。

**疑问 2：`SUBAGENT_DELEGATION_PROMPT` 拼接顺序**
→ **确认：后缀**。`preset.system_prompt + "\n\n" + SUBAGENT_DELEGATION_PROMPT`。用户自定义指令在前（LLM 优先理解），委派行为约束在后（压轴，难被其他内容淹没）。

**疑问 3：`display_name` DB 迁移策略**
→ **确认：迁移时把旧 `name` 复制到 `display_name`**。Alembic 迁移脚本中执行 `UPDATE agent_presets SET display_name = name WHERE display_name IS NULL`，确保旧数据界面显示不受影响。
