"""CV parsing and NLP analysis for knowledge extraction."""

import re
import spacy
import nltk
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from src.core.logging import get_logger
from src.core.config import settings

logger = get_logger(__name__)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except OSError:
    logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
    SPACY_AVAILABLE = False
    nlp = None

# Download NLTK data if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


@dataclass
class CVSection:
    """Represents a section of a CV."""
    title: str
    content: str
    start_line: int
    end_line: int
    confidence: float = 1.0


@dataclass
class ExperienceEntry:
    """Work experience entry."""
    title: str
    company: str
    duration: str
    description: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skills: List[str] = None
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []


@dataclass
class EducationEntry:
    """Education entry."""
    degree: str
    institution: str
    duration: str
    description: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class SkillEntry:
    """Skill entry with confidence."""
    name: str
    category: str
    confidence: float
    context: str = ""


class CVParser:
    """Advanced CV parser using NLP techniques."""
    
    def __init__(self):
        self.section_patterns = {
            'experience': [
                r'(?i)(work\s+experience|employment|professional\s+experience|career)',
                r'(?i)(experience|work\s+history|job\s+history)'
            ],
            'education': [
                r'(?i)(education|academic|qualification|degree)',
                r'(?i)(academic\s+background|educational\s+background)'
            ],
            'skills': [
                r'(?i)(skills|technical\s+skills|competencies|abilities)',
                r'(?i)(key\s+skills|core\s+competencies|technical\s+abilities)'
            ],
            'projects': [
                r'(?i)(projects|portfolio|work\s+projects)',
                r'(?i)(personal\s+projects|project\s+experience)'
            ],
            'certifications': [
                r'(?i)(certifications|certificates|credentials)',
                r'(?i)(professional\s+certifications|licenses)'
            ],
            'languages': [
                r'(?i)(languages|language\s+proficiency)',
                r'(?i)(spoken\s+languages|language\s+skills)'
            ]
        }
        
        # Skill categories with keywords
        self.skill_categories = {
            'programming': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
                'react', 'angular', 'vue', 'nodejs', 'django', 'flask', 'spring', 'dotnet'
            ],
            'databases': [
                'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
                'oracle', 'sqlite', 'cassandra', 'dynamodb'
            ],
            'cloud': [
                'aws', 'azure', 'gcp', 'google cloud', 'terraform', 'kubernetes',
                'docker', 'serverless', 'microservices', 'devops'
            ],
            'tools': [
                'git', 'github', 'gitlab', 'jenkins', 'ci/cd', 'jira', 'confluence',
                'vs code', 'intellij', 'eclipse', 'postman', 'swagger'
            ],
            'methodologies': [
                'agile', 'scrum', 'kanban', 'waterfall', 'lean', 'tdd', 'bdd',
                'continuous integration', 'continuous deployment'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving',
                'critical thinking', 'creativity', 'adaptability', 'time management'
            ]
        }
        
        # Common degree keywords
        self.degree_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'associate', 'diploma',
            'certificate', 'b.s.', 'm.s.', 'b.a.', 'm.a.', 'b.eng', 'm.eng'
        ]
    
    def parse_cv(self, cv_text: str) -> Dict[str, Any]:
        """
        Parse CV text and extract structured information.
        
        Args:
            cv_text: Raw CV text
            
        Returns:
            Dictionary containing parsed CV data
        """
        logger.info("Starting CV parsing")
        start_time = datetime.now()
        
        try:
            # Clean and preprocess text
            cleaned_text = self._clean_text(cv_text)
            
            # Extract sections
            sections = self._extract_sections(cleaned_text)
            
            # Parse each section
            experience = self._parse_experience(sections.get('experience', ''))
            education = self._parse_education(sections.get('education', ''))
            skills = self._parse_skills(sections.get('skills', ''), cleaned_text)
            projects = self._parse_projects(sections.get('projects', ''))
            certifications = self._parse_certifications(sections.get('certifications', ''))
            languages = self._parse_languages(sections.get('languages', ''))
            
            # Extract contact information
            contact_info = self._extract_contact_info(cleaned_text)
            
            # Calculate overall metrics
            total_experience_years = self._calculate_total_experience(experience)
            skill_diversity = len(set(skill.name for skill in skills))
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                'contact_info': contact_info,
                'sections': sections,
                'experience': [self._experience_to_dict(exp) for exp in experience],
                'education': [self._education_to_dict(edu) for edu in education],
                'skills': [self._skill_to_dict(skill) for skill in skills],
                'projects': projects,
                'certifications': certifications,
                'languages': languages,
                'metrics': {
                    'total_experience_years': total_experience_years,
                    'skill_diversity': skill_diversity,
                    'processing_time_ms': processing_time
                },
                'parsing_metadata': {
                    'spacy_available': SPACY_AVAILABLE,
                    'sections_found': list(sections.keys()),
                    'confidence_score': self._calculate_confidence_score(sections, skills, experience)
                }
            }
            
            logger.info(f"CV parsing completed in {processing_time:.2f}ms")
            return result
            
        except Exception as e:
            logger.error(f"CV parsing failed: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize CV text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s@.,;:!?()\-\[\]/]', ' ', text)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        return text.strip()
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract different sections from CV text."""
        sections = {}
        lines = text.split('\n')
        
        current_section = None
        current_content = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Check if this line is a section header
            section_found = None
            for section_name, patterns in self.section_patterns.items():
                for pattern in patterns:
                    if re.match(pattern, line):
                        section_found = section_name
                        break
                if section_found:
                    break
            
            if section_found:
                # Save previous section if exists
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = section_found
                current_content = []
            elif current_section:
                # Add line to current section
                current_content.append(line)
            else:
                # No section yet, add to default
                if 'summary' not in sections:
                    sections['summary'] = []
                if 'summary' in sections:
                    sections['summary'].append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        elif 'summary' in sections and sections['summary']:
            sections['summary'] = '\n'.join(sections['summary'])
        
        return sections
    
    def _parse_experience(self, experience_text: str) -> List[ExperienceEntry]:
        """Parse work experience section."""
        experiences = []
        
        if not experience_text:
            return experiences
        
        # Split by common delimiters
        entries = re.split(r'\n(?=\w)|\n\s*\n', experience_text)
        
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            
            # Extract title and company
            title, company = self._extract_title_company(entry)
            
            # Extract duration
            duration = self._extract_duration(entry)
            
            # Extract description
            description = self._extract_description(entry)
            
            # Extract dates
            start_date, end_date = self._extract_dates(entry)
            
            # Extract skills from description
            skills = self._extract_skills_from_text(description)
            
            if title or company:
                experiences.append(ExperienceEntry(
                    title=title or "Unknown Position",
                    company=company or "Unknown Company",
                    duration=duration,
                    description=description,
                    start_date=start_date,
                    end_date=end_date,
                    skills=skills
                ))
        
        return experiences
    
    def _parse_education(self, education_text: str) -> List[EducationEntry]:
        """Parse education section."""
        education = []
        
        if not education_text:
            return education
        
        entries = re.split(r'\n(?=\w)|\n\s*\n', education_text)
        
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            
            # Extract degree
            degree = self._extract_degree(entry)
            
            # Extract institution
            institution = self._extract_institution(entry)
            
            # Extract duration
            duration = self._extract_duration(entry)
            
            # Extract description
            description = self._extract_description(entry)
            
            # Extract dates
            start_date, end_date = self._extract_dates(entry)
            
            if degree or institution:
                education.append(EducationEntry(
                    degree=degree or "Unknown Degree",
                    institution=institution or "Unknown Institution",
                    duration=duration,
                    description=description,
                    start_date=start_date,
                    end_date=end_date
                ))
        
        return education
    
    def _parse_skills(self, skills_text: str, full_text: str) -> List[SkillEntry]:
        """Parse skills section and extract from full text."""
        skills = []
        
        # Parse dedicated skills section
        if skills_text:
            section_skills = self._extract_skills_from_text(skills_text)
            skills.extend(section_skills)
        
        # Extract skills from entire CV
        full_text_skills = self._extract_skills_from_text(full_text)
        
        # Merge and deduplicate
        seen_skills = set()
        for skill in skills + full_text_skills:
            key = (skill.name.lower(), skill.category)
            if key not in seen_skills:
                seen_skills.add(key)
                skills.append(skill)
        
        return skills
    
    def _parse_projects(self, projects_text: str) -> List[Dict[str, Any]]:
        """Parse projects section."""
        projects = []
        
        if not projects_text:
            return projects
        
        # Simple project extraction - can be enhanced
        entries = re.split(r'\n(?=\w)|\n\s*\n', projects_text)
        
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            
            projects.append({
                'name': self._extract_project_name(entry),
                'description': entry,
                'technologies': self._extract_skills_from_text(entry)
            })
        
        return projects
    
    def _parse_certifications(self, cert_text: str) -> List[str]:
        """Parse certifications section."""
        if not cert_text:
            return []
        
        # Split by common delimiters
        certs = re.split(r'[,;]|\n', cert_text)
        return [cert.strip() for cert in certs if cert.strip()]
    
    def _parse_languages(self, lang_text: str) -> List[Dict[str, str]]:
        """Parse languages section."""
        languages = []
        
        if not lang_text:
            return languages
        
        # Extract language and proficiency
        lines = lang_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Simple pattern matching
            match = re.match(r'(.+?)\s*[:\-]\s*(.+)', line)
            if match:
                languages.append({
                    'language': match.group(1).strip(),
                    'proficiency': match.group(2).strip()
                })
            else:
                languages.append({
                    'language': line,
                    'proficiency': 'Not specified'
                })
        
        return languages
    
    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from CV."""
        contact = {}
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact['email'] = emails[0]
        
        # Phone
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        if phones:
            contact['phone'] = phones[0]
        
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w\-]+'
        linkedin = re.findall(linkedin_pattern, text)
        if linkedin:
            contact['linkedin'] = f"https://{linkedin[0]}"
        
        # GitHub
        github_pattern = r'github\.com/[\w\-]+'
        github = re.findall(github_pattern, text)
        if github:
            contact['github'] = f"https://{github[0]}"
        
        return contact
    
    def _extract_skills_from_text(self, text: str) -> List[SkillEntry]:
        """Extract skills from text using pattern matching and NLP."""
        skills = []
        
        if SPACY_AVAILABLE and nlp:
            # Use spaCy for better extraction
            doc = nlp(text.lower())
            
            # Extract noun chunks and named entities
            for chunk in doc.noun_chunks:
                skill_text = chunk.text.strip()
                if len(skill_text) > 2 and len(skill_text) < 50:
                    category = self._categorize_skill(skill_text)
                    confidence = self._calculate_skill_confidence(skill_text, chunk)
                    
                    skills.append(SkillEntry(
                        name=skill_text.title(),
                        category=category,
                        confidence=confidence,
                        context=chunk.sent.text
                    ))
        
        # Fallback to pattern matching
        for category, keywords in self.skill_categories.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    skills.append(SkillEntry(
                        name=match,
                        category=category,
                        confidence=0.8,
                        context=text[max(0, text.lower().find(match.lower())-50):text.lower().find(match.lower())+50]
                    ))
        
        return skills
    
    def _categorize_skill(self, skill_text: str) -> str:
        """Categorize a skill based on keywords."""
        skill_lower = skill_text.lower()
        
        for category, keywords in self.skill_categories.items():
            for keyword in keywords:
                if keyword in skill_lower:
                    return category
        
        return 'other'
    
    def _calculate_skill_confidence(self, skill_text: str, chunk) -> float:
        """Calculate confidence score for skill extraction."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for longer, more specific skills
        if len(skill_text) > 5:
            confidence += 0.1
        
        # Boost confidence for technical terms
        if any(char.isupper() for char in skill_text):
            confidence += 0.1
        
        # Boost confidence if it's a named entity
        if hasattr(chunk, 'label_') and chunk.label_ in ['ORG', 'PRODUCT']:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _extract_title_company(self, text: str) -> Tuple[str, str]:
        """Extract job title and company from experience entry."""
        lines = text.split('\n')
        
        title = ""
        company = ""
        
        if lines:
            first_line = lines[0].strip()
            
            # Common patterns
            patterns = [
                r'(.+?)\s+@\s+(.+)',  # Title @ Company
                r'(.+?)\s*\|\s*(.+)',  # Title | Company
                r'(.+?)\s*-\s*(.+)',  # Title - Company
                r'(.+?),\s*(.+)',     # Title, Company
            ]
            
            for pattern in patterns:
                match = re.match(pattern, first_line)
                if match:
                    title, company = match.group(1).strip(), match.group(2).strip()
                    break
            
            # If no pattern matched, use heuristics
            if not title and not company:
                words = first_line.split()
                if len(words) >= 2:
                    title = ' '.join(words[:len(words)//2])
                    company = ' '.join(words[len(words)//2:])
        
        return title, company
    
    def _extract_duration(self, text: str) -> str:
        """Extract duration from text."""
        # Common duration patterns
        patterns = [
            r'(\d{1,2}\s*(?:years?|yrs?))\s*(?:to|\-|–)\s*(\d{1,2}\s*(?:years?|yrs?))',
            r'(\d{1,2}\s*(?:years?|yrs?))\s*(?:to|\-|–)\s*(present|current)',
            r'(\w{3}\s*\d{4})\s*(?:to|\-|–)\s*(\w{3}\s*\d{4})',
            r'(\w{3}\s*\d{4})\s*(?:to|\-|–)\s*(present|current)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return ' - '.join(match.groups())
        
        return ""
    
    def _extract_dates(self, text: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Extract start and end dates from text."""
        # This is a simplified version - could use more sophisticated date parsing
        start_date = None
        end_date = None
        
        # Look for year patterns
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, text)
        
        if len(years) >= 2:
            try:
                start_date = datetime(int(years[0]), 1, 1)
                end_date = datetime(int(years[1]), 12, 31)
            except ValueError:
                pass
        elif len(years) == 1:
            try:
                start_date = datetime(int(years[0]), 1, 1)
            except ValueError:
                pass
        
        return start_date, end_date
    
    def _extract_description(self, text: str) -> str:
        """Extract description from experience/education entry."""
        lines = text.split('\n')
        
        # Skip first line (usually title/company)
        if len(lines) > 1:
            return '\n'.join(line.strip() for line in lines[1:] if line.strip())
        
        return ""
    
    def _extract_degree(self, text: str) -> str:
        """Extract degree from education entry."""
        for keyword in self.degree_keywords:
            if keyword.lower() in text.lower():
                return text.strip()
        
        return ""
    
    def _extract_institution(self, text: str) -> str:
        """Extract institution from education entry."""
        # Look for university/company names
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if len(line) > 10 and not any(keyword in line.lower() for keyword in self.degree_keywords):
                return line
        
        return ""
    
    def _extract_project_name(self, text: str) -> str:
        """Extract project name from project entry."""
        lines = text.split('\n')
        return lines[0].strip() if lines else ""
    
    def _calculate_total_experience(self, experiences: List[ExperienceEntry]) -> float:
        """Calculate total years of experience."""
        total_days = 0
        
        for exp in experiences:
            if exp.start_date:
                end_date = exp.end_date or datetime.now()
                total_days += (end_date - exp.start_date).days
        
        return total_days / 365.25  # Convert to years
    
    def _calculate_confidence_score(self, sections: Dict, skills: List, experiences: List) -> float:
        """Calculate overall parsing confidence score."""
        score = 0.0
        
        # Section completeness
        section_weight = 0.3
        expected_sections = ['experience', 'education', 'skills']
        found_sections = sum(1 for section in expected_sections if section in sections)
        score += (found_sections / len(expected_sections)) * section_weight
        
        # Skills extraction
        skills_weight = 0.3
        if skills:
            avg_confidence = sum(skill.confidence for skill in skills) / len(skills)
            score += avg_confidence * skills_weight
        
        # Experience structure
        experience_weight = 0.4
        if experiences:
            structured_experiences = sum(1 for exp in experiences if exp.title and exp.company)
            score += (structured_experiences / len(experiences)) * experience_weight
        
        return min(score, 1.0)
    
    def _experience_to_dict(self, exp: ExperienceEntry) -> Dict[str, Any]:
        """Convert ExperienceEntry to dictionary."""
        return {
            'title': exp.title,
            'company': exp.company,
            'duration': exp.duration,
            'description': exp.description,
            'start_date': exp.start_date.isoformat() if exp.start_date else None,
            'end_date': exp.end_date.isoformat() if exp.end_date else None,
            'skills': [self._skill_to_dict(skill) for skill in exp.skills]
        }
    
    def _education_to_dict(self, edu: EducationEntry) -> Dict[str, Any]:
        """Convert EducationEntry to dictionary."""
        return {
            'degree': edu.degree,
            'institution': edu.institution,
            'duration': edu.duration,
            'description': edu.description,
            'start_date': edu.start_date.isoformat() if edu.start_date else None,
            'end_date': edu.end_date.isoformat() if edu.end_date else None
        }
    
    def _skill_to_dict(self, skill: SkillEntry) -> Dict[str, Any]:
        """Convert SkillEntry to dictionary."""
        return {
            'name': skill.name,
            'category': skill.category,
            'confidence': skill.confidence,
            'context': skill.context
        }
