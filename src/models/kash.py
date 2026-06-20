"""KASH (Knowledge, Abilities, Skills, Intelligence) models."""

from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.core.database import Base


class KashProfile(Base):
    """Complete KASH profile for a user combining all assessment results."""
    
    __tablename__ = "kash_profiles"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Profile metadata
    profile_version = Column(String(20), default="1.0", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Overall KASH scores (0-100 scale)
    knowledge_score = Column(Float, nullable=True)
    abilities_score = Column(Float, nullable=True)
    skills_score = Column(Float, nullable=True)
    intelligence_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    
    # Score confidence and metadata
    score_confidence = Column(Float, nullable=True)  # 0-1 scale
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Weight configuration for scoring
    knowledge_weight = Column(Float, default=0.25, nullable=False)
    abilities_weight = Column(Float, default=0.25, nullable=False)
    skills_weight = Column(Float, default=0.25, nullable=False)
    intelligence_weight = Column(Float, default=0.25, nullable=False)
    
    # Detailed breakdowns
    domain_breakdown = Column(JSON, nullable=True)  # Detailed scores by subdomain
    strength_areas = Column(JSON, nullable=True)  # Top strength areas
    development_areas = Column(JSON, nullable=True)  # Areas needing development
    
    # Career recommendations
    recommended_careers = Column(JSON, nullable=True)  # Career path suggestions
    skill_gaps = Column(JSON, nullable=True)  # Identified skill gaps
    learning_recommendations = Column(JSON, nullable=True)  # Learning paths
    
    # Relationships
    user = relationship("User", back_populates="kash_profiles")
    predictions = relationship("IntelligencePrediction", back_populates="kash_profile", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KashProfile(id={self.id}, user_id={self.user_id}, overall_score={self.overall_score})>"


class IntelligencePrediction(Base):
    """ML predictions and explainability for intelligence module."""
    
    __tablename__ = "intelligence_predictions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kash_profile_id = Column(UUID(as_uuid=True), ForeignKey("kash_profiles.id"), nullable=False)
    
    # Prediction metadata
    prediction_type = Column(String(50), nullable=False)  # career_success, skill_match, learning_path
    model_version = Column(String(50), nullable=False)
    prediction_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Prediction results
    predicted_value = Column(Float, nullable=False)  # Main prediction value
    prediction_class = Column(String(100), nullable=True)  # Classification result
    confidence_score = Column(Float, nullable=True)  # Model confidence
    
    # Explainability (SHAP values)
    feature_importance = Column(JSON, nullable=True)  # SHAP feature importance
    feature_contributions = Column(JSON, nullable=True)  # Individual feature contributions
    base_value = Column(Float, nullable=True)  # SHAP base value
    
    # Input features used
    input_features = Column(JSON, nullable=True)  # Features used for prediction
    feature_metadata = Column(JSON, nullable=True)  # Feature descriptions and types
    
    # Alternative predictions
    alternative_predictions = Column(JSON, nullable=True)  # Other possible outcomes
    prediction_range = Column(JSON, nullable=True)  # Confidence intervals
    
    # Performance metrics
    model_accuracy = Column(Float, nullable=True)  # Historical accuracy
    calibration_score = Column(Float, nullable=True)  # Prediction calibration
    
    # Relationships
    kash_profile = relationship("KashProfile", back_populates="predictions")
    
    def __repr__(self):
        return f"<IntelligencePrediction(id={self.id}, type={self.prediction_type}, confidence={self.confidence_score})>"


class CareerPath(Base):
    """Career path definitions and requirements."""
    
    __tablename__ = "career_paths"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Career information
    career_name = Column(String(200), nullable=False)
    career_category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # ESCO/O*NET mappings
    esco_codes = Column(JSON, nullable=True)  # Related ESCO occupation codes
    onet_code = Column(String(10), nullable=True)  # O*NET occupation code
    
    # Required KASH profile
    required_knowledge_score = Column(Float, nullable=True)
    required_abilities_score = Column(Float, nullable=True)
    required_skills_score = Column(Float, nullable=True)
    required_intelligence_score = Column(Float, nullable=True)
    
    # Skill requirements
    required_skills = Column(JSON, nullable=True)  # List of required skills
    preferred_skills = Column(JSON, nullable=True)  # Preferred but not required
    
    # Career metadata
    average_salary = Column(Float, nullable=True)
    growth_projection = Column(Float, nullable=True)  # 5-year growth projection
    education_requirements = Column(JSON, nullable=True)
    experience_requirements = Column(String(100), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<CareerPath(id={self.id}, name={self.career_name}, category={self.career_category})>"


class SkillTaxonomy(Base):
    """Skills taxonomy for mapping and classification."""
    
    __tablename__ = "skill_taxonomy"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Skill information
    skill_name = Column(String(200), nullable=False)
    skill_category = Column(String(100), nullable=False)
    skill_description = Column(Text, nullable=True)
    
    # Taxonomy mappings
    esco_skill_code = Column(String(50), nullable=True)
    esco_skill_uri = Column(Text, nullable=True)
    onet_skill_id = Column(String(10), nullable=True)
    
    # Skill metadata
    difficulty_level = Column(Integer, nullable=True)  # 1-10 scale
    learning_time_hours = Column(Float, nullable=True)
    prerequisite_skills = Column(JSON, nullable=True)  # Required prerequisite skills
    
    # KASH domain classification
    primary_domain = Column(
        ENUM('knowledge', 'abilities', 'skills', 'intelligence', name='skill_domain_enum'),
        nullable=False
    )
    secondary_domains = Column(JSON, nullable=True)  # Can belong to multiple domains
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<SkillTaxonomy(id={self.id}, name={self.skill_name}, domain={self.primary_domain})>"
