"""Integration tests for the complete Skills pipeline."""

import json
import pytest
import tempfile
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.modules.skills.skills_service import SkillsService
from src.modules.skills.github.models import RepositorySnapshot, ReliabilitySignals
from src.modules.skills.code_analysis import SeverityLevel


class TestSkillsPipelineIntegration:
    """Integration tests for the complete Skills analysis pipeline."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def temp_repo_dir(self):
        """Create a temporary repository with test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create Python files with various code quality issues
            (temp_path / "main.py").write_text("""
import os
import sys

def calculate_sum(a, b):
    x = a + b
    return x

class TestClass:
    def __init__(self):
        self.value = 42
    
    def method_with_long_name_that_exceeds_pep8_recommended_length(self):
        print("This method name is too long")
        return self.value

if __name__ == "__main__":
    result = calculate_sum(10, 20)
    print(f"Result: {result}")
""")
            
            (temp_path / "utils.py").write_text("""
def helper_function():
    pass

# Unused variable
unused_var = "This is not used"

def another_function():
    # TODO: Implement this function
    pass
""")
            
            (temp_path / "README.md").write_text("""
# Test Repository

This is a test repository for code analysis.

## Features
- Feature 1
- Feature 2
""")
            
            yield temp_path

    @pytest.fixture
    def skills_service(self, mock_db):
        """Create a SkillsService instance with mocked dependencies."""
        with patch('src.modules.skills.skills_service.GitHubSyncManager') as mock_sync_manager, \
             patch('src.modules.skills.skills_service.MiniProjectEvaluationManager') as mock_eval_manager, \
             patch('src.modules.skills.skills_service.MiniProjectDashboard') as mock_dashboard:
            
            service = SkillsService(mock_db)
            service.github_sync_manager = mock_sync_manager.return_value
            service.evaluation_manager = mock_eval_manager.return_value
            service.dashboard = mock_dashboard.return_value
            
            # Initialize code analysis components
            from src.modules.skills.code_analysis import CodeAnalysisEngine, CodeAnalysisStore
            service.code_analysis_engine = CodeAnalysisEngine()
            service.code_analysis_store = CodeAnalysisStore()
            
            return service

    @pytest.fixture
    def sample_repo_snapshot(self):
        """Create a sample repository snapshot."""
        return RepositorySnapshot(
            owner="testowner",
            name="testrepo",
            default_branch="main",
            languages={"Python": 2000},
            language_summary={"Python": 2000, "total": 2000},
            stars=15,
            forks=8,
            open_issues=3,
            topics=["python", "test"],
            size_kb=150,
            last_pushed_at=datetime.utcnow(),
            reliability=ReliabilitySignals(
                attribution_confidence=0.95,
                last_synced_at=datetime.utcnow(),
                warnings=[],
            ),
            commit_sha="abc123def456789",
        )

    @pytest.mark.asyncio
    async def test_full_repository_analysis_pipeline(
        self, skills_service, temp_repo_dir, sample_repo_snapshot
    ):
        """Test the complete repository analysis pipeline."""
        submission_id = str(uuid.uuid4())
        learner_id = str(uuid.uuid4())
        template_id = "test-template"
        
        # Mock GitHubSyncManager to return our temp repository
        skills_service.github_sync_manager.get_local_repo_path.return_value = temp_repo_dir
        
        # Mock persistence methods to capture calls
        skills_service._persist_analysis_artifacts = AsyncMock()
        skills_service._emit_analysis_telemetry = AsyncMock()
        
        # Run the complete pipeline
        await skills_service._run_code_analysis_from_repository(
            submission_id, learner_id, template_id, sample_repo_snapshot
        )
        
        # Verify the analysis was executed
        skills_service.code_analysis_engine.analyze.assert_called_once()
        
        # Get the call arguments for verification
        call_args = skills_service.code_analysis_engine.analyze.call_args[0][0]
        assert call_args.submission_id == submission_id
        assert call_args.learner_id == learner_id
        assert call_args.template_id == template_id
        assert call_args.root_path == temp_repo_dir
        assert call_args.commit_sha == sample_repo_snapshot.commit_sha
        assert call_args.analysis_profile == "standard"
        
        # Verify persistence was called
        skills_service._persist_analysis_artifacts.assert_called_once()
        skills_service._emit_analysis_telemetry.assert_called_once()
        skills_service.code_analysis_store.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_analysis_artifact_persistence_structure(
        self, skills_service, temp_repo_dir, sample_repo_snapshot
    ):
        """Test that analysis artifacts are persisted with correct structure."""
        submission_id = str(uuid.uuid4())
        learner_id = str(uuid.uuid4())
        template_id = "test-template"
        
        # Mock GitHubSyncManager
        skills_service.github_sync_manager.get_local_repo_path.return_value = temp_repo_dir
        
        # Mock the actual persistence to capture data
        persisted_data = {}
        
        async def capture_persist_data(submission_id, learner_id, template_id, result, repo_snapshot):
            persisted_data.update({
                "submission_id": submission_id,
                "learner_id": learner_id,
                "template_id": template_id,
                "overall_score": result.overall_score,
                "grade": skills_service._score_to_grade(result.overall_score),
                "confidence": result.confidence,
                "commit_sha": repo_snapshot.commit_sha,
                "repo_name": repo_snapshot.name,
                "repo_owner": repo_snapshot.owner,
            })
        
        skills_service._persist_analysis_artifacts = capture_persist_data
        skills_service._emit_analysis_telemetry = AsyncMock()
        
        # Run analysis
        await skills_service._run_code_analysis_from_repository(
            submission_id, learner_id, template_id, sample_repo_snapshot
        )
        
        # Verify persisted data structure
        assert persisted_data["submission_id"] == submission_id
        assert persisted_data["learner_id"] == learner_id
        assert persisted_data["template_id"] == template_id
        assert isinstance(persisted_data["overall_score"], (int, float))
        assert 0 <= persisted_data["overall_score"] <= 100
        assert persisted_data["grade"] in ["A", "B", "C", "D", "F"]
        assert 0 <= persisted_data["confidence"] <= 1
        assert persisted_data["commit_sha"] == sample_repo_snapshot.commit_sha
        assert persisted_data["repo_name"] == sample_repo_snapshot.name
        assert persisted_data["repo_owner"] == sample_repo_snapshot.owner

    @pytest.mark.asyncio
    async def test_reviewer_override_workflow(
        self, skills_service, temp_repo_dir, sample_repo_snapshot
    ):
        """Test the complete reviewer override workflow."""
        submission_id = str(uuid.uuid4())
        learner_id = str(uuid.uuid4())
        reviewer_id = str(uuid.uuid4())
        
        # First, run an analysis
        skills_service.github_sync_manager.get_local_repo_path.return_value = temp_repo_dir
        skills_service._persist_analysis_artifacts = AsyncMock()
        skills_service._emit_analysis_telemetry = AsyncMock()
        
        await skills_service._run_code_analysis_from_repository(
            submission_id, learner_id, "test-template", sample_repo_snapshot
        )
        
        # Mock the analysis artifacts for override testing
        mock_artifacts = {
            "submission_id": submission_id,
            "automated_score": 75.0,
            "adjusted_score": 75.0,
            "grade": "C",
            "overrides": [],
        }
        
        skills_service.get_analysis_artifacts = AsyncMock(return_value=mock_artifacts)
        skills_service._persist_analysis_artifacts_update = AsyncMock()
        
        # Apply reviewer override
        override_result = await skills_service.apply_reviewer_override(
            submission_id, reviewer_id, 10.0, "Good implementation, minor improvements needed"
        )
        
        # Verify override was applied correctly
        assert override_result["submission_id"] == submission_id
        assert override_result["updated_scores"]["automated_score"] == 75.0
        assert override_result["updated_scores"]["adjusted_score"] == 85.0
        assert override_result["updated_scores"]["grade"] == "B"
        assert override_result["override"]["score_delta"] == 10.0
        assert override_result["override"]["justification"] == "Good implementation, minor improvements needed"
        assert override_result["override"]["reviewer_id"] == reviewer_id

    @pytest.mark.asyncio
    async def test_telemetry_emission_structure(
        self, skills_service, temp_repo_dir, sample_repo_snapshot
    ):
        """Test that telemetry events are emitted with correct structure."""
        submission_id = str(uuid.uuid4())
        learner_id = str(uuid.uuid4())
        template_id = "test-template"
        
        # Mock GitHubSyncManager
        skills_service.github_sync_manager.get_local_repo_path.return_value = temp_repo_dir
        skills_service._persist_analysis_artifacts = AsyncMock()
        
        # Capture telemetry calls
        telemetry_calls = []
        
        def capture_telemetry(event_data):
            telemetry_calls.append(json.loads(event_data.split("TELEMETRY: ")[1]))
        
        with patch('src.modules.skills.skills_service.logger') as mock_logger:
            mock_logger.info.side_effect = capture_telemetry
            
            # Run analysis
            await skills_service._run_code_analysis_from_repository(
                submission_id, learner_id, template_id, sample_repo_snapshot
            )
            
            # Verify telemetry was emitted
            assert len(telemetry_calls) == 1
            telemetry = telemetry_calls[0]
            
            assert telemetry["event_type"] == "skills.code_analysis.completed"
            assert telemetry["submission_id"] == submission_id
            assert telemetry["learner_id"] == learner_id
            assert telemetry["template_id"] == template_id
            assert telemetry["analysis_profile"] == "standard"
            assert "repository" in telemetry
            assert "analysis_summary" in telemetry
            assert "findings_by_category" in telemetry
            
            # Verify repository data in telemetry
            repo_data = telemetry["repository"]
            assert repo_data["name"] == sample_repo_snapshot.name
            assert repo_data["owner"] == sample_repo_snapshot.owner
            assert repo_data["commit_sha"] == sample_repo_snapshot.commit_sha
            assert repo_data["reliability_score"] == sample_repo_snapshot.reliability.attribution_confidence
            
            # Verify analysis summary in telemetry
            summary = telemetry["analysis_summary"]
            assert isinstance(summary["overall_score"], (int, float))
            assert isinstance(summary["confidence"], (int, float))
            assert isinstance(summary["total_findings"], int)
            assert "severity_breakdown" in summary
            assert "analyzer_count" in summary
            assert "execution_time_ms" in summary

    @pytest.mark.asyncio
    async def test_api_endpoint_integration(self, skills_service, temp_repo_dir, sample_repo_snapshot):
        """Test API endpoint integration with the analysis pipeline."""
        from src.api.v1.skills import get_submission_analysis
        from fastapi import HTTPException
        
        submission_id = str(uuid.uuid4())
        learner_id = str(uuid.uuid4())
        
        # Run analysis first
        skills_service.github_sync_manager.get_local_repo_path.return_value = temp_repo_dir
        skills_service._persist_analysis_artifacts = AsyncMock()
        skills_service._emit_analysis_telemetry = AsyncMock()
        
        await skills_service._run_code_analysis_from_repository(
            submission_id, learner_id, "test-template", sample_repo_snapshot
        )
        
        # Mock analysis artifacts for API testing
        mock_artifacts = {
            "submission_id": submission_id,
            "learner_id": learner_id,
            "analysis_profile": "standard",
            "analyzed_at": datetime.utcnow().isoformat(),
            "commit_sha": sample_repo_snapshot.commit_sha,
            "repository": {
                "name": sample_repo_snapshot.name,
                "owner": sample_repo_snapshot.owner,
                "languages": sample_repo_snapshot.languages,
                "reliability": sample_repo_snapshot.reliability.attribution_confidence,
            },
            "overall_score": 85.0,
            "automated_score": 85.0,
            "adjusted_score": 85.0,
            "grade": "B",
            "confidence": 0.9,
            "severity_buckets": {
                "critical": 0,
                "high": 2,
                "medium": 5,
                "low": 3,
                "info": 1,
            },
            "findings": [
                {
                    "analyzer": "heuristics",
                    "analyzer_version": "1.0.0",
                    "execution_time_ms": 150,
                    "findings": [
                        {
                            "rule_id": "PEP8_LINE_LENGTH",
                            "message": "Line too long",
                            "file_path": "main.py",
                            "line_number": 10,
                            "severity": "medium",
                            "category": "style",
                            "score_impact": -2.0,
                            "metadata": {},
                        }
                    ],
                }
            ],
            "overrides": [],
            "summary": "Analysis completed successfully",
        }
        
        skills_service.get_analysis_artifacts = AsyncMock(return_value=mock_artifacts)
        
        # Mock user and database
        mock_user = MagicMock()
        mock_user.id = learner_id
        mock_db = MagicMock()
        
        # Test API endpoint
        result = await get_submission_analysis(submission_id, mock_user, mock_db)
        
        # Verify API response structure
        assert result["submission_id"] == submission_id
        assert result["analysis_profile"] == "standard"
        assert "scores" in result
        assert "severity_summary" in result
        assert "findings" in result
        assert "overrides" in result
        
        # Verify scores structure
        scores = result["scores"]
        assert scores["automated_score"] == 85.0
        assert scores["adjusted_score"] == 85.0
        assert scores["grade"] == "B"
        assert scores["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_error_handling_missing_repo_path(self, skills_service, sample_repo_snapshot):
        """Test error handling when local repository path is not found."""
        submission_id = str(uuid.uuid4())
        learner_id = str(uuid.uuid4())
        
        # Mock GitHubSyncManager to return None (no local path)
        skills_service.github_sync_manager.get_local_repo_path.return_value = None
        
        # Run analysis - should handle missing path gracefully
        await skills_service._run_code_analysis_from_repository(
            submission_id, learner_id, "test-template", sample_repo_snapshot
        )
        
        # Verify that analysis was not attempted
        skills_service.code_analysis_engine.analyze.assert_not_called()
        skills_service.code_analysis_store.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_multi_language_analysis(self, skills_service, temp_repo_dir, sample_repo_snapshot):
        """Test analysis of repositories with multiple programming languages."""
        # Add JavaScript file to test multi-language support
        (temp_repo_dir / "app.js").write_text("""
function calculateTotal(items) {
    let total = 0;
    for (let i = 0; i < items.length; i++) {
        total += items[i].price;
    }
    return total;
}

// Unused function
function unusedHelper() {
    console.log("This is not used");
}
""")
        
        submission_id = str(uuid.uuid4())
        learner_id = str(uuid.uuid4())
        
        # Update repo snapshot to include multiple languages
        sample_repo_snapshot.languages = {"Python": 1500, "JavaScript": 800}
        sample_repo_snapshot.language_summary = {"Python": 1500, "JavaScript": 800, "total": 2300}
        
        # Mock GitHubSyncManager
        skills_service.github_sync_manager.get_local_repo_path.return_value = temp_repo_dir
        skills_service._persist_analysis_artifacts = AsyncMock()
        skills_service._emit_analysis_telemetry = AsyncMock()
        
        # Run analysis
        await skills_service._run_code_analysis_from_repository(
            submission_id, learner_id, "test-template", sample_repo_snapshot
        )
        
        # Verify analysis was executed
        skills_service.code_analysis_engine.analyze.assert_called_once()
        
        # Get the repository input from the call
        call_args = skills_service.code_analysis_engine.analyze.call_args[0][0]
        
        # Verify files include both Python and JavaScript files
        file_paths = [f.name for f in call_args.files]
        assert "main.py" in file_paths
        assert "utils.py" in file_paths
        assert "app.js" in file_paths
        assert "README.md" in file_paths

    @pytest.mark.asyncio
    async def test_versioned_artifact_storage(self, skills_service, temp_repo_dir, sample_repo_snapshot):
        """Test that analysis artifacts are versioned by commit SHA."""
        submission_id = str(uuid.uuid4())
        learner_id = str(uuid.uuid4())
        
        # Mock GitHubSyncManager
        skills_service.github_sync_manager.get_local_repo_path.return_value = temp_repo_dir
        
        # Capture persistence calls to verify versioning
        persist_calls = []
        
        async def capture_persist_call(submission_id, learner_id, template_id, result, repo_snapshot):
            persist_calls.append({
                "submission_id": submission_id,
                "commit_sha": repo_snapshot.commit_sha,
                "overall_score": result.overall_score,
            })
        
        skills_service._persist_analysis_artifacts = capture_persist_call
        skills_service._emit_analysis_telemetry = AsyncMock()
        
        # Run analysis with first commit
        await skills_service._run_code_analysis_from_repository(
            submission_id, learner_id, "test-template", sample_repo_snapshot
        )
        
        # Update commit SHA and run again
        sample_repo_snapshot.commit_sha = "def456abc123789"
        await skills_service._run_code_analysis_from_repository(
            submission_id, learner_id, "test-template", sample_repo_snapshot
        )
        
        # Verify both analyses were persisted with different commit SHAs
        assert len(persist_calls) == 2
        assert persist_calls[0]["commit_sha"] == "abc123def456789"
        assert persist_calls[1]["commit_sha"] == "def456abc123789"
        assert persist_calls[0]["submission_id"] == submission_id
        assert persist_calls[1]["submission_id"] == submission_id


if __name__ == "__main__":
    pytest.main([__file__])
