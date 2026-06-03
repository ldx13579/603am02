from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CommitRecord, FileModStat, Repo
from app.schemas import CommitFrequencyResponse, FileModStatResponse, KeywordStatResponse

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/{repo_id}/file-extensions", response_model=list[FileModStatResponse])
def get_file_extension_stats(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    stats = (
        db.query(FileModStat)
        .filter(FileModStat.repo_id == repo_id)
        .order_by(FileModStat.modification_count.desc())
        .all()
    )
    return stats


@router.get("/{repo_id}/keywords", response_model=list[KeywordStatResponse])
def get_keyword_stats(
    repo_id: int,
    top_n: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    commits = db.query(CommitRecord).filter(CommitRecord.repo_id == repo_id).all()
    if not commits:
        return []

    from dataclasses import dataclass, field
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
    return [KeywordStatResponse(keyword=kw, score=round(score, 4)) for kw, score in keywords]
