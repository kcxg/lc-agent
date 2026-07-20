# 工具调用参数预览 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让工具调用卡片仅为 `ask_user.options` 使用 A/B/C 编号，其余数组与对象均安全显示为紧凑单行 JSON。

**Architecture:** 仅调整 Vue 组件 `ToolCallCard.vue` 内的参数格式化函数。格式化函数读取工具调用名称和参数键，以工具名后缀精确识别 `ask_user.options`；普通复合值采用安全的 JSON 序列化，其余值维持原有文本展示与长度截断。中断恢复和 `ask_user` 工具协议不改动。

**Tech Stack:** Vue 3、TypeScript、Vite、vue-tsc

## Global Constraints

- 仅修改前端工具调用参数展示；不得修改 SSE、中断恢复、`ask_user` 工具、数据库或 Agent 行为。
- `ask_user.options` 保留 A/B/C 编号，用户自然语言输入不做正则解析或强制映射。
- 所有普通数组和对象使用紧凑单行 JSON，避免 `[object Object]`。
- 格式化结果继续在 200 字符后追加 `...`。
- 不新增依赖，不添加代码注释。

---

### Task 1: 更新工具调用参数格式化

**Files:**
- Modify: `frontend/src/components/chat/ToolCallCard.vue:24,201-214`

**Interfaces:**
- Consumes: `ToolCall` 的 `name: string` 与 `args: Record<string, unknown>`。
- Produces: `formatArgs(name: string, args: Record<string, unknown>): Array<{ key: string; value: string }>`，供模板逐行渲染参数。

- [ ] **Step 1: 确认当前构建基线可通过**

Run:

```powershell
npm run build
```

Expected: `vue-tsc --noEmit && vite build` 以退出码 0 完成。

- [ ] **Step 2: 让模板向格式化函数传入工具名**

在 `frontend/src/components/chat/ToolCallCard.vue` 的参数循环中，将：

```vue
<div v-for="arg in formatArgs(toolCall.args)" :key="arg.key" class="arg-row">
```

替换为：

```vue
<div v-for="arg in formatArgs(toolCall.name, toolCall.args)" :key="arg.key" class="arg-row">
```

- [ ] **Step 3: 实现精确的 ask_user 选项与普通值格式化**

将现有 `formatArgs` 替换为以下实现：

```ts
function formatArgs(name: string, args: Record<string, unknown>): { key: string; value: string }[] {
  return Object.entries(args).map(([key, value]) => {
    let formatted: string
    if (name.endsWith('ask_user') && key === 'options' && Array.isArray(value)) {
      formatted = value.map((item, index) => `${String.fromCharCode(65 + index)}. ${String(item)}`).join('\n')
    } else if (typeof value === 'string') {
      formatted = value
    } else {
      try {
        formatted = JSON.stringify(value) ?? String(value)
      } catch {
        formatted = String(value)
      }
    }
    if (formatted.length > 200) formatted = `${formatted.slice(0, 200)}...`
    return { key, value: formatted }
  })
}
```

要求：

- `name.endsWith('ask_user') && key === 'options'` 是唯一生成 A/B/C 编号的条件，同时兼容显式工具名和 `{group}__ask_user` 命名。
- `queries` 等普通数组通过 `JSON.stringify` 显示对象字段。
- 保留 JSON 序列化异常时的字符串回退，避免单个参数导致卡片渲染失败。

- [ ] **Step 4: 执行类型检查与生产构建**

Run:

```powershell
npm run build
```

Expected: `vue-tsc --noEmit` 和 `vite build` 均成功，退出码为 0。

- [ ] **Step 5: 进行浏览器手工验收**

启动 bfzs 服务与前端开发服务器后，在聊天界面分别触发以下工具调用并检查卡片：

1. 普通工具传入对象数组 `queries`，确认它显示为单行 JSON，包含对象字段且不出现 `[object Object]`。
2. 普通工具传入字符串数组，确认显示为 JSON 数组而不是 A/B/C 列表。
3. `ask_user` 传入 `options`，确认仍显示 A/B/C 前缀与选项文本。
4. 在 `ask_user` 自由输入框填写 `A` 或自然语言，确认能继续恢复 Agent，且不引入额外前端解析。
5. 传入超过 200 字符的参数，确认显示内容末尾为 `...`。

- [ ] **Step 6: 检查工作区差异并提交**

Run:

```powershell
git diff --check
git diff -- frontend/src/components/chat/ToolCallCard.vue
git status --short
```

Expected: `git diff --check` 无输出；差异仅含预期的工具参数格式化改动及本计划/设计文档。

Commit:

```powershell
git add frontend/src/components/chat/ToolCallCard.vue docs/superpowers/specs/2026-07-20-tool-call-argument-preview-design.md docs/superpowers/plans/2026-07-20-tool-call-argument-preview.md
git commit -m "fix: format tool call arguments safely"
```

Expected: 创建一个包含参数预览修复与设计文档的提交。
