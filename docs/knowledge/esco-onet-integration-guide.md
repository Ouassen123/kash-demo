# ESCO/O*NET Integration Guide

## Overview

This guide explains how the ESCO and O*NET taxonomy integration works in the KASH Knowledge Module and how to use it for enriching CV analysis results.

## Architecture

### Components

1. **ESCO Client** (`src/modules/knowledge/taxonomy/esco_client.py`)
   - Async HTTP client for European Skills/Competences, Qualifications and Occupations (ESCO) API
   - Handles skill and occupation searches
   - Implements confidence scoring and URI validation
   - Includes rate limiting and caching

2. **O*NET Client** (`src/modules/knowledge/taxonomy/onet_client.py`)
   - Async HTTP client for O*NET API
   - Handles occupation searches and related data retrieval
   - Implements confidence scoring and code validation
   - Includes rate limiting and caching

3. **Taxonomy Service** (`src/modules/knowledge/taxonomy/taxonomy_service.py`)
   - Orchestrates both ESCO and O*NET clients
   - Provides unified interface for taxonomy lookups
   - Implements caching and statistics
   - Handles fallback strategies

4. **Enrichment Service** (`src/modules/knowledge/taxonomy/enrichment_service.py`)
   - High-level service for enriching CV analysis
   - Batch processing capabilities
   - Quality scoring and validation
   - Integration with NLP pipeline

## Usage

### Basic Skill Mapping

```python
from modules.knowledge.taxonomy.taxonomy_service import TaxonomyService

# Initialize service
taxonomy_service = TaxonomyService()

# Map a skill to ESCO
result = await taxonomy_service.map_skill_to_esco("Python")
if result:
    print(f"ESCO URI: {result['uri']}")
    print(f"Label: {result['label']}")
    print(f"Confidence: {result['confidence']}")
```

### Batch Skill Enrichment

```python
# Enrich CV analysis with taxonomy data
cv_analysis = {
    "skills": [
        {"name": "Python", "confidence": 0.9},
        {"name": "JavaScript", "confidence": 0.8}
    ]
}

enriched = await taxonomy_service.enrich_cv_analysis(cv_analysis)

# Enriched skills will have ESCO data
for skill in enriched["skills"]:
    if skill.get("esco_uri"):
        print(f"{skill['name']} -> {skill['esco_label']} ({skill['esco_confidence']})")
```

### Occupation Mapping

```python
# Map job title to O*NET
result = await taxonomy_service.map_occupation_to_onet("Software Engineer")
if result:
    print(f"O*NET Code: {result['code']}")
    print(f"Title: {result['title']}")
    print(f"Confidence: {result['confidence']}")
```

## API Reference

### TaxonomyService Methods

#### `map_skill_to_esco(skill, language="en", min_confidence=None)`
Map a skill to ESCO taxonomy.

**Parameters:**
- `skill` (str): Skill name to map
- `language` (str): Language code (default: "en")
- `min_confidence` (float): Minimum confidence threshold (default: 0.7)

**Returns:** Dict with ESCO match or None

#### `map_occupation_to_onet(occupation, min_confidence=None)`
Map an occupation to O*NET taxonomy.

**Parameters:**
- `occupation` (str): Occupation name to map
- `min_confidence` (float): Minimum confidence threshold (default: 0.7)

**Returns:** Dict with O*NET match or None

#### `enrich_cv_analysis(cv_analysis, language="en")`
Enrich complete CV analysis with taxonomy data.

**Parameters:**
- `cv_analysis` (Dict): CV analysis from NLP pipeline
- `language` (str): Language code for taxonomy lookup

**Returns:** Enriched CV analysis with taxonomy metadata

#### `get_taxonomy_versions()`
Get current versions of taxonomy APIs.

**Returns:** Dict with version information

#### `health_check()`
Check health of taxonomy services and dependencies.

**Returns:** Health check results

#### `get_statistics()`
Get taxonomy service statistics.

**Returns:** Statistics dictionary

## Configuration

### Environment Variables

```bash
# ESCO API (optional)
ESCO_API_KEY=your_esco_api_key

# O*NET API (optional)
ONET_API_KEY=your_onet_api_key

# Base URLs
ESCO_BASE_URL=https://ec.europa.eu/esco/api
ONET_BASE_URL=https://services.onetcenter.org/ws/migrate
```

### Service Configuration

```python
from datetime import timedelta

taxonomy_service = TaxonomyService(
    cache_ttl=timedelta(hours=24),
    min_confidence=0.7,
    fallback_strategy="esco_priority"
)
```

## Data Contracts

### ESCO Skill Match

```json
{
    "uri": "http://data.europa.eu/esco/skill/abcd123",
    "label": "Python programming",
    "confidence": 0.95,
    "language": "en",
    "mapping_timestamp": "2026-02-16T22:49:00Z"
}
```

### O*NET Occupation Match

```json
{
    "code": "15-1252.00",
    "title": "Software Developers",
    "confidence": 0.85,
    "zone": "4",
    "mapping_timestamp": "2026-02-16T22:49:00Z"
}
```

### Enriched Skill

```json
{
    "name": "Python",
    "confidence": 0.9,
    "esco_uri": "http://data.europa.eu/esco/skill/abcd123",
    "esco_label": "Python programming",
    "esco_confidence": 0.95,
    "esco_language": "en",
    "enrichment_timestamp": "2026-02-16T22:49:00Z"
}
```

### Enriched Experience

