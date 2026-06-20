"""Base class for educational rule sets."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..models import SeverityLevel


class EducationalLevel(Enum):
    """Educational levels for rule targeting."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class EducationalRule:
    """A single educational rule with learning context."""
    rule_id: str
    title: str
    description: str
    educational_level: EducationalLevel
    learning_objective: str
    common_mistake: str
    best_practice: str
    improvement_suggestion: str
    resources: List[str]  # Links to learning resources
    severity: SeverityLevel
    score_impact: float
    tags: List[str]


@dataclass
class EducationalFeedback:
    """Structured feedback for educational purposes."""
    rule_id: str
    title: str
    what_is_wrong: str
    why_it_matters: str
    how_to_fix: str
    example_before: str
    example_after: str
    additional_resources: List[str]
    next_steps: List[str]


class EducationalRuleSet(ABC):
    """Base class for language-specific educational rule sets."""
    
    def __init__(self, language: str):
        self.language = language
        self.rules = self._load_rules()
    
    @abstractmethod
    def _load_rules(self) -> Dict[str, EducationalRule]:
        """Load language-specific educational rules."""
        pass
    
    def get_rule(self, rule_id: str) -> Optional[EducationalRule]:
        """Get a specific educational rule by ID."""
        return self.rules.get(rule_id)
    
    def get_rules_by_level(self, level: EducationalLevel) -> List[EducationalRule]:
        """Get all rules for a specific educational level."""
        return [rule for rule in self.rules.values() if rule.educational_level == level]
    
    def get_rules_by_tag(self, tag: str) -> List[EducationalRule]:
        """Get all rules with a specific tag."""
        return [rule for rule in self.rules.values() if tag in rule.tags]
    
    def generate_feedback(self, rule_id: str, context: Dict[str, Any]) -> EducationalFeedback:
        """Generate educational feedback for a specific rule."""
        rule = self.get_rule(rule_id)
        if not rule:
            raise ValueError(f"Rule {rule_id} not found")
        
        return EducationalFeedback(
            rule_id=rule.rule_id,
            title=rule.title,
            what_is_wrong=rule.common_mistake,
            why_it_matters=rule.learning_objective,
            how_to_fix=rule.improvement_suggestion,
            example_before=self._get_bad_example(rule_id, context),
            example_after=self._get_good_example(rule_id, context),
            additional_resources=rule.resources,
            next_steps=self._get_next_steps(rule_id, context),
        )
    
    def _get_bad_example(self, rule_id: str, context: Dict[str, Any]) -> str:
        """Get a bad code example for this rule."""
        return "// Bad example - see specific rule implementation"
    
    def _get_good_example(self, rule_id: str, context: Dict[str, Any]) -> str:
        """Get a good code example for this rule."""
        return "// Good example - see specific rule implementation"
    
    def _get_next_steps(self, rule_id: str, context: Dict[str, Any]) -> List[str]:
        """Get next learning steps for this rule."""
        return [
            "Practice this concept with simple exercises",
            "Review the learning resources provided",
            "Apply this pattern in your next project"
        ]
    
    def get_educational_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate an educational summary of analysis findings."""
        rule_counts = {}
        level_counts = {level.value: 0 for level in EducationalLevel}
        tag_counts = {}
        
        for finding in findings:
            rule_id = finding.get("rule_id", "unknown")
            rule = self.get_rule(rule_id)
            
            if rule:
                rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1
                level_counts[rule.educational_level.value] += 1
                
                for tag in rule.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            "language": self.language,
            "total_rules_violated": len(rule_counts),
            "rules_by_frequency": sorted(rule_counts.items(), key=lambda x: x[1], reverse=True),
            "educational_level_distribution": level_counts,
            "topic_distribution": tag_counts,
            "focus_areas": self._get_focus_areas(rule_counts, tag_counts),
            "recommended_learning_path": self._get_learning_path(level_counts),
        }
    
    def _get_focus_areas(self, rule_counts: Dict[str, int], tag_counts: Dict[str, int]) -> List[str]:
        """Determine focus areas based on rule violations."""
        # Get top 3 most violated tags
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        return [tag for tag, count in top_tags]
    
    def _get_learning_path(self, level_counts: Dict[str, int]) -> List[str]:
        """Suggest a learning path based on violation levels."""
        path = []
        
        if level_counts[EducationalLevel.BEGINNER.value] > 0:
            path.append("Focus on fundamental concepts and basic syntax")
        
        if level_counts[EducationalLevel.INTERMEDIATE.value] > 0:
            path.append("Work on intermediate patterns and best practices")
        
        if level_counts[EducationalLevel.ADVANCED.value] > 0:
            path.append("Explore advanced techniques and optimization")
        
        if not path:
            path.append("Great job! Focus on code organization and documentation")
        
        return path
