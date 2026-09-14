import asyncio
import json

import pytest

from lc_agent.mcp.tool_adapter import create_langchain_tools_from_schemas


def test_create_langchain_tools_basic():
    """Should create StructuredTool from MCP schema."""
    schemas = [
        {
            "name": "read_file",
            "description": "Read a file from disk",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"],
            },
        }
    ]

    tools = create_langchain_tools_from_schemas("filesystem", schemas)
    assert len(tools) == 1
    assert tools[0].name == "mcp__filesystem__read_file"
    assert "Read a file" in tools[0].description


def test_create_langchain_tools_empty():
    """Empty schemas should return empty list."""
    tools = create_langchain_tools_from_schemas("test", [])
    assert tools == []


def test_tool_has_correct_group():
    """Tool name should follow mcp__{server}__{tool} convention."""
    schemas = [{"name": "list_repos", "description": "List repos", "input_schema": {"type": "object", "properties": {}}}]
    tools = create_langchain_tools_from_schemas("github", schemas)
    assert tools[0].name == "mcp__github__list_repos"


def test_no_arg_tool_declares_no_parameters():
    """无参数的工具不该凭空多出一个参数。

    历史上这里塞过一个 placeholder 假参数，它会跟着 schema 一起发给模型，
    模型于是照着编值（"{}"、"no params" 之类），最后显示成一条假的入参。
    """
    schemas = [{"name": "nbrag_stats", "description": "Stats", "input_schema": {"type": "object", "properties": {}}}]
    tool = create_langchain_tools_from_schemas("nbrag", schemas)[0]

    assert tool.args == {}
    assert "properties" in json.dumps(tool.tool_call_schema.model_json_schema())
    assert "placeholder" not in json.dumps(tool.tool_call_schema.model_json_schema())


def test_tool_without_properties_key_declares_no_parameters():
    """schema 里连 properties 都不给，同样不该塞占位参数。"""
    schemas = [{"name": "nbrag_help", "description": "Help", "input_schema": {"type": "object"}}]
    tool = create_langchain_tools_from_schemas("nbrag", schemas)[0]
    assert tool.args == {}


def test_declared_parameters_are_kept():
    """有参数的工具不能受影响：该有的参数一个不少。"""
    schemas = [
        {
            "name": "read_file",
            "description": "Read a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "offset": {"type": "integer", "description": "Start line"},
                },
                "required": ["path"],
            },
        }
    ]
    tool = create_langchain_tools_from_schemas("filesystem", schemas)[0]
    assert set(tool.args) == {"path", "offset"}


def test_no_arg_tool_is_callable_without_arguments():
    """无参数工具要能直接调用，并且不会把多余字段透传给 MCP 服务。"""
    seen = {}

    async def invoke(tool_name, args):
        seen["tool_name"] = tool_name
        seen["args"] = args
        return "ok"

    schemas = [{"name": "nbrag_stats", "description": "Stats", "input_schema": {"type": "object", "properties": {}}}]
    tool = create_langchain_tools_from_schemas("nbrag", schemas, invoke_fn=invoke)[0]

    assert asyncio.run(tool.ainvoke({})) == "ok"
    assert seen == {"tool_name": "nbrag_stats", "args": {}}
