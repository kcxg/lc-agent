import asyncio
import mimetypes
from collections import deque
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
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
# 前端用 CodeMirror 虚拟滚动渲染，可按大文件放开行数；仍保留上限防止把巨型生成物拉进浏览器
_FILE_READ_MAX_LINES = 200_000

# 图片后缀：前端按图片渲染，不走文本/二进制分支
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".ico", ".avif"}
# 图片预览体积上限，超过则只提示不传输
_IMAGE_READ_MAX_SIZE = 8 * 1024 * 1024  # 8 MB

# 文件管理操作中被忽略的目录名：新建/重命名时不允许落进这些目录
_FORBIDDEN_ENTRY_NAMES = {"", ".", ".."}


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


def _resolve_project_file_path(path: str, project_root: Path) -> str:
    """Resolve a project-relative (or absolute) file path against the project root."""
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = project_root / candidate
    return _require_path_within_project(str(candidate), project_root)


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
        if agent_id:
            # 项目模式下前端可能传项目相对路径（如文件树），统一按项目根解析
            project_root = await _get_project_preview_root(agent_id, engine, user, db)
            resolved = _resolve_project_file_path(path, project_root)
        else:
            resolved = validate_read_path(path)
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

    # 图片文件：返回 base64 data URL 供前端直接渲染
    if file_path.suffix.lower() in _IMAGE_EXTENSIONS:
        if size > _IMAGE_READ_MAX_SIZE:
            return {
                "file": str(file_path),
                "image": True,
                "image_too_large": True,
                "size": size,
            }
        try:
            import base64

            raw = file_path.read_bytes()
            mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
            encoded = base64.b64encode(raw).decode("ascii")
        except OSError as e:
            return {"error": str(e)}
        return {
            "file": str(file_path),
            "image": True,
            "image_too_large": False,
            "size": size,
            "data_url": f"data:{mime};base64,{encoded}",
        }

    # 二进制嗅探：读前 8KB，出现 NUL 或大量不可打印字节即视为二进制文件
    try:
        with file_path.open("rb") as fh:
            probe = fh.read(8192)
        if b"\x00" in probe:
            return {"file": str(file_path), "binary": True}
        printable = sum(1 for b in probe if b == 9 or b == 10 or b == 13 or 32 <= b < 127 or b >= 128)
        if probe and printable / len(probe) < 0.7:
            return {"file": str(file_path), "binary": True}
    except OSError as e:
        return {"error": str(e)}

    try:
        text = file_path.read_text(encoding="utf-8")
        utf8_lossless = True
    except UnicodeDecodeError:
        # 非 UTF-8：只能用替换字符读出来显示，但必须标记为不可编辑，
        # 否则把 U+FFFD 写回去会永久损坏原文件
        text = file_path.read_text(encoding="utf-8", errors="replace")
        utf8_lossless = False
    except Exception as e:
        return {"error": str(e)}

    # 换行符与 BOM 必须在写回时原样保留，否则整个文件 diff 会全红
    crlf_count = text.count("\r\n")
    has_bom = text.startswith("\ufeff")
    if has_bom:
        text = text[1:]
    lf_only = text.count("\n") - crlf_count
    newline = "crlf" if crlf_count and crlf_count >= lf_only else "lf"

    lines = text.split("\n")
    try:
        mtime = file_path.stat().st_mtime
    except OSError:
        mtime = 0.0

    return {
        "file": str(file_path),
        "lines": lines[:max_lines],
        "total_lines": len(lines),
        "truncated": len(lines) > max_lines,
        "size": size,
        "mtime": mtime,
        "newline": newline,
        "has_bom": has_bom,
        # 以下条件满足才允许前端编辑保存
        "editable": utf8_lossless and len(lines) <= max_lines,
        # 不满足时给出原因，前端直接展示，避免用户困惑为什么不能编辑
        "readonly_reason": (
            "" if (utf8_lossless and len(lines) <= max_lines)
            else ("文件不是 UTF-8 编码，编辑会导致编码损坏" if not utf8_lossless
                  else f"文件超过 {max_lines} 行未全部加载，编辑会丢失后续内容")
        ),
    }


