#!/usr/bin/env python
"""Test script for multi-language analyzer support."""

import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

async def test_multi_language_analysis():
    """Test the multi-language analysis capabilities."""
    print("🧪 Testing Multi-Language Analysis Support")
    print("=" * 50)
    
    from src.modules.skills.code_analysis import CodeAnalysisEngine
    from src.modules.skills.code_analysis.context import RepositoryInput
    
    # Create temporary directory with multi-language files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create Python file
        py_file = temp_path / "test.py"
        py_file.write_text("""
def hello_world():
    print("Hello from Python!")
    return 42

class TestClass:
    def method(self):
        pass
""")
        
        # Create Java file
        java_file = temp_path / "Test.java"
        java_file.write_text("""
import java.util.List;

public class Test {
    private int value;
    
    public Test(int value) {
        this.value = value;
    }
    
    public void method() {
        System.out.println("Hello from Java!");
    }
}
""")
        
        # Create JavaScript file
        js_file = temp_path / "test.js"
        js_file.write_text("""
function helloWorld() {
    console.log("Hello from JavaScript!");
    return 42;
}

class TestClass {
    constructor() {
        this.value = 42;
    }
    
    method() {
        console.log("Method called");
    }
}

// Arrow function
const arrowFunction = () => {
    return "arrow";
};
""")
        
        # Create C++ file
        cpp_file = temp_path / "test.cpp"
        cpp_file.write_text("""
#include <iostream>
#include <vector>

class Test {
private:
    int value;
    
public:
    Test(int v) : value(v) {}
    
    void method() {
        std::cout << "Hello from C++!" << std::endl;
    }
};

int main() {
    Test test(42);
    test.method();
    return 0;
}
""")
        
        print(f"📁 Created test files in: {temp_path}")
        print(f"  📄 Python: {py_file.name}")
        print(f"  ☕ Java: {java_file.name}")
        print(f"  🟨 JavaScript: {js_file.name}")
        print(f"  ⚙️  C++: {cpp_file.name}")
        
        # Test with different analysis profiles
        engine = CodeAnalysisEngine()
        
        test_cases = [
            ("default", "Default profile (heuristics only)"),
            ("standard", "Standard profile (auto-detect languages)"),
            ("comprehensive", "Comprehensive profile (all analyzers)"),
        ]
        
        for profile, description in test_cases:
            print(f"\n🔍 Testing {description}")
            print("-" * 40)
            
            try:
                repo_input = RepositoryInput(
                    submission_id="test-multi-lang",
                    learner_id="test-learner",
                    template_id="test-template",
                    root_path=temp_path,
                    files=[py_file, java_file, js_file, cpp_file],
                    analysis_profile=profile,
                )
                
                result = await engine.analyze(repo_input)
                
                print(f"✅ Analysis completed successfully!")
                print(f"  📊 Overall Score: {result.overall_score:.1f}")
                print(f"  🎯 Confidence: {result.confidence:.2f}")
                print(f"  🔧 Analyzers used: {[report.analyzer_name for report in result.analyzer_reports]}")
                print(f"  📋 Total findings: {sum(len(report.findings) for report in result.analyzer_reports)}")
                
                # Show findings by analyzer
                for report in result.analyzer_reports:
                    print(f"\n  🔍 {report.analyzer_name}:")
                    print(f"    ⏱️  Execution time: {report.execution_time_ms}ms")
                    print(f"    📊 Findings: {len(report.findings)}")
                    
                    # Show a few sample findings
                    for i, finding in enumerate(report.findings[:3]):
                        print(f"      {i+1}. [{finding.severity.value.upper()}] {finding.message}")
                
            except Exception as e:
                print(f"❌ Analysis failed: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n🎉 Multi-language analysis test completed!")
        print(f"📁 Test directory cleaned up: {temp_path}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_multi_language_analysis())
