import difflib
import os
import shutil
import threading
from pathlib import Path
from typing import Annotated

from lc_agent.tools.registry import tool
from lc_agent.tools.system_tools._config import get_file_write_config, validate_write_path
from lc_agent.tools.system_tools._file_change_tracker import emit_file_change

_CONTEXT_LINES = 5
_WRITE_PREVIEW_LINES = 20

# Real file text echoed around the edited area / around the closest fuzzy match.
_EDIT_PREVIEW_LINES = 10
# Blocks larger than this still run, but the result suggests splitting them.
_EDIT_MAX_LINES_DEFAULT = 50
# Similarity (0-1) at or above which the closest real text is handed back for an exact retry.
_FUZZY_THRESHOLD = 0.7

_BOM_UTF8 = b"\xef\xbb\xbf"

# Characters that look alike on screen but differ in bytes.
_CHAR_NAMES = {
    "\t": "TAB",
    " ": "SPACE",
    "\r": "CR",
    "\n": "LF",
    "\u00a0": "NO-BREAK SPACE",
    "\u3000": "IDEOGRAPHIC SPACE",
    "\u200b": "ZERO-WIDTH SPACE",
    "\ufeff": "BOM",
}

# Serializes edit_block executions process-wide. edit_block performs a
# read-modify-write: two concurrent calls on the same file both read the
# original content, and the later write silently drops the earlier change.
_EDIT_BLOCK_LOCK = threading.Lock()


def _edit_max_lines() -> int:
    """Configured guideline for how many lines one edit block may span."""
    try:
        return int(get_file_write_config().get("edit_max_lines", _EDIT_MAX_LINES_DEFAULT))
    except Exception:
        return _EDIT_MAX_LINES_DEFAULT


def _detect_newline(raw: bytes) -> str:
    """Predominant line ending of the raw file bytes (platform default when empty)."""
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    cr = raw.count(b"\r") - crlf
    if crlf > lf and crlf > cr:
        return "\r\n"
    if lf > cr:
        return "\n"
    if cr > 0:
        return "\r"
    return "\r\n" if os.name == "nt" else "\n"


def _read_text_preserving(path: Path) -> tuple[str, str, bool]:
    """Read a file as LF-normalized text, remembering its line ending and BOM.

    Matching happens on LF-normalized text so callers can use plain "\\n" anchors
    regardless of how the file stores its line breaks; the original convention is
    restored on write.
    """
    raw = path.read_bytes()
    has_bom = raw.startswith(_BOM_UTF8)
    text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    return text, _detect_newline(raw), has_bom


def _write_text_preserving(path: Path, text_lf: str, newline: str, has_bom: bool) -> None:
    """Write LF-normalized text back with the file's own line ending and BOM."""
    data = (_BOM_UTF8 if has_bom else b"") + text_lf.replace("\n", newline).encode("utf-8")
    path.write_bytes(data)


def _char_label(char: str) -> str:
    name = _CHAR_NAMES.get(char)
    return f"U+{ord(char):04X} ({name})" if name else f"U+{ord(char):04X}"


def _first_difference(expected: str, actual: str) -> str:
    """Describe the first differing character with line, column and code point."""
    limit = min(len(expected), len(actual))
    index = next((i for i in range(limit) if expected[i] != actual[i]), limit)
    if index == limit and len(expected) == len(actual):
        return "no character-level difference found"
    line = expected.count("\n", 0, index) + 1
    column = index - expected.rfind("\n", 0, index)
    left = _char_label(expected[index]) if index < len(expected) else "the end of old_string"
    right = _char_label(actual[index]) if index < len(actual) else "the end of the found text"
    return f"first difference at line {line}, column {column}: old_string has {left}, the file has {right}"


