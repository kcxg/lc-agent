"""图片 token 估算（实测拟合模型）的单元测试。"""
import base64
import io

from PIL import Image

from lc_agent.utils.image_tokens import (
    estimate_content_image_tokens,
    estimate_image_tokens,
)


def _png_b64(width: int, height: int) -> str:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), "white").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def test_estimate_floor_for_small_images():
    assert estimate_image_tokens(512, 512) == 184
    assert estimate_image_tokens(1, 1) == 184


def test_estimate_scales_with_pixels():
    # 1024x1024 = 1,048,576 px -> ceil(1048576/1600) = 656
    assert estimate_image_tokens(1024, 1024) == 656
    # 1280x720 = 921,600 px -> 576
    assert estimate_image_tokens(1280, 720) == 576


def test_estimate_capped_for_huge_images():
    assert estimate_image_tokens(4000, 3000) == 1024
    assert estimate_image_tokens(12000, 9000) == 1024


def test_estimate_invalid_dimensions_uses_floor():
    assert estimate_image_tokens(0, 0) == 184


def test_estimate_content_counts_base64_image_blocks():
    content = [
        {"type": "text", "text": "x"},
        {"type": "image", "base64": _png_b64(1024, 1024), "mime_type": "image/png"},
    ]

    count, tokens = estimate_content_image_tokens(content)

    assert count == 1
    assert tokens == 656


def test_estimate_content_counts_image_url_data_urls():
    content = [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_png_b64(512, 512)}"}},
    ]

    count, tokens = estimate_content_image_tokens(content)

    assert count == 1
    assert tokens == 184


def test_estimate_content_ignores_non_image_content():
    assert estimate_content_image_tokens("plain text") == (0, 0)
    assert estimate_content_image_tokens([{"type": "text", "text": "x"}]) == (0, 0)


def test_estimate_content_broken_payload_still_counts_image():
    content = [{"type": "image", "base64": "not-an-image", "mime_type": "image/png"}]

    count, tokens = estimate_content_image_tokens(content)

    assert count == 1
    assert tokens == 184
