"""Quality metrics calculation for Skills code analysis."""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum

from ..models import AnalyzerFinding, SeverityLevel


class MetricCategory(Enum):
    """Categories for quality metrics."""
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    STYLE = "style"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    DOCUMENTATION = "documentation"


@dataclass
class QualityMetric:
    """A single quality metric with score and details."""
    name: str
    category: MetricCategory
    score: float  # 0-100
    weight: float  # Importance weight (0-1)
    description: str
    details: Dict[str, Any]
    findings_count: int
    severity_distribution: Dict[str, int]


@dataclass
class QualityScore:
    """Overall quality score with breakdown."""
    overall_score: float  # 0-100
    confidence: float  # 0-1
    metrics: List[QualityMetric]
    grade: str  # A-F
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


class QualityMetricsCalculator:
    """Calculates quality metrics from analyzer findings."""
    
    def __init__(self):
        # Category weights for overall score calculation
        self.category_weights = {
            MetricCategory.COMPLEXITY: 0.25,
            MetricCategory.MAINTAINABILITY: 0.20,
            MetricCategory.SECURITY: 0.20,
            MetricCategory.STYLE: 0.15,
            MetricCategory.PERFORMANCE: 0.10,
            MetricCategory.RELIABILITY: 0.05,
            MetricCategory.DOCUMENTATION: 0.05,
        }
        
        # Severity impact scores
        self.severity_impacts = {
            SeverityLevel.CRITICAL: -10.0,
            SeverityLevel.HIGH: -5.0,
            SeverityLevel.MEDIUM: -2.0,
            SeverityLevel.LOW: -1.0,
            SeverityLevel.INFO: -0.5,
        }
    
    def calculate_metrics(self, findings: List[AnalyzerFinding], language: str) -> QualityScore:
        """Calculate quality metrics from analyzer findings."""
        # Group findings by category
        categorized_findings = self._categorize_findings(findings)
        
        # Calculate individual metrics
        metrics = []
        for category, category_findings in categorized_findings.items():
            metric = self._calculate_category_metric(category, category_findings, language)
            metrics.append(metric)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(metrics)
        confidence = self._calculate_confidence(findings, metrics)
        grade = self._calculate_grade(overall_score)
        
        # Generate insights
        strengths = self._identify_strengths(metrics)
        weaknesses = self._identify_weaknesses(metrics)
        recommendations = self._generate_recommendations(metrics, language)
        
        return QualityScore(
            overall_score=overall_score,
            confidence=confidence,
            metrics=metrics,
            grade=grade,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )
    
    def _categorize_findings(self, findings: List[AnalyzerFinding]) -> Dict[MetricCategory, List[AnalyzerFinding]]:
        """Categorize findings by quality metric."""
        categorized = {category: [] for category in MetricCategory}
        
        for finding in findings:
            category = self._determine_category(finding)
            categorized[category].append(finding)
        
        return categorized
    
    def _determine_category(self, finding: AnalyzerFinding) -> MetricCategory:
        """Determine the quality category for a finding."""
        # Rule-based categorization
        rule_category_mapping = {
            # Complexity
            "complexity": MetricCategory.COMPLEXITY,
            "HIGH_COMPLEXITY": MetricCategory.COMPLEXITY,
            "LONG_METHOD": MetricCategory.COMPLEXITY,
            "LONG_FUNCTION": MetricCategory.COMPLEXITY,
            "TOO_MANY_PARAMETERS": MetricCategory.COMPLEXITY,
            
            # Maintainability
            "maintainability": MetricCategory.MAINTAINABILITY,
            "naming": MetricCategory.MAINTAINABILITY,
            "MAGIC_NUMBERS": MetricCategory.MAINTAINABILITY,
            "LONG_FILE": MetricCategory.MAINTAINABILITY,
            "TOO_MANY_CLASSES": MetricCategory.MAINTAINABILITY,
            
            # Security
            "security": MetricCategory.SECURITY,
            "DANGEROUS_MACRO": MetricCategory.SECURITY,
            "BITS_INCLUDE": MetricCategory.SECURITY,
            "PUBLIC_FIELDS": MetricCategory.SECURITY,
            
            # Style
            "style": MetricCategory.STYLE,
            "CLASS_NAMING": MetricCategory.STYLE,
            "METHOD_NAMING": MetricCategory.STYLE,
            "FUNCTION_NAMING": MetricCategory.STYLE,
            "VAR_DECLARATION": MetricCategory.STYLE,
            "CONSOLE_LOG": MetricCategory.STYLE,
            "GOTO_STATEMENT": MetricCategory.STYLE,
            
            # Performance
            "performance": MetricCategory.PERFORMANCE,
            "RAW_MEMORY_ALLOCATION": MetricCategory.PERFORMANCE,
            "STRING_CONCATENATION": MetricCategory.PERFORMANCE,
            "HIGH_ASYNC_RATIO": MetricCategory.PERFORMANCE,
            
            # Reliability
            "reliability": MetricCategory.RELIABILITY,
            "error": MetricCategory.RELIABILITY,
            "EXCEPTION_HANDLING": MetricCategory.RELIABILITY,
            "MISSING_INCLUDE_GUARD": MetricCategory.RELIABILITY,
            
            # Documentation
            "documentation": MetricCategory.DOCUMENTATION,
            "LOW_COMMENT_RATIO": MetricCategory.DOCUMENTATION,
            "MISSING_DOCSTRINGS": MetricCategory.DOCUMENTATION,
        }
        
        # Check rule_id first
        for pattern, category in rule_category_mapping.items():
            if pattern in finding.rule_id:
                return category
        
        # Check category field
        if finding.category in rule_category_mapping:
            return rule_category_mapping[finding.category]
        
        # Default to maintainability
        return MetricCategory.MAINTAINABILITY
    
    def _calculate_category_metric(self, category: MetricCategory, findings: List[AnalyzerFinding], language: str) -> QualityMetric:
        """Calculate metric for a specific category."""
        if not findings:
            return QualityMetric(
                name=category.value.title(),
                category=category,
                score=100.0,  # Perfect score if no findings
                weight=self.category_weights[category],
                description=f"No {category.value} issues found",
                details={"language": language},
                findings_count=0,
                severity_distribution={level.value: 0 for level in SeverityLevel},
            )
        
        # Calculate base score from findings
        base_score = 100.0
        severity_counts = {level.value: 0 for level in SeverityLevel}
        
        for finding in findings:
            impact = self.severity_impacts.get(finding.severity, -1.0)
            base_score += impact
            severity_counts[finding.severity.value] += 1
        
        # Apply category-specific adjustments
        adjusted_score = self._apply_category_adjustments(category, base_score, findings, language)
        
        # Ensure score is within bounds
        final_score = max(0, min(100, adjusted_score))
        
        return QualityMetric(
            name=category.value.title(),
            category=category,
            score=final_score,
            weight=self.category_weights[category],
            description=self._get_metric_description(category, final_score),
            details={
                "language": language,
                "base_score": base_score,
                "adjusted_score": adjusted_score,
                "findings_summary": self._summarize_findings(findings),
            },
            findings_count=len(findings),
            severity_distribution=severity_counts,
        )
    
    def _apply_category_adjustments(self, category: MetricCategory, base_score: float, findings: List[AnalyzerFinding], language: str) -> float:
        """Apply category-specific score adjustments."""
        adjusted_score = base_score
        
        if category == MetricCategory.COMPLEXITY:
            # Penalize heavily for complexity issues
            critical_count = sum(1 for f in findings if f.severity == SeverityLevel.CRITICAL)
            if critical_count > 0:
                adjusted_score -= critical_count * 5  # Extra penalty for critical complexity issues
        
        elif category == MetricCategory.SECURITY:
            # Security issues are very important
            high_count = sum(1 for f in findings if f.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH])
            if high_count > 0:
                adjusted_score -= high_count * 3  # Extra penalty for high-severity security issues
        
        elif category == MetricCategory.DOCUMENTATION:
            # Be more lenient with documentation for beginners
            low_count = sum(1 for f in findings if f.severity == SeverityLevel.LOW)
            if low_count > 0:
                adjusted_score += low_count * 0.5  # Small bonus for having some documentation issues
        
        elif category == MetricCategory.STYLE:
            # Style issues are less critical
            adjusted_score = max(60, adjusted_score)  # Minimum score for style issues
        
        return adjusted_score
    
    def _get_metric_description(self, category: MetricCategory, score: float) -> str:
        """Get description for a metric based on score."""
        if score >= 90:
            return f"Excellent {category.value} - very few issues"
        elif score >= 80:
            return f"Good {category.value} - some minor issues"
        elif score >= 70:
            return f"Fair {category.value} - moderate number of issues"
        elif score >= 60:
            return f"Poor {category.value} - many issues need attention"
        else:
            return f"Very Poor {category.value} - critical issues require immediate attention"
    
    def _summarize_findings(self, findings: List[AnalyzerFinding]) -> Dict[str, Any]:
        """Summarize findings for metric details."""
        rule_counts = {}
        file_counts = {}
        
        for finding in findings:
            rule_counts[finding.rule_id] = rule_counts.get(finding.rule_id, 0) + 1
            file_path = str(finding.file_path)
            file_counts[file_path] = file_counts.get(file_path, 0) + 1
        
        return {
            "most_common_rules": sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "most_affected_files": sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "total_rules_violated": len(rule_counts),
            "files_affected": len(file_counts),
        }
    
    def _calculate_overall_score(self, metrics: List[QualityMetric]) -> float:
        """Calculate overall weighted score."""
        if not metrics:
            return 100.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric in metrics:
            weighted_sum += metric.score * metric.weight
            total_weight += metric.weight
        
        return weighted_sum / total_weight if total_weight > 0 else 100.0
    
    def _calculate_confidence(self, findings: List[AnalyzerFinding], metrics: List[QualityMetric]) -> float:
        """Calculate confidence in the score."""
        if not findings:
            return 0.3  # Low confidence with no findings
        
        # Confidence based on number of findings and metrics coverage
        finding_confidence = min(1.0, len(findings) / 20.0)  # More findings = higher confidence
        metric_confidence = len(metrics) / len(MetricCategory)  # More categories = higher confidence
        
        return (finding_confidence + metric_confidence) / 2.0
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score."""
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
    
    def _identify_strengths(self, metrics: List[QualityMetric]) -> List[str]:
        """Identify code strengths from metrics."""
        strengths = []
        
        for metric in metrics:
            if metric.score >= 85:
                strengths.append(f"Excellent {metric.category.value} (score: {metric.score:.1f})")
            elif metric.findings_count == 0:
                strengths.append(f"No {metric.category.value} issues found")
        
        if not strengths:
            strengths.append("Code follows basic quality standards")
        
        return strengths
    
    def _identify_weaknesses(self, metrics: List[QualityMetric]) -> List[str]:
        """Identify code weaknesses from metrics."""
        weaknesses = []
        
        for metric in metrics:
            if metric.score < 60:
                weaknesses.append(f"Poor {metric.category.value} (score: {metric.score:.1f})")
            elif metric.findings_count > 10:
                weaknesses.append(f"Many {metric.category.value} issues ({metric.findings_count} findings)")
        
        return weaknesses
    
    def _generate_recommendations(self, metrics: List[QualityMetric], language: str) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        # Sort metrics by score (worst first)
        sorted_metrics = sorted(metrics, key=lambda m: m.score)
        
        for metric in sorted_metrics[:3]:  # Top 3 worst metrics
            if metric.score < 80:
                recommendations.extend(self._get_category_recommendations(metric.category, language))
        
        if not recommendations:
            recommendations.append("Continue following current coding practices")
        
        return recommendations
    
    def _get_category_recommendations(self, category: MetricCategory, language: str) -> List[str]:
        """Get specific recommendations for a category."""
        recommendations = {
            MetricCategory.COMPLEXITY: [
                "Break large functions into smaller, focused functions",
                "Reduce cyclomatic complexity by simplifying control flow",
                "Consider design patterns to reduce complexity",
            ],
            MetricCategory.MAINTAINABILITY: [
                "Follow consistent naming conventions",
                "Extract magic numbers into named constants",
                "Add meaningful comments and documentation",
            ],
            MetricCategory.SECURITY: [
                "Review and fix security vulnerabilities",
                "Use secure coding practices",
                "Validate all user inputs",
            ],
            MetricCategory.STYLE: [
                "Follow language-specific style guides",
                "Use a linter to catch style issues",
                "Format code consistently",
            ],
            MetricCategory.PERFORMANCE: [
                "Optimize algorithms and data structures",
                "Reduce unnecessary computations",
                "Use efficient memory management",
            ],
            MetricCategory.RELIABILITY: [
                "Add proper error handling",
                "Improve exception handling",
                "Add input validation",
            ],
            MetricCategory.DOCUMENTATION: [
                "Add docstrings to functions and classes",
                "Document complex algorithms",
                "Add inline comments for unclear code",
            ],
        }
        
        return recommendations.get(category, ["Focus on improving code quality"])
