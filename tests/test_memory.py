import pytest


class FakeRuntime:
    def __init__(self, store):
        self.store = store


@pytest.mark.asyncio
async def test_sqlite_memory_store_persists_across_connections(tmp_path):
    from lc_agent.core.memory import create_sqlite_memory_store

    memory_path = tmp_path / "memory.db"

    first = await create_sqlite_memory_store(str(memory_path))
    await first.aput(("lc-agent", "memories"), "favorite", {"content": "用户喜欢 SQLite 持久化记忆"})
    await first.conn.close()

    second = await create_sqlite_memory_store(str(memory_path))
    item = await second.aget(("lc-agent", "memories"), "favorite")
    await second.conn.close()

    assert item is not None
    assert item.value == {"content": "用户喜欢 SQLite 持久化记忆"}


@pytest.mark.asyncio
async def test_memory_tools_use_runtime_store():
    from langgraph.store.memory import InMemoryStore

    from lc_agent.core.memory import build_memory_tools

    store = InMemoryStore()
    runtime = FakeRuntime(store)
    tools = {tool.name: tool for tool in build_memory_tools(namespace=("lc-agent", "memories"))}

    saved = await tools["memory__save_memory"].ainvoke(
        {"key": "style", "content": "用户喜欢直接的回答", "runtime": runtime}
    )
    found = await tools["memory__search_memories"].ainvoke({"query": "回答风格", "runtime": runtime})
    deleted = await tools["memory__delete_memory"].ainvoke({"key": "style", "runtime": runtime})
    found_after_delete = await tools["memory__search_memories"].ainvoke({"query": "回答风格", "runtime": runtime})

    assert "已保存" in saved
    assert "style" in found
    assert "用户喜欢直接的回答" in found
    assert "已删除" in deleted
    assert "没有找到" in found_after_delete
