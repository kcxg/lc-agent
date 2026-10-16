import json
import os
import platform
import re
import subprocess
import threading
import time
from typing import Annotated

from nb_langchain_agentskills import (
    build_shell_command,
    decode_output,
    render_shell_report,
    resolve_shell,
)

from lc_agent.tools.registry import tool
from lc_agent.tools.system_tools._config import get_command_config, get_shell_preference


# ---------------------------------------------------------------------------
# Background process manager
# ---------------------------------------------------------------------------

class _ProcessEntry:
    __slots__ = ("proc", "stdout_buf", "stderr_buf", "stream_buf", "start_time", "command", "_lock")

    def __init__(self, proc: subprocess.Popen, command: str):
        self.proc = proc
        self.stdout_buf: list[str] = []
        self.stderr_buf: list[str] = []
        # stdout and stderr merged in arrival order for live streaming.
        self.stream_buf: list[str] = []
        self.start_time = time.time()
        self.command = command
        self._lock = threading.Lock()

    def append_stdout(self, line: str):
        with self._lock:
            self.stdout_buf.append(line)
            self.stream_buf.append(line)

    def append_stderr(self, line: str):
        with self._lock:
            self.stderr_buf.append(line)
            self.stream_buf.append(line)

    def get_output(self, offset: int = 0) -> tuple[str, int]:
        """Return buffered output from offset. Returns (text, new_offset)."""
        with self._lock:
            all_lines = self.stdout_buf[offset:]
            new_offset = len(self.stdout_buf)
        return "".join(all_lines), new_offset

    def get_output_parts(self) -> tuple[str, str]:
        """Return buffered stdout and stderr separately."""
        with self._lock:
            return "".join(self.stdout_buf), "".join(self.stderr_buf)

    def get_full_output(self) -> str:
        with self._lock:
            stdout = "".join(self.stdout_buf)
            stderr = "".join(self.stderr_buf)
        parts = []
        if stdout:
            parts.append(stdout)
        if stderr:
            parts.append(f"[stderr]\n{stderr}")
        return "\n".join(parts) if parts else "(no output)"


_processes: dict[int, _ProcessEntry] = {}
_MAX_BUFFER_LINES = 5000
_MAX_BG_PROCESSES = 10


def _reader_thread(entry: _ProcessEntry, stream, append_fn):
    """Background thread that reads lines from a process stream."""
    buffer_full = False
    try:
        for line in iter(stream.readline, b""):
            if not line:
                break
            if not buffer_full:
                append_fn(decode_output(line))
                with entry._lock:
                    if len(entry.stdout_buf) + len(entry.stderr_buf) > _MAX_BUFFER_LINES:
                        buffer_full = True
                        append_fn("[output buffer full, further output discarded]\n")
    except (ValueError, OSError):
        pass
    finally:
        try:
            stream.close()
        except Exception:
            pass


def _reap_exited_processes():
    """Clean up entries for processes that have exited."""
    to_remove = []
    for pid, entry in _processes.items():
        if entry.proc.poll() is not None:
            try:
                entry.proc.wait(timeout=0)
            except Exception:
                pass
            to_remove.append(pid)
    for pid in to_remove:
        del _processes[pid]

