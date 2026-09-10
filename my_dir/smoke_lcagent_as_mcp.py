"""lcagent_as_mcp 端到端冒烟：真 uvicorn + 真 MCP 客户端 SDK。

只验证协议链路（不真跑 LLM）：连上 /mcp → initialize → tools/list 能看到
按规则暴露的工具；被安全闸过滤的不出现。
"""

import asyncio
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, r"D:\codes\lc-agent")

import uvicorn

TMP = Path(tempfile.mkdtemp(prefix="lcagent_mcp_e2e_"))
DB_URL = f"sqlite+aiosqlite:///{TMP / 'e2e.db'}"
PORT = 8931


async def build_app():
    import lc_agent.db.models  # noqa: F401
    from lc_agent.db.models import AgentPresetDB
    from lc_agent.db.engine import reset_engine
    from lc_agent.server.app import create_app
    from lc_agent.lcagent_as_mcp import mount_lcagent_as_mcp
    from sqlmodel import SQLModel
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    reset_engine()
    engine = create_async_engine(DB_URL)
    # 同步建表：直接用 asyncio.run 简单起见
    async def _init():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        sf = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with sf() as s:
            s.add(AgentPresetDB(
                id="p-rag", name="rag-search", display_name="RAG检索",
                can_be_subagent=True, allowed_tool_groups=["file_read"],
                default_delegation_description="在知识库中检索资料",
            ))
            s.add(AgentPresetDB(
                id="p-coder", name="coder", can_be_subagent=True,
                allowed_tool_groups=["file_write", "command"],
            ))
            await s.commit()
    await _init()

    app = create_app(config={"database": {"url": DB_URL}, "lcagent_as_mcp": {"enabled": True}})

    class FakeEngine:  # tools/call 需要真 LLM，本冒烟不触发
        pass

    assert mount_lcagent_as_mcp(app, FakeEngine(), DB_URL)
    return app


async def main():
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    app = await build_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    for _ in range(50):
        if server.started:
            break
        await asyncio.sleep(0.2)
    assert server.started, "uvicorn 未启动"

    try:
        async with streamablehttp_client(f"http://127.0.0.1:{PORT}/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                print("[E2E] initialize OK, server =", init.serverInfo.name)

                tools = await session.list_tools()
                names = [t.name for t in tools.tools]
                print("[E2E] tools/list =", names)
                assert "lcagent__rag-search" in names, names
                assert not any("coder" in n for n in names), "安全闸失效：coder 不该出现"

                # 中文 preset：slug 化 + 冲突哈希逻辑单测已覆盖，这里只验证合法名
                assert all(n.replace("lcagent__", "").replace("-", "").replace("_", "").isalnum() for n in names)

                # 未知工具调用要返回明确错误文本而不是崩
                bad = await session.call_tool("lcagent__nope", {"prompt": "x"})
                assert "未知工具" in bad.content[0].text
                print("[E2E] 未知工具错误提示 OK")
        print("[E2E] 全部通过 ✔")
    finally:
        server.should_exit = True
        server_thread.join(timeout=10)


if __name__ == "__main__":
    asyncio.run(main())
