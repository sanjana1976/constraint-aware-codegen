#!/usr/bin/env python3
"""
HiLDe-Lite Completion Engine
Simplified code generation engine for semester project
Uses Qwen2.5-Coder-7B for code completion
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
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
    
    def generate_completion(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Generate code completion based on prompt
        
        Args:
            prompt: Input code prompt
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            String containing the generated code completion
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
            
            # Generate completion
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    max_new_tokens=max_tokens,
                    do_sample=True,
                    top_k=50,
                    top_p=0.9,
                    temperature=0.1,  # Low temperature for more deterministic output
                    pad_token_id=self.tokenizer.eos_token_id,
                    use_cache=True  # Enable KV cache for efficiency
                )
            
            # Get generated tokens
            generated_ids = outputs[0][len(input_ids[0]):]
            completion = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
            
            return completion
            
        except Exception as e:
            print(f"❌ Generation error: {e}")
            return ""
    


# Example usage and testing
if __name__ == "__main__":
    # Initialize the completion engine
    engine = HiLDeCompletionEngine()
    
    # Test with a sample prompt
    test_prompt = "def hash_password(password):"
    
    print(f"\n🧪 Testing with prompt: '{test_prompt}'")
    completion = engine.generate_completion(test_prompt, max_tokens=50)
    
    print(f"\n📝 Generated completion: {completion}")