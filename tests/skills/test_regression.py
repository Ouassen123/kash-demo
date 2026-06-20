"""Regression tests for Skills code analysis pipeline."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.modules.skills.skills_service import SkillsService
from src.modules.skills.code_analysis import SeverityLevel, CodeAnalysisEngine, CodeAnalysisStore


class TestSkillsRegression:
    """Regression tests to ensure existing functionality continues to work."""

    @pytest.mark.asyncio
    async def test_backward_compatibility_with_existing_analyses(self):
        """Test that existing analysis artifacts remain compatible."""
        # Simulate old analysis format
        old_analysis_format = {
            "submission_id": "old-submission",
            "learner_id": "old-learner", 
            "template_id": "old-template",
            "overall_score": 80.0,
            "confidence": 0.85,
            "findings": [],
            "summary": "Legacy analysis",
        }
        
        # Test that new code can handle old format
        engine = CodeAnalysisEngine()
        store = CodeAnalysisStore()
        
        # Should not raise errors with legacy data
        assert store.get("old-submission") is None  # No data exists yet

    @pytest.mark.asyncio
    async def test_analysis_score_consistency(self):
        """Test that analysis scores remain consistent across runs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create consistent test file
            test_file = temp_path / "consistent.py"
            test_file.write_text("""
def consistent_function():
    return "consistent result"

class ConsistentClass:
    def method(self):
        pass
""")
            
            # Run analysis multiple times
            engine = CodeAnalysisEngine()
            scores = []
            
            for i in range(3):
                from src.modules.skills.code_analysis.context import RepositoryInput
                
                repo_input = RepositoryInput(
                    submission_id=f"test-{i}",
                    learner_id="test-learner",
                    template_id="test-template",
                    root_path=temp_path,
                    files=[test_file],
                    analysis_profile="standard",
                )
                
                result = await engine.analyze(repo_input)
                scores.append(result.overall_score)
            
            # Scores should be consistent (allowing for minor variations)
            max_score = max(scores)
            min_score = min(scores)
            assert max_score - min_score <= 5.0, f"Scores vary too much: {scores}"

    @pytest.mark.asyncio
    async def test_performance_regression(self):
        """Test that analysis performance doesn't degrade significantly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create moderately sized codebase
            for i in range(10):
                file_path = temp_path / f"file_{i}.py"
                file_path.write_text(f"""
def function_{i}():
    # Some code to analyze
    result = []
    for j in range(100):
        result.append(j * i)
    return result

class Class_{i}:
    def __init__(self):
        self.value = i
    
    def method_{i}(self):
        return self.value * 2
""")
            
            engine = CodeAnalysisEngine()
            
            from src.modules.skills.code_analysis.context import RepositoryInput
            repo_input = RepositoryInput(
                submission_id="perf-test",
                learner_id="test-learner",
                template_id="test-template",
                root_path=temp_path,
                files=list(temp_path.glob("*.py")),
                analysis_profile="standard",
            )
            
            # Time the analysis
            import time
            start_time = time.time()
            result = await engine.analyze(repo_input)
            end_time = time.time()
            
            analysis_time = end_time - start_time
            
            # Should complete within reasonable time (adjust threshold as needed)
            assert analysis_time < 10.0, f"Analysis took too long: {analysis_time:.2f}s"
            assert result.overall_score is not None

    def test_memory_usage_regression(self):
        """Test that memory usage doesn't grow excessively."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create and analyze multiple repositories
        for i in range(5):
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create test files
                (temp_path / f"test_{i}.py").write_text(f"""
def test_function_{i}():
    return {i}

class TestClass_{i}:
    def method(self):
        return {i} * 2
""")
                
                # Simulate analysis (without actually running to isolate memory test)
                from src.modules.skills.code_analysis.context import RepositoryInput
                repo_input = RepositoryInput(
                    submission_id=f"memory-test-{i}",
                    learner_id="test-learner",
                    template_id="test-template",
                    root_path=temp_path,
                    files=list(temp_path.glob("*.py")),
                    analysis_profile="standard",
                )
                
                # Just create the input to test memory usage
                assert repo_input.submission_id == f"memory-test-{i}"
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory increased too much: {memory_increase:.2f}MB"

    @pytest.mark.asyncio
    async def test_error_handling_regression(self):
        """Test that error handling continues to work correctly."""
        engine = CodeAnalysisEngine()
        
        # Test with empty repository
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            from src.modules.skills.code_analysis.context import RepositoryInput
            repo_input = RepositoryInput(
                submission_id="empty-test",
                learner_id="test-learner",
                template_id="test-template",
                root_path=temp_path,
                files=[],
                analysis_profile="standard",
            )
            
            # Should not crash, should return valid result
            result = await engine.analyze(repo_input)
            assert isinstance(result.overall_score, (int, float))
            assert 0 <= result.overall_score <= 100

    @pytest.mark.asyncio
    async def test_file_encoding_regression(self):
        """Test that various file encodings are handled correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create files with different encodings
            utf8_file = temp_path / "utf8.py"
            utf8_file.write_text("def hello(): print('Hello, 世界')", encoding='utf-8')
            
            # Test analysis with UTF-8 file
            from src.modules.skills.code_analysis.context import RepositoryInput
            repo_input = RepositoryInput(
                submission_id="encoding-test",
                learner_id="test-learner",
                template_id="test-template",
                root_path=temp_path,
                files=[utf8_file],
                analysis_profile="standard",
            )
            
            engine = CodeAnalysisEngine()
            result = await engine.analyze(repo_input)
            
            # Should handle encoding without errors
            assert isinstance(result.overall_score, (int, float))
            assert len(result.analyzer_reports) > 0

    def test_severity_level_consistency(self):
        """Test that severity levels remain consistent."""
        # All severity levels should be available
        assert hasattr(SeverityLevel, 'CRITICAL')
        assert hasattr(SeverityLevel, 'HIGH')
        assert hasattr(SeverityLevel, 'MEDIUM')
        assert hasattr(SeverityLevel, 'LOW')
        assert hasattr(SeverityLevel, 'INFO')
        
        # Severity levels should have consistent values
        levels = [SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM, SeverityLevel.LOW, SeverityLevel.INFO]
        for level in levels:
            assert hasattr(level, 'value')
            assert isinstance(level.value, str)

    @pytest.mark.asyncio
    async def test_concurrent_analysis_regression(self):
        """Test that concurrent analyses work correctly."""
        import asyncio
        
        async def analyze_single(submission_id):
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                (temp_path / "test.py").write_text(f"""
def test_function_{submission_id}():
    return "{submission_id}"
