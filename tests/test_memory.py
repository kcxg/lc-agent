import pytest


EXPECTED_MEMORY_TOOL_NAMES = {
    "memory__insert_memory",
    "memory__update_memory",
    "memory__get_memory",
    "memory__search_memories",
    "memory__list_memories",
    "memory__delete_memory",
}
MEMORY_NAMESPACE = ("lc-agent", "memories")


class FakeRuntime:
    def __init__(self, store, context):
        self.store = store
        self.context = context


def user_memory_namespace(user_id: str) -> tuple[str, str, str]:
    return (*MEMORY_NAMESPACE, user_id)


async def get_stored_memory(store, user_id: str, key: str):
    return await store.aget(user_memory_namespace(user_id), key)


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

    from lc_agent.core.memory import AgentRuntimeContext, build_memory_tools

    store = InMemoryStore()
    runtime = FakeRuntime(store, AgentRuntimeContext(user_id="user-123"))
    tools = {tool.name: tool for tool in build_memory_tools(namespace=MEMORY_NAMESPACE)}

    assert EXPECTED_MEMORY_TOOL_NAMES == set(tools)

    await tools["memory__insert_memory"].ainvoke(
        {"key": "style", "content": "用户喜欢直接的回答", "runtime": runtime}
    )
    stored = await get_stored_memory(store, "user-123", "style")
    listed = await tools["memory__list_memories"].ainvoke({"runtime": runtime})
    found = await tools["memory__search_memories"].ainvoke(
        {"query": "回答风格", "runtime": runtime}
    )
    await tools["memory__update_memory"].ainvoke(
        {"key": "style", "content": "用户喜欢简洁直接的回答", "runtime": runtime}
    )
    stored_after_update = await get_stored_memory(store, "user-123", "style")
    await tools["memory__delete_memory"].ainvoke({"key": "style", "runtime": runtime})
    stored_after_delete = await get_stored_memory(store, "user-123", "style")
    found_after_delete = await tools["memory__search_memories"].ainvoke(
        {"query": "回答风格", "runtime": runtime}
    )

    assert stored is not None
    assert stored.value == {"content": "用户喜欢直接的回答"}
    assert "style" in listed
    assert "style" in found
    assert "用户喜欢直接的回答" in found
    assert stored_after_update is not None
    assert stored_after_update.value == {"content": "用户喜欢简洁直接的回答"}
    assert stored_after_delete is None
    assert "style" not in found_after_delete


def test_memory_tools_do_not_expose_runtime_argument():
    from lc_agent.core.memory import build_memory_tools

    for tool in build_memory_tools(namespace=MEMORY_NAMESPACE):
        assert "runtime" not in tool.args


def test_memory_store_index_targets_content_field():
    from lc_agent.core.memory import OpenAICompatibleEmbeddings, build_store_index

    index = build_store_index(
        {
            "semantic_search": {
                "enabled": True,
                "api_key": "test-key",
                "base_url": "https://embeddings.example/v1",
                "model": "test-embedding-model",
                "dims": 1024,
            }
        }
    )

    assert index is not None
    assert index["fields"] == ["content"]
    assert "text_fields" not in index
    assert index["dims"] == 1024
    assert isinstance(index["embed"], OpenAICompatibleEmbeddings)


@pytest.mark.asyncio
async def test_memory_insert_does_not_overwrite_existing_key_for_same_user():
    from langgraph.store.memory import InMemoryStore

    from lc_agent.core.memory import AgentRuntimeContext, build_memory_tools

    store = InMemoryStore()
    runtime = FakeRuntime(store, AgentRuntimeContext(user_id="user-123"))
    tools = {tool.name: tool for tool in build_memory_tools(namespace=MEMORY_NAMESPACE)}

    await tools["memory__insert_memory"].ainvoke(
        {"key": "style", "content": "原始记忆：用户喜欢直接的回答", "runtime": runtime}
    )
    duplicate_insert = await tools["memory__insert_memory"].ainvoke(
        {"key": "style", "content": "覆盖尝试：用户喜欢冗长回答", "runtime": runtime}
    )
    stored = await get_stored_memory(store, "user-123", "style")

    assert stored is not None
    assert stored.value == {"content": "原始记忆：用户喜欢直接的回答"}
    assert "覆盖尝试：用户喜欢冗长回答" not in str(stored.value)
    assert any(token in duplicate_insert.lower() for token in ["exist", "conflict", "duplicate", "已有", "已存在"])


