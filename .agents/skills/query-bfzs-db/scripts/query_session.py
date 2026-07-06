"""Query bfzs session data (messages, tools, presets, users) from SQLite databases.

Usage:
  python query_session.py --sessions [--limit N] [--search KEYWORD]
  python query_session.py --presets
  python query_session.py --users
  python query_session.py --msgs <session_id>      # UI messages from chat_ui_messages (fast, has usage/traces)
  python query_session.py <session_id>              # Full messages from LangGraph checkpoint
  python query_session.py --tools <session_id>      # Tool calls only, from checkpoint
  python query_session.py --state                   # Runtime MCP/tool state via API
  python query_session.py --last                    # Most recent session messages (shortcut)
  python query_session.py --last --tools            # Tool calls for most recent session
"""
import argparse
import asyncio
import json
import sqlite3
import sys
import urllib.request
from pathlib import Path

BFZS_DIR = Path(r"D:\codes\lc-agent-bfzs")
DATA_DB = BFZS_DIR / "bfzs_data.db"
CHECKPOINT_DB = BFZS_DIR / "bfzs_checkpoints.db"
API_BASE = "http://127.0.0.1:8001/api"


def get_conn(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}")
        sys.exit(1)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


# ─── sessions ───────────────────────────────────────────────────────────────

def list_sessions(limit: int = 10, search: str | None = None):
    conn = get_conn(DATA_DB)
    c = conn.cursor()
    sql = """
        SELECT s.id, s.title, s.agent_id, s.model, s.message_count,
               s.updated_at, s.is_pinned,
               u.username
        FROM sessions s
        LEFT JOIN users u ON s.user_id = u.id
        {where}
        ORDER BY s.updated_at DESC
        LIMIT ?
    """
    if search:
        c.execute(sql.format(where="WHERE s.title LIKE ?"), (f"%{search}%", limit))
    else:
        c.execute(sql.format(where=""), (limit,))

    rows = c.fetchall()
    print(f"\n{'ID':<38} {'Title':<28} {'Agent':<14} {'Model':<20} {'Msgs':>4}  {'Updated':<20} {'User'}")
    print("-" * 145)
    for r in rows:
        pin = "*" if r["is_pinned"] else " "
        updated = (r["updated_at"] or "")[:19]
        user = r["username"] or "-"
        model = (r["model"] or "-")[:20]
        print(f"{pin}{r['id']:<37} {r['title'][:27]:<28} {r['agent_id'][:13]:<14} {model:<20} {r['message_count']:>4}  {updated:<20} {user}")
    print(f"\n({len(rows)} sessions)")
    conn.close()


