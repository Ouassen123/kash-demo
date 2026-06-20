"""Async GitHub integration service for the Skills module."""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from src.core.config import DATA_DIR, settings
from src.core.logging import get_logger
from src.modules.skills.github.models import (
    ContributionSnapshot,
    ContributionMetrics,
    PullRequestSnapshot,
    ReliabilitySignals,
    RepositorySnapshot,
    SubmissionSyncRequest,
    SubmissionSyncResult,
)
from src.modules.skills.github.token_manager import GitHubTokenManager

logger = get_logger(__name__)


class RateLimiter:
    """Simple async rate limiter using a sliding time window."""

    def __init__(self, max_calls: int, per_seconds: int = 60) -> None:
        self.max_calls = max_calls
        self.per_seconds = per_seconds
        self._timestamps: deque[datetime] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = datetime.utcnow()
            while self._timestamps and (now - self._timestamps[0]).total_seconds() > self.per_seconds:
                self._timestamps.popleft()

            if len(self._timestamps) >= self.max_calls:
                sleep_time = self.per_seconds - (now - self._timestamps[0]).total_seconds()
                await asyncio.sleep(max(sleep_time, 0.01))
                await self.acquire()
                return

            self._timestamps.append(datetime.utcnow())


class GitHubIntegrationService:
    """Fetches GitHub data and normalizes it for the Skills module."""

    def __init__(
        self,
        token_manager: Optional[GitHubTokenManager] = None,
        base_url: Optional[str] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        self.token_manager = token_manager or GitHubTokenManager()
        self.base_url = base_url or settings.github_api_url.rstrip("/")
        calls_per_minute = max(settings.github_rate_limit_per_minute, 1)
        self.rate_limiter = rate_limiter or RateLimiter(calls_per_minute, 60)

    async def sync_submission(self, request: SubmissionSyncRequest) -> SubmissionSyncResult:
        token = request.github_token or await self.token_manager.get_token(request.learner_id)
        if not token:
            reliability = self._build_default_reliability("missing_repo_link", request.expected_owner or request.learner_id)
            return SubmissionSyncResult(
                submission_id=request.submission_id,
                repository=None,
                synced_at=datetime.utcnow(),
                reliability=reliability,
                contributions_count=0,
                pull_requests_count=0,
                errors=["missing_token"],
            )

        owner, repo = self._split_repo_name(request.repository_full_name)
        client_timeout = httpx.Timeout(30.0, connect=10.0)

        async with httpx.AsyncClient(timeout=client_timeout, headers=self._build_headers(token)) as client:
            repo_data = await self._get_repository(client, owner, repo)
            if not repo_data:
                reliability = self._build_default_reliability("repo_not_found", request.expected_owner or request.learner_id)
                return SubmissionSyncResult(
                    submission_id=request.submission_id,
                    repository=None,
                    synced_at=datetime.utcnow(),
                    reliability=reliability,
                    contributions_count=0,
                    pull_requests_count=0,
                    errors=["repo_not_found"],
                )

            languages = await self._get_languages(client, owner, repo)
            commits = await self._get_commits(client, owner, repo, limit=request.max_items)
            pull_requests = await self._get_pull_requests(client, owner, repo, limit=request.max_items)

            contributions = [self._normalize_commit(item) for item in commits]
            prs = [self._normalize_pull_request(item) for item in pull_requests]

            suspected_unrelated = await self._detect_unrelated_repo(repo_data, request)
            reliability = self._build_reliability(repo_data, contributions, request, client, suspected_unrelated)

            repository_snapshot = RepositorySnapshot(
                owner=repo_data["owner"]["login"],
                name=repo_data["name"],
                default_branch=repo_data.get("default_branch", "main"),
                languages=languages,
                language_summary=self._build_language_summary(languages),
                stars=repo_data.get("stargazers_count", 0),
                forks=repo_data.get("forks_count", 0),
                open_issues=repo_data.get("open_issues_count", 0),
                topics=repo_data.get("topics", []),
                size_kb=repo_data.get("size", 0),
                last_pushed_at=self._parse_datetime(repo_data.get("pushed_at")),
                reliability=reliability,
                contributions=contributions,
                pull_requests=prs,
                metrics=self._calculate_metrics(contributions, prs),
            )

            return SubmissionSyncResult(
                submission_id=request.submission_id,
                repository=repository_snapshot,
                synced_at=datetime.utcnow(),
                reliability=reliability,
                contributions_count=len(contributions),
                pull_requests_count=len(prs),
                errors=[],
            )

    async def _get_repository(self, client: httpx.AsyncClient, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        endpoint = f"/repos/{owner}/{repo}"
        return await self._get(client, endpoint)

    async def _get_languages(self, client: httpx.AsyncClient, owner: str, repo: str) -> Dict[str, int]:
        endpoint = f"/repos/{owner}/{repo}/languages"
        result = await self._get(client, endpoint)
        return result if isinstance(result, dict) else {}

    async def _get_commits(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        endpoint = f"/repos/{owner}/{repo}/commits"
        params = {"per_page": min(limit, 100)}
        result = await self._get(client, endpoint, params)
        return result if isinstance(result, list) else []

    async def _get_pull_requests(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        endpoint = f"/repos/{owner}/{repo}/pulls"
        params = {"per_page": min(limit, 100), "state": "all"}
        result = await self._get(client, endpoint, params)
        return result if isinstance(result, list) else []

    async def _get(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        await self.rate_limiter.acquire()
        url = f"{self.base_url}{endpoint}"
        try:
            response = await client.get(url, params=params)
            if response.status_code == httpx.codes.OK:
                return response.json()
            logger.warning("GitHub API call failed (%s): %s", response.status_code, url)
            return None
        except httpx.HTTPError as exc:
            logger.error("GitHub request failed: %s", exc)
            return None

    def _normalize_commit(self, commit: Dict[str, Any]) -> ContributionSnapshot:
        commit_data = commit.get("commit", {})
        stats = commit.get("stats", {})
        author = commit_data.get("author", {})
        return ContributionSnapshot(
            sha=commit.get("sha", "unknown"),
            message=commit_data.get("message", ""),
            author_name=author.get("name"),
            author_email=author.get("email"),
            date=self._parse_datetime(author.get("date")),
            additions=stats.get("additions", 0),
            deletions=stats.get("deletions", 0),
            changed_files=stats.get("total", 0),
        )

    def _normalize_pull_request(self, pr: Dict[str, Any]) -> PullRequestSnapshot:
        return PullRequestSnapshot(
            number=pr.get("number"),
            title=pr.get("title", ""),
            state=pr.get("state", "unknown"),
            additions=pr.get("additions", 0),
            deletions=pr.get("deletions", 0),
            changed_files=pr.get("changed_files", 0),
            created_at=self._parse_datetime(pr.get("created_at")),
            updated_at=self._parse_datetime(pr.get("updated_at")),
            merged_at=self._parse_datetime(pr.get("merged_at")),
            author=pr.get("user", {}).get("login"),
            is_draft=pr.get("draft", False),
        )

    async def _detect_unrelated_repo(self, repo_data: Dict[str, Any], request: SubmissionSyncRequest) -> bool:
        """Heuristic to flag forks or repos where learner has zero commits."""
        if repo_data.get("fork") and repo_data.get("owner", {}).get("login") != request.learner_id:
            return True
        return False

    def _calculate_confidence(
        self,
        repo_data: Dict[str, Any],
        contributions: List[ContributionSnapshot],
        suspected_unrelated: bool = False,
    ) -> float:
        confidence = 0.5
        if contributions:
            confidence += 0.2
        if repo_data.get("owner", {}).get("type") == "User":
            confidence += 0.1
        if not repo_data.get("fork", False):
            confidence += 0.1
        if suspected_unrelated:
            confidence -= 0.3
        return min(confidence, 1.0)

    def _build_headers(self, token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "Skills-Module-Integration",
        }

    def _build_default_reliability(
        self,
        warning: str,
        expected_owner: Optional[str],
    ) -> ReliabilitySignals:
        warnings = [warning]
        if expected_owner:
            warnings.append(f"expected_owner={expected_owner}")
        return ReliabilitySignals(
            attribution_confidence=0.0,
            last_synced_at=datetime.utcnow(),
            warnings=warnings,
        )

    def _build_reliability(
        self,
        repo_data: Dict[str, Any],
        contributions: List[ContributionSnapshot],
        request: SubmissionSyncRequest,
        client: httpx.AsyncClient,
        suspected_unrelated: bool,
    ) -> ReliabilitySignals:
        rate_limit_remaining: Optional[int] = None
        if client.headers:
            try:
                rate_limit_remaining = int(client.headers.get("x-ratelimit-remaining", "0"))
            except (TypeError, ValueError):
                rate_limit_remaining = None

        warnings = self._build_warnings(repo_data, request)
        if suspected_unrelated:
            warnings.append("suspected_unrelated_repo")

        return ReliabilitySignals(
            attribution_confidence=self._calculate_confidence(repo_data, contributions, suspected_unrelated),
            last_synced_at=datetime.utcnow(),
            rate_limit_remaining=rate_limit_remaining,
            is_fork=repo_data.get("fork", False),
            is_private=repo_data.get("private", False),
            suspected_unrelated=suspected_unrelated,
            fork_parent_full_name=(repo_data.get("parent") or {}).get("full_name"),
            warnings=warnings,
        )

    def _parse_datetime(self, value: Optional[str]) -> datetime:
        if not value:
            return datetime.utcnow()
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.utcnow()

    def _split_repo_name(self, full_name: str) -> tuple[str, str]:
        if "/" not in full_name:
            return full_name, ""
        owner, repo = full_name.split("/", 1)
        return owner, repo

    def get_local_repo_path(self, submission_id: str) -> Optional[Path]:
        """
        Get the local path where a repository is stored for analysis.
        
        Args:
            submission_id: The submission ID to get the repo path for
            
        Returns:
            Path to the local repository directory or None if not found
        """
        # For now, we use a simple local storage structure under DATA_DIR
        # In a full implementation, this would coordinate with git clone operations
        repo_dir = DATA_DIR / "skills" / "repositories" / submission_id
        if repo_dir.exists() and repo_dir.is_dir():
            return repo_dir
        return None
