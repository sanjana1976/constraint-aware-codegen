#!/usr/bin/env python3
"""
Example demonstrating HILDE Constraint-Aware Debugging
Shows how to use the constraint checking functionality
"""

import requests
import json

def example_constraint_checking():
    """Example of using constraint checking"""
    
    # Example code with multiple constraint violations
    problematic_code = """
import os

# Global variable (violates no_global_vars)
global_config = {"api_key": "sk-1234567890"}

def get_user_data():
    # Unsanitized input (violates sanitize_inputs)
    user_id = input("Enter user ID: ")
    
    # Raw SQL query (violates disallow_raw_sql)
    query = "SELECT * FROM users WHERE id = " + user_id
    
    # No error handling (violates require_error_handling)
    result = execute_query(query)
    
    return result

def execute_query(sql):
    # Hardcoded credentials (violates no_hardcoded_secrets)
    password = "admin123"
    return sql
"""
    
    print("🔍 Example: Constraint-Aware Debugging")
    print("=" * 50)
    print("Code to analyze:")
    print(problematic_code)
    print("\n" + "=" * 50)
    
    # Check constraints
    try:
        response = requests.post(
            "http://localhost:8002/constraints",
            json={
                "code": problematic_code,
                "language": "python"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            violations = data.get("violations", [])
            summary = data.get("summary", {})
            
            print(f"📊 Analysis Results:")
            print(f"   Total violations: {summary.get('total_violations', 0)}")
            print(f"   Status: {summary.get('status', 'unknown')}")
            print(f"   By severity: {summary.get('by_severity', {})}")
            
            print(f"\n🔴 Constraint Violations Found:")
            for i, violation in enumerate(violations, 1):
                print(f"\n   {i}. Rule: {violation['rule']}")
                print(f"      Line: {violation['line']}")
                print(f"      Severity: {violation['severity']}")
                print(f"      Explanation: {violation['explanation']}")
                print(f"      Code: {violation['code_snippet']}")
            
            # Show how to fix violations
            print(f"\n💡 Suggested Fixes:")
            print("   1. Remove global variables - use function parameters or class attributes")
            print("   2. Sanitize inputs - use input validation and sanitization functions")
            print("   3. Use parameterized queries - replace string concatenation with placeholders")
            print("   4. Add error handling - wrap risky operations in try-catch blocks")
            print("   5. Use environment variables - store secrets in config files or env vars")
            
        else:
            print(f"❌ Constraint check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def example_hilde_completion_with_constraints():
    """Example of HILDE completion with constraint checking"""
    
    print("\n\n🎯 Example: HILDE Completion with Constraint Checking")
    print("=" * 60)
    
    # Test prompts that might generate constraint violations
    prompts = [
        "def authenticate_user(username, password):",
        "def save_user_data(user_data):",
        "def process_payment(amount, card_number):"
    ]
    
    for prompt in prompts:
        print(f"\n📝 Prompt: {prompt}")
        
        try:
            response = requests.post(
                "http://localhost:8000/hilde/completion",
                json={
                    "prompt": prompt,
                    "max_tokens": 100,
                    "temperature": 0.1,
                    "top_k": 5,
                    "enable_analysis": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                completion = data.get("completion", "")
                violations = data.get("constraint_violations", [])
                
                print(f"✅ Generated completion:")
                print(f"   {completion}")
                
                if violations:
                    print(f"🔴 Constraint violations detected:")
                    for violation in violations:
                        print(f"   - {violation['rule']}: {violation['explanation']}")
                else:
                    print(f"✅ No constraint violations detected")
                
            else:
                print(f"❌ Completion failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def example_custom_constraints():
    """Example of custom constraint configuration"""
    
    print("\n\n⚙️ Example: Custom Constraint Configuration")
    print("=" * 50)
    
    # Show how to create custom constraints
    custom_constraints = {
        "constraints": {
            "no_print_statements": {
                "enabled": True,
                "description": "Prevent print statements in production code",
                "severity": "warning",
                "message": "Print statements should be replaced with proper logging."
            },
            "require_docstrings": {
                "enabled": True,
                "description": "Require docstrings for all functions",
                "severity": "info",
                "message": "Functions should have docstrings for better documentation."
            },
            "max_function_length": {
                "enabled": True,
                "description": "Limit function length to 50 lines",
                "severity": "warning",
                "message": "Long functions are hard to maintain. Consider breaking into smaller functions."
            }
        }
    }
    
    print("Custom constraint configuration example:")
    print(json.dumps(custom_constraints, indent=2))
    
    print("\n💡 To use custom constraints:")
    print("   1. Save the configuration to constraints.json")
    print("   2. Restart the analysis service")
    print("   3. The new constraints will be automatically applied")

def main():
    """Main example runner"""
    print("🚀 HILDE Constraint-Aware Debugging Examples")
    print("=" * 60)
    print("This example demonstrates:")
    print("1. Direct constraint checking")
    print("2. HILDE completion with constraint integration")
    print("3. Custom constraint configuration")
    print("=" * 60)
    
    # Check if services are running
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code != 200:
            print("❌ Analysis service is not running")
            print("   Please start the services first: ./start_hilde.sh")
            return
        
        # Run examples
        example_constraint_checking()
        example_hilde_completion_with_constraints()
        example_custom_constraints()
        
        print("\n" + "=" * 60)
        print("🎉 Examples complete!")
        print("📚 The constraint-aware debugging system is working correctly")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to HILDE services")
        print("   Please start the services first: ./start_hilde.sh")
    except Exception as e:
        print(f"❌ Example error: {e}")

if __name__ == "__main__":
    main()