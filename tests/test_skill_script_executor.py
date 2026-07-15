import sys

import pytest
from langchain_agentskills import SkillsToolkit
from langchain_agentskills.executor import ScriptExecutor

from lc_agent.app import LcAgentApp
from lc_agent.skills.script_executor import (
    WindowsScriptExecutor,
    patch_windows_script_executor,
)


def test_windows_patch_replaces_toolkit_executor(monkeypatch, tmp_path):
    toolkit = SkillsToolkit(directories=[str(tmp_path)])
    monkeypatch.setattr("lc_agent.skills.script_executor.platform.system", lambda: "Windows")

    patch_windows_script_executor(toolkit)

    assert isinstance(toolkit._executor, WindowsScriptExecutor)


def test_windows_python_executor_uses_current_interpreter(monkeypatch, tmp_path):
    script = tmp_path / "script.py"
    script.write_text("print('not executed')", encoding="utf-8")
    executor = WindowsScriptExecutor()
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs

        class Result:
            returncode = 0
            stdout = "ok"
            stderr = ""

        return Result()

    monkeypatch.setattr("lc_agent.skills.script_executor.subprocess.run", fake_run)

    assert executor.run(script, ["search", "query"]) == "ok"
    assert captured["command"] == [
        sys.executable,
        str(script),
        "search",
        "query",
    ]
    assert captured["kwargs"] == {
        "capture_output": True,
        "text": True,
        "timeout": 30,
        "cwd": str(tmp_path),
    }


@pytest.mark.parametrize(
    ("suffix", "runtime", "expected_prefix"),
    [
        (".js", "node", ["C:/runtime/node.exe"]),
        (
            ".ps1",
            "powershell",
            [
                "C:/runtime/powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
            ],
        ),
        (".sh", "bash", ["C:/runtime/bash.exe"]),
    ],
)
def test_windows_executor_uses_runtime_for_interpreter_scripts(
    monkeypatch, tmp_path, suffix, runtime, expected_prefix
):
    script = tmp_path / f"script{suffix}"
    script.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "lc_agent.skills.script_executor.shutil.which",
        lambda name: f"C:/runtime/{name}.exe" if name == runtime else None,
    )

    command = WindowsScriptExecutor._build_command(script)

    assert command == [*expected_prefix, str(script)]


def test_non_windows_patch_keeps_default_executor(monkeypatch, tmp_path):
    toolkit = SkillsToolkit(directories=[str(tmp_path)])
    original_executor = toolkit._executor
    monkeypatch.setattr("lc_agent.skills.script_executor.platform.system", lambda: "Linux")

    patch_windows_script_executor(toolkit)

    assert toolkit._executor is original_executor
    assert isinstance(toolkit._executor, ScriptExecutor)


def test_app_applies_windows_executor_to_skills_toolkit(monkeypatch, tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    monkeypatch.setattr("lc_agent.skills.script_executor.platform.system", lambda: "Windows")

    app = LcAgentApp(
        {
            "provider": {},
            "agent": {"system_prompt": "Test", "default_model": ""},
            "skills": [str(skills_dir)],
        }
    )

    assert isinstance(app.skills_toolkit._executor, WindowsScriptExecutor)
