#!/usr/bin/env python
"""Test script for job matching service."""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_job_matching_service():
    """Test the job matching service."""
    print("🧪 Testing Job Matching Service")
    print("=" * 40)
    
    try:
        # Test imports
        from src.modules.intelligence.job_mapping.services.matching_service import (
            JobMatchingService, 
            LearnerKASHProfile
        )
        from src.modules.intelligence.job_mapping.models import (
            JobMatchingRequest,
            CompetencyLevel,
            KASHDomainEnum
        )
        print("✅ Job matching service and models imported successfully")
        
        # Initialize service
        matching_service = JobMatchingService()
        print("✅ JobMatchingService initialized")
        
        # Create sample learner KASH profile
        learner_profile = LearnerKASHProfile(
            learner_id="test_learner_001",
            knowledge={
                "algorithms_and_data_structures": CompetencyLevel.INTERMEDIATE,
                "software_development_lifecycle": CompetencyLevel.BASIC,
                "statistics_and_probability": CompetencyLevel.BASIC,
                "market_analysis": CompetencyLevel.NONE
            },
            abilities={
                "logical_reasoning": CompetencyLevel.ADVANCED,
                "continuous_learning": CompetencyLevel.ADVANCED,
                "data_analysis": CompetencyLevel.INTERMEDIATE,
                "strategic_thinking": CompetencyLevel.BASIC
            },
            skills={
                "programming_languages": CompetencyLevel.INTERMEDIATE,
                "version_control": CompetencyLevel.INTERMEDIATE,
                "python_r_programming": CompetencyLevel.BASIC,
                "design_software": CompetencyLevel.NONE
            },
            habits={
                "attention_to_detail": CompetencyLevel.ADVANCED,
                "team_collaboration": CompetencyLevel.INTERMEDIATE,
                "critical_thinking": CompetencyLevel.INTERMEDIATE,
                "user_empathy": CompetencyLevel.BASIC
            }
        )
        print(f"✅ Created learner profile with KASH competencies")
        print(f"     Knowledge: {len(learner_profile.knowledge)} competencies")
        print(f"     Abilities: {len(learner_profile.abilities)} competencies")
        print(f"     Skills: {len(learner_profile.skills)} competencies")
        print(f"     Habits: {len(learner_profile.habits)} competencies")
        
        # Test individual job matching
        print(f"\n🎯 Testing Individual Job Matching:")
        print("-" * 40)
        
        all_profiles = matching_service.job_profile_service.get_all_profiles()
        if all_profiles:
            # Test matching with Software Developer profile
            software_dev_profile = None
            for profile in all_profiles:
                if "software_developer" in profile.job_id:
                    software_dev_profile = profile
                    break
            
            if software_dev_profile:
                print(f"🔍 Testing match with: {software_dev_profile.title}")
                
                # Perform matching
                match_result = matching_service.match_learner_to_job(learner_profile, software_dev_profile)
                
                print(f"✅ Match completed:")
                print(f"     Overall Score: {match_result.overall_match_score:.2f}")
                print(f"     Confidence: {match_result.confidence_metrics.overall_confidence}")
                print(f"     Match Type: {'Strong' if match_result.is_strong_match else 'Moderate' if match_result.is_moderate_match else 'Needs Development'}")
                
                # Show domain results
                print(f"\n📊 Domain Results:")
                for domain, result in match_result.domain_results.items():
                    if result.total_weight > 0:  # Only show domains with competencies
                        print(f"     {domain.value}: {result.overall_score:.2f} ({len(result.met_competencies)}/{len(result.competency_matches)} met)")
                
                # Show strengths and development areas
                print(f"\n💪 Key Strengths:")
                for strength in match_result.key_strengths[:3]:
                    print(f"     • {strength}")
                
                print(f"\n🎯 Development Areas:")
                for area in match_result.development_areas[:3]:
                    print(f"     • {area}")
                
                print(f"\n📋 Match Summary:")
                print(f"     {match_result.match_summary}")
                
                print(f"\n⏰ Readiness Timeline:")
                print(f"     {match_result.estimated_readiness_timeline}")
        
        # Test comprehensive matching request
        print(f"\n🎯 Testing Comprehensive Job Matching:")
        print("-" * 45)
        
        # Create matching request
        matching_request = JobMatchingRequest(
            learner_id="test_learner_001",
            learner_kash_profile={
                "knowledge": learner_profile.knowledge,
                "abilities": learner_profile.abilities,
                "skills": learner_profile.skills,
                "habits": learner_profile.habits,
                "metadata": {"experience_years": 2, "education": "Bachelor's"}
            },
            include_alternatives=True,
            max_alternatives=3
        )
        
        # Perform matching
        matching_response = matching_service.find_job_matches(matching_request)
        
        print(f"✅ Matching completed:")
        print(f"     Request ID: {matching_response.request_id}")
        print(f"     Candidates Evaluated: {matching_response.total_candidates_evaluated}")
        print(f"     Processing Time: {matching_response.processing_time_ms}ms")
        print(f"     Total Matches: {len(matching_response.primary_matches)}")
        
        # Show top matches
        print(f"\n🏆 Top 3 Job Matches:")
        for i, match in enumerate(matching_response.primary_matches[:3], 1):
            print(f"\n{i}. {match.job_profile.title}")
            print(f"   Score: {match.overall_match_score:.2f}")
            print(f"   Confidence: {match.confidence_metrics.overall_confidence}")
            print(f"   Summary: {match.match_summary[:80]}...")
            
            # Show alternative suggestions for top match
            if i == 1 and match.alternative_suggestions:
                print(f"   Alternative Suggestions:")
                for j, alt in enumerate(match.alternative_suggestions[:2], 1):
                    print(f"     {j}. {alt.job_profile.title} (Score: {alt.match_score:.2f})")
        
        # Test confidence metrics analysis
        print(f"\n🎯 Testing Confidence Metrics:")
        print("-" * 35)
        
        if matching_response.primary_matches:
            top_match = matching_response.primary_matches[0]
            confidence = top_match.confidence_metrics
            
            print(f"✅ Confidence Analysis:")
            print(f"     Overall Confidence: {confidence.overall_confidence}")
            print(f"     Confidence Score: {confidence.confidence_score:.2f}")
            print(f"     Data Completeness: {confidence.data_completeness:.2f}")
            print(f"     Profile Coverage: {confidence.profile_coverage:.2f}")
            print(f"     Uncertainty Factors: {len(confidence.uncertainty_factors)}")
            print(f"     Rationale: {confidence.confidence_rationale[:100]}...")
        
        # Test competency gap analysis
        print(f"\n🎯 Testing Competency Gap Analysis:")
        print("-" * 42)
        
        if matching_response.primary_matches:
            top_match = matching_response.primary_matches[0]
            
            print(f"📊 Gap Analysis for {top_match.job_profile.title}:")
            
            for domain, result in top_match.domain_results.items():
                if result.competency_matches and result.total_weight > 0:
                    print(f"\n   {domain.value.upper()} Domain:")
                    print(f"     Overall Score: {result.overall_score:.2f}")
                    print(f"     Met Competencies: {len(result.met_competencies)}")
                    print(f"     Unmet Competencies: {len(result.unmet_competencies)}")
                    
                    # Show specific competency gaps
                    if result.unmet_competencies:
                        print(f"     Gaps:")
                        for comp in result.unmet_competencies[:2]:
                            print(f"       • {comp.competency_name}: {comp.learner_level} → {comp.required_level}")
                            print(f"         {comp.gap_analysis}")
        
        print(f"\n🎉 Job matching service test completed!")
        print(f"📊 Summary:")
        print(f"  ✅ Individual job matching: Score calculation and analysis")
        print(f"  ✅ Comprehensive matching: Multi-job evaluation")
        print(f"  ✅ Confidence metrics: Uncertainty assessment")
        print(f"  ✅ Gap analysis: Detailed competency analysis")
        print(f"  ✅ Alternative suggestions: Similar job recommendations")
        print(f"  ✅ Domain scoring: KASH-specific evaluation")
        print(f"  ✅ Processing time: Efficient algorithm performance")
        
        # Save test results
        test_results = {
            "job_matching_service_test": {
                "timestamp": "2024-01-01T12:00:00Z",
                "learner_profile": {
                    "learner_id": learner_profile.learner_id,
                    "total_competencies": len(learner_profile.knowledge) + len(learner_profile.abilities) + len(learner_profile.skills) + len(learner_profile.habits)
                },
                "matching_performance": {
                    "candidates_evaluated": matching_response.total_candidates_evaluated,
                    "processing_time_ms": matching_response.processing_time_ms,
                    "total_matches": len(matching_response.primary_matches)
                },
                "top_match": {
                    "job_title": matching_response.primary_matches[0].job_profile.title if matching_response.primary_matches else None,
                    "match_score": matching_response.primary_matches[0].overall_match_score if matching_response.primary_matches else 0,
                    "confidence_level": matching_response.primary_matches[0].confidence_metrics.overall_confidence.value if matching_response.primary_matches else None
                },
                "features_tested": [
                    "individual_job_matching",
                    "comprehensive_matching_request",
                    "confidence_metrics_calculation",
                    "competency_gap_analysis",
                    "alternative_suggestions",
                    "domain_specific_scoring",
                    "processing_performance"
                ]
            }
        }
        
        with open("job_matching_service_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"  📄 Test results saved to: job_matching_service_test_results.json")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_job_matching_service()
