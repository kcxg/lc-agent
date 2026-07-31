import base64
import mimetypes
import os
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from lc_agent.tools.registry import tool
from lc_agent.tools.system_tools._config import validate_read_path

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}
_DEFAULT_LINE_LIMIT = 1000
_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
_MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB


@tool(group="file_read", group_description="文件读取")
def read_file(
    path: Annotated[str, "要读取的文件路径（绝对路径或相对于工作目录的相对路径）"],
    offset: Annotated[
        int,
        "起始行号。0 表示从头开始；正数为从第 N 行开始（0-indexed）；"
        "负数表示 tail 模式，读取最后 |offset| 行。",
    ] = 0,
    length: Annotated[
        int,
        "读取的最大行数（默认 1000）。设 -1 表示读取全部。",
    ] = _DEFAULT_LINE_LIMIT,
) -> str:
    """读取文件内容。支持文本文件分页读取和图片文件 base64 返回。"""
    resolved = validate_read_path(path)
    file_path = Path(resolved)

    if not file_path.exists():
        return f"Error: File not found: {path}"
    if file_path.is_dir():
        return f"Error: '{path}' is a directory, use list_directory instead"

    file_size = file_path.stat().st_size
    if file_path.suffix.lower() in _IMAGE_EXTENSIONS:
        if file_size > _MAX_IMAGE_SIZE:
            return f"Error: Image too large ({file_size / 1024 / 1024:.1f} MB). Max {_MAX_IMAGE_SIZE // 1024 // 1024} MB."
        return _read_image(file_path)

    if file_size > _MAX_FILE_SIZE:
        return (
            f"Error: File too large ({file_size / 1024 / 1024:.1f} MB, max {_MAX_FILE_SIZE // 1024 // 1024} MB). "
            f"Use offset/length parameters to read specific sections, or use search_files to find relevant content."
        )

    return _read_text(file_path, offset, length)


def _read_image(file_path: Path) -> str:
    try:
        data = file_path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        mime = mimetypes.guess_type(str(file_path))[0] or "image/png"
        size_kb = len(data) / 1024
        return (
            f"[Image: {file_path.name}, {size_kb:.1f} KB, type={mime}]\n"
            f"data:{mime};base64,{b64}"
        )
    except Exception as e:
        return f"Error reading image: {e}"


def _read_text(file_path: Path, offset: int, length: int) -> str:
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error reading file: {e}"

    lines = text.splitlines(keepends=True)
    total = len(lines)

    if offset < 0:
        start = max(0, total + offset)
        selected = lines[start:]
    else:
        start = offset
        selected = lines[start:]

    if length >= 0:
        selected = selected[:length]

    content = "".join(selected)
    end_line = start + len(selected)
    header = f"[Lines {start + 1}-{end_line} of {total} total]"

    if end_line < total:
        header += f" (use offset={end_line} to read more)"

    return f"{header}\n{content}"


@tool(group="file_read", group_description="文件读取")
def read_multiple_files(
    paths: Annotated[list[str], "要读取的文件路径列表"],
) -> str:
    """批量读取多个文件。单个文件失败不影响整体。"""
    results: list[str] = []
    for p in paths:
        try:
            resolved = validate_read_path(p)
            file_path = Path(resolved)
            if not file_path.exists():
                results.append(f"--- {p} ---\nError: File not found")
                continue
            if file_path.is_dir():
                results.append(f"--- {p} ---\nError: Is a directory")
                continue
            text = file_path.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines(keepends=True)
            if len(lines) > _DEFAULT_LINE_LIMIT:
                content = "".join(lines[:_DEFAULT_LINE_LIMIT])
                content += f"\n... [{len(lines) - _DEFAULT_LINE_LIMIT} more lines truncated]"
            else:
                content = text
            results.append(f"--- {p} ---\n{content}")
        except PermissionError as e:
            results.append(f"--- {p} ---\nError: {e}")
        except Exception as e:
            results.append(f"--- {p} ---\nError: {e}")
    return "\n\n".join(results)


@tool(group="file_read", group_description="文件读取")
def list_directory(
    path: Annotated[str, "目录路径"],
    depth: Annotated[int, "递归深度（默认 2，0 表示只列当前层）"] = 2,
) -> str:
    """列出目录内容，递归显示子目录结构。"""
    resolved = validate_read_path(path)
    dir_path = Path(resolved)

    if not dir_path.exists():
        return f"Error: Directory not found: {path}"
    if not dir_path.is_dir():
        return f"Error: '{path}' is not a directory"

    lines: list[str] = []
    _walk_dir(dir_path, lines, depth, current_depth=0, max_items=200)
    return "\n".join(lines)


_ALWAYS_IGNORE = frozenset({".git"})


