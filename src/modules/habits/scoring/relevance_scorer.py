"""Relevance scorer — semantic similarity + lemma overlap (spaCy baseline)."""

from __future__ import annotations

import math
from typing import List

from src.core.logging import get_logger

logger = get_logger(__name__)

# POS tags we consider "important" content words.
_CONTENT_POS = {"NOUN", "VERB", "ADJ"}


class RelevanceScorer:
    """Deterministic relevance scorer based on question/answer alignment.

    Score composition:
      - 60% Cosine similarity between the question and answer spaCy vectors
        (requires a model with word vectors, e.g. ``fr_core_news_md`` or
        ``en_core_web_md``).  Falls back to 0 if vectors are not available.
      - 40% Overlap ratio of important lemmas (NOUN, VERB, ADJ excluding
        stopwords) between the question and the answer.
    """

    def __init__(self, nlp):
        """Initialise the scorer with a loaded spaCy pipeline.

        Args:
            nlp: A ``spacy.language.Language`` instance with vectors loaded
                (``md`` or ``lg`` model recommended).
        """
        self.nlp = nlp

    # ── Public API ────────────────────────────────────────────

    def score(self, question_text: str, answer_text: str) -> float:
        """Compute the relevance score (0-100) for a single Q/A pair.

        Args:
            question_text: The interview question.
            answer_text: The candidate's answer.

        Returns:
            Float score in [0, 100].
        """
        if not question_text or not answer_text:
            return 0.0

        q_doc = self.nlp(question_text)
        a_doc = self.nlp(answer_text)

        sim_score = self._semantic_similarity(q_doc, a_doc)
        overlap_score = self._lemma_overlap(q_doc, a_doc)

        final = (sim_score * 0.6) + (overlap_score * 0.4)
        final = max(0.0, min(100.0, final))

        logger.debug(
            "RelevanceScorer: sim=%.1f overlap=%.1f final=%.1f",
            sim_score,
            overlap_score,
            final,
        )
        return final

    def score_answers(self, pairs: List[tuple]) -> float:
        """Compute the average relevance score across multiple Q/A pairs.

        Args:
            pairs: List of ``(question_text, answer_text)`` tuples.

        Returns:
            Average score in [0, 100].
        """
        if not pairs:
            return 0.0
        scores = [self.score(q, a) for q, a in pairs]
        return sum(scores) / len(scores)

    # ── Internal helpers ──────────────────────────────────────

    def _semantic_similarity(self, q_doc, a_doc) -> float:
        """Cosine similarity between spaCy document vectors (0-100 scale)."""
        # ``similarity`` returns a float in [-1, 1]; we clamp to [0, 1] then scale.
        if not q_doc.has_vector or not a_doc.has_vector:
            logger.debug("RelevanceScorer: no vectors available, similarity=0")
            return 0.0

        # Use max sentence-level similarity to avoid dilution from long answers.
        try:
            q_sents = list(q_doc.sents)
        except ValueError:
            q_sents = [q_doc]
        try:
            a_sents = list(a_doc.sents)
        except ValueError:
            a_sents = [a_doc]
        if not q_sents:
            q_sents = [q_doc]
        if not a_sents:
            a_sents = [a_doc]
        best = 0.0
        for q_sent in q_sents:
            if not q_sent.has_vector:
                continue
            for a_sent in a_sents:
                if not a_sent.has_vector:
                    continue
                s = q_sent.similarity(a_sent)
                if s > best:
                    best = s
        best = max(0.0, min(1.0, best))
        # Apply sqrt scaling: raw cosine similarity between short French sentences
        # tends to cluster in the 0.3-0.6 range.  sqrt maps 0.25→0.5, 0.36→0.6,
        # 0.49→0.7, giving better score distribution across the 0-100 range.
        scaled = math.sqrt(best)
        return scaled * 100.0

    def _lemma_overlap(self, q_doc, a_doc) -> float:
        """Overlap ratio of content-word lemmas between question and answer.

        Returns the Jaccard-like ratio: |intersection| / |question lemmas|,
        scaled to 0-100.  If the question has no content lemmas, returns 0.
        """
        q_lemmas = self._content_lemmas(q_doc)
        a_lemmas = self._content_lemmas(a_doc)

        if not q_lemmas:
            return 0.0

        # Bidirectional overlap: how many question lemmas appear in the answer
        # AND how many answer content lemmas relate to the question.
        # This rewards answers that address the question's key concepts.
        overlap = q_lemmas & a_lemmas
        q_coverage = len(overlap) / len(q_lemmas) if q_lemmas else 0.0
        # Also reward answers that use a rich vocabulary around the question topics.
        a_relevance = len(overlap) / len(a_lemmas) if a_lemmas else 0.0
        # Weighted blend: primarily question coverage, secondary answer relevance.
        ratio = (q_coverage * 0.7) + (a_relevance * 0.3)
        return min(1.0, ratio) * 100.0

    @staticmethod
    def _content_lemmas(doc) -> set:
        """Extract a set of lowercased content-word lemmas from a spaCy doc.

        Keeps only tokens whose POS is in ``_CONTENT_POS`` and that are not
        stopwords, punctuation, or spaces.
        """
        return {
            t.lemma_.lower()
            for t in doc
            if t.pos_ in _CONTENT_POS
            and not t.is_stop
            and not t.is_punct
            and not t.is_space
        }
