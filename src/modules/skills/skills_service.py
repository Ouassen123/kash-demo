"""Skills module service for GitHub integration and code analysis."""

import asyncio
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import json

from src.core.database import get_db
from src.core.logging import get_logger
from src.models.user import User
from src.models.assessment import UserAssessment, SkillsAssessment
from src.modules.skills.code_analyzer import CodeAnalyzer
from src.modules.skills.code_analysis import (
    AnalysisContext,
    AnalysisResult,
    CodeAnalysisEngine,
    CodeAnalysisStore,
    SeverityLevel,
    StoredAnalysis,
)
from src.modules.skills.code_analysis.context import RepositoryInput
from src.modules.skills.github.models import RepositorySnapshot
from src.integration.github_client import GitHubClient
from src.modules.skills.evaluation import (
    MiniProjectEvaluationManager,
    MiniProjectSubmission,
    SubmissionArtifact,
)
from src.modules.skills.evaluation.dashboard import MiniProjectDashboard
from src.modules.skills.github import GitHubSyncManager, GitHubSyncStore, SubmissionSyncResult
from src.modules.skills.github.link_registry import LearnerRepoLink
from src.modules.skills.github.sync_store import SyncLogEntry

logger = get_logger(__name__)

_github_sync_manager = GitHubSyncManager()
_github_sync_store = GitHubSyncStore()
_code_analysis_engine = CodeAnalysisEngine()
_code_analysis_store = CodeAnalysisStore()


