from __future__ import annotations

from typing import Any

from lc_agent.core.chat_model import ChatOpenAIReasoning
from lc_agent.core.http_trace import get_http_trace_collector
from lc_agent.core.http_trace_httpx import TracingAsyncClient


def create_traced_openai_http_client(
    *,
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    timeout: float = 120,
    **kwargs: Any,
) -> TracingAsyncClient:
    """Create an OpenAI-compatible async HTTP client with lc-agent tracing enabled."""
    return TracingAsyncClient(
        collector_getter=get_http_trace_collector,
        provider=provider,
        model=model,
        base_url=base_url or "https://api.openai.com/v1",
        timeout=timeout,
        **kwargs,
    )


def create_traced_chat_openai(
    *,
    model: str,
    base_url: str | None = None,
    api_key: str = "not-set",
    provider: str | None = None,
    timeout: float = 120,
    stream_usage: bool = True,
    **kwargs: Any,
) -> ChatOpenAIReasoning:
    """Create a ChatOpenAIReasoning model that records HTTP request/response traces.

    This helper is intended for code-registered agents built with StateGraph,
    langchain.agents.create_agent(model=llm), deepagents, or any other
    LangChain-compatible graph where the application code owns LLM construction.
    """
    return ChatOpenAIReasoning(
        model=model,
        base_url=base_url,
        api_key=api_key,
        stream_usage=stream_usage,
        http_async_client=create_traced_openai_http_client(
            provider=provider,
            model=model,
            base_url=base_url,
            timeout=timeout,
        ),
        **kwargs,
    )
