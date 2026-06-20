"""Data models for GitHub integration within the Skills module."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any


@dataclass
class ReliabilitySignals:
    """Metadata describing how reliable a GitHub snapshot is."""

    attribution_confidence: float
    last_synced_at: datetime
    rate_limit_remaining: Optional[int] = None
    is_fork: bool = False
    is_private: bool = False
    suspected_unrelated: bool = False
    fork_parent_full_name: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class ContributionMetrics:
    """Aggregate metrics derived from contributions and pull requests."""

    commit_count_30d: int = 0
    additions_30d: int = 0
    deletions_30d: int = 0
    active_days_30d: int = 0
    average_changes_per_commit: float = 0.0


@dataclass
class ContributionSnapshot:
    """Normalized commit/contribution information."""

    sha: str
    message: str
    author_name: Optional[str]
    author_email: Optional[str]
    date: datetime
    additions: int
    deletions: int
    changed_files: int


@dataclass
class PullRequestSnapshot:
    """Pull request metadata used for scoring."""

    number: int
    title: str
    state: str
    additions: int
    deletions: int
    changed_files: int
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime]
    author: Optional[str]
    is_draft: bool = False


@dataclass
class RepositorySnapshot:
    """Normalized repository snapshot for the Skills module."""

    owner: str
    name: str
    default_branch: str
    languages: Dict[str, int]
    language_summary: List[Dict[str, Any]]
    stars: int
    forks: int
    open_issues: int
    topics: List[str]
    size_kb: int
    last_pushed_at: datetime
    reliability: ReliabilitySignals
    contributions: List[ContributionSnapshot] = field(default_factory=list)
    pull_requests: List[PullRequestSnapshot] = field(default_factory=list)
    metrics: ContributionMetrics = field(default_factory=ContributionMetrics)
    commit_sha: Optional[str] = None


@dataclass
class SubmissionSyncRequest:
    """Input payload describing which submission to sync with GitHub."""

    submission_id: str
    learner_id: str
    template_id: str
    repository_full_name: str
    project_id: Optional[str] = None
    expected_owner: Optional[str] = None
    github_token: Optional[str] = None
    include_private: bool = False
    max_items: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubmissionSyncResult:
    """Result of syncing a mini-project submission with GitHub."""

    submission_id: str
    repository: Optional[RepositorySnapshot]
    synced_at: datetime
    reliability: ReliabilitySignals
    contributions_count: int
    pull_requests_count: int
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "submission_id": self.submission_id,
            "synced_at": self.synced_at.isoformat(),
            "reliability": {
                "attribution_confidence": self.reliability.attribution_confidence,
                "last_synced_at": self.reliability.last_synced_at.isoformat(),
                "rate_limit_remaining": self.reliability.rate_limit_remaining,
                "is_fork": self.reliability.is_fork,
                "is_private": self.reliability.is_private,
                "warnings": self.reliability.warnings,
            },
            "repository": self.repository,
            "contributions_count": self.contributions_count,
            "pull_requests_count": self.pull_requests_count,
            "errors": self.errors,
        }
