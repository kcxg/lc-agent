"""回归测试：ChatOpenAIReasoning 对「同一条流里重复下发的 usage」做幂等去重。

背景：部分 OpenAI 兼容网关会把整份 usage 在多个流式分片里各发一遍（OpenAI 规范要求
usage 只在最后一个分片出现一次）。LangChain 合并分片时对 usage_metadata 做的是累加
（langchain_core.messages.ai.add_usage），重复下发会让上报用量直接翻倍。

覆盖：
- 重复 usage 只算一次；
- usage 值不同时保持原有累加行为不变；
- 普通「内容分片 + usage 分片」不受影响；
- 两条流之间互相隔离（新流不会被上一条流的 usage 影响）。

不依赖网络：直接喂构造好的分片字典。
"""

from langchain_core.messages import AIMessageChunk

from langchain_openai.chat_models.base import BaseChatOpenAI

from lc_agent.core.chat_model import ChatOpenAIReasoning


def _make_model() -> ChatOpenAIReasoning:
    return ChatOpenAIReasoning(model="gpt-4o", api_key="not-set", base_url="http://localhost")


def _usage_chunk(prompt: int, completion: int) -> dict:
    return {
        "choices": [],
        "usage": {
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": prompt + completion,
        },
    }


def _content_chunk(text: str) -> dict:
    return {
        "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}],
        "usage": None,
    }


def _feed(model: ChatOpenAIReasoning, chunks: list[dict]) -> list:
    out = []
    for chunk in chunks:
        gc = model._convert_chunk_to_generation_chunk(chunk, AIMessageChunk, None)
        if gc is not None:
            out.append(gc)
    return out


def _agg(chunks: list) -> AIMessageChunk:
    total = None
    for gc in chunks:
        total = gc.message if total is None else total + gc.message
    return total


def test_duplicate_usage_counted_once():
    """同一份 usage 发两遍 → 只算一次（修复前会翻倍成 200）。"""
    model = _make_model()
    model._last_usage_key.set(None)

    chunks = _feed(model, [_usage_chunk(100, 5), _usage_chunk(100, 5)])
    assert len(chunks) == 2
    assert chunks[0].message.usage_metadata is not None
    assert chunks[1].message.usage_metadata is None, "重复的 usage 分片应被丢弃"

    usage = _agg(chunks).usage_metadata
    assert usage["input_tokens"] == 100, f"usage 被重复累加：{usage}"
    assert usage["output_tokens"] == 5
    assert usage["total_tokens"] == 105


def test_distinct_usage_keeps_original_accumulation():
    """usage 值不同 → 维持原有累加行为，不误伤。"""
    model = _make_model()
    model._last_usage_key.set(None)

    chunks = _feed(model, [_usage_chunk(100, 5), _usage_chunk(140, 6)])
    assert all(gc.message.usage_metadata is not None for gc in chunks)

    usage = _agg(chunks).usage_metadata
    assert usage["input_tokens"] == 240
    assert usage["output_tokens"] == 11


def test_normal_stream_unaffected():
    """普通流：内容分片 + 一份 usage → 内容与 usage 都正常。"""
    model = _make_model()
    model._last_usage_key.set(None)

    chunks = _feed(model, [_content_chunk("hello"), _content_chunk(" world"), _usage_chunk(100, 2)])
    assert _agg(chunks).content == "hello world"
    assert _agg(chunks).usage_metadata["input_tokens"] == 100


def test_usage_state_resets_between_streams(monkeypatch):
    """两条流之间隔离：新流的第一份 usage 不能被上一条流的状态吃掉。"""
    dup = [_usage_chunk(100, 5), _usage_chunk(100, 5)]

    def fake_stream(self, *args, **kwargs):
        for chunk in dup:
            gc = self._convert_chunk_to_generation_chunk(chunk, AIMessageChunk, None)
            if gc is not None:
                yield gc

    monkeypatch.setattr(BaseChatOpenAI, "_stream", fake_stream)

    model = _make_model()

    first = list(model._stream())
    assert first[0].message.usage_metadata is not None
    assert first[1].message.usage_metadata is None

    second = list(model._stream())
    assert second[0].message.usage_metadata is not None, "新流的第一份 usage 不应被丢弃"
    assert second[1].message.usage_metadata is None
    assert _agg(second).usage_metadata["input_tokens"] == 100


if __name__ == "__main__":
    test_duplicate_usage_counted_once()
    test_distinct_usage_keeps_original_accumulation()
    test_normal_stream_unaffected()

    class _MP:
        @staticmethod
        def setattr(obj, name, value):
            setattr(obj, name, value)

    test_usage_state_resets_between_streams(_MP())
    print("全部通过：重复 usage 只算一次 / 不同 usage 原行为不变 / 普通流不受影响 / 流间隔离")
