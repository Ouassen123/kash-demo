"""Educational rules for JavaScript/TypeScript code analysis."""

from typing import Dict, Any
from .base import EducationalRuleSet, EducationalRule, EducationalLevel
from ..models import SeverityLevel


class JavaScriptEducationalRules(EducationalRuleSet):
    """Educational rules specifically designed for JavaScript/TypeScript learners."""
    
    def __init__(self):
        super().__init__("javascript")
    
    def _load_rules(self) -> Dict[str, EducationalRule]:
        """Load JavaScript/TypeScript-specific educational rules."""
        return {
            "JS001_CLASS_NAMING": EducationalRule(
                rule_id="JS001_CLASS_NAMING",
                title="Class Naming Convention",
                description="JavaScript classes should use PascalCase (CamelCase with first letter capitalized)",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Learn JavaScript naming conventions for classes",
                common_mistake="Using lowercase or snake_case for class names",
                best_practice="Use PascalCase for class names (e.g., MyClass, UserService)",
                improvement_suggestion="Rename your class to follow PascalCase convention",
                resources=[
                    "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes",
                    "https://airbnb.io/javascript/#classes--constructor",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.0,
                tags=["naming", "style", "beginner"],
            ),
            
            "JS002_FUNCTION_NAMING": EducationalRule(
                rule_id="JS002_FUNCTION_NAMING",
                title="Function Naming Convention",
                description="JavaScript functions should use camelCase (first letter lowercase, subsequent words capitalized)",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Learn JavaScript naming conventions for functions",
                common_mistake="Using PascalCase or snake_case for function names",
                best_practice="Use camelCase for function names (e.g., calculateTotal, getUserData)",
                improvement_suggestion="Rename your functions to follow camelCase convention",
                resources=[
                    "https://www.w3schools.com/js/js_conventions.asp",
                    "https://airbnb.io/javascript/#naming--camelCase",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.0,
                tags=["naming", "style", "beginner"],
            ),
            
            "JS003_VAR_DECLARATIONS": EducationalRule(
                rule_id="JS003_VAR_DECLARATIONS",
                title="Use const and let instead of var",
                description="Prefer const and let over var for better scoping",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Understand modern JavaScript variable declarations",
                common_mistake="Using var which has function scope and hoisting issues",
                best_practice="Use const for variables that won't be reassigned, let for those that will",
                improvement_suggestion="Replace var declarations with const or let",
                resources=[
                    "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let",
                    "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/const",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.5,
                tags=["variables", "modern-js", "beginner"],
            ),
            
            "JS004_CONSOLE_LOG": EducationalRule(
                rule_id="JS004_CONSOLE_LOG",
                title="Remove Console Log Statements",
                description="Remove console.log statements before production",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Learn to clean up debugging code",
                common_mistake="Leaving console.log statements in production code",
                best_practice="Remove or comment out console.log statements before deployment",
                improvement_suggestion="Remove this console.log statement or replace with proper logging",
                resources=[
                    "https://developer.mozilla.org/en-US/docs/Web/API/console/log",
                    "https://stackoverflow.com/questions/20485402/remove-console-log-in-production",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-1.5,
                tags=["debugging", "cleanup", "beginner"],
            ),
            
            "JS005_RELATIVE_IMPORTS": EducationalRule(
                rule_id="JS005_RELATIVE_IMPORTS",
                title="Avoid Deep Relative Imports",
                description="Avoid deep relative imports like '../../../utils'",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn about module organization and import strategies",
                common_mistake="Using deep relative imports that are hard to maintain",
                best_practice="Use absolute imports or configure module resolution",
                improvement_suggestion="Consider using absolute imports or restructuring modules",
                resources=[
                    "https://www.typescriptlang.org/docs/handbook/module-resolution.html",
                    "https://webpack.js.org/configuration/resolve/",
                ],
                severity=SeverityLevel.LOW,
                score_impact=-1.0,
                tags=["modules", "imports", "intermediate"],
            ),
            
            "JS006_TOO_MANY_PARAMETERS": EducationalRule(
                rule_id="JS006_TOO_MANY_PARAMETERS",
                title="Too Many Function Parameters",
                description="Functions should not have too many parameters (ideally ≤ 5)",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn to design functions with appropriate parameter counts",
                common_mistake="Creating functions with many parameters",
                best_practice="Use parameter objects or destructuring for functions with many parameters",
                improvement_suggestion="Consider using a parameter object or destructuring pattern",
                resources=[
                    "https://eslint.org/docs/rules/max-params",
                    "https://javascript.info/destructuring-assignment",
                ],
                severity=SeverityLevel.HIGH,
                score_impact="-3.0",
                tags=["functions", "design", "intermediate"],
            ),
            
            "JS007_MAGIC_NUMBERS": EducationalRule(
                rule_id="JS007_MAGIC_NUMBERS",
                title="Magic Numbers",
                description="Avoid using unnamed numeric literals in code",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn to use named constants instead of magic numbers",
                common_mistake="Using numbers directly in code without explanation",
                best_practice="Define constants with meaningful names for numeric values",
                improvement_suggestion="Replace magic numbers with named constants",
                resources=[
                    "https://eslint.org/docs/rules/no-magic-numbers",
                    "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/const",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact="-2.5",
                tags=["constants", "readability", "intermediate"],
            ),
            
            "JS008_ANY_TYPE": EducationalRule(
                rule_id="JS008_ANY_TYPE",
                title="Avoid Using 'any' Type in TypeScript",
                description="Avoid using 'any' type - use specific types for better type safety",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn TypeScript type safety and proper typing",
                common_mistake="Using 'any' type when unsure of the proper type",
                best_practice="Define specific types or interfaces for better type safety",
                improvement_suggestion="Replace 'any' with proper TypeScript types",
                resources=[
                    "https://www.typescriptlang.org/docs/handbook/basic-types.html",
                    "https://www.typescriptlang.org/docs/handbook/interfaces.html",
                ],
                severity=SeverityLevel.HIGH,
                score_impact="-3.0",
                tags=["typescript", "types", "intermediate"],
            ),
            
            "JS009_INTERFACE_NAMING": EducationalRule(
                rule_id="JS009_INTERFACE_NAMING",
                title="TypeScript Interface Naming",
                description="TypeScript interfaces should start with 'I' prefix",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn TypeScript interface naming conventions",
                common_mistake="Not using 'I' prefix for interface names",
                best_practice="Use 'I' prefix for interface names (e.g., IUser, IProduct)",
                improvement_suggestion="Rename this interface to start with 'I' prefix",
                resources=[
                    "https://typescript-eslint.io/rules/naming-convention/",
                    "https://www.typescriptlang.org/docs/handbook/interfaces.html",
                ],
                severity=SeverityLevel.LOW,
                score_impact="-1.0",
                tags=["typescript", "naming", "intermediate"],
            ),
            
            "JS010_ASYNC_FUNCTIONS": EducationalRule(
                rule_id="JS010_ASYNC_FUNCTIONS",
                title="Async Function Best Practices",
                description="Use async/await properly and handle promises correctly",
                educational_level=EducationalLevel.ADVANCED,
                learning_objective="Learn modern asynchronous JavaScript patterns",
                common_mistake="Not handling promise rejections or mixing patterns incorrectly",
                best_practice="Always handle promise rejections and use consistent async patterns",
                improvement_suggestion="Add proper error handling and use consistent async patterns",
                resources=[
                    "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function",
                    "https://javascript.info/async-await",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact="-2.5",
                tags=["async", "promises", "advanced"],
            ),
        }
    
    def _get_bad_example(self, rule_id: str, context: Dict[str, Any]) -> str:
        """Get bad code examples for JavaScript/TypeScript rules."""
        examples = {
            "JS001_CLASS_NAMING": """class myClass {
    constructor(value) {
        this.value = value;
    }
}""",
            
            "JS002_FUNCTION_NAMING": """function Calculate_Total(a, b) {
    return a + b;
}""",
            
            "JS003_VAR_DECLARATIONS": """function process() {
    var x = 10;
    var y = 20;
    return x + y;
}""",
            
            "JS004_CONSOLE_LOG": """function calculateTotal(items) {
    console.log("Calculating total for:", items);
    let total = 0;
    for (let item of items) {
        total += item.price;
        console.log("Added:", item.price);
    }
    console.log("Final total:", total);
    return total;
}""",
            
            "JS005_RELATIVE_IMPORTS": """import { utils } from '../../../shared/utils/helpers';
import { constants } from '../../../../config/constants';""",
            
            "JS006_TOO_MANY_PARAMETERS": """function createUser(firstName, lastName, email, phone, address, city, state, zipCode, country) {
    // function implementation
}""",
            
            "JS007_MAGIC_NUMBERS": """function calculateDiscount(price) {
    if (price > 100) {
        return price * 0.9;
    } else if (price > 50) {
        return price * 0.95;
    }
    return price;
}""",
            
            "JS008_ANY_TYPE": """function processData(data: any): any {
    return data.map((item: any) => ({
        id: item.id,
        value: item.value * 2
    }));
}""",
            
            "JS009_INTERFACE_NAMING": """interface User {
    id: number;
    name: string;
    email: string;
}""",
            
            "JS010_ASYNC_FUNCTIONS": """async function fetchUserData(userId) {
    const response = await fetch(`/api/users/${userId}`);
    const data = await response.json();
    return data;
    // No error handling
}""",
        }
        return examples.get(rule_id, "// Bad example not available")
    
    def _get_good_example(self, rule_id: str, context: Dict[str, Any]) -> str:
        """Get good code examples for JavaScript/TypeScript rules."""
        examples = {
            "JS001_CLASS_NAMING": """class MyClass {
    constructor(value) {
        this.value = value;
    }
}""",
            
            "JS002_FUNCTION_NAMING": """function calculateTotal(a, b) {
    return a + b;
}""",
            
            "JS003_VAR_DECLARATIONS": """function process() {
    const x = 10;
    const y = 20;
    return x + y;
}""",
            
            "JS004_CONSOLE_LOG": """function calculateTotal(items) {
    let total = 0;
    for (let item of items) {
        total += item.price;
    }
    return total;
}""",
            
            "JS005_RELATIVE_IMPORTS": """import { utils } from '@/shared/utils/helpers';
import { constants } from '@/config/constants';""",
            
            "JS006_TOO_MANY_PARAMETERS": """interface UserData {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    address: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
}

function createUser(userData: UserData) {
    // function implementation
}""",
            
            "JS007_MAGIC_NUMBERS": """const DISCOUNT_THRESHOLDS = {
    HIGH: 100,
    MEDIUM: 50
};

const DISCOUNT_RATES = {
    HIGH: 0.9,
    MEDIUM: 0.95
};

function calculateDiscount(price: number): number {
    if (price > DISCOUNT_THRESHOLDS.HIGH) {
        return price * DISCOUNT_RATES.HIGH;
    } else if (price > DISCOUNT_THRESHOLDS.MEDIUM) {
        return price * DISCOUNT_RATES.MEDIUM;
    }
    return price;
}""",
            
            "JS008_ANY_TYPE": """interface DataItem {
    id: number;
    value: number;
}

interface ProcessedData {
    id: number;
    value: number;
}

function processData(data: DataItem[]): ProcessedData[] {
    return data.map((item: DataItem): ProcessedData => ({
        id: item.id,
        value: item.value * 2
    }));
}""",
            
            "JS009_INTERFACE_NAMING": """interface IUser {
    id: number;
    name: string;
    email: string;
}""",
            
            "JS010_ASYNC_FUNCTIONS": """async function fetchUserData(userId: string): Promise<UserData> {
    try {
        const response = await fetch(`/api/users/${userId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Failed to fetch user data:', error);
        throw error;
    }
}""",
        }
        return examples.get(rule_id, "// Good example not available")
    
    def _get_next_steps(self, rule_id: str, context: Dict[str, Any]) -> list[str]:
        """Get next learning steps for JavaScript/TypeScript rules."""
        steps = {
            "JS001_CLASS_NAMING": [
                "Study JavaScript naming conventions",
                "Practice class naming in your projects",
                "Set up ESLint to enforce naming conventions",
            ],
            "JS002_FUNCTION_NAMING": [
                "Learn camelCase vs PascalCase conventions",
                "Practice function naming in your projects",
                "Use ESLint to catch naming issues",
            ],
            "JS003_VAR_DECLARATIONS": [
                "Study let, const, and var differences",
                "Learn about scope and hoisting",
                "Practice replacing var with let/const",
            ],
            "JS004_CONSOLE_LOG": [
                "Learn about proper logging strategies",
                "Set up build process to remove console logs",
                "Practice debugging without console logs",
            ],
            "JS005_RELATIVE_IMPORTS": [
                "Learn about module resolution strategies",
                "Study absolute imports and path mapping",
                "Practice restructuring module dependencies",
            ],
            "JS006_TOO_MANY_PARAMETERS": [
                "Study object destructuring patterns",
                "Learn about parameter objects",
                "Practice refactoring functions with many parameters",
            ],
            "JS007_MAGIC_NUMBERS": [
                "Learn about const and let for constants",
                "Practice extracting magic numbers",
                "Study configuration management in JavaScript",
            ],
            "JS008_ANY_TYPE": [
                "Study TypeScript type system",
                "Learn about interfaces and type aliases",
                "Practice replacing any with proper types",
            ],
            "JS009_INTERFACE_NAMING": [
                "Study TypeScript naming conventions",
                "Practice interface naming patterns",
                "Set up ESLint TypeScript rules",
            ],
            "JS010_ASYNC_FUNCTIONS": [
                "Study async/await patterns in depth",
                "Learn about error handling in async code",
                "Practice promise chaining vs async/await",
            ],
        }
        return steps.get(rule_id, [
            "Practice this concept with simple exercises",
            "Review the learning resources provided",
            "Apply this pattern in your next project",
        ])
