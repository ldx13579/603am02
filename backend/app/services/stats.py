from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from app.services.git_analyzer import CommitInfo


def compute_daily_stats(commits: list[CommitInfo]) -> list[dict]:
    daily: dict[str, dict] = defaultdict(
        lambda: {"commit_count": 0, "insertions": 0, "deletions": 0, "files_changed": 0}
    )

    for c in commits:
        date_key = c.timestamp.strftime("%Y-%m-%d")
        daily[date_key]["commit_count"] += 1
        daily[date_key]["insertions"] += c.insertions
        daily[date_key]["deletions"] += c.deletions
        daily[date_key]["files_changed"] += c.files_changed

    result = [{"date": k, **v} for k, v in sorted(daily.items())]
    return result


def compute_weekly_stats(daily_stats: list[dict]) -> list[dict]:
    weekly: dict[str, dict] = defaultdict(
        lambda: {"commit_count": 0, "insertions": 0, "deletions": 0, "files_changed": 0}
    )

    for day in daily_stats:
        dt = datetime.strptime(day["date"], "%Y-%m-%d")
        iso_year, iso_week, _ = dt.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"
        weekly[week_key]["commit_count"] += day["commit_count"]
        weekly[week_key]["insertions"] += day["insertions"]
        weekly[week_key]["deletions"] += day["deletions"]
        weekly[week_key]["files_changed"] += day["files_changed"]

    result = [{"week": k, **v} for k, v in sorted(weekly.items())]
    return result


def compute_streaks(daily_stats: list[dict]) -> tuple[int, int]:
    if not daily_stats:
        return 0, 0

    dates_with_commits = set()
    for day in daily_stats:
        if day["commit_count"] > 0:
            dates_with_commits.add(day["date"])

    if not dates_with_commits:
        return 0, 0

    sorted_dates = sorted(dates_with_commits)
    all_dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in sorted_dates]

    longest = 1
    current = 1
    for i in range(1, len(all_dates)):
        if all_dates[i] - all_dates[i - 1] == timedelta(days=1):
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    today = datetime.now().date()
    current_streak = 0
    for d in reversed(all_dates):
        if d == today - timedelta(days=current_streak):
            current_streak += 1
        elif d == today - timedelta(days=current_streak + 1):
            current_streak += 1
        else:
            break

    return current_streak, longest
