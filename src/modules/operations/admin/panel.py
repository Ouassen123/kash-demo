"""Admin panel service for readiness and compliance-oriented status views."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List


@dataclass
class AdminModuleStatus:
    """Per-module readiness status entry."""

    module: str
    readiness: str
    owner: str
    notes: str
    linked_story: str


@dataclass
class AdminReadinessSnapshot:
    """Aggregated admin view for pilot operations."""

    generated_at: str
    pilot_site: str
    modules: List[AdminModuleStatus]
    overall_status: str


class AdminPanelService:
    """Provides centralized status payload for operations/admin views."""

    def __init__(self, pilot_site: str = "combined") -> None:
        self.pilot_site = pilot_site

    def build_snapshot(self) -> Dict[str, object]:
        modules = [
            AdminModuleStatus("knowledge", "ready", "knowledge-team", "ESCO mapping stable", "1-2-esco-onet-integration"),
            AdminModuleStatus("abilities", "ready", "abilities-team", "Adaptive scoring validated", "2-1-text-based-cognitive-tests"),
            AdminModuleStatus("skills", "ready", "skills-team", "Skills deep dive available", "3-2-github-api-integration"),
            AdminModuleStatus("intelligence", "ready", "intelligence-team", "Explainability integrated", "4-4-explainability-integration"),
            AdminModuleStatus("operations", "ready", "ops-team", "Performance and pilot deployment complete", "5-4-pilot-deployment-2-schools"),
        ]

        snapshot = AdminReadinessSnapshot(
            generated_at=datetime.utcnow().isoformat(),
            pilot_site=self.pilot_site,
            modules=modules,
            overall_status="ready",
        )
        return asdict(snapshot)
