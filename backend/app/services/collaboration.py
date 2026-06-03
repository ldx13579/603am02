from __future__ import annotations

import logging
from collections import defaultdict
from io import BytesIO
from itertools import combinations
from pathlib import Path

import git
import networkx as nx
from git import InvalidGitRepositoryError

logger = logging.getLogger(__name__)


def compute_collaboration_graph(
    repo_path: str | Path,
    branch: str = "main",
    max_commits: int | None = None,
) -> dict:
    from app.config import get_settings

    if max_commits is None:
        max_commits = get_settings().MAX_COMMITS

    repo_path = Path(repo_path)
    if not repo_path.exists():
        return {"nodes": [], "edges": []}

    try:
        repo = git.Repo(str(repo_path))
    except (InvalidGitRepositoryError, Exception):
        return {"nodes": [], "edges": []}

    try:
        if branch in [b.name for b in repo.branches]:
            rev = branch
        else:
            rev = "HEAD"
    except Exception:
        rev = "HEAD"

    file_authors: dict[str, set[str]] = defaultdict(set)
    author_commits: dict[str, int] = defaultdict(int)

    try:
        for i, commit in enumerate(repo.iter_commits(rev)):
            if i >= max_commits:
                break
            try:
                author = str(commit.author)
                author_commits[author] += 1
                for filepath in commit.stats.files:
                    file_authors[filepath].add(author)
            except Exception:
                continue
    except Exception:
        return {"nodes": [], "edges": []}

    edge_weights: dict[tuple[str, str], int] = defaultdict(int)
    edge_files: dict[tuple[str, str], list[str]] = defaultdict(list)

    for filepath, authors in file_authors.items():
        if len(authors) < 2:
            continue
        for a, b in combinations(sorted(authors), 2):
            edge_weights[(a, b)] += 1
            if len(edge_files[(a, b)]) < 5:
                edge_files[(a, b)].append(filepath)

    connected_authors = set()
    for a, b in edge_weights:
        connected_authors.add(a)
        connected_authors.add(b)

    nodes = [
        {"id": author, "commit_count": author_commits[author]}
        for author in connected_authors
    ]

    edges = [
        {
            "source": pair[0],
            "target": pair[1],
            "weight": weight,
            "shared_files": edge_files[pair][:5],
        }
        for pair, weight in sorted(edge_weights.items(), key=lambda x: -x[1])
    ]

    return {"nodes": nodes, "edges": edges}


def render_collaboration_image(graph_data: dict) -> BytesIO:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    G = nx.Graph()

    for node in graph_data.get("nodes", []):
        G.add_node(node["id"], commit_count=node["commit_count"])

    for edge in graph_data.get("edges", []):
        G.add_edge(edge["source"], edge["target"], weight=edge["weight"])

    buf = BytesIO()

    if len(G.nodes) == 0:
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        ax.text(0.5, 0.5, "No collaboration data", ha="center", va="center", fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf

    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

    commit_counts = [G.nodes[n].get("commit_count", 1) for n in G.nodes]
    max_count = max(commit_counts) if commit_counts else 1
    node_sizes = [300 + (c / max_count) * 2000 for c in commit_counts]

    weights = [G.edges[e].get("weight", 1) for e in G.edges]
    max_weight = max(weights) if weights else 1
    edge_widths = [0.5 + (w / max_weight) * 4 for w in weights]

    nx.draw_networkx_edges(G, pos, ax=ax, width=edge_widths, alpha=0.4, edge_color="#666666")
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes, node_color="#4A90D9", alpha=0.8)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=8, font_weight="bold")

    ax.set_title("Developer Collaboration Network", fontsize=14, fontweight="bold")
    ax.axis("off")

    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf
