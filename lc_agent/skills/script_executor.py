import platform
import shutil
import subprocess
import sys
from pathlib import Path

from langchain_agentskills import SkillsToolkit
from langchain_agentskills.exceptions import SkillScriptExecutionError
from langchain_agentskills.executor import ScriptExecutor


class WindowsScriptExecutor(ScriptExecutor):
    """Run interpreter-based skill scripts with their required Windows runtime."""

    def run(
        self,
        script_path: Path,
        args: list[str] | None = None,
        timeout: int | None = None,
    ) -> str:
        effective_timeout = timeout if timeout is not None else self._timeout
        script_name = script_path.name

        if not script_path.is_file():
            raise SkillScriptExecutionError(f"Script not found: {script_path}")

        command = self._build_command(script_path)
        if args:
            command.extend(args)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=str(script_path.parent),
            )
        except subprocess.TimeoutExpired:
            raise SkillScriptExecutionError(
                f"Script '{script_name}' timed out after {effective_timeout}s"
            )
        except OSError as exc:
            raise SkillScriptExecutionError(f"Failed to execute script '{script_name}': {exc}")

        output = result.stdout
        if result.returncode != 0:
            output += f"\n[stderr]\n{result.stderr}" if result.stderr else ""
            raise SkillScriptExecutionError(
                f"Script '{script_name}' exited with code {result.returncode}:\n{output}"
            )

        return output

    @staticmethod
    def _build_command(script_path: Path) -> list[str]:
        suffix = script_path.suffix.lower()
        script = str(script_path)

        if suffix == ".py":
            return [sys.executable, script]
        if suffix == ".js":
            return [_find_runtime("node", script_path), script]
        if suffix == ".ps1":
            return [
                _find_runtime("powershell", script_path),
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                script,
            ]
        if suffix == ".sh":
            return [_find_runtime("bash", script_path), script]

        return [script]


def _find_runtime(name: str, script_path: Path) -> str:
    runtime = shutil.which(name)
    if runtime:
        return runtime
    raise SkillScriptExecutionError(
        f"Script '{script_path.name}' requires '{name}', but it was not found on PATH"
    )


def patch_windows_script_executor(toolkit: SkillsToolkit) -> None:
    """Replace the third-party default executor only for Windows processes."""
    if platform.system() != "Windows":
        return
    toolkit._executor = WindowsScriptExecutor(timeout=toolkit.script_timeout)
