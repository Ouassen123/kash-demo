"""Repository for encrypted transcript storage and retrieval."""

from typing import Dict, Any, Optional, List
import json
import hashlib
from datetime import datetime
from pathlib import Path

from src.core.logging import get_logger
from .provider_base import TranscriptPackage

logger = get_logger(__name__)


class TranscriptRepository:
    """Manages encrypted storage and retrieval of transcript artifacts."""

    def __init__(self, storage_path: Optional[Path] = None, encryption_key: Optional[str] = None):
        """
        Initialize repository.

        Args:
            storage_path: Base path for transcript files (defaults to ./transcripts)
            encryption_key: Optional encryption key for sensitive data
        """
        self.storage_path = storage_path or Path("./transcripts")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.encryption_key = encryption_key or "default_transcript_key"
        self._index: Dict[str, Dict[str, Any]] = {}

    async def store_transcript(
        self,
        transcript: TranscriptPackage,
        audio_hash: Optional[str] = None,
        raw_audio_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Store a transcript package with metadata.

        Args:
            transcript: Structured transcript package
            audio_hash: Hash of the source audio for deduplication
            raw_audio_path: Optional path to raw audio file

        Returns:
            Storage result with file paths and metadata
        """
        try:
            # Generate transcript ID
            transcript_id = self._generate_transcript_id(transcript.session_id, transcript.prompt_id)

            # Prepare storage metadata
            storage_meta = {
                "transcript_id": transcript_id,
                "session_id": transcript.session_id,
                "prompt_id": transcript.prompt_id,
                "learner_id": transcript.learner_id,
                "audio_hash": audio_hash,
                "provider": transcript.provider,
                "qa_status": transcript.qa_status,
                "created_at": transcript.created_at,
                "stored_at": datetime.utcnow().isoformat(),
                "file_paths": {},
            }

            # Serialize transcript to JSON
            transcript_json = self._serialize_transcript(transcript)

            # Encrypt and store structured transcript
            encrypted_json = self._encrypt_data(transcript_json)
            json_path = self.storage_path / f"{transcript_id}.json.enc"
            json_path.write_text(encrypted_json)
            storage_meta["file_paths"]["structured"] = str(json_path)

            # Store plain text version for QA (redacted if needed)
            plain_text = self._extract_plain_text(transcript)
            text_path = self.storage_path / f"{transcript_id}.txt"
            text_path.write_text(plain_text)
            storage_meta["file_paths"]["plain_text"] = str(text_path)

            # Update index
            self._index[transcript_id] = storage_meta

            logger.info(f"Transcript stored: {transcript_id} for session {transcript.session_id}")
            return {
                "status": "stored",
                "transcript_id": transcript_id,
                "storage_meta": storage_meta,
            }

        except Exception as e:
            logger.error(f"Failed to store transcript for session {transcript.session_id}: {e}")
            return {"status": "error", "error": str(e)}

    async def retrieve_transcript(self, transcript_id: str) -> Optional[TranscriptPackage]:
        """
        Retrieve a transcript package by ID.

        Args:
            transcript_id: Unique transcript identifier

        Returns:
            Transcript package or None if not found
        """
        try:
            storage_meta = self._index.get(transcript_id)
            if not storage_meta:
                return None

            # Load and decrypt structured transcript
            json_path = Path(storage_meta["file_paths"]["structured"])
            encrypted_json = json_path.read_text()
            transcript_json = self._decrypt_data(encrypted_json)

            # Deserialize back to TranscriptPackage
            transcript = self._deserialize_transcript(transcript_json)

            logger.info(f"Transcript retrieved: {transcript_id}")
            return transcript

        except Exception as e:
            logger.error(f"Failed to retrieve transcript {transcript_id}: {e}")
            return None

    async def list_transcripts(
        self,
        session_id: Optional[str] = None,
        learner_id: Optional[str] = None,
        qa_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List transcripts with optional filtering.

        Args:
            session_id: Filter by session ID
            learner_id: Filter by learner ID
            qa_status: Filter by QA status

        Returns:
            List of transcript metadata entries
        """
        results = []
        for transcript_id, meta in self._index.items():
            # Apply filters
            if session_id and meta.get("session_id") != session_id:
                continue
            if learner_id and meta.get("learner_id") != learner_id:
                continue
            if qa_status and meta.get("qa_status") != qa_status:
                continue

            results.append(meta.copy())

        return results

    async def update_qa_status(self, transcript_id: str, qa_status: str, updated_by: Optional[str] = None) -> bool:
        """
        Update QA status for a transcript.

        Args:
            transcript_id: Transcript identifier
            qa_status: New QA status
            updated_by: Optional user who made the change

        Returns:
            True if updated successfully
        """
        if transcript_id not in self._index:
            return False

        self._index[transcript_id]["qa_status"] = qa_status
        self._index[transcript_id]["qa_updated_at"] = datetime.utcnow().isoformat()
        if updated_by:
            self._index[transcript_id]["qa_updated_by"] = updated_by

        logger.info(f"QA status updated for {transcript_id}: {qa_status}")
        return True

    async def purge_session(self, session_id: str) -> Dict[str, Any]:
        """
        Delete all transcripts for a session (privacy compliance).

        Args:
            session_id: Session ID to purge

        Returns:
            Purge result with counts and status
        """
        deleted_count = 0
        errors = []

        # Find all transcripts for this session
        to_delete = [
            tid for tid, meta in self._index.items()
            if meta.get("session_id") == session_id
        ]

        for transcript_id in to_delete:
            try:
                meta = self._index[transcript_id]
                
                # Delete files
                for file_path in meta.get("file_paths", {}).values():
                    Path(file_path).unlink(missing_ok=True)

                # Remove from index
                del self._index[transcript_id]
                deleted_count += 1

                logger.info(f"Purged transcript: {transcript_id}")

            except Exception as e:
                errors.append(f"Failed to purge {transcript_id}: {e}")
                logger.error(f"Purge error for {transcript_id}: {e}")

        return {
            "status": "completed",
            "session_id": session_id,
            "deleted_count": deleted_count,
            "errors": errors,
        }

    def _generate_transcript_id(self, session_id: str, prompt_id: str) -> str:
        """Generate unique transcript ID."""
        base = f"{session_id}_{prompt_id}_{datetime.utcnow().isoformat()}"
        return f"transcript_{hashlib.sha256(base.encode()).hexdigest()[:16]}"

    def _serialize_transcript(self, transcript: TranscriptPackage) -> str:
        """Serialize transcript package to JSON."""
        return json.dumps({
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
            "created_at": transcript.created_at,
            "qa_status": transcript.qa_status,
        }, indent=2)

    def _deserialize_transcript(self, transcript_json: str) -> TranscriptPackage:
        """Deserialize JSON back to TranscriptPackage."""
        from .provider_base import TranscriptSegment, TranscriptWord

        data = json.loads(transcript_json)

        segments = []
        for seg_data in data["segments"]:
            words = [
                TranscriptWord(
                    text=w["text"],
                    start=w["start"],
                    end=w["end"],
                    confidence=w["confidence"],
                )
                for w in seg_data["words"]
            ]

            segments.append(TranscriptSegment(
                segment_id=seg_data["segment_id"],
                speaker=seg_data["speaker"],
                start=seg_data["start"],
                end=seg_data["end"],
                text=seg_data["text"],
                confidence=seg_data["confidence"],
                words=words,
                noise_level=seg_data["noise_level"],
                flags=seg_data["flags"],
            ))

        return TranscriptPackage(
            session_id=data["session_id"],
            prompt_id=data["prompt_id"],
            learner_id=data["learner_id"],
            language=data["language"],
            segments=segments,
            aggregate_confidence=data["aggregate_confidence"],
            provider=data["provider"],
            created_at=data["created_at"],
            qa_status=data.get("qa_status", "pending_review"),
        )

    def _extract_plain_text(self, transcript: TranscriptPackage) -> str:
        """Extract plain text from transcript for QA review."""
        lines = []
        for seg in transcript.segments:
            timestamp = f"[{seg.start:.2f}-{seg.end:.2f}]"
            speaker_tag = f"{seg.speaker}:"
            lines.append(f"{timestamp} {speaker_tag} {seg.text}")
        return "\n".join(lines)

    def _encrypt_data(self, data: str) -> str:
        """Encrypt data (mock implementation)."""
        # In production, use proper encryption
        return f"enc_{hashlib.sha256((data + self.encryption_key).encode()).hexdigest()}_{data}"

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data (mock implementation)."""
        # In production, use proper decryption
        if encrypted_data.startswith("enc_"):
            # Extract original data after hash prefix
            parts = encrypted_data.split("_", 2)
            if len(parts) >= 3:
                return parts[2]
        return encrypted_data
