#!/usr/bin/env python3
"""
HiLDe-Lite Completion Engine
Optimized for Google Colab T4 GPU (16GB VRAM)
Uses Qwen2.5-Coder-7B for code generation with token alternatives
"""

import torch
import numpy as np
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List, Dict, Any, Tuple
import gc

class HiLDeCompletionEngine:
    def __init__(self, model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct"):
        """
        Initialize the completion engine with optimizations for T4 GPU
        
        Args:
            model_name: HuggingFace model name for the code completion model
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"Initializing HiLDe-Lite Completion Engine...")
        print(f"Device: {self.device}")
        print(f"Model: {model_name}")
        
        self._load_model()
    
    def _load_model(self):
        """Load the model with T4 GPU optimizations"""
        try:
            # Clear GPU memory
            torch.cuda.empty_cache()
            gc.collect()
            
            print("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            print("Loading model with T4 optimizations...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,  # Use half precision for memory efficiency
                device_map="auto",          # Automatically distribute across available devices
                trust_remote_code=True,
                low_cpu_mem_usage=True,    # Reduce CPU memory usage during loading
                max_memory={0: "14GB"}      # Limit GPU memory usage to 14GB (leave 2GB buffer)
            )
            
            self.model.eval()
            
            print("✅ Model loaded successfully!")
            print(f"Model device: {next(self.model.parameters()).device}")
            print(f"Model dtype: {next(self.model.parameters()).dtype}")
            
            # Memory usage
            if torch.cuda.is_available():
                print(f"GPU memory used: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
                print(f"GPU memory cached: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")
                
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise
    
    def generate_with_alternatives(self, prompt: str, max_tokens: int = 100, top_k: int = 5) -> Dict[str, Any]:
        """
        Generate completion with token-level alternatives
        
        Args:
            prompt: Input code prompt
            max_tokens: Maximum number of tokens to generate
            top_k: Number of top alternatives to consider for each token
            
        Returns:
            Dictionary containing completion, alternatives, and entropy scores
        """
        try:
            # Tokenize input with truncation to fit in context
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=512  # Conservative limit for T4
            )
            input_ids = inputs["input_ids"].to(self.model.device)
            
            # Generate with top-k sampling to get alternatives
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    max_new_tokens=max_tokens,
                    do_sample=True,
                    top_k=top_k,
                    top_p=0.9,
                    temperature=0.1,  # Low temperature for more deterministic output
                    pad_token_id=self.tokenizer.eos_token_id,
                    return_dict_in_generate=True,
                    output_scores=True,
                    use_cache=True  # Enable KV cache for efficiency
                )
            
            # Get generated tokens
            generated_ids = outputs.sequences[0][len(input_ids[0]):]
            completion = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
            
            # Extract token alternatives and probabilities
            token_alternatives = self._extract_token_alternatives(
                input_ids, generated_ids, outputs.scores, top_k
            )
            
            # Calculate entropy for highlighting
            entropy_scores = self._calculate_entropy_scores(token_alternatives)
            
            # Identify highlighted positions (high entropy = uncertain decisions)
            highlighted_positions = self._identify_highlights(entropy_scores)
            
            return {
                "completion": completion,
                "token_alternatives": token_alternatives,
                "entropy_scores": entropy_scores,
                "highlighted_positions": highlighted_positions,
                "prompt": prompt
            }
            
        except Exception as e:
            print(f"❌ Generation error: {e}")
            return {
                "completion": "",
                "token_alternatives": [],
                "entropy_scores": [],
                "highlighted_positions": [],
                "prompt": prompt,
                "error": str(e)
            }
    
    def _extract_token_alternatives(self, input_ids, generated_ids, scores, top_k: int) -> List[List[Dict]]:
        """Extract top-k alternatives for each generated token"""
        alternatives = []
        
        for i, score_tensor in enumerate(scores):
            # Get probabilities
            probs = F.softmax(score_tensor[0], dim=-1)
            
            # Get top-k tokens and probabilities
            top_probs, top_indices = torch.topk(probs, top_k)
            
            token_alts = []
            for j in range(top_k):
                token_id = top_indices[j].item()
                prob = top_probs[j].item()
                token_text = self.tokenizer.decode([token_id])
                
                token_alts.append({
                    "token": token_text,
                    "token_id": token_id,
                    "probability": prob,
                    "log_prob": np.log(prob) if prob > 0 else -float('inf')
                })
            
            alternatives.append(token_alts)
        
        return alternatives
    
    def _calculate_entropy_scores(self, token_alternatives: List[List[Dict]]) -> List[float]:
        """Calculate entropy for each token position"""
        entropy_scores = []
        
        for alts in token_alternatives:
            probs = [alt["probability"] for alt in alts]
            # Calculate entropy: H = -Σ(p * log(p))
            entropy = -sum(p * np.log(p) for p in probs if p > 0)
            entropy_scores.append(entropy)
        
        return entropy_scores
    
    def _identify_highlights(self, entropy_scores: List[float], threshold: float = 0.5) -> List[int]:
        """
        Identify positions with high entropy (uncertain decisions)
        
        Args:
            entropy_scores: List of entropy values for each token position
            threshold: Entropy threshold above which to highlight
            
        Returns:
            List of position indices to highlight
        """
        return [i for i, entropy in enumerate(entropy_scores) if entropy > threshold]
    
    def get_memory_usage(self) -> Dict[str, str]:
        """Get current memory usage information"""
        if torch.cuda.is_available():
            return {
                "gpu_memory_used": f"{torch.cuda.memory_allocated() / 1024**3:.2f} GB",
                "gpu_memory_cached": f"{torch.cuda.memory_reserved() / 1024**3:.2f} GB",
                "gpu_memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB"
            }
        else:
            return {"gpu_memory": "N/A (CPU only)"}
    
    def clear_cache(self):
        """Clear GPU cache to free memory"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
            print("✅ GPU cache cleared")

# Example usage and testing
if __name__ == "__main__":
    # Initialize the completion engine
    engine = HiLDeCompletionEngine()
    
    # Test with a sample prompt
    test_prompt = "def hash_password(password):"
    
    print(f"\n🧪 Testing with prompt: '{test_prompt}'")
    result = engine.generate_with_alternatives(test_prompt, max_tokens=50, top_k=5)
    
    print(f"\n📝 Completion: {result['completion']}")
    print(f"🔍 Highlighted positions: {result['highlighted_positions']}")
    print(f"📊 Entropy scores: {[f'{e:.3f}' for e in result['entropy_scores'][:5]]}")
    
    # Show token alternatives for first few positions
    print(f"\n🔍 Token Alternatives (first 3 positions):")
    for i, alts in enumerate(result['token_alternatives'][:3]):
        print(f"\nPosition {i}:")
        for j, alt in enumerate(alts[:3]):  # Show top 3 alternatives
            marker = "🟢" if j == 0 else "🔵"
            print(f"  {marker} '{alt['token']}' (prob: {alt['probability']:.3f})")
    
    # Memory usage
    print(f"\n💾 Memory Usage:")
    for key, value in engine.get_memory_usage().items():
        print(f"  {key}: {value}")