#!/usr/bin/env python
"""Test script for educational rules integration."""

import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

async def test_educational_rules():
    """Test the educational rules integration."""
    print("🧪 Testing Educational Rules Integration")
    print("=" * 50)
    
    from src.modules.skills.code_analysis import CodeAnalysisEngine
    from src.modules.skills.code_analysis.context import RepositoryInput
    
    # Create temporary directory with problematic code
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create Java file with educational rule violations
        java_file = temp_path / "BadClass.java"
        java_file.write_text("""
import java.util.*;
import java.io.*;

class badClass {
    public String name;
    public int age;
    
    public int calculate_Total(int a, int b, int c, int d, int e, int f, int g) {
        return a + b + c + d + e + f + g;
    }
}""")
        
        print(f"📁 Created test files in: {temp_path}")
        print(f"  ☕ Java: {java_file.name} (with educational violations)")
        
        # Test with educational profile
        engine = CodeAnalysisEngine()
        
        try:
            repo_input = RepositoryInput(
                submission_id="test-educational",
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
            
            # Show educational findings
            for report in result.analyzer_reports:
                print(f"\n  🔍 {report.analyzer_name}:")
                print(f"    ⏱️  Execution time: {report.execution_time_ms}ms")
                print(f"    📊 Findings: {len(report.findings)}")
                
                for i, finding in enumerate(report.findings):
                    print(f"      {i+1}. [{finding.severity.value.upper()}] {finding.message}")
                    print(f"         Rule ID: {finding.rule_id}")
                    
                    # Show educational metadata if available
                    if finding.metadata:
                        print(f"         Educational Level: {finding.metadata.get('educational_level', 'N/A')}")
                        print(f"         Learning Objective: {finding.metadata.get('learning_objective', 'N/A')}")
                        print(f"         Improvement: {finding.metadata.get('improvement_suggestion', 'N/A')}")
                        print(f"         Resources: {finding.metadata.get('resources', [])}")
                        print()
            
            # Test educational feedback generation
            print(f"\n📚 Testing Educational Feedback Generation:")
            print("-" * 50)
            
            from src.modules.skills.code_analysis.rules import JavaEducationalRules
            java_rules = JavaEducationalRules()
            
            if result.analyzer_reports and result.analyzer_reports[0].findings:
                first_finding = result.analyzer_reports[0].findings[0]
                rule_id = first_finding.rule_id
                
                try:
                    feedback = java_rules.generate_feedback(rule_id, {"file": str(java_file)})
                    print(f"  📖 Feedback for {rule_id}:")
                    print(f"    Title: {feedback.title}")
                    print(f"    What's wrong: {feedback.what_is_wrong}")
                    print(f"    Why it matters: {feedback.why_it_matters}")
                    print(f"    How to fix: {feedback.how_to_fix}")
                    print(f"    Example before: {feedback.example_before}")
                    print(f"    Example after: {feedback.example_after}")
                    print(f"    Next steps: {feedback.next_steps}")
                except Exception as e:
                    print(f"  ❌ Feedback generation failed: {e}")
            
            # Test educational summary
            print(f"\n📊 Educational Summary:")
            print("-" * 30)
            
            all_findings = []
            for report in result.analyzer_reports:
                all_findings.extend([
                    {"rule_id": finding.rule_id, "severity": finding.severity.value}
                    for finding in report.findings
                ])
            
            summary = java_rules.get_educational_summary(all_findings)
            print(f"  Language: {summary['language']}")
            print(f"  Rules violated: {summary['total_rules_violated']}")
            print(f"  Focus areas: {summary['focus_areas']}")
            print(f"  Learning path: {summary['recommended_learning_path']}")
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n🎉 Educational rules test completed!")
        print(f"📁 Test directory cleaned up: {temp_path}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_educational_rules())
