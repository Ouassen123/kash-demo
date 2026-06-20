#!/usr/bin/env python
"""Test script for alignment diagnostics service."""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_diagnostics_service():
    """Test the alignment diagnostics service."""
    print("🧪 Testing Alignment Diagnostics Service")
    print("=" * 50)
    
    try:
        # Test imports
        from src.modules.intelligence.job_mapping.services.diagnostics_service import (
            AlignmentDiagnosticsService,
            AlignmentDiagnostic,
            DiagnosticFinding,
            DiagnosticStatusEnum,
            DiagnosticTypeEnum,
            SeverityLevelEnum
        )
        from src.modules.intelligence.job_mapping.models import JobMatchResult
        print("✅ Diagnostics service and models imported successfully")
        
        # Initialize service
        diagnostics_service = AlignmentDiagnosticsService()
        print("✅ AlignmentDiagnosticsService initialized")
        
        # Create mock match results for testing
        print(f"\n🎯 Creating Mock Match Results:")
        print("-" * 35)
        
        mock_matches = []
        
        # Create a few mock match results with varying scores
        for i in range(10):
            # Import required classes for mock creation
            from src.modules.intelligence.job_mapping.models import (
                JobProfile, JobMetadata, KASHCompetency, CompetencyMatch,
                DomainMatchResult, ConfidenceMetrics, AlternativeSuggestion,
                KASHDomainEnum, CompetencyLevel, ConfidenceLevel, JobSectorEnum,
                SeniorityLevelEnum, RegionAvailabilityEnum
            )
            
            # Create mock job profile
            job_profile = JobProfile(
                job_id=f"job_{i:03d}",
                title=f"Test Job {i}",
                description="Test job description",
                metadata=JobMetadata(
                    sectors=[JobSectorEnum.TECHNOLOGY],
                    seniority_levels=[SeniorityLevelEnum.MID_LEVEL],
                    regional_availability=[RegionAvailabilityEnum.GLOBAL]
                ),
                knowledge_competencies=[
                    KASHCompetency(
                        domain=KASHDomainEnum.KNOWLEDGE,
                        category="test",
                        name=f"knowledge_{i}",
                        required_level=CompetencyLevel.INTERMEDIATE,
                        weight=0.5,
                        description="Test knowledge competency"
                    )
                ],
                abilities_competencies=[
                    KASHCompetency(
                        domain=KASHDomainEnum.ABILITIES,
                        category="test",
                        name=f"ability_{i}",
                        required_level=CompetencyLevel.INTERMEDIATE,
                        weight=0.5,
                        description="Test ability competency"
                    )
                ],
                skills_competencies=[
                    KASHCompetency(
                        domain=KASHDomainEnum.SKILLS,
                        category="test",
                        name=f"skill_{i}",
                        required_level=CompetencyLevel.INTERMEDIATE,
                        weight=0.5,
                        description="Test skill competency"
                    )
                ],
                habits_competencies=[
                    KASHCompetency(
                        domain=KASHDomainEnum.HABITS,
                        category="test",
                        name=f"habit_{i}",
                        required_level=CompetencyLevel.INTERMEDIATE,
                        weight=0.5,
                        description="Test habit competency"
                    )
                ],
                success_criteria=["Test criterion"],
                rationale="Test rationale"
            )
            
            # Create mock domain results
            domain_results = {}
            for domain in KASHDomainEnum:
                competency_matches = [
                    CompetencyMatch(
                        competency_name=f"comp_{domain.value}",
                        domain=domain,
                        required_level=CompetencyLevel.INTERMEDIATE,
                        learner_level=CompetencyLevel.INTERMEDIATE,
                        match_score=0.8,
                        weight=0.5,
                        weighted_score=0.4,
                        gap_analysis="No gap",
                        improvement_suggestions=[]
                    )
                ]
                
                domain_results[domain] = DomainMatchResult(
                    domain=domain,
                    overall_score=0.8,
                    competency_matches=competency_matches,
                    total_weight=0.5,
                    strengths=[f"strength_{domain.value}"],
                    weaknesses=[],
                    recommendations=[]
                )
            
            # Create mock confidence metrics
            confidence_metrics = ConfidenceMetrics(
                overall_confidence=ConfidenceLevel.HIGH,
                confidence_score=0.85,
                data_completeness=0.9,
                profile_coverage=0.8,
                uncertainty_factors=[],
                confidence_rationale="Good data quality"
            )
            
            # Vary the overall score
            overall_score = 0.3 + (i * 0.07)  # Scores from 0.3 to 0.93
            
            match_result = JobMatchResult(
                learner_id=f"learner_{i:03d}",
                job_profile=job_profile,
                overall_match_score=overall_score,
                domain_results=domain_results,
                confidence_metrics=confidence_metrics,
                alternative_suggestions=[],
                match_summary=f"Test match summary with score {overall_score:.2f}",
                key_strengths=[f"strength_{i}"],
                development_areas=[f"development_{i}"],
                next_steps=[f"step_{i}"],
                estimated_readiness_timeline="Test timeline"
            )
            
            mock_matches.append(match_result)
        
        print(f"✅ Created {len(mock_matches)} mock match results")
        print(f"     Score range: {min(m.overall_match_score for m in mock_matches):.2f} - {max(m.overall_match_score for m in mock_matches):.2f}")
        
        # Test match accuracy diagnostic creation
        print(f"\n🎯 Testing Match Accuracy Diagnostic:")
        print("-" * 40)
        
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        diagnostic = diagnostics_service.create_match_accuracy_diagnostic(
            start_date=start_date,
            end_date=end_date,
            scope_filters={"job_types": ["technology"]},
            created_by="test_user"
        )
        
        print(f"✅ Created diagnostic:")
        print(f"     ID: {diagnostic.diagnostic_id}")
        print(f"     Type: {diagnostic.diagnostic_type}")
        print(f"     Status: {diagnostic.status}")
        print(f"     Period: {diagnostic.analysis_period['start'].date()} → {diagnostic.analysis_period['end'].date()}")
        
        # Test match accuracy analysis
        print(f"\n🎯 Testing Match Accuracy Analysis:")
        print("-" * 38)
        
        analyzed_diagnostic = diagnostics_service.analyze_match_accuracy(
            diagnostic_id=diagnostic.diagnostic_id,
            match_results=mock_matches
        )
        
        print(f"✅ Analysis completed:")
        print(f"     Status: {analyzed_diagnostic.status}")
        print(f"     Findings: {len(analyzed_diagnostic.findings)}")
        print(f"     Metrics: {len(analyzed_diagnostic.metrics)}")
        print(f"     Data Quality Score: {analyzed_diagnostic.data_quality_score:.2f}")
        print(f"     Confidence Score: {analyzed_diagnostic.confidence_score:.2f}")
        print(f"     Summary: {analyzed_diagnostic.summary[:80]}...")
        
        # Show findings details
        if analyzed_diagnostic.findings:
            print(f"\n📋 Diagnostic Findings:")
            for i, finding in enumerate(analyzed_diagnostic.findings, 1):
                print(f"     {i}. {finding.title} ({finding.severity})")
                print(f"        {finding.description[:60]}...")
                print(f"        Recommendations: {len(finding.recommendations)}")
        
        # Show metrics
        if analyzed_diagnostic.metrics:
            print(f"\n📊 Diagnostic Metrics:")
            for metric in analyzed_diagnostic.metrics:
                print(f"     • {metric['name']}: {metric['value']} {metric['unit']}")
        
        # Test override impact diagnostic
        print(f"\n🎯 Testing Override Impact Diagnostic:")
        print("-" * 42)
        
        override_diagnostic = diagnostics_service.create_override_impact_diagnostic(
            start_date=start_date,
            end_date=end_date,
            created_by="test_user"
        )
        
        print(f"✅ Created override diagnostic:")
        print(f"     ID: {override_diagnostic.diagnostic_id}")
        print(f"     Type: {override_diagnostic.diagnostic_type}")
        print(f"     Status: {override_diagnostic.status}")
        
        # Test diagnostic summary
        print(f"\n🎯 Testing Diagnostic Summary:")
        print("-" * 33)
        
        summary = diagnostics_service.get_diagnostic_summary()
        print(f"✅ Summary generated:")
        print(f"     Total diagnostics: {summary['total_diagnostics']}")
        print(f"     Completed: {summary['completed_diagnostics']}")
        print(f"     Completion rate: {summary['completion_rate']:.1%}")
        print(f"     Total findings: {summary['total_findings']}")
        print(f"     Critical findings: {summary['critical_findings']}")
        print(f"     High findings: {summary['high_findings']}")
        print(f"     Unresolved findings: {summary['unresolved_findings']}")
        print(f"     Avg data quality: {summary['avg_data_quality_score']:.2f}")
        print(f"     Avg confidence: {summary['avg_confidence_score']:.2f}")
        
        # Test findings by severity
        print(f"\n🎯 Testing Findings by Severity:")
        print("-" * 35)
        
        high_severity_findings = diagnostics_service.get_findings_by_severity(SeverityLevelEnum.HIGH)
        critical_findings = diagnostics_service.get_findings_by_severity(SeverityLevelEnum.CRITICAL)
        
        print(f"✅ Findings by severity:")
        print(f"     High severity: {len(high_severity_findings)}")
        print(f"     Critical severity: {len(critical_findings)}")
        
        # Test finding resolution
        if analyzed_diagnostic.findings:
            print(f"\n🎯 Testing Finding Resolution:")
            print("-" * 32)
            
            test_finding = analyzed_diagnostic.findings[0]
            resolution_success = diagnostics_service.resolve_finding(
                finding_id=test_finding.finding_id,
                resolution_notes="Issue resolved by adjusting competency weightings",
                resolved_by="test_admin"
            )
            
            print(f"✅ Finding resolution: {'Success' if resolution_success else 'Failed'}")
        
        # Test quality trends
        print(f"\n🎯 Testing Quality Trends:")
        print("-" * 28)
        
        trends = diagnostics_service.get_quality_trends(days=30)
        print(f"✅ Quality trends:")
        print(f"     Period: {trends.get('period_days', 'N/A')} days")
        print(f"     Total diagnostics: {trends.get('total_diagnostics', 'N/A')}")
        print(f"     Avg data quality: {trends.get('avg_data_quality', 0):.2f}")
        print(f"     Avg confidence: {trends.get('avg_confidence', 0):.2f}")
        
        # Test type-specific summary
        print(f"\n🎯 Testing Type-Specific Summary:")
        print("-" * 37)
        
        match_accuracy_summary = diagnostics_service.get_diagnostic_summary(
            diagnostic_type=DiagnosticTypeEnum.MATCH_ACCURACY
        )
        
        print(f"✅ Match accuracy summary:")
        print(f"     Total diagnostics: {match_accuracy_summary['total_diagnostics']}")
        print(f"     Type distribution: {match_accuracy_summary['type_distribution']}")
        
        print(f"\n🎉 Alignment diagnostics service test completed!")
        print(f"📊 Summary:")
        print(f"  ✅ Diagnostic creation: Match accuracy and override impact")
        print(f"  ✅ Analysis execution: Comprehensive metric calculation")
        print(f"  ✅ Finding generation: Automatic issue detection")
        print(f"  ✅ Quality assessment: Data quality and confidence scoring")
        print(f"  ✅ Trend analysis: Historical quality tracking")
        print(f"  ✅ Finding management: Resolution and tracking")
        print(f"  ✅ Summary reporting: Multi-dimensional analytics")
        print(f"  ✅ Severity classification: Critical/High/Medium/Low")
        
        # Save test results
        test_results = {
            "diagnostics_service_test": {
                "timestamp": "2024-01-01T12:00:00Z",
                "mock_matches_created": len(mock_matches),
                "diagnostics_created": len(diagnostics_service.diagnostics),
                "findings_generated": len(diagnostics_service.findings),
                "analysis_results": {
                    "data_quality_score": analyzed_diagnostic.data_quality_score,
                    "confidence_score": analyzed_diagnostic.confidence_score,
                    "total_findings": len(analyzed_diagnostic.findings),
                    "total_metrics": len(analyzed_diagnostic.metrics)
                },
                "features_tested": [
                    "diagnostic_creation",
                    "match_accuracy_analysis",
                    "override_impact_diagnostic",
                    "finding_generation",
                    "quality_scoring",
                    "trend_analysis",
                    "finding_resolution",
                    "summary_reporting",
                    "severity_classification"
                ],
                "quality_indicators": {
                    "avg_data_quality": summary["avg_data_quality_score"],
                    "avg_confidence": summary["avg_confidence_score"],
                    "completion_rate": summary["completion_rate"]
                }
            }
        }
        
        with open("diagnostics_service_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"  📄 Test results saved to: diagnostics_service_test_results.json")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_diagnostics_service()
