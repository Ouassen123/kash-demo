"""Reviewer override service for manual analysis adjustments."""

from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid
import json
from pathlib import Path

from src.schemas.reviewer_overrides import (
    ReviewerOverrideRequest,
    ReviewerOverrideResponse,
    OverrideHistoryItem,
    OverrideHistoryResponse,
    ReviewerDashboardRequest,
    ReviewerDashboardResponse,
    ReviewerStats,
    OverrideTemplate,
    OverrideTemplateRequest,
    OverrideValidationRequest,
    OverrideValidationResponse,
    OverrideReasonEnum,
    OverrideStatusEnum,
    FindingOverride,
    ScoreOverride,
    GradeOverride,
)
from src.modules.skills.code_analysis.models import AnalysisResult, AnalyzerFinding, SeverityLevel


class ReviewerOverrideService:
    """Service for managing reviewer overrides of analysis results."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("data/reviewer_overrides")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize template storage
        self.templates_file = self.storage_path / "templates.json"
        self._load_templates()
    
    def _load_templates(self):
        """Load override templates from storage."""
        if self.templates_file.exists():
            with open(self.templates_file, 'r') as f:
                data = json.load(f)
                self.templates = {
                    tid: OverrideTemplate(**template) 
                    for tid, template in data.items()
                }
        else:
            self.templates = {}
            self._save_templates()
    
    def _save_templates(self):
        """Save override templates to storage."""
        data = {
            tid: template.model_dump() 
            for tid, template in self.templates.items()
        }
        with open(self.templates_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def create_override(self, request: ReviewerOverrideRequest, original_analysis: AnalysisResult) -> ReviewerOverrideResponse:
        """Create a new reviewer override."""
        override_id = str(uuid.uuid4())
        
        # Apply overrides to create modified analysis
        modified_analysis = self._apply_overrides(request, original_analysis)
        
        # Calculate changes summary
        changes_summary = self._calculate_changes_summary(original_analysis, modified_analysis, request)
        
        # Create override record
        from dataclasses import asdict
        override_record = ReviewerOverrideResponse(
            override_id=override_id,
            submission_id=request.submission_id,
            reviewer_id=request.reviewer_id,
            status=OverrideStatusEnum.PENDING,
            original_analysis=asdict(original_analysis),
            modified_analysis=asdict(modified_analysis),
            changes_summary=changes_summary,
            created_at=datetime.utcnow(),
        )
        
        # Save override record
        self._save_override_record(override_record)
        
        return override_record
    
    def _apply_overrides(self, request: ReviewerOverrideRequest, original_analysis: AnalysisResult) -> AnalysisResult:
        """Apply overrides to create modified analysis."""
        # Create a copy of the original analysis
        from dataclasses import replace
        modified = replace(original_analysis)
        
        # Apply finding overrides
        if request.finding_overrides:
            modified.analyzer_reports = self._apply_finding_overrides(
                modified.analyzer_reports, 
                request.finding_overrides
            )
        
        # Apply score override
        if request.score_override:
            modified.overall_score = request.score_override.new_score
        
        # Apply grade override
        if request.grade_override:
            # Note: Grade would need to be added to AnalysisResult model
            pass
        
        # Update summary
        modified.summary = self._update_analysis_summary(modified, request)
        
        return modified
    
    def _apply_finding_overrides(self, reports, finding_overrides: List[FindingOverride]):
        """Apply finding-level overrides."""
        override_map = {fo.finding_id: fo for fo in finding_overrides}
        
        for report in reports:
            modified_findings = []
            for finding in report.findings:
                finding_id = f"{finding.metadata.get('rule_id', 'UNKNOWN')}_{finding.line}"
                
                if finding_id in override_map:
                    override = override_map[finding_id]
                    # Create modified finding
                    from dataclasses import replace
                    modified_finding = replace(finding)
                    
                    if override.new_severity:
                        modified_finding.severity = SeverityLevel(override.new_severity.value)
                    
                    # Note: score_impact doesn't exist in the current model, skip for now
                    
                    # Add override metadata
                    modified_finding.metadata.update({
                        "manual_override": True,
                        "override_reason": override.reason.value,
                        "override_comment": override.comment,
                        "original_severity": override.original_severity.value,
                        "original_score_impact": override.original_score_impact,
                    })
                    
                    modified_findings.append(modified_finding)
                else:
                    modified_findings.append(finding)
            
            report.findings = modified_findings
        
        return reports
    
    def _calculate_changes_summary(self, original, modified, request: ReviewerOverrideRequest) -> Dict[str, Any]:
        """Calculate summary of changes made by overrides."""
        original_score = original.overall_score
        modified_score = modified.overall_score
        score_change = modified_score - original_score
        
        # Count finding changes
        original_findings = sum(len(report.findings) for report in original.analyzer_reports)
        modified_findings = sum(len(report.findings) for report in modified.analyzer_reports)
        
        # Count severity changes
        severity_changes = 0
        for orig_report, mod_report in zip(original.analyzer_reports, modified.analyzer_reports):
            for orig_finding, mod_finding in zip(orig_report.findings, mod_report.findings):
                if orig_finding.severity != mod_finding.severity:
                    severity_changes += 1
        
        return {
            "score_change": score_change,
            "original_score": original_score,
            "modified_score": modified_score,
            "finding_overrides": len(request.finding_overrides) if request.finding_overrides else 0,
            "score_override": request.score_override is not None,
            "grade_override": request.grade_override is not None,
            "severity_changes": severity_changes,
            "total_findings_original": original_findings,
            "total_findings_modified": modified_findings,
        }
    
    def _update_analysis_summary(self, analysis: AnalysisResult, request: ReviewerOverrideRequest) -> str:
        """Update analysis summary to reflect overrides."""
        base_summary = analysis.summary
        
        override_parts = []
        if request.finding_overrides:
            override_parts.append(f"{len(request.finding_overrides)} findings manually overridden")
        if request.score_override:
            override_parts.append(f"score manually adjusted from {request.score_override.original_score} to {request.score_override.new_score}")
        if request.grade_override:
            override_parts.append(f"grade manually changed from {request.grade_override.original_grade} to {request.grade_override.new_grade}")
        
        if override_parts:
            override_summary = ". Manual overrides: " + ", ".join(override_parts) + f". Reviewer notes: {request.reviewer_notes}"
            return base_summary + override_summary
        
        return base_summary
    
    def _save_override_record(self, record: ReviewerOverrideResponse):
        """Save override record to storage."""
        file_path = self.storage_path / f"overrides_{record.submission_id}.json"
        
        # Load existing records for this submission
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
        else:
            data = []
        
        # Add new record
        data.append(record.model_dump())
        
        # Save
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def get_override_history(self, submission_id: str) -> OverrideHistoryResponse:
        """Get override history for a submission."""
        file_path = self.storage_path / f"overrides_{submission_id}.json"
        
        if not file_path.exists():
            return OverrideHistoryResponse(
                submission_id=submission_id,
                total_overrides=0,
                overrides=[],
                current_analysis={}
            )
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert to history items
        overrides = []
        for record in reversed(data):  # Most recent first
            history_item = OverrideHistoryItem(
                override_id=record["override_id"],
                reviewer_id=record["reviewer_id"],
                changes_made=record["changes_summary"],
                reason=OverrideReasonEnum(record.get("reason", "instructor_judgment")),
                comment=record.get("reviewer_notes", ""),
                created_at=datetime.fromisoformat(record["created_at"]),
                status=OverrideStatusEnum(record["status"])
            )
            overrides.append(history_item)
        
        # Get current analysis (most recent override's modified analysis)
        current_analysis = data[-1]["modified_analysis"] if data else {}
        
        return OverrideHistoryResponse(
            submission_id=submission_id,
            total_overrides=len(overrides),
            overrides=overrides,
            current_analysis=current_analysis
        )
    
    def get_reviewer_dashboard(self, request: ReviewerDashboardRequest) -> ReviewerDashboardResponse:
        """Get reviewer dashboard data."""
        # This would typically query a database
        # For now, return mock data
        
        pending_submissions = [
            {
                "submission_id": "sub-123",
                "learner_id": "learner-456",
                "submitted_at": datetime.utcnow().isoformat(),
                "original_score": 75.5,
                "needs_review": True,
                "auto_analysis_issues": ["Complexity issues", "Style violations"]
            },
            {
                "submission_id": "sub-124",
                "learner_id": "learner-457", 
                "submitted_at": datetime.utcnow().isoformat(),
                "original_score": 82.0,
                "needs_review": True,
                "auto_analysis_issues": ["Naming conventions"]
            }
        ]
        
        recent_overrides = [
            OverrideHistoryItem(
                override_id="override-1",
                reviewer_id="reviewer-789",
                changes_made={"score_change": 5.0},
                reason=OverrideReasonEnum.EDUCATIONAL_CONTEXT,
                comment="Good creative solution",
                created_at=datetime.utcnow(),
                status=OverrideStatusEnum.APPROVED
            )
        ]
        
        reviewer_stats = ReviewerStats(
            reviewer_id=request.reviewer_id or "reviewer-789",
            reviewer_name="Dr. Smith",
            total_reviews=45,
            pending_reviews=2,
            approved_overrides=38,
            rejected_overrides=5,
            average_score_adjustment=2.3,
            most_common_reasons=[
                {"reason": "educational_context", "count": 15},
                {"reason": "false_positive", "count": 8}
            ],
            recent_activity=recent_overrides[:5]
        )
        
        return ReviewerDashboardResponse(
            reviewer_stats=reviewer_stats,
            pending_submissions=pending_submissions,
            recent_overrides=recent_overrides,
            summary_stats={
                "total_submissions_today": 12,
                "average_processing_time": "15 minutes",
                "override_rate": 0.15
            }
        )
    
    def create_template(self, request: OverrideTemplateRequest, creator_id: str) -> OverrideTemplate:
        """Create a new override template."""
        template_id = str(uuid.uuid4())
        
        template = OverrideTemplate(
            template_id=template_id,
            name=request.name,
            description=request.description,
            reason=request.reason,
            comment_template=request.comment_template,
            common_findings=request.common_findings,
            score_adjustment=request.score_adjustment,
            created_by=creator_id,
            created_at=datetime.utcnow()
        )
        
        self.templates[template_id] = template
        self._save_templates()
        
        return template
    
    def get_templates(self, reason: Optional[OverrideReasonEnum] = None) -> List[OverrideTemplate]:
        """Get override templates, optionally filtered by reason."""
        templates = list(self.templates.values())
        
        if reason:
            templates = [t for t in templates if t.reason == reason]
        
        return templates
    
    def validate_override(self, request: OverrideValidationRequest, original_analysis: AnalysisResult) -> OverrideValidationResponse:
        """Validate a proposed override before applying."""
        validation_errors = []
        validation_warnings = []
        recommendations = []
        
        # Validate finding overrides
        for override in request.proposed_overrides:
            if override.new_score_impact is not None and override.new_score_impact > 0:
                validation_warnings.append(f"Finding {override.finding_id} has positive score impact, which is unusual")
            
            if override.new_severity and override.new_severity.value == "critical" and override.original_severity.value == "info":
                validation_errors.append(f"Cannot upgrade finding {override.finding_id} from info to critical")
        
        # Validate score override
        if request.proposed_score_override:
            if request.proposed_score_override.new_score < 0 or request.proposed_score_override.new_score > 100:
                validation_errors.append("Score must be between 0 and 100")
            
            score_change = request.proposed_score_override.new_score - request.proposed_score_override.original_score
            if abs(score_change) > 20:
                validation_warnings.append(f"Large score adjustment ({score_change:+.1f}) requires strong justification")
        
        # Calculate estimated impact
        estimated_impact = {
            "score_change": 0,
            "findings_affected": len(request.proposed_overrides),
            "severity_changes": sum(1 for fo in request.proposed_overrides if fo.new_severity != fo.original_severity)
        }
        
        if request.proposed_score_override:
            estimated_impact["score_change"] = (
                request.proposed_score_override.new_score - request.proposed_score_override.original_score
            )
        
        # Generate recommendations
        if len(request.proposed_overrides) > 5:
            recommendations.append("Consider creating a template for common overrides")
        
        if not validation_errors:
            recommendations.append("Override appears valid and ready for application")
        
        return OverrideValidationResponse(
            is_valid=len(validation_errors) == 0,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            estimated_impact=estimated_impact,
            recommendations=recommendations
        )
    
    def apply_template(self, template_id: str, submission_id: str, context: Dict[str, Any]) -> FindingOverride:
        """Apply a template to create a finding override."""
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.templates[template_id]
        
        # Fill template placeholders
        comment = template.comment_template
        for key, value in context.items():
            comment = comment.replace(f"{{{key}}}", str(value))
        
        # Create finding override
        override = FindingOverride(
            finding_id=context.get("finding_id", ""),
            original_severity=SeverityLevel(context.get("original_severity", "medium")),
            new_severity=SeverityLevel(context.get("new_severity", "low")),
            original_score_impact=context.get("original_score_impact", -2.0),
            new_score_impact=template.score_adjustment,
            reason=template.reason,
            comment=comment,
            evidence=context.get("evidence", [])
        )
        
        return override
