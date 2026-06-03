from __future__ import annotations

from app.services.git_analyzer import CommitInfo, analyze_repo
from app.services.stats import compute_daily_stats, compute_weekly_stats, compute_streaks


def generate_report(
    repo_name: str,
    repo_path: str,
    branch: str = "main",
    since=None,
    until=None,
    progress_callback=None,
) -> dict:
    commits = analyze_repo(
        repo_path=repo_path,
        branch=branch,
        since=since,
        until=until,
        progress_callback=progress_callback,
    )

    daily_stats = compute_daily_stats(commits)
    weekly_stats = compute_weekly_stats(daily_stats)
    current_streak, longest_streak = compute_streaks(daily_stats)

    date_range = ("", "")
    if daily_stats:
        date_range = (daily_stats[0]["date"], daily_stats[-1]["date"])

    return {
        "repo_name": repo_name,
        "repo_path": repo_path,
        "branch": branch,
        "total_commits": len(commits),
        "date_range": date_range,
        "daily_stats": daily_stats,
        "weekly_stats": weekly_stats,
        "streak_current": current_streak,
        "streak_longest": longest_streak,
        "commits": [
            {
                "hash": c.hash,
                "timestamp": c.timestamp.isoformat(),
                "author": c.author,
                "message": c.message,
                "files_changed": c.files_changed,
                "insertions": c.insertions,
                "deletions": c.deletions,
            }
            for c in commits
        ],
    }
