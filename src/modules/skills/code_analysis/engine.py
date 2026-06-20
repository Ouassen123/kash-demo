"""Orchestrates Skills code analysis runs using configured analyzers."""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Type

from .context import AnalysisContext, RepositoryInput
from .models import AnalysisResult, AnalyzerReport, SeverityLevel
from .analyzers import ANALYZER_REGISTRY, BaseAnalyzer


DEFAULT_PROFILES: Dict[str, Dict[str, Any]] = {
    "default": {
        "analyzers": ["heuristics"],
    },
    "standard": {
        "analyzers": ["heuristics"],
        "auto_detect_languages": True,
    },
    "comprehensive": {
        "analyzers": ["heuristics", "java_analyzer", "cpp_analyzer", "javascript_analyzer"],
        "auto_detect_languages": True,
    },
    "educational": {
        "analyzers": ["heuristics", "java_analyzer", "cpp_analyzer", "javascript_analyzer"],
        "auto_detect_languages": True,
        "educational_mode": True,
    }
}

# Language to analyzer mapping
LANGUAGE_ANALYZER_MAP = {
    ".py": ["heuristics"],
    ".java": ["java_analyzer"],
    ".cpp": ["cpp_analyzer"],
    ".cc": ["cpp_analyzer"],
    ".cxx": ["cpp_analyzer"],
    ".c": ["cpp_analyzer"],
    ".h": ["cpp_analyzer"],
    ".hpp": ["cpp_analyzer"],
    ".hxx": ["cpp_analyzer"],
    ".js": ["javascript_analyzer"],
    ".jsx": ["javascript_analyzer"],
    ".ts": ["javascript_analyzer"],
    ".tsx": ["javascript_analyzer"],
    ".mjs": ["javascript_analyzer"],
}


