"""read_file 图片支持：返回标准 content blocks + 图片块的下游脱敏。"""
import base64

import pytest
from langchain_core.messages import ToolMessage
from langchain_core.tools import StructuredTool

from lc_agent.config import set_config
from lc_agent.core.engine_helpers.content_helpers import blocks_to_display_text, has_image_block
from lc_agent.server.stream_utils import _tool_result_display
from lc_agent.tools.system_tools import file_read_tools
from lc_agent.tools.system_tools.file_read_tools import read_file, read_multiple_files

# 1x1 透明 PNG
_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def _make_png(tmp_path, name="pic.png"):
    p = tmp_path / name
    p.write_bytes(_PNG_BYTES)
    return p


def test_read_file_png_returns_image_blocks(tmp_path):
    png = _make_png(tmp_path)

    result = read_file(str(png))

    assert isinstance(result, list)
    assert result[0]["type"] == "text"
    assert png.name in result[0]["text"]
    assert result[1]["type"] == "image"
    assert result[1]["mime_type"] == "image/png"
    assert base64.b64decode(result[1]["base64"]) == _PNG_BYTES


def test_langchain_tool_returns_toolmessage_with_image_block(tmp_path):
    """端到端验证 LangChain 契约：工具返回的 blocks 不被 stringify。

    不依赖全局 ToolRegistry（其它测试会清空它），直接按注册时的同一方式构造。
    """
    png = _make_png(tmp_path)
    tool_obj = StructuredTool.from_function(
        name="file_read__read_file",
        func=file_read_tools.read_file.__wrapped__,
        response_format="content",
    )

    result = tool_obj.invoke(
        {"name": "file_read__read_file", "args": {"path": str(png)}, "id": "call_1", "type": "tool_call"}
    )

    assert isinstance(result, ToolMessage)
    assert isinstance(result.content, list)
    assert result.content[0]["type"] == "text"
    assert result.content[1]["type"] == "image"


def test_read_file_image_switch_off_returns_base64_text(tmp_path):
    set_config({"agent": {"multimodal_tool_results": False}})
    png = _make_png(tmp_path)

    result = read_file(str(png))

    assert isinstance(result, str)
    assert "data:image/png;base64," in result


def test_read_file_svg_is_read_as_text(tmp_path):
    svg = tmp_path / "icon.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>', encoding="utf-8")

    result = read_file(str(svg))

    assert isinstance(result, str)
    assert "<svg" in result


def test_read_file_bmp_not_inlined(tmp_path):
    bmp = tmp_path / "img.bmp"
    bmp.write_bytes(b"BM" + b"\x00" * 64)

    result = read_file(str(bmp))

    assert isinstance(result, str)
    assert "暂不支持" in result


def test_read_multiple_files_mixed_inline(tmp_path):
    txt = tmp_path / "a.txt"
    txt.write_text("hello", encoding="utf-8")
    png = _make_png(tmp_path)

    result = read_multiple_files([str(txt), str(png)])

    assert isinstance(result, list)
    assert has_image_block(result)
    texts = [b["text"] for b in result if b["type"] == "text"]
    assert any("hello" in t for t in texts)


def test_read_multiple_files_all_text_returns_str(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("aaa", encoding="utf-8")
    b.write_text("bbb", encoding="utf-8")

    result = read_multiple_files([str(a), str(b)])

    assert isinstance(result, str)
    assert "aaa" in result and "bbb" in result


def test_read_multiple_files_caps_inlined_images(tmp_path):
    paths = [str(_make_png(tmp_path, f"p{i}.png")) for i in range(6)]

    result = read_multiple_files(paths)

    assert isinstance(result, list)
    images = [b for b in result if b["type"] == "image"]
    assert len(images) == 5
    assert any("最多内联查看 5 张图片" in b["text"] for b in result if b["type"] == "text")


def test_blocks_to_display_text_replaces_images():
    blocks = [
        {"type": "text", "text": "[Image: a.png, 1.0 KB, image/png]"},
        {"type": "image", "base64": "AAAA" * 100, "mime_type": "image/png"},
    ]

    out = blocks_to_display_text(blocks)

    assert "AAAA" not in out
    assert "image/png" in out


def test_blocks_to_display_text_passes_plain_str_through():
    assert blocks_to_display_text("plain text") == "plain text"


def test_tool_output_text_strips_base64_from_tool_message():
    msg = ToolMessage(
        content=[
            {"type": "text", "text": "[Image: a.png]"},
            {"type": "image", "base64": "SECRET" * 50, "mime_type": "image/jpeg"},
        ],
        tool_call_id="call_1",
    )

    text, image_count, image_tokens = _tool_result_display(msg)

    assert "SECRET" not in text
    assert "image/jpeg" in text
    assert image_count == 1
    assert image_tokens == 184  # 不是合法图片 -> 取下限，但绝不报 0


def test_tool_result_display_reports_image_stats_from_read_file(tmp_path):
    png = _make_png(tmp_path)

    text, image_count, image_tokens = _tool_result_display(read_file(str(png)))

    assert "base64" not in text
    assert image_count == 1
    assert image_tokens == 184  # 1x1 像素 -> 下限


def test_tool_result_display_on_plain_text():
    text, image_count, image_tokens = _tool_result_display("just text")

    assert text == "just text"
    assert (image_count, image_tokens) == (0, 0)
