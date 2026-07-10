# lc_agent/core/engine.py
import logging
from dataclasses import dataclass
import re
from typing import Annotated, Any, AsyncIterator, Literal

from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain.agents.middleware.summarization import SummarizationMiddleware
from langchain.agents.middleware.todo import WRITE_TODOS_SYSTEM_PROMPT, WRITE_TODOS_TOOL_DESCRIPTION
try:
    from langchain.agents.middleware.types import AgentMiddleware as _AgentMiddlewareBase
    from langchain_core.messages import SystemMessage
    _HAS_MIDDLEWARE_BASE = True
except ImportError:
    _AgentMiddlewareBase = object  # type: ignore[misc,assignment]
    _HAS_MIDDLEWARE_BASE = False

from lc_agent.core.http_trace import (
    HttpTraceCollector,
    bind_http_trace_collector,
    get_http_trace_collector,
    register_subagent_collector,
    reset_http_trace_collector,
)
from lc_agent.core.http_trace_httpx import TracingAsyncClient
from lc_agent.core.models import AgentPreset, ModelInfo
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool as lc_tool
from pydantic import Field as _PydanticField

from lc_agent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

TODO_FINAL_ANSWER_GUARD = """## Final Answer Guard for `write_todos`

- Do not create todo items whose only purpose is to write, organize, summarize, or deliver the final answer.
- Before writing the substantive final answer to the user, make your last necessary `write_todos` call.
- After you start writing the substantive final answer, do not call `write_todos` again in the same turn.
- If the only remaining todo is about producing the final answer, do not call `write_todos` just to mark it complete. Deliver the final answer directly.
"""

TODO_SYSTEM_PROMPT = f"{WRITE_TODOS_SYSTEM_PROMPT}\n\n{TODO_FINAL_ANSWER_GUARD}"
TODO_TOOL_DESCRIPTION = f"{WRITE_TODOS_TOOL_DESCRIPTION}\n\n{TODO_FINAL_ANSWER_GUARD}"

_LOAD_SKILL_DESCRIPTION = (
    "Retrieve the full step-by-step instructions for a skill. "
    "This MUST be called before executing any task that matches a skill — "
    "the brief description in the system prompt is only a trigger hint, "
    "not the actual procedure. "
    "Returns the skill's markdown body, available resources, and scripts. "
    "Skill names are listed in the system prompt under '## Available Skills'."
)


class _SystemBlockMiddleware(_AgentMiddlewareBase):  # type: ignore[misc]
    """Injects a text block as a separate system message content block."""

    def __init__(self, text: str, middleware_name: str, *, prepend: bool = False) -> None:
        super().__init__()
        self._text = text
        self._middleware_name = middleware_name
        self._prepend = prepend

    @property
    def name(self) -> str:  # type: ignore[override]
        return self._middleware_name

    def _patched_system(self, existing: Any) -> Any:
        if self._prepend:
            new_block = {"type": "text", "text": self._text}
            new_content = [new_block, *(existing.content_blocks if existing is not None else [])]
        else:
            new_block = {"type": "text", "text": f"\n\n{self._text}"}
            new_content = [*(existing.content_blocks if existing is not None else []), new_block]
        return SystemMessage(content_blocks=new_content)  # type: ignore[call-arg]

    def wrap_model_call(self, request: Any, handler: Any) -> Any:
        return handler(request.override(system_message=self._patched_system(request.system_message)))

    async def awrap_model_call(self, request: Any, handler: Any) -> Any:
        return await handler(request.override(system_message=self._patched_system(request.system_message)))


# Keep old name as alias for backwards compatibility
_SkillsPromptMiddleware = _SystemBlockMiddleware

# --------------------------------------------------------------------------- #
# Subagent prompts
# --------------------------------------------------------------------------- #

SUBAGENT_DELEGATION_PROMPT = (
    "In order to complete the objective that the user asks of you, "
    "you have access to a number of standard tools.\n\n"
    "You receive a single task message and cannot ask for clarification or send follow-up messages. "
    "Complete the task entirely within this one invocation.\n\n"
    "Only your **last assistant message** is returned as the final output — "
    "every message you produce during tool use (including thoughts between tool calls) is discarded. "
    "After finishing all tool use, write a single complete answer in your final message. "
    "Do NOT say 'as shown above' or reference any intermediate tool output — "
    "your final message must be fully self-contained and contain the complete answer."
)

TASK_SYSTEM_PROMPT = """\
## task（子智能体调度器）

你拥有 `task` 工具，可以将独立任务委派给专用子智能体完成。\
这些子智能体是一次性的，仅在任务期间存在，完成后返回单一结果。

**每次子智能体调用都是无状态且单次往返（stateless, one-shot）**：子智能体看不到你的对话历史、记忆或上下文，\
你也无法向它追加消息。它只会收到你在 `description` 参数里写的内容，并在唯一一次回复中返回结果。\
因此，`description` 必须包含子智能体**独立完成任务**所需的全部背景和上下文，\
并明确说明它需要在唯一回复中返回什么内容（格式、语言、字数等）。

`description` 错误示例（子智能体无法访问你的对话历史）：
- ❌ "帮我查一下" （无背景、无上下文、无输出要求）
- ❌ "修复上面讨论的 bug" （子智能体没有"上面"的对话上下文）

**子智能体的返回结果对用户不可见**——它只返回给你。你有责任将结果整合后再呈现给用户，而不是直接转发原文。

子智能体的完整生命周期：
1. **派遣** → 在 `description` 里写明角色、任务、期望输出格式和语言
2. **执行** → 子智能体自主完成任务
3. **返回** → 子智能体以单条消息返回结果给你
4. **整合** → 你将结果融合到当前对话，呈现给用户

**重要：若有多个独立任务，必须在同一条消息中同时发起多个 `task` 调用并行执行，而不是逐一等待。**\
并行调用能显著减少用户等待时间，请务必利用：
- ❌ 错误：先调用 `task(A)`，等 A 返回后再调用 `task(B)`
- ✅ 正确：在同一条 assistant 消息里同时发出 `task(A)` 和 `task(B)` 两个工具调用
- ⚠️ 例外：若 B 依赖 A 的结果，则必须等 A 返回后才能发起 B

何时使用 `task`：
- 任务复杂、多步骤，且可以完整委派，不需要你参与中间过程
- 任务相互独立，可以并行启动以节省时间（例如：同时研究 A 话题和 B 话题）
- 任务需要大量工具调用或 token，委派可以避免你的上下文窗口被污染
- 你只关心子智能体的最终输出，不需要中间步骤

何时**不**使用 `task`：
- 任务简单（几次工具调用或快速查询即可）
- 你需要看到中间推理过程（task 工具会隐藏中间步骤）
- 委派的子任务过于简短，拆分只会增加延迟而没有收益
- 任务依赖你的当前上下文，无法独立表达为完整的委派描述"""


@dataclass(frozen=True)
class SubAgentDescriptor:
    subagent_type: str
    preset_id: str
    display_name: str
    description: str


_GENERAL_PURPOSE_DESCRIPTION = (
    "当你需要一个与当前智能体能力相近、但在隔离上下文中并行处理复杂任务的工作线程时调用它。"
)


def _extract_subagent_result(messages: list[Any]) -> str:
    """Extract the last non-empty AI message text from a subagent's message list.

    Iterates in reverse to skip any trailing empty messages that some providers
    (e.g. Anthropic Claude) may append after the final tool call.
    Returns the first non-empty AI text found — the subagent's conclusive answer.
    """
    for msg in reversed(messages):
        if getattr(msg, "type", None) != "ai":
            continue
        content = getattr(msg, "content", "")
        if isinstance(content, str):
            text = content.strip()
        elif isinstance(content, list):
            text = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            ).strip()
        else:
            text = str(content).strip()
        if text:
            return text
    return ""

try:
    from langchain_core.tools import InjectedToolCallId
    _HAS_INJECTED_TOOL_CALL_ID = True
except ImportError:
    InjectedToolCallId = None  # type: ignore[assignment,misc]
    _HAS_INJECTED_TOOL_CALL_ID = False


