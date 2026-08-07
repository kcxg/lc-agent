# tests/test_tools.py
import pytest

import lc_agent.tools.system_tools.file_read_tools as file_read_tools
from lc_agent.tools.registry import ToolRegistry, tool


class TestToolDecorator:
    def setup_method(self):
        """Reset global registry before each test."""
        ToolRegistry._instance = None
        ToolRegistry._global_tools = {}
        ToolRegistry._group_descriptions = {}

    def test_registers_function_as_tool(self):
        @tool
        def greet(name: str) -> str:
            """Say hello."""
            return f"Hello, {name}"

        registry = ToolRegistry()
        tools = registry.get_all_tools()
        assert "greet" in [t.name for t in tools]

    def test_registers_with_group(self):
        @tool(group="utils")
        def get_time() -> str:
            """Get current time."""
            return "12:00"

        registry = ToolRegistry()
        tools = registry.get_all_tools()
        tool_names = [t.name for t in tools]
        assert "utils__get_time" in tool_names

    def test_tool_is_callable(self):
        @tool
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        assert add(2, 3) == 5

    def test_get_tools_by_group(self):
        @tool(group="math")
        def add(a: int, b: int) -> int:
            """Add."""
            return a + b

        @tool(group="math")
        def sub(a: int, b: int) -> int:
            """Subtract."""
            return a - b

        @tool(group="text")
        def upper(s: str) -> str:
            """Uppercase."""
            return s.upper()

        registry = ToolRegistry()
        math_tools = registry.get_tools_by_groups(["math"])
        assert len(math_tools) == 2

    def test_filter_by_allowed_groups_none_returns_all(self):
        @tool(group="a")
        def fa() -> str:
            """A."""
            return "a"

        @tool(group="b")
        def fb() -> str:
            """B."""
            return "b"

        registry = ToolRegistry()
        filtered = registry.get_filtered_tools(allowed_groups=None)
        assert len(filtered) == 2

    def test_filter_by_allowed_groups_empty_returns_none(self):
        @tool(group="a")
        def fc() -> str:
            """A."""
            return "a"

        registry = ToolRegistry()
        filtered = registry.get_filtered_tools(allowed_groups=[])
        assert len(filtered) == 0

    def test_get_group_names(self):
        @tool(group="alpha")
        def fx() -> str:
            """X."""
            return "x"

        @tool(group="beta")
        def fy() -> str:
            """Y."""
            return "y"

        registry = ToolRegistry()
        groups = registry.get_group_names()
        assert "alpha" in groups
        assert "beta" in groups


class TestListDirectory:
    def test_depth_one_lists_only_direct_children(self, tmp_path, monkeypatch):
        (tmp_path / "root.txt").write_text("root")
        child = tmp_path / "child"
        child.mkdir()
        (child / "nested.txt").write_text("nested")
        monkeypatch.setattr(file_read_tools, "validate_read_path", lambda _: str(tmp_path))

        result = file_read_tools.list_directory("ignored", depth=1)

        assert "[FILE] root.txt" in result
        assert "[DIR] child/" in result
        assert "nested.txt" not in result

    def test_depth_two_lists_nested_children(self, tmp_path, monkeypatch):
        child = tmp_path / "child"
        child.mkdir()
        (child / "nested.txt").write_text("nested")
        monkeypatch.setattr(file_read_tools, "validate_read_path", lambda _: str(tmp_path))

        result = file_read_tools.list_directory("ignored", depth=2)

        assert "  [FILE] nested.txt" in result

    def test_rejects_depth_below_one(self, tmp_path, monkeypatch):
        monkeypatch.setattr(file_read_tools, "validate_read_path", lambda _: str(tmp_path))

        assert file_read_tools.list_directory("ignored", depth=0) == "Error: depth must be at least 1"

    def test_truncation_uses_global_limit_and_guidance(self, tmp_path, monkeypatch):
        for index in range(3):
            (tmp_path / f"file-{index}.txt").write_text("")
        monkeypatch.setattr(file_read_tools, "validate_read_path", lambda _: str(tmp_path))
        monkeypatch.setattr(file_read_tools, "_MAX_DIRECTORY_ITEMS", 2)

        result = file_read_tools.list_directory("ignored", depth=1)

        assert result.count("[FILE]") == 2
        assert "showing the first 2 entries" in result
        assert "Reduce depth" in result
        assert "individual subdirectories" in result
