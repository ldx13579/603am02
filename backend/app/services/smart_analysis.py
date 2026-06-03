from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Callable

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud

from app.services.git_analyzer import CommitInfo


COMMIT_STOPWORDS_EN = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "because", "but", "and", "or", "if", "while", "about", "up",
    "that", "this", "these", "those", "it", "its", "we", "they", "them",
    "what", "which", "who", "whom", "whose", "he", "she", "him", "her",
    "i", "me", "my", "you", "your", "also", "get", "got", "use", "using",
    "make", "made", "new", "now", "see", "way", "well", "back", "file",
    "files", "change", "changes", "changed", "commit", "commits",
    "update", "updated", "updates", "add", "added", "remove", "removed",
    "set", "pr", "wip", "todo", "done", "etc", "via", "ie", "eg",
    "instead", "since", "still", "already", "yet", "much", "many",
}

COMMIT_STOPWORDS_ZH = {
    "的", "了", "和", "是", "在", "有", "不", "这", "那", "就",
    "也", "都", "要", "会", "对", "为", "与", "或", "及", "等",
    "把", "被", "让", "给", "从", "到", "上", "下", "中", "里",
    "但", "而", "又", "所", "以", "因", "如", "则", "已", "于",
    "着", "过", "吗", "呢", "吧", "啊", "哦", "嗯", "呀", "哈",
    "个", "些", "每", "各", "某", "该", "其", "此", "之", "者",
    "来", "去", "出", "进", "做", "用", "可", "能", "将", "还",
    "很", "更", "最", "比", "太", "非常", "十分", "特别", "相当",
    "一个", "一些", "一下", "这个", "那个", "什么", "怎么", "如何",
    "我们", "他们", "它们", "你们", "自己", "大家", "所有", "没有",
    "可以", "需要", "应该", "必须", "已经", "正在", "通过", "进行",
    "然后", "但是", "因为", "所以", "如果", "虽然", "不过", "而且",
    "或者", "以及", "关于", "按照", "根据", "由于", "对于", "除了",
    "提交", "修改", "代码", "文件", "功能", "问题", "处理", "完成",
    "实现", "优化", "调整", "增加", "删除", "更新", "修复", "添加",
}

COMMIT_STOPWORDS = COMMIT_STOPWORDS_EN | COMMIT_STOPWORDS_ZH

HEATMAP_COLOR_SCHEMES = {
    "github": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    "ocean": ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"],
    "fire": ["#fff5f0", "#fcbba1", "#fb6a4a", "#cb181d", "#67000d"],
    "purple": ["#f2f0f7", "#cbc9e2", "#9e9ac8", "#756bb1", "#54278f"],
    "warm": ["#ffffcc", "#fed976", "#fd8d3c", "#e31a1c", "#800026"],
}


@dataclass
class WordCloudConfig:
    max_font_size: int = 80
    min_font_size: int = 10
    max_words: int = 100
    colormap: str = "viridis"
    color_list: list[str] = field(default_factory=list)
    background_color: str = "white"
    width: int = 1200
    height: int = 600
    prefer_horizontal: float = 0.7
    custom_stopwords: list[str] = field(default_factory=list)


@dataclass
class SmartAnalysisConfig:
    late_night_start: int = 23
    late_night_end: int = 5
    timezone: str = ""
    heatmap_scheme: str = "github"
    wordcloud: WordCloudConfig = field(default_factory=WordCloudConfig)

    def __post_init__(self):
        if isinstance(self.wordcloud, dict):
            self.wordcloud = WordCloudConfig(**self.wordcloud)

    def get_tz(self) -> timezone | None:
        if not self.timezone:
            return None
        tz_str = self.timezone.strip()
        if tz_str.upper() == "UTC":
            return timezone.utc
        match = re.match(r"^UTC([+-])(\d{1,2})(?::(\d{2}))?$", tz_str, re.IGNORECASE)
        if match:
            sign = 1 if match.group(1) == "+" else -1
            hours = int(match.group(2))
            minutes = int(match.group(3)) if match.group(3) else 0
            return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))
        try:
            import zoneinfo
            return zoneinfo.ZoneInfo(tz_str)
        except (ImportError, KeyError):
            return None


