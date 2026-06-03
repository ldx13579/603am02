from datetime import datetime
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import cache_service
from app.models import AnalysisRun, CommitRecord, DailyStat, Repo
from app.schemas import (
    AnalysisTriggerRequest,
    AnalysisTriggerResponse,
    CommitFrequencyResponse,
    DailyStatResponse,
    ReportResponse,
    WeeklyStatResponse,
)
from app.services.stats import compute_weekly_stats, compute_streaks

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/trigger", response_model=AnalysisTriggerResponse)
def trigger_analysis(data: AnalysisTriggerRequest, db: Session = Depends(get_db)):
    from app.tasks.scan_tasks import scan_all_repos

    repo_ids = data.repo_ids
    if not repo_ids:
        repos = db.query(Repo).filter(Repo.is_active == True).all()
        repo_ids = [r.id for r in repos]

    if not repo_ids:
        raise HTTPException(status_code=400, detail="No active repositories to analyze")

    task = scan_all_repos.delay(repo_ids, data.since, data.until)

    return AnalysisTriggerResponse(task_id=task.id, status="PENDING")


@router.get("/reports")
def list_reports(db: Session = Depends(get_db)):
    runs = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.status == "completed")
        .order_by(AnalysisRun.completed_at.desc())
        .limit(50)
        .all()
    )
    results = []
    for run in runs:
        repo = db.query(Repo).filter(Repo.id == run.repo_id).first()
        results.append({
            "run_id": run.id,
            "repo_id": run.repo_id,
            "repo_name": repo.name if repo else "Unknown",
            "total_commits": run.total_commits,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "date_range": [run.date_range_start, run.date_range_end],
        })
    return results


@router.get("/reports/{repo_id}", response_model=ReportResponse)
def get_report(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    stats = (
        db.query(DailyStat)
        .filter(DailyStat.repo_id == repo_id)
        .order_by(DailyStat.date)
        .all()
    )

    if not stats:
        raise HTTPException(status_code=404, detail="No analysis data found for this repository")

    daily = [
        {
            "date": s.date,
            "commit_count": s.commit_count,
            "insertions": s.total_insertions,
            "deletions": s.total_deletions,
            "files_changed": s.total_files_changed,
        }
        for s in stats
    ]

    weekly = compute_weekly_stats(daily)
    current_streak, longest_streak = compute_streaks(daily)

    date_range = (stats[0].date, stats[-1].date) if stats else ("", "")
    total_commits = sum(s.commit_count for s in stats)

    return ReportResponse(
        repo_id=repo_id,
        repo_name=repo.name,
        total_commits=total_commits,
        date_range=date_range,
        daily_stats=[DailyStatResponse(**d) for d in daily],
        weekly_stats=[WeeklyStatResponse(**w) for w in weekly],
        streak_current=current_streak,
        streak_longest=longest_streak,
    )


@router.get("/reports/{repo_id}/daily")
def get_daily_stats(
    repo_id: int,
    since: str | None = None,
    until: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(DailyStat).filter(DailyStat.repo_id == repo_id)
    if since:
        query = query.filter(DailyStat.date >= since)
    if until:
        query = query.filter(DailyStat.date <= until)

    stats = query.order_by(DailyStat.date).all()
    return [
        {
            "date": s.date,
            "commit_count": s.commit_count,
            "insertions": s.total_insertions,
            "deletions": s.total_deletions,
            "files_changed": s.total_files_changed,
        }
        for s in stats
    ]


@router.get("/reports/aggregate")
def get_aggregate_stats(
    since: str | None = None,
    until: str | None = None,
    db: Session = Depends(get_db),
):
    cache_key = f"aggregate_stats:{since or 'all'}:{until or 'all'}"
    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached

    query = db.query(DailyStat)
    if since:
        query = query.filter(DailyStat.date >= since)
    if until:
        query = query.filter(DailyStat.date <= until)

    stats = query.order_by(DailyStat.date).all()

    aggregated = defaultdict(lambda: {"commit_count": 0, "insertions": 0, "deletions": 0, "files_changed": 0})

    for s in stats:
        aggregated[s.date]["commit_count"] += s.commit_count
        aggregated[s.date]["insertions"] += s.total_insertions
        aggregated[s.date]["deletions"] += s.total_deletions
        aggregated[s.date]["files_changed"] += s.total_files_changed

    result = [{"date": k, **v} for k, v in sorted(aggregated.items())]

    cache_service.set(cache_key, result)

    return result


@router.get("/reports/{repo_id}/frequency", response_model=list[CommitFrequencyResponse])
def get_commit_frequency(
    repo_id: int,
    granularity: str = Query(default="weekly", regex="^(daily|weekly|monthly|quarterly|yearly)$"),
    since: str | None = None,
    until: str | None = None,
    db: Session = Depends(get_db),
):
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    query = db.query(DailyStat).filter(DailyStat.repo_id == repo_id)
    if since:
        query = query.filter(DailyStat.date >= since)
    if until:
        query = query.filter(DailyStat.date <= until)

    stats = query.order_by(DailyStat.date).all()

    if granularity == "daily":
        return [
            CommitFrequencyResponse(
                period=s.date,
                commit_count=s.commit_count,
                insertions=s.total_insertions,
                deletions=s.total_deletions,
                files_changed=s.total_files_changed,
            )
            for s in stats
        ]

    grouped = defaultdict(lambda: {"commit_count": 0, "insertions": 0, "deletions": 0, "files_changed": 0})

    for s in stats:
        from datetime import date as date_type
        d = date_type.fromisoformat(s.date)
        if granularity == "weekly":
            key = f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}"
        elif granularity == "monthly":
            key = s.date[:7]
        elif granularity == "quarterly":
            quarter = (d.month - 1) // 3 + 1
            key = f"{d.year}-Q{quarter}"
        else:
            key = str(d.year)
        grouped[key]["commit_count"] += s.commit_count
        grouped[key]["insertions"] += s.total_insertions
        grouped[key]["deletions"] += s.total_deletions
        grouped[key]["files_changed"] += s.total_files_changed

    return [
        CommitFrequencyResponse(period=k, **v)
        for k, v in sorted(grouped.items())
    ]