class SkillsService:
    """Service for skills domain operations including GitHub analysis and code evaluation."""
    
    def __init__(self, db: Session):
        self.db = db
        self.code_analyzer = CodeAnalyzer()
        self.github_client = GitHubClient()
        self.mini_project_manager = MiniProjectEvaluationManager()
        self.mini_project_dashboard = MiniProjectDashboard(self.mini_project_manager)
        self.github_sync_manager = _github_sync_manager
        self.github_sync_store = _github_sync_store
        self.code_analysis_engine = _code_analysis_engine
        self.code_analysis_store = _code_analysis_store
    
    async def analyze_github_repository(
        self, 
        user_id: str, 
        owner: str, 
        repo: str,
        github_token: Optional[str] = None
    ) -> UserAssessment:
        """
        Analyze GitHub repository for skills assessment.
        
        Args:
            user_id: User UUID
            owner: Repository owner
            repo: Repository name
            github_token: Optional GitHub access token
            
        Returns:
            UserAssessment with complete analysis results
        """
        logger.info(f"Starting GitHub repository analysis for {owner}/{repo}")
        start_time = datetime.now()
        
        try:
            # Initialize GitHub client with token if provided
            if github_token:
                self.github_client = GitHubClient(github_token)
            
            # Analyze repository
            repo_analysis = await self.github_client.analyze_repository(owner, repo)
            
            # Extract code files for detailed analysis
            files = await self.github_client.get_repository_contents(owner, repo, recursive=True)
            code_files = []
            
            # Limit files to analyze to avoid timeouts
            max_files = 50
            analyzed_count = 0
            
            for file in files:
                if analyzed_count >= max_files:
                    break
                
                if self.github_client._should_analyze_file(file.path):
                    content = await self.github_client.get_file_content(owner, repo, file.path)
                    if content:
                        code_files.append({
                            'path': file.path,
                            'content': content
                        })
                        analyzed_count += 1
            
            # Perform detailed code analysis
            if code_files:
                code_analysis = self.code_analyzer.analyze_repository(code_files)
            else:
                code_analysis = {
                    'summary': {'total_files_analyzed': 0},
                    'technical_skills': [],
                    'overall_scores': {'overall_score': 0}
                }
            
            # Calculate skills scores
            skills_scores = self._calculate_skills_scores(repo_analysis, code_analysis)
            
            # Create user assessment record
            assessment = UserAssessment(
                id=uuid.uuid4(),
                user_id=user_id,
                assessment_type='skills',
                assessment_name=f'GitHub Repository Analysis - {owner}/{repo}',
                assessment_version='1.0',
                status='completed',
                raw_score=skills_scores['raw_score'],
                normalized_score=skills_scores['normalized_score'],
                confidence_score=skills_scores['confidence_score'],
                input_data={
                    'source_type': 'github',
                    'source_url': f'https://github.com/{owner}/{repo}',
                    'repository_info': repo_analysis.get('repository', {}),
                    'files_analyzed': len(code_files),
                    'github_token_provided': bool(github_token)
                },
                result_data={
                    'repository_analysis': repo_analysis,
                    'code_analysis': code_analysis,
                    'skills_scores': skills_scores
                },
                created_at=datetime.now(),
                started_at=datetime.now(),
                completed_at=datetime.now()
            )
            
            self.db.add(assessment)
            self.db.flush()  # Get the assessment ID
            
            # Create skills-specific assessment record
            skills_assessment = SkillsAssessment(
                id=uuid.uuid4(),
                assessment_id=assessment.id,
                source_type='github',
                source_url=f'https://github.com/{owner}/{repo}',
                source_metadata={
                    'owner': owner,
                    'repo': repo,
                    'full_name': repo_analysis.get('repository', {}).get('full_name', f'{owner}/{repo}'),
                    'default_branch': repo_analysis.get('repository', {}).get('default_branch', 'main'),
                    'languages': repo_analysis.get('repository', {}).get('languages', {}),
                    'stars': repo_analysis.get('repository', {}).get('stars', 0),
                    'forks': repo_analysis.get('repository', {}).get('forks', 0)
                },
                programming_languages=repo_analysis.get('code_analysis', {}).get('languages_detected', []),
                code_quality_metrics=code_analysis.get('metrics', {}),
                technical_skills=code_analysis.get('technical_skills', []),
                project_complexity=repo_analysis.get('project_complexity', 0),
                collaboration_indicators=repo_analysis.get('collaboration', {}),
                learning_trajectory=repo_analysis.get('learning_trajectory', []),
                analyzer_version='1.0',
                analysis_date=datetime.now()
            )
            
            self.db.add(skills_assessment)
            self.db.commit()
            
            logger.info(f"GitHub repository analysis completed for {owner}/{repo} in {(datetime.now() - start_time).total_seconds():.2f}s")
            return assessment
            
        except Exception as e:
            logger.error(f"GitHub repository analysis failed for {owner}/{repo}: {e}")
            self.db.rollback()
            raise

    async def evaluate_mini_project_submission(
        self,
        learner_id: str,
        template_id: str,
        artifacts: List[Dict[str, Any]],
        telemetry: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate a mini-project submission using the Skills evaluation pipeline."""

        submission = MiniProjectSubmission(
            submission_id=str(uuid.uuid4()),
            learner_id=learner_id,
            template_id=template_id,
            artifacts=[
                SubmissionArtifact(
                    path=item.get("path", ""),
                    artifact_type=item.get("artifact_type", "code"),
                    metadata=item.get("metadata", {}),
                    content_hash=item.get("content_hash"),
                    size_bytes=item.get("size_bytes"),
                )
                for item in artifacts
            ],
            telemetry=telemetry or {},
            notes=notes,
        )

        return self.mini_project_manager.process_submission(submission)

    def get_mini_project_dashboard_overview(self, limit: int = 10) -> Dict[str, Any]:
        """Return summary for Skills dashboards."""
        return self.mini_project_dashboard.overview(limit)

    def get_mini_project_submission_report(self, submission_id: str) -> Dict[str, Any]:
        """Return a single submission report for reviewers."""
        return self.mini_project_dashboard.submission_detail(submission_id)

    def get_mini_project_history(self, learner_id: str, limit: int = 5) -> Dict[str, Any]:
        """Return learner-specific evaluation history."""
        return self.mini_project_dashboard.learner_history(learner_id, limit)

    def register_github_link(
        self,
        learner_id: str,
        repository_full_name: str,
        project_id: Optional[str] = None,
        github_handle: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Register or update a learner→GitHub repository link."""

        entry = self.github_sync_manager.link_registry.register_link(
            learner_id,
            repository_full_name,
            project_id=project_id,
            github_handle=github_handle,
            metadata=metadata or {},
        )
        return self._serialize_link(entry)

    def get_github_links(self, learner_id: str) -> List[Dict[str, Any]]:
        """List the learner's registered GitHub repository links."""

        links = self.github_sync_manager.link_registry.get_links(learner_id)
        return [self._serialize_link(link) for link in links]

    async def sync_github_submission(
        self,
        learner_id: str,
        submission_id: str,
        template_id: str,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Trigger a GitHub submission sync and record it for auditing."""

        metadata_payload = dict(metadata) if metadata else {}
        result = await self.github_sync_manager.sync_submission_by_project(
            learner_id=learner_id,
            submission_id=submission_id,
            template_id=template_id,
            project_id=project_id,
            metadata=metadata_payload,
        )
        if result.repository:
            await self._run_code_analysis_from_repository(
                submission_id=submission_id,
                learner_id=learner_id,
                template_id=template_id,
                repo_snapshot=result.repository,
            )
        self.github_sync_store.record_sync(
            learner_id=learner_id,
            submission_id=submission_id,
            template_id=template_id,
            project_id=project_id,
            metadata=metadata_payload,
            result=result,
        )
        return self._serialize_sync_result(result)

    def get_latest_github_sync(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Return the latest sync log for a submission."""

        entry = self.github_sync_store.get_latest_by_submission(submission_id)
        if not entry:
            return None
        return self._serialize_sync_log_entry(entry)

    def list_github_sync_history(self, learner_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Return most recent GitHub sync logs for a learner."""

        history = self.github_sync_store.list_by_learner(learner_id, limit)
        return [self._serialize_sync_log_entry(entry) for entry in history]

    async def analyze_code_upload(
        self, 
        user_id: str, 
        files: List[Dict[str, str]],
        project_name: str = "Uploaded Project"
    ) -> UserAssessment:
        """
        Analyze uploaded code files.
        
        Args:
            user_id: User UUID
            files: List of file dictionaries with 'path' and 'content' keys
            project_name: Name for the project
            
        Returns:
            UserAssessment with complete analysis results
        """
        logger.info(f"Starting code upload analysis for {len(files)} files")
        start_time = datetime.now()
        
        try:
            # Perform code analysis
            code_analysis = self.code_analyzer.analyze_repository(files)
            await self._run_code_analysis_from_files(
                submission_id=str(uuid.uuid4()),
                learner_id=user_id,
                template_id="uploaded-code",
                files=files,
            )
            
            # Calculate skills scores
            skills_scores = self._calculate_skills_scores_from_code_analysis(code_analysis)
            
            # Create user assessment record
            assessment = UserAssessment(
                id=uuid.uuid4(),
                user_id=user_id,
                assessment_type='skills',
                assessment_name=f'Code Analysis - {project_name}',
                assessment_version='1.0',
                status='completed',
                raw_score=skills_scores['raw_score'],
                normalized_score=skills_scores['normalized_score'],
                confidence_score=skills_scores['confidence_score'],
                input_data={
                    'source_type': 'upload',
                    'project_name': project_name,
                    'files_count': len(files),
                    'file_paths': [file.get('path', '') for file in files]
                },
                result_data={
                    'code_analysis': code_analysis,
                    'skills_scores': skills_scores
                },
                created_at=datetime.now(),
                started_at=datetime.now(),
                completed_at=datetime.now()
            )
            
            self.db.add(assessment)
            self.db.flush()  # Get the assessment ID
            
            # Create skills-specific assessment record
            skills_assessment = SkillsAssessment(
                id=uuid.uuid4(),
                assessment_id=assessment.id,
                source_type='upload',
                source_url=None,
                source_metadata={
                    'project_name': project_name,
                    'files_count': len(files),
                    'total_lines': code_analysis.get('metrics', {}).get('total_lines', 0)
                },
                programming_languages=code_analysis.get('summary', {}).get('language_distribution', {}),
                code_quality_metrics=code_analysis.get('metrics', {}),
                technical_skills=code_analysis.get('technical_skills', []),
                project_complexity=code_analysis.get('overall_scores', {}).get('overall_score', 0),
                collaboration_indicators={},
                learning_trajectory=[],
                analyzer_version='1.0',
                analysis_date=datetime.now()
            )
            
            self.db.add(skills_assessment)
            self.db.commit()
            
            logger.info(f"Code upload analysis completed in {(datetime.now() - start_time).total_seconds():.2f}s")
            return assessment
            
        except Exception as e:
            logger.error(f"Code upload analysis failed: {e}")
            self.db.rollback()
            raise

    async def _run_code_analysis_from_files(
        self,
        submission_id: str,
        learner_id: str,
        template_id: str,
        files: List[Dict[str, str]],
    ) -> None:
        repo_input = RepositoryInput(
            submission_id=submission_id,
            learner_id=learner_id,
            template_id=template_id,
            root_path=Path("."),
            files=[],
            inline_files=files,
        )
        result = await self.code_analysis_engine.analyze(repo_input)
        self.code_analysis_store.save(
            StoredAnalysis(
                submission_id=submission_id,
                learner_id=learner_id,
                template_id=template_id,
                result=result,
            )
        )

    async def _run_code_analysis_from_repository(
        self,
        submission_id: str,
        learner_id: str,
        template_id: str,
        repo_snapshot: RepositorySnapshot,
    ) -> None:
        # Phase 1: Repository Hydration - Get real repo path from GitHubSyncManager
        local_repo_path = self.github_sync_manager.get_local_repo_path(submission_id)
        
        if not local_repo_path:
            logger.warning(f"No local repository path found for submission {submission_id}")
            return
        
        # Get the analysis profile from the template (default to "standard" if not specified)
        analysis_profile = "standard"  # TODO: Get from template
        
        # Phase 1: Build RepositoryInput with real files and commit SHA
        repo_input = RepositoryInput(
            submission_id=submission_id,
            learner_id=learner_id,
            template_id=template_id,
            root_path=local_repo_path,
            files=list(local_repo_path.glob("**/*")),  # Get all files in the repo
            analysis_profile=analysis_profile,
            commit_sha=repo_snapshot.commit_sha,
            metadata={
                "repo_name": repo_snapshot.name,
                "repo_owner": repo_snapshot.owner,
                "default_branch": repo_snapshot.default_branch,
                "languages": repo_snapshot.languages,
                "reliability": repo_snapshot.reliability.attribution_confidence,
            },
        )
        
        # Run the analysis
        result = await self.code_analysis_engine.analyze(repo_input)
        
        # Phase 2: Persist structured analysis artifacts
        await self._persist_analysis_artifacts(
            submission_id=submission_id,
            learner_id=learner_id,
            template_id=template_id,
            result=result,
            repo_snapshot=repo_snapshot,
        )
        
        # Phase 5: Emit telemetry event
        await self._emit_analysis_telemetry(
            submission_id=submission_id,
            learner_id=learner_id,
            template_id=template_id,
            result=result,
            repo_snapshot=repo_snapshot,
        )
        
        # Also store in memory for quick access
        self.code_analysis_store.save(
            StoredAnalysis(
                submission_id=submission_id,
                learner_id=learner_id,
                template_id=template_id,
                result=result,
            )
        )
    
    async def _persist_analysis_artifacts(
        self,
        submission_id: str,
        learner_id: str,
        template_id: str,
        result: "AnalysisResult",
        repo_snapshot: RepositorySnapshot,
    ) -> None:
        """
        Phase 2: Persist structured analysis artifacts to DATA_DIR/skills/code_analysis/
        
        Creates versioned snapshots if commit changes, never overwrites previous runs.
        """
        from src.core.config import DATA_DIR
        import json
        from datetime import datetime
        
        # Create analysis directory structure
        analysis_dir = DATA_DIR / "skills" / "code_analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename with submission ID and commit SHA for versioning
        commit_suffix = f"_{repo_snapshot.commit_sha[:8]}" if repo_snapshot.commit_sha else ""
        filename = f"{submission_id}{commit_suffix}.json"
        artifact_path = analysis_dir / filename
        
        # Build structured analysis artifact
        artifact = {
            "submission_id": submission_id,
            "learner_id": learner_id,
            "template_id": template_id,
            "analysis_profile": result.analysis_profile,
            "analyzed_at": result.analyzed_at.isoformat() if result.analyzed_at else datetime.utcnow().isoformat(),
            "commit_sha": repo_snapshot.commit_sha,
            "repository": {
                "name": repo_snapshot.name,
                "owner": repo_snapshot.owner,
                "default_branch": repo_snapshot.default_branch,
                "languages": repo_snapshot.languages,
                "language_summary": repo_snapshot.language_summary,
                "reliability": repo_snapshot.reliability.attribution_confidence,
            },
            "overall_score": result.overall_score,
            "automated_score": result.overall_score,  # Same until overrides are applied
            "adjusted_score": result.overall_score,  # Same until overrides are applied
            "grade": self._score_to_grade(result.overall_score),
            "confidence": result.confidence,
            "severity_buckets": {
                "critical": len([f for report in result.analyzer_reports for f in report.findings if f.severity == SeverityLevel.CRITICAL]),
                "high": len([f for report in result.analyzer_reports for f in report.findings if f.severity == SeverityLevel.HIGH]),
                "medium": len([f for report in result.analyzer_reports for f in report.findings if f.severity == SeverityLevel.MEDIUM]),
                "low": len([f for report in result.analyzer_reports for f in report.findings if f.severity == SeverityLevel.LOW]),
                "info": len([f for report in result.analyzer_reports for f in report.findings if f.severity == SeverityLevel.INFO]),
            },
            "findings": [
                {
                    "analyzer": report.analyzer_name,
                    "analyzer_version": report.analyzer_version,
                    "execution_time_ms": report.execution_time_ms,
                    "findings": [
                        {
                            "rule_id": f.rule_id,
                            "message": f.message,
                            "file_path": str(f.file_path),
                            "line_number": f.line_number,
                            "severity": f.severity.value,
                            "category": f.category,
                            "score_impact": f.score_impact,
                            "metadata": f.metadata,
                        }
                        for f in report.findings
                    ],
                }
                for report in result.analyzer_reports
            ],
            "overrides": [],  # TODO: Implement reviewer overrides
            "summary": result.summary,
        }
        
        # Write artifact to file (atomic write)
        temp_path = artifact_path.with_suffix(".tmp")
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(artifact, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_path.rename(artifact_path)
            logger.info(f"Persisted analysis artifact: {artifact_path}")
            
        except Exception as e:
            logger.error(f"Failed to persist analysis artifact for {submission_id}: {e}")
            if temp_path.exists():
                temp_path.unlink()
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    async def get_analysis_artifacts(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """
        Phase 3: Get analysis artifacts for a submission.
        
        Args:
            submission_id: The submission ID to get artifacts for
            
        Returns:
            Analysis artifact data or None if not found
        """
        from src.core.config import DATA_DIR
        import json
        
        analysis_dir = DATA_DIR / "skills" / "code_analysis"
        analysis_files = list(analysis_dir.glob(f"{submission_id}*.json"))
        
        if not analysis_files:
            return None
        
        # Get the most recent analysis file
        latest_file = max(analysis_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load analysis artifact for {submission_id}: {e}")
            return None
    
    async def apply_reviewer_override(
        self,
        submission_id: str,
        reviewer_id: str,
        score_delta: float,
        justification: str,
    ) -> Dict[str, Any]:
        """
        Phase 4: Apply reviewer override to analysis results.
        
        Args:
            submission_id: The submission ID to apply override to
            reviewer_id: The ID of the reviewer applying the override
            score_delta: The score adjustment (can be positive or negative)
            justification: Reason for the override
            
        Returns:
            Updated analysis artifact with override applied
        """
        from src.core.config import DATA_DIR
        import json
        from datetime import datetime
        
        # Get existing analysis
        analysis_data = await self.get_analysis_artifacts(submission_id)
        if not analysis_data:
            raise ValueError(f"No analysis found for submission {submission_id}")
        
        # Apply override logic: adjusted_score = automated_score + sum(score_delta)
        current_adjusted = analysis_data.get("adjusted_score", analysis_data["automated_score"])
        new_adjusted = current_adjusted + score_delta
        
        # Cap between 0-100
        new_adjusted = max(0, min(100, new_adjusted))
        
        # Create override record
        override_record = {
            "override_id": str(uuid.uuid4()),
            "reviewer_id": reviewer_id,
            "score_delta": score_delta,
            "justification": justification,
            "applied_at": datetime.utcnow().isoformat(),
            "previous_adjusted_score": current_adjusted,
            "new_adjusted_score": new_adjusted,
        }
        
        # Add to overrides list
        if "overrides" not in analysis_data:
            analysis_data["overrides"] = []
        analysis_data["overrides"].append(override_record)
        
        # Update adjusted score and grade
        analysis_data["adjusted_score"] = new_adjusted
        analysis_data["grade"] = self._score_to_grade(new_adjusted)
        
        # Persist updated artifact
        await self._persist_analysis_artifacts_update(analysis_data)
        
        # Update in-memory store
        stored_analysis = self.code_analysis_store.get(submission_id)
        if stored_analysis:
            # TODO: Update the AnalysisResult object with override
            pass
        
        logger.info(f"Applied reviewer override for submission {submission_id}: {score_delta} points by {reviewer_id}")
        
        return {
            "submission_id": submission_id,
            "override": override_record,
            "updated_scores": {
                "automated_score": analysis_data["automated_score"],
                "adjusted_score": new_adjusted,
                "grade": analysis_data["grade"],
            },
        }
    
    async def _persist_analysis_artifacts_update(self, analysis_data: Dict[str, Any]) -> None:
        """
        Helper method to persist updated analysis artifacts.
        
        Args:
            analysis_data: The updated analysis data to persist
        """
        from src.core.config import DATA_DIR
        import json
        
        analysis_dir = DATA_DIR / "skills" / "code_analysis"
        submission_id = analysis_data["submission_id"]
        commit_sha = analysis_data.get("commit_sha")
        
        # Create filename with submission ID and commit SHA for versioning
        commit_suffix = f"_{commit_sha[:8]}" if commit_sha else ""
        filename = f"{submission_id}{commit_suffix}.json"
        artifact_path = analysis_dir / filename
        
        # Write artifact to file (atomic write)
        temp_path = artifact_path.with_suffix(".tmp")
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_path.rename(artifact_path)
            logger.info(f"Updated analysis artifact: {artifact_path}")
            
        except Exception as e:
            logger.error(f"Failed to update analysis artifact for {submission_id}: {e}")
            if temp_path.exists():
                temp_path.unlink()
    
    async def _emit_analysis_telemetry(
        self,
        submission_id: str,
        learner_id: str,
        template_id: str,
        result: "AnalysisResult",
        repo_snapshot: RepositorySnapshot,
    ) -> None:
        """
        Phase 5: Emit telemetry event for code analysis completion.
        
        Args:
            submission_id: The submission ID
            learner_id: The learner ID
            template_id: The template ID
            result: The analysis result
            repo_snapshot: The repository snapshot
        """
        from datetime import datetime
        
        # Count findings by severity
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }
        
        total_findings = 0
        analyzer_count = len(result.analyzer_reports)
        
        for report in result.analyzer_reports:
            for finding in report.findings:
                severity_counts[finding.severity.value] += 1
                total_findings += 1
        
        # Build telemetry payload
        telemetry_event = {
            "event_type": "skills.code_analysis.completed",
            "timestamp": datetime.utcnow().isoformat(),
            "submission_id": submission_id,
            "learner_id": learner_id,
            "template_id": template_id,
            "analysis_profile": result.analysis_profile,
            "repository": {
                "name": repo_snapshot.name,
                "owner": repo_snapshot.owner,
                "languages": repo_snapshot.languages,
                "commit_sha": repo_snapshot.commit_sha,
                "reliability_score": repo_snapshot.reliability.attribution_confidence,
            },
            "analysis_summary": {
                "overall_score": result.overall_score,
                "confidence": result.confidence,
                "total_findings": total_findings,
                "severity_breakdown": severity_counts,
                "analyzer_count": analyzer_count,
                "execution_time_ms": sum(report.execution_time_ms for report in result.analyzer_reports),
            },
            "findings_by_category": self._categorize_findings(result.analyzer_reports),
        }
        
        # Log telemetry event (in a real implementation, this would go to a telemetry system)
        logger.info(f"TELEMETRY: {json.dumps(telemetry_event)}")
        
        # TODO: Send to actual telemetry system (e.g., OpenTelemetry, custom events)
    
    def _categorize_findings(self, analyzer_reports: List) -> Dict[str, int]:
        """Categorize findings by type for telemetry."""
        categories = {}
        
        for report in analyzer_reports:
            for finding in report.findings:
                category = finding.category or "unknown"
                categories[category] = categories.get(category, 0) + 1
        
        return categories
    
    async def get_skills_assessment(
        self, 
        assessment_id: str, 
        user_id: str
    ) -> Optional[UserAssessment]:
        """
        Get skills assessment by ID for a specific user.
        
        Args:
            assessment_id: Assessment UUID
            user_id: User UUID
            
        Returns:
            UserAssessment or None if not found
        """
        assessment = self.db.query(UserAssessment).filter(
            UserAssessment.id == assessment_id,
            UserAssessment.user_id == user_id,
            UserAssessment.assessment_type == 'skills'
        ).first()
        
        if assessment:
            # Load related skills assessment
            skills_assessment = self.db.query(SkillsAssessment).filter(
                SkillsAssessment.assessment_id == assessment.id
            ).first()
            
            if skills_assessment:
                # Add detailed data to result
                assessment.result_data.update({
                    'skills_assessment': {
                        'source_type': skills_assessment.source_type,
                        'source_url': skills_assessment.source_url,
                        'source_metadata': skills_assessment.source_metadata,
                        'programming_languages': skills_assessment.programming_languages,
                        'code_quality_metrics': skills_assessment.code_quality_metrics,
                        'technical_skills': skills_assessment.technical_skills,
                        'project_complexity': skills_assessment.project_complexity,
                        'collaboration_indicators': skills_assessment.collaboration_indicators,
                        'learning_trajectory': skills_assessment.learning_trajectory,
                        'analyzer_version': skills_assessment.analyzer_version,
                        'analysis_date': skills_assessment.analysis_date.isoformat() if skills_assessment.analysis_date else None
                    }
                })
        
        return assessment
    
    async def get_user_skills_assessments(self, user_id: str, limit: int = 10) -> List[UserAssessment]:
        """
        Get all skills assessments for a user.
        
        Args:
            user_id: User UUID
            limit: Maximum number of assessments to return
            
        Returns:
            List of UserAssessment records
        """
        assessments = self.db.query(UserAssessment).filter(
            UserAssessment.user_id == user_id,
            UserAssessment.assessment_type == 'skills'
        ).order_by(UserAssessment.created_at.desc()).limit(limit).all()
        
        return assessments
    
    async def get_user_skills_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive skills profile for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            User's skills profile with aggregated data
        """
        assessments = self.db.query(UserAssessment).filter(
            UserAssessment.user_id == user_id,
            UserAssessment.assessment_type == 'skills',
            UserAssessment.status == 'completed'
        ).order_by(UserAssessment.created_at.desc()).all()
        
        if not assessments:
            return {
                'user_id': user_id,
                'total_assessments': 0,
                'technical_skills': {},
                'programming_languages': {},
                'overall_performance': {},
                'project_complexity_trend': [],
                'recommendations': [],
                'recent_activity': [],
                'last_assessment': None
            }
        
        # Aggregate technical skills
        all_skills = []
        all_languages = {}
        project_complexities = []
        
        for assessment in assessments:
            result_data = assessment.result_data or {}
            code_analysis = result_data.get('code_analysis', {})
            skills_assessment = result_data.get('skills_assessment', {})
            
            # Collect skills
            for skill in code_analysis.get('technical_skills', []):
                all_skills.append({
                    'name': skill['name'],
                    'category': skill['category'],
                    'confidence': skill['confidence'],
                    'proficiency_level': skill.get('proficiency_level', 'intermediate')
                })
            
            # Collect languages
            for language, count in skills_assessment.get('programming_languages', {}).items():
                all_languages[language] = all_languages.get(language, 0) + count
            
            # Collect project complexities
            complexity = skills_assessment.get('project_complexity', 0)
            project_complexities.append({
                'complexity': complexity,
                'date': assessment.created_at.isoformat(),
                'project_name': assessment.input_data.get('project_name', 'Unknown')
            })
        
        # Aggregate skills by category and proficiency
        aggregated_skills = self._aggregate_skills_profile(all_skills)
        
        # Calculate overall performance metrics
        all_scores = [assessment.normalized_score for assessment in assessments if assessment.normalized_score is not None]
        overall_performance = {
            'average_score': sum(all_scores) / len(all_scores) if all_scores else 0,
            'best_score': max(all_scores) if all_scores else 0,
            'total_assessments': len(assessments),
            'improvement_trend': self._calculate_improvement_trend(assessments),
            'skill_diversity': len(set(skill['name'] for skill in all_skills)),
            'language_diversity': len(all_languages)
        }
        
        # Generate recommendations
        recommendations = self._generate_skills_recommendations(aggregated_skills, overall_performance)
        
        # Recent activity
        recent_activity = []
        for assessment in assessments[:5]:  # Last 5 assessments
            result_data = assessment.result_data or {}
            skills_assessment = result_data.get('skills_assessment', {})
            
            recent_activity.append({
                'assessment_id': str(assessment.id),
                'project_name': assessment.input_data.get('project_name', 'Unknown'),
                'source_type': skills_assessment.get('source_type', 'unknown'),
                'score': assessment.normalized_score or 0,
                'languages': list(skills_assessment.get('programming_languages', {}).keys()),
                'completed_at': assessment.completed_at.isoformat() if assessment.completed_at else None
            })
        
        return {
            'user_id': user_id,
            'total_assessments': len(assessments),
            'technical_skills': aggregated_skills,
            'programming_languages': all_languages,
            'overall_performance': overall_performance,
            'project_complexity_trend': project_complexities[:10],  # Last 10 projects
            'recommendations': recommendations,
            'recent_activity': recent_activity,
            'last_assessment': assessments[0].completed_at.isoformat() if assessments[0].completed_at else None
        }
    
    async def get_github_repository_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Get basic GitHub repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository information or None if not found
        """
        try:
            repo_info = await self.github_client.get_repository(owner, repo)
            if not repo_info:
                return None
            
            return {
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
                'is_private': repo_info.is_private,
                'default_branch': repo_info.default_branch
            }
            
        except Exception as e:
            logger.error(f"Failed to get repository info for {owner}/{repo}: {e}")
            return None
    
    def _calculate_skills_scores(self, repo_analysis: Dict[str, Any], code_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive skills scores."""
        # Base scores from code analysis
        overall_scores = code_analysis.get('overall_scores', {})
        code_quality = overall_scores.get('code_quality', 0)
        skill_proficiency = overall_scores.get('skill_proficiency', 0)
        technical_diversity = overall_scores.get('technical_diversity', 0)
        
        # Repository metrics
        repo_info = repo_analysis.get('repository', {})
        stars = repo_info.get('stars', 0)
        forks = repo_info.get('forks', 0)
        languages = repo_info.get('languages', {})
        
        # Collaboration score
        collaboration = repo_analysis.get('collaboration', {})
        collaboration_score = 50  # Base score
        if collaboration.get('is_collaborative', False):
            collaboration_score += 30
        if collaboration.get('total_authors', 0) > 1:
            collaboration_score += 20
        
        # Project complexity score
        project_complexity = repo_analysis.get('project_complexity', 0)
        complexity_score = min(project_complexity * 10, 100)  # Scale to 0-100
        
        # Activity score (based on commits)
        commit_activity = repo_analysis.get('commit_activity', {})
        activity_score = min(commit_activity.get('avg_commits_per_week', 0) * 2, 100)
        
        # Calculate weighted raw score
        raw_score = (
            code_quality * 0.25 +
            skill_proficiency * 0.25 +
            technical_diversity * 0.15 +
            collaboration_score * 0.15 +
            complexity_score * 0.1 +
            activity_score * 0.1
        )
        
        # Normalize to 0-100 scale
        normalized_score = min(raw_score, 100)
        
        # Calculate confidence based on data quality
        confidence_factors = {
            'files_analyzed': code_analysis.get('summary', {}).get('files_analyzed', 0),
            'languages_detected': len(languages),
            'has_commits': commit_activity.get('total_commits', 0) > 0,
            'has_collaboration': collaboration.get('total_authors', 0) > 1
        }
        
        confidence = 0.5  # Base confidence
        if confidence_factors['files_analyzed'] > 0:
            confidence += 0.2
        if confidence_factors['languages_detected'] > 0:
            confidence += 0.1
        if confidence_factors['has_commits']:
            confidence += 0.1
        if confidence_factors['has_collaboration']:
            confidence += 0.1
        
        confidence = min(confidence, 1.0)
        
        return {
            'raw_score': raw_score,
            'normalized_score': normalized_score,
            'confidence_score': confidence,
            'component_scores': {
                'code_quality': code_quality,
                'skill_proficiency': skill_proficiency,
                'technical_diversity': technical_diversity,
                'collaboration': collaboration_score,
                'project_complexity': complexity_score,
                'activity': activity_score
            }
        }
    
    def _calculate_skills_scores_from_code_analysis(self, code_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate skills scores from code analysis only (no GitHub data)."""
        overall_scores = code_analysis.get('overall_scores', {})
        
        # Use available scores
        code_quality = overall_scores.get('code_quality', 0)
        skill_proficiency = overall_scores.get('skill_proficiency', 0)
        technical_diversity = overall_scores.get('technical_diversity', 0)
        best_practices = overall_scores.get('best_practices', 0)
        
        # Calculate weighted raw score
        raw_score = (
            code_quality * 0.3 +
            skill_proficiency * 0.3 +
            technical_diversity * 0.2 +
            best_practices * 0.2
        )
        
        # Normalize to 0-100 scale
        normalized_score = min(raw_score, 100)
        
        # Calculate confidence based on data quality
        files_analyzed = code_analysis.get('summary', {}).get('total_files_analyzed', 0)
        confidence = min(0.3 + (files_analyzed * 0.02), 1.0)  # More files = higher confidence
        
        return {
            'raw_score': raw_score,
            'normalized_score': normalized_score,
            'confidence_score': confidence,
            'component_scores': {
                'code_quality': code_quality,
                'skill_proficiency': skill_proficiency,
                'technical_diversity': technical_diversity,
                'best_practices': best_practices
            }
        }
    
    def _aggregate_skills_profile(self, all_skills: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate skills by category and proficiency."""
        skills_by_category = {}
        proficiency_counts = {'beginner': 0, 'intermediate': 0, 'advanced': 0, 'expert': 0}
        
        for skill in all_skills:
            category = skill.get('category', 'unknown')
            proficiency = skill.get('proficiency_level', 'intermediate')
            confidence = skill.get('confidence', 0)
            
            if category not in skills_by_category:
                skills_by_category[category] = []
            
            skills_by_category[category].append({
                'name': skill['name'],
                'confidence': confidence,
                'proficiency_level': proficiency
            })
            
            proficiency_counts[proficiency] = proficiency_counts.get(proficiency, 0) + 1
        
        # Sort skills within each category by confidence
        for category in skills_by_category:
            skills_by_category[category].sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'skills_by_category': skills_by_category,
            'proficiency_distribution': proficiency_counts,
            'total_unique_skills': len(set(skill['name'] for skill in all_skills)),
            'top_skills': sorted(all_skills, key=lambda x: x['confidence'], reverse=True)[:10]
        }
    
    def _calculate_improvement_trend(self, assessments: List[UserAssessment]) -> str:
        """Calculate improvement trend over recent assessments."""
        if len(assessments) < 2:
            return "insufficient_data"
        
        # Take last 5 assessments
        recent_assessments = assessments[:5]
        scores = [assessment.normalized_score for assessment in recent_assessments if assessment.normalized_score is not None]
        
        if len(scores) < 2:
            return "insufficient_data"
        
        # Calculate trend
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg + 5:
            return "improving"
        elif second_avg < first_avg - 5:
            return "declining"
        else:
            return "stable"
    
    def _generate_skills_recommendations(
        self, 
        aggregated_skills: Dict[str, Any], 
        overall_performance: Dict[str, Any]
    ) -> List[str]:
        """Generate personalized skills recommendations."""
        recommendations = []
        
        # Overall performance recommendations
        avg_score = overall_performance.get('average_score', 0)
        if avg_score >= 85:
            recommendations.append("Excellent technical skills! Consider contributing to open-source projects.")
        elif avg_score >= 70:
            recommendations.append("Good technical foundation. Focus on deepening expertise in key areas.")
        elif avg_score >= 55:
            recommendations.append("Fair technical skills. Work on code quality and best practices.")
        else:
            recommendations.append("Focus on fundamental programming concepts and code quality.")
        
        # Skill diversity recommendations
        skill_diversity = overall_performance.get('skill_diversity', 0)
        if skill_diversity < 5:
            recommendations.append("Expand your technical skill set by learning new programming languages or frameworks.")
        
        # Language diversity recommendations
        language_diversity = overall_performance.get('language_diversity', 0)
        if language_diversity == 1:
            recommendations.append("Consider learning additional programming languages to increase versatility.")
        
        # Proficiency-based recommendations
        proficiency_dist = aggregated_skills.get('proficiency_distribution', {})
        if proficiency_dist.get('beginner', 0) > proficiency_dist.get('advanced', 0):
            recommendations.append("Focus on advancing your beginner skills to intermediate level.")
        
        # Category-specific recommendations
        skills_by_category = aggregated_skills.get('skills_by_category', {})
        if 'programming_languages' in skills_by_category and len(skills_by_category['programming_languages']) == 1:
            recommendations.append("Learn additional programming languages to broaden your skill set.")
        
        if len(recommendations) == 0:
            recommendations.append("Continue developing your technical skills and explore new technologies.")
        
        return recommendations[:5]  # Top 5 recommendations

    def _serialize_sync_result(self, result: SubmissionSyncResult) -> Dict[str, Any]:
        payload = asdict(result)
        return self._prepare_for_json(payload)

    def _serialize_sync_log_entry(self, entry: SyncLogEntry) -> Dict[str, Any]:
        return {
            "learner_id": entry.learner_id,
            "submission_id": entry.submission_id,
            "template_id": entry.template_id,
            "project_id": entry.project_id,
            "metadata": entry.metadata,
            "recorded_at": entry.recorded_at.isoformat(),
            "result": self._serialize_sync_result(entry.result),
        }

    def _serialize_link(self, link: LearnerRepoLink) -> Dict[str, Any]:
        return {
            "learner_id": link.learner_id,
            "repository_full_name": link.repository_full_name,
            "project_id": link.project_id,
            "github_handle": link.github_handle,
            "last_refreshed_at": link.last_refreshed_at.isoformat(),
            "metadata": link.metadata,
        }

    def _prepare_for_json(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, list):
            return [self._prepare_for_json(item) for item in value]
        if isinstance(value, dict):
            return {key: self._prepare_for_json(item) for key, item in value.items()}
        return value