def get_last_session_id() -> str:
    conn = get_conn(DATA_DB)
    c = conn.cursor()
    c.execute("SELECT id FROM sessions ORDER BY updated_at DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if not row:
        print("No sessions found")
        sys.exit(1)
    return row["id"]


# ─── presets ─────────────────────────────────────────────────────────────────

def list_presets():
    conn = get_conn(DATA_DB)
    c = conn.cursor()
    c.execute("""
        SELECT id, name, default_model, system_prompt,
               allowed_tool_groups, allowed_mcp_servers, allowed_skills,
               updated_at
        FROM agent_presets
        ORDER BY updated_at DESC
    """)
    rows = c.fetchall()
    print(f"\n=== Agent Presets ({len(rows)}) ===\n")
    for r in rows:
        tools = json.loads(r["allowed_tool_groups"]) if r["allowed_tool_groups"] else None
        mcp = json.loads(r["allowed_mcp_servers"]) if r["allowed_mcp_servers"] else None
        skills = json.loads(r["allowed_skills"]) if r["allowed_skills"] else None
        prompt_preview = (r["system_prompt"] or "")[:80].replace("\n", " ")
        print(f"  ID:      {r['id']}")
        print(f"  Name:    {r['name']}")
        print(f"  Model:   {r['default_model'] or '-'}")
        print(f"  Prompt:  {prompt_preview}{'...' if len(r['system_prompt'] or '') > 80 else ''}")
        print(f"  Tools:   {tools}")
        print(f"  MCP:     {mcp}")
        print(f"  Skills:  {skills}")
        print(f"  Updated: {(r['updated_at'] or '')[:19]}")
        print()
    conn.close()


# ─── users ───────────────────────────────────────────────────────────────────

def list_users():
    conn = get_conn(DATA_DB)
    c = conn.cursor()
    c.execute("SELECT id, username, role, created_at FROM users ORDER BY created_at")
    users = c.fetchall()
    print(f"\n=== Users ({len(users)}) ===\n")
    print(f"{'ID':<38} {'Username':<20} {'Role':<10} {'Created'}")
    print("-" * 95)
    for u in users:
        print(f"{u['id']:<38} {u['username']:<20} {u['role']:<10} {(u['created_at'] or '')[:19]}")
        c2 = conn.cursor()
        c2.execute("SELECT agent_id FROM user_agent_access WHERE user_id = ?", (u["id"],))
        agents = [row["agent_id"] for row in c2.fetchall()]
        if agents:
            print(f"  {'Agents:':<10} {agents}")
    conn.close()


# ─── chat_ui_messages (UI table, fast, has usage/traces) ─────────────────────

def query_ui_messages(session_id: str):
    conn = get_conn(DATA_DB)
    c = conn.cursor()

    c.execute("SELECT title, agent_id, model FROM sessions WHERE id = ?", (session_id,))
    sess = c.fetchone()
    if sess:
        print(f"\n=== Session: {sess['title']} | agent={sess['agent_id']} | model={sess['model'] or '-'} ===")

    c.execute("""
        SELECT id, role, content, tool_calls, usage, created_at
        FROM chat_ui_messages
        WHERE session_id = ?
        ORDER BY created_at, id
    """, (session_id,))
    rows = c.fetchall()

    if not rows:
        print(f"No UI messages found for session: {session_id}")
        conn.close()
        return

    print(f"  ({len(rows)} messages)\n")
    for r in rows:
        role_icon = {"user": "USER", "assistant": "AI", "tool": "TOOL", "system": "SYS"}.get(r["role"], r["role"].upper())
        print(f"[{role_icon}] {(r['created_at'] or '')[:19]}")

        content = (r["content"] or "").strip()
        if content:
            print(f"  {content[:600]}{'...' if len(content) > 600 else ''}")

        if r["tool_calls"]:
            try:
                tcs = json.loads(r["tool_calls"]) if isinstance(r["tool_calls"], str) else r["tool_calls"]
                for tc in (tcs or []):
                    name = tc.get("name", "?")
                    args = tc.get("args", {})
                    print(f"  TOOL_CALL: {name}")
                    print(f"    args: {json.dumps(args, ensure_ascii=False, default=str)[:200]}")
            except Exception:
                pass

        if r["usage"]:
            try:
                usage = json.loads(r["usage"]) if isinstance(r["usage"], str) else r["usage"]
                tokens = f"in={usage.get('input_tokens', 0)} out={usage.get('output_tokens', 0)}"
                print(f"  usage: {tokens}")
            except Exception:
                pass
        print()

    conn.close()


# ─── checkpoint messages (LangGraph, full detail) ────────────────────────────

def query_messages(session_id: str):
    async def _load():
        import aiosqlite
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        conn = await aiosqlite.connect(str(CHECKPOINT_DB))
        saver = AsyncSqliteSaver(conn)

        config = {"configurable": {"thread_id": session_id}}
        checkpoint_tuple = await saver.aget_tuple(config)

        if not checkpoint_tuple:
            print(f"No checkpoint for session: {session_id}")
            await conn.close()
            return

        checkpoint = checkpoint_tuple.checkpoint
        messages = checkpoint.get("channel_values", {}).get("messages", [])
        print(f"\n=== Checkpoint Messages ({len(messages)}) for {session_id} ===\n")

        for msg in messages:
            msg_type = getattr(msg, "type", "?")
            content = getattr(msg, "content", "")
            tool_calls = getattr(msg, "tool_calls", [])
            kwargs = getattr(msg, "additional_kwargs", {})

            icon = {"human": "USER", "ai": "AI", "system": "SYS", "tool": "TOOL"}.get(msg_type, msg_type)
            print(f"[{icon}]")
            if content:
                print(f"  {str(content)[:800]}")
            if tool_calls:
                for tc in tool_calls:
                    name = tc.get("name", "?") if isinstance(tc, dict) else getattr(tc, "name", "?")
                    args = tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {})
                    print(f"  TOOL_CALL: {name}")
                    print(f"    args: {json.dumps(args, ensure_ascii=False, default=str)[:200]}")
            if kwargs:
                print(f"  kwargs: {json.dumps(kwargs, ensure_ascii=False, default=str)[:300]}")
            print()

        await conn.close()

    asyncio.run(_load())


