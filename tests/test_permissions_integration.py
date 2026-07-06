"""Integration tests for the permanent permissions system."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from lc_agent.core.engine import AgentEngine
from lc_agent.core.permissions import PermissionsService


@pytest.fixture
def full_engine(tmp_path):
    config = {
        "provider": {"test": {"base_url": "http://fake", "api_key": "k", "models": [{"id": "m1"}]}},
        "agent": {"default_model": "m1", "system_prompt": "Test"},
    }
    engine = AgentEngine(config)
    engine._permissions_service = PermissionsService(
        permissions_path=tmp_path / "permissions.jsonc"
    )
    engine._checkpointer = MagicMock()
    return engine


def test_allowed_tool_produces_no_interrupt(full_engine):
    """When a tool is in the allowlist, the when predicate returns False (no interrupt)."""
    full_engine._permissions_service.allow_tool("web_search")
    mock_request = type("R", (), {"tool_call": {"name": "web_search", "args": {}}})()
    assert full_engine._permissions_service.should_interrupt(mock_request) is False


def test_disallowed_tool_triggers_interrupt(full_engine):
    """When a tool is NOT in the allowlist, the when predicate returns True (interrupt)."""
    mock_request = type("R", (), {"tool_call": {"name": "dangerous_delete", "args": {}}})()
    assert full_engine._permissions_service.should_interrupt(mock_request) is True


def test_dynamic_allow_takes_effect_without_rebuild(full_engine):
    """Adding a tool to allowlist takes effect immediately for existing predicate."""
    mock_request = type("R", (), {"tool_call": {"name": "web_search", "args": {}}})()

    assert full_engine._permissions_service.should_interrupt(mock_request) is True

    full_engine._permissions_service.allow_tool("web_search")

    assert full_engine._permissions_service.should_interrupt(mock_request) is False


def test_remove_revokes_permission(full_engine):
    """Removing a tool from allowlist re-enables interrupt."""
    full_engine._permissions_service.allow_tool("web_search")
    mock_request = type("R", (), {"tool_call": {"name": "web_search", "args": {}}})()
    assert full_engine._permissions_service.should_interrupt(mock_request) is False

    full_engine._permissions_service.remove_tool("web_search")
    assert full_engine._permissions_service.should_interrupt(mock_request) is True


def test_persistence_survives_service_restart(tmp_path):
    """Permissions persist across service restarts."""
    path = tmp_path / "permissions.jsonc"
    svc1 = PermissionsService(permissions_path=path)
    svc1.allow_tool("tool_a")
    svc1.allow_tool("tool_b")

    svc2 = PermissionsService(permissions_path=path)
    mock_a = type("R", (), {"tool_call": {"name": "tool_a", "args": {}}})()
    mock_b = type("R", (), {"tool_call": {"name": "tool_b", "args": {}}})()
    mock_c = type("R", (), {"tool_call": {"name": "tool_c", "args": {}}})()

    assert svc2.should_interrupt(mock_a) is False
    assert svc2.should_interrupt(mock_b) is False
    assert svc2.should_interrupt(mock_c) is True
