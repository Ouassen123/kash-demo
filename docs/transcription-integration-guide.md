# Speech-to-Text Integration Guide

This guide explains how to use the new speech-to-text transcription pipeline integrated into the Abilities module for Story 2.4.

## Overview

The transcription pipeline converts audio responses captured in the voice recording interface into structured transcripts that can flow into multimodal fusion, QA, and scoring pipelines. The system includes:

- **High-fidelity transcription** with timestamps, speaker tags, and confidence scores
- **Resilient fallback strategies** for low-bandwidth or offline scenarios
- **QA integration** for transcript review and correction
- **Privacy compliance** with encrypted storage and data purging

## Quick Start

### 1. Initialize the Extended Service

```python
from src.modules.abilities.abilities_service_transcription import AbilitiesServiceWithTranscription
from src.core.database import get_db

# Get database session
db = next(get_db())

# Initialize extended service
service = AbilitiesServiceWithTranscription(db)

# Start transcription services
await service.start_transcription_services(num_workers=3)
```

### 2. Process Audio Response

```python
# Process audio with automatic transcription
result = await service.process_audio_response(
    user_id="user_123",
    session_id="session_456", 
    prompt_id="prompt_789",
    audio_blob=audio_data,
    metadata={
        "language": "en-US",
        "duration_seconds": 15.5,
        "noise_level": 0.1,
    }
)

print(result)
# {
#   "status": "processed",
#   "session_id": "session_456",
#   "audio_processing": {...},
#   "transcription": {"status": "queued", "job_id": "job_123"},
# }
```

### 3. Get Session with Transcripts

```python
# Retrieve session data including approved transcripts
session_data = await service.get_session_with_transcripts(
    user_id="user_123",
    session_id="session_456"
)

if session_data["has_transcripts"]:
    transcripts = session_data["transcripts"]["transcripts"]
    for transcript in transcripts:
        print(f"Text: {transcript['content']['text']}")
        print(f"Confidence: {transcript['content']['aggregate_confidence']}")
```

## Architecture

### Core Components

1. **TranscriptionIntegration**: Main orchestrator that connects all components
2. **SpeechToTextPipeline**: Handles job queuing and processing with background workers
3. **TranscriptRepository**: Encrypted storage and retrieval of transcripts
4. **QAReviewHooks**: Integration with existing QA workflows
5. **FallbackOrchestrator**: Provider selection and fallback logic
6. **TelemetryRecorder**: Metrics and diagnostics

### Data Flow

```
Audio Upload → AudioProcessor → TranscriptionIntegration → SpeechToTextPipeline
                                                              ↓
                                                        Provider Selection
                                                              ↓
                                                        Transcription
                                                              ↓
                                                        Repository Storage
                                                              ↓
                                                        QA Review Hooks
                                                              ↓
                                                        Fusion Integration
```

## Provider Configuration

### Cloud Providers (Primary)

```python
from src.modules.abilities.transcription.providers.mock_provider import MockWhisperProvider

# Primary cloud providers
primary_providers = [
    MockWhisperProvider(model_size="base", mode="cloud"),
    MockWhisperProvider(model_size="small", mode="cloud"),
]
```

### Offline Providers (Fallback)

```python
from src.modules.abilities.transcription.providers.offline_provider import OfflineRNNProvider

# Offline fallback providers
offline_providers = [
    OfflineRNNProvider(model_name="rnn-t-small"),
]
```

### Provider Policies

```python
from src.modules.abilities.transcription.fallback_orchestrator import ProviderPolicy

policy = ProviderPolicy(
    name="whisper-base",
    priority=10,  # Higher priority = preferred
    max_latency_ms=5000,
    min_confidence=0.8,
    bandwidth_requirement_kbps=500,
    supports_streaming=True,
    supports_offline=False,
    cost_per_minute=0.01,
    languages=["en-US", "es-ES", "fr-FR"],
)
```

## QA Integration

### Register for Review

```python
# Transcripts are automatically registered for QA
# Review through the existing QA dashboard
qa_dashboard = await service.get_qa_dashboard()

print(f"Pending reviews: {qa_dashboard['pending_review']}")
print(f"Auto-approved: {qa_dashboard['auto_approved']}")
```

### Manual Review Interface

```python
from src.modules.abilities.transcription.qa.review_interface import TranscriptReviewInterface

review_interface = TranscriptReviewInterface(
    qa_hooks=service.transcription_integration.qa_hooks,
    repository=service.transcription_integration.repository
)

# Start review session
session = await review_interface.start_review_session(
    transcript_id="transcript_123",
    reviewer_id="reviewer_456"
)

# Get transcript data for review
review_data = await review_interface.get_review_data(session["session_id"])

# Add corrections
await review_interface.add_correction(
    session_id=session["session_id"],
    segment_id="seg_1",
    correction_type="text",
    original_value="hello world",
    corrected_value="hello world!",
    reason="Added punctuation"
)

# Complete review with approval
await review_interface.complete_review(
    session_id=session["session_id"],
    decision="approve",
    final_notes="Minor punctuation corrections applied"
)
```

## Fusion Integration

### Get Approved Transcripts for Fusion