```json
{
    "title": "Software Engineer",
    "company": "Tech Corp",
    "dates": "2020-Present",
    "description": "Developed RESTful APIs",
    "onet_code": "15-1252.00",
    "onet_title": "Software Developers",
    "onet_confidence": 0.85,
    "enrichment_timestamp": "2026-02-16T22:49:00Z"
}
```

### Taxonomy Metadata

```json
{
    "esco_version": "v1.1.0",
    "onet_version": "v27.3",
    "enrichment_timestamp": "2026-02-16T22:49:00Z",
    "confidence_threshold": 0.7,
    "fallback_strategy": "esco_priority"
}
```

## Error Handling

### Common Errors

1. **API Unavailable**: Services will gracefully degrade when APIs are unavailable
2. **Rate Limiting**: Built-in rate limiting prevents API abuse
3. **Invalid Data**: Invalid URIs or codes are filtered out
4. **Network Issues**: Network errors are logged and handled gracefully

### Fallback Strategies

When ESCO and O*NET are both unavailable, the service will:
- Return None for all lookups
- Log fallback events
- Continue with unenriched data

### Logging

The service logs:
- Successful matches
- Fallback events
- API errors
- Cache hits/misses
- Performance metrics

## Performance

### Caching

- **TTL**: 24 hours by default
- **Cache Hit Rate**: Tracked in statistics
- **Cache Size**: Monitored for memory usage

### Rate Limiting

- **ESCO**: 100ms between requests
- **O*NET**: 200ms between requests
- **Batch Processing**: Available for bulk operations

### Async Processing

- All API calls are asynchronous
- Batch processing available for better performance
- Proper cleanup with async context managers

## Monitoring

### Health Checks

```python
health = await taxonomy_service.health_check()
print(f"Status: {health['status']}")
print(f"ESCO: {health['services']['esco']['status']}")
print(f"O*NET: {health['services']['onet']['status']}")
```

### Statistics

```python
stats = taxonomy_service.get_statistics()
print(f"Total lookups: {stats['total_lookups']}")
print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
print(f"ESCO matches: {stats['esco_matches']}")
print(f"O*NET matches: {stats['onet_matches']}")
```

## Integration Examples

### With NLP Pipeline

```python
from modules.knowledge.nlp.cv_analyzer import CVAnalyzer
from modules.knowledge.taxonomy.enrichment_service import EnrichmentService

# Analyze CV
analyzer = CVAnalyzer()
cv_analysis = analyzer.analyze_cv(cv_text)

# Enrich with taxonomy
enrichment_service = EnrichmentService()
enriched_analysis = await enrichment_service.enrich_cv_analysis(cv_analysis)
```

### With Knowledge Service

```python
from src.modules.knowledge.knowledge_service import KnowledgeService
from src.modules.knowledge.taxonomy.taxonomy_service import TaxonomyService

# Initialize services
knowledge_service = KnowledgeService(db)
taxonomy_service = TaxonomyService()

# Process CV with full enrichment
user_assessment = await knowledge_service.analyze_cv(user_id, cv_text)
enriched_assessment = await taxonomy_service.enrich_cv_analysis(user_assessment.result_data)
```

## Testing

### Unit Tests

```bash
# Run all taxonomy tests
python -m pytest tests/knowledge/test_taxonomy_*.py -v

# Run only basic tests
python -m pytest tests/knowledge/test_taxonomy_basic.py -v
```

### Integration Tests

```bash
# Run integration tests
python -m pytest tests/knowledge/test_integration.py -v
```

### Mock Testing

```python
# Mock external APIs for unit tests
with patch('modules.knowledge.taxonomy.esco_client.ESCOClient.search_skills') as mock_search:
    mock_search.return_value = [
        {"uri": "esco://python", "label": "Python programming", "confidence": 0.95}
    ]
    
    result = await taxonomy_service.map_skill_to_esco("Python")
    assert result["uri"] == "esco://python"
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed (`pip install httpx aiohttp`)
2. **API Keys**: Set environment variables for API access
3. **Network Issues**: Check firewall and proxy settings
4. **Cache Issues**: Clear cache if stale data is suspected

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging in services
logger.setLevel(logging.DEBUG)
```

### Performance Issues

1. **Slow Lookups**: Check cache hit rate
2. **Memory Usage**: Monitor cache size
3. **Network Latency**: Check API response times

## Best Practices

1. **Use Async**: Always await async methods
2. **Handle Exceptions**: Wrap API calls in try/catch blocks
3. **Monitor Health**: Regular health checks
4. **Validate Data**: Validate API responses
5. **Log Events**: Log important events and errors

## Migration Guide

### From Manual Integration

```python
# Before
from esco_client import ESCOClient
from onet_client import ONETClient

# After
from modules.knowledge.taxonomy.taxonomy_service import TaxonomyService

# Initialize unified service
taxonomy_service = TaxonomyService()
```

### From Mock Testing

```python
# Before
mock_esco = Mock()
mock_onet = Mock()

# After
taxonomy_service = TaxonomyService()
# Mock the internal clients if needed
taxonomy_service.esco_client = mock_esco
taxonomy_service.onet_client = mock_onet
```

## Version Compatibility

- **ESCO API**: v1.0.0+
- **O*NET API**: v27.3+
- **Python**: 3.8+
- **httpx**: 0.28.0+
- **aiohttp**: 3.13.3+

## Support

For issues and questions:

1. Check the logs for error messages
2. Review the documentation for specific use cases
3. Create minimal reproduction cases for bugs
4. Check API status pages for service availability
