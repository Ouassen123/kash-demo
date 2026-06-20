"""Heuristics-based analyzer wrapping the legacy CodeAnalyzer."""

from __future__ import annotations

import asyncio
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from src.modules.skills.code_analyzer import CodeAnalyzer

from .base import BaseAnalyzer, AnalyzerConfig
from ..models import AnalyzerReport, AnalyzerFinding, SeverityLevel


class HeuristicsAnalyzer(BaseAnalyzer):
    """Adapter that reuses the existing CodeAnalyzer heuristics."""

    name = "heuristics"
    supported_extensions = {".py", ".js", ".ts", ".java", ".cs", ".cpp", ".c", ".go", ".rs"}

    def __init__(self, config: AnalyzerConfig | None = None) -> None:
        super().__init__(config)
        self._analyzer = CodeAnalyzer()

    async def analyze(self, repository_input) -> List[AnalyzerFinding]:
        """Analyze files using the heuristics analyzer."""
        loop = asyncio.get_event_loop()
        files_payload = await loop.run_in_executor(None, self._collect_files, repository_input)

        if not files_payload:
            return []

        analysis = await loop.run_in_executor(None, self._analyzer.analyze_repository, files_payload)
        
        # Convert legacy analysis results to new format
        findings = []
        
        # Extract findings from analysis results
        for file_path, file_analysis in analysis.get("files", {}).items():
            for issue in file_analysis.get("issues", []):
                severity_map = {
                    "error": SeverityLevel.CRITICAL,
                    "warning": SeverityLevel.HIGH,
                    "info": SeverityLevel.MEDIUM,
                    "style": SeverityLevel.LOW,
                }
                
                finding = AnalyzerFinding(
                    rule_id=issue.get("rule_id", "HEURISTIC_ISSUE"),
                    message=issue.get("message", "Code quality issue detected"),
                    file_path=repository_input.root_path / file_path if hasattr(repository_input, 'root_path') else Path(file_path),
                    line_number=issue.get("line_number", 1),
                    severity=severity_map.get(issue.get("severity", "info"), SeverityLevel.MEDIUM),
                    category=issue.get("category", "quality"),
                    score_impact=issue.get("score_impact", -2.0),
                    metadata=issue.get("metadata", {}),
                )
                findings.append(finding)
        
        return findings

    def _collect_files(self, repository_input) -> List[Dict[str, Any]]:
        """Collect file payloads for the legacy analyzer."""
        files_payload = []
        
        for file_path in repository_input.files:
            if file_path.suffix not in self.supported_extensions:
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                files_payload.append({
                    "path": str(file_path.relative_to(repository_input.root_path)) if hasattr(repository_input, 'root_path') else str(file_path),
                    "content": content,
                    "language": self._detect_language(file_path),
                })
            except Exception:
                continue  # Skip files that can't be read
        
        # Also handle inline files
        if repository_input.inline_files:
            for file_data in repository_input.inline_files:
                files_payload.append({
                    "path": file_data.get("path", "inline"),
                    "content": file_data.get("content", ""),
                    "language": self._detect_language_from_path(file_data.get("path", "")),
                })
        
        return files_payload
    
    def _detect_language(self, file_path) -> str:
        """Detect programming language from file extension."""
        extension_map = {
            ".py": "python",
            ".js": "javascript", 
            ".ts": "typescript",
            ".java": "java",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rs": "rust",
        }
        return extension_map.get(file_path.suffix.lower(), "unknown")
    
    def _detect_language_from_path(self, path: str) -> str:
        """Detect programming language from file path string."""
        if "." not in path:
            return "unknown"
        extension = "." + path.split(".")[-1].lower()
        extension_map = {
            ".py": "python",
            ".js": "javascript", 
            ".ts": "typescript",
            ".java": "java",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rs": "rust",
        }
        return extension_map.get(extension, "unknown")
