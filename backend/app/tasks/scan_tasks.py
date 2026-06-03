from datetime import datetime

from app.tasks.celery_app import celery_app
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
