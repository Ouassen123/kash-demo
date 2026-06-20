"""Explainability service with SHAP integration for KASH models."""

import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

# Optional SHAP import
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

from ..models.explanation_models import (
    ExplanationMetadata, ExplanationSnapshot, StandardizedExplanation,
    ExplanationComparison, FeatureContribution, ExplanationType,
    ExplanationScope, ContributionDirection, ConfidenceLevel,
    ExplainabilityConfig, QAQuery, QAQueryResult
)


class ExplainabilityService:
    """Service for generating and managing model explanations."""
    
    def __init__(self, config: Optional[ExplainabilityConfig] = None, 
                 cache_path: Optional[Path] = None):
        self.config = config or ExplainabilityConfig()
        self.cache_path = cache_path or Path(__file__).parent.parent / "data" / "explanation_cache"
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize services (lazy loading to avoid circular imports)
        self._scoring_pipeline = None
        self._ml_service = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Cache for explanations
        self.explanation_cache = {}
        self._load_cache()
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        
        # Background datasets for SHAP
        self.background_datasets = {}
        self._prepare_background_datasets()
        
        self.logger.info("Explainability service initialized")
    
    @property
    def scoring_pipeline(self):
        """Lazy loading of scoring pipeline."""
        if self._scoring_pipeline is None:
            try:
                from ...compatibility.services.scoring_pipeline import ScoringPipeline
                self._scoring_pipeline = ScoringPipeline()
            except ImportError:
                self.logger.warning("Could not import ScoringPipeline, using fallback")
                self._scoring_pipeline = None
        return self._scoring_pipeline
    
    @property
    def ml_service(self):
        """Lazy loading of ML service."""
        if self._ml_service is None:
            try:
                from ...predictive_model.services.ml_service import PredictiveModelService
                self._ml_service = PredictiveModelService()
            except ImportError:
                self.logger.warning("Could not import PredictiveModelService, using fallback")
                self._ml_service = None
        return self._ml_service
    
    def _load_cache(self):
        """Load explanation cache from storage."""
        cache_file = self.cache_path / "explanations.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    for exp_id, exp_data in cache_data.items():
                        # Convert datetime strings back
                        for field in ['generated_at', 'created_at', 'updated_at']:
                            if exp_data.get(field):
                                exp_data[field] = datetime.fromisoformat(exp_data[field])
                        
                        # Reconstruct ExplanationSnapshot
                        if 'explanation_metadata' in exp_data:
                            metadata = ExplanationMetadata(**exp_data['explanation_metadata'])
                            exp_data['explanation_metadata'] = metadata
                        
                        self.explanation_cache[exp_id] = exp_data
                
                self.logger.info(f"Loaded {len(self.explanation_cache)} explanations from cache")
            except Exception as e:
                self.logger.error(f"Error loading cache: {e}")
                self.explanation_cache = {}
    
    def _save_cache(self):
        """Save explanation cache to storage."""
        try:
            cache_file = self.cache_path / "explanations.json"
            cache_data = {}
            
            for exp_id, exp_data in self.explanation_cache.items():
                # Convert to serializable format
                serializable_data = exp_data.copy()
                if 'explanation_metadata' in serializable_data:
                    metadata = serializable_data['explanation_metadata']
                    if hasattr(metadata, 'model_dump'):
                        serializable_data['explanation_metadata'] = metadata.model_dump()
                
                cache_data[exp_id] = serializable_data
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2, default=str)
            
            self.logger.info(f"Saved {len(self.explanation_cache)} explanations to cache")
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")
    
    def _prepare_background_datasets(self):
        """Prepare background datasets for SHAP explanations."""
        try:
            # Create synthetic background data for compatibility models
            self.background_datasets['compatibility'] = self._generate_compatibility_background()
            
            # Create synthetic background data for predictive models
            self.background_datasets['predictive'] = self._generate_predictive_background()
            
            self.logger.info("Background datasets prepared for SHAP explanations")
        except Exception as e:
            self.logger.error(f"Error preparing background datasets: {e}")
    
    def _generate_compatibility_background(self) -> pd.DataFrame:
        """Generate background dataset for compatibility model explanations."""
        # Create synthetic background data
        np.random.seed(42)
        n_samples = self.config.shap_background_size
        
        background_data = {
            'knowledge_score': np.random.uniform(0, 1, n_samples),
            'skills_score': np.random.uniform(0, 1, n_samples),
            'abilities_score': np.random.uniform(0, 1, n_samples),
            'habits_score': np.random.uniform(0, 1, n_samples),
            'data_quality_score': np.random.uniform(0.5, 1, n_samples),
            'signal_freshness_score': np.random.uniform(0.5, 1, n_samples),
            'completeness_score': np.random.uniform(0.5, 1, n_samples),
            'total_signals': np.random.randint(5, 20, n_samples),
            'missing_signals_count': np.random.randint(0, 5, n_samples),
            'stale_signals_count': np.random.randint(0, 3, n_samples),
            'signal_age_days': np.random.randint(1, 30, n_samples)
        }
        
        return pd.DataFrame(background_data)
    
    def _generate_predictive_background(self) -> pd.DataFrame:
        """Generate background dataset for predictive model explanations."""
        # Create synthetic background data with 56 features
        np.random.seed(42)
        n_samples = self.config.shap_background_size
        n_features = 56
        
        feature_names = [f"feature_{i}" for i in range(n_features)]
        background_data = {}
        
        for i, name in enumerate(feature_names):
            if i < 17:  # Compatibility features
                background_data[name] = np.random.uniform(0, 1, n_samples)
            elif i < 38:  # Historical features
                background_data[name] = np.random.uniform(0, 1, n_samples)
            else:  # Demographic/behavioral features
                background_data[name] = np.random.uniform(0, 1, n_samples)
        
        return pd.DataFrame(background_data)
    
    def explain_compatibility_score(self, learner_id: str, job_family: str,
                                  include_recommendations: bool = True) -> StandardizedExplanation:
        """Generate explanation for compatibility score using SHAP."""
        try:
            if not SHAP_AVAILABLE:
                return self._create_fallback_explanation(
                    learner_id, "compatibility", "SHAP not available"
                )
            
            # Check if scoring pipeline is available
            if self.scoring_pipeline is None:
                return self._create_fallback_explanation(
                    learner_id, "compatibility", "Scoring pipeline not available"
                )
            
            # Get compatibility score and features
            compatibility_features = self._get_compatibility_features(learner_id, job_family)
            score_result = self.scoring_pipeline.calculate_compatibility_score(
                learner_id, job_family, compatibility_features
            )
            
            # Prepare feature vector for SHAP
            feature_vector = self._compatibility_features_to_vector(compatibility_features)
            feature_names = self._get_compatibility_feature_names()
            
            # Get or create SHAP explainer
            explainer = self._get_compatibility_explainer()
            
            # Generate SHAP values
            shap_values = explainer.shap_values(pd.DataFrame([feature_vector], columns=feature_names))
            
            # Create explanation
            explanation = self._create_standardized_explanation(
                explanation_type=ExplanationType.SHAP,
                explanation_scope=ExplanationScope.LOCAL,
                prediction_value=score_result.overall_score,
                feature_names=feature_names,
                feature_values=feature_vector,
                shap_values=shap_values[0] if isinstance(shap_values, list) else shap_values,
                base_value=explainer.expected_value,
                learner_id=learner_id,
                model_info={
                    "model_type": "compatibility",
                    "model_id": "compatibility_pipeline",
                    "job_family": job_family
                },
                generation_info={
                    "method": "shap",
                    "background_size": len(self.background_datasets['compatibility']),
                    "computation_time_ms": None  # Will be set below
                }
            )
            
            # Add recommendations if requested
            if include_recommendations:
                explanation.actionable_recommendations = self._generate_compatibility_recommendations(
                    explanation.feature_contributions, score_result
                )
            
            # Cache the explanation
            self._cache_explanation(explanation, learner_id, "compatibility", job_family)
            
            self.logger.info(f"Generated compatibility explanation for learner {learner_id}")
            return explanation
            
        except Exception as e:
            self.logger.error(f"Error generating compatibility explanation: {e}")
            return self._create_fallback_explanation(
                learner_id, "compatibility", f"Error: {str(e)}"
            )
    
    def explain_prediction(self, model_id: str, feature_vector: List[float],
                          feature_names: List[str], learner_id: Optional[str] = None,
                          include_recommendations: bool = True) -> StandardizedExplanation:
        """Generate explanation for predictive model using SHAP."""
        try:
            if not SHAP_AVAILABLE:
                return self._create_fallback_explanation(
                    learner_id or "unknown", "predictive", "SHAP not available"
                )
            
            # Check if ML service is available
            if self.ml_service is None:
                return self._create_fallback_explanation(
                    learner_id or "unknown", "predictive", "ML service not available"
                )
            
            # Get model and prediction
            model_metadata = self.ml_service.get_model(model_id)
            if not model_metadata:
                raise ValueError(f"Model {model_id} not found")
            
            # Load model
            model_path = self.ml_service.model_registry_path / f"{model_id}.pkl"
            import joblib
            model = joblib.load(model_path)
            
            # Make prediction
            prediction = model.predict([feature_vector])[0]
            
            # Get or create SHAP explainer
            explainer = self._get_predictive_explainer(model, model_metadata)
            
            # Generate SHAP values
            shap_values = explainer.shap_values(pd.DataFrame([feature_vector], columns=feature_names))
            
            # Create explanation
            explanation = self._create_standardized_explanation(
                explanation_type=ExplanationType.SHAP,
                explanation_scope=ExplanationScope.LOCAL,
                prediction_value=float(prediction),
                feature_names=feature_names,
                feature_values=feature_vector,
                shap_values=shap_values[0] if isinstance(shap_values, list) else shap_values,
                base_value=explainer.expected_value,
                learner_id=learner_id,
                model_info={
                    "model_type": "predictive",
                    "model_id": model_id,
                    "algorithm": model_metadata.algorithm,
                    "prediction_target": model_metadata.prediction_target.value
                },
                generation_info={
                    "method": "shap",
                    "background_size": len(self.background_datasets['predictive']),
                    "computation_time_ms": None
                }
            )
            
            # Add recommendations if requested
            if include_recommendations:
                explanation.actionable_recommendations = self._generate_predictive_recommendations(
                    explanation.feature_contributions, prediction
                )
            
            # Cache the explanation
            self._cache_explanation(explanation, learner_id, "predictive", model_id)
            
            self.logger.info(f"Generated prediction explanation for model {model_id}")
            return explanation
            
        except Exception as e:
            self.logger.error(f"Error generating prediction explanation: {e}")
            return self._create_fallback_explanation(
                learner_id or "unknown", "predictive", f"Error: {str(e)}"
            )
    
    def _get_compatibility_features(self, learner_id: str, job_family: str):
        """Get compatibility features for a learner."""
        from ...predictive_model.services.feature_engineering import FeatureEngineeringService
        
        feature_service = FeatureEngineeringService()
        return feature_service.create_compatibility_features(learner_id, job_family)
    
    def _compatibility_features_to_vector(self, features) -> List[float]:
        """Convert compatibility features to vector format."""
        return [
            features.overall_compatibility_score,
            features.compatibility_confidence,
            features.knowledge_score,
            features.skills_score,
            features.abilities_score,
            features.habits_score,
            features.data_quality_score,
            features.signal_freshness_score,
            features.completeness_score,
            features.total_signals,
            features.knowledge_signals,
            features.skills_signals,
            features.abilities_signals,
            features.habits_signals,
            features.missing_signals_count,
            features.stale_signals_count,
            features.signal_age_days
        ]
    
    def _get_compatibility_feature_names(self) -> List[str]:
        """Get compatibility feature names."""
        return [
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
        ]
    
    def _get_compatibility_explainer(self):
        """Get or create SHAP explainer for compatibility model."""
        if 'compatibility_explainer' not in self.background_datasets:
            # Create a simple linear model explainer for compatibility
            background = self.background_datasets['compatibility']
            
            # Use KernelExplainer as a model-agnostic approach
            def compatibility_model(features):
                # Simple compatibility model for explanation
                weights = np.array([0.3, 0.1, 0.2, 0.2, 0.1, 0.05, 0.02, 0.01, 0.01, 0.01])
                return np.dot(features.iloc[:, :len(weights)].values, weights)
            
            explainer = shap.KernelExplainer(compatibility_model, background)
            self.background_datasets['compatibility_explainer'] = explainer
        
        return self.background_datasets['compatibility_explainer']
    
    def _get_predictive_explainer(self, model, model_metadata):
        """Get or create SHAP explainer for predictive model."""
        explainer_key = f"{model_metadata.model_id}_explainer"
        
        if explainer_key not in self.background_datasets:
            background = self.background_datasets['predictive']
            
            # Choose explainer based on model type
            if hasattr(model, 'feature_importances_'):
                # Tree-based model
                explainer = shap.TreeExplainer(model, background)
            elif hasattr(model, 'coef_'):
                # Linear model
                explainer = shap.LinearExplainer(model, background)
            else:
                # Model-agnostic
                explainer = shap.KernelExplainer(model.predict, background)
            
            self.background_datasets[explainer_key] = explainer
        
        return self.background_datasets[explainer_key]
    
    def _create_standardized_explanation(self, explanation_type: ExplanationType,
                                        explanation_scope: ExplanationScope,
                                        prediction_value: float,
                                        feature_names: List[str],
                                        feature_values: List[float],
                                        shap_values: np.ndarray,
                                        base_value: Optional[float],
                                        learner_id: Optional[str],
                                        model_info: Dict[str, str],
                                        generation_info: Dict[str, Any]) -> StandardizedExplanation:
        """Create standardized explanation from SHAP values."""
        
        # Create feature contributions
        feature_contributions = []
        total_abs_shap = np.sum(np.abs(shap_values))
        
        for i, (name, value, shap_val) in enumerate(zip(feature_names, feature_values, shap_values)):
            if total_abs_shap > 0:
                contribution_percentage = abs(shap_val) / total_abs_shap
            else:
                contribution_percentage = 0.0
            
            direction = ContributionDirection.POSITIVE if shap_val > 0 else ContributionDirection.NEGATIVE
            
            contribution = FeatureContribution(
                feature_name=name,
                feature_value=value,
                contribution_score=float(shap_val),
                contribution_direction=direction,
                contribution_percentage=contribution_percentage,
                feature_type=self._classify_feature_type(name),
                importance_rank=i + 1,
                baseline_value=base_value
            )
            feature_contributions.append(contribution)
        
        # Sort by contribution magnitude
        feature_contributions.sort(key=lambda x: abs(x.contribution_score), reverse=True)
        
        # Update importance ranks
        for i, contribution in enumerate(feature_contributions):
            contribution.importance_rank = i + 1
        
        # Separate positive and negative factors
        positive_factors = [f for f in feature_contributions if f.contribution_direction == ContributionDirection.POSITIVE]
        negative_factors = [f for f in feature_contributions if f.contribution_direction == ContributionDirection.NEGATIVE]
        
        # Generate key insights
        key_insights = self._generate_key_insights(feature_contributions, prediction_value)
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(feature_contributions)
        
        # Create explanation
        explanation = StandardizedExplanation(
            explanation_id=str(uuid.uuid4()),
            explanation_type=explanation_type,
            explanation_scope=explanation_scope,
            prediction_value=prediction_value,
            base_value=base_value,
            feature_contributions=feature_contributions,
            top_positive_factors=positive_factors[:5],
            top_negative_factors=negative_factors[:5],
            key_insights=key_insights,
            confidence_level=confidence_level,
            learner_id=learner_id,
            model_info=model_info,
            generation_info=generation_info,
            technical_metadata={
                "shap_values": shap_values.tolist(),
                "feature_values": feature_values,
                "base_value": base_value
            }
        )
        
        return explanation
    
    def _classify_feature_type(self, feature_name: str) -> str:
        """Classify feature type based on name."""
        if any(keyword in feature_name.lower() for keyword in ['compatibility', 'score']):
            return 'compatibility_score'
        elif any(keyword in feature_name.lower() for keyword in ['gpa', 'grade', 'completion', 'performance']):
            return 'historical_performance'
        elif any(keyword in feature_name.lower() for keyword in ['age', 'education', 'experience']):
            return 'demographic'
        else:
            return 'behavioral'
    
    def _generate_key_insights(self, contributions: List[FeatureContribution], 
                             prediction_value: float) -> List[str]:
        """Generate key insights from feature contributions."""
        insights = []
        
        if not contributions:
            return ["No feature contributions available"]
        
        # Top contributors
        top_contributor = contributions[0]
        insights.append(f"Top contributor: {top_contributor.feature_name} ({top_contributor.contribution_direction.value})")
        
        # Overall assessment
        positive_sum = sum(c.contribution_score for c in contributions if c.contribution_direction == ContributionDirection.POSITIVE)
        negative_sum = sum(c.contribution_score for c in contributions if c.contribution_direction == ContributionDirection.NEGATIVE)
        
        if abs(positive_sum) > abs(negative_sum):
            insights.append("Overall prediction driven by positive factors")
        else:
            insights.append("Overall prediction driven by negative factors")
        
        # Prediction level
        if prediction_value > 0.8:
            insights.append("Very high prediction score")
        elif prediction_value > 0.6:
            insights.append("High prediction score")
        elif prediction_value > 0.4:
            insights.append("Moderate prediction score")
        else:
            insights.append("Low prediction score")
        
        return insights
    
    def _determine_confidence_level(self, contributions: List[FeatureContribution]) -> ConfidenceLevel:
        """Determine confidence level based on feature contributions."""
        if not contributions:
            return ConfidenceLevel.VERY_LOW
        
        # Calculate concentration of contributions
        total_contribution = sum(abs(c.contribution_score) for c in contributions)
        if total_contribution == 0:
            return ConfidenceLevel.VERY_LOW
        
        top_3_contribution = sum(abs(c.contribution_score) for c in contributions[:3])
        concentration = top_3_contribution / total_contribution
        
        if concentration > 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif concentration > 0.6:
            return ConfidenceLevel.HIGH
        elif concentration > 0.4:
            return ConfidenceLevel.MEDIUM
        elif concentration > 0.2:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _generate_compatibility_recommendations(self, contributions: List[FeatureContribution],
                                              score_result) -> List[str]:
        """Generate recommendations based on compatibility explanation."""
        recommendations = []
        
        # Find negative contributors
        negative_factors = [c for c in contributions if c.contribution_direction == ContributionDirection.NEGATIVE]
        
        for factor in negative_factors[:3]:  # Top 3 negative factors
            if 'knowledge' in factor.feature_name.lower():
                recommendations.append("Focus on improving knowledge domain through targeted learning")
            elif 'skills' in factor.feature_name.lower():
                recommendations.append("Develop practical skills through hands-on projects")
            elif 'abilities' in factor.feature_name.lower():
                recommendations.append("Strengthen core abilities through practice and feedback")
            elif 'habits' in factor.feature_name.lower():
                recommendations.append("Build consistent learning habits and study routines")
            elif 'quality' in factor.feature_name.lower():
                recommendations.append("Ensure data quality and completeness in assessments")
        
        # Overall recommendations
        if score_result.overall_score < 0.6:
            recommendations.append("Consider additional training or skill development")
        elif score_result.overall_score > 0.8:
            recommendations.append("Maintain current performance and seek advancement opportunities")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _generate_predictive_recommendations(self, contributions: List[FeatureContribution],
                                           prediction_value: float) -> List[str]:
        """Generate recommendations based on prediction explanation."""
        recommendations = []
        
        # Find negative contributors
        negative_factors = [c for c in contributions if c.contribution_direction == ContributionDirection.NEGATIVE]
        
        for factor in negative_factors[:3]:
            if 'learning' in factor.feature_name.lower() or 'velocity' in factor.feature_name.lower():
                recommendations.append("Improve learning pace and consistency")
            elif 'engagement' in factor.feature_name.lower():
                recommendations.append("Increase engagement with learning activities")
            elif 'performance' in factor.feature_name.lower():
                recommendations.append("Focus on improving academic performance")
            elif 'quality' in factor.feature_name.lower():
                recommendations.append("Ensure high-quality data and assessments")
        
        # Prediction-based recommendations
        if prediction_value < 0.3:
            recommendations.append("Consider intensive support and intervention")
        elif prediction_value > 0.8:
            recommendations.append("Ready for advanced challenges and leadership roles")
        
        return recommendations[:5]
    
    def _create_fallback_explanation(self, learner_id: str, model_type: str, 
                                   reason: str) -> StandardizedExplanation:
        """Create fallback explanation when SHAP is not available."""
        return StandardizedExplanation(
            explanation_id=str(uuid.uuid4()),
            explanation_type=ExplanationType.FEATURE_IMPORTANCE,
            explanation_scope=ExplanationScope.LOCAL,
            prediction_value=0.5,
            feature_contributions=[],
            top_positive_factors=[],
            top_negative_factors=[],
            key_insights=[f"Explanation unavailable: {reason}"],
            confidence_level=ConfidenceLevel.VERY_LOW,
            learner_id=learner_id,
            model_info={"model_type": model_type, "status": "fallback"},
            generation_info={"method": "fallback", "reason": reason}
        )
    
    def _cache_explanation(self, explanation: StandardizedExplanation, learner_id: str,
                          model_type: str, model_id: str):
        """Cache explanation for future reference."""
        if not self.config.cache_enabled:
            return
        
        # Create snapshot
        snapshot = ExplanationSnapshot(
            explanation_metadata=ExplanationMetadata(
                explanation_type=explanation.explanation_type,
                explanation_scope=explanation.explanation_scope,
                model_id=model_id,
                model_version="1.0",
                model_type=model_type,
                generated_by="explainability_service",
                feature_count=len(explanation.feature_contributions),
                feature_list=[f.feature_name for f in explanation.feature_contributions],
                confidence_level=explanation.confidence_level
            ),
            learner_id=learner_id,
            target_role=model_id if model_type == "compatibility" else None,
            input_features={f.feature_name: f.feature_value for f in explanation.feature_contributions if f.feature_value is not None},
            prediction_value=explanation.prediction_value,
            feature_contributions=explanation.feature_contributions,
            base_value=explanation.base_value,
            total_contribution=sum(f.contribution_score for f in explanation.feature_contributions)
        )
        
        # Add to cache
        self.explanation_cache[explanation.explanation_id] = snapshot.model_dump()
        
        # Save cache periodically
        if len(self.explanation_cache) % 100 == 0:
            self._save_cache()
    
    def get_cached_explanation(self, explanation_id: str) -> Optional[ExplanationSnapshot]:
        """Get cached explanation by ID."""
        if explanation_id in self.explanation_cache:
            data = self.explanation_cache[explanation_id]
            return ExplanationSnapshot(**data)
        return None
    
    def query_explanations(self, query: QAQuery) -> QAQueryResult:
        """Query explanations with filters and pagination."""
        try:
            start_time = datetime.utcnow()
            
            # Filter explanations
            filtered_explanations = []
            
            for exp_data in self.explanation_cache.values():
                # Apply filters
                if query.learner_id and exp_data.get('learner_id') != query.learner_id:
                    continue
                
                if query.model_id and exp_data.get('explanation_metadata', {}).get('model_id') != query.model_id:
                    continue
                
                # Date range filter
                if query.date_range:
                    exp_date = exp_data.get('created_at')
                    if isinstance(exp_date, str):
                        exp_date = datetime.fromisoformat(exp_date)
                    
                    if exp_date < query.date_range.get('start') or exp_date > query.date_range.get('end'):
                        continue
                
                filtered_explanations.append(ExplanationSnapshot(**exp_data))
            
            # Sort results
            reverse_order = query.sort_order.lower() == 'desc'
            if query.sort_by == 'generated_at':
                filtered_explanations.sort(key=lambda x: x.created_at, reverse=reverse_order)
            elif query.sort_by == 'quality_score':
                filtered_explanations.sort(key=lambda x: x.explanation_metadata.explanation_quality_score or 0, reverse=reverse_order)
            
            # Apply pagination
            total_count = len(filtered_explanations)
            start_idx = query.offset
            end_idx = start_idx + query.limit
            paginated_explanations = filtered_explanations[start_idx:end_idx]
            
            # Calculate statistics
            quality_scores = [exp.explanation_metadata.explanation_quality_score for exp in paginated_explanations 
                            if exp.explanation_metadata.explanation_quality_score is not None]
            avg_quality = np.mean(quality_scores) if quality_scores else None
            
            quality_dist = {}
            for exp in paginated_explanations:
                level = exp.explanation_metadata.confidence_level.value
                quality_dist[level] = quality_dist.get(level, 0) + 1
            
            # Calculate query time
            query_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return QAQueryResult(
                query_id=query.query_id,
                result_type="explanation_query",
                explanations=paginated_explanations,
                total_explanations=total_count,
                average_quality_score=avg_quality,
                quality_distribution=quality_dist,
                query_time_ms=query_time,
                cache_hit=False,
                processed_at=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error querying explanations: {e}")
            return QAQueryResult(
                query_id=query.query_id,
                result_type="error",
                query_time_ms=0,
                processed_at=datetime.utcnow()
            )
    
    def compare_explanations(self, explanation_1_id: str, explanation_2_id: str,
                           comparison_reason: str, compared_by: str) -> ExplanationComparison:
        """Compare two explanations."""
        try:
            # Get explanations
            exp1 = self.get_cached_explanation(explanation_1_id)
            exp2 = self.get_cached_explanation(explanation_2_id)
            
            if not exp1 or not exp2:
                raise ValueError("One or both explanations not found")
            
            # Analyze changes
            feature_changes = []
            exp1_contributions = {f.feature_name: f.contribution_score for f in exp1.feature_contributions}
            exp2_contributions = {f.feature_name: f.contribution_score for f in exp2.feature_contributions}
            
            all_features = set(exp1_contributions.keys()) | set(exp2_contributions.keys())
            
            for feature in all_features:
                contrib1 = exp1_contributions.get(feature, 0)
                contrib2 = exp2_contributions.get(feature, 0)
                
                if abs(contrib2 - contrib1) > 0.01:  # Significant change
                    feature_changes.append({
                        "feature_name": feature,
                        "old_contribution": contrib1,
                        "new_contribution": contrib2,
                        "change": contrib2 - contrib1,
                        "change_percentage": ((contrib2 - contrib1) / abs(contrib1) * 100) if contrib1 != 0 else 0
                    })
            
            # Sort by magnitude of change
            feature_changes.sort(key=lambda x: abs(x["change"]), reverse=True)
            
            # Identify top changes
            new_top_features = [f["feature_name"] for f in feature_changes[:5] if f["change"] > 0]
            lost_top_features = [f["feature_name"] for f in feature_changes[:5] if f["change"] < 0]
            
            # Calculate overall changes
            prediction_change = (exp2.prediction_value or 0) - (exp1.prediction_value or 0)
            
            # Generate summary
            if len(feature_changes) > 0:
                summary = f"Found {len(feature_changes)} significant feature changes"
                significance_level = "high" if len(feature_changes) > 5 else "medium"
            else:
                summary = "No significant changes detected"
                significance_level = "low"
            
            # Generate recommendations
            recommendations = []
            if prediction_change > 0.1:
                recommendations.append("Prediction improved significantly")
            elif prediction_change < -0.1:
                recommendations.append("Prediction declined significantly")
            
            if len(new_top_features) > 0:
                recommendations.append(f"Focus on new top contributors: {', '.join(new_top_features[:3])}")
            
            return ExplanationComparison(
                explanation_1_id=explanation_1_id,
                explanation_2_id=explanation_2_id,
                comparison_reason=comparison_reason,
                compared_by=compared_by,
                feature_changes=feature_changes,
                new_top_features=new_top_features,
                lost_top_features=lost_top_features,
                prediction_change=prediction_change,
                change_summary=summary,
                significance_level=significance_level,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error comparing explanations: {e}")
            raise
    
    def cleanup_cache(self):
        """Clean up old explanations from cache."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.config.cache_ttl_hours)
            
            to_remove = []
            for exp_id, exp_data in self.explanation_cache.items():
                created_at = exp_data.get('created_at')
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at)
                
                if created_at < cutoff_time:
                    to_remove.append(exp_id)
            
            for exp_id in to_remove:
                del self.explanation_cache[exp_id]
            
            if to_remove:
                self._save_cache()
                self.logger.info(f"Cleaned up {len(to_remove)} old explanations from cache")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {e}")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "cache_size": len(self.explanation_cache),
            "shap_available": SHAP_AVAILABLE,
            "config": self.config.model_dump(),
            "background_datasets": {
                "compatibility": len(self.background_datasets.get('compatibility', [])),
                "predictive": len(self.background_datasets.get('predictive', []))
            },
            "cache_path": str(self.cache_path)
        }
