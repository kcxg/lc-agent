import os
import platform

from lc_agent.tools.registry import tool


@tool(group="utility", group_description="通用工具")
def get_system_info() -> str:
    """获取当前系统的基础环境信息（操作系统、架构、Shell 等）。

    仅在需要确认用户操作系统类型时调用（如不确定该用什么命令语法、路径分隔符等），
    不要在每次对话开始时自动调用。
    """
    system = platform.system()
    info_lines = [
        f"os: {system}",
        f"os_version: {platform.version()}",
        f"architecture: {platform.machine()}",
        f"hostname: {platform.node()}",
    ]

    if system == "Windows":
        shell = os.environ.get("COMSPEC", "cmd.exe")
        if "powershell" in shell.lower() or "pwsh" in shell.lower():
            info_lines.append(f"shell: {shell}")
        else:
            info_lines.append("shell: PowerShell (default for run_command)")
    else:
        info_lines.append(f"shell: {os.environ.get('SHELL', '/bin/sh')}")

    return "\n".join(info_lines)
