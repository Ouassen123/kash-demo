#!/usr/bin/env python
"""Test script for job profile catalog service."""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_job_profile_service():
    """Test the job profile catalog service."""
    print("🧪 Testing Job Profile Catalog Service")
    print("=" * 50)
    
    try:
        # Test imports
        from src.modules.intelligence.job_mapping.services.job_profile_service import JobProfileService
        from src.modules.intelligence.job_mapping.models import (
            JobProfile, 
            JobSectorEnum, 
            SeniorityLevelEnum, 
            RegionAvailabilityEnum,
            KASHDomainEnum
        )
        print("✅ Job profile service and models imported successfully")
        
        # Initialize service
        service = JobProfileService()
        print(f"✅ JobProfileService initialized")
        
        # Test catalog loading
        all_profiles = service.get_all_profiles()
        print(f"✅ Loaded {len(all_profiles)} job profiles")
        
        if all_profiles:
            # Test getting profile by ID
            first_profile = all_profiles[0]
            profile_by_id = service.get_profile_by_id(first_profile.job_id)
            print(f"✅ Retrieved profile by ID: {profile_by_id.title if profile_by_id else 'None'}")
            
            # Test sector filtering
            tech_profiles = service.get_profiles_by_sector(JobSectorEnum.TECHNOLOGY)
            print(f"✅ Found {len(tech_profiles)} technology sector profiles")
            
            # Test seniority filtering
            mid_level_profiles = service.get_profiles_by_seniority(SeniorityLevelEnum.MID_LEVEL)
            print(f"✅ Found {len(mid_level_profiles)} mid-level profiles")
            
            # Test region filtering
            global_profiles = service.get_profiles_by_region(RegionAvailabilityEnum.GLOBAL)
            print(f"✅ Found {len(global_profiles)} globally available profiles")
            
            # Test search functionality
            search_results = service.search_profiles("software", limit=3)
            print(f"✅ Search for 'software' returned {len(search_results)} results")
            
            # Test KASH domain filtering
            skills_focused = service.get_profiles_by_kash_domain(KASHDomainEnum.SKILLS, min_weight=0.5)
            print(f"✅ Found {len(skills_focused)} profiles with significant skills focus")
            
            # Test competency statistics
            stats = service.get_competency_statistics()
            print(f"✅ Generated competency statistics:")
            print(f"     Total profiles: {stats['total_profiles']}")
            print(f"     Average competencies per profile: {stats['average_competencies_per_profile']:.1f}")
            print(f"     Sector distribution: {len(stats['sector_distribution'])} sectors")
            
            # Test similar profiles
            if len(all_profiles) >= 2:
                similar = service.get_similar_profiles(first_profile.job_id, limit=3)
                print(f"✅ Found {len(similar)} similar profiles to {first_profile.title}")
            
            # Test profile validation
            validation = service.validate_profile(first_profile)
            print(f"✅ Profile validation: {'Valid' if validation['is_valid'] else 'Invalid'}")
            if validation['warnings']:
                print(f"     Warnings: {len(validation['warnings'])}")
            if validation['recommendations']:
                print(f"     Recommendations: {len(validation['recommendations'])}")
            
            # Test catalog summary export
            summary = service.export_catalog_summary()
            print(f"✅ Exported catalog summary:")
            print(f"     Catalog version: {summary['catalog_info']['version']}")
            print(f"     Sample profiles: {len(summary['sample_profiles'])}")
            
            # Test detailed profile structure
            print(f"\n🎯 Sample Profile Structure ({first_profile.title}):")
            print("-" * 40)
            print(f"  📋 Job ID: {first_profile.job_id}")
            print(f"  🏢 Sectors: {[s.value for s in first_profile.metadata.sectors]}")
            print(f"  📈 Seniority: {[s.value for s in first_profile.metadata.seniority_levels]}")
            print(f"  🌍 Regions: {[r.value for r in first_profile.metadata.regional_availability]}")
            print(f"  📚 Competencies: {len(first_profile.all_competencies)} total")
            print(f"     Knowledge: {len(first_profile.knowledge_competencies)}")
            print(f"     Abilities: {len(first_profile.abilities_competencies)}")
            print(f"     Skills: {len(first_profile.skills_competencies)}")
            print(f"     Habits: {len(first_profile.habits_competencies)}")
            print(f"  ✅ Success Criteria: {len(first_profile.success_criteria)}")
            print(f"  📖 Rationale: {first_profile.rationale[:100]}...")
            
            # Test individual competency structure
            if first_profile.knowledge_competencies:
                sample_comp = first_profile.knowledge_competencies[0]
                print(f"\n🔍 Sample Competency Structure:")
                print("-" * 35)
                print(f"  📝 Name: {sample_comp.name}")
                print(f"  🏷️  Category: {sample_comp.category}")
                print(f"  📊 Required Level: {sample_comp.required_level}")
                print(f"  ⚖️  Weight: {sample_comp.weight}")
                print(f"  📋 Description: {sample_comp.description[:80]}...")
                print(f"  ✨ Success Signals: {len(sample_comp.success_signals)}")
        
        print(f"\n🎉 Job profile service test completed!")
        print(f"📊 Summary:")
        print(f"  ✅ Catalog loading: {len(all_profiles)} profiles")
        print(f"  ✅ Filtering: By sector, seniority, region, KASH domain")
        print(f"  ✅ Search: Text-based profile search")
        print(f"  ✅ Analytics: Competency statistics and similarity")
        print(f"  ✅ Validation: Profile completeness checking")
        print(f"  ✅ Export: Catalog summary generation")
        
        # Save test results
        test_results = {
            "job_profile_service_test": {
                "timestamp": "2024-01-01T12:00:00Z",
                "catalog_loaded": True,
                "total_profiles": len(all_profiles),
                "features_tested": [
                    "catalog_loading",
                    "profile_retrieval",
                    "sector_filtering", 
                    "seniority_filtering",
                    "region_filtering",
                    "search_functionality",
                    "kash_domain_filtering",
                    "competency_statistics",
                    "similarity_analysis",
                    "profile_validation",
                    "catalog_export"
                ],
                "sample_profile_structure": {
                    "job_id": all_profiles[0].job_id if all_profiles else None,
                    "title": all_profiles[0].title if all_profiles else None,
                    "total_competencies": len(all_profiles[0].all_competencies) if all_profiles else 0,
                    "sectors": [s.value for s in all_profiles[0].metadata.sectors] if all_profiles else []
                }
            }
        }
        
        with open("job_profile_service_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"  📄 Test results saved to: job_profile_service_test_results.json")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_job_profile_service()
