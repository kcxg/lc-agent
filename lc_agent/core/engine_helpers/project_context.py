"""Project context builder — git snapshot and OS info for the agent system prompt."""


def _build_project_context_text(project_root: str) -> str:
    """Build a project context block with git snapshot and OS info.

    Runs git commands synchronously (called once at agent build time).
    """
    import os
    import platform
    import subprocess

    os_name = platform.system()
    # Mirror run_command's shell selection logic for consistency:
    # Windows defaults to powershell; Linux/macOS reads $SHELL.
    # Check config.jsonc's system_tools.command.default_shell first.
    try:
        from lc_agent.tools.system_tools._config import get_command_config
        _cmd_cfg = get_command_config()
        _configured_shell = _cmd_cfg.get("default_shell", "")
    except Exception:
        _configured_shell = ""
    if _configured_shell:
        shell = _configured_shell.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
    elif os_name == "Windows":
        shell = "powershell"
    else:
        shell = os.environ.get("SHELL", "bash").rsplit("/", 1)[-1]
    try:
        import platform as _pl
        os_version = _pl.version() if os_name == "Linux" else _pl.release()
        os_info = f"{os_name} {os_version} ({shell})"
    except Exception:
        os_info = f"{os_name} ({shell})"

    def _git(cmd: list[str]) -> str:
        try:
            r = subprocess.run(
                cmd, cwd=project_root, capture_output=True, text=True, timeout=5
            )
            return r.stdout.strip()
        except Exception:
            return ""

    is_git = _git(["git", "rev-parse", "--git-dir"])
    if is_git:
        branch = _git(["git", "branch", "--show-current"]) or "(detached HEAD)"
        last_commit = _git(["git", "log", "-1", "--oneline"]) or "(no commits)"
        status_out = _git(["git", "status", "--short"])
        git_section = (
            f"**Branch**: {branch}\n"
            f"**Last Commit**: {last_commit}\n"
            f"**Git Status** (snapshot at session start):\n"
            f"```\n{status_out or '(clean)'}\n```\n\n"
            f"> Git status is a snapshot. Run `run_command` to refresh if needed."
        )
    else:
        git_section = "**Git Status**: Not a git repository"

    return (
        "<project_context>\n"
        "## Project Context\n\n"
        f"**Root**: {project_root}\n"
        f"**OS**: {os_info}\n"
        f"{git_section}"
        "\n</project_context>"
    )
