"""Analyzer plugins for the Skills code analysis pipeline."""

from .base import BaseAnalyzer
from .heuristics import HeuristicsAnalyzer
from .java_analyzer import JavaAnalyzer
from .cpp_analyzer import CppAnalyzer
from .javascript_analyzer import JavaScriptAnalyzer

ANALYZER_REGISTRY = {
    HeuristicsAnalyzer.name: HeuristicsAnalyzer,
    JavaAnalyzer.name: JavaAnalyzer,
    CppAnalyzer.name: CppAnalyzer,
    JavaScriptAnalyzer.name: JavaScriptAnalyzer,
}

__all__ = [
    "BaseAnalyzer",
    "HeuristicsAnalyzer",
    "JavaAnalyzer",
    "CppAnalyzer", 
    "JavaScriptAnalyzer",
    "ANALYZER_REGISTRY",
]
