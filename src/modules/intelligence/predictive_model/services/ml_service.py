"""Machine learning service for predictive modeling."""

import pickle
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import json
import logging
from pydantic import BaseModel, Field
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.svm import SVC, SVR
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_squared_error, mean_absolute_error, r2_score,
    classification_report, confusion_matrix
)

# Optional SHAP import for explainability
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

from ..models.feature_models import TrainingExample, TrainingPipeline, FeatureStore
from ..models.prediction_models import (
    ModelMetadata, ModelPerformance, PredictionResult, PredictionTarget,
    ModelType, FeatureImportance, PredictionExplanation, ConfidenceLevel, DataQuality
)


class PredictiveModelService:
    """Service for training and managing predictive models."""
    
    def __init__(self, model_registry_path: Optional[Path] = None):
        self.model_registry_path = model_registry_path or Path(__file__).parent.parent / "data" / "model_registry"
        self.model_registry_path.mkdir(parents=True, exist_ok=True)
        
        # Model registry
        self.models_file = self.model_registry_path / "models.json"
        self.models = self._load_models()
        
        # Training pipelines
        self.pipelines_file = self.model_registry_path / "pipelines.json"
        self.pipelines = self._load_pipelines()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Algorithm registry
        self.algorithms = {
            ModelType.CLASSIFICATION: {
                "random_forest": RandomForestClassifier,
                "gradient_boosting": GradientBoostingClassifier,
                "logistic_regression": LogisticRegression,
                "svm": SVC,
                "neural_network": MLPClassifier
            },
            ModelType.REGRESSION: {
                "random_forest": RandomForestRegressor,
                "gradient_boosting": GradientBoostingRegressor,
                "linear_regression": LinearRegression,
                "ridge": Ridge,
                "lasso": Lasso,
                "svm": SVR,
                "neural_network": MLPRegressor
            }
        }
        
        # Default hyperparameters
        self.default_hyperparameters = {
            "random_forest": {
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 5,
                "min_samples_leaf": 2,
                "random_state": 42
            },
            "gradient_boosting": {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 6,
                "random_state": 42
            },
            "logistic_regression": {
                "random_state": 42,
                "max_iter": 1000
            },
            "linear_regression": {},
            "ridge": {"alpha": 1.0, "random_state": 42},
            "lasso": {"alpha": 1.0, "random_state": 42},
            "svm": {"random_state": 42},
            "neural_network": {
                "hidden_layer_sizes": (100, 50),
                "max_iter": 500,
                "random_state": 42
            }
        }
    
    def _load_models(self) -> Dict[str, ModelMetadata]:
        """Load model registry from storage."""
        if not self.models_file.exists():
            return {}
        
        try:
            with open(self.models_file, 'r') as f:
                data = json.load(f)
            
            models = {}
            for model_id, model_data in data.items():
                # Convert datetime strings back to datetime objects
                for field in ["training_date", "deployment_date", "approval_date", "last_retraining_date"]:
                    if model_data.get(field):
                        model_data[field] = datetime.fromisoformat(model_data[field])
                
                # Convert performance metrics
                if "performance" in model_data and "evaluation_date" in model_data["performance"]:
                    model_data["performance"]["evaluation_date"] = datetime.fromisoformat(
                        model_data["performance"]["evaluation_date"]
                    )
                
                models[model_id] = ModelMetadata(**model_data)
            
            return models
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            return {}
    
    def _load_pipelines(self) -> Dict[str, TrainingPipeline]:
        """Load training pipelines from storage."""
        if not self.pipelines_file.exists():
            return {}
        
        try:
            with open(self.pipelines_file, 'r') as f:
                data = json.load(f)
            
            pipelines = {}
            for pipeline_id, pipeline_data in data.items():
                # Convert datetime strings back to datetime objects
                for field in ["start_time", "end_time"]:
                    if pipeline_data.get(field):
                        pipeline_data[field] = datetime.fromisoformat(pipeline_data[field])
                
                pipelines[pipeline_id] = TrainingPipeline(**pipeline_data)
            
            return pipelines
        except Exception as e:
            self.logger.error(f"Error loading pipelines: {e}")
            return {}
    
    def _save_models(self):
        """Save model registry to storage."""
        try:
            data = {}
            for model_id, model in self.models.items():
                data[model_id] = model.model_dump()
            
            with open(self.models_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving models: {e}")
            raise
    
    def _save_pipelines(self):
        """Save training pipelines to storage."""
        try:
            data = {}
            for pipeline_id, pipeline in self.pipelines.items():
                data[pipeline_id] = pipeline.model_dump()
            
            with open(self.pipelines_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving pipelines: {e}")
            raise
    
    def create_training_pipeline(self, pipeline_config: Dict[str, Any]) -> TrainingPipeline:
        """Create a new training pipeline."""
        pipeline = TrainingPipeline(**pipeline_config)
        self.pipelines[pipeline.pipeline_id] = pipeline
        self._save_pipelines()
        
        self.logger.info(f"Created training pipeline: {pipeline.pipeline_id}")
        return pipeline
    
    def prepare_training_data(self, examples: List[TrainingExample]) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data from examples."""
        try:
            # Create feature matrix
            feature_data = []
            targets = []
            
            for example in examples:
                feature_data.append(example.feature_vector)
                targets.append(example.target.target_value)
            
            X = pd.DataFrame(feature_data)
            y = pd.Series(targets)
            
            # Filter by data quality
            quality_threshold = 0.5
            valid_indices = [i for i, example in enumerate(examples) 
                           if example.data_quality_score >= quality_threshold]
            
            if len(valid_indices) < len(examples):
                self.logger.warning(f"Filtered {len(examples) - len(valid_indices)} low-quality examples")
                X = X.iloc[valid_indices]
                y = y.iloc[valid_indices]
                examples = [examples[i] for i in valid_indices]
            
            # Remove examples with missing target values
            valid_mask = ~y.isnull()
            X = X[valid_mask]
            y = y[valid_mask]
            
            self.logger.info(f"Prepared training data: {X.shape[0]} samples, {X.shape[1]} features")
            
            return X, y
            
        except Exception as e:
            self.logger.error(f"Error preparing training data: {e}")
            raise
    
    def train_model(self, pipeline_id: str, examples: List[TrainingExample]) -> ModelMetadata:
        """Train a predictive model using the specified pipeline."""
        try:
            # Get pipeline configuration
            if pipeline_id not in self.pipelines:
                raise ValueError(f"Pipeline {pipeline_id} not found")
            
            pipeline = self.pipelines[pipeline_id]
            pipeline.status = "running"
            pipeline.start_time = datetime.utcnow()
            self._save_pipelines()
            
            # Prepare training data
            X, y = self.prepare_training_data(examples)
            
            # Split data
            if pipeline.validation_split + pipeline.test_split >= 1.0:
                raise ValueError("Validation and test splits sum to >= 1.0")
            
            X_train, X_temp, y_train, y_temp = train_test_split(
                X, y, test_size=(pipeline.validation_split + pipeline.test_split), 
                random_state=pipeline.random_seed
            )
            
            val_size = pipeline.validation_split / (pipeline.validation_split + pipeline.test_split)
            X_val, X_test, y_val, y_test = train_test_split(
                X_temp, y_temp, test_size=(1 - val_size), random_state=pipeline.random_seed
            )
            
            # Get algorithm
            algorithm_name = pipeline.algorithm
            if pipeline.model_type not in self.algorithms:
                raise ValueError(f"Unsupported model type: {pipeline.model_type}")
            
            if algorithm_name not in self.algorithms[pipeline.model_type]:
                raise ValueError(f"Algorithm {algorithm_name} not supported for {pipeline.model_type}")
            
            algorithm_class = self.algorithms[pipeline.model_type][algorithm_name]
            
            # Get hyperparameters
            hyperparams = self.default_hyperparameters.get(algorithm_name, {})
            hyperparams.update(pipeline.hyperparameters)
            
            # Train model
            self.logger.info(f"Training {algorithm_name} model...")
            model = algorithm_class(**hyperparams)
            
            # Handle SVM probability calibration
            if algorithm_name == "svm" and pipeline.model_type == ModelType.CLASSIFICATION:
                hyperparams["probability"] = True
                model = algorithm_class(**hyperparams)
            
            model.fit(X_train, y_train)
            
            # Evaluate model
            train_metrics = self._evaluate_model(model, X_train, y_train, pipeline.model_type)
            val_metrics = self._evaluate_model(model, X_val, y_val, pipeline.model_type)
            test_metrics = self._evaluate_model(model, X_test, y_test, pipeline.model_type)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=pipeline.cross_validation_folds)
            cv_score = cv_scores.mean()
            
            # Calculate feature importance
            feature_importance = self._calculate_feature_importance(model, X.columns.tolist(), pipeline.model_type)
            
            # Create training dataset metadata
            class LocalTrainingFeature(BaseModel):
                feature_name: str = Field(..., description="Name of the feature")
                feature_type: str = Field(..., description="Type of feature")
                data_type: str = Field(..., description="Data type")
                source: str = Field(..., description="Source of the feature")
            
            class LocalTrainingDataset(BaseModel):
                dataset_name: str = Field(..., description="Name of the dataset")
                version: str = Field(..., description="Dataset version")
                created_at: datetime = Field(default_factory=datetime.utcnow)
                total_samples: int = Field(..., description="Total number of samples")
                training_samples: int = Field(..., description="Number of training samples")
                validation_samples: int = Field(..., description="Number of validation samples")
                test_samples: int = Field(..., description="Number of test samples")
                feature_count: int = Field(..., description="Number of features")
                features: List[LocalTrainingFeature] = Field(..., description="List of features")
                target_variable: str = Field(..., description="Target variable name")
                target_distribution: Dict[str, float] = Field(..., description="Target variable distribution")
                missing_data_percentage: float = Field(..., description="Percentage of missing data")
                outlier_percentage: float = Field(..., description="Percentage of outliers")
                data_sources: List[str] = Field(..., description="Data sources used")
            
            training_dataset = LocalTrainingDataset(
                dataset_name=f"dataset_{pipeline.prediction_target.value}_{datetime.utcnow().strftime('%Y%m%d')}",
                version="1.0",
                total_samples=len(examples),
                training_samples=len(X_train),
                validation_samples=len(X_val),
                test_samples=len(X_test),
                feature_count=X.shape[1],
                features=[
                    LocalTrainingFeature(
                        feature_name=f"feature_{i}",
                        feature_type="compatibility_score",  # Use valid enum value
                        data_type="numeric",
                        source="feature_engineering"
                    ) for i in range(X.shape[1])
                ],
                target_variable=pipeline.prediction_target.value,
                target_distribution={str(k): v for k, v in y.value_counts().to_dict().items()},
                missing_data_percentage=0.0,  # Would be calculated from actual data
                outlier_percentage=0.0,  # Would be calculated from actual data
                data_sources=["feature_engineering"]
            )
            
            # Create performance metrics
            performance = ModelPerformance(
                model_version="1.0",
                evaluation_date=datetime.utcnow(),
                accuracy=train_metrics.get("accuracy"),
                precision=train_metrics.get("precision"),
                recall=train_metrics.get("recall"),
                f1_score=train_metrics.get("f1_score"),
                auc_roc=train_metrics.get("auc_roc"),
                mse=train_metrics.get("mse"),
                rmse=train_metrics.get("rmse"),
                mae=train_metrics.get("mae"),
                r2_score=train_metrics.get("r2_score"),
                cross_validation_score=cv_score
            )
            
            # Create model metadata
            model_metadata = ModelMetadata(
                model_name=f"{pipeline.prediction_target.value}_{algorithm_name}",
                model_version="1.0",
                model_type=pipeline.model_type,
                prediction_target=pipeline.prediction_target,
                training_dataset=training_dataset.model_dump(),
                training_duration_hours=0,  # Would be calculated
                hyperparameters=hyperparams,
                feature_importance=feature_importance,
                performance=performance,
                cross_validation_score=cv_score,
                validation_method=f"{pipeline.cross_validation_folds}-fold CV",
                created_by="predictive_model_service",
                description=f"Predictive model for {pipeline.prediction_target.value}",
                business_objective=f"Predict {pipeline.prediction_target.value} for learners",
                intended_use="Career prediction and recommendation",
                framework="scikit-learn",
                algorithm=algorithm_name
            )
            
            # Save model
            model_path = self.model_registry_path / f"{model_metadata.model_id}.pkl"
            joblib.dump(model, model_path)
            model_metadata.model_size_mb = model_path.stat().st_size / (1024 * 1024)
            
            # Update pipeline
            pipeline.model_id = model_metadata.model_id
            pipeline.status = "completed"
            pipeline.end_time = datetime.utcnow()
            pipeline.duration_minutes = (pipeline.end_time - pipeline.start_time).total_seconds() / 60
            pipeline.training_metrics = train_metrics
            pipeline.validation_metrics = val_metrics
            pipeline.model_artifact_path = str(model_path)
            self._save_pipelines()
            
            # Register model
            self.models[model_metadata.model_id] = model_metadata
            self._save_models()
            
            self.logger.info(f"Successfully trained model: {model_metadata.model_id}")
            
            return model_metadata
            
        except Exception as e:
            pipeline.status = "failed"
            pipeline.end_time = datetime.utcnow()
            self._save_pipelines()
            
            self.logger.error(f"Error training model: {e}")
            raise
    
    def _evaluate_model(self, model, X, y, model_type: ModelType) -> Dict[str, float]:
        """Evaluate model performance."""
        try:
            y_pred = model.predict(X)
            
            if model_type == ModelType.CLASSIFICATION:
                # Classification metrics
                metrics = {
                    "accuracy": accuracy_score(y, y_pred),
                    "precision": precision_score(y, y_pred, average='weighted', zero_division=0),
                    "recall": recall_score(y, y_pred, average='weighted', zero_division=0),
                    "f1_score": f1_score(y, y_pred, average='weighted', zero_division=0)
                }
                
                # AUC-ROC for binary classification
                if len(np.unique(y)) == 2:
                    try:
                        y_proba = model.predict_proba(X)[:, 1]
                        metrics["auc_roc"] = roc_auc_score(y, y_proba)
                    except:
                        metrics["auc_roc"] = 0.0
                
            else:  # Regression
                metrics = {
                    "mse": mean_squared_error(y, y_pred),
                    "rmse": np.sqrt(mean_squared_error(y, y_pred)),
                    "mae": mean_absolute_error(y, y_pred),
                    "r2_score": r2_score(y, y_pred)
                }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error evaluating model: {e}")
            return {}
    
    def _calculate_feature_importance(self, model, feature_names: List[str], model_type: ModelType) -> List[FeatureImportance]:
        """Calculate feature importance for model explainability."""
        try:
            feature_importance = []
            
            if hasattr(model, 'feature_importances_'):
                # Tree-based models
                importances = model.feature_importances_
            elif hasattr(model, 'coef_'):
                # Linear models
                importances = np.abs(model.coef_).flatten()
            else:
                # Use SHAP for other models if available
                if SHAP_AVAILABLE:
                    try:
                        explainer = shap.Explainer(model)
                        shap_values = explainer.shap_values(pd.DataFrame([[0] * len(feature_names)], columns=feature_names))
                        importances = np.abs(shap_values).mean(0)
                    except:
                        # Fallback: equal importance
                        importances = np.ones(len(feature_names)) / len(feature_names)
                else:
                    # SHAP not available, use equal importance
                    importances = np.ones(len(feature_names)) / len(feature_names)
            
            # Normalize importances
            importances = importances / np.sum(importances)
            
            # Create feature importance objects
            for i, (name, importance) in enumerate(zip(feature_names, importances)):
                # Handle NaN values
                if np.isnan(importance):
                    importance = 0.0
                
                feature_importance.append(FeatureImportance(
                    feature_name=str(name),
                    importance_score=float(importance),
                    feature_type="compatibility_score",  # Use valid enum value
                    contribution_direction="positive" if importance > 0 else "negative",
                    importance_rank=i + 1
                ))
            
            # Sort by importance
            feature_importance.sort(key=lambda x: x.importance_score, reverse=True)
            
            return feature_importance
            
        except Exception as e:
            self.logger.error(f"Error calculating feature importance: {e}")
            return []
    
    def predict(self, model_id: str, feature_vector: List[float], 
               feature_names: List[str], include_explanation: bool = True) -> PredictionResult:
        """Make a prediction using a trained model."""
        try:
            # Get model
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            model_metadata = self.models[model_id]
            
            # Load model
            model_path = self.model_registry_path / f"{model_id}.pkl"
            if not model_path.exists():
                raise ValueError(f"Model file not found: {model_path}")
            
            model = joblib.load(model_path)
            
            # Prepare input
            if len(feature_vector) != len(feature_names):
                raise ValueError("Feature vector length doesn't match feature names length")
            
            X = pd.DataFrame([feature_vector], columns=feature_names)
            
            # Make prediction
            start_time = datetime.utcnow()
            prediction = model.predict(X)[0]
            
            # Get prediction probability if available
            confidence_score = 0.5  # Default
            if hasattr(model, 'predict_proba'):
                try:
                    probabilities = model.predict_proba(X)[0]
                    confidence_score = np.max(probabilities)
                except:
                    pass
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(confidence_score)
            
            # Create explanation
            explanation = None
            if include_explanation:
                explanation = self._create_prediction_explanation(
                    model, X, model_metadata, feature_names
                )
            
            # Ensure explanation is not None
            if explanation is None:
                explanation = PredictionExplanation(
                    primary_factors=[],
                    secondary_factors=[],
                    competency_gaps=[],
                    strength_areas=[],
                    data_limitations=["Explanation generation disabled"],
                    confidence_factors={}
                )
            
            # Create prediction result
            result = PredictionResult(
                learner_id="unknown",  # Should be provided by caller
                prediction_type=model_metadata.prediction_target,
                predicted_value=float(prediction),
                confidence_level=confidence_level,
                confidence_score=confidence_score,
                explanation=explanation,
                model_version=model_metadata.model_version,
                data_quality=DataQuality.GOOD,  # Should be calculated
                feature_count=len(feature_vector)
            )
            
            # Calculate inference latency
            end_time = datetime.utcnow()
            inference_latency_ms = (end_time - start_time).total_seconds() * 1000
            
            self.logger.info(f"Prediction completed in {inference_latency_ms:.2f}ms")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error making prediction: {e}")
            raise
    
    def _calculate_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """Convert confidence score to confidence level."""
        if confidence_score >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence_score >= 0.75:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.6:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.4:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _create_prediction_explanation(self, model, X, model_metadata: ModelMetadata, 
                                      feature_names: List[str]) -> PredictionExplanation:
        """Create explanation for prediction."""
        try:
            # Get top features from model metadata
            top_features = model_metadata.feature_importance[:10]
            
            # Separate primary and secondary factors
            primary_factors = top_features[:5]
            secondary_factors = top_features[5:10]
            
            # Identify competency gaps and strengths
            competency_gaps = []
            strength_areas = []
            
            for feature in primary_factors:
                if feature.importance_score > 0.1 and "score" in feature.feature_name:
                    if feature.importance_score < 0.5:
                        competency_gaps.append(feature.feature_name.replace("_score", ""))
                    else:
                        strength_areas.append(feature.feature_name.replace("_score", ""))
            
            # Data limitations
            data_limitations = []
            if model_metadata.training_dataset.missing_data_percentage > 10:
                data_limitations.append("High missing data rate in training")
            if model_metadata.training_dataset.outlier_percentage > 5:
                data_limitations.append("High outlier rate in training")
            
            # Confidence factors
            confidence_factors = {
                "model_confidence": model_metadata.performance.accuracy or 0.0,
                "data_quality": 1.0 - model_metadata.training_dataset.missing_data_percentage / 100,
                "feature_coverage": len(feature_names) / model_metadata.training_dataset.feature_count
            }
            
            return PredictionExplanation(
                primary_factors=primary_factors,
                secondary_factors=secondary_factors,
                competency_gaps=competency_gaps,
                strength_areas=strength_areas,
                data_limitations=data_limitations,
                confidence_factors=confidence_factors
            )
            
        except Exception as e:
            self.logger.error(f"Error creating prediction explanation: {e}")
            # Return minimal explanation
            return PredictionExplanation(
                primary_factors=[],
                secondary_factors=[],
                competency_gaps=[],
                strength_areas=[],
                data_limitations=["Explanation generation failed"],
                confidence_factors={}
            )
    
    def batch_predict(self, model_id: str, feature_vectors: List[List[float]], 
                     feature_names: List[str], include_explanations: bool = True) -> List[PredictionResult]:
        """Make batch predictions."""
        results = []
        
        for i, feature_vector in enumerate(feature_vectors):
            try:
                result = self.predict(model_id, feature_vector, feature_names, include_explanations)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error in batch prediction {i}: {e}")
                # Continue with other predictions
        
        return results
    
    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model metadata by ID."""
        return self.models.get(model_id)
    
    def list_models(self, prediction_target: Optional[PredictionTarget] = None,
                   model_type: Optional[ModelType] = None,
                   is_deployed: Optional[bool] = None) -> List[ModelMetadata]:
        """List models with optional filters."""
        models = list(self.models.values())
        
        if prediction_target:
            models = [m for m in models if m.prediction_target == prediction_target]
        
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        
        if is_deployed is not None:
            models = [m for m in models if m.is_deployed == is_deployed]
        
        return models
    
    def deploy_model(self, model_id: str, deployment_environment: str = "production") -> bool:
        """Deploy a model."""
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            model = self.models[model_id]
            model.is_deployed = True
            model.deployment_date = datetime.utcnow()
            model.deployment_environment = deployment_environment
            
            self._save_models()
            
            self.logger.info(f"Deployed model {model_id} to {deployment_environment}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deploying model: {e}")
            return False
    
    def undeploy_model(self, model_id: str) -> bool:
        """Undeploy a model."""
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            model = self.models[model_id]
            model.is_deployed = False
            
            self._save_models()
            
            self.logger.info(f"Undeployed model {model_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error undeploying model: {e}")
            return False
    
    def delete_model(self, model_id: str) -> bool:
        """Delete a model."""
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            # Delete model file
            model_path = self.model_registry_path / f"{model_id}.pkl"
            if model_path.exists():
                model_path.unlink()
            
            # Remove from registry
            del self.models[model_id]
            self._save_models()
            
            self.logger.info(f"Deleted model {model_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting model: {e}")
            return False
    
    def get_model_performance_summary(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get performance summary for a model."""
        try:
            model = self.get_model(model_id)
            if not model:
                return None
            
            perf = model.performance
            
            summary = {
                "model_id": model_id,
                "model_name": model.model_name,
                "model_type": model.model_type.value,
                "prediction_target": model.prediction_target.value,
                "training_date": model.training_date.isoformat(),
                "cross_validation_score": model.cross_validation_score,
                "performance": {}
            }
            
            # Add relevant metrics based on model type
            if model.model_type == ModelType.CLASSIFICATION:
                summary["performance"] = {
                    "accuracy": perf.accuracy,
                    "precision": perf.precision,
                    "recall": perf.recall,
                    "f1_score": perf.f1_score,
                    "auc_roc": perf.auc_roc
                }
            else:
                summary["performance"] = {
                    "mse": perf.mse,
                    "rmse": perf.rmse,
                    "mae": perf.mae,
                    "r2_score": perf.r2_score
                }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting model performance summary: {e}")
            return None