def _git_branch_info(project_root: Path) -> str | None:
    """Return the current git branch, or None when the project is not a git repo."""
    import subprocess

    def _git(args: list[str]) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return ""
        if result.returncode != 0:
            return ""
        return result.stdout.strip()

    if not _git(["rev-parse", "--is-inside-work-tree"]):
        return None
    return _git(["branch", "--show-current"]) or "(detached HEAD)"


async def _resolve_writable_project_path(
    path: str,
    agent_id: str | None,
    engine: AgentEngine,
    user: User,
    db,
    *,
    allow_root: bool = False,
) -> tuple[Path, Path]:
    """把前端传来的项目内路径解析为绝对路径，并做越权与根目录保护校验。

    返回 (project_root, target)：目录不存在、越出项目根、或目标是项目根时抛 PermissionError。
    """
    if not agent_id:
        raise PermissionError("agent_id is required")

    project_root = await _get_project_preview_root(agent_id, engine, user, db)

    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = project_root / candidate
    target = Path(_require_path_within_project(str(candidate), project_root))

    if target == project_root and not allow_root:
        raise PermissionError("Cannot modify the project root directory")
    return project_root, target


def _validate_entry_name(name: str) -> str:
    """校验新建/重命名时用户输入的单段名称，拒绝路径穿越与非法字符。"""
    cleaned = name.strip()
    if cleaned in _FORBIDDEN_ENTRY_NAMES:
        raise PermissionError("名称不能为空")
    if "/" in cleaned or "\\" in cleaned:
        raise PermissionError("名称不能包含路径分隔符")
    if any(ch in cleaned for ch in '<>:"|?*\0'):
        raise PermissionError('名称不能包含 < > : " | ? * 等字符')
    if cleaned in {".", ".."}:
        raise PermissionError("名称不合法")
    return cleaned


@router.post("/tools/project/file/create")
async def create_project_entry(
    path: str,
    name: str,
    entry_type: str = "file",
    agent_id: str | None = None,
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db_session),
):
    """在项目内指定目录下新建文件或文件夹。path 为父目录（相对项目根，空串表示根）。"""
    try:
        _, parent = await _resolve_writable_project_path(path, agent_id, engine, user, db, allow_root=True)
        entry_name = _validate_entry_name(name)
    except PermissionError as e:
        return {"error": str(e)}

    if not parent.is_dir():
        return {"error": f"目录不存在：{path or '.'}"}

    target = parent / entry_name
    if target.exists():
        return {"error": f"已存在同名文件或文件夹：{entry_name}"}

    try:
        if entry_type == "dir":
            target.mkdir(parents=False)
        else:
            target.touch()
    except OSError as e:
        return {"error": str(e)}

    return {"ok": True, "name": entry_name}


@router.post("/tools/project/file/rename")
async def rename_project_entry(
    path: str,
    new_name: str,
    agent_id: str | None = None,
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db_session),
):
    """重命名项目内的文件或文件夹。path 为现有路径（相对项目根）。"""
    try:
        _, target = await _resolve_writable_project_path(path, agent_id, engine, user, db)
        entry_name = _validate_entry_name(new_name)
    except PermissionError as e:
        return {"error": str(e)}

    if not target.exists():
        return {"error": f"文件不存在：{path}"}

    destination = target.parent / entry_name
    if destination == target:
        return {"ok": True, "name": entry_name}
    if destination.exists():
        return {"error": f"已存在同名文件或文件夹：{entry_name}"}

    try:
        target.rename(destination)
    except OSError as e:
        return {"error": str(e)}

    return {"ok": True, "name": entry_name}


@router.post("/tools/project/file/delete")
async def delete_project_entry(
    path: str,
    agent_id: str | None = None,
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db_session),
):
    """删除项目内的文件或目录（目录连同内容一并删除，前端会二次确认）。"""
    import shutil

    try:
        _, target = await _resolve_writable_project_path(path, agent_id, engine, user, db)
    except PermissionError as e:
        return {"error": str(e)}

    if not target.exists():
        return {"error": f"文件不存在：{path}"}

    try:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    except OSError as e:
        return {"error": str(e)}

    return {"ok": True}