def _get_subprocess_env() -> dict[str, str]:
    """Get environment dict that forces unbuffered output for common runtimes."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


# Newlines separate commands in every supported shell (sh/bash, PowerShell, cmd),
# so they belong in the separator set next to ; & | — without them a blocked
# command can hide behind a newline. The extractor stays best-effort: it is a
# guardrail, not a security boundary (variables, interpreters and script files
# are out of reach by design).
_SHELL_SEPARATORS = re.compile(r"[;&|\r\n]|\|\||&&")
_SUBCOMMAND_PATTERN = re.compile(r"\$\(([^)]+)\)|`([^`]+)`")


def _extract_commands(command: str) -> list[str]:
    """Extract all command names from a potentially compound command string."""
    commands: list[str] = []

    for sub_match in _SUBCOMMAND_PATTERN.finditer(command):
        inner = sub_match.group(1) or sub_match.group(2)
        commands.extend(_extract_commands(inner))

    parts = _SHELL_SEPARATORS.split(command)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        for sub_match in _SUBCOMMAND_PATTERN.finditer(part):
            inner = sub_match.group(1) or sub_match.group(2)
            commands.extend(_extract_commands(inner))
        clean = _SUBCOMMAND_PATTERN.sub("", part).strip()
        if clean:
            cmd_name = clean.split()[0] if clean.split() else ""
            if cmd_name:
                commands.append(cmd_name)
    return commands


_EXE_SUFFIXES = (".exe", ".cmd", ".bat", ".com")


def _normalize_command_name(token: str) -> str:
    """Map `"rm"`, `rm.exe` and `/usr/bin/rm` onto the plain name `rm`."""
    name = token.strip().strip("\"'`")
    name = re.split(r"[/\\]", name)[-1] or name
    lowered = name.lower()
    for suffix in _EXE_SUFFIXES:
        if lowered.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _validate_command(command: str) -> str | None:
    """Check the command against the configured blocklist.

    Best-effort guardrail, not a security boundary: it compares the command names
    the shell is expected to run, and that cannot be extracted reliably for every
    shell construct (variables, interpreters, script files).
    """
    config = get_command_config()
    blocked = config.get("blocked_commands", [])
    if not blocked:
        return None

    extracted = _extract_commands(command)
    for cmd in extracted:
        cmd_name = _normalize_command_name(cmd).lower()
        if not cmd_name:
            continue
        for blocked_cmd in blocked:
            blocked_lower = blocked_cmd.strip().lower()
            if cmd_name == blocked_lower or cmd_name.endswith(f"/{blocked_lower}") or cmd_name.endswith(f"\\{blocked_lower}"):
                return f"Command '{cmd}' is blocked by security configuration"
    return None


def _shell_info():
    """The shell commands will actually run through.

    Resolved by the shared resolver from the configured preference — the very
    same fact the ``<user_os>`` system prompt block is built from
    (``middlewares/user_os_middleware.py``), so syntax guidance cannot drift
    away from execution.
    """
    return resolve_shell(get_shell_preference())


@tool(group="command", group_description="命令执行")
def run_command(
    command: Annotated[str, "Command string to execute"],
    max_run_ms: Annotated[
        int,
        "Maximum run time in milliseconds before force-killing the process (default 30000 = 30s)",
    ] = 30000,
    working_directory: Annotated[
        str | None,
        "Working directory for the command; omit to use the agent's working directory",
    ] = None,
) -> str:
    """
    You must first verify that your command is safe — never execute dangerous commands.
    Generate commands according to the user’s operating system — do not execute Linux-syntax commands on Windows.
    
    Execute a one-shot command and wait for it to finish. The process is force-killed on timeout.
    Returns a JSON object: {"exit_code": int, "duration_ms": int, "timed_out": bool, "stdout": str, "stderr": str, "shell": {exe, family, version, fallback_from}}.
    The `shell` field reports which shell actually ran the command — write your next command in that shell's syntax.

    The shell is resolved per project config (see the <user_os> block of your system prompt for its syntax and
    version-specific limits, e.g. whether `&&` and `??` work).

    Use for:  pip install, git status, build scripts, or any command that exits on its own.
    Do NOT use for: long-running servers (Flask, Celery, dev servers) — use start_background_process instead.
    """
    error = _validate_command(command)
    if error:
        return f"Error: {error}"

    config = get_command_config()
    if max_run_ms <= 0:
        max_run_ms = config.get("timeout_ms", 30000)
    timeout_s = max_run_ms / 1000.0

    shell_info = _shell_info()
    full_cmd = build_shell_command(command, shell_info)

    cwd = working_directory
    if not cwd:
        from lc_agent.tools.system_tools._config import get_active_project_root
        cwd = get_active_project_root()
    if cwd:
        cwd_path = os.path.expanduser(cwd)
        if not os.path.isdir(cwd_path):
            return f"Error: Working directory not found: {cwd}"
        cwd = cwd_path

    start = time.time()
    try:
        proc = subprocess.Popen(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=_get_subprocess_env(),
        )
    except Exception as e:
        return f"Error executing command: {e}"

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    # stdout and stderr merged in arrival order for live streaming.
    stream_lines: list[str] = []
    buf_lock = threading.Lock()
    timed_out = False
    stdout_done = threading.Event()
    _stdout = proc.stdout
    _stderr = proc.stderr
    assert _stdout is not None
    assert _stderr is not None

    def _read_stdout():
        try:
            for line in iter(_stdout.readline, b""):
                if not line:
                    break
                text = decode_output(line)
                with buf_lock:
                    stdout_lines.append(text)
                    stream_lines.append(text)
        except (ValueError, OSError):
            pass
        finally:
            try:
                _stdout.close()
            except Exception:
                pass
            stdout_done.set()

    def _read_stderr():
        try:
            for line in iter(_stderr.readline, b""):
                if not line:
                    break
                text = decode_output(line)
                with buf_lock:
                    stderr_lines.append(text)
                    stream_lines.append(text)
        except (ValueError, OSError):
            pass
        finally:
            try:
                _stderr.close()
            except Exception:
                pass

    stdout_thread = threading.Thread(target=_read_stdout, daemon=True)
    stderr_thread = threading.Thread(target=_read_stderr, daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    deadline = time.time() + timeout_s
    last_emitted_len = 0
    poll_interval = 0.2

    while not stdout_done.wait(timeout=poll_interval):
        with buf_lock:
            pending = stream_lines[last_emitted_len:]
        if pending:
            _emit_output_chunk("".join(pending))
            last_emitted_len += len(pending)
        if time.time() >= deadline:
            timed_out = True
            proc.kill()
            break

    with buf_lock:
        pending = stream_lines[last_emitted_len:]
    if pending:
        _emit_output_chunk("".join(pending))
    last_emitted_len += len(pending)

    if not timed_out:
        try:
            remaining = max(0, deadline - time.time())
            proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            try:
                proc.wait(timeout=5)
            except Exception:
                pass
    else:
        try:
            proc.wait(timeout=5)
        except Exception:
            pass

    stdout_thread.join(timeout=3)
    stderr_thread.join(timeout=3)

    with buf_lock:
        pending = stream_lines[last_emitted_len:]
    if pending:
        _emit_output_chunk("".join(pending))

    elapsed_ms = int((time.time() - start) * 1000)

    max_output = 50000

    def _field(text: str) -> str:
        if len(text) > max_output:
            return text[:max_output] + f"\n[truncated: showing first {max_output} of {len(text)} characters]"
        return text

    return json.dumps(
        {
            "exit_code": proc.returncode,
            "duration_ms": elapsed_ms,
            "timed_out": timed_out,
            "stdout": _field("".join(stdout_lines)),
            "stderr": _field("".join(stderr_lines)),
            "shell": render_shell_report(shell_info),
        },
        ensure_ascii=False,
        indent=2,
    )


def _emit_process_info(pid: int, command: str) -> None:
    """Emit process info event so frontend can show PID immediately."""
    try:
        from langchain_core.callbacks import dispatch_custom_event
        dispatch_custom_event("command_process_info", {"pid": pid, "command": command})
    except Exception:
        pass


_emit_failed_logged = False


def _emit_output_chunk(content: str) -> None:
    """Try to emit a real-time output chunk via LangChain's custom event system."""
    global _emit_failed_logged
    try:
        from langchain_core.callbacks import dispatch_custom_event
        dispatch_custom_event("command_output", {"content": content})
    except Exception:
        if not _emit_failed_logged:
            _emit_failed_logged = True
            import logging
            logging.getLogger(__name__).debug(
                "dispatch_custom_event unavailable, streaming output disabled",
                exc_info=True,
            )


