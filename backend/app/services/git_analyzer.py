from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import git
from git import InvalidGitRepositoryError, GitCommandError

logger = logging.getLogger(__name__)


@dataclass
class CommitInfo:
    hash: str
    timestamp: datetime
    author: str
    message: str
    files_changed: int
    insertions: int
    deletions: int


def safe_message(commit: git.Commit) -> str:
    msg = commit.message
    if isinstance(msg, bytes):
        for enc in ("utf-8", "latin-1", "cp1252", "gbk"):
            try:
                return msg.decode(enc).strip()[:200]
            except (UnicodeDecodeError, LookupError):
                continue
        return msg.decode("utf-8", errors="replace").strip()[:200]
    return (msg or "").strip()[:200]


def analyze_repo(
    repo_path: str | Path,
    branch: str = "main",
    since: datetime | None = None,
    until: datetime | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[CommitInfo]:
    repo_path = Path(repo_path)

    if not repo_path.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

    try:
        repo = git.Repo(str(repo_path))
    except InvalidGitRepositoryError:
        raise InvalidGitRepositoryError(f"Not a valid git repository: {repo_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied accessing repository: {repo_path}")

    try:
        if branch in [b.name for b in repo.branches]:
            rev = branch
        elif repo.remotes and branch in [
            ref.remote_head for ref in repo.remotes.origin.refs
        ]:
            rev = f"origin/{branch}"
        else:
            rev = repo.active_branch.name
    except (GitCommandError, TypeError, ValueError):
        rev = "HEAD"

    kwargs: dict = {}
    if since:
        kwargs["since"] = since.isoformat()
    if until:
        kwargs["until"] = until.isoformat()

    try:
        commits_iter = list(repo.iter_commits(rev, **kwargs))
    except GitCommandError as e:
        raise GitCommandError(e.command, e.status, stderr_value=f"Failed to iterate commits: {e}")

    total = len(commits_iter)
    results: list[CommitInfo] = []

    for i, commit in enumerate(commits_iter):
        try:
            stats = commit.stats.total
            info = CommitInfo(
                hash=commit.hexsha[:8],
                timestamp=datetime.fromtimestamp(commit.committed_date),
                author=str(commit.author),
                message=safe_message(commit),
                files_changed=stats.get("files", 0),
                insertions=stats.get("insertions", 0),
                deletions=stats.get("deletions", 0),
            )
            results.append(info)
        except Exception as e:
            logger.warning(f"Skipping commit {commit.hexsha[:8]}: {e}")
            continue

        if progress_callback and (i % 100 == 0 or i == total - 1):
            progress_callback(i + 1, total)

    return results
