import shutil
import logging
from pathlib import Path

import git
from celery.exceptions import SoftTimeLimitExceeded

from app.tasks.celery_app import celery_app
from app.config import get_settings
from app.database import SessionLocal
from app.models import Repo

logger = logging.getLogger(__name__)
settings = get_settings()

RETRYABLE_ERRORS = (
    "Connection refused",
    "Connection timed out",
    "Could not resolve host",
    "SSL",
    "Network is unreachable",
    "Connection reset",
    "HTTP 500",
    "HTTP 502",
    "HTTP 503",
    "fetch-pack",
    "early EOF",
)


def _is_retryable(error_msg: str) -> bool:
    return any(pattern.lower() in error_msg.lower() for pattern in RETRYABLE_ERRORS)


@celery_app.task(
    bind=True,
    name="clone_repo",
    soft_time_limit=settings.SCAN_TIMEOUT_SECONDS,
    time_limit=settings.SCAN_TIMEOUT_SECONDS + 60,
    max_retries=settings.CLONE_MAX_RETRIES,
    default_retry_delay=settings.CLONE_RETRY_BACKOFF,
    autoretry_for=(),
)
def clone_repo(self, repo_id: int):
    db = SessionLocal()
    try:
        repo = db.query(Repo).filter(Repo.id == repo_id).first()
        if not repo or not repo.git_url:
            return {"repo_id": repo_id, "status": "failed", "error": "Invalid repo or missing git_url"}

        repo.clone_status = "cloning"
        db.commit()

        self.update_state(
            state="PROGRESS",
            meta={"stage": "cloning", "progress": 10, "message": "Starting clone..."},
        )

        clone_dir = Path(settings.GIT_CLONE_DIR) / f"repo_{repo_id}"

        if clone_dir.exists():
            shutil.rmtree(str(clone_dir))

        try:
            self.update_state(
                state="PROGRESS",
                meta={"stage": "cloning", "progress": 20, "message": "Shallow clone in progress..."},
            )
            git.Repo.clone_from(
                repo.git_url,
                str(clone_dir),
                branch=repo.branch,
                depth=1,
                single_branch=True,
            )
        except SoftTimeLimitExceeded:
            repo.clone_status = "failed"
            repo.clone_error = "Clone timed out"
            db.commit()
            if clone_dir.exists():
                shutil.rmtree(str(clone_dir))
            raise
        except Exception as e:
            error_msg = str(e)[:500]
            if clone_dir.exists():
                shutil.rmtree(str(clone_dir))

            if _is_retryable(error_msg) and self.request.retries < self.max_retries:
                repo.clone_status = "retrying"
                repo.clone_error = f"Retry {self.request.retries + 1}/{self.max_retries}: {error_msg}"
                db.commit()
                logger.info(
                    f"Retrying clone for repo {repo_id} "
                    f"(attempt {self.request.retries + 1}/{self.max_retries})"
                )
                backoff = min(
                    settings.CLONE_RETRY_BACKOFF * (2 ** self.request.retries),
                    settings.CLONE_RETRY_MAX_BACKOFF,
                )
                raise self.retry(exc=e, countdown=backoff)

            repo.clone_status = "failed"
            repo.clone_error = error_msg
            db.commit()
            return {"repo_id": repo_id, "status": "failed", "error": error_msg}

        self.update_state(
            state="PROGRESS",
            meta={"stage": "fetching_history", "progress": 60, "message": "Fetching full history..."},
        )

        cloned = git.Repo(str(clone_dir))
        try:
            cloned.git.fetch("--unshallow")
        except git.GitCommandError:
            pass

        self.update_state(
            state="PROGRESS",
            meta={"stage": "finalizing", "progress": 90, "message": "Finalizing..."},
        )

        repo.local_path = str(clone_dir)
        repo.clone_status = "ready"
        repo.clone_error = None
        db.commit()

        return {"repo_id": repo_id, "status": "ready", "path": str(clone_dir), "progress": 100}
    except SoftTimeLimitExceeded:
        raise
    except self.MaxRetriesExceededError:
        db2 = SessionLocal()
        try:
            r = db2.query(Repo).filter(Repo.id == repo_id).first()
            if r:
                r.clone_status = "failed"
                r.clone_error = "Max retries exceeded"
                db2.commit()
        finally:
            db2.close()
        return {"repo_id": repo_id, "status": "failed", "error": "Max retries exceeded"}
    except Exception as e:
        logger.error(f"Unexpected error cloning repo {repo_id}: {e}")
        return {"repo_id": repo_id, "status": "failed", "error": str(e)[:500]}
    finally:
        db.close()
