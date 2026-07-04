# Code Agent Semantic Convergence Design

Date: 2026-07-04

## Background

`lc-agent` supports three agent sources: built-in presets, user-created presets, and code-registered agents. Code-registered agents are added through `app.add_agent(name, graph, description)` as pre-built compiled LangGraph graphs.

Unlike built-in and user-created presets, code agents do not go through `AgentEngine.build_agent()`. Their model, prompt, tools, MCP usage, Skills usage, middleware, and context management are defined by the graph supplied by user code.

The current UI/API semantics can imply that framework-level prompt/model/tools/MCP/Skills are configurable for code agents. This is misleading and can become unsafe if cache/model/MCP changes accidentally route a code agent through normal preset-building logic.

## Decision

Use semantic convergence across backend and frontend:

- Code agents are non-framework-managed compiled graphs.
- Framework-level prompt, model, tools, MCP, Skills, and middleware are not configurable for code agents.
- The frontend should not show concrete configurable tool/MCP/Skill lists for code agents.
- The chat transcript should still show actual tool calls emitted during graph execution, because those are runtime evidence from the graph, not configurable framework capabilities.

## Backend Design

### `app.add_agent()` metadata

When registering a code agent, create its `AgentPreset` with explicit non-applicable framework capabilities:

- `source = "code"`
- `default_model = "custom"`
- `allowed_tool_groups = []`
- `allowed_mcp_servers = []`
- `allowed_skills = []`
- `default_enabled = False`

The `description` passed to `add_agent()` remains UI metadata only. It must not be injected as an additional system prompt into the compiled graph.

### Runtime resolution

`AgentEngine._get_or_build_agent()` should detect `preset.source == "code"` or `preset_id in self._custom_presets` and directly return the registered graph from `self._agents[preset_id]`.

For code agents, runtime should ignore:

- frontend model override
- MCP generation cache invalidation
- framework tool group toggles
- framework MCP toggles
- framework Skills toggles
- framework middleware assembly

This prevents code agents from accidentally being rebuilt through `build_agent()`.

### Default toggle endpoint

The endpoint that applies an agent's default tool/MCP toggle state should treat code agents as no-op and return an explanatory result. Selecting a code agent must not globally enable or disable framework tools or MCP servers.

### API semantics

Agent list/detail responses should return code agents with explicit empty framework capability arrays. This makes future frontend logic naturally interpret code agents as having no framework-managed configurable capabilities.

## Frontend Design

### Right panel behavior

When the selected agent has `source === "code"`:

- Hide model selector for runtime override.
- Hide summarization configuration.
- Hide tool group list.
- Hide MCP server list.
- Hide Skills list.
- Show a read-only explanation card.

Suggested card text:

> 此智能体由代码注册，工具、MCP、Skills、提示词和模型由代码中的 graph 决定。当前面板的框架级配置不适用于它。

### Agent editor behavior

When editing a code agent:

- Do not show editable system prompt, model, tools, MCP, or Skills controls.
- Show a read-only explanation that code agents are defined by their compiled graph.
- If name/description editing is not supported for code agents, keep the dialog informational only.

### Message sending

When sending a message to a code agent:

- Continue passing `preset_id` so backend resolves the registered graph.
- Do not pass the current UI model override, or pass an empty model string.
- Do not imply that right-panel toggles affect the code agent.

### Runtime tool call display

Do not hide tool call cards or token usage details in the chat transcript. These represent actual events emitted by the graph and remain useful for debugging and auditing.

## Success Criteria

- Selecting a code agent shows a read-only explanatory right-panel state instead of configurable framework tools.
- Editing a code agent no longer suggests prompt/model/tool/MCP/Skill settings can be changed through the UI.
- API responses for code agents expose empty framework capability arrays.
- Code agents always execute the originally registered graph and never route through `build_agent()` because of model override, cache miss, or MCP generation changes.
- Built-in and user-created preset agents keep their existing configurable behavior.
- Actual runtime tool calls from code graphs still appear in chat messages.

## Non-goals

- Do not inspect or infer tools inside an arbitrary compiled graph.
- Do not add migration compatibility for older code-agent metadata; this project is still early-stage.
- Do not split code agents into a separate API resource yet. The current AgentPreset shape remains sufficient for this fix.

## Testing Plan

- Backend unit test: `app.add_agent()` creates code-agent metadata with empty framework capability arrays and `source="code"`.
- Backend unit test: `_get_or_build_agent()` returns the registered graph for code agents and does not call `build_agent()`.
- Backend route test: applying default toggles to a code agent is a no-op.
- Frontend unit/component test: right panel renders the read-only code-agent card and hides tool/MCP/Skill controls.
- Frontend unit/component test: agent editor hides framework configuration controls for code agents.
- Manual test: select `__power__`, then a code agent, then back to `__power__`; framework-managed preset behavior remains unchanged.
