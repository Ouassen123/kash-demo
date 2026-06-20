"""Taxonomy mapping for normalizing extracted CV data."""

from typing import Dict, List, Any, Optional, Tuple
import re

from src.core.logging import get_logger
from .utils import MappingResult

logger = get_logger(__name__)


class TaxonomyMapper:
    """Maps extracted CV data to normalized taxonomy."""
    
    def __init__(self):
        """Initialize taxonomy mapper."""
        self._load_default_taxonomy()
        self._load_mapping_rules()
    
    def _load_default_taxonomy(self):
        """Load default taxonomy for mapping."""
        self.default_taxonomy = {
            'skills': {
                'programming': {
                    'languages': [
                        'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Rust',
                        'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala', 'TypeScript'
                    ],
                    'frameworks': [
                        'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask',
                        'FastAPI', 'Spring', '.NET', 'Express.js', 'Laravel'
                    ],
                    'databases': [
                        'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
                        'Cassandra', 'DynamoDB', 'SQLite', 'Oracle', 'SQL Server'
                    ],
                    'tools': [
                        'Git', 'Docker', 'Kubernetes', 'Jenkins', 'CI/CD',
                        'Terraform', 'Ansible', 'Webpack', 'Babel', 'ESLint'
                    ]
                },
                'cloud': {
                    'providers': ['AWS', 'Azure', 'GCP', 'Google Cloud', 'Heroku'],
                    'services': [
                        'EC2', 'S3', 'Lambda', 'API Gateway', 'CloudFormation',
                        'Azure Functions', 'Blob Storage', 'App Engine', 'Cloud Run'
                    ]
                },
                'soft_skills': {
                    'leadership': [
                        'Team Management', 'Project Leadership', 'Mentoring',
                        'Strategic Planning', 'Decision Making'
                    ],
                    'communication': [
                        'Public Speaking', 'Written Communication', 'Presentation',
                        'Negotiation', 'Client Communication'
                    ],
                    'collaboration': [
                        'Teamwork', 'Cross-functional Collaboration', 'Agile',
                        'Scrum', 'Pair Programming'
                    ]
                }
            },
            'education_levels': {
                'bachelor': [
                    'Bachelor of Science', 'B.S.', 'B.Sc.', 'Bachelor of Arts',
                    'B.A.', 'Licence', 'Undergraduate Degree'
                ],
                'master': [
                    'Master of Science', 'M.S.', 'M.Sc.', 'Master of Arts',
                    'M.A.', 'Master', 'Graduate Degree'
                ],
                'phd': [
                    'Doctor of Philosophy', 'Ph.D.', 'PhD', 'Doctorate',
                    'Doctoral Degree', 'Doctorat'
                ],
                'associate': [
                    'Associate Degree', 'A.S.', 'A.A.', 'Diploma', 'Certificate'
                ]
            },
            'experience_levels': {
                'entry': [
                    'Junior', 'Entry Level', 'Intern', 'Trainee', 'Graduate',
                    'Junior Developer', 'Junior Engineer'
                ],
                'mid': [
                    'Software Engineer', 'Developer', 'Engineer', 'Analyst',
                    'Specialist', 'Consultant', 'Coordinator'
                ],
                'senior': [
                    'Senior', 'Lead', 'Principal', 'Staff', 'Senior Developer',
                    'Senior Engineer', 'Lead Developer', 'Principal Engineer'
                ],
                'management': [
                    'Manager', 'Director', 'Head', 'Chief', 'VP', 'Vice President',
                    'CTO', 'CIO', 'Engineering Manager', 'Product Manager'
                ]
            }
        }
    
    def _load_mapping_rules(self):
        """Load mapping rules and synonyms."""
        self.skill_synonyms = {
            'JS': 'JavaScript',
            'TS': 'TypeScript',
            'C#': 'C#',
            'C++': 'C++',
            'Node': 'Node.js',
            'ReactJS': 'React',
            'VueJS': 'Vue.js',
            'AWS': 'AWS',
            'Azure': 'Azure',
            'GCP': 'GCP',
            'Git': 'Git',
            'Docker': 'Docker',
            'K8s': 'Kubernetes'
        }
        
        self.degree_variations = {
            'BSc': 'Bachelor of Science',
            'MSc': 'Master of Science',
            'BSc Computer Science': 'Bachelor of Science in Computer Science',
            'MS Computer Science': 'Master of Science in Computer Science',
            'BS CS': 'Bachelor of Science in Computer Science',
            'MS CS': 'Master of Science in Computer Science'
        }
    
    def map_skill(self, user_skill: str, taxonomy: Optional[Dict] = None) -> MappingResult:
        """
        Map a user skill to taxonomy.
        
        Args:
            user_skill: Skill name from CV
            taxonomy: Custom taxonomy (optional, uses default if None)
            
        Returns:
            MappingResult with mapped skill and metadata
        """
        if taxonomy is None:
            taxonomy = self.default_taxonomy
        
        user_skill_clean = user_skill.strip()
        
        # Check synonyms first
        if user_skill_clean in self.skill_synonyms:
            mapped_skill = self.skill_synonyms[user_skill_clean]
            return self._create_mapping_result(
                user_skill_clean, mapped_skill, taxonomy, 'exact', 0.95
            )
        
        # Try exact match
        exact_result = self._try_exact_match(user_skill_clean, taxonomy['skills'])
        if exact_result:
            return exact_result
        
        # Try partial match
        partial_result = self._try_partial_match(user_skill_clean, taxonomy['skills'])
        if partial_result:
            return partial_result
        
        # Try semantic match
        semantic_result = self._try_semantic_match(user_skill_clean, taxonomy['skills'])
        if semantic_result:
            return semantic_result
        
        # No match found
        return MappingResult(
            original_value=user_skill_clean,
            mapped_value=user_skill_clean,
            match_type='no_match',
            confidence=0.1
        )
    
    def map_education_level(self, degree: str, taxonomy: Optional[Dict] = None) -> MappingResult:
        """
        Map education level to normalized form.
        
        Args:
            degree: Degree string from CV
            taxonomy: Custom taxonomy (optional)
            
        Returns:
            MappingResult with normalized education level
        """
        if taxonomy is None:
            taxonomy = self.default_taxonomy
        
        degree_clean = degree.strip()
        
        # Check variations first
        if degree_clean in self.degree_variations:
            normalized = self.degree_variations[degree_clean]
            level = self._find_education_level(normalized, taxonomy['education_levels'])
            return MappingResult(
                original_value=degree_clean,
                mapped_value=normalized,
                category=level,
                match_type='exact',
                confidence=0.9
            )
        
        # Try exact match
        for level, degrees in taxonomy['education_levels'].items():
            for degree_variant in degrees:
                if degree_variant.lower() == degree_clean.lower():
                    return MappingResult(
                        original_value=degree_clean,
                        mapped_value=degree_variant,
                        category=level,
                        match_type='exact',
                        confidence=0.9
                    )
        
        # Try partial match
        for level, degrees in taxonomy['education_levels'].items():
            for degree_variant in degrees:
                if degree_variant.lower() in degree_clean.lower() or degree_clean.lower() in degree_variant.lower():
                    return MappingResult(
                        original_value=degree_clean,
                        mapped_value=degree_variant,
                        category=level,
                        match_type='partial',
                        confidence=0.7
                    )
        
        # No match
        return MappingResult(
            original_value=degree_clean,
            mapped_value=degree_clean,
            match_type='no_match',
            confidence=0.2
        )
    
    def map_experience_level(self, job_title: str, taxonomy: Optional[Dict] = None) -> MappingResult:
        """
        Map job title to experience level.
        
        Args:
            job_title: Job title from CV
            taxonomy: Custom taxonomy (optional)
            
        Returns:
            MappingResult with experience level
        """
        if taxonomy is None:
            taxonomy = self.default_taxonomy
        
        title_clean = job_title.strip().lower()
        
        level_priority = ['management', 'senior', 'entry', 'mid']
        ordered_levels = [level for level in level_priority if level in taxonomy['experience_levels']]
        ordered_levels += [
            level for level in taxonomy['experience_levels'].keys()
            if level not in ordered_levels
        ]
        experience_levels = {level: taxonomy['experience_levels'][level] for level in ordered_levels}
        
        # Try exact match prioritizing seniority
        for level, titles in experience_levels.items():
            for title_variant in titles:
                if title_variant.lower() == title_clean:
                    return MappingResult(
                        original_value=job_title,
                        mapped_value=title_variant,
                        category=level,
                        match_type='exact',
                        confidence=0.9
                    )
        
        # Try partial match (check if title contains level indicator)
        for level, titles in experience_levels.items():
            for title_variant in titles:
                if title_variant.lower() in title_clean:
                    return MappingResult(
                        original_value=job_title,
                        mapped_value=title_variant,
                        category=level,
                        match_type='partial',
                        confidence=0.7
                    )
        
        # Try keyword matching
        for level, titles in experience_levels.items():
            for title_variant in titles:
                keywords = title_variant.lower().split()
                if any(keyword in title_clean for keyword in keywords if len(keyword) > 3):
                    return MappingResult(
                        original_value=job_title,
                        mapped_value=title_variant,
                        category=level,
                        match_type='semantic',
                        confidence=0.6
                    )
        
        # No match
        return MappingResult(
            original_value=job_title,
            mapped_value=job_title,
            match_type='no_match',
            confidence=0.3
        )
    
    def map_skills_batch(self, user_skills: List[str], taxonomy: Optional[Dict] = None) -> List[MappingResult]:
        """
        Map multiple skills to taxonomy.
        
        Args:
            user_skills: List of skill names
            taxonomy: Custom taxonomy (optional)
            
        Returns:
            List of MappingResult objects
        """
        results = []
        for skill in user_skills:
            result = self.map_skill(skill, taxonomy)
            results.append(result)
        return results
    
    def validate_taxonomy(self, taxonomy: Dict) -> bool:
        """
        Validate taxonomy structure.
        
        Args:
            taxonomy: Taxonomy dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_sections = ['skills']
        optional_sections = ['education_levels', 'experience_levels']
        
        if not isinstance(taxonomy, dict):
            return False
        
        for section in required_sections:
            if section not in taxonomy or not isinstance(taxonomy[section], dict):
                return False
            if not taxonomy[section]:
                return False
        
        for section in optional_sections:
            if section in taxonomy and not isinstance(taxonomy[section], dict):
                return False
        
        return True
    
    def calculate_mapping_statistics(self, mapping_results: List[MappingResult]) -> Dict[str, Any]:
        """
        Calculate statistics for mapping results.
        
        Args:
            mapping_results: List of mapping results
            
        Returns:
            Statistics dictionary
        """
        total_skills = len(mapping_results)
        mapped_skills = sum(1 for r in mapping_results if r.match_type != 'no_match')
        unmapped_skills = total_skills - mapped_skills
        
        mapping_rate = mapped_skills / total_skills if total_skills > 0 else 0
        
        # Average confidence
        confidences = [r.confidence for r in mapping_results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Match type distribution
        match_types = [r.match_type for r in mapping_results]
        match_type_dist = {
            match_type: match_types.count(match_type) 
            for match_type in set(match_types)
        }
        
        return {
            'total_skills': total_skills,
            'mapped_skills': mapped_skills,
            'unmapped_skills': unmapped_skills,
            'mapping_rate': mapping_rate,
            'average_confidence': avg_confidence,
            'match_type_distribution': match_type_dist
        }
    
    def _try_exact_match(self, skill: str, skills_taxonomy: Dict) -> Optional[MappingResult]:
        """Try exact match against taxonomy."""
        for category, subcategories in skills_taxonomy.items():
            for subcategory, skills in subcategories.items():
                for taxonomy_skill in skills:
                    if taxonomy_skill.lower() == skill.lower():
                        return self._create_mapping_result(
                            skill, taxonomy_skill, skills_taxonomy, 'exact', 0.95,
                            category, subcategory
                        )
        return None
    
    def _try_partial_match(self, skill: str, skills_taxonomy: Dict) -> Optional[MappingResult]:
        """Try partial match against taxonomy."""
        for category, subcategories in skills_taxonomy.items():
            for subcategory, skills in subcategories.items():
                for taxonomy_skill in skills:
                    if (taxonomy_skill.lower() in skill.lower() or 
                        skill.lower() in taxonomy_skill.lower()):
                        return self._create_mapping_result(
                            skill, taxonomy_skill, skills_taxonomy, 'partial', 0.8,
                            category, subcategory
                        )
        return None
    
    def _try_semantic_match(self, skill: str, skills_taxonomy: Dict) -> Optional[MappingResult]:
        """Try semantic match against taxonomy."""
        skill_words = set(skill.lower().split())
        
        for category, subcategories in skills_taxonomy.items():
            for subcategory, skills in subcategories.items():
                for taxonomy_skill in skills:
                    taxonomy_words = set(taxonomy_skill.lower().split())
                    
                    # Calculate word overlap
                    overlap = len(skill_words.intersection(taxonomy_words))
                    total_words = len(skill_words.union(taxonomy_words))
                    
                    if total_words > 0 and overlap / total_words >= 0.4:
                        confidence = 0.6 + (overlap / total_words) * 0.2
                        return self._create_mapping_result(
                            skill, taxonomy_skill, skills_taxonomy, 'semantic', confidence,
                            category, subcategory
                        )
        return None
    
    def _create_mapping_result(self, original: str, mapped: str, taxonomy: Dict,
                            match_type: str, confidence: float,
                            category: Optional[str] = None,
                            subcategory: Optional[str] = None) -> MappingResult:
        """Create MappingResult object."""
        return MappingResult(
            original_value=original,
            mapped_value=mapped,
            category=category,
            subcategory=subcategory,
            match_type=match_type,
            confidence=confidence
        )
    
    def _find_education_level(self, degree: str, education_taxonomy: Dict) -> Optional[str]:
        """Find education level for degree."""
        for level, degrees in education_taxonomy.items():
            if degree in degrees:
                return level
        return None
