# lc_agent/core/engine.py
from __future__ import annotations

import logging
from typing import Annotated, Any, AsyncIterator

from langchain.agents.middleware import TodoListMiddleware
from langchain.agents.middleware.summarization import SummarizationMiddleware

from lc_agent.core.http_trace import get_http_trace_collector
from lc_agent.core.http_trace_httpx import TracingAsyncClient
from lc_agent.core.models import AgentPreset, ModelInfo
from lc_agent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

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

    BUILTIN_IDS = {"__chat__", "__empty__", "__power__"}

    def get_builtin_presets(self) -> list[AgentPreset]:
        """Return the three built-in agent presets."""
        agent_conf = self.config.get("agent", {})
        default_model = agent_conf.get("default_model", "")
        return [
            AgentPreset(
                id="__chat__",
                name="Chat",
                system_prompt="You are a helpful assistant. Respond in the user's language.",
                default_model=default_model,
                allowed_tool_groups=[],
                allowed_mcp_servers=[],
                allowed_skills=[],
                source="builtin",
                default_enabled=False,
            ),
            AgentPreset(
                id="__empty__",
                name="Empty",
                system_prompt=agent_conf.get("system_prompt", "You are a helpful assistant."),
                default_model=default_model,
                allowed_tool_groups=None,
                allowed_mcp_servers=None,
                allowed_skills=[],
                source="builtin",
                default_enabled=False,
            ),
            AgentPreset(
                id="__power__",
                name="Power",
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

    def _make_subagent_tool(
        self,
        subagent_id: str,
        depth: int,
        building_set: frozenset[str],
    ):
        """Wrap a sub-agent preset as an async langchain tool.

        Returns None if the sub-agent cannot be found or if circular dependency.
        Propagates RunnableConfig so nested events appear in the parent stream.
        """
        from langchain_core.tools import tool as lc_tool
        from langchain_core.runnables import RunnableConfig

        has_injected = _HAS_INJECTED_TOOL_CALL_ID

        if subagent_id in building_set:
            logger.warning("Subagent circular reference detected: %s — skipping", subagent_id)
            return None

        if not self._preset_exists(subagent_id):
            logger.warning("Subagent preset not found: %s — skipping", subagent_id)
            return None

        subagent_preset = self._resolve_preset(subagent_id)

        try:
            sub_agent = self._get_or_build_agent(subagent_id, _depth=depth)
        except Exception as exc:
            logger.warning("Could not build subagent %s: %s — skipping", subagent_id, exc)
            return None

        agent_name = subagent_id
        agent_desc = f"{subagent_preset.name}: {subagent_preset.system_prompt[:200]}"

        if has_injected:
            @lc_tool(agent_name, description=agent_desc)
            async def _call_subagent(
                query: str,
                tool_call_id: Annotated[str, InjectedToolCallId],
                config: RunnableConfig,
            ) -> str:
                """Invoke a specialist sub-agent. Pass the full task as query."""
                tc_id = tool_call_id
                parent_tid = (config or {}).get("configurable", {}).get("thread_id") or ""
                sub_thread_id = f"{parent_tid}/sa/{tc_id}"

                sub_config = {
                    **(config or {}),
                    "configurable": {
                        **((config or {}).get("configurable") or {}),
                        "thread_id": sub_thread_id,
                        "sub_session_id": sub_thread_id,
                    },
                }

                try:
                    result = await sub_agent.ainvoke(
                        {"messages": [{"role": "user", "content": query}]},
                        config=sub_config,
                    )
                    msgs = result.get("messages", [])
                    return msgs[-1].content if msgs else ""
                except Exception as exc:
                    logger.exception("Subagent %s failed: %s", subagent_id, exc)
                    return f"[Sub-agent error: {exc}]"
        else:
            @lc_tool(agent_name, description=agent_desc)
            async def _call_subagent(query: str, config: RunnableConfig) -> str:
                """Invoke a specialist sub-agent. Pass the full task as query."""
                import uuid

                tc_id = (config or {}).get("configurable", {}).get("tool_call_id") or uuid.uuid4().hex
                parent_tid = (config or {}).get("configurable", {}).get("thread_id") or ""
                sub_thread_id = f"{parent_tid}/sa/{tc_id}"

                sub_config = {
                    **(config or {}),
                    "configurable": {
                        **((config or {}).get("configurable") or {}),
                        "thread_id": sub_thread_id,
                        "sub_session_id": sub_thread_id,
                    },
                }

                try:
                    result = await sub_agent.ainvoke(
                        {"messages": [{"role": "user", "content": query}]},
                        config=sub_config,
                    )
                    msgs = result.get("messages", [])
                    return msgs[-1].content if msgs else ""
                except Exception as exc:
                    logger.exception("Subagent %s failed: %s", subagent_id, exc)
                    return f"[Sub-agent error: {exc}]"

        return _call_subagent

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
        tools = self.tool_registry.get_filtered_tools(preset.allowed_tool_groups)

        if hasattr(self, '_skills_toolkit') and self._skills_toolkit:
            allowed = preset.allowed_skills
            if allowed is None or allowed:
                skill_tools = [
                    t for t in self._skills_toolkit.get_tools()
                    if t.name != "list_skills"
                ]
                tools = tools + skill_tools
                loader = self._skills_toolkit._resolved_loader
                if loader:
                    all_skills = loader.list_skills()
                    if allowed is not None:
                        all_skills = [s for s in all_skills if s.name in allowed]
                    if all_skills:
                        lines = ["# Available Skills", ""]
                        for s in all_skills:
                            lines.append(f"- **{s.name}**: {s.description}")
                        lines.append("")
                        lines.append(
                            "Use `load_skill` to get full instructions for a skill, "
                            "`read_skill_resource` to read its resources, "
                            "and `run_skill_script` to execute its scripts."
                        )
                        system_prompt = f"{system_prompt}\n\n" + "\n".join(lines)

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
            system_prompt = f"{system_prompt}\n\n{MEMORY_SYSTEM_PROMPT}"
            kwargs["store"] = self._store
            kwargs["context_schema"] = AgentRuntimeContext

        subagent_tool_names: set[str] = set()
        if getattr(preset, "subagent_ids", None):
            max_depth = self.config.get("agent", {}).get("max_subagent_depth", 2)
            if _depth < max_depth:
                new_building = (building_set or frozenset()) | {preset.id}
                for sid in preset.subagent_ids:
                    sa_tool = self._make_subagent_tool(sid, _depth + 1, new_building)
                    if sa_tool is not None:
                        tools.append(sa_tool)
                        subagent_tool_names.add(sid)

        model_info = self._find_model(preset.default_model)
        effective_params = {**(preset.llm_params or {}), **(llm_params or {})}
        llm = self._create_llm(model_info, preset.default_model, llm_params=effective_params or None)

        from langchain.agents import create_agent

        middleware = [TodoListMiddleware()]
        middleware.extend(self._build_summarization_middleware(preset))

        if hasattr(self, '_permissions_service') and self._permissions_service:
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
        """Return the set of tool names that are sub-agents for the given preset."""
        cache_key = self._get_agent_cache_key(
            preset_id,
            model_id if self._find_model(model_id) else "",
            llm_params=llm_params,
            _depth=_depth,
        )
        return self._agent_subagent_tools.get(cache_key, set())

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

    def invalidate_all_agents(self) -> None:
        """Remove all cached agents, forcing rebuild on next use."""
        self._agents.clear()
        self._agent_mcp_gen.clear()
        self._agent_subagent_tools.clear()

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
        preset_id: str = "__chat__",
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
        preset_id: str = "__chat__",
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
