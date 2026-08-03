from contextvars import ContextVar
from pathlib import Path
from typing import Any

_cached_config: dict[str, Any] | None = None

# Per-request project context stored in ContextVar so concurrent async tasks
# (different users / sessions) don't overwrite each other's values.
_active_project_root_var: ContextVar[str | None] = ContextVar(
    "lc_agent_active_project_root", default=None
)
_active_extra_dirs_var: ContextVar[list[str] | None] = ContextVar(
    "lc_agent_active_extra_dirs", default=None
)


def set_active_project(project_root: str | None, extra_dirs: list[str] | None = None) -> None:
    """Set the active project context for the current async task.

    Uses ContextVar so each concurrent request has its own isolated value.
    """
    if project_root:
        _active_project_root_var.set(str(Path(project_root).expanduser().resolve()))
    else:
        _active_project_root_var.set(None)
    _active_extra_dirs_var.set([
        str(Path(d).expanduser().resolve()) for d in (extra_dirs or [])
    ])


def get_active_project_root() -> str | None:
    """Return the currently active project root for this task, or None."""
    return _active_project_root_var.get()


def get_system_tools_config() -> dict[str, Any]:
    """Return the 'system_tools' section from config.jsonc (cached)."""
    global _cached_config
    if _cached_config is not None:
        return _cached_config

    from lc_agent.config.loader import load_config
    full_config = load_config()
    _cached_config = full_config.get("system_tools", {})
    return _cached_config


def get_file_read_config() -> dict[str, Any]:
    return get_system_tools_config().get("file_read", {})


def get_file_write_config() -> dict[str, Any]:
    return get_system_tools_config().get("file_write", {})


def get_command_config() -> dict[str, Any]:
    return get_system_tools_config().get("command", {})


def _get_effective_allowed_dirs(config_dirs: list[str]) -> list[str]:
    """Compute effective allowed directories considering active project context."""
    root = _active_project_root_var.get()
    if root:
        return [root] + (_active_extra_dirs_var.get() or [])
    return config_dirs


def validate_path_access(path: str, allowed_directories: list[str]) -> str:
    """Validate that the resolved path is within allowed directories.

    Returns the resolved absolute path if allowed.
    Raises PermissionError if path is outside allowed directories.
    """
    resolved = Path(path).expanduser().resolve()

    if not allowed_directories:
        return str(resolved)

    for allowed in allowed_directories:
        allowed_resolved = Path(allowed).expanduser().resolve()
        try:
            resolved.relative_to(allowed_resolved)
            return str(resolved)
        except ValueError:
            continue

    raise PermissionError(
        f"Access denied: '{path}' is outside allowed directories: {allowed_directories}"
    )


def validate_read_path(path: str) -> str:
    """Validate path for read operations."""
    config = get_file_read_config()
    allowed = _get_effective_allowed_dirs(config.get("allowed_directories", []))
    return validate_path_access(path, allowed)


def validate_write_path(path: str) -> str:
    """Validate path for write operations (directory + extension checks)."""
    config = get_file_write_config()
    allowed = _get_effective_allowed_dirs(config.get("allowed_directories", []))
    resolved = validate_path_access(path, allowed)

    blocked_ext = config.get("blocked_extensions", [])
    if blocked_ext:
        ext = Path(resolved).suffix.lower()
        if ext in blocked_ext:
            raise PermissionError(
                f"Writing files with extension '{ext}' is blocked by configuration"
            )
    return resolved
