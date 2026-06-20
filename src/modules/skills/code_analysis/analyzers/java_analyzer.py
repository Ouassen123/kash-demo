"""Java analyzer for Skills code analysis pipeline."""

import re
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .base import BaseAnalyzer, AnalyzerConfig
from ..models import AnalyzerFinding, SeverityLevel
from ..rules import JavaEducationalRules


@dataclass
class JavaMetrics:
    """Metrics specific to Java code analysis."""
    class_count: int = 0
    method_count: int = 0
    interface_count: int = 0
    package_count: int = 0
    import_count: int = 0
    cyclomatic_complexity: int = 0
    lines_of_code: int = 0
    comment_lines: int = 0


class JavaAnalyzer(BaseAnalyzer):
    """Java-specific code analyzer using pattern matching and heuristics."""
    
    name = "java_analyzer"
    supported_extensions = {".java"}
    
    def __init__(self, config: Optional[AnalyzerConfig] = None):
        super().__init__(config)
        self.metrics = JavaMetrics()
        self.educational_rules = JavaEducationalRules()
        
        # Java patterns for analysis
        self.patterns = {
            "class": re.compile(r'^\s*(public\s+|private\s+|protected\s+)?(abstract\s+|final\s+)?class\s+(\w+)'),
            "interface": re.compile(r'^\s*(public\s+|private\s+)?interface\s+(\w+)'),
            "method": re.compile(r'^\s*(public\s+|private\s+|protected\s+)?(static\s+)?(final\s+)?(abstract\s+)?(native\s+)?(synchronized\s+)?([a-zA-Z_$][\w$<>]*\s+)+(\w+)\s*\([^)]*\)\s*(throws\s+[\w\s,]+)?\s*[{;]'),
            "package": re.compile(r'^\s*package\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*;'),
            "import": re.compile(r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_.*]*)\s*;'),
            "comment_single": re.compile(r'//.*'),
            "comment_multi_start": re.compile(r'/\*'),
            "comment_multi_end": re.compile(r'\*/'),
            "cyclomatic_complexity": re.compile(r'\b(if|else|for|while|do|switch|case|catch|&&|\|\||\?)\b'),
        }
    
    async def analyze(self, repository_input) -> List[AnalyzerFinding]:
        """Analyze Java files in the repository."""
        findings = []
        
        # Filter Java files
        java_files = [f for f in repository_input.files if f.suffix in self.supported_extensions]
        
        for file_path in java_files:
            try:
                file_findings = await self._analyze_java_file(file_path)
                findings.extend(file_findings)
            except Exception as e:
                findings.append(AnalyzerFinding(
                    rule_id="JAVA_PARSE_ERROR",
                    message=f"Failed to parse Java file: {str(e)}",
                    file_path=file_path,
                    line_number=1,
                    severity=SeverityLevel.LOW,
                    category="parsing",
                    score_impact=-1.0,
                    metadata={"error": str(e)},
                ))
        
        # Add aggregate findings based on metrics
        findings.extend(self._generate_metric_findings())
        
        return findings
    
    async def _analyze_java_file(self, file_path: Path) -> List[AnalyzerFinding]:
        """Analyze a single Java file."""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except UnicodeDecodeError:
            # Try different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
                lines = content.split('\n')
        
        file_metrics = JavaMetrics()
        in_multiline_comment = False
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # Track multiline comments
            if self.patterns["comment_multi_start"].search(line) and not in_multiline_comment:
                in_multiline_comment = True
                file_metrics.comment_lines += 1
            elif self.patterns["comment_multi_end"].search(line) and in_multiline_comment:
                in_multiline_comment = False
                file_metrics.comment_lines += 1
            elif in_multiline_comment:
                file_metrics.comment_lines += 1
            elif self.patterns["comment_single"].search(line):
                file_metrics.comment_lines += 1
            else:
                file_metrics.lines_of_code += 1
            
            # Analyze patterns
            if self.patterns["package"].search(line):
                file_metrics.package_count += 1
            
            if self.patterns["import"].search(line):
                file_metrics.import_count += 1
                import_match = self.patterns["import"].search(line)
                import_file = import_match.group(1) if import_match else "Unknown"
                
                # Check for wildcard imports - Educational Rule JAVA003
                if ".*" in line:
                    rule = self.educational_rules.get_rule("JAVA003_WILDCARD_IMPORTS")
                    if rule:
                        findings.append(AnalyzerFinding(
                            rule_id=rule.rule_id,
                            message=rule.description,
                            file_path=file_path,
                            line_number=line_num,
                            severity=rule.severity,
                            category="style",
                            score_impact=rule.score_impact,
                            metadata={
                                "import_line": line,
                                "educational_level": rule.educational_level.value,
                                "learning_objective": rule.learning_objective,
                                "improvement_suggestion": rule.improvement_suggestion,
                                "resources": rule.resources,
                            },
                        ))
            
            if self.patterns["class"].search(line):
                file_metrics.class_count += 1
                class_match = self.patterns["class"].search(line)
                class_name = class_match.group(3) if class_match else "Unknown"
                
                # Check class naming convention - Educational Rule JAVA001
                if not class_name[0].isupper():
                    rule = self.educational_rules.get_rule("JAVA001_CLASS_NAMING")
                    if rule:
                        findings.append(AnalyzerFinding(
                            rule_id=rule.rule_id,
                            message=rule.description,
                            file_path=file_path,
                            line_number=line_num,
                            severity=rule.severity,
                            category="style",
                            score_impact=rule.score_impact,
                            metadata={
                                "class_name": class_name,
                                "educational_level": rule.educational_level.value,
                                "learning_objective": rule.learning_objective,
                                "improvement_suggestion": rule.improvement_suggestion,
                                "resources": rule.resources,
                            },
                        ))
            
            if self.patterns["interface"].search(line):
                file_metrics.interface_count += 1
            
            if self.patterns["method"].search(line):
                file_metrics.method_count += 1
                method_match = self.patterns["method"].search(line)
                method_name = method_match.groups()[-2] if method_match else "Unknown"
                
                # Check method naming convention - Educational Rule JAVA002
                if not method_name[0].islower():
                    rule = self.educational_rules.get_rule("JAVA002_METHOD_NAMING")
                    if rule:
                        findings.append(AnalyzerFinding(
                            rule_id=rule.rule_id,
                            message=rule.description,
                            file_path=file_path,
                            line_number=line_num,
                            severity=rule.severity,
                            category="style",
                            score_impact=rule.score_impact,
                            metadata={
                                "method_name": method_name,
                                "educational_level": rule.educational_level.value,
                                "learning_objective": rule.learning_objective,
                                "improvement_suggestion": rule.improvement_suggestion,
                                "resources": rule.resources,
                            },
                        ))
                
                # Check for long parameter lists - Educational Rule JAVA004
                param_count = line.count(',') + 1
                if param_count > 5:
                    rule = self.educational_rules.get_rule("JAVA004_TOO_MANY_PARAMETERS")
                    if rule:
                        findings.append(AnalyzerFinding(
                            rule_id=rule.rule_id,
                            message=rule.description,
                            file_path=file_path,
                            line_number=line_num,
                            severity=rule.severity,
                            category="complexity",
                            score_impact=rule.score_impact,
                            metadata={
                                "method_name": method_name,
                                "parameter_count": param_count,
                                "educational_level": rule.educational_level.value,
                                "learning_objective": rule.learning_objective,
                                "improvement_suggestion": rule.improvement_suggestion,
                                "resources": rule.resources,
                            },
                        ))
            
            # Calculate cyclomatic complexity
            complexity_matches = self.patterns["cyclomatic_complexity"].findall(line)
            file_metrics.cyclomatic_complexity += len(complexity_matches)
        
        # Check for missing package declaration - Educational Rule JAVA007
        if file_metrics.package_count == 0 and file_metrics.lines_of_code > 5:
            rule = self.educational_rules.get_rule("JAVA007_MISSING_INCLUDE_GUARD")
            if rule:
                findings.append(AnalyzerFinding(
                    rule_id=rule.rule_id,
                    message=rule.description,
                    file_path=file_path,
                    line_number=1,
                    severity=rule.severity,
                    category="organization",
                    score_impact=rule.score_impact,
                    metadata={
                        "file_type": "java",
                        "educational_level": rule.educational_level.value,
                        "learning_objective": rule.learning_objective,
                        "improvement_suggestion": rule.improvement_suggestion,
                        "resources": rule.resources,
                    },
                ))
        
        # Add file-level findings
        if file_metrics.lines_of_code > 500:
            rule = self.educational_rules.get_rule("JAVA005_LONG_METHOD")
            if rule:
                findings.append(AnalyzerFinding(
                    rule_id=rule.rule_id,
                    message=f"Java file is too long ({file_metrics.lines_of_code} lines)",
                    file_path=file_path,
                    line_number=1,
                    severity=rule.severity,
                    category="complexity",
                    score_impact=rule.score_impact,
                    metadata={
                        "lines_of_code": file_metrics.lines_of_code,
                        "educational_level": rule.educational_level.value,
                        "learning_objective": rule.learning_objective,
                        "improvement_suggestion": rule.improvement_suggestion,
                        "resources": rule.resources,
                    },
                ))
        
        if file_metrics.cyclomatic_complexity > 20:
            findings.append(AnalyzerFinding(
                rule_id="JAVA_HIGH_COMPLEXITY",
                message=f"File has high cyclomatic complexity ({file_metrics.cyclomatic_complexity})",
                file_path=file_path,
                line_number=1,
                severity=SeverityLevel.HIGH,
                category="complexity",
                score_impact=-8.0,
                metadata={"cyclomatic_complexity": file_metrics.cyclomatic_complexity},
            ))
        
        # Update global metrics
        self.metrics.class_count += file_metrics.class_count
        self.metrics.method_count += file_metrics.method_count
        self.metrics.interface_count += file_metrics.interface_count
        self.metrics.package_count += file_metrics.package_count
        self.metrics.import_count += file_metrics.import_count
        self.metrics.cyclomatic_complexity += file_metrics.cyclomatic_complexity
        self.metrics.lines_of_code += file_metrics.lines_of_code
        self.metrics.comment_lines += file_metrics.comment_lines
        
        return findings
    
    def _generate_metric_findings(self) -> List[AnalyzerFinding]:
        """Generate findings based on aggregate metrics."""
        findings = []
        
        # Check for too many classes
        if self.metrics.class_count > 20:
            findings.append(AnalyzerFinding(
                rule_id="JAVA_TOO_MANY_CLASSES",
                message=f"Project has too many classes ({self.metrics.class_count})",
                file_path=Path("project"),
                line_number=1,
                severity=SeverityLevel.MEDIUM,
                category="architecture",
                score_impact=-3.0,
                metadata={"class_count": self.metrics.class_count},
            ))
        
        # Check comment ratio
        if self.metrics.lines_of_code > 0:
            comment_ratio = self.metrics.comment_lines / (self.metrics.lines_of_code + self.metrics.comment_lines)
            if comment_ratio < 0.1:
                findings.append(AnalyzerFinding(
                    rule_id="JAVA_LOW_COMMENT_RATIO",
                    message=f"Low comment ratio ({comment_ratio:.2%}) - consider adding more documentation",
                    file_path=Path("project"),
                    line_number=1,
                    severity=SeverityLevel.MEDIUM,
                    category="documentation",
                    score_impact=-3.0,
                    metadata={"comment_ratio": comment_ratio},
                ))
        
        return findings
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return analysis metrics."""
        return {
            "language": "java",
            "class_count": self.metrics.class_count,
            "method_count": self.metrics.method_count,
            "interface_count": self.metrics.interface_count,
            "package_count": self.metrics.package_count,
            "import_count": self.metrics.import_count,
            "cyclomatic_complexity": self.metrics.cyclomatic_complexity,
            "lines_of_code": self.metrics.lines_of_code,
            "comment_lines": self.metrics.comment_lines,
        }
