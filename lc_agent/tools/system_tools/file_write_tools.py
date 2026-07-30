import os
import shutil
from pathlib import Path
from typing import Annotated

from lc_agent.tools.registry import tool
from lc_agent.tools.system_tools._config import validate_write_path

_CONTEXT_LINES = 5
_WRITE_PREVIEW_LINES = 20


def _emit_edit_diff(
    original: str, new_content: str, old_string: str, new_string: str, file_path: str,
    expected_replacements: int = 1,
) -> None:
    """Dispatch diff data to frontend via custom event."""
    if expected_replacements != 1:
        return

    try:
        from langchain_core.callbacks import dispatch_custom_event
    except Exception:
        return

    lines = original.split("\n")
    pos = original.find(old_string)
    if pos < 0:
        return
    start_line = original[:pos].count("\n")

    old_lines = old_string.split("\n") if old_string else []
    new_lines = new_string.split("\n") if new_string else []

    ctx_start = max(0, start_line - _CONTEXT_LINES)
    context_before = lines[ctx_start:start_line]

    new_file_lines = new_content.split("\n")
    new_after_start = start_line + len(new_lines)
    context_after = new_file_lines[new_after_start:new_after_start + _CONTEXT_LINES]

    try:
        dispatch_custom_event("file_edit_diff", {
            "file": file_path,
            "start_line": ctx_start + 1,
            "context_before": context_before,
            "removed": old_lines,
            "added": new_lines,
            "context_after": context_after,
        })
    except Exception:
        pass


def _emit_write_preview(file_path: str, content: str, mode: str) -> None:
    """Dispatch write preview data to frontend via custom event."""
    try:
        from langchain_core.callbacks import dispatch_custom_event
    except Exception:
        return

    lines = content.split("\n") if content else []
    total = len(lines)
    preview = lines[:_WRITE_PREVIEW_LINES]

    start_line = 1
    if mode == "append":
        try:
            existing = Path(file_path).read_text(encoding="utf-8")
            start_line = existing.count("\n") + 1 - total
            if start_line < 1:
                start_line = 1
        except Exception:
            pass

    try:
        dispatch_custom_event("file_write_preview", {
            "file": file_path,
            "mode": mode,
            "preview_lines": preview,
            "total_lines": total,
            "start_line": start_line,
        })
    except Exception:
        pass


@tool(group="file_write", group_description="文件写入")
def write_file(
    path: Annotated[str, "要写入的文件路径"],
    content: Annotated[str, "要写入的文本内容"],
    mode: Annotated[
        str,
        "写入模式：'rewrite' 覆盖全部内容（默认）；'append' 追加到文件末尾",
    ] = "rewrite",
) -> str:
    """写入文件内容。支持覆盖写入和追加模式，自动创建父目录。"""
    try:
        resolved = validate_write_path(path)
    except PermissionError as e:
        return f"Error: {e}"

    file_path = Path(resolved)

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return f"Error creating parent directory: {e}"

    try:
        if mode == "append":
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(content)
            action = "Appended"
        else:
            file_path.write_text(content, encoding="utf-8")
            action = "Written"
    except Exception as e:
        return f"Error writing file: {e}"

    line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

    _emit_write_preview(resolved, content, mode)

    return f"{action} {line_count} lines to {resolved}"


@tool(group="file_write", group_description="文件写入")
def create_directory(
    path: Annotated[str, "要创建的目录路径（支持多级创建）"],
) -> str:
    """创建目录。自动创建所有不存在的父级目录。"""
    try:
        resolved = validate_write_path(path)
    except PermissionError as e:
        return f"Error: {e}"

    dir_path = Path(resolved)

    if dir_path.exists():
        if dir_path.is_dir():
            return f"Directory already exists: {resolved}"
        return f"Error: A file with that name already exists: {resolved}"

    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return f"Error creating directory: {e}"

    return f"Created directory: {resolved}"


@tool(group="file_write", group_description="文件写入")
def move_file(
    source: Annotated[str, "源文件或目录的路径"],
    destination: Annotated[str, "目标路径"],
) -> str:
    """移动或重命名文件/目录。"""
    try:
        resolved_src = validate_write_path(source)
        resolved_dst = validate_write_path(destination)
    except PermissionError as e:
        return f"Error: {e}"

    src_path = Path(resolved_src)
    dst_path = Path(resolved_dst)

    if not src_path.exists():
        return f"Error: Source not found: {source}"

    try:
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
    except Exception as e:
        return f"Error moving file: {e}"

    return f"Moved: {resolved_src} → {resolved_dst}"


@tool(group="file_write", group_description="文件写入")
def edit_block(
    file_path: Annotated[str, "要编辑的文件路径"],
    old_string: Annotated[str, "要被替换的原始文本（必须精确匹配文件中的内容）"],
    new_string: Annotated[str, "替换后的新文本"],
    expected_replacements: Annotated[
        int,
        "期望替换的次数（默认 1）。用于校验精确性——如果实际匹配数不等于此值则拒绝替换。",
    ] = 1,
) -> str:
    """精确查找并替换文件中的文本片段。

    要求 old_string 在文件中的出现次数恰好等于 expected_replacements，
    否则拒绝操作以防止误修改。
    """
    try:
        resolved = validate_write_path(file_path)
    except PermissionError as e:
        return f"Error: {e}"

    path = Path(resolved)
    if not path.exists():
        return f"Error: File not found: {file_path}"
    if path.is_dir():
        return f"Error: '{file_path}' is a directory"

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"

    count = content.count(old_string)
    if count == 0:
        snippet = old_string[:80]
        return (
            f"Error: old_string not found in file.\n"
            f"Searched for: \"{snippet}{'...' if len(old_string) > 80 else ''}\"\n"
            f"Make sure the text matches exactly (including whitespace and newlines)."
        )

    if count != expected_replacements:
        return (
            f"Error: Expected {expected_replacements} occurrence(s) of old_string, "
            f"but found {count}. Refusing to replace to avoid unintended modifications.\n"
            f"Set expected_replacements={count} if you intend to replace all occurrences."
        )

    new_content = content.replace(old_string, new_string, expected_replacements)

    try:
        path.write_text(new_content, encoding="utf-8")
    except Exception as e:
        return f"Error writing file: {e}"

    old_lines = old_string.count("\n") + 1
    new_lines = new_string.count("\n") + 1

    _emit_edit_diff(content, new_content, old_string, new_string, resolved, expected_replacements)

    return (
        f"Replaced {count} occurrence(s) in {resolved}\n"
        f"  {old_lines} lines → {new_lines} lines"
    )
