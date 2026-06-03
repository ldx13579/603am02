import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import CollaborationEdge, Repo
from app.schemas import CollaborationGraphResponse

router = APIRouter(prefix="/api/collaboration", tags=["collaboration"])


def _truncate_graph(nodes: list[dict], edges: list[dict], max_nodes: int) -> dict:
    if len(nodes) <= max_nodes:
        return {"nodes": nodes, "edges": edges}

    sorted_nodes = sorted(nodes, key=lambda n: n["commit_count"], reverse=True)
    top_nodes = sorted_nodes[:max_nodes]
    top_ids = {n["id"] for n in top_nodes}

    others = sorted_nodes[max_nodes:]
    others_total_commits = sum(n["commit_count"] for n in others)

    top_nodes.append({
        "id": f"Others ({len(others)})",
        "commit_count": others_total_commits,
        "is_cluster": True,
    })
    cluster_id = f"Others ({len(others)})"

    other_ids = {n["id"] for n in others}
    filtered_edges = []
    cluster_edges: dict[str, int] = {}

    for edge in edges:
        src_in_top = edge["source"] in top_ids
        tgt_in_top = edge["target"] in top_ids

        if src_in_top and tgt_in_top:
            filtered_edges.append(edge)
        elif src_in_top and edge["target"] in other_ids:
            cluster_edges[edge["source"]] = cluster_edges.get(edge["source"], 0) + edge["weight"]
        elif tgt_in_top and edge["source"] in other_ids:
            cluster_edges[edge["target"]] = cluster_edges.get(edge["target"], 0) + edge["weight"]

    for author, weight in cluster_edges.items():
        filtered_edges.append({
            "source": author,
            "target": cluster_id,
            "weight": weight,
            "shared_files": [],
        })

    return {"nodes": top_nodes, "edges": filtered_edges}


@router.get("/{repo_id}/graph", response_model=CollaborationGraphResponse)
def get_collaboration_graph(
    repo_id: int,
    max_nodes: int = Query(default=None, ge=5, le=200),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if max_nodes is None:
        max_nodes = settings.COLLABORATION_MAX_NODES

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
        return _truncate_graph(graph_data["nodes"], graph_data["edges"], max_nodes)

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

    return _truncate_graph(nodes, edge_list, max_nodes)
