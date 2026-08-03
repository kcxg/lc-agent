"""Subagent descriptor and result-extraction helpers."""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SubAgentDescriptor:
    subagent_type: str
    preset_id: str
    display_name: str
    description: str


def _extract_subagent_result(messages: list[Any]) -> str:
    """Extract the last non-empty AI message text from a subagent's message list.

    Iterates in reverse to skip any trailing empty messages that some providers
    (e.g. Anthropic Claude) may append after the final tool call.
    Returns the first non-empty AI text found — the subagent's conclusive answer.
    """
    for msg in reversed(messages):
        if getattr(msg, "type", None) != "ai":
            continue
        content = getattr(msg, "content", "")
        if isinstance(content, str):
            text = content.strip()
        elif isinstance(content, list):
            text = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            ).strip()
        else:
            text = str(content).strip()
        if text:
            return text
    return ""
