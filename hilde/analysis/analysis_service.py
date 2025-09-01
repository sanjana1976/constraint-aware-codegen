#!/usr/bin/env python3
"""
HILDE Analysis Service
Provides semantic analysis of token alternatives using GPT-4.1-nano
"""

import os
import json
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HILDE Analysis Service", version="1.0.0")

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.warning("OPENAI_API_KEY not found in environment variables")

class AnalysisRequest(BaseModel):
    base_completion: str
    original_token: str
    alternative_token: str
    context: str
    language: str = "python"

class AnalysisResponse(BaseModel):
    detailed_explanation: str
    explanation_summary: str
    category: str  # "Significant", "Minor", or "Incorrect"
    importance_score: float  # 0.0 to 1.0

class HILDEAnalysisEngine:
    def __init__(self):
        self.model = "gpt-4o-mini"  # Using GPT-4o-mini as a proxy for GPT-4.1-nano
    
    def analyze_token_alternative(self, request: AnalysisRequest) -> AnalysisResponse:
        """Analyze a token alternative and provide structured explanation"""
        try:
            prompt = self._build_analysis_prompt(request)
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse the response
            content = response.choices[0].message.content
            return self._parse_analysis_response(content, request)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # Return a fallback response
            return AnalysisResponse(
                detailed_explanation=f"Analysis failed: {str(e)}",
                explanation_summary="Analysis error",
                category="Minor",
                importance_score=0.1
            )
    
    def _get_system_prompt(self) -> str:
        return """You are an expert code analyzer for the HILDE system. Your task is to analyze token alternatives in code and provide structured explanations.

For each token alternative, provide:
1. A detailed explanation of how the change affects the code
2. A concise summary (1-2 lines)
3. A category: "Significant" (affects behavior/security/efficiency), "Minor" (stylistic), or "Incorrect" (syntax error)
4. An importance score from 0.0 to 1.0

Focus on security implications, performance impacts, and code correctness."""
    
    def _build_analysis_prompt(self, request: AnalysisRequest) -> str:
        return f"""Analyze this token alternative in {request.language} code:

Context: {request.context}
Base completion: {request.base_completion}
Original token: "{request.original_token}"
Alternative token: "{request.alternative_token}"

Provide your analysis in this exact JSON format:
{{
    "detailed_explanation": "Detailed analysis of the change...",
    "explanation_summary": "Brief summary...",
    "category": "Significant|Minor|Incorrect",
    "importance_score": 0.75
}}"""
    
    def _parse_analysis_response(self, content: str, request: AnalysisRequest) -> AnalysisResponse:
        """Parse the LLM response into structured format"""
        try:
            # Try to extract JSON from the response
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                data = json.loads(json_str)
                
                return AnalysisResponse(
                    detailed_explanation=data.get("detailed_explanation", "No explanation provided"),
                    explanation_summary=data.get("explanation_summary", "No summary"),
                    category=data.get("category", "Minor"),
                    importance_score=float(data.get("importance_score", 0.5))
                )
        except Exception as e:
            logger.warning(f"Failed to parse JSON response: {e}")
        
        # Fallback parsing
        return self._fallback_analysis(request)
    
    def _fallback_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        """Provide fallback analysis when parsing fails"""
        if request.original_token == request.alternative_token:
            return AnalysisResponse(
                detailed_explanation="No change detected",
                explanation_summary="No change",
                category="Minor",
                importance_score=0.0
            )
        
        # Basic heuristic analysis
        if len(request.original_token) != len(request.alternative_token):
            return AnalysisResponse(
                detailed_explanation=f"Token length changed from {len(request.original_token)} to {len(request.alternative_token)}",
                explanation_summary="Token length change",
                category="Minor",
                importance_score=0.3
            )
        
        return AnalysisResponse(
            detailed_explanation=f"Token changed from '{request.original_token}' to '{request.alternative_token}'",
            explanation_summary="Token substitution",
            category="Minor",
            importance_score=0.2
        )

# Initialize the analysis engine
analysis_engine = HILDEAnalysisEngine()

@app.post("/analysis", response_model=AnalysisResponse)
async def analyze_token_alternative(request: AnalysisRequest):
    """Analyze a token alternative and provide structured explanation"""
    return analysis_engine.analyze_token_alternative(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model": analysis_engine.model}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
