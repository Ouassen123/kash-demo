#!/usr/bin/env python
"""Test script for scoring and feedback system."""

import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

async def test_scoring_feedback():
    """Test the scoring and feedback system."""
    print("🧪 Testing Scoring and Feedback System")
    print("=" * 50)
    
    from src.modules.skills.code_analysis import CodeAnalysisEngine
    from src.modules.skills.code_analysis.context import RepositoryInput
    from src.modules.skills.code_analysis.models import AnalyzerFinding, SeverityLevel
    
    # Create temporary directory with problematic code
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create Java file with multiple issues
        java_file = temp_path / "ProblematicClass.java"
        java_file.write_text("""
import java.util.*;
import java.io.*;

class badClass {
    public String name;
    public int age;
    
    public int calculate_Total(int a, int b, int c, int d, int e, int f, int g) {
        if (a > 0) {
            if (b > 0) {
                if (c > 0) {
                    for (int i = 0; i < 10; i++) {
                        if (i % 2 == 0) {
                            System.out.println("Even: " + i);
                        } else {
                            System.out.println("Odd: " + i);
                        }
                    }
                }
            }
        }
        return a + b + c + d + e + f + g;
    }
}""")
        
        print(f"📁 Created test files in: {temp_path}")
        print(f"  ☕ Java: {java_file.name} (with multiple violations)")
        
        # Test with educational profile (includes scoring and feedback)
        engine = CodeAnalysisEngine()
        
        try:
            repo_input = RepositoryInput(
                submission_id="test-scoring-feedback",
                learner_id="test-learner",
                template_id="test-template",
                root_path=temp_path,
                files=[java_file],
                analysis_profile="educational",
            )
            
            result = await engine.analyze(repo_input)
            
            print(f"\n✅ Analysis completed successfully!")
            print(f"  📊 Overall Score: {result.overall_score:.1f}")
            print(f"  🎯 Confidence: {result.confidence:.2f}")
            print(f"  🔧 Analyzers used: {[report.analyzer_name for report in result.analyzer_reports]}")
            print(f"  📋 Total findings: {sum(len(report.findings) for report in result.analyzer_reports)}")
            
            # Show quality score details
            if hasattr(result, 'quality_score') and result.quality_score:
                qs = result.quality_score
                print(f"\n📈 Quality Score Breakdown:")
                print(f"  🎯 Grade: {qs.grade}")
                print(f"  📊 Overall: {qs.overall_score:.1f}/100")
                print(f"  💪 Strengths: {len(qs.strengths)}")
                print(f"  ⚠️  Weaknesses: {len(qs.weaknesses)}")
                
                print(f"\n📋 Metric Details:")
                for metric in qs.metrics:
                    print(f"  🔍 {metric.name}: {metric.score:.1f}/100 (weight: {metric.weight:.2f})")
                    print(f"     📝 {metric.description}")
                    print(f"     📊 Findings: {metric.findings_count}")
                
                print(f"\n💪 Strengths:")
                for strength in qs.strengths:
                    print(f"  ✅ {strength}")
                
                print(f"\n⚠️  Weaknesses:")
                for weakness in qs.weaknesses:
                    print(f"  ❌ {weakness}")
                
                print(f"\n🎯 Recommendations:")
                for rec in qs.recommendations:
                    print(f"  💡 {rec}")
            
            # Show educational feedback
            if hasattr(result, 'educational_feedback') and result.educational_feedback:
                ef = result.educational_feedback
                print(f"\n📚 Educational Feedback:")
                print(f"  📖 Summary: {ef.overall_summary}")
                print(f"  🎓 Learning Path: {ef.learning_path.value}")
                print(f"  🌟 Motivational: {ef.motivational_message}")
                
                print(f"\n📝 Feedback Items:")
                for item in ef.feedback_items:
                    print(f"  🔍 {item.type.value.upper()}: {item.title}")
                    print(f"     💬 {item.message}")
                    print(f"     ⏱️  Effort: {item.estimated_effort}")
                    print(f"     📚 Resources: {len(item.learning_resources)}")
                
                print(f"\n🎯 Learning Recommendations:")
                for rec in ef.recommendations:
                    print(f"  📚 {rec.skill_area}: {rec.current_level} → {rec.target_level}")
                    print(f"     ⏱️  Time: {rec.estimated_time}")
                    print(f"     📖 Resources: {len(rec.resources)}")
                
                print(f"\n📊 Progress Indicators:")
                indicators = ef.progress_indicators
                print(f"  📈 Total Issues: {indicators.get('total_issues', 0)}")
                print(f"  🎯 Next Milestone: {indicators.get('next_milestone', 'N/A')}")
                print(f"  📊 Improvement Potential: {indicators.get('improvement_potential', 0)}")
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n🎉 Scoring and feedback test completed!")
        print(f"📁 Test directory cleaned up: {temp_path}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_scoring_feedback())
