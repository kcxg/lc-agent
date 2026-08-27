import subprocess
from types import SimpleNamespace

from lc_agent.server.routes.file_changes import (
    _build_hunk_diff,
    _count_diff_lines,
    _git_files_for_baseline,
    _resolve_baseline,
)


def test_edit_after_create_does_not_render_created_file_as_full_addition():
    changes = [
        SimpleNamespace(
            change_type="create",
            old_string=None,
            new_string="10\n11\n12\n13\n14",
            move_destination=None,
        ),
        SimpleNamespace(
            change_type="edit",
            old_string="12",
            new_string="12b",
            move_destination=None,
        ),
    ]

    hunks = _build_hunk_diff(changes, "t2.py")

    assert hunks == [
        {
            "type": "edit",
            "removed": ["12"],
            "added": ["12b"],
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
