"""GitHub client for repository analysis and skill extraction."""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import re
from pathlib import Path

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GitHubRepo:
    """GitHub repository information."""
    id: int
    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    languages: Dict[str, int]  # language -> bytes of code
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    size: int  # repository size in KB
    default_branch: str
    owner: Dict[str, Any]
    topics: List[str]
    license: Optional[Dict[str, Any]]
    is_private: bool


@dataclass
class GitHubFile:
    """GitHub file information."""
    name: str
    path: str
    type: str  # file, dir, symlink
    size: int
    content: Optional[str]  # Base64 encoded content
    sha: str
    download_url: Optional[str]


@dataclass
class GitHubCommit:
    """GitHub commit information."""
    sha: str
    message: str
    author: Dict[str, Any]
    committer: Dict[str, Any]
    date: datetime
    additions: int
    deletions: int
    changed_files: int


@dataclass
class CodeAnalysis:
    """Code analysis results."""
    file_path: str
    language: str
    lines_of_code: int
    complexity_score: float
    technical_skills: List[str]
    frameworks: List[str]
    patterns: List[str]
    quality_metrics: Dict[str, Any]


class GitHubClient:
    """Client for GitHub API integration with caching."""
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.base_url = "https://api.github.com"
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = timedelta(hours=1)
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = datetime.now()
        
        # File extensions for language detection
        self.language_extensions = {
            'python': ['.py'],
            'javascript': ['.js', '.jsx', '.mjs'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'csharp': ['.cs'],
            'cpp': ['.cpp', '.cxx', '.cc'],
            'c': ['.c'],
            'go': ['.go'],
            'rust': ['.rs'],
            'php': ['.php'],
            'ruby': ['.rb'],
            'swift': ['.swift'],
            'kotlin': ['.kt', '.kts'],
            'scala': ['.scala'],
            'html': ['.html', '.htm'],
            'css': ['.css', '.scss', '.sass', '.less'],
            'sql': ['.sql'],
            'shell': ['.sh', '.bash', '.zsh', '.fish'],
            'dockerfile': ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml'],
            'yaml': ['.yml', '.yaml'],
            'json': ['.json'],
            'markdown': ['.md', '.markdown'],
            'text': ['.txt'],
        }
        
        # Technical skills patterns
        self.skill_patterns = {
            'frameworks': {
                'react': r'react|React|jsx?|tsx?',
                'vue': r'vue|Vue|\.vue',
                'angular': r'angular|Angular|ng-',
                'django': r'django|Django',
                'flask': r'flask|Flask',
                'fastapi': r'fastapi|FastAPI',
                'spring': r'spring|Spring|@Spring',
                'express': r'express|Express|express\(\)',
                'rails': r'rails|Rails|Rails\.',
                'laravel': r'laravel|Laravel',
                'nextjs': r'next|Next|next\.js|Next\.js',
                'nuxtjs': r'nuxt|Nuxt|nuxt\.js|Nuxt\.js',
            },
            'databases': {
                'postgresql': r'postgresql|postgres|psycopg|pg_',
                'mysql': r'mysql|MySQL|pymysql|mysql2',
                'mongodb': r'mongodb|Mongo|pymongo|mongoose',
                'redis': r'redis|Redis|redis_',
                'sqlite': r'sqlite|SQLite|sqlite3',
                'elasticsearch': r'elasticsearch|ElasticSearch|elastic',
                'cassandra': r'cassandra|Cassandra',
            },
            'cloud': {
                'aws': r'aws|AWS|boto3|aws_',
                'azure': r'azure|Azure|azure_',
                'gcp': r'gcp|GCP|google\.cloud',
                'terraform': r'terraform|Terraform|\.tf',
                'kubernetes': r'kubernetes|k8s|k8s|kubectl',
                'docker': r'docker|Docker|dockerfile|docker-',
            },
            'testing': {
                'pytest': r'pytest|PyTest|@pytest',
                'jest': r'jest|Jest|describe\(|it\(',
                'mocha': r'mocha|Mocha|describe\(|it\(',
                'unittest': r'unittest|TestCase|setUp|tearDown',
                'junit': r'junit|JUnit|@Test',
                'selenium': r'selenium|Selenium|webdriver',
            },
            'tools': {
                'git': r'git|Git|\.git',
                'webpack': r'webpack|Webpack|webpack\.',
                'vite': r'vite|Vite|vite\.',
                'babel': r'babel|Babel|babel-',
                'eslint': r'eslint|ESLint|\.eslintrc',
                'prettier': r'prettier|Prettier|\.prettierrc',
                'jenkins': r'jenkins|Jenkins|Jenkinsfile',
                'github': r'github|GitHub|\.github',
                'gitlab': r'gitlab|GitLab|\.gitlab',
            }
        }
    
    async def get_repository(self, owner: str, repo: str) -> Optional[GitHubRepo]:
        """
        Get repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            GitHubRepo object or None
        """
        cache_key = f"repo:{owner}/{repo}"
        
        # Check cache
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for repository: {owner}/{repo}")
                return cached_result
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Get languages
                        languages = await self.get_repository_languages(owner, repo)
                        
                        repo_info = GitHubRepo(
                            id=data['id'],
                            name=data['name'],
                            full_name=data['full_name'],
                            description=data.get('description'),
                            language=data.get('language'),
                            languages=languages,
                            stargazers_count=data['stargazers_count'],
                            forks_count=data['forks_count'],
                            open_issues_count=data['open_issues_count'],
                            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')),
                            pushed_at=datetime.fromisoformat(data['pushed_at'].replace('Z', '+00:00')),
                            size=data['size'],
                            default_branch=data['default_branch'],
                            owner=data['owner'],
                            topics=data.get('topics', []),
                            license=data.get('license'),
                            is_private=data.get('private', False)
                        )
                        
                        # Cache result
                        self.cache[cache_key] = (repo_info, datetime.now())
                        logger.info(f"Retrieved repository: {owner}/{repo}")
                        return repo_info
                    else:
                        logger.error(f"GitHub API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting repository {owner}/{repo}: {e}")
            return None
    
    async def get_repository_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get repository language breakdown."""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/languages"
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {}
                        
        except Exception as e:
            logger.error(f"Error getting languages for {owner}/{repo}: {e}")
            return {}
    
    async def get_repository_contents(
        self, 
        owner: str, 
        repo: str, 
        path: str = "", 
        recursive: bool = False
    ) -> List[GitHubFile]:
        """
        Get repository contents.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: Path to get contents for
            recursive: Whether to get all files recursively
            
        Returns:
            List of GitHubFile objects
        """
        try:
            if recursive:
                return await self._get_all_files(owner, repo)
            else:
                return await self._get_directory_contents(owner, repo, path)
                
        except Exception as e:
            logger.error(f"Error getting contents for {owner}/{repo}/{path}: {e}")
            return []
    
    async def _get_directory_contents(self, owner: str, repo: str, path: str) -> List[GitHubFile]:
        """Get contents of a specific directory."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        headers = self._get_headers()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, list):
                        files = []
                        for item in data:
                            file_info = GitHubFile(
                                name=item['name'],
                                path=item['path'],
                                type=item['type'],
                                size=item.get('size', 0),
                                content=item.get('content'),
                                sha=item['sha'],
                                download_url=item.get('download_url')
                            )
                            files.append(file_info)
                        return files
                    else:
                        # Single file
                        file_info = GitHubFile(
                            name=data['name'],
                            path=data['path'],
                            type=data['type'],
                            size=data.get('size', 0),
                            content=data.get('content'),
                            sha=data['sha'],
                            download_url=data.get('download_url')
                        )
                        return [file_info]
                else:
                    return []
    
    async def _get_all_files(self, owner: str, repo: str) -> List[GitHubFile]:
        """Get all files in repository recursively."""
        all_files = []
        seen_paths = set()
        
        # Use GitHub API to get all files
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{owner}/{repo}?recursive=1"
        headers = self._get_headers()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data.get('tree', []):
                        if item['type'] == 'blob' and item['path'] not in seen_paths:
                            # Skip common non-code files
                            if self._should_analyze_file(item['path']):
                                file_info = GitHubFile(
                                    name=item['path'].split('/')[-1],
                                    path=item['path'],
                                    type=item['type'],
                                    size=item.get('size', 0),
                                    content=None,  # Don't fetch content yet
                                    sha=item['sha'],
                                    download_url=None
                                )
                                all_files.append(file_info)
                                seen_paths.add(item['path'])
        
        return all_files
    
    async def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """Get decoded file content."""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('content') and data.get('encoding') == 'base64':
                            import base64
                            return base64.b64decode(data['content']).decode('utf-8', errors='ignore')
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting file content {owner}/{repo}/{path}: {e}")
            return None
    
    async def get_commits(self, owner: str, repo: str, limit: int = 100) -> List[GitHubCommit]:
        """Get repository commits."""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/commits"
            headers = self._get_headers()
            params = {'per_page': min(limit, 100)}
            
            commits = []
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for commit_data in data:
                            commit = GitHubCommit(
                                sha=commit_data['sha'],
                                message=commit_data['commit']['message'],
                                author=commit_data['commit']['author'],
                                committer=commit_data['commit']['committer'],
                                date=datetime.fromisoformat(commit_data['commit']['author']['date'].replace('Z', '+00:00')),
                                additions=commit_data.get('stats', {}).get('additions', 0),
                                deletions=commit_data.get('stats', {}).get('deletions', 0),
                                changed_files=commit_data.get('stats', {}).get('total', 0)
                            )
                            commits.append(commit)
                    
                    return commits
                    
        except Exception as e:
            logger.error(f"Error getting commits for {owner}/{repo}: {e}")
            return []
    
    async def analyze_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Perform comprehensive repository analysis.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Starting repository analysis for {owner}/{repo}")
        start_time = datetime.now()
        
        try:
            # Get repository info
            repo_info = await self.get_repository(owner, repo)
            if not repo_info:
                raise ValueError(f"Repository {owner}/{repo} not found")
            
            # Get all files
            files = await self.get_repository_contents(owner, repo, recursive=True)
            
            # Analyze code files
            code_analyses = []
            total_loc = 0
            technical_skills = set()
            frameworks = set()
            tools = set()
            
            # Limit analysis to avoid timeouts
            max_files_to_analyze = 50
            analyzed_files = 0
            
            for file in files:
                if analyzed_files >= max_files_to_analyze:
                    break
                
                if self._should_analyze_file(file.path):
                    content = await self.get_file_content(owner, repo, file.path)
                    if content:
                        analysis = self._analyze_code_content(file.path, content)
                        code_analyses.append(analysis)
                        total_loc += analysis.lines_of_code
                        
                        # Collect skills and frameworks
                        technical_skills.update(analysis.technical_skills)
                        frameworks.update(analysis.frameworks)
                        tools.update(analysis.patterns)
                        
                        analyzed_files += 1
            
            # Get recent commits
            commits = await self.get_commits(owner, repo, limit=50)
            
            # Calculate collaboration metrics
            collaboration_metrics = self._calculate_collaboration_metrics(commits)
            
            # Calculate learning trajectory
            learning_trajectory = self._calculate_learning_trajectory(commits)
            
            # Calculate project complexity
            project_complexity = self._calculate_project_complexity(repo_info, code_analyses)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            results = {
                'repository': {
                    'name': repo_info.full_name,
                    'description': repo_info.description,
                    'language': repo_info.language,
                    'languages': repo_info.languages,
                    'stars': repo_info.stargazers_count,
                    'forks': repo_info.forks_count,
                    'open_issues': repo_info.open_issues_count,
                    'created_at': repo_info.created_at.isoformat(),
                    'updated_at': repo_info.updated_at.isoformat(),
                    'size_kb': repo_info.size,
                    'topics': repo_info.topics,
                    'is_private': repo_info.is_private
                },
                'code_analysis': {
                    'files_analyzed': len(code_analyses),
                    'total_lines_of_code': total_loc,
                    'technical_skills': list(technical_skills),
                    'frameworks': list(frameworks),
                    'tools': list(tools),
                    'languages_detected': list(set(analysis.language for analysis in code_analyses)),
                    'average_complexity': sum(analysis.complexity_score for analysis in code_analyses) / len(code_analyses) if code_analyses else 0,
                    'file_analyses': [self._analysis_to_dict(analysis) for analysis in code_analyses[:10]]  # Top 10 files
                },
                'collaboration': collaboration_metrics,
                'learning_trajectory': learning_trajectory,
                'project_complexity': project_complexity,
                'commit_activity': {
                    'total_commits': len(commits),
                    'recent_commits': len([c for c in commits if (datetime.now(timezone.utc) - c.date).days <= 30]),
                    'avg_commits_per_week': self._calculate_commits_per_week(commits),
                    'most_active_day': self._get_most_active_day(commits)
                },
                'processing_metadata': {
                    'processing_time_ms': processing_time,
                    'files_found': len(files),
                    'files_analyzed': len(code_analyses),
                    'analysis_date': datetime.now().isoformat()
                }
            }
            
            logger.info(f"Repository analysis completed for {owner}/{repo} in {processing_time:.2f}ms")
            return results
            
        except Exception as e:
            logger.error(f"Repository analysis failed for {owner}/{repo}: {e}")
            raise
    
    def _should_analyze_file(self, file_path: str) -> bool:
        """Determine if a file should be analyzed."""
        # Skip common non-code files and directories
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
            r'\.lock$',
            r'package-lock\.json',
            r'yarn\.lock',
            r'Gemfile\.lock'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, file_path, re.IGNORECASE):
                return False
        
        # Check if file has analyzable extension
        file_ext = Path(file_path).suffix.lower()
        for language, extensions in self.language_extensions.items():
            if file_ext in extensions:
                return True
        
        return False
    
    def _analyze_code_content(self, file_path: str, content: str) -> CodeAnalysis:
        """Analyze code content for skills and patterns."""
        language = self._detect_language(file_path)
        lines_of_code = len([line for line in content.split('\n') if line.strip()])
        
        # Calculate complexity (simplified)
        complexity_score = self._calculate_complexity(content, language)
        
        # Extract technical skills
        technical_skills = self._extract_technical_skills(content)
        
        # Extract frameworks
        frameworks = self._extract_frameworks(content)
        
        # Extract patterns
        patterns = self._extract_patterns(content)
        
        # Quality metrics
        quality_metrics = self._calculate_quality_metrics(content, language)
        
        return CodeAnalysis(
            file_path=file_path,
            language=language,
            lines_of_code=lines_of_code,
            complexity_score=complexity_score,
            technical_skills=technical_skills,
            frameworks=frameworks,
            patterns=patterns,
            quality_metrics=quality_metrics
        )
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path."""
        file_ext = Path(file_path).suffix.lower()
        
        for language, extensions in self.language_extensions.items():
            if file_ext in extensions:
                return language
        
        # Special cases
        if file_path.lower().endswith('dockerfile'):
            return 'dockerfile'
        elif file_path.lower().endswith(('.yml', '.yaml')):
            return 'yaml'
        elif file_path.lower().endswith(('.json', '.lock')):
            return 'json'
        elif file_path.lower().endswith(('.md', '.markdown')):
            return 'markdown'
        
        return 'text'
    
    def _calculate_complexity(self, content: str, language: str) -> float:
        """Calculate code complexity score (0-10)."""
        complexity = 1.0  # Base complexity
        
        # Count complexity indicators
        if language in ['python', 'javascript', 'typescript', 'java', 'csharp']:
            # Control structures
            complexity += content.count('if ') * 0.1
            complexity += content.count('for ') * 0.1
            complexity += content.count('while ') * 0.1
            complexity += content.count('def ') * 0.2
            complexity += content.count('class ') * 0.3
            complexity += content.count('try ') * 0.2
            complexity += content.count('except ') * 0.2
            complexity += content.count('catch ') * 0.2
            
        # Nested structures
        max_indent = 0
        for line in content.split('\n'):
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)
        
        complexity += max_indent * 0.05
        
        return min(complexity, 10.0)
    
    def _extract_technical_skills(self, content: str) -> List[str]:
        """Extract technical skills from code content."""
        skills = []
        
        # Common programming languages and libraries
        skill_patterns = {
            'python': r'import\s+\w+|from\s+\w+\s+import|def\s+\w+|class\s+\w+',
            'javascript': r'function\s+\w+|const\s+\w+|let\s+\w+|var\s+\w+|require\(|import\s+.*from',
            'react': r'React|jsx|tsx|useState|useEffect|ReactDOM',
            'vue': r'Vue|vue|\.vue|Vue\.component',
            'angular': r'angular|Angular|ng-|@Component|@Injectable',
            'nodejs': r'require\(|module\.exports|process\.|__dirname',
            'sql': r'SELECT|INSERT|UPDATE|DELETE|CREATE TABLE|ALTER TABLE',
            'html': r'<html|<div|<span|<p>|<h[1-6]>|<!DOCTYPE',
            'css': r'\.css|color:|background:|margin:|padding:|display:',
            'docker': r'FROM|RUN|CMD|EXPOSE|dockerfile',
            'git': r'git\s+|\.git|commit|push|pull|branch',
        }
        
        for skill, pattern in skill_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                skills.append(skill)
        
        return list(set(skills))
    
    def _extract_frameworks(self, content: str) -> List[str]:
        """Extract frameworks from code content."""
        frameworks = []
        
        for category, patterns in self.skill_patterns.items():
            if category == 'frameworks':
                for framework, pattern in patterns.items():
                    if re.search(pattern, content, re.IGNORECASE):
                        frameworks.append(framework)
        
        return frameworks
    
    def _extract_patterns(self, content: str) -> List[str]:
        """Extract coding patterns and tools."""
        patterns = []
        
        # Extract from all categories except frameworks
        for category, category_patterns in self.skill_patterns.items():
            if category != 'frameworks':
                for pattern_name, pattern in category_patterns.items():
                    if re.search(pattern, content, re.IGNORECASE):
                        patterns.append(pattern_name)
        
        return patterns
    
    def _calculate_quality_metrics(self, content: str, language: str) -> Dict[str, Any]:
        """Calculate code quality metrics."""
        lines = content.split('\n')
        total_lines = len(lines)
        code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        empty_lines = total_lines - code_lines - comment_lines
        
        # Function/method count
        function_count = 0
        if language in ['python']:
            function_count = len(re.findall(r'def\s+\w+', content))
        elif language in ['javascript', 'typescript']:
            function_count = len(re.findall(r'function\s+\w+|const\s+\w+\s*=|\w+\s*:\s*function', content))
        elif language in ['java', 'csharp']:
            function_count = len(re.findall(r'(public|private|protected)?\s*(static)?\s*\w+\s+\w+\s*\(', content))
        
        return {
            'total_lines': total_lines,
            'code_lines': code_lines,
            'comment_lines': comment_lines,
            'empty_lines': empty_lines,
            'function_count': function_count,
            'avg_function_length': code_lines / function_count if function_count > 0 else 0,
            'comment_ratio': comment_lines / code_lines if code_lines > 0 else 0
        }
    
    def _calculate_collaboration_metrics(self, commits: List[GitHubCommit]) -> Dict[str, Any]:
        """Calculate collaboration metrics from commits."""
        if not commits:
            return {}
        
        # Author contributions
        author_contributions = {}
        for commit in commits:
            author = commit.author.get('name', 'Unknown')
            if author not in author_contributions:
                author_contributions[author] = {
                    'commits': 0,
                    'additions': 0,
                    'deletions': 0
                }
            
            author_contributions[author]['commits'] += 1
            author_contributions[author]['additions'] += commit.additions
            author_contributions[author]['deletions'] += commit.deletions
        
        # Calculate collaboration indicators
        total_authors = len(author_contributions)
        main_author_contributions = max(author_contributions.values(), key=lambda x: x['commits'])['commits']
        collaboration_ratio = main_author_contributions / len(commits) if commits else 0
        
        return {
            'total_authors': total_authors,
            'author_contributions': author_contributions,
            'collaboration_ratio': collaboration_ratio,
            'is_collaborative': total_authors > 1 and collaboration_ratio < 0.8
        }
    
    def _calculate_learning_trajectory(self, commits: List[GitHubCommit]) -> List[Dict[str, Any]]:
        """Calculate learning trajectory from commit history."""
        if len(commits) < 2:
            return []
        
        trajectory = []
        
        # Group commits by month
        monthly_commits = {}
        for commit in commits:
            month_key = commit.date.strftime('%Y-%m')
            if month_key not in monthly_commits:
                monthly_commits[month_key] = []
            monthly_commits[month_key].append(commit)
        
        # Calculate metrics for each month
        for month in sorted(monthly_commits.keys()):
            month_commits = monthly_commits[month]
            total_additions = sum(c.additions for c in month_commits)
            total_deletions = sum(c.deletions for c in month_commits)
            avg_commit_size = (total_additions + total_deletions) / len(month_commits)
            
            trajectory.append({
                'month': month,
                'commits': len(month_commits),
                'total_additions': total_additions,
                'total_deletions': total_deletions,
                'avg_commit_size': avg_commit_size,
                'complexity_trend': 'increasing' if avg_commit_size > 100 else 'stable'
            })
        
        return trajectory
    
    def _calculate_project_complexity(self, repo_info: GitHubRepo, analyses: List[CodeAnalysis]) -> float:
        """Calculate overall project complexity score (0-10)."""
        if not analyses:
            return 1.0
        
        # Base complexity from code analyses
        avg_complexity = sum(analysis.complexity_score for analysis in analyses) / len(analyses)
        
        # Adjust based on repository metrics
        size_factor = min(repo_info.size / 1000, 2.0)  # Size factor (max 2.0)
        language_factor = len(repo_info.languages) * 0.1  # Multiple languages
        
        # Adjust for collaboration
        collaboration_factor = 1.0
        if repo_info.forks_count > 10:
            collaboration_factor += 0.5
        if repo_info.open_issues_count > 50:
            collaboration_factor += 0.3
        
        complexity = avg_complexity * (1 + size_factor + language_factor + collaboration_factor)
        
        return min(complexity, 10.0)
    
    def _calculate_commits_per_week(self, commits: List[GitHubCommit]) -> float:
        """Calculate average commits per week."""
        if not commits:
            return 0.0
        
        # Get date range
        dates = [c.date for c in commits]
        date_range = (max(dates) - min(dates)).days
        
        if date_range < 7:
            return len(commits)
        
        weeks = date_range / 7
        return len(commits) / weeks
    
    def _get_most_active_day(self, commits: List[GitHubCommit]) -> str:
        """Get most active day of week."""
        if not commits:
            return "None"
        
        day_counts = {}
        for commit in commits:
            day = commit.date.strftime('%A')
            day_counts[day] = day_counts.get(day, 0) + 1
        
        return max(day_counts, key=day_counts.get)
    
    def _analysis_to_dict(self, analysis: CodeAnalysis) -> Dict[str, Any]:
        """Convert CodeAnalysis to dictionary."""
        return {
            'file_path': analysis.file_path,
            'language': analysis.language,
            'lines_of_code': analysis.lines_of_code,
            'complexity_score': analysis.complexity_score,
            'technical_skills': analysis.technical_skills,
            'frameworks': analysis.frameworks,
            'patterns': analysis.patterns,
            'quality_metrics': analysis.quality_metrics
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for GitHub API requests."""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'KASH-Platform/1.0'
        }
        
        if self.access_token:
            headers['Authorization'] = f'token {self.access_token}'
        
        return headers
    
    def clear_cache(self):
        """Clear the in-memory cache."""
        self.cache.clear()
        logger.info("GitHub client cache cleared")
    
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
