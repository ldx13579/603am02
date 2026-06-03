from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Repo(Base):
    __tablename__ = "repos"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    local_path = Column(String(500), nullable=False)
    branch = Column(String(100), default="main")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analysis_runs = relationship("AnalysisRun", back_populates="repo", cascade="all, delete-orphan")
    commit_records = relationship("CommitRecord", back_populates="repo", cascade="all, delete-orphan")
    daily_stats = relationship("DailyStat", back_populates="repo", cascade="all, delete-orphan")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), nullable=False)
    celery_task_id = Column(String(200), nullable=True)
    status = Column(String(50), default="pending")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    total_commits = Column(Integer, default=0)
    date_range_start = Column(String(20), nullable=True)
    date_range_end = Column(String(20), nullable=True)

    repo = relationship("Repo", back_populates="analysis_runs")


class CommitRecord(Base):
    __tablename__ = "commit_records"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), nullable=False)
    hash = Column(String(8), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    message = Column(String(200), nullable=True)
    files_changed = Column(Integer, default=0)
    insertions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)

    repo = relationship("Repo", back_populates="commit_records")


class DailyStat(Base):
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), nullable=False)
    date = Column(String(10), nullable=False)
    commit_count = Column(Integer, default=0)
    total_insertions = Column(Integer, default=0)
    total_deletions = Column(Integer, default=0)
    total_files_changed = Column(Integer, default=0)

    repo = relationship("Repo", back_populates="daily_stats")
