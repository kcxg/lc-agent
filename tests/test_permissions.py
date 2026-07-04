import json
import pytest
from pathlib import Path

from lc_agent.core.permissions import PermissionsService


@pytest.fixture
def tmp_permissions(tmp_path):
    """Return a PermissionsService backed by a temp file."""
    return PermissionsService(permissions_path=tmp_path / "permissions.jsonc")


def test_empty_state_nothing_allowed(tmp_permissions):
    assert tmp_permissions.is_allowed("web_search") is False
    assert tmp_permissions.get_allowlist() == []


def test_allow_tool_persists(tmp_permissions):
    tmp_permissions.allow_tool("web_search")
    assert tmp_permissions.is_allowed("web_search") is True
    assert "web_search" in tmp_permissions.get_allowlist()


def test_remove_tool(tmp_permissions):
    tmp_permissions.allow_tool("web_search")
    tmp_permissions.remove_tool("web_search")
    assert tmp_permissions.is_allowed("web_search") is False


def test_set_allowlist_replaces(tmp_permissions):
    tmp_permissions.allow_tool("a")
    tmp_permissions.set_allowlist(["b", "c"])
    assert tmp_permissions.is_allowed("a") is False
    assert tmp_permissions.is_allowed("b") is True
    assert tmp_permissions.is_allowed("c") is True


def test_file_persistence(tmp_path):
    path = tmp_path / "permissions.jsonc"
    svc1 = PermissionsService(permissions_path=path)
    svc1.allow_tool("web_search")
    svc1.allow_tool("filesystem__read_file")

    svc2 = PermissionsService(permissions_path=path)
    assert svc2.is_allowed("web_search") is True
    assert svc2.is_allowed("filesystem__read_file") is True


def test_corrupted_file_falls_back_to_empty(tmp_path):
    path = tmp_path / "permissions.jsonc"
    path.write_text("not valid json {{{", encoding="utf-8")
    svc = PermissionsService(permissions_path=path)
    assert svc.get_allowlist() == []


def test_duplicate_add_is_idempotent(tmp_permissions):
    tmp_permissions.allow_tool("web_search")
    tmp_permissions.allow_tool("web_search")
    assert tmp_permissions.get_allowlist().count("web_search") == 1


def test_should_interrupt_returns_true_when_not_allowed(tmp_permissions):
    mock_request = type("R", (), {"tool_call": {"name": "dangerous_tool", "args": {}}})()
    assert tmp_permissions.should_interrupt(mock_request) is True


def test_should_interrupt_returns_false_when_allowed(tmp_permissions):
    tmp_permissions.allow_tool("safe_tool")
    mock_request = type("R", (), {"tool_call": {"name": "safe_tool", "args": {}}})()
    assert tmp_permissions.should_interrupt(mock_request) is False
