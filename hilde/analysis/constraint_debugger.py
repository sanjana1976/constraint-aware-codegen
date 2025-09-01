#!/usr/bin/env python3
"""
HILDE Constraint-Aware Debugging Module
Analyzes code for constraint violations and provides human-readable explanations
"""

import ast
import re
import json
import os
from typing import List, Dict, Any, Optional, Tuple
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
    def __init__(self, constraints_file: str = "constraints.json"):
        self.constraints_file = constraints_file
        self.constraints = self._load_constraints()
        self.violations = []
    
    def _load_constraints(self) -> Dict[str, Any]:
        """Load constraints from JSON file"""
        try:
            constraints_path = Path(self.constraints_file)
            if not constraints_path.exists():
                # Create default constraints file
                self._create_default_constraints()
            
            with open(constraints_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading constraints: {e}")
            return {"constraints": {}}
    
    def _create_default_constraints(self):
        """Create default constraints file if it doesn't exist"""
        default_constraints = {
            "constraints": {
                "no_global_vars": {
                    "enabled": True,
                    "description": "Prevent global variable declarations",
                    "severity": "warning",
                    "message": "Global variables can cause hidden side effects and make code harder to test and maintain."
                },
                "sanitize_inputs": {
                    "enabled": True,
                    "description": "Ensure user inputs are properly sanitized",
                    "severity": "error",
                    "message": "User inputs should be sanitized to prevent injection attacks and data corruption."
                }
            }
        }
        
        with open(self.constraints_file, 'w') as f:
            json.dump(default_constraints, f, indent=2)
    
    def analyze_code(self, code: str, language: str = "python") -> List[ConstraintViolation]:
        """
        Analyze code for constraint violations
        
        Args:
            code: The code to analyze
            language: Programming language of the code
            
        Returns:
            List of constraint violations found
        """
        self.violations = []
        
        if language.lower() == "python":
            self._analyze_python_code(code)
        elif language.lower() in ["javascript", "js"]:
            self._analyze_javascript_code(code)
        elif language.lower() in ["typescript", "ts"]:
            self._analyze_typescript_code(code)
        else:
            # Fallback to regex-based analysis
            self._analyze_generic_code(code, language)
        
        return self.violations
    
    def _analyze_python_code(self, code: str):
        """Analyze Python code using AST"""
        try:
            tree = ast.parse(code)
            
            # Check each constraint
            for rule_name, rule_config in self.constraints.get("constraints", {}).items():
                if not rule_config.get("enabled", False):
                    continue
                
                if rule_name == "no_global_vars":
                    self._check_global_variables(tree, code, rule_config)
                elif rule_name == "sanitize_inputs":
                    self._check_input_sanitization(tree, code, rule_config)
                elif rule_name == "disallow_raw_sql":
                    self._check_raw_sql(tree, code, rule_config)
                elif rule_name == "no_hardcoded_secrets":
                    self._check_hardcoded_secrets(tree, code, rule_config)
                elif rule_name == "require_error_handling":
                    self._check_error_handling(tree, code, rule_config)
                elif rule_name == "require_type_hints":
                    self._check_type_hints(tree, code, rule_config)
        
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
    
    def _check_global_variables(self, tree: ast.AST, code: str, rule_config: Dict[str, Any]):
        """Check for global variable declarations"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                line_num = node.lineno
                line_content = code.split('\n')[line_num - 1] if line_num <= len(code.split('\n')) else ""
                
                self.violations.append(ConstraintViolation(
                    rule="no_global_vars",
                    line=line_num,
                    column=node.col_offset,
                    explanation=rule_config.get("message", "Global variable declaration found"),
                    severity=rule_config.get("severity", "warning"),
                    code_snippet=line_content.strip()
                ))
    
    def _check_input_sanitization(self, tree: ast.AST, code: str, rule_config: Dict[str, Any]):
        """Check for proper input sanitization"""
        input_functions = ['input', 'raw_input', 'sys.stdin.read', 'sys.stdin.readline']
        sanitization_functions = ['strip', 'escape', 'sanitize', 'validate', 'clean']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if it's an input function
                if isinstance(node.func, ast.Name) and node.func.id in input_functions:
                    # Check if the result is sanitized
                    line_num = node.lineno
                    line_content = code.split('\n')[line_num - 1] if line_num <= len(code.split('\n')) else ""
                    
                    # Simple check: look for sanitization in the same line or nearby
                    is_sanitized = any(func in line_content for func in sanitization_functions)
                    
                    if not is_sanitized:
                        self.violations.append(ConstraintViolation(
                            rule="sanitize_inputs",
                            line=line_num,
                            column=node.col_offset,
                            explanation=rule_config.get("message", "Input not properly sanitized"),
                            severity=rule_config.get("severity", "error"),
                            code_snippet=line_content.strip()
                        ))
    
    def _check_raw_sql(self, tree: ast.AST, code: str, rule_config: Dict[str, Any]):
        """Check for raw SQL queries"""
        sql_patterns = [
            r'SELECT\s+.*FROM',
            r'INSERT\s+INTO',
            r'UPDATE\s+.*SET',
            r'DELETE\s+FROM',
            r'DROP\s+TABLE',
            r'CREATE\s+TABLE'
        ]
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in sql_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Check if it's using parameterized queries
                    if not any(param in line for param in ['%s', '?', ':', 'format(', 'f"']):
                        self.violations.append(ConstraintViolation(
                            rule="disallow_raw_sql",
                            line=i,
                            column=0,
                            explanation=rule_config.get("message", "Raw SQL query detected without parameterization"),
                            severity=rule_config.get("severity", "error"),
                            code_snippet=line.strip()
                        ))
    
    def _check_hardcoded_secrets(self, tree: ast.AST, code: str, rule_config: Dict[str, Any]):
        """Check for hardcoded secrets"""
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']'
        ]
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.violations.append(ConstraintViolation(
                        rule="no_hardcoded_secrets",
                        line=i,
                        column=0,
                        explanation=rule_config.get("message", "Hardcoded secret detected"),
                        severity=rule_config.get("severity", "error"),
                        code_snippet=line.strip()
                    ))
    
    def _check_error_handling(self, tree: ast.AST, code: str, rule_config: Dict[str, Any]):
        """Check for proper error handling"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_try_except = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Try):
                        has_try_except = True
                        break
                
                if not has_try_except and len(node.body) > 0:
                    # Check if function has any risky operations
                    has_risky_ops = False
                    for child in ast.walk(node):
                        if isinstance(child, (ast.Call, ast.Attribute)):
                            has_risky_ops = True
                            break
                    
                    if has_risky_ops:
                        self.violations.append(ConstraintViolation(
                            rule="require_error_handling",
                            line=node.lineno,
                            column=node.col_offset,
                            explanation=rule_config.get("message", "Function lacks proper error handling"),
                            severity=rule_config.get("severity", "warning"),
                            code_snippet=code.split('\n')[node.lineno - 1].strip()
                        ))
    
    def _check_type_hints(self, tree: ast.AST, code: str, rule_config: Dict[str, Any]):
        """Check for type hints in function definitions"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has return type annotation
                if node.returns is None:
                    self.violations.append(ConstraintViolation(
                        rule="require_type_hints",
                        line=node.lineno,
                        column=node.col_offset,
                        explanation=rule_config.get("message", "Function missing return type hint"),
                        severity=rule_config.get("severity", "info"),
                        code_snippet=code.split('\n')[node.lineno - 1].strip()
                    ))
                
                # Check if parameters have type annotations
                for arg in node.args.args:
                    if arg.annotation is None:
                        self.violations.append(ConstraintViolation(
                            rule="require_type_hints",
                            line=node.lineno,
                            column=node.col_offset,
                            explanation=rule_config.get("message", f"Parameter '{arg.arg}' missing type hint"),
                            severity=rule_config.get("severity", "info"),
                            code_snippet=code.split('\n')[node.lineno - 1].strip()
                        ))
    
    def _analyze_javascript_code(self, code: str):
        """Analyze JavaScript code using regex patterns"""
        lines = code.split('\n')
        
        # Check for eval usage
        for i, line in enumerate(lines, 1):
            if 'eval(' in line:
                self.violations.append(ConstraintViolation(
                    rule="no_eval",
                    line=i,
                    column=line.find('eval('),
                    explanation="eval() can execute arbitrary code and is a security risk",
                    severity="error",
                    code_snippet=line.strip()
                ))
    
    def _analyze_typescript_code(self, code: str):
        """Analyze TypeScript code (similar to JavaScript for now)"""
        self._analyze_javascript_code(code)
    
    def _analyze_generic_code(self, code: str, language: str):
        """Fallback analysis using regex patterns"""
        lines = code.split('\n')
        
        # Generic patterns that might apply to multiple languages
        patterns = {
            'hardcoded_secrets': r'(password|api_key|secret|token)\s*=\s*["\'][^"\']+["\']',
            'raw_sql': r'(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE)\s+.*',
            'eval_usage': r'eval\s*\('
        }
        
        for i, line in enumerate(lines, 1):
            for pattern_name, pattern in patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    self.violations.append(ConstraintViolation(
                        rule=pattern_name,
                        line=i,
                        column=0,
                        explanation=f"Potential {pattern_name.replace('_', ' ')} detected",
                        severity="warning",
                        code_snippet=line.strip()
                    ))
    
    def get_violations_summary(self) -> Dict[str, Any]:
        """Get a summary of constraint violations"""
        if not self.violations:
            return {
                "total_violations": 0,
                "by_severity": {},
                "by_rule": {},
                "status": "compliant"
            }
        
        by_severity = {}
        by_rule = {}
        
        for violation in self.violations:
            # Count by severity
            by_severity[violation.severity] = by_severity.get(violation.severity, 0) + 1
            
            # Count by rule
            by_rule[violation.rule] = by_rule.get(violation.rule, 0) + 1
        
        # Determine overall status
        if by_severity.get("error", 0) > 0:
            status = "non_compliant"
        elif by_severity.get("warning", 0) > 0:
            status = "warnings"
        else:
            status = "compliant"
        
        return {
            "total_violations": len(self.violations),
            "by_severity": by_severity,
            "by_rule": by_rule,
            "status": status
        }

# Example usage
if __name__ == "__main__":
    debugger = ConstraintDebugger()
    
    # Test with sample code
    test_code = """
import os

def process_user_input():
    user_data = input("Enter data: ")
    return user_data

def connect_database():
    password = "secret123"
    query = "SELECT * FROM users WHERE id = " + user_id
    return query

global_var = "I'm global"
"""
    
    violations = debugger.analyze_code(test_code, "python")
    
    print("Constraint Violations Found:")
    for violation in violations:
        print(f"  {violation.rule} (line {violation.line}): {violation.explanation}")
    
    summary = debugger.get_violations_summary()
    print(f"\nSummary: {summary}")