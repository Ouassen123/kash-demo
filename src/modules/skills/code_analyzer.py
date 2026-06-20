"""Code analyzer for skills assessment and technical evaluation."""

import re
import ast
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CodeMetric:
    """Code quality metric."""
    name: str
    value: float
    description: str
    threshold: float
    is_good: bool


@dataclass
class TechnicalSkill:
    """Technical skill with confidence score."""
    name: str
    category: str
    confidence: float
    evidence: List[str]
    proficiency_level: str  # beginner, intermediate, advanced, expert


@dataclass
class CodePattern:
    """Code pattern or practice."""
    name: str
    type: str  # design_pattern, anti_pattern, best_practice
    description: str
    locations: List[str]
    frequency: int


class CodeAnalyzer:
    """Advanced code analyzer for technical skills assessment."""
    
    def __init__(self):
        self.language_analyzers = {
            'python': PythonAnalyzer(),
            'javascript': JavaScriptAnalyzer(),
            'typescript': TypeScriptAnalyzer(),
            'java': JavaAnalyzer(),
            'csharp': CSharpAnalyzer(),
            'cpp': CppAnalyzer(),
            'go': GoAnalyzer(),
            'rust': RustAnalyzer(),
        }
        
        # Technical skills taxonomy
        self.skill_categories = {
            'programming_languages': {
                'python': ['python', 'py', 'django', 'flask', 'fastapi'],
                'javascript': ['javascript', 'js', 'node', 'express', 'react', 'vue', 'angular'],
                'typescript': ['typescript', 'ts', 'tsx'],
                'java': ['java', 'spring', 'hibernate', 'maven'],
                'csharp': ['csharp', 'c#', '.net', 'aspnet', 'entityframework'],
                'go': ['go', 'golang'],
                'rust': ['rust', 'cargo'],
                'cpp': ['cpp', 'c++', 'stl', 'boost'],
                'sql': ['sql', 'mysql', 'postgresql', 'sqlite', 'oracle'],
            },
            'frameworks_libraries': {
                'web_frameworks': ['react', 'vue', 'angular', 'django', 'flask', 'fastapi', 'express', 'spring', 'aspnet'],
                'testing_frameworks': ['pytest', 'jest', 'mocha', 'junit', 'unittest', 'selenium'],
                'orm_frameworks': ['sqlalchemy', 'django-orm', 'hibernate', 'entityframework', 'mongoose', 'prisma'],
                'build_tools': ['webpack', 'vite', 'babel', 'maven', 'gradle', 'npm', 'yarn', 'pip', 'poetry'],
            },
            'databases': {
                'relational': ['mysql', 'postgresql', 'sqlite', 'oracle', 'sqlserver'],
                'nosql': ['mongodb', 'redis', 'cassandra', 'elasticsearch', 'dynamodb'],
                'cloud_databases': ['aws-rds', 'azure-sql', 'gcp-sql'],
            },
            'cloud_devops': {
                'cloud_platforms': ['aws', 'azure', 'gcp'],
                'containerization': ['docker', 'kubernetes', 'k8s', 'container'],
                'infrastructure': ['terraform', 'cloudformation', 'arm', 'pulumi'],
                'cicd': ['jenkins', 'github-actions', 'gitlab-ci', 'travis', 'circleci'],
            },
            'tools_practices': {
                'version_control': ['git', 'github', 'gitlab', 'bitbucket'],
                'api_design': ['rest', 'graphql', 'grpc', 'openapi', 'swagger'],
                'testing': ['unit-test', 'integration-test', 'e2e-test', 'tdd', 'bdd'],
                'security': ['oauth', 'jwt', 'encryption', 'authentication', 'authorization'],
            }
        }
        
        # Code quality thresholds
        self.quality_thresholds = {
            'cyclomatic_complexity': 10.0,
            'maintainability_index': 70.0,
            'test_coverage': 80.0,
            'duplication': 5.0,
            'code_smells': 3.0,
        }
    
    def analyze_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Analyze a single code file.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            Dictionary with analysis results
        """
        try:
            language = self._detect_language(file_path)
            analyzer = self.language_analyzers.get(language, GenericAnalyzer())
            
            # Basic metrics
            metrics = analyzer.calculate_metrics(content)
            
            # Technical skills extraction
            skills = self._extract_technical_skills(content, language)
            
            # Code patterns detection
            patterns = analyzer.detect_patterns(content)
            
            # Quality assessment
            quality_metrics = self._assess_code_quality(content, language, metrics)
            
            # Security analysis
            security_issues = analyzer.analyze_security(content)
            
            # Performance analysis
            performance_issues = analyzer.analyze_performance(content)
            
            return {
                'file_path': file_path,
                'language': language,
                'metrics': metrics,
                'technical_skills': [self._skill_to_dict(skill) for skill in skills],
                'patterns': [self._pattern_to_dict(pattern) for pattern in patterns],
                'quality_metrics': [self._metric_to_dict(metric) for metric in quality_metrics],
                'security_issues': security_issues,
                'performance_issues': performance_issues,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze file {file_path}: {e}")
            return {
                'file_path': file_path,
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    def analyze_repository(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze multiple files from a repository.
        
        Args:
            files: List of file dictionaries with 'path' and 'content' keys
            
        Returns:
            Dictionary with repository analysis results
        """
        logger.info(f"Starting repository analysis for {len(files)} files")
        start_time = datetime.now()
        
        try:
            file_analyses = []
            all_skills = []
            all_patterns = []
            language_distribution = {}
            total_metrics = {
                'total_lines': 0,
                'total_files': 0,
                'total_functions': 0,
                'total_classes': 0,
                'avg_complexity': 0,
                'avg_maintainability': 0,
            }
            
            # Analyze each file
            for file_info in files:
                file_path = file_info.get('path', '')
                content = file_info.get('content', '')
                
                if not content or not self._should_analyze_file(file_path):
                    continue
                
                analysis = self.analyze_file(file_path, content)
                file_analyses.append(analysis)
                
                # Aggregate data
                if 'error' not in analysis:
                    language = analysis['language']
                    language_distribution[language] = language_distribution.get(language, 0) + 1
                    
                    # Collect skills
                    for skill in analysis.get('technical_skills', []):
                        all_skills.append(TechnicalSkill(
                            name=skill['name'],
                            category=skill['category'],
                            confidence=skill['confidence'],
                            evidence=skill.get('evidence', []),
                            proficiency_level=skill.get('proficiency_level', 'intermediate')
                        ))
                    
                    # Collect patterns
                    for pattern in analysis.get('patterns', []):
                        all_patterns.append(CodePattern(
                            name=pattern['name'],
                            type=pattern['type'],
                            description=pattern['description'],
                            locations=pattern.get('locations', []),
                            frequency=pattern.get('frequency', 1)
                        ))
                    
                    # Aggregate metrics
                    metrics = analysis.get('metrics', {})
                    total_metrics['total_lines'] += metrics.get('lines_of_code', 0)
                    total_metrics['total_files'] += 1
                    total_metrics['total_functions'] += metrics.get('function_count', 0)
                    total_metrics['total_classes'] += metrics.get('class_count', 0)
                    total_metrics['avg_complexity'] += metrics.get('cyclomatic_complexity', 0)
                    total_metrics['avg_maintainability'] += metrics.get('maintainability_index', 0)
            
            # Calculate averages
            if total_metrics['total_files'] > 0:
                total_metrics['avg_complexity'] /= total_metrics['total_files']
                total_metrics['avg_maintainability'] /= total_metrics['total_files']
            
            # Aggregate skills
            aggregated_skills = self._aggregate_skills(all_skills)
            
            # Aggregate patterns
            aggregated_patterns = self._aggregate_patterns(all_patterns)
            
            # Calculate overall scores
            overall_scores = self._calculate_overall_scores(
                total_metrics, aggregated_skills, aggregated_patterns
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                aggregated_skills, aggregated_patterns, overall_scores
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            results = {
                'summary': {
                    'total_files_analyzed': len(file_analyses),
                    'total_lines_of_code': total_metrics['total_lines'],
                    'language_distribution': language_distribution,
                    'processing_time_ms': processing_time
                },
                'metrics': total_metrics,
                'technical_skills': [self._skill_to_dict(skill) for skill in aggregated_skills],
                'patterns': [self._pattern_to_dict(pattern) for pattern in aggregated_patterns],
                'overall_scores': overall_scores,
                'recommendations': recommendations,
                'file_analyses': file_analyses[:10],  # Top 10 files
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Repository analysis completed in {processing_time:.2f}ms")
            return results
            
        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            raise
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path."""
        file_ext = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cs': 'csharp',
            '.cpp': 'cpp',
            '.cxx': 'cpp',
            '.cc': 'cpp',
            '.c': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'css',
            '.sass': 'css',
            '.less': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.dockerfile': 'dockerfile',
        }
        
        # Special cases
        if file_path.lower().endswith('dockerfile'):
            return 'dockerfile'
        elif file_path.lower().endswith(('.yml', '.yaml')):
            return 'yaml'
        elif file_path.lower().endswith(('.json', '.lock')):
            return 'json'
        
        return language_map.get(file_ext, 'text')
    
    def _should_analyze_file(self, file_path: str) -> bool:
        """Determine if a file should be analyzed."""
        # Skip common non-code files
        skip_patterns = [
            r'\.git/',
            r'node_modules/',
            r'__pycache__/',
            r'\.vscode/',
            r'\.idea/',
            r'build/',
            r'dist/',
            r'\.min\.js$',
            r'\.min\.css$',
            r'\.map$',
            r'\.png$',
            r'\.jpg$',
            r'\.jpeg$',
            r'\.gif$',
            r'\.svg$',
            r'\.ico$',
            r'\.pdf$',
            r'\.zip$',
            r'\.tar\.gz$',
            r'package-lock\.json',
            r'yarn\.lock',
            r'Gemfile\.lock'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, file_path, re.IGNORECASE):
                return False
        
        return True
    
    def _extract_technical_skills(self, content: str, language: str) -> List[TechnicalSkill]:
        """Extract technical skills from code content."""
        skills = []
        content_lower = content.lower()
        
        # Extract skills based on patterns
        for category, skills_dict in self.skill_categories.items():
            for subcategory, skill_list in skills_dict.items():
                for skill in skill_list:
                    # Check for skill mentions
                    pattern = r'\b' + re.escape(skill) + r'\b'
                    matches = re.findall(pattern, content_lower, re.IGNORECASE)
                    
                    if matches:
                        # Calculate confidence based on frequency and context
                        confidence = min(len(matches) * 0.2, 1.0)
                        
                        # Determine proficiency level
                        proficiency = self._determine_proficiency_level(content, skill, matches)
                        
                        # Extract evidence
                        evidence = self._extract_skill_evidence(content, skill)
                        
                        skills.append(TechnicalSkill(
                            name=skill,
                            category=f"{category}_{subcategory}",
                            confidence=confidence,
                            evidence=evidence,
                            proficiency_level=proficiency
                        ))
        
        return skills
    
    def _determine_proficiency_level(self, content: str, skill: str, matches: List[str]) -> str:
        """Determine proficiency level for a skill."""
        # Simple heuristic based on usage patterns
        if skill in ['python', 'javascript', 'java', 'csharp']:
            # Check for advanced patterns
            advanced_patterns = [
                r'decorator|@.*',  # Python decorators
                r'async|await',    # Async programming
                r'lambda',         # Lambda functions
                r'generator',      # Generators
                r'comprehension',  # List/dict comprehensions
                r'class\s+\w+\s*\([^)]*\):',  # Class inheritance
                r'interface|abstract',  # OOP concepts
            ]
            
            advanced_count = sum(1 for pattern in advanced_patterns if re.search(pattern, content, re.IGNORECASE))
            
            if advanced_count >= 3:
                return 'advanced'
            elif advanced_count >= 1:
                return 'intermediate'
            else:
                return 'beginner'
        
        elif skill in ['react', 'vue', 'angular']:
            # Check for framework-specific patterns
            framework_patterns = [
                r'component|Component',
                r'hook|Hook',
                r'state|State',
                r'props|Props',
                r'router|Router',
                r'redux|Redux',
                r'mobx|MobX',
            ]
            
            framework_count = sum(1 for pattern in framework_patterns if re.search(pattern, content, re.IGNORECASE))
            
            if framework_count >= 4:
                return 'advanced'
            elif framework_count >= 2:
                return 'intermediate'
            else:
                return 'beginner'
        
        else:
            # Default based on frequency
            if len(matches) >= 10:
                return 'advanced'
            elif len(matches) >= 3:
                return 'intermediate'
            else:
                return 'beginner'
    
    def _extract_skill_evidence(self, content: str, skill: str) -> List[str]:
        """Extract evidence of skill usage."""
        evidence = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if re.search(r'\b' + re.escape(skill) + r'\b', line, re.IGNORECASE):
                # Get context (surrounding lines)
                start = max(0, i - 1)
                end = min(len(lines), i + 2)
                context = '\n'.join(lines[start:end]).strip()
                
                if len(context) < 200:  # Keep evidence concise
                    evidence.append(context)
        
        return evidence[:3]  # Top 3 evidence pieces
    
    def _assess_code_quality(self, content: str, language: str, metrics: Dict[str, Any]) -> List[CodeMetric]:
        """Assess code quality metrics."""
        quality_metrics = []
        
        # Cyclomatic complexity
        complexity = metrics.get('cyclomatic_complexity', 0)
        quality_metrics.append(CodeMetric(
            name='cyclomatic_complexity',
            value=complexity,
            description='Code complexity based on control flow',
            threshold=self.quality_thresholds['cyclomatic_complexity'],
            is_good=complexity <= self.quality_thresholds['cyclomatic_complexity']
        ))
        
        # Maintainability index (simplified calculation)
        maintainability = self._calculate_maintainability_index(content, metrics)
        quality_metrics.append(CodeMetric(
            name='maintainability_index',
            value=maintainability,
            description='Code maintainability score (0-100)',
            threshold=self.quality_thresholds['maintainability_index'],
            is_good=maintainability >= self.quality_thresholds['maintainability_index']
        ))
        
        # Function length
        avg_function_length = metrics.get('avg_function_length', 0)
        quality_metrics.append(CodeMetric(
            name='avg_function_length',
            value=avg_function_length,
            description='Average function length in lines',
            threshold=50.0,
            is_good=avg_function_length <= 50.0
        ))
        
        # Comment ratio
        comment_ratio = metrics.get('comment_ratio', 0)
        quality_metrics.append(CodeMetric(
            name='comment_ratio',
            value=comment_ratio * 100,  # Convert to percentage
            description='Ratio of comments to code',
            threshold=15.0,  # At least 15% comments
            is_good=comment_ratio >= 0.15
        ))
        
        return quality_metrics
    
    def _calculate_maintainability_index(self, content: str, metrics: Dict[str, Any]) -> float:
        """Calculate maintainability index (simplified Halstead volume)."""
        lines_of_code = metrics.get('lines_of_code', 1)
        complexity = metrics.get('cyclomatic_complexity', 1)
        
        # Simplified maintainability index calculation
        volume = lines_of_code * complexity
        maintainability = max(0, 171 - 3.42 * math.log(volume) - 0.23 * complexity - 16.2 * math.log(lines_of_code))
        
        return min(maintainability, 100)
    
    def _aggregate_skills(self, skills: List[TechnicalSkill]) -> List[TechnicalSkill]:
        """Aggregate and deduplicate skills across files."""
        skill_map = {}
        
        for skill in skills:
            key = skill.name.lower()
            if key not in skill_map:
                skill_map[key] = {
                    'name': skill.name,
                    'category': skill.category,
                    'confidence': skill.confidence,
                    'evidence': skill.evidence.copy(),
                    'proficiency_level': skill.proficiency_level,
                    'frequency': 1
                }
            else:
                # Aggregate confidence (average)
                existing = skill_map[key]
                existing['confidence'] = (existing['confidence'] + skill.confidence) / 2
                existing['evidence'].extend(skill.evidence)
                existing['frequency'] += 1
                
                # Update proficiency level if higher
                proficiency_levels = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4}
                if proficiency_levels.get(skill.proficiency_level, 0) > proficiency_levels.get(existing['proficiency_level'], 0):
                    existing['proficiency_level'] = skill.proficiency_level
        
        # Convert back to TechnicalSkill objects
        aggregated = []
        for skill_data in skill_map.values():
            aggregated.append(TechnicalSkill(
                name=skill_data['name'],
                category=skill_data['category'],
                confidence=skill_data['confidence'],
                evidence=skill_data['evidence'][:5],  # Top 5 evidence pieces
                proficiency_level=skill_data['proficiency_level']
            ))
        
        # Sort by confidence
        aggregated.sort(key=lambda x: x.confidence, reverse=True)
        return aggregated
    
    def _aggregate_patterns(self, patterns: List[CodePattern]) -> List[CodePattern]:
        """Aggregate and deduplicate patterns across files."""
        pattern_map = {}
        
        for pattern in patterns:
            key = pattern.name.lower()
            if key not in pattern_map:
                pattern_map[key] = {
                    'name': pattern.name,
                    'type': pattern.type,
                    'description': pattern.description,
                    'locations': pattern.locations.copy(),
                    'frequency': pattern.frequency
                }
            else:
                existing = pattern_map[key]
                existing['locations'].extend(pattern.locations)
                existing['frequency'] += pattern.frequency
        
        # Convert back to CodePattern objects
        aggregated = []
        for pattern_data in pattern_map.values():
            aggregated.append(CodePattern(
                name=pattern_data['name'],
                type=pattern_data['type'],
                description=pattern_data['description'],
                locations=pattern_data['locations'][:10],  # Top 10 locations
                frequency=pattern_data['frequency']
            ))
        
        # Sort by frequency
        aggregated.sort(key=lambda x: x.frequency, reverse=True)
        return aggregated
    
    def _calculate_overall_scores(
        self, 
        metrics: Dict[str, Any], 
        skills: List[TechnicalSkill], 
        patterns: List[CodePattern]
    ) -> Dict[str, float]:
        """Calculate overall scores for different aspects."""
        
        # Technical diversity score
        categories = set(skill.category for skill in skills)
        diversity_score = min(len(categories) / 10, 1.0) * 100
        
        # Skill proficiency score
        proficiency_weights = {'beginner': 0.25, 'intermediate': 0.5, 'advanced': 0.75, 'expert': 1.0}
        proficiency_score = sum(
            skill.confidence * proficiency_weights.get(skill.proficiency_level, 0.5) 
            for skill in skills
        ) / len(skills) if skills else 0
        
        # Code quality score
        quality_score = min(
            (100 - metrics.get('avg_complexity', 0)) * 0.6 + 
            metrics.get('avg_maintainability', 0) * 0.4,
            100
        )
        
        # Best practices score
        best_practices = [p for p in patterns if p.type == 'best_practice']
        anti_patterns = [p for p in patterns if p.type == 'anti_pattern']
        practices_score = max(0, (len(best_practices) - len(anti_patterns)) / max(len(patterns), 1)) * 100
        
        return {
            'technical_diversity': diversity_score,
            'skill_proficiency': proficiency_score * 100,
            'code_quality': quality_score,
            'best_practices': practices_score,
            'overall_score': (diversity_score + proficiency_score * 100 + quality_score + practices_score) / 4
        }
    
    def _generate_recommendations(
        self, 
        skills: List[TechnicalSkill], 
        patterns: List[CodePattern], 
        scores: Dict[str, float]
    ) -> List[str]:
        """Generate personalized recommendations."""
        recommendations = []
        
        # Skill-based recommendations
        if scores['technical_diversity'] < 30:
            recommendations.append("Consider learning additional programming languages or frameworks to increase technical diversity.")
        
        if scores['skill_proficiency'] < 50:
            recommendations.append("Focus on deepening your current skills through practice and advanced concepts.")
        
        # Quality-based recommendations
        if scores['code_quality'] < 60:
            recommendations.append("Improve code quality by reducing complexity and adding documentation.")
        
        # Pattern-based recommendations
        anti_patterns = [p for p in patterns if p.type == 'anti_pattern']
        if anti_patterns:
            recommendations.append(f"Address {len(anti_patterns)} identified anti-patterns to improve code maintainability.")
        
        # Specific skill recommendations
        top_skills = [skill for skill in skills if skill.confidence > 0.8][:5]
        if top_skills:
            recommendations.append(f"Leverage your strengths in {', '.join([skill.name for skill in top_skills])} for career opportunities.")
        
        # Learning recommendations
        beginner_skills = [skill for skill in skills if skill.proficiency_level == 'beginner']
        if beginner_skills:
            recommendations.append(f"Consider advancing your {', '.join([skill.name for skill in beginner_skills[:3]])} skills to intermediate level.")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _skill_to_dict(self, skill: TechnicalSkill) -> Dict[str, Any]:
        """Convert TechnicalSkill to dictionary."""
        return {
            'name': skill.name,
            'category': skill.category,
            'confidence': skill.confidence,
            'evidence': skill.evidence,
            'proficiency_level': skill.proficiency_level
        }
    
    def _pattern_to_dict(self, pattern: CodePattern) -> Dict[str, Any]:
        """Convert CodePattern to dictionary."""
        return {
            'name': pattern.name,
            'type': pattern.type,
            'description': pattern.description,
            'locations': pattern.locations,
            'frequency': pattern.frequency
        }
    
    def _metric_to_dict(self, metric: CodeMetric) -> Dict[str, Any]:
        """Convert CodeMetric to dictionary."""
        return {
            'name': metric.name,
            'value': metric.value,
            'description': metric.description,
            'threshold': metric.threshold,
            'is_good': metric.is_good
        }


class GenericAnalyzer:
    """Generic code analyzer for unsupported languages."""
    
    def calculate_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate basic metrics for any text file."""
        lines = content.split('\n')
        total_lines = len(lines)
        code_lines = len([line for line in lines if line.strip()])
        empty_lines = total_lines - code_lines
        
        return {
            'lines_of_code': code_lines,
            'total_lines': total_lines,
            'empty_lines': empty_lines,
            'function_count': 0,
            'class_count': 0,
            'cyclomatic_complexity': 1.0,
            'maintainability_index': 70.0,
            'avg_function_length': 0,
            'comment_ratio': 0.0
        }
    
    def detect_patterns(self, content: str) -> List[CodePattern]:
        """Detect basic patterns."""
        return []
    
    def analyze_security(self, content: str) -> List[str]:
        """Analyze security issues."""
        return []
    
    def analyze_performance(self, content: str) -> List[str]:
        """Analyze performance issues."""
        return []


# Language-specific analyzers
class PythonAnalyzer(GenericAnalyzer):
    """Python-specific code analyzer."""
    
    def calculate_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate Python-specific metrics."""
        base_metrics = super().calculate_metrics(content)
        
        try:
            tree = ast.parse(content)
            
            # Count functions and classes
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node)
            
            # Calculate function lengths
            function_lengths = []
            for func in functions:
                if hasattr(func, 'end_lineno') and func.lineno:
                    length = func.end_lineno - func.lineno + 1
                    function_lengths.append(length)
            
            avg_function_length = sum(function_lengths) / len(function_lengths) if function_lengths else 0
            
            # Calculate cyclomatic complexity (simplified)
            complexity = 1
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
            
            # Count comments
            comment_lines = 0
            for line in content.split('\n'):
                if line.strip().startswith('#'):
                    comment_lines += 1
            
            comment_ratio = comment_lines / base_metrics['lines_of_code'] if base_metrics['lines_of_code'] > 0 else 0
            
            base_metrics.update({
                'function_count': len(functions),
                'class_count': len(classes),
                'cyclomatic_complexity': complexity,
                'avg_function_length': avg_function_length,
                'comment_ratio': comment_ratio
            })
            
        except SyntaxError:
            # Handle syntax errors gracefully
            pass
        
        return base_metrics
    
    def detect_patterns(self, content: str) -> List[CodePattern]:
        """Detect Python-specific patterns."""
        patterns = []
        
        # Design patterns
        if re.search(r'class\s+\w+\s*\([^)]*\):', content):
            patterns.append(CodePattern(
                name='inheritance',
                type='design_pattern',
                description='Class inheritance detected',
                locations=[],
                frequency=1
            ))
        
        if re.search(r'def\s+__.*__\s*\(', content):
            patterns.append(CodePattern(
                name='magic_methods',
                type='design_pattern',
                description='Python magic methods detected',
                locations=[],
                frequency=1
            ))
        
        # Best practices
        if re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', content):
            patterns.append(CodePattern(
                name='main_guard',
                type='best_practice',
                description='Main execution guard detected',
                locations=[],
                frequency=1
            ))
        
        # Anti-patterns
        if re.search(r'import\s+\*', content):
            patterns.append(CodePattern(
                name='wildcard_import',
                type='anti_pattern',
                description='Wildcard import detected',
                locations=[],
                frequency=1
            ))
        
        return patterns
    
    def analyze_security(self, content: str) -> List[str]:
        """Analyze Python security issues."""
        issues = []
        
        # Check for eval/exec
        if re.search(r'\b(eval|exec)\s*\(', content):
            issues.append("Use of eval/exec detected - potential security risk")
        
        # Check for hardcoded passwords
        if re.search(r'(password|pwd|secret)\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
            issues.append("Hardcoded password detected")
        
        # Check for SQL injection
        if re.search(r'execute\s*\(\s*["\'].*%.*["\']', content, re.IGNORECASE):
            issues.append("Potential SQL injection vulnerability")
        
        return issues
    
    def analyze_performance(self, content: str) -> List[str]:
        """Analyze Python performance issues."""
        issues = []
        
        # Check for inefficient string concatenation
        if re.search(r'\+\s*=\s*["\']', content):
            issues.append("Inefficient string concatenation detected")
        
        # Check for global variables in functions
        if re.search(r'global\s+\w+', content):
            issues.append("Use of global variables detected")
        
        return issues


class JavaScriptAnalyzer(GenericAnalyzer):
    """JavaScript-specific code analyzer."""
    
    def calculate_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate JavaScript-specific metrics."""
        base_metrics = super().calculate_metrics(content)
        
        # Count functions
        function_count = len(re.findall(r'function\s+\w+|const\s+\w+\s*=|\w+\s*:\s*function', content))
        
        # Count classes (ES6)
        class_count = len(re.findall(r'class\s+\w+', content))
        
        # Simplified complexity calculation
        complexity = 1
        complexity += len(re.findall(r'\b(if|else|for|while|catch|switch)\b', content))
        complexity += len(re.findall(r'&&|\|\|', content))
        
        # Count comments
        comment_lines = len(re.findall(r'//.*|/\*.*?\*/', content, re.MULTILINE | re.DOTALL))
        comment_ratio = comment_lines / base_metrics['lines_of_code'] if base_metrics['lines_of_code'] > 0 else 0
        
        base_metrics.update({
            'function_count': function_count,
            'class_count': class_count,
            'cyclomatic_complexity': complexity,
            'maintainability_index': 70.0,  # Placeholder
            'avg_function_length': 20.0,  # Placeholder
            'comment_ratio': comment_ratio
        })
        
        return base_metrics
    
    def detect_patterns(self, content: str) -> List[CodePattern]:
        """Detect JavaScript-specific patterns."""
        patterns = []
        
        # Framework detection
        if re.search(r'React|jsx|useState|useEffect', content):
            patterns.append(CodePattern(
                name='react',
                type='framework',
                description='React framework detected',
                locations=[],
                frequency=1
            ))
        
        if re.search(r'Vue|vue|\.vue', content):
            patterns.append(CodePattern(
                name='vue',
                type='framework',
                description='Vue framework detected',
                locations=[],
                frequency=1
            ))
        
        # Async patterns
        if re.search(r'async|await|Promise', content):
            patterns.append(CodePattern(
                name='async_programming',
                type='design_pattern',
                description='Async/await patterns detected',
                locations=[],
                frequency=1
            ))
        
        return patterns
    
    def analyze_security(self, content: str) -> List[str]:
        """Analyze JavaScript security issues."""
        issues = []
        
        # Check for eval
        if re.search(r'\beval\s*\(', content):
            issues.append("Use of eval detected - potential security risk")
        
        # Check for innerHTML
        if re.search(r'innerHTML\s*=', content):
            issues.append("Direct innerHTML assignment - potential XSS risk")
        
        return issues
    
    def analyze_performance(self, content: str) -> List[str]:
        """Analyze JavaScript performance issues."""
        issues = []
        
        # Check for DOM queries in loops
        if re.search(r'for.*\{.*getElementById', content, re.DOTALL):
            issues.append("DOM queries inside loops detected")
        
        return issues


# Placeholder analyzers for other languages
class TypeScriptAnalyzer(JavaScriptAnalyzer):
    pass

class JavaAnalyzer(GenericAnalyzer):
    pass

class CSharpAnalyzer(GenericAnalyzer):
    pass

class CppAnalyzer(GenericAnalyzer):
    pass

class GoAnalyzer(GenericAnalyzer):
    pass

class RustAnalyzer(GenericAnalyzer):
    pass
