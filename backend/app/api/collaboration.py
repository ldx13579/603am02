import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CollaborationEdge, Repo
from app.schemas import CollaborationGraphResponse

router = APIRouter(prefix="/api/collaboration", tags=["collaboration"])


@router.get("/{repo_id}/graph", response_model=CollaborationGraphResponse)
def get_collaboration_graph(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    edges = (
        db.query(CollaborationEdge)
        .filter(CollaborationEdge.repo_id == repo_id)
        .all()
    )

    if not edges:
        from app.services.collaboration import compute_collaboration_graph
        graph_data = compute_collaboration_graph(repo.local_path, repo.branch)
        return graph_data

    author_commits: dict[str, int] = {}
    edge_list = []

    for edge in edges:
        if edge.author_a not in author_commits:
            author_commits[edge.author_a] = 0
        if edge.author_b not in author_commits:
            author_commits[edge.author_b] = 0
        author_commits[edge.author_a] += edge.weight
        author_commits[edge.author_b] += edge.weight

        shared = []
        if edge.shared_files:
            try:
                shared = json.loads(edge.shared_files)
            except (json.JSONDecodeError, TypeError):
                shared = []

        edge_list.append({
            "source": edge.author_a,
            "target": edge.author_b,
            "weight": edge.weight,
            "shared_files": shared,
        })

    nodes = [{"id": author, "commit_count": count} for author, count in author_commits.items()]

    return {"nodes": nodes, "edges": edge_list}
