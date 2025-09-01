#!/usr/bin/env python3
"""
HiLDe-Lite Analysis Engine
Uses GPT-4 API for semantic analysis of token alternatives
Provides human-readable explanations for code generation decisions
"""

import openai
import os
import json
import time
from typing import Dict, Any, List, Optional

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
            print("⚠️ Warning: No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
            print("   Analysis will use fallback explanations.")
    
    def analyze_alternatives(self, prompt: str, completion: str, alternatives: List[Dict]) -> List[Dict]:
        """
        Analyze token alternatives using GPT-4
        
        Args:
            prompt: Original code prompt
            completion: Generated completion
            alternatives: List of token alternatives for each position
            
        Returns:
            List of alternatives with added analysis
        """
        if not self.api_key:
            return self._fallback_analysis(alternatives)
        
        analyzed_alternatives = []
        
        # Analyze only highlighted positions to save API calls
        for i, alt_group in enumerate(alternatives):
            if len(alt_group) < 2:
                # No alternatives to analyze
                analyzed_alternatives.append(alt_group)
                continue
            
            # Get the top alternative and a few others
            top_token = alt_group[0]
            other_tokens = alt_group[1:3]  # Take up to 2 alternatives
            
            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(
                prompt, completion, top_token, other_tokens, i
            )
            
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=200
                )
                
                analysis = self._parse_analysis_response(response.choices[0].message.content)
                
                # Add analysis to alternatives
                for j, alt in enumerate(alt_group):
                    if j == 0:
                        alt["analysis"] = analysis.get("top_analysis", {})
                    elif j-1 < len(analysis.get("alternatives", [])):
                        alt["analysis"] = analysis["alternatives"][j-1]
                    else:
                        alt["analysis"] = {
                            "explanation": "Alternative token", 
                            "category": "Minor",
                            "importance_score": 0.3
                        }
                
            except Exception as e:
                print(f"⚠️ GPT-4 analysis failed for position {i}: {e}")
                # Add fallback analysis
                for alt in alt_group:
                    alt["analysis"] = {
                        "explanation": "Analysis unavailable", 
                        "category": "Minor",
                        "importance_score": 0.5
                    }
            
            analyzed_alternatives.append(alt_group)
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
        
        return analyzed_alternatives
    
    def _create_analysis_prompt(self, prompt: str, completion: str, top_token: Dict, other_tokens: List[Dict], position: int) -> str:
        """Create prompt for GPT-4 analysis"""
        return f"""Analyze these token alternatives in Python code:

Context: {prompt}
Generated completion: {completion}
Position: {position}

Top token: "{top_token['token']}" (probability: {top_token['probability']:.3f})
Alternatives: {[f'"{t['token']}" (probability: {t['probability']:.3f})' for t in other_tokens]}

Provide analysis in this JSON format:
{{
    "top_analysis": {{
        "explanation": "Brief explanation of the top choice",
        "category": "Significant|Minor|Incorrect",
        "importance_score": 0.8
    }},
    "alternatives": [
        {{
            "explanation": "Brief explanation of this alternative",
            "category": "Significant|Minor|Incorrect",
            "importance_score": 0.6
        }}
    ]
}}"""
    
    def _get_system_prompt(self) -> str:
        """System prompt for GPT-4"""
        return """You are an expert code analyzer for the HiLDe system. Analyze token alternatives in code and provide structured explanations.

For each alternative, provide:
1. A brief explanation of the choice
2. A category: "Significant" (affects behavior/security/efficiency), "Minor" (stylistic), or "Incorrect" (syntax error)
3. An importance score from 0.0 to 1.0

Focus on security implications, performance impacts, and code correctness. Be concise but informative."""
    
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
            "top_analysis": {
                "explanation": "Analysis parsing failed",
                "category": "Minor",
                "importance_score": 0.5
            },
            "alternatives": []
        }
    
    def _fallback_analysis(self, alternatives: List[Dict]) -> List[Dict]:
        """Fallback analysis when GPT-4 is not available"""
        for alt_group in alternatives:
            for alt in alt_group:
                alt["analysis"] = {
                    "explanation": "GPT-4 analysis not available (no API key)",
                    "category": "Minor",
                    "importance_score": 0.5
                }
        return alternatives
    
    def analyze_single_alternative(self, prompt: str, completion: str, token: str, position: int) -> Dict[str, Any]:
        """
        Analyze a single token alternative (for detailed analysis)
        
        Args:
            prompt: Original code prompt
            completion: Generated completion
            token: Token to analyze
            position: Position in the completion
            
        Returns:
            Analysis dictionary
        """
        if not self.api_key:
            return {
                "explanation": "GPT-4 analysis not available",
                "category": "Minor",
                "importance_score": 0.5
            }
        
        try:
            analysis_prompt = f"""Analyze this specific token choice in Python code:

Context: {prompt}
Generated completion: {completion}
Token: "{token}" at position {position}

Provide a detailed analysis in this JSON format:
{{
    "explanation": "Detailed explanation of why this token was chosen and its implications",
    "category": "Significant|Minor|Incorrect",
    "importance_score": 0.8,
    "security_implications": "Any security considerations",
    "performance_impact": "Any performance implications",
    "best_practices": "Relevant coding best practices"
}}"""
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            return self._parse_analysis_response(response.choices[0].message.content)
            
        except Exception as e:
            print(f"⚠️ Single token analysis failed: {e}")
            return {
                "explanation": "Analysis failed",
                "category": "Minor",
                "importance_score": 0.5
            }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics (if available)"""
        if not self.api_key:
            return {"status": "No API key configured"}
        
        try:
            # This would require additional OpenAI API calls to get usage stats
            # For now, return basic info
            return {
                "model": self.model,
                "api_key_configured": True,
                "status": "Ready"
            }
        except:
            return {"status": "Unable to get usage stats"}

# Example usage and testing
if __name__ == "__main__":
    # Initialize the analysis engine
    analysis_engine = GPT4AnalysisEngine()
    
    # Test with sample alternatives
    sample_alternatives = [
        [
            {"token": "return", "probability": 0.95, "token_id": 123},
            {"token": "yield", "probability": 0.03, "token_id": 456},
            {"token": "print", "probability": 0.02, "token_id": 789}
        ],
        [
            {"token": "hashlib", "probability": 0.7, "token_id": 101},
            {"token": "bcrypt", "probability": 0.2, "token_id": 102},
            {"token": "scrypt", "probability": 0.1, "token_id": 103}
        ]
    ]
    
    print("🧪 Testing GPT-4 Analysis Engine...")
    
    result = analysis_engine.analyze_alternatives(
        "def hash_password(password):",
        "return hashlib.sha256(password.encode()).hexdigest()",
        sample_alternatives
    )
    
    print(f"\n📊 Analysis Results:")
    for i, alt_group in enumerate(result):
        print(f"\nPosition {i}:")
        for j, alt in enumerate(alt_group):
            marker = "🟢" if j == 0 else "🔵"
            analysis = alt.get("analysis", {})
            print(f"  {marker} '{alt['token']}' (prob: {alt['probability']:.3f})")
            print(f"     Analysis: {analysis.get('explanation', 'N/A')}")
            print(f"     Category: {analysis.get('category', 'N/A')}")
            print(f"     Importance: {analysis.get('importance_score', 'N/A')}")
    
    # Usage stats
    print(f"\n📈 Usage Stats:")
    for key, value in analysis_engine.get_usage_stats().items():
        print(f"  {key}: {value}")