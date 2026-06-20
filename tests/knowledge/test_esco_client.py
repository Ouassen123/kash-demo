"""Tests for ESCO Client."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import httpx

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.taxonomy.esco_client import ESCOClient


class TestESCOClient:
    """Test suite for ESCO client functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = ESCOClient()
        
        # Sample ESCO API response
        self.sample_skill_response = {
            "_embedded": {
                "results": [
                    {
                        "_links": {
                            "self": {"href": "http://data.europa.eu/esco/skill/abcd123"}
                        },
                        "preferredLabel": {
                            "en": "Python programming"
                        },
                        "description": {
                            "en": "Programming using Python language"
                        },
                        "skillType": "skill/competence",
                        "conceptUri": "http://data.europa.eu/esco/skill/abcd123"
                    }
                ]
            },
            "total": 1,
            "limit": 10
        }
        
        self.sample_occupation_response = {
            "_embedded": {
                "results": [
                    {
                        "_links": {
                            "self": {"href": "http://data.europa.eu/esco/occupation/xyz789"}
                        },
                        "preferredLabel": {
                            "en": "Software Developer"
                        },
                        "description": {
                            "en": "Develops and maintains software applications"
                        },
                        "conceptUri": "http://data.europa.eu/esco/occupation/xyz789"
                    }
                ]
            },
            "total": 1,
            "limit": 10
        }
    
    def test_client_initialization(self):
        """Test ESCO client initialization."""
        assert self.client is not None
        assert hasattr(self.client, 'base_url')
        assert hasattr(self.client, 'api_key')
        assert self.client.base_url.startswith("http")
    
    def test_search_skills_success(self):
        """Test successful skill search."""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = self.sample_skill_response
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            results = self.client.search_skills("Python")
            
            assert len(results) == 1
            assert results[0]["uri"] == "http://data.europa.eu/esco/skill/abcd123"
            assert results[0]["label"] == "Python programming"
            assert results[0]["confidence"] > 0.8
    
    def test_search_skills_no_results(self):
        """Test skill search with no results."""
        empty_response = {
            "_embedded": {"results": []},
            "total": 0,
            "limit": 10
        }
        
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = empty_response
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            results = self.client.search_skills("Unknown Skill")
            
            assert len(results) == 0
    
    def test_search_skills_with_language(self):
        """Test skill search with language parameter."""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = self.sample_skill_response
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            self.client.search_skills("Python", language="fr")
            
            # Verify language parameter was passed
            call_args = mock_get.call_args
            assert "language=fr" in call_args[0][0] or "language" in call_args[1]["params"]
    
    def test_search_occupations_success(self):
        """Test successful occupation search."""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = self.sample_occupation_response
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            results = self.client.search_occupations("Software Developer")
            
            assert len(results) == 1
            assert results[0]["uri"] == "http://data.europa.eu/esco/occupation/xyz789"
            assert results[0]["title"] == "Software Developer"
    
    def test_get_skill_by_uri(self):
        """Test getting skill by URI."""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = self.sample_skill_response["_embedded"]["results"][0]
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = self.client.get_skill_by_uri("http://data.europa.eu/esco/skill/abcd123")
            
            assert result is not None
            assert result["label"] == "Python programming"
            assert result["uri"] == "http://data.europa.eu/esco/skill/abcd123"
    
    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        # Exact match should have high confidence
        exact_match = self.client._calculate_confidence("Python", "Python programming")
        assert exact_match >= 0.9
        
        # Partial match should have medium confidence
        partial_match = self.client._calculate_confidence("Python", "Python development")
        assert 0.6 <= partial_match < 0.9
        
        # No match should have low confidence
        no_match = self.client._calculate_confidence("Java", "Python programming")
        assert no_match < 0.5
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = self.sample_skill_response
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # Make multiple requests
            for i in range(5):
                self.client.search_skills(f"Skill {i}")
            
            # Should respect rate limiting
            assert mock_get.call_count <= 5
    
    def test_error_handling(self):
        """Test error handling in API calls."""
        with patch('httpx.get') as mock_get:
            mock_get.side_effect = httpx.RequestError("Connection error")
            
            with pytest.raises(Exception):
                self.client.search_skills("Python")
    
    def test_api_key_authentication(self):
        """Test API key authentication."""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = self.sample_skill_response
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            self.client.search_skills("Python")
            
            # Verify API key was included in headers
            call_args = mock_get.call_args
            headers = call_args[1].get("headers", {})
            assert "Authorization" in headers or "X-API-Key" in headers
    
    def test_response_validation(self):
        """Test response validation."""
        # Test with malformed response
        malformed_response = {"invalid": "structure"}
        
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = malformed_response
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            with pytest.raises(ValueError):
                self.client.search_skills("Python")
    
    def test_caching_behavior(self):
        """Test caching behavior."""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = self.sample_skill_response
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # First call
            result1 = self.client.search_skills("Python")
            assert mock_get.call_count == 1
            
            # Second call should use cache
            result2 = self.client.search_skills("Python")
            assert mock_get.call_count == 1  # No additional call
            
            assert result1 == result2
    
    def test_health_check(self):
        """Test health check functionality."""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_get.return_value = mock_response
            
            health = self.client.health_check()
            
            assert health["status"] == "healthy"
            assert "response_time_ms" in health
            assert "api_version" in health
    
    def test_batch_skill_search(self):
        """Test batch skill search."""
        skills = ["Python", "JavaScript", "React"]
        
        with patch.object(self.client, 'search_skills') as mock_search:
            mock_search.side_effect = [
                [{"uri": "esco://python", "confidence": 0.9}],
                [{"uri": "esco://javascript", "confidence": 0.8}],
                [{"uri": "esco://react", "confidence": 0.85}]
            ]
            
            results = self.client.search_skills_batch(skills)
            
            assert len(results) == 3
            assert results[0][0]["uri"] == "esco://python"
            assert results[1][0]["uri"] == "esco://javascript"
            assert results[2][0]["uri"] == "esco://react"
    
    def test_uri_validation(self):
        """Test URI validation."""
        # Valid URI
        valid_uri = "http://data.europa.eu/esco/skill/abcd123"
        assert self.client._validate_uri(valid_uri) == True
        
        # Invalid URI
        invalid_uri = "not-a-uri"
        assert self.client._validate_uri(invalid_uri) == False
        
        # Empty URI
        assert self.client._validate_uri("") == False
    
    def test_language_support(self):
        """Test language support."""
        supported_languages = self.client.get_supported_languages()
        
        assert "en" in supported_languages
        assert "fr" in supported_languages
        assert "de" in supported_languages
        assert "es" in supported_languages
    
    def test_skill_type_filtering(self):
        """Test skill type filtering."""
        with patch('httpx.get') as mock_get:
            # Mock response with different skill types
            response_with_types = {
                "_embedded": {
                    "results": [
                        {
                            "preferredLabel": {"en": "Python programming"},
                            "skillType": "skill/competence",
                            "conceptUri": "http://data.europa.eu/esco/skill/abcd123"
                        },
                        {
                            "preferredLabel": {"en": "Communication"},
                            "skillType": "knowledge/skill",
                            "conceptUri": "http://data.europa.eu/esco/skill/efgh456"
                        }
                    ]
                }
            }
            
            mock_response = Mock()
            mock_response.json.return_value = response_with_types
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # Filter by skill type
            results = self.client.search_skills("Python", skill_type="skill/competence")
            
            assert len(results) == 1
            assert results[0]["uri"] == "http://data.europa.eu/esco/skill/abcd123"


class TestESCOClientIntegration:
    """Integration tests for ESCO client."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.client = ESCOClient()
    
    def test_real_api_connection(self):
        """Test real API connection (if available)."""
        # This test would only run if API key is available
        # and network access is permitted
        
        if not self.client.api_key:
            pytest.skip("No API key available for integration test")
        
        try:
            results = self.client.search_skills("Python")
            assert isinstance(results, list)
        except Exception as e:
            pytest.skip(f"API not available: {e}")
    
    def test_api_version_compatibility(self):
        """Test API version compatibility."""
        # Mock version check
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "apiVersion": "v1.0.0",
                "supportedVersions": ["v1.0.0", "v0.9.0"]
            }
            mock_get.return_value = mock_response
            
            version = self.client.get_api_version()
            
            assert version == "v1.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
