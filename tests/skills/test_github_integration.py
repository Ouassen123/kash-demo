"""Tests for GitHub integration in Skills module."""

import json
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from pathlib import Path

from src.modules.skills.github.models import (
    RepositorySnapshot,
    ReliabilitySignals,
    SubmissionSyncRequest,
    SubmissionSyncResult,
    ContributionSnapshot,
    PullRequestSnapshot,
    ContributionMetrics,
)
from src.modules.skills.github.integration_service import GitHubIntegrationService
from src.modules.skills.github.sync_manager import GitHubSyncManager
from src.modules.skills.github.link_registry import GitHubLinkRegistry, LearnerRepoLink
from src.modules.skills.github.token_manager import GitHubTokenManager
from src.modules.skills.github.token_store import EncryptedTokenStore


class TestGitHubIntegrationService:
    """Test cases for GitHubIntegrationService."""

    @pytest.fixture
    def integration_service(self):
        """Create a GitHubIntegrationService instance for testing."""
        with patch('src.modules.skills.github.integration_service.GitHubTokenManager'):
            return GitHubIntegrationService()

    @pytest.fixture
    def sample_sync_request(self):
        """Create a sample SubmissionSyncRequest for testing."""
        return SubmissionSyncRequest(
            submission_id="test-submission",
            learner_id="test-learner",
            template_id="test-template",
            repository_full_name="testowner/testrepo",
            expected_owner="testowner",
            github_token="test-token",
        )

    @pytest.mark.asyncio
    async def test_sync_submission_success(self, integration_service, sample_sync_request):
        """Test successful submission synchronization."""
        # Mock HTTP client responses
        mock_repo_data = {
            "name": "testrepo",
            "owner": {"login": "testowner"},
            "default_branch": "main",
            "stargazers_count": 10,
            "forks_count": 5,
            "open_issues_count": 2,
            "size": 100,
            "pushed_at": "2023-01-01T00:00:00Z",
            "topics": ["test"],
            "fork": False,
            "private": False,
            "language": "Python",
        }
        
        mock_languages = {"Python": 1000}
        mock_commits = [
            {
                "sha": "abc123",
                "commit": {
                    "author": {"date": "2023-01-01T00:00:00Z"},
                    "message": "Test commit"
                }
            }
        ]
        mock_prs = [
            {
                "number": 1,
                "title": "Test PR",
                "state": "closed",
                "created_at": "2023-01-01T00:00:00Z",
                "merged_at": "2023-01-01T00:00:00Z",
                "head": {"ref": "feature-branch"},
                "base": {"ref": "main"}
            }
        ]
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Setup mock responses
            mock_client.get.side_effect = [
                AsyncMock(status_code=200, json=AsyncMock(return_value=mock_repo_data)),
                AsyncMock(status_code=200, json=AsyncMock(return_value=mock_languages)),
                AsyncMock(status_code=200, json=AsyncMock(return_value=mock_commits)),
                AsyncMock(status_code=200, json=AsyncMock(return_value=mock_prs)),
            ]
            
            # Run sync
            result = await integration_service.sync_submission(sample_sync_request)
            
            # Verify result
            assert isinstance(result, SubmissionSyncResult)
            assert result.submission_id == "test-submission"
            assert result.repository is not None
            assert result.repository.name == "testrepo"
            assert result.repository.owner == "testowner"
            assert result.contributions_count == 1
            assert result.pull_requests_count == 1
            assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_sync_submission_repo_not_found(self, integration_service, sample_sync_request):
        """Test synchronization when repository is not found."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock 404 response
            mock_client.get.return_value = AsyncMock(status_code=404)
            
            # Run sync
            result = await integration_service.sync_submission(sample_sync_request)
            
            # Verify result
            assert isinstance(result, SubmissionSyncResult)
            assert result.submission_id == "test-submission"
            assert result.repository is None
            assert "repo_not_found" in result.errors

    @pytest.mark.asyncio
    async def test_sync_submission_missing_token(self, integration_service, sample_sync_request):
        """Test synchronization with missing token."""
        # Remove token from request
        sample_sync_request.github_token = None
        
        # Mock token manager returning no token
        integration_service.token_manager.get_token.return_value = None
        
        # Run sync
        result = await integration_service.sync_submission(sample_sync_request)
        
        # Verify result
        assert isinstance(result, SubmissionSyncResult)
        assert result.repository is None
        assert "missing_token" in result.errors

    def test_get_local_repo_path_exists(self, integration_service):
        """Test getting local repo path when it exists."""
        with patch('src.modules.skills.github.integration_service.DATA_DIR') as mock_data_dir:
            # Mock existing directory
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.is_dir.return_value = True
            mock_data_dir.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_path
            
            result = integration_service.get_local_repo_path("test-submission")
            
            assert result == mock_path

    def test_get_local_repo_path_not_exists(self, integration_service):
        """Test getting local repo path when it doesn't exist."""
        with patch('src.modules.skills.github.integration_service.DATA_DIR') as mock_data_dir:
            # Mock non-existing directory
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_data_dir.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_path
            
            result = integration_service.get_local_repo_path("test-submission")
            
            assert result is None


class TestGitHubSyncManager:
    """Test cases for GitHubSyncManager."""

    @pytest.fixture
    def sync_manager(self):
        """Create a GitHubSyncManager instance for testing."""
        mock_integration_service = MagicMock()
        mock_link_registry = MagicMock()
        return GitHubSyncManager(mock_integration_service, mock_link_registry)

    @pytest.fixture
    def sample_sync_request(self):
        """Create a sample sync request."""
        return SubmissionSyncRequest(
            submission_id="test-submission",
            learner_id="test-learner",
            template_id="test-template",
            repository_full_name="testowner/testrepo",
        )

    @pytest.mark.asyncio
    async def test_sync_submission_by_project(self, sync_manager, sample_sync_request):
        """Test syncing submission by project."""
        # Mock successful sync
        mock_result = MagicMock()
        mock_result.repository = MagicMock()
        sync_manager.integration_service.sync_submission.return_value = mock_result
        
        # Run sync
        result = await sync_manager.sync_submission_by_project(sample_sync_request)
        
        # Verify integration service was called
        sync_manager.integration_service.sync_submission.assert_called_once_with(sample_sync_request)
        assert result == mock_result

    def test_get_local_repo_path_delegation(self, sync_manager):
        """Test that get_local_repo_path delegates to integration service."""
        test_path = Path("/test/path")
        sync_manager.integration_service.get_local_repo_path.return_value = test_path
        
        result = sync_manager.get_local_repo_path("test-submission")
        
        assert result == test_path
        sync_manager.integration_service.get_local_repo_path.assert_called_once_with("test-submission")


class TestGitHubLinkRegistry:
    """Test cases for GitHubLinkRegistry."""

    @pytest.fixture
    def link_registry(self):
        """Create a GitHubLinkRegistry instance for testing."""
        return GitHubLinkRegistry()

    def test_register_link(self, link_registry):
        """Test registering a new GitHub link."""
        link = LearnerRepoLink(
            learner_id="test-learner",
            project_id="test-project",
            repository_full_name="testowner/testrepo",
            github_handle="testhandle",
            registered_at=datetime.utcnow(),
        )
        
        link_registry.register(link)
        
        retrieved = link_registry.get_by_learner_and_project("test-learner", "test-project")
        assert retrieved is not None
        assert retrieved.repository_full_name == "testowner/testrepo"

    def test_refresh_handle(self, link_registry):
        """Test refreshing GitHub handle for a learner."""
        # Register initial link
        link = LearnerRepoLink(
            learner_id="test-learner",
            project_id="test-project",
            repository_full_name="testowner/testrepo",
            github_handle="oldhandle",
            registered_at=datetime.utcnow(),
        )
        link_registry.register(link)
        
        # Refresh handle
        link_registry.refresh_handle("test-learner", "newhandle")
        
        # Verify update
        retrieved = link_registry.get_by_learner("test-learner")
        assert retrieved is not None
        assert retrieved.github_handle == "newhandle"

    def test_find_by_repository(self, link_registry):
        """Test finding links by repository name."""
        link1 = LearnerRepoLink(
            learner_id="learner1",
            project_id="project1",
            repository_full_name="testowner/testrepo",
            github_handle="handle1",
            registered_at=datetime.utcnow(),
        )
        link2 = LearnerRepoLink(
            learner_id="learner2",
            project_id="project2",
            repository_full_name="testowner/testrepo",
            github_handle="handle2",
            registered_at=datetime.utcnow(),
        )
        
        link_registry.register(link1)
        link_registry.register(link2)
        
        results = link_registry.find_by_repository("testowner/testrepo")
        assert len(results) == 2

    def test_to_dict(self, link_registry):
        """Test serializing registry to dictionary."""
        link = LearnerRepoLink(
            learner_id="test-learner",
            project_id="test-project",
            repository_full_name="testowner/testrepo",
            github_handle="testhandle",
            registered_at=datetime.utcnow(),
        )
        link_registry.register(link)
        
        data = link_registry.to_dict()
        assert "links" in data
        assert len(data["links"]) == 1
        assert data["links"][0]["learner_id"] == "test-learner"


