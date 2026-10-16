"""blocked_commands 校验的回归测试：换行 / 引号 / 后缀这几类漏判。

定位说明：这是"尽力而为的护栏"，不是安全边界 —— 变量拼接、解释器、脚本文件
等间接形式不在字符串层能识别的范围内（见文件末尾的已知边界测试）。
"""

from lc_agent.tools.system_tools import command_tools


def _block_only(monkeypatch, *names: str) -> None:
    monkeypatch.setattr(
        command_tools, "get_command_config", lambda: {"blocked_commands": list(names)}
    )


def _blocked(command: str) -> bool:
    return command_tools._validate_command(command) is not None


def test_semicolon_control_case_is_blocked(monkeypatch):
    _block_only(monkeypatch, "rm")
    assert _blocked("echo start; rm --version")


def test_newline_separated_command_is_blocked(monkeypatch):
    _block_only(monkeypatch, "rm")
    assert _blocked("echo start\nrm --version")


def test_crlf_separated_command_is_blocked(monkeypatch):
    _block_only(monkeypatch, "rm")
    assert _blocked("echo start\r\nrm --version")


def test_quoted_quoted_path_and_suffixed_forms_are_blocked(monkeypatch):
    _block_only(monkeypatch, "rm")
    for command in (
        'echo start; "rm" --version',
        "echo start; rm.exe --version",
        "echo start; rm.cmd --version",
        "echo start; /usr/bin/rm --version",
        r"echo start; C:\tools\rm --version",
    ):
        assert _blocked(command), command


def test_normalize_command_name_helper():
    assert command_tools._normalize_command_name('"rm"') == "rm"
    assert command_tools._normalize_command_name("rm.exe") == "rm"
    assert command_tools._normalize_command_name("/usr/bin/RM.CMD") == "RM"
    assert command_tools._normalize_command_name(r"C:\tools\rm") == "rm"


def test_blocked_word_used_as_argument_is_allowed(monkeypatch):
    """`echo rm` 里的 rm 只是参数：不做整串词边界匹配，避免误报。"""
    _block_only(monkeypatch, "rm")
    assert not _blocked("echo rm")


def test_similar_name_is_not_blocked(monkeypatch):
    _block_only(monkeypatch, "rm")
    assert not _blocked("echo start; rm2 --version")


def test_empty_blocklist_allows_everything(monkeypatch):
    monkeypatch.setattr(command_tools, "get_command_config", lambda: {})
    assert not _blocked("rm --version")


def test_run_command_refuses_newline_separated_blocked_command(monkeypatch):
    """工具层：换行绕过必须在 spawn 之前就被拒。"""
    _block_only(monkeypatch, "rm")
    out = command_tools.run_command("echo start\nrm --version")
    assert out.startswith("Error:")
    assert "blocked" in out


def test_start_background_process_refuses_newline_separated_blocked_command(monkeypatch):
    _block_only(monkeypatch, "rm")
    out = command_tools.start_background_process("echo start\nrm --version")
    assert out.startswith("Error:")
    assert "blocked" in out


def test_known_limit_variable_indirection_is_not_detected(monkeypatch):
    """已知设计边界：变量拼接的间接调用识别不了（字符串层的天花板）。"""
    _block_only(monkeypatch, "rm")
    assert not _blocked("X=rm; $X --version")
