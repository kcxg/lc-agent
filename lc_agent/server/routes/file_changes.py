"""API routes for session file changes and Git-based diff views."""

import asyncio
import os
import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from lc_agent.db.models_auth import User
from lc_agent.db.repository import FileChangeRepository, SessionRepository
from lc_agent.server.auth_middleware import get_current_user
from lc_agent.server.dependencies import get_db_session

router = APIRouter(tags=["file-changes"])

_BASELINE_SESSION = "session"
_BASELINE_HEAD = "head"
_BASELINE_STAGED = "staged"
_BASELINE_COMMIT = "commit"
_BASELINES = {
    _BASELINE_SESSION,
    _BASELINE_HEAD,
    _BASELINE_STAGED,
    _BASELINE_COMMIT,
}


def _check_session_access(sess, user: User) -> None:
    if sess.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")


def _aggregate_file_changes(changes: list) -> list[dict]:
    """Aggregate per-file tool changes into summary entries."""
    file_map: dict[str, dict] = {}
    for change in changes:
        file_path = change.file_path
        if file_path not in file_map:
            file_map[file_path] = {
                "file_path": file_path,
                "change_type": change.change_type,
                "edit_count": 0,
                "last_change_at": change.created_at.isoformat(),
            }
        entry = file_map[file_path]
        entry["edit_count"] += 1
        entry["last_change_at"] = change.created_at.isoformat()

        if change.change_type == "delete":
            entry["change_type"] = "delete"
        elif change.change_type == "move":
            entry["change_type"] = "move"
            entry["move_destination"] = change.move_destination
        elif entry["change_type"] not in ("delete", "move"):
            if change.change_type == "create":
                entry["change_type"] = "create"
            elif entry["change_type"] != "create":
                entry["change_type"] = "edit"
    return list(file_map.values())


def _run_git(cwd: str, args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
    )


def _find_repo_root(file_path: str) -> Path | None:
    try:
        path = Path(file_path)
        cwd = path if path.is_dir() else path.parent
        result = _run_git(str(cwd), ["rev-parse", "--show-toplevel"], 10)
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip()).resolve()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def _resolve_commit_ref(cwd: str, ref: str | None) -> str | None:
    """Resolve a user-supplied ref to a commit hash before passing it to git diff."""
    if not ref or ref.startswith("-"):
        return None
    try:
        result = _run_git(cwd, ["rev-parse", "--verify", f"{ref}^{{commit}}"], 10)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def _resolve_baseline(
    sess,
    file_path: str,
    baseline: str,
    commit: str | None,
) -> dict | None:
    if baseline not in _BASELINES:
        raise HTTPException(status_code=422, detail=f"不支持的 Git 基准: {baseline}")

    repo_root = _find_repo_root(file_path)
    if repo_root is None:
        return None

    cwd = str(repo_root)
    if baseline == _BASELINE_SESSION:
        ref = _resolve_commit_ref(cwd, sess.git_base_hash)
        if ref is None:
            return None
        return {
            "key": baseline,
            "label": "会话基准",
            "ref": ref,
            "diff_args": [ref],
            "include_untracked_agent_files": True,
        }

    if baseline == _BASELINE_HEAD:
        ref = _resolve_commit_ref(cwd, "HEAD")
        if ref is None:
            return None
        return {
            "key": baseline,
            "label": "HEAD",
            "ref": ref,
            "diff_args": [ref],
            "include_untracked_agent_files": True,
        }

    if baseline == _BASELINE_STAGED:
        head_ref = _resolve_commit_ref(cwd, "HEAD")
        if head_ref is None:
            return None
        return {
            "key": baseline,
            "label": "暂存区（HEAD → 暂存区）",
            "ref": head_ref,
            "diff_args": ["--cached"],
            "include_untracked_agent_files": False,
        }

    ref = _resolve_commit_ref(cwd, commit)
    if ref is None:
        return None
    return {
        "key": baseline,
        "label": f"提交 {ref[:10]}",
        "ref": ref,
        "diff_args": [ref],
        "include_untracked_agent_files": True,
    }