def _closest_match(text_lf: str, old_string: str, anchors: int = 5) -> tuple[float, str, int]:
    """Find the file text most similar to old_string.

    Two stages so large files stay fast: probe every line with a cheap ratio to pick
    anchor positions, then score a block-sized window around each anchor.
    Returns (similarity 0-1, closest text, 1-based start line); similarity is -1 when
    the file is empty.
    """
    text_lines = text_lf.split("\n")
    old_lines = old_string.split("\n")
    span = max(1, len(old_lines))
    probe = next((line for line in old_lines if line.strip()), old_lines[0])
    ranked = sorted(
        (
            (difflib.SequenceMatcher(None, probe, line, autojunk=False).quick_ratio(), index)
            for index, line in enumerate(text_lines)
        ),
        key=lambda item: item[0],
        reverse=True,
    )[:anchors]

    best_ratio, best_text, best_start = -1.0, "", 1
    for _, anchor in ranked:
        for shift in (0, 1, 2):
            start = max(0, anchor - 1) + shift
            if start >= len(text_lines):
                continue
            block = text_lines[start:start + span + shift]
            candidate = "\n".join(block)
            if not candidate.strip():
                continue
            ratio = difflib.SequenceMatcher(None, old_string, candidate, autojunk=False).ratio()
            if ratio > best_ratio:
                best_ratio, best_text, best_start = ratio, candidate, start + 1
    return best_ratio, best_text, best_start


def _not_found_report(resolved: str, text_lf: str, old_string: str) -> str:
    """Error text for a missing old_string, returning the closest real text when close."""
    ratio, candidate, start = _closest_match(text_lf, old_string)
    if ratio < 0:
        return f"Error: old_string not found in {resolved}."
    percent = round(ratio * 100)
    end = start + candidate.count("\n")
    if ratio >= _FUZZY_THRESHOLD:
        return (
            f"Error: old_string not found in {resolved}. Nothing was modified.\n"
            f"Closest match: lines {start}-{end} ({percent}% similar).\n\n"
            f"--- exact text in the file ---\n{candidate}\n--- end of exact text ---\n\n"
            f"--- difference ---\n{_first_difference(old_string, candidate)}\n\n"
            f"Re-send the edit with the exact text above as old_string."
        )
    return (
        f"Error: old_string not found in {resolved}. Nothing was modified.\n"
        f"Closest match (lines {start}-{end}) is only {percent}% similar.\n"
        f"{_first_difference(old_string, candidate)}\n"
        f"Read the file again and copy its exact text, or shorten old_string to the target line "
        f"plus 1-2 lines of context."
    )


def _edit_receipt(
    resolved: str, new_text_lf: str, line_start: int, new_lines: int, count: int, old_lines: int,
) -> str:
    """Result text: what changed, where, and the real text around it."""
    all_lines = new_text_lf.split("\n")
    body_lines = len(all_lines) - 1 if new_text_lf.endswith("\n") else len(all_lines)
    first = max(1, line_start - _EDIT_PREVIEW_LINES)
    last = min(body_lines, line_start + new_lines - 1 + _EDIT_PREVIEW_LINES)
    preview = "\n".join(all_lines[first - 1:last])
    return (
        f"Replaced {count} occurrence(s) in {resolved}\n"
        f"  starting at line {line_start} ({old_lines} lines → {new_lines} lines); "
        f"file has {body_lines} lines\n"
        f"[lines {first}-{last} of {body_lines} — file content after the edit]\n\n{preview}"
    )


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

    Relative paths resolve from the agent's working directory; absolute paths are also accepted. Parent directories are created automatically.
    IMPORTANT: If the file already exists and you intend to rewrite it, call `read_file` first to avoid accidentally discarding content you didn't mean to remove.
    For partial edits to an existing file, prefer `edit_block` instead of a full rewrite.
    Line endings are kept as they are: rewriting an existing file keeps its own line ending and BOM, appending follows the target file's line ending, and a new file is written exactly as given.
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
    if existed_before:
        try:
            original_content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            if mode != "append":
                return f"Error reading existing file: {e}"

    try:
        if mode == "append":
            newline = "\n"
            if existed_before:
                try:
                    newline = _detect_newline(file_path.read_bytes())
                except Exception:
                    pass
            appended = content.replace("\r\n", "\n").replace("\r", "\n").replace("\n", newline)
            with open(file_path, "a", encoding="utf-8", newline="") as f:
                f.write(appended)
            action = "Appended"
        elif existed_before:
            raw = file_path.read_bytes()
            _write_text_preserving(
                file_path,
                content.replace("\r\n", "\n").replace("\r", "\n"),
                _detect_newline(raw),
                raw.startswith(_BOM_UTF8),
            )
            action = "Written"
        else:
            file_path.write_bytes(content.encode("utf-8"))
            action = "Written"
    except Exception as e:
        return f"Error writing file: {e}"

    line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

    _emit_write_preview(resolved, content, mode)

    if mode == "append":
        if original_content:
            append_line_start = original_content.count("\n") + (0 if original_content.endswith("\n") else 1) + 1
            pre_lines = original_content.split("\n")
            if original_content.endswith("\n"):
                pre_lines = pre_lines[:-1]
            append_ctx_before = "\n".join(pre_lines[-5:]) or None
        else:
            append_line_start = 1
            append_ctx_before = None
        emit_file_change(
            resolved,
            "append",
            new_string=content,
            line_start=append_line_start,
            context_before=append_ctx_before,
        )
    elif existed_before:
        emit_file_change(
            resolved,
            "edit",
            old_string=original_content,
            new_string=content,
            line_start=1,
        )
    else:
        emit_file_change(resolved, "create", new_string=content, line_start=1)

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
    old_string: Annotated[
        str,
        "Exact text to replace. Must match the file character-for-character, including indentation, "
        "blank lines and trailing whitespace. Keep the target line plus 1-2 lines of context — enough "
        "to be unique; copying it from read_file output is safer than retyping it.",
    ],
    new_string: Annotated[
        str,
        "Replacement text. Pass an empty string to delete the text matched by old_string.",
    ],
    expected_replacements: Annotated[
        int,
        "How many times old_string is expected to occur, default 1. The tool counts the actual "
        "occurrences and refuses the edit when the count differs; set it to the reported count when "
        "every occurrence should be replaced.",
    ] = 1,
) -> str:
    """Precisely find and replace a text block in a file — use this for any change to an existing file instead of rewriting the whole file.

    Call `read_file` on the target file first. The tool reports an error and changes nothing when old_string occurs a different number of times than expected_replacements. Editing never changes the file's line ending or BOM.

    Usage:
    - Copy old_string from read_file output; do not retype it from memory.
    - Keep old_string short but unique: the target line plus 1-2 lines of context. Extra context only adds chances of a whitespace mismatch.
    - Same text occurs several times: to change one occurrence, widen old_string until it is unique; to change all of them, set expected_replacements to the reported count.
    - When old_string is not found, the result returns the closest text in the file, its similarity and where the first difference is — re-send the edit with that exact text.
    - The result names the edited line and shows the surrounding file content, so the change can be checked without reading the file again.
    - Use `write_file` to create a file or to replace an entire file.
    """
    with _EDIT_BLOCK_LOCK:
        return _edit_block_impl(file_path, old_string, new_string, expected_replacements)


