# Abilities Speech-to-Text Module

Story 2.4 introduces a dedicated transcription module that converts captured audio into structured transcripts that can flow directly into multimodal fusion, QA, and scoring pipelines. This document describes the architecture, data flow, and privacy controls for the upcoming implementation.

## Goals

1. **High-fidelity transcription** with timestamps, speaker tags, and confidence metrics per word/segment.
2. **Resilient ingestion** that supports multiple speech-to-text providers (cloud + offline) with automatic fallback.
3. **Traceability** into Abilities sessions: every transcript maps to `session_id`, `prompt_id`, and learner metadata reused in Stories 2.1–2.3.
4. **QA hooks** that let reviewers inspect, edit, and replay transcripts before they reach scoring/fusion.
5. **Privacy-first storage** so that encrypted audio and transcripts can be purged or redacted on demand.

## High-Level Components

| Component | Responsibility |
| --- | --- |
| `SpeechToTextPipeline` | Orchestrates provider selection, batching, metadata enrichment, and persistence. |
| `TranscriptionProvider` (abstract) | Defines the contract for provider plug-ins (e.g., Whisper, DeepSpeech, offline RNN). |
| `TranscriptRepository` | Handles encrypted storage + retrieval of transcript artifacts alongside audio hashes from `AudioProcessor`. |
| `QAReviewHooks` | Provides callbacks/queues for QA workflows to register transcripts for manual verification before fusion. |
| `FallbackOrchestrator` | Applies heuristics for low-bandwidth/offline scenarios (e.g., downgrade model, queue for later sync). |
| `TelemetryRecorder` | Emits reliability and confidence signals to `FusionDiagnostics` and other monitoring surfaces. |

### Data Flow

1. **Audio Capture**
   - Voice recording interface uploads audio to `AudioProcessor`, which emits a pipeline trigger and stores encrypted blobs.
   - Trigger metadata includes `session_id`, `prompt_id`, `learner_id`, device/noise stats, and `audio_hash`.
2. **Transcription Intake**
   - `SpeechToTextPipeline.enqueue_job` receives the trigger metadata plus a storage pointer to the audio blob.
   - The pipeline normalizes metadata and looks up any prior transcript attempts for deduplication.
3. **Provider Execution**
   - Provider selection is driven by policy (preferred model, locale, bandwidth, privacy).  The base provider contract expects streaming and batch modes.
   - Providers return `TranscriptPackage` objects: segments with start/end timestamps, speaker labels, word-level confidences, noise level, and reliability signals.
4. **Persistence + Enrichment**
   - Pipeline stamps Abilities session metadata, calculates aggregate confidence (mean/min), and records fallback decisions.
   - `TranscriptRepository` stores both the structured transcript JSON and a diff-friendly text version for QA.
5. **QA + Review**
   - QA hooks push transcripts into `audio.qa_manager.QAManager` with links to playback tokens and editing endpoints.
   - QA status feeds back into transcript metadata so downstream consumers know whether manual review is required.
6. **Downstream Consumption**
   - Once approved (or auto-approved per policy), transcripts are emitted to the multimodal fusion preprocessor via `FusionAPI.add_modality_data()` with modality=`"text_from_audio"`.
   - Telemetry (confidence, noise) flows into `FusionDiagnostics` for alerting.

### Metadata Contract

```json
{
  "session_id": "uuid",
  "prompt_id": "quiz_prompt_42",
  "learner_id": "uuid",
  "language": "en-US",
  "segments": [
    {
      "segment_id": "seg_1",
      "speaker": "learner",
      "start": 0.00,
      "end": 7.42,
      "text": "I like working with robotics...",
      "confidence": 0.94,
      "words": [
        {"text": "I", "start": 0.00, "end": 0.12, "confidence": 0.99},
        {"text": "like", "start": 0.12, "end": 0.38, "confidence": 0.97}
      ],
      "noise_level": 0.12,
      "flags": []
    }
  ],
  "aggregate_confidence": 0.91,
  "provider": {
    "name": "whisper-large-v3",
    "mode": "cloud",
    "latency_ms": 1830,
    "fallback_used": false
  },
  "qa_status": "pending_review",
  "created_at": "2026-02-24T11:10:00Z"
}
```

### Fallback Strategy Overview

1. **Primary provider**: Cloud model tuned per locale (Whisper/Deepgram/etc.).
2. **Degraded provider**: Low-bandwidth streaming mode with lower sampling rate and chunked uploads.
3. **Offline provider**: On-device RNN/keyword engine used when network unreachable; stores encrypted deltas for later reconcile.
4. **Manual fallback**: QA queue receives audio for human transcription if automated confidence < threshold.

Fallback decisions must be captured in the transcript metadata: `fallback_used`, `fallback_reason`, and `retry_policy`.

### Privacy + Compliance

- **Encryption**: Reuse the `AudioProcessor` encryption helper for transcripts; wrap repository accesses with audit logging.
- **Retention**: Provide `TranscriptRepository.purge_session(session_id)` so privacy officers can delete both audio and transcription artifacts in tandem.
- **PII Handling**: No transcripts leave protected storage without redaction; QA tools operate on redacted view unless elevated permissions are granted.

## Next Steps

1. Implement scaffolding classes in `speech_to_text` module (pipeline orchestration, provider interfaces, repositories).
2. Connect pipeline triggers from `AudioProcessor._trigger_pipelines` to the new queue/dispatcher.
3. Add contract tests that validate the transcript metadata schema and fallback selection logic.
4. Integrate QA hooks so that transcripts appear in the existing QA dashboard with review statuses.
5. Document streaming/offline behaviors and expose admin toggles for preferred providers per locale.