def _try_no_index_diff(file_path: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "diff", "--no-index", "--", os.devnull, file_path],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(Path(file_path).parent),
        )
        # git diff --no-index returns 1 when differences exist.
        if result.stdout.strip():
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def _try_git_file_diff_with_baseline(baseline: dict, file_path: str) -> str | None:
    try:
        result = _run_git(
            str(Path(file_path).parent),
            ["diff", *baseline["diff_args"], "--", file_path],
            10,
        )
        if result.stdout.strip():
            return result.stdout

        if baseline["include_untracked_agent_files"] and Path(file_path).exists():
            tracked = _run_git(
                str(Path(file_path).parent),
                ["ls-files", "--error-unmatch", file_path],
                5,
            )
            if tracked.returncode != 0:
                return _try_no_index_diff(file_path)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def _try_git_file_diff(git_base_hash: str, file_path: str) -> str | None:
    """Backward-compatible helper for the session-baseline file view."""
    return _try_git_file_diff_with_baseline(
        {
            "diff_args": [git_base_hash],
            "include_untracked_agent_files": True,
        },
        file_path,
    )


def _is_git_tracked(file_path: str) -> bool:
    try:
        result = _run_git(
            str(Path(file_path).parent),
            ["ls-files", "--error-unmatch", file_path],
            5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def _count_diff_lines(unified_diff: str | None) -> tuple[int, int]:
    """Count added and removed body lines, excluding unified diff headers."""
    if not unified_diff:
        return 0, 0
    additions = 0
    deletions = 0
    for line in unified_diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            additions += 1
        elif line.startswith("-"):
            deletions += 1
    return additions, deletions


def _parse_git_name_status(stdout: str, repo_root: Path) -> list[dict]:
    files: list[dict] = []
    for line in stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status_token = parts[0]
        status = status_token[:1]
        relative_path = parts[-1]
        item = {
            "file_path": str((repo_root / relative_path).resolve()),
            "change_type": {
                "M": "edit",
                "A": "create",
                "D": "delete",
                "R": "move",
            }.get(status, "edit"),
            "additions": 0,
            "deletions": 0,
        }
        if status == "R" and len(parts) >= 3:
            item["move_source"] = str((repo_root / parts[1]).resolve())
        files.append(item)
    return files


def _git_files_for_baseline(cwd: str, baseline: dict, changes: list) -> dict:
    repo_root = _find_repo_root(cwd)
    if repo_root is None:
        return {"available": False, "reason": "当前文件不在 Git 仓库中"}

    try:
        result = _run_git(cwd, ["diff", *baseline["diff_args"], "--name-status"], 30)
        if result.returncode != 0:
            return {"available": False, "reason": result.stderr.strip() or "git diff failed"}

        files = _parse_git_name_status(result.stdout, repo_root)
        tracked_paths = {str(Path(item["file_path"]).resolve()).lower() for item in files}

        for item in files:
            diff_text = _try_git_file_diff_with_baseline(baseline, item["file_path"])
            item["additions"], item["deletions"] = _count_diff_lines(diff_text)

        if baseline["include_untracked_agent_files"]:
            for change in _aggregate_file_changes(changes):
                file_path = change["file_path"]
                normalized_path = str(Path(file_path).resolve()).lower()
                if normalized_path in tracked_paths or not Path(file_path).exists():
                    continue
                diff_text = _try_no_index_diff(file_path)
                additions, deletions = _count_diff_lines(diff_text)
                files.append({
                    "file_path": file_path,
                    "change_type": change["change_type"],
                    "additions": additions,
                    "deletions": deletions,
                })

        if not files:
            return {"available": False, "reason": "当前基准下没有可显示的 Git 变更"}
        return {
            "available": True,
            "base_hash": baseline["ref"],
            "baseline": baseline["key"],
            "baseline_label": baseline["label"],
            "files": files,
        }
    except FileNotFoundError:
        return {"available": False, "reason": "git is not installed"}
    except subprocess.TimeoutExpired:
        return {"available": False, "reason": "git diff timed out"}
    except OSError as exc:
        return {"available": False, "reason": str(exc)}


def _build_hunk_diff(file_changes: list, file_path: str) -> list[dict]:
    """Build diff hunks from recorded changes when Git is unavailable."""
    hunks = []
    has_edit = any(change.change_type == "edit" for change in file_changes)
    for change in file_changes:
        if change.change_type == "edit" and change.old_string and change.new_string is not None:
            hunks.append({
                "type": "edit",
                "removed": change.old_string.split("\n"),
                "added": change.new_string.split("\n"),
            })
        elif change.change_type == "create" and has_edit:
            continue
        elif change.change_type in ("create", "append") and change.new_string:
            hunks.append({
                "type": change.change_type,
                "added": change.new_string.split("\n"),
            })
        elif change.change_type == "delete":
            hunks.append({"type": "delete"})
        elif change.change_type == "move":
            hunks.append({
                "type": "move",
                "destination": change.move_destination,
            })
    return hunks


@router.get("/sessions/{session_id}/file-changes")
async def list_file_changes(
    session_id: str,
    include_subagents: bool = Query(True, description="Include sub-agent file changes"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get the Agent-recorded file changes for a session."""
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_session_access(sess, user)

    fc_repo = FileChangeRepository(db)
    changes = await fc_repo.list_by_session(session_id)
    sub_sessions: list[dict] = []
    if include_subagents:
        child_sessions = await repo.list_children(session_id)
        for child in child_sessions:
            child_changes = await fc_repo.list_by_session(child.id)
            if child_changes:
                sub_sessions.append({
                    "sub_session_id": child.id,
                    "title": child.title or child.id.split("--sa--")[-1][:8],
                    "file_count": len(set(change.file_path for change in child_changes)),
                    "files": _aggregate_file_changes(child_changes),
                })

    return {
        "session_id": session_id,
        "git_base_hash": sess.git_base_hash,
        "files": _aggregate_file_changes(changes),
        "sub_sessions": sub_sessions,
    }


@router.get("/sessions/{session_id}/file-changes/diff")
async def get_file_diff(
    session_id: str,
    file_path: str = Query(..., description="Absolute path of the file"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get the Agent-recorded final diff for one file."""
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_session_access(sess, user)

    fc_repo = FileChangeRepository(db)
    all_changes = await fc_repo.list_by_session(session_id)
    file_changes = [change for change in all_changes if change.file_path == file_path]
    if not file_changes:
        raise HTTPException(status_code=404, detail="No changes found for this file")

    final_type = file_changes[-1].change_type
    if any(change.change_type == "delete" for change in file_changes):
        final_type = "delete"

    unified_diff = None
    if sess.git_base_hash and await asyncio.to_thread(_is_git_tracked, file_path):
        unified_diff = await asyncio.to_thread(_try_git_file_diff, sess.git_base_hash, file_path)

    if unified_diff:
        return {
            "file_path": file_path,
            "final_type": final_type,
            "unified_diff": unified_diff,
            "hunks": None,
            "change_count": len(file_changes),
            "diff_source": "git",
        }

    return {
        "file_path": file_path,
        "final_type": final_type,
        "unified_diff": None,
        "hunks": _build_hunk_diff(file_changes, file_path),
        "change_count": len(file_changes),
        "diff_source": "hunks",
    }


async def _get_git_context(session_id: str, user: User, db: AsyncSession):
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_session_access(sess, user)
    fc_repo = FileChangeRepository(db)
    changes = await fc_repo.list_by_session(session_id)
    if not changes:
        return sess, changes, None
    return sess, changes, str(Path(changes[0].file_path).parent)


@router.get("/sessions/{session_id}/git-diff/commits")
async def list_git_commits(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List recent commits that can be selected as a Git diff baseline."""
    _, changes, cwd = await _get_git_context(session_id, user, db)
    if not changes or cwd is None:
        return {"available": False, "commits": [], "reason": "No file changes in this session"}
    try:
        result = await asyncio.to_thread(
            _run_git,
            cwd,
            ["log", "-n", "30", "--format=%H%x09%h%x09%s"],
            10,
        )
        if result.returncode != 0:
            return {"available": False, "commits": [], "reason": result.stderr.strip() or "无法读取 Git 提交"}
        commits = []
        for line in result.stdout.splitlines():
            parts = line.split("\t", 2)
            if len(parts) == 3:
                commits.append({"hash": parts[0], "short_hash": parts[1], "subject": parts[2]})
        return {"available": bool(commits), "commits": commits}
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        return {"available": False, "commits": [], "reason": str(exc)}


@router.get("/sessions/{session_id}/git-diff")
async def get_git_diff(
    session_id: str,
    baseline: str = Query(_BASELINE_SESSION),
    commit: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a complete Git diff for the selected baseline."""
    sess, changes, cwd = await _get_git_context(session_id, user, db)
    if not changes or cwd is None:
        return {"available": False, "reason": "No file changes in this session"}
    git_baseline = _resolve_baseline(sess, changes[0].file_path, baseline, commit)
    if git_baseline is None:
        return {"available": False, "reason": "无法解析所选 Git 基准"}

    try:
        result = await asyncio.to_thread(_run_git, cwd, ["diff", *git_baseline["diff_args"]], 30)
        diff_parts = [result.stdout] if result.returncode == 0 and result.stdout.strip() else []
        if git_baseline["include_untracked_agent_files"]:
            for change in _aggregate_file_changes(changes):
                if Path(change["file_path"]).exists() and not await asyncio.to_thread(_is_git_tracked, change["file_path"]):
                    untracked_diff = await asyncio.to_thread(_try_no_index_diff, change["file_path"])
                    if untracked_diff:
                        diff_parts.append(untracked_diff)
        if not diff_parts:
            return {"available": False, "reason": "当前基准下没有可显示的 Git 变更"}
        return {
            "available": True,
            "base_hash": git_baseline["ref"],
            "baseline": baseline,
            "baseline_label": git_baseline["label"],
            "diff": "\n".join(diff_parts),
        }
    except FileNotFoundError:
        return {"available": False, "reason": "git is not installed"}
    except subprocess.TimeoutExpired:
        return {"available": False, "reason": "git diff timed out"}
    except OSError as exc:
        return {"available": False, "reason": str(exc)}


@router.get("/sessions/{session_id}/git-diff/files")
async def list_git_diff_files(
    session_id: str,
    baseline: str = Query(_BASELINE_SESSION),
    commit: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get changed files for one Git baseline; file bodies load separately."""
    sess, changes, cwd = await _get_git_context(session_id, user, db)
    if not changes or cwd is None:
        return {"available": False, "reason": "No file changes in this session"}
    git_baseline = _resolve_baseline(sess, changes[0].file_path, baseline, commit)
    if git_baseline is None:
        return {"available": False, "reason": "无法解析所选 Git 基准"}
    return await asyncio.to_thread(_git_files_for_baseline, cwd, git_baseline, changes)


@router.get("/sessions/{session_id}/git-diff/file")
async def get_git_file_diff(
    session_id: str,
    file_path: str = Query(..., description="Absolute path of the file"),
    baseline: str = Query(_BASELINE_SESSION),
    commit: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get one file's Git diff for the selected baseline."""
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_session_access(sess, user)
    git_baseline = _resolve_baseline(sess, file_path, baseline, commit)
    if git_baseline is None:
        return {"available": False, "reason": "无法解析所选 Git 基准"}

    diff_text = await asyncio.to_thread(_try_git_file_diff_with_baseline, git_baseline, file_path)
    if not diff_text:
        return {"available": False, "reason": "无法获取该文件的 Git Diff"}
    return {
        "available": True,
        "file_path": file_path,
        "baseline": baseline,
        "baseline_label": git_baseline["label"],
        "diff": diff_text,
    }