def load_analysis_config(raw: dict | None) -> SmartAnalysisConfig:
    if not raw:
        return SmartAnalysisConfig()

    wc_raw = raw.get("wordcloud", {})
    wc_config = WordCloudConfig(**{k: v for k, v in wc_raw.items() if k in WordCloudConfig.__dataclass_fields__})

    return SmartAnalysisConfig(
        late_night_start=raw.get("late_night_start", 23),
        late_night_end=raw.get("late_night_end", 5),
        timezone=raw.get("timezone", ""),
        heatmap_scheme=raw.get("heatmap_scheme", "github"),
        wordcloud=wc_config,
    )


def _get_local_hour(commit: CommitInfo, config: SmartAnalysisConfig) -> tuple[int, int]:
    tz = config.get_tz()
    if tz is None:
        return commit.timestamp.weekday(), commit.timestamp.hour
    utc_dt = commit.timestamp.replace(tzinfo=timezone.utc)
    local_dt = utc_dt.astimezone(tz)
    return local_dt.weekday(), local_dt.hour


def _is_late_night(hour: int, start: int, end: int) -> bool:
    if start > end:
        return hour >= start or hour < end
    return start <= hour < end


def _get_stopwords(config: WordCloudConfig) -> set[str]:
    stopwords = COMMIT_STOPWORDS.copy()
    stopwords.update(w.lower() for w in config.custom_stopwords)
    return stopwords


def _build_color_func(color_list: list[str]):
    import random
    colors = [c.strip() for c in color_list if c.strip()]
    if not colors:
        return None

    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        return random.choice(colors)

    return color_func


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


def extract_keywords_tfidf(
    commits: list[CommitInfo],
    config: WordCloudConfig,
    top_n: int = 50,
) -> list[tuple[str, float]]:
    docs = _preprocess_messages(commits)
    if not docs:
        return []

    stopwords = list(_get_stopwords(config))

    vectorizer = TfidfVectorizer(
        max_features=500,
        ngram_range=(1, 2),
        stop_words=stopwords,
        min_df=2,
        max_df=0.85,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(docs)
    except ValueError:
        vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            stop_words=stopwords,
            min_df=1,
        )
        tfidf_matrix = vectorizer.fit_transform(docs)

    feature_names = vectorizer.get_feature_names_out()
    scores = np.asarray(tfidf_matrix.sum(axis=0)).flatten()

    top_indices = scores.argsort()[::-1][:top_n]
    keywords = [(feature_names[i], float(scores[i])) for i in top_indices if scores[i] > 0]
    return keywords


def generate_wordcloud(
    keywords: list[tuple[str, float]],
    output_path: Path,
    config: WordCloudConfig,
) -> Path:
    if not keywords:
        return output_path

    freq_dict = {word: score for word, score in keywords}

    color_func = _build_color_func(config.color_list)

    wc_kwargs = dict(
        width=config.width,
        height=config.height,
        max_font_size=config.max_font_size,
        min_font_size=config.min_font_size,
        max_words=config.max_words,
        background_color=config.background_color,
        relative_scaling=0.5,
        prefer_horizontal=config.prefer_horizontal,
    )

    if color_func:
        wc_kwargs["color_func"] = color_func
    else:
        wc_kwargs["colormap"] = config.colormap

    wc = WordCloud(**wc_kwargs)
    wc.generate_from_frequencies(freq_dict)

    fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("Commit Message Keywords (TF-IDF)", fontsize=14, pad=10)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output_path


def compute_late_night_ratio(commits: list[CommitInfo], config: SmartAnalysisConfig) -> dict:
    if not commits:
        return {"total": 0, "late_night_count": 0, "ratio": 0.0, "period": "N/A", "timezone": config.timezone or "local"}

    start, end = config.late_night_start, config.late_night_end
    late_count = sum(
        1 for c in commits if _is_late_night(_get_local_hour(c, config)[1], start, end)
    )

    return {
        "total": len(commits),
        "late_night_count": late_count,
        "ratio": round(late_count / len(commits), 4),
        "period": f"{start:02d}:00-{end:02d}:00",
        "timezone": config.timezone or "local",
    }


