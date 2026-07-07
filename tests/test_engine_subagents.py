import pytest
from unittest.mock import MagicMock
from lc_agent.core.models import AgentPreset
from lc_agent.core.engine import AgentEngine


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


def test_make_subagent_tool_returns_none_on_circular():
    engine = AgentEngine(MINIMAL_CONFIG)
    # "a" already in building_set → circular → returns None
    tool = engine._make_subagent_tool("a", depth=1, building_set=frozenset(["a"]))
    assert tool is None


def test_get_subagent_tool_names_returns_empty_before_build():
    engine = AgentEngine(MINIMAL_CONFIG)
    names = engine.get_subagent_tool_names("__chat__")
    assert names == set()
