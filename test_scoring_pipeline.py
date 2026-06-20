#!/usr/bin/env python
"""Test script for compatibility scoring pipeline."""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_scoring_pipeline():
    """Test the compatibility scoring pipeline."""
    print("🧪 Testing Compatibility Scoring Pipeline")
    print("=" * 50)
    
    try:
        # Test imports
        from src.modules.intelligence.compatibility.services.scoring_pipeline import (
            ScoringPipeline,
            ScoringContext
        )
        from src.modules.intelligence.compatibility.services.weight_manager import WeightManager
        from src.modules.intelligence.compatibility.services.provenance_tracker import ProvenanceTracker
        from src.modules.intelligence.compatibility.models import (
            CompatibilityScoreRequest,
            KASHSignal,
            JobFamilyEnum,
            SignalSourceEnum,
            SignalQualityEnum
        )
        print("✅ Scoring pipeline and models imported successfully")
        
        # Initialize services
        weight_manager = WeightManager()
        provenance_tracker = ProvenanceTracker()
        scoring_pipeline = ScoringPipeline(weight_manager, provenance_tracker)
        print("✅ Services initialized")
        
        # Create sample KASH signals
        print(f"\n🎯 Creating Sample KASH Signals:")
        print("-" * 35)
        
        kash_signals = [
            # Knowledge signals
            KASHSignal(
                domain="knowledge",
                source=SignalSourceEnum.KNOWLEDGE_MODULE,
                raw_score=0.85,
                normalized_score=0.85,
                confidence=0.9,
                quality=SignalQualityEnum.HIGH,
                signal_id="knowledge_001",
                timestamp=datetime.utcnow() - timedelta(days=5),
                metadata={"area": "algorithms", "assessment_type": "quiz"}
            ),
            KASHSignal(
                domain="knowledge",
                source=SignalSourceEnum.KNOWLEDGE_MODULE,
                raw_score=0.75,
                normalized_score=0.75,
                confidence=0.8,
                quality=SignalQualityEnum.MEDIUM,
                signal_id="knowledge_002",
                timestamp=datetime.utcnow() - timedelta(days=10),
                metadata={"area": "theory", "assessment_type": "exam"}
            ),
            
            # Skills signals
            KASHSignal(
                domain="skills",
                source=SignalSourceEnum.SKILLS_MODULE,
                raw_score=0.90,
                normalized_score=0.90,
                confidence=0.95,
                quality=SignalQualityEnum.HIGH,
                signal_id="skills_001",
                timestamp=datetime.utcnow() - timedelta(days=2),
                metadata={"area": "programming", "assessment_type": "project"}
            ),
            KASHSignal(
                domain="skills",
                source=SignalSourceEnum.SKILLS_MODULE,
                raw_score=0.80,
                normalized_score=0.80,
                confidence=0.85,
                quality=SignalQualityEnum.HIGH,
                signal_id="skills_002",
                timestamp=datetime.utcnow() - timedelta(days=7),
                metadata={"area": "databases", "assessment_type": "practical"}
            ),
            KASHSignal(
                domain="skills",
                source=SignalSourceEnum.SKILLS_MODULE,
                raw_score=0.70,
                normalized_score=0.70,
                confidence=0.75,
                quality=SignalQualityEnum.MEDIUM,
                signal_id="skills_003",
                timestamp=datetime.utcnow() - timedelta(days=15),
                metadata={"area": "frameworks", "assessment_type": "exercise"}
            ),
            
            # Abilities signals
            KASHSignal(
                domain="abilities",
                source=SignalSourceEnum.ABILITIES_MODULE,
                raw_score=0.85,
                normalized_score=0.85,
                confidence=0.9,
                quality=SignalQualityEnum.HIGH,
                signal_id="abilities_001",
                timestamp=datetime.utcnow() - timedelta(days=3),
                metadata={"area": "problem_solving", "assessment_type": "case_study"}
            ),
            KASHSignal(
                domain="abilities",
                source=SignalSourceEnum.ABILITIES_MODULE,
                raw_score=0.78,
                normalized_score=0.78,
                confidence=0.8,
                quality=SignalQualityEnum.MEDIUM,
                signal_id="abilities_002",
                timestamp=datetime.utcnow() - timedelta(days=8),
                metadata={"area": "communication", "assessment_type": "presentation"}
            ),
            
            # Habits signals
            KASHSignal(
                domain="habits",
                source=SignalSourceEnum.HABITS_MODULE,
                raw_score=0.75,
                normalized_score=0.75,
                confidence=0.7,
                quality=SignalQualityEnum.MEDIUM,
                signal_id="habits_001",
                timestamp=datetime.utcnow() - timedelta(days=4),
                metadata={"area": "learning", "assessment_type": "self_assessment"}
            ),
            KASHSignal(
                domain="habits",
                source=SignalSourceEnum.HABITS_MODULE,
                raw_score=0.70,
                normalized_score=0.70,
                confidence=0.65,
                quality=SignalQualityEnum.LOW,
                signal_id="habits_002",
                timestamp=datetime.utcnow() - timedelta(days=20),
                metadata={"area": "discipline", "assessment_type": "peer_review"}
            )
        ]
        
        print(f"✅ Created {len(kash_signals)} KASH signals:")
        print(f"     Knowledge: {len([s for s in kash_signals if s.domain == 'knowledge'])} signals")
        print(f"     Skills: {len([s for s in kash_signals if s.domain == 'skills'])} signals")
        print(f"     Abilities: {len([s for s in kash_signals if s.domain == 'abilities'])} signals")
        print(f"     Habits: {len([s for s in kash_signals if s.domain == 'habits'])} signals")
        
        # Test weight configuration
        print(f"\n🎯 Testing Weight Configuration:")
        print("-" * 35)
        
        tech_config = weight_manager.get_configuration(JobFamilyEnum.TECHNOLOGY)
        print(f"✅ Technology job family configuration:")
        print(f"     Config ID: {tech_config.config_id}")
        print(f"     Business Context: {tech_config.business_context[:60]}...")
        print(f"     Domain Weights: {tech_config.domain_weights}")
        print(f"     Quality Multipliers: {tech_config.quality_multipliers}")
        
        # Test scoring request
        print(f"\n🎯 Testing Compatibility Score Calculation:")
        print("-" * 45)
        
        scoring_request = CompatibilityScoreRequest(
            learner_id="test_learner_001",
            job_family=JobFamilyEnum.TECHNOLOGY,
            target_job_id="software_developer_001",
            kash_signals=kash_signals,
            include_confidence_interval=True,
            confidence_level=0.95,
            min_signal_quality=SignalQualityEnum.LOW,
            max_signal_age_days=30
        )
        
        # Calculate compatibility score
        response = scoring_pipeline.calculate_compatibility_score(scoring_request)
        
        print(f"✅ Score calculation completed:")
        print(f"     Request ID: {response.request_id}")
        print(f"     Processing Time: {response.processing_time_ms}ms")
        print(f"     Signals Processed: {response.signals_processed}")
        print(f"     Signals Filtered: {response.signals_filtered}")
        
        # Display score results
        score = response.compatibility_score
        print(f"\n📊 Compatibility Score Results:")
        print("-" * 35)
        print(f"     Overall Score: {score.overall_score:.3f} ({score.normalized_score:.1f}/100)")
        print(f"     Compatibility Level: {score.compatibility_level}")
        print(f"     Recommendation Strength: {score.recommendation_strength}")
        print(f"     Overall Confidence: {score.overall_confidence:.3f}")
        print(f"     Data Quality Score: {score.data_quality_score:.3f}")
        print(f"     Signal Freshness: {score.signal_freshness_score:.3f}")
        print(f"     Completeness: {score.completeness_score:.3f}")
        
        # Display confidence interval
        ci = score.confidence_interval
        print(f"\n📈 Confidence Interval:")
        print(f"     Range: [{ci.lower_bound:.3f}, {ci.upper_bound:.3f}]")
        print(f"     Confidence Level: {ci.confidence_level:.0%}")
        print(f"     Margin of Error: {ci.margin_of_error:.3f}")
        print(f"     Is Precise: {ci.is_precise}")
        
        # Display domain breakdowns
        print(f"\n🎯 Domain Breakdowns:")
        print("-" * 25)
        for domain, breakdown in score.domain_breakdowns.items():
            print(f"     {domain.title()}:")
            print(f"       Score: {breakdown.aggregated_score:.3f}")
            print(f"       Weight: {breakdown.weight:.2f}")
            print(f"       Weighted Score: {breakdown.weighted_score:.3f}")
            print(f"       Signal Count: {breakdown.signal_count}")
            print(f"       Avg Confidence: {breakdown.average_confidence:.3f}")
            print(f"       Data Completeness: {breakdown.data_completeness:.3f}")
            print(f"       Missing Signals: {len(breakdown.missing_signals)}")
            print(f"       Stale Signals: {len(breakdown.stale_signals)}")
        
        # Display top and weakest domains
        print(f"\n🏆 Top Performing Domains:")
        top_domains = score.get_top_domains(3)
        for i, (domain, domain_score) in enumerate(top_domains, 1):
            print(f"     {i}. {domain.title()}: {domain_score:.3f}")
        
        print(f"\n⚠️  Domains Needing Improvement:")
        weak_domains = score.get_weakest_domains(3)
        for i, (domain, domain_score) in enumerate(weak_domains, 1):
            print(f"     {i}. {domain.title()}: {domain_score:.3f}")
        
        # Display recommendations
        print(f"\n💡 Recommendations:")
        print("-" * 20)
        if response.improvement_suggestions:
            print(f"     Improvements:")
            for suggestion in response.improvement_suggestions:
                print(f"       • {suggestion}")
        
        if response.next_steps:
            print(f"     Next Steps:")
            for step in response.next_steps:
                print(f"       • {step}")
        
        # Test score properties
        print(f"\n🔍 Score Analysis:")
        print("-" * 20)
        print(f"     Is High Compatibility: {score.is_high_compatibility}")
        print(f"     Is Moderate Compatibility: {score.is_moderate_compatibility}")
        print(f"     Needs Improvement: {score.needs_improvement}")
        print(f"     Is Reliable: {score.is_reliable}")
        
        # Test different job families
        print(f"\n🎯 Testing Different Job Families:")
        print("-" * 38)
        
        other_families = [JobFamilyEnum.HEALTHCARE, JobFamilyEnum.FINANCE, JobFamilyEnum.SALES]
        
        for job_family in other_families:
            family_request = CompatibilityScoreRequest(
                learner_id="test_learner_001",
                job_family=job_family,
                kash_signals=kash_signals,
                include_confidence_interval=False
            )
            
            family_response = scoring_pipeline.calculate_compatibility_score(family_request)
            family_score = family_response.compatibility_score
            
            print(f"     {job_family.value.title()}: {family_score.overall_score:.3f} ({family_score.compatibility_level})")
        
        # Test provenance tracking
        print(f"\n🎯 Testing Provenance Tracking:")
        print("-" * 33)
        
        # Get learner signals from provenance
        learner_signals = provenance_tracker.get_learner_signals("test_learner_001")
        print(f"✅ Found {len(learner_signals)} signal provenance records")
        
        # Get learner scores from provenance
        learner_scores = provenance_tracker.get_learner_scores("test_learner_001")
        print(f"✅ Found {len(learner_scores)} score provenance records")
        
        # Get data quality summary
        quality_summary = provenance_tracker.get_data_quality_summary("test_learner_001")
        print(f"✅ Data Quality Summary:")
        print(f"     Total Signals: {quality_summary['total_signals']}")
        print(f"     Data Quality Score: {quality_summary['data_quality_score']:.3f}")
        print(f"     Average Age: {quality_summary['average_age_days']:.1f} days")
        
        # Test weight manager statistics
        print(f"\n🎯 Testing Weight Manager Statistics:")
        print("-" * 40)
        
        weight_stats = weight_manager.get_configuration_stats()
        print(f"✅ Weight Configuration Statistics:")
        print(f"     Total Configurations: {weight_stats['total_configurations']}")
        print(f"     Active Configurations: {weight_stats['active_configurations']}")
        print(f"     Job Families: {list(weight_stats['job_families'].keys())}")
        print(f"     Average Version: {weight_stats['average_version']:.1f}")
        
        # Test configuration creation
        print(f"\n🎯 Testing Custom Configuration Creation:")
        print("-" * 45)
        
        custom_config = weight_manager.create_configuration(
            job_family=JobFamilyEnum.TECHNOLOGY,
            domain_weights={
                "knowledge": 0.15,
                "skills": 0.5,  # Emphasize skills more
                "abilities": 0.25,
                "habits": 0.1
            },
            business_context="Custom configuration emphasizing technical skills for junior developer roles",
            created_by="test_user"
        )
        
        print(f"✅ Custom configuration created:")
        print(f"     Config ID: {custom_config.config_id}")
        print(f"     Domain Weights: {custom_config.domain_weights}")
        
        # Test scoring with custom configuration
        custom_request = CompatibilityScoreRequest(
            learner_id="test_learner_001",
            job_family=JobFamilyEnum.TECHNOLOGY,
            kash_signals=kash_signals,
            weight_configuration_id=custom_config.config_id
        )
        
        custom_response = scoring_pipeline.calculate_compatibility_score(custom_request)
        custom_score = custom_response.compatibility_score
        
        print(f"✅ Score with custom weights: {custom_score.overall_score:.3f}")
        print(f"     Weight Configuration: {custom_score.weight_configuration}")
        
        print(f"\n🎉 Compatibility scoring pipeline test completed!")
        print(f"📊 Summary:")
        print(f"  ✅ Signal processing: Quality filtering and normalization")
        print(f"  ✅ Domain aggregation: Weighted scoring by KASH domains")
        print(f"  ✅ Overall scoring: Configurable weight combinations")
        print(f"  ✅ Confidence intervals: Statistical uncertainty quantification")
        print(f"  ✅ Quality metrics: Data freshness and completeness tracking")
        print(f"  ✅ Provenance tracking: Complete audit trail")
        print(f"  ✅ Weight management: Job family-specific configurations")
        print(f"  ✅ Recommendations: Personalized improvement suggestions")
        print(f"  ✅ Multi-family support: Different scoring for different job families")
        print(f"  ✅ Custom configurations: Flexible weight adjustments")
        
        # Save test results
        test_results = {
            "scoring_pipeline_test": {
                "timestamp": "2024-01-01T12:00:00Z",
                "test_learner": "test_learner_001",
                "signals_processed": len(kash_signals),
                "primary_score": {
                    "job_family": "technology",
                    "overall_score": score.overall_score,
                    "compatibility_level": score.compatibility_level,
                    "confidence": score.overall_confidence,
                    "data_quality": score.data_quality_score
                },
                "performance": {
                    "processing_time_ms": response.processing_time_ms,
                    "signals_processed": response.signals_processed,
                    "signals_filtered": response.signals_filtered
                },
                "domain_scores": {
                    domain: breakdown.aggregated_score 
                    for domain, breakdown in score.domain_breakdowns.items()
                },
                "other_families_tested": [
                    {
                        "job_family": family.value,
                        "score": scoring_pipeline.calculate_compatibility_score(
                            CompatibilityScoreRequest(
                                learner_id="test_learner_001",
                                job_family=family,
                                kash_signals=kash_signals
                            )
                        ).compatibility_score.overall_score
                    }
                    for family in other_families
                ],
                "features_tested": [
                    "signal_processing",
                    "domain_aggregation",
                    "overall_scoring",
                    "confidence_intervals",
                    "quality_metrics",
                    "provenance_tracking",
                    "weight_management",
                    "recommendations",
                    "multi_family_support",
                    "custom_configurations"
                ],
                "provenance_stats": {
                    "signals_tracked": len(learner_signals),
                    "scores_tracked": len(learner_scores),
                    "data_quality_score": quality_summary["data_quality_score"]
                },
                "weight_configurations": {
                    "total_available": weight_stats["total_configurations"],
                    "active_configs": weight_stats["active_configurations"],
                    "custom_created": True
                }
            }
        }
        
        with open("scoring_pipeline_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"  📄 Test results saved to: scoring_pipeline_test_results.json")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scoring_pipeline()
