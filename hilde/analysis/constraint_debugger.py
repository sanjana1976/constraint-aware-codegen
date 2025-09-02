#!/usr/bin/env python3
"""
HILDE Constraint-Aware Debugging Module
Focused static code analysis tool for Python code
Analyzes code for specific rule violations using AST parsing
"""

import ast
import json
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ConstraintViolation:
    rule: str
    line: int
    column: int
    explanation: str
    severity: str
    code_snippet: str

class ConstraintDebugger:
    def __init__(self):
        self.violations = []
        self.max_function_length = 20  # Configurable limit for function length
    
    def analyze_code(self, code: str) -> List[ConstraintViolation]:
        """
        Analyze Python code for constraint violations
        
        Args:
            code: The Python code to analyze
            
        Returns:
            List of constraint violations found
        """
        self.violations = []
        self._analyze_python_code(code)
        return self.violations
    
    def _analyze_python_code(self, code: str):
        """Analyze Python code using AST for three specific checks"""
        try:
            tree = ast.parse(code)
            
            # Check for global variables
            self._check_global_variables(tree, code)
            
            # Check for input sanitization
            self._check_input_sanitization(tree, code)
            
            # Check for function length
            self._check_max_function_length(tree, code)
        
        except SyntaxError as e:
            # If code has syntax errors, add a violation
            self.violations.append(ConstraintViolation(
                rule="syntax_error",
                line=e.lineno or 1,
                column=e.offset or 0,
                explanation=f"Syntax error in code: {e.msg}",
                severity="error",
                code_snippet=code.split('\n')[e.lineno - 1] if e.lineno else ""
            ))
    
    def _check_global_variables(self, tree: ast.AST, code: str):
        """Check for global variable declarations"""
        lines = code.split('\n')
        
        # Check for top-level assignments (global variables)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Check if this assignment is at module level (not inside a function/class)
                if self._is_module_level(node, tree):
                    line_num = node.lineno
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                    
                    self.violations.append(ConstraintViolation(
                        rule="no_global_vars",
                        line=line_num,
                        column=node.col_offset,
                        explanation="Global variable declaration found. Global variables can cause hidden side effects and make code harder to test and maintain.",
                        severity="warning",
                        code_snippet=line_content.strip()
                    ))
    
    def _is_module_level(self, node: ast.AST, tree: ast.AST) -> bool:
        """Check if a node is at module level (not inside function/class)"""
        for parent in ast.walk(tree):
            if hasattr(parent, 'body'):
                if node in parent.body:
                    # If parent is a function or class, this is not module level
                    if isinstance(parent, (ast.FunctionDef, ast.ClassDef)):
                        return False
                    # If parent is the module itself, this is module level
                    elif isinstance(parent, ast.Module):
                        return True
        return True
    
    def _check_input_sanitization(self, tree: ast.AST, code: str):
        """Check for proper input sanitization"""
        lines = code.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if it's an input function call
                if isinstance(node.func, ast.Name) and node.func.id == 'input':
                    line_num = node.lineno
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                    
                    # Check if the input is assigned to a variable and if it's sanitized
                    # Look for patterns like: variable = input("prompt")
                    # and check if the variable is later sanitized
                    is_sanitized = self._check_input_sanitization_context(node, tree, lines)
                    
                    if not is_sanitized:
                        self.violations.append(ConstraintViolation(
                            rule="sanitize_inputs",
                            line=line_num,
                            column=node.col_offset,
                            explanation="User input not properly sanitized. User inputs should be sanitized to prevent injection attacks and data corruption.",
                            severity="error",
                            code_snippet=line_content.strip()
                        ))
    
    def _check_input_sanitization_context(self, input_node: ast.Call, tree: ast.AST, lines: List[str]) -> bool:
        """Check if input is properly sanitized in its context"""
        # Look for the parent assignment
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if input_node in ast.walk(node):
                    # Check if the assigned variable is sanitized later
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            # Look for sanitization of this variable
                            return self._find_sanitization(var_name, tree, lines)
        return False
    
    def _find_sanitization(self, var_name: str, tree: ast.AST, lines: List[str]) -> bool:
        """Find if a variable is sanitized"""
        sanitization_methods = ['.strip()', '.lower()', '.upper()', '.replace(', 'escape', 'sanitize', 'validate']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == var_name:
                # Check if this variable is used in a sanitization context
                line_num = node.lineno
                if line_num <= len(lines):
                    line_content = lines[line_num - 1]
                    if any(method in line_content for method in sanitization_methods):
                        return True
        return False
    
    def _check_max_function_length(self, tree: ast.AST, code: str):
        """Check for functions that exceed maximum length"""
        lines = code.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Calculate function length using line numbers
                function_start = node.lineno
                
                # Find the last line of the function
                function_end = self._get_function_end_line(node, lines)
                function_length = function_end - function_start + 1
                
                if function_length > self.max_function_length:
                    self.violations.append(ConstraintViolation(
                        rule="max_function_length",
                        line=function_start,
                        column=node.col_offset,
                        explanation=f"Function '{node.name}' is {function_length} lines long, exceeding the maximum of {self.max_function_length} lines. Long functions are hard to maintain and should be broken into smaller functions.",
                        severity="warning",
                        code_snippet=f"def {node.name}(...):"
                    ))
    
    def _get_function_end_line(self, function_node: ast.FunctionDef, lines: List[str]) -> int:
        """Get the last line number of a function"""
        # Start with the function's own line number
        last_line = function_node.lineno
        
        # Walk through all nodes in the function to find the last line
        for node in ast.walk(function_node):
            if hasattr(node, 'lineno') and node.lineno > last_line:
                last_line = node.lineno
        
        # If we couldn't find a better end line, estimate based on indentation
        if last_line == function_node.lineno and function_node.body:
            # Look for the last statement in the function body
            last_stmt = function_node.body[-1]
            if hasattr(last_stmt, 'lineno'):
                last_line = last_stmt.lineno
        
        return last_line

# Example usage
if __name__ == "__main__":
    debugger = ConstraintDebugger()
    
    # Test with sample code that demonstrates all three checks
    test_code = """
import os

# Global variable (should trigger no_global_vars)
global_config = {"api_key": "sk-1234567890"}

def process_user_input():
    # Unsanitized input (should trigger sanitize_inputs)
    user_data = input("Enter data: ")
    return user_data

def very_long_function():
    # This function is intentionally long to trigger max_function_length
    print("This is line 1")
    print("This is line 2")
    print("This is line 3")
    print("This is line 4")
    print("This is line 5")
    print("This is line 6")
    print("This is line 7")
    print("This is line 8")
    print("This is line 9")
    print("This is line 10")
    print("This is line 11")
    print("This is line 12")
    print("This is line 13")
    print("This is line 14")
    print("This is line 15")
    print("This is line 16")
    print("This is line 17")
    print("This is line 18")
    print("This is line 19")
    print("This is line 20")
    print("This is line 21")  # This should trigger the violation
    return "done"

def good_function():
    # This function is short and should not trigger violations
    sanitized_input = input("Enter data: ").strip()
    return sanitized_input
"""
    
    violations = debugger.analyze_code(test_code)
    
    print("🔍 Constraint Violations Found:")
    print("=" * 50)
    
    if violations:
        for violation in violations:
            print(f"\n❌ Rule: {violation.rule}")
            print(f"   Line: {violation.line}")
            print(f"   Severity: {violation.severity}")
            print(f"   Explanation: {violation.explanation}")
            print(f"   Code: {violation.code_snippet}")
    else:
        print("✅ No constraint violations found!")
    
    print(f"\n📊 Total violations: {len(violations)}")