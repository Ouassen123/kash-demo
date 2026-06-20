"""Core scoring pipeline for compatibility score calculation."""

import uuid
import statistics
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from ..models import (
    CompatibilityScore,
    CompatibilityScoreRequest,
    CompatibilityScoreResponse,
    KASHSignal,
    SignalBreakdown,
    ConfidenceInterval,
    WeightConfiguration,
    SignalInput,
    SignalValidationResult,
    SignalAggregationRule,
    SignalFilter,
    JobFamilyEnum,
    SignalSourceEnum,
    SignalQualityEnum,
    NormalizationMethod,
    DataFreshness,
    ProvenanceEventType
)
from .weight_manager import WeightManager
from .provenance_tracker import ProvenanceTracker


@dataclass
class ScoringContext:
    """Context for scoring operations."""
    request_id: str
    learner_id: str
    job_family: JobFamilyEnum
    target_job_id: Optional[str]
    weight_config: WeightConfiguration
    aggregation_rules: Dict[str, SignalAggregationRule]
    signal_filter: SignalFilter
    calculation_version: str
    provenance_tracker: ProvenanceTracker


class ScoringPipeline:
    """Main pipeline for calculating compatibility scores."""
    
    def __init__(self, weight_manager: Optional[WeightManager] = None,
                 provenance_tracker: Optional[ProvenanceTracker] = None):
        self.weight_manager = weight_manager or WeightManager()
        self.provenance_tracker = provenance_tracker or ProvenanceTracker()
        
        # Default aggregation rules
        self.default_aggregation_rules = self._create_default_aggregation_rules()
        
        # Quality multipliers
        self.quality_multipliers = {
            SignalQualityEnum.HIGH: 1.0,
            SignalQualityEnum.MEDIUM: 0.8,
            SignalQualityEnum.LOW: 0.6,
            SignalQualityEnum.UNKNOWN: 0.4
        }
    
    def calculate_compatibility_score(self, request: CompatibilityScoreRequest) -> CompatibilityScoreResponse:
        """Calculate compatibility score for a learner-job combination."""
        start_time = datetime.utcnow()
        request_id = str(uuid.uuid4())
        
        try:
            # Create scoring context
            context = self._create_scoring_context(request, request_id)
            
            # Provenance: Start calculation
            self.provenance_tracker.record_event(
                event_type=ProvenanceEventType.SCORE_CALCULATED,
                description=f"Score calculation started for learner {request.learner_id} in {request.job_family.value}",
                learner_id=request.learner_id,
                details={"job_family": request.job_family.value, "request_id": request_id}
            )
            
            # Process signals
            processed_signals = self._process_signals(request.kash_signals, context)
            
            # Calculate domain breakdowns
            domain_breakdowns = self._calculate_domain_breakdowns(processed_signals, context)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(domain_breakdowns, context)
            
            # Calculate confidence interval
            confidence_interval = self._calculate_confidence_interval(
                overall_score, domain_breakdowns, context
            )
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(processed_signals, domain_breakdowns)
            
            # Create compatibility score
            compatibility_score = self._create_compatibility_score(
                context, overall_score, domain_breakdowns, confidence_interval, quality_metrics
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(compatibility_score, domain_breakdowns)
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Provenance: Complete calculation
            self.provenance_tracker.record_event(
                event_type=ProvenanceEventType.SCORE_CALCULATED,
                description=f"Score calculation completed for learner {request.learner_id} with score {overall_score:.3f}",
                learner_id=request.learner_id,
                score_id=compatibility_score.score_id,
                details={
                    "overall_score": overall_score,
                    "processing_time_ms": processing_time_ms,
                    "signals_processed": len(processed_signals)
                }
            )
            
            return CompatibilityScoreResponse(
                request_id=request_id,
                compatibility_score=compatibility_score,
                processing_time_ms=processing_time_ms,
                signals_processed=len(processed_signals),
                signals_filtered=len(request.kash_signals) - len(processed_signals),
                input_data_quality=quality_metrics,
                calculation_diagnostics=self._get_calculation_diagnostics(context),
                improvement_suggestions=recommendations["improvements"],
                next_steps=recommendations["next_steps"]
            )
            
        except Exception as e:
            # Provenance: Record error
            self.provenance_tracker.record_event(
                event_type=ProvenanceEventType.ERROR_OCCURRED,
                description=f"Error in score calculation for learner {request.learner_id}: {str(e)}",
                learner_id=request.learner_id,
                details={"error": str(e), "request_id": request_id}
            )
            raise
    
    def _create_scoring_context(self, request: CompatibilityScoreRequest, request_id: str) -> ScoringContext:
        """Create scoring context from request."""
        # Get weight configuration
        weight_config = self.weight_manager.get_configuration(
            request.job_family, 
            request.weight_configuration_id
        )
        
        # Get aggregation rules
        aggregation_rules = self._get_aggregation_rules(request.job_family)
        
        # Create signal filter
        signal_filter = self._create_signal_filter(request)
        
        return ScoringContext(
            request_id=request_id,
            learner_id=request.learner_id,
            job_family=request.job_family,
            target_job_id=request.target_job_id,
            weight_config=weight_config,
            aggregation_rules=aggregation_rules,
            signal_filter=signal_filter,
            calculation_version="1.0",
            provenance_tracker=self.provenance_tracker
        )
    
    def _process_signals(self, signals: List[KASHSignal], context: ScoringContext) -> List[KASHSignal]:
        """Process and filter signals."""
        processed_signals = []
        
        for signal in signals:
            # Apply signal filter
            if not self._signal_passes_filter(signal, context.signal_filter):
                continue
            
            # Apply quality multiplier
            quality_multiplier = self.quality_multipliers.get(signal.quality, 0.4)
            adjusted_score = signal.normalized_score * quality_multiplier
            
            # Create processed signal
            processed_signal = KASHSignal(
                domain=signal.domain,
                source=signal.source,
                raw_score=signal.raw_score,
                normalized_score=adjusted_score,
                confidence=signal.confidence,
                quality=signal.quality,
                signal_id=signal.signal_id,
                timestamp=signal.timestamp,
                version=signal.version,
                metadata={
                    **signal.metadata,
                    "quality_multiplier": quality_multiplier,
                    "original_normalized_score": signal.normalized_score,
                    "processed_at": datetime.utcnow().isoformat()
                }
            )
            
            processed_signals.append(processed_signal)
        
        return processed_signals
    
    def _signal_passes_filter(self, signal: KASHSignal, signal_filter: SignalFilter) -> bool:
        """Check if signal passes the filter."""
        # Domain filter
        if signal_filter.domains and signal.domain not in signal_filter.domains:
            return False
        
        # Source filter
        if signal_filter.sources and signal.source not in signal_filter.sources:
            return False
        
        # Quality filter
        quality_hierarchy = {
            SignalQualityEnum.UNKNOWN: 0,
            SignalQualityEnum.LOW: 1,
            SignalQualityEnum.MEDIUM: 2,
            SignalQualityEnum.HIGH: 3
        }
        
        if quality_hierarchy.get(signal.quality, 0) < quality_hierarchy.get(signal_filter.min_quality, 0):
            return False
        
        # Confidence filter
        if signal.confidence < signal_filter.min_confidence:
            return False
        
        # Age filter
        if signal_filter.max_age_days:
            age_days = (datetime.utcnow() - signal.timestamp).days
            if age_days > signal_filter.max_age_days:
                return False
        
        return True
    
    def _calculate_domain_breakdowns(self, signals: List[KASHSignal], 
                                    context: ScoringContext) -> Dict[str, SignalBreakdown]:
        """Calculate breakdown by KASH domains."""
        domain_breakdowns = {}
        
        # Group signals by domain
        domain_signals = {}
        for signal in signals:
            if signal.domain not in domain_signals:
                domain_signals[signal.domain] = []
            domain_signals[signal.domain].append(signal)
        
        # Calculate breakdown for each domain
        for domain, domain_signal_list in domain_signals.items():
            breakdown = self._calculate_single_domain_breakdown(domain, domain_signal_list, context)
            domain_breakdowns[domain] = breakdown
        
        return domain_breakdowns
    
    def _calculate_single_domain_breakdown(self, domain: str, signals: List[KASHSignal],
                                         context: ScoringContext) -> SignalBreakdown:
        """Calculate breakdown for a single domain."""
        if not signals:
            return SignalBreakdown(
                domain=domain,
                signals=[],
                aggregated_score=0.0,
                weight=context.weight_config.get_domain_weight(domain),
                weighted_score=0.0,
                signal_count=0,
                average_confidence=0.0,
                quality_distribution={},
                missing_signals=[],
                stale_signals=[]
            )
        
        # Get aggregation rule for this domain
        rule = context.aggregation_rules.get(domain, self.default_aggregation_rules.get(domain))
        
        # Calculate aggregated score based on rule
        if rule and rule.aggregation_method == "weighted_average":
            aggregated_score = self._calculate_weighted_average(signals, rule.weight_distribution)
        elif rule and rule.aggregation_method == "median":
            aggregated_score = statistics.median([s.normalized_score for s in signals])
        elif rule and rule.aggregation_method == "max":
            aggregated_score = max(s.normalized_score for s in signals)
        else:
            # Default: simple average
            aggregated_score = sum(s.normalized_score for s in signals) / len(signals)
        
        # Calculate metrics
        weight = context.weight_config.get_domain_weight(domain)
        weighted_score = aggregated_score * weight
        average_confidence = sum(s.confidence for s in signals) / len(signals)
        
        # Quality distribution
        quality_distribution = {}
        for signal in signals:
            quality_distribution[signal.quality] = quality_distribution.get(signal.quality, 0) + 1
        
        # Check for missing and stale signals
        missing_signals = self._identify_missing_signals(domain, context)
        stale_signals = self._identify_stale_signals(signals, context)
        
        return SignalBreakdown(
            domain=domain,
            signals=signals,
            aggregated_score=aggregated_score,
            weight=weight,
            weighted_score=weighted_score,
            signal_count=len(signals),
            average_confidence=average_confidence,
            quality_distribution=quality_distribution,
            missing_signals=missing_signals,
            stale_signals=stale_signals
        )
    
    def _calculate_weighted_average(self, signals: List[KASHSignal], 
                                  weight_distribution: Dict[str, float]) -> float:
        """Calculate weighted average of signals."""
        if not weight_distribution:
            # Simple average if no weights provided
            return sum(s.normalized_score for s in signals) / len(signals)
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for signal in signals:
            # Use signal ID or domain to find weight
            signal_weight = weight_distribution.get(signal.signal_id, 
                                                weight_distribution.get(signal.domain, 1.0))
            weighted_sum += signal.normalized_score * signal_weight
            total_weight += signal_weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _identify_missing_signals(self, domain: str, context: ScoringContext) -> List[str]:
        """Identify expected but missing signals for a domain."""
        # This is a simplified implementation
        # In practice, you'd have a registry of expected signals per domain
        expected_signals = {
            "knowledge": ["algorithms", "theory", "concepts"],
            "skills": ["programming", "tools", "frameworks"],
            "abilities": ["problem_solving", "communication", "teamwork"],
            "habits": ["learning", "discipline", "time_management"]
        }
        
        missing = []
        expected = expected_signals.get(domain, [])
        
        # Check if we have signals for expected areas
        existing_signal_areas = set()
        for signal in context.provenance_tracker.get_learner_signals(context.learner_id):
            if signal.domain == domain:
                existing_signal_areas.add(signal.metadata.get("area", "unknown"))
        
        for expected_area in expected:
            if expected_area not in existing_signal_areas:
                missing.append(f"{domain}:{expected_area}")
        
        return missing
    
    def _identify_stale_signals(self, signals: List[KASHSignal], context: ScoringContext) -> List[str]:
        """Identify signals that are too old."""
        stale_threshold = timedelta(days=90)  # 90 days
        stale_signals = []
        
        for signal in signals:
            if datetime.utcnow() - signal.timestamp > stale_threshold:
                stale_signals.append(signal.signal_id)
        
        return stale_signals
    
    def _calculate_overall_score(self, domain_breakdowns: Dict[str, SignalBreakdown],
                               context: ScoringContext) -> float:
        """Calculate overall compatibility score."""
        total_weighted_score = sum(breakdown.weighted_score for breakdown in domain_breakdowns.values())
        
        # Apply minimum requirements if specified
        min_requirements = context.weight_config.minimum_domain_scores
        for domain, min_score in min_requirements.items():
            if domain in domain_breakdowns:
                domain_score = domain_breakdowns[domain].aggregated_score
                if domain_score < min_score:
                    # Apply penalty for not meeting minimum requirements
                    penalty = (min_score - domain_score) * 0.5
                    total_weighted_score -= penalty
        
        return max(0.0, min(1.0, total_weighted_score))
    
    def _calculate_confidence_interval(self, overall_score: float,
                                     domain_breakdowns: Dict[str, SignalBreakdown],
                                     context: ScoringContext) -> ConfidenceInterval:
        """Calculate confidence interval for the overall score."""
        # Calculate variance based on domain variances and signal confidences
        all_confidences = []
        for breakdown in domain_breakdowns.values():
            for signal in breakdown.signals:
                all_confidences.append(signal.confidence)
        
        if not all_confidences:
            # Default confidence interval if no data
            return ConfidenceInterval(
                lower_bound=max(0.0, overall_score - 0.1),
                upper_bound=min(1.0, overall_score + 0.1),
                confidence_level=0.95,
                margin_of_error=0.1
            )
        
        # Calculate standard error based on confidences
        avg_confidence = statistics.mean(all_confidences)
        standard_error = (1 - avg_confidence) * 0.2  # Simplified calculation
        
        # Calculate margin of error (95% confidence level)
        margin_of_error = standard_error * 1.96  # Z-score for 95% confidence
        
        # Calculate confidence interval
        lower_bound = max(0.0, overall_score - margin_of_error)
        upper_bound = min(1.0, overall_score + margin_of_error)
        
        return ConfidenceInterval(
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            confidence_level=0.95,
            margin_of_error=margin_of_error
        )
    
    def _calculate_quality_metrics(self, signals: List[KASHSignal],
                                 domain_breakdowns: Dict[str, SignalBreakdown]) -> Dict[str, Any]:
        """Calculate quality metrics for the calculation."""
        # Data quality score
        if signals:
            quality_scores = [self.quality_multipliers.get(s.quality, 0.4) for s in signals]
            data_quality_score = statistics.mean(quality_scores)
        else:
            data_quality_score = 0.0
        
        # Signal freshness score
        if signals:
            freshness_scores = []
            for signal in signals:
                age_days = (datetime.utcnow() - signal.timestamp).days
                if age_days <= 7:
                    freshness = 1.0
                elif age_days <= 30:
                    freshness = 0.8
                elif age_days <= 90:
                    freshness = 0.6
                else:
                    freshness = 0.4
                freshness_scores.append(freshness)
            
            signal_freshness_score = statistics.mean(freshness_scores)
        else:
            signal_freshness_score = 0.0
        
        # Completeness score
        total_expected_signals = 12  # Simplified: 3 signals per domain × 4 domains
        actual_signals = len(signals)
        completeness_score = min(1.0, actual_signals / total_expected_signals)
        
        return {
            "data_quality_score": data_quality_score,
            "signal_freshness_score": signal_freshness_score,
            "completeness_score": completeness_score,
            "total_signals": len(signals),
            "domains_covered": len(domain_breakdowns)
        }
    
    def _create_compatibility_score(self, context: ScoringContext, overall_score: float,
                                 domain_breakdowns: Dict[str, SignalBreakdown],
                                 confidence_interval: ConfidenceInterval,
                                 quality_metrics: Dict[str, Any]) -> CompatibilityScore:
        """Create the final compatibility score object."""
        # Determine compatibility level
        if overall_score >= 0.8:
            compatibility_level = "excellent"
        elif overall_score >= 0.6:
            compatibility_level = "good"
        elif overall_score >= 0.4:
            compatibility_level = "moderate"
        else:
            compatibility_level = "poor"
        
        # Determine recommendation strength
        avg_confidence = quality_metrics["data_quality_score"]
        if overall_score >= 0.7 and avg_confidence >= 0.8:
            recommendation_strength = "strong"
        elif overall_score >= 0.5 and avg_confidence >= 0.6:
            recommendation_strength = "moderate"
        else:
            recommendation_strength = "weak"
        
        return CompatibilityScore(
            score_id=str(uuid.uuid4()),
            learner_id=context.learner_id,
            job_family=context.job_family,
            target_job_id=context.target_job_id,
            overall_score=overall_score,
            normalized_score=overall_score * 100,
            domain_breakdowns=domain_breakdowns,
            confidence_interval=confidence_interval,
            overall_confidence=avg_confidence,
            data_quality_score=quality_metrics["data_quality_score"],
            signal_freshness_score=quality_metrics["signal_freshness_score"],
            completeness_score=quality_metrics["completeness_score"],
            compatibility_level=compatibility_level,
            recommendation_strength=recommendation_strength,
            calculated_at=datetime.utcnow(),
            calculation_version=context.calculation_version,
            weight_configuration=context.weight_config.config_id
        )
    
    def _generate_recommendations(self, score: CompatibilityScore,
                                domain_breakdowns: Dict[str, SignalBreakdown]) -> Dict[str, List[str]]:
        """Generate improvement recommendations."""
        improvements = []
        next_steps = []
        
        # Analyze weakest domains
        weakest_domains = score.get_weakest_domains(2)
        for domain, domain_score in weakest_domains:
            if domain_score < 0.6:
                improvements.append(f"Improve {domain} competencies (current score: {domain_score:.2f})")
                
                # Specific recommendations based on domain
                if domain == "skills":
                    next_steps.append("Practice technical skills through projects and exercises")
                elif domain == "knowledge":
                    next_steps.append("Study theoretical concepts and best practices")
                elif domain == "abilities":
                    next_steps.append("Develop problem-solving and analytical abilities")
                elif domain == "habits":
                    next_steps.append("Build consistent learning and work habits")
        
        # Check for missing signals
        for breakdown in domain_breakdowns.values():
            if breakdown.missing_signals:
                improvements.append(f"Address missing {breakdown.domain} assessments: {', '.join(breakdown.missing_signals)}")
        
        # Check data quality
        if score.data_quality_score < 0.7:
            improvements.append("Improve data quality through more recent and complete assessments")
            next_steps.append("Schedule updated assessments for better signal quality")
        
        # Overall recommendations
        if score.overall_score >= 0.8:
            next_steps.append("Ready to pursue opportunities in this job family")
        elif score.overall_score >= 0.6:
            next_steps.append("Focus on identified improvement areas before pursuing opportunities")
        else:
            next_steps.append("Consider foundational development before targeting this job family")
        
        return {
            "improvements": improvements[:5],  # Limit to top 5
            "next_steps": next_steps[:5]  # Limit to top 5
        }
    
    def _get_calculation_diagnostics(self, context: ScoringContext) -> List[str]:
        """Get diagnostic messages from the calculation."""
        diagnostics = []
        
        # Check weight configuration
        if not context.weight_config.validate_weights():
            diagnostics.append("Warning: Domain weights do not sum to 1.0")
        
        # Check signal coverage
        if len(context.aggregation_rules) < 4:
            diagnostics.append("Warning: Limited aggregation rules available")
        
        # Check data freshness
        # This would be implemented with actual signal age checking
        
        return diagnostics
    
    def _get_aggregation_rules(self, job_family: JobFamilyEnum) -> Dict[str, SignalAggregationRule]:
        """Get aggregation rules for a job family."""
        # In practice, this would load rules based on job family
        return self.default_aggregation_rules
    
    def _create_signal_filter(self, request: CompatibilityScoreRequest) -> SignalFilter:
        """Create signal filter from request."""
        return SignalFilter(
            filter_id=f"filter_{request.learner_id}_{request.job_family.value}",
            filter_name=f"Filter for {request.learner_id} in {request.job_family.value}",
            min_quality=request.min_signal_quality,
            max_age_days=request.max_signal_age_days,
            created_by="scoring_pipeline"
        )
    
    def _create_default_aggregation_rules(self) -> Dict[str, SignalAggregationRule]:
        """Create default aggregation rules."""
        rules = {}
        
        for domain in ["knowledge", "skills", "abilities", "habits"]:
            rule = SignalAggregationRule(
                rule_id=f"rule_{domain}_default",
                domain=domain,
                rule_name=f"Default {domain} aggregation",
                aggregation_method="weighted_average",
                min_signal_quality=SignalQualityEnum.LOW,
                min_signal_count=1,
                created_by="scoring_pipeline"
            )
            rules[domain] = rule
        
        return rules
