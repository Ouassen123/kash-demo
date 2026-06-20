"""Tests for the Skills code analysis pipeline."""

import json
import pytest
import tempfile
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.modules.skills.code_analysis import (
    AnalysisResult,
    AnalyzerReport,
    AnalyzerFinding,
    SeverityLevel,
    CodeAnalysisEngine,
    CodeAnalysisStore,
    RepositoryInput,
)
from src.modules.skills.code_analysis.context import AnalysisContext
from src.modules.skills.skills_service import SkillsService
from src.modules.skills.github.models import RepositorySnapshot, ReliabilitySignals


class TestCodeAnalysisEngine:
    """Test cases for CodeAnalysisEngine."""

    @pytest.fixture
    def engine(self):
        """Create a CodeAnalysisEngine instance for testing."""
        return CodeAnalysisEngine()

    @pytest.fixture
    def sample_repo_input(self):
        """Create a sample RepositoryInput for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create sample files
            (temp_path / "test.py").write_text("""
def hello_world():
    print("Hello, World!")
    return 42

class TestClass:
    def method(self):
        pass
""")
            
            (temp_path / "README.md").write_text("# Test Repository")
            
            return RepositoryInput(
                submission_id="test-submission",
                learner_id="test-learner",
                template_id="test-template",
                root_path=temp_path,
                files=list(temp_path.glob("**/*")),
                analysis_profile="standard",
            )

    @pytest.mark.asyncio
    async def test_analyze_repository(self, engine, sample_repo_input):
        """Test analyzing a repository."""
        result = await engine.analyze(sample_repo_input)
        
        assert isinstance(result, AnalysisResult)
        assert result.submission_id == "test-submission"
        assert result.learner_id == "test-learner"
        assert result.template_id == "test-template"
        assert result.analysis_profile == "standard"
        assert isinstance(result.overall_score, (int, float))
        assert 0 <= result.overall_score <= 100
        assert isinstance(result.confidence, (int, float))
        assert 0 <= result.confidence <= 1
        assert len(result.analyzer_reports) > 0
        assert isinstance(result.summary, str)

    @pytest.mark.asyncio
    async def test_analyze_with_inline_files(self, engine):
        """Test analyzing inline files without a repository."""
        inline_files = [
            {
                "path": "test.js",
                "content": """
