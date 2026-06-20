"""Basic tests for Taxonomy Service functionality."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.taxonomy.taxonomy_service import TaxonomyService


class TestTaxonomyServiceBasic:
    """Basic test suite for taxonomy service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TaxonomyService()
    
    def test_service_initialization(self):
        """Test service initialization."""
        assert self.service is not None
        assert hasattr(self.service, 'esco_client')
        assert hasattr(self.service, 'onet_client')
        assert hasattr(self.service, 'cache')
        assert hasattr(self.service, 'stats')
        assert self.service.min_confidence == 0.7
        assert self.service.fallback_strategy == "esco_priority"
    
    def test_statistics_initialization(self):
        """Test statistics initialization."""
        stats = self.service.get_statistics()
        
        assert "total_lookups" in stats
        assert "cache_hits" in stats
        assert "esco_matches" in stats
        assert "onet_matches" in stats
        assert "no_matches" in stats
        assert stats["total_lookups"] == 0
    
    def test_cache_ttl_setting(self):
        """Test cache TTL setting."""
        from datetime import timedelta
        
        service = TaxonomyService(cache_ttl=timedelta(hours=12))
        assert service.cache_ttl == timedelta(hours=12)
    
    def test_confidence_thresholds(self):
        """Test confidence thresholds."""
        assert self.service.min_confidence == 0.7
        assert self.service.high_confidence == 0.9
    
    def test_fallback_strategy(self):
        """Test fallback strategy."""
        assert self.service.fallback_strategy == "esco_priority"
    
    def test_log_fallback(self):
        """Test fallback logging."""
        # This should not raise an exception
        self.service._log_fallback("skill", "Unknown Skill", "no_match")
    
    def test_enrichment_metadata_creation(self):
        """Test enrichment metadata creation."""
        from modules.knowledge.taxonomy.taxonomy_service import EnrichmentMetadata
        
        metadata = EnrichmentMetadata(
            esco_version="v1.1.0",
            onet_version="v27.3",
            enrichment_timestamp="2026-02-16T22:49:00Z",
            confidence_threshold=0.7,
            fallback_strategy="esco_priority"
        )
        
        assert metadata.esco_version == "v1.1.0"
        assert metadata.onet_version == "v27.3"
        assert metadata.confidence_threshold == 0.7
        assert metadata.fallback_strategy == "esco_priority"
    
    def test_taxonomy_match_creation(self):
        """Test taxonomy match creation."""
        from modules.knowledge.taxonomy.taxonomy_service import TaxonomyMatch
        
        match = TaxonomyMatch(
            uri="http://data.europa.eu/esco/skill/abcd123",
            label="Python programming",
            confidence=0.95,
            source="esco",
            language="en"
        )
        
        assert match.uri == "http://data.europa.eu/esco/skill/abcd123"
        assert match.label == "Python programming"
        assert match.confidence == 0.95
        assert match.source == "esco"
        assert match.language == "en"
    
    def test_cache_set_and_get(self):
        """Test cache set and get operations."""
        # Set cache
        cache_key = "test:key"
        test_data = {"test": "data"}
        self.service._set_cache(cache_key, test_data)
        
        # Get from cache
        cached_data = self.service._get_from_cache(cache_key)
        assert cached_data == test_data
        
        # Test cache miss
        non_existent = self.service._get_from_cache("nonexistent:key")
        assert non_existent is None


class TestESCOClientBasic:
    """Basic tests for ESCO client."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from modules.knowledge.taxonomy.esco_client import ESCOClient
        
        self.client = ESCOClient()
    
    def test_client_initialization(self):
        """Test ESCO client initialization."""
        assert self.client is not None
        assert hasattr(self.client, 'base_url')
        assert hasattr(self.client, 'cache')
        assert self.client.base_url.startswith("http")
    
    def test_default_headers(self):
        """Test default HTTP headers."""
        headers = self.client._get_default_headers()
        
        assert "Accept" in headers
        assert "Content-Type" in headers
        assert "User-Agent" in headers
    
    def test_supported_languages(self):
        """Test supported languages."""
        languages = self.client.get_supported_languages()
        
        assert isinstance(languages, list)
        assert "en" in languages
        assert "fr" in languages
        assert "de" in languages


class TestONETClientBasic:
    """Basic tests for O*NET client."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from modules.knowledge.taxonomy.onet_client import ONETClient
        
        self.client = ONETClient()
    
    def test_client_initialization(self):
        """Test O*NET client initialization."""
        assert self.client is not None
        assert hasattr(self.client, 'base_url')
        assert hasattr(self.client, 'cache')
        assert self.client.base_url.startswith("http")
    
    def test_default_headers(self):
        """Test default HTTP headers."""
        headers = self.client._get_default_headers()
        
        assert "Accept" in headers
        assert "Content-Type" in headers
        assert "User-Agent" in headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
