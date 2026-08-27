"""API routes for file change tracking per session."""

import asyncio
import re
import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from lc_agent.db.models_auth import User
from lc_agent.db.repository import FileChangeRepository, SessionRepository
from lc_agent.server.auth_middleware import get_current_user
from lc_agent.server.dependencies import get_db_session

router = APIRouter(tags=["file-changes"])


def _check_session_access(sess, user: User) -> None:
    if sess.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")


def _aggregate_file_changes(changes: list) -> list[dict]:
    """Aggregate per-file changes into summary entries."""
    file_map: dict[str, dict] = {}
    for c in changes:
        fp = c.file_path
        if fp not in file_map:
            file_map[fp] = {
                "file_path": fp,
                "change_type": c.change_type,
                "edit_count": 0,
                "last_change_at": c.created_at.isoformat(),
            }
        entry = file_map[fp]
        entry["edit_count"] += 1
        entry["last_change_at"] = c.created_at.isoformat()

        if c.change_type == "delete":
            entry["change_type"] = "delete"
        elif c.change_type == "move":
            entry["change_type"] = "move"
            entry["move_destination"] = c.move_destination
        elif entry["change_type"] not in ("delete", "move"):
            if c.change_type == "create":
                entry["change_type"] = "create"
            elif entry["change_type"] != "create":
                entry["change_type"] = "edit"
    return list(file_map.values())


