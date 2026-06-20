Technical Story: NLP CV Analysis Development Plan
Module: Knowledge Evaluation — NLP Analysis Engine
Developer: ML/NLP Engineer
Estimated Time: 3 days

Technical Requirements:
- Build a multi-format CV ingestion service that handles PDF, DOCX, TXT, and OCRed scans with language detection and sentence/paragraph segmentation.
- Normalize extracted text into the Knowledge Module schema so skills, education, certifications, and career highlights align with the shared taxonomy.
- Surface attribute-level confidence scores and ambiguity flags for downstream scoring so uncertain signals can be weighted appropriately.
- Persist structured analysis with source references in the Knowledge Module model and expose APIs that downstream scoring/quiz services can call directly.

Implementation Details:
- **Ingestion & Preprocessing**: Leverage PyPDF2/pdfplumber for PDFs, python-docx for Word documents, and Tesseract for scanned uploads. Feed raw text through langdetect and spaCy pipelines to clean, segment, and annotate sentences.
- **Entity & Pattern Extraction**: Use a spaCy pipeline with custom NER components to tag skills, education, certifications, projects, and organizations. Map outputs to the normalized taxonomy using rule-based parsers backed by ESCO/O*NET references.
- **Confidence & Ambiguity Layer**: After extraction, compute attribute confidence from model probabilities, attribute coverage, and ensemble agreement. Attach ambiguity metadata (e.g., overlapping spans, low probability) so reviewers and scoring can inspect uncertain facts.
- **Storage & APIs**: Store CVAnalysis records in the Knowledge Module tables (or JSONB schema) with source URIs and timestamps. Provide REST/GraphQL endpoints that return structured attributes plus confidence for scoring, quizzes, and analytics consumers.
- **Monitoring**: Emit telemetry for extraction coverage, confidence distribution, and format-specific errors so future accuracy drift can be tracked.

Acceptance Criteria:
- Given a batch of CVs, when the engine ingests them, then it outputs the normalized schema with skills, education, certifications, and experience highlights.
- Given an extracted attribute, when the pipeline finishes, then it includes confidence/ambiguity metadata so downstream scoring weights and human review can react.
- Given the analysis results, when the scoring or quiz services query the API, then they receive structured, schema-aligned payloads with source references and timestamps.

Testing Strategy:
- Unit tests: Validate each extractor (formatters, regexes, taxonomy mapper) and confidence calculator against curated CV fragments.
- Integration tests: End-to-end CV upload → extraction → normalization → storage pipeline using representative PDF/DOCX/TXT samples.
- Performance tests: Ensure average processing time stays under 30s per CV and scale with async worker pools.
- Monitoring & regression: Synthetic CV feeds should exercise ambiguity flags and confidence drift alerts so issues are caught before production.

Dependencies:
- spaCy (en_core_web_lg) and Transformers for language understanding and classification.
- PDF/DOCX/OCR libraries (PyPDF2/pdfplumber, python-docx, pytesseract) for multi-format ingestion.
- ESCO/O*NET taxonomy data plus the Knowledge Module database schema for normalization and persistence.
- Knowledge scoring, adaptive quiz, and analytics services that consume the resulting payloads.

Risks & Mitigations:
- **Low extraction accuracy on noisy CVs**: Combine rule-based heuristics with model ensembles and expose confidence thresholds so low-quality attributes can be filtered.
- **Schema drift between NLP output and scoring expectations**: Keep taxonomy files versioned with the extractor and establish a handshake with consumers through shared contracts.
- **Performance bottlenecks for large batches**: Process CVs asynchronously with worker queues and cache intermediate computations (e.g., taxonomy lookups).