@pytest.mark.asyncio
async def test_memory_update_does_not_create_missing_key_for_same_user():
    from langgraph.store.memory import InMemoryStore

    from lc_agent.core.memory import AgentRuntimeContext, build_memory_tools

    store = InMemoryStore()
    runtime = FakeRuntime(store, AgentRuntimeContext(user_id="user-123"))
    tools = {tool.name: tool for tool in build_memory_tools(namespace=MEMORY_NAMESPACE)}

    update_result = await tools["memory__update_memory"].ainvoke(
        {"key": "missing", "content": "不应通过 update 新建", "runtime": runtime}
    )
    stored = await get_stored_memory(store, "user-123", "missing")
    listed = await tools["memory__list_memories"].ainvoke({"runtime": runtime})
    found = await tools["memory__search_memories"].ainvoke(
        {"query": "不应通过 update 新建", "runtime": runtime}
    )

    assert stored is None
    assert "missing" not in listed
    assert "不应通过 update 新建" not in found
    assert any(token in update_result.lower() for token in ["missing", "not found", "不存在", "未找到"])


@pytest.mark.asyncio
async def test_memory_tools_isolate_memories_by_user():
    from langgraph.store.memory import InMemoryStore

    from lc_agent.core.memory import AgentRuntimeContext, build_memory_tools

    store = InMemoryStore()
    tools = {tool.name: tool for tool in build_memory_tools(namespace=MEMORY_NAMESPACE)}
    user_a_runtime = FakeRuntime(store, AgentRuntimeContext(user_id="user-a"))
    user_b_runtime = FakeRuntime(store, AgentRuntimeContext(user_id="user-b"))

    await tools["memory__insert_memory"].ainvoke(
        {"key": "favorite", "content": "用户 A 喜欢 SQLite", "runtime": user_a_runtime}
    )
    await tools["memory__insert_memory"].ainvoke(
        {"key": "favorite", "content": "用户 B 喜欢 Postgres", "runtime": user_b_runtime}
    )

    user_a_memory = await tools["memory__get_memory"].ainvoke(
        {"key": "favorite", "runtime": user_a_runtime}
    )
    user_b_memory = await tools["memory__get_memory"].ainvoke(
        {"key": "favorite", "runtime": user_b_runtime}
    )
    namespaces = await store.alist_namespaces()
    user_a_stored = await get_stored_memory(store, "user-a", "favorite")
    user_b_stored = await get_stored_memory(store, "user-b", "favorite")
    user_a_list = await tools["memory__list_memories"].ainvoke({"runtime": user_a_runtime})
    user_b_list = await tools["memory__list_memories"].ainvoke({"runtime": user_b_runtime})
    user_a_search = await tools["memory__search_memories"].ainvoke(
        {"query": "Postgres", "runtime": user_a_runtime}
    )
    user_b_search = await tools["memory__search_memories"].ainvoke(
        {"query": "SQLite", "runtime": user_b_runtime}
    )
    user_a_delete = await tools["memory__delete_memory"].ainvoke(
        {"key": "favorite", "runtime": user_a_runtime}
    )
    user_a_after_delete = await tools["memory__get_memory"].ainvoke(
        {"key": "favorite", "runtime": user_a_runtime}
    )
    user_b_after_user_a_delete = await tools["memory__get_memory"].ainvoke(
        {"key": "favorite", "runtime": user_b_runtime}
    )
    user_a_stored_after_delete = await get_stored_memory(store, "user-a", "favorite")
    user_b_stored_after_user_a_delete = await get_stored_memory(store, "user-b", "favorite")

    assert user_memory_namespace("user-a") in namespaces
    assert user_memory_namespace("user-b") in namespaces
    assert user_a_stored is not None
    assert user_a_stored.value == {"content": "用户 A 喜欢 SQLite"}
    assert user_b_stored is not None
    assert user_b_stored.value == {"content": "用户 B 喜欢 Postgres"}
    assert "用户 A 喜欢 SQLite" in user_a_memory
    assert "用户 B 喜欢 Postgres" in user_b_memory
    assert "用户 B 喜欢 Postgres" not in user_a_memory
    assert "用户 A 喜欢 SQLite" not in user_b_memory
    assert "用户 A 喜欢 SQLite" in user_a_list
    assert "用户 B 喜欢 Postgres" not in user_a_list
    assert "用户 B 喜欢 Postgres" in user_b_list
    assert "用户 A 喜欢 SQLite" not in user_b_list
    assert "用户 B 喜欢 Postgres" not in user_a_search
    assert "用户 A 喜欢 SQLite" not in user_b_search
    assert "favorite" not in user_a_after_delete
    assert user_a_stored_after_delete is None
    assert user_b_stored_after_user_a_delete is not None
    assert user_b_stored_after_user_a_delete.value == {"content": "用户 B 喜欢 Postgres"}
    assert "用户 B 喜欢 Postgres" in user_b_after_user_a_delete
    assert "favorite" in user_a_delete
