"""Feature engineering service for predictive modeling."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import json
import logging

from ..models.feature_models import (
    FeatureDefinition,
    FeatureStore,
    CompatibilityFeatures,
    HistoricalPerformanceFeatures,
    DemographicFeatures,
    BehavioralFeatures,
    TrainingExample,
    FeatureEngineeringStep
)
from ..models.prediction_models import FeatureType, DataQuality
from ...compatibility.services.scoring_pipeline import ScoringPipeline
from ...compatibility.services.weight_manager import WeightManager


class FeatureEngineeringService:
    """Service for engineering features for predictive modeling."""
    
    def __init__(self, feature_store_path: Optional[Path] = None):
        self.feature_store_path = feature_store_path or Path(__file__).parent.parent / "data" / "feature_store"
        self.feature_store_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize feature store
        self.feature_store_file = self.feature_store_path / "feature_store.json"
        self.feature_store = self._load_feature_store()
        
        # Initialize dependencies
        self.scoring_pipeline = ScoringPipeline()
        self.weight_manager = WeightManager()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Feature engineering registry
        self.engineering_steps = {}
        self._register_engineering_steps()
    
    def _load_feature_store(self) -> FeatureStore:
        """Load feature store from storage."""
        if not self.feature_store_file.exists():
            # Create default feature store
            feature_store = FeatureStore(
                store_name="kash_predictive_features",
                version="1.0",
                feature_definitions=[],
                active_features=[],
                data_sources={
                    "compatibility_scores": "Compatibility scoring service",
                    "historical_performance": "LMS and assessment data",
                    "demographics": "User profile data",
                    "behavioral": "Platform interaction data"
                },
                refresh_schedule="daily",
                description="Feature store for KASH predictive modeling",
                created_by="feature_engineering_service"
            )
            self._save_feature_store(feature_store)
            return feature_store
        
        try:
            with open(self.feature_store_file, 'r') as f:
                data = json.load(f)
            return FeatureStore(**data)
        except Exception as e:
            self.logger.error(f"Error loading feature store: {e}")
            raise
    
    def _save_feature_store(self, feature_store: FeatureStore):
        """Save feature store to storage."""
        try:
            with open(self.feature_store_file, 'w') as f:
                json.dump(feature_store.model_dump(), f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving feature store: {e}")
            raise
    
    def _register_engineering_steps(self):
        """Register feature engineering steps."""
        self.engineering_steps = {
            "normalize_compatibility_scores": self._normalize_compatibility_scores,
            "calculate_domain_ratios": self._calculate_domain_ratios,
            "create_trend_features": self._create_trend_features,
            "calculate_interaction_features": self._calculate_interaction_features,
            "create_polynomial_features": self._create_polynomial_features,
            "calculate_aggregation_features": self._calculate_aggregation_features,
            "encode_categorical_features": self._encode_categorical_features,
            "handle_missing_values": self._handle_missing_values,
            "detect_outliers": self._detect_outliers,
            "scale_features": self._scale_features
        }
    
    def create_compatibility_features(self, learner_id: str, job_family: str) -> CompatibilityFeatures:
        """Create compatibility features for a learner."""
        try:
            # Get compatibility scores from the compatibility service
            # This would typically involve calling the compatibility API
            # For now, we'll create a mock implementation
            
            # Mock data - in reality, this would come from the compatibility service
            compatibility_data = {
                "overall_score": 0.75,
                "confidence": 0.85,
                "domain_scores": {
                    "knowledge": 0.70,
                    "skills": 0.80,
                    "abilities": 0.75,
                    "habits": 0.65
                },
                "quality_metrics": {
                    "data_quality": 0.88,
                    "signal_freshness": 0.92,
                    "completeness": 0.78
                },
                "signal_counts": {
                    "total": 12,
                    "knowledge": 3,
                    "skills": 4,
                    "abilities": 3,
                    "habits": 2
                },
                "missing_signals": 2,
                "stale_signals": 1,
                "last_updated": datetime.utcnow(),
                "signal_age_days": 5
            }
            
            features = CompatibilityFeatures(
                learner_id=learner_id,
                job_family=job_family,
                overall_compatibility_score=compatibility_data["overall_score"],
                compatibility_confidence=compatibility_data["confidence"],
                knowledge_score=compatibility_data["domain_scores"]["knowledge"],
                skills_score=compatibility_data["domain_scores"]["skills"],
                abilities_score=compatibility_data["domain_scores"]["abilities"],
                habits_score=compatibility_data["domain_scores"]["habits"],
                data_quality_score=compatibility_data["quality_metrics"]["data_quality"],
                signal_freshness_score=compatibility_data["quality_metrics"]["signal_freshness"],
                completeness_score=compatibility_data["quality_metrics"]["completeness"],
                total_signals=compatibility_data["signal_counts"]["total"],
                knowledge_signals=compatibility_data["signal_counts"]["knowledge"],
                skills_signals=compatibility_data["signal_counts"]["skills"],
                abilities_signals=compatibility_data["signal_counts"]["abilities"],
                habits_signals=compatibility_data["signal_counts"]["habits"],
                missing_signals_count=compatibility_data["missing_signals"],
                stale_signals_count=compatibility_data["stale_signals"],
                last_updated=compatibility_data["last_updated"],
                signal_age_days=compatibility_data["signal_age_days"]
            )
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error creating compatibility features for learner {learner_id}: {e}")
            raise
    
    def create_historical_performance_features(self, learner_id: str) -> HistoricalPerformanceFeatures:
        """Create historical performance features for a learner."""
        try:
            # Mock historical performance data
            # In reality, this would come from LMS, assessment systems, etc.
            
            historical_data = {
                "academic": {
                    "gpa_trend": [3.2, 3.3, 3.4, 3.5, 3.6],
                    "course_completion_rate": 0.92,
                    "average_grade": 85.5,
                    "grade_improvement_trend": 0.15
                },
                "skills": {
                    "assessment_scores": [75, 80, 85, 88, 90],
                    "improvement_rate": 0.12,
                    "mastery_levels": 8
                },
                "projects": {
                    "success_rate": 0.88,
                    "complexity_trend": [0.6, 0.7, 0.75, 0.8, 0.85],
                    "collaboration_score": 0.82
                },
                "engagement": {
                    "login_frequency": 4.5,  # per week
                    "time_spent_learning": 12.3,  # hours per week
                    "interaction_level": 0.78,
                    "peer_engagement": 0.75
                },
                "progress": {
                    "skill_acquisition_rate": 2.1,  # skills per month
                    "learning_velocity": 0.85,
                    "milestone_completion_rate": 0.90
                },
                "temporal": {
                    "learning_consistency": 0.83,
                    "peak_hours": [10, 14, 19],  # 24-hour format
                    "seasonal_patterns": {
                        "spring": 0.88,
                        "summer": 0.75,
                        "fall": 0.92,
                        "winter": 0.80
                    }
                },
                "risk": {
                    "dropout_risk": 0.15,
                    "disengagement": ["reduced_login_frequency", "lower_interaction"],
                    "interventions": ["academic_warning", "mentor_assignment"]
                },
                "program": {
                    "days_in_program": 180,
                    "current_level": "intermediate",
                    "progress_percentage": 65.0
                }
            }
            
            features = HistoricalPerformanceFeatures(
                learner_id=learner_id,
                gpa_trend=historical_data["academic"]["gpa_trend"],
                course_completion_rate=historical_data["academic"]["course_completion_rate"],
                average_grade=historical_data["academic"]["average_grade"],
                grade_improvement_trend=historical_data["academic"]["grade_improvement_trend"],
                skills_assessment_scores=historical_data["skills"]["assessment_scores"],
                skills_improvement_rate=historical_data["skills"]["improvement_rate"],
                mastery_level_achieved=historical_data["skills"]["mastery_levels"],
                project_success_rate=historical_data["projects"]["success_rate"],
                project_complexity_trend=historical_data["projects"]["complexity_trend"],
                collaboration_score=historical_data["projects"]["collaboration_score"],
                login_frequency=historical_data["engagement"]["login_frequency"],
                time_spent_learning=historical_data["engagement"]["time_spent_learning"],
                interaction_level=historical_data["engagement"]["interaction_level"],
                peer_engagement_score=historical_data["engagement"]["peer_engagement"],
                skill_acquisition_rate=historical_data["progress"]["skill_acquisition_rate"],
                learning_velocity=historical_data["progress"]["learning_velocity"],
                milestone_completion_rate=historical_data["progress"]["milestone_completion_rate"],
                learning_consistency=historical_data["temporal"]["learning_consistency"],
                peak_performance_hours=historical_data["temporal"]["peak_hours"],
                seasonal_patterns=historical_data["temporal"]["seasonal_patterns"],
                dropout_risk_score=historical_data["risk"]["dropout_risk"],
                disengagement_indicators=historical_data["risk"]["disengagement"],
                intervention_history=historical_data["risk"]["interventions"],
                days_in_program=historical_data["program"]["days_in_program"],
                current_level=historical_data["program"]["current_level"],
                progress_percentage=historical_data["program"]["progress_percentage"]
            )
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error creating historical performance features for learner {learner_id}: {e}")
            raise
    
    def create_demographic_features(self, learner_id: str) -> Optional[DemographicFeatures]:
        """Create demographic features for a learner."""
        try:
            # Mock demographic data
            # In reality, this would come from user profiles with privacy considerations
            
            demographic_data = {
                "age": 23,
                "education": "bachelor_in_progress",
                "field_of_study": "computer_science",
                "experience": {
                    "years": 1.5,
                    "industries": ["technology", "education"],
                    "leadership": False
                },
                "geographic": {
                    "country": "US",
                    "region": "west",
                    "timezone": "PST"
                },
                "language": {
                    "native": "english",
                    "spoken": ["english", "spanish"]
                },
                "accessibility": ["visual_aids"],
                "learning": ["visual", "kinesthetic"]
            }
            
            features = DemographicFeatures(
                learner_id=learner_id,
                age=demographic_data["age"],
                education_level=demographic_data["education"],
                field_of_study=demographic_data["field_of_study"],
                years_of_experience=demographic_data["experience"]["years"],
                industry_experience=demographic_data["experience"]["industries"],
                leadership_experience=demographic_data["experience"]["leadership"],
                country=demographic_data["geographic"]["country"],
                region=demographic_data["geographic"]["region"],
                timezone=demographic_data["geographic"]["timezone"],
                native_language=demographic_data["language"]["native"],
                languages_spoken=demographic_data["language"]["spoken"],
                accessibility_needs=demographic_data["accessibility"],
                learning_preferences=demographic_data["learning"]
            )
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error creating demographic features for learner {learner_id}: {e}")
            # Demographic features are optional, so return None on error
            return None
    
    def create_behavioral_features(self, learner_id: str) -> Optional[BehavioralFeatures]:
        """Create behavioral features for a learner."""
        try:
            # Mock behavioral data
            # In reality, this would come from platform analytics
            
            behavioral_data = {
                "learning": {
                    "preferred_time": "morning",
                    "session_duration": 45.5,  # minutes
                    "break_frequency": 2.3  # breaks per hour
                },
                "content": {
                    "preferred_types": ["video", "interactive", "text"],
                    "difficulty": "intermediate",
                    "style": {
                        "visual": 0.85,
                        "auditory": 0.65,
                        "kinesthetic": 0.75
                    }
                },
                "social": {
                    "forum_participation": 0.72,
                    "peer_frequency": 3.2,  # interactions per week
                    "mentor_engagement": 0.68
                },
                "self_regulation": {
                    "goal_setting": 0.88,
                    "self_assessment": 1.5,  # per week
                    "help_seeking": 0.75
                },
                "motivation": {
                    "intrinsic": 0.82,
                    "extrinsic": 0.65,
                    "persistence": 0.90
                },
                "risk": {
                    "procrastination": ["deadline_pressure", "task_avoidance"],
                    "avoidance": ["difficult_topics", "group_work"],
                    "burnout": 0.25
                },
                "technology": {
                    "usage": {
                        "desktop": 0.70,
                        "mobile": 0.25,
                        "tablet": 0.05
                    },
                    "devices": ["laptop", "smartphone"],
                    "proficiency": 0.85
                }
            }
            
            features = BehavioralFeatures(
                learner_id=learner_id,
                preferred_learning_time=behavioral_data["learning"]["preferred_time"],
                learning_session_duration=behavioral_data["learning"]["session_duration"],
                break_frequency=behavioral_data["learning"]["break_frequency"],
                preferred_content_types=behavioral_data["content"]["preferred_types"],
                difficulty_preference=behavioral_data["content"]["difficulty"],
                learning_style_indicators=behavioral_data["content"]["style"],
                forum_participation=behavioral_data["social"]["forum_participation"],
                peer_interaction_frequency=behavioral_data["social"]["peer_frequency"],
                mentor_engagement=behavioral_data["social"]["mentor_engagement"],
                goal_setting_behavior=behavioral_data["self_regulation"]["goal_setting"],
                self_assessment_frequency=behavioral_data["self_regulation"]["self_assessment"],
                help_seeking_behavior=behavioral_data["self_regulation"]["help_seeking"],
                intrinsic_motivation_score=behavioral_data["motivation"]["intrinsic"],
                extrinsic_motivation_score=behavioral_data["motivation"]["extrinsic"],
                persistence_score=behavioral_data["motivation"]["persistence"],
                procrastination_indicators=behavioral_data["risk"]["procrastination"],
                avoidance_patterns=behavioral_data["risk"]["avoidance"],
                burnout_risk_score=behavioral_data["risk"]["burnout"],
                platform_usage_patterns=behavioral_data["technology"]["usage"],
                device_preferences=behavioral_data["technology"]["devices"],
                technical_proficiency=behavioral_data["technology"]["proficiency"]
            )
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error creating behavioral features for learner {learner_id}: {e}")
            # Behavioral features are optional, so return None on error
            return None
    
    def create_training_example(self, learner_id: str, target_data: Dict[str, Any]) -> TrainingExample:
        """Create a complete training example for a learner."""
        try:
            # Create all feature types
            compatibility_features = self.create_compatibility_features(
                learner_id, target_data.get("job_family", "technology")
            )
            historical_features = self.create_historical_performance_features(learner_id)
            demographic_features = self.create_demographic_features(learner_id)
            behavioral_features = self.create_behavioral_features(learner_id)
            
            # Create feature vector and names
            feature_vector, feature_names = self._create_feature_vector(
                compatibility_features, historical_features, 
                demographic_features, behavioral_features
            )
            
            # Calculate data quality score
            data_quality_score = self._calculate_data_quality_score(
                compatibility_features, historical_features,
                demographic_features, behavioral_features
            )
            
            # Create training example
            from ..models.feature_models import TargetVariable
            from ..models.prediction_models import PredictionTarget
            
            target = TargetVariable(
                learner_id=learner_id,
                target_type=PredictionTarget(target_data["target_type"]),
                target_value=target_data["target_value"],
                target_role=target_data.get("target_role"),
                time_horizon_days=target_data.get("time_horizon_days"),
                observation_date=target_data["observation_date"],
                outcome_date=target_data.get("outcome_date"),
                confidence_in_label=target_data.get("confidence_in_label", 1.0),
                label_source=target_data.get("label_source", "system"),
                contributing_factors=target_data.get("contributing_factors", [])
            )
            
            example = TrainingExample(
                learner_id=learner_id,
                compatibility_features=compatibility_features,
                historical_features=historical_features,
                demographic_features=demographic_features,
                behavioral_features=behavioral_features,
                target=target,
                feature_vector=feature_vector,
                feature_names=feature_names,
                data_quality_score=data_quality_score,
                missing_features=self._identify_missing_features(
                    compatibility_features, historical_features,
                    demographic_features, behavioral_features
                ),
                outlier_indicators=self._detect_feature_outliers(feature_vector, feature_names),
                snapshot_date=datetime.utcnow(),
                feature_freshness_days=self._calculate_feature_freshness(
                    compatibility_features, historical_features
                )
            )
            
            return example
            
        except Exception as e:
            self.logger.error(f"Error creating training example for learner {learner_id}: {e}")
            raise
    
    def _create_feature_vector(self, compatibility: CompatibilityFeatures, 
                              historical: HistoricalPerformanceFeatures,
                              demographic: Optional[DemographicFeatures],
                              behavioral: Optional[BehavioralFeatures]) -> Tuple[List[float], List[str]]:
        """Create flattened feature vector and feature names."""
        features = []
        feature_names = []
        
        # Compatibility features
        features.extend([
            compatibility.overall_compatibility_score,
            compatibility.compatibility_confidence,
            compatibility.knowledge_score,
            compatibility.skills_score,
            compatibility.abilities_score,
            compatibility.habits_score,
            compatibility.data_quality_score,
            compatibility.signal_freshness_score,
            compatibility.completeness_score,
            compatibility.total_signals,
            compatibility.knowledge_signals,
            compatibility.skills_signals,
            compatibility.abilities_signals,
            compatibility.habits_signals,
            compatibility.missing_signals_count,
            compatibility.stale_signals_count,
            compatibility.signal_age_days
        ])
        
        feature_names.extend([
            "overall_compatibility_score",
            "compatibility_confidence",
            "knowledge_score",
            "skills_score",
            "abilities_score",
            "habits_score",
            "data_quality_score",
            "signal_freshness_score",
            "completeness_score",
            "total_signals",
            "knowledge_signals",
            "skills_signals",
            "abilities_signals",
            "habits_signals",
            "missing_signals_count",
            "stale_signals_count",
            "signal_age_days"
        ])
        
        # Historical performance features
        features.extend([
            np.mean(historical.gpa_trend) if historical.gpa_trend else 0,
            historical.course_completion_rate,
            historical.average_grade or 0,
            historical.grade_improvement_trend or 0,
            np.mean(historical.skills_assessment_scores) if historical.skills_assessment_scores else 0,
            historical.skills_improvement_rate,
            historical.mastery_level_achieved,
            historical.project_success_rate,
            np.mean(historical.project_complexity_trend) if historical.project_complexity_trend else 0,
            historical.collaboration_score or 0,
            historical.login_frequency,
            historical.time_spent_learning,
            historical.interaction_level,
            historical.peer_engagement_score or 0,
            historical.skill_acquisition_rate,
            historical.learning_velocity,
            historical.milestone_completion_rate,
            historical.learning_consistency,
            historical.dropout_risk_score,
            historical.days_in_program,
            historical.progress_percentage
        ])
        
        feature_names.extend([
            "avg_gpa",
            "course_completion_rate",
            "average_grade",
            "grade_improvement_trend",
            "avg_skills_score",
            "skills_improvement_rate",
            "mastery_level_achieved",
            "project_success_rate",
            "avg_project_complexity",
            "collaboration_score",
            "login_frequency",
            "time_spent_learning",
            "interaction_level",
            "peer_engagement_score",
            "skill_acquisition_rate",
            "learning_velocity",
            "milestone_completion_rate",
            "learning_consistency",
            "dropout_risk_score",
            "days_in_program",
            "progress_percentage"
        ])
        
        # Demographic features (if available)
        if demographic:
            features.extend([
                demographic.age or 0,
                1 if demographic.years_of_experience and demographic.years_of_experience > 0 else 0,
                1 if demographic.leadership_experience else 0,
                len(demographic.industry_experience) if demographic.industry_experience else 0,
                len(demographic.languages_spoken) if demographic.languages_spoken else 0
            ])
            
            feature_names.extend([
                "age",
                "has_experience",
                "has_leadership_experience",
                "industry_count",
                "language_count"
            ])
        
        # Behavioral features (if available)
        if behavioral:
            features.extend([
                behavioral.learning_session_duration,
                behavioral.break_frequency,
                behavioral.forum_participation,
                behavioral.peer_interaction_frequency,
                behavioral.mentor_engagement,
                behavioral.goal_setting_behavior,
                behavioral.self_assessment_frequency,
                behavioral.help_seeking_behavior,
                behavioral.intrinsic_motivation_score,
                behavioral.extrinsic_motivation_score,
                behavioral.persistence_score,
                behavioral.burnout_risk_score,
                behavioral.technical_proficiency
            ])
            
            feature_names.extend([
                "session_duration",
                "break_frequency",
                "forum_participation",
                "peer_interaction_frequency",
                "mentor_engagement",
                "goal_setting",
                "self_assessment_frequency",
                "help_seeking",
                "intrinsic_motivation",
                "extrinsic_motivation",
                "persistence",
                "burnout_risk",
                "technical_proficiency"
            ])
        
        return features, feature_names
    
    def _calculate_data_quality_score(self, compatibility: CompatibilityFeatures,
                                     historical: HistoricalPerformanceFeatures,
                                     demographic: Optional[DemographicFeatures],
                                     behavioral: Optional[BehavioralFeatures]) -> float:
        """Calculate overall data quality score for a training example."""
        quality_scores = []
        
        # Compatibility quality
        quality_scores.append(compatibility.data_quality_score)
        
        # Historical quality (based on completeness)
        # Use dropout risk as inverse quality indicator
        historical_completeness = 1.0 - historical.dropout_risk_score
        quality_scores.append(historical_completeness)
        
        # Demographic quality (if available)
        if demographic:
            demographic_quality = 0.9  # High quality if present
            quality_scores.append(demographic_quality)
        
        # Behavioral quality (if available)
        if behavioral:
            behavioral_quality = 0.85  # Good quality if present
            quality_scores.append(behavioral_quality)
        
        return np.mean(quality_scores) if quality_scores else 0.0
    
    def _identify_missing_features(self, compatibility: CompatibilityFeatures,
                                  historical: HistoricalPerformanceFeatures,
                                  demographic: Optional[DemographicFeatures],
                                  behavioral: Optional[BehavioralFeatures]) -> List[str]:
        """Identify missing features in the training example."""
        missing_features = []
        
        # Check for missing demographic features
        if demographic is None:
            missing_features.extend(["demographic_features"])
        
        # Check for missing behavioral features
        if behavioral is None:
            missing_features.extend(["behavioral_features"])
        
        # Check for specific missing values
        if not historical.average_grade:
            missing_features.append("average_grade")
        
        if not historical.collaboration_score:
            missing_features.append("collaboration_score")
        
        return missing_features
    
    def _detect_feature_outliers(self, feature_vector: List[float], feature_names: List[str]) -> List[str]:
        """Detect outliers in the feature vector."""
        outliers = []
        
        if len(feature_vector) != len(feature_names):
            return outliers
        
        try:
            # Use IQR method for outlier detection
            feature_array = np.array(feature_vector)
            
            for i, (value, name) in enumerate(zip(feature_vector, feature_names)):
                if np.isnan(value) or np.isinf(value):
                    outliers.append(f"{name}_invalid")
                    continue
                
                # Calculate IQR for this feature across all examples
                # For now, use simple threshold-based detection
                if value > 3.0 or value < -3.0:  # Assuming normalized features
                    outliers.append(f"{name}_outlier")
                
        except Exception as e:
            self.logger.warning(f"Error detecting outliers: {e}")
        
        return outliers
    
    def _calculate_feature_freshness(self, compatibility: CompatibilityFeatures,
                                    historical: HistoricalPerformanceFeatures) -> Dict[str, int]:
        """Calculate freshness of features in days."""
        freshness = {}
        
        # Compatibility freshness
        freshness["compatibility"] = compatibility.signal_age_days
        
        # Historical freshness (based on last update)
        freshness["historical"] = 7  # Assume updated weekly
        
        return freshness
    
    # Feature engineering step implementations
    def _normalize_compatibility_scores(self, features: pd.DataFrame) -> pd.DataFrame:
        """Normalize compatibility scores to 0-1 range."""
        compatibility_cols = [col for col in features.columns if 'compatibility' in col or 'score' in col]
        
        for col in compatibility_cols:
            if col in features.columns:
                min_val = features[col].min()
                max_val = features[col].max()
                if max_val > min_val:
                    features[col] = (features[col] - min_val) / (max_val - min_val)
        
        return features
    
    def _calculate_domain_ratios(self, features: pd.DataFrame) -> pd.DataFrame:
        """Calculate ratios between different domain scores."""
        if all(col in features.columns for col in ['knowledge_score', 'skills_score', 'abilities_score', 'habits_score']):
            features['knowledge_to_skills_ratio'] = features['knowledge_score'] / (features['skills_score'] + 1e-8)
            features['abilities_to_habits_ratio'] = features['abilities_score'] / (features['habits_score'] + 1e-8)
            features['overall_balance_score'] = 1.0 - features[['knowledge_score', 'skills_score', 'abilities_score', 'habits_score']].std(axis=1)
        
        return features
    
    def _create_trend_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Create trend-based features from temporal data."""
        # This would analyze trends in GPA, skills scores, etc.
        # For now, placeholder implementation
        return features
    
    def _calculate_interaction_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Calculate interaction features between important variables."""
        if 'overall_compatibility_score' in features.columns and 'learning_velocity' in features.columns:
            features['compatibility_learning_interaction'] = (
                features['overall_compatibility_score'] * features['learning_velocity']
            )
        
        return features
    
    def _create_polynomial_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Create polynomial features for non-linear relationships."""
        important_cols = ['overall_compatibility_score', 'learning_velocity', 'dropout_risk_score']
        
        for col in important_cols:
            if col in features.columns:
                features[f'{col}_squared'] = features[col] ** 2
                features[f'{col}_cubed'] = features[col] ** 3
        
        return features
    
    def _calculate_aggregation_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Calculate aggregated features."""
        score_cols = [col for col in features.columns if 'score' in col and col.endswith('_score')]
        
        if score_cols:
            features['avg_all_scores'] = features[score_cols].mean(axis=1)
            features['max_all_scores'] = features[score_cols].max(axis=1)
            features['min_all_scores'] = features[score_cols].min(axis=1)
            features['score_variance'] = features[score_cols].var(axis=1)
        
        return features
    
    def _encode_categorical_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical features."""
        categorical_cols = features.select_dtypes(include=['object', 'category']).columns
        
        for col in categorical_cols:
            if col in features.columns and features[col].nunique() < 20:  # Only encode low-cardinality features
                features = pd.get_dummies(features, columns=[col], prefix=col)
        
        return features
    
    def _handle_missing_values(self, features: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in features."""
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if features[col].isnull().sum() > 0:
                # Use median for numeric features
                features[col].fillna(features[col].median(), inplace=True)
        
        return features
    
    def _detect_outliers(self, features: pd.DataFrame) -> pd.DataFrame:
        """Detect and handle outliers."""
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col in features.columns:
                Q1 = features[col].quantile(0.25)
                Q3 = features[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Cap outliers instead of removing them
                features[col] = features[col].clip(lower_bound, upper_bound)
        
        return features
    
    def _scale_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Scale features to standard range."""
        from sklearn.preprocessing import StandardScaler
        
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        
        scaler = StandardScaler()
        features[numeric_cols] = scaler.fit_transform(features[numeric_cols])
        
        return features
    
    def apply_feature_engineering_pipeline(self, features: pd.DataFrame, 
                                         pipeline_steps: List[str]) -> pd.DataFrame:
        """Apply a series of feature engineering steps."""
        engineered_features = features.copy()
        
        for step_name in pipeline_steps:
            if step_name in self.engineering_steps:
                try:
                    engineered_features = self.engineering_steps[step_name](engineered_features)
                    self.logger.info(f"Applied feature engineering step: {step_name}")
                except Exception as e:
                    self.logger.error(f"Error applying feature engineering step {step_name}: {e}")
                    raise
            else:
                self.logger.warning(f"Unknown feature engineering step: {step_name}")
        
        return engineered_features
    
    def register_feature_definition(self, feature_def: FeatureDefinition):
        """Register a new feature definition."""
        # Check if feature already exists
        existing_features = [f for f in self.feature_store.feature_definitions if f.feature_name == feature_def.feature_name]
        
        if existing_features:
            # Update existing feature
            for i, existing in enumerate(self.feature_store.feature_definitions):
                if existing.feature_name == feature_def.feature_name:
                    self.feature_store.feature_definitions[i] = feature_def
                    break
        else:
            # Add new feature
            self.feature_store.feature_definitions.append(feature_def)
        
        # Update active features list
        if feature_def.is_active and feature_def.feature_name not in self.feature_store.active_features:
            self.feature_store.active_features.append(feature_def.feature_name)
        
        # Save updated feature store
        self._save_feature_store(self.feature_store)
        
        self.logger.info(f"Registered feature definition: {feature_def.feature_name}")
    
    def get_feature_store(self) -> FeatureStore:
        """Get the current feature store."""
        return self.feature_store
    
    def refresh_feature_statistics(self):
        """Refresh statistics for all features in the store."""
        # This would typically involve querying the actual data
        # For now, it's a placeholder implementation
        self.logger.info("Feature statistics refresh completed")
