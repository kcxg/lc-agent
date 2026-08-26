"""Track file changes during agent tool execution.

Emits custom events that the SSE layer persists to the file_changes table.
Also handles git base hash snapshotting on first file write per session.
"""

import subprocess
from contextvars import ContextVar, Token
from pathlib import Path

_session_id_var: ContextVar[str | None] = ContextVar(
    "lc_agent_file_change_session_id", default=None
)
_git_snapshot_done_var: ContextVar[set] = ContextVar(
    "lc_agent_git_snapshot_done", default=None
)


def bind_session_for_file_tracking(session_id: str) -> Token:
    """Bind session_id for file change tracking. Returns a token for reset."""
    token = _session_id_var.set(session_id)
    existing = _git_snapshot_done_var.get(None)
    if existing is None:
        _git_snapshot_done_var.set(set())
    return token


def reset_session_for_file_tracking(token: Token) -> None:
    """Restore the previous session_id binding."""
    _session_id_var.reset(token)


def get_tracking_session_id() -> str | None:
    return _session_id_var.get(None)


def _get_git_head_hash(file_path: str) -> str | None:
    """Get the current git HEAD hash for the repo containing file_path."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=str(Path(file_path).parent),
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _try_snapshot_git_base(session_id: str, file_path: str) -> None:
    """Snapshot git HEAD hash before first file write in this session.

    Uses ContextVar set to track whether we already did this for the session.
    Saves the hash via persistence (async, fire-and-forget).
    """
    done = _git_snapshot_done_var.get(None)
    if done is None:
        done = set()
        _git_snapshot_done_var.set(done)

    if session_id in done:
        return
    done.add(session_id)

    git_hash = _get_git_head_hash(file_path)
    if not git_hash:
        return

    try:
        from langchain_core.callbacks import dispatch_custom_event
        dispatch_custom_event("file_change_git_snapshot", {
            "session_id": session_id,
            "git_base_hash": git_hash,
        })
    except Exception:
        pass


def emit_file_change(
    file_path: str,
    change_type: str,
    *,
    old_string: str | None = None,
    new_string: str | None = None,
    move_destination: str | None = None,
) -> None:
    """Emit a file change event for the SSE layer to persist."""
    session_id = _session_id_var.get(None)
    if not session_id:
        return

    _try_snapshot_git_base(session_id, file_path)

    try:
        from langchain_core.callbacks import dispatch_custom_event
        dispatch_custom_event("file_change_record", {
            "session_id": session_id,
            "file_path": file_path,
            "change_type": change_type,
            "old_string": old_string,
            "new_string": new_string,
            "move_destination": move_destination,
        })
    except Exception:
        pass