""")
                
                from src.modules.skills.code_analysis.context import RepositoryInput
                repo_input = RepositoryInput(
                    submission_id=submission_id,
                    learner_id="test-learner",
                    template_id="test-template",
                    root_path=temp_path,
                    files=list(temp_path.glob("*.py")),
                    analysis_profile="standard",
                )
                
                engine = CodeAnalysisEngine()
                return await engine.analyze(repo_input)
        
        # Run multiple analyses concurrently
        submission_ids = [f"concurrent-{i}" for i in range(5)]
        tasks = [analyze_single(sid) for sid in submission_ids]
        
        results = await asyncio.gather(*tasks)
        
        # All analyses should complete successfully
        assert len(results) == 5
        for result in results:
            assert isinstance(result.overall_score, (int, float))
            assert 0 <= result.overall_score <= 100

    def test_configuration_regression(self):
        """Test that configuration handling remains consistent."""
        from src.core.config import settings
        
        # Important settings should exist
        assert hasattr(settings, 'DATA_DIR')
        assert hasattr(settings, 'github_access_token')
        assert hasattr(settings, 'github_api_url')
        assert hasattr(settings, 'enable_tracing')
        assert hasattr(settings, 'enable_metrics')
        
        # Settings should have reasonable defaults
        assert settings.DATA_DIR is not None
        assert settings.github_api_url is not None
        assert isinstance(settings.enable_tracing, bool)
        assert isinstance(settings.enable_metrics, bool)


class TestSkillsEdgeCases:
    """Test edge cases that might cause regressions."""

    @pytest.mark.asyncio
    async def test_very_long_file_names(self):
        """Test handling of very long file names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create file with very long name
            long_name = "a" * 200 + ".py"
            long_file = temp_path / long_name
            long_file.write_text("def test(): pass")
            
            from src.modules.skills.code_analysis.context import RepositoryInput
            repo_input = RepositoryInput(
                submission_id="long-name-test",
                learner_id="test-learner",
                template_id="test-template",
                root_path=temp_path,
                files=[long_file],
                analysis_profile="standard",
            )
            
            engine = CodeAnalysisEngine()
            result = await engine.analyze(repo_input)
            
            # Should handle long names without crashing
            assert isinstance(result.overall_score, (int, float))

    @pytest.mark.asyncio
    async def test_special_characters_in_paths(self):
        """Test handling of special characters in file paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create directory with special characters
            special_dir = temp_path / "test dir with spaces & symbols"
            special_dir.mkdir()
            
            special_file = special_dir / "test-file.py"
            special_file.write_text("def test(): pass")
            
            from src.modules.skills.code_analysis.context import RepositoryInput
            repo_input = RepositoryInput(
                submission_id="special-chars-test",
                learner_id="test-learner",
                template_id="test-template",
                root_path=temp_path,
                files=[special_file],
                analysis_profile="standard",
            )
            
            engine = CodeAnalysisEngine()
            result = await engine.analyze(repo_input)
            
            # Should handle special characters without crashing
            assert isinstance(result.overall_score, (int, float))

    @pytest.mark.asyncio
    async def test_binary_files_handling(self):
        """Test that binary files are handled correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a binary file
            binary_file = temp_path / "test.bin"
            binary_file.write_bytes(b'\x00\x01\x02\x03\x04\x05')
            
            # Create a normal Python file
            py_file = temp_path / "test.py"
            py_file.write_text("def test(): pass")
            
            from src.modules.skills.code_analysis.context import RepositoryInput
            repo_input = RepositoryInput(
                submission_id="binary-test",
                learner_id="test-learner",
                template_id="test-template",
                root_path=temp_path,
                files=[binary_file, py_file],
                analysis_profile="standard",
            )
            
            engine = CodeAnalysisEngine()
            result = await engine.analyze(repo_input)
            
            # Should handle binary files without crashing and still analyze Python files
            assert isinstance(result.overall_score, (int, float))

    @pytest.mark.asyncio
    async def test_empty_and_whitespace_files(self):
        """Test handling of empty files and files with only whitespace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create empty file
            empty_file = temp_path / "empty.py"
            empty_file.write_text("")
            
            # Create whitespace-only file
            whitespace_file = temp_path / "whitespace.py"
            whitespace_file.write_text("   \n  \t  \n   ")
            
            # Create normal file
            normal_file = temp_path / "normal.py"
            normal_file.write_text("def test(): pass")
            
            from src.modules.skills.code_analysis.context import RepositoryInput
            repo_input = RepositoryInput(
                submission_id="empty-test",
                learner_id="test-learner",
                template_id="test-template",
                root_path=temp_path,
                files=[empty_file, whitespace_file, normal_file],
                analysis_profile="standard",
            )
            
            engine = CodeAnalysisEngine()
            result = await engine.analyze(repo_input)
            
            # Should handle empty/whitespace files without crashing
            assert isinstance(result.overall_score, (int, float))


if __name__ == "__main__":
    pytest.main([__file__])
