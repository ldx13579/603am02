import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path

from celery.exceptions import SoftTimeLimitExceeded

logger = logging.getLogger(__name__)

from app.tasks.celery_app import celery_app
from app.config import get_settings
from app.database import SessionLocal
from app.models import AnalysisRun, CollaborationEdge, CommitRecord, CommitViolation, DailyStat, FileModStat, Repo
from app.services.git_analyzer import analyze_repo, compute_file_extension_stats
from app.services.stats import compute_daily_stats


@celery_app.task(bind=True, name="scan_single_repo", max_retries=2)
def scan_single_repo(self, repo_id: int, since: str | None = None, until: str | None = None):
    db = SessionLocal()
    try:
        repo = db.query(Repo).filter(Repo.id == repo_id).first()
        if not repo:
            return {"repo_id": repo_id, "status": "failed", "error": "Repo not found"}

        if repo.source_type == "remote" and repo.clone_status != "ready":
            return {"repo_id": repo_id, "status": "failed", "error": "Repo not yet cloned"}

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
        except SoftTimeLimitExceeded:
            run.status = "failed"
            run.error_message = "Analysis timed out"
            run.completed_at = datetime.utcnow()
            db.commit()
            return {"repo_id": repo_id, "status": "failed", "error": "Analysis timed out"}
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)[:500]
            run.completed_at = datetime.utcnow()
            db.commit()
            return {"repo_id": repo_id, "status": "failed", "error": str(e)}

        db.query(CommitRecord).filter(CommitRecord.repo_id == repo_id).delete()
        db.query(DailyStat).filter(DailyStat.repo_id == repo_id).delete()
        db.query(FileModStat).filter(FileModStat.repo_id == repo_id).delete()

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

        ext_stats = compute_file_extension_stats(repo.local_path, repo.branch)
        for ext, data in ext_stats.items():
            db.add(FileModStat(
                repo_id=repo_id,
                extension=ext,
                file_count=data["file_count"],
                modification_count=data["modification_count"],
            ))

        # Compute collaboration graph
        import json
        from app.services.collaboration import compute_collaboration_graph
        db.query(CollaborationEdge).filter(CollaborationEdge.repo_id == repo_id).delete()
        collab_data = compute_collaboration_graph(repo.local_path, repo.branch)
        for edge in collab_data.get("edges", []):
            db.add(CollaborationEdge(
                repo_id=repo_id,
                author_a=edge["source"],
                author_b=edge["target"],
                weight=edge["weight"],
                shared_files=json.dumps(edge["shared_files"]),
            ))

        # Rule engine: detect violations
        from app.services.rule_engine import create_default_engine
        settings = get_settings()
        if settings.RULE_ENABLED:
            db.query(CommitViolation).filter(CommitViolation.repo_id == repo_id).delete()
            engine = create_default_engine(settings)
            violations = engine.evaluate(commits)
            for v in violations:
                db.add(CommitViolation(
                    repo_id=repo_id,
                    commit_hash=v.commit_hash,
                    rule_name=v.rule_name,
                    severity=v.severity,
                    description=v.description,
                    author=v.author,
                ))
            db.flush()

            if violations and settings.DINGTALK_WEBHOOK_URL:
                from app.services.dingtalk import send_dingtalk_alert
                try:
                    send_dingtalk_alert(settings.DINGTALK_WEBHOOK_URL, violations, repo.name)
                except Exception as e:
                    logger.warning(f"DingTalk alert failed: {e}")

        run.status = "completed"
        run.total_commits = len(commits)
        run.completed_at = datetime.utcnow()
        if daily_stats:
            run.date_range_start = daily_stats[0]["date"]
            run.date_range_end = daily_stats[-1]["date"]

        db.commit()

        from app.dependencies import cache_service
        cache_service.invalidate("aggregate_stats:*")
        cache_service.invalidate(f"file_ext_stats:{repo_id}")
        cache_service.invalidate(f"keyword_stats:{repo_id}:*")

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

    db = SessionLocal()
    try:
        timeout = 60
        poll_interval = 5
        elapsed = 0

        while elapsed < timeout:
            running = (
                db.query(AnalysisRun)
                .filter(AnalysisRun.status.in_(["pending", "running"]))
                .count()
            )
            if running == 0:
                break
            time.sleep(poll_interval)
            elapsed += poll_interval
            db.expire_all()
    finally:
        db.close()

    backup_dir = Path(settings.DB_BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"githabits_{timestamp}.sql"

    try:
        result = subprocess.run(
            ["pg_dump", settings.DATABASE_URL, "-f", str(backup_path)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            return {"status": "failed", "error": result.stderr[:500]}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"status": "failed", "error": str(e)[:200]}

    backups = sorted(backup_dir.glob("githabits_*.sql"), key=lambda p: p.stat().st_mtime)
    keep_count = settings.DB_BACKUP_KEEP_COUNT
    if len(backups) > keep_count:
        for old_backup in backups[:-keep_count]:
            old_backup.unlink()

    return {
        "status": "completed",
        "backup_path": str(backup_path),
        "total_backups": min(len(backups), keep_count),
    }
