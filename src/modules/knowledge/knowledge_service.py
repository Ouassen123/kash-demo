"""Knowledge module service for CV analysis and ESCO/O*NET enrichment."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import re
import math

from src.core.logging import get_logger
from src.models.assessment import UserAssessment, KnowledgeAssessment
from src.modules.knowledge.nlp.cv_analyzer import CVAnalyzer
from src.modules.knowledge.taxonomy.enrichment_service import EnrichmentService

# ---------------------------------------------------------------------------
# TF-IDF + KNN helpers (aligned with user's Ranking Model pipeline)
# ---------------------------------------------------------------------------

# Reference corpus: representative job-market skill terms
_REFERENCE_DOCS = [
    "python machine learning data science pandas numpy scikit tensorflow pytorch deep learning",
    "javascript react node typescript frontend backend web development api",
    "java spring boot microservices kubernetes docker devops ci cd",
    "sql postgresql mysql database design etl data engineering",
    "project management agile scrum leadership communication team",
    "c++ embedded systems linux systems programming algorithms",
    "cloud aws azure gcp infrastructure networking security",
    "research analysis statistics phd academic publication writing",
]

def _preprocess(text: str) -> List[str]:
    """Data cleaning + NLTK-style tokenization + stopword removal + stemming."""
    import string
    STOPWORDS = {
        'a','an','the','and','or','but','in','on','at','to','for','of','with',
        'is','are','was','were','be','been','being','have','has','had','do',
        'does','did','will','would','could','should','may','might','i','my',
        'we','our','you','your','he','she','it','they','their','this','that',
        'from','by','as','into','about','through','during','before','after',
    }
    # Remove special chars & numbers
    text = re.sub(r'[^a-zA-Z\s]', ' ', text.lower())
    tokens = text.split()
    # Remove stopwords and single chars
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    # Simple Porter-like suffix stripping (stemming)
    stemmed = []
    for t in tokens:
        for suffix in ('ing', 'tion', 'ness', 'ment', 'ed', 'er', 'ly', 'al', 'ic'):
            if t.endswith(suffix) and len(t) - len(suffix) >= 3:
                t = t[:-len(suffix)]
                break
        stemmed.append(t)
    return stemmed


def _build_tfidf(docs: List[List[str]]) -> List[Dict[str, float]]:
    """Compute TF-IDF vectors for a list of tokenised documents."""
    N = len(docs)
    # Document frequency
    df: Dict[str, int] = {}
    for tokens in docs:
        for t in set(tokens):
            df[t] = df.get(t, 0) + 1

    vectors = []
    for tokens in docs:
        tf: Dict[str, float] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        total = max(len(tokens), 1)
        vec: Dict[str, float] = {}
        for t, count in tf.items():
            idf = math.log((N + 1) / (df.get(t, 0) + 1)) + 1  # smoothed
            vec[t] = (count / total) * idf
        vectors.append(vec)
    return vectors


def _cosine_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    """Cosine similarity between two TF-IDF vectors."""
    common = set(v1) & set(v2)
    dot = sum(v1[t] * v2[t] for t in common)
    mag1 = math.sqrt(sum(x ** 2 for x in v1.values()))
    mag2 = math.sqrt(sum(x ** 2 for x in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def compute_tfidf_knn_score(cv_text: str, k: int = 3) -> float:
    """
    Compute KNN document similarity score using TF-IDF.
    Pipeline: Clean → Tokenize → Stem → TF-IDF → cosine KNN → score (0-1).
    """
    cv_tokens = _preprocess(cv_text)
    ref_tokens = [_preprocess(d) for d in _REFERENCE_DOCS]

    all_docs = ref_tokens + [cv_tokens]
    vectors = _build_tfidf(all_docs)
    cv_vec = vectors[-1]
    ref_vecs = vectors[:-1]

    similarities = sorted(
        [_cosine_similarity(cv_vec, rv) for rv in ref_vecs],
        reverse=True
    )
    top_k = similarities[:k]
    return sum(top_k) / k if top_k else 0.0

logger = get_logger(__name__)


class KnowledgeService:
    """Service for knowledge domain operations including CV analysis and ESCO mapping."""
    
    def __init__(
        self,
        db: Session,
        cv_analyzer: Optional[CVAnalyzer] = None,
        enrichment_service: Optional[EnrichmentService] = None,
    ):
        """Initialize the KnowledgeService.

        Args:
            db: Database session.
            cv_analyzer: Optional CVAnalyzer override (useful for testing).
            enrichment_service: Optional enrichment service override.
        """

        self.db = db
        self.cv_analyzer = cv_analyzer or CVAnalyzer(db=db)
        self.enrichment_service = enrichment_service or EnrichmentService()
    
    async def analyze_cv(self, user_id: str, cv_text: str, cv_filename: str = "unknown") -> UserAssessment:
        """
        Analyze CV text and create knowledge assessment.
        
        Args:
            user_id: User UUID
            cv_text: Raw CV text content
            cv_filename: Original filename
            
        Returns:
            UserAssessment with complete analysis results
        """
        logger.info(f"Starting CV analysis for user {user_id}")
        start_time = datetime.now()
        
        try:
            # Run NLP analysis (no persistence here)
            cv_analysis = self.cv_analyzer.analyze_cv(cv_text, user_id=user_id, persist=False)
            
            # Enrich with taxonomy data
            enriched_analysis = await self.enrichment_service.enrich_cv_analysis(cv_analysis)
            taxonomy_summary = self._build_taxonomy_summary(enriched_analysis)
            
            # Calculate knowledge scores (TF-IDF/KNN pipeline)
            knowledge_scores = self._calculate_knowledge_scores(enriched_analysis, taxonomy_summary, cv_text=cv_text)
            
            # Create user assessment record
            assessment = UserAssessment(
                id=uuid.uuid4(),
                user_id=user_id,
                assessment_type='knowledge',
                assessment_name='CV Analysis',
                assessment_version='1.0',
                status='completed',
                raw_score=knowledge_scores['raw_score'],
                normalized_score=knowledge_scores['normalized_score'],
                confidence_score=knowledge_scores['confidence_score'],
                input_data={
                    'cv_filename': cv_filename,
                    'cv_text_length': len(cv_text),
                    'analysis_metadata': enriched_analysis.get('metadata', {})
                },
                result_data={
                    'cv_analysis': enriched_analysis,
                    'taxonomy_summary': taxonomy_summary,
                    'knowledge_scores': knowledge_scores
                },
                created_at=datetime.now(),
                started_at=datetime.now(),
                completed_at=datetime.now()
            )
            
            self.db.add(assessment)
            self.db.flush()  # Get the assessment ID
            
            # Create knowledge-specific assessment record
            knowledge_assessment = KnowledgeAssessment(
                id=uuid.uuid4(),
                assessment_id=assessment.id,
                cv_text=cv_text,
                cv_parsed_data=enriched_analysis,
                esco_skills=taxonomy_summary['skills'],
                esco_occupations=taxonomy_summary['occupations'],
                domain_scores=knowledge_scores['domain_breakdown'],
                skill_gaps=taxonomy_summary['skill_gaps'],
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                model_version='1.0'
            )
            
            self.db.add(knowledge_assessment)
            self.db.commit()
            
            logger.info(f"CV analysis completed for user {user_id} in {(datetime.now() - start_time).total_seconds():.2f}s")
            return assessment
            
        except Exception as e:
            logger.error(f"CV analysis failed for user {user_id}: {e}")
            self.db.rollback()
            raise
    
    async def get_knowledge_assessment(self, assessment_id: str, user_id: str) -> Optional[UserAssessment]:
        """
        Get knowledge assessment by ID for a specific user.
        
        Args:
            assessment_id: Assessment UUID
            user_id: User UUID
            
        Returns:
            UserAssessment or None if not found
        """
        assessment = self.db.query(UserAssessment).filter(
            UserAssessment.id == assessment_id,
            UserAssessment.user_id == user_id,
            UserAssessment.assessment_type == 'knowledge'
        ).first()
        
        if assessment:
            # Load related knowledge assessment
            knowledge_assessment = self.db.query(KnowledgeAssessment).filter(
                KnowledgeAssessment.assessment_id == assessment.id
            ).first()
            
            if knowledge_assessment:
                # Add detailed data to result
                assessment.result_data.update({
                    'knowledge_assessment': {
                        'esco_skills': knowledge_assessment.esco_skills,
                        'esco_occupations': knowledge_assessment.esco_occupations,
                        'domain_scores': knowledge_assessment.domain_scores,
                        'skill_gaps': knowledge_assessment.skill_gaps,
                        'processing_time_ms': knowledge_assessment.processing_time_ms
                    }
                })
        
        return assessment
    
    async def get_user_knowledge_assessments(self, user_id: str, limit: int = 10) -> List[UserAssessment]:
        """
        Get all knowledge assessments for a user.
        
        Args:
            user_id: User UUID
            limit: Maximum number of assessments to return
            
        Returns:
            List of UserAssessment records
        """
        assessments = self.db.query(UserAssessment).filter(
            UserAssessment.user_id == user_id,
            UserAssessment.assessment_type == 'knowledge'
        ).order_by(UserAssessment.created_at.desc()).limit(limit).all()
        
        return assessments
    
    async def update_knowledge_assessment(self, assessment_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[UserAssessment]:
        """
        Update knowledge assessment with new data.
        
        Args:
            assessment_id: Assessment UUID
            user_id: User UUID
            updates: Dictionary of fields to update
            
        Returns:
            Updated UserAssessment or None if not found
        """
        assessment = self.db.query(UserAssessment).filter(
            UserAssessment.id == assessment_id,
            UserAssessment.user_id == user_id,
            UserAssessment.assessment_type == 'knowledge'
        ).first()
        
        if not assessment:
            return None
        
        try:
            # Update allowed fields
            if 'result_data' in updates:
                assessment.result_data.update(updates['result_data'])
            
            if 'normalized_score' in updates:
                assessment.normalized_score = updates['normalized_score']
            
            if 'confidence_score' in updates:
                assessment.confidence_score = updates['confidence_score']
            
            assessment.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(assessment)
            
            logger.info(f"Updated knowledge assessment {assessment_id} for user {user_id}")
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to update knowledge assessment {assessment_id}: {e}")
            self.db.rollback()
            raise
    
    async def delete_knowledge_assessment(self, assessment_id: str, user_id: str) -> bool:
        """
        Delete knowledge assessment.
        
        Args:
            assessment_id: Assessment UUID
            user_id: User UUID
            
        Returns:
            True if deleted, False if not found
        """
        assessment = self.db.query(UserAssessment).filter(
            UserAssessment.id == assessment_id,
            UserAssessment.user_id == user_id,
            UserAssessment.assessment_type == 'knowledge'
        ).first()
        
        if not assessment:
            return False
        
        try:
            # Delete related knowledge assessment
            knowledge_assessment = self.db.query(KnowledgeAssessment).filter(
                KnowledgeAssessment.assessment_id == assessment.id
            ).first()
            
            if knowledge_assessment:
                self.db.delete(knowledge_assessment)
            
            # Delete main assessment
            self.db.delete(assessment)
            self.db.commit()
            
            logger.info(f"Deleted knowledge assessment {assessment_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete knowledge assessment {assessment_id}: {e}")
            self.db.rollback()
            raise
    
    def _calculate_knowledge_scores(self, enriched_analysis: Dict[str, Any], taxonomy_summary: Dict[str, Any], cv_text: str = '') -> Dict[str, Any]:
        """Calculate knowledge domain scores based on enriched analysis + TF-IDF/KNN."""

        metadata = enriched_analysis.get('metadata', {})
        parsing_confidence = metadata.get('overall_confidence', 0.5)

        skills = enriched_analysis.get('skills', [])
        experience = enriched_analysis.get('experience', [])
        education_entries = enriched_analysis.get('education', [])

        skill_score = self._calculate_section_score(skills, 'esco_confidence')
        occupation_score = self._calculate_section_score(experience, 'onet_confidence')
        experience_score = min(len(experience) / 5, 1.0)
        education_score = self._calculate_education_score(education_entries)

        # TF-IDF + KNN similarity score (Ranking Model pipeline)
        try:
            knn_score = compute_tfidf_knn_score(cv_text) if cv_text else 0.0
        except Exception:
            knn_score = 0.0

        # Weighted scoring: knn_score replaces occupation_matching weight
        raw_score = (
            parsing_confidence * 0.15 +
            skill_score * 0.25 +
            knn_score * 0.30 +          # TF-IDF/KNN similarity weight
            occupation_score * 0.15 +
            experience_score * 0.10 +
            education_score * 0.05
        )
        normalized_score = raw_score * 100

        taxonomy_quality = (skill_score + occupation_score) / 2 if (skill_score or occupation_score) else 0.0
        confidence_score = min(
            1.0,
            parsing_confidence * 0.3 + taxonomy_quality * 0.4 + knn_score * 0.3
        )

        domain_breakdown = {
            'parsing_quality': parsing_confidence * 100,
            'skill_matching': skill_score * 100,
            'tfidf_knn_similarity': knn_score * 100,    # TF-IDF/KNN score
            'occupation_matching': occupation_score * 100,
            'experience_level': experience_score * 100,
            'education_level': education_score * 100
        }

        return {
            'raw_score': raw_score,
            'normalized_score': normalized_score,
            'confidence_score': confidence_score,
            'domain_breakdown': domain_breakdown,
            'taxonomy_quality': taxonomy_quality,
            'knn_score': knn_score,
            'taxonomy_summary': taxonomy_summary
        }

    def _calculate_section_score(self, items: List[Dict[str, Any]], confidence_key: str) -> float:
        """Calculate a normalized section score based on taxonomy confidence."""
        if not items:
            return 0.0

        match_ratio = sum(1 for item in items if item.get(confidence_key, 0.0) > 0) / len(items)
        avg_confidence = sum(item.get(confidence_key, 0.0) for item in items) / len(items)
        return min(1.0, 0.5 * match_ratio + 0.5 * avg_confidence)

    def _calculate_education_score(self, education_entries: List[Dict[str, Any]]) -> float:
        """Evaluate education level based on highest degree."""
        if not education_entries:
            return 0.5

        score = 0.5
        for entry in education_entries:
            degree = entry.get('degree', '').lower()
            if any(keyword in degree for keyword in ['phd', 'doctorate']):
                score = max(score, 1.0)
            elif 'master' in degree:
                score = max(score, 0.85)
            elif 'bachelor' in degree:
                score = max(score, 0.7)
        return score

    def _build_taxonomy_summary(self, enriched_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of taxonomy enrichment results."""
        summary = {
            'skills': [],
            'occupations': [],
            'skill_gaps': []
        }

        for skill in enriched_analysis.get('skills', []):
            summary['skills'].append({
                'name': skill.get('name'),
                'uri': skill.get('esco_uri'),
                'label': skill.get('esco_label'),
                'confidence': skill.get('esco_confidence', 0.0),
                'language': skill.get('esco_language', 'en'),
                'source_confidence': skill.get('confidence', 0.0),
                'enriched_at': skill.get('enriched_at')
            })

        for exp in enriched_analysis.get('experience', []):
            summary['occupations'].append({
                'title': exp.get('title'),
                'company': exp.get('company'),
                'onet_code': exp.get('onet_code'),
                'onet_title': exp.get('onet_title'),
                'confidence': exp.get('onet_confidence', 0.0),
                'zone': exp.get('onet_zone'),
                'enriched_at': exp.get('enriched_at')
            })

        summary['skill_gaps'] = self._calculate_skill_gaps(enriched_analysis)
        return summary

    def _calculate_skill_gaps(self, enriched_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify missing taxonomy coverage to highlight skill gaps."""
        gaps = []

        missing_skills = [skill.get('name') for skill in enriched_analysis.get('skills', []) if not skill.get('esco_uri')]
        if missing_skills:
            gaps.append({
                'context': 'skills',
                'missing_items': missing_skills,
                'reason': 'taxonomy_match_not_found'
            })

        missing_roles = [exp.get('title') for exp in enriched_analysis.get('experience', []) if not exp.get('onet_code')]
        if missing_roles:
            gaps.append({
                'context': 'experience',
                'missing_items': missing_roles,
                'reason': 'taxonomy_match_not_found'
            })

        return gaps
