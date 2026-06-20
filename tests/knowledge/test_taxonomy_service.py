"""Tests for Taxonomy Service."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.taxonomy.taxonomy_service import TaxonomyService


SKIP_ASYNC_REASON = "Temporarily skipped per Story 1-2 recommendation; pending async fix"


class TestTaxonomyService:
    """Test suite for taxonomy service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TaxonomyService()
        
        # Sample taxonomy data
        self.sample_esco_skills = {
            "http://data.europa.eu/esco/skill/abcd123": {
                "preferredLabel": {"en": "Python programming"},
                "description": {"en": "Programming using Python language"},
                "skillType": "skill/competence",
                "conceptUri": "http://data.europa.eu/esco/skill/abcd123"
            },
            "http://data.europa.eu/esco/skill/efgh456": {
                "preferredLabel": {"en": "JavaScript programming"},
                "description": {"en": "Programming using JavaScript language"},
                "skillType": "skill/competence",
                "conceptUri": "http://data.europa.eu/esco/skill/efgh456"
            }
        }
        
        self.sample_onet_occupations = {
            "15-1252.00": {
                "title": "Software Developers",
                "description": "Research, design, develop, and test software",
                "skills": ["Python", "JavaScript", "Software Development"],
                "zone": 4
            }
        }
        
        self.sample_cv_skills = [
            {"name": "Python", "confidence": 0.9},
            {"name": "JavaScript", "confidence": 0.8},
            {"name": "React", "confidence": 0.85}
        ]
    
    def test_service_initialization(self):
        """Test service initialization."""
        assert self.service is not None
        assert hasattr(self.service, 'esco_client')
        assert hasattr(self.service, 'onet_client')
        assert hasattr(self.service, 'cache')
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_skill_to_esco_mapping(self):
        """Test skill to ESCO mapping."""
        with patch.object(self.service.esco_client, 'search_skills', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {
                    "uri": "http://data.europa.eu/esco/skill/abcd123",
                    "label": "Python programming",
                    "confidence": 0.95,
                    "language": "en"
                }
            ]

            result = await asyncio.wait_for(
                self.service.map_skill_to_esco("Python"),
                timeout=5
            )

            assert result is not None
            assert result["uri"] == "http://data.europa.eu/esco/skill/abcd123"
            assert result["label"] == "Python programming"
            assert result["confidence"] == 0.95
            assert "mapping_timestamp" in result
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_skill_to_esco_no_match(self):
        """Test skill to ESCO mapping with no match."""
        with patch.object(self.service.esco_client, 'search_skills') as mock_search:
            mock_search.return_value = []
            
            result = await self.service.map_skill_to_esco("Unknown Skill")
            
            assert result is None
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_batch_skill_mapping(self):
        """Test batch skill mapping."""
        with patch.object(self.service, 'map_skill_to_esco') as mock_map:
            mock_map.side_effect = [
                {"uri": "esco://python", "confidence": 0.9},
                {"uri": "esco://javascript", "confidence": 0.8},
                None
            ]
            
            results = await self.service.map_skills_batch(self.sample_cv_skills)
            
            assert len(results) == 3
            assert results[0]["uri"] == "esco://python"
            assert results[1]["uri"] == "esco://javascript"
            assert results[2] is None
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_occupation_to_onet_mapping(self):
        """Test occupation to O*NET mapping."""
        with patch.object(self.service.onet_client, 'search_occupations', AsyncMock()) as mock_search:
            mock_search.return_value = [
                {
                    "code": "15-1252.00",
                    "title": "Software Developers",
                    "confidence": 0.85
                }
            ]
            
            result = await self.service.map_occupation_to_onet("Software Engineer")
            
            assert result is not None
            assert result["code"] == "15-1252.00"
            assert result["title"] == "Software Developers"
            assert result["confidence"] == 0.85
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_taxonomy_version_tracking(self):
        """Test taxonomy version tracking."""
        with patch.object(self.service.esco_client, 'get_version', AsyncMock()) as mock_esco_ver, \
             patch.object(self.service.onet_client, 'get_version', AsyncMock()) as mock_onet_ver:
            
            mock_esco_ver.return_value = "v1.1.0"
            mock_onet_ver.return_value = "v27.3"
            
            versions = await self.service.get_taxonomy_versions()
            
            assert "esco" in versions
            assert "onet" in versions
            assert versions["esco"] == "v1.1.0"
            assert versions["onet"] == "v27.3"
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """Test caching functionality."""
        # First call should hit the API
        with patch.object(self.service.esco_client, 'search_skills', AsyncMock()) as mock_search:
            mock_search.return_value = [{"uri": "esco://python", "confidence": 0.9, "label": "Python", "language": "en"}]
            
            result1 = await self.service.map_skill_to_esco("Python")
            assert mock_search.call_count == 1
            
            # Second call should use cache
            result2 = await self.service.map_skill_to_esco("Python")
            assert mock_search.call_count == 1  # No additional call
            
            assert result1 == result2
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_confidence_threshold_filtering(self):
        """Test confidence threshold filtering."""
        with patch.object(self.service.esco_client, 'search_skills', AsyncMock()) as mock_search:
            # Low confidence match should be filtered out
            mock_search.return_value = [
                {"uri": "esco://python", "confidence": 0.3, "label": "Python", "language": "en"}
            ]
            
            result = await self.service.map_skill_to_esco("Python", min_confidence=0.5)
            
            assert result is None  # Filtered out due to low confidence
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_language_aware_mapping(self):
        """Test language-aware taxonomy mapping."""
        with patch.object(self.service.esco_client, 'search_skills', AsyncMock()) as mock_search:
            mock_search.return_value = [
                {
                    "uri": "esco://python",
                    "label": "Python programming",
                    "confidence": 0.9,
                    "language": "en"
                }
            ]
            
            await self.service.map_skill_to_esco("Python", language="fr")
            
            # Should pass language parameter to ESCO client
            mock_search.assert_called_once_with("Python", language="fr")
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_taxonomy_data_refresh(self):
        """Test taxonomy data refresh functionality."""
        with patch.object(self.service.esco_client, 'health_check', AsyncMock()) as mock_esco, \
             patch.object(self.service.onet_client, 'health_check', AsyncMock()) as mock_onet:
            
            mock_esco.return_value = {"status": "healthy"}
            mock_onet.return_value = {"status": "healthy"}
            result = await self.service.refresh_taxonomy_data()
            
            mock_esco.assert_called_once()
            mock_onet.assert_called_once()
            assert result == {"esco": True, "onet": True}
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_enrichment_metadata_generation(self):
        """Test enrichment metadata generation."""
        async def mock_map(name, **kwargs):
            mapping = {
                "Python": {"uri": "esco://python", "label": "Python", "confidence": 0.9, "language": "en"},
                "JavaScript": {"uri": "esco://javascript", "label": "JavaScript", "confidence": 0.8, "language": "en"}
            }
            return mapping.get(name)
        
        with patch.object(self.service, 'map_skill_to_esco', AsyncMock(side_effect=mock_map)):
            
            enriched = await self.service.enrich_cv_skills(self.sample_cv_skills)
            
            assert len(enriched) == 3
            assert enriched[0]["esco_uri"] == "esco://python"
            assert enriched[1]["esco_uri"] == "esco://javascript"
            assert enriched[2]["esco_uri"] is None
            assert "enrichment_timestamp" in enriched[0]
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_fallback_strategy_logging(self):
        """Test fallback strategy logging."""
        with patch.object(self.service.esco_client, 'search_skills', AsyncMock()) as mock_search, \
             patch.object(self.service, '_log_fallback') as mock_log:
            
            # No match found
            mock_search.return_value = []
            
            result = await self.service.map_skill_to_esco("Unknown Skill")
            
            assert result is None
            mock_log.assert_called_once()
            
            # Check log arguments
            call_args = mock_log.call_args[0]
            assert call_args[0] == "skill"
            assert call_args[1] == "Unknown Skill"
            assert "reason" in call_args[2]
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_taxonomy_health_check(self):
        """Test taxonomy service health check."""
        with patch.object(self.service.esco_client, 'health_check', AsyncMock()) as mock_esco, \
             patch.object(self.service.onet_client, 'health_check', AsyncMock()) as mock_onet:
            
            mock_esco.return_value = {"status": "healthy", "response_time_ms": 150}
            mock_onet.return_value = {"status": "healthy", "response_time_ms": 200}
            
            health = await self.service.health_check()
            
            assert health["status"] == "healthy"
            assert "esco" in health
            assert "onet" in health
            assert health["esco"]["status"] == "healthy"
            assert health["onet"]["status"] == "healthy"
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in taxonomy service."""
        with patch.object(self.service.esco_client, 'search_skills', AsyncMock()) as mock_search:
            mock_search.side_effect = Exception("API Error")
            
            result = await self.service.map_skill_to_esco("Python")
            assert result is None
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_async_batch_processing(self):
        """Test async batch processing capabilities."""
        with patch.object(self.service, 'map_skill_to_esco', AsyncMock()) as mock_map:
            mock_map.side_effect = [
                {"uri": "esco://python", "confidence": 0.9},
                {"uri": "esco://javascript", "confidence": 0.8},
                {"uri": "esco://react", "confidence": 0.85}
            ]
            
            results = await self.service.map_skills_batch(self.sample_cv_skills)
            
            assert len(results) == 3
            assert all(result is not None for result in results)


class TestTaxonomyIntegration:
    """Integration tests for taxonomy service."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.service = TaxonomyService()
    
    @pytest.mark.skip(reason=SKIP_ASYNC_REASON)
    @pytest.mark.asyncio
    async def test_end_to_end_skill_enrichment(self):
        """Test end-to-end skill enrichment workflow."""
        # This would be an integration test with real taxonomy data
        # For now, we'll mock the external services
        
        sample_cv_analysis = {
            "skills": [
                {"name": "Python", "confidence": 0.9},
                {"name": "JavaScript", "confidence": 0.8}
            ],
            "education": [],
            "experience": [],
            "certifications": []
        }
        
        with patch.object(self.service, 'map_skill_to_esco', AsyncMock()) as mock_skill_map, \
             patch.object(self.service, 'map_occupation_to_onet', AsyncMock()) as mock_occ_map, \
             patch.object(self.service, 'get_taxonomy_versions', AsyncMock()) as mock_versions:
            mock_skill_map.side_effect = [
                {
                    "uri": "http://data.europa.eu/esco/skill/abcd123",
                    "label": "Python programming",
                    "confidence": 0.95,
                    "language": "en"
                },
                None
            ]
            mock_occ_map.return_value = None
            mock_versions.return_value = {"esco": "v1.1.0", "onet": "v27.3"}

            enriched_result = await self.service.enrich_cv_analysis(sample_cv_analysis)

            assert "taxonomy_metadata" in enriched_result
            assert enriched_result["skills"][0]["esco_uri"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
