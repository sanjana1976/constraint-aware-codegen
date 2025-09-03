#!/usr/bin/env python3
"""
HiLDe-Lite Analysis Engine
Uses GPT-4 API to analyze complete code blocks
Provides human-readable explanations for code quality, security, and best practices
"""

import openai
import os
import json
from typing import Dict, Any

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
    
    def analyze_code_completion(self, code: str) -> Dict[str, Any]:
        """
        Analyze a complete code block using GPT-4
        
        Args:
            code: Complete code block to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(code)
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            analysis = self._parse_analysis_response(response.choices[0].message.content)
            return analysis
            
        except Exception as e:
            print(f"❌ GPT-4 analysis failed: {e}")
            return {
                "analysis": "Analysis failed due to API error",
                "security_issues": [],
                "best_practices": [],
                "overall_rating": "Error"
            }
    
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
    
    def _create_analysis_prompt(self, code: str) -> str:
        """Create prompt for GPT-4 analysis of complete code block"""
        return f"""Analyze this Python code for security, correctness, and best practices:

```python
{code}
```

Provide a comprehensive analysis in this JSON format:
{{
    "analysis": "Overall assessment of the code quality and functionality",
    "security_issues": [
        "List any security vulnerabilities or concerns"
    ],
    "best_practices": [
        "List any coding best practices that should be followed"
    ],
    "overall_rating": "Excellent|Good|Fair|Poor",
    "recommendations": [
        "Specific recommendations for improvement"
    ]
}}"""
    
    def _get_system_prompt(self) -> str:
        """System prompt for GPT-4"""
        return """You are an expert code analyzer specializing in Python security, correctness, and best practices. 

Your analysis should focus on:
1. Security vulnerabilities (injection attacks, weak cryptography, etc.)
2. Code correctness and potential bugs
3. Best practices and code quality
4. Performance implications
5. Maintainability and readability

Provide clear, actionable feedback that helps developers write better, more secure code."""
    
    def _parse_analysis_response(self, content: str) -> Dict[str, Any]:
        """Parse GPT-4 response"""
        try:
            # Try to extract JSON from response
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback parsing
        return {
            "analysis": "Analysis parsing failed - could not extract structured response",
            "security_issues": ["Unable to parse security analysis"],
            "best_practices": ["Unable to parse best practices"],
            "overall_rating": "Error",
            "recommendations": ["Please check the raw response for details"]
        }
    


# Example usage and testing
if __name__ == "__main__":
    # Initialize the analysis engine
    analysis_engine = GPT4AnalysisEngine()
    
    # Test with a complete code block (example from the paper)
    sample_code = """
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
"""
    
    print("🧪 Testing GPT-4 Analysis Engine...")
    print(f"📝 Analyzing code:\n{sample_code}")
    
    result = analysis_engine.analyze_code_completion(sample_code)
    
    print(f"\n📊 Analysis Results:")
    print(f"Overall Assessment: {result.get('analysis', 'N/A')}")
    print(f"Rating: {result.get('overall_rating', 'N/A')}")
    
    security_issues = result.get('security_issues', [])
    if security_issues:
        print(f"\n🔒 Security Issues:")
        for issue in security_issues:
            print(f"  • {issue}")
    
    best_practices = result.get('best_practices', [])
    if best_practices:
        print(f"\n✅ Best Practices:")
        for practice in best_practices:
            print(f"  • {practice}")
    
    recommendations = result.get('recommendations', [])
    if recommendations:
        print(f"\n💡 Recommendations:")
        for rec in recommendations:
            print(f"  • {rec}")