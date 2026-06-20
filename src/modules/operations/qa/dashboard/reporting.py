"""Manual checklist and audit reporting helpers for final QA."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List


@dataclass
class ManualChecklistItem:
    """Single manual QA item for reviewer tracking."""

    id: str
    area: str
    description: str
    status: str  # pass/fail/blocked
    reviewer: str
    notes: str = ""


@dataclass
class ValidationAuditEntry:
    """Audit metadata for one validation report."""

    pilot_site: str
    reviewer: str
    started_at: str
    finished_at: str
    go_no_go: str
    blockers: List[str]


class QADashboardExporter:
    """Exports manual checklist + audit metadata for admin reporting."""

    def __init__(self, output_dir: str = "./qa-results") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_manual_checklist(self, items: List[ManualChecklistItem]) -> Path:
        payload = {
            "generated_at": datetime.utcnow().isoformat(),
            "items": [asdict(item) for item in items],
        }
        target = self.output_dir / "manual_checklist.json"
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return target

    def export_audit_entry(self, audit: ValidationAuditEntry) -> Path:
        payload = {
            "generated_at": datetime.utcnow().isoformat(),
            "audit": asdict(audit),
        }
        target = self.output_dir / "validation_audit.json"
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return target
