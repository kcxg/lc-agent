from pathlib import Path

import pytest

from lc_agent.server.routes.tools import (
    _git_branch_info,
    _require_path_within_project,
    _resolve_project_file_path,
    _search_project_tree,
)


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


def test_project_file_preview_resolves_relative_path_from_project_root(tmp_path: Path) -> None:
    """文件树传的是项目相对路径，必须按项目根解析而非服务进程 cwd。"""
    project_root = tmp_path / "project"
    (project_root / "examples").mkdir(parents=True)
    example = project_root / "examples" / "example_easy.py"
    example.write_text("print('hi')", encoding="utf-8")

    assert _resolve_project_file_path("examples/example_easy.py", project_root) == str(example.resolve())


def test_project_file_preview_resolves_absolute_path_within_root(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    readme = project_root / "README.md"
    readme.write_text("# hi", encoding="utf-8")

    assert _resolve_project_file_path(str(readme), project_root) == str(readme.resolve())


def test_project_file_preview_rejects_relative_path_escaping_root(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (tmp_path / "secret.md").write_text("private", encoding="utf-8")

    with pytest.raises(PermissionError, match="outside"):
        _resolve_project_file_path("../secret.md", project_root)


def _make_search_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "project"
    (project_root / "examples").mkdir(parents=True)
    (project_root / "examples" / "example_easy.py").write_text("a", encoding="utf-8")
    (project_root / "examples" / "nested").mkdir()
    (project_root / "examples" / "nested" / "example_deep.py").write_text("b", encoding="utf-8")
    (project_root / "README.md").write_text("c", encoding="utf-8")
    (project_root / "funboost").mkdir()
    (project_root / "funboost" / "example_other.py").write_text("d", encoding="utf-8")
    return project_root


def test_project_search_finds_files_in_unexpanded_directories(tmp_path: Path) -> None:
    """搜索必须覆盖未展开的目录，而不是只过滤已加载层。"""
    project_root = _make_search_project(tmp_path)

    found = _search_project_tree(project_root, "example_deep")

    assert [r["path"] for r in found["results"]] == ["examples/nested/example_deep.py"]
    assert found["truncated"] is False


def test_project_search_returns_nested_relative_paths(tmp_path: Path) -> None:
    project_root = _make_search_project(tmp_path)

    paths = sorted(r["path"] for r in _search_project_tree(project_root, "example_")["results"])

    assert paths == [
        "examples/example_easy.py",
        "examples/nested/example_deep.py",
        "funboost/example_other.py",
    ]


def test_project_search_matches_directories_too(tmp_path: Path) -> None:
    project_root = _make_search_project(tmp_path)

    results = _search_project_tree(project_root, "funboost")["results"]

    assert [(r["name"], r["type"]) for r in results] == [("funboost", "dir")]


def test_project_search_respects_limit_and_marks_truncated(tmp_path: Path) -> None:
    project_root = _make_search_project(tmp_path)

    found = _search_project_tree(project_root, "example_", limit=2)

    assert len(found["results"]) == 2
    assert found["truncated"] is True


def test_project_search_empty_keyword_returns_nothing(tmp_path: Path) -> None:
    project_root = _make_search_project(tmp_path)

    assert _search_project_tree(project_root, "   ") == {"results": [], "truncated": False}


def test_git_branch_info_returns_none_for_non_git_directory(tmp_path: Path) -> None:
    project_root = tmp_path / "plain"
    project_root.mkdir()

    assert _git_branch_info(project_root) is None


def test_git_branch_info_returns_current_branch(tmp_path: Path) -> None:
    import subprocess

    project_root = tmp_path / "repo"
    project_root.mkdir()
    subprocess.run(["git", "init", "-b", "feature-x"], cwd=project_root, capture_output=True, text=True)

    assert _git_branch_info(project_root) == "feature-x"


def test_git_branch_info_reports_detached_head(tmp_path: Path) -> None:
    import subprocess

    project_root = tmp_path / "repo"
    project_root.mkdir()
    run = lambda *a: subprocess.run(["git", *a], cwd=project_root, capture_output=True, text=True)
    run("init", "-b", "main")
    run("config", "user.email", "t@example.com")
    run("config", "user.name", "t")
    (project_root / "a.txt").write_text("a", encoding="utf-8")
    run("add", "a.txt")
    run("commit", "-m", "init")
    head = run("rev-parse", "HEAD").stdout.strip()
    run("checkout", head)

    assert _git_branch_info(project_root) == "(detached HEAD)"
