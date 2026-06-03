from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RepoCreate(BaseModel):
    name: str
    local_path: str | None = None
    git_url: str | None = None
    branch: str = "main"


class RepoUpdate(BaseModel):
    name: str | None = None
    local_path: str | None = None
    branch: str | None = None
    is_active: bool | None = None


class RepoResponse(BaseModel):
    id: int
    name: str
    local_path: str
    git_url: str | None = None
    source_type: str
    clone_status: str | None = None
    branch: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalysisTriggerRequest(BaseModel):
    repo_ids: list[int] | None = None
    since: str | None = None
    until: str | None = None


class AnalysisTriggerResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int | None = None
    result: dict | None = None
    error: str | None = None


class DailyStatResponse(BaseModel):
    date: str
    commit_count: int
    insertions: int
    deletions: int
    files_changed: int

    class Config:
        from_attributes = True


class WeeklyStatResponse(BaseModel):
    week: str
    commit_count: int
    insertions: int
    deletions: int
    files_changed: int


class ReportResponse(BaseModel):
    repo_id: int
    repo_name: str
    total_commits: int
    date_range: tuple[str, str]
    daily_stats: list[DailyStatResponse]
    weekly_stats: list[WeeklyStatResponse]
    streak_current: int
    streak_longest: int


class YAMLImportRequest(BaseModel):
    config_path: str | None = None


class FileModStatResponse(BaseModel):
    extension: str
    file_count: int
    modification_count: int

    class Config:
        from_attributes = True


class KeywordStatResponse(BaseModel):
    keyword: str
    score: float


class CommitFrequencyResponse(BaseModel):
    period: str
    commit_count: int
    insertions: int
    deletions: int
    files_changed: int


class CollaborationNode(BaseModel):
    id: str
    commit_count: int
    is_cluster: bool = False


class CollaborationEdgeResponse(BaseModel):
    source: str
    target: str
    weight: int
    shared_files: list[str] = []


class CollaborationGraphResponse(BaseModel):
    nodes: list[CollaborationNode]
    edges: list[CollaborationEdgeResponse]


class ViolationResponse(BaseModel):
    id: int
    commit_hash: str
    rule_name: str
    severity: str
    description: str | None
    author: str | None
    detected_at: datetime

    class Config:
        from_attributes = True


class ViolationSummary(BaseModel):
    total: int
    by_rule: dict[str, int]
    violations: list[ViolationResponse]


class RuleConfigResponse(BaseModel):
    enabled: bool
    max_files_per_commit: int
    min_message_length: int
    max_lines_changed: int
    dingtalk_webhook_url: bool
    dingtalk_silence_minutes: int


class RuleConfigUpdate(BaseModel):
    enabled: bool | None = None
    max_files_per_commit: int | None = None
    min_message_length: int | None = None
    max_lines_changed: int | None = None
    dingtalk_silence_minutes: int | None = None
