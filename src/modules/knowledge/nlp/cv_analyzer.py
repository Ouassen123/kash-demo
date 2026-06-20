"""CV Analysis NLP pipeline for knowledge extraction."""

import re
import spacy
import nltk
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

from src.core.logging import get_logger
from src.core.config import settings
from sqlalchemy.orm import Session
from src.models.assessment import UserAssessment, KnowledgeAssessment
from .confidence_scorer import ConfidenceScorer
from .taxonomy_mapper import TaxonomyMapper

logger = get_logger(__name__)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except OSError:
    logger.warning("spaCy model not found. Falling back to lightweight blank English tokenizer")
    SPACY_AVAILABLE = True
    nlp = spacy.blank("en")
    if "sentencizer" not in nlp.pipe_names:
        nlp.add_pipe("sentencizer")

# Verify NLTK data is available
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    logger.error("NLTK data not found. Run: python scripts/setup_nlp_models.py")
    raise ImportError("NLTK data not available. Run setup script first.")


@dataclass
class TextExtractionResult:
    """Result of text extraction and preprocessing."""
    cleaned_text: str
    language_detected: str
    sentences: List[str]
    word_count: int
    line_count: int


@dataclass
class ExtractedItem:
    """Base class for extracted CV items."""
    name: str
    confidence: float
    context: str
    position: str
    source_text: str


@dataclass
class SkillItem(ExtractedItem):
    """Extracted skill information."""
    skill_type: Optional[str] = None
    proficiency_level: Optional[str] = None
    years_experience: Optional[float] = None


@dataclass
class EducationItem(ExtractedItem):
    """Extracted education information."""
    degree: str
    institution: str
    dates: Optional[str] = None
    gpa: Optional[str] = None
    field_of_study: Optional[str] = None


@dataclass
class ExperienceItem(ExtractedItem):
    """Extracted work experience information."""
    title: str
    company: str
    dates: Optional[str] = None
    description: Optional[str] = None
    achievements: List[str] = None
    
    def __post_init__(self):
        if self.achievements is None:
            self.achievements = []


@dataclass
class CertificationItem(ExtractedItem):
    """Extracted certification information."""
    issuer: Optional[str] = None
    date: Optional[str] = None
    credential_id: Optional[str] = None
    expiry_date: Optional[str] = None


