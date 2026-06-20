"""QA review integration hooks for transcription pipeline."""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from src.core.logging import get_logger
from .provider_base import TranscriptPackage

logger = get_logger(__name__)


class QAReviewHooks:
    """Integrates transcription pipeline with existing QA workflows."""

    def __init__(self, audio_qa_manager):
        """
        Initialize QA hooks.

        Args:
            audio_qa_manager: Existing QAManager from audio module
        """
        self.qa_manager = audio_qa_manager
        self.transcript_sessions: Dict[str, Dict[str, Any]] = {}

    async def register_for_review(
        self,
        transcript_id: str,
        transcript: TranscriptPackage,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Register a transcript for QA review.

        Args:
            transcript_id: Unique transcript identifier
            transcript: Structured transcript package
            metadata: Additional metadata from pipeline

        Returns:
            Registration result
        """
        try:
            # Create QA session entry
            qa_session = {
                "transcript_id": transcript_id,
                "session_id": transcript.session_id,
                "prompt_id": transcript.prompt_id,
                "learner_id": transcript.learner_id,
                "provider": transcript.provider,
                "aggregate_confidence": transcript.aggregate_confidence,
                "qa_status": "pending_review",
                "registered_at": datetime.utcnow().isoformat(),
                "metadata": metadata,
                "transcript": transcript,
            }

            self.transcript_sessions[transcript_id] = qa_session

            # Register with existing QA manager
            audio_info = {
                "transcript_id": transcript_id,
                "session_id": transcript.session_id,
                "confidence": transcript.aggregate_confidence,
                "provider": transcript.provider,
                "segment_count": len(transcript.segments),
                "duration_seconds": max(seg.end for seg in transcript.segments) if transcript.segments else 0,
                "language": transcript.language,
                "metadata": metadata,
            }

            registration_result = self.qa_manager.register_session(transcript_id, audio_info)

            # Auto-approve if confidence is high and no flags
            if transcript.aggregate_confidence >= 0.95 and not any(seg.flags for seg in transcript.segments):
                await self.auto_approve(transcript_id, "High confidence auto-approval")

            logger.info(f"Transcript {transcript_id} registered for QA review")
            return {
                "status": "registered",
                "transcript_id": transcript_id,
                "qa_session_id": transcript_id,
                "auto_approved": qa_session.get("qa_status") == "approved",
                "registration": registration_result,
            }

        except Exception as e:
            logger.error(f"Failed to register transcript {transcript_id} for QA: {e}")
            return {
                "status": "error",
                "transcript_id": transcript_id,
                "error": str(e),
            }

    async def get_transcript_for_review(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """
        Get transcript details for QA review.

        Args:
            transcript_id: Transcript identifier

        Returns:
            Review-ready transcript data or None
        """
        qa_session = self.transcript_sessions.get(transcript_id)
        if not qa_session:
            return None

        transcript = qa_session["transcript"]
        return {
            "transcript_id": transcript_id,
            "session_id": transcript.session_id,
            "prompt_id": transcript.prompt_id,
            "learner_id": transcript.learner_id,
            "language": transcript.language,
            "segments": [
                {
                    "segment_id": seg.segment_id,
                    "speaker": seg.speaker,
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "confidence": seg.confidence,
                    "words": [
                        {
                            "text": w.text,
                            "start": w.start,
                            "end": w.end,
                            "confidence": w.confidence,
                        }
                        for w in seg.words
                    ],
                    "noise_level": seg.noise_level,
                    "flags": seg.flags,
                }
                for seg in transcript.segments
            ],
            "aggregate_confidence": transcript.aggregate_confidence,
            "provider": transcript.provider,
            "qa_status": qa_session["qa_status"],
            "registered_at": qa_session["registered_at"],
            "metadata": qa_session["metadata"],
        }

    async def approve_transcript(
        self,
        transcript_id: str,
        reviewed_by: str,
        notes: Optional[str] = None,
        corrections: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Approve a transcript for downstream use.

        Args:
            transcript_id: Transcript identifier
            reviewed_by: Reviewer identifier
            notes: Optional review notes
            corrections: Optional list of corrections made

        Returns:
            Approval result
        """
        qa_session = self.transcript_sessions.get(transcript_id)
        if not qa_session:
            return {"error": "Transcript not found"}

        # Apply corrections if provided
        if corrections:
            await self._apply_corrections(transcript_id, corrections)

        # Update QA status
        qa_session["qa_status"] = "approved"
        qa_session["reviewed_by"] = reviewed_by
        qa_session["reviewed_at"] = datetime.utcnow().isoformat()
        if notes:
            qa_session["review_notes"] = notes
        if corrections:
            qa_session["corrections"] = corrections

        # Approve in audio QA manager
        approval_result = self.qa_manager.approve_session(
            transcript_id,
            reviewed_by,
            qa_session["transcript"].aggregate_confidence,
            notes,
        )

        logger.info(f"Transcript {transcript_id} approved by {reviewed_by}")
        return {
            "status": "approved",
            "transcript_id": transcript_id,
            "reviewed_by": reviewed_by,
            "reviewed_at": qa_session["reviewed_at"],
            "corrections_applied": len(corrections) if corrections else 0,
            "qa_approval": approval_result,
        }

    async def reject_transcript(
        self,
        transcript_id: str,
        reviewed_by: str,
        reason: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reject a transcript.

        Args:
            transcript_id: Transcript identifier
            reviewed_by: Reviewer identifier
            reason: Rejection reason
            notes: Optional additional notes

        Returns:
            Rejection result
        """
        qa_session = self.transcript_sessions.get(transcript_id)
        if not qa_session:
            return {"error": "Transcript not found"}

        # Update QA status
        qa_session["qa_status"] = "rejected"
        qa_session["reviewed_by"] = reviewed_by
        qa_session["reviewed_at"] = datetime.utcnow().isoformat()
        qa_session["rejection_reason"] = reason
        if notes:
            qa_session["review_notes"] = notes

        # Reject in audio QA manager
        rejection_result = self.qa_manager.reject_session(transcript_id, reviewed_by, reason, notes)

        logger.warning(f"Transcript {transcript_id} rejected by {reviewed_by}: {reason}")
        return {
            "status": "rejected",
            "transcript_id": transcript_id,
            "reviewed_by": reviewed_by,
            "reviewed_at": qa_session["reviewed_at"],
            "rejection_reason": reason,
            "qa_rejection": rejection_result,
        }

    async def flag_transcript(
        self,
        transcript_id: str,
        reason: str,
        severity: str = "medium",
        flagged_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Flag a transcript for QA issues.

        Args:
            transcript_id: Transcript identifier
            reason: Flag reason
            severity: Flag severity
            flagged_by: Optional reviewer identifier

        Returns:
            Flag result
        """
        qa_session = self.transcript_sessions.get(transcript_id)
        if not qa_session:
            return {"error": "Transcript not found"}

        # Flag in audio QA manager
        flag_result = self.qa_manager.flag_session(transcript_id, reason, severity, flagged_by)

        # Update session status if critical
        if severity == "critical":
            qa_session["qa_status"] = "critical_issue"

        logger.warning(f"Transcript {transcript_id} flagged: {reason} ({severity})")
        return {
            "status": "flagged",
            "transcript_id": transcript_id,
            "flag_id": flag_result.get("flag_id"),
            "reason": reason,
            "severity": severity,
            "qa_flag": flag_result,
        }

    async def auto_approve(self, transcript_id: str, reason: str) -> None:
        """
        Auto-approve a transcript based on confidence thresholds.

        Args:
            transcript_id: Transcript identifier
            reason: Auto-approval reason
        """
        qa_session = self.transcript_sessions.get(transcript_id)
        if not qa_session:
            return

        qa_session["qa_status"] = "auto_approved"
        qa_session["auto_approval_reason"] = reason
        qa_session["auto_approved_at"] = datetime.utcnow().isoformat()

        # Auto-approve in audio QA manager
        self.qa_manager.approve_session(
            transcript_id,
            "system",
            qa_session["transcript"].aggregate_confidence,
            f"Auto-approved: {reason}",
        )

        logger.info(f"Auto-approved transcript {transcript_id}: {reason}")

    async def _apply_corrections(self, transcript_id: str, corrections: List[Dict[str, Any]]) -> None:
        """
        Apply corrections to a transcript.

        Args:
            transcript_id: Transcript identifier
            corrections: List of correction objects
        """
        qa_session = self.transcript_sessions.get(transcript_id)
        if not qa_session:
            return

        transcript = qa_session["transcript"]

        for correction in corrections:
            seg_id = correction.get("segment_id")
            new_text = correction.get("corrected_text")
            
            # Find and update segment
            for seg in transcript.segments:
                if seg.segment_id == seg_id:
                    seg.text = new_text
                    # Recalculate confidence (simplified)
                    seg.confidence = max(0.5, seg.confidence * 0.9)
                    break

        # Recalculate aggregate confidence
        if transcript.segments:
            transcript.aggregate_confidence = sum(seg.confidence for seg in transcript.segments) / len(transcript.segments)

        logger.info(f"Applied {len(corrections)} corrections to transcript {transcript_id}")

    async def get_qa_dashboard(self) -> Dict[str, Any]:
        """Get QA dashboard summary for transcripts."""
        total_transcripts = len(self.transcript_sessions)
        status_counts = {}
        confidence_distribution = {"high": 0, "medium": 0, "low": 0}

        for session in self.transcript_sessions.values():
            status = session["qa_status"]
            status_counts[status] = status_counts.get(status, 0) + 1

            confidence = session["transcript"].aggregate_confidence
            if confidence >= 0.9:
                confidence_distribution["high"] += 1
            elif confidence >= 0.7:
                confidence_distribution["medium"] += 1
            else:
                confidence_distribution["low"] += 1

        return {
            "total_transcripts": total_transcripts,
            "status_breakdown": status_counts,
            "confidence_distribution": confidence_distribution,
            "pending_review": status_counts.get("pending_review", 0),
            "auto_approved": status_counts.get("auto_approved", 0),
            "approved": status_counts.get("approved", 0),
            "rejected": status_counts.get("rejected", 0),
            "critical_issues": status_counts.get("critical_issue", 0),
            "generated_at": datetime.utcnow().isoformat(),
        }
