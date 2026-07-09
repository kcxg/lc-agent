import pytest
from unittest.mock import MagicMock

from lc_agent.core.models import AgentPreset, SubAgentLink
from lc_agent.core.engine import AgentEngine, SubAgentDescriptor


MINIMAL_CONFIG = {
    "provider": {
        "test": {
            "base_url": "http://localhost:4000/v1",
            "api_key": "test",
            "models": [{"id": "test-model", "context_limit": 8000}],
        }
    },
    "agent": {"default_model": "test-model", "max_subagent_depth": 2},
}


def test_engine_no_longer_exposes_legacy_make_subagent_tool():
    engine = AgentEngine(MINIMAL_CONFIG)
    assert not hasattr(engine, "_make_subagent_tool")


def test_get_subagent_tool_names_returns_empty_before_build():
    engine = AgentEngine(MINIMAL_CONFIG)
    names = engine.get_subagent_tool_names("__chat__")
    assert names == set()


def test_build_subagent_registry_uses_link_description_then_default_fallback():
    engine = AgentEngine(MINIMAL_CONFIG)
    child_with_link = AgentPreset(
        id="child-with-link",
        name="资料查询",
        system_prompt="查资料",
        default_model="test-model",
        default_delegation_description="默认描述不会被使用",
    )
    child_with_default = AgentPreset(
        id="child-with-default",
        name="代码审查",
        system_prompt="做代码审查",
        default_model="test-model",
        default_delegation_description="当你需要代码审查时调用它",
    )
    parent = AgentPreset(
        id="parent",
        name="主智能体",
        system_prompt="负责协调",
        default_model="test-model",
        subagents=[
            SubAgentLink(
                agent_id="child-with-link",
                delegation_description="当你需要查资料时调用它",
            ),
            SubAgentLink(
                agent_id="child-with-default",
                delegation_description="",
            ),
        ],
    )

    engine._presets = {
        child_with_link.id: child_with_link,
        child_with_default.id: child_with_default,
        parent.id: parent,
    }

    registry = engine._build_subagent_registry(parent, depth=0, building_set=frozenset())

    assert registry == {
        "资料查询": SubAgentDescriptor(
            subagent_type="资料查询",
            preset_id="child-with-link",
            display_name="资料查询",
            description="当你需要查资料时调用它",
        ),
        "代码审查": SubAgentDescriptor(
            subagent_type="代码审查",
            preset_id="child-with-default",
            display_name="代码审查",
            description="当你需要代码审查时调用它",
        ),
    }


def test_build_agent_injects_single_task_tool_and_records_display_map(monkeypatch):
    engine = AgentEngine(MINIMAL_CONFIG)
    child = AgentPreset(
        id="research-agent",
        name="研究专家",
        system_prompt="做研究",
        default_model="test-model",
        default_delegation_description="当你需要深入研究时调用它",
    )
    parent = AgentPreset(
        id="parent-agent",
        name="主智能体",
        system_prompt="协调任务",
        default_model="test-model",
        subagents=[
            SubAgentLink(
                agent_id="research-agent",
                delegation_description="",
            )
        ],
    )
    engine._presets = {child.id: child, parent.id: parent}

    captured = {}

    monkeypatch.setattr(engine, "_create_llm", lambda model_info, model_id, llm_params=None: object())
    monkeypatch.setattr(engine, "_build_summarization_middleware", lambda preset: [])

    def fake_create_agent(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    monkeypatch.setattr("lc_agent.core.engine.create_agent", fake_create_agent)

    engine.build_agent(parent, cache_key="parent-agent")

    task_tools = [tool for tool in captured["tools"] if tool.name == "task"]

    assert [tool.name for tool in task_tools] == ["task"]
    assert all(not tool.name.startswith("subagent_") for tool in captured["tools"])
    assert task_tools[0].description == (
        "Delegate a task to one configured sub-agent.\n\n"
        "Use the exact `subagent_type` value from the list below.\n"
        "Do not rename it, paraphrase it, translate it, or invent a new value.\n\n"
        "Available subagents:\n\n"
        "====================\n\n"
        "subagent_type: 研究专家\n\n"
        "delegation_description:\n"
        "当你需要深入研究时调用它"
    )
    assert engine.get_subagent_tool_names("parent-agent") == {"task"}
    assert engine.get_subagent_display_name_map("parent-agent") == {"研究专家": "研究专家"}


def test_build_subagent_registry_injects_general_purpose():
    engine = AgentEngine(MINIMAL_CONFIG)
    parent = AgentPreset(
        id="parent-agent",
        name="主智能体",
        system_prompt="协调任务",
        default_model="test-model",
        enable_general_purpose_subagent=True,
    )
    engine._presets = {parent.id: parent}

    registry = engine._build_subagent_registry(parent, depth=0, building_set=frozenset())

    assert "通用助手" in registry
    gp = registry["通用助手"]
    assert gp.preset_id == "__gp__:parent-agent"
    assert gp.display_name == "通用助手"
    assert "隔离上下文" in gp.description

    # The cloned general-purpose preset must not have subagents or gp flag
    gp_preset = engine._presets["__gp__:parent-agent"]
    assert gp_preset.subagents is None
    assert gp_preset.enable_general_purpose_subagent is False


def test_build_subagent_registry_no_general_purpose_when_disabled():
    engine = AgentEngine(MINIMAL_CONFIG)
    parent = AgentPreset(
        id="parent-agent",
        name="主智能体",
        system_prompt="协调任务",
        default_model="test-model",
        enable_general_purpose_subagent=False,
    )
    engine._presets = {parent.id: parent}

    registry = engine._build_subagent_registry(parent, depth=0, building_set=frozenset())

    assert "通用助手" not in registry
    assert "__gp__:parent-agent" not in engine._presets
