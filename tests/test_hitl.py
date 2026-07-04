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
                "models": [{"id": "test-model"}],
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
