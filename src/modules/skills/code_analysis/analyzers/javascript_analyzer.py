"""JavaScript/TypeScript analyzer for Skills code analysis pipeline."""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .base import BaseAnalyzer, AnalyzerConfig
from ..models import AnalyzerFinding, SeverityLevel


@dataclass
class JSMetrics:
    """Metrics specific to JavaScript/TypeScript code analysis."""
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    export_count: int = 0
    cyclomatic_complexity: int = 0
    lines_of_code: int = 0
    comment_lines: int = 0
    async_function_count: int = 0
    arrow_function_count: int = 0


class JavaScriptAnalyzer(BaseAnalyzer):
    """JavaScript/TypeScript-specific code analyzer."""
    
    name = "javascript_analyzer"
    supported_extensions = {".js", ".jsx", ".ts", ".tsx", ".mjs"}
    
    def __init__(self, config: Optional[AnalyzerConfig] = None):
        super().__init__(config)
        self.metrics = JSMetrics()
        self.is_typescript = False
        
        # JavaScript/TypeScript patterns
        self.patterns = {
            "function": re.compile(r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))'),
            "class": re.compile(r'(?:class\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*class)'),
            "import": re.compile(r'^\s*import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]'),
            "require": re.compile(r'(?:const|let|var)\s+(?:\{[^}]*\}|\w+)\s*=\s*require\([\'"]([^\'"]+)[\'"]\)'),
            "export": re.compile(r'^\s*export\s+(?:default\s+)?(?:class|function|const|let|var|interface|type)'),
            "async_function": re.compile(r'\basync\s+(?:function|(\w+)\s*\()'),
            "arrow_function": re.compile(r'=\s*(?:async\s+)?\([^)]*\)\s*=>|const\s+\w+\s*=\s*(?:async\s+)?\w+\s*=>'),
            "comment_single": re.compile(r'//.*'),
            "comment_multi_start": re.compile(r'/\*'),
            "comment_multi_end": re.compile(r'\*/'),
            "cyclomatic_complexity": re.compile(r'\b(if|else|for|while|do|switch|case|catch|&&|\|\||\?|try)\b'),
            "console_log": re.compile(r'console\.(log|warn|error|debug|info)'),
            "var_declaration": re.compile(r'\bvar\s+(\w+)'),
            "any_type": re.compile(r':\s*any\b|<any>'),
            "typescript_interface": re.compile(r'interface\s+(\w+)'),
            "typescript_type": re.compile(r'(?:type\s+(\w+)|interface\s+(\w+))'),
        }
    
    async def analyze(self, repository_input) -> List[AnalyzerFinding]:
        """Analyze JavaScript/TypeScript files in the repository."""
        findings = []
        
        # Filter JS/TS files
        js_files = [f for f in repository_input.files if f.suffix in self.supported_extensions]
        
        for file_path in js_files:
            try:
                # Check if it's TypeScript
                self.is_typescript = file_path.suffix in {".ts", ".tsx"}
                file_findings = await self._analyze_js_file(file_path)
                findings.extend(file_findings)
            except Exception as e:
                findings.append(AnalyzerFinding(
                    rule_id="JS_PARSE_ERROR",
                    message=f"Failed to parse JavaScript/TypeScript file: {str(e)}",
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
    
    async def _analyze_js_file(self, file_path: Path) -> List[AnalyzerFinding]:
        """Analyze a single JavaScript/TypeScript file."""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
                lines = content.split('\n')
        
        file_metrics = JSMetrics()
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
            if self.patterns["import"].search(line):
                file_metrics.import_count += 1
                import_match = self.patterns["import"].search(line)
                import_module = import_match.group(1) if import_match else "Unknown"
                
                # Check for relative imports
                if import_module.startswith('./') or import_module.startswith('../'):
                    findings.append(AnalyzerFinding(
                        rule_id="JS_RELATIVE_IMPORT",
                        message=f"Consider using absolute imports instead of relative: {import_module}",
                        file_path=file_path,
                        line_number=line_num,
                        severity=SeverityLevel.LOW,
                        category="style",
                        score_impact=-1.0,
                        metadata={"import_module": import_module},
                    ))
            
            if self.patterns["require"].search(line):
                file_metrics.import_count += 1
                require_match = self.patterns["require"].search(line)
                require_module = require_match.group(1) if require_match else "Unknown"
                
                # Check for require in what should be ES modules
                if file_path.suffix in {".mjs", ".js"} and "package.json" not in str(file_path):
                    findings.append(AnalyzerFinding(
                        rule_id="JS_MIXED_MODULE_SYSTEMS",
                        message="Mixing require() with ES modules - consider using import/export consistently",
                        file_path=file_path,
                        line_number=line_num,
                        severity=SeverityLevel.MEDIUM,
                        category="style",
                        score_impact=-3.0,
                        metadata={"require_module": require_module},
                    ))
            
            if self.patterns["export"].search(line):
                file_metrics.export_count += 1
            
            if self.patterns["function"].search(line):
                file_metrics.function_count += 1
                func_match = self.patterns["function"].search(line)
                func_name = func_match.group(1) or func_match.group(2) or "anonymous"
                
                # Check function naming conventions
                if func_name != "anonymous" and not func_name.startswith('_') and not func_name[0].islower():
                    findings.append(AnalyzerFinding(
                        rule_id="JS_FUNCTION_NAMING",
                        message=f"Function name '{func_name}' should start with lowercase letter",
                        file_path=file_path,
                        line_number=line_num,
                        severity=SeverityLevel.MEDIUM,
                        category="style",
                        score_impact=-2.0,
                        metadata={"function_name": func_name},
                    ))
            
            if self.patterns["class"].search(line):
                file_metrics.class_count += 1
                class_match = self.patterns["class"].search(line)
                class_name = class_match.group(1) or class_match.group(2) or "Anonymous"
                
                # Check class naming convention
                if class_name != "Anonymous" and not class_name[0].isupper():
                    findings.append(AnalyzerFinding(
                        rule_id="JS_CLASS_NAMING",
                        message=f"Class name '{class_name}' should start with uppercase letter (PascalCase)",
                        file_path=file_path,
                        line_number=line_num,
                        severity=SeverityLevel.MEDIUM,
                        category="style",
                        score_impact=-3.0,
                        metadata={"class_name": class_name},
                    ))
            
            if self.patterns["async_function"].search(line):
                file_metrics.async_function_count += 1
            
            if self.patterns["arrow_function"].search(line):
                file_metrics.arrow_function_count += 1
            
            # Check for console.log statements (should be removed in production)
            if self.patterns["console_log"].search(line):
                findings.append(AnalyzerFinding(
                    rule_id="JS_CONSOLE_LOG",
                    message="Remove console.log statements before production",
                    file_path=file_path,
                    line_number=line_num,
                    severity=SeverityLevel.MEDIUM,
                    category="debugging",
                    score_impact=-2.0,
                    metadata={"console_line": line},
                ))
            
            # Check for var declarations (prefer const/let)
            if self.patterns["var_declaration"].search(line):
                findings.append(AnalyzerFinding(
                    rule_id="JS_VAR_DECLARATION",
                    message="Use 'const' or 'let' instead of 'var' for better scoping",
                    file_path=file_path,
                    line_number=line_num,
                    severity=SeverityLevel.MEDIUM,
                    category="style",
                    score_impact=-2.0,
                    metadata={"var_line": line},
                ))
            
            # TypeScript-specific checks
            if self.is_typescript:
                if self.patterns["any_type"].search(line):
                    findings.append(AnalyzerFinding(
                        rule_id="TS_ANY_TYPE",
                        message="Avoid using 'any' type - use specific types for better type safety",
                        file_path=file_path,
                        line_number=line_num,
                        severity=SeverityLevel.HIGH,
                        category="typescript",
                        score_impact=-4.0,
                        metadata={"any_line": line},
                    ))
                
                if self.patterns["typescript_interface"].search(line):
                    interface_match = self.patterns["typescript_interface"].search(line)
                    interface_name = interface_match.group(1) if interface_match else "Unknown"
                    
                    # Check interface naming convention
                    if not interface_name.startswith('I'):
                        findings.append(AnalyzerFinding(
                            rule_id="TS_INTERFACE_NAMING",
                            message=f"Interface '{interface_name}' should start with 'I' prefix",
                            file_path=file_path,
                            line_number=line_num,
                            severity=SeverityLevel.LOW,
                            category="typescript",
                            score_impact=-1.0,
                            metadata={"interface_name": interface_name},
                        ))
            
            # Calculate cyclomatic complexity
            complexity_matches = self.patterns["cyclomatic_complexity"].findall(line)
            file_metrics.cyclomatic_complexity += len(complexity_matches)
        
        # Add file-level findings
        if file_metrics.lines_of_code > 300:
            findings.append(AnalyzerFinding(
                rule_id="JS_LONG_FILE",
                message=f"JavaScript/TypeScript file is too long ({file_metrics.lines_of_code} lines)",
                file_path=file_path,
                line_number=1,
                severity=SeverityLevel.HIGH,
                category="complexity",
                score_impact=-5.0,
                metadata={"lines_of_code": file_metrics.lines_of_code},
            ))
        
        if file_metrics.cyclomatic_complexity > 15:
            findings.append(AnalyzerFinding(
                rule_id="JS_HIGH_COMPLEXITY",
                message=f"File has high cyclomatic complexity ({file_metrics.cyclomatic_complexity})",
                file_path=file_path,
                line_number=1,
                severity=SeverityLevel.HIGH,
                category="complexity",
                score_impact=-7.0,
                metadata={"cyclomatic_complexity": file_metrics.cyclomatic_complexity},
            ))
        
        # Check for too many functions in one file
        if file_metrics.function_count > 15:
            findings.append(AnalyzerFinding(
                rule_id="JS_TOO_MANY_FUNCTIONS",
                message=f"File has too many functions ({file_metrics.function_count}) - consider splitting",
                file_path=file_path,
                line_number=1,
                severity=SeverityLevel.MEDIUM,
                category="architecture",
                score_impact=-3.0,
                metadata={"function_count": file_metrics.function_count},
            ))
        
        # Update global metrics
        self.metrics.function_count += file_metrics.function_count
        self.metrics.class_count += file_metrics.class_count
        self.metrics.import_count += file_metrics.import_count
        self.metrics.export_count += file_metrics.export_count
        self.metrics.cyclomatic_complexity += file_metrics.cyclomatic_complexity
        self.metrics.lines_of_code += file_metrics.lines_of_code
        self.metrics.comment_lines += file_metrics.comment_lines
        self.metrics.async_function_count += file_metrics.async_function_count
        self.metrics.arrow_function_count += file_metrics.arrow_function_count
        
        return findings
    
    def _generate_metric_findings(self) -> List[AnalyzerFinding]:
        """Generate findings based on aggregate metrics."""
        findings = []
        
        # Check comment ratio
        if self.metrics.lines_of_code > 0:
            comment_ratio = self.metrics.comment_lines / (self.metrics.lines_of_code + self.metrics.comment_lines)
            if comment_ratio < 0.12:
                findings.append(AnalyzerFinding(
                    rule_id="JS_LOW_COMMENT_RATIO",
                    message=f"Low comment ratio ({comment_ratio:.2%}) - JavaScript code needs documentation",
                    file_path=Path("project"),
                    line_number=1,
                    severity=SeverityLevel.MEDIUM,
                    category="documentation",
                    score_impact=-3.0,
                    metadata={"comment_ratio": comment_ratio},
                ))
        
        # Check async function usage
        if self.metrics.function_count > 0:
            async_ratio = self.metrics.async_function_count / self.metrics.function_count
            if async_ratio > 0.5:
                findings.append(AnalyzerFinding(
                    rule_id="JS_HIGH_ASYNC_RATIO",
                    message=f"High async function ratio ({async_ratio:.2%}) - consider simplifying async patterns",
                    file_path=Path("project"),
                    line_number=1,
                    severity=SeverityLevel.LOW,
                    category="complexity",
                    score_impact=-2.0,
                    metadata={"async_ratio": async_ratio},
                ))
        
        return findings
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return analysis metrics."""
        return {
            "language": "javascript" if not self.is_typescript else "typescript",
            "function_count": self.metrics.function_count,
            "class_count": self.metrics.class_count,
            "import_count": self.metrics.import_count,
            "export_count": self.metrics.export_count,
            "async_function_count": self.metrics.async_function_count,
            "arrow_function_count": self.metrics.arrow_function_count,
            "cyclomatic_complexity": self.metrics.cyclomatic_complexity,
            "lines_of_code": self.metrics.lines_of_code,
            "comment_lines": self.metrics.comment_lines,
        }
