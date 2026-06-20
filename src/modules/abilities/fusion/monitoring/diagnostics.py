"""Diagnostics and monitoring for multimodal fusion."""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta

from src.core.logging import get_logger

logger = get_logger(__name__)


class FusionDiagnostics:
    """Provides diagnostics and monitoring for multimodal fusion."""

    def __init__(self):
        """Initialize diagnostics system."""
        self.session_diagnostics: Dict[str, Dict[str, Any]] = {}
        self.system_metrics: Dict[str, Any] = {}
        self.alert_thresholds = {
            "alignment_confidence": 0.5,
            "overall_confidence": 0.6,
            "missing_modalities_threshold": 1,
        }

    def record_session_diagnostics(
        self,
        session_id: str,
        fusion_result: Dict[str, Any],
        session_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Record diagnostic information for a fusion session.

        Args:
            session_id: Session identifier
            fusion_result: Result from fusion engine
            session_data: Complete session data

        Returns:
            Diagnostic recording result.
        """
        diagnostics = {
            "session_id": session_id,
            "recorded_at": datetime.utcnow().isoformat(),
            "fusion_confidence": fusion_result["confidence_metadata"],
            "modality_availability": self._check_modality_availability(session_data),
            "data_quality_metrics": self._calculate_data_quality_metrics(session_data),
            "performance_metrics": self._calculate_performance_metrics(fusion_result),
            "alerts": [],
            "recommendations": [],
        }

        # Check for alerts
        alerts = self._generate_alerts(diagnostics, fusion_result)
        diagnostics["alerts"] = alerts

        # Generate recommendations
        recommendations = self._generate_recommendations(diagnostics, fusion_result)
        diagnostics["recommendations"] = recommendations

        # Store diagnostics
        self.session_diagnostics[session_id] = diagnostics

        logger.info(f"Recorded diagnostics for session {session_id} with {len(alerts)} alerts")
        return {
            "session_id": session_id,
            "alerts_count": len(alerts),
            "recommendations_count": len(recommendations),
            "recorded_at": diagnostics["recorded_at"],
            "alerts": alerts,
            "recommendations": recommendations,
            "diagnostics": diagnostics,
        }

    def get_session_diagnostics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get diagnostic information for a session."""
        return self.session_diagnostics.get(session_id)

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics."""
        if not self.session_diagnostics:
            return {
                "status": "no_data",
                "message": "No session diagnostics available",
                "generated_at": datetime.utcnow().isoformat(),
            }

        total_sessions = len(self.session_diagnostics)
        recent_sessions = self._get_recent_sessions(hours=24)
        
        health_metrics = {
            "total_sessions": total_sessions,
            "recent_sessions_24h": len(recent_sessions),
            "average_confidence": self._calculate_average_confidence(recent_sessions),
            "alert_rate": self._calculate_alert_rate(recent_sessions),
            "modality_availability": self._calculate_modality_availability_stats(recent_sessions),
            "system_status": "healthy",
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Determine system status
        if health_metrics["alert_rate"] > 0.3:
            health_metrics["system_status"] = "degraded"
        elif health_metrics["alert_rate"] > 0.5:
            health_metrics["system_status"] = "critical"

        return health_metrics

    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of recent alerts."""
        recent_sessions = self._get_recent_sessions(hours=hours)
        
        alert_summary = {
            "timeframe_hours": hours,
            "total_sessions": len(recent_sessions),
            "alerts_by_type": {},
            "alerts_by_severity": {},
            "alert_trends": [],
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Aggregate alerts
        for session_id, diagnostics in recent_sessions.items():
            for alert in diagnostics.get("alerts", []):
                alert_type = alert.get("type", "unknown")
                severity = alert.get("severity", "medium")
                
                alert_summary["alerts_by_type"][alert_type] = alert_summary["alerts_by_type"].get(alert_type, 0) + 1
                alert_summary["alerts_by_severity"][severity] = alert_summary["alerts_by_severity"].get(severity, 0) + 1

        return alert_summary

    def get_modality_drift_report(self, days: int = 7) -> Dict[str, Any]:
        """Report on modality availability drift over time."""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        drift_data = {
            "timeframe_days": days,
            "modality_trends": {},
            "drift_detected": False,
            "drift_details": [],
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Calculate daily modality availability
        daily_availability = {}
        for session_id, diagnostics in self.session_diagnostics.items():
            recorded_at = datetime.fromisoformat(diagnostics["recorded_at"])
            if recorded_at >= cutoff_time:
                day_key = recorded_at.strftime("%Y-%m-%d")
                if day_key not in daily_availability:
                    daily_availability[day_key] = {"text": 0, "audio": 0, "behavioral": 0}
                
                availability = diagnostics["modality_availability"]
                for modality, available in availability.items():
                    if available:
                        daily_availability[day_key][modality] += 1

        # Detect trends
        if len(daily_availability) > 1:
            days = sorted(daily_availability.keys())
            first_day = daily_availability[days[0]]
            last_day = daily_availability[days[-1]]
            
            for modality in ["text", "audio", "behavioral"]:
                first_rate = first_day[modality] / len(daily_availability)
                last_rate = last_day[modality] / len(daily_availability)
                change = last_rate - first_rate
                
                drift_data["modality_trends"][modality] = {
                    "initial_rate": first_rate,
                    "final_rate": last_rate,
                    "change": change,
                    "trend": "increasing" if change > 0.1 else "decreasing" if change < -0.1 else "stable"
                }
                
                # Detect significant drift
                if abs(change) > 0.2:
                    drift_data["drift_detected"] = True
                    drift_data["drift_details"].append({
                        "modality": modality,
                        "change": change,
                        "severity": "high" if abs(change) > 0.3 else "medium",
                    })

        return drift_data

    def export_diagnostics_report(self, format_type: str = "json") -> Dict[str, Any]:
        """Export comprehensive diagnostics report."""
        report = {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "format_type": format_type,
                "total_sessions": len(self.session_diagnostics),
            },
            "system_health": self.get_system_health(),
            "alert_summary": self.get_alert_summary(),
            "modality_drift": self.get_modality_drift_report(),
            "session_diagnostics": list(self.session_diagnostics.values()),
        }

        if format_type == "json":
            return report
        else:
            return {"error": f"Unsupported format: {format_type}"}

    def _check_modality_availability(self, session_data: Dict[str, Any]) -> Dict[str, bool]:
        """Check availability of each modality."""
        return {
            "text": bool(session_data.get("text_data")),
            "audio": bool(session_data.get("audio_data")),
            "behavioral": bool(session_data.get("behavioral_tags")),
        }

    def _calculate_data_quality_metrics(self, session_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate data quality metrics."""
        metrics = {
            "completeness": 0.0,
            "consistency": 0.0,
            "timeliness": 0.0,
        }

        # Completeness: percentage of available modalities
        available_modalities = sum([
            1 for modality in ["text", "audio", "behavioral"]
            if session_data.get(modality.replace("behavioral_tags", "behavioral"))
        ])
        metrics["completeness"] = available_modalities / 3.0

        # Consistency: based on synchronization quality if available
        if session_data.get("synchronization"):
            metrics["consistency"] = session_data["synchronization"].get("alignment_confidence", 0.0)

        # Timeliness: based on session creation and data addition times
        created_at_value = session_data.get("created_at")
        try:
            datetime.fromisoformat(created_at_value) if created_at_value else None
        except ValueError:
            created_at_value = None
        metrics["timeliness"] = 1.0  # Simplified - would calculate based on data addition times

        return metrics

    def _calculate_performance_metrics(self, fusion_result: Dict[str, Any]) -> Dict[str, float]:
        """Calculate performance metrics."""
        return {
            "fusion_speed": 0.0,  # Would measure actual processing time
            "feature_vector_size": len(fusion_result.get("feature_vector", [])),
            "confidence_score": fusion_result["confidence_metadata"].get("overall_confidence", 0.0),
        }

    def _generate_alerts(self, diagnostics: Dict[str, Any], fusion_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on diagnostics."""
        alerts = []

        # Low confidence alerts
        overall_confidence = fusion_result["confidence_metadata"].get("overall_confidence", 0.0)
        if overall_confidence < self.alert_thresholds["overall_confidence"]:
            alerts.append({
                "type": "low_confidence",
                "severity": "high" if overall_confidence < 0.4 else "medium",
                "message": f"Low overall confidence: {overall_confidence:.2f}",
                "threshold": self.alert_thresholds["overall_confidence"],
            })

        # Missing modalities alerts
        missing_modalities = diagnostics["modality_availability"]
        missing_count = sum(1 for available in missing_modalities.values() if not available)
        if missing_count >= self.alert_thresholds["missing_modalities_threshold"]:
            alerts.append({
                "type": "missing_modalities",
                "severity": "high" if missing_count >= 2 else "medium",
                "message": f"Missing {missing_count} modalities",
                "missing_modalities": [mod for mod, available in missing_modalities.items() if not available],
            })

        # Poor alignment alerts
        alignment_confidence = diagnostics.get("data_quality_metrics", {}).get("consistency", 0.0)
        if alignment_confidence < self.alert_thresholds["alignment_confidence"]:
            alerts.append({
                "type": "poor_alignment",
                "severity": "medium",
                "message": f"Poor temporal alignment: {alignment_confidence:.2f}",
                "threshold": self.alert_thresholds["alignment_confidence"],
            })

        return alerts

    def _generate_recommendations(self, diagnostics: Dict[str, Any], fusion_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on diagnostics."""
        recommendations = []

        # Confidence recommendations
        overall_confidence = fusion_result["confidence_metadata"].get("overall_confidence", 0.0)
        if overall_confidence < 0.6:
            recommendations.append("Consider collecting additional modalities to improve confidence")
        if overall_confidence < 0.4:
            recommendations.append("Review data quality and alignment procedures")

        # Modality availability recommendations
        missing_modalities = diagnostics["modality_availability"]
        if not missing_modalities["text"]:
            recommendations.append("Add text responses for better cognitive assessment")
        if not missing_modalities["audio"]:
            recommendations.append("Include audio recordings for behavioral insights")
        if not missing_modalities["behavioral"]:
            recommendations.append("Collect behavioral tags for comprehensive evaluation")

        # Data quality recommendations
        quality_metrics = diagnostics.get("data_quality_metrics", {})
        if quality_metrics.get("completeness", 0) < 0.7:
            recommendations.append("Improve data completeness by collecting missing modalities")
        if quality_metrics.get("consistency", 0) < 0.7:
            recommendations.append("Review synchronization procedures to improve temporal alignment")

        return recommendations

    def _get_recent_sessions(self, hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """Get recent sessions within specified hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent = {}
        for session_id, diagnostics in self.session_diagnostics.items():
            recorded_at = diagnostics.get("recorded_at")
            try:
                recorded_time = datetime.fromisoformat(recorded_at) if recorded_at else None
            except ValueError:
                recorded_time = None
            if recorded_time and recorded_time >= cutoff_time:
                recent[session_id] = diagnostics
        return recent

    def _calculate_average_confidence(self, sessions: Dict[str, Dict[str, Any]]) -> float:
        """Calculate average confidence from sessions."""
        if not sessions:
            return 0.0
        confidences = [
            diagnostics["fusion_confidence"].get("overall_confidence", 0.0)
            for diagnostics in sessions.values()
        ]
        return sum(confidences) / len(confidences)

    def _calculate_alert_rate(self, sessions: Dict[str, Dict[str, Any]]) -> float:
        """Calculate alert rate from sessions."""
        if not sessions:
            return 0.0
        total_alerts = sum(len(diagnostics.get("alerts", [])) for diagnostics in sessions.values())
        return total_alerts / len(sessions)

    def _calculate_modality_availability_stats(self, sessions: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Calculate modality availability statistics."""
        stats = {"text": 0.0, "audio": 0.0, "behavioral": 0.0}
        
        for diagnostics in sessions.values():
            availability = diagnostics.get("modality_availability", {})
            for modality, available in availability.items():
                if available:
                    stats[modality] += 1

        # Convert to percentages
        total = len(sessions)
        if total > 0:
            for modality in stats:
                stats[modality] = stats[modality] / total

        return stats
