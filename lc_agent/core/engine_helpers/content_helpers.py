"""Message content conversion helpers."""
from typing import Any


_IMAGE_BLOCK_TYPES = frozenset({"image", "image_url"})


def _image_placeholder(block: dict[str, Any]) -> str:
    """图片块的展示占位（绝不包含 base64）。"""
    mime = block.get("mime_type") or ""
    if not mime:
        image_url = block.get("image_url")
        if isinstance(image_url, dict):
            url = image_url.get("url", "")
            if isinstance(url, str) and url.startswith("data:") and ";" in url:
                mime = url[len("data:"):url.index(";")]
    return f"[图片: {mime}]" if mime else "[图片]"


def has_image_block(content: Any) -> bool:
    """content 中是否含图片块。"""
    if not isinstance(content, list):
        return False
    return any(
        isinstance(block, dict) and block.get("type") in _IMAGE_BLOCK_TYPES
        for block in content
    )


def blocks_to_display_text(content: Any) -> str:
    """把消息 content（可能是多模态 content blocks）压成可展示的纯文本。

    图片块只留占位、其它非文本块回退 repr——避免把图片 base64 灌进 SSE 事件
    和历史接口（前端与库存储都不该承受这份体积）。模型侧仍使用原始 blocks。
    """
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content)

    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict):
            block_type = block.get("type", "")
            if block_type == "text":
                parts.append(block.get("text", ""))
            elif block_type in _IMAGE_BLOCK_TYPES:
                parts.append(_image_placeholder(block))
            else:
                parts.append(repr(block))
        else:
            parts.append(repr(block))
    return "\n".join(parts)


def _convert_text_file_blocks(content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert text_file blocks to native text blocks for LangChain consumption."""
    converted = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text_file":
            name = block.get("name", "")
            text_content = block.get("textContent", "")
            lang = block.get("lang", "")
            converted.append(
                {
                    "type": "text",
                    "text": f"📎 `{name}`:\n```{lang}\n{text_content}\n```",
                }
            )
        else:
            converted.append(block)
    return converted


def _convert_history_item(item: dict[str, Any]) -> dict[str, Any]:
    """Convert text_file blocks in a history message's content."""
    content = item.get("content")
    if isinstance(content, list):
        return {**item, "content": _convert_text_file_blocks(content)}
    return item
