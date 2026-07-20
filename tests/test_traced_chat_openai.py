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


def test_chat_openai_reasoning_default_params_restore_legacy_max_tokens_only():
    """非 OpenAI 兼容端点不能同时收到两个 token 上限字段。"""
    from lc_agent.core.chat_model import ChatOpenAIReasoning

    llm = ChatOpenAIReasoning(model="test-model", api_key="test-key", max_tokens=123)

    assert llm._default_params["max_tokens"] == 123
    assert "max_completion_tokens" not in llm._default_params


def test_chat_openai_reasoning_request_payload_restores_legacy_max_tokens_only():
    """实际请求载荷同样必须移除 OpenAI 专用字段，避免 API 400。"""
    from lc_agent.core.chat_model import ChatOpenAIReasoning

    llm = ChatOpenAIReasoning(model="test-model", api_key="test-key", max_tokens=123)
    payload = llm._get_request_payload("hello")

    assert payload["max_tokens"] == 123
    assert "max_completion_tokens" not in payload
