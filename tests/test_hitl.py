import pytest
from lc_agent.core.engine import AgentEngine
from lc_agent.core.models import AgentPreset
from lc_agent.core.permissions import PermissionsService
from lc_agent.tools.registry import ToolRegistry, tool


@pytest.fixture
def hitl_engine(tmp_path):
    ToolRegistry._global_tools = {}
    ToolRegistry._group_descriptions = {}
    ToolRegistry._instance = None

    @tool(group="filesystem")
    def delete_file(path: str) -> str:
        """Delete a file."""
        return "deleted"

    config = {
        "provider": {
            "test": {
                "api_key": "test-key",
                "base_url": "http://localhost:11434/v1",
                "models": [{"model_id": "test-model", "raw_model_id": "test-model"}],
            }
        },
        "agent": {
            "system_prompt": "You are helpful.",
            "default_model": "test-model",
        },
    }
    engine = AgentEngine(config)
    engine._permissions_service = PermissionsService(tmp_path / "permissions.jsonc")
    yield engine
    ToolRegistry._global_tools = {}
    ToolRegistry._group_descriptions = {}
    ToolRegistry._instance = None


def test_build_agent_with_permissions_service(hitl_engine):
    """Agent with permissions service should build successfully."""
    preset = AgentPreset(
        id="test-hitl",
        name="HITL Agent",
        system_prompt="Be careful.",
        default_model="test-model",
    )
    agent = hitl_engine.build_agent(preset)
    assert agent is not None


def test_build_agent_without_permissions_service(hitl_engine):
    """Agent without permissions service should build without HITL middleware."""
    hitl_engine._permissions_service = None
    preset = AgentPreset(
        id="test-safe",
        name="Safe Agent",
        system_prompt="Be safe.",
        default_model="test-model",
    )
    agent = hitl_engine.build_agent(preset)
    assert agent is not None


def test_build_agent_bypass_permissions_skips_hitl(hitl_engine, monkeypatch):
    """bypass_permissions=True：顶层 agent 不挂 HITL，也不提供 ask_user（无人值守通道）。"""
    import langchain.agents.middleware as lcm
    import lc_agent.middlewares as lcam
    from langchain.agents.middleware import HumanInTheLoopMiddleware

    hitl_created, ask_user_created = [], []

    class _RecordingHITL(HumanInTheLoopMiddleware):
        def __init__(self, *args, **kwargs):
            hitl_created.append(True)
            super().__init__(*args, **kwargs)

    class _RecordingAskUser(lcam.AskUserMiddleware):
        def __init__(self, *args, **kwargs):
            ask_user_created.append(True)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(lcm, "HumanInTheLoopMiddleware", _RecordingHITL)
    monkeypatch.setattr(lcam, "AskUserMiddleware", _RecordingAskUser)

    preset = AgentPreset(
        id="test-bypass",
        name="Bypass Agent",
        system_prompt="Unattended.",
        default_model="test-model",
    )
    hitl_engine.build_agent(preset)
    assert hitl_created and ask_user_created

    hitl_created.clear()
    ask_user_created.clear()
    hitl_engine.build_agent(preset, bypass_permissions=True)
    assert not hitl_created and not ask_user_created


def test_cache_key_bypass_suffix(hitl_engine):
    base = hitl_engine._get_agent_cache_key("p-x")
    assert hitl_engine._get_agent_cache_key("p-x", _bypass_permissions=True) == base + "::nohitl"


def test_get_or_build_agent_bypass_variant_cached_separately(hitl_engine):
    """免审变体按独立缓存键缓存，不覆盖带审批的 agent 实例。"""
    preset = AgentPreset(
        id="p-sep",
        name="Sep Agent",
        system_prompt="Separate.",
        default_model="test-model",
    )
    hitl_engine._presets["p-sep"] = preset
    with_hitl = hitl_engine._get_or_build_agent("p-sep")
    no_hitl = hitl_engine._get_or_build_agent("p-sep", bypass_permissions=True)
    assert with_hitl is not no_hitl
    assert hitl_engine._get_or_build_agent("p-sep", bypass_permissions=True) is no_hitl
    assert "p-sep::nohitl" in hitl_engine._agents
