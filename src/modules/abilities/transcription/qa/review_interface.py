"""QA review interface for transcript inspection and correction."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from src.core.logging import get_logger
from ..provider_base import TranscriptPackage, TranscriptSegment, TranscriptWord

logger = get_logger(__name__)


@dataclass
class TranscriptCorrection:
    """Represents a correction made to a transcript."""
    segment_id: str
    original_text: str
    corrected_text: str
    correction_type: str  # text, timing, speaker, confidence
    corrected_by: str
    corrected_at: str
    reason: Optional[str] = None


@dataclass
class QAReviewSession:
    """QA review session for a transcript."""
    transcript_id: str
    reviewer_id: str
    started_at: str
    status: str  # in_progress, completed, abandoned
    corrections: List[TranscriptCorrection]
    notes: List[str]
    final_decision: Optional[str]  # approve, reject, needs_revision


class TranscriptReviewInterface:
    """Interface for QA reviewers to inspect and correct transcripts."""

    def __init__(self, qa_hooks, repository):
        """
        Initialize review interface.

        Args:
            qa_hooks: QA hooks for integration
            repository: Transcript repository for data access
        """
        self.qa_hooks = qa_hooks
        self.repository = repository
        self.review_sessions: Dict[str, QAReviewSession] = {}

    async def start_review_session(
        self,
        transcript_id: str,
        reviewer_id: str,
    ) -> Dict[str, Any]:
        """
        Start a new QA review session.

        Args:
            transcript_id: Transcript to review
            reviewer_id: Reviewer identifier

        Returns:
            Review session information
        """
        # Get transcript data
        transcript = await self.repository.retrieve_transcript(transcript_id)
        if not transcript:
            return {"error": "Transcript not found"}

        # Create review session
        session_id = f"review_{transcript_id}_{reviewer_id}_{datetime.utcnow().timestamp()}"
        review_session = QAReviewSession(
            transcript_id=transcript_id,
            reviewer_id=reviewer_id,
            started_at=datetime.utcnow().isoformat(),
            status="in_progress",
            corrections=[],
            notes=[],
            final_decision=None,
        )

        self.review_sessions[session_id] = review_session

        logger.info(f"Started QA review session {session_id} for transcript {transcript_id}")
        return {
            "session_id": session_id,
            "transcript_id": transcript_id,
            "reviewer_id": reviewer_id,
            "status": "in_progress",
            "started_at": review_session.started_at,
        }

    async def get_review_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get transcript data for review.

        Args:
            session_id: Review session ID

        Returns:
            Review-ready transcript data
        """
        session = self.review_sessions.get(session_id)
        if not session:
            return None

        # Get transcript from QA hooks
        transcript_data = await self.qa_hooks.get_transcript_for_review(session.transcript_id)
        if not transcript_data:
            return None

        # Add review-specific information
        transcript_data["review_session_id"] = session_id
        transcript_data["reviewer_id"] = session.reviewer_id
        transcript_data["review_started_at"] = session.started_at
        transcript_data["corrections_made"] = len(session.corrections)

        return transcript_data

    async def add_correction(
        self,
        session_id: str,
        segment_id: str,
        correction_type: str,
        original_value: Any,
        corrected_value: Any,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a correction to the transcript.

        Args:
            session_id: Review session ID
            segment_id: Segment being corrected
            correction_type: Type of correction
            original_value: Original value
            corrected_value: Corrected value
            reason: Reason for correction

        Returns:
            Correction result
        """
        session = self.review_sessions.get(session_id)
        if not session:
            return {"error": "Review session not found"}

        # Get original segment text
        transcript = await self.repository.retrieve_transcript(session.transcript_id)
        if not transcript:
            return {"error": "Transcript not found"}

        original_segment = None
        for seg in transcript.segments:
            if seg.segment_id == segment_id:
                original_segment = seg
                break

        if not original_segment:
            return {"error": "Segment not found"}

        # Create correction
        correction = TranscriptCorrection(
            segment_id=segment_id,
            original_text=str(original_value),
            corrected_text=str(corrected_value),
            correction_type=correction_type,
            corrected_by=session.reviewer_id,
            corrected_at=datetime.utcnow().isoformat(),
            reason=reason,
        )

        session.corrections.append(correction)

        logger.info(f"Added correction to session {session_id}: {correction_type}")
        return {
            "status": "correction_added",
            "correction_id": len(session.corrections),
            "segment_id": segment_id,
            "correction_type": correction_type,
        }

    async def add_note(self, session_id: str, note: str) -> Dict[str, Any]:
        """
        Add a review note.

        Args:
            session_id: Review session ID
            note: Review note text

        Returns:
            Note addition result
        """
        session = self.review_sessions.get(session_id)
        if not session:
            return {"error": "Review session not found"}

        note_entry = {
            "note": note,
            "added_by": session.reviewer_id,
            "added_at": datetime.utcnow().isoformat(),
        }

        session.notes.append(note)

        logger.info(f"Added note to review session {session_id}")
        return {
            "status": "note_added",
            "note_id": len(session.notes),
            "added_at": note_entry["added_at"],
        }

    async def complete_review(
        self,
        session_id: str,
        decision: str,
        final_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Complete the review session.

        Args:
            session_id: Review session ID
            decision: Final decision (approve/reject/needs_revision)
            final_notes: Optional final notes

        Returns:
            Review completion result
        """
        session = self.review_sessions.get(session_id)
        if not session:
            return {"error": "Review session not found"}

        session.status = "completed"
        session.final_decision = decision

        # Apply corrections if approved
        if decision == "approve" and session.corrections:
            corrections_data = [
                {
                    "segment_id": c.segment_id,
                    "correction_type": c.correction_type,
                    "original_text": c.original_text,
                    "corrected_text": c.corrected_text,
                    "reason": c.reason,
                }
                for c in session.corrections
            ]

            await self.qa_hooks.approve_transcript(
                session.transcript_id,
                session.reviewer_id,
                final_notes,
                corrections_data,
            )

        elif decision == "reject":
            await self.qa_hooks.reject_transcript(
                session.transcript_id,
                session.reviewer_id,
                final_notes or "Rejected during QA review",
            )

        logger.info(f"Completed review session {session_id} with decision: {decision}")
        return {
            "status": "completed",
            "session_id": session_id,
            "decision": decision,
            "corrections_applied": len(session.corrections),
            "review_duration_seconds": (
                datetime.utcnow() - datetime.fromisoformat(session.started_at)
            ).total_seconds(),
        }

    async def get_review_history(self, transcript_id: str) -> List[Dict[str, Any]]:
        """
        Get review history for a transcript.

        Args:
            transcript_id: Transcript ID

        Returns:
            List of review sessions
        """
        history = []
        for session_id, session in self.review_sessions.items():
            if session.transcript_id == transcript_id:
                history.append({
                    "session_id": session_id,
                    "reviewer_id": session.reviewer_id,
                    "started_at": session.started_at,
                    "status": session.status,
                    "final_decision": session.final_decision,
                    "corrections_count": len(session.corrections),
                    "notes_count": len(session.notes),
                })

        return sorted(history, key=lambda x: x["started_at"], reverse=True)

    async def get_reviewer_stats(self, reviewer_id: str) -> Dict[str, Any]:
        """
        Get statistics for a reviewer.

        Args:
            reviewer_id: Reviewer identifier

        Returns:
            Reviewer performance statistics
        """
        reviewer_sessions = [
            s for s in self.review_sessions.values()
            if s.reviewer_id == reviewer_id
        ]

        if not reviewer_sessions:
            return {"error": "No reviews found for reviewer"}

        total_reviews = len(reviewer_sessions)
        completed_reviews = len([s for s in reviewer_sessions if s.status == "completed"])
        approved_count = len([s for s in reviewer_sessions if s.final_decision == "approve"])
        rejected_count = len([s for s in reviewer_sessions if s.final_decision == "reject"])
        total_corrections = sum(len(s.corrections) for s in reviewer_sessions)

        # Calculate average review time
        completed_sessions = [s for s in reviewer_sessions if s.status == "completed"]
        avg_review_time = 0
        if completed_sessions:
            total_time = sum(
                (datetime.fromisoformat(s.started_at) - datetime.fromisoformat(s.started_at)).total_seconds()
                for s in completed_sessions
            )
            avg_review_time = total_time / len(completed_sessions)

        return {
            "reviewer_id": reviewer_id,
            "total_reviews": total_reviews,
            "completed_reviews": completed_reviews,
            "approval_rate": approved_count / completed_reviews if completed_reviews > 0 else 0,
            "rejection_rate": rejected_count / completed_reviews if completed_reviews > 0 else 0,
            "total_corrections": total_corrections,
            "avg_corrections_per_review": total_corrections / completed_reviews if completed_reviews > 0 else 0,
            "avg_review_time_seconds": avg_review_time,
        }
