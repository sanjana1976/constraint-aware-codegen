#!/usr/bin/env python3
"""
HiLDe-Lite Analysis Engine - Streamlined Version
Uses GPT-4 API to summarize constraint violations into human-readable format
"""

import openai
import os
import json
from typing import List, Dict, Any

class GPT4AnalysisEngine:
    def __init__(self, api_key: str = None, model: str = "gpt-4"):
        """
        Initialize the GPT-4 analysis engine
        
        Args:
            api_key: OpenAI API key (if None, will try to get from environment)
            model: OpenAI model to use (default: gpt-4)
        """
        self.model = model
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if self.api_key:
            openai.api_key = self.api_key
            print(f"✅ GPT-4 Analysis Engine initialized with {model}")
        else:
            print("❌ Error: No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
            raise ValueError("OpenAI API key is required")
    
    def summarize_violations(self, violations: List[Dict[str, Any]]) -> str:
        """
        Summarize constraint violations into human-readable format using GPT-4
        
        Args:
            violations: List of constraint violations from ConstraintDebugger
            
        Returns:
            Human-readable summary of violations and fixes
        """
        if not violations:
            return "✅ No constraint violations found. Code follows all defined rules."
        
        try:
            # Create prompt for violation summarization
            violations_json = json.dumps(violations, indent=2)
            
            prompt = f"""Act as a senior software engineer and code quality expert. 

The following JSON contains constraint violations found in a Python code snippet:
{violations_json}

Please provide a concise, high-level summary that:
1. Explains what problems were found
2. Suggests how to fix each issue
3. Uses clear, non-technical language suitable for developers
4. Focuses on the most critical issues first

Format your response as a clear, actionable summary that a developer can immediately understand and act upon."""

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior software engineer specializing in code quality, security, and best practices. Provide clear, actionable feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ GPT-4 violation summarization failed: {e}")
            # Fallback to simple summary
            return self._create_fallback_summary(violations)
    
    def _create_fallback_summary(self, violations: List[Dict[str, Any]]) -> str:
        """Create a simple fallback summary when GPT-4 is unavailable"""
        if not violations:
            return "✅ No constraint violations found."
        
        summary = f"🔍 Found {len(violations)} constraint violation(s):\n"
        
        for i, violation in enumerate(violations, 1):
            rule = violation.get('rule', 'Unknown rule')
            line = violation.get('line', 'Unknown line')
            explanation = violation.get('explanation', 'No explanation available')
            severity = violation.get('severity', 'warning')
            
            severity_emoji = "🔴" if severity == "error" else "🟡" if severity == "warning" else "🔵"
            
            summary += f"\n{i}. {severity_emoji} {rule} (Line {line}): {explanation}"
        
        return summary