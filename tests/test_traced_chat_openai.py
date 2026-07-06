from __future__ import annotations


def test_create_traced_chat_openai_returns_reasoning_model_with_http_tracing():
    from lc_agent import create_traced_chat_openai
    from lc_agent.core.chat_model import ChatOpenAIReasoning
    from lc_agent.core.http_trace_httpx import TracingAsyncClient

    llm = create_traced_chat_openai(
        provider="litellm",
        model="go-deepseek-v4-flash",
        base_url="http://localhost:4000/v1",
        api_key="not_need_key_because_litellm",
        temperature=0.3,
        max_tokens=123,
    )

    assert isinstance(llm, ChatOpenAIReasoning)
    assert llm.model_name == "go-deepseek-v4-flash"
    assert llm.temperature == 0.3
    assert llm.max_tokens == 123
    assert llm.stream_usage is True

    assert isinstance(llm.http_async_client, TracingAsyncClient)
    assert llm.http_async_client.provider == "litellm"
    assert llm.http_async_client.model == "go-deepseek-v4-flash"
    assert str(llm.http_async_client.base_url) == "http://localhost:4000/v1/"


def test_create_traced_chat_openai_defaults_to_openai_base_url_for_trace_metadata():
    from lc_agent import create_traced_chat_openai

    llm = create_traced_chat_openai(
        model="gpt-5-mini",
        api_key="test-key",
    )

    assert str(llm.http_async_client.base_url) == "https://api.openai.com/v1/"
    assert llm.http_async_client.provider is None
    assert llm.http_async_client.model == "gpt-5-mini"
