"""Educational rule sets for Skills code analysis pipeline."""

from .base import EducationalRuleSet
from .python_rules import PythonEducationalRules
from .java_rules import JavaEducationalRules
from .cpp_rules import CppEducationalRules
from .javascript_rules import JavaScriptEducationalRules

EDUCATIONAL_RULES = {
    "python": PythonEducationalRules(),
    "java": JavaEducationalRules(),
    "cpp": CppEducationalRules(),
    "javascript": JavaScriptEducationalRules(),
    "typescript": JavaScriptEducationalRules(),
}

__all__ = [
    "EducationalRuleSet",
    "PythonEducationalRules",
    "JavaEducationalRules", 
    "CppEducationalRules",
    "JavaScriptEducationalRules",
    "EDUCATIONAL_RULES",
]
