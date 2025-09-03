#!/usr/bin/env python3
"""
Test script for the new Generate → Analyze → Summarize workflow
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hilde_lite_completion_engine import HiLDeCompletionEngine
from hilde_lite_analysis_engine import GPT4AnalysisEngine
from hilde.analysis.constraint_debugger import ConstraintDebugger

def test_new_workflow():
    """Test the new Generate → Analyze → Summarize workflow"""
    print("🧪 Testing New HiLDe-Lite Workflow")
    print("=" * 50)
    
    # Test prompt that should trigger violations
    test_prompt = "def process_user_input():\n    user_data = input('Enter data: ')\n    return user_data"
    
    print(f"📝 Test Prompt: {test_prompt}")
    print("\n🔄 Step 1: Generating code completion...")
    
    try:
        # Step 1: Generate Code
        completion_engine = HiLDeCompletionEngine()
        completion = completion_engine.generate_completion(test_prompt, max_tokens=50)
        print(f"✅ Generated: {completion}")
        
        # Step 2: Analyze with Constraint Debugger
        print("\n🔍 Step 2: Analyzing with constraint debugger...")
        constraint_debugger = ConstraintDebugger()
        violations = constraint_debugger.analyze_code(completion)
        
        print(f"✅ Found {len(violations)} violations:")
        for i, violation in enumerate(violations, 1):
            severity_emoji = "🔴" if violation.severity == "error" else "🟡" if violation.severity == "warning" else "🔵"
            print(f"  {i}. {severity_emoji} {violation.rule} (Line {violation.line}): {violation.explanation}")
        
        # Step 3: Summarize with GPT-4 (if API key available)
        print("\n📝 Step 3: Summarizing violations with GPT-4...")
        try:
            analysis_engine = GPT4AnalysisEngine()
            violations_dict = [
                {
                    "rule": v.rule,
                    "line": v.line,
                    "column": v.column,
                    "explanation": v.explanation,
                    "severity": v.severity,
                    "code_snippet": v.code_snippet
                }
                for v in violations
            ]
            summary = analysis_engine.summarize_violations(violations_dict)
            print(f"✅ GPT-4 Summary: {summary}")
        except Exception as e:
            print(f"⚠️  GPT-4 summarization failed (API key needed): {e}")
            print("✅ Using fallback summary...")
            if violations:
                summary = f"Found {len(violations)} constraint violation(s). Check the detailed violations above."
            else:
                summary = "No constraint violations found."
            print(f"📋 Fallback Summary: {summary}")
        
        # Final Result
        print(f"\n🎯 Final Result:")
        print(f"  Completion: {completion}")
        print(f"  Violations: {len(violations)}")
        print(f"  Summary: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_new_workflow()
    if success:
        print("\n✅ New workflow test completed successfully!")
    else:
        print("\n❌ New workflow test failed!")