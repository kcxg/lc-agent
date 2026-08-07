from pathlib import Path

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select

from lc_agent.core.engine import AgentEngine
from lc_agent.db.models_auth import User, UserAgentAccess
from lc_agent.server.auth_middleware import get_current_user
from lc_agent.server.dependencies import get_db_session, get_engine, get_registry
from lc_agent.tools.registry import ToolRegistry

router = APIRouter(tags=["tools"])


@router.get("/tools")
def list_tools(
    user: User = Depends(get_current_user),
    registry: ToolRegistry = Depends(get_registry),
):
    """List all registered tools."""
    tools = []
    for name, entry in registry._global_tools.items():
        group = entry["group"]
        tools.append({
            "name": name,
            "group": group,
            "group_description": registry._group_descriptions.get(group, group),
            "description": entry["tool"].description,
        })
    return tools


@router.get("/tools/groups")
def list_tool_groups(
    user: User = Depends(get_current_user),
    registry: ToolRegistry = Depends(get_registry),
):
    """List tool groups with their tools."""
    from lc_agent.tools.registry import _BUILTIN_GROUP
    groups: dict[str, list] = {}
    for name, entry in registry._global_tools.items():
        group_name = entry["group"] or "__ungrouped__"
        if group_name == _BUILTIN_GROUP:
            continue  # always-on builtin tools are not user-selectable
        if group_name not in groups:
            groups[group_name] = []
        tool_obj = entry["tool"]
        schema = None
        if hasattr(tool_obj, "args_schema") and tool_obj.args_schema:
            try:
                schema = tool_obj.args_schema.model_json_schema()
            except Exception:
                pass
        groups[group_name].append({
            "name": name,
            "description": tool_obj.description,
            "input_schema": schema,
        })
    disabled = registry._disabled_groups
    return [
        {
            "id": group,
            "description": registry._group_descriptions.get(group, group),
            "tools": tools,
            "enabled": group not in disabled,
        }
        for group, tools in sorted(groups.items())
    ]


@router.post("/tools/groups/{group_id}/toggle")
def toggle_tool_group(
    group_id: str,
    user: User = Depends(get_current_user),
    registry: ToolRegistry = Depends(get_registry),
    engine: AgentEngine = Depends(get_engine),
):
    """Toggle a tool group's enabled state."""
    if group_id in registry._disabled_groups:
        registry._disabled_groups.discard(group_id)
        enabled = True
    else:
        registry._disabled_groups.add(group_id)
        enabled = False
    engine._mcp_generation += 1
    return {"id": group_id, "enabled": enabled}


@router.post("/tools/process/{pid}/kill")
def kill_background_process(
    pid: int,
    user: User = Depends(get_current_user),
):
    """Kill a background process started by start_background_process tool."""
    import os
    import platform
    import subprocess
    from lc_agent.tools.system_tools.command_tools import _processes

    entry = _processes.get(pid)
    if entry is None:
        return {"success": False, "error": f"Process {pid} is not tracked"}

    if entry.proc.poll() is not None:
        _processes.pop(pid, None)
        return {"success": True, "message": f"Process {pid} already exited (code={entry.proc.returncode})"}

    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["taskkill", "/PID", str(pid), "/F", "/T"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip() or "taskkill failed"}
        else:
            import signal
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    except PermissionError:
        return {"success": False, "error": "Permission denied"}
    except Exception as e:
        return {"success": False, "error": str(e)}

    entry.append_stdout("\n[Process terminated by user]\n")

    try:
        entry.proc.wait(timeout=5)
    except Exception:
        pass
    _processes.pop(pid, None)
    return {"success": True, "message": f"Process {pid} terminated"}


@router.get("/tools/process/{pid}/output")
def get_process_output(
    pid: int,
    offset: int = 0,
    user: User = Depends(get_current_user),
):
    """Get incremental output from a background process.

    Returns new output lines since `offset`, plus current process status.
    Frontend can poll this endpoint to keep the tool card updated.
    """
    from lc_agent.tools.system_tools.command_tools import _processes

    entry = _processes.get(pid)
    if entry is None:
        return {"pid": pid, "status": "not_found", "output": "", "offset": offset}

    is_running = entry.proc.poll() is None
    text, new_offset = entry.get_output(offset)

    status = "running" if is_running else f"exited:{entry.proc.returncode}"

    return {
        "pid": pid,
        "status": status,
        "output": text,
        "offset": new_offset,
    }


_FILE_READ_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
_FILE_READ_MAX_LINES = 2000


async def _get_project_preview_root(
    agent_id: str,
    engine: AgentEngine,
    user: User,
    db,
) -> Path:
    if not engine._preset_exists(agent_id):
        raise PermissionError("Agent not found")

    if user.role != "admin":
        access_stmt = select(UserAgentAccess.agent_id).where(
            UserAgentAccess.user_id == user.id,
            UserAgentAccess.agent_id == agent_id,
        )
        access = await db.execute(access_stmt)
        if access.scalar_one_or_none() is None:
            raise PermissionError("Access denied for this agent")

    preset = engine._resolve_preset(agent_id)
    if not preset.project_mode or not preset.project_root:
        raise PermissionError("This agent has no project directory configured")

    project_root = Path(preset.project_root).expanduser().resolve()
    if not project_root.is_dir():
        raise PermissionError("The agent project directory is unavailable")
    return project_root


def _require_path_within_project(path: str, project_root: Path) -> str:
    resolved = Path(path).resolve()
    try:
        resolved.relative_to(project_root)
    except ValueError as e:
        raise PermissionError("File is outside the agent project directory") from e
    return str(resolved)


@router.get("/tools/file/read")
async def read_file_content(
    path: str,
    max_lines: int = 500,
    agent_id: str | None = None,
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db_session),
):
    """Read a file's content for frontend preview. Returns up to max_lines lines."""
    from lc_agent.tools.system_tools._config import validate_read_path

    try:
        resolved = validate_read_path(path)
        if agent_id:
            project_root = await _get_project_preview_root(agent_id, engine, user, db)
            resolved = _require_path_within_project(resolved, project_root)
    except PermissionError as e:
        return {"error": str(e)}

    file_path = Path(resolved)
    if not file_path.exists():
        return {"error": f"File not found: {path}"}
    if not file_path.is_file():
        return {"error": f"Not a file: {path}"}

    try:
        size = file_path.stat().st_size
    except OSError:
        return {"error": "Cannot stat file"}
    if size > _FILE_READ_MAX_SIZE:
        return {"error": f"File too large ({size} bytes, max {_FILE_READ_MAX_SIZE})"}

    max_lines = min(max_lines, _FILE_READ_MAX_LINES)

    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"error": str(e)}

    lines = text.split("\n")
    return {
        "file": str(file_path),
        "lines": lines[:max_lines],
        "total_lines": len(lines),
        "truncated": len(lines) > max_lines,
    }


@router.get("/tools/processes")
def list_tracked_processes(
    user: User = Depends(get_current_user),
):
    """List all background processes started by start_background_process."""
    import time as _time
    from lc_agent.tools.system_tools.command_tools import _processes, _reap_exited_processes

    _reap_exited_processes()

    items = []
    for pid, entry in _processes.items():
        is_running = entry.proc.poll() is None
        items.append({
            "pid": pid,
            "command": entry.command,
            "status": "running" if is_running else f"exited:{entry.proc.returncode}",
            "elapsed_s": round(_time.time() - entry.start_time),
        })
    return {"processes": items}
