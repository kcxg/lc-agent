from pathlib import Path

import base64

import pytest

from lc_agent.server.routes.tools import (
    _DOCUMENT_MIME_TYPES,
    _DOCUMENT_READ_MAX_SIZE,
    _git_branch_info,
    _require_path_within_project,
    _resolve_project_file_path,
    _search_project_tree,
    read_file_content,
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


@pytest.mark.parametrize(
    ("suffix", "kind"),
    [(".pdf", "pdf"), (".docx", "docx"), (".xlsx", "xlsx"), (".pptx", "pptx")],
)
async def test_document_preview_returns_base64_data_url(tmp_path: Path, suffix: str, kind: str) -> None:
    """四类文档必须返回 data URL 与格式标记，前端才能选对应预览组件。"""
    doc = tmp_path / f"sample{suffix}"
    doc.write_bytes(b"PK\x03\x04document-bytes")

    result = await read_file_content(path=str(doc))

    assert result["document"] is True
    assert result["document_kind"] == kind
    assert result["document_too_large"] is False
    assert result["data_url"].startswith(f"data:{_DOCUMENT_MIME_TYPES['.' + kind]};base64,")
    assert base64.b64decode(result["data_url"].split(",", 1)[1]) == b"PK\x03\x04document-bytes"


async def test_document_preview_reports_too_large_without_transferring(tmp_path: Path) -> None:
    """超过上限只回尺寸提示，不下发 base64，避免把大文件塞进响应体。"""
    doc = tmp_path / "huge.pdf"
    with open(doc, "wb") as f:
        f.truncate(_DOCUMENT_READ_MAX_SIZE + 1)

    result = await read_file_content(path=str(doc))

    # 超限提示也必须带 mtime：前端靠它轮询发现外部改动
    assert result["file"] == str(doc.resolve())
    assert result["document"] is True
    assert result["document_too_large"] is True
    assert result["size"] == _DOCUMENT_READ_MAX_SIZE + 1
    assert result["mtime"] > 0


async def test_text_file_is_not_treated_as_document(tmp_path: Path) -> None:
    """普通文本仍走原有文本分支，不能被文档分流截走。"""
    text_file = tmp_path / "notes.txt"
    text_file.write_text("hello", encoding="utf-8")

    result = await read_file_content(path=str(text_file))

    assert "document" not in result
    assert result["lines"] == ["hello"]


@pytest.mark.parametrize("suffix", [".txt", ".pdf", ".png"])
async def test_preview_always_returns_mtime(tmp_path: Path, suffix: str) -> None:
    """文本/文档/图片分支都要回传 mtime，前端轮询外部改动依赖它。"""
    target = tmp_path / f"sample{suffix}"
    target.write_bytes(b"x")

    result = await read_file_content(path=str(target))

    assert result["mtime"] > 0


async def test_binary_preview_returns_mtime(tmp_path: Path) -> None:
    """二进制占位也要带 mtime，否则前端无法判断它是否被替换过。"""
    blob = tmp_path / "data.bin"
    blob.write_bytes(b"\x00\x01\x02binary")

    result = await read_file_content(path=str(blob))

    assert result["binary"] is True
    assert result["mtime"] > 0


async def test_batch_stat_reports_changed_mtime(tmp_path: Path, monkeypatch) -> None:
    """批量 stat 必须反映真实磁盘 mtime，这是轮询发现外部改动的依据。"""
    import os
    import time

    from lc_agent.server.routes.tools import BatchStatPayload, stat_project_files
    from lc_agent.tools.system_tools import _config as cfg

    watched = tmp_path / "watched.py"
    watched.write_text("v1", encoding="utf-8")
    first = watched.stat().st_mtime

    # 模拟外部程序（VSCode / WPS / Agent 脚本）改写文件
    time.sleep(0.01)
    watched.write_text("v2", encoding="utf-8")
    os.utime(watched, (first + 10, first + 10))

    monkeypatch.setattr(cfg, "validate_read_path", lambda p: str(p))

    result = await stat_project_files(
        payload=BatchStatPayload(paths=[str(watched)]),
        agent_id=None,
    )

    entry = result["files"][0]
    assert entry["exists"] is True
    assert entry["mtime"] > first
    assert entry["size"] == 2


async def test_batch_stat_marks_missing_file(tmp_path: Path, monkeypatch) -> None:
    """文件被删除时必须回 exists=False，前端据此判定内容已过期。"""
    from lc_agent.server.routes.tools import BatchStatPayload, stat_project_files
    from lc_agent.tools.system_tools import _config as cfg

    monkeypatch.setattr(cfg, "validate_read_path", lambda p: str(p))

    missing = tmp_path / "gone.py"
    result = await stat_project_files(
        payload=BatchStatPayload(paths=[str(missing)]),
        agent_id=None,
    )

    assert result["files"] == [{"path": str(missing), "exists": False}]


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
