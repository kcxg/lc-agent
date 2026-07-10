
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Any

import aiosqlite
import httpx
from langchain.tools import ToolRuntime
from langchain_core.tools import StructuredTool
from langchain_core.tools.base import InjectedToolArg
from langgraph.store.base import IndexConfig
from langgraph.store.sqlite.aio import AsyncSqliteStore
from pydantic import BaseModel, ConfigDict, Field


DEFAULT_MEMORY_NAMESPACE = ("lc-agent", "memories")

MEMORY_SYSTEM_PROMPT = """You may use the memory tools to store and retrieve durable user memories.
Only save stable, user-relevant preferences or facts when the user explicitly asks you to remember them
or when a memory is clearly useful for future conversations. Keep memory keys short and specific."""


@dataclass(frozen=True)
class AgentRuntimeContext:
    user_id: str


def normalize_memory_user_id(user_id: str | None) -> str:
    normalized = (user_id or "anonymous").strip()
    return normalized or "anonymous"


def memory_namespace(
    user_id: str | None,
    base_namespace: tuple[str, ...] = DEFAULT_MEMORY_NAMESPACE,
) -> tuple[str, ...]:
    return (*base_namespace, normalize_memory_user_id(user_id))


class OpenAICompatibleEmbeddings:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 60.0,
    ) -> None:
        if not api_key:
            raise ValueError("memory semantic_search.api_key is required when semantic search is enabled")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._aembed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]

    async def aembed_query(self, text: str) -> list[float]:
        return (await self._aembed([text]))[0]

    def __call__(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed(list(texts))

    async def _acall(self, texts: Sequence[str]) -> list[list[float]]:
        return await self._aembed(list(texts))

    def _payload(self, texts: list[str]) -> dict[str, Any]:
        return {
            "model": self.model,
            "input": texts,
            "encoding_format": "float",
        }

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _embed(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            f"{self.base_url}/embeddings",
            json=self._payload(texts),
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return _extract_embeddings(response.json())

    async def _aembed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                json=self._payload(texts),
                headers=self._headers(),
            )
            response.raise_for_status()
            return _extract_embeddings(response.json())


def _extract_embeddings(payload: dict[str, Any]) -> list[list[float]]:
    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("Embedding response missing data list")
    return [item["embedding"] for item in data]


def _get_config_value(config: Any, name: str, default: Any = None) -> Any:
    if config is None:
        return default
    if isinstance(config, dict):
        return config.get(name, default)
    return getattr(config, name, default)


def build_store_index(memory_config: Any) -> IndexConfig | None:
    semantic = _get_config_value(memory_config, "semantic_search")
    if semantic is None or not _get_config_value(semantic, "enabled", False):
        return None

    api_key = _get_config_value(semantic, "api_key", "")
    if not api_key:
        raise ValueError("memory.semantic_search.api_key is required when semantic search is enabled")

    embeddings = OpenAICompatibleEmbeddings(
        api_key=api_key,
        base_url=_get_config_value(semantic, "base_url", ""),
        model=_get_config_value(semantic, "model", ""),
    )
    return IndexConfig(
        embed=embeddings,
        dims=int(_get_config_value(semantic, "dims", 0)),
        fields=["content"],
    )


async def create_sqlite_memory_store(
    path: str,
    memory_config: Any | None = None,
) -> AsyncSqliteStore:
    index = build_store_index(memory_config) if memory_config is not None else None
    conn = await aiosqlite.connect(path, isolation_level=None)
    store = AsyncSqliteStore(conn, index=index)
    await store.setup()
    return store


async def aclose_memory_store(store: AsyncSqliteStore) -> None:
    await store.conn.close()


class _RuntimeArgs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    runtime: Annotated[Any, InjectedToolArg()] = Field(description="Injected LangChain runtime")


class _KeyContentArgs(_RuntimeArgs):
    key: str = Field(description="Memory key")
    content: str = Field(description="Memory content")


class _KeyArgs(_RuntimeArgs):
    key: str = Field(description="Memory key")


class _SearchArgs(_RuntimeArgs):
    query: str = Field(description="Search query")
    limit: int = Field(default=10, description="Maximum number of memories to return")


def _runtime_namespace(runtime: Any, namespace: tuple[str, ...]) -> tuple[str, ...]:
    context = getattr(runtime, "context", None)
    user_id = getattr(context, "user_id", None)
    if isinstance(context, dict):
        user_id = context.get("user_id", user_id)
    return memory_namespace(user_id, namespace)


def _format_memory_item(item: Any) -> str:
    value = getattr(item, "value", None)
    content = value.get("content") if isinstance(value, dict) else value
    key = getattr(item, "key", "")
    return f"{key}: {content}" if key else str(content)


async def _insert_memory(*, key: str, content: str, runtime: Any, namespace: tuple[str, ...]) -> str:
    store = runtime.store
    ns = _runtime_namespace(runtime, namespace)
    existing = await store.aget(ns, key)
    if existing is not None:
        return f"Memory key '{key}' already exists; conflict/duplicate insert ignored."
    await store.aput(ns, key, {"content": content})
    return f"Inserted memory '{key}'."


async def _update_memory(*, key: str, content: str, runtime: Any, namespace: tuple[str, ...]) -> str:
    store = runtime.store
    ns = _runtime_namespace(runtime, namespace)
    existing = await store.aget(ns, key)
    if existing is None:
        return f"Memory key '{key}' is missing/not found; update ignored."
    await store.aput(ns, key, {"content": content})
    return f"Updated memory '{key}'."


async def _get_memory(*, key: str, runtime: Any, namespace: tuple[str, ...]) -> str:
    item = await runtime.store.aget(_runtime_namespace(runtime, namespace), key)
    if item is None:
        return "Memory not found."
    return _format_memory_item(item)


async def _search_memories(
    *,
    query: str,
    runtime: Any,
    namespace: tuple[str, ...],
    limit: int = 10,
) -> str:
    results = await runtime.store.asearch(
        _runtime_namespace(runtime, namespace),
        query=query,
        limit=limit,
    )
    if not results:
        return "No memories found."
    return "\n".join(_format_memory_item(item) for item in results)


async def _list_memories(*, runtime: Any, namespace: tuple[str, ...]) -> str:
    results = await runtime.store.asearch(
        _runtime_namespace(runtime, namespace),
        limit=100,
    )
    if not results:
        return "No memories found."
    return "\n".join(_format_memory_item(item) for item in results)


async def _delete_memory(*, key: str, runtime: Any, namespace: tuple[str, ...]) -> str:
    store = runtime.store
    ns = _runtime_namespace(runtime, namespace)
    existing = await store.aget(ns, key)
    if existing is None:
        return f"Memory key '{key}' not found."
    await store.adelete(ns, key)
    return f"Deleted memory '{key}'."


def _tool_from_coroutine(
    *,
    name: str,
    description: str,
    args_schema: type[BaseModel],
    coroutine: Any,
) -> StructuredTool:
    return StructuredTool.from_function(
        func=None,
        coroutine=coroutine,
        name=name,
        description=description,
        args_schema=args_schema,
    )


def build_memory_tools(
    namespace: tuple[str, ...] = DEFAULT_MEMORY_NAMESPACE,
) -> list[StructuredTool]:
    async def insert_memory(key: str, content: str, runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str:
        return await _insert_memory(key=key, content=content, runtime=runtime, namespace=namespace)

    async def update_memory(key: str, content: str, runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str:
        return await _update_memory(key=key, content=content, runtime=runtime, namespace=namespace)

    async def get_memory(key: str, runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str:
        return await _get_memory(key=key, runtime=runtime, namespace=namespace)

    async def search_memories(
        query: str,
        runtime: ToolRuntime[AgentRuntimeContext, Any],
        limit: int = 10,
    ) -> str:
        return await _search_memories(query=query, runtime=runtime, namespace=namespace, limit=limit)

    async def list_memories(runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str:
        return await _list_memories(runtime=runtime, namespace=namespace)

    async def delete_memory(key: str, runtime: ToolRuntime[AgentRuntimeContext, Any]) -> str:
        return await _delete_memory(key=key, runtime=runtime, namespace=namespace)

    return [
        _tool_from_coroutine(
            name="memory__insert_memory",
            description="Insert a new durable memory for the current user. Fails if the key already exists.",
            args_schema=_KeyContentArgs,
            coroutine=insert_memory,
        ),
        _tool_from_coroutine(
            name="memory__update_memory",
            description="Update an existing durable memory for the current user. Fails if the key is missing.",
            args_schema=_KeyContentArgs,
            coroutine=update_memory,
        ),
        _tool_from_coroutine(
            name="memory__get_memory",
            description="Get one durable memory by key for the current user.",
            args_schema=_KeyArgs,
            coroutine=get_memory,
        ),
        _tool_from_coroutine(
            name="memory__search_memories",
            description="Search durable memories for the current user.",
            args_schema=_SearchArgs,
            coroutine=search_memories,
        ),
        _tool_from_coroutine(
            name="memory__list_memories",
            description="List durable memories for the current user.",
            args_schema=_RuntimeArgs,
            coroutine=list_memories,
        ),
        _tool_from_coroutine(
            name="memory__delete_memory",
            description="Delete one durable memory by key for the current user.",
            args_schema=_KeyArgs,
            coroutine=delete_memory,
        ),
    ]
