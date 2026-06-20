"""Alignment diagnostics service for QA and retrospective analysis."""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field

from ..models import (
    JobMatchResult,
    KASHDomainEnum,
    CompetencyLevel,
    ConfidenceLevel
)
from .matching_service import LearnerKASHProfile


class DiagnosticStatusEnum(str, Enum):
    """Status of diagnostic analysis."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    ARCHIVED = "archived"


class DiagnosticTypeEnum(str, Enum):
    """Types of diagnostic analyses."""
    MATCH_ACCURACY = "match_accuracy"
    CONFIDENCE_VALIDATION = "confidence_validation"
    OVERRIDE_IMPACT = "override_impact"
    SYSTEM_PERFORMANCE = "system_performance"
    DATA_QUALITY = "data_quality"
    PREDICTIVE_ACCURACY = "predictive_accuracy"


class SeverityLevelEnum(str, Enum):
    """Severity levels for diagnostic findings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DiagnosticMetric:
    """Individual diagnostic metric."""
    name: str
    value: float
    unit: str
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    is_within_threshold: bool = True
    description: str = ""
    
    def __post_init__(self):
        if self.threshold_min is not None:
            self.is_within_threshold = self.value >= self.threshold_min
        if self.threshold_max is not None:
            self.is_within_threshold = self.is_within_threshold and self.value <= self.threshold_max


class DiagnosticFinding(BaseModel):
    """Individual diagnostic finding."""
    finding_id: str = Field(..., description="Unique finding identifier")
    diagnostic_type: DiagnosticTypeEnum = Field(..., description="Type of diagnostic")
    severity: SeverityLevelEnum = Field(..., description="Severity level")
    title: str = Field(..., description="Finding title")
    description: str = Field(..., description="Detailed description")
    
    # Context information
    learner_id: Optional[str] = Field(None, description="Related learner ID")
    job_id: Optional[str] = Field(None, description="Related job ID")
    sme_id: Optional[str] = Field(None, description="Related SME ID if applicable")
    
    # Metrics and evidence
    metrics: List[Dict[str, Any]] = Field(default_factory=list, description="Supporting metrics")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Recommended actions")
    impact_assessment: str = Field(..., description="Assessment of potential impact")
    
    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = Field(None, description="When finding was resolved")
    is_resolved: bool = Field(False, description="Whether finding has been resolved")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "finding_id": "finding_123",
                "diagnostic_type": "match_accuracy",
                "severity": "medium",
                "title": "Consistently low match scores for senior roles",
                "description": "Analysis shows learners consistently score below 0.4 for senior-level positions",
                "metrics": [{"name": "average_score", "value": 0.35, "unit": "score"}],
                "recommendations": ["Review senior role requirements", "Adjust competency weightings"],
                "impact_assessment": "May affect learner motivation and system credibility"
            }
        }
    }


class AlignmentDiagnostic(BaseModel):
    """Complete alignment diagnostic analysis."""
    diagnostic_id: str = Field(..., description="Unique diagnostic identifier")
    diagnostic_type: DiagnosticTypeEnum = Field(..., description="Type of diagnostic")
    status: DiagnosticStatusEnum = Field(..., description="Diagnostic status")
    
    # Analysis scope
    analysis_period: Dict[str, datetime] = Field(..., description="Analysis period (start, end)")
    scope_filters: Dict[str, Any] = Field(default_factory=dict, description="Filters applied to analysis")
    
    # Results
    summary: str = Field(..., description="Diagnostic summary")
    findings: List[DiagnosticFinding] = Field(default_factory=list, description="Diagnostic findings")
    metrics: List[Dict[str, Any]] = Field(default_factory=list, description="Overall metrics")
    
    # Quality indicators
    data_quality_score: float = Field(..., ge=0, le=1, description="Overall data quality score")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in diagnostic results")
    
    # Recommendations
    priority_actions: List[str] = Field(default_factory=list, description="High-priority recommended actions")
    improvement_suggestions: List[str] = Field(default_factory=list, description="General improvement suggestions")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None, description="When diagnostic was completed")
    created_by: str = Field(..., description="Who created the diagnostic")
    
    @property
    def critical_findings(self) -> List[DiagnosticFinding]:
        """Get critical findings."""
        return [f for f in self.findings if f.severity == SeverityLevelEnum.CRITICAL]
    
    @property
    def high_findings(self) -> List[DiagnosticFinding]:
        """Get high severity findings."""
        return [f for f in self.findings if f.severity == SeverityLevelEnum.HIGH]
    
    @property
    def unresolved_findings(self) -> List[DiagnosticFinding]:
        """Get unresolved findings."""
        return [f for f in self.findings if not f.is_resolved]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "diagnostic_id": "diag_456",
                "diagnostic_type": "match_accuracy",
                "status": "completed",
                "summary": "Overall system accuracy is within acceptable ranges, but some issues identified with senior role matching",
                "data_quality_score": 0.85,
                "confidence_score": 0.92,
                "priority_actions": ["Review senior role competency definitions"]
            }
        }
    }


