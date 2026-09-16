# 横向会话标签栏 — 计划文档

> 状态：**全部决策已确认，设计树已清空，待实施**
> 日期：2026-09-15
> 相关代码：`frontend/src/App.vue`、`frontend/src/views/ChatView.vue`、`frontend/src/components/layout/LeftSidebar.vue`、`frontend/src/stores/chat.ts`、`frontend/src/stores/sessions.ts`、`frontend/src/stores/file-changes.ts`
> 相关文档：`docs/design-right-panel-tabs.md`（右侧面板 tab 化，已完成，与本方案无关但同属"tab 化"主题）

## 1. 为什么做

现在会话只能从左侧栏竖向切换，有三个体感问题：

1. **切换要重新加载**。切走一个空闲会话立刻被逐出缓存，切回必须重拉消息 + 重拉 file-changes。
2. **现场全丢**。滚动位置、思考块展开态、输入框草稿都不按会话保存，切回后是从头滚到底、思考块全折叠。
3. **没有"已打开"概念**。没有标签栏，"刚才那个会话"只能靠侧边栏记忆，几十个会话时靠标题找。

目标：新增类似浏览器的横向标签栏，已打开的会话在标签间切换时**不重新请求、不丢滚动位置**。左侧竖向列表保留（当会话导航用）。

## 2. 现状诊断（已核实的四个关键事实）

### 2.1 数据结构上已经是"按 sessionId 分桶"，但会回收

