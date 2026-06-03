import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CollaborationEdge, CommitViolation, DailyStat, Repo
from app.services.pdf_export import generate_pdf_report
from app.services.stats import compute_weekly_stats, compute_streaks

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/{repo_id}/pdf")
def export_pdf(repo_id: int, db: Session = Depends(get_db)):
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
        raise HTTPException(status_code=404, detail="No analysis data for this repository")

    daily_stats = [
        {
            "date": s.date,
            "commit_count": s.commit_count,
            "insertions": s.total_insertions,
            "deletions": s.total_deletions,
            "files_changed": s.total_files_changed,
        }
        for s in stats
    ]

    weekly_stats = compute_weekly_stats(daily_stats)
    current_streak, longest_streak = compute_streaks(daily_stats)

    # Collaboration data
    edges = db.query(CollaborationEdge).filter(CollaborationEdge.repo_id == repo_id).all()
    collaboration_data = None
    if edges:
        author_commits: dict[str, int] = {}
        edge_list = []
        for edge in edges:
            author_commits.setdefault(edge.author_a, 0)
            author_commits.setdefault(edge.author_b, 0)
            author_commits[edge.author_a] += edge.weight
            author_commits[edge.author_b] += edge.weight
            shared = []
            if edge.shared_files:
                try:
                    shared = json.loads(edge.shared_files)
                except (json.JSONDecodeError, TypeError):
                    pass
            edge_list.append({
                "source": edge.author_a,
                "target": edge.author_b,
                "weight": edge.weight,
                "shared_files": shared,
            })
        collaboration_data = {
            "nodes": [{"id": a, "commit_count": c} for a, c in author_commits.items()],
            "edges": edge_list,
        }

    # Violations
    violations_raw = (
        db.query(CommitViolation)
        .filter(CommitViolation.repo_id == repo_id)
        .order_by(CommitViolation.detected_at.desc())
        .limit(50)
        .all()
    )
    violations = [
        {
            "commit_hash": v.commit_hash,
            "rule_name": v.rule_name,
            "severity": v.severity,
            "description": v.description,
            "author": v.author,
        }
        for v in violations_raw
    ] if violations_raw else None

    buffer = generate_pdf_report(
        repo_name=repo.name,
        daily_stats=daily_stats,
        weekly_stats=weekly_stats,
        collaboration_data=collaboration_data,
        violations=violations,
        streak_current=current_streak,
        streak_longest=longest_streak,
    )

    filename = f"{repo.name.replace(' ', '_')}_report.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