@router.get("/sessions/{session_id}/file-changes")
async def list_file_changes(
    session_id: str,
    include_subagents: bool = Query(True, description="Include sub-agent file changes"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get aggregated file changes for a session.

    Returns per-file summary with final change type and edit count.
    When include_subagents=True, also returns sub-agent change summaries.
    """
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
                    "file_count": len(set(c.file_path for c in child_changes)),
                    "files": _aggregate_file_changes(child_changes),
                })

    return {
        "session_id": session_id,
        "git_base_hash": sess.git_base_hash,
        "files": _aggregate_file_changes(changes),
        "sub_sessions": sub_sessions,
    }


def _try_git_file_diff(git_base_hash: str, file_path: str) -> str | None:
    """Try to get a unified diff for a single file from git."""
    try:
        cwd = str(Path(file_path).parent)
        result = subprocess.run(
            ["git", "diff", git_base_hash, "--", file_path],
            capture_output=True, text=True, timeout=10, cwd=cwd,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout

        # File might be untracked (new); try --no-index
        if Path(file_path).exists():
            check = subprocess.run(
                ["git", "ls-files", "--error-unmatch", file_path],
                capture_output=True, timeout=5, cwd=cwd,
            )
            if check.returncode != 0:
                new_diff = subprocess.run(
                    ["git", "diff", "--no-index", "/dev/null", file_path],
                    capture_output=True, text=True, timeout=10, cwd=cwd,
                )
                if new_diff.stdout.strip():
                    return new_diff.stdout
    except Exception:
        pass
    return None


def _is_git_tracked(file_path: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", file_path],
            capture_output=True,
            timeout=5,
            cwd=str(Path(file_path).parent),
        )
        return result.returncode == 0
    except Exception:
        return False


def _build_hunk_diff(file_changes: list, file_path: str) -> list[dict]:
    """Build diff hunks from recorded changes (fallback when git unavailable)."""
    hunks = []
    has_edit = any(c.change_type == "edit" for c in file_changes)
    for c in file_changes:
        if c.change_type == "edit" and c.old_string and c.new_string is not None:
            hunks.append({
                "type": "edit",
                "removed": c.old_string.split("\n"),
                "added": c.new_string.split("\n"),
            })
        elif c.change_type == "create" and has_edit:
            continue
        elif c.change_type in ("create", "append") and c.new_string:
            hunks.append({
                "type": c.change_type,
                "added": c.new_string.split("\n"),
            })
        elif c.change_type == "delete":
            hunks.append({"type": "delete"})
        elif c.change_type == "move":
            hunks.append({
                "type": "move",
                "destination": c.move_destination,
            })
    return hunks


@router.get("/sessions/{session_id}/file-changes/diff")
async def get_file_diff(
    session_id: str,
    file_path: str = Query(..., description="Absolute path of the file"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get the final diff for a single file in the session.

    Prefers git diff (real final state) when git_base_hash is available.
    Falls back to per-hunk reconstruction from recorded changes.
    """
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_session_access(sess, user)

    fc_repo = FileChangeRepository(db)
    all_changes = await fc_repo.list_by_session(session_id)

    file_changes = [c for c in all_changes if c.file_path == file_path]
    if not file_changes:
        raise HTTPException(status_code=404, detail="No changes found for this file")

    final_type = file_changes[-1].change_type
    if any(c.change_type == "delete" for c in file_changes):
        final_type = "delete"

    unified_diff = None
    if sess.git_base_hash and final_type != "delete" and await asyncio.to_thread(_is_git_tracked, file_path):
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


@router.get("/sessions/{session_id}/git-diff")
async def get_git_diff(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get git diff from the session's base hash to current state.

    Only available when the session has a git_base_hash recorded.
    """
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_session_access(sess, user)

    if not sess.git_base_hash:
        return {"available": False, "reason": "No git base hash recorded for this session"}

    fc_repo = FileChangeRepository(db)
    changes = await fc_repo.list_by_session(session_id)
    if not changes:
        return {"available": False, "reason": "No file changes in this session"}

    first_file = changes[0].file_path
    cwd = str(Path(first_file).parent)
    base_hash = sess.git_base_hash

    changed_paths = [c.file_path for c in changes]

    def _run_git_diff():
        try:
            # Tracked file changes
            result = subprocess.run(
                ["git", "diff", base_hash],
                capture_output=True, text=True, timeout=30,
                cwd=cwd,
            )
            diff_parts = []
            if result.returncode == 0 and result.stdout.strip():
                diff_parts.append(result.stdout)

            # Untracked new files: generate diffs for files the agent created
            for fp in changed_paths:
                if not Path(fp).exists():
                    continue
                check = subprocess.run(
                    ["git", "ls-files", "--error-unmatch", fp],
                    capture_output=True, timeout=5, cwd=cwd,
                )
                if check.returncode != 0:
                    new_diff = subprocess.run(
                        ["git", "diff", "--no-index", "/dev/null", fp],
                        capture_output=True, text=True, timeout=10, cwd=cwd,
                    )
                    if new_diff.stdout.strip():
                        diff_parts.append(new_diff.stdout)

            if not diff_parts:
                return {"available": False, "reason": "文件已恢复到基准状态，当前没有未提交的差异"}
            return {"available": True, "base_hash": base_hash, "diff": "\n".join(diff_parts)}
        except FileNotFoundError:
            return {"available": False, "reason": "git is not installed"}
        except subprocess.TimeoutExpired:
            return {"available": False, "reason": "git diff timed out"}
        except Exception as e:
            return {"available": False, "reason": str(e)}

    return await asyncio.to_thread(_run_git_diff)


@router.get("/sessions/{session_id}/git-diff/files")
async def list_git_diff_files(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get only the changed-file list for Git Diff; file bodies load separately."""
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_session_access(sess, user)

    if not sess.git_base_hash:
        return {"available": False, "reason": "No git base hash recorded for this session"}

    fc_repo = FileChangeRepository(db)
    changes = await fc_repo.list_by_session(session_id)
    if not changes:
        return {"available": False, "reason": "No file changes in this session"}

    cwd = str(Path(changes[0].file_path).parent)
    base_hash = sess.git_base_hash

    def _run_git_file_list():
        try:
            root_result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, timeout=10, cwd=cwd,
            )
            repo_root = Path(root_result.stdout.strip()) if root_result.returncode == 0 else Path(cwd)

            result = subprocess.run(
                ["git", "diff", base_hash, "--name-status"],
                capture_output=True, text=True, timeout=30, cwd=cwd,
            )
            if result.returncode != 0:
                return {"available": False, "reason": result.stderr.strip() or "git diff failed"}

            type_map = {"M": "edit", "A": "create", "D": "delete", "R": "move"}
            files: list[dict] = []
            tracked_paths: set[str] = set()
            for line in result.stdout.splitlines():
                parts = line.split("\t")
                if len(parts) < 2:
                    continue
                status = parts[0][:1]
                relative_path = parts[-1]
                absolute_path = str(repo_root / relative_path)
                tracked_paths.add(str(Path(absolute_path).resolve()).lower())
                files.append({
                    "file_path": absolute_path,
                    "change_type": type_map.get(status, "edit"),
                    "additions": 0,
                    "deletions": 0,
                })

            # git diff does not include untracked files; add files recorded by the tracker.
            for change in _aggregate_file_changes(changes):
                normalized_path = str(Path(change["file_path"]).resolve()).lower()
                if normalized_path not in tracked_paths and Path(change["file_path"]).exists():
                    files.append({
                        "file_path": change["file_path"],
                        "change_type": change["change_type"],
                        "additions": 0,
                        "deletions": 0,
                    })

            if not files:
                return {"available": False, "reason": "文件已恢复到基准状态，当前没有未提交的差异"}
            return {"available": True, "base_hash": base_hash, "files": files}
        except FileNotFoundError:
            return {"available": False, "reason": "git is not installed"}
        except subprocess.TimeoutExpired:
            return {"available": False, "reason": "git diff timed out"}
        except Exception as e:
            return {"available": False, "reason": str(e)}

    return await asyncio.to_thread(_run_git_file_list)


@router.get("/sessions/{session_id}/git-diff/file")
async def get_git_file_diff(
    session_id: str,
    file_path: str = Query(..., description="Absolute path of the file"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get one Git file diff on demand."""
    repo = SessionRepository(db)
    sess = await repo.get_by_id(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_session_access(sess, user)

    if not sess.git_base_hash:
        return {"available": False, "reason": "No git base hash recorded for this session"}

    diff_text = await asyncio.to_thread(_try_git_file_diff, sess.git_base_hash, file_path)
    if not diff_text:
        return {"available": False, "reason": "无法获取该文件的 Git Diff"}
    return {"available": True, "file_path": file_path, "diff": diff_text}
