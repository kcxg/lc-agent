import os
import platform

from lc_agent.tools.registry import tool


@tool(group="utility", group_description="通用工具")
def get_system_info() -> str:
    """获取当前系统的基础环境信息（操作系统、架构、Shell 等）。

    会话开始时调用此工具，以确保后续命令与用户环境兼容。
    """
    system = platform.system()
    info_lines = [
        f"os: {system}",
        f"os_version: {platform.version()}",
        f"architecture: {platform.machine()}",
        f"hostname: {platform.node()}",
        f"cwd: {os.getcwd()}",
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
