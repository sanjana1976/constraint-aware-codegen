#!/usr/bin/env python3
"""
HILDE API Gateway
Orchestrates communication between completion and analysis services
"""

import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import httpx
from loguru import logger

# Configure logging
logger.add("logs/hilde_gateway.log", rotation="1 day", retention="7 days")

app = FastAPI(title="HILDE API Gateway", version="1.0.0")

# Service URLs
COMPLETION_SERVICE_URL = os.getenv("COMPLETION_SERVICE_URL", "http://completion-llm:8000")
ANALYSIS_SERVICE_URL = os.getenv("ANALYSIS_SERVICE_URL", "http://analysis-llm:8000")

class HILDECompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.1
    top_k: int = 10
    stop_tokens: Optional[List[str]] = None
    enable_analysis: bool = True

class TokenAlternative(BaseModel):
    token: str
    probability: float
    log_prob: float
    analysis: Optional[Dict[str, Any]] = None

class ConstraintViolation(BaseModel):
    rule: str
    line: int
    column: int
    explanation: str
    severity: str
    code_snippet: str

class HILDECompletionResponse(BaseModel):
    completion: str
    tokens: List[TokenAlternative]
    top_k_tokens: List[List[TokenAlternative]]
    corrected_entropy_scores: List[float]
    highlighted_positions: List[int]
    constraint_violations: List[ConstraintViolation] = []

class HILDEGateway:
    def __init__(self):
        self.completion_client = httpx.AsyncClient(timeout=30.0)
        self.analysis_client = httpx.AsyncClient(timeout=30.0)
    
    async def generate_completion_with_analysis(self, request: HILDECompletionRequest) -> HILDECompletionResponse:
        """Generate completion with semantic analysis of alternatives"""
        try:
            # Step 1: Get base completion with token alternatives
            completion_response = await self._get_completion(request)
            
            # Step 2: Analyze token alternatives if enabled
            if request.enable_analysis:
                await self._analyze_alternatives(completion_response)
            
            # Step 3: Check constraints on the generated code
            constraint_violations = await self._check_constraints(
                completion_response["completion"], 
                "python"  # Default to python, could be made configurable
            )
            
            # Step 4: Calculate corrected entropy and identify highlights
            corrected_entropy = self._calculate_corrected_entropy(completion_response)
            highlighted_positions = self._identify_highlights(corrected_entropy)
            
            return HILDECompletionResponse(
                completion=completion_response["completion"],
                tokens=completion_response["tokens"],
                top_k_tokens=completion_response["top_k_tokens"],
                corrected_entropy_scores=corrected_entropy,
                highlighted_positions=highlighted_positions,
                constraint_violations=constraint_violations
            )
            
        except Exception as e:
            logger.error(f"Gateway error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _get_completion(self, request: HILDECompletionRequest) -> Dict[str, Any]:
        """Get completion from completion service"""
        try:
            response = await self.completion_client.post(
                f"{COMPLETION_SERVICE_URL}/completion",
                json=request.dict(exclude={"enable_analysis"})
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Completion service error: {e}")
            raise HTTPException(status_code=500, detail=f"Completion service error: {e}")
    
    async def _analyze_alternatives(self, completion_response: Dict[str, Any]):
        """Analyze token alternatives using analysis service"""
        try:
            # Analyze each position with alternatives
            for i, alternatives in enumerate(completion_response["top_k_tokens"]):
                for j, alt in enumerate(alternatives[1:], 1):  # Skip the first (top) token
                    analysis = await self._analyze_single_alternative(
                        completion_response["completion"],
                        alternatives[0]["token"],  # Original token
                        alt["token"],  # Alternative token
                        f"Position {i} in completion"
                    )
                    alt["analysis"] = analysis
            
            logger.info("Completed analysis of token alternatives")
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            # Continue without analysis rather than failing completely
    
    async def _analyze_single_alternative(self, completion: str, original: str, alternative: str, context: str) -> Dict[str, Any]:
        """Analyze a single token alternative"""
        try:
            response = await self.analysis_client.post(
                f"{ANALYSIS_SERVICE_URL}/analysis",
                json={
                    "base_completion": completion,
                    "original_token": original,
                    "alternative_token": alternative,
                    "context": context,
                    "language": "python"
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Single analysis failed: {e}")
            return {
                "detailed_explanation": "Analysis failed",
                "explanation_summary": "Analysis error",
                "category": "Minor",
                "importance_score": 0.1
            }
    
    def _calculate_corrected_entropy(self, completion_response: Dict[str, Any]) -> List[float]:
        """Calculate corrected entropy using importance scores"""
        corrected_entropy = []
        
        for i, alternatives in enumerate(completion_response["top_k_tokens"]):
            if len(alternatives) < 2:
                corrected_entropy.append(0.0)
                continue
            
            # Calculate entropy considering importance scores
            probs = []
            for alt in alternatives:
                importance = alt.get("analysis", {}).get("importance_score", 0.5)
                # Adjust probability based on importance
                adjusted_prob = alt["probability"] * importance
                probs.append(adjusted_prob)
            
            # Normalize probabilities
            total = sum(probs)
            if total > 0:
                probs = [p / total for p in probs]
            
            # Calculate entropy
            entropy = -sum(p * (p.bit_length() if p > 0 else 0) for p in probs)
            corrected_entropy.append(entropy)
        
        return corrected_entropy
    
    def _identify_highlights(self, corrected_entropy: List[float], threshold: float = 0.3) -> List[int]:
        """Identify positions that should be highlighted"""
        return [i for i, entropy in enumerate(corrected_entropy) if entropy > threshold]
    
    async def _check_constraints(self, code: str, language: str) -> List[ConstraintViolation]:
        """Check code for constraint violations"""
        try:
            response = await self.analysis_client.post(
                f"{ANALYSIS_SERVICE_URL}/constraints",
                json={
                    "code": code,
                    "language": language
                }
            )
            response.raise_for_status()
            constraint_data = response.json()
            
            # Convert to ConstraintViolation objects
            violations = []
            for violation in constraint_data.get("violations", []):
                violations.append(ConstraintViolation(
                    rule=violation["rule"],
                    line=violation["line"],
                    column=violation["column"],
                    explanation=violation["explanation"],
                    severity=violation["severity"],
                    code_snippet=violation["code_snippet"]
                ))
            
            return violations
            
        except Exception as e:
            logger.warning(f"Constraint checking failed: {e}")
            return []

# Initialize the gateway
gateway = HILDEGateway()

@app.post("/hilde/completion", response_model=HILDECompletionResponse)
async def hilde_completion(request: HILDECompletionRequest):
    """Main HILDE completion endpoint with semantic analysis"""
    return await gateway.generate_completion_with_analysis(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "completion_service": COMPLETION_SERVICE_URL,
        "analysis_service": ANALYSIS_SERVICE_URL
    }

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await gateway.completion_client.aclose()
    await gateway.analysis_client.aclose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