function hello() {
    console.log("Hello");
    return null;
}
"""
            }
        ]
        
        repo_input = RepositoryInput(
            submission_id="test-submission",
            learner_id="test-learner",
            template_id="test-template",
            root_path=Path("."),
            files=[],
            inline_files=inline_files,
            analysis_profile="standard",
        )
        
        result = await engine.analyze(repo_input)
        
        assert isinstance(result, AnalysisResult)
        assert result.submission_id == "test-submission"
        assert len(result.analyzer_reports) > 0

    @pytest.mark.asyncio
    async def test_analyze_with_different_profiles(self, engine, sample_repo_input):
        """Test analyzing with different analysis profiles."""
        profiles = ["standard", "strict", "quick"]
        
        for profile in profiles:
            sample_repo_input.analysis_profile = profile
            result = await engine.analyze(sample_repo_input)
            
            assert result.analysis_profile == profile
            assert isinstance(result, AnalysisResult)


class TestCodeAnalysisStore:
    """Test cases for CodeAnalysisStore."""

    @pytest.fixture
    def store(self):
        """Create a CodeAnalysisStore instance for testing."""
        return CodeAnalysisStore()

    @pytest.fixture
    def sample_result(self):
        """Create a sample AnalysisResult for testing."""
        return AnalysisResult(
            submission_id="test-submission",
            learner_id="test-learner",
            template_id="test-template",
            analysis_profile="standard",
            analyzed_at=datetime.utcnow(),
            overall_score=85.5,
            confidence=0.9,
            analyzer_reports=[
                AnalyzerReport(
                    analyzer_name="test_analyzer",
                    analyzer_version="1.0.0",
                    execution_time_ms=100,
                    findings=[
                        AnalyzerFinding(
                            rule_id="TEST001",
                            message="Test finding",
                            file_path=Path("test.py"),
                            line_number=10,
                            severity=SeverityLevel.MEDIUM,
                            category="test",
                            score_impact=-5.0,
                            metadata={},
                        )
                    ],
                )
            ],
            summary="Test analysis completed",
        )

    def test_save_and_get_analysis(self, store, sample_result):
        """Test saving and retrieving analysis results."""
        from src.modules.skills.code_analysis.store import StoredAnalysis
        
        stored = StoredAnalysis(
            submission_id=sample_result.submission_id,
            learner_id=sample_result.learner_id,
            template_id=sample_result.template_id,
            result=sample_result,
        )
        
        # Save the analysis
        store.save(stored)
        
        # Retrieve the analysis
        retrieved = store.get(sample_result.submission_id)
        
        assert retrieved is not None
        assert retrieved.submission_id == sample_result.submission_id
        assert retrieved.learner_id == sample_result.learner_id
        assert retrieved.template_id == sample_result.template_id
        assert retrieved.result.overall_score == sample_result.overall_score

    def test_list_by_learner(self, store, sample_result):
        """Test listing analyses by learner."""
        from src.modules.skills.code_analysis.store import StoredAnalysis
        
        # Save multiple analyses for the same learner
        for i in range(3):
            stored = StoredAnalysis(
                submission_id=f"submission-{i}",
                learner_id=sample_result.learner_id,
                template_id=sample_result.template_id,
                result=sample_result,
            )
            store.save(stored)
        
        # List analyses by learner
        learner_analyses = store.list_by_learner(sample_result.learner_id)
        
        assert len(learner_analyses) == 3
        for analysis in learner_analyses:
            assert analysis.learner_id == sample_result.learner_id

    def test_get_nonexistent_analysis(self, store):
        """Test retrieving a non-existent analysis."""
        result = store.get("nonexistent-submission")
        assert result is None


class TestSkillsServiceIntegration:
    """Test cases for SkillsService integration with code analysis."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def skills_service(self, mock_db):
        """Create a SkillsService instance for testing."""
        with patch('src.modules.skills.skills_service.GitHubSyncManager'), \
             patch('src.modules.skills.skills_service.CodeAnalysisEngine'), \
             patch('src.modules.skills.skills_service.CodeAnalysisStore'):
            return SkillsService(mock_db)

    @pytest.fixture
    def sample_repo_snapshot(self):
        """Create a sample RepositorySnapshot for testing."""
        return RepositorySnapshot(
            owner="testowner",
            name="testrepo",
            default_branch="main",
            languages={"Python": 1000},
            language_summary={"Python": 1000, "total": 1000},
            stars=10,
            forks=5,
            open_issues=2,
            topics=["test"],
            size_kb=100,
            last_pushed_at=datetime.utcnow(),
            reliability=ReliabilitySignals(
                attribution_confidence=0.9,
                last_synced_at=datetime.utcnow(),
                warnings=[],
            ),
            commit_sha="abc123def456",
        )

    @pytest.mark.asyncio
    async def test_run_code_analysis_from_repository(self, skills_service, sample_repo_snapshot):
        """Test running code analysis from a repository snapshot."""
        submission_id = str(uuid.uuid4())
        learner_id = str(uuid.uuid4())
        template_id = "test-template"
        
        # Mock the GitHubSyncManager to return a temp path
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "test.py").write_text("print('test')")
            
            skills_service.github_sync_manager.get_local_repo_path.return_value = temp_path
            
            # Mock the code analysis engine
            mock_result = MagicMock()
            mock_result.overall_score = 85.0
            mock_result.analyzer_reports = []
            mock_result.analyzed_at = datetime.utcnow()
            skills_service.code_analysis_engine.analyze.return_value = mock_result
            
            # Mock the persist method to avoid file I/O
            skills_service._persist_analysis_artifacts = AsyncMock()
            skills_service._emit_analysis_telemetry = AsyncMock()
            
            # Run the analysis
            await skills_service._run_code_analysis_from_repository(
                submission_id, learner_id, template_id, sample_repo_snapshot
            )
            
            # Verify the analysis was run
            skills_service.code_analysis_engine.analyze.assert_called_once()
            skills_service._persist_analysis_artifacts.assert_called_once()
            skills_service._emit_analysis_telemetry.assert_called_once()
            skills_service.code_analysis_store.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_reviewer_override(self, skills_service):
        """Test applying reviewer overrides to analysis results."""
        submission_id = str(uuid.uuid4())
        reviewer_id = str(uuid.uuid4())
        score_delta = 10.0
        justification = "Good extra work"
        
        # Mock existing analysis data
        mock_analysis_data = {
            "submission_id": submission_id,
            "automated_score": 80.0,
            "adjusted_score": 80.0,
            "grade": "B",
            "overrides": [],
        }
        
        skills_service.get_analysis_artifacts = AsyncMock(return_value=mock_analysis_data)
        skills_service._persist_analysis_artifacts_update = AsyncMock()
        
        # Apply the override
        result = await skills_service.apply_reviewer_override(
            submission_id, reviewer_id, score_delta, justification
        )
        
        # Verify the override was applied
        assert result["submission_id"] == submission_id
        assert result["updated_scores"]["automated_score"] == 80.0
        assert result["updated_scores"]["adjusted_score"] == 90.0  # 80 + 10
        assert result["updated_scores"]["grade"] == "A"  # 90+ maps to A
        assert result["override"]["score_delta"] == score_delta
        assert result["override"]["justification"] == justification
        assert result["override"]["reviewer_id"] == reviewer_id

    @pytest.mark.asyncio
    async def test_get_analysis_artifacts(self, skills_service):
        """Test retrieving analysis artifacts."""
        submission_id = str(uuid.uuid4())
        
        # Mock analysis data
        mock_analysis_data = {
            "submission_id": submission_id,
            "overall_score": 85.0,
            "grade": "B",
        }
        
        with patch('src.modules.skills.skills_service.DATA_DIR') as mock_data_dir, \
             patch('pathlib.Path.glob') as mock_glob, \
             patch('builtins.open', mock_open_read(json.dumps(mock_analysis_data))):
            
            # Setup mocks
            mock_file = MagicMock()
            mock_file.stat.return_value.st_mtime = 1234567890
            mock_glob.return_value = [mock_file]
            
            # Get artifacts
            result = await skills_service.get_analysis_artifacts(submission_id)
            
            assert result is not None
            assert result["submission_id"] == submission_id
            assert result["overall_score"] == 85.0

    @pytest.mark.asyncio
    async def test_emit_analysis_telemetry(self, skills_service, sample_repo_snapshot):
        """Test telemetry emission for analysis completion."""
        submission_id = str(uuid.uuid4())
        learner_id = str(uuid.uuid4())
        template_id = "test-template"
        
        # Mock analysis result
        mock_result = MagicMock()
        mock_result.overall_score = 85.0
        mock_result.confidence = 0.9
        mock_result.analysis_profile = "standard"
        mock_result.analyzer_reports = []
        
        # Emit telemetry
        with patch('src.modules.skills.skills_service.logger') as mock_logger:
            await skills_service._emit_analysis_telemetry(
                submission_id, learner_id, template_id, mock_result, sample_repo_snapshot
            )
            
            # Verify telemetry was logged
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "TELEMETRY:" in call_args
            assert "skills.code_analysis.completed" in call_args