class AgentEngine:
    """Core agent engine wrapping langchain.agents.create_agent with middleware support."""

    def __init__(self, config: dict, checkpointer=None, store=None):
        self.config = config
        self.tool_registry = ToolRegistry()
        self._checkpointer = checkpointer
        self._store = store
        self._agents: dict[str, Any] = {}
        self._agent_subagent_tools: dict[str, set[str]] = {}
        self._agent_subagent_display_map: dict[str, dict[str, str]] = {}
        self._current_preset: AgentPreset | None = None
        self._models: list[ModelInfo] = self._parse_models(config)
        self._presets: dict[str, AgentPreset] = {}
        self._custom_presets: dict[str, AgentPreset] = {}
        self._agent_mcp_gen: dict[str, int] = {}
        self._mcp_generation: int = 0
        self.recursion_limit: int = config.get("agent", {}).get("recursion_limit", 100)

    def _memory_enabled(self) -> bool:
        memory_conf = self.config.get("memory", {})
        if isinstance(memory_conf, dict):
            return memory_conf.get("enabled", True)
        return getattr(memory_conf, "enabled", True)

    def _is_code_agent(self, preset_id: str) -> bool:
        preset = self._resolve_preset(preset_id)
        return preset.source == "code" or preset_id in self._custom_presets

    def _should_use_memory_context(self, preset_id: str) -> bool:
        return self._store is not None and self._memory_enabled() and not self._is_code_agent(preset_id)

    def _parse_models(self, config: dict) -> list[ModelInfo]:
        """Extract ModelInfo list from config."""
        models = []
        for provider_name, provider_conf in config.get("provider", {}).items():
            if isinstance(provider_conf, dict):
                for model_conf in provider_conf.get("models", []):
                    models.append(ModelInfo(
                        id=model_conf["id"],
                        provider=provider_name,
                        base_url=provider_conf.get("base_url", ""),
                        context_limit=model_conf.get("context_limit", 8000),
                        max_output_tokens=model_conf.get("max_output_tokens", 0),
                        api_key=provider_conf.get("api_key", ""),
                    ))
        return models

    def get_models(self) -> list[ModelInfo]:
        """Return available models."""
        return self._models

    BUILTIN_IDS = {"chat", "empty", "power"}

    def get_builtin_presets(self) -> list[AgentPreset]:
        """Return the three built-in agent presets."""
        agent_conf = self.config.get("agent", {})
        default_model = agent_conf.get("default_model", "")
        return [
            AgentPreset(
                id="chat",
                name="chat",
                display_name="普通对话",
                system_prompt="You are a helpful assistant. Respond in the user's language.",
                default_model=default_model,
                allowed_tool_groups=[],
                allowed_mcp_servers=[],
                allowed_skills=[],
                source="builtin",
                default_enabled=False,
            ),
            AgentPreset(
                id="empty",
                name="empty",
                display_name="空模板",
                system_prompt=agent_conf.get("system_prompt", "You are a helpful assistant."),
                default_model=default_model,
                allowed_tool_groups=None,
                allowed_mcp_servers=None,
                allowed_skills=[],
                source="builtin",
                default_enabled=False,
            ),
            AgentPreset(
                id="power",
                name="power",
                display_name="全功能",
                system_prompt=agent_conf.get("system_prompt", "You are a helpful assistant."),
                default_model=default_model,
                allowed_tool_groups=None,
                allowed_mcp_servers=None,
                allowed_skills=None,
                source="builtin",
                default_enabled=True,
            ),
        ]

    def get_default_preset(self) -> AgentPreset:
        """Return the default agent (Chat - safest)."""
        return self.get_builtin_presets()[0]

    def _preset_exists(self, preset_id: str) -> bool:
        """Return True if preset_id refers to a known preset."""
        return (
            preset_id in self.BUILTIN_IDS
            or preset_id in self._custom_presets
            or preset_id in self._presets
        )

    def _build_subagent_registry(
        self,
        preset: AgentPreset,
        depth: int,
        building_set: frozenset[str],
    ) -> dict[str, SubAgentDescriptor]:
        max_depth = self.config.get("agent", {}).get("max_subagent_depth", 2)
        if depth >= max_depth:
            return {}

        registry: dict[str, SubAgentDescriptor] = {}
        subagent_candidates: list[tuple[str, str]] = []
        if getattr(preset, "subagents", None):
            for subagent_link in preset.subagents:
                subagent_candidates.append((
                    subagent_link.agent_id,
                    (subagent_link.delegation_description or "").strip(),
                ))

        for subagent_id, relationship_description in subagent_candidates:
            if subagent_id in building_set:
                logger.warning("Subagent circular reference detected: %s — skipping", subagent_id)
                continue
            if not self._preset_exists(subagent_id):
                logger.warning("Subagent preset not found: %s — skipping", subagent_id)
                continue
            subagent_preset = self._resolve_preset(subagent_id)
            display_name = subagent_preset.display_name or subagent_preset.name
            subagent_type = subagent_preset.name
            suffix = 1
            while subagent_type in registry:
                suffix += 1
                subagent_type = f"{subagent_preset.name}-{suffix}"
            registry[subagent_type] = SubAgentDescriptor(
                subagent_type=subagent_type,
                preset_id=subagent_id,
                display_name=display_name,
                description=(
                    relationship_description
                    or (getattr(subagent_preset, "default_delegation_description", "") or "").strip()
                    or display_name
                ),
            )

        if getattr(preset, "enable_general_purpose_subagent", False):
            gp_id = f"__gp__:{preset.id}"
            gp_preset = preset.model_copy(update={
                "id": gp_id,
                "subagents": None,
                "enable_general_purpose_subagent": False,
            })
            self._presets[gp_id] = gp_preset
            registry["general-purpose"] = SubAgentDescriptor(
                subagent_type="general-purpose",
                preset_id=gp_id,
                display_name="通用助手",
                description=_GENERAL_PURPOSE_DESCRIPTION,
            )

        return registry

    def _make_task_tool(
        self,
        registry: dict[str, SubAgentDescriptor],
        depth: int,
        building_set: frozenset[str],
    ):
        async def _run_subagent(subagent_type: str, description: str, config: RunnableConfig, tool_call_id: str) -> str:
            descriptor = registry.get(subagent_type)
            if descriptor is None:
                available = ", ".join(sorted(registry))
                return f"[Sub-agent error: Unknown subagent_type '{subagent_type}'. Available: {available}]"

            try:
                sub_agent = self._get_or_build_agent(descriptor.preset_id, _depth=depth)
            except Exception as exc:
                logger.exception("Subagent %s failed to build: %s", descriptor.preset_id, exc)
                return f"[Sub-agent error: {exc}]"

            configurable = (config or {}).get("configurable", {})
            parent_tid = configurable.get("thread_id") or ""
            lg_ns = configurable.get("checkpoint_ns", "")
            tc_id = next(
                (seg.split(":", 1)[1] for seg in lg_ns.split("|") if seg.startswith("tools:")),
                tool_call_id,
            )
            sub_thread_id = f"{parent_tid}--sa--{tc_id}"
            sub_config = {
                **(config or {}),
                "configurable": {
                    **((config or {}).get("configurable") or {}),
                    "thread_id": sub_thread_id,
                    "sub_session_id": sub_thread_id,
                },
            }

            _sa_collector = HttpTraceCollector(provider=None, model=None)
            _trace_token = bind_http_trace_collector(_sa_collector)
            try:
                result = await sub_agent.ainvoke(
                    {"messages": [{"role": "user", "content": description}]},
                    config=sub_config,
                )
                msgs = result.get("messages", [])
                return _extract_subagent_result(msgs)
            except Exception as exc:
                logger.exception("Subagent %s failed: %s", descriptor.preset_id, exc)
                return f"[Sub-agent error: {exc}]"
            finally:
                reset_http_trace_collector(_trace_token)
                register_subagent_collector(sub_thread_id, _sa_collector)

        description_lines = [
            "Delegate a task to one configured sub-agent.",
            "",
            "Each call is **stateless and one-shot**: the sub-agent only sees what you put in",
            "the `description` argument. Therefore `description` must be fully self-contained:",
            "include ALL background, specify exactly what to return in the **final and only reply**",
            "(sections, format, language, length).",
            "",
            "**Good description example**:",
            "  \"The user is building a Python project using LangChain. Please research LangChain",
            "  v0.3's checkpointing mechanism, focusing on: (1) InMemorySaver vs SqliteSaver",
            "  differences, (2) per-user memory configuration. Return a detailed Chinese analysis",
            "  with code examples, in sections: Overview / Comparison / Recommendation.\"",
            "**Bad description examples**:",
            "  ❌ \"Research LangChain memory.\" (no context, no output format)",
            "  ❌ \"Fix the checkpoint bug we discussed above.\" (sub-agent has no 'above' context)",
            "",
            "Use the exact `subagent_type` value from the list below.",
            "Do not rename it, paraphrase it, translate it, or invent a new value.",
            "",
            "Available subagents:",
            "",
        ]
        for descriptor in registry.values():
            description_lines.extend([
                "====================",
                "",
                f"subagent_type: {descriptor.subagent_type}",
                "",
                "when_to_use:",
                descriptor.description,
                "",
            ])
        if description_lines and description_lines[-1] == "":
            description_lines.pop()
        task_description = "\n".join(description_lines)

        available_types = sorted(descriptor.subagent_type for descriptor in registry.values())
        subagent_type_field_desc = (
            f"The type of subagent to use. Must be exactly one of: "
            f"{', '.join(repr(t) for t in available_types)}. "
            "Do not translate or modify it."
        )
        description_field_desc = (
            "A detailed description of the task for the subagent to perform autonomously. "
            "Must include ALL necessary background and context — the subagent cannot access your "
            "conversation history and you cannot send follow-up messages. "
            "Specify exactly what the subagent must return in its final and only reply "
            "(sections, format, language, length)."
        )

        if _HAS_INJECTED_TOOL_CALL_ID:
            @lc_tool("task", description=task_description)
            async def task(
                subagent_type: Annotated[Literal[*available_types], _PydanticField(  # type: ignore[valid-type]
                    description=subagent_type_field_desc,
                )],
                description: Annotated[str, _PydanticField(description=description_field_desc)],
                tool_call_id: Annotated[str, InjectedToolCallId],
                config: RunnableConfig,
            ) -> str:
                return await _run_subagent(subagent_type, description, config, tool_call_id)
        else:
            @lc_tool("task", description=task_description)
            async def task(
                subagent_type: Annotated[Literal[*available_types], _PydanticField(  # type: ignore[valid-type]
                    description=subagent_type_field_desc,
                )],
                description: Annotated[str, _PydanticField(description=description_field_desc)],
                config: RunnableConfig,
            ) -> str:
                import uuid

                tool_call_id = ((config or {}).get("configurable") or {}).get("tool_call_id") or uuid.uuid4().hex
                return await _run_subagent(subagent_type, description, config, tool_call_id)

        return task
    def build_agent(
        self,
        preset: AgentPreset | None = None,
        cache_key: str | None = None,
        llm_params: dict | None = None,
        building_set: frozenset[str] | None = None,
        _depth: int = 0,
    ):
        """Build a LangGraph ReAct agent from preset."""
        if preset is None:
            preset = self.get_default_preset()
        self._current_preset = preset

        system_prompt = preset.system_prompt
        # Subagents need an explicit reminder that only the final message is returned to the caller
        if _depth > 0 and not _HAS_MIDDLEWARE_BASE:
            system_prompt = f"{system_prompt}\n\n{SUBAGENT_DELEGATION_PROMPT}"
        tools = self.tool_registry.get_filtered_tools(preset.allowed_tool_groups)

        _memory_middleware: _SystemBlockMiddleware | None = None
        _skills_middleware: _SystemBlockMiddleware | None = None
        if hasattr(self, '_skills_toolkit') and self._skills_toolkit:
            allowed = preset.allowed_skills
            if allowed is None or allowed:
                skill_tools = []
                for _t in self._skills_toolkit.get_tools():
                    if _t.name == "list_skills":
                        continue
                    if _t.name == "load_skill":
                        try:
                            _t = _t.model_copy(update={"description": _LOAD_SKILL_DESCRIPTION})
                        except Exception:
                            pass
                    skill_tools.append(_t)
                tools = tools + skill_tools
                loader = self._skills_toolkit._resolved_loader
                if loader:
                    all_skills = loader.list_skills()
                    if allowed is not None:
                        all_skills = [s for s in all_skills if s.name in allowed]
                    if all_skills and _HAS_MIDDLEWARE_BASE:
                        import json as _json
                        skill_entries = [
                            {
                                "skill_name": s.name,
                                "description": s.description.splitlines()[0],
                            }
                            for s in all_skills
                        ]
                        lines = [
                            "## Available Skills",
                            "",
                            "The descriptions below are **triggers** — they tell you WHEN a skill applies.",
                            "The actual step-by-step instructions, required tools, and constraints are INSIDE the skill.",
                            "",
                            "**MANDATORY RULE**: When the user's request matches a skill's description,",
                            "you MUST call `load_skill(skill_name=\"<skill_name>\")` FIRST to retrieve",
                            "the full instructions, then follow them exactly.",
                            "Do NOT skip this step and proceed with your default approach.",
                            "",
                            "```json",
                            _json.dumps(skill_entries, ensure_ascii=False, indent=2),
                            "```",
                            "",
                            "After loading a skill, you may also call `read_skill_resource` to fetch",
                            "its reference files or `run_skill_script` to execute its scripts.",
                        ]
                        _skills_middleware = _SystemBlockMiddleware("\n".join(lines), "SkillsPromptMiddleware")

        if hasattr(self, '_mcp_manager') and self._mcp_manager:
            mcp_tools = self._mcp_manager.get_filtered_langchain_tools(preset.allowed_mcp_servers)
            tools = tools + mcp_tools

        kwargs: dict[str, Any] = {}
        if self._checkpointer:
            kwargs["checkpointer"] = self._checkpointer

        if self._store is not None and self._memory_enabled():
            from lc_agent.core.memory import (
                AgentRuntimeContext,
                MEMORY_SYSTEM_PROMPT,
                build_memory_tools,
            )

            tools = tools + build_memory_tools()
            if _HAS_MIDDLEWARE_BASE:
                _memory_middleware = _SystemBlockMiddleware(MEMORY_SYSTEM_PROMPT, "MemoryPromptMiddleware")
            else:
                system_prompt = f"{system_prompt}\n\n{MEMORY_SYSTEM_PROMPT}"
            kwargs["store"] = self._store
            kwargs["context_schema"] = AgentRuntimeContext

        new_building = (building_set or frozenset()) | {preset.id}
        subagent_registry = self._build_subagent_registry(preset, depth=_depth, building_set=new_building)
        subagent_tool_names: set[str] = set()
        subagent_display_map: dict[str, str] = {}
        if subagent_registry:
            tools.append(self._make_task_tool(subagent_registry, _depth + 1, new_building))
            subagent_tool_names = {"task"}
            subagent_display_map = {
                descriptor.subagent_type: descriptor.display_name
                for descriptor in subagent_registry.values()
            }

        model_info = self._find_model(preset.default_model)
        effective_params = {**(preset.llm_params or {}), **(llm_params or {})}
        llm = self._create_llm(model_info, preset.default_model, llm_params=effective_params or None)

        middleware = []
        if _depth > 0 and _HAS_MIDDLEWARE_BASE:
            middleware.append(_SystemBlockMiddleware(
                SUBAGENT_DELEGATION_PROMPT, "SubagentDelegationMiddleware", prepend=True
            ))
        if _memory_middleware is not None:
            middleware.append(_memory_middleware)
        if _skills_middleware is not None:
            middleware.append(_skills_middleware)
        if _depth == 0 and subagent_registry:
            if _HAS_MIDDLEWARE_BASE:
                middleware.append(_SystemBlockMiddleware(TASK_SYSTEM_PROMPT, "TaskSystemPromptMiddleware"))
            else:
                system_prompt = f"{system_prompt}\n\n{TASK_SYSTEM_PROMPT}"
        if _depth == 0:
            middleware.append(TodoListMiddleware(
                system_prompt=TODO_SYSTEM_PROMPT,
                tool_description=TODO_TOOL_DESCRIPTION,
            ))
        middleware.extend(self._build_summarization_middleware(preset))

        # Only top-level agents need human-in-the-loop approval; sub-agents run autonomously
        if hasattr(self, '_permissions_service') and self._permissions_service and _depth == 0:
            from langchain.agents.middleware import HumanInTheLoopMiddleware
            interrupt_on = {
                tool.name: {
                    "allowed_decisions": ["approve", "reject"],
                    "when": self._permissions_service.should_interrupt,
                }
                for tool in tools
                if tool.name != "ask_user"
            }
            if interrupt_on:
                middleware.append(HumanInTheLoopMiddleware(interrupt_on=interrupt_on))

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
            middleware=middleware,
            **kwargs,
        )

        resolved_cache_key = cache_key or preset.id
        self._agents[resolved_cache_key] = agent
        self._agent_subagent_tools[resolved_cache_key] = subagent_tool_names
        self._agent_subagent_display_map[resolved_cache_key] = subagent_display_map
        return agent

    def _build_tracing_async_client(self, model_info: ModelInfo | None, model_id: str):
        provider = model_info.provider if model_info else None
        resolved_model = model_info.id if model_info else model_id
        base_url = model_info.base_url if model_info and model_info.base_url else None
        return TracingAsyncClient(
            collector_getter=get_http_trace_collector,
            provider=provider,
            model=resolved_model,
            base_url=base_url or "https://api.openai.com/v1",
            timeout=120,
        )

    def _create_llm(
        self,
        model_info: ModelInfo | None,
        model_id: str,
        llm_params: dict | None = None,
    ):
        """Create a chat model instance.

        Uses ChatOpenAIReasoning when base_url is set — extracts reasoning_content
        from any provider that returns it (DeepSeek, GLM, etc).
        Uses init_chat_model for standard providers (handles provider routing).
        """
        params = llm_params or {}
        temperature = params.get("temperature", 0.7)
        reasoning_effort = params.get("reasoning_effort")
        # passthrough: top_p, top_k, presence_penalty, frequency_penalty, max_tokens, etc.
        HANDLED_KEYS = {"temperature", "reasoning_effort"}
        extra_params = {k: v for k, v in params.items() if k not in HANDLED_KEYS and v is not None}

        if model_info and model_info.base_url:
            from lc_agent.core.chat_model import ChatOpenAIReasoning
            kwargs: dict[str, Any] = dict(
                model=model_info.id,
                base_url=model_info.base_url,
                api_key=model_info.api_key or "not-set",
                temperature=temperature,
                stream_usage=True,
                http_async_client=self._build_tracing_async_client(model_info, model_id),
                **extra_params,
            )
            if model_info.max_output_tokens > 0:
                kwargs["max_tokens"] = model_info.max_output_tokens
            if reasoning_effort:
                kwargs["reasoning_effort"] = reasoning_effort
            return ChatOpenAIReasoning(**kwargs)

        from langchain.chat_models import init_chat_model

        if model_info:
            model_str = f"{model_info.provider}:{model_info.id}" if model_info.provider else model_info.id
            kwargs: dict[str, Any] = dict(
                api_key=model_info.api_key or "not-set",
                temperature=temperature,
                stream_usage=True,
                **extra_params,
            )
            if reasoning_effort:
                kwargs["reasoning_effort"] = reasoning_effort
            return init_chat_model(model_str, **kwargs)

        kwargs: dict[str, Any] = dict(api_key="not-set", temperature=temperature, stream_usage=True, **extra_params)
        if reasoning_effort:
            kwargs["reasoning_effort"] = reasoning_effort
        return init_chat_model(model_id, **kwargs)

    def _find_model(self, model_id: str) -> ModelInfo | None:
        """Find model info by ID."""
        for m in self._models:
            if m.id == model_id:
                return m
        return None

    def _build_summarization_middleware(self, preset: AgentPreset) -> list:
        """Build SummarizationMiddleware based on config, returns empty list if disabled."""
        summ_conf = self.config.get("agent", {}).get("summarization", {})
        if not summ_conf.get("enabled", True):
            return []

        summ_model_id = summ_conf.get("default_model", "") or preset.default_model
        model_info = self._find_model(summ_model_id)
        llm = self._create_llm(model_info, summ_model_id)

        trigger = self._parse_context_size(summ_conf.get("trigger")) or ("fraction", 0.85)
        keep = self._parse_context_size(summ_conf.get("keep")) or ("fraction", 0.20)

        needs_profile = trigger[0] == "fraction" or keep[0] == "fraction"
        if needs_profile and model_info:
            llm.profile = {"max_input_tokens": model_info.context_limit}

        kwargs: dict[str, Any] = {"model": llm, "keep": keep, "trigger": trigger}

        try:
            mw = SummarizationMiddleware(**kwargs)
            logger.info("SummarizationMiddleware enabled: trigger=%s, keep=%s", trigger, keep)
            return [mw]
        except Exception:
            logger.exception("Failed to create SummarizationMiddleware")
            return []

    @staticmethod
    def _parse_context_size(value) -> tuple | None:
        """Parse a context size value from config (e.g. ["fraction", 0.85]) into a tuple."""
        if value is None:
            return None
        if isinstance(value, (list, tuple)) and len(value) == 2:
            kind, amount = value
            if kind in ("fraction", "tokens", "messages"):
                return (kind, amount)
        return None

    def _resolve_preset(self, preset_id: str) -> AgentPreset:
        """Resolve a preset ID to an AgentPreset object."""
        if preset_id in self.BUILTIN_IDS:
            for bp in self.get_builtin_presets():
                if bp.id == preset_id:
                    return bp
        if preset_id in self._custom_presets:
            return self._custom_presets[preset_id]
        if preset_id in self._presets:
            return self._presets[preset_id]
        return self.get_default_preset()

    def _get_agent_cache_key(
        self,
        preset_id: str,
        model_id: str = "",
        llm_params: dict | None = None,
        _depth: int = 0,
    ) -> str:
        key = f"{preset_id}::model::{model_id}" if model_id else preset_id
        if llm_params:
            import json
            key = f"{key}::llm::{json.dumps(llm_params, sort_keys=True)}"
        if _depth:
            key = f"{key}::depth::{_depth}"
        return key

    def get_subagent_tool_names(
        self,
        preset_id: str,
        model_id: str = "",
        llm_params: dict | None = None,
        _depth: int = 0,
    ) -> set[str]:
        """Return the set of tool names (not IDs) that are sub-agents for the given preset."""
        cache_key = self._get_agent_cache_key(
            preset_id,
            model_id if self._find_model(model_id) else "",
            llm_params=llm_params,
            _depth=_depth,
        )
        return self._agent_subagent_tools.get(cache_key, set())

    def get_subagent_display_name_map(
        self,
        preset_id: str,
        model_id: str = "",
        llm_params: dict | None = None,
        _depth: int = 0,
    ) -> dict[str, str]:
        """Return {tool_name: display_name} for sub-agents of the given preset."""
        cache_key = self._get_agent_cache_key(
            preset_id,
            model_id if self._find_model(model_id) else "",
            llm_params=llm_params,
            _depth=_depth,
        )
        return self._agent_subagent_display_map.get(cache_key, {})

    def invalidate_agent_cache(self, preset_id: str, keep_exact: bool = False) -> None:
        """Remove cached agents for a preset, including model/llm_params override variants."""
        prefix = f"{preset_id}::"
        keys = [
            key
            for key in self._agents
            if key.startswith(prefix) or (key == preset_id and not keep_exact)
        ]
        for key in keys:
            self._agents.pop(key, None)
            self._agent_mcp_gen.pop(key, None)
            self._agent_subagent_tools.pop(key, None)
            self._agent_subagent_display_map.pop(key, None)

    def invalidate_all_agents(self) -> None:
        """Remove all cached agents, forcing rebuild on next use."""
        self._agents.clear()
        self._agent_mcp_gen.clear()
        self._agent_subagent_tools.clear()
        self._agent_subagent_display_map.clear()

    def _resolve_preset_for_model(self, preset_id: str, model_id: str = "") -> AgentPreset:
        preset = self._resolve_preset(preset_id)
        if model_id and self._find_model(model_id):
            return preset.model_copy(update={"default_model": model_id})
        return preset

    def _get_or_build_agent(
        self,
        preset_id: str,
        model_id: str = "",
        llm_params: dict | None = None,
        _depth: int = 0,
    ):
        """Get cached agent or build a new one. Rebuilds preset agents if MCP state changed."""
        preset = self._resolve_preset(preset_id)
        if preset.source == "code" or preset_id in self._custom_presets:
            agent = self._agents.get(preset_id)
            if agent is None:
                raise ValueError(f"Code agent '{preset_id}' is registered without a graph")
            return agent

        if model_id and self._find_model(model_id):
            preset = preset.model_copy(update={"default_model": model_id})
        cache_key = self._get_agent_cache_key(
            preset_id,
            model_id if preset.default_model == model_id else "",
            llm_params=llm_params,
            _depth=_depth,
        )
        mcp_gen = getattr(self, '_mcp_generation', 0)
        cached = self._agents.get(cache_key)
        cached_gen = self._agent_mcp_gen.get(cache_key, -1)
        if cached is None or cached_gen != mcp_gen:
            agent = self.build_agent(preset, cache_key=cache_key, llm_params=llm_params, _depth=_depth)
            self._agent_mcp_gen[cache_key] = mcp_gen
            return agent
        return cached

    async def chat(
        self,
        message: str,
        thread_id: str,
        preset_id: str = "chat",
        model_id: str = "",
        user_id: str = "anonymous",
    ) -> str:
        """Send a message and get a response (non-streaming)."""
        agent = self._get_or_build_agent(preset_id, model_id)

        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": self.recursion_limit}
        invoke_kwargs: dict[str, Any] = {"config": config}
        if self._should_use_memory_context(preset_id):
            from lc_agent.core.memory import AgentRuntimeContext, normalize_memory_user_id

            invoke_kwargs["context"] = AgentRuntimeContext(user_id=normalize_memory_user_id(user_id))
        result = await agent.ainvoke({"messages": [{"role": "user", "content": message}]}, **invoke_kwargs)
        messages = result.get("messages", [])
        if messages:
            return messages[-1].content
        return ""

    async def chat_stream(
        self,
        message: str,
        thread_id: str,
        preset_id: str = "chat",
        model_id: str = "",
        history: list[dict[str, str]] | None = None,
        llm_params: dict | None = None,
        user_id: str = "anonymous",
    ) -> AsyncIterator[dict]:
        """Stream chat responses as events."""
        agent = self._get_or_build_agent(preset_id, model_id, llm_params=llm_params)

        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": self.recursion_limit}
        input_messages = list(history or [])
        input_messages.append({"role": "user", "content": message})
        stream_kwargs: dict[str, Any] = {"config": config, "version": "v2"}
        if self._should_use_memory_context(preset_id):
            from lc_agent.core.memory import AgentRuntimeContext, normalize_memory_user_id

            stream_kwargs["context"] = AgentRuntimeContext(user_id=normalize_memory_user_id(user_id))
        async for event in agent.astream_events(
            {"messages": input_messages},
            **stream_kwargs,
        ):
            yield event

    async def reset_thread(self, thread_id: str) -> None:
        """Delete all checkpoints for a thread if the checkpointer supports it."""
        if not self._checkpointer:
            return

        deleter = getattr(self._checkpointer, "adelete_thread", None)
        if callable(deleter):
            await deleter(thread_id)
            return

        sync_deleter = getattr(self._checkpointer, "delete_thread", None)
        if callable(sync_deleter):
            sync_deleter(thread_id)

    async def generate_title(self, user_message: str, model_id: str = "") -> str:
        """Generate a short conversation title from the user's first message."""
        model_info = self._find_model(model_id) if model_id else None
        if model_info is None and self._models:
            model_info = self._models[0]
        if model_info is None:
            return user_message[:20]

        llm = self._create_llm(model_info, model_info.id)
        try:
            resp = await llm.ainvoke([
                {"role": "system", "content": "用10个字以内为这段对话生成一个简洁标题。只输出标题，不要标点符号和引号。"},
                {"role": "user", "content": user_message[:200]},
            ])
            title = resp.content.strip().strip('"\'""').strip()
            return title[:30] if title else user_message[:20]
        except Exception:
            return user_message[:20]

    def get_presets(self) -> list[AgentPreset]:
        """Return all agent presets (including default and custom)."""
        default = self.get_default_preset()
        return [default] + list(self._presets.values()) + list(self._custom_presets.values())

    def add_preset(self, preset: AgentPreset) -> AgentPreset:
        """Add a new agent preset."""
        self._presets[preset.id] = preset
        return preset

    def update_preset(self, preset_id: str, data: dict) -> AgentPreset | None:
        """Update an existing preset."""
        if preset_id not in self._presets:
            return None
        existing = self._presets[preset_id]
        updated = existing.model_copy(update=data)
        self._presets[preset_id] = updated
        return updated

    def delete_preset(self, preset_id: str) -> bool:
        """Delete a preset. Cannot delete builtin."""
        if preset_id in self.BUILTIN_IDS:
            return False
        return self._presets.pop(preset_id, None) is not None
