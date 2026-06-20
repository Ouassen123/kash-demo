"""Reporting exporter service for admin panel and pilot milestones."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from ..admin.panel import AdminPanelService


@dataclass
class ReportRequest:
    """Input contract for report generation."""

    report_type: str
    pilot_site: str
    reviewer: str
    frequency: str = "weekly"


@dataclass
class ReportArtifact:
    """Generated report metadata."""

    report_id: str
    report_type: str
    pilot_site: str
    generated_at: str
    json_path: str
    csv_path: str


class PilotReportingService:
    """Generates JSON/CSV admin reports for pilot governance."""

    def __init__(self, output_dir: str = "./reports") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, request: ReportRequest) -> Dict[str, object]:
        snapshot = AdminPanelService(pilot_site=request.pilot_site).build_snapshot()
        now = datetime.utcnow()
        report_id = f"{request.report_type}-{request.pilot_site}-{now.strftime('%Y%m%d%H%M%S')}"

        payload = {
            "report_id": report_id,
            "request": asdict(request),
            "generated_at": now.isoformat(),
            "snapshot": snapshot,
        }

        json_path = self.output_dir / f"{report_id}.json"
        csv_path = self.output_dir / f"{report_id}.csv"

        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        rows: List[str] = ["module,readiness,owner,linked_story,notes"]
        for item in snapshot["modules"]:
            safe_notes = str(item["notes"]).replace(",", " ")
            rows.append(
                f"{item['module']},{item['readiness']},{item['owner']},{item['linked_story']},{safe_notes}"
            )
        csv_path.write_text("\n".join(rows), encoding="utf-8")

        artifact = ReportArtifact(
            report_id=report_id,
            report_type=request.report_type,
            pilot_site=request.pilot_site,
            generated_at=now.isoformat(),
            json_path=str(json_path),
            csv_path=str(csv_path),
        )

        return asdict(artifact)
