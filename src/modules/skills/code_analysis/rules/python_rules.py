"""Educational rules for Python code analysis."""

from typing import Dict, Any
from .base import EducationalRuleSet, EducationalRule, EducationalLevel
from ..models import SeverityLevel


class PythonEducationalRules(EducationalRuleSet):
    """Educational rules specifically designed for Python learners."""
    
    def __init__(self):
        super().__init__("python")
    
    def _load_rules(self) -> Dict[str, EducationalRule]:
        """Load Python-specific educational rules."""
        return {
            "PY001_NAME_CONVENTION": EducationalRule(
                rule_id="PY001_NAME_CONVENTION",
                title="Variable and Function Naming Convention",
                description="Python uses snake_case for variable and function names",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Learn Python naming conventions for better code readability",
                common_mistake="Using camelCase or PascalCase for variables/functions",
                best_practice="Use snake_case (lowercase_with_underscores) for variables and functions",
                improvement_suggestion="Rename your variables and functions to follow snake_case convention",
                resources=[
                    "https://pep8.org/#descriptive-naming-styles",
                    "https://realpython.com/python-pep8/",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.0,
                tags=["naming", "style", "beginner"],
            ),
            
            "PY002_LONG_LINE": EducationalRule(
                rule_id="PY002_LONG_LINE",
                title="Line Length Limit",
                description="Python code should not exceed 79 characters per line",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Understand the importance of readable line lengths",
                common_mistake="Writing very long lines that are hard to read",
                best_practice="Keep lines under 79 characters for better readability",
                improvement_suggestion="Break long lines into multiple lines using parentheses or backslashes",
                resources=[
                    "https://pep8.org/#maximum-line-length",
                    "https://realpython.com/python-pep8/#code-layout",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-1.5,
                tags=["style", "formatting", "beginner"],
            ),
            
            "PY003_UNUSED_IMPORT": EducationalRule(
                rule_id="PY003_UNUSED_IMPORT",
                title="Unused Imports",
                description="Remove imports that are not used in the code",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Keep imports clean and only import what's needed",
                common_mistake="Importing modules but not using them",
                best_practice="Only import modules and functions that you actually use",
                improvement_suggestion="Remove unused import statements to keep code clean",
                resources=[
                    "https://realpython.com/python-import/",
                    "https://docs.python.org/3/tutorial/modules.html",
                ],
                severity=SeverityLevel.LOW,
                score_impact=-1.0,
                tags=["imports", "cleanup", "beginner"],
            ),
            
            "PY004_FUNCTION_COMPLEXITY": EducationalRule(
                rule_id="PY004_FUNCTION_COMPLEXITY",
                title="Function Complexity",
                description="Functions should be simple and do one thing well",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn to write simple, focused functions",
                common_mistake="Writing functions that do too many things",
                best_practice="Break complex functions into smaller, single-purpose functions",
                improvement_suggestion="Split this function into smaller functions that each handle one responsibility",
                resources=[
                    "https://realpython.com/python-refactoring/",
                    "https://clean-code-developer.com/single-responsibility-principle/",
                ],
                severity=SeverityLevel.HIGH,
                score_impact=-4.0,
                tags=["functions", "complexity", "intermediate"],
            ),
            
            "PY005_MAGIC_NUMBERS": EducationalRule(
                rule_id="PY005_MAGIC_NUMBERS",
                title="Magic Numbers",
                description="Avoid using unnamed numeric literals in code",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn to use named constants instead of magic numbers",
                common_mistake="Using numbers directly in code without explanation",
                best_practice="Define constants with meaningful names for numeric values",
                improvement_suggestion="Replace magic numbers with named constants that explain their purpose",
                resources=[
                    "https://realpython.com/python-constants/",
                    "https://stackoverflow.com/questions/47882/what-is-a-magic-number-and-why-is-it-bad",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.5,
                tags=["constants", "readability", "intermediate"],
            ),
            
            "PY006_EXCEPTION_HANDLING": EducationalRule(
                rule_id="PY006_EXCEPTION_HANDLING",
                title="Proper Exception Handling",
                description="Handle exceptions properly and avoid bare except clauses",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn proper exception handling patterns in Python",
                common_mistake="Using bare except clauses or catching too broad exceptions",
                best_practice="Catch specific exceptions and handle them appropriately",
                improvement_suggestion="Replace bare except with specific exception types and proper handling",
                resources=[
                    "https://realpython.com/python-exceptions/",
                    "https://docs.python.org/3/tutorial/errors.html",
                ],
                severity=SeverityLevel.HIGH,
                score_impact=-3.5,
                tags=["exceptions", "error-handling", "intermediate"],
            ),
            
            "PY007_DOCSTRINGS": EducationalRule(
                rule_id="PY007_DOCSTRINGS",
                title="Missing Docstrings",
                description="Functions and classes should have docstrings",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Learn to document code using docstrings",
                common_mistake="Writing functions and classes without documentation",
                best_practice="Add clear docstrings explaining what functions do and their parameters",
                improvement_suggestion="Add docstrings to your functions and classes following PEP 257",
                resources=[
                    "https://pep8.org/#docstrings",
                    "https://realpython.com/documenting-python-code/",
                ],
                severity=SeverityLevel.LOW,
                score_impact=-1.0,
                tags=["documentation", "style", "beginner"],
            ),
            
            "PY008_LIST_COMPREHENSION": EducationalRule(
                rule_id="PY008_LIST_COMPREHENSION",
                title="Use List Comprehensions",
                description="Use list comprehensions instead of loops for simple list creation",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn Pythonic ways to create lists",
                common_mistake="Using for loops when list comprehensions would be clearer",
                best_practice="Use list comprehensions for simple list transformations",
                improvement_suggestion="Replace this loop with a more Pythonic list comprehension",
                resources=[
                    "https://realpython.com/list-comprehension-python/",
                    "https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions",
                ],
                severity=SeverityLevel.LOW,
                score_impact=-1.0,
                tags=["pythonic", "lists", "intermediate"],
            ),
            
            "PY009_GLOBAL_VARIABLES": EducationalRule(
                rule_id="PY009_GLOBAL_VARIABLES",
                title="Avoid Global Variables",
                description="Avoid using global variables in functions",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Understand why global variables make code hard to maintain",
                common_mistake="Using global variables instead of passing parameters",
                best_practice="Pass data as parameters rather than using global variables",
                improvement_suggestion="Refactor to pass data as parameters instead of using globals",
                resources=[
                    "https://realpython.com/python-scope-legb-rule/",
                    "https://stackoverflow.com/questions/19158339/why-are-global-variables-evil",
                ],
                severity=SeverityLevel.HIGH,
                score_impact=-4.0,
                tags=["scope", "variables", "intermediate"],
            ),
            
            "PY010_CONTEXT_MANAGER": EducationalRule(
                rule_id="PY010_CONTEXT_MANAGER",
                title="Use Context Managers for Files",
                description="Use 'with' statement for file operations",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Learn proper resource management using context managers",
                common_mistake="Forgetting to close files or not handling file errors properly",
                best_practice="Always use 'with' statement for file operations",
                improvement_suggestion="Replace manual file handling with 'with' statement",
                resources=[
                    "https://realpython.com/with-statement-python/",
                    "https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-3.0,
                tags=["files", "resources", "beginner"],
            ),
        }
    
    def _get_bad_example(self, rule_id: str, context: Dict[str, Any]) -> str:
        """Get bad code examples for Python rules."""
        examples = {
            "PY001_NAME_CONVENTION": """def calculateTotal(items):
    totalPrice = 0
    for item in items:
        totalPrice += item.price
    return totalPrice""",
            
            "PY002_LONG_LINE": """result = some_function_with_very_long_name(parameter1, parameter2, parameter3, parameter4, parameter5)""",
            
            "PY003_UNUSED_IMPORT": """import os
import sys
import json

def calculate():
    total = 0
    return total""",
            
            "PY004_FUNCTION_COMPLEXITY": """def process_data(data):
    # Validate data
    if not data:
        return None
    # Clean data
    cleaned = []
    for item in data:
        if item and item.isdigit():
            cleaned.append(int(item))
    # Calculate sum
    total = sum(cleaned)
    # Calculate average
    avg = total / len(cleaned) if cleaned else 0
    # Format result
    result = f"Sum: {total}, Average: {avg}"
    # Save to file
    with open("result.txt", "w") as f:
        f.write(result)
    return result""",
            
            "PY005_MAGIC_NUMBERS": """def calculate_discount(price):
    if price > 100:
        return price * 0.9
    elif price > 50:
        return price * 0.95
    else:
        return price""",
            
            "PY006_EXCEPTION_HANDLING": """def divide_numbers(a, b):
    try:
        return a / b
    except:
        return None""",
            
            "PY007_DOCSTRINGS": """def calculate_area(length, width):
    return length * width""",
            
            "PY008_LIST_COMPREHENSION": """squares = []
for i in range(10):
    squares.append(i * i)""",
            
            "PY009_GLOBAL_VARIABLES": """result = 0

def add_to_result(value):
    global result
    result += value""",
            
            "PY010_CONTEXT_MANAGER": """def read_file():
    f = open("data.txt", "r")
    content = f.read()
    f.close()
    return content""",
        }
        return examples.get(rule_id, "# Bad example not available")
    
    def _get_good_example(self, rule_id: str, context: Dict[str, Any]) -> str:
        """Get good code examples for Python rules."""
        examples = {
            "PY001_NAME_CONVENTION": """def calculate_total(items):
    total_price = 0
    for item in items:
        total_price += item.price
    return total_price""",
            
            "PY002_LONG_LINE": """result = some_function_with_very_long_name(
    parameter1, parameter2, parameter3, parameter4, parameter5
)""",
            
            "PY003_UNUSED_IMPORT": """def calculate():
    total = 0
    return total""",
            
            "PY004_FUNCTION_COMPLEXITY": """def validate_data(data):
    if not data:
        return None
    return [int(item) for item in data if item and item.isdigit()]

def calculate_statistics(cleaned_data):
    total = sum(cleaned_data)
    avg = total / len(cleaned_data) if cleaned_data else 0
    return total, avg

def save_result(total, avg):
    result = f"Sum: {total}, Average: {avg}"
    with open("result.txt", "w") as f:
        f.write(result)

def process_data(data):
    cleaned = validate_data(data)
    if not cleaned:
        return None
    total, avg = calculate_statistics(cleaned)
    save_result(total, avg)
    return f"Sum: {total}, Average: {avg}" """,
            
            "PY005_MAGIC_NUMBERS": """DISCOUNT_HIGH = 0.9
DISCOUNT_MEDIUM = 0.95

def calculate_discount(price):
    if price > 100:
        return price * DISCOUNT_HIGH
    elif price > 50:
        return price * DISCOUNT_MEDIUM
    else:
        return price""",
            
            "PY006_EXCEPTION_HANDLING": """def divide_numbers(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return None
    except TypeError:
        return "Invalid input types" """,
            
            "PY007_DOCSTRINGS": """def calculate_area(length, width):
    \"\"\"Calculate the area of a rectangle.
    
    Args:
        length (float): The length of the rectangle
        width (float): The width of the rectangle
    
    Returns:
        float: The area of the rectangle
    \"\"\"
    return length * width""",
            
            "PY008_LIST_COMPREHENSION": """squares = [i * i for i in range(10)]""",
            
            "PY009_GLOBAL_VARIABLES": """def add_to_result(current_result, value):
    return current_result + value

# Usage
result = 0
result = add_to_result(result, 5)""",
            
            "PY010_CONTEXT_MANAGER": """def read_file():
    with open("data.txt", "r") as f:
        content = f.read()
    return content""",
        }
        return examples.get(rule_id, "# Good example not available")
    
    def _get_next_steps(self, rule_id: str, context: Dict[str, Any]) -> list[str]:
        """Get next learning steps for Python rules."""
        steps = {
            "PY001_NAME_CONVENTION": [
                "Read PEP 8 naming conventions",
                "Practice renaming variables in existing code",
                "Use a linter to catch naming issues",
            ],
            "PY002_LONG_LINE": [
                "Set up your editor to show a line at column 79",
                "Practice breaking long expressions",
                "Learn about Python line continuation techniques",
            ],
            "PY003_UNUSED_IMPORT": [
                "Use a linter like flake8 to detect unused imports",
                "Learn about Python module organization",
                "Practice cleaning up imports in your projects",
            ],
            "PY004_FUNCTION_COMPLEXITY": [
                "Study the Single Responsibility Principle",
                "Practice refactoring large functions",
                "Learn about function composition patterns",
            ],
            "PY005_MAGIC_NUMBERS": [
                "Learn about Python constants",
                "Practice extracting magic numbers",
                "Study configuration management in Python",
            ],
            "PY006_EXCEPTION_HANDLING": [
                "Study Python's exception hierarchy",
                "Practice writing specific exception handlers",
                "Learn about custom exceptions",
            ],
            "PY007_DOCSTRINGS": [
                "Read PEP 257 for docstring conventions",
                "Practice writing docstrings for your functions",
                "Learn about different docstring formats (Google, NumPy)",
            ],
            "PY008_LIST_COMPREHENSION": [
                "Practice converting loops to comprehensions",
                "Learn about dictionary and set comprehensions",
                "Study when comprehensions are appropriate",
            ],
            "PY009_GLOBAL_VARIABLES": [
                "Study Python scoping rules (LEGB)",
                "Practice parameter passing patterns",
                "Learn about dependency injection",
            ],
            "PY010_CONTEXT_MANAGER": [
                "Study Python's context manager protocol",
                "Practice writing custom context managers",
                "Learn about resource management patterns",
            ],
        }
        return steps.get(rule_id, [
            "Practice this concept with simple exercises",
            "Review the learning resources provided",
            "Apply this pattern in your next project",
        ])
