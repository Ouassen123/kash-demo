"""Base interfaces for Skills code analyzers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Protocol

from ..context import AnalysisContext
from ..models import AnalyzerReport


@dataclass
class AnalyzerConfig:
    name: str
    enabled: bool = True
    severity_map: Dict[str, str] | None = None
    extra: Dict[str, Any] | None = None


class BaseAnalyzer(Protocol):
    """Protocol that all analyzers must implement."""

    name: str
    supported_languages: tuple[str, ...]

    async def run(self, context: AnalysisContext) -> AnalyzerReport:
        ...
