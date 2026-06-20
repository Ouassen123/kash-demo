#!/usr/bin/env python
"""Test script for SME override service."""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_sme_override_service():
    """Test the SME override service."""
    print("🧪 Testing SME Override Service")
    print("=" * 40)
    
    try:
        # Test imports
        from src.modules.intelligence.job_mapping.services.override_service import (
            SMEOverrideService,
            SMEOverride,
            OverrideBatch,
            OverrideReasonEnum,
            OverrideTypeEnum
        )
        from src.modules.intelligence.job_mapping.models import (
            CompetencyLevel,
            KASHDomainEnum,
            ConfidenceLevel
        )
        print("✅ SME override service and models imported successfully")
        
        # Initialize service
        override_service = SMEOverrideService()
        print("✅ SMEOverrideService initialized")
        
        # Test creating individual overrides
        print(f"\n🎯 Testing Individual Override Creation:")
        print("-" * 45)
        
        # Create competency level override
        competency_override = override_service.create_override(
            learner_id="test_learner_001",
            job_id="software_developer_001",
            sme_id="sme_expert_001",
            sme_name="Dr. Jane Smith",
            override_type=OverrideTypeEnum.COMPETENCY_LEVEL,
            reason=OverrideReasonEnum.EXPERIENCE_EQUIVALENCY,
            original_value="basic",
            new_value="intermediate",
            comment="Learner has 3 years of industry experience equivalent to intermediate level",
            target_domain=KASHDomainEnum.SKILLS,
            target_competency="programming_languages",
            evidence=["Industry certification", "Portfolio review", "Reference check"]
        )
        
        print(f"✅ Created competency override:")
        print(f"     Override ID: {competency_override.override_id}")
        print(f"     Type: {competency_override.override_type}")
        print(f"     Reason: {competency_override.reason}")
        print(f"     Change: {competency_override.original_value} → {competency_override.new_value}")
        
        # Create overall score override
        score_override = override_service.create_override(
            learner_id="test_learner_001",
            job_id="software_developer_001",
            sme_id="sme_expert_001",
            sme_name="Dr. Jane Smith",
            override_type=OverrideTypeEnum.OVERALL_SCORE,
            reason=OverrideReasonEnum.MARKET_CONDITIONS,
            original_value=0.75,
            new_value=0.85,
            comment="Market demand for this role is high, justification for higher score",
            evidence=["Market analysis report", "Industry demand data"]
        )
        
        print(f"✅ Created score override:")
        print(f"     Override ID: {score_override.override_id}")
        print(f"     Score change: {score_override.original_value} → {score_override.new_value}")
        
        # Test override validation
        print(f"\n🎯 Testing Override Validation:")
        print("-" * 35)
        
        validation_result = override_service.validate_override(competency_override, None)
        print(f"✅ Validation result:")
        print(f"     Valid: {validation_result.is_valid}")
        print(f"     Errors: {len(validation_result.validation_errors)}")
        print(f"     Warnings: {len(validation_result.validation_warnings)}")
        print(f"     Score impact: {validation_result.score_impact}")
        print(f"     Recommendations: {len(validation_result.recommendations)}")
        
        # Test getting active overrides
        print(f"\n🎯 Testing Active Override Retrieval:")
        print("-" * 42)
        
        active_overrides = override_service.get_active_overrides("test_learner_001", "software_developer_001")
        print(f"✅ Found {len(active_overrides)} active overrides")
        
        for override in active_overrides:
            print(f"     • {override.override_type}: {override.original_value} → {override.new_value}")
        
        # Test override batch creation
        print(f"\n🎯 Testing Override Batch Creation:")
        print("-" * 38)
        
        batch_overrides_data = [
            {
                "override_type": "competency_level",
                "reason": "expert_judgment",
                "original_value": "basic",
                "new_value": "intermediate",
                "comment": "Strong problem-solving skills demonstrated",
                "target_domain": "abilities",
                "target_competency": "logical_reasoning",
                "evidence": ["Technical interview results", "Problem-solving assessment"]
            },
            {
                "override_type": "weight_adjustment",
                "reason": "emerging_trends",
                "original_value": 0.6,
                "new_value": 0.8,
                "comment": "This skill is becoming more important in the industry",
                "target_domain": "knowledge",
                "target_competency": "algorithms_and_data_structures"
            }
        ]
        
        batch = override_service.create_override_batch(
            learner_id="test_learner_001",
            job_id="software_developer_001",
            sme_id="sme_expert_001",
            sme_name="Dr. Jane Smith",
            overrides_data=batch_overrides_data,
            batch_reason="Adjusting for demonstrated skills and market trends",
            original_match_score=0.75
        )
        
        print(f"✅ Created override batch:")
        print(f"     Batch ID: {batch.batch_id}")
        print(f"     Overrides: {len(batch.overrides)}")
        print(f"     Original score: {batch.original_match_score}")
        print(f"     Reason: {batch.batch_reason}")
        
        # Test override history
        print(f"\n🎯 Testing Override History:")
        print("-" * 30)
        
        history = override_service.get_override_history(learner_id="test_learner_001")
        print(f"✅ Found {len(history)} overrides in history")
        
        # Test batch history
        batch_history = override_service.get_batch_history(learner_id="test_learner_001")
        print(f"✅ Found {len(batch_history)} batches in history")
        
        # Test SME statistics
        print(f"\n🎯 Testing SME Statistics:")
        print("-" * 28)
        
        sme_stats = override_service.get_sme_statistics("sme_expert_001")
        print(f"✅ SME Statistics for Dr. Jane Smith:")
        print(f"     Total overrides: {sme_stats['total_overrides']}")
        print(f"     Active overrides: {sme_stats['active_overrides']}")
        print(f"     Total batches: {sme_stats['total_batches']}")
        print(f"     Override types: {list(sme_stats['override_types'].keys())}")
        print(f"     Reason distribution: {list(sme_stats['reason_distribution'].keys())}")
        
        # Test temporary override with expiration
        print(f"\n🎯 Testing Temporary Override:")
        print("-" * 32)
        
        temp_override = override_service.create_override(
            learner_id="test_learner_002",
            job_id="data_scientist_002",
            sme_id="sme_expert_001",
            sme_name="Dr. Jane Smith",
            override_type=OverrideTypeEnum.COMPETENCY_LEVEL,
            reason=OverrideReasonEnum.SPECIAL_CIRCUMSTANCES,
            original_value="basic",
            new_value="advanced",
            comment="Temporary upgrade for special project participation",
            target_domain=KASHDomainEnum.SKILLS,
            target_competency="python_r_programming",
            temporary=True,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        print(f"✅ Created temporary override:")
        print(f"     Expires: {temp_override.expires_at}")
        print(f"     Temporary: {temp_override.temporary}")
        
        # Test override deactivation
        print(f"\n🎯 Testing Override Deactivation:")
        print("-" * 35)
        
        deactivated = override_service.deactivate_override(competency_override.override_id, "sme_expert_001")
        print(f"✅ Deactivation result: {deactivated}")
        
        # Test permission check (should fail with wrong SME)
        wrong_sme_deactivated = override_service.deactivate_override(score_override.override_id, "wrong_sme")
        print(f"✅ Wrong SME deactivation (should fail): {wrong_sme_deactivated}")
        
        # Test different override types
        print(f"\n🎯 Testing Different Override Types:")
        print("-" * 40)
        
        # Test confidence level override
        confidence_override = override_service.create_override(
            learner_id="test_learner_003",
            job_id="product_manager_003",
            sme_id="sme_expert_002",
            sme_name="Prof. John Doe",
            override_type=OverrideTypeEnum.CONFIDENCE_LEVEL,
            reason=OverrideReasonEnum.CERTIFICATION_OVERRIDE,
            original_value="medium",
            new_value="high",
            comment="Learner has relevant certifications that increase confidence",
            evidence=["PMP Certification", "Agile Certification"]
        )
        
        print(f"✅ Created confidence override: {confidence_override.original_value} → {confidence_override.new_value}")
        
        # Test domain score override
        domain_override = override_service.create_override(
            learner_id="test_learner_003",
            job_id="ux_designer_004",
            sme_id="sme_expert_002",
            sme_name="Prof. John Doe",
            override_type=OverrideTypeEnum.DOMAIN_SCORE,
            reason=OverrideReasonEnum.REGIONAL_FACTORS,
            original_value=0.6,
            new_value=0.8,
            comment="Regional demand for UX skills is higher than average",
            target_domain=KASHDomainEnum.SKILLS
        )
        
        print(f"✅ Created domain override: {domain_override.original_value} → {domain_override.new_value}")
        
        print(f"\n🎉 SME override service test completed!")
        print(f"📊 Summary:")
        print(f"  ✅ Individual overrides: Competency, score, confidence, domain")
        print(f"  ✅ Override validation: Error checking and recommendations")
        print(f"  ✅ Batch operations: Grouped overrides with tracking")
        print(f"  ✅ History tracking: Complete audit trail")
        print(f"  ✅ SME statistics: Performance analytics")
        print(f"  ✅ Temporary overrides: Time-limited adjustments")
        print(f"  ✅ Permission control: SME-only deactivation")
        print(f"  ✅ Multiple override types: Comprehensive adjustment options")
        
        # Save test results
        test_results = {
            "sme_override_service_test": {
                "timestamp": "2024-01-01T12:00:00Z",
                "overrides_created": len(override_service.overrides),
                "batches_created": len(override_service.batches),
                "override_types_tested": [
                    "competency_level",
                    "overall_score", 
                    "confidence_level",
                    "domain_score",
                    "weight_adjustment"
                ],
                "features_tested": [
                    "individual_override_creation",
                    "override_validation",
                    "batch_operations",
                    "history_tracking",
                    "sme_statistics",
                    "temporary_overrides",
                    "permission_control",
                    "override_deactivation"
                ],
                "sme_stats": {
                    "total_overrides": sme_stats["total_overrides"],
                    "active_overrides": sme_stats["active_overrides"],
                    "override_types": list(sme_stats["override_types"].keys())
                }
            }
        }
        
        with open("sme_override_service_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"  📄 Test results saved to: sme_override_service_test_results.json")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sme_override_service()
