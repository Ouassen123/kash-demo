"""Context objects for code analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional


@dataclass
class RepositoryInput:
    """Reference to repository artifacts available for analysis."""

    submission_id: str
    learner_id: str
    template_id: str
    root_path: Path
    files: List[Path]
    metadata: Dict[str, Any] = field(default_factory=dict)
    inline_files: List[Dict[str, str]] = field(default_factory=list)
    analysis_profile: str = "default"
    commit_sha: Optional[str] = None


@dataclass
class AnalysisContext:
    """Context passed to analyzers containing configuration and artifacts."""

    repository: RepositoryInput
    analysis_profile: str
    analyzers: List[str]
    config: Dict[str, Any] = field(default_factory=dict)
    extra_metadata: Dict[str, Any] = field(default_factory=dict)
    temp_dir: Optional[Path] = None

    def get_config(self, analyzer_name: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        profile_config = self.config.get("profiles", {}).get(self.analysis_profile, {})
        analyzer_config = profile_config.get(analyzer_name, {})
        return {**(default or {}), **analyzer_config}
