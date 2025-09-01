#!/usr/bin/env python3
"""
HiLDe-Lite API Gateway
Flask server that orchestrates completion and analysis engines
Optimized for Google Colab deployment
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import os
import torch
from typing import Dict, Any

# Import our engines
from hilde_lite_completion_engine import HiLDeCompletionEngine
from hilde_lite_analysis_engine import GPT4AnalysisEngine

class HiLDeLiteGateway:
    def __init__(self):
        """Initialize the HiLDe-Lite gateway"""
        self.completion_engine = None
        self.analysis_engine = None
        self.initialized = False
        
        print("🚀 Initializing HiLDe-Lite Gateway...")
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize both completion and analysis engines"""
        try:
            # Initialize completion engine
            print("📦 Loading completion engine...")
            self.completion_engine = HiLDeCompletionEngine()
            
            # Initialize analysis engine
            print("🧠 Initializing analysis engine...")
            self.analysis_engine = GPT4AnalysisEngine()
            
            self.initialized = True
            print("✅ HiLDe-Lite Gateway initialized successfully!")
            
        except Exception as e:
            print(f"❌ Failed to initialize gateway: {e}")
            self.initialized = False
    
    def generate_completion(self, prompt: str, max_tokens: int = 100, top_k: int = 5, enable_analysis: bool = True) -> Dict[str, Any]:
        """
        Generate completion with alternatives and analysis
        
        Args:
            prompt: Code prompt
            max_tokens: Maximum tokens to generate
            top_k: Number of alternatives per token
            enable_analysis: Whether to use GPT-4 analysis
            
        Returns:
            Dictionary with completion, alternatives, and analysis
        """
        if not self.initialized:
            return {"error": "Gateway not initialized"}
        
        try:
            # Generate completion with alternatives
            result = self.completion_engine.generate_with_alternatives(
                prompt, max_tokens, top_k
            )
            
            if "error" in result:
                return result
            
            # Add analysis if enabled
            if enable_analysis and self.analysis_engine:
                result['token_alternatives'] = self.analysis_engine.analyze_alternatives(
                    prompt, result['completion'], result['token_alternatives']
                )
            
            # Add metadata
            result['metadata'] = {
                'model': 'Qwen2.5-Coder-7B',
                'analysis_enabled': enable_analysis,
                'timestamp': time.time(),
                'memory_usage': self.completion_engine.get_memory_usage()
            }
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the gateway"""
        status = {
            "status": "healthy" if self.initialized else "unhealthy",
            "initialized": self.initialized,
            "timestamp": time.time()
        }
        
        if self.initialized:
            status.update({
                "completion_engine": "ready",
                "analysis_engine": "ready" if self.analysis_engine.api_key else "no_api_key",
                "gpu_available": torch.cuda.is_available(),
                "memory_usage": self.completion_engine.get_memory_usage()
            })
        
        return status

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for Colab

# Initialize gateway
gateway = HiLDeLiteGateway()

@app.route('/hilde/completion', methods=['POST'])
def hilde_completion():
    """Main HiLDe completion endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        prompt = data.get('prompt', '')
        max_tokens = data.get('max_tokens', 100)
        top_k = data.get('top_k', 5)
        enable_analysis = data.get('enable_analysis', True)
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Validate parameters
        max_tokens = min(max_tokens, 200)  # Cap at 200 tokens for T4
        top_k = min(top_k, 10)  # Cap at 10 alternatives
        
        # Generate completion
        result = gateway.generate_completion(prompt, max_tokens, top_k, enable_analysis)
        
        if "error" in result:
            return jsonify(result), 500
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(gateway.get_health_status())