class CodeAnalysisEngine:
    """Coordinates analyzer execution and aggregates results."""

    def __init__(
        self,
        analyzer_registry: Optional[Dict[str, Type[BaseAnalyzer]]] = None,
        profiles: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        self.analyzer_registry = analyzer_registry or ANALYZER_REGISTRY.copy()
        self.profiles = profiles or DEFAULT_PROFILES

    def _detect_languages(self, repository: RepositoryInput) -> List[str]:
        """Detect programming languages in the repository and return appropriate analyzers."""
        detected_analyzers = set()
        
        # Check file extensions
        for file_path in repository.files:
            extension = file_path.suffix.lower()
            if extension in LANGUAGE_ANALYZER_MAP:
                detected_analyzers.update(LANGUAGE_ANALYZER_MAP[extension])
        
        # Also check inline files if provided
        if repository.inline_files:
            for file_data in repository.inline_files:
                file_path = file_data.get("path", "")
                if "." in file_path:
                    extension = "." + file_path.split(".")[-1].lower()
                    if extension in LANGUAGE_ANALYZER_MAP:
                        detected_analyzers.update(LANGUAGE_ANALYZER_MAP[extension])
        
        return list(detected_analyzers)

    async def analyze(
        self,
        repository: RepositoryInput,
        analysis_profile: str = "default",
        selected_analyzers: Optional[List[str]] = None,
        extra_config: Optional[Dict[str, Any]] = None,
    ) -> AnalysisResult:
        profile_config = self.profiles.get(analysis_profile, self.profiles["default"])
        
        # Auto-detect languages if enabled
        if selected_analyzers is None and profile_config.get("auto_detect_languages", False):
            selected_analyzers = self._detect_languages(repository)
            # Fall back to profile analyzers if no languages detected
            if not selected_analyzers:
                selected_analyzers = profile_config.get("analyzers", ["heuristics"])
        else:
            selected_analyzers = selected_analyzers or profile_config.get("analyzers", [])
        
        # Remove duplicates while preserving order
        seen = set()
        analyzers_to_run = []
        for analyzer in selected_analyzers:
            if analyzer not in seen:
                analyzers_to_run.append(analyzer)
                seen.add(analyzer)

        context = AnalysisContext(
            repository=repository,
            analysis_profile=analysis_profile,
            analyzers=analyzers_to_run,
            config={"profiles": self.profiles, "extra": extra_config or {}},
        )

        reports: List[AnalyzerReport] = []
        for analyzer_name in analyzers_to_run:
            analyzer_cls = self.analyzer_registry.get(analyzer_name)
            if not analyzer_cls:
                continue
            analyzer = analyzer_cls() if callable(analyzer_cls) else analyzer_cls
            try:
                findings = await analyzer.analyze(context.repository)
                execution_time = 0  # TODO: Implement timing
                
                # Get metrics if available
                metrics = {}
                if hasattr(analyzer, 'get_metrics'):
                    metrics = analyzer.get_metrics()
                
                report = AnalyzerReport(
                    analyzer_name=analyzer_name,
                    analyzer_version="1.0.0",  # TODO: Get from analyzer
                    execution_time_ms=execution_time,
                    findings=findings,
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                report = AnalyzerReport(
                    analyzer_name=analyzer_name,
                    analyzer_version="1.0.0",
                    execution_time_ms=0,
                    findings=[],
                )
                # Add error as a finding
                report.findings.append(AnalyzerFinding(
                    rule_id="ANALYZER_ERROR",
                    message=f"Analyzer failed: {exc}",
                    file_path=repository.root_path / "error" if hasattr(repository, 'root_path') else Path("error"),
                    line_number=1,
                    severity=SeverityLevel.CRITICAL,
                    category="error",
                    score_impact=-10.0,
                    metadata={"error": str(exc)},
                ))
            reports.append(report)

        # Collect all findings
        all_findings = []
        for report in reports:
            all_findings.extend(report.findings)
        
        # Calculate overall score and confidence
        overall_score, confidence = self._calculate_overall_score(reports)
        
        summary = self._build_summary(reports)
        
        return AnalysisResult(
            submission_id=repository.submission_id,
            learner_id=repository.learner_id,
            template_id=repository.template_id,
            analysis_profile=analysis_profile,
            overall_score=overall_score,
            confidence=confidence,
            analyzer_reports=reports,
            summary=summary,
            analyzed_at=datetime.utcnow(),
        )

    def _calculate_overall_score(self, reports: List[AnalyzerReport]) -> tuple[float, float]:
        """Calculate overall score and confidence from analyzer reports."""
        if not reports:
            return 50.0, 0.0  # Neutral score with no confidence
        
        total_score = 0.0
        total_weight = 0.0
        total_findings = 0
        
        for report in reports:
            # Base score starts at 100, subtract penalties
            report_score = 100.0
            
            for finding in report.findings:
                report_score += finding.score_impact
                total_findings += 1
            
            # Weight by number of findings (more findings = more weight)
            weight = max(1, len(report.findings))
            total_score += report_score * weight
            total_weight += weight
        
        # Calculate final score
        if total_weight > 0:
            overall_score = max(0, min(100, total_score / total_weight))
        else:
            overall_score = 100.0
        
        # Confidence based on number of findings and analyzers
        if total_findings > 0:
            confidence = min(1.0, total_findings / 10.0)  # More findings = higher confidence
        else:
            confidence = 0.5  # Neutral confidence for no findings
        
        confidence = min(1.0, len(reports) / 4.0)  # More analyzers = higher confidence
        
        return overall_score, confidence

    def _build_summary(self, reports: List[AnalyzerReport]) -> str:
        """Build a human-readable summary of the analysis."""
        if not reports:
            return "No analysis reports available."
        
        total_findings = sum(len(report.findings) for report in reports)
        severity_counts = {level.value: 0 for level in SeverityLevel}
        
        for report in reports:
            for finding in report.findings:
                severity_counts[finding.severity.value] += 1
        
        summary_parts = [
            f"Analysis completed with {len(reports)} analyzer(s).",
            f"Found {total_findings} total findings.",
        ]
        
        # Add severity breakdown
        if total_findings > 0:
            severity_parts = []
            for severity, count in severity_counts.items():
                if count > 0:
                    severity_parts.append(f"{count} {severity}")
            summary_parts.append(f"Severity breakdown: {', '.join(severity_parts)}.")
        
        # Add analyzer-specific info
        analyzer_names = [report.analyzer_name for report in reports]
        summary_parts.append(f"Analyzers used: {', '.join(analyzer_names)}.")
        
        return " ".join(summary_parts)
