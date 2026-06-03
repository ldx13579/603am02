from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import cache_service
from app.models import CommitRecord, FileModStat, Repo
from app.schemas import FileModStatResponse, KeywordStatResponse

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/{repo_id}/file-extensions", response_model=list[FileModStatResponse])
def get_file_extension_stats(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    cache_key = f"file_ext_stats:{repo_id}"
    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached

    stats = (
        db.query(FileModStat)
        .filter(FileModStat.repo_id == repo_id)
        .order_by(FileModStat.modification_count.desc())
        .all()
    )

    result = [
        {"extension": s.extension, "file_count": s.file_count, "modification_count": s.modification_count}
        for s in stats
    ]

    settings = get_settings()
    cache_service.set(cache_key, result, ttl=settings.STATS_CACHE_TTL_SECONDS)
    return result


@router.get("/{repo_id}/keywords", response_model=list[KeywordStatResponse])
def get_keyword_stats(
    repo_id: int,
    top_n: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    cache_key = f"keyword_stats:{repo_id}:{top_n}"
    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached

    commits = db.query(CommitRecord).filter(CommitRecord.repo_id == repo_id).all()
    if not commits:
        return []

    from app.services.git_analyzer import CommitInfo
    from app.services.smart_analysis import extract_keywords_tfidf, WordCloudConfig

    commit_infos = [
        CommitInfo(
            hash=c.hash,
            timestamp=c.timestamp,
            author="",
            message=c.message or "",
            files_changed=c.files_changed,
            insertions=c.insertions,
            deletions=c.deletions,
        )
        for c in commits
    ]

    keywords = extract_keywords_tfidf(commit_infos, WordCloudConfig(), top_n=top_n)
    result = [{"keyword": kw, "score": round(score, 4)} for kw, score in keywords]

    settings = get_settings()
    cache_service.set(cache_key, result, ttl=settings.STATS_CACHE_TTL_SECONDS)
    return result