@tool(group="command", group_description="命令执行")
def list_all_processes() -> str:
    """List all currently running system processes with their PID, name, and memory usage. Limited to the first 100 results.
    Returns a JSON object: {"count": int, "truncated": bool, "processes": [...]}."""
    system = platform.system()
    try:
        if system == "Windows":
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace",
            )
            if result.returncode != 0:
                return f"Error: tasklist failed: {result.stderr}"
            lines = result.stdout.strip().splitlines()
            processes = []
            for line in lines[:100]:
                parts = [p.strip('"') for p in line.split('","')]
                if len(parts) >= 5:
                    try:
                        pid = int(parts[1])
                    except ValueError:
                        continue
                    processes.append({"pid": pid, "name": parts[0], "memory": parts[4]})
            return json.dumps(
                {
                    "count": len(processes),
                    "truncated": len(lines) > 100,
                    "processes": processes,
                },
                ensure_ascii=False,
                indent=2,
            )
        else:
            result = subprocess.run(
                ["ps", "aux", "--sort=-rss"],
                capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace",
            )
            if result.returncode != 0:
                return f"Error: ps failed: {result.stderr}"
            lines = result.stdout.strip().splitlines()
            return json.dumps(
                {
                    "count": min(len(lines), 100),
                    "truncated": len(lines) > 100,
                    "processes": lines[:100],
                },
                ensure_ascii=False,
                indent=2,
            )
    except Exception as e:
        return f"Error listing processes: {e}"


