"""Educational feedback system for Skills code analysis."""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum

from ..models import AnalyzerFinding, SeverityLevel
from ..rules.base import EducationalRuleSet
from .quality_calculator import QualityScore, MetricCategory


class FeedbackType(Enum):
    """Types of educational feedback."""
    IMMEDIATE = "immediate"  # Quick fixes and suggestions
    LEARNING = "learning"   # Educational explanations
    IMPROVEMENT = "improvement"  # Structured improvement plan
    ENCOURAGEMENT = "encouragement"  # Positive reinforcement


class LearningPath(Enum):
    """Learning paths based on skill level."""
    BEGINNER_FOCUS = "beginner_focus"
    INTERMEDIATE_GROWTH = "intermediate_growth"
    ADVANCED_MASTERY = "advanced_mastery"
    MIXED_LEVEL = "mixed_level"


@dataclass
class FeedbackItem:
    """A single feedback item with context and actions."""
    type: FeedbackType
    title: str
    message: str
    priority: int  # 1-10, higher = more important
    actionable: bool
    estimated_effort: str  # "quick", "moderate", "significant"
    related_findings: List[str]  # Rule IDs
    learning_resources: List[str]
    next_steps: List[str]


@dataclass
class LearningRecommendation:
    """A learning recommendation for skill development."""
    skill_area: str
    current_level: str
    target_level: str
    description: str
    resources: List[Dict[str, str]]
    practice_exercises: List[str]
    estimated_time: str
    prerequisites: List[str]


@dataclass
class EducationalFeedback:
    """Comprehensive educational feedback for a code analysis."""
    overall_summary: str
    grade: str
    strengths: List[str]
    improvement_areas: List[str]
    feedback_items: List[FeedbackItem]
    learning_path: LearningPath
    recommendations: List[LearningRecommendation]
    progress_indicators: Dict[str, Any]
    motivational_message: str


