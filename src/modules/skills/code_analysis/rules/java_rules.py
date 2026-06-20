"""Educational rules for Java code analysis."""

from typing import Dict, Any
from .base import EducationalRuleSet, EducationalRule, EducationalLevel
from ..models import SeverityLevel


class JavaEducationalRules(EducationalRuleSet):
    """Educational rules specifically designed for Java learners."""
    
    def __init__(self):
        super().__init__("java")
    
    def _load_rules(self) -> Dict[str, EducationalRule]:
        """Load Java-specific educational rules."""
        return {
            "JAVA001_CLASS_NAMING": EducationalRule(
                rule_id="JAVA001_CLASS_NAMING",
                title="Class Naming Convention",
                description="Java classes should use PascalCase (CamelCase with first letter capitalized)",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Learn Java naming conventions for classes",
                common_mistake="Using lowercase or snake_case for class names",
                best_practice="Use PascalCase for class names (e.g., MyClass, UserService)",
                improvement_suggestion="Rename your class to follow PascalCase convention",
                resources=[
                    "https://www.oracle.com/java/technologies/javase/codeconventions-namingconventions.html",
                    "https://clean-code-developer.com/naming-conventions-java/",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.0,
                tags=["naming", "style", "beginner"],
            ),
            
            "JAVA002_METHOD_NAMING": EducationalRule(
                rule_id="JAVA002_METHOD_NAMING",
                title="Method Naming Convention",
                description="Java methods should use camelCase (first letter lowercase, subsequent words capitalized)",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Learn Java naming conventions for methods",
                common_mistake="Using PascalCase or snake_case for method names",
                best_practice="Use camelCase for method names (e.g., calculateTotal, getUserData)",
                improvement_suggestion="Rename your methods to follow camelCase convention",
                resources=[
                    "https://www.oracle.com/java/technologies/javase/codeconventions-namingconventions.html",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.0,
                tags=["naming", "style", "beginner"],
            ),
            
            "JAVA003_WILDCARD_IMPORTS": EducationalRule(
                rule_id="JAVA003_WILDCARD_IMPORTS",
                title="Avoid Wildcard Imports",
                description="Avoid using wildcard imports like 'import java.util.*;'",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Understand why explicit imports are better than wildcard imports",
                common_mistake="Using wildcard imports for convenience",
                best_practice="Import specific classes explicitly",
                improvement_suggestion="Replace wildcard imports with explicit class imports",
                resources=[
                    "https://stackoverflow.com/questions/147454/why-is-using-a-wildcard-import-statement-a-bad-idea-in-java",
                    "https://clean-code-developer.com/import-statements/",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.0,
                tags=["imports", "style", "beginner"],
            ),
            
            "JAVA004_TOO_MANY_PARAMETERS": EducationalRule(
                rule_id="JAVA004_TOO_MANY_PARAMETERS",
                title="Too Many Method Parameters",
                description="Methods should not have too many parameters (ideally ≤ 5)",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn to design methods with appropriate parameter counts",
                common_mistake="Creating methods with many parameters",
                best_practice="Use parameter objects or builder patterns for methods with many parameters",
                improvement_suggestion="Consider using a parameter object or breaking this method into smaller methods",
                resources=[
                    "https://refactoring.guide/replace-parameter-with-method-call.html",
                    "https://www.baeldung.com/java-many-method-parameters",
                ],
                severity=SeverityLevel.HIGH,
                score_impact=-3.0,
                tags=["methods", "design", "intermediate"],
            ),
            
            "JAVA005_LONG_METHOD": EducationalRule(
                rule_id="JAVA005_LONG_METHOD",
                title="Long Methods",
                description="Methods should be short and focused on a single responsibility",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn to write concise, focused methods",
                common_mistake="Writing methods that are too long and do too many things",
                best_practice="Keep methods under 20-30 lines with a single responsibility",
                improvement_suggestion="Break this method into smaller, more focused methods",
                resources=[
                    "https://refactoring.guide/extract-method.html",
                    "https://clean-code-developer.com/single-responsibility-principle/",
                ],
                severity=SeverityLevel.HIGH,
                score_impact=-4.0,
                tags=["methods", "complexity", "intermediate"],
            ),
            
            "JAVA006_MAGIC_NUMBERS": EducationalRule(
                rule_id="JAVA006_MAGIC_NUMBERS",
                title="Magic Numbers",
                description="Avoid using unnamed numeric literals in code",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn to use named constants instead of magic numbers",
                common_mistake="Using numbers directly in code without explanation",
                best_practice="Define constants with meaningful names for numeric values",
                improvement_suggestion="Replace magic numbers with named constants that explain their purpose",
                resources=[
                    "https://www.baeldung.com/java-magic-numbers",
                    "https://refactoring.guide/replace-magic-number-with-symbolic-constant.html",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.5,
                tags=["constants", "readability", "intermediate"],
            ),
            
            "JAVA007_MISSING_INCLUDE_GUARD": EducationalRule(
                rule_id="JAVA007_MISSING_INCLUDE_GUARD",
                title="Missing Package Declaration",
                description="Java files should have proper package declarations",
                educational_level=EducationalLevel.BEGINNER,
                learning_objective="Understand Java package structure and organization",
                common_mistake="Writing Java files without package declarations",
                best_practice="Always include a package declaration at the top of Java files",
                improvement_suggestion="Add a proper package declaration to this file",
                resources=[
                    "https://docs.oracle.com/javase/tutorial/java/package/packages.html",
                    "https://www.baeldung.com/java-package",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.0,
                tags=["packages", "organization", "beginner"],
            ),
            
            "JAVA008_PUBLIC_FIELDS": EducationalRule(
                rule_id="JAVA008_PUBLIC_FIELDS",
                title="Public Fields in Classes",
                description="Avoid public fields in classes - use private fields with getters/setters",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn about encapsulation and data hiding in Java",
                common_mistake="Making class fields public for easy access",
                best_practice="Keep fields private and provide public getter/setter methods",
                improvement_suggestion="Make this field private and provide appropriate getter/setter methods",
                resources=[
                    "https://www.baeldung.com/java-getters-setters",
                    "https://docs.oracle.com/javase/tutorial/java/javaOO/encapsulation.html",
                ],
                severity=SeverityLevel.HIGH,
                score_impact=-3.5,
                tags=["encapsulation", "design", "intermediate"],
            ),
            
            "JAVA009_EXCEPTION_HANDLING": EducationalRule(
                rule_id="JAVA009_EXCEPTION_HANDLING",
                title="Proper Exception Handling",
                description="Handle exceptions properly and avoid empty catch blocks",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Learn proper exception handling patterns in Java",
                common_mistake="Using empty catch blocks or catching too broad exceptions",
                best_practice="Catch specific exceptions and handle them appropriately",
                improvement_suggestion="Replace empty catch blocks with proper exception handling",
                resources=[
                    "https://www.baeldung.com/java-exceptions",
                    "https://docs.oracle.com/javase/tutorial/essential/exceptions/",
                ],
                severity=SeverityLevel.HIGH,
                score_impact=-3.5,
                tags=["exceptions", "error-handling", "intermediate"],
            ),
            
            "JAVA010_STRING_CONCATENATION": EducationalRule(
                rule_id="JAVA010_STRING_CONCATENATION",
                title="String Concatenation in Loops",
                description="Avoid string concatenation in loops - use StringBuilder instead",
                educational_level=EducationalLevel.INTERMEDIATE,
                learning_objective="Understand string performance in Java",
                common_mistake="Using + operator for string concatenation in loops",
                best_practice="Use StringBuilder for efficient string concatenation in loops",
                improvement_suggestion="Replace string concatenation with StringBuilder in loops",
                resources=[
                    "https://www.baeldung.com/java-string-builder-string-buffer",
                    "https://stackoverflow.com/questions/1532461/stringbuilder-vs-string-concatenation",
                ],
                severity=SeverityLevel.MEDIUM,
                score_impact=-2.5,
                tags=["performance", "strings", "intermediate"],
            ),
        }
    
    def _get_bad_example(self, rule_id: str, context: Dict[str, Any]) -> str:
        """Get bad code examples for Java rules."""
        examples = {
            "JAVA001_CLASS_NAMING": """public class myClass {
    private int value;
}""",
            
            "JAVA002_METHOD_NAMING": """public class Calculator {
    public int Calculate_Total(int a, int b) {
        return a + b;
    }
}""",
            
            "JAVA003_WILDCARD_IMPORTS": """import java.util.*;
import java.io.*;

public class Example {
    private List<String> items = new ArrayList<>();
}""",
            
            "JAVA004_TOO_MANY_PARAMETERS": """public void createUser(String firstName, String lastName, String email, 
                                   String phone, String address, String city, 
                                   String state, String zipCode, String country) {
    // method implementation
}""",
            
            "JAVA005_LONG_METHOD": """public void processOrder(Order order) {
    // Validate order
    if (order == null) {
        throw new IllegalArgumentException("Order cannot be null");
    }
    if (order.getItems().isEmpty()) {
        throw new IllegalArgumentException("Order has no items");
    }
    
    // Calculate total
    double total = 0;
    for (OrderItem item : order.getItems()) {
        total += item.getPrice() * item.getQuantity();
    }
    
    // Apply discount
    if (order.hasDiscount()) {
        total *= (1 - order.getDiscountPercentage() / 100);
    }
    
    // Update inventory
    for (OrderItem item : order.getItems()) {
        Inventory inventory = inventoryService.getByProductId(item.getProductId());
        inventory.setQuantity(inventory.getQuantity() - item.getQuantity());
        inventoryService.update(inventory);
    }
    
    // Save order
    order.setTotal(total);
    order.setStatus("PROCESSED");
    orderRepository.save(order);
    
    // Send confirmation email
    emailService.sendOrderConfirmation(order);
    
    // Log the transaction
    logger.info("Order processed: " + order.getId());
}""",
            
            "JAVA006_MAGIC_NUMBERS": """public class DiscountCalculator {
    public double calculateDiscount(double price) {
        if (price > 100) {
            return price * 0.9;
        } else if (price > 50) {
            return price * 0.95;
        } else {
            return price;
        }
    }
}""",
            
            "JAVA007_MISSING_INCLUDE_GUARD": """public class UserService {
    // No package declaration
    private UserRepository userRepository;
}""",
            
            "JAVA008_PUBLIC_FIELDS": """public class User {
    public String name;
    public String email;
    public int age;
}""",
            
            "JAVA009_EXCEPTION_HANDLING": """public class FileProcessor {
    public void processFile(String filename) {
        try {
            BufferedReader reader = new BufferedReader(new FileReader(filename));
            // process file
        } catch (Exception e) {
            // Empty catch block
        }
    }
}""",
            
            "JAVA010_STRING_CONCATENATION": """public class StringExample {
    public String buildListString(List<String> items) {
        String result = "";
        for (String item : items) {
            result += item + ", ";
        }
        return result;
    }
}""",
        }
        return examples.get(rule_id, "// Bad example not available")
    
    def _get_good_example(self, rule_id: str, context: Dict[str, Any]) -> str:
        """Get good code examples for Java rules."""
        examples = {
            "JAVA001_CLASS_NAMING": """public class MyClass {
    private int value;
}""",
            
            "JAVA002_METHOD_NAMING": """public class Calculator {
    public int calculateTotal(int a, int b) {
        return a + b;
    }
}""",
            
            "JAVA003_WILDCARD_IMPORTS": """import java.util.List;
import java.util.ArrayList;
import java.io.BufferedReader;
import java.io.FileReader;

public class Example {
    private List<String> items = new ArrayList<>();
}""",
            
            "JAVA004_TOO_MANY_PARAMETERS": """public class UserCreator {
    public void createUser(UserData userData) {
        // method implementation
    }
}

public class UserData {
    private String firstName;
    private String lastName;
    private String email;
    // other fields with getters/setters
}""",
            
            "JAVA005_LONG_METHOD": """public class OrderProcessor {
    public void processOrder(Order order) {
        validateOrder(order);
        double total = calculateTotal(order);
        updateInventory(order);
        saveOrder(order, total);
        sendConfirmation(order);
        logTransaction(order);
    }
    
    private void validateOrder(Order order) { /* ... */ }
    private double calculateTotal(Order order) { /* ... */ }
    private void updateInventory(Order order) { /* ... */ }
    private void saveOrder(Order order, double total) { /* ... */ }
    private void sendConfirmation(Order order) { /* ... */ }
    private void logTransaction(Order order) { /* ... */ }
}""",
            
            "JAVA006_MAGIC_NUMBERS": """public class DiscountCalculator {
    private static final double HIGH_DISCOUNT_THRESHOLD = 100.0;
    private static final double MEDIUM_DISCOUNT_THRESHOLD = 50.0;
    private static final double HIGH_DISCOUNT_RATE = 0.9;
    private static final double MEDIUM_DISCOUNT_RATE = 0.95;
    
    public double calculateDiscount(double price) {
        if (price > HIGH_DISCOUNT_THRESHOLD) {
            return price * HIGH_DISCOUNT_RATE;
        } else if (price > MEDIUM_DISCOUNT_THRESHOLD) {
            return price * MEDIUM_DISCOUNT_RATE;
        } else {
            return price;
        }
    }
}""",
            
            "JAVA007_MISSING_INCLUDE_GUARD": """package com.example.service;

public class UserService {
    private UserRepository userRepository;
}""",
            
            "JAVA008_PUBLIC_FIELDS": """public class User {
    private String name;
    private String email;
    private int age;
    
    // Getters and setters
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    // ... other getters/setters
}""",
            
            "JAVA009_EXCEPTION_HANDLING": """public class FileProcessor {
    public void processFile(String filename) {
        try {
            BufferedReader reader = new BufferedReader(new FileReader(filename));
            // process file
        } catch (FileNotFoundException e) {
            logger.error("File not found: " + filename, e);
            throw new ProcessingException("Cannot find file: " + filename, e);
        } catch (IOException e) {
            logger.error("Error reading file: " + filename, e);
            throw new ProcessingException("Error reading file: " + filename, e);
        }
    }
}""",
            
            "JAVA010_STRING_CONCATENATION": """public class StringExample {
    public String buildListString(List<String> items) {
        StringBuilder builder = new StringBuilder();
        for (String item : items) {
            builder.append(item).append(", ");
        }
        return builder.toString();
    }
}""",
        }
        return examples.get(rule_id, "// Good example not available")
    
    def _get_next_steps(self, rule_id: str, context: Dict[str, Any]) -> list[str]:
        """Get next learning steps for Java rules."""
        steps = {
            "JAVA001_CLASS_NAMING": [
                "Study Java naming conventions from Oracle documentation",
                "Practice renaming classes in existing code",
                "Set up IDE to enforce naming conventions",
            ],
            "JAVA002_METHOD_NAMING": [
                "Learn camelCase vs PascalCase conventions",
                "Practice method naming in your projects",
                "Use IDE refactoring tools to rename methods",
            ],
            "JAVA003_WILDCARD_IMPORTS": [
                "Learn about Java package organization",
                "Practice explicit imports in your code",
                "Configure IDE to organize imports automatically",
            ],
            "JAVA004_TOO_MANY_PARAMETERS": [
                "Study parameter object pattern",
                "Learn about builder pattern",
                "Practice refactoring methods with many parameters",
            ],
            "JAVA005_LONG_METHOD": [
                "Study Single Responsibility Principle",
                "Practice extracting methods from long methods",
                "Learn about method composition patterns",
            ],
            "JAVA006_MAGIC_NUMBERS": [
                "Learn about Java constants (static final)",
                "Practice extracting magic numbers",
                "Study configuration management in Java",
            ],
            "JAVA007_MISSING_INCLUDE_GUARD": [
                "Study Java package structure",
                "Learn about organizing code in packages",
                "Practice creating proper package hierarchies",
            ],
            "JAVA008_PUBLIC_FIELDS": [
                "Study encapsulation principle",
                "Learn about getter/setter patterns",
                "Practice making fields private with proper accessors",
            ],
            "JAVA009_EXCEPTION_HANDLING": [
                "Study Java exception hierarchy",
                "Learn about checked vs unchecked exceptions",
                "Practice writing specific exception handlers",
            ],
            "JAVA010_STRING_CONCATENATION": [
                "Study StringBuilder vs StringBuffer",
                "Learn about string performance in Java",
                "Practice optimizing string operations",
            ],
        }
        return steps.get(rule_id, [
            "Practice this concept with simple exercises",
            "Review the learning resources provided",
            "Apply this pattern in your next project",
        ])
