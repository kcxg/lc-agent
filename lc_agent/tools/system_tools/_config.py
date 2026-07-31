from pathlib import Path
from typing import Any

_cached_config: dict[str, Any] | None = None


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
    allowed = config.get("allowed_directories", [])
    return validate_path_access(path, allowed)


def validate_write_path(path: str) -> str:
    """Validate path for write operations (directory + extension checks)."""
    config = get_file_write_config()
    allowed = config.get("allowed_directories", [])
    resolved = validate_path_access(path, allowed)

    blocked_ext = config.get("blocked_extensions", [])
    if blocked_ext:
        ext = Path(resolved).suffix.lower()
        if ext in blocked_ext:
            raise PermissionError(
                f"Writing files with extension '{ext}' is blocked by configuration"
            )
    return resolved