[chat.ts](file:///d:/codes/lc-agent/frontend/src/stores/chat.ts#L593-L595)：

```ts
const activeSessions = shallowReactive(new Map<string, SessionState>())
const activeSessionId = ref<string | null>(null)
const sessionOffsets = new Map<string, number>()
```

每个会话独立持有 `messages` / `isStreaming` / `todos` / `interrupt` / **自己的 SSE client**（[SessionState 定义](file:///d:/codes/lc-agent/frontend/src/stores/chat-session-state.ts#L6-L43)）。

但 [switchToSession](file:///d:/codes/lc-agent/frontend/src/stores/chat.ts#L1051-L1089) 的回收策略是：

- 离开**流式中**的会话 → 保留在 Map（L1061 注释 `Streaming session: keep in map`），切回 L1071 直接 return，**不重请求**
- 离开**空闲**会话 → L1058-1060 立刻 `_releaseBackgroundSession` 删除 → 切回必须重拉

日常切换的几乎都是空闲会话，所以"每次都重载"。**结论：分桶地基已经具备，缺的只是"保留策略"。**

### 2.2 对外是"单指针代理"，但因为同一时刻只渲染一个面板，这个不用改

[chat.ts](file:///d:/codes/lc-agent/frontend/src/stores/chat.ts#L601-L611) 把 `messages` / `isStreaming` / `todos` 等全部暴露为 `activeSessionId` 的 computed 代理。

**因为 Q3 选了"同一时刻只显示一个面板"，ChatView 保持单实例复用，这套代理可以直接沿用**，多实例渲染（KeepAlive / v-for 多面板 / 把 `storeToRefs` 改为按 id 取数）**都不需要**。这是本方案比预想简单很多的原因。

### 2.3 真正要补的是"每会话 UI 态"

这些目前是 ChatView 的**组件本地 ref / 无条件行为**，切换时既不保存也不区分：

| 项 | 位置 | 现状 |
|----|------|------|
| 滚动位置 | `messagesContainerRef` [ChatView.vue#L410](file:///d:/codes/lc-agent/frontend/src/views/ChatView.vue#L410) | 不保存；且 [L1075-L1077](file:///d:/codes/lc-agent/frontend/src/views/ChatView.vue#L1075-L1077) **无条件 `scrollMessagesToBottom`**，切回即滚到底 |
| 思考块展开态 | `thinkingExpandedBySegment` / `thinkingOverflowBySegment` | 组件本地 ref，不按会话分离 |
| 加载更早消息按钮 | `showLoadOlderMessages` [L411](file:///d:/codes/lc-agent/frontend/src/views/ChatView.vue#L411) | 同上 |
| 输入框草稿 / 附件 | `messageText` / `attachments` [ChatInput.vue#L193-L194](file:///d:/codes/lc-agent/frontend/src/components/chat/ChatInput.vue#L193-L194) | 组件本地 ref，多标签共用一个草稿框 |

### 2.4 三个全局单值，是跨标签冲突的来源

| 全局状态 | 位置 | 冲突 |
|----------|------|------|
| `currentAgentId` | [agents.ts#L77-L79](file:///d:/codes/lc-agent/frontend/src/stores/agents.ts#L77-L79) | 驱动右侧"文件"tab 显隐、项目树（按 agentId 缓存）、模型默认值 |
| `currentModel` | [tools.ts#L280-L282](file:///d:/codes/lc-agent/frontend/src/stores/tools.ts#L280-L282) | 切会话时被 `applyModel` 改写 |
| `sessionNavStack` | [sessions.ts#L30-L35](file:///d:/codes/lc-agent/frontend/src/stores/sessions.ts#L30-L35) | **正确性 bug**：钻进 B 的子会话后切到 A 标签，渲染出的仍是 B 的子会话内容 |

### 2.5 两个易踩的坑

- **每个会话一条独立 SSE 流**（`fetch` + ReadableStream，非 WebSocket/EventSource）。浏览器同域 HTTP/1.1 上限 6 连接，标签开多且同时流式会互相挤占。非激活标签**继续在后台跑**是刻意设计，本期不改。
- **"新对话"的 id 会被改写**：[persistSession](file:///d:/codes/lc-agent/frontend/src/stores/sessions.ts#L132-L151) 先用本地 id，首条消息落库后才换成真实 id。标签栏若以 sessionId 作 key，**必须同步搬迁标签**，否则标签会指向不存在的会话。
- **`/` 与 `/c/:id` 之间 ChatView 会真正销毁重建**（不同路由记录，[App.vue#L267-L277](file:///d:/codes/lc-agent/frontend/src/App.vue#L267-L277)），组件本地态会丢一次；跨 `/c/:id` 之间的切换则是复用实例（[router/index.ts](file:///d:/codes/lc-agent/frontend/src/router/index.ts#L6-L17) 只有一条路由记录，`<router-view>` 无 key）。

## 3. 全部决策

### 3.1 第一轮：方向

| # | 决策点 | 最终选择 |
|---|--------|----------|
| R1-Q1 | 是否一步到位 | **B 一步到位**：横向标签栏 + 保活一起做，不做"先解耦保活再上 UI"的分步 |
| R1-Q2 | 侧边栏点击语义 | **B 每次点击都新开标签**（替换语义不做） |
| R1-Q3 | 同时显示几个会话 | **A 只显示一个**：标签切换，主区永远一份消息面板。**因此不需要多实例渲染** |

### 3.2 第二轮：形态

| # | 决策点 | 最终选择 |
|---|--------|----------|
| R2-Q1 | 标签上限与淘汰 | **不设上限，不自动淘汰**（原话："用户不是傻子，开多了用户知道关闭标签"）。内存与 SSE 连接数完全交给用户手动管理 |
| R2-Q2 | 重复打开同一会话 | **A 去重**：点击已在标签栏的会话 → 激活已有标签，不再开重复标签 |
| R2-Q3 | 标签栏作用范围 | **A 只管聊天会话**。Admin / Usage 等仍是整页路由跳转，不产生标签 |
| R2-Q4 | 标签栏位置 | **A 只贴在中间聊天列顶部**（左侧栏、右侧面板保持通高不变），不横跨整窗 |
| R2-Q5 | 刷新后恢复 | **A 持久化到 localStorage**，标签集合与激活项都恢复；恢复时过滤掉已删除的会话 |
| R2-Q6 | 关闭当前标签后激活谁 | **A 右邻 → 左邻 → 最后一个**（浏览器/VSCode 惯例） |

> **R1-Q2 与 R2-Q2 的合并语义**：点击一个**未打开**的会话 → 新开标签；点击一个**已打开**的会话 → 激活该标签。两条不冲突，共同定义了"标签集合 = 已打开会话集合"（这也是 R2-Q1 敢不设上限的前提）。

### 3.3 第三轮：跨标签冲突

| # | 决策点 | 最终选择 |
|---|--------|----------|
| R3-Q1 | 标签栏 agent 作用域 | **B 跨 agent 全局一个标签栏**：激活某标签时若 agent 不同，自动切换 agent；header 的 agent 下拉会随标签跳动 |
| R3-Q2 | 子会话导航栈是否按标签隔离 | **A 每标签各存一份导航栈**：切回时仍停在原来那个子会话，面包屑一致 |
| R3-Q3 | 关闭正在流式的标签 | **A 直接断开、后端继续跑**：关闭只是本地停止接收，跑完后端仍会入库；重新打开靠 DB 重载，过程中看不到实时输出 |
| R3-Q4 | 右侧"变更"面板是否分桶 | **A 分桶**：`loadedSessionId` 单值改为 `Map<sessionId, 状态>`，切回不重拉、保留展开态 |
| R3-Q5 | 标签溢出行为 | **A 横向滚动**：标签不压缩，标题始终可读，鼠标滚轮/按钮可滚，激活标签自动滚入可视区 |

## 4. 实施要点

### 4.1 新增：标签状态

建议新建 `frontend/src/stores/session-tabs.ts`，持有：

- `openTabIds: string[]` — 已打开的会话 id（有序，决定标签栏顺序；去重由它保证）
- `activeTabId: string | null` — 当前激活标签
- `navStackByTab: Map<string, Array<{session_id, label}>>` — 每个标签的子会话导航栈（R3-Q2 = A）
- localStorage 持久化 + 恢复时过滤已删除会话（R2-Q5）

注意 R3-Q1 选了跨 agent 全局标签栏，所以标签栏**不再按 agent 分组**，一个数组装全部。

### 4.2 改动：`stores/chat.ts` — 保活

把"进入即释放"改为**受已打开标签集合约束**：

- [switchToSession L1054-L1062](file:///d:/codes/lc-agent/frontend/src/stores/chat.ts#L1054-L1062)：离开时若 `openTabIds` 含旧会话 → 保留，不 `_releaseBackgroundSession`
- [done/cancelled/error handler](file:///d:/codes/lc-agent/frontend/src/stores/chat.ts#L982-L1034)：后台流跑完后**不要**因为"不是当前会话"就释放，否则标签内容当场丢
- 关闭标签时（只有这时）才真正 `_releaseBackgroundSession` 并清理 `sessionOffsets`
- 新增 `isSessionStreaming` 已被侧边栏复用，标签栏可同样用它显示流式小圆点与"已完成未查看"徽标

### 4.3 改动：`views/ChatView.vue` — 每会话 UI 态

- 滚动位置：按 sessionId 存（切标签前记录、切回后恢复），并**把 [L1075-L1077](file:///d:/codes/lc-agent/frontend/src/views/ChatView.vue#L1075-L1077) 的无条件 `scrollMessagesToBottom` 改为**仅在"当前激活标签 + 正在流式"时触发
- `thinkingExpandedBySegment` / `thinkingOverflowBySegment` / `showLoadOlderMessages` 按 sessionId 分桶（或提升到 store）
- 注意 `/` ↔ `/c/:id` 会销毁重建一次，这几个状态不能只留在组件 ref 里

### 4.4 改动：`ChatInput.vue` — 草稿按标签分离

`messageText` / `attachments` 需按 sessionId 分离，否则两个标签共用一个草稿框。

### 4.5 改动：`stores/sessions.ts` — 导航栈与 id 改写

- `sessionNavStack` 从全局单值改为按标签存（R3-Q2 = A），修掉 2.4 的正确性 bug
- `persistSession` 换真实 id 时（[L141-L149](file:///d:/codes/lc-agent/frontend/src/stores/sessions.ts#L141-L149)），**必须原子搬迁标签**：`openTabIds` 里的旧 id 换成新 id、`activeTabId` 同步、导航栈与各种 per-session Map 的 key 一起重写

### 4.6 改动：`stores/file-changes.ts` — 分桶（R3-Q4 = A）

`loadedSessionId` 单值 + `reset()` 整份清空 → 改为 `Map<sessionId, 状态>`；[FileChangesPanel.vue L624-L640](file:///d:/codes/lc-agent/frontend/src/components/panels/FileChangesPanel.vue#L624-L640) 的清空 diff 缓存 watch、以及 `selectedRound` / 展开态一并按 sessionId 存。

> 注：`project-tree.ts` 按 **agentId** 缓存（非 sessionId），所以同一 agent 下切换标签，文件树缓存天然保留，无需改动。但 R3-Q1 选了跨 agent，**切 agent 时文件树仍会重新加载**，这是预期行为。

### 4.7 新增：标签栏组件

- 放在中间聊天列顶部（R2-Q4 = A），标签栏 UI 参考 `design-right-panel-tabs.md` 的自定义 segmented 风格（渐变激活胶囊 + 图标文字），与右侧 tab 栏视觉统一
- 每个标签：标题 + 关闭按钮 + 状态点（流式中 / 已完成未查看）
- 溢出横向滚动 + 激活项自动滚入可视区（R3-Q5 = A）
- 关闭当前标签后按 R2-Q6 激活右邻

### 4.8 不改的东西

- 左侧竖向会话列表（保留，作导航用）
- Admin / Usage 页面（不进标签栏）
- 非激活标签的后台 SSE 继续跑（不排队、不取消）
- 右侧面板 tab 结构（已完成）

## 5. 决策已全部确认

三轮问答共 14 项决策，无待确认项：

- 第一轮 R1-Q1~Q3：方向（一步到位 / 点击即开标签 / 只显示一个面板）
- 第二轮 R2-Q1~Q6：形态（不设上限 / 去重 / 只管会话 / 贴聊天列顶部 / localStorage 恢复 / 右邻优先）
- 第三轮 R3-Q1~Q5：跨标签冲突（跨 agent 全局 / 导航栈隔离 / 关闭即断开 / 变更面板分桶 / 横向滚动）

## 6. 已识别风险

1. **SSE 连接数**：R2-Q1 不设上限 ⇒ 标签开多且同时流式会撞浏览器同域 6 连接上限。已明确接受，由用户手动关闭缓解。
2. **跨 agent 标签栏（R3-Q1）**：每次跨 agent 激活标签都会触发 `selectAgent` → 项目树重拉 + 模型改写 + header 下拉跳动。已确认接受。
3. **"新对话"id 改写**：见 4.5，是唯一可能产生"幽灵标签"的地方，必须原子搬迁。
4. **`/` ↔ `/c/:id` 的销毁重建**：组件本地态会丢一次，per-session 状态必须落在 store 而非组件 ref。
5. **`sessionOffsets` 是非响应式 Map**：复用即可，改动时注意别破坏响应性。