class FileSavePayload(BaseModel):
    """保存文件的请求体：正文可能很大，放 body 而不是 URL。"""

    content: str
    mtime: float = 0.0
    newline: str = "lf"
    has_bom: bool = False


@router.post("/tools/project/file/save")
async def save_project_file(
    payload: FileSavePayload,
    path: str,
    agent_id: str | None = None,
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db_session),
):
    """保存项目内文本文件。

    用读取时的 mtime 做乐观锁：文件若已被 Agent 或其他会话改过则拒绝保存，
    避免静默覆盖掉别人的修改。
    """
    from lc_agent.tools.system_tools._config import validate_write_path

    content = payload.content
    mtime = payload.mtime
    newline = payload.newline
    has_bom = payload.has_bom

    try:
        project_root = await _get_project_preview_root(agent_id, engine, user, db)
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = project_root / candidate
        target = Path(_require_path_within_project(str(candidate), project_root))
    except PermissionError as e:
        return {"error": str(e)}

    if not target.is_file():
        return {"error": f"文件不存在：{path}"}

    # 复用系统工具的白名单/扩展名校验，避免绕过 Agent 侧同样的写入约束
    try:
        validate_write_path(str(target))
    except PermissionError as e:
        return {"error": str(e)}

    try:
        current_mtime = target.stat().st_mtime
    except OSError as e:
        return {"error": str(e)}

    # mtime 容差 1ms：文件系统精度差异会造成无意义的冲突
    if mtime and abs(current_mtime - mtime) > 0.001:
        return {
            "error": "文件已被其他会话或 Agent 修改，请重新加载后再编辑",
            "conflict": True,
            "mtime": current_mtime,
        }

    text = content
    if has_bom:
        text = "\ufeff" + text
    if newline == "crlf":
        # 先归一化再统一替换，避免 CRLF 被写成 CRCRLF
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")

    try:
        target.write_text(text, encoding="utf-8")
    except OSError as e:
        return {"error": str(e)}

    try:
        saved_mtime = target.stat().st_mtime
    except OSError:
        saved_mtime = 0.0

    return {"ok": True, "mtime": saved_mtime}


@router.get("/tools/project/tree")
async def list_project_directory(
    path: str = "",
    agent_id: str | None = None,
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db_session),
):
    """List one level of the agent's project directory for the file tree.

    Paths are relative to the project root; an empty path lists the root itself.
    """
    if not agent_id:
        return {"error": "agent_id is required"}

    try:
        project_root = await _get_project_preview_root(agent_id, engine, user, db)
    except PermissionError as e:
        return {"error": str(e)}

    target = (project_root / path).resolve() if path else project_root
    try:
        target.relative_to(project_root)
    except ValueError:
        return {"error": "Path is outside the agent project directory"}

    if not target.is_dir():
        return {"error": f"Directory not found: {path or '.'}"}

    entries = []
    try:
        for child in target.iterdir():
            try:
                is_dir = child.is_dir()
            except OSError:
                continue
            entries.append({
                "name": child.name,
                "path": str(child.relative_to(project_root)).replace("\\", "/"),
                "type": "dir" if is_dir else "file",
            })
    except OSError as e:
        return {"error": str(e)}

    entries.sort(key=lambda e: (e["type"] != "dir", e["name"].lower()))

    return {
        "project_root": str(project_root),
        "git_branch": await asyncio.to_thread(_git_branch_info, project_root),
        "path": str(target.relative_to(project_root)).replace("\\", "/") if target != project_root else "",
        "entries": entries,
    }


_PROJECT_SEARCH_MAX_RESULTS = 100
_PROJECT_SEARCH_MAX_SCANNED = 20000


