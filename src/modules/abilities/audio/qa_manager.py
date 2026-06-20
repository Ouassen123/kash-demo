"""QA management API for replay, flag, and annotate recording sessions."""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class QAManager:
    """QA management for voice recording sessions."""

    def __init__(self):
        """Initialize QA manager."""
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.flags: List[Dict[str, Any]] = []
        self.annotations: List[Dict[str, Any]] = []

    def register_session(self, session_id: str, audio_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a session for QA review.

        Args:
            session_id: Session identifier
            audio_info: Audio processing information

        Returns:
            Registration result.
        """
        qa_session = {
            "session_id": session_id,
            "status": "pending_review",
            "audio_info": audio_info,
            "registered_at": datetime.utcnow().isoformat(),
            "reviewed_by": None,
            "reviewed_at": None,
            "flags": [],
            "annotations": [],
            "final_score": None,
        }
        self.sessions[session_id] = qa_session

        logger.info(f"Session {session_id} registered for QA review")
        return {
            "status": "registered",
            "session_id": session_id,
            "qa_status": qa_session["status"],
            "registered_at": qa_session["registered_at"],
        }

    def get_session_for_review(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details for QA review."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        return {
            "session_id": session_id,
            "status": session["status"],
            "audio_info": session["audio_info"],
            "flags": session["flags"],
            "annotations": session["annotations"],
            "registered_at": session["registered_at"],
            "reviewed_by": session["reviewed_by"],
            "reviewed_at": session["reviewed_at"],
        }

    def replay_audio(self, session_id: str) -> Dict[str, Any]:
        """
        Get audio data for replay.

        Args:
            session_id: Session identifier

        Returns:
            Audio replay information.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        # Mock audio replay - real implementation would retrieve encrypted audio
        audio_info = session["audio_info"]
        return {
            "session_id": session_id,
            "audio_available": True,
            "audio_hash": audio_info.get("audio_hash"),
            "duration_seconds": audio_info.get("metadata", {}).get("duration_seconds"),
            "quality_score": audio_info.get("quality_score"),
            "replay_token": f"replay_token_{session_id}_{int(datetime.utcnow().timestamp())}",
        }

    def flag_session(
        self,
        session_id: str,
        reason: str,
        severity: str = "medium",
        flagged_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Flag a session for QA issues.

        Args:
            session_id: Session identifier
            reason: Flag reason
            severity: Flag severity (low, medium, high, critical)
            flagged_by: Optional reviewer identifier

        Returns:
            Flag result.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        flag = {
            "session_id": session_id,
            "reason": reason,
            "severity": severity,
            "flagged_by": flagged_by or "unknown",
            "flagged_at": datetime.utcnow().isoformat(),
            "flag_id": f"flag_{session_id}_{len(self.flags) + 1}",
        }

        self.flags.append(flag)
        session["flags"].append(flag)

        # Update session status if critical flag
        if severity == "critical":
            session["status"] = "critical_issue"

        logger.warning(f"Session {session_id} flagged: {reason} ({severity})")
        return {
            "status": "flagged",
            "session_id": session_id,
            "flag_id": flag["flag_id"],
            "reason": reason,
            "severity": severity,
            "flagged_by": flagged_by or "unknown",
            "flagged_at": flag["flagged_at"],
        }

    def annotate_session(
        self,
        session_id: str,
        annotation: str,
        annotation_type: str = "general",
        annotated_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add annotation to a session.

        Args:
            session_id: Session identifier
            annotation: Annotation text
            annotation_type: Type of annotation (general, quality, content, technical)
            annotated_by: Optional reviewer identifier

        Returns:
            Annotation result.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        annotation_entry = {
            "session_id": session_id,
            "annotation": annotation,
            "type": annotation_type,
            "annotated_by": annotated_by or "unknown",
            "annotated_at": datetime.utcnow().isoformat(),
            "annotation_id": f"annotation_{session_id}_{len(self.annotations) + 1}",
        }

        self.annotations.append(annotation_entry)
        session["annotations"].append(annotation_entry)

        logger.info(f"Annotation added to session {session_id}: {annotation_type}")
        return {
            "status": "annotated",
            "session_id": session_id,
            "annotation_id": annotation_entry["annotation_id"],
            "type": annotation_type,
            "annotated_by": annotated_by or "unknown",
            "annotated_at": annotation_entry["annotated_at"],
        }

    def approve_session(
        self,
        session_id: str,
        reviewed_by: str,
        final_score: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Approve a session for analytics.

        Args:
            session_id: Session identifier
            reviewed_by: Reviewer identifier
            final_score: Optional final quality score
            notes: Optional review notes

        Returns:
            Approval result.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        session["status"] = "approved"
        session["reviewed_by"] = reviewed_by
        session["reviewed_at"] = datetime.utcnow().isoformat()
        session["final_score"] = final_score
        if notes:
            session["review_notes"] = notes

        logger.info(f"Session {session_id} approved by {reviewed_by}")
        return {
            "status": "approved",
            "session_id": session_id,
            "reviewed_by": reviewed_by,
            "reviewed_at": session["reviewed_at"],
            "final_score": final_score,
        }

    def reject_session(
        self,
        session_id: str,
        reviewed_by: str,
        rejection_reason: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reject a session from analytics.

        Args:
            session_id: Session identifier
            reviewed_by: Reviewer identifier
            rejection_reason: Reason for rejection
            notes: Optional additional notes

        Returns:
            Rejection result.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        session["status"] = "rejected"
        session["reviewed_by"] = reviewed_by
        session["reviewed_at"] = datetime.utcnow().isoformat()
        session["rejection_reason"] = rejection_reason
        if notes:
            session["review_notes"] = notes

        logger.warning(f"Session {session_id} rejected by {reviewed_by}: {rejection_reason}")
        return {
            "status": "rejected",
            "session_id": session_id,
            "reviewed_by": reviewed_by,
            "reviewed_at": session["reviewed_at"],
            "rejection_reason": rejection_reason,
        }

    def get_qa_dashboard(self) -> Dict[str, Any]:
        """Get QA dashboard summary."""
        total_sessions = len(self.sessions)
        status_counts = {}
        severity_counts = {}

        for session in self.sessions.values():
            status = session["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        for flag in self.flags:
            severity = flag["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total_sessions": total_sessions,
            "status_breakdown": status_counts,
            "flag_severity_breakdown": severity_counts,
            "pending_review": status_counts.get("pending_review", 0),
            "critical_issues": status_counts.get("critical_issue", 0),
            "approved": status_counts.get("approved", 0),
            "rejected": status_counts.get("rejected", 0),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def list_sessions_by_status(self, status: str) -> List[str]:
        """List sessions by QA status."""
        return [
            session_id for session_id, session in self.sessions.items()
            if session["status"] == status
        ]
