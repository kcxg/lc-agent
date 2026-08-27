# 文件变更审查抽屉 — 设计方案

> 状态：已确认共识，实施中
> 分支：filediff
> 日期：2026-08-25

## 功能概述

为 lc-agent 前端新增一个"文件变更审查抽屉"，让用户在编程场景下能**集中查看当前会话中 agent 修改了哪些文件**，并能查看每个文件的 diff。定位为**轻量审查工具（类 Codex Web）**，不做成 Web IDE。

## 交互流程

1. Agent 开始编程任务，执行 `edit_block`/`write_file`/`delete_file`/`move_file` 等文件操作
2. Header 区域出现/更新 Badge：`📁 3`，hover 显示文件名列表（Tooltip 预览）
3. 用户点击 Badge → 右侧滑出 40% overlay 抽屉（不挤压聊天区）
4. 抽屉内：文件列表（路径 + M/A/D 状态标签），点击文件就地展开 unified diff（diff2html 渲染）
5. 用户可切换 unified/side-by-side 视图
6. 如果有子 Agent 变更，显示汇总条目，点击钻入子会话面板
7. 如果项目是 git 仓库，面板顶部提供"查看 Git Diff"独立按钮
8. 移动端下抽屉变为全屏 modal

## 全部 18 项设计决策

| # | 决策点 | 最终选择 |
|---|--------|----------|
| Q1 | 核心用户故事 | **全局感知**（我不知道 agent 改了哪些文件） |
| Q2 | 追踪粒度 | **Tool Call 实时 + Git 全局汇总** |
| Q3 | UI 位置 | **独立侧面板/抽屉** |
| Q4 | 定位边界 | **轻量审查工具（类 Codex Web）** |
| Q5 | Diff 渲染库 | **diff2html** |
| Q6 | 触发方式 | **常驻 Badge + 手动展开** |
| Q7 | 内部布局 | **文件列表 + 就地展开 diff（GitHub PR 风格）** |
| Q8 | 持久化 | **独立 `file_changes` 表** |
| Q9 | Git 快照时机 | **第一次文件操作前自动快照** |
| Q10 | 非 Git fallback | **仅 Tool Call 级追踪** |
| Q11 | 多次编辑聚合 | **只显示最终 diff** |
| Q12 | 子 Agent 变更 | **汇总条目 + 钻入子会话** |
| Q13 | Diff 数据源 | **Tool Call 优先**，git diff 作为独立按钮功能 |
| Q14 | 抽屉样式 | **右侧 40% overlay，不挤压聊天** |
| Q15 | Diff 视图模式 | **默认 Unified + 提供切换按钮** |
| Q16 | 操作能力 | **纯只读审查（V1）** |
| Q17 | Badge 显示 | **数字 + Tooltip 文件名预览** |
| Q18 | 移动端行为 | **全屏 modal** |

## 技术方案

### 后端改动

#### 1. 新增 `FileChange` 数据模型 (`lc_agent/db/models.py`)

```python
class FileChange(SQLModel, table=True):
    __tablename__ = "file_changes"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    session_id: str = Field(index=True)
    file_path: str
    change_type: str  # "edit" | "create" | "append" | "delete" | "move"
    old_string: str | None = None  # edit_block 的 old_string
    new_string: str | None = None  # edit_block 的 new_string
    tool_call_id: str | None = None
    move_destination: str | None = None  # move_file 的目标路径
    created_at: datetime = Field(default_factory=utcnow)
```

#### 2. `SessionMeta` 增加 `git_base_hash` 字段

在 `SessionMeta` 模型新增：
```python
git_base_hash: str | None = Field(default=None)
```

首次文件写入操作前，自动记录 `git rev-parse HEAD` 到此字段。

#### 3. 文件工具中记录变更 (`file_write_tools.py`)

在 `edit_block`、`write_file`、`delete_file`、`move_file` 成功执行后，
通过 `dispatch_custom_event("file_change_record", {...})` 发出事件，
然后在 SSE 流处理中持久化到 `file_changes` 表。

或者直接在工具函数内调用持久化（通过 ContextVar 传入 session_id）。

#### 4. 新增 API 端点 (`lc_agent/server/routes/file_changes.py`)

- `GET /api/sessions/{session_id}/file-changes` — 获取文件变更列表
  - 返回：聚合后的文件列表（每个文件最终状态 + 变更次数）
- `GET /api/sessions/{session_id}/file-changes/{file_path}/diff` — 获取单个文件的最终 diff
  - 对 edit_block：从 old_string/new_string 重建 diff
  - 对 write_file(create)：整个文件内容为 added
- `GET /api/sessions/{session_id}/git-diff` — Git 全局 diff（独立按钮）
  - 从 session_meta.git_base_hash 到当前状态的 git diff

### 前端改动

#### 1. 安装依赖

```bash
npm install diff2html
```

#### 2. 新增 Pinia Store (`stores/file-changes.ts`)

- `fileChanges: FileChangeItem[]` — 当前会话的文件变更列表
- `isDrawerOpen: boolean`
- `fetchFileChanges(sessionId)` — 从 API 加载
- `addFileChange(change)` — SSE 实时推送时追加
- `fileChangeCount` — computed getter

#### 3. 新增组件

- `FileChangesBadge.vue` — Header 中的 Badge（数字 + Tooltip 文件名预览）
- `FileChangesDrawer.vue` — 抽屉主体
  - 文件列表（路径 + M/A/D 标签）
  - 就地展开 diff（diff2html 渲染）
  - Unified/Side-by-side 切换按钮
  - 子 Agent 变更汇总条目
  - Git Diff 独立按钮（如有 git_base_hash）
  - 移动端全屏 modal 适配

#### 4. 集成到 AppHeader

在 `AppHeader.vue` 中引入 `FileChangesBadge` 组件。

#### 5. SSE 事件新增

在 `stream_utils.py` 的 `convert_stream_event` 中处理 `file_change_record` 自定义事件，
转为 `tool_file_change` SSE 事件推送给前端。

前端 `chat.ts` store 中接收 `tool_file_change` 事件，更新 `file-changes` store。

## 实施 TODO

- [x] 后端：创建 FileChange 数据模型 + SessionMeta 增加 git_base_hash 字段
- [x] 后端：在文件工具执行时记录 file_changes + 首次写入前自动快照 git HEAD
- [x] 后端：新增 API 端点（file-changes 列表、per-file diff、git-diff）
- [x] 前端：安装 diff2html 依赖
- [x] 前端：创建 file-changes Pinia store
- [x] 前端：创建 FileChangesDrawer 组件（抽屉+内联diff）
- [x] 前端：创建 Badge 组件并集成到 AppHeader
- [x] 前端：移动端全屏 modal 适配
- [x] Q11：最终 diff 聚合（git diff 优先，hunks fallback）
- [x] Q12：子 Agent 变更追踪（ContextVar rebind + 汇总 UI + 钻入子会话 diff）
- [x] 派遣子 agent 审查代码（共 4 轮审查，所有 CRITICAL/WARNING 已修复）
