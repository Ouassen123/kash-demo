"""QA tooling for explanation analysis and validation."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Optional matplotlib import
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from ..models.explanation_models import (
    ExplanationSnapshot, ExplanationComparison, QAQuery, QAQueryResult,
    FeatureContribution, ExplanationMetadata, ConfidenceLevel
)
from ..services.explainability_service import ExplainabilityService


class ExplainabilityQATools:
    """QA tools for explanation analysis, validation, and comparison."""
    
    def __init__(self, explainability_service: ExplainabilityService,
                 output_path: Optional[Path] = None):
        self.service = explainability_service
        self.output_path = output_path or Path(__file__).parent.parent / "data" / "qa_reports"
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # QA thresholds and rules
        self.quality_thresholds = {
            "min_confidence": 0.6,
            "max_computation_time_ms": 5000,
            "min_feature_contributions": 3,
            "max_concentration_ratio": 0.9,
            "min_explanation_quality": 0.7
        }
        
        self.anomaly_patterns = {
            "zero_contributions": "All feature contributions are zero",
            "extreme_concentration": "One feature dominates explanation",
            "negative_prediction_high_confidence": "Low prediction with high confidence",
            "high_computation_time": "Explanation took too long to compute",
            "missing_features": "Expected features missing from explanation"
        }
        
        self.logger.info("QA tools initialized")
    
    def analyze_explanation_history(self, learner_id: Optional[str] = None,
                                  model_id: Optional[str] = None,
                                  days_back: int = 30) -> Dict[str, Any]:
        """Analyze explanation history for trends and patterns."""
        try:
            # Query explanations
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            query = QAQuery(
                query_type="history_analysis",
                parameters={"analysis_type": "trends"},
                learner_id=learner_id,
                model_id=model_id,
                date_range={"start": start_date, "end": end_date},
                limit=1000,
                sort_by="generated_at",
                sort_order="asc",
                requested_by="qa_tools"
            )
            
            result = self.service.query_explanations(query)
            explanations = result.explanations
            
            if not explanations:
                return {"status": "no_data", "message": "No explanations found for analysis"}
            
            # Convert to DataFrame for analysis
            df_data = []
            for exp in explanations:
                df_data.append({
                    "explanation_id": exp.explanation_metadata.explanation_id,
                    "generated_at": exp.created_at,
                    "prediction_value": exp.prediction_value,
                    "confidence_level": exp.explanation_metadata.confidence_level.value,
                    "quality_score": exp.explanation_metadata.explanation_quality_score,
                    "feature_count": exp.explanation_metadata.feature_count,
                    "computation_time_ms": exp.explanation_metadata.computation_time_ms,
                    "model_type": exp.explanation_metadata.model_type,
                    "learner_id": exp.learner_id,
                    "total_contribution": exp.total_contribution
                })
            
            df = pd.DataFrame(df_data)
            
            # Perform trend analysis
            analysis = {
                "summary": self._generate_summary_stats(df),
                "trends": self._analyze_trends(df),
                "quality_analysis": self._analyze_quality(df),
                "performance_analysis": self._analyze_performance(df),
                "feature_analysis": self._analyze_features(explanations),
                "anomalies": self._detect_anomalies(explanations),
                "recommendations": self._generate_recommendations(df, explanations)
            }
            
            # Generate report
            report_path = self._generate_qa_report(analysis, learner_id, model_id, days_back)
            analysis["report_path"] = str(report_path)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing explanation history: {e}")
            return {"status": "error", "message": str(e)}
    
    def _generate_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics."""
        return {
            "total_explanations": len(df),
            "date_range": {
                "start": df["generated_at"].min().isoformat(),
                "end": df["generated_at"].max().isoformat()
            },
            "prediction_stats": {
                "mean": float(df["prediction_value"].mean()),
                "std": float(df["prediction_value"].std()),
                "min": float(df["prediction_value"].min()),
                "max": float(df["prediction_value"].max())
            },
            "confidence_distribution": df["confidence_level"].value_counts().to_dict(),
            "quality_stats": {
                "mean": float(df["quality_score"].mean()) if "quality_score" in df.columns else None,
                "min": float(df["quality_score"].min()) if "quality_score" in df.columns else None,
                "max": float(df["quality_score"].max()) if "quality_score" in df.columns else None
            },
            "model_types": df["model_type"].value_counts().to_dict()
        }
    
    def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends over time."""
        # Sort by date
        df_sorted = df.sort_values("generated_at")
        
        # Prediction trend
        prediction_trend = []
        for i in range(0, len(df_sorted), max(1, len(df_sorted) // 10)):
            subset = df_sorted.iloc[:i+1]
            prediction_trend.append({
                "date": subset["generated_at"].iloc[-1].isoformat(),
                "cumulative_mean": float(subset["prediction_value"].mean()),
                "count": len(subset)
            })
        
        # Quality trend
        quality_trend = []
        if "quality_score" in df.columns:
            for i in range(0, len(df_sorted), max(1, len(df_sorted) // 10)):
                subset = df_sorted.iloc[:i+1]
                quality_trend.append({
                    "date": subset["generated_at"].iloc[-1].isoformat(),
                    "cumulative_mean": float(subset["quality_score"].mean()),
                    "count": len(subset)
                })
        
        return {
            "prediction_trend": prediction_trend,
            "quality_trend": quality_trend,
            "volume_trend": self._calculate_volume_trend(df_sorted)
        }
    
    def _calculate_volume_trend(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Calculate explanation volume trend."""
        df["date"] = df["generated_at"].dt.date
        daily_counts = df.groupby("date").size().reset_index(name="count")
        
        trend = []
        for _, row in daily_counts.iterrows():
            trend.append({
                "date": row["date"].isoformat(),
                "count": int(row["count"])
            })
        
        return trend
    
    def _analyze_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze explanation quality."""
        if "quality_score" not in df.columns:
            return {"status": "no_quality_data"}
        
        quality_scores = df["quality_score"].dropna()
        
        # Quality distribution
        quality_bins = [0, 0.5, 0.7, 0.85, 1.0]
        quality_labels = ["Poor", "Fair", "Good", "Excellent"]
        df["quality_category"] = pd.cut(quality_scores, bins=quality_bins, labels=quality_labels, include_lowest=True)
        
        return {
            "overall_quality": {
                "mean": float(quality_scores.mean()),
                "median": float(quality_scores.median()),
                "std": float(quality_scores.std())
            },
            "quality_distribution": df["quality_category"].value_counts().to_dict(),
            "low_quality_explanations": len(quality_scores[quality_scores < self.quality_thresholds["min_explanation_quality"]]),
            "quality_by_model_type": df.groupby("model_type")["quality_score"].mean().to_dict()
        }
    
    def _analyze_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze explanation performance metrics."""
        performance = {}
        
        if "computation_time_ms" in df.columns:
            computation_times = df["computation_time_ms"].dropna()
            performance["computation_time"] = {
                "mean_ms": float(computation_times.mean()),
                "median_ms": float(computation_times.median()),
                "max_ms": float(computation_times.max()),
                "slow_explanations": len(computation_times[computation_times > self.quality_thresholds["max_computation_time_ms"]])
            }
        
        if "feature_count" in df.columns:
            feature_counts = df["feature_count"]
            performance["feature_count"] = {
                "mean": float(feature_counts.mean()),
                "median": float(feature_counts.median()),
                "min": int(feature_counts.min()),
                "max": int(feature_counts.max())
            }
        
        return performance
    
    def _analyze_features(self, explanations: List[ExplanationSnapshot]) -> Dict[str, Any]:
        """Analyze feature contributions across explanations."""
        feature_stats = {}
        contribution_stats = []
        
        for exp in explanations:
            for contribution in exp.feature_contributions:
                feature_name = contribution.feature_name
                
                if feature_name not in feature_stats:
                    feature_stats[feature_name] = {
                        "appearances": 0,
                        "total_contribution": 0.0,
                        "positive_contributions": 0,
                        "negative_contributions": 0,
                        "avg_importance_rank": []
                    }
                
                feature_stats[feature_name]["appearances"] += 1
                feature_stats[feature_name]["total_contribution"] += abs(contribution.contribution_score)
                feature_stats[feature_name]["avg_importance_rank"].append(contribution.importance_rank)
                
                if contribution.contribution_direction.value == "positive":
                    feature_stats[feature_name]["positive_contributions"] += 1
                else:
                    feature_stats[feature_name]["negative_contributions"] += 1
                
                contribution_stats.append(abs(contribution.contribution_score))
        
        # Calculate final statistics
        for feature_name, stats in feature_stats.items():
            stats["avg_contribution"] = stats["total_contribution"] / stats["appearances"]
            stats["avg_importance_rank"] = np.mean(stats["avg_importance_rank"])
            stats["positive_ratio"] = stats["positive_contributions"] / stats["appearances"]
        
        # Sort by average contribution
        top_features = sorted(feature_stats.items(), key=lambda x: x[1]["avg_contribution"], reverse=True)[:20]
        
        return {
            "total_unique_features": len(feature_stats),
            "top_features": dict(top_features),
            "contribution_stats": {
                "mean": float(np.mean(contribution_stats)),
                "median": float(np.median(contribution_stats)),
                "std": float(np.std(contribution_stats))
            }
        }
    
    def _detect_anomalies(self, explanations: List[ExplanationSnapshot]) -> List[Dict[str, Any]]:
        """Detect anomalies in explanations."""
        anomalies = []
        
        for exp in explanations:
            exp_anomalies = []
            
            # Check for zero contributions
            total_contribution = sum(abs(c.contribution_score) for c in exp.feature_contributions)
            if total_contribution < 0.001:
                exp_anomalies.append(self.anomaly_patterns["zero_contributions"])
            
            # Check for extreme concentration
            if exp.feature_contributions:
                top_contribution = max(abs(c.contribution_score) for c in exp.feature_contributions)
                if total_contribution > 0 and top_contribution / total_contribution > self.quality_thresholds["max_concentration_ratio"]:
                    exp_anomalies.append(self.anomaly_patterns["extreme_concentration"])
            
            # Check computation time
            if (exp.explanation_metadata.computation_time_ms and 
                exp.explanation_metadata.computation_time_ms > self.quality_thresholds["max_computation_time_ms"]):
                exp_anomalies.append(self.anomaly_patterns["high_computation_time"])
            
            # Check confidence vs prediction mismatch
            if (exp.prediction_value is not None and 
                exp.explanation_metadata.confidence_level == ConfidenceLevel.VERY_HIGH and
                exp.prediction_value < 0.3):
                exp_anomalies.append(self.anomaly_patterns["negative_prediction_high_confidence"])
            
            if exp_anomalies:
                anomalies.append({
                    "explanation_id": exp.explanation_metadata.explanation_id,
                    "learner_id": exp.learner_id,
                    "generated_at": exp.created_at.isoformat(),
                    "anomalies": exp_anomalies,
                    "prediction_value": exp.prediction_value,
                    "confidence_level": exp.explanation_metadata.confidence_level.value
                })
        
        return anomalies
    
    def _generate_recommendations(self, df: pd.DataFrame, explanations: List[ExplanationSnapshot]) -> List[str]:
        """Generate QA recommendations."""
        recommendations = []
        
        # Quality recommendations
        if "quality_score" in df.columns:
            low_quality_pct = (df["quality_score"] < self.quality_thresholds["min_explanation_quality"]).mean()
            if low_quality_pct > 0.2:
                recommendations.append(f"{low_quality_pct:.1%} of explanations have low quality - review feature engineering")
        
        # Performance recommendations
        if "computation_time_ms" in df.columns:
            slow_pct = (df["computation_time_ms"] > self.quality_thresholds["max_computation_time_ms"]).mean()
            if slow_pct > 0.1:
                recommendations.append(f"{slow_pct:.1%} of explanations are slow - optimize SHAP computation")
        
        # Feature recommendations
        if explanations:
            avg_features = np.mean([len(exp.feature_contributions) for exp in explanations])
            if avg_features < self.quality_thresholds["min_feature_contributions"]:
                recommendations.append("Low number of feature contributions - check feature selection")
        
        # Anomaly recommendations
        anomalies = self._detect_anomalies(explanations)
        if len(anomalies) > len(explanations) * 0.1:
            recommendations.append("High anomaly rate detected - investigate explanation generation process")
        
        # Volume recommendations
        if len(df) < 10:
            recommendations.append("Low explanation volume - consider increasing explanation generation frequency")
        
        return recommendations
    
    def compare_explanation_versions(self, explanation_id: str,
                                   days_back: int = 7) -> Dict[str, Any]:
        """Compare explanation with previous versions."""
        try:
            # Get current explanation
            current_exp = self.service.get_cached_explanation(explanation_id)
            if not current_exp:
                return {"status": "error", "message": "Explanation not found"}
            
            # Find previous explanations for same learner/model
            learner_id = current_exp.learner_id
            model_id = current_exp.explanation_metadata.model_id
            
            query = QAQuery(
                query_type="version_comparison",
                parameters={"explanation_id": explanation_id},
                learner_id=learner_id,
                model_id=model_id,
                date_range={
                    "start": current_exp.created_at - timedelta(days=days_back),
                    "end": current_exp.created_at
                },
                limit=10,
                sort_by="generated_at",
                sort_order="desc",
                requested_by="qa_tools"
            )
            
            result = self.service.query_explanations(query)
            previous_explanations = [exp for exp in result.explanations if exp.explanation_metadata.explanation_id != explanation_id]
            
            if not previous_explanations:
                return {"status": "no_previous_versions", "message": "No previous versions found"}
            
            # Compare with most recent previous version
            previous_exp = previous_explanations[0]
            comparison = self.service.compare_explanations(
                explanation_1_id=previous_exp.explanation_metadata.explanation_id,
                explanation_2_id=explanation_id,
                comparison_reason="Version comparison",
                compared_by="qa_tools"
            )
            
            # Analyze changes
            analysis = {
                "comparison": comparison.model_dump(),
                "change_analysis": self._analyze_version_changes(current_exp, previous_exp),
                "quality_comparison": self._compare_quality(current_exp, previous_exp),
                "recommendations": self._generate_version_recommendations(comparison)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error comparing explanation versions: {e}")
            return {"status": "error", "message": str(e)}
    
    def _analyze_version_changes(self, current: ExplanationSnapshot, previous: ExplanationSnapshot) -> Dict[str, Any]:
        """Analyze changes between explanation versions."""
        current_contributions = {f.feature_name: f.contribution_score for f in current.feature_contributions}
        previous_contributions = {f.feature_name: f.contribution_score for f in previous.feature_contributions}
        
        # Calculate changes
        changes = {}
        for feature in set(current_contributions.keys()) | set(previous_contributions.keys()):
            current_val = current_contributions.get(feature, 0)
            previous_val = previous_contributions.get(feature, 0)
            changes[feature] = current_val - previous_val
        
        # Statistics
        change_values = list(changes.values())
        
        return {
            "total_features_changed": len([c for c in change_values if abs(c) > 0.01]),
            "largest_change": max(change_values, key=abs) if change_values else 0,
            "average_change": float(np.mean(np.abs(change_values))) if change_values else 0,
            "prediction_change": (current.prediction_value or 0) - (previous.prediction_value or 0),
            "feature_changes": changes
        }
    
    def _compare_quality(self, current: ExplanationSnapshot, previous: ExplanationSnapshot) -> Dict[str, Any]:
        """Compare quality metrics between versions."""
        current_quality = current.explanation_metadata.explanation_quality_score
        previous_quality = previous.explanation_metadata.explanation_quality_score
        
        comparison = {
            "current_quality": current_quality,
            "previous_quality": previous_quality,
            "quality_change": (current_quality or 0) - (previous_quality or 0) if current_quality and previous_quality else None
        }
        
        # Confidence levels
        comparison["confidence_change"] = {
            "current": current.explanation_metadata.confidence_level.value,
            "previous": previous.explanation_metadata.confidence_level.value,
            "improved": current.explanation_metadata.confidence_level.value > previous.explanation_metadata.confidence_level.value
        }
        
        return comparison
    
    def _generate_version_recommendations(self, comparison: ExplanationComparison) -> List[str]:
        """Generate recommendations based on version comparison."""
        recommendations = []
        
        if comparison.prediction_change and abs(comparison.prediction_change) > 0.2:
            recommendations.append("Significant prediction change detected - review feature stability")
        
        if len(comparison.new_top_features) > 3:
            recommendations.append("Many new top features emerged - investigate feature drift")
        
        if len(comparison.lost_top_features) > 3:
            recommendations.append("Many top features disappeared - check data quality")
        
        if comparison.significance_level == "high":
            recommendations.append("High significance changes detected - consider model retraining")
        
        return recommendations
    
    def _generate_qa_report(self, analysis: Dict[str, Any], learner_id: Optional[str],
                           model_id: Optional[str], days_back: int) -> Path:
        """Generate QA report file."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"qa_report_{learner_id or 'all'}_{model_id or 'all'}_{timestamp}.json"
        report_path = self.output_path / filename
        
        report_data = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "learner_id": learner_id,
                "model_id": model_id,
                "analysis_period_days": days_back,
                "qa_version": "1.0"
            },
            "analysis": analysis
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self.logger.info(f"QA report generated: {report_path}")
        return report_path
    
    def validate_explanation(self, explanation_id: str,
                           validation_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate a single explanation against quality criteria."""
        try:
            explanation = self.service.get_cached_explanation(explanation_id)
            if not explanation:
                return {"status": "error", "message": "Explanation not found"}
            
            criteria = validation_criteria or self.quality_thresholds
            
            validation_results = {
                "explanation_id": explanation_id,
                "validation_timestamp": datetime.utcnow().isoformat(),
                "criteria_used": criteria,
                "checks": {}
            }
            
            # Check confidence level
            confidence_score = self._confidence_to_score(explanation.explanation_metadata.confidence_level)
            validation_results["checks"]["confidence"] = {
                "passed": confidence_score >= criteria.get("min_confidence", 0.6),
                "value": confidence_score,
                "threshold": criteria.get("min_confidence", 0.6)
            }
            
            # Check computation time
            if explanation.explanation_metadata.computation_time_ms:
                validation_results["checks"]["computation_time"] = {
                    "passed": explanation.explanation_metadata.computation_time_ms <= criteria.get("max_computation_time_ms", 5000),
                    "value": explanation.explanation_metadata.computation_time_ms,
                    "threshold": criteria.get("max_computation_time_ms", 5000)
                }
            
            # Check feature contributions
            validation_results["checks"]["feature_contributions"] = {
                "passed": len(explanation.feature_contributions) >= criteria.get("min_feature_contributions", 3),
                "value": len(explanation.feature_contributions),
                "threshold": criteria.get("min_feature_contributions", 3)
            }
            
            # Check explanation quality
            if explanation.explanation_metadata.explanation_quality_score:
                validation_results["checks"]["quality_score"] = {
                    "passed": explanation.explanation_metadata.explanation_quality_score >= criteria.get("min_explanation_quality", 0.7),
                    "value": explanation.explanation_metadata.explanation_quality_score,
                    "threshold": criteria.get("min_explanation_quality", 0.7)
                }
            
            # Overall validation result
            passed_checks = sum(1 for check in validation_results["checks"].values() if check["passed"])
            total_checks = len(validation_results["checks"])
            validation_results["overall_passed"] = passed_checks == total_checks
            validation_results["passed_checks"] = passed_checks
            validation_results["total_checks"] = total_checks
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating explanation: {e}")
            return {"status": "error", "message": str(e)}
    
    def _confidence_to_score(self, confidence: ConfidenceLevel) -> float:
        """Convert confidence level to numeric score."""
        mapping = {
            ConfidenceLevel.VERY_LOW: 0.2,
            ConfidenceLevel.LOW: 0.4,
            ConfidenceLevel.MEDIUM: 0.6,
            ConfidenceLevel.HIGH: 0.8,
            ConfidenceLevel.VERY_HIGH: 1.0
        }
        return mapping.get(confidence, 0.5)
    
    def batch_validate_explanations(self, explanation_ids: List[str],
                                  validation_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate multiple explanations in batch."""
        try:
            results = []
            
            for exp_id in explanation_ids:
                result = self.validate_explanation(exp_id, validation_criteria)
                results.append(result)
            
            # Summary statistics
            total_validations = len(results)
            passed_validations = sum(1 for r in results if r.get("overall_passed", False))
            
            summary = {
                "total_validations": total_validations,
                "passed_validations": passed_validations,
                "failed_validations": total_validations - passed_validations,
                "pass_rate": passed_validations / total_validations if total_validations > 0 else 0,
                "validation_timestamp": datetime.utcnow().isoformat()
            }
            
            return {
                "summary": summary,
                "individual_results": results
            }
            
        except Exception as e:
            self.logger.error(f"Error in batch validation: {e}")
            return {"status": "error", "message": str(e)}
