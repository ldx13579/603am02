import shutil
from datetime import datetime
from pathlib import Path

from app.tasks.celery_app import celery_app
from app.config import get_settings
from app.database import SessionLocal
from app.models import AnalysisRun, CommitRecord, DailyStat, Repo
from app.services.git_analyzer import analyze_repo
from app.services.stats import compute_daily_stats


@celery_app.task(bind=True, name="scan_single_repo", max_retries=2)
def scan_single_repo(self, repo_id: int, since: str | None = None, until: str | None = None):
    db = SessionLocal()
    try:
        repo = db.query(Repo).filter(Repo.id == repo_id).first()
        if not repo:
            return {"repo_id": repo_id, "status": "failed", "error": "Repo not found"}

        run = AnalysisRun(
            repo_id=repo_id,
            celery_task_id=self.request.id,
            status="running",
            started_at=datetime.utcnow(),
        )
        db.add(run)
        db.commit()

        since_dt = datetime.fromisoformat(since) if since else None
        until_dt = datetime.fromisoformat(until) if until else None

        def on_progress(current: int, total: int):
            self.update_state(state="PROGRESS", meta={"current": current, "total": total})

        try:
            commits = analyze_repo(
                repo_path=repo.local_path,
                branch=repo.branch,
                since=since_dt,
                until=until_dt,
                progress_callback=on_progress,
            )
        except (FileNotFoundError, PermissionError, Exception) as e:
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            db.commit()
            return {"repo_id": repo_id, "status": "failed", "error": str(e)}

        db.query(CommitRecord).filter(CommitRecord.repo_id == repo_id).delete()
        db.query(DailyStat).filter(DailyStat.repo_id == repo_id).delete()

        for c in commits:
            record = CommitRecord(
                repo_id=repo_id,
                hash=c.hash,
                timestamp=c.timestamp,
                message=c.message,
                files_changed=c.files_changed,
                insertions=c.insertions,
                deletions=c.deletions,
            )
            db.add(record)

        daily_stats = compute_daily_stats(commits)
        for ds in daily_stats:
            stat = DailyStat(
                repo_id=repo_id,
                date=ds["date"],
                commit_count=ds["commit_count"],
                total_insertions=ds["insertions"],
                total_deletions=ds["deletions"],
                total_files_changed=ds["files_changed"],
            )
            db.add(stat)

        run.status = "completed"
        run.total_commits = len(commits)
        run.completed_at = datetime.utcnow()
        if daily_stats:
            run.date_range_start = daily_stats[0]["date"]
            run.date_range_end = daily_stats[-1]["date"]

        db.commit()

        from app.dependencies import cache_service
        cache_service.invalidate("aggregate_stats:*")

        return {
            "repo_id": repo_id,
            "status": "completed",
            "total_commits": len(commits),
        }
    finally:
        db.close()


@celery_app.task(bind=True, name="scan_all_repos")
def scan_all_repos(self, repo_ids: list[int], since: str | None = None, until: str | None = None):
    results = []
    total = len(repo_ids)

    for i, repo_id in enumerate(repo_ids):
        self.update_state(state="PROGRESS", meta={"current": i, "total": total})
        result = scan_single_repo(repo_id, since, until)
        results.append(result)

    return {"status": "completed", "results": results, "total": total}


@celery_app.task(name="backup_database")
def backup_database():
    settings = get_settings()

    db_url = settings.DATABASE_URL
    db_path = db_url.replace("sqlite:///", "")
    source = Path(db_path)

    if not source.exists():
        return {"status": "skipped", "reason": "Database file not found"}

    backup_dir = Path(settings.DB_BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"analysis_{timestamp}.db"

    shutil.copy2(str(source), str(backup_path))

    backups = sorted(backup_dir.glob("analysis_*.db"), key=lambda p: p.stat().st_mtime)
    keep_count = settings.DB_BACKUP_KEEP_COUNT
    if len(backups) > keep_count:
        for old_backup in backups[:-keep_count]:
            old_backup.unlink()

    return {
        "status": "completed",
        "backup_path": str(backup_path),
        "total_backups": min(len(backups), keep_count),
    }
