import os
import shutil
from pathlib import Path
from typing import Annotated

from lc_agent.tools.registry import tool
from lc_agent.tools.system_tools._config import validate_write_path
from lc_agent.tools.system_tools._file_change_tracker import emit_file_change

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
    path: Annotated[str, "Path to the file to write"],
    content: Annotated[str, "Text content to write"],
    mode: Annotated[
        str,
        "Write mode: 'rewrite' replaces the entire file (default); 'append' adds content to the end",
    ] = "rewrite",
) -> str:
    """Write content to a file, creating it if it doesn't exist or replacing it entirely — no confirmation is asked.

    Paths resolve relative to the project root (project mode) or server working directory; absolute paths are also accepted. Parent directories are created automatically.
    IMPORTANT: If the file already exists and you intend to rewrite it, call `read_file` first to avoid accidentally discarding content you didn't mean to remove.
    For partial edits to an existing file, prefer `edit_block` instead of a full rewrite.
    """
    try:
        resolved = validate_write_path(path)
    except PermissionError as e:
        return f"Error: {e}"

    file_path = Path(resolved)

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return f"Error creating parent directory: {e}"

    existed_before = file_path.exists()
    original_content: str | None = None
    if existed_before and mode != "append":
        try:
            original_content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading existing file: {e}"

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

    if mode == "append":
        emit_file_change(resolved, "append", new_string=content)
    elif existed_before:
        emit_file_change(
            resolved,
            "edit",
            old_string=original_content,
            new_string=content,
        )
    else:
        emit_file_change(resolved, "create", new_string=content)

    return f"{action} {line_count} lines to {resolved}"


@tool(group="file_write", group_description="文件写入")
def create_directory(
    path: Annotated[str, "Directory path to create (multi-level creation supported)"],
) -> str:
    """Create a directory (and all missing parent directories) at the given path."""
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
    source: Annotated[str, "Source file or directory path"],
    destination: Annotated[str, "Destination path"],
) -> str:
    """Move or rename a file or directory. Destination parent directories are created automatically."""
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

    emit_file_change(resolved_src, "move", move_destination=resolved_dst)

    return f"Moved: {resolved_src} → {resolved_dst}"


@tool(group="file_write", group_description="文件写入")
def delete_file(
    path: Annotated[str, "Path to the file to delete"],
) -> str:
    """Delete a single file. You must be very careful — this is a dangerous operation."""
    try:
        resolved = validate_write_path(path)
    except PermissionError as e:
        return f"Error: {e}"

    file_path = Path(resolved)

    if not file_path.exists():
        return f"Error: File not found: {path}"
    if file_path.is_dir():
        return f"Error: '{path}' is a directory, not a file"

    try:
        file_path.unlink()
    except Exception as e:
        return f"Error deleting file: {e}"

    emit_file_change(resolved, "delete")

    return f"Deleted: {resolved}"


@tool(group="file_write", group_description="文件写入")
def edit_block(
    file_path: Annotated[str, "Path to the file to edit"],
    old_string: Annotated[str, "Exact text to replace; must match the file content character-for-character including whitespace"],
    new_string: Annotated[str, "Replacement text"],
    expected_replacements: Annotated[
        int,
        "Expected number of replacements (default 1). The edit is refused if the actual match count differs, preventing accidental bulk changes.",
    ] = 1,
) -> str:
    """Precisely find and replace a text block in a file.

    IMPORTANT: Call `read_file` on the target file before using this tool. The old_string must match the current file content exactly (character-for-character, including indentation and newlines) — use the text returned by `read_file` as the source.
    Requires old_string to appear exactly expected_replacements times; refuses to edit if the count doesn't match, preventing accidental bulk changes.
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

    emit_file_change(resolved, "edit", old_string=old_string, new_string=new_string)

    return (
        f"Replaced {count} occurrence(s) in {resolved}\n"
        f"  {old_lines} lines → {new_lines} lines"
    )
