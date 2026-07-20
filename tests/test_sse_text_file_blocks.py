from lc_agent.server.sse import _extract_text_from_blocks


def test_extract_text_from_plain_text_block():
    content = [{"type": "text", "text": "你好"}]
    assert _extract_text_from_blocks(content) == "你好"


def test_extract_text_from_text_file_block_returns_filename():
    content = [{"type": "text_file", "name": "foo.py", "textContent": "print('hello')", "lang": "python"}]
    assert _extract_text_from_blocks(content) == "foo.py"


def test_extract_text_mixed_blocks():
    content = [
        {"type": "text", "text": "请检查"},
        {"type": "text_file", "name": "foo.py", "textContent": "x=1", "lang": "python"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}},
    ]
    result = _extract_text_from_blocks(content)
    assert "请检查" in result
    assert "foo.py" in result
    assert "x=1" not in result


def test_extract_text_empty_content():
    assert _extract_text_from_blocks([]) == ""


def test_extract_text_file_block_missing_name():
    content = [{"type": "text_file", "textContent": "x=1", "lang": "python"}]
    assert _extract_text_from_blocks(content) == ""