class AlignmentDiagnosticsService:
    """Service for managing alignment diagnostics and QA analysis."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).parent.parent / "data" / "diagnostics"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Diagnostic storage files
        self.diagnostics_file = self.storage_path / "alignment_diagnostics.json"
        self.findings_file = self.storage_path / "diagnostic_findings.json"
        
        # Load existing diagnostics
        self.diagnostics = self._load_diagnostics()
        self.findings = self._load_findings()
    
    def _load_diagnostics(self) -> Dict[str, AlignmentDiagnostic]:
        """Load existing diagnostics from storage."""
        if not self.diagnostics_file.exists():
            return {}
        
        try:
            with open(self.diagnostics_file, 'r') as f:
                data = json.load(f)
            
            diagnostics = {}
            for diag_id, diag_data in data.items():
                # Convert datetime strings back to datetime objects
                if diag_data.get("created_at"):
                    diag_data["created_at"] = datetime.fromisoformat(diag_data["created_at"])
                if diag_data.get("completed_at"):
                    diag_data["completed_at"] = datetime.fromisoformat(diag_data["completed_at"])
                
                # Convert analysis period dates
                if diag_data.get("analysis_period"):
                    period = diag_data["analysis_period"]
                    if period.get("start"):
                        period["start"] = datetime.fromisoformat(period["start"])
                    if period.get("end"):
                        period["end"] = datetime.fromisoformat(period["end"])
                
                diagnostics[diag_id] = AlignmentDiagnostic(**diag_data)
            
            return diagnostics
        except Exception as e:
            print(f"Error loading diagnostics: {e}")
            return {}
    
    def _load_findings(self) -> Dict[str, DiagnosticFinding]:
        """Load existing findings from storage."""
        if not self.findings_file.exists():
            return {}
        
        try:
            with open(self.findings_file, 'r') as f:
                data = json.load(f)
            
            findings = {}
            for finding_id, finding_data in data.items():
                # Convert datetime strings back to datetime objects
                if finding_data.get("created_at"):
                    finding_data["created_at"] = datetime.fromisoformat(finding_data["created_at"])
                if finding_data.get("resolved_at"):
                    finding_data["resolved_at"] = datetime.fromisoformat(finding_data["resolved_at"])
                
                findings[finding_id] = DiagnosticFinding(**finding_data)
            
            return findings
        except Exception as e:
            print(f"Error loading findings: {e}")
            return {}
    
    def _save_diagnostics(self):
        """Save diagnostics to storage."""
        data = {}
        for diag_id, diagnostic in self.diagnostics.items():
            data[diag_id] = diagnostic.model_dump()
        
        with open(self.diagnostics_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _save_findings(self):
        """Save findings to storage."""
        data = {}
        for finding_id, finding in self.findings.items():
            data[finding_id] = finding.model_dump()
        
        with open(self.findings_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def create_match_accuracy_diagnostic(self, start_date: datetime, end_date: datetime,
                                       scope_filters: Optional[Dict[str, Any]] = None,
                                       created_by: str = "system") -> AlignmentDiagnostic:
        """Create a match accuracy diagnostic."""
        
        diagnostic_id = str(uuid.uuid4())
        
        diagnostic = AlignmentDiagnostic(
            diagnostic_id=diagnostic_id,
            diagnostic_type=DiagnosticTypeEnum.MATCH_ACCURACY,
            status=DiagnosticStatusEnum.IN_PROGRESS,
            analysis_period={"start": start_date, "end": end_date},
            scope_filters=scope_filters or {},
            summary="Analyzing match accuracy across learner-job pairings",
            data_quality_score=0.0,  # Will be calculated
            confidence_score=0.0,    # Will be calculated
            created_by=created_by
        )
        
        # Store diagnostic
        self.diagnostics[diagnostic_id] = diagnostic
        self._save_diagnostics()
        
        return diagnostic
    
    def analyze_match_accuracy(self, diagnostic_id: str, 
                             match_results: List[JobMatchResult]) -> AlignmentDiagnostic:
        """Analyze match accuracy and update diagnostic."""
        
        diagnostic = self.diagnostics.get(diagnostic_id)
        if not diagnostic:
            raise ValueError(f"Diagnostic {diagnostic_id} not found")
        
        findings = []
        metrics = []
        
        # Calculate overall accuracy metrics
        if match_results:
            scores = [match.overall_match_score for match in match_results]
            avg_score = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)
            
            metrics.extend([
                {"name": "average_match_score", "value": avg_score, "unit": "score"},
                {"name": "min_match_score", "value": min_score, "unit": "score"},
                {"name": "max_match_score", "value": max_score, "unit": "score"},
                {"name": "total_matches", "value": len(match_results), "unit": "count"}
            ])
            
            # Check for low score patterns
            low_score_matches = [match for match in match_results if match.overall_match_score < 0.3]
            if len(low_score_matches) / len(match_results) > 0.3:
                finding = DiagnosticFinding(
                    finding_id=str(uuid.uuid4()),
                    diagnostic_type=DiagnosticTypeEnum.MATCH_ACCURACY,
                    severity=SeverityLevelEnum.HIGH,
                    title="High percentage of low match scores",
                    description=f"{len(low_score_matches)}/{len(match_results)} matches have scores below 0.3",
                    metrics=[
                        {"name": "low_score_percentage", "value": len(low_score_matches) / len(match_results), "unit": "percentage"}
                    ],
                    evidence=[f"Match scores range: {min_score:.2f} - {max_score:.2f}"],
                    recommendations=[
                        "Review job profile requirements",
                        "Adjust competency weightings",
                        "Improve learner data quality"
                    ],
                    impact_assessment="May indicate system calibration issues or data quality problems"
                )
                findings.append(finding)
            
            # Check confidence score consistency
            confidence_levels = [match.confidence_metrics.overall_confidence for match in match_results]
            low_confidence_matches = [match for match in match_results 
                                    if match.confidence_metrics.overall_confidence in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]]
            
            if len(low_confidence_matches) / len(match_results) > 0.2:
                finding = DiagnosticFinding(
                    finding_id=str(uuid.uuid4()),
                    diagnostic_type=DiagnosticTypeEnum.MATCH_ACCURACY,
                    severity=SeverityLevelEnum.MEDIUM,
                    title="Low confidence in match results",
                    description=f"{len(low_confidence_matches)}/{len(match_results)} matches have low confidence",
                    metrics=[
                        {"name": "low_confidence_percentage", "value": len(low_confidence_matches) / len(match_results), "unit": "percentage"}
                    ],
                    recommendations=[
                        "Improve data completeness",
                        "Validate competency assessments",
                        "Review confidence calculation logic"
                    ],
                    impact_assessment="Low confidence may reduce trust in matching results"
                )
                findings.append(finding)
        
        # Calculate data quality and confidence scores
        data_quality_score = self._calculate_data_quality_score(match_results)
        confidence_score = self._calculate_diagnostic_confidence(match_results, findings)
        
        # Update diagnostic
        diagnostic.findings = findings
        diagnostic.metrics = metrics
        diagnostic.data_quality_score = data_quality_score
        diagnostic.confidence_score = confidence_score
        diagnostic.status = DiagnosticStatusEnum.COMPLETED
        diagnostic.completed_at = datetime.utcnow()
        
        if avg_score >= 0.7:
            diagnostic.summary = f"Match accuracy analysis completed. Average score: {avg_score:.2f} - Good performance"
        elif avg_score >= 0.5:
            diagnostic.summary = f"Match accuracy analysis completed. Average score: {avg_score:.2f} - Moderate performance, some improvements needed"
        else:
            diagnostic.summary = f"Match accuracy analysis completed. Average score: {avg_score:.2f} - Poor performance, significant improvements needed"
        
        # Generate priority actions based on findings
        critical_findings = [f for f in findings if f.severity == SeverityLevelEnum.CRITICAL]
        high_findings = [f for f in findings if f.severity == SeverityLevelEnum.HIGH]
        
        if critical_findings:
            diagnostic.priority_actions = [f"URGENT: {f.title}" for f in critical_findings]
        if high_findings:
            diagnostic.priority_actions.extend([f"HIGH: {f.title}" for f in high_findings])
        
        # Store findings
        for finding in findings:
            self.findings[finding.finding_id] = finding
        
        # Save updated diagnostic and findings
        self._save_diagnostics()
        self._save_findings()
        
        return diagnostic
    
    def _calculate_data_quality_score(self, match_results: List[JobMatchResult]) -> float:
        """Calculate overall data quality score."""
        if not match_results:
            return 0.0
        
        quality_scores = []
        
        for match in match_results:
            # Factors affecting data quality
            completeness_score = match.confidence_metrics.data_completeness
            profile_coverage = match.confidence_metrics.profile_coverage
            uncertainty_penalty = len(match.confidence_metrics.uncertainty_factors) * 0.1
            
            match_quality = (completeness_score + profile_coverage) / 2 - uncertainty_penalty
            quality_scores.append(max(0.0, match_quality))
        
        return sum(quality_scores) / len(quality_scores)
    
    def _calculate_diagnostic_confidence(self, match_results: List[JobMatchResult], 
                                       findings: List[DiagnosticFinding]) -> float:
        """Calculate confidence in diagnostic results."""
        if not match_results:
            return 0.0
        
        base_confidence = min(1.0, len(match_results) / 100)  # More data = higher confidence
        
        # Reduce confidence based on severity of findings
        severity_penalties = {
            SeverityLevelEnum.CRITICAL: 0.3,
            SeverityLevelEnum.HIGH: 0.2,
            SeverityLevelEnum.MEDIUM: 0.1,
            SeverityLevelEnum.LOW: 0.05
        }
        
        total_penalty = 0.0
        for finding in findings:
            total_penalty += severity_penalties.get(finding.severity, 0.0)
        
        final_confidence = max(0.0, base_confidence - total_penalty)
        return final_confidence
    
    def create_override_impact_diagnostic(self, start_date: datetime, end_date: datetime,
                                        created_by: str = "system") -> AlignmentDiagnostic:
        """Create an override impact diagnostic."""
        
        diagnostic_id = str(uuid.uuid4())
        
        diagnostic = AlignmentDiagnostic(
            diagnostic_id=diagnostic_id,
            diagnostic_type=DiagnosticTypeEnum.OVERRIDE_IMPACT,
            status=DiagnosticStatusEnum.PENDING,
            analysis_period={"start": start_date, "end": end_date},
            summary="Analyzing the impact of SME overrides on match results",
            data_quality_score=0.0,
            confidence_score=0.0,
            created_by=created_by
        )
        
        self.diagnostics[diagnostic_id] = diagnostic
        self._save_diagnostics()
        
        return diagnostic
    
    def get_diagnostic_summary(self, diagnostic_type: Optional[DiagnosticTypeEnum] = None) -> Dict[str, Any]:
        """Get summary of diagnostics."""
        diagnostics = list(self.diagnostics.values())
        
        if diagnostic_type:
            diagnostics = [d for d in diagnostics if d.diagnostic_type == diagnostic_type]
        
        if not diagnostics:
            return {"total_diagnostics": 0, "message": "No diagnostics found"}
        
        # Calculate summary statistics
        total_diagnostics = len(diagnostics)
        completed_diagnostics = len([d for d in diagnostics if d.status == DiagnosticStatusEnum.COMPLETED])
        
        total_findings = sum(len(d.findings) for d in diagnostics)
        critical_findings = sum(len(d.critical_findings) for d in diagnostics)
        high_findings = sum(len(d.high_findings) for d in diagnostics)
        unresolved_findings = sum(len(d.unresolved_findings) for d in diagnostics)
        
        avg_data_quality = sum(d.data_quality_score for d in diagnostics) / len(diagnostics)
        avg_confidence = sum(d.confidence_score for d in diagnostics) / len(diagnostics)
        
        # Type distribution
        type_distribution = {}
        for diagnostic in diagnostics:
            diag_type = diagnostic.diagnostic_type.value
            type_distribution[diag_type] = type_distribution.get(diag_type, 0) + 1
        
        return {
            "total_diagnostics": total_diagnostics,
            "completed_diagnostics": completed_diagnostics,
            "completion_rate": completed_diagnostics / total_diagnostics if total_diagnostics > 0 else 0,
            "total_findings": total_findings,
            "critical_findings": critical_findings,
            "high_findings": high_findings,
            "unresolved_findings": unresolved_findings,
            "avg_data_quality_score": avg_data_quality,
            "avg_confidence_score": avg_confidence,
            "type_distribution": type_distribution,
            "recent_diagnostics": [
                {
                    "id": d.diagnostic_id,
                    "type": d.diagnostic_type.value,
                    "status": d.status.value,
                    "created_at": d.created_at.isoformat(),
                    "summary": d.summary[:100] + "..." if len(d.summary) > 100 else d.summary
                }
                for d in sorted(diagnostics, key=lambda x: x.created_at, reverse=True)[:5]
            ]
        }
    
    def get_findings_by_severity(self, severity: SeverityLevelEnum) -> List[DiagnosticFinding]:
        """Get findings filtered by severity level."""
        return [f for f in self.findings.values() if f.severity == severity and not f.is_resolved]
    
    def resolve_finding(self, finding_id: str, resolution_notes: str, resolved_by: str) -> bool:
        """Mark a finding as resolved."""
        finding = self.findings.get(finding_id)
        if not finding:
            return False
        
        finding.is_resolved = True
        finding.resolved_at = datetime.utcnow()
        finding.description += f"\n\nRESOLVED ({resolved_by}): {resolution_notes}"
        
        self._save_findings()
        return True
    
    def get_quality_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get quality trends over time."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_diagnostics = [
            d for d in self.diagnostics.values() 
            if d.created_at >= cutoff_date and d.status == DiagnosticStatusEnum.COMPLETED
        ]
        
        if not recent_diagnostics:
            return {"message": "No recent diagnostics available"}
        
        # Sort by date
        recent_diagnostics.sort(key=lambda x: x.created_at)
        
        # Calculate trends
        data_quality_trend = [(d.created_at.isoformat(), d.data_quality_score) for d in recent_diagnostics]
        confidence_trend = [(d.created_at.isoformat(), d.confidence_score) for d in recent_diagnostics]
        
        return {
            "period_days": days,
            "total_diagnostics": len(recent_diagnostics),
            "data_quality_trend": data_quality_trend,
            "confidence_trend": confidence_trend,
            "avg_data_quality": sum(d.data_quality_score for d in recent_diagnostics) / len(recent_diagnostics),
            "avg_confidence": sum(d.confidence_score for d in recent_diagnostics) / len(recent_diagnostics)
        }
