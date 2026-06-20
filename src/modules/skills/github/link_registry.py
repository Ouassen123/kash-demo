"""Registry for learner GitHub links and repository mappings."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class LearnerRepoLink:
    learner_id: str
    repository_full_name: str
    project_id: Optional[str]
    github_handle: Optional[str]
    last_refreshed_at: datetime
    metadata: Dict[str, str] = field(default_factory=dict)


class GitHubLinkRegistry:
    """In-memory registry tracking learner-to-repository links."""

    def __init__(self) -> None:
        self._links: Dict[str, List[LearnerRepoLink]] = {}

    def register_link(
        self,
        learner_id: str,
        repository_full_name: str,
        project_id: Optional[str] = None,
        github_handle: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> LearnerRepoLink:
        entry = LearnerRepoLink(
            learner_id=learner_id,
            repository_full_name=repository_full_name,
            project_id=project_id,
            github_handle=github_handle,
            last_refreshed_at=datetime.utcnow(),
            metadata=metadata or {},
        )
        links = self._links.setdefault(learner_id, [])
        links = [link for link in links if link.repository_full_name != repository_full_name]
        links.append(entry)
        self._links[learner_id] = links
        return entry

    def refresh_handle(self, learner_id: str, github_handle: str) -> None:
        links = self._links.get(learner_id, [])
        for link in links:
            link.github_handle = github_handle
            link.last_refreshed_at = datetime.utcnow()

    def get_links(self, learner_id: str) -> List[LearnerRepoLink]:
        return list(self._links.get(learner_id, []))

    def find_repo(self, learner_id: str, project_id: Optional[str] = None) -> Optional[LearnerRepoLink]:
        links = self._links.get(learner_id, [])
        if project_id:
            for link in links:
                if link.project_id == project_id:
                    return link
        return links[0] if links else None

    def to_dict(self) -> Dict[str, List[Dict[str, str]]]:
        return {
            learner: [
                {
                    "repository_full_name": link.repository_full_name,
                    "project_id": link.project_id,
                    "github_handle": link.github_handle,
                    "last_refreshed_at": link.last_refreshed_at.isoformat(),
                    "metadata": link.metadata,
                }
                for link in links
            ]
            for learner, links in self._links.items()
        }
