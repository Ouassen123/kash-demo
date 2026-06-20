"""Role-based access and audit logging helpers for operations admin panel."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List


@dataclass
class AccessLogEntry:
    """Audit record for admin/reporting resource access."""

    timestamp: str
    user_id: str
    role: str
    action: str
    resource: str
    allowed: bool
    reason: str


class AccessControlService:
    """Simple RBAC policy and JSONL audit trail export."""

    ROLE_PERMISSIONS: Dict[str, List[str]] = {
        "admin": ["view_dashboard", "export_reports", "view_sensitive_logs"],
        "ops": ["view_dashboard", "export_reports"],
        "reviewer": ["view_dashboard"],
    }

    def __init__(self, audit_log_path: str = "./reports/access_audit.jsonl") -> None:
        self.audit_log_path = Path(audit_log_path)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def authorize(self, user_id: str, role: str, action: str, resource: str) -> bool:
        allowed_actions = self.ROLE_PERMISSIONS.get(role, [])
        allowed = action in allowed_actions
        reason = "allowed" if allowed else f"role '{role}' cannot '{action}'"

        self._write_log(
            AccessLogEntry(
                timestamp=datetime.utcnow().isoformat(),
                user_id=user_id,
                role=role,
                action=action,
                resource=resource,
                allowed=allowed,
                reason=reason,
            )
        )
        return allowed

    def _write_log(self, entry: AccessLogEntry) -> None:
        with self.audit_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(entry)) + "\n")
