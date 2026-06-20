"""Telemetry and diagnostics recording for transcription pipeline."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

from src.core.logging import get_logger
from .provider_base import TranscriptPackage

logger = get_logger(__name__)


@dataclass
class TranscriptionMetrics:
    """Metrics recorded for transcription operations."""
    job_id: str
    session_id: str
    provider_name: str
    provider_mode: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[int]
    status: str  # success, failure, timeout
    error_message: Optional[str]
    confidence_score: Optional[float]
    segment_count: int
    word_count: int
    audio_duration_seconds: float
    fallback_used: bool
    network_available: bool
    bandwidth_kbps: Optional[int]


class TelemetryRecorder:
    """Records telemetry and diagnostics for transcription operations."""

    def __init__(self):
        """Initialize telemetry recorder."""
        self.metrics: List[TranscriptionMetrics] = []
        self.provider_stats: Dict[str, Dict[str, Any]] = {}
        self.session_stats: Dict[str, Dict[str, Any]] = {}
        self.alerts: List[Dict[str, Any]] = []

    async def record_transcription_start(
        self,
        job_id: str,
        session_id: str,
        provider_name: str,
        provider_mode: str,
        audio_duration_seconds: float,
        network_available: bool,
        bandwidth_kbps: Optional[int] = None,
    ) -> None:
        """
        Record the start of a transcription job.

        Args:
            job_id: Unique job identifier
            session_id: Abilities session ID
            provider_name: Selected provider name
            provider_mode: Provider mode (cloud/offline)
            audio_duration_seconds: Duration of audio in seconds
            network_available: Whether network was available
            bandwidth_kbps: Available bandwidth
        """
        metric = TranscriptionMetrics(
            job_id=job_id,
            session_id=session_id,
            provider_name=provider_name,
            provider_mode=provider_mode,
            start_time=datetime.utcnow(),
            end_time=None,
            duration_ms=None,
            status="in_progress",
            error_message=None,
            confidence_score=None,
            segment_count=0,
            word_count=0,
            audio_duration_seconds=audio_duration_seconds,
            fallback_used=provider_mode == "offline" and not network_available,
            network_available=network_available,
            bandwidth_kbps=bandwidth_kbps,
        )

        self.metrics.append(metric)
        logger.info(f"Started recording telemetry for job {job_id}")

    async def record_transcription_success(
        self,
        job_id: str,
        transcript: TranscriptPackage,
        provider_name: str,
    ) -> None:
        """
        Record successful transcription completion.

        Args:
            job_id: Job identifier
            transcript: Completed transcript package
            provider_name: Provider that completed the job
        """
        # Find the metric
        metric = self._find_metric(job_id)
        if not metric:
            logger.warning(f"No metric found for job {job_id}")
            return

        # Update metric
        metric.end_time = datetime.utcnow()
        metric.duration_ms = int((metric.end_time - metric.start_time).total_seconds() * 1000)
        metric.status = "success"
        metric.confidence_score = transcript.aggregate_confidence
        metric.segment_count = len(transcript.segments)
        metric.word_count = sum(len(seg.words) for seg in transcript.segments)

        # Update provider stats
        self._update_provider_stats(provider_name, metric)

        # Update session stats
        self._update_session_stats(metric.session_id, metric)

        # Check for alerts
        await self._check_success_alerts(metric)

        logger.info(f"Recorded successful transcription for job {job_id}")

    async def record_transcription_failure(
        self,
        job_id: str,
        error_message: str,
    ) -> None:
        """
        Record transcription failure.

        Args:
            job_id: Job identifier
            error_message: Error description
        """
        metric = self._find_metric(job_id)
        if not metric:
            logger.warning(f"No metric found for job {job_id}")
            return

        metric.end_time = datetime.utcnow()
        metric.duration_ms = int((metric.end_time - metric.start_time).total_seconds() * 1000)
        metric.status = "failure"
        metric.error_message = error_message

        # Update provider stats
        self._update_provider_stats(metric.provider_name, metric)

        # Check for failure alerts
        await self._check_failure_alerts(metric)

        logger.error(f"Recorded transcription failure for job {job_id}: {error_message}")

    def get_provider_performance(
        self,
        provider_name: Optional[str] = None,
        hours_back: int = 24,
    ) -> Dict[str, Any]:
        """
        Get provider performance statistics.

        Args:
            provider_name: Specific provider or None for all
            hours_back: Time window in hours

        Returns:
            Performance statistics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        recent_metrics = [
            m for m in self.metrics
            if m.start_time >= cutoff_time
            and (provider_name is None or m.provider_name == provider_name)
        ]

        if not recent_metrics:
            return {"error": "No data available"}

        # Calculate statistics
        total_jobs = len(recent_metrics)
        successful_jobs = len([m for m in recent_metrics if m.status == "success"])
        failed_jobs = total_jobs - successful_jobs

        # Duration and confidence stats (successful jobs only)
        successful_metrics = [m for m in recent_metrics if m.status == "success"]
        durations = [m.duration_ms for m in successful_metrics if m.duration_ms]
        confidences = [m.confidence_score for m in successful_metrics if m.confidence_score]

        return {
            "provider_name": provider_name or "all",
            "time_window_hours": hours_back,
            "total_jobs": total_jobs,
            "successful_jobs": successful_jobs,
            "failed_jobs": failed_jobs,
            "success_rate": successful_jobs / total_jobs if total_jobs > 0 else 0,
            "avg_duration_ms": sum(durations) / len(durations) if durations else None,
            "min_duration_ms": min(durations) if durations else None,
            "max_duration_ms": max(durations) if durations else None,
            "avg_confidence": sum(confidences) / len(confidences) if confidences else None,
            "min_confidence": min(confidences) if confidences else None,
            "max_confidence": max(confidences) if confidences else None,
            "fallback_rate": len([m for m in recent_metrics if m.fallback_used]) / total_jobs if total_jobs > 0 else 0,
        }

    def get_session_telemetry(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get telemetry data for a specific session.

        Args:
            session_id: Session identifier

        Returns:
            Session telemetry or None if not found
        """
        session_metrics = [m for m in self.metrics if m.session_id == session_id]
        if not session_metrics:
            return None

        return {
            "session_id": session_id,
            "total_jobs": len(session_metrics),
            "successful_jobs": len([m for m in session_metrics if m.status == "success"]),
            "failed_jobs": len([m for m in session_metrics if m.status == "failure"]),
            "providers_used": list(set(m.provider_name for m in session_metrics)),
            "total_confidence": sum(m.confidence_score or 0 for m in session_metrics),
            "avg_confidence": sum(m.confidence_score or 0 for m in session_metrics) / len(session_metrics),
            "total_duration_ms": sum(m.duration_ms or 0 for m in session_metrics),
            "fallback_used": any(m.fallback_used for m in session_metrics),
        }

    def get_system_health(self, hours_back: int = 1) -> Dict[str, Any]:
        """
        Get overall system health status.

        Args:
            hours_back: Time window for health calculation

        Returns:
            System health summary
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        recent_metrics = [m for m in self.metrics if m.start_time >= cutoff_time]

        if not recent_metrics:
            return {
                "status": "unknown",
                "message": "No recent activity",
                "time_window_hours": hours_back,
            }

        total_jobs = len(recent_metrics)
        successful_jobs = len([m for m in recent_metrics if m.status == "success"])
        success_rate = successful_jobs / total_jobs if total_jobs > 0 else 0

        # Determine health status
        if success_rate >= 0.95:
            status = "healthy"
        elif success_rate >= 0.8:
            status = "degraded"
        else:
            status = "unhealthy"

        # Recent alerts
        recent_alerts = [
            a for a in self.alerts
            if datetime.fromisoformat(a["created_at"]) >= cutoff_time
        ]

        return {
            "status": status,
            "success_rate": success_rate,
            "total_jobs": total_jobs,
            "successful_jobs": successful_jobs,
            "failed_jobs": total_jobs - successful_jobs,
            "recent_alerts": len(recent_alerts),
            "critical_alerts": len([a for a in recent_alerts if a["severity"] == "critical"]),
            "time_window_hours": hours_back,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_alerts(
        self,
        severity: Optional[str] = None,
        hours_back: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        Get alerts with optional filtering.

        Args:
            severity: Filter by severity level
            hours_back: Time window in hours

        Returns:
            List of alerts
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        alerts = [
            a for a in self.alerts
            if datetime.fromisoformat(a["created_at"]) >= cutoff_time
        ]

        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]

        return sorted(alerts, key=lambda x: x["created_at"], reverse=True)

    def _find_metric(self, job_id: str) -> Optional[TranscriptionMetrics]:
        """Find metric by job ID."""
        for metric in self.metrics:
            if metric.job_id == job_id:
                return metric
        return None

    def _update_provider_stats(self, provider_name: str, metric: TranscriptionMetrics) -> None:
        """Update provider statistics."""
        if provider_name not in self.provider_stats:
            self.provider_stats[provider_name] = {
                "total_jobs": 0,
                "successful_jobs": 0,
                "failed_jobs": 0,
                "total_duration_ms": 0,
                "total_confidence": 0,
                "fallback_count": 0,
            }

        stats = self.provider_stats[provider_name]
        stats["total_jobs"] += 1
        if metric.status == "success":
            stats["successful_jobs"] += 1
            stats["total_duration_ms"] += metric.duration_ms or 0
            stats["total_confidence"] += metric.confidence_score or 0
        else:
            stats["failed_jobs"] += 1

        if metric.fallback_used:
            stats["fallback_count"] += 1

    def _update_session_stats(self, session_id: str, metric: TranscriptionMetrics) -> None:
        """Update session statistics."""
        if session_id not in self.session_stats:
            self.session_stats[session_id] = {
                "total_jobs": 0,
                "successful_jobs": 0,
                "failed_jobs": 0,
                "providers_used": set(),
                "total_confidence": 0,
            }

        stats = self.session_stats[session_id]
        stats["total_jobs"] += 1
        if metric.status == "success":
            stats["successful_jobs"] += 1
            stats["total_confidence"] += metric.confidence_score or 0
        else:
            stats["failed_jobs"] += 1

        stats["providers_used"].add(metric.provider_name)

    async def _check_success_alerts(self, metric: TranscriptionMetrics) -> None:
        """Check for alerts on successful transcriptions."""
        # Low confidence alert
        if metric.confidence_score and metric.confidence_score < 0.7:
            await self._create_alert(
                "low_confidence",
                "medium",
                f"Low confidence score: {metric.confidence_score:.2f} for job {metric.job_id}",
                metric.session_id,
                metric.provider_name,
            )

        # High duration alert
        if metric.duration_ms and metric.duration_ms > 10000:  # 10 seconds
            await self._create_alert(
                "high_duration",
                "low",
                f"High transcription duration: {metric.duration_ms}ms for job {metric.job_id}",
                metric.session_id,
                metric.provider_name,
            )

    async def _check_failure_alerts(self, metric: TranscriptionMetrics) -> None:
        """Check for alerts on failed transcriptions."""
        # Failure alert
        await self._create_alert(
            "transcription_failure",
            "high",
            f"Transcription failed for job {metric.job_id}: {metric.error_message}",
            metric.session_id,
            metric.provider_name,
        )

    async def _create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        session_id: str,
        provider_name: str,
    ) -> None:
        """Create an alert."""
        alert = {
            "alert_id": f"alert_{len(self.alerts) + 1}",
            "type": alert_type,
            "severity": severity,
            "message": message,
            "session_id": session_id,
            "provider_name": provider_name,
            "created_at": datetime.utcnow().isoformat(),
        }

        self.alerts.append(alert)
        logger.warning(f"Alert created: {alert_type} - {message}")