class EducationalFeedbackGenerator:
    """Generates educational feedback from analysis results."""
    
    def __init__(self):
        # Learning resource mappings
        self.resource_library = {
            "python": {
                "naming": [
                    {"title": "PEP 8 Style Guide", "url": "https://pep8.org/"},
                    {"title": "Python Naming Conventions", "url": "https://realpython.com/python-pep8/"},
                ],
                "functions": [
                    {"title": "Writing Clean Functions", "url": "https://realpython.com/python-clean-code/"},
                    {"title": "Function Best Practices", "url": "https://docs.python.org/3/tutorial/controlflow.html#defining-functions"},
                ],
                "complexity": [
                    {"title": "Understanding Cyclomatic Complexity", "url": "https://en.wikipedia.org/wiki/Cyclomatic_complexity"},
                    {"title": "Refactoring Complex Functions", "url": "https://refactoring.guide/extract-function.html"},
                ],
                "documentation": [
                    {"title": "Python Docstrings", "url": "https://pep8.org/#docstrings"},
                    {"title": "Writing Good Documentation", "url": "https://realpython.com/documenting-python-code/"},
                ],
            },
            "java": {
                "naming": [
                    {"title": "Java Naming Conventions", "url": "https://www.oracle.com/java/technologies/javase/codeconventions-namingconventions.html"},
                    {"title": "Clean Code in Java", "url": "https://clean-code-developer.com/"},
                ],
                "oop": [
                    {"title": "Java OOP Best Practices", "url": "https://www.baeldung.com/java-oop"},
                    {"title": "Design Patterns in Java", "url": "https://refactoring.guru/design-patterns/java"},
                ],
                "exception_handling": [
                    {"title": "Java Exception Handling", "url": "https://www.baeldung.com/java-exceptions"},
                    {"title": "Best Practices for Exceptions", "url": "https://docs.oracle.com/javase/tutorial/essential/exceptions/"},
                ],
            },
            "javascript": {
                "modern_js": [
                    {"title": "Modern JavaScript Features", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript"},
                    {"title": "ES6+ Features", "url": "https://github.com/lukehoban/es6features"},
                ],
                "async": [
                    {"title": "Async/Await Guide", "url": "https://javascript.info/async-await"},
                    {"title": "JavaScript Promises", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise"},
                ],
                "best_practices": [
                    {"title": "JavaScript Best Practices", "url": "https://github.com/ryanmcdermott/clean-code-javascript"},
                    {"title": "Airbnb Style Guide", "url": "https://airbnb.io/javascript/"},
                ],
            },
            "cpp": {
                "modern_cpp": [
                    {"title": "Modern C++ Features", "url": "https://github.com/AnthonyCalandra/modern-cpp-features"},
                    {"title": "C++ Core Guidelines", "url": "https://isocpp.github.io/CppCoreGuidelines/"},
                ],
                "memory": [
                    {"title": "Smart Pointers", "url": "https://www.cplusplus.com/memory/"},
                    {"title": "RAII in C++", "url": "https://en.cppreference.com/w/cpp/language/raii"},
                ],
                "best_practices": [
                    {"title": "C++ Best Practices", "url": "https://isocpp.github.io/CppCoreGuidelines/"},
                    {"title": "Google C++ Style Guide", "url": "https://google.github.io/styleguide/cppguide.html"},
                ],
            },
        }
    
    def generate_feedback(self, 
                         findings: List[AnalyzerFinding], 
                         quality_score: QualityScore, 
                         language: str,
                         educational_rules: Optional[EducationalRuleSet] = None) -> EducationalFeedback:
        """Generate comprehensive educational feedback."""
        
        # Determine learning path
        learning_path = self._determine_learning_path(quality_score, findings)
        
        # Generate feedback items
        feedback_items = self._generate_feedback_items(findings, quality_score, language, educational_rules)
        
        # Generate learning recommendations
        recommendations = self._generate_learning_recommendations(quality_score, language, learning_path)
        
        # Create overall summary
        overall_summary = self._create_overall_summary(quality_score, findings)
        
        # Generate motivational message
        motivational_message = self._generate_motivational_message(quality_score, learning_path)
        
        # Calculate progress indicators
        progress_indicators = self._calculate_progress_indicators(findings, quality_score)
        
        return EducationalFeedback(
            overall_summary=overall_summary,
            grade=quality_score.grade,
            strengths=quality_score.strengths,
            improvement_areas=quality_score.weaknesses,
            feedback_items=feedback_items,
            learning_path=learning_path,
            recommendations=recommendations,
            progress_indicators=progress_indicators,
            motivational_message=motivational_message,
        )
    
    def _determine_learning_path(self, quality_score: QualityScore, findings: List[AnalyzerFinding]) -> LearningPath:
        """Determine the appropriate learning path based on performance."""
        score = quality_score.overall_score
        
        # Count issues by severity
        critical_issues = sum(1 for f in findings if f.severity == SeverityLevel.CRITICAL)
        high_issues = sum(1 for f in findings if f.severity == SeverityLevel.HIGH)
        
        if score >= 85 and critical_issues == 0 and high_issues <= 1:
            return LearningPath.ADVANCED_MASTERY
        elif score >= 70 and critical_issues == 0:
            return LearningPath.INTERMEDIATE_GROWTH
        elif score >= 50:
            return LearningPath.BEGINNER_FOCUS
        else:
            return LearningPath.MIXED_LEVEL
    
    def _generate_feedback_items(self, 
                                findings: List[AnalyzerFinding], 
                                quality_score: QualityScore, 
                                language: str,
                                educational_rules: Optional[EducationalRuleSet]) -> List[FeedbackItem]:
        """Generate specific feedback items from findings."""
        feedback_items = []
        
        # Group findings by category and severity
        critical_findings = [f for f in findings if f.severity == SeverityLevel.CRITICAL]
        high_findings = [f for f in findings if f.severity == SeverityLevel.HIGH]
        
        # Generate immediate feedback for critical issues
        for finding in critical_findings[:3]:  # Top 3 critical issues
            item = self._create_immediate_feedback(finding, language, educational_rules)
            feedback_items.append(item)
        
        # Generate learning feedback for high-priority issues
        for finding in high_findings[:3]:  # Top 3 high issues
            item = self._create_learning_feedback(finding, language, educational_rules)
            feedback_items.append(item)
        
        # Generate improvement feedback for the worst quality areas
        worst_metrics = sorted(quality_score.metrics, key=lambda m: m.score)[:2]
        for metric in worst_metrics:
            item = self._create_improvement_feedback(metric, language)
            feedback_items.append(item)
        
        # Add encouragement if score is good
        if quality_score.overall_score >= 80:
            item = self._create_encouragement_feedback(quality_score)
            feedback_items.append(item)
        
        # Sort by priority
        feedback_items.sort(key=lambda x: x.priority, reverse=True)
        
        return feedback_items
    
    def _create_immediate_feedback(self, 
                                  finding: AnalyzerFinding, 
                                  language: str,
                                  educational_rules: Optional[EducationalRuleSet]) -> FeedbackItem:
        """Create immediate feedback for critical issues."""
        educational_context = self._extract_educational_context(finding, educational_rules)
        
        return FeedbackItem(
            type=FeedbackType.IMMEDIATE,
            title=f"Fix Critical Issue: {finding.rule_id}",
            message=finding.message,
            priority=10,
            actionable=True,
            estimated_effort="quick",
            related_findings=[finding.rule_id],
            learning_resources=educational_context.get("resources", []),
            next_steps=educational_context.get("next_steps", ["Fix this issue immediately"]),
        )
    
    def _create_learning_feedback(self, 
                                 finding: AnalyzerFinding, 
                                 language: str,
                                 educational_rules: Optional[EducationalRuleSet]) -> FeedbackItem:
        """Create learning feedback for high-priority issues."""
        educational_context = self._extract_educational_context(finding, educational_rules)
        
        return FeedbackItem(
            type=FeedbackType.LEARNING,
            title=f"Learn: {finding.rule_id}",
            message=educational_context.get("learning_objective", finding.message),
            priority=8,
            actionable=True,
            estimated_effort="moderate",
            related_findings=[finding.rule_id],
            learning_resources=educational_context.get("resources", []),
            next_steps=educational_context.get("next_steps", ["Study this concept"]),
        )
    
    def _create_improvement_feedback(self, metric, language: str) -> FeedbackItem:
        """Create improvement feedback for quality metrics."""
        resources = self._get_metric_resources(metric.category, language)
        
        return FeedbackItem(
            type=FeedbackType.IMPROVEMENT,
            title=f"Improve {metric.category.value}",
            message=f"Focus on improving {metric.category.value} (current score: {metric.score:.1f})",
            priority=6,
            actionable=True,
            estimated_effort="significant",
            related_findings=[],
            learning_resources=resources,
            next_steps=[f"Practice {metric.category.value} exercises", "Review related documentation"],
        )
    
    def _create_encouragement_feedback(self, quality_score: QualityScore) -> FeedbackItem:
        """Create encouragement feedback for good performance."""
        return FeedbackItem(
            type=FeedbackType.ENCOURAGEMENT,
            title="Great Job!",
            message=f"Your code quality is excellent (Score: {quality_score.overall_score:.1f})",
            priority=5,
            actionable=False,
            estimated_effort="none",
            related_findings=[],
            learning_resources=[],
            next_steps=["Continue following best practices", "Help others learn"],
        )
    
    def _extract_educational_context(self, 
                                   finding: AnalyzerFinding, 
                                   educational_rules: Optional[EducationalRuleSet]) -> Dict[str, Any]:
        """Extract educational context from a finding."""
        if educational_rules:
            rule = educational_rules.get_rule(finding.rule_id)
            if rule:
                return {
                    "learning_objective": rule.learning_objective,
                    "resources": rule.resources,
                    "next_steps": educational_rules._get_next_steps(finding.rule_id, {}),
                    "improvement_suggestion": rule.improvement_suggestion,
                }
        
        # Fallback to finding metadata
        return {
            "learning_objective": finding.metadata.get("learning_objective", "Learn best practices"),
            "resources": finding.metadata.get("resources", []),
            "next_steps": finding.metadata.get("next_steps", ["Study this concept"]),
            "improvement_suggestion": finding.metadata.get("improvement_suggestion", "Improve this code"),
        }
    
    def _get_metric_resources(self, category: MetricCategory, language: str) -> List[str]:
        """Get learning resources for a specific metric category."""
        language_resources = self.resource_library.get(language, {})
        
        # Map categories to resource keys
        category_mapping = {
            MetricCategory.STYLE: "naming",
            MetricCategory.MAINTAINABILITY: "naming",
            MetricCategory.DOCUMENTATION: "documentation",
            MetricCategory.COMPLEXITY: "complexity",
            MetricCategory.RELIABILITY: "best_practices",
            MetricCategory.SECURITY: "best_practices",
            MetricCategory.PERFORMANCE: "best_practices",
        }
        
        resource_key = category_mapping.get(category, "best_practices")
        resources = language_resources.get(resource_key, [])
        
        return [r["url"] for r in resources]
    
    def _generate_learning_recommendations(self, 
                                          quality_score: QualityScore, 
                                          language: str,
                                          learning_path: LearningPath) -> List[LearningRecommendation]:
        """Generate personalized learning recommendations."""
        recommendations = []
        
        # Get worst metrics
        worst_metrics = sorted(quality_score.metrics, key=lambda m: m.score)[:3]
        
        for metric in worst_metrics:
            if metric.score < 80:
                recommendation = self._create_metric_recommendation(metric, language, learning_path)
                recommendations.append(recommendation)
        
        # Add general recommendations based on learning path
        general_rec = self._create_general_recommendation(learning_path, language)
        if general_rec:
            recommendations.append(general_rec)
        
        return recommendations
    
    def _create_metric_recommendation(self, 
                                    metric, 
                                    language: str, 
                                    learning_path: LearningPath) -> LearningRecommendation:
        """Create a learning recommendation for a specific metric."""
        skill_area = metric.category.value
        current_level = self._get_skill_level_from_score(metric.score)
        target_level = self._get_target_level(learning_path)
        
        resources = self._get_metric_resources(metric.category, language)
        resource_objects = [{"title": f"Learn {skill_area}", "url": url} for url in resources]
        
        return LearningRecommendation(
            skill_area=skill_area,
            current_level=current_level,
            target_level=target_level,
            description=f"Improve your {skill_area} skills from {current_level} to {target_level} level",
            resources=resource_objects,
            practice_exercises=[
                f"Practice {skill_area} with small exercises",
                f"Refactor existing code to improve {skill_area}",
                f"Study and implement {skill_area} best practices",
            ],
            estimated_time="2-4 hours",
            prerequisites=self._get_prerequisites(metric.category),
        )
    
    def _create_general_recommendation(self, learning_path: LearningPath, language: str) -> Optional[LearningRecommendation]:
        """Create a general learning recommendation."""
        if learning_path == LearningPath.BEGINNER_FOCUS:
            return LearningRecommendation(
                skill_area="Fundamentals",
                current_level="beginner",
                target_level="intermediate",
                description="Build strong programming fundamentals",
                resources=[{"title": "Language Basics", "url": "https://docs.python.org/3/tutorial/"}],
                practice_exercises=["Complete basic coding exercises", "Build small projects"],
                estimated_time="1-2 weeks",
                prerequisites=["Basic computer skills"],
            )
        elif learning_path == LearningPath.INTERMEDIATE_GROWTH:
            return LearningRecommendation(
                skill_area="Best Practices",
                current_level="intermediate",
                target_level="advanced",
                description="Master programming best practices and design patterns",
                resources=[{"title": "Clean Code", "url": "https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350884"}],
                practice_exercises=["Refactor existing code", "Study design patterns"],
                estimated_time="2-3 weeks",
                prerequisites=["Solid programming fundamentals"],
            )
        
        return None
    
    def _get_skill_level_from_score(self, score: float) -> str:
        """Convert score to skill level description."""
        if score >= 90:
            return "expert"
        elif score >= 80:
            return "advanced"
        elif score >= 70:
            return "intermediate"
        elif score >= 60:
            return "developing"
        else:
            return "beginner"
    
    def _get_target_level(self, learning_path: LearningPath) -> str:
        """Get target skill level based on learning path."""
        mapping = {
            LearningPath.BEGINNER_FOCUS: "intermediate",
            LearningPath.INTERMEDIATE_GROWTH: "advanced",
            LearningPath.ADVANCED_MASTERY: "expert",
            LearningPath.MIXED_LEVEL: "intermediate",
        }
        return mapping.get(learning_path, "intermediate")
    
    def _get_prerequisites(self, category: MetricCategory) -> List[str]:
        """Get prerequisites for a skill area."""
        prerequisites = {
            MetricCategory.STYLE: ["Basic syntax knowledge"],
            MetricCategory.MAINTAINABILITY: ["Understanding of variables and functions"],
            MetricCategory.DOCUMENTATION: ["Basic programming knowledge"],
            MetricCategory.COMPLEXITY: ["Understanding of control flow"],
            MetricCategory.RELIABILITY: ["Knowledge of error handling basics"],
            MetricCategory.SECURITY: ["Understanding of input validation"],
            MetricCategory.PERFORMANCE: ["Basic algorithm knowledge"],
        }
        return prerequisites.get(category, [])
    
    def _create_overall_summary(self, quality_score: QualityScore, findings: List[AnalyzerFinding]) -> str:
        """Create an overall summary of the analysis."""
        score = quality_score.overall_score
        grade = quality_score.grade
        total_findings = len(findings)
        critical_issues = sum(1 for f in findings if f.severity == SeverityLevel.CRITICAL)
        
        if score >= 90:
            return f"Excellent work! Your code scored {score:.1f}/100 (Grade: {grade}) with only {total_findings} issues found."
        elif score >= 80:
            return f"Good job! Your code scored {score:.1f}/100 (Grade: {grade}) with {total_findings} issues to address."
        elif score >= 70:
            return f"Fair effort. Your code scored {score:.1f}/100 (Grade: {grade}) with {total_findings} issues needing attention."
        elif score >= 60:
            return f"Needs improvement. Your code scored {score:.1f}/100 (Grade: {grade}) with {total_findings} issues to fix."
        else:
            critical_msg = f" including {critical_issues} critical issues" if critical_issues > 0 else ""
            return f"Significant improvement needed. Your code scored {score:.1f}/100 (Grade: {grade}) with {total_findings} issues{critical_msg}."
    
    def _generate_motivational_message(self, quality_score: QualityScore, learning_path: LearningPath) -> str:
        """Generate a motivational message based on performance."""
        score = quality_score.overall_score
        
        if learning_path == LearningPath.ADVANCED_MASTERY:
            return "🌟 Outstanding! You're demonstrating advanced programming skills. Keep challenging yourself with complex problems!"
        elif learning_path == LearningPath.INTERMEDIATE_GROWTH:
            return "🚀 Great progress! You're building a strong foundation. Focus on consistency and best practices to reach the next level."
        elif learning_path == LearningPath.BEGINNER_FOCUS:
            return "🌱 You're on the right track! Every expert was once a beginner. Keep practicing and don't be afraid to ask questions."
        else:
            return "💪 Programming is a journey! Focus on one improvement at a time, and you'll see amazing progress."
    
    def _calculate_progress_indicators(self, findings: List[AnalyzerFinding], quality_score: QualityScore) -> Dict[str, Any]:
        """Calculate progress indicators for tracking improvement."""
        total_findings = len(findings)
        severity_counts = {level.value: 0 for level in SeverityLevel}
        
        for finding in findings:
            severity_counts[finding.severity.value] += 1
        
        return {
            "total_issues": total_findings,
            "severity_breakdown": severity_counts,
            "quality_score": quality_score.overall_score,
            "grade": quality_score.grade,
            "categories_analyzed": len(quality_score.metrics),
            "improvement_potential": max(0, 100 - quality_score.overall_score),
            "next_milestone": self._get_next_milestone(quality_score.overall_score),
        }
    
    def _get_next_milestone(self, current_score: float) -> str:
        """Get the next milestone based on current score."""
        if current_score < 60:
            return "Reach 60 points (Grade D)"
        elif current_score < 70:
            return "Reach 70 points (Grade C)"
        elif current_score < 80:
            return "Reach 80 points (Grade B)"
        elif current_score < 90:
            return "Reach 90 points (Grade A)"
        else:
            return "Maintain excellence (95+ points)"
