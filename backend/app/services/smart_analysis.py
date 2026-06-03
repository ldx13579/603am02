from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud

from app.services.git_analyzer import CommitInfo


LATE_NIGHT_START = 23
LATE_NIGHT_END = 5


def _is_late_night(hour: int) -> bool:
    return hour >= LATE_NIGHT_START or hour < LATE_NIGHT_END


def _preprocess_messages(commits: list[CommitInfo]) -> list[str]:
    docs = []
    for c in commits:
        msg = c.message.lower().strip()
        msg = re.sub(r"merge (branch|pull request|remote)", "", msg)
        msg = re.sub(r"#\d+", "", msg)
        msg = re.sub(r"[^a-z一-鿿\s]", " ", msg)
        msg = re.sub(r"\s+", " ", msg).strip()
        if len(msg) > 2:
            docs.append(msg)
    return docs


def extract_keywords_tfidf(commits: list[CommitInfo], top_n: int = 50) -> list[tuple[str, float]]:
    docs = _preprocess_messages(commits)
    if not docs:
        return []

    vectorizer = TfidfVectorizer(
        max_features=500,
        ngram_range=(1, 2),
        stop_words="english",
        min_df=2,
        max_df=0.85,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(docs)
    except ValueError:
        vectorizer_fallback = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            stop_words="english",
            min_df=1,
        )
        tfidf_matrix = vectorizer_fallback.fit_transform(docs)
        vectorizer = vectorizer_fallback

    feature_names = vectorizer.get_feature_names_out()
    scores = np.asarray(tfidf_matrix.sum(axis=0)).flatten()

    top_indices = scores.argsort()[::-1][:top_n]
    keywords = [(feature_names[i], float(scores[i])) for i in top_indices if scores[i] > 0]
    return keywords


def generate_wordcloud(keywords: list[tuple[str, float]], output_path: Path) -> Path:
    if not keywords:
        return output_path

    freq_dict = {word: score for word, score in keywords}

    wc = WordCloud(
        width=1200,
        height=600,
        background_color="white",
        colormap="viridis",
        max_words=100,
        relative_scaling=0.5,
        prefer_horizontal=0.7,
    )
    wc.generate_from_frequencies(freq_dict)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("Commit Message Keywords (TF-IDF)", fontsize=14, pad=10)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output_path


def compute_late_night_ratio(commits: list[CommitInfo]) -> dict:
    if not commits:
        return {"total": 0, "late_night_count": 0, "ratio": 0.0}

    late_count = sum(1 for c in commits if _is_late_night(c.timestamp.hour))

    return {
        "total": len(commits),
        "late_night_count": late_count,
        "ratio": round(late_count / len(commits), 4),
    }


def compute_author_late_night(commits: list[CommitInfo]) -> dict[str, dict]:
    author_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "late_night": 0})

    for c in commits:
        author = c.author
        author_stats[author]["total"] += 1
        if _is_late_night(c.timestamp.hour):
            author_stats[author]["late_night"] += 1

    result = {}
    for author, stats in author_stats.items():
        result[author] = {
            **stats,
            "ratio": round(stats["late_night"] / stats["total"], 4) if stats["total"] > 0 else 0.0,
        }
    return result


def compute_schedule_heatmap_data(commits: list[CommitInfo]) -> np.ndarray:
    heatmap = np.zeros((7, 24), dtype=int)

    for c in commits:
        weekday = c.timestamp.weekday()
        hour = c.timestamp.hour
        heatmap[weekday][hour] += 1

    return heatmap


def generate_schedule_heatmap(commits: list[CommitInfo], output_path: Path) -> Path:
    heatmap_data = compute_schedule_heatmap_data(commits)

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours = [f"{h:02d}:00" for h in range(24)]

    fig, ax = plt.subplots(figsize=(16, 5))

    colors = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
    cmap = LinearSegmentedColormap.from_list("github", colors, N=256)

    im = ax.imshow(heatmap_data, cmap=cmap, aspect="auto", interpolation="nearest")

    ax.set_xticks(range(24))
    ax.set_xticklabels(hours, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(7))
    ax.set_yticklabels(days, fontsize=10)

    ax.axvspan(LATE_NIGHT_START - 0.5, 23.5, alpha=0.08, color="red")
    ax.axvspan(-0.5, LATE_NIGHT_END - 0.5, alpha=0.08, color="red")

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Commit Count", fontsize=10)

    ax.set_title("Team Schedule Heatmap (Commits by Day & Hour)", fontsize=13, pad=12)
    ax.set_xlabel("Hour of Day", fontsize=10)
    ax.set_ylabel("Day of Week", fontsize=10)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output_path


def run_smart_analysis(
    commits: list[CommitInfo],
    output_dir: Path,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    keywords = extract_keywords_tfidf(commits)

    wordcloud_path = output_dir / "wordcloud.png"
    generate_wordcloud(keywords, wordcloud_path)

    late_night_stats = compute_late_night_ratio(commits)

    heatmap_path = output_dir / "schedule_heatmap.png"
    generate_schedule_heatmap(commits, heatmap_path)

    return {
        "keywords": keywords[:30],
        "late_night": late_night_stats,
        "heatmap_data": compute_schedule_heatmap_data(commits).tolist(),
        "output_files": {
            "wordcloud": str(wordcloud_path),
            "heatmap": str(heatmap_path),
        },
    }
