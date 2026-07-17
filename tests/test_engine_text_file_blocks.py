from lc_agent.core.engine import _convert_history_item, _convert_text_file_blocks


def test_convert_text_file_block_to_text():
    content = [
        {"type": "text", "text": "请检查这个文件"},
        {"type": "text_file", "name": "foo.py", "textContent": "print('hello')", "lang": "python"},
    ]
    result = _convert_text_file_blocks(content)
    assert len(result) == 2
    assert result[0] == {"type": "text", "text": "请检查这个文件"}
    assert result[1]["type"] == "text"
    assert result[1]["text"] == "📎 `foo.py`:\n```python\nprint('hello')\n```"


def test_convert_passes_through_text_and_image_blocks():
    content = [
        {"type": "text", "text": "hello"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}},
    ]
    result = _convert_text_file_blocks(content)
    assert result == content


def test_convert_text_file_block_empty_content():
    content = [{"type": "text_file", "name": "empty.txt", "textContent": "", "lang": ""}]
    result = _convert_text_file_blocks(content)
    assert result == [{"type": "text", "text": "📎 `empty.txt`:\n```\n\n```"}]


def test_convert_text_file_block_missing_fields():
    content = [{"type": "text_file"}]
    result = _convert_text_file_blocks(content)
    assert result == [{"type": "text", "text": "📎 ``:\n```\n\n```"}]


def test_convert_empty_list():
    assert _convert_text_file_blocks([]) == []


def test_convert_history_item_with_list_content():
    item = {
        "role": "user",
        "content": [
            {"type": "text", "text": "hi"},
            {"type": "text_file", "name": "a.py", "textContent": "x=1", "lang": "python"},
        ],
    }
    result = _convert_history_item(item)
    assert result["role"] == "user"
    assert result["content"][0] == {"type": "text", "text": "hi"}
    assert result["content"][1]["type"] == "text"
    assert "📎 `a.py`" in result["content"][1]["text"]


def test_convert_history_item_with_string_content():
    item = {"role": "assistant", "content": "hello world"}
    result = _convert_history_item(item)
    assert result == item


def test_convert_history_item_does_not_mutate_original():
    original = {"role": "user", "content": [{"type": "text_file", "name": "x.py", "textContent": "y", "lang": "python"}]}
    _convert_history_item(original)
    assert original["content"][0]["type"] == "text_file"


async def test_chat_stream_converts_text_file_blocks(sample_config, monkeypatch):
    from lc_agent.core.engine import AgentEngine

    captured = {}
    engine = AgentEngine(sample_config)

    class FakeAgent:
        async def astream_events(self, payload, **kwargs):
            captured["payload"] = payload
            captured["kwargs"] = kwargs
            if False:
                yield {}

    monkeypatch.setattr(engine, "_get_or_build_agent", lambda *args, **kwargs: FakeAgent())

    message = [
        {"type": "text", "text": "看下这个文件"},
        {"type": "text_file", "name": "foo.py", "textContent": "print('hi')", "lang": "python"},
    ]
    history = [
        {
            "role": "user",
            "content": [{"type": "text_file", "name": "old.py", "textContent": "x=1", "lang": "python"}],
        }
    ]

    events = [event async for event in engine.chat_stream(message, "thread-1", history=history)]

    assert events == []
    messages = captured["payload"]["messages"]
    history_blocks = messages[0]["content"]
    user_blocks = messages[-1]["content"]
    assert all(block["type"] != "text_file" for block in history_blocks)
    assert all(block["type"] != "text_file" for block in user_blocks)
    assert history_blocks[0]["text"] == "📎 `old.py`:\n```python\nx=1\n```"
    assert user_blocks[0] == {"type": "text", "text": "看下这个文件"}
    assert user_blocks[1]["text"] == "📎 `foo.py`:\n```python\nprint('hi')\n```"
