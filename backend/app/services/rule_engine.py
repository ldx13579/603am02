from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.services.git_analyzer import CommitInfo

logger = logging.getLogger(__name__)


@dataclass
class Violation:
    commit_hash: str
    rule_name: str
    severity: str
    description: str
    author: str


class BaseRule(ABC):
    name: str = ""
    severity: str = "warning"

    @abstractmethod
    def check(self, commit: CommitInfo) -> Violation | None:
        ...


class TooManyFilesRule(BaseRule):
    name = "too_many_files"
    severity = "warning"

    def __init__(self, threshold: int = 20):
        self.threshold = threshold

    def check(self, commit: CommitInfo) -> Violation | None:
        if commit.files_changed > self.threshold:
            return Violation(
                commit_hash=commit.hash,
                rule_name=self.name,
                severity=self.severity,
                description=f"Commit touches {commit.files_changed} files (threshold: {self.threshold})",
                author=commit.author,
            )
        return None


class EmptyMessageRule(BaseRule):
    name = "empty_message"
    severity = "warning"

    def __init__(self, min_length: int = 5):
        self.min_length = min_length

    def check(self, commit: CommitInfo) -> Violation | None:
        msg = (commit.message or "").strip()
        if len(msg) < self.min_length:
            return Violation(
                commit_hash=commit.hash,
                rule_name=self.name,
                severity=self.severity,
                description=f"Commit message too short ({len(msg)} chars, min: {self.min_length})",
                author=commit.author,
            )
        return None


class LargeCommitRule(BaseRule):
    name = "large_commit"
    severity = "warning"

    def __init__(self, threshold: int = 1000):
        self.threshold = threshold

    def check(self, commit: CommitInfo) -> Violation | None:
        total_lines = commit.insertions + commit.deletions
        if total_lines > self.threshold:
            return Violation(
                commit_hash=commit.hash,
                rule_name=self.name,
                severity=self.severity,
                description=f"Commit changes {total_lines} lines (threshold: {self.threshold})",
                author=commit.author,
            )
        return None


class RuleEngine:
    def __init__(self, rules: list[BaseRule]):
        self.rules = rules

    def evaluate(self, commits: list[CommitInfo]) -> list[Violation]:
        violations = []
        for commit in commits:
            for rule in self.rules:
                try:
                    v = rule.check(commit)
                    if v:
                        violations.append(v)
                except Exception as e:
                    logger.warning(f"Rule {rule.name} failed on commit {commit.hash}: {e}")
        return violations


def create_default_engine(settings) -> RuleEngine:
    rules: list[BaseRule] = [
        TooManyFilesRule(threshold=settings.RULE_MAX_FILES_PER_COMMIT),
        EmptyMessageRule(min_length=settings.RULE_MIN_MESSAGE_LENGTH),
        LargeCommitRule(threshold=settings.RULE_MAX_LINES_CHANGED),
    ]
    return RuleEngine(rules)
