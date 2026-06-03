from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CommitViolation, Repo
from app.schemas import ViolationResponse, ViolationSummary

router = APIRouter(prefix="/api/violations", tags=["violations"])


@router.get("/{repo_id}", response_model=ViolationSummary)
def get_violations(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    violations = (
        db.query(CommitViolation)
        .filter(CommitViolation.repo_id == repo_id)
        .order_by(CommitViolation.detected_at.desc())
        .limit(200)
        .all()
    )

    by_rule: dict[str, int] = defaultdict(int)
    for v in violations:
        by_rule[v.rule_name] += 1

    return ViolationSummary(
        total=len(violations),
        by_rule=dict(by_rule),
        violations=[ViolationResponse.model_validate(v) for v in violations],
    )
