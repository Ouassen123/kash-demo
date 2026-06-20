"""Override service for SME (Subject Matter Expert) adjustments to job mappings."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field

from ..models import (
    JobMatchResult,
    KASHDomainEnum,
    CompetencyLevel,
    ConfidenceLevel
)
from .matching_service import LearnerKASHProfile


class OverrideReasonEnum(str, Enum):
    """Reasons for SME overrides."""
    EXPERT_JUDGMENT = "expert_judgment"
    MARKET_CONDITIONS = "market_conditions"
    SPECIAL_CIRCUMSTANCES = "special_circumstances"
    DATA_QUALITY = "data_quality"
    EMERGING_TRENDS = "emerging_trends"
    REGIONAL_FACTORS = "regional_factors"
    EXPERIENCE_EQUIVALENCY = "experience_equivalency"
    CERTIFICATION_OVERRIDE = "certification_override"


class OverrideTypeEnum(str, Enum):
    """Types of overrides that can be applied."""
    COMPETENCY_LEVEL = "competency_level"
    WEIGHT_ADJUSTMENT = "weight_adjustment"
    DOMAIN_SCORE = "domain_score"
    OVERALL_SCORE = "overall_score"
    CONFIDENCE_LEVEL = "confidence_level"
    ALTERNATIVE_ADDITION = "alternative_addition"
    ALTERNATIVE_REMOVAL = "alternative_removal"


class SMEOverride(BaseModel):
    """Individual SME override record."""
    override_id: str = Field(..., description="Unique override identifier")
    learner_id: str = Field(..., description="Learner identifier")
    job_id: str = Field(..., description="Job profile identifier")
    sme_id: str = Field(..., description="SME identifier")
    sme_name: str = Field(..., description="SME name")
    override_type: OverrideTypeEnum = Field(..., description="Type of override")
    reason: OverrideReasonEnum = Field(..., description="Reason for override")
    
    # Original values
    original_value: Any = Field(..., description="Original value before override")
    
    # Override values
    new_value: Any = Field(..., description="New override value")
    target_domain: Optional[KASHDomainEnum] = Field(None, description="Target domain if applicable")
    target_competency: Optional[str] = Field(None, description="Target competency if applicable")
    
    # Metadata
    comment: str = Field(..., description="SME comment explaining the override")
    evidence: List[str] = Field(default_factory=list, description="Evidence supporting the override")
    temporary: bool = Field(False, description="Whether this is a temporary override")
    expires_at: Optional[datetime] = Field(None, description="Expiration date for temporary overrides")
    
    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    applied_at: Optional[datetime] = Field(None, description="When override was applied")
    is_active: bool = Field(True, description="Whether override is currently active")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "override_id": "override_123",
                "learner_id": "learner_456",
                "job_id": "software_developer_001",
                "sme_id": "sme_789",
                "sme_name": "Dr. Jane Smith",
                "override_type": "competency_level",
                "reason": "experience_equivalency",
                "original_value": "basic",
                "new_value": "intermediate",
                "target_domain": "skills",
                "target_competency": "programming_languages",
                "comment": "Learner has 3 years of industry experience equivalent to intermediate level",
                "evidence": ["Industry certification", "Portfolio review", "Reference check"]
            }
        }
    }


class OverrideBatch(BaseModel):
    """Batch of related overrides for a specific learner-job combination."""
    batch_id: str = Field(..., description="Unique batch identifier")
    learner_id: str = Field(..., description="Learner identifier")
    job_id: str = Field(..., description="Job profile identifier")
    sme_id: str = Field(..., description="SME identifier")
    sme_name: str = Field(..., description="SME name")
    
    overrides: List[SMEOverride] = Field(..., description="List of overrides in this batch")
    batch_reason: str = Field(..., description="Overall reason for this batch of overrides")
    
    # Original and modified match results
    original_match_score: float = Field(..., description="Original match score before overrides")
    modified_match_score: float = Field(..., description="Modified match score after overrides")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    applied_at: Optional[datetime] = Field(None, description="When batch was applied")
    is_active: bool = Field(True, description="Whether batch is currently active")
    
    @property
    def score_change(self) -> float:
        """Calculate the change in match score."""
        return self.modified_match_score - self.original_match_score
    
    @property
    def score_change_percentage(self) -> float:
        """Calculate percentage change in match score."""
        if self.original_match_score == 0:
            return 0.0
        return (self.score_change / self.original_match_score) * 100
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "batch_id": "batch_456",
                "learner_id": "learner_123",
                "job_id": "software_developer_001",
                "sme_id": "sme_789",
                "sme_name": "Dr. Jane Smith",
                "batch_reason": "Adjusting for industry experience and certifications",
                "original_match_score": 0.65,
                "modified_match_score": 0.82
            }
        }
    }


class OverrideValidationResult(BaseModel):
    """Result of override validation."""
    is_valid: bool = Field(..., description="Whether override is valid")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    validation_warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    
    # Impact analysis
    score_impact: Optional[float] = Field(None, description="Estimated impact on match score")
    confidence_impact: Optional[str] = Field(None, description="Impact on confidence level")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "is_valid": True,
                "validation_errors": [],
                "validation_warnings": ["Large score adjustment may require additional justification"],
                "recommendations": ["Document evidence for this override"],
                "score_impact": 0.15,
                "confidence_impact": "Medium increase"
            }
        }
    }


class SMEOverrideService:
    """Service for managing SME overrides to job matching results."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).parent.parent / "data" / "overrides"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Override storage files
        self.overrides_file = self.storage_path / "sme_overrides.json"
        self.batches_file = self.storage_path / "override_batches.json"
        
        # Load existing overrides
        self.overrides = self._load_overrides()
        self.batches = self._load_batches()
    
    def _load_overrides(self) -> Dict[str, SMEOverride]:
        """Load existing overrides from storage."""
        if not self.overrides_file.exists():
            return {}
        
        try:
            with open(self.overrides_file, 'r') as f:
                data = json.load(f)
            
            overrides = {}
            for override_id, override_data in data.items():
                # Convert datetime strings back to datetime objects
                if override_data.get("created_at"):
                    override_data["created_at"] = datetime.fromisoformat(override_data["created_at"])
                if override_data.get("expires_at"):
                    override_data["expires_at"] = datetime.fromisoformat(override_data["expires_at"])
                if override_data.get("applied_at"):
                    override_data["applied_at"] = datetime.fromisoformat(override_data["applied_at"])
                
                overrides[override_id] = SMEOverride(**override_data)
            
            return overrides
        except Exception as e:
            print(f"Error loading overrides: {e}")
            return {}
    
    def _load_batches(self) -> Dict[str, OverrideBatch]:
        """Load existing override batches from storage."""
        if not self.batches_file.exists():
            return {}
        
        try:
            with open(self.batches_file, 'r') as f:
                data = json.load(f)
            
            batches = {}
            for batch_id, batch_data in data.items():
                # Convert datetime strings back to datetime objects
                if batch_data.get("created_at"):
                    batch_data["created_at"] = datetime.fromisoformat(batch_data["created_at"])
                if batch_data.get("applied_at"):
                    batch_data["applied_at"] = datetime.fromisoformat(batch_data["applied_at"])
                
                # Convert overrides in batch
                overrides = []
                for override_data in batch_data.get("overrides", []):
                    if override_data.get("created_at"):
                        override_data["created_at"] = datetime.fromisoformat(override_data["created_at"])
                    if override_data.get("expires_at"):
                        override_data["expires_at"] = datetime.fromisoformat(override_data["expires_at"])
                    if override_data.get("applied_at"):
                        override_data["applied_at"] = datetime.fromisoformat(override_data["applied_at"])
                    
                    overrides.append(SMEOverride(**override_data))
                
                batch_data["overrides"] = overrides
                batches[batch_id] = OverrideBatch(**batch_data)
            
            return batches
        except Exception as e:
            print(f"Error loading batches: {e}")
            return {}
    
    def _save_overrides(self):
        """Save overrides to storage."""
        data = {}
        for override_id, override in self.overrides.items():
            data[override_id] = override.model_dump()
        
        with open(self.overrides_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _save_batches(self):
        """Save override batches to storage."""
        data = {}
        for batch_id, batch in self.batches.items():
            data[batch_id] = batch.model_dump()
        
        with open(self.batches_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def validate_override(self, override: SMEOverride, 
                         original_match_result: JobMatchResult) -> OverrideValidationResult:
        """Validate an override before applying it."""
        result = OverrideValidationResult(is_valid=True)
        
        # Check if override is expired
        if override.expires_at and override.expires_at < datetime.utcnow():
            result.is_valid = False
            result.validation_errors.append("Override has expired")
            return result
        
        # Validate competency level overrides
        if override.override_type == OverrideTypeEnum.COMPETENCY_LEVEL:
            if not override.target_domain or not override.target_competency:
                result.is_valid = False
                result.validation_errors.append("Competency level overrides must specify target domain and competency")
            
            # Check if new value is a valid competency level
            try:
                new_level = CompetencyLevel(override.new_value)
                original_level = CompetencyLevel(override.original_value)
                
                # Calculate score impact
                level_diff = self.level_hierarchy.get(new_level, 0) - self.level_hierarchy.get(original_level, 0)
                result.score_impact = level_diff * 0.1  # Rough estimate
                
                if abs(level_diff) > 2:
                    result.validation_warnings.append("Large competency level jump detected")
                
            except ValueError:
                result.is_valid = False
                result.validation_errors.append("Invalid competency level specified")
        
        # Validate weight adjustment overrides
        elif override.override_type == OverrideTypeEnum.WEIGHT_ADJUSTMENT:
            try:
                new_weight = float(override.new_value)
                if not 0 <= new_weight <= 1:
                    result.is_valid = False
                    result.validation_errors.append("Weight must be between 0 and 1")
                
                result.score_impact = (new_weight - float(override.original_value)) * 0.5
                
            except (ValueError, TypeError):
                result.is_valid = False
                result.validation_errors.append("Invalid weight value specified")
        
        # Validate overall score overrides
        elif override.override_type == OverrideTypeEnum.OVERALL_SCORE:
            try:
                new_score = float(override.new_value)
                if not 0 <= new_score <= 1:
                    result.is_valid = False
                    result.validation_errors.append("Overall score must be between 0 and 1")
                
                result.score_impact = new_score - float(override.original_value)
                
                if abs(result.score_impact) > 0.3:
                    result.validation_warnings.append("Large overall score adjustment detected")
                
            except (ValueError, TypeError):
                result.is_valid = False
                result.validation_errors.append("Invalid overall score value specified")
        
        # Check for duplicate overrides
        existing_overrides = self.get_active_overrides(override.learner_id, override.job_id)
        for existing in existing_overrides:
            if (existing.override_type == override.override_type and 
                existing.target_domain == override.target_domain and
                existing.target_competency == override.target_competency and
                existing.is_active):
                result.validation_warnings.append("Similar override already exists")
        
        # Generate recommendations
        if result.is_valid:
            if not override.evidence:
                result.recommendations.append("Add evidence to support this override")
            
            if len(override.comment) < 20:
                result.recommendations.append("Provide more detailed justification")
            
            if override.reason == OverrideReasonEnum.EXPERT_JUDGMENT:
                result.recommendations.append("Document specific expertise that justifies this judgment")
        
        return result
    
    def create_override(self, learner_id: str, job_id: str, sme_id: str, sme_name: str,
                       override_type: OverrideTypeEnum, reason: OverrideReasonEnum,
                       original_value: Any, new_value: Any, comment: str,
                       target_domain: Optional[KASHDomainEnum] = None,
                       target_competency: Optional[str] = None,
                       evidence: Optional[List[str]] = None,
                       temporary: bool = False,
                       expires_at: Optional[datetime] = None) -> SMEOverride:
        """Create a new SME override."""
        
        override = SMEOverride(
            override_id=str(uuid.uuid4()),
            learner_id=learner_id,
            job_id=job_id,
            sme_id=sme_id,
            sme_name=sme_name,
            override_type=override_type,
            reason=reason,
            original_value=original_value,
            new_value=new_value,
            target_domain=target_domain,
            target_competency=target_competency,
            comment=comment,
            evidence=evidence or [],
            temporary=temporary,
            expires_at=expires_at
        )
        
        # Store override
        self.overrides[override.override_id] = override
        self._save_overrides()
        
        return override
    
    def apply_overrides_to_match(self, original_match: JobMatchResult) -> JobMatchResult:
        """Apply all active overrides to a match result."""
        # Get active overrides for this learner-job combination
        active_overrides = self.get_active_overrides(
            original_match.learner_id, 
            original_match.job_profile.job_id
        )
        
        if not active_overrides:
            return original_match
        
        # Create a copy of the match result to modify
        modified_match = JobMatchResult(
            learner_id=original_match.learner_id,
            job_profile=original_match.job_profile,
            overall_match_score=original_match.overall_match_score,
            domain_results=original_match.domain_results.copy(),
            confidence_metrics=original_match.confidence_metrics,
            alternative_suggestions=original_match.alternative_suggestions.copy(),
            match_summary=original_match.match_summary,
            key_strengths=original_match.key_strengths.copy(),
            development_areas=original_match.development_areas.copy(),
            next_steps=original_match.next_steps.copy(),
            estimated_readiness_timeline=original_match.estimated_readiness_timeline,
            calculated_at=original_match.calculated_at,
            calculation_version=original_match.calculation_version
        )
        
        # Apply overrides in order
        for override in active_overrides:
            self._apply_single_override(modified_match, override)
            override.applied_at = datetime.utcnow()
        
        # Save updated overrides
        self._save_overrides()
        
        # Update match summary based on changes
        if modified_match.overall_match_score != original_match.overall_match_score:
            modified_match.match_summary = f"Adjusted by SME: {modified_match.match_summary}"
        
        return modified_match
    
    def _apply_single_override(self, match_result: JobMatchResult, override: SMEOverride):
        """Apply a single override to a match result."""
        
        if override.override_type == OverrideTypeEnum.COMPETENCY_LEVEL:
            # Update competency level in domain results
            if override.target_domain and override.target_competency:
                domain_result = match_result.domain_results.get(override.target_domain)
                if domain_result:
                    for comp_match in domain_result.competency_matches:
                        if comp_match.competency_name == override.target_competency:
                            comp_match.learner_level = CompetencyLevel(override.new_value)
                            
                            # Recalculate match score for this competency
                            required_level_value = self.level_hierarchy[comp_match.required_level]
                            learner_level_value = self.level_hierarchy[comp_match.learner_level]
                            
                            if learner_level_value >= required_level_value:
                                comp_match.match_score = 1.0
                            else:
                                level_diff = required_level_value - learner_level_value
                                comp_match.match_score = max(0.0, 1.0 - (level_diff * 0.3))
                            
                            comp_match.weighted_score = comp_match.match_score * comp_match.weight
                            break
        
        elif override.override_type == OverrideTypeEnum.OVERALL_SCORE:
            # Directly override overall score
            match_result.overall_match_score = float(override.new_value)
        
        elif override.override_type == OverrideTypeEnum.DOMAIN_SCORE:
            # Override domain-specific score
            if override.target_domain:
                domain_result = match_result.domain_results.get(override.target_domain)
                if domain_result:
                    domain_result.overall_score = float(override.new_value)
        
        elif override.override_type == OverrideTypeEnum.CONFIDENCE_LEVEL:
            # Override confidence level
            try:
                match_result.confidence_metrics.overall_confidence = ConfidenceLevel(override.new_value)
            except ValueError:
                pass  # Invalid confidence level, ignore
    
    def get_active_overrides(self, learner_id: str, job_id: str) -> List[SMEOverride]:
        """Get all active overrides for a specific learner-job combination."""
        active_overrides = []
        
        for override in self.overrides.values():
            if (override.learner_id == learner_id and 
                override.job_id == job_id and 
                override.is_active):
                
                # Check if override is expired
                if override.expires_at and override.expires_at < datetime.utcnow():
                    override.is_active = False
                    continue
                
                active_overrides.append(override)
        
        # Sort by creation date (newest first)
        active_overrides.sort(key=lambda x: x.created_at, reverse=True)
        return active_overrides
    
    def create_override_batch(self, learner_id: str, job_id: str, sme_id: str, sme_name: str,
                            overrides_data: List[Dict[str, Any]], batch_reason: str,
                            original_match_score: float) -> OverrideBatch:
        """Create a batch of related overrides."""
        
        batch_overrides = []
        
        for override_data in overrides_data:
            override = self.create_override(
                learner_id=learner_id,
                job_id=job_id,
                sme_id=sme_id,
                sme_name=sme_name,
                override_type=OverrideTypeEnum(override_data["override_type"]),
                reason=OverrideReasonEnum(override_data["reason"]),
                original_value=override_data["original_value"],
                new_value=override_data["new_value"],
                comment=override_data["comment"],
                target_domain=KASHDomainEnum(override_data["target_domain"]) if override_data.get("target_domain") else None,
                target_competency=override_data.get("target_competency"),
                evidence=override_data.get("evidence", []),
                temporary=override_data.get("temporary", False),
                expires_at=datetime.fromisoformat(override_data["expires_at"]) if override_data.get("expires_at") else None
            )
            batch_overrides.append(override)
        
        # Create batch
        batch = OverrideBatch(
            batch_id=str(uuid.uuid4()),
            learner_id=learner_id,
            job_id=job_id,
            sme_id=sme_id,
            sme_name=sme_name,
            overrides=batch_overrides,
            batch_reason=batch_reason,
            original_match_score=original_match_score,
            modified_match_score=original_match_score  # Will be updated after application
        )
        
        # Store batch
        self.batches[batch.batch_id] = batch
        self._save_batches()
        
        return batch
    
    def get_override_history(self, learner_id: Optional[str] = None, 
                           job_id: Optional[str] = None,
                           sme_id: Optional[str] = None) -> List[SMEOverride]:
        """Get override history with optional filtering."""
        history = []
        
        for override in self.overrides.values():
            # Apply filters
            if learner_id and override.learner_id != learner_id:
                continue
            if job_id and override.job_id != job_id:
                continue
            if sme_id and override.sme_id != sme_id:
                continue
            
            history.append(override)
        
        # Sort by creation date (newest first)
        history.sort(key=lambda x: x.created_at, reverse=True)
        return history
    
    def get_batch_history(self, learner_id: Optional[str] = None,
                         sme_id: Optional[str] = None) -> List[OverrideBatch]:
        """Get override batch history with optional filtering."""
        batches = []
        
        for batch in self.batches.values():
            # Apply filters
            if learner_id and batch.learner_id != learner_id:
                continue
            if sme_id and batch.sme_id != sme_id:
                continue
            
            batches.append(batch)
        
        # Sort by creation date (newest first)
        batches.sort(key=lambda x: x.created_at, reverse=True)
        return batches
    
    def deactivate_override(self, override_id: str, sme_id: str) -> bool:
        """Deactivate an override (can only be done by the creating SME or admin)."""
        override = self.overrides.get(override_id)
        if not override:
            return False
        
        # Check permissions (simplified - in real app, check admin role too)
        if override.sme_id != sme_id:
            return False
        
        override.is_active = False
        self._save_overrides()
        return True
    
    def get_sme_statistics(self, sme_id: str) -> Dict[str, Any]:
        """Get statistics for a specific SME."""
        sme_overrides = [o for o in self.overrides.values() if o.sme_id == sme_id]
        sme_batches = [b for b in self.batches.values() if b.sme_id == sme_id]
        
        stats = {
            "sme_id": sme_id,
            "total_overrides": len(sme_overrides),
            "active_overrides": len([o for o in sme_overrides if o.is_active]),
            "total_batches": len(sme_batches),
            "override_types": {},
            "reason_distribution": {},
            "average_score_impact": 0.0,
            "most_common_jobs": {}
        }
        
        # Calculate override type distribution
        for override in sme_overrides:
            override_type = override.override_type.value
            stats["override_types"][override_type] = stats["override_types"].get(override_type, 0) + 1
        
        # Calculate reason distribution
        for override in sme_overrides:
            reason = override.reason.value
            stats["reason_distribution"][reason] = stats["reason_distribution"].get(reason, 0) + 1
        
        # Calculate most common jobs
        job_counts = {}
        for override in sme_overrides:
            job_counts[override.job_id] = job_counts.get(override.job_id, 0) + 1
        
        stats["most_common_jobs"] = dict(sorted(job_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        
        return stats
    
    # Helper property for competency level hierarchy
    @property
    def level_hierarchy(self) -> Dict[CompetencyLevel, int]:
        """Get competency level hierarchy."""
        return {
            CompetencyLevel.NONE: 0,
            CompetencyLevel.BASIC: 1,
            CompetencyLevel.INTERMEDIATE: 2,
            CompetencyLevel.ADVANCED: 3,
            CompetencyLevel.EXPERT: 4
        }
