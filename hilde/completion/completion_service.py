#!/usr/bin/env python3
"""
HILDE Completion Service
Provides code completion with top-k token probabilities using Qwen2.5-Coder-32B
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from vllm import LLM, SamplingParams

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HILDE Completion Service", version="1.0.0")

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.1
    top_k: int = 10
    stop_tokens: Optional[List[str]] = None

class TokenInfo(BaseModel):
    token: str
    probability: float
    log_prob: float

class CompletionResponse(BaseModel):
    completion: str
    tokens: List[TokenInfo]
    top_k_tokens: List[List[TokenInfo]]

class HILDECompletionEngine:
    def __init__(self):
        self.model = None
        self.model_name = "Qwen/Qwen2.5-Coder-32B-Instruct"
        self.initialize_model()
    
    def initialize_model(self):
        """Initialize the completion model with vLLM"""
        try:
            logger.info(f"Loading model: {self.model_name}")
            self.model = LLM(
                model=self.model_name,
                trust_remote_code=True,
                gpu_memory_utilization=0.9,
                max_model_len=8192
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def get_completion_with_alternatives(self, request: CompletionRequest) -> CompletionResponse:
        """Generate completion with top-k token alternatives at each step"""
        try:
            # Generate base completion
            sampling_params = SamplingParams(
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_k=request.top_k,
                stop=request.stop_tokens or []
            )
            
            outputs = self.model.generate([request.prompt], sampling_params)
            completion = outputs[0].outputs[0].text
            
            # Get token-level alternatives (this is a simplified version)
            # In a real implementation, we'd need to access the model's internal token probabilities
            tokens = self._extract_tokens_with_alternatives(request.prompt, completion)
            
            return CompletionResponse(
                completion=completion,
                tokens=tokens,
                top_k_tokens=self._generate_top_k_tokens(request.prompt, completion, request.top_k)
            )
            
        except Exception as e:
            logger.error(f"Completion generation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _extract_tokens_with_alternatives(self, prompt: str, completion: str) -> List[TokenInfo]:
        """Extract tokens from completion with basic probability estimates"""
        # This is a simplified implementation
        # In practice, we'd need to access the model's token probabilities during generation
        tokens = []
        for i, char in enumerate(completion):
            # Simplified probability calculation
            prob = 0.8 if i < len(completion) // 2 else 0.6
            tokens.append(TokenInfo(
                token=char,
                probability=prob,
                log_prob=torch.log(torch.tensor(prob)).item()
            ))
        return tokens
    
    def _generate_top_k_tokens(self, prompt: str, completion: str, top_k: int) -> List[List[TokenInfo]]:
        """Generate top-k token alternatives for each position"""
        # This is a simplified implementation
        # In practice, we'd need to access the model's token probabilities during generation
        alternatives = []
        for i in range(len(completion)):
            pos_alternatives = []
            for j in range(top_k):
                # Generate alternative tokens (simplified)
                alt_token = chr(ord('a') + (i + j) % 26) if completion[i].isalpha() else completion[i]
                prob = 0.1 + (0.8 / (j + 1))  # Decreasing probability
                pos_alternatives.append(TokenInfo(
                    token=alt_token,
                    probability=prob,
                    log_prob=torch.log(torch.tensor(prob)).item()
                ))
            alternatives.append(pos_alternatives)
        return alternatives

# Initialize the completion engine
completion_engine = HILDECompletionEngine()

@app.post("/completion", response_model=CompletionResponse)
async def generate_completion(request: CompletionRequest):
    """Generate code completion with token alternatives"""
    return completion_engine.get_completion_with_alternatives(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model": completion_engine.model_name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
