"""Assessment models for KASH Platform."""

from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.core.database import Base


class UserAssessment(Base):
    """User assessment tracking across all KASH domains."""
    
    __tablename__ = "user_assessments"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Assessment metadata
    assessment_type = Column(
        ENUM('knowledge', 'abilities', 'skills', 'intelligence', name='assessment_type_enum'),
        nullable=False
    )
    assessment_name = Column(String(200), nullable=False)
    assessment_version = Column(String(20), default="1.0", nullable=False)
    
    # Status tracking
    status = Column(
        ENUM('pending', 'in_progress', 'completed', 'failed', 'expired', name='assessment_status_enum'),
        default='pending',
        nullable=False
    )
    
    # Scoring
    raw_score = Column(Float, nullable=True)
    normalized_score = Column(Float, nullable=True)  # 0-100 scale
    confidence_score = Column(Float, nullable=True)  # 0-1 scale
    
    # Assessment data
    input_data = Column(JSON, nullable=True)  # CV text, quiz answers, code, etc.
    result_data = Column(JSON, nullable=True)  # Detailed results, explanations
    assessment_metadata = Column(JSON, nullable=True)  # Additional context
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="assessments")
    knowledge_assessments = relationship("KnowledgeAssessment", back_populates="assessment", cascade="all, delete-orphan")
    abilities_assessments = relationship("AbilitiesAssessment", back_populates="assessment", cascade="all, delete-orphan")
    skills_assessments = relationship("SkillsAssessment", back_populates="assessment", cascade="all, delete-orphan")
    intelligence_assessments = relationship("IntelligenceAssessment", back_populates="assessment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserAssessment(id={self.id}, type={self.assessment_type}, status={self.status})>"


class KnowledgeAssessment(Base):
    """Knowledge domain specific assessment data (CV analysis, ESCO mapping)."""
    
    __tablename__ = "knowledge_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("user_assessments.id"), nullable=False)
    
    # CV analysis results
    cv_text = Column(Text, nullable=True)
    cv_parsed_data = Column(JSON, nullable=True)  # Parsed sections, skills, experience
    
    # ESCO/O*NET mappings
    esco_skills = Column(JSON, nullable=True)  # Matched ESCO skills with confidence
    esco_occupations = Column(JSON, nullable=True)  # Suggested occupations
    onet_scores = Column(JSON, nullable=True)  # O*NET work values/interests
    
    # Knowledge domain scores
    domain_scores = Column(JSON, nullable=True)  # Scores by knowledge domain
    skill_gaps = Column(JSON, nullable=True)  # Identified skill gaps
    
    # Processing metadata
    processing_time_ms = Column(Float, nullable=True)
    model_version = Column(String(50), nullable=True)
    
    # Relationships
    assessment = relationship("UserAssessment", back_populates="knowledge_assessments")
    
    def __repr__(self):
        return f"<KnowledgeAssessment(id={self.id}, assessment_id={self.assessment_id})>"


class AbilitiesAssessment(Base):
    """Abilities domain specific assessment data (adaptive quizzes, cognitive tests)."""
    
    __tablename__ = "abilities_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("user_assessments.id"), nullable=False)
    
    # Quiz configuration
    quiz_type = Column(String(50), nullable=False)  # cognitive, behavioral, technical
    difficulty_level = Column(String(20), nullable=True)  # adaptive based on performance
    question_count = Column(Integer, default=0, nullable=False)
    
    # Quiz results
    total_questions = Column(Integer, default=0, nullable=False, server_default="0")
    correct_answers = Column(Integer, default=0, nullable=False, server_default="0")
    time_spent_minutes = Column(Float, nullable=True)
    
    # Ability scores
    cognitive_scores = Column(JSON, nullable=True)  # Memory, reasoning, problem-solving
    behavioral_scores = Column(JSON, nullable=True)  # Personality, work style
    technical_scores = Column(JSON, nullable=True)  # Technical aptitude
    
    # Adaptive algorithm data
    difficulty_progression = Column(JSON, nullable=True)  # How difficulty changed
    response_patterns = Column(JSON, nullable=True)  # Time per question, changes
    
    # Relationships
    assessment = relationship("UserAssessment", back_populates="abilities_assessments")
    
    def __repr__(self):
        return f"<AbilitiesAssessment(id={self.id}, quiz_type={self.quiz_type})>"


class SkillsAssessment(Base):
    """Skills domain specific assessment data (GitHub analysis, code evaluation)."""
    
    __tablename__ = "skills_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("user_assessments.id"), nullable=False)
    
    # Source information
    source_type = Column(String(20), nullable=False)  # github, upload, text
    source_url = Column(Text, nullable=True)  # GitHub repo URL
    source_metadata = Column(JSON, nullable=True)  # Repo info, file count, etc.
    
    # Code analysis results
    programming_languages = Column(JSON, nullable=True)  # Languages with usage percentages
    code_quality_metrics = Column(JSON, nullable=True)  # Complexity, maintainability, etc.
    technical_skills = Column(JSON, nullable=True)  # Identified technical skills
    
    # Project analysis
    project_complexity = Column(Float, nullable=True)  # Overall complexity score
    collaboration_indicators = Column(JSON, nullable=True)  # Team work patterns
    learning_trajectory = Column(JSON, nullable=True)  # Skill progression over time
    
    # Processing metadata
    analysis_date = Column(DateTime(timezone=True), nullable=True)
    analyzer_version = Column(String(50), nullable=True)
    
    # Relationships
    assessment = relationship("UserAssessment", back_populates="skills_assessments")
    
    def __repr__(self):
        return f"<SkillsAssessment(id={self.id}, source_type={self.source_type})>"


class IntelligenceAssessment(Base):
    """Intelligence domain specific assessment data (KASH scoring, SHAP explainability)."""
    
    __tablename__ = "intelligence_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("user_assessments.id"), nullable=False)
    
    # KASH scoring configuration
    kash_weights = Column(JSON, nullable=True)  # Custom weights for KASH domains
    industry_weights = Column(JSON, nullable=True)  # Industry-specific weight adjustments
    
    # SHAP explainability data
    feature_importance_data = Column(JSON, nullable=True)  # SHAP values and explanations
    career_path_explanations = Column(JSON, nullable=True)  # Career path match explanations
    skill_gap_analysis = Column(JSON, nullable=True)  # Skill gap analysis results
    assessment_impact_data = Column(JSON, nullable=True)  # Impact of each assessment
    recommendation_explanations = Column(JSON, nullable=True)  # Why recommendations were made
    
    # Intelligence analysis results
    kash_domain_scores = Column(JSON, nullable=True)  # Detailed KASH domain breakdowns
    career_stage_predictions = Column(JSON, nullable=True)  # Career stage analysis
    learning_trajectory = Column(JSON, nullable=True)  # Predicted learning path
    
    # Model and analysis metadata
    model_version = Column(String(50), nullable=True)
    analysis_date = Column(DateTime(timezone=True), nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    
    # Relationships
    assessment = relationship("UserAssessment", back_populates="intelligence_assessments")
    
    def __repr__(self):
        return f"<IntelligenceAssessment(id={self.id}, model_version={self.model_version})>"
