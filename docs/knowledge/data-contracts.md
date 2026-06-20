# Knowledge Module Data Contracts

## Overview

This document defines the data contracts and expected formats for the Knowledge Module NLP CV Analysis engine, ensuring seamless integration with downstream components (Abilities, Skills, Intelligence modules).

## CV Analysis Output Format

### Complete Analysis Response

```json
{
  "skills": [
    {
      "name": "Python",
      "confidence": 0.95,
      "context": "Skills: Python, JavaScript, Java",
      "position": "skills_section",
      "source_text": "Skills: Python, JavaScript, Java, SQL",
      "skill_type": "programming",
      "proficiency_level": null,
      "years_experience": null
    }
  ],
  "education": [
    {
      "name": "Bachelor of Science in Computer Science",
      "confidence": 0.9,
      "context": "EDUCATION\nBachelor of Science in Computer Science",
      "position": "education_section",
      "source_text": "Bachelor of Science in Computer Science",
      "degree": "Bachelor of Science in Computer Science",
      "institution": "Stanford University",
      "dates": "2015-2019",
      "gpa": "3.8/4.0",
      "field_of_study": "Computer Science"
    }
  ],
  "experience": [
    {
      "name": "Senior Software Engineer",
      "confidence": 0.85,
      "context": "EXPERIENCE\nSenior Software Engineer at Tech Corp",
      "position": "experience_section",
      "source_text": "Senior Software Engineer at Tech Corp (2020-Present)",
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "dates": "2020-Present",
      "description": "Developed RESTful APIs using Python and FastAPI",
      "achievements": ["Led team of 5 developers", "Improved performance by 40%"]
    }
  ],
  "certifications": [
    {
      "name": "AWS Certified Solutions Architect",
      "confidence": 0.9,
      "context": "CERTIFICATIONS\nAWS Certified Solutions Architect (2022)",
      "position": "certification_section",
      "source_text": "AWS Certified Solutions Architect (2022)",
      "issuer": "Amazon Web Services",
      "date": "2022",
      "credential_id": null,
      "expiry_date": null
    }
  ],
  "metadata": {
    "analysis_timestamp": "2026-02-16T22:49:00Z",
    "language_detected": "en",
    "total_sections_found": 4,
    "word_count": 150,
    "line_count": 25,
    "overall_confidence": 0.87
  }
}
```

## Downstream Integration Contracts

### 1. Abilities Module Integration

**Expected Input Format:**
```json
{
  "knowledge_profile": {
    "skills": [...],
    "education": [...],
    "confidence_score": 0.87,
    "language": "en"
  }
}
```

**Usage in Abilities Module:**
- Skills confidence weighting for adaptive quiz generation
- Education level for cognitive test difficulty calibration
- Language detection for test localization

### 2. Skills Module Integration

**Expected Input Format:**
```json
{
  "extracted_skills": [
    {
      "name": "Python",
      "confidence": 0.95,
      "mapped_taxonomy": {
        "category": "programming",
        "subcategory": "languages",
        "normalized_skill": "Python"
      }
    }
  ]
}
```

**Usage in Skills Module:**
- Baseline skill inventory for GitHub integration comparison
- Confidence scores for skill validation
- Taxonomy mapping for mini-project recommendations

### 3. Intelligence Module Integration

**Expected Input Format:**
```json
{
  "knowledge_vectors": {
    "skills_vector": [0.8, 0.6, 0.9, ...],
    "education_vector": [0.7, 0.8, 0.5, ...],
    "experience_vector": [0.9, 0.7, 0.6, ...],
    "confidence_weights": [0.95, 0.9, 0.85, ...]
  }
}
```

**Usage in Intelligence Module:**
- Input features for LightGBM prediction model
- Confidence weights for prediction reliability
- ESCO/O*NET mapping foundation for job matching

## Database Schema Integration

### UserAssessment Table (Knowledge Records)

