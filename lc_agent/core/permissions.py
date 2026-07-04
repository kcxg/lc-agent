from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_JSONC_COMMENT_RE = re.compile(r"//.*?$|/\*.*?\*/", re.MULTILINE | re.DOTALL)


def _strip_jsonc_comments(text: str) -> str:
    """Remove // and /* */ comments from JSONC text."""
    return _JSONC_COMMENT_RE.sub("", text)


class PermissionsService:
    """Manages tool permissions with JSONC file persistence.

    All tools require approval by default. Tools listed in ``tool_allowlist``
    skip the human-in-the-loop interrupt.
    """

    def __init__(self, permissions_path: Path):
        self._path = Path(permissions_path)
        self._allowlist: set[str] = set()
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            self._allowlist = set()
            return
        try:
            raw = self._path.read_text(encoding="utf-8")
            cleaned = _strip_jsonc_comments(raw)
            data = json.loads(cleaned)
            tools = data.get("tool_allowlist", [])
            self._allowlist = set(tools) if isinstance(tools, list) else set()
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load permissions from %s: %s — using empty allowlist", self._path, e)
            self._allowlist = set()

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "tool_allowlist": sorted(self._allowlist),
        }
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._path)

    def is_allowed(self, tool_name: str) -> bool:
        return tool_name in self._allowlist

    def should_interrupt(self, request: Any) -> bool:
        """``when`` predicate for HumanInTheLoopMiddleware.

        Returns True to interrupt (tool NOT in allowlist).
        Returns False to auto-approve (tool IS in allowlist).
        """
        tool_name = request.tool_call["name"]
        return not self.is_allowed(tool_name)

    def allow_tool(self, tool_name: str) -> None:
        self._allowlist.add(tool_name)
        self._save()

    def remove_tool(self, tool_name: str) -> None:
        self._allowlist.discard(tool_name)
        self._save()

    def get_allowlist(self) -> list[str]:
        return sorted(self._allowlist)

    def set_allowlist(self, tools: list[str]) -> None:
        self._allowlist = set(tools)
        self._save()
