from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RepoCreate(BaseModel):
    name: str
    local_path: str
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
