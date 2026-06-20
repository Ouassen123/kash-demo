"""ESCO client for skills and occupation mapping."""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
from datetime import datetime, timedelta
import hashlib

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ESCOSkill:
    """ESCO skill entity."""
    uri: str
    preferred_label: str
    description: str
    skill_type: str
    concept_uri: str
    confidence: float = 1.0


@dataclass
class ESCOOccupation:
    """ESCO occupation entity."""
    uri: str
    preferred_label: str
    description: str
    concept_uri: str
    isco_code: Optional[str] = None
    confidence: float = 1.0


@dataclass
class SkillMatch:
    """Skill matching result."""
    user_skill: str
    esco_skill: ESCOSkill
    similarity_score: float
    match_type: str  # exact, partial, semantic


@dataclass
class OccupationMatch:
    """Occupation matching result."""
    occupation: ESCOOccupation
    match_score: float
    required_skills: List[str]
    missing_skills: List[str]
    skill_coverage: float


class ESCOClient:
    """Client for ESCO API integration with caching."""
    
    def __init__(self):
        self.base_url = settings.esco_api_url
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = timedelta(hours=24)
        
        # ESCO API endpoints
        self.endpoints = {
            'search': '/search',
            'skill': '/skill',
            'occupation': '/occupation',
            'skills_by_occupation': '/occupation/{occupation_uri}/skills',
            'occupations_by_skill': '/skill/{skill_uri}/occupations'
        }
    
    async def search_skills(self, query: str, limit: int = 10) -> List[ESCOSkill]:
        """
        Search for skills in ESCO database.
        
        Args:
            query: Search term
            limit: Maximum number of results
            
        Returns:
            List of ESCO skills
        """
        cache_key = f"skills_search:{query}:{limit}"
        
        # Check cache
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for skills search: {query}")
                return cached_result
        
        try:
            params = {
                'text': query,
                'type': 'skill',
                'limit': limit,
                'language': 'en'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}{self.endpoints['search']}", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        skills = []
                        
                        for item in data.get('_embedded', {}).get('results', []):
                            skill = ESCOSkill(
                                uri=item.get('uri', ''),
                                preferred_label=item.get('preferredLabel', {}).get('en', ''),
                                description=item.get('description', {}).get('en', ''),
                                skill_type=item.get('skillType', ''),
                                concept_uri=item.get('conceptUri', '')
                            )
                            skills.append(skill)
                        
                        # Cache result
                        self.cache[cache_key] = (skills, datetime.now())
                        logger.info(f"Found {len(skills)} skills for query: {query}")
                        return skills
                    else:
                        logger.error(f"ESCO API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error searching ESCO skills: {e}")
            return []
    
    async def search_occupations(self, query: str, limit: int = 10) -> List[ESCOOccupation]:
        """
        Search for occupations in ESCO database.
        
        Args:
            query: Search term
            limit: Maximum number of results
            
        Returns:
            List of ESCO occupations
        """
        cache_key = f"occupations_search:{query}:{limit}"
        
        # Check cache
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for occupations search: {query}")
                return cached_result
        
        try:
            params = {
                'text': query,
                'type': 'occupation',
                'limit': limit,
                'language': 'en'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}{self.endpoints['search']}", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        occupations = []
                        
                        for item in data.get('_embedded', {}).get('results', []):
                            occupation = ESCOOccupation(
                                uri=item.get('uri', ''),
                                preferred_label=item.get('preferredLabel', {}).get('en', ''),
                                description=item.get('description', {}).get('en', ''),
                                concept_uri=item.get('conceptUri', ''),
                                isco_code=item.get('iscoCode')
                            )
                            occupations.append(occupation)
                        
                        # Cache result
                        self.cache[cache_key] = (occupations, datetime.now())
                        logger.info(f"Found {len(occupations)} occupations for query: {query}")
                        return occupations
                    else:
                        logger.error(f"ESCO API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error searching ESCO occupations: {e}")
            return []
    
    async def get_skill_details(self, skill_uri: str) -> Optional[ESCOSkill]:
        """
        Get detailed information about a specific skill.
        
        Args:
            skill_uri: ESCO skill URI
            
        Returns:
            ESCO skill details or None
        """
        cache_key = f"skill_details:{skill_uri}"
        
        # Check cache
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for skill details: {skill_uri}")
                return cached_result
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}{self.endpoints['skill']}/{skill_uri}") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        skill = ESCOSkill(
                            uri=data.get('uri', ''),
                            preferred_label=data.get('preferredLabel', {}).get('en', ''),
                            description=data.get('description', {}).get('en', ''),
                            skill_type=data.get('skillType', ''),
                            concept_uri=data.get('conceptUri', '')
                        )
                        
                        # Cache result
                        self.cache[cache_key] = (skill, datetime.now())
                        return skill
                    else:
                        logger.error(f"ESCO API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting ESCO skill details: {e}")
            return None
    
    async def get_occupation_details(self, occupation_uri: str) -> Optional[ESCOOccupation]:
        """
        Get detailed information about a specific occupation.
        
        Args:
            occupation_uri: ESCO occupation URI
            
        Returns:
            ESCO occupation details or None
        """
        cache_key = f"occupation_details:{occupation_uri}"
        
        # Check cache
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for occupation details: {occupation_uri}")
                return cached_result
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}{self.endpoints['occupation']}/{occupation_uri}") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        occupation = ESCOOccupation(
                            uri=data.get('uri', ''),
                            preferred_label=data.get('preferredLabel', {}).get('en', ''),
                            description=data.get('description', {}).get('en', ''),
                            concept_uri=data.get('conceptUri', ''),
                            isco_code=data.get('iscoCode')
                        )
                        
                        # Cache result
                        self.cache[cache_key] = (occupation, datetime.now())
                        return occupation
                    else:
                        logger.error(f"ESCO API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting ESCO occupation details: {e}")
            return None
    
    async def get_skills_for_occupation(self, occupation_uri: str) -> List[ESCOSkill]:
        """
        Get all skills required for a specific occupation.
        
        Args:
            occupation_uri: ESCO occupation URI
            
        Returns:
            List of required skills
        """
        cache_key = f"occupation_skills:{occupation_uri}"
        
        # Check cache
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for occupation skills: {occupation_uri}")
                return cached_result
        
        try:
            endpoint = self.endpoints['skills_by_occupation'].format(occupation_uri=occupation_uri)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        skills = []
                        
                        for item in data.get('_embedded', {}).get('results', []):
                            skill = ESCOSkill(
                                uri=item.get('uri', ''),
                                preferred_label=item.get('preferredLabel', {}).get('en', ''),
                                description=item.get('description', {}).get('en', ''),
                                skill_type=item.get('skillType', ''),
                                concept_uri=item.get('conceptUri', '')
                            )
                            skills.append(skill)
                        
                        # Cache result
                        self.cache[cache_key] = (skills, datetime.now())
                        logger.info(f"Found {len(skills)} skills for occupation: {occupation_uri}")
                        return skills
                    else:
                        logger.error(f"ESCO API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting skills for occupation: {e}")
            return []
    
    async def get_occupations_for_skill(self, skill_uri: str) -> List[ESCOOccupation]:
        """
        Get all occupations that require a specific skill.
        
        Args:
            skill_uri: ESCO skill URI
            
        Returns:
            List of related occupations
        """
        cache_key = f"skill_occupations:{skill_uri}"
        
        # Check cache
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for skill occupations: {skill_uri}")
                return cached_result
        
        try:
            endpoint = self.endpoints['occupations_by_skill'].format(skill_uri=skill_uri)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        occupations = []
                        
                        for item in data.get('_embedded', {}).get('results', []):
                            occupation = ESCOOccupation(
                                uri=item.get('uri', ''),
                                preferred_label=item.get('preferredLabel', {}).get('en', ''),
                                description=item.get('description', {}).get('en', ''),
                                concept_uri=item.get('conceptUri', ''),
                                isco_code=item.get('iscoCode')
                            )
                            occupations.append(occupation)
                        
                        # Cache result
                        self.cache[cache_key] = (occupations, datetime.now())
                        logger.info(f"Found {len(occupations)} occupations for skill: {skill_uri}")
                        return occupations
                    else:
                        logger.error(f"ESCO API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting occupations for skill: {e}")
            return []
    
    async def match_user_skills_to_esco(self, user_skills: List[str]) -> List[SkillMatch]:
        """
        Match user skills to ESCO skills database.
        
        Args:
            user_skills: List of user skills
            
        Returns:
            List of skill matches with similarity scores
        """
        matches = []
        
        for user_skill in user_skills:
            # Search for exact matches first
            exact_matches = await self.search_skills(user_skill, limit=5)
            
            if exact_matches:
                for esco_skill in exact_matches:
                    similarity = self._calculate_similarity(user_skill.lower(), esco_skill.preferred_label.lower())
                    if similarity > 0.7:  # High similarity threshold
                        matches.append(SkillMatch(
                            user_skill=user_skill,
                            esco_skill=esco_skill,
                            similarity_score=similarity,
                            match_type='exact' if similarity > 0.9 else 'partial'
                        ))
            else:
                # Try partial matching with keywords
                keywords = self._extract_keywords(user_skill)
                for keyword in keywords:
                    partial_matches = await self.search_skills(keyword, limit=3)
                    for esco_skill in partial_matches:
                        similarity = self._calculate_similarity(user_skill.lower(), esco_skill.preferred_label.lower())
                        if similarity > 0.5:  # Lower threshold for partial matches
                            matches.append(SkillMatch(
                                user_skill=user_skill,
                                esco_skill=esco_skill,
                                similarity_score=similarity,
                                match_type='semantic'
                            ))
        
        # Sort by similarity score and remove duplicates
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        seen_skills = set()
        unique_matches = []
        
        for match in matches:
            if match.esco_skill.uri not in seen_skills:
                seen_skills.add(match.esco_skill.uri)
                unique_matches.append(match)
        
        logger.info(f"Matched {len(unique_matches)} user skills to ESCO database")
        return unique_matches
    
    async def suggest_occupations(self, skill_matches: List[SkillMatch], limit: int = 10) -> List[OccupationMatch]:
        """
        Suggest occupations based on matched skills.
        
        Args:
            skill_matches: List of skill matches
            limit: Maximum number of suggestions
            
        Returns:
            List of occupation matches with scores
        """
        # Get occupations for each matched skill
        occupation_scores = {}
        skill_coverage = {}
        
        for skill_match in skill_matches:
            occupations = await self.get_occupations_for_skill(skill_match.esco_skill.uri)
            
            for occupation in occupations:
                if occupation.uri not in occupation_scores:
                    occupation_scores[occupation.uri] = {
                        'occupation': occupation,
                        'score': 0,
                        'matched_skills': [],
                        'total_skills_needed': 0
                    }
                
                occupation_scores[occupation.uri]['score'] += skill_match.similarity_score
                occupation_scores[occupation.uri]['matched_skills'].append(skill_match)
        
        # Get required skills for each occupation to calculate coverage
        occupation_matches = []
        
        for uri, data in occupation_scores.items():
            occupation = data['occupation']
            required_skills = await self.get_skills_for_occupation(uri)
            
            # Calculate skill coverage
            matched_skill_uris = {match.esco_skill.uri for match in data['matched_skills']}
            required_skill_uris = {skill.uri for skill in required_skills}
            
            coverage = len(matched_skill_uris & required_skill_uris) / len(required_skill_uris) if required_skill_uris else 0
            
            # Calculate final score (combination of skill match scores and coverage)
            final_score = (data['score'] / len(data['matched_skills'])) * 0.7 + coverage * 0.3
            
            # Identify missing skills
            missing_skills = [skill for skill in required_skills if skill.uri not in matched_skill_uris]
            
            occupation_matches.append(OccupationMatch(
                occupation=occupation,
                match_score=final_score,
                required_skills=[skill.preferred_label for skill in required_skills],
                missing_skills=[skill.preferred_label for skill in missing_skills],
                skill_coverage=coverage
            ))
        
        # Sort by match score and return top results
        occupation_matches.sort(key=lambda x: x.match_score, reverse=True)
        
        logger.info(f"Generated {len(occupation_matches)} occupation suggestions")
        return occupation_matches[:limit]
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.
        Simple implementation using Jaccard similarity.
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for partial matching."""
        # Simple keyword extraction - can be enhanced with NLP
        words = text.lower().split()
        keywords = []
        
        # Filter out common stop words and keep meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        for word in words:
            if len(word) > 2 and word not in stop_words:
                keywords.append(word)
        
        return keywords
    
    def clear_cache(self):
        """Clear the in-memory cache."""
        self.cache.clear()
        logger.info("ESCO client cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        expired_entries = sum(1 for _, timestamp in self.cache.values() 
                            if datetime.now() - timestamp > self.cache_ttl)
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'active_entries': total_entries - expired_entries,
            'cache_ttl_hours': self.cache_ttl.total_seconds() / 3600
        }
