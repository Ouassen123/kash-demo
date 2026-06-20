"""Coordinates GitHub submissions syncs for the Skills module."""

from __future__ import annotations

from typing import Dict, Any, Optional
from pathlib import Path

from .integration_service import GitHubIntegrationService
from .link_registry import GitHubLinkRegistry, LearnerRepoLink
from .models import SubmissionSyncRequest, SubmissionSyncResult


class GitHubSyncManager:
    """High-level orchestrator connecting submissions to GitHub data."""

    def __init__(
        self,
        integration_service: Optional[GitHubIntegrationService] = None,
        link_registry: Optional[GitHubLinkRegistry] = None,
    ) -> None:
        self.integration_service = integration_service or GitHubIntegrationService()
        self.link_registry = link_registry or GitHubLinkRegistry()

    async def sync_submission_by_project(
        self,
        learner_id: str,
        submission_id: str,
        template_id: str,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SubmissionSyncResult:
        link = self.link_registry.find_repo(learner_id, project_id)
        if not link:
            return SubmissionSyncResult(
                submission_id=submission_id,
                repository=None,
                synced_at=self.integration_service._parse_datetime(None),
                reliability=self.integration_service._build_default_reliability("no_repo_link"),
                contributions_count=0,
                pull_requests_count=0,
                errors=["missing_repo_link"],
            )

        request = SubmissionSyncRequest(
            submission_id=submission_id,
            learner_id=learner_id,
            template_id=template_id,
            repository_full_name=link.repository_full_name,
            project_id=project_id,
            metadata=metadata or {},
        )
        return await self.integration_service.sync_submission(request)

    def register_link(
        self,
        learner_id: str,
        repository_full_name: str,
        project_id: Optional[str] = None,
        github_handle: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> LearnerRepoLink:
        return self.link_registry.register_link(
            learner_id,
            repository_full_name,
            project_id=project_id,
            github_handle=github_handle,
            metadata=metadata,
        )

    async def refresh_learner_handle(self, learner_id: str, github_handle: str) -> None:
        self.link_registry.refresh_handle(learner_id, github_handle)
        await self.integration_service.token_manager.refresh_learner_link(learner_id, github_handle)

    def get_local_repo_path(self, submission_id: str) -> Optional[Path]:
        return self.integration_service.get_local_repo_path(submission_id)