def mock_open_read(content):
    """Mock open() for reading files."""
    from unittest.mock import mock_open
    return mock_open(read_data=content)


class TestRepositoryHydration:
    """Test cases for repository hydration functionality."""

    @pytest.mark.asyncio
    async def test_get_local_repo_path_integration(self):
        """Test GitHubSyncManager.get_local_repo_path integration."""
        from src.modules.skills.github.sync_manager import GitHubSyncManager
        from src.modules.skills.github.integration_service import GitHubIntegrationService
        
        # Mock the integration service
        mock_integration_service = MagicMock()
        test_path = Path("/test/path")
        mock_integration_service.get_local_repo_path.return_value = test_path
        
        # Create sync manager with mocked integration service
        sync_manager = GitHubSyncManager(mock_integration_service)
        
        # Test getting local repo path
        result = sync_manager.get_local_repo_path("test-submission")
        
        assert result == test_path
        mock_integration_service.get_local_repo_path.assert_called_once_with("test-submission")

    def test_integration_service_local_repo_path(self):
        """Test GitHubIntegrationService.get_local_repo_path."""
        from src.modules.skills.github.integration_service import GitHubIntegrationService
        
        with patch('src.modules.skills.github.integration_service.DATA_DIR') as mock_data_dir:
            mock_data_dir.mkdir.return_value = None
            
            # Create a mock path that exists
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.is_dir.return_value = True
            mock_data_dir.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_path
            
            service = GitHubIntegrationService()
            result = service.get_local_repo_path("test-submission")
            
            assert result == mock_path


if __name__ == "__main__":
    pytest.main([__file__])
