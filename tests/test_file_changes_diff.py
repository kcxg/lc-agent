import subprocess
from datetime import datetime
from types import SimpleNamespace

from lc_agent.server.routes.file_changes import (
    _build_hunk_diff,
    _build_round_groups,
    _count_diff_lines,
    _git_files_for_baseline,
    _resolve_baseline,
)


def _change(file_path: str, change_type: str, round_number: int | None = None, **kwargs):
    kwargs.setdefault("line_start", None)
    return SimpleNamespace(
        file_path=file_path,
        change_type=change_type,
        round_number=round_number,
        created_at=datetime(2026, 1, 1),
        move_destination=None,
        **kwargs,
    )


def test_build_round_groups_filters_legacy_and_merges_sub_sessions():
    changes = [
        _change("a.py", "create", 1),
        _change("a.py", "edit", 1),
        _change("b.py", "edit", 2),
        _change("legacy.py", "edit", None),  # 旧数据无轮次
    ]
    sub_sessions = [
        ("sess--sa--tc1", "子代理", [
            _change("c.py", "create", 2),
            _change("d.py", "edit", None),
        ])
    ]

    rounds = _build_round_groups(changes, sub_sessions)

    assert [r["round_number"] for r in rounds] == [1, 2]
    round1, round2 = rounds
    assert [f["file_path"] for f in round1["files"]] == ["a.py"]
    assert round1["files"][0]["edit_count"] == 2
    assert round1["sub_sessions"] == []
    assert [f["file_path"] for f in round2["files"]] == ["b.py"]
    assert round2["sub_sessions"][0]["sub_session_id"] == "sess--sa--tc1"
    assert [f["file_path"] for f in round2["sub_sessions"][0]["files"]] == ["c.py"]


def test_build_hunk_diff_respects_round_filtered_changes():
    round1_changes = [_change("a.py", "edit", 1, old_string="old1", new_string="new1")]
    round2_changes = [_change("a.py", "edit", 2, old_string="old2", new_string="new2")]

    assert _build_hunk_diff(round1_changes, "a.py") == [
        {"type": "edit", "line_start": 1, "context_before": [], "removed": ["old1"], "added": ["new1"], "context_after": []}
    ]
    assert _build_hunk_diff(round2_changes, "a.py") == [
        {"type": "edit", "line_start": 1, "context_before": [], "removed": ["old2"], "added": ["new2"], "context_after": []}
    ]


def test_build_hunk_diff_uses_recorded_line_start():
    changes = [
        _change("a.py", "edit", 3, line_start=42, old_string="alpha\nbeta", new_string="alpha2\nbeta\ngamma"),
        _change("b.py", "append", 3, line_start=10, new_string="x\ny"),
    ]

    assert _build_hunk_diff(changes, "a.py") == [
        {
            "type": "edit",
            "line_start": 42,
            "context_before": [],
            "removed": ["alpha", "beta"],
            "added": ["alpha2", "beta", "gamma"],
            "context_after": [],
        },
        {
            "type": "append",
            "line_start": 10,
            "context_before": [],
            "added": ["x", "y"],
        },
    ]


def test_build_hunk_diff_includes_context_lines():
    changes = [
        _change(
            "a.py",
            "edit",
            3,
            line_start=16,
            old_string="12i",
            new_string="12j",
            context_before="11\n12\n13\n14\n15",
            context_after="17\n18",
        ),
    ]

    assert _build_hunk_diff(changes, "a.py") == [
        {
            "type": "edit",
            "line_start": 16,
            "context_before": ["11", "12", "13", "14", "15"],
            "removed": ["12i"],
            "added": ["12j"],
            "context_after": ["17", "18"],
        },
    ]


def test_edit_after_create_does_not_render_created_file_as_full_addition():
    changes = [
        SimpleNamespace(
            change_type="create",
            old_string=None,
            new_string="10\n11\n12\n13\n14",
            move_destination=None,
            line_start=1,
        ),
        SimpleNamespace(
            change_type="edit",
            old_string="12",
            new_string="12b",
            move_destination=None,
            line_start=3,
        ),
    ]

    hunks = _build_hunk_diff(changes, "t2.py")

    assert hunks == [
        {
            "type": "edit",
            "line_start": 3,
            "context_before": [],
            "removed": ["12"],
            "added": ["12b"],
            "context_after": [],
        }
    ]


def _run_git(cwd, *args):
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def test_count_diff_lines_ignores_unified_headers():
    additions, deletions = _count_diff_lines(
        "--- a/t2.py\n+++ b/t2.py\n-old\n+new\n context\n"
    )

    assert (additions, deletions) == (1, 1)


def test_git_baselines_report_expected_file_stats(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init")
    _run_git(repo, "config", "user.email", "test@example.com")
    _run_git(repo, "config", "user.name", "Test User")

    file_path = repo / "sample.py"
    file_path.write_text("one\ntwo\n", encoding="utf-8")
    _run_git(repo, "add", "sample.py")
    _run_git(repo, "commit", "-m", "initial")
    base_hash = _run_git(repo, "rev-parse", "HEAD").stdout.strip()

    file_path.write_text("one\nthree\nfour\n", encoding="utf-8")
    session = SimpleNamespace(git_base_hash=base_hash)
    session_baseline = _resolve_baseline(session, str(file_path), "session", None)
    assert session_baseline is not None

    session_result = _git_files_for_baseline(str(repo), session_baseline, [])
    assert session_result["available"] is True
    assert session_result["files"][0]["change_type"] == "edit"
    assert session_result["files"][0]["additions"] == 2
    assert session_result["files"][0]["deletions"] == 1

    _run_git(repo, "add", "sample.py")
    staged_baseline = _resolve_baseline(session, str(file_path), "staged", None)
    assert staged_baseline is not None
    staged_result = _git_files_for_baseline(str(repo), staged_baseline, [])
    assert staged_result["available"] is True
    assert staged_result["baseline"] == "staged"
    assert staged_result["files"][0]["additions"] == 2
    assert staged_result["files"][0]["deletions"] == 1

    commit_baseline = _resolve_baseline(session, str(file_path), "commit", base_hash)
    assert commit_baseline is not None
    commit_result = _git_files_for_baseline(str(repo), commit_baseline, [])
    assert commit_result["available"] is True
    assert commit_result["baseline"] == "commit"
    assert commit_result["files"][0]["file_path"] == str(file_path.resolve())
