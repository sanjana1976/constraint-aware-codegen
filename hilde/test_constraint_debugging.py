#!/usr/bin/env python3
"""
Test script for HILDE Constraint-Aware Debugging
Demonstrates the constraint checking functionality
"""

import requests
import json
import time

def test_constraint_debugging():
    """Test the constraint debugging functionality"""
    print("🔍 Testing HILDE Constraint-Aware Debugging")
    print("=" * 60)
    
    # Test cases with different constraint violations
    test_cases = [
        {
            "name": "Global Variables Test",
            "code": """
import os

global_var = "I'm a global variable"

def process_data():
    return global_var
""",
            "expected_violations": ["no_global_vars"]
        },
        {
            "name": "Input Sanitization Test",
            "code": """
def get_user_input():
    user_data = input("Enter your data: ")
    return user_data  # Not sanitized
""",
            "expected_violations": ["sanitize_inputs"]
        },
        {
            "name": "Raw SQL Test",
            "code": """
def get_user_by_id(user_id):
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    return query  # Vulnerable to SQL injection
""",
            "expected_violations": ["disallow_raw_sql"]
        },
        {
            "name": "Hardcoded Secrets Test",
            "code": """
def connect_to_api():
    api_key = "sk-1234567890abcdef"
    password = "admin123"
    return api_key, password
""",
            "expected_violations": ["no_hardcoded_secrets"]
        },
        {
            "name": "Error Handling Test",
            "code": """
def risky_operation():
    result = 10 / 0  # No error handling
    return result
""",
            "expected_violations": ["require_error_handling"]
        },
        {
            "name": "Type Hints Test",
            "code": """
def calculate_sum(a, b):
    return a + b  # Missing type hints
""",
            "expected_violations": ["require_type_hints"]
        }
    ]
    
    # Test constraint checking endpoint directly
    print("🧪 Testing Analysis Service Constraint Endpoint")
    print("-" * 40)
    
    for test_case in test_cases:
        print(f"\n📝 Test: {test_case['name']}")
        print(f"Code:\n{test_case['code']}")
        
        try:
            response = requests.post(
                "http://localhost:8002/constraints",
                json={
                    "code": test_case["code"],
                    "language": "python"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                violations = data.get("violations", [])
                summary = data.get("summary", {})
                
                print(f"✅ Constraint check successful")
                print(f"   Violations found: {len(violations)}")
                print(f"   Status: {summary.get('status', 'unknown')}")
                
                for violation in violations:
                    print(f"   🔴 {violation['rule']} (line {violation['line']}): {violation['explanation']}")
                    print(f"      Severity: {violation['severity']}")
                    print(f"      Code: {violation['code_snippet']}")
                
                # Check if expected violations were found
                found_rules = [v["rule"] for v in violations]
                expected_rules = test_case["expected_violations"]
                
                for expected_rule in expected_rules:
                    if expected_rule in found_rules:
                        print(f"   ✅ Expected violation '{expected_rule}' found")
                    else:
                        print(f"   ❌ Expected violation '{expected_rule}' not found")
                
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(0.5)  # Brief pause between requests
    
    # Test integrated HILDE completion with constraint checking
    print("\n\n🎯 Testing Integrated HILDE Completion with Constraints")
    print("-" * 50)
    
    test_prompts = [
        "def hash_password(password):",
        "def connect_database():",
        "def process_user_input():"
    ]
    
    for prompt in test_prompts:
        print(f"\n📝 Prompt: {prompt}")
        
        try:
            response = requests.post(
                "http://localhost:8000/hilde/completion",
                json={
                    "prompt": prompt,
                    "max_tokens": 50,
                    "temperature": 0.1,
                    "top_k": 5,
                    "enable_analysis": True
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                completion = data.get("completion", "")
                violations = data.get("constraint_violations", [])
                
                print(f"✅ Completion: {completion}")
                print(f"🔍 Constraint violations: {len(violations)}")
                
                for violation in violations:
                    print(f"   🔴 {violation['rule']} (line {violation['line']}): {violation['explanation']}")
                
            else:
                print(f"❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(1)

def test_constraint_configuration():
    """Test constraint configuration loading"""
    print("\n\n⚙️ Testing Constraint Configuration")
    print("-" * 40)
    
    try:
        with open("constraints.json", "r") as f:
            constraints = json.load(f)
        
        print("✅ Constraints file loaded successfully")
        print(f"   Total constraints: {len(constraints.get('constraints', {}))}")
        
        for rule_name, rule_config in constraints.get("constraints", {}).items():
            status = "✅ Enabled" if rule_config.get("enabled", False) else "❌ Disabled"
            severity = rule_config.get("severity", "unknown")
            print(f"   {rule_name}: {status} ({severity})")
        
    except Exception as e:
        print(f"❌ Error loading constraints: {e}")

def main():
    """Main test runner"""
    print("🚀 HILDE Constraint-Aware Debugging Test Suite")
    print("=" * 60)
    print("This test suite validates the constraint debugging functionality:")
    print("1. Direct constraint checking via analysis service")
    print("2. Integrated constraint checking in HILDE completion")
    print("3. Constraint configuration validation")
    print("=" * 60)
    
    # Check if services are running
    try:
        # Check analysis service
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code != 200:
            print("❌ Analysis service is not running")
            return
        
        # Check API gateway
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ API gateway is not running")
            return
        
        print("✅ All services are running")
        
        # Run tests
        test_constraint_configuration()
        test_constraint_debugging()
        
        print("\n" + "=" * 60)
        print("🎉 Constraint debugging tests complete!")
        print("📚 Check the results above to verify functionality")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to HILDE services")
        print("   Please start the services first: ./start_hilde.sh")
    except Exception as e:
        print(f"❌ Test suite error: {e}")

if __name__ == "__main__":
    main()