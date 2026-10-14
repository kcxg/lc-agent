"""图片 token 估算：供 UI 展示"这张图大概花多少 token"，不参与真实计费。

用实测数据拟合（commandcode `deepseek/deepseek-v4.1-flash`，纯色图，扣掉同段文本基线）：

    尺寸            像素      实测图片 token
    260x90          23k       186
    512x512         262k      184
    768x768         590k      382
    1280x720        922k      578
    1024x1024       1049k     652
    1536x1536       2359k     994
    2048x2048       4194k     994
    4000x3000       12000k    1001

拟合结果：有下限（≈184）和上限（≈1000），中间近似线性，约每 1600 像素 1 token。
即 ``tokens ≈ clamp(pixels / 1600, 184, 1024)``。ark 侧同尺寸实测也在同一量级
（4000x3000 ≈ 1028），所以这个粗略模型对两家都能用。

注意：各 provider 都会先把图归一化分辨率再计费，所以**文件体积（KB）不影响这个数**，
只有像素数影响。
"""

import base64
import io
import logging
import math
from typing import Any

from PIL import Image

logger = logging.getLogger(__name__)

# 实测拟合参数：每 1600 像素 ≈ 1 token，下限 184、上限 1024
_PIXELS_PER_TOKEN = 1600
_MIN_TOKENS = 184
_MAX_TOKENS = 1024

_IMAGE_BLOCK_TYPES = ("image", "image_url")


def estimate_image_tokens(width: int, height: int) -> int:
    """按像素尺寸估算单张图片的 token 数。"""
    if width <= 0 or height <= 0:
        return _MIN_TOKENS
    pixels = width * height
    tokens = math.ceil(pixels / _PIXELS_PER_TOKEN)
    return max(_MIN_TOKENS, min(_MAX_TOKENS, tokens))


def _image_bytes(block: dict[str, Any]) -> bytes | None:
    """取出图片块里的原始字节（支持 base64 字段与 image_url data URL）。"""
    b64 = block.get("base64")
    if not (isinstance(b64, str) and b64):
        image_url = block.get("image_url")
        url = image_url.get("url") if isinstance(image_url, dict) else None
        if isinstance(url, str) and url.startswith("data:") and ";base64," in url:
            b64 = url.split(";base64,", 1)[1]
    if not (isinstance(b64, str) and b64):
        return None
    try:
        return base64.b64decode(b64, validate=False)
    except ValueError:
        logger.warning("image block base64 payload is not decodable")
        return None


def _pixel_size(data: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(data)) as im:
        return im.size


def estimate_content_image_tokens(content: Any) -> tuple[int, int]:
    """统计 content 中的图片块，返回 ``(图片张数, 估算 token 总数)``。

    图片块数量永远如实统计；单个块读不出尺寸时按 _MIN_TOKENS 计并告警——
    既不能把图片当 0 token（那正是要修的误导），也不能让一张坏图炸掉 SSE 流。
    """
    if not isinstance(content, list):
        return 0, 0

    count = 0
    tokens = 0
    for block in content:
        if not isinstance(block, dict) or block.get("type") not in _IMAGE_BLOCK_TYPES:
            continue
        count += 1
        data = _image_bytes(block)
        if data is None:
            logger.warning("image block has no decodable base64 payload; using min estimate")
            tokens += _MIN_TOKENS
            continue
        try:
            width, height = _pixel_size(data)
        except Exception as e:
            logger.warning("failed to read image dimensions: %s", e)
            tokens += _MIN_TOKENS
            continue
        tokens += estimate_image_tokens(width, height)
    return count, tokens