def _edit_block_impl(
    file_path: str,
    old_string: str,
    new_string: str,
    expected_replacements: int = 1,
) -> str:
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
        content, newline, has_bom = _read_text_preserving(path)
    except Exception as e:
        return f"Error reading file: {e}"

    count = content.count(old_string)
    if count == 0:
        return _not_found_report(resolved, content, old_string)

    if count != expected_replacements:
        return (
            f"Error: old_string occurs {count} time(s) in {resolved}, but expected_replacements "
            f"is {expected_replacements}. Nothing was modified.\n"
            f"- To change one occurrence: add more surrounding lines to old_string until it is unique.\n"
            f"- To change all {count} occurrences: set expected_replacements={count}."
        )

    new_content = content.replace(old_string, new_string, expected_replacements)

    try:
        _write_text_preserving(path, new_content, newline, has_bom)
    except Exception as e:
        return f"Error writing file: {e}"

    old_lines = old_string.count("\n") + 1
    new_lines = new_string.count("\n") + 1

    match_pos = content.find(old_string)
    line_start = content[:match_pos].count("\n") + 1 if match_pos >= 0 else 1

    _emit_edit_diff(content, new_content, old_string, new_string, resolved, expected_replacements)

    lines = content.split("\n")
    start_index = line_start - 1
    end_index = start_index + old_string.count("\n") + 1
    context_before = lines[max(0, start_index - _CONTEXT_LINES):start_index]
    context_after = lines[end_index:end_index + _CONTEXT_LINES]

    emit_file_change(
        resolved,
        "edit",
        old_string=old_string,
        new_string=new_string,
        line_start=line_start,
        context_before="\n".join(context_before) or None,
        context_after="\n".join(context_after) or None,
    )

    receipt = _edit_receipt(resolved, new_content, line_start, new_lines, count, old_lines)
    limit = _edit_max_lines()
    biggest = max(old_lines, new_lines)
    if biggest > limit:
        return (
            f"{receipt}\n\n"
            f"Note: this block spans {biggest} lines (guideline: {limit}). Large blocks are harder "
            f"to verify — splitting the change into smaller edits is safer."
        )
    return receipt
