"""Clarity scorer — lexical richness + sentence structure (spaCy baseline)."""

from __future__ import annotations

from typing import List

from src.core.logging import get_logger

logger = get_logger(__name__)


class ClarityScorer:
    """Deterministic clarity scorer based on lexical richness and sentence structure.

    Score composition:
      - 50% Lexical richness: Type-Token Ratio (TTR) normalised against a 0.6 target.
      - 50% Sentence structure: proportion of sentences within the optimal length
        range of 12-28 words.
    """

    TARGET_TTR: float = 0.6
    OPT_MIN_WORDS: int = 12
    OPT_MAX_WORDS: int = 28

    def __init__(self, nlp):
        """Initialise the scorer with a loaded spaCy pipeline.

        Args:
            nlp: A ``spacy.language.Language`` instance (any medium/large model
                with ``tok2vec`` or ``tagger`` is sufficient — we only need tokens
                and sentence boundaries).
        """
        self.nlp = nlp

    # ── Public API ────────────────────────────────────────────

    def score(self, text: str) -> float:
        """Compute the clarity score (0-100) for a single text.

        Args:
            text: The candidate's answer text.

        Returns:
            Float score in [0, 100].
        """
        if not text or not text.strip():
            return 0.0

        doc = self.nlp(text)

        ttr_score = self._lexical_richness(doc)
        struct_score = self._sentence_structure(doc)

        final = (ttr_score * 0.5) + (struct_score * 0.5)
        final = max(0.0, min(100.0, final))

        logger.debug(
            "ClarityScorer: ttr=%.1f struct=%.1f final=%.1f",
            ttr_score,
            struct_score,
            final,
        )
        return final

    def score_answers(self, texts: List[str]) -> float:
        """Compute the average clarity score across multiple answers.

        Args:
            texts: List of answer texts.

        Returns:
            Average score in [0, 100].
        """
        if not texts:
            return 0.0
        scores = [self.score(t) for t in texts]
        return sum(scores) / len(scores)

    # ── Internal helpers ──────────────────────────────────────

    def _lexical_richness(self, doc) -> float:
        """Type-Token Ratio normalised against ``TARGET_TTR``.

        TTR = unique_tokens / total_tokens.
        The score is linearly mapped so that TTR == 0 → 0, TTR == target → 100,
        and capped at 100 for TTR above target.
        """
        tokens = [t for t in doc if not t.is_space and not t.is_punct]
        if not tokens:
            return 0.0

        unique_lemmas = {t.lemma_.lower() for t in tokens if not t.is_stop}
        total = len(tokens)
        ttr = len(unique_lemmas) / total if total else 0.0

        score = (ttr / self.TARGET_TTR) * 100.0 if self.TARGET_TTR > 0 else 0.0
        return max(0.0, min(100.0, score))

    def _sentence_structure(self, doc) -> float:
        """Proportion of sentences whose word count falls in the optimal range."""
        try:
            sentences = list(doc.sents)
        except ValueError:
            sentences = [doc]
        if not sentences:
            return 0.0

        optimal = 0
        for sent in sentences:
            word_count = sum(
                1 for t in sent if not t.is_space and not t.is_punct
            )
            if self.OPT_MIN_WORDS <= word_count <= self.OPT_MAX_WORDS:
                optimal += 1

        ratio = optimal / len(sentences)
        return ratio * 100.0