```sql
-- Knowledge assessment records
INSERT INTO user_assessments (
    id, user_id, assessment_type, assessment_name, 
    input_data, result_data, confidence_score, 
    normalized_score, assessment_metadata
) VALUES (
    'uuid', 'user_uuid', 'knowledge', 'CV Analysis',
    '{"cv_text": "..."}', 
    '{"skills": [...], "education": [...]}',
    0.87, 87.0,
    '{"analysis_engine": "nlp_cv_analyzer_v1"}'
);
```

### KnowledgeAssessment Table

```sql
-- Detailed knowledge assessment data
INSERT INTO knowledge_assessments (
    id, assessment_id, cv_text, cv_parsed_data,
    esco_skills, esco_occupations
) VALUES (
    'uuid', 'assessment_uuid', 'CV text content',
    '{"skills": [...], "education": [...]}',
    '[{"skill": "Python", "esco_id": "3c1e2a1"}]',
    '[{"occupation": "Software Developer", "esco_id": "1a2b3c4"}]'
);
```

## API Endpoints Contract

### POST /api/v1/knowledge/analyze-cv

**Request:**
```json
{
  "cv_text": "Raw CV text content...",
  "user_id": "user-uuid",
  "persist": true
}
```

**Response:**
```json
{
  "assessment_id": "uuid",
  "status": "completed",
  "analysis_result": { /* Complete analysis format */ },
  "confidence_score": 0.87,
  "processing_time_ms": 1250
}
```

### GET /api/v1/knowledge/analysis/{assessment_id}

**Response:**
```json
{
  "assessment_id": "uuid",
  "user_id": "user-uuid",
  "analysis_result": { /* Complete analysis format */ },
  "created_at": "2026-02-16T22:49:00Z",
  "confidence_score": 0.87
}
```

## Error Handling Contract

### Validation Errors

```json
{
  "error": "validation_error",
  "message": "CV text must be at least 100 characters long",
  "field": "cv_text",
  "code": "INVALID_INPUT"
}
```

### Processing Errors

```json
{
  "error": "processing_error",
  "message": "Failed to analyze CV due to NLP processing error",
  "details": "spaCy model not available",
  "code": "PROCESSING_FAILED"
}
```

### Database Errors

```json
{
  "error": "persistence_error",
  "message": "Failed to save analysis results",
  "details": "Database connection timeout",
  "code": "PERSISTENCE_FAILED"
}
```

## Performance Requirements

### Response Time Targets

- **Simple CV (500 words):** < 500ms
- **Complex CV (2000 words):** < 1500ms
- **Batch processing (10 CVs):** < 5000ms

### Memory Limits

- **Maximum CV size:** 100,000 characters
- **Concurrent analyses:** 10 simultaneous
- **Memory per analysis:** < 100MB

## Quality Assurance

### Confidence Thresholds

- **High confidence:** ≥ 0.8 - Ready for automated processing
- **Medium confidence:** 0.6-0.8 - Requires human review
- **Low confidence:** < 0.6 - Flag for manual verification

### Ambiguity Detection

Items flagged with ambiguity score ≥ 0.5 should be:
- Highlighted in UI for human review
- Weighted lower in scoring calculations
- Logged for quality monitoring

## Monitoring and Observability

### Metrics to Track

- Analysis success rate
- Average processing time
- Confidence score distribution
- Ambiguity detection rate
- Error rates by category

### Logging Requirements

- Structured JSON logging
- Request/response correlation IDs
- Performance metrics
- Error details with stack traces

## Versioning and Compatibility

### API Versioning

- Current version: v1
- Backward compatibility maintained for 6 months
- Breaking changes require version bump

### Data Format Evolution

- New fields added as optional
- Existing fields maintain compatibility
- Deprecation warnings for removed fields

## Security Considerations

### Data Privacy

- CV text encrypted at rest
- Analysis results anonymized in logs
- User consent required for processing

### Input Validation

- Maximum size limits enforced
- Content sanitization for malicious input
- Rate limiting per user/IP

### Access Control

- User-scoped data access
- Role-based permissions for analysis
- Audit logging for data access
