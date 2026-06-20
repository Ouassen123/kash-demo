"""Educational rules for C++ code analysis."""

from typing import Dict, Any
from .base import EducationalRuleSet, EducationalRule, EducationalLevel
from ..models import SeverityLevel


class CppEducationalRules(EducationalRuleSet):
    """Educational rules specifically designed for C++ learners."""
    
    def __init__(self):
        super().__init__("cpp")
    
    def _load_rules(self) -> Dict[str, EducationalRule]:
        """Load C++-specific educational rules."""
        return {
            "CPP001_CLASS_NAMING": EducationalRule(
                rule_id="CPP001_CLASS_NAMING",
                title="Class/Struct Naming Convention",
                description="C++ classes and structs should use PascalCase (CamelCase with first letter capitalized)",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Learn C++ naming conventions for classes and structs",
                common_mistake="Using lowercase or snake_case for class/struct names",
                best_practice="Use PascalCase for class/struct names (e.g., MyClass, UserData)",
                improvement_suggestion="Rename your class/struct to follow PascalCase convention",
                resources=[
                    "https://google.github.io/styleguide/cppguide.html#Class_Names",
                    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Rl-class",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.0,
                tags=["naming", "style", "beginner"],
            ),
            
            "CPP002_FUNCTION_NAMING": EducationalRule(
                rule_id="CPP002_FUNCTION_NAMING",
                title="Function Naming Convention",
                description="C++ functions should use snake_case (lowercase with underscores)",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Learn C++ naming conventions for functions",
                common_mistake="Using camelCase or PascalCase for function names",
                best_practice="Use snake_case for function names (e.g., calculate_total, get_user_data)",
                improvement_suggestion="Rename your functions to follow snake_case convention",
                resources=[
                    "https://google.github.io/styleguide/cppguide.html#Function_Names",
                    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Rl-function",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.0,
                tags=["naming", "style", "beginner"],
            ),
            
            "CPP003_GOTO_STATEMENTS": EducationalRule(
                rule_id="CPP003_GOTO_STATEMENTS",
                title="Avoid Goto Statements",
                description="Avoid using goto statements in favor of structured control flow",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Learn why goto statements are considered harmful",
                common_mistake="Using goto for control flow",
                best_practice="Use structured control flow (if/else, loops, functions) instead of goto",
                improvement_suggestion="Replace goto statements with proper control structures",
                resources=[
                    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Res-goto",
                    "https://en.wikipedia.org/wiki/Considered_harmful",
                ],
                severity=SeverityLevel.HIGH,
                score_impact=-5.0,
                tags=["control-flow", "style", "beginner"],
            ),
            
            "CPP004_RAW_MEMORY_MANAGEMENT": EducationalRule(
                rule_id="CPP004_RAW_MEMORY_MANAGEMENT",
                title="Raw Memory Management",
                description="Prefer smart pointers over raw new/delete",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn modern C++ memory management with smart pointers",
                common_mistake="Using raw new/delete without proper RAII",
                best_practice="Use std::unique_ptr, std::shared_ptr for automatic memory management",
                improvement_suggestion="Replace raw new/delete with smart pointers",
                resources=[
                    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Rr-memory",
                    "https://www.cplusplus.com/memory/",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-3.0,
                tags=["memory", "modern-cpp", "intermediate"],
            ),
            
            "CPP005_MISSING_INCLUDE_GUARD": EducationalRule(
                rule_id="CPP005_MISSING_INCLUDE_GUARD",
                title="Missing Include Guards",
                description="Header files should have include guards to prevent multiple inclusion",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Understand why header files need include guards",
                common_mistake="Writing header files without include guards",
                best_practice="Always use #ifndef/#define/#endif guards or #pragma once",
                improvement_suggestion="Add include guards to this header file",
                resources=[
                    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Rl-include-guards",
                    "https://www.cplusplus.com/forum/articles/10627/",
                ],
                severity=SeverityLevel.HIGH,
                score_impact=-3.0,
                tags=["headers", "preprocessor", "beginner"],
            ),
            
            "CPP006_USING_NAMESPACE_STD": EducationalRule(
                rule_id="CPP006_USING_NAMESPACE_STD",
                title="Using namespace std in Headers",
                description="Avoid 'using namespace std' in header files",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Understand why 'using namespace std' in headers is problematic",
                common_mistake="Putting 'using namespace std' in header files",
                best_practice="Use std:: prefix explicitly in headers, or using declarations locally",
                improvement_suggestion="Remove 'using namespace std' from header and use std:: prefix",
                resources=[
                    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Rl-using",
                    "https://stackoverflow.com/questions/1452721/why-is-using-namespace-std-considered-bad-practice",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.5,
                tags=["namespaces", "headers", "intermediate"],
            ),
            
            "CPP007_MAGIC_NUMBERS": EducationalRule(
                rule_id="CPP007_MAGIC_NUMBERS",
                title="Magic Numbers",
                description="Avoid using unnamed numeric literals in code",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn to use named constants instead of magic numbers",
                common_mistake="Using numbers directly in code without explanation",
                best_practice="Define const or constexpr variables with meaningful names",
                improvement_suggestion="Replace magic numbers with named constants",
                resources=[
                    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Res-magic",
                    "https://www.cplusplus.com/forum/beginner/166234/",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.5,
                tags=["constants", "readability", "intermediate"],
            ),
            
            "CPP008_LONG_FUNCTION": EducationalRule(
                rule_id="CPP008_LONG_FUNCTION",
                title="Long Functions",
                description="Functions should be short and focused on a single responsibility",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn to write concise, focused functions",
                common_mistake="Writing functions that are too long and do too many things",
                best_practice="Keep functions under 20-30 lines with a single responsibility",
                improvement_suggestion="Break this function into smaller, more focused functions",
                resources=[
                    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Rf-single",
                    "https://refactoring.guide/extract-function.html",
                ],
                severity=SeverityLevel.HIGH,
                score_impact=-4.0,
                tags=["functions", "complexity", "intermediate"],
            ),
            
            "CPP009_PUBLIC_MEMBERS": EducationalRule(
                rule_id="CPP009_PUBLIC_MEMBERS",
                title="Public Data Members",
                description="Avoid public data members in classes - use private with accessors",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn about encapsulation and data hiding in C++",
                common_mistake="Making class members public for easy access",
                best_practice="Keep members private and provide public getter/setter methods",
                improvement_suggestion="Make this member private and provide appropriate accessors",
                resources=[
                    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Rc-class",
                    "https://www.cplusplus.com/doc/tutorial/classes/",
                ],
                severity=SeverityLevel.HIGH,
                score_impact="-3.5",
                tags=["encapsulation", "design", "intermediate"],
            ),
            
            "CPP010_CONST_CORRECTNESS": EducationalRule(
                rule_id="CPP010_CONST_CORRECTNESS",
                title="Const Correctness",
                description="Use const to indicate when values and functions don't modify data",
                educational_level=EducationalLevel.ADVANCED,
                learning_objective="Learn to write const-correct C++ code",
                common_mistake="Not using const where appropriate",
                best_practice="Mark functions const when they don't modify object state",
                improvement_suggestion="Add const qualifiers to appropriate parameters and member functions",
                resources=[
                    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Rc-const",
                    "https://www.cplusplus.com/doc/tutorial/const/",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact="-2.0",
                tags=["const", "safety", "advanced"],
            ),
        }
    
    def _get_bad_example(self, rule_id: str, context: Dict[str, Any]) -> str:
        """Get bad code examples for C++ rules."""
        examples = {
            "CPP001_CLASS_NAMING": """class myClass {
private:
    int value;
};""",
            
            "CPP002_FUNCTION_NAMING": """class Calculator {
public:
    int CalculateTotal(int a, int b) {
        return a + b;
    }
};""",
            
            "CPP003_GOTO_STATEMENTS": """void processData() {
    // ... some code ...
    if (error) {
        goto cleanup;
    }
    // ... more code ...
cleanup:
    // cleanup code
}""",
            
            "CPP004_RAW_MEMORY_MANAGEMENT": """class DataProcessor {
public:
    void processData() {
        int* data = new int[100];
        // process data
        delete[] data;
    }
};""",
            
            "CPP005_MISSING_INCLUDE_GUARD": """// myheader.h
class MyClass {
    int value;
};""",
            
            "CPP006_USING_NAMESPACE_STD": """// myheader.h
#include <vector>
#include <string>

using namespace std;

class MyClass {
    vector<string> items;
};""",
            
            "CPP007_MAGIC_NUMBERS": """class Calculator {
public:
    double calculateDiscount(double price) {
        if (price > 100) {
            return price * 0.9;
        } else if (price > 50) {
            return price * 0.95;
        }
        return price;
    }
};""",
            
            "CPP008_LONG_FUNCTION": """void processOrder(Order* order) {
    // Validate order
    if (!order) {
        throw std::invalid_argument("Order cannot be null");
    }
    if (order->items.empty()) {
        throw std::invalid_argument("Order has no items");
    }
    
    // Calculate total
    double total = 0;
    for (const auto& item : order->items) {
        total += item.price * item.quantity;
    }
    
    // Apply discount
    if (order->hasDiscount) {
        total *= (1 - order->discountPercentage / 100);
    }
    
    // Update inventory
    for (const auto& item : order->items) {
        Inventory* inv = getInventory(item.productId);
        inv->quantity -= item.quantity;
        updateInventory(inv);
    }
    
    // Save order
    order->total = total;
    order->status = "PROCESSED";
    saveOrder(order);
    
    // Send confirmation
    sendConfirmation(*order);
}""",
            
            "CPP009_PUBLIC_MEMBERS": """class User {
public:
    std::string name;
    std::string email;
    int age;
};""",
            
            "CPP010_CONST_CORRECTNESS": """class Calculator {
private:
    int value;
    
public:
    int getValue() {
        return value;
    }
    
    void printValue() {
        std::cout << value << std::endl;
    }
};""",
        }
        return examples.get(rule_id, "// Bad example not available")
    
    def _get_good_example(self, rule_id: str, context: Dict[str, Any]) -> str:
        """Get good code examples for C++ rules."""
        examples = {
            "CPP001_CLASS_NAMING": """class MyClass {
private:
    int value;
};""",
            
            "CPP002_FUNCTION_NAMING": """class Calculator {
public:
    int calculate_total(int a, int b) {
        return a + b;
    }
};""",
            
            "CPP003_GOTO_STATEMENTS": """void process_data() {
    try {
        // ... some code ...
        if (error) {
            throw std::runtime_error("Processing failed");
        }
        // ... more code ...
    } catch (const std::exception& e) {
        // cleanup code
        cleanup();
        throw;
    }
}""",
            
            "CPP004_RAW_MEMORY_MANAGEMENT": """#include <memory>

class DataProcessor {
public:
    void processData() {
        auto data = std::make_unique<int[]>(100);
        // process data
        // Automatic cleanup when data goes out of scope
    }
};""",
            
            "CPP005_MISSING_INCLUDE_GUARD": """#ifndef MYHEADER_H
#define MYHEADER_H

class MyClass {
    int value;
};

#endif // MYHEADER_H""",
            
            "CPP006_USING_NAMESPACE_STD": """// myheader.h
#include <vector>
#include <string>

class MyClass {
    std::vector<std::string> items;
};""",
            
            "CPP007_MAGIC_NUMBERS": """class Calculator {
private:
    static constexpr double HIGH_DISCOUNT_THRESHOLD = 100.0;
    static constexpr double MEDIUM_DISCOUNT_THRESHOLD = 50.0;
    static constexpr double HIGH_DISCOUNT_RATE = 0.9;
    static constexpr double MEDIUM_DISCOUNT_RATE = 0.95;
    
public:
    double calculateDiscount(double price) {
        if (price > HIGH_DISCOUNT_THRESHOLD) {
            return price * HIGH_DISCOUNT_RATE;
        } else if (price > MEDIUM_DISCOUNT_THRESHOLD) {
            return price * MEDIUM_DISCOUNT_RATE;
        }
        return price;
    }
};""",
            
            "CPP008_LONG_FUNCTION": """class OrderProcessor {
public:
    void processOrder(Order* order) {
        validateOrder(order);
        double total = calculateTotal(order);
        updateInventory(order);
        saveOrder(order, total);
        sendConfirmation(*order);
    }
    
private:
    void validateOrder(Order* order) { /* ... */ }
    double calculateTotal(Order* order) { /* ... */ }
    void updateInventory(Order* order) { /* ... */ }
    void saveOrder(Order* order, double total) { /* ... */ }
    void sendConfirmation(const Order& order) { /* ... */ }
};""",
            
            "CPP009_PUBLIC_MEMBERS": """class User {
private:
    std::string name;
    std::string email;
    int age;
    
public:
    const std::string& getName() const { return name; }
    void setName(const std::string& newName) { name = newName; }
    const std::string& getEmail() const { return email; }
    void setEmail(const std::string& newEmail) { email = newEmail; }
    int getAge() const { return age; }
    void setAge(int newAge) { age = newAge; }
};""",
            
            "CPP010_CONST_CORRECTNESS": """class Calculator {
private:
    int value;
    
public:
    int getValue() const { return value; }
    
    void printValue() const {
        std::cout << value << std::endl;
    }
    
    void setValue(int newValue) { value = newValue; }
};""",
        }
        return examples.get(rule_id, "// Good example not available")
    
    def _get_next_steps(self, rule_id: str, context: Dict[str, Any]) -> list[str]:
        """Get next learning steps for C++ rules."""
        steps = {
            "CPP001_CLASS_NAMING": [
                "Study C++ naming conventions from Google Style Guide",
                "Practice renaming classes in existing code",
                "Set up IDE to enforce naming conventions",
            ],
            "CPP002_FUNCTION_NAMING": [
                "Learn snake_case vs camelCase conventions in C++",
                "Practice function naming in your projects",
                "Use IDE refactoring tools to rename functions",
            ],
            "CPP003_GOTO_STATEMENTS": [
                "Study structured programming principles",
                "Learn about exception handling in C++",
                "Practice replacing goto with proper control structures",
            ],
            "CPP004_RAW_MEMORY_MANAGEMENT": [
                "Study modern C++ smart pointers",
                "Learn about RAII (Resource Acquisition Is Initialization)",
                "Practice replacing raw pointers with smart pointers",
            ],
            "CPP005_MISSING_INCLUDE_GUARD": [
                "Learn about C++ preprocessor and include guards",
                "Study #pragma once vs traditional guards",
                "Practice adding guards to existing headers",
            ],
            "CPP006_USING_NAMESPACE_STD": [
                "Learn about C++ namespaces and scope",
                "Study why using directives in headers are problematic",
                "Practice using std:: prefix explicitly",
            ],
            "CPP007_MAGIC_NUMBERS": [
                "Learn about const and constexpr in C++",
                "Practice extracting magic numbers",
                "Study configuration management in C++",
            ],
            "CPP008_LONG_FUNCTION": [
                "Study Single Responsibility Principle",
                "Practice extracting functions from long functions",
                "Learn about function composition patterns",
            ],
            "CPP009_PUBLIC_MEMBERS": [
                "Study encapsulation principle in C++",
                "Learn about accessors and mutators",
                "Practice making members private with proper accessors",
            ],
            "CPP010_CONST_CORRECTNESS": [
                "Study const correctness in depth",
                "Learn about const member functions and parameters",
                "Practice adding const qualifiers to existing code",
            ],
        }
        return steps.get(rule_id, [
            "Practice this concept with simple exercises",
            "Review the learning resources provided",
            "Apply this pattern in your next project",
        ])
