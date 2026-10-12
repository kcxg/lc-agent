"""ChatOpenAI subclass that extracts reasoning_content from streaming deltas.

ChatOpenAI only supports official OpenAI API fields. Many providers (DeepSeek,
GLM, etc.) return a non-standard ``reasoning_content`` field in the streaming
delta for chain-of-thought / thinking content. This subclass captures it into
``additional_kwargs["reasoning_content"]`` so downstream handlers can display it.

For models that embed reasoning inside ``<think>...</think>`` tags within the
regular content stream (e.g. MiniMax-M3), those tags are detected, stripped,
and the enclosed text is likewise moved to ``reasoning_content``.

It also re-injects ``reasoning_content`` into outbound request payloads so
providers that require it (DeepSeek V4 thinking mode) do not reject follow-up
messages with HTTP 400.
"""


import contextvars
from collections.abc import AsyncIterator, Iterator
from typing import Any, ClassVar

from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.outputs import ChatGenerationChunk
from langchain_openai import ChatOpenAI

_THINK_OPEN = "<think>"
_THINK_CLOSE = "</think>"


class ChatOpenAIReasoning(ChatOpenAI):
    """ChatOpenAI with reasoning_content extraction from streaming deltas.

    Drop-in replacement for ChatOpenAI. Works with any provider that returns
    ``reasoning_content`` or ``reasoning`` in the streaming delta dict (e.g.
    DeepSeek, GLM with thinking mode, OpenRouter).

    Also detects ``<think>...</think>`` tags in the content stream and moves
    the enclosed text to ``additional_kwargs["reasoning_content"]``.
    """

    _think_mode: ClassVar[contextvars.ContextVar[bool]] = contextvars.ContextVar(
        "ChatOpenAIReasoning__think_mode", default=False,
    )

    # 同一条流里上一份 usage 的身份，用于丢弃重复下发的 usage。
    _last_usage_key: ClassVar[contextvars.ContextVar[tuple[int, int, int] | None]] = (
        contextvars.ContextVar("ChatOpenAIReasoning__last_usage_key", default=None)
    )

    def _stream(self, *args: Any, **kwargs: Any) -> Iterator[ChatGenerationChunk]:
        token = self._last_usage_key.set(None)
        try:
            yield from super()._stream(*args, **kwargs)
        finally:
            self._last_usage_key.reset(token)

    async def _astream(
        self, *args: Any, **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        token = self._last_usage_key.set(None)
        try:
            async for chunk in super()._astream(*args, **kwargs):
                yield chunk
        finally:
            self._last_usage_key.reset(token)

    def _get_request_payload(
        self,
        input_: Any,
        *,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> dict:
        messages = self._convert_input(input_).to_messages()

        reasoning_by_assistant_idx: list[str | None] = []
        for msg in messages:
            if isinstance(msg, AIMessage):
                reasoning_by_assistant_idx.append(
                    msg.additional_kwargs.get("reasoning_content")
                )

        payload = super()._get_request_payload(input_, stop=stop, **kwargs)

        if any(reasoning_by_assistant_idx) and "messages" in payload:
            ai_counter = 0
            for msg_dict in payload["messages"]:
                if msg_dict.get("role") == "assistant":
                    if (
                        ai_counter < len(reasoning_by_assistant_idx)
                        and reasoning_by_assistant_idx[ai_counter]
                    ):
                        msg_dict["reasoning_content"] = reasoning_by_assistant_idx[ai_counter]
                    ai_counter += 1
        return payload

    def _dedupe_stream_usage(self, generation_chunk: ChatGenerationChunk) -> None:
        """丢弃同一条流里重复下发的 usage。

        部分 OpenAI 兼容网关会把整份 usage 在多个分片里各发一遍，而 OpenAI 规范要求
        usage 只在最后一个分片出现一次。LangChain 合并流式分片时会累加 usage_metadata，
        重复下发会直接让上报用量翻倍。这里以 (输入, 输出, 总计) 作为同一份 usage 的身份，
        一条流内只保留第一份。
        """
        message = generation_chunk.message
        if not isinstance(message, AIMessageChunk) or not message.usage_metadata:
            return
        usage = message.usage_metadata
        key = (
            int(usage.get("input_tokens") or 0),
            int(usage.get("output_tokens") or 0),
            int(usage.get("total_tokens") or 0),
        )
        if self._last_usage_key.get() == key:
            message.usage_metadata = None
        else:
            self._last_usage_key.set(key)

    def _convert_chunk_to_generation_chunk(
        self,
        chunk: dict,
        default_chunk_class: type,
        base_generation_info: dict | None,
    ) -> ChatGenerationChunk | None:
        generation_chunk = super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info,
        )
        if generation_chunk is None:
            return None

        self._dedupe_stream_usage(generation_chunk)

        choices = chunk.get("choices") or chunk.get("chunk", {}).get("choices") or []
        if not choices:
            return generation_chunk

        delta = choices[0].get("delta") or {}
        if isinstance(generation_chunk.message, AIMessageChunk):
            reasoning = delta.get("reasoning_content")
            if reasoning is None:
                reasoning = delta.get("reasoning")
            if reasoning is not None:
                generation_chunk.message.additional_kwargs["reasoning_content"] = reasoning
            else:
                self._extract_think_tags(generation_chunk.message)

        return generation_chunk

    # ------------------------------------------------------------------
    # <think> tag extraction
    # ------------------------------------------------------------------

    def _extract_think_tags(self, message: AIMessageChunk) -> None:
        """Move ``<think>...</think>`` content to ``reasoning_content``."""
        content = message.content
        if not isinstance(content, str) or not content:
            return

        in_think = self._think_mode.get()

        if not in_think:
            idx = content.find(_THINK_OPEN)
            if idx == -1:
                return
            before = content[:idx]
            after = content[idx + len(_THINK_OPEN):]

            end_idx = after.find(_THINK_CLOSE)
            if end_idx != -1:
                reasoning_text = after[:end_idx]
                rest = after[end_idx + len(_THINK_CLOSE):]
                message.content = before + rest
                if reasoning_text:
                    message.additional_kwargs["reasoning_content"] = reasoning_text
            else:
                self._think_mode.set(True)
                message.content = before
                if after:
                    message.additional_kwargs["reasoning_content"] = after
        else:
            end_idx = content.find(_THINK_CLOSE)
            if end_idx != -1:
                reasoning_text = content[:end_idx]
                rest = content[end_idx + len(_THINK_CLOSE):]
                self._think_mode.set(False)
                message.content = rest
                if reasoning_text:
                    message.additional_kwargs["reasoning_content"] = reasoning_text
            else:
                message.additional_kwargs["reasoning_content"] = content
                message.content = ""
