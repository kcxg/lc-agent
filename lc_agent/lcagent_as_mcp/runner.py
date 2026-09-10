"""执行一次 agent run，返回最终文本。

复用现有执行链路（AgentRunService，chat 与定时任务同款），
不自己拼 LLM 调用。一次 tools/call = 一次独立运行 = 一个新会话（§3.6 非目标）。
"""

from datetime import datetime
from uuid import uuid4

from lc_agent.db.engine import get_business_async_session
from lc_agent.db.models import AgentPresetDB
from lc_agent.db.repository import SessionRepository
from lc_agent.lcagent_as_mcp.service_user import ensure_service_user
from lc_agent.utils.loggers import server_logger


async def run_agent_once(
    engine,
    preset_id: str,
    prompt: str,
) -> tuple[str, str | None]:
    """跑一次指定 agent，返回 (最终输出, 错误)。

    调用归属服务用户 lcagent_as_mcp_user（§3.5），用量记它头上；
    不查 UserAgentAccess 白名单——服务用户是系统账号，
    暴露与否由 tool_builder 的两道过滤决定。
    """
    session_id = str(uuid4())
    db = get_business_async_session()
    try:
        user = await ensure_service_user(db)
        preset = await db.get(AgentPresetDB, preset_id)
        display = (preset.display_name or preset.name) if preset else preset_id
        title = f"[MCP] {display} · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        await SessionRepository(db).create(
            id=session_id,
            title=title,
            agent_id=preset_id,
            model="",
            user_id=user.id,
            message_count=0,
        )
    finally:
        await db.close()

    # 惰性导入，避免与 server 路由产生循环依赖（automation.py 同款做法）
    from lc_agent.server.agent_runner import AgentRunService

    service = AgentRunService(engine)
    result = await service.run(
        session_id=session_id,
        prompt=prompt,
        preset_id=preset_id,
        user_id=user.id,
    )
    if result.error:
        server_logger.error(
            "lcagent_as_mcp: agent「%s」执行失败: %s", preset_id, result.error
        )
        return "", result.error
    return result.final_output, None