def _search_project_tree(
    project_root: Path,
    keyword: str,
    limit: int = _PROJECT_SEARCH_MAX_RESULTS,
) -> dict:
    """Breadth-first name search across the whole project directory."""
    keyword = keyword.strip().lower()
    if not keyword:
        return {"results": [], "truncated": False}

    limit = max(1, min(limit, _PROJECT_SEARCH_MAX_RESULTS))

    results: list[dict[str, str]] = []
    truncated = False
    scanned = 0
    queue = deque([project_root])

    while queue and not truncated:
        current = queue.popleft()
        try:
            children = sorted(current.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            continue

        for child in children:
            scanned += 1
            if scanned > _PROJECT_SEARCH_MAX_SCANNED:
                truncated = True
                break
            try:
                is_dir = child.is_dir()
            except OSError:
                continue
            if keyword in child.name.lower():
                if len(results) >= limit:
                    truncated = True
                    break
                results.append({
                    "name": child.name,
                    "path": str(child.relative_to(project_root)).replace("\\", "/"),
                    "type": "dir" if is_dir else "file",
                })
            if is_dir:
                queue.append(child)

    return {"results": results, "truncated": truncated}


@router.get("/tools/project/search")
async def search_project_files(
    q: str = "",
    agent_id: str | None = None,
    limit: int = _PROJECT_SEARCH_MAX_RESULTS,
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db_session),
):
    """Search file and directory names anywhere under the agent's project directory."""
    if not agent_id:
        return {"error": "agent_id is required"}

    try:
        project_root = await _get_project_preview_root(agent_id, engine, user, db)
    except PermissionError as e:
        return {"error": str(e)}

    found = _search_project_tree(project_root, q, limit)
    branch = await asyncio.to_thread(_git_branch_info, project_root)
    return {"project_root": str(project_root), "git_branch": branch, **found}


_PROJECT_GREP_MAX_RESULTS = 200
_PROJECT_GREP_MAX_FILE_SIZE = 2 * 1024 * 1024  # 跳过超过 2MB 的文件
# 内容搜索时跳过的目录：避免进入依赖/构建/缓存等噪音目录
_PROJECT_GREP_SKIP_DIRS = {
    ".git", ".hg", ".svn",
    "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "target",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".idea", ".vscode",
}


def _grep_project_tree(
    project_root: Path,
    keyword: str,
    limit: int = _PROJECT_GREP_MAX_RESULTS,
    case_sensitive: bool = False,
) -> dict:
    """Breadth-first content (grep) search across the whole project directory."""
    needle = keyword if case_sensitive else keyword.strip().lower()
    if not needle:
        return {"matches": [], "truncated": False}

    limit = max(1, min(limit, _PROJECT_GREP_MAX_RESULTS))

    matches: list[dict] = []
    truncated = False
    queue = deque([project_root])

    while queue and not truncated:
        current = queue.popleft()
        try:
            children = sorted(current.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            continue

        for child in children:
            try:
                is_dir = child.is_dir()
            except OSError:
                continue

            if is_dir:
                if child.name in _PROJECT_GREP_SKIP_DIRS:
                    continue
                queue.append(child)
                continue

            try:
                if child.stat().st_size > _PROJECT_GREP_MAX_FILE_SIZE:
                    continue
                with child.open("rb") as fh:
                    probe = fh.read(8192)
                if b"\x00" in probe:
                    continue
            except OSError:
                continue

            try:
                text = child.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            rel_path = str(child.relative_to(project_root)).replace("\\", "/")
            for line_no, line in enumerate(text.split("\n"), start=1):
                haystack = line if case_sensitive else line.lower()
                if needle not in haystack:
                    continue
                if len(matches) >= limit:
                    truncated = True
                    break
                matches.append({
                    "path": rel_path,
                    "name": child.name,
                    "line": line_no,
                    "text": line.strip()[:300],
                })
            if truncated:
                break

    return {"matches": matches, "truncated": truncated}


@router.get("/tools/project/grep")
async def grep_project_files(
    q: str = "",
    agent_id: str | None = None,
    limit: int = _PROJECT_GREP_MAX_RESULTS,
    case_sensitive: bool = False,
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db_session),
):
    """Search file contents anywhere under the agent's project directory."""
    if not agent_id:
        return {"error": "agent_id is required"}

    keyword = q.strip()
    if not keyword:
        return {"matches": [], "truncated": False}

    try:
        project_root = await _get_project_preview_root(agent_id, engine, user, db)
    except PermissionError as e:
        return {"error": str(e)}

    found = await asyncio.to_thread(_grep_project_tree, project_root, keyword, limit, case_sensitive)
    return {"project_root": str(project_root), **found}


@router.get("/tools/processes")
async def list_tracked_processes(
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
