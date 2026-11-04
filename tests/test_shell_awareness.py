"""命令执行的 shell 感知：<user_os> 提示词与 run_command 必须来自同一份事实。

背景：以前 user_os_middleware 自己复制了一套 shell 判断，Windows 上
`... or os_name == "Windows"` 恒真 → cmd/bash 分支是死代码：配了 cmd，执行层用 cmd，
提示词却说"必须用 PowerShell 语法"。现在两者都走 nb_langchain_agentskills.resolve_shell。
"""

import dataclasses
import json

import pytest
from nb_langchain_agentskills import ShellInfo, reset_shell_cache, resolve_shell

from lc_agent.middlewares import user_os_middleware
from lc_agent.tools.system_tools import _config, command_tools


@pytest.fixture(autouse=True)
def _clear_shell_cache():
    reset_shell_cache()
    yield
    reset_shell_cache()


def _info(family: str, version: str = "", caps: tuple[str, ...] = ()) -> ShellInfo:
    return ShellInfo(
        exe=f"{family}.exe",
        family=family,
        args=(),
        version=version,
        capabilities=frozenset(caps),
    )


def _user_os_text(monkeypatch, info: ShellInfo) -> str:
    # 中间件在模块顶层 import 了 resolve_shell（早绑定），所以要打桩模块内的名字，
    # 而不是 nb_langchain_agentskills 包属性。
    monkeypatch.setattr(user_os_middleware, "resolve_shell", lambda preference="": info)
    return user_os_middleware._get_user_os_text()


def test_user_os_reports_the_resolved_shell(monkeypatch):
    text = _user_os_text(
        monkeypatch,
        _info("pwsh", "7.6.7", ("chain_ops", "null_coalescing", "utf8_output")),
    )

    assert text.startswith("<user_os>")
    assert "pwsh 7.6.7" in text
    assert "ARE supported" in text


def test_user_os_reports_5_1_limits(monkeypatch):
    text = _user_os_text(monkeypatch, _info("powershell", "5.1.22621.6133"))

    assert "NOT supported" in text
    assert "cmd1; if ($?) { cmd2 }" in text


def test_user_os_says_cmd_when_cmd_is_configured(monkeypatch):
    """回归：Windows 上曾经无论配什么 shell 都说 PowerShell。"""
    text = _user_os_text(monkeypatch, _info("cmd", "", ("chain_ops",)))

    assert "cmd.exe" in text
    assert "PowerShell syntax" not in text


def test_user_os_reports_fallback(monkeypatch):
    info = dataclasses.replace(_info("powershell", "5.1.6718"), fallback_from="pwsh")

    assert "(pwsh unavailable)" in _user_os_text(monkeypatch, info)


def test_shell_preference_reads_the_command_config_key(monkeypatch):
    monkeypatch.setattr(_config, "get_command_config", lambda: {"default_shell": "cmd"})
    assert _config.get_shell_preference() == "cmd"

    monkeypatch.setattr(_config, "get_command_config", lambda: {})
    assert _config.get_shell_preference() == ""

    monkeypatch.setattr(_config, "get_command_config", lambda: None)
    assert _config.get_shell_preference() == ""


def test_command_tools_use_the_configured_preference(monkeypatch):
    monkeypatch.setattr(command_tools, "get_shell_preference", lambda: "cmd")
    seen: list[str] = []

    def _fake_resolve(preference: str = "") -> ShellInfo:
        seen.append(preference)
        return _info("cmd")

    monkeypatch.setattr(command_tools, "resolve_shell", _fake_resolve)

    command_tools._shell_info()

    assert seen == ["cmd"]


def test_run_command_echoes_the_resolved_shell(monkeypatch):
    real = resolve_shell("")  # 真实解析本机 shell
    fake = dataclasses.replace(real, version="9.9.9-probe")
    monkeypatch.setattr(command_tools, "resolve_shell", lambda preference="": fake)

    out = command_tools.run_command("echo lc-agent-shell-probe")

    payload = json.loads(out)
    assert payload["shell"]["version"] == "9.9.9-probe"
    assert payload["shell"]["family"] == real.family
    assert payload["exit_code"] == 0
    assert "lc-agent-shell-probe" in payload["stdout"]