@tool(group="command", group_description="命令执行")
def list_agent_started_processes() -> str:
    """List all background processes started by start_background_process that are currently tracked in this session.
    Returns a JSON object: {"count": int, "processes": [{"pid": int, "status": str, "running_for_s": int, "command": str}]}."""
    _reap_exited_processes()

    if not _processes:
        return json.dumps({"count": 0, "processes": []}, ensure_ascii=False, indent=2)

    processes = []
    for pid, entry in _processes.items():
        is_running = entry.proc.poll() is None
        status = "running" if is_running else f"exited (code={entry.proc.returncode})"
        processes.append(
            {
                "pid": pid,
                "status": status,
                "running_for_s": int(time.time() - entry.start_time),
                "command": entry.command,
            }
        )
    return json.dumps({"count": len(processes), "processes": processes}, ensure_ascii=False, indent=2)


@tool(group="command", group_description="命令执行")
def kill_process(
    pid: Annotated[int, "PID of the process to terminate"],
) -> str:
    """Terminate a process by its PID using SIGKILL on Linux/macOS or taskkill /F on Windows.
    Returns a JSON object: {"pid": int, "killed": bool, "detail": str}."""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                return f"Error: Failed to kill process {pid}: {result.stderr.strip()}"
        else:
            import signal
            os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return f"Error: Process {pid} not found"
    except PermissionError:
        return f"Error: Permission denied to kill process {pid}"
    except Exception as e:
        return f"Error killing process {pid}: {e}"

    _processes.pop(pid, None)
    return json.dumps(
        {"pid": pid, "killed": True, "detail": f"Process {pid} terminated"},
        ensure_ascii=False,
        indent=2,
    )