class CVAnalyzer:
    """Main CV analysis engine using NLP techniques."""
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize the CV analyzer.
        
        Args:
            db: Database session for persistence (optional)
        """
        self.db = db
        self.confidence_scorer = ConfidenceScorer()
        self.taxonomy_mapper = TaxonomyMapper()
        
        # Load patterns and rules
        self._load_extraction_patterns()
    
    def _load_extraction_patterns(self):
        """Load and pre-compile regex patterns for CV section extraction."""
        # Pre-compile section patterns for better performance
        self.section_patterns = {
            'education': [
                re.compile(r'EDUCATION\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'ACADEMIC\s+BACKGROUND\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'QUALIFICATIONS\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'FORMATION\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'ÉDUCATION\s*:?\s*', re.IGNORECASE | re.MULTILINE)
            ],
            'experience': [
                re.compile(r'EXPERIENCE\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'WORK\s+HISTORY\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'PROFESSIONAL\s+EXPERIENCE\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'EMPLOYMENT\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'EXPÉRIENCE\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'EXPÉRIENCE\s+PROFESSIONNELLE\s*:?\s*', re.IGNORECASE | re.MULTILINE)
            ],
            'skills': [
                re.compile(r'SKILLS\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'TECHNICAL\s+SKILLS\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'COMPETENCES\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'COMPÉTENCES\s+TECHNIQUES\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'PROGRAMMING\s+LANGUAGES\s*:?\s*', re.IGNORECASE | re.MULTILINE)
            ],
            'certifications': [
                re.compile(r'CERTIFICATIONS\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'CERTIFICATES\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'LICENSES\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'CERTIFICATION\s*:?\s*', re.IGNORECASE | re.MULTILINE),
                re.compile(r'AGRÉMENT\s*:?\s*', re.IGNORECASE | re.MULTILINE)
            ]
        }
        
        # Pre-compile skill patterns
        self.skill_patterns = [
            re.compile(r'\b(Python|JavaScript|Java|C\+\+|React|Angular|Vue\.js|Node\.js|Django|Flask|FastAPI|Spring|\.NET|PHP|Ruby|Go|Rust|Swift|Kotlin|Scala)\b', re.IGNORECASE),
            re.compile(r'\b(SQL|PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|Cassandra|DynamoDB|Firebase)\b', re.IGNORECASE),
            re.compile(r'\b(AWS|Azure|GCP|Google\s+Cloud|Heroku|DigitalOcean|Vercel|Netlify)\b', re.IGNORECASE),
            re.compile(r'\b(Docker|Kubernetes|Jenkins|GitLab|GitHub|CircleCI|TravisCI)\b', re.IGNORECASE),
            re.compile(r'\b(Agile|Scrum|Kanban|DevOps|CI/CD|TDD|BDD)\b', re.IGNORECASE)
        ]
        
        # Pre-compile education patterns
        self.education_patterns = [
            re.compile(r'(Bachelor|Master|PhD|Doctorate|B\.S\.|M\.S\.|Ph\.D\.|B\.Sc\.|M\.Sc\.|Licence|Master|Doctorat)\s+(?:of\s+)?(?:Science|Arts|Engineering|Computer\s+Science|Information\s+Technology)', re.IGNORECASE),
            re.compile(r'(University|College|Institute|École|Université)\s+(?:of\s+)?[A-Za-z\s]+', re.IGNORECASE),
            re.compile(r'(?:GPA|Grade\s+Point\s+Average):\s*[\d\.]+', re.IGNORECASE),
            re.compile(r'\d{4}\s*[-–]\s*\d{4}', re.IGNORECASE)  # Date ranges
        ]
    
    def extract_text(self, cv_text: str) -> TextExtractionResult:
        """
        Extract and preprocess CV text.
        
        Args:
            cv_text: Raw CV text content
            
        Returns:
            TextExtractionResult with processed text and metadata
        """
        if not cv_text or len(cv_text.strip()) < 100:
            raise ValueError("CV text must be at least 100 characters long")
        
        # Clean text
        cleaned_text = self._clean_text(cv_text)
        
        # Detect language
        language = self._detect_language(cleaned_text)
        
        # Segment sentences
        sentences = self._segment_sentences(cleaned_text, language)
        
        # Calculate statistics
        word_count = len(cleaned_text.split())
        line_count = len(cleaned_text.split('\n'))
        
        return TextExtractionResult(
            cleaned_text=cleaned_text,
            language_detected=language,
            sentences=sentences,
            word_count=word_count,
            line_count=line_count
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\-\.\,\!\?\:\;\(\)\[\]/\n]', ' ', text)
        
        # Normalize line breaks
        text = re.sub(r'\r\n|\r', '\n', text)
        
        return text.strip()
    
    def _detect_language(self, text: str) -> str:
        """Detect document language."""
        # Simple language detection based on common words
        french_indicators = [
            'et', 'le', 'la', 'les', 'des', 'dans', 'pour', 'avec', 'par', 'sur',
            'université', 'diplôme', 'je', 'suis', 'ingénieur', 'ingenieur', 'logiciel',
            'expérience'
        ]
        spanish_indicators = [
            'y', 'el', 'la', 'las', 'los', 'en', 'para', 'con', 'por', 'sobre',
            'universidad', 'soy', 'ingeniero', 'experiencia'
        ]
        
        text_lower = text.lower()

        def count_occurrences(words):
            total = 0
            for word in words:
                pattern = rf'\b{re.escape(word)}\b'
                total += len(re.findall(pattern, text_lower))
            return total

        french_count = count_occurrences(french_indicators)
        spanish_count = count_occurrences(spanish_indicators)
        
        if french_count >= 3:
            return 'fr'
        elif spanish_count >= 3:
            return 'es'
        else:
            return 'en'
    
    def _segment_sentences(self, text: str, language: str) -> List[str]:
        """Segment text into sentences."""
        if SPACY_AVAILABLE and language == 'en':
            doc = nlp(text)
            return [sent.text.strip() for sent in doc.sents]
        else:
            # Fallback to NLTK
            try:
                sentences = nltk.sent_tokenize(text)
                return [sent.strip() for sent in sentences if sent.strip()]
            except:
                # Simple fallback
                return [line.strip() for line in text.split('\n') if line.strip()]
    
    def extract_skills(self, cv_text: str) -> Dict[str, List[SkillItem]]:
        """Extract skills from CV text."""
        skills = []
        
        # Find skills section
        skills_section = self._extract_section(cv_text, 'skills')
        
        if skills_section:
            # Extract skills using patterns
            for pattern in self.skill_patterns:
                matches = pattern.finditer(skills_section)
                for match in matches:
                    skill_name = match.group(1) if match.groups() else match.group(0)
                    
                    # Calculate confidence
                    skill_data = {
                        'name': skill_name,
                        'context': match.group(0),
                        'position': 'skills_section',
                        'explicit_mention': True
                    }
                    confidence = self.confidence_scorer.calculate_skill_confidence(skill_data)
                    
                    skill_item = SkillItem(
                        name=skill_name,
                        confidence=confidence,
                        context=match.group(0),
                        position='skills_section',
                        source_text=skills_section
                    )
                    skills.append(skill_item)
        
        # Also look for skills in experience section
        experience_section = self._extract_section(cv_text, 'experience')
        if experience_section:
            for pattern in self.skill_patterns:
                matches = pattern.finditer(experience_section)
                for match in matches:
                    skill_name = match.group(1) if match.groups() else match.group(0)
                    
                    # Check if already found
                    if not any(skill.name.lower() == skill_name.lower() for skill in skills):
                        skill_data = {
                            'name': skill_name,
                            'context': match.group(0),
                            'position': 'experience_description',
                            'explicit_mention': False
                        }
                        confidence = self.confidence_scorer.calculate_skill_confidence(skill_data)
                        
                        skill_item = SkillItem(
                            name=skill_name,
                            confidence=confidence,
                            context=match.group(0),
                            position='experience_description',
                            source_text=experience_section
                        )
                        skills.append(skill_item)
        
        return {'skills': skills}
    
    def extract_education(self, cv_text: str) -> Dict[str, List[EducationItem]]:
        """Extract education information."""
        education = []
        
        education_section = self._extract_section(cv_text, 'education')
        
        if education_section:
            # Extract degree information
            degree_pattern = r'(Bachelor|Master|PhD|Doctorate|B\.S\.|M\.S\.|Ph\.D\.|B\.Sc\.|M\.Sc\.|Licence|Master|Doctorat)[^,\n]*'
            institution_pattern = r'([A-Za-z\s]*?(?:University|College|Institute|École|Université)[^,\n]*)'
            gpa_pattern = r'(?:GPA|Grade\s+Point\s+Average):\s*([\d\.]+)'
            date_pattern = r'\d{4}\s*[-–]\s*\d{4}'
            
            # Find education entries
            lines = education_section.split('\n')
            current_education = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_education:
                        # Create education item
                        confidence = self.confidence_scorer.calculate_education_confidence(current_education)
                        education_item = EducationItem(
                            name=current_education.get('degree', 'Unknown Degree'),
                            confidence=confidence,
                            context=education_section,
                            position='education_section',
                            source_text=line,
                            degree=current_education.get('degree', ''),
                            institution=current_education.get('institution', ''),
                            dates=current_education.get('dates'),
                            gpa=current_education.get('gpa'),
                            field_of_study=current_education.get('field_of_study')
                        )
                        education.append(education_item)
                        current_education = {}
                    continue
                
                # Extract degree
                degree_match = re.search(degree_pattern, line, re.IGNORECASE)
                if degree_match:
                    current_education['degree'] = degree_match.group(0)
                
                # Extract institution
                inst_match = re.search(institution_pattern, line, re.IGNORECASE)
                if inst_match:
                    current_education['institution'] = inst_match.group(0)
                
                # Extract GPA
                gpa_match = re.search(gpa_pattern, line, re.IGNORECASE)
                if gpa_match:
                    current_education['gpa'] = gpa_match.group(1)
                
                # Extract dates
                date_match = re.search(date_pattern, line)
                if date_match:
                    current_education['dates'] = date_match.group(0)
            
            # Handle last education entry
            if current_education:
                confidence = self.confidence_scorer.calculate_education_confidence(current_education)
                education_item = EducationItem(
                    name=current_education.get('degree', 'Unknown Degree'),
                    confidence=confidence,
                    context=education_section,
                    position='education_section',
                    source_text=education_section,
                    degree=current_education.get('degree', ''),
                    institution=current_education.get('institution', ''),
                    dates=current_education.get('dates'),
                    gpa=current_education.get('gpa'),
                    field_of_study=current_education.get('field_of_study')
                )
                education.append(education_item)
        
        return {'education': education}
    
    def extract_experience(self, cv_text: str) -> Dict[str, List[ExperienceItem]]:
        """Extract work experience information."""
        experience = []
        
        experience_section = self._extract_section(cv_text, 'experience')
        
        if experience_section:
            # Pattern for company and title
            position_pattern = r'([A-Za-z\s]+(?:Engineer|Developer|Manager|Director|Analyst|Consultant|Specialist|Architect|Lead|Senior|Junior))\s+(?:at|@)\s+([A-Za-z\s]+)'
            date_pattern = r'\((\d{4}\s*[-–]\s*(?:Present|\d{4}|Current))\)'
            
            lines = experience_section.split('\n')
            current_experience = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_experience:
                        # Create experience item
                        confidence = self.confidence_scorer.calculate_experience_confidence(current_experience)
                        experience_item = ExperienceItem(
                            name=current_experience.get('title', 'Unknown Position'),
                            confidence=confidence,
                            context=experience_section,
                            position='experience_section',
                            source_text=line,
                            title=current_experience.get('title', ''),
                            company=current_experience.get('company', ''),
                            dates=current_experience.get('dates'),
                            description=current_experience.get('description'),
                            achievements=current_experience.get('achievements', [])
                        )
                        experience.append(experience_item)
                        current_experience = {}
                    continue
                
                # Extract position and company
                pos_match = re.search(position_pattern, line, re.IGNORECASE)
                if pos_match:
                    current_experience['title'] = pos_match.group(1).strip()
                    current_experience['company'] = pos_match.group(2).strip()
                
                # Extract dates
                date_match = re.search(date_pattern, line)
                if date_match:
                    current_experience['dates'] = date_match.group(1)
                
                # Look for achievements (bulleted points)
                if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    if 'achievements' not in current_experience:
                        current_experience['achievements'] = []
                    current_experience['achievements'].append(line.lstrip('-•* ').strip())
                elif current_experience and 'description' not in current_experience:
                    current_experience['description'] = line
            
            # Handle last experience entry
            if current_experience:
                confidence = self.confidence_scorer.calculate_experience_confidence(current_experience)
                experience_item = ExperienceItem(
                    name=current_experience.get('title', 'Unknown Position'),
                    confidence=confidence,
                    context=experience_section,
                    position='experience_section',
                    source_text=experience_section,
                    title=current_experience.get('title', ''),
                    company=current_experience.get('company', ''),
                    dates=current_experience.get('dates'),
                    description=current_experience.get('description'),
                    achievements=current_experience.get('achievements', [])
                )
                experience.append(experience_item)
        
        return {'experience': experience}
    
    def extract_certifications(self, cv_text: str) -> Dict[str, List[CertificationItem]]:
        """Extract certification information."""
        certifications = []
        
        cert_section = self._extract_section(cv_text, 'certifications')
        
        if cert_section:
            # Pattern for certifications
            cert_pattern = r'([A-Za-z\s]+(?:Certified|Certificate|Certification)[^,\n]*)'
            issuer_pattern = r'(AWS|Google|Microsoft|Oracle|Cisco|IBM|Amazon|Azure)'
            date_pattern = r'\((\d{4})\)'
            
            lines = cert_section.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Extract certification name
                cert_match = re.search(cert_pattern, line, re.IGNORECASE)
                if cert_match:
                    cert_name = cert_match.group(1).strip()
                    
                    # Extract issuer
                    issuer = None
                    issuer_match = re.search(issuer_pattern, line, re.IGNORECASE)
                    if issuer_match:
                        issuer = issuer_match.group(1)
                    
                    # Extract date
                    date = None
                    date_match = re.search(date_pattern, line)
                    if date_match:
                        date = date_match.group(1)
                    
                    # Calculate confidence
                    cert_data = {
                        'name': cert_name,
                        'issuer': issuer,
                        'date': date,
                        'section_type': 'certification'
                    }
                    confidence = self.confidence_scorer.calculate_certification_confidence(cert_data)
                    
                    cert_item = CertificationItem(
                        name=cert_name,
                        confidence=confidence,
                        context=line,
                        position='certification_section',
                        source_text=cert_section,
                        issuer=issuer,
                        date=date
                    )
                    certifications.append(cert_item)
        
        return {'certifications': certifications}
    
    def _extract_section(self, cv_text: str, section_type: str) -> Optional[str]:
        """Extract a specific section from CV text."""
        patterns = self.section_patterns.get(section_type, [])
        
        for pattern in patterns:
            # Patterns are precompiled with necessary flags
            match = pattern.search(cv_text)
            if match:
                start_pos = match.end()
                
                # Find next section header
                remaining_text = cv_text[start_pos:]
                next_section_match = None
                
                for other_patterns in self.section_patterns.values():
                    if other_patterns == patterns:
                        continue
                    for other_pattern in other_patterns:
                        other_match = other_pattern.search(remaining_text)
                        if other_match and (next_section_match is None or other_match.start() < next_section_match.start()):
                            next_section_match = other_match
                
                if next_section_match:
                    section_text = remaining_text[:next_section_match.start()].strip()
                else:
                    section_text = remaining_text.strip()
                
                return section_text
        
        return None
    
    def analyze_cv(self, cv_text: str, user_id: Optional[str] = None, persist: bool = True) -> Dict[str, Any]:
        """
        Perform complete CV analysis with optional persistence.
        
        Args:
            cv_text: Raw CV text content
            user_id: User ID for persistence (optional)
            persist: Whether to persist results to database (default: True)
            
        Returns:
            Complete analysis results with all sections
        """
        # Validate input
        self._validate_cv_input(cv_text)

        # Extract all sections and metadata
        sections = self._extract_all_sections(cv_text)
        text_result = self.extract_text(cv_text)

        # Calculate confidence and build response
        overall_confidence = self._calculate_overall_confidence(sections)
        result = self._build_analysis_result(sections, text_result)
        result['metadata']['overall_confidence'] = overall_confidence

        # Persist if requested
        if persist and self.db and user_id:
            self._persist_analysis_result(result, user_id, cv_text)

        return result

    def _validate_cv_input(self, cv_text: str) -> None:
        """Validate CV text input before processing."""
        if not cv_text or len(cv_text.strip()) < 100:
            raise ValueError("CV text must be at least 100 characters long")

        if len(cv_text) > 50000:
            raise ValueError("CV text too long (max 50,000 characters)")

    def _extract_all_sections(self, cv_text: str) -> Dict[str, List[ExtractedItem]]:
        """Extract all sections from CV and return structured lists."""
        skills = self.extract_skills(cv_text).get('skills', [])
        education = self.extract_education(cv_text).get('education', [])
        experience = self.extract_experience(cv_text).get('experience', [])
        certifications = self.extract_certifications(cv_text).get('certifications', [])

        return {
            'skills': skills,
            'education': education,
            'experience': experience,
            'certifications': certifications
        }

    def _calculate_overall_confidence(self, sections: Dict[str, List[ExtractedItem]]) -> float:
        """Calculate overall confidence using extracted sections."""
        payload = {
            'skills': [self._item_to_dict(item) for item in sections.get('skills', [])],
            'education': [self._item_to_dict(item) for item in sections.get('education', [])],
            'experience': [self._item_to_dict(item) for item in sections.get('experience', [])],
            'certifications': [self._item_to_dict(item) for item in sections.get('certifications', [])]
        }
        return self.confidence_scorer.calculate_overall_confidence(payload)

    def _build_analysis_result(self, sections: Dict[str, Any], text_result: TextExtractionResult) -> Dict[str, Any]:
        """Build the final analysis result dictionary."""
        return {
            'skills': [self._item_to_dict(item) for item in sections.get('skills', [])],
            'education': [self._item_to_dict(item) for item in sections.get('education', [])],
            'experience': [self._item_to_dict(item) for item in sections.get('experience', [])],
            'certifications': [self._item_to_dict(item) for item in sections.get('certifications', [])],
            'metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'language_detected': text_result.language_detected,
                'total_sections_found': len([s for s in [sections.get('skills'), sections.get('education'), sections.get('experience'), sections.get('certifications')] if s]),
                'word_count': text_result.word_count,
                'line_count': text_result.line_count,
                'overall_confidence': self._calculate_overall_confidence(sections)
            }
        }
    
    def _item_to_dict(self, item: ExtractedItem) -> Dict[str, Any]:
        """Convert dataclass item to dictionary."""
        if hasattr(item, '__dict__'):
            return {k: v for k, v in item.__dict__.items() if not k.startswith('_')}
        return {}


    def _persist_analysis_result(self, result: Dict[str, Any], user_id: str, cv_text: str):
        """Persist analysis results to database.
        
        Args:
            result: Analysis results dictionary
            user_id: User ID
            cv_text: Original CV text
        """
        try:
            # Create UserAssessment record
            user_assessment = UserAssessment(
                user_id=user_id,
                assessment_type='knowledge',
                assessment_name='CV Analysis',
                assessment_version='1.0',
                status='completed',
                normalized_score=result['metadata']['overall_confidence'] * 100,  # Convert to 0-100 scale
                confidence_score=result['metadata']['overall_confidence'],
                input_data={'cv_text': cv_text},
                result_data=result,
                assessment_metadata={
                    'analysis_engine': 'nlp_cv_analyzer_v1',
                    'language': result['metadata']['language_detected'],
                    'word_count': result['metadata']['word_count']
                }
            )
            
            self.db.add(user_assessment)
            self.db.flush()  # Get the ID
            
            # Create KnowledgeAssessment record
            knowledge_assessment = KnowledgeAssessment(
                assessment_id=user_assessment.id,
                cv_text=cv_text,
                cv_parsed_data=result
            )
            
            self.db.add(knowledge_assessment)
            self.db.commit()
            
            logger.info(f"CV analysis persisted for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to persist CV analysis: {e}")
            self.db.rollback()
            raise