```python
# Transcripts in fusion-ready format
fusion_data = await service.transcription_integration.get_approved_transcripts_for_fusion(
    session_id="session_456"
)

if fusion_data["status"] == "success":
    for transcript in fusion_data["transcripts"]:
        # Ready for multimodal fusion
        fusion_input = {
            "modality": "text_from_audio",
            "session_id": transcript["session_id"],
            "prompt_id": transcript["prompt_id"],
            "content": transcript["content"],
            "metadata": transcript["metadata"],
        }
```

### Integration with Multimodal Fusion

```python
from src.modules.abilities.fusion.api import MultimodalFusionAPI

# Initialize fusion API
fusion_api = MultimodalFusionAPI()

# Add transcript as text modality
for transcript in fusion_data["transcripts"]:
    await fusion_api.add_modality_data(
        session_id=transcript["session_id"],
        modality="text_from_audio",
        data=transcript["content"],
        metadata=transcript["metadata"]
    )

# Run fusion with audio transcript
fusion_result = await fusion_api.fuse_session_features(transcript["session_id"])
```

## Monitoring and Health

### Service Health

```python
# Get overall transcription health
health = await service.get_transcription_health()

print(f"Status: {health['status']}")
print(f"Workers active: {health['pipeline']['workers_active']}")
print(f"Queue size: {health['pipeline']['queue_size']}")
print(f"Success rate: {health['system_health']['success_rate']}")
```

### Provider Performance

```python
# Get provider performance metrics
performance = service.transcription_integration.telemetry_recorder.get_provider_performance(
    provider_name="whisper-base",
    hours_back=24
)

print(f"Average confidence: {performance['avg_confidence']}")
print(f"Average duration: {performance['avg_duration_ms']}ms")
print(f"Success rate: {performance['success_rate']}")
```

## Privacy and Compliance

### Data Purging

```python
# Complete session cleanup (privacy compliance)
cleanup_result = await service.cleanup_session_data(
    user_id="user_123",
    session_id="session_456"
)

print(f"Transcripts purged: {cleanup_result['transcripts_purged']}")
print(f"Audio deleted: {cleanup_result['audio_deleted']}")
print(f"QA deleted: {cleanup_result['qa_deleted']}")
```

### Encrypted Storage

All transcripts are stored with encryption:
- Structured JSON transcripts are encrypted at rest
- Plain text versions are stored for QA review only
- Audio hashes link transcripts to original audio files
- Full audit trail for all access and modifications

## Error Handling

### Common Error Scenarios

```python
# Handle transcription failures
result = await service.process_audio_response(
    user_id="user_123",
    session_id="session_456",
    prompt_id="prompt_789",
    audio_blob=audio_data
)

if result["transcription"]["status"] == "error":
    logger.error(f"Transcription failed: {result['transcription']['error']}")
    # Implement retry logic or fallback to manual processing

# Handle missing transcripts
session_data = await service.get_session_with_transcripts("user_123", "session_456")
if not session_data["has_transcripts"]:
    logger.warning("No approved transcripts available for fusion")
    # Proceed with other modalities or request manual review
```

## Configuration

### Environment Variables

```bash
# Transcription storage path
TRANSCRIPTION_STORAGE_PATH="./transcripts"

# Encryption key for transcript storage
TRANSCRIPTION_ENCRYPTION_KEY="your_secure_key_here"

# Number of transcription workers
TRANSCRIPTION_WORKERS=3

# Provider preferences
PRIMARY_PROVIDER="whisper-base"
FALLBACK_PROVIDER="offline-rnn"
```

### Service Configuration

```python
# Custom configuration
service = AbilitiesServiceWithTranscription(db)

# Start with custom settings
await service.start_transcription_services(num_workers=5)

# Update network status for fallback logic
service.transcription_integration.fallback_orchestrator.update_network_status(
    available=True,
    bandwidth_kbps=2000
)
```

## Testing

### Unit Tests

```bash
# Run transcription tests
python -m pytest tests/abilities/test_transcription_*.py -v
```

### Integration Tests

```python
# Test end-to-end flow
async def test_transcription_flow():
    service = AbilitiesServiceWithTranscription(db)
    await service.start_transcription_services()
    
    # Process audio
    result = await service.process_audio_response(
        user_id="test_user",
        session_id="test_session",
        prompt_id="test_prompt",
        audio_blob=b"mock_audio_data"
    )
    
    assert result["status"] == "processed"
    
    # Wait for transcription (in real scenario)
    await asyncio.sleep(2)
    
    # Check transcripts
    session_data = await service.get_session_with_transcripts("test_user", "test_session")
    assert session_data["has_transcripts"] == True
```

## Troubleshooting

### Common Issues

1. **Workers not starting**: Check if asyncio event loop is properly configured
2. **Transcription jobs stuck**: Verify provider health and network connectivity
3. **QA not receiving transcripts**: Ensure QA hooks are properly initialized
4. **Fusion not getting transcripts**: Check QA approval status and metadata format

### Debug Logging

```python
# Enable debug logging
import logging
logging.getLogger("src.modules.abilities.transcription").setLevel(logging.DEBUG)

# Monitor job queue
health = await service.get_transcription_health()
print(f"Queue size: {health['pipeline']['queue_size']}")
```

## Next Steps

1. **Production Providers**: Replace mock providers with real Whisper/Deepgram implementations
2. **Streaming Support**: Enable real-time streaming transcription for live feedback
3. **Advanced QA**: Implement AI-assisted QA review and confidence-based auto-approval
4. **Analytics**: Add detailed analytics on transcription quality and user engagement
5. **Multi-language**: Expand provider support for additional languages and locales
