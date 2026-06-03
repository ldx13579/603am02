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


@celery_app.task(
    bind=True,
    name="clone_repo",
    soft_time_limit=settings.SCAN_TIMEOUT_SECONDS,
    time_limit=settings.SCAN_TIMEOUT_SECONDS + 60,
    max_retries=1,
)
def clone_repo(self, repo_id: int):
    db = SessionLocal()
    try:
        repo = db.query(Repo).filter(Repo.id == repo_id).first()
        if not repo or not repo.git_url:
            return {"repo_id": repo_id, "status": "failed", "error": "Invalid repo or missing git_url"}

        repo.clone_status = "cloning"
        db.commit()

        clone_dir = Path(settings.GIT_CLONE_DIR) / f"repo_{repo_id}"

        if clone_dir.exists():
            shutil.rmtree(str(clone_dir))

        try:
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
            repo.clone_status = "failed"
            repo.clone_error = str(e)[:500]
            db.commit()
            if clone_dir.exists():
                shutil.rmtree(str(clone_dir))
            return {"repo_id": repo_id, "status": "failed", "error": str(e)[:500]}

        cloned = git.Repo(str(clone_dir))
        try:
            cloned.git.fetch("--unshallow")
        except git.GitCommandError:
            pass

        repo.local_path = str(clone_dir)
        repo.clone_status = "ready"
        repo.clone_error = None
        db.commit()

        return {"repo_id": repo_id, "status": "ready", "path": str(clone_dir)}
    except SoftTimeLimitExceeded:
        raise
    except Exception as e:
        logger.error(f"Unexpected error cloning repo {repo_id}: {e}")
        return {"repo_id": repo_id, "status": "failed", "error": str(e)[:500]}
    finally:
        db.close()
