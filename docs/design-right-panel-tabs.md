# 右侧面板 Tab 化 — 计划文档

> 状态：已确认共识，待实施
> 日期：2026-09-14
> 相关代码：`frontend/src/components/layout/RightPanel.vue`、`frontend/src/components/chat/FileChangesDrawer.vue`、`frontend/src/components/chat/FileChangesBadge.vue`、`frontend/src/components/layout/AppHeader.vue`、`frontend/src/App.vue`
> 相关文档：`docs/design-file-changes-drawer.md`（抽屉被本方案取代）

## 1. 为什么做

右侧面板现在是 12 组 section 纵向堆在一个滚动列里（模型 → 窗口裁剪 → Markdown 版式/色盘 → 输入框动画 → 自动化任务 → 后台进程 → 工具/MCP/Skills → 会话），调一次模型要滚过一堆低频外观项；操作类（进程 kill、MCP 刷新）和配置类混在一起。拆成 tab 后高频配置一屏可见，低频项收进对应 tab。

## 2. 全部 12 项决策

| # | 决策点 | 最终选择 |
|---|--------|----------|
| Q1 | 起步几个 tab | **5 个一次到位**：模型 / 能力 / 变更 / 任务 / 外观 |
| Q2 | 默认 tab 与记忆 | 默认**模型**；last-tab 存 localStorage（全局）；**切换 agent 时重置回模型**（与现有"切换 agent 重置覆盖"逻辑一致） |
| Q3 | badge 角标 | **都要**：任务 tab（后台进程运行数）、能力 tab（MCP error 数） |
| Q4 | TodoList 与提示横幅 | **置顶不进 tab**：放 tab 栏上方常驻，切哪个 tab 都看得见；进 tab 的只是纯配置项 |
| Q5 | 实现形式 | **自定义 segmented**（flex-wrap 换行 + 渐变激活胶囊 + 图标文字），不用 el-tabs 原生 |
| Q6 | 变更 tab 与抽屉关系 | **抽屉搬进 tab**（右侧可拉宽，diff 在宽栏下可用） |
| Q7 | badge 点亮阈值 | **有异常才亮**：运行中进程数 > 0 才显示；MCP error > 0 才显示；平时干净 |
| Q8 | 移动端（~340px 抽屉） | **折行**：允许折 2 行，不断字不溢出 |
| Q9 | 契约测试 | **新增专项契约** `scripts/check-right-panel-tabs-contract.mjs` |
| Q10 | 旧抽屉与 Header Badge | **删抽屉，Badge 跳 tab**：删 40% overlay 抽屉；Header 📁 Badge 点击改为切到右侧变更 tab |
| Q11 | tab 排序 | **模型 / 能力 / 变更 / 任务 / 外观**（高频在前，外观沉底） |
| Q12 | 窄栏 diff 模式 | **保留 unified/side-by-side 切换，默认 unified**；窄栏用户自己拉宽再切 side-by-side |

## 3. Tab 内容归属（现有 section 一处不丢）

| Tab | 内容（全部是搬运现有 section，不新增概念） |
|-----|------------------------------------------|
| 模型 | 模型选择 + 思考级别 + 温度（现 fixed 区）、窗口裁剪模型（从 scroll 区搬上来）、会话 Thread |
| 能力 | 工具组、MCP 服务器、Skills、PermissionsPanel |
| 变更 | `FileChangesDrawer` 内容整体搬入：Agent 修改 / Git Diff 双源、轮次筛选、unified/side-by-side diff |
| 任务 | 自动化任务入口（含现有 `启用数/总数` 计数）、Agent 启动的后台进程（含刷新/终止/modal） |
| 外观 | Markdown 版式、Markdown 色盘、输入框动画 |
| 置顶（不进 tab） | TodoList（有 todo 时）、code-agent-hint / chat-only-hint 横幅 |

`fixedCollapsed` 折叠逻辑可删除——tab 本身就是折叠的替代品。

## 4. 布局与视觉

- tab 栏独立占 header 下方一行（全宽），不挤在标题旁；`display:flex; flex-wrap:wrap; gap:6px`，按钮 `flex:1 1 auto` + `white-space:nowrap`，宽时一行、窄时自然折 2 行。
- 容器为圆角胶囊槽（14px + 淡 fill + 细边框），与 `panel-section` 卡片语言统一。
- 激活态：渐变胶囊（主色→info 色 `linear-gradient(135deg,…)`）+ 白字 + 柔光阴影；未激活透明底 + 次级文色，hover 淡 fill + 上浮 1px。
- 每个 tab 配 Element Plus 图标（模型 Cpu、能力 Tools/Connection、外观 Brush、任务 Clock、变更 Files/Document）。
- badge 为贴在 tab 右上角的小红/小橙圆点，不占文字位，折行时宽度稳定。
- 内容切换：淡入 + 轻微上浮（`fadeUp 0.18s`），`prefers-reduced-motion` 下关闭。
- 颜色只用 `var(--el-*)` + `color-mix` 推导，不写死 hex（暗色适配）。

## 5. 跨组件联动（实施时定实现细节，行为已定）

- Header 📁 Badge 点击 → 切右侧到变更 tab（需一种跨组件通信：pinia UI store 或事件，实施时选）。
- `App.vue` 中移除 `FileChangesDrawer` overlay 挂载；`FileChangesBadge` 改为"跳转"语义。
- 抽屉的移动端全屏 modal 逻辑随抽屉删除而删除；变更 tab 在移动端抽屉（~340px）内折行显示。
- 轮次筛选、Git 基准、commit 选择等抽屉状态沿用 `file-changes` store，保持可复用。

## 6. 契约测试（新增）

`frontend/scripts/check-right-panel-tabs-contract.mjs`（+ `package.json` 加 `test:right-panel-tabs`）：

1. 5 个 tab 按钮存在且顺序为模型/能力/变更/任务/外观
2. 默认 tab 为模型
3. last-tab localStorage 记忆逻辑存在
4. 切换 agent 重置回模型
5. badge 规则：运行中进程数 / MCP error 数，> 0 才显示
6. 旧 section 全有归属（模型/温度/窗口裁剪/版式/色盘/动画/自动化/进程/工具/MCP/Skills/权限/会话，一个不能丢）
7. `FileChangesDrawer` overlay 不再被挂载；Badge 跳 tab 逻辑存在
8. tab 栏 `flex-wrap` 换行样式存在

## 7. 实施顺序与验收

1. `RightPanel.vue` 模板重构：header → tab 栏 → pinned 条 → 5 个 `v-if` 内容块；删 `fixedCollapsed`。
2. 变更 tab：搬入抽屉内容（复用 store + diff 渲染逻辑）。
3. 跨组件联动：Badge 跳 tab；`App.vue` 拆抽屉。
4. tab 栏 CSS（胶囊槽 + 渐变激活 + badge + 折行动画）。
5. 新增契约测试并通过；现有 `test:chat-width` / `test:responsive` 同步更新（旧断言引用 fixed/抽屉的部分）。
6. 验收：`npm run build` 通过 + 契约全过；手动把右侧拉窄确认折 2 行，拉宽确认 side-by-side 可用。

## 8. 明确不做

- opencode 式"工作区文件树"（根目录是什么是产品问题，本期不碰；见第 1 轮讨论）。
- 卡内直接改文件/重跑命令（延续 tool-cards 原则：只读审查）。
- tab 拖拽排序、用户自定义 tab（设一次的复杂度不值得）。
