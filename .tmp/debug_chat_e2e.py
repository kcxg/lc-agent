import asyncio
import json
from pathlib import Path

import httpx
from sqlalchemy import text

from lc_agent.app import LcAgentApp
from lc_agent.config.loader import load_config
from lc_agent.db.engine import get_async_engine, get_async_session, reset_engine
from lc_agent.db.repository import SessionRepository

BASE_URL = "http://127.0.0.1:8001"
ROOT = Path(r"D:\codes\lc-agent-bfzs")
CONFIG_PATH = ROOT / "config.jsonc"
LOG_DIR = Path(r"D:\codes\lc-agent\.tmp\bfzs-runlogs")
PY_DB_URL = "sqlite+aiosqlite:///D:/codes/lc-agent-bfzs/bfzs_data.db"


def show_latest_logs() -> None:
    print("LATEST_LOGS_BEGIN")
    logs = sorted(LOG_DIR.glob("bfzs-restart-*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:2]
    for log in sorted(logs):
        print(f"===== {log} =====")
        try:
            lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in lines[-180:]:
                print(line)
        except Exception as exc:
            print(f"READ_LOG_FAILED {log}: {type(exc).__name__}: {exc}")
    print("LATEST_LOGS_END")


async def probe_raw_engine(url: str) -> None:
    print(f"RAW_ENGINE_URL {url}")
    reset_engine()
    engine = get_async_engine(url)
    try:
        async with engine.connect() as conn:
            rows = (await conn.execute(text("pragma database_list"))).fetchall()
            print(f"RAW_DATABASE_LIST {rows}")
            quick = (await conn.execute(text("pragma quick_check"))).fetchall()
            print(f"RAW_QUICK_CHECK {quick}")
    except Exception as exc:
        print(f"RAW_PROBE_FAILED_NON_BLOCKING {type(exc).__name__}: {exc}")
    finally:
        await engine.dispose()
        reset_engine()


async def probe_app_repo() -> None:
    reset_engine()
    config = load_config(str(CONFIG_PATH))
    app = LcAgentApp(config, host="127.0.0.1", port=8001)
    db_url = app.fastapi_app.state.config["database"]["url"]
    checkpoint_path = app.fastapi_app.state.config["database"].get("checkpoint_path")
    print(f"APP_DB_URL {db_url}")
    print(f"APP_CHECKPOINT_PATH {checkpoint_path}")
    session = get_async_session(db_url)
    try:
        repo = SessionRepository(session)
        created = await repo.create(title="debug script repo probe", agent_id="__chat__", model="", user_id="debug-script")
        print(f"APP_REPO_CREATE_OK {created.id}")
    finally:
        await session.close()
    reset_engine()


async def probe_http_chat() -> None:
    async with httpx.AsyncClient(timeout=90.0) as client:
        login = await client.post(f"{BASE_URL}/api/auth/login", json={"username": "admin", "password": "123456"})
        print(f"LOGIN_STATUS {login.status_code}")
        print(login.text[:1000])
        login.raise_for_status()
        data = login.json()
        token = data.get("access_token") or data.get("token") or data.get("accessToken")
        if not token:
            raise RuntimeError(f"login returned no token: {data}")
        headers = {"Authorization": f"Bearer {token}"}

        session = await client.post(
            f"{BASE_URL}/api/sessions",
            headers=headers,
            json={"title": "chat e2e test", "agent_id": "__chat__", "model": ""},
        )
        print(f"SESSION_STATUS {session.status_code}")
        print(session.text[:2000])
        session.raise_for_status()
        thread_id = session.json()["id"]
        print(f"SESSION_ID {thread_id}")

        async with client.stream(
            "POST",
            f"{BASE_URL}/api/threads/{thread_id}/runs/stream",
            headers=headers,
            json={"input": "你好，请只回复 OK", "preset_id": "__chat__", "model": ""},
        ) as response:
            print(f"SSE_STATUS {response.status_code}")
            response.raise_for_status()
            events = []
            async for line in response.aiter_lines():
                if line:
                    print(f"SSE {line}")
                    events.append(line)
                if len(events) > 200 or any(line.startswith("event: done") for line in events):
                    break
            joined = "\n".join(events)
            if "event: error" in joined or not any(x in joined for x in ["event: token", "event: content", "event: done"]):
                raise RuntimeError("SSE did not produce a healthy assistant reply")


async def main() -> int:
    try:
        await probe_raw_engine(PY_DB_URL)
        try:
            await probe_app_repo()
        except Exception as exc:
            print(f"APP_REPO_PROBE_FAILED_NON_BLOCKING {type(exc).__name__}: {exc}")
        await probe_http_chat()
        print("CHAT_E2E_OK")
        return 0
    except Exception as exc:
        print(f"DEBUG_FAILED {type(exc).__name__}: {exc}")
        show_latest_logs()
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
