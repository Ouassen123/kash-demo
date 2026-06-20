"""C++ analyzer for Skills code analysis pipeline."""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .base import BaseAnalyzer, AnalyzerConfig
from ..models import AnalyzerFinding, SeverityLevel


@dataclass
class CppMetrics:
    """Metrics specific to C++ code analysis."""
    class_count: int = 0
    function_count: int = 0
    header_count: int = 0
    include_count: int = 0
    cyclomatic_complexity: int = 0
    lines_of_code: int = 0
    comment_lines: int = 0
    macro_count: int = 0


class CppAnalyzer(BaseAnalyzer):
    """C++-specific code analyzer using pattern matching and heuristics."""
    
    name = "cpp_analyzer"
    supported_extensions = {".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hxx"}
    
    def __init__(self, config: Optional[AnalyzerConfig] = None):
        super().__init__(config)
        self.metrics = CppMetrics()
        
        # C++ patterns for analysis
        self.patterns = {
            "class": re.compile(r'^\s*(class|struct)\s+(\w+)'),
            "function": re.compile(r'^\s*(\w+\s+)*(\w+)\s*\([^)]*\)\s*(const\s*)?(->\s*\w+)?\s*[{;]'),
            "include": re.compile(r'^\s*#include\s*[<"]([^>"]+)[>"]'),
            "macro": re.compile(r'^\s*#define\s+(\w+)'),
            "comment_single": re.compile(r'//.*'),
            "comment_multi_start": re.compile(r'/\*'),
            "comment_multi_end": re.compile(r'\*/'),
            "cyclomatic_complexity": re.compile(r'\b(if|else|for|while|do|switch|case|catch|&&|\|\||\?)\b'),
            "goto": re.compile(r'\bgoto\s+(\w+)'),
            "memory_alloc": re.compile(r'\b(new|delete|malloc|free)\b'),
        }
    
    async def analyze(self, repository_input) -> List[AnalyzerFinding]:
        """Analyze C++ files in the repository."""
        findings = []
        
        # Filter C++ files
        cpp_files = [f for f in repository_input.files if f.suffix in self.supported_extensions]
        
        for file_path in cpp_files:
            try:
                file_findings = await self._analyze_cpp_file(file_path)
                findings.extend(file_findings)
            except Exception as e:
                findings.append(AnalyzerFinding(
                    rule_id="CPP_PARSE_ERROR",
                    message=f"Failed to parse C++ file: {str(e)}",
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
    
    async def _analyze_cpp_file(self, file_path: Path) -> List[AnalyzerFinding]:
        """Analyze a single C++ file."""
        findings = []
        is_header = file_path.suffix in {".h", ".hpp", ".hxx"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
                lines = content.split('\n')
        
        file_metrics = CppMetrics()
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
            if self.patterns["include"].search(line):
                file_metrics.include_count += 1
                include_match = self.patterns["include"].search(line)
                include_file = include_match.group(1) if include_match else "Unknown"
                
                # Check for system vs local includes
                if "<" in line and ">" in line:
                    # System include
                    if include_file.startswith("bits/"):
                        findings.append(AnalyzerFinding(
                            rule_id="CPP_BITS_INCLUDE",
                            message="Avoid including compiler-specific headers like bits/stdc++",
                            file_path=file_path,
                            line_number=line_num,
                            severity=SeverityLevel.HIGH,
                            category="portability",
                            score_impact=-5.0,
                            metadata={"include_file": include_file},
                        ))
            
            if self.patterns["macro"].search(line):
                file_metrics.macro_count += 1
                macro_match = self.patterns["macro"].search(line)
                macro_name = macro_match.group(1) if macro_match else "Unknown"
                
                # Check for dangerous macros
                if macro_name.isupper() and macro_name in ["MIN", "MAX", "TRUE", "FALSE"]:
                    findings.append(AnalyzerFinding(
                        rule_id="CPP_DANGEROUS_MACRO",
                        message=f"Macro '{macro_name}' may conflict with standard library definitions",
                        file_path=file_path,
                        line_number=line_num,
                        severity=SeverityLevel.HIGH,
                        category="security",
                        score_impact=-6.0,
                        metadata={"macro_name": macro_name},
                    ))
            
            if self.patterns["class"].search(line):
                file_metrics.class_count += 1
                class_match = self.patterns["class"].search(line)
                class_name = class_match.group(2) if class_match else "Unknown"
                class_type = class_match.group(1) if class_match else "class"
                
                # Check class naming convention
                if not class_name[0].isupper():
                    findings.append(AnalyzerFinding(
                        rule_id="CPP_CLASS_NAMING",
                        message=f"{class_type.title()} name '{class_name}' should start with uppercase letter",
                        file_path=file_path,
                        line_number=line_num,
                        severity=SeverityLevel.MEDIUM,
                        category="style",
                        score_impact=-3.0,
                        metadata={"class_name": class_name, "type": class_type},
                    ))
            
            if self.patterns["function"].search(line):
                file_metrics.function_count += 1
                function_match = self.patterns["function"].search(line)
                function_name = function_match.groups()[-2] if function_match else "Unknown"
                
                # Skip constructors/destructors and class methods
                if "::" in function_name or function_name in ["main", "~", function_name]:
                    pass
                else:
                    # Check function naming convention
                    if not function_name[0].islower():
                        findings.append(AnalyzerFinding(
                            rule_id="CPP_FUNCTION_NAMING",
                            message=f"Function name '{function_name}' should start with lowercase letter",
                            file_path=file_path,
                            line_number=line_num,
                            severity=SeverityLevel.MEDIUM,
                            category="style",
                            score_impact=-2.0,
                            metadata={"function_name": function_name},
                        ))
                
                # Check for long parameter lists
                param_count = line.count(',') + 1
                if param_count > 6:
                    findings.append(AnalyzerFinding(
                        rule_id="CPP_TOO_MANY_PARAMETERS",
                        message=f"Function '{function_name}' has too many parameters ({param_count})",
                        file_path=file_path,
                        line_number=line_num,
                        severity=SeverityLevel.HIGH,
                        category="complexity",
                        score_impact=-5.0,
                        metadata={"function_name": function_name, "parameter_count": param_count},
                    ))
            
            # Check for goto statements
            if self.patterns["goto"].search(line):
                findings.append(AnalyzerFinding(
                    rule_id="CPP_GOTO_STATEMENT",
                    message="Avoid using goto statements - use structured control flow instead",
                    file_path=file_path,
                    line_number=line_num,
                    severity=SeverityLevel.HIGH,
                    category="style",
                    score_impact=-7.0,
                    metadata={"goto_line": line},
                ))
            
            # Check for memory management
            if self.patterns["memory_alloc"].search(line):
                if "new" in line and "delete" not in line:
                    findings.append(AnalyzerFinding(
                        rule_id="CPP_RAW_MEMORY_ALLOCATION",
                        message="Consider using smart pointers instead of raw new/delete",
                        file_path=file_path,
                        line_number=line_num,
                        severity=SeverityLevel.MEDIUM,
                        category="memory",
                        score_impact=-3.0,
                        metadata={"allocation_line": line},
                    ))
            
            # Calculate cyclomatic complexity
            complexity_matches = self.patterns["cyclomatic_complexity"].findall(line)
            file_metrics.cyclomatic_complexity += len(complexity_matches)
        
        # Header-specific checks
        if is_header:
            file_metrics.header_count += 1
            
            # Check for missing include guards
            has_include_guard = any("#ifndef" in line or "#define" in line for line in lines[:10])
            if not has_include_guard and file_metrics.lines_of_code > 5:
                findings.append(AnalyzerFinding(
                    rule_id="CPP_MISSING_INCLUDE_GUARD",
                    message="Header file should include include guards",
                    file_path=file_path,
                    line_number=1,
                    severity=SeverityLevel.HIGH,
                    category="best_practices",
                    score_impact=-4.0,
                    metadata={"file_type": "header"},
                ))
        
        # Add file-level findings
        if file_metrics.lines_of_code > 800:
            findings.append(AnalyzerFinding(
                rule_id="CPP_LONG_FILE",
                message=f"C++ file is too long ({file_metrics.lines_of_code} lines)",
                file_path=file_path,
                line_number=1,
                severity=SeverityLevel.HIGH,
                category="complexity",
                score_impact=-5.0,
                metadata={"lines_of_code": file_metrics.lines_of_code},
            ))
        
        if file_metrics.cyclomatic_complexity > 25:
            findings.append(AnalyzerFinding(
                rule_id="CPP_HIGH_COMPLEXITY",
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
        self.metrics.function_count += file_metrics.function_count
        self.metrics.header_count += file_metrics.header_count
        self.metrics.include_count += file_metrics.include_count
        self.metrics.cyclomatic_complexity += file_metrics.cyclomatic_complexity
        self.metrics.lines_of_code += file_metrics.lines_of_code
        self.metrics.comment_lines += file_metrics.comment_lines
        self.metrics.macro_count += file_metrics.macro_count
        
        return findings
    
    def _generate_metric_findings(self) -> List[AnalyzerFinding]:
        """Generate findings based on aggregate metrics."""
        findings = []
        
        # Check for too many classes
        if self.metrics.class_count > 30:
            findings.append(AnalyzerFinding(
                rule_id="CPP_TOO_MANY_CLASSES",
                message=f"Project has too many classes/structs ({self.metrics.class_count})",
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
            if comment_ratio < 0.15:
                findings.append(AnalyzerFinding(
                    rule_id="CPP_LOW_COMMENT_RATIO",
                    message=f"Low comment ratio ({comment_ratio:.2%}) - C++ code needs good documentation",
                    file_path=Path("project"),
                    line_number=1,
                    severity=SeverityLevel.MEDIUM,
                    category="documentation",
                    score_impact=-3.0,
                    metadata={"comment_ratio": comment_ratio},
                ))
        
        # Check header to source ratio
        if self.metrics.header_count > 0 and self.metrics.function_count > 0:
            header_ratio = self.metrics.header_count / (self.metrics.header_count + self.metrics.function_count)
            if header_ratio > 0.5:
                findings.append(AnalyzerFinding(
                    rule_id="CPP_MANY_HEADERS",
                    message=f"High header to implementation ratio ({header_ratio:.2%})",
                    file_path=Path("project"),
                    line_number=1,
                    severity=SeverityLevel.LOW,
                    category="architecture",
                    score_impact=-2.0,
                    metadata={"header_ratio": header_ratio},
                ))
        
        return findings
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return analysis metrics."""
        return {
            "language": "cpp",
            "class_count": self.metrics.class_count,
            "function_count": self.metrics.function_count,
            "header_count": self.metrics.header_count,
            "include_count": self.metrics.include_count,
            "macro_count": self.metrics.macro_count,
            "cyclomatic_complexity": self.metrics.cyclomatic_complexity,
            "lines_of_code": self.metrics.lines_of_code,
            "comment_lines": self.metrics.comment_lines,
        }