@tool(group="command", group_description="命令执行")
def start_background_process(
    command: Annotated[str, "Command string to execute in the background"],
    wait_ms: Annotated[
        int,
        "Milliseconds to wait for initial output (default 10000 = 10s). After the wait the process keeps running in the background.",
    ] = 10000,
    working_directory: Annotated[
        str | None,
        "Working directory for the command; omit to use the agent's working directory",
    ] = None,
) -> str:
    """
    Start a long-running process in the background.
    Returns a JSON object: {"pid": int, "status": str, "exit_code": int|null, "command": str, "stdout": str, "stderr": str, "shell": {exe, family, version, fallback_from}} with initial output.
    The `shell` field reports which shell actually ran the command.
    Generate commands according to the user’s operating system — do not execute Linux-syntax commands on Windows.

    Use for: Flask/Django/FastAPI servers, Celery workers, webpack dev servers, or any daemon that doesn't exit on its own.
    Do NOT use for: one-shot commands that exit by themselves — use run_command instead.

    After starting, use read_process_output to poll subsequent output and kill_process to terminate.
    """
    _reap_exited_processes()

    if len(_processes) >= _MAX_BG_PROCESSES:
        return (
            f"Error: Maximum background processes ({_MAX_BG_PROCESSES}) reached. "
            f"Use kill_process to terminate unused processes first."
        )

    error = _validate_command(command)
    if error:
        return f"Error: {error}"

    shell_info = _shell_info()
    full_cmd = build_shell_command(command, shell_info)

    cwd = working_directory
    if not cwd:
        from lc_agent.tools.system_tools._config import get_active_project_root
        cwd = get_active_project_root()
    if cwd:
        cwd_path = os.path.expanduser(cwd)
        if not os.path.isdir(cwd_path):
            return f"Error: Working directory not found: {cwd}"
        cwd = cwd_path

    try:
        proc = subprocess.Popen(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=_get_subprocess_env(),
        )
    except Exception as e:
        return f"Error starting process: {e}"

    entry = _ProcessEntry(proc, command)
    _processes[proc.pid] = entry

    _emit_process_info(proc.pid, command)

    stdout_thread = threading.Thread(
        target=_reader_thread, args=(entry, proc.stdout, entry.append_stdout), daemon=True
    )
    stderr_thread = threading.Thread(
        target=_reader_thread, args=(entry, proc.stderr, entry.append_stderr), daemon=True
    )
    stdout_thread.start()
    stderr_thread.start()

    deadline = time.time() + wait_ms / 1000.0
    last_emitted_len = 0
    poll_interval = 0.2

    while time.time() < deadline:
        time.sleep(poll_interval)
        with entry._lock:
            current_len = len(entry.stream_buf)
            new_lines = entry.stream_buf[last_emitted_len:current_len]
        if new_lines:
            _emit_output_chunk("".join(new_lines))
            last_emitted_len = current_len
        if proc.poll() is not None:
            time.sleep(0.3)
            break

    with entry._lock:
        new_lines = entry.stream_buf[last_emitted_len:]
    if new_lines:
        _emit_output_chunk("".join(new_lines))

    initial_stdout, initial_stderr = entry.get_output_parts()
    is_running = proc.poll() is None

    if is_running:
        status = "running"
    elif "[Process terminated by user]" in initial_stdout:
        status = "terminated by user"
    else:
        status = f"exited (code={proc.returncode})"

    return json.dumps(
        {
            "pid": proc.pid,
            "status": status,
            "exit_code": None if is_running else proc.returncode,
            "command": command,
            "stdout": initial_stdout,
            "stderr": initial_stderr,
            "shell": render_shell_report(shell_info),
        },
        ensure_ascii=False,
        indent=2,
    )


@tool(group="command", group_description="命令执行")
def read_process_output(
    pid: Annotated[int, "PID of the background process (returned by start_background_process)"],
    tail: Annotated[
        int,
        "Number of tail lines to return (default 50). Set 0 to return all buffered output.",
    ] = 50,
) -> str:
    """Read buffered stdout/stderr from a tracked background process.
    Returns a JSON object: {"pid": int, "status": str, "running_for_s": number, "command": str, "output": str}."""
    entry = _processes.get(pid)
    if entry is None:
        return f"Error: No tracked background process with PID {pid}. Use start_background_process to start one."

    is_running = entry.proc.poll() is None
    elapsed = time.time() - entry.start_time
    status = "running" if is_running else f"exited (code={entry.proc.returncode})"

    full_output = entry.get_full_output()
    if tail > 0:
        lines = full_output.splitlines()
        if len(lines) > tail:
            full_output = "\n".join(lines[-tail:])
            full_output = f"... [{len(lines) - tail} earlier lines omitted]\n{full_output}"

    return json.dumps(
        {
            "pid": pid,
            "status": status,
            "running_for_s": round(elapsed, 1),
            "command": entry.command,
            "output": full_output,
        },
        ensure_ascii=False,
        indent=2,
    )