def query_tools_used(session_id: str):
    async def _load():
        import aiosqlite
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        conn = await aiosqlite.connect(str(CHECKPOINT_DB))
        saver = AsyncSqliteSaver(conn)

        config = {"configurable": {"thread_id": session_id}}
        checkpoint_tuple = await saver.aget_tuple(config)

        if not checkpoint_tuple:
            print(f"No checkpoint for session: {session_id}")
            await conn.close()
            return

        messages = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])
        tool_calls = []
        tool_results = []

        for msg in messages:
            if getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    name = tc.get("name", "?") if isinstance(tc, dict) else getattr(tc, "name", "?")
                    args = tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {})
                    tool_calls.append({"name": name, "args": args})
            if getattr(msg, "type", "") == "tool":
                tool_results.append({
                    "name": getattr(msg, "name", "?"),
                    "content": str(getattr(msg, "content", ""))[:200],
                })

        if tool_calls:
            print(f"\n=== Tool Calls ({len(tool_calls)}) ===\n")
            for tc in tool_calls:
                print(f"  -> {tc['name']}")
                print(f"     args: {json.dumps(tc['args'], ensure_ascii=False, default=str)[:200]}")
        if tool_results:
            print(f"\n=== Tool Results ({len(tool_results)}) ===\n")
            for tr in tool_results:
                print(f"  <- {tr['name']}: {tr['content'][:150]}")
        if not tool_calls and not tool_results:
            print("No tool calls in this session")

        await conn.close()

    asyncio.run(_load())


# ─── runtime state ───────────────────────────────────────────────────────────

def show_runtime_state():
    try:
        resp = urllib.request.urlopen(f"{API_BASE}/mcp")
        mcp = json.loads(resp.read())
        print("=== MCP Servers ===")
        for s in mcp:
            status_icon = {"connected": "v", "error": "x", "disabled": "-", "disconnected": "?"}.get(s["status"], "?")
            print(f"  [{status_icon}] {s['name']}: enabled={s['enabled']}, status={s['status']}, tools={len(s['tools'])}")

        resp = urllib.request.urlopen(f"{API_BASE}/tools/groups")
        groups = json.loads(resp.read())
        print("\n=== Tool Groups ===")
        for g in groups:
            icon = "v" if g["enabled"] else "-"
            print(f"  [{icon}] {g['id']} ({g['description']}): {len(g['tools'])} tools")
    except Exception as e:
        print(f"ERROR connecting to API: {e}")
        print("Is the server running on http://127.0.0.1:8001?")


# ─── main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Query bfzs session data")
    parser.add_argument("session_id", nargs="?", help="Session/thread ID to query")
    parser.add_argument("--presets", action="store_true", help="List agent presets (all fields)")
    parser.add_argument("--sessions", action="store_true", help="List recent sessions")
    parser.add_argument("--users", action="store_true", help="List users and their agent access")
    parser.add_argument("--msgs", action="store_true", help="Show UI messages from chat_ui_messages (fast)")
    parser.add_argument("--tools", action="store_true", help="Show tool calls for session (from checkpoint)")
    parser.add_argument("--state", action="store_true", help="Show runtime MCP/tool state via API")
    parser.add_argument("--last", action="store_true", help="Use the most recent session")
    parser.add_argument("--limit", type=int, default=10, help="Limit for --sessions (default: 10)")
    parser.add_argument("--search", type=str, default=None, help="Search sessions by title keyword")
    args = parser.parse_args()

    if args.last:
        session_id = get_last_session_id()
        print(f"[--last] Using session: {session_id}")
        if args.tools:
            query_tools_used(session_id)
        elif args.msgs:
            query_ui_messages(session_id)
        else:
            query_messages(session_id)
        return

    if args.presets:
        list_presets()
    elif args.sessions:
        list_sessions(args.limit, args.search)
    elif args.users:
        list_users()
    elif args.state:
        show_runtime_state()
    elif args.session_id:
        if args.tools:
            query_tools_used(args.session_id)
        elif args.msgs:
            query_ui_messages(args.session_id)
        else:
            query_messages(args.session_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
