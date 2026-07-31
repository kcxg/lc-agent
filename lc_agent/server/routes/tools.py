from fastapi import APIRouter, Depends

from lc_agent.core.engine import AgentEngine
from lc_agent.db.models_auth import User
from lc_agent.server.auth_middleware import get_current_user
from lc_agent.server.dependencies import get_engine, get_registry
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
    groups: dict[str, list] = {}
    for name, entry in registry._global_tools.items():
        group_name = entry["group"] or "__ungrouped__"
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