def compute_author_late_night(commits: list[CommitInfo], config: SmartAnalysisConfig) -> dict[str, dict]:
    author_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "late_night": 0})
    start, end = config.late_night_start, config.late_night_end

    for c in commits:
        author = c.author
        _, hour = _get_local_hour(c, config)
        author_stats[author]["total"] += 1
        if _is_late_night(hour, start, end):
            author_stats[author]["late_night"] += 1

    result = {}
    for author, stats in author_stats.items():
        result[author] = {
            **stats,
            "ratio": round(stats["late_night"] / stats["total"], 4) if stats["total"] > 0 else 0.0,
        }
    return result


def compute_schedule_heatmap_data(commits: list[CommitInfo], config: SmartAnalysisConfig) -> np.ndarray:
    heatmap = np.zeros((7, 24), dtype=int)

    for c in commits:
        weekday, hour = _get_local_hour(c, config)
        heatmap[weekday][hour] += 1

    return heatmap


def generate_schedule_heatmap(
    commits: list[CommitInfo],
    output_path: Path,
    config: SmartAnalysisConfig,
) -> Path:
    heatmap_data = compute_schedule_heatmap_data(commits, config)

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours = [f"{h:02d}:00" for h in range(24)]

    fig, ax = plt.subplots(figsize=(16, 5))

    scheme_name = config.heatmap_scheme
    colors = HEATMAP_COLOR_SCHEMES.get(scheme_name, HEATMAP_COLOR_SCHEMES["github"])
    cmap = LinearSegmentedColormap.from_list(scheme_name, colors, N=256)

    im = ax.imshow(heatmap_data, cmap=cmap, aspect="auto", interpolation="nearest")

    ax.set_xticks(range(24))
    ax.set_xticklabels(hours, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(7))
    ax.set_yticklabels(days, fontsize=10)

    start, end = config.late_night_start, config.late_night_end
    if start > end:
        ax.axvspan(start - 0.5, 23.5, alpha=0.08, color="red")
        ax.axvspan(-0.5, end - 0.5, alpha=0.08, color="red")
    else:
        ax.axvspan(start - 0.5, end - 0.5, alpha=0.08, color="red")

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Commit Count", fontsize=10)

    tz_label = f" (TZ: {config.timezone})" if config.timezone else ""
    ax.set_title(f"Team Schedule Heatmap (Commits by Day & Hour){tz_label}", fontsize=13, pad=12)
    ax.set_xlabel("Hour of Day", fontsize=10)
    ax.set_ylabel("Day of Week", fontsize=10)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output_path


def run_smart_analysis(
    commits: list[CommitInfo],
    output_dir: Path,
    config: SmartAnalysisConfig | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> dict:
    if config is None:
        config = SmartAnalysisConfig()

    output_dir.mkdir(parents=True, exist_ok=True)
    total_steps = 4

    if progress_callback:
        progress_callback(1, total_steps, "Extracting keywords (TF-IDF)")
    keywords = extract_keywords_tfidf(commits, config.wordcloud)

    if progress_callback:
        progress_callback(2, total_steps, "Generating word cloud")
    wordcloud_path = output_dir / "wordcloud.png"
    generate_wordcloud(keywords, wordcloud_path, config.wordcloud)

    if progress_callback:
        progress_callback(3, total_steps, "Computing late-night statistics")
    late_night_stats = compute_late_night_ratio(commits, config)

    if progress_callback:
        progress_callback(4, total_steps, "Generating schedule heatmap")
    heatmap_path = output_dir / "schedule_heatmap.png"
    generate_schedule_heatmap(commits, heatmap_path, config)

    return {
        "keywords": keywords[:30],
        "late_night": late_night_stats,
        "heatmap_data": compute_schedule_heatmap_data(commits, config).tolist(),
        "output_files": {
            "wordcloud": str(wordcloud_path),
            "heatmap": str(heatmap_path),
        },
    }
