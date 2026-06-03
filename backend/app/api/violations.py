from collections import defaultdict

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import CommitViolation, Repo
from app.schemas import RuleConfigResponse, RuleConfigUpdate, ViolationResponse, ViolationSummary

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


@router.get("/rules/config", response_model=RuleConfigResponse)
def get_rule_config():
    settings = get_settings()
    return RuleConfigResponse(
        enabled=settings.RULE_ENABLED,
        max_files_per_commit=settings.RULE_MAX_FILES_PER_COMMIT,
        min_message_length=settings.RULE_MIN_MESSAGE_LENGTH,
        max_lines_changed=settings.RULE_MAX_LINES_CHANGED,
        dingtalk_webhook_url=bool(settings.DINGTALK_WEBHOOK_URL),
        dingtalk_silence_minutes=settings.DINGTALK_SILENCE_MINUTES,
    )


@router.put("/rules/config", response_model=RuleConfigResponse)
def update_rule_config(config: RuleConfigUpdate = Body(...)):
    import os

    if config.enabled is not None:
        os.environ["RULE_ENABLED"] = str(config.enabled).lower()
    if config.max_files_per_commit is not None:
        os.environ["RULE_MAX_FILES_PER_COMMIT"] = str(config.max_files_per_commit)
    if config.min_message_length is not None:
        os.environ["RULE_MIN_MESSAGE_LENGTH"] = str(config.min_message_length)
    if config.max_lines_changed is not None:
        os.environ["RULE_MAX_LINES_CHANGED"] = str(config.max_lines_changed)
    if config.dingtalk_silence_minutes is not None:
        os.environ["DINGTALK_SILENCE_MINUTES"] = str(config.dingtalk_silence_minutes)

    # Clear cached settings so next call picks up env changes
    from app.config import get_settings as _get_settings
    _get_settings.cache_clear()

    settings = get_settings()
    return RuleConfigResponse(
        enabled=settings.RULE_ENABLED,
        max_files_per_commit=settings.RULE_MAX_FILES_PER_COMMIT,
        min_message_length=settings.RULE_MIN_MESSAGE_LENGTH,
        max_lines_changed=settings.RULE_MAX_LINES_CHANGED,
        dingtalk_webhook_url=bool(settings.DINGTALK_WEBHOOK_URL),
        dingtalk_silence_minutes=settings.DINGTALK_SILENCE_MINUTES,
    )