class TestGitHubTokenManager:
    """Test cases for GitHubTokenManager."""

    @pytest.fixture
    def token_manager(self):
        """Create a GitHubTokenManager instance for testing."""
        with patch('src.modules.skills.github.token_manager.EncryptedTokenStore'):
            return GitHubTokenManager()

    @pytest.mark.asyncio
    async def test_get_token_for_learner(self, token_manager):
        """Test getting token for a specific learner."""
        # Mock stored token
        token_manager.store.get_token.return_value = "learner-token"
        
        token = await token_manager.get_token("test-learner")
        
        assert token == "learner-token"
        token_manager.store.get_token.assert_called_once_with("test-learner")

    @pytest.mark.asyncio
    async def test_get_token_fallback_to_shared(self, token_manager):
        """Test falling back to shared token when learner token is not available."""
        # Mock no learner token, but shared token available
        token_manager.store.get_token.return_value = None
        
        with patch('src.modules.skills.github.token_manager.settings') as mock_settings:
            mock_settings.github_access_token = "shared-token"
            
            token = await token_manager.get_token("test-learner")
            
            assert token == "shared-token"

    @pytest.mark.asyncio
    async def test_get_token_none_available(self, token_manager):
        """Test when no token is available."""
        # Mock no tokens available
        token_manager.store.get_token.return_value = None
        
        with patch('src.modules.skills.github.token_manager.settings') as mock_settings:
            mock_settings.github_access_token = None
            
            token = await token_manager.get_token("test-learner")
            
            assert token is None

    @pytest.mark.asyncio
    async def test_set_token_for_learner(self, token_manager):
        """Test setting token for a learner."""
        await token_manager.set_token("test-learner", "new-token")
        
        token_manager.store.set_token.assert_called_once_with("test-learner", "new-token")


class TestEncryptedTokenStore:
    """Test cases for EncryptedTokenStore."""

    @pytest.fixture
    def token_store(self):
        """Create an EncryptedTokenStore instance for testing."""
        with patch('src.modules.skills.github.token_store.Fernet'), \
             patch('src.modules.skills.github.token_store.DATA_DIR'):
            return EncryptedTokenStore(encryption_key="test-key")

    def test_set_and_get_token(self, token_store):
        """Test setting and getting tokens."""
        # Mock file operations
        token_store._fernet.encrypt.return_value = b"encrypted_data"
        token_store._fernet.decrypt.return_value = b"test-token"
        
        with patch('builtins.open', mock_open_read('{"tokens": {}}')):
            token_store.set_token("test-learner", "test-token")
            
            # Verify token was encrypted
            token_store._fernet.encrypt.assert_called_once()

    def test_get_token_not_found(self, token_store):
        """Test getting a token that doesn't exist."""
        with patch('builtins.open', mock_open_read('{"tokens": {}}')):
            token = token_store.get_token("nonexistent-learner")
            assert token is None

    def test_delete_token(self, token_store):
        """Test deleting a token."""
        with patch('builtins.open', mock_open_read('{"tokens": {"test-learner": "encrypted"}}')):
            token_store.delete_token("test-learner")
            # Verify the token would be removed from the dict

    def test_list_learners(self, token_store):
        """Test listing all learners with tokens."""
        test_data = '{"tokens": {"learner1": "token1", "learner2": "token2"}}'
        
        with patch('builtins.open', mock_open_read(test_data)):
            learners = token_store.list_learners()
            assert set(learners) == {"learner1", "learner2"}


def mock_open_read(content):
    """Mock open() for reading files."""
    from unittest.mock import mock_open
    return mock_open(read_data=content)


if __name__ == "__main__":
    pytest.main([__file__])
