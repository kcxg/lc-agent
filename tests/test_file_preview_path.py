from pathlib import Path

import pytest

from lc_agent.server.routes.tools import _require_path_within_project


def test_project_file_preview_allows_file_within_root(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    readme = project_root / "FEATURES.md"
    readme.write_text("# Features", encoding="utf-8")

    assert _require_path_within_project(str(readme), project_root) == str(readme.resolve())


def test_project_file_preview_rejects_file_outside_root(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    outside = tmp_path / "secret.md"
    outside.write_text("private", encoding="utf-8")

    with pytest.raises(PermissionError, match="outside"):
        _require_path_within_project(str(outside), project_root)