@app.route('/demo', methods=['GET'])
def demo():
    """Demo endpoint with sample completion"""
    sample_prompt = "def hash_password(password):"
    
    try:
        result = gateway.generate_completion(sample_prompt, 50, 5, True)
        
        return jsonify({
            'prompt': sample_prompt,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/memory', methods=['GET'])
def memory_usage():
    """Get memory usage information"""
    if gateway.initialized:
        return jsonify(gateway.completion_engine.get_memory_usage())
    else:
        return jsonify({'error': 'Gateway not initialized'}), 500

@app.route('/clear_cache', methods=['POST'])
def clear_cache():
    """Clear GPU cache to free memory"""
    if gateway.initialized:
        gateway.completion_engine.clear_cache()
        return jsonify({'status': 'Cache cleared'})
    else:
        return jsonify({'error': 'Gateway not initialized'}), 500

@app.route('/test', methods=['POST'])
def test_endpoint():
    """Test endpoint for quick validation"""
    data = request.get_json() or {}
    test_prompt = data.get('prompt', 'def test_function():')
    
    try:
        result = gateway.generate_completion(test_prompt, 30, 3, True)
        
        return jsonify({
            'test_prompt': test_prompt,
            'success': 'error' not in result,
            'completion_length': len(result.get('completion', '')),
            'alternatives_count': len(result.get('token_alternatives', [])),
            'highlighted_positions': len(result.get('highlighted_positions', [])),
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask server"""
    print(f"🌐 Starting HiLDe-Lite server on {host}:{port}")
    print(f"📡 Health check: http://{host}:{port}/health")
    print(f"🎯 Demo: http://{host}:{port}/demo")
    print(f"🔧 Main endpoint: POST http://{host}:{port}/hilde/completion")
    
    app.run(host=host, port=port, debug=debug, use_reloader=False)

# Colab-specific setup
def setup_for_colab():
    """Setup function specifically for Google Colab"""
    print("🔧 Setting up HiLDe-Lite for Google Colab...")
    
    # Check if we're in Colab
    try:
        import google.colab
        print("✅ Running in Google Colab")
        
        # Set up ngrok for external access (optional)
        try:
            from pyngrok import ngrok
            print("📡 Setting up ngrok tunnel...")
            public_url = ngrok.connect(5000)
            print(f"🌍 Public URL: {public_url}")
        except ImportError:
            print("💡 Install pyngrok for public access: !pip install pyngrok")
        
    except ImportError:
        print("💻 Running locally (not in Colab)")
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, args=('0.0.0.0', 5000, False))
    server_thread.daemon = True
    server_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    print("🚀 HiLDe-Lite is ready!")
    print("📝 Use the test functions below to interact with the API")

# Example usage and testing functions
def test_completion(prompt: str = "def hash_password(password):"):
    """Test completion with a given prompt"""
    import requests
    
    try:
        response = requests.post('http://localhost:5000/hilde/completion', 
                               json={
                                   'prompt': prompt,
                                   'max_tokens': 80,
                                   'top_k': 5,
                                   'enable_analysis': True
                               })
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"🎯 Results for: '{prompt}'")
            print(f"📝 Completion: {result['completion']}")
            print(f"🔍 Highlighted decisions: {len(result['highlighted_positions'])} positions")
            
            # Show key alternatives
            for pos in result['highlighted_positions'][:2]:  # Show first 2 highlighted positions
                if pos < len(result['token_alternatives']):
                    alts = result['token_alternatives'][pos]
                    print(f"\n📍 Position {pos} (entropy: {result['entropy_scores'][pos]:.3f}):")
                    for j, alt in enumerate(alts[:3]):
                        marker = "🟢" if j == 0 else "🔵"
                        analysis = alt.get('analysis', {})
                        print(f"  {marker} '{alt['token']}' (prob: {alt['probability']:.3f})")
                        if analysis and analysis.get('explanation') != 'Analysis unavailable':
                            print(f"     💡 {analysis.get('explanation', 'N/A')}")
            
            return result
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_multiple_prompts():
    """Test multiple prompts"""
    test_prompts = [
        "def hash_password(password):",
        "def connect_database():",
        "def process_payment(amount, card_number):",
        "def validate_email(email):",
        "def generate_api_key():"
    ]
    
    print("🧪 Testing multiple prompts:")
    print("=" * 50)
    
    for prompt in test_prompts:
        test_completion(prompt)
        print("\n" + "-" * 30 + "\n")

if __name__ == "__main__":
    # Setup for Colab
    setup_for_colab()
    
    # Run some tests
    print("\n🧪 Running tests...")
    test_completion()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down HiLDe-Lite...")