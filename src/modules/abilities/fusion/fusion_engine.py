"""Fusion logic for cognitive and behavioral feature generation."""

from typing import Dict, Any, List, Optional, Tuple
import json
import math
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class MultimodalFusionEngine:
    """Fuses multimodal data into interpretable cognitive and behavioral features."""

    def __init__(self, modality_weights: Optional[Dict[str, float]] = None):
        """
        Initialize fusion engine.

        Args:
            modality_weights: Optional weights for text, audio, behavioral modalities
        """
        self.modality_weights = modality_weights or {
            "text": 0.4,
            "audio": 0.4,
            "behavioral": 0.2,
        }
        self.feature_version = "1.0"

    def fuse_session_features(
        self,
        session_data: Dict[str, Any],
        alignment_data: Optional[Dict[str, Any]] = None,
        fallback_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Fuse session data into interpretable feature vectors.

        Args:
            session_data: Complete session data from preprocessor
            alignment_data: Optional synchronization data
            fallback_data: Optional fallback handling data

        Returns:
            Fusion result with feature vectors and confidence metadata.
        """
        session_id = session_data["session_id"]
        
        # Extract modality-specific features
        text_features = self._extract_text_features(session_data.get("text_data"))
        audio_features = self._extract_audio_features(session_data.get("audio_data"))
        behavioral_features = self._extract_behavioral_features(session_data.get("behavioral_tags"))

        # Apply modality weights
        weighted_features = self._apply_modality_weights(
            text_features, audio_features, behavioral_features
        )

        # Generate cognitive dimensions
        cognitive_features = self._generate_cognitive_dimensions(weighted_features)
        
        # Generate behavioral indicators
        behavioral_indicators = self._generate_behavioral_indicators(weighted_features)

        # Calculate confidence scores
        confidence_metadata = self._calculate_confidence(
            text_features, audio_features, behavioral_features,
            alignment_data, fallback_data
        )

        # Create final feature vector
        feature_vector = self._create_feature_vector(
            cognitive_features, behavioral_indicators, weighted_features
        )

        # Generate interpretability metadata
        interpretability = self._generate_interpretability(
            text_features, audio_features, behavioral_features,
            cognitive_features, behavioral_indicators
        )

        fusion_result = {
            "session_id": session_id,
            "feature_vector": feature_vector,
            "cognitive_features": cognitive_features,
            "behavioral_indicators": behavioral_indicators,
            "modality_contributions": {
                "text": self._get_modality_contribution(text_features),
                "audio": self._get_modality_contribution(audio_features),
                "behavioral": self._get_modality_contribution(behavioral_features),
            },
            "confidence_metadata": confidence_metadata,
            "interpretability": interpretability,
            "feature_version": self.feature_version,
            "fused_at": datetime.utcnow().isoformat(),
        }
        fusion_result["modality"] = fusion_result["modality_contributions"]

        logger.info(f"Fused features for session {session_id} with confidence {confidence_metadata['overall_confidence']:.2f}")
        return fusion_result

    def _extract_text_features(self, text_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract features from text responses."""
        if not text_data or not text_data.get("responses"):
            return {"available": False, "features": {}}

        metrics = {
            "response_count": len(text_data["responses"]),
            "avg_response_length": 0.0,
            "lexical_diversity": 0.0,
            "response_time_variance": 0.0,
            "content_complexity": 0.0,
        }

        # Calculate text metrics
        total_length = 0
        lengths = []
        timestamps = []
        
        for response in text_data["responses"]:
            text = response.get("response_text", "")
            total_length += len(text)
            lengths.append(len(text))
            if "timestamp" in response:
                timestamps.append(response["timestamp"])

        if lengths:
            metrics["avg_response_length"] = sum(lengths) / len(lengths)
            metrics["lexical_diversity"] = self._calculate_lexical_diversity(text_data["responses"])
            metrics["response_time_variance"] = self._calculate_time_variance(timestamps)
            metrics["content_complexity"] = self._calculate_content_complexity(text_data["responses"])

        result = {"available": True, "features": metrics}
        result.update(metrics)
        return result

    def _extract_audio_features(self, audio_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract features from audio segments."""
        if not audio_data or not audio_data.get("segments"):
            return {"available": False, "features": {}}

        metrics = {
            "segment_count": len(audio_data["segments"]),
            "total_duration": 0.0,
            "avg_speaking_rate": 0.0,
            "voice_stability": 0.0,
            "prosody_variance": 0.0,
            "audio_quality": 0.0,
        }

        # Calculate audio metrics
        total_duration = 0.0
        speaking_rates = []
        stabilities = []
        
        for segment in audio_data["segments"]:
            duration = segment.get("duration_seconds", 0.0)
            total_duration += duration
            
            # Mock speaking rate calculation (words per minute)
            word_count = len(segment.get("transcript", "").split()) if "transcript" in segment else 10
            speaking_rate = (word_count / duration * 60) if duration > 0 else 0
            speaking_rates.append(speaking_rate)
            
            # Mock stability and prosody features
            stabilities.append(segment.get("stability_score", 0.5))

        if speaking_rates:
            metrics["total_duration"] = total_duration
            metrics["avg_speaking_rate"] = sum(speaking_rates) / len(speaking_rates)
            metrics["voice_stability"] = sum(stabilities) / len(stabilities)
            metrics["prosody_variance"] = self._calculate_variance(speaking_rates)
            metrics["audio_quality"] = self._calculate_audio_quality(audio_data["segments"])

        result = {"available": True, "features": metrics}
        result.update(metrics)
        return result

    def _extract_behavioral_features(self, behavioral_tags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract features from behavioral tags."""
        if not behavioral_tags:
            return {"available": False, "features": {}}

        metrics = {
            "tag_count": len(behavioral_tags),
            "engagement_level": 0.0,
            "persistence_score": 0.0,
            "adaptability_score": 0.0,
            "emotional_regulation": 0.0,
        }

        # Calculate behavioral metrics
        engagement_scores = []
        persistence_scores = []
        adaptability_scores = []
        emotional_scores = []
        
        for tag in behavioral_tags:
            tag_type = tag.get("tag_type", "general")
            confidence = tag.get("confidence", 0.5)
            value = tag.get("value", 0.5)
            
            if tag_type == "engagement":
                engagement_scores.append(confidence * value)
            elif tag_type == "persistence":
                persistence_scores.append(confidence * value)
            elif tag_type == "adaptability":
                adaptability_scores.append(confidence * value)
            elif tag_type == "emotional":
                emotional_scores.append(confidence * value)

        if engagement_scores:
            metrics["engagement_level"] = sum(engagement_scores) / len(engagement_scores)
        if persistence_scores:
            metrics["persistence_score"] = sum(persistence_scores) / len(persistence_scores)
        if adaptability_scores:
            metrics["adaptability_score"] = sum(adaptability_scores) / len(adaptability_scores)
        if emotional_scores:
            metrics["emotional_regulation"] = sum(emotional_scores) / len(emotional_scores)

        result = {"available": True, "features": metrics}
        result.update(metrics)
        return result

    def _apply_modality_weights(
        self,
        text_features: Dict[str, Any],
        audio_features: Dict[str, Any],
        behavioral_features: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply modality weights to features."""
        weighted = {
            "text": text_features.copy(),
            "audio": audio_features.copy(),
            "behavioral": behavioral_features.copy(),
        }

        # Apply weights to available modalities
        if text_features.get("available"):
            for key, value in text_features.get("features", {}).items():
                if isinstance(value, (int, float)):
                    weighted["text"]["features"][key] = value * self.modality_weights["text"]

        if audio_features.get("available"):
            for key, value in audio_features.get("features", {}).items():
                if isinstance(value, (int, float)):
                    weighted["audio"]["features"][key] = value * self.modality_weights["audio"]

        if behavioral_features.get("available"):
            for key, value in behavioral_features.get("features", {}).items():
                if isinstance(value, (int, float)):
                    weighted["behavioral"]["features"][key] = value * self.modality_weights["behavioral"]

        return weighted

    def _generate_cognitive_dimensions(self, weighted_features: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cognitive dimension scores."""
        dimensions = {
            "reasoning": 0.0,
            "comprehension": 0.0,
            "creativity": 0.0,
            "memory": 0.0,
            "attention": 0.0,
            "executive_function": 0.0,
        }

        # Text contributions to cognitive dimensions
        if weighted_features["text"].get("available"):
            text_feats = weighted_features["text"]["features"]
            dimensions["reasoning"] += text_feats.get("content_complexity", 0) * 0.6
            dimensions["comprehension"] += text_feats.get("avg_response_length", 0) * 0.4
            dimensions["memory"] += text_feats.get("lexical_diversity", 0) * 0.5
            dimensions["attention"] += text_feats.get("response_time_variance", 0) * 0.3

        # Audio contributions to cognitive dimensions
        if weighted_features["audio"].get("available"):
            audio_feats = weighted_features["audio"]["features"]
            dimensions["attention"] += audio_feats.get("voice_stability", 0) * 0.4
            dimensions["executive_function"] += audio_feats.get("prosody_variance", 0) * 0.3
            dimensions["reasoning"] += audio_feats.get("avg_speaking_rate", 0) * 0.2

        # Behavioral contributions to cognitive dimensions
        if weighted_features["behavioral"].get("available"):
            beh_feats = weighted_features["behavioral"]["features"]
            dimensions["executive_function"] += beh_feats.get("persistence_score", 0) * 0.5
            dimensions["attention"] += beh_feats.get("engagement_level", 0) * 0.3
            dimensions["creativity"] += beh_feats.get("adaptability_score", 0) * 0.4

        # Normalize dimensions to 0-1 range
        for key in dimensions:
            dimensions[key] = min(1.0, max(0.0, dimensions[key]))

        return dimensions

    def _generate_behavioral_indicators(self, weighted_features: Dict[str, Any]) -> Dict[str, Any]:
        """Generate behavioral indicator scores."""
        indicators = {
            "task_engagement": 0.0,
            "social_collaboration": 0.0,
            "self_regulation": 0.0,
            "problem_solving": 0.0,
            "communication": 0.0,
        }

        # Text contributions
        if weighted_features["text"].get("available"):
            text_feats = weighted_features["text"]["features"]
            indicators["communication"] += text_feats.get("avg_response_length", 0) * 0.3
            indicators["problem_solving"] += text_feats.get("content_complexity", 0) * 0.4

        # Audio contributions
        if weighted_features["audio"].get("available"):
            audio_feats = weighted_features["audio"]["features"]
            indicators["communication"] += audio_feats.get("audio_quality", 0) * 0.4
            indicators["self_regulation"] += audio_feats.get("voice_stability", 0) * 0.3

        # Behavioral contributions
        if weighted_features["behavioral"].get("available"):
            beh_feats = weighted_features["behavioral"]["features"]
            indicators["task_engagement"] += beh_feats.get("engagement_level", 0) * 0.5
            indicators["self_regulation"] += beh_feats.get("emotional_regulation", 0) * 0.4
            indicators["social_collaboration"] += beh_feats.get("adaptability_score", 0) * 0.3

        # Normalize indicators to 0-1 range
        for key in indicators:
            indicators[key] = min(1.0, max(0.0, indicators[key]))

        return indicators

    def _calculate_confidence(
        self,
        text_features: Dict[str, Any],
        audio_features: Dict[str, Any],
        behavioral_features: Dict[str, Any],
        alignment_data: Optional[Dict[str, Any]],
        fallback_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate confidence scores for fusion results."""
        confidence = {
            "modality_confidence": {},
            "alignment_confidence": 0.0,
            "overall_confidence": 0.0,
            "adjustments": [],
        }

        # Modality-specific confidence
        available_modalities = 0
        confidence_sum = 0.0

        if text_features.get("available"):
            text_conf = 0.8  # High confidence in text analysis
            confidence["modality_confidence"]["text"] = text_conf
            confidence_sum += text_conf
            available_modalities += 1

        if audio_features.get("available"):
            audio_conf = 0.7  # Medium confidence in audio analysis
            confidence["modality_confidence"]["audio"] = audio_conf
            confidence_sum += audio_conf
            available_modalities += 1

        if behavioral_features.get("available"):
            beh_conf = 0.6  # Lower confidence in behavioral tags
            confidence["modality_confidence"]["behavioral"] = beh_conf
            confidence_sum += beh_conf
            available_modalities += 1

        # Alignment confidence
        if alignment_data:
            confidence["alignment_confidence"] = alignment_data.get("alignment_confidence", 0.0)
            if confidence["alignment_confidence"] < 0.5:
                confidence["adjustments"].append("Poor temporal alignment detected")

        # Fallback adjustments
        if fallback_data:
            adjustment = fallback_data.get("confidence_adjustment", 0.0)
            confidence_sum += adjustment
            confidence["adjustments"].append(f"fallback adjustment: {adjustment}")

        # Normalize overall confidence
        if available_modalities > 0:
            confidence["overall_confidence"] = max(0.0, min(1.0, confidence_sum / available_modalities))
        else:
            confidence["overall_confidence"] = 0.0
            confidence["adjustments"].append("No modalities available")

        return confidence

    def _create_feature_vector(
        self,
        cognitive_features: Dict[str, Any],
        behavioral_indicators: Dict[str, Any],
        weighted_features: Dict[str, Any],
    ) -> List[float]:
        """Create final feature vector."""
        has_modalities = any(weighted_features[m].get("available") for m in ["text", "audio", "behavioral"])
        if not has_modalities:
            return []

        vector = []

        # Add cognitive dimensions
        for key, value in cognitive_features.items():
            vector.append(value)

        # Add behavioral indicators
        for key, value in behavioral_indicators.items():
            vector.append(value)

        for modality in ["text", "audio", "behavioral"]:
            if weighted_features[modality].get("available"):
                for key, value in weighted_features[modality].get("features", {}).items():
                    if isinstance(value, (int, float)):
                        vector.append(value)

        return vector

    def _generate_interpretability(
        self,
        text_features: Dict[str, Any],
        audio_features: Dict[str, Any],
        behavioral_features: Dict[str, Any],
        cognitive_features: Dict[str, Any],
        behavioral_indicators: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate interpretability metadata."""
        return {
            "feature_importance": {
                "text_features": self._calculate_feature_importance(text_features),
                "audio_features": self._calculate_feature_importance(audio_features),
                "behavioral_features": self._calculate_feature_importance(behavioral_features),
            },
            "dimension_explanations": {
                "reasoning": "Logical reasoning and problem-solving ability",
                "comprehension": "Understanding and processing information",
                "creativity": "Original and innovative thinking",
                "memory": "Information retention and recall",
                "attention": "Focus and concentration",
                "executive_function": "Planning and self-regulation",
            },
            "indicator_explanations": {
                "task_engagement": "Level of participation and involvement",
                "social_collaboration": "Ability to work with others",
                "self_regulation": "Emotional and behavioral control",
                "problem_solving": "Approach to challenges",
                "communication": "Clarity and effectiveness of expression",
            },
            "modality_contributions": {
                "text": "Written responses and content analysis",
                "audio": "Speech patterns and vocal characteristics",
                "behavioral": "Observed behaviors and interactions",
            },
        }

    def _get_modality_contribution(self, features: Dict[str, Any]) -> float:
        """Get overall contribution score for a modality."""
        if not features.get("available"):
            return 0.0

        feature_values = [
            v for v in features.get("features", {}).values()
            if isinstance(v, (int, float))
        ]
        return sum(feature_values) / len(feature_values) if feature_values else 0.0

    def _calculate_lexical_diversity(self, responses: List[Dict[str, Any]]) -> float:
        """Calculate lexical diversity in text responses."""
        all_words = set()
        total_words = 0
        
        for response in responses:
            words = response.get("response_text", "").lower().split()
            all_words.update(words)
            total_words += len(words)

        return len(all_words) / total_words if total_words > 0 else 0.0

    def _calculate_time_variance(self, timestamps: List[str]) -> float:
        """Calculate variance in response timestamps."""
        if len(timestamps) < 2:
            return 0.0

        times = [datetime.fromisoformat(ts).timestamp() for ts in timestamps]
        mean_time = sum(times) / len(times)
        variance = sum((t - mean_time) ** 2 for t in times) / len(times)
        return math.sqrt(variance) / mean_time if mean_time > 0 else 0.0

    def _calculate_content_complexity(self, responses: List[Dict[str, Any]]) -> float:
        """Calculate content complexity based on response length and structure."""
        avg_length = sum(len(r.get("response_text", "")) for r in responses) / len(responses)
        # Normalize to 0-1 scale (assuming max 500 chars as high complexity)
        return min(1.0, avg_length / 500.0)

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values."""
        if len(values) < 2:
            return 0.0
        mean_val = sum(values) / len(values)
        return sum((v - mean_val) ** 2 for v in values) / len(values)

    def _calculate_audio_quality(self, segments: List[Dict[str, Any]]) -> float:
        """Calculate overall audio quality score."""
        quality_scores = [s.get("quality_score", 0.5) for s in segments]
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.5

    def _calculate_feature_importance(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Calculate importance scores for features."""
        if not features.get("available"):
            return {}

        importance = {}
        for key, value in features.get("features", {}).items():
            if isinstance(value, (int, float)):
                # Simple importance based on feature magnitude
                importance[key] = abs(value)
        return importance
