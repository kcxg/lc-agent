"""Message content conversion helpers."""
from typing import Any


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