def _walk_dir(
    dir_path: Path, lines: list[str], max_depth: int, current_depth: int, max_items: int
) -> None:
    indent = "  " * current_depth
    try:
        entries = sorted(dir_path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        lines.append(f"{indent}[Permission denied]")
        return

    for entry in entries:
        if len(lines) >= max_items:
            lines.append(f"{indent}... [truncated, {max_items} items limit reached]")
            return

        if entry.name in _ALWAYS_IGNORE:
            continue

        if entry.is_dir():
            lines.append(f"{indent}[DIR] {entry.name}/")
            if current_depth < max_depth:
                _walk_dir(entry, lines, max_depth, current_depth + 1, max_items)
        else:
            size = entry.stat().st_size
            lines.append(f"{indent}[FILE] {entry.name} ({_format_size(size)})")


def _format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


@tool(group="file_read", group_description="文件读取")
def get_file_info(
    path: Annotated[str, "文件或目录路径"],
) -> str:
    """获取文件或目录的详细元信息。"""
    resolved = validate_read_path(path)
    file_path = Path(resolved)

    if not file_path.exists():
        return f"Error: Path not found: {path}"

    stat = file_path.stat()
    info_lines = [
        f"path: {resolved}",
        f"type: {'directory' if file_path.is_dir() else 'file'}",
        f"size: {_format_size(stat.st_size)}",
        f"created: {datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat()}",
        f"modified: {datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()}",
    ]

    if file_path.is_file():
        if stat.st_size > _MAX_FILE_SIZE:
            info_lines.append(f"line_count: [file too large to count, {stat.st_size / 1024 / 1024:.1f} MB]")
        else:
            try:
                text = file_path.read_text(encoding="utf-8", errors="replace")
                line_count = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
                info_lines.append(f"line_count: {line_count}")
            except Exception:
                info_lines.append("line_count: [unable to count - binary?]")

    return "\n".join(info_lines)


@tool(group="file_read", group_description="文件读取")
def search_files(
    path: Annotated[str, "搜索的根目录路径"],
    pattern: Annotated[str, "搜索模式。content 模式为正则/文本；files 模式为 glob 模式（如 *.py）"],
    search_type: Annotated[
        str,
        "搜索类型：'content' 在文件内容中搜索文本；'files' 按文件名模式搜索文件",
    ] = "content",
    max_results: Annotated[int, "最大返回结果数"] = 50,
    ignore_case: Annotated[bool, "是否忽略大小写"] = True,
    file_pattern: Annotated[
        str | None,
        "文件名过滤 glob（仅 content 模式有效），如 '*.py' 只搜索 Python 文件",
    ] = None,
    context_lines: Annotated[int, "上下文行数（仅 content 模式有效）"] = 2,
) -> str:
    """搜索文件名或文件内容。内部调用 ripgrep 实现高性能搜索。"""
    resolved = validate_read_path(path)

    rg_path = shutil.which("rg")
    if not rg_path:
        return "Error: ripgrep (rg) not found on PATH. Please install ripgrep."

    if search_type == "files":
        return _search_files_by_name(rg_path, resolved, pattern, max_results, ignore_case)
    else:
        return _search_files_by_content(
            rg_path, resolved, pattern, max_results, ignore_case, file_pattern, context_lines
        )


def _search_files_by_name(
    rg_path: str, root: str, pattern: str, max_results: int, ignore_case: bool
) -> str:
    cmd = [rg_path, "--files"]
    glob_flag = "--iglob" if ignore_case else "--glob"
    cmd.extend([glob_flag, pattern])
    cmd.append(root)

    return _run_rg(cmd, max_results)


def _search_files_by_content(
    rg_path: str,
    root: str,
    pattern: str,
    max_results: int,
    ignore_case: bool,
    file_pattern: str | None,
    context_lines: int,
) -> str:
    cmd = [rg_path, "--line-number", "--no-heading"]
    if ignore_case:
        cmd.append("--ignore-case")
    if context_lines > 0:
        cmd.extend(["-C", str(context_lines)])
    if max_results > 0:
        cmd.extend(["-m", str(max_results)])
    if file_pattern:
        cmd.extend(["--glob", file_pattern])
    cmd.extend(["--", pattern, root])

    return _run_rg(cmd, max_results)


def _run_rg(cmd: list[str], max_results: int) -> str:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return "Error: Search timed out after 30 seconds. Try a more specific pattern or directory."
    except Exception as e:
        return f"Error running search: {e}"

    if result.returncode == 1:
        return "No matches found."
    if result.returncode not in (0, 1):
        return f"Search error (exit code {result.returncode}): {result.stderr.strip()}"

    output = result.stdout
    lines = output.splitlines()
    if len(lines) > max_results * 5:
        output = "\n".join(lines[:max_results * 5])
        output += f"\n\n... [output truncated, showing first {max_results * 5} lines]"

    return output
