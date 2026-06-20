"""Preprocessing pipelines for synchronizing text, audio, and behavioral metadata."""

from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class MultimodalPreprocessor:
    """Preprocesses and synchronizes multimodal data for fusion."""

    def __init__(self):
        """Initialize preprocessor."""
        self.session_data: Dict[str, Dict[str, Any]] = {}

    def register_session(self, session_id: str) -> Dict[str, Any]:
        """
        Register a new fusion session.

        Args:
            session_id: Session identifier (shared with text/audio services)

        Returns:
            Session registration result.
        """
        session = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "text_data": None,
            "audio_data": None,
            "behavioral_tags": [],
            "metadata": {},
            "status": "initialized",
            "warnings": [],
        }
        self.session_data[session_id] = session

        logger.info(f"Registered fusion session {session_id}")
        return {
            "session_id": session_id,
            "status": session["status"],
            "created_at": session["created_at"],
        }

    def add_text_data(
        self,
        session_id: str,
        text_responses: List[Dict[str, Any]],
        prompt_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add text response data to session.

        Args:
            session_id: Session identifier
            text_responses: List of text responses with timestamps
            prompt_metadata: Optional prompt-level metadata

        Returns:
            Addition result.
        """
        session = self.session_data.get(session_id)
        if not session:
            return {"error": "Session not found"}

        # Validate text data
        if not text_responses:
            session["warnings"].append("No text responses provided")
            return {"error": "No text responses provided"}

        # Process and validate timestamps
        processed_responses = []
        for i, response in enumerate(text_responses):
            if "response_text" not in response:
                response["response_text"] = f"Response {i+1}"
            if "timestamp" not in response:
                response["timestamp"] = datetime.utcnow().isoformat()
            if "prompt_id" not in response:
                response["prompt_id"] = f"prompt_{i+1}"
            processed_responses.append(response)

        session["text_data"] = {
            "responses": processed_responses,
            "prompt_metadata": prompt_metadata or {},
            "added_at": datetime.utcnow().isoformat(),
        }
        session["status"] = "text_added"

        logger.info(f"Added {len(processed_responses)} text responses to session {session_id}")
        return {
            "session_id": session_id,
            "status": "text_added",
            "responses_count": len(processed_responses),
        }

    def add_audio_data(
        self,
        session_id: str,
        audio_segments: List[Dict[str, Any]],
        audio_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add audio segment data to session.

        Args:
            session_id: Session identifier
            audio_segments: List of audio segments with timestamps
            audio_metadata: Optional audio-level metadata

        Returns:
            Addition result.
        """
        session = self.session_data.get(session_id)
        if not session:
            return {"error": "Session not found"}

        # Validate audio data
        if not audio_segments:
            session["warnings"].append("No audio segments provided")
            return {"error": "No audio segments provided"}

        # Process and validate timestamps
        processed_segments = []
        for i, segment in enumerate(audio_segments):
            if "audio_blob" not in segment:
                segment["audio_blob"] = b"mock_audio_" + str(i).encode()
            if "timestamp" not in segment:
                segment["timestamp"] = datetime.utcnow().isoformat()
            if "duration_seconds" not in segment:
                segment["duration_seconds"] = 5.0
            if "prompt_id" not in segment:
                segment["prompt_id"] = f"prompt_{i+1}"
            processed_segments.append(segment)

        session["audio_data"] = {
            "segments": processed_segments,
            "audio_metadata": audio_metadata or {},
            "added_at": datetime.utcnow().isoformat(),
        }
        if session["status"] == "text_added":
            session["status"] = "audio_added"
        elif session["status"] == "initialized":
            session["status"] = "audio_only"

        logger.info(f"Added {len(processed_segments)} audio segments to session {session_id}")
        return {
            "session_id": session_id,
            "status": session["status"],
            "segments_count": len(processed_segments),
        }

    def add_behavioral_tags(
        self,
        session_id: str,
        behavioral_tags: List[Dict[str, Any]],
        tag_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add behavioral tags to session.

        Args:
            session_id: Session identifier
            behavioral_tags: List of behavioral tags with timestamps
            tag_metadata: Optional tag-level metadata

        Returns:
            Addition result.
        """
        session = self.session_data.get(session_id)
        if not session:
            return {"error": "Session not found"}

        # Process tags
        processed_tags = []
        for i, tag in enumerate(behavioral_tags):
            if "tag_type" not in tag:
                tag["tag_type"] = "general"
            if "value" not in tag:
                tag["value"] = f"tag_{i+1}"
            if "confidence" not in tag:
                tag["confidence"] = 0.5
            if "timestamp" not in tag:
                tag["timestamp"] = datetime.utcnow().isoformat()
            processed_tags.append(tag)

        session["behavioral_tags"] = processed_tags
        session["metadata"]["tag_metadata"] = tag_metadata or {}

        # Update status if needed
        if session["status"] in ["text_added", "audio_added"]:
            session["status"] = "tags_added"
        elif session["status"] in ["text_only", "audio_only", "initialized"]:
            session["status"] = "partial"

        logger.info(f"Added {len(processed_tags)} behavioral tags to session {session_id}")
        return {
            "session_id": session_id,
            "status": session["status"],
            "tags_count": len(processed_tags),
        }

    def synchronize_modalities(self, session_id: str) -> Dict[str, Any]:
        """
        Synchronize time-aligned modalities and detect misalignments.

        Args:
            session_id: Session identifier

        Returns:
            Synchronization result with alignment metrics.
        """
        session = self.session_data.get(session_id)
        if not session:
            return {"error": "Session not found"}

        alignment_result = {
            "session_id": session_id,
            "text_count": 0,
            "audio_count": 0,
            "tags_count": len(session["behavioral_tags"]),
            "aligned_pairs": 0,
            "aligned_pair_details": [],
            "misalignments": [],
            "missing_modalities": [],
            "alignment_confidence": 0.0,
        }

        # Count modalities
        if session["text_data"]:
            alignment_result["text_count"] = len(session["text_data"]["responses"])
        if session["audio_data"]:
            alignment_result["audio_count"] = len(session["audio_data"]["segments"])

        # Find aligned pairs by prompt_id
        text_by_prompt = {}
        if session["text_data"]:
            for response in session["text_data"]["responses"]:
                prompt_id = response["prompt_id"]
                text_by_prompt[prompt_id] = response

        audio_by_prompt = {}
        if session["audio_data"]:
            for segment in session["audio_data"]["segments"]:
                prompt_id = segment["prompt_id"]
                audio_by_prompt[prompt_id] = segment

        # Find aligned pairs
        common_prompts = set(text_by_prompt.keys()) & set(audio_by_prompt.keys())
        good_alignment_count = 0
        aligned_pair_details = []
        for prompt_id in common_prompts:
            text_resp = text_by_prompt[prompt_id]
            audio_seg = audio_by_prompt[prompt_id]
            
            # Calculate time difference
            text_time = datetime.fromisoformat(text_resp["timestamp"])
            audio_time = datetime.fromisoformat(audio_seg["timestamp"])
            time_diff = abs((text_time - audio_time).total_seconds())
            alignment_quality = "good" if time_diff < 60 else "poor"
            if alignment_quality == "good":
                good_alignment_count += 1
            
            aligned_pair_details.append({
                "prompt_id": prompt_id,
                "time_difference_seconds": time_diff,
                "text_timestamp": text_resp["timestamp"],
                "audio_timestamp": audio_seg["timestamp"],
                "alignment_quality": alignment_quality,
            })

        # Detect misalignments
        for prompt_id in common_prompts:
            pair = next(p for p in aligned_pair_details if p["prompt_id"] == prompt_id)
            if pair["alignment_quality"] == "poor":
                alignment_result["misalignments"].append({
                    "prompt_id": prompt_id,
                    "issue": "time_difference",
                    "time_difference_seconds": pair["time_difference_seconds"],
                })

        # Detect missing modalities
        text_only_prompts = set(text_by_prompt.keys()) - set(audio_by_prompt.keys())
        audio_only_prompts = set(audio_by_prompt.keys()) - set(text_by_prompt.keys())
        
        for prompt_id in text_only_prompts:
            alignment_result["missing_modalities"].append({
                "prompt_id": prompt_id,
                "missing": "audio",
                "available": "text",
            })
        
        for prompt_id in audio_only_prompts:
            alignment_result["missing_modalities"].append({
                "prompt_id": prompt_id,
                "missing": "text",
                "available": "audio",
            })

        # Attach alignment metadata
        alignment_result["aligned_pair_details"] = aligned_pair_details
        alignment_result["aligned_pairs"] = len(aligned_pair_details)

        # Calculate overall alignment confidence
        total_expected = max(alignment_result["text_count"], alignment_result["audio_count"])
        if total_expected > 0:
            alignment_result["alignment_confidence"] = good_alignment_count / total_expected

        # Update session status
        if alignment_result["alignment_confidence"] > 0.8:
            session["status"] = "synchronized"
        elif alignment_result["alignment_confidence"] > 0.5:
            session["status"] = "partially_synchronized"
        else:
            session["status"] = "poorly_synchronized"

        session["synchronization"] = alignment_result
        session["synchronized_at"] = datetime.utcnow().isoformat()

        logger.info(f"Synchronized session {session_id} with confidence {alignment_result['alignment_confidence']:.2f}")
        return alignment_result

    def handle_partial_session(self, session_id: str) -> Dict[str, Any]:
        """
        Handle partial sessions gracefully with fallbacks.

        Args:
            session_id: Session identifier

        Returns:
            Fallback handling result.
        """
        session = self.session_data.get(session_id)
        if not session:
            return {"error": "Session not found"}

        fallback_result = {
            "session_id": session_id,
            "available_modalities": [],
            "missing_modalities": [],
            "fallback_strategy": None,
            "confidence_adjustment": 0.0,
        }

        # Check available modalities
        if session["text_data"]:
            fallback_result["available_modalities"].append("text")
        if session["audio_data"]:
            fallback_result["available_modalities"].append("audio")
        if session["behavioral_tags"]:
            fallback_result["available_modalities"].append("behavioral")

        # Determine missing modalities
        all_modalities = ["text", "audio", "behavioral"]
        fallback_result["missing_modalities"] = [m for m in all_modalities if m not in fallback_result["available_modalities"]]

        # Apply fallback strategy
        if len(fallback_result["available_modalities"]) == 1:
            fallback_result["fallback_strategy"] = "single_modality"
            fallback_result["confidence_adjustment"] = -0.3
        elif len(fallback_result["available_modalities"]) == 2:
            fallback_result["fallback_strategy"] = "dual_modality"
            fallback_result["confidence_adjustment"] = -0.1
        else:
            fallback_result["fallback_strategy"] = "full_modality"
            fallback_result["confidence_adjustment"] = 0.0

        session["fallback"] = fallback_result
        session["status"] = "partial_handled"

        logger.info(f"Applied fallback strategy for session {session_id}: {fallback_result['fallback_strategy']}")
        return fallback_result

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get complete session summary."""
        session = self.session_data.get(session_id)
        if not session:
            return None

        return {
            "session_id": session_id,
            "status": session["status"],
            "created_at": session["created_at"],
            "text_data": session.get("text_data"),
            "audio_data": session.get("audio_data"),
            "behavioral_tags": session["behavioral_tags"],
            "metadata": session["metadata"],
            "warnings": session["warnings"],
            "synchronization": session.get("synchronization"),
            "fallback": session.get("fallback"),
        }
