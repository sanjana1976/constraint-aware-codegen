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
from hilde.analysis.constraint_debugger import ConstraintDebugger

class HiLDeLiteGateway:
    def __init__(self):
        """Initialize the HiLDe-Lite gateway"""
        self.completion_engine = None
        self.analysis_engine = None
        self.constraint_debugger = None
        self.initialized = False
        
        print("🚀 Initializing HiLDe-Lite Gateway...")
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize completion, analysis, and constraint debugging engines"""
        try:
            # Initialize completion engine
            print("📦 Loading completion engine...")
            self.completion_engine = HiLDeCompletionEngine()
            
            # Initialize analysis engine
            print("🧠 Initializing analysis engine...")
            self.analysis_engine = GPT4AnalysisEngine()
            
            # Initialize constraint debugger
            print("🔍 Initializing constraint debugger...")
            self.constraint_debugger = ConstraintDebugger()
            
            self.initialized = True
            print("✅ HiLDe-Lite Gateway initialized successfully!")
            
        except Exception as e:
            print(f"❌ Failed to initialize gateway: {e}")
            self.initialized = False
    
    def generate_completion(self, prompt: str, max_tokens: int = 100, enable_analysis: bool = True) -> Dict[str, Any]:
        """
        Generate completion with constraint analysis and human-readable summaries
        
        Args:
            prompt: Code prompt
            max_tokens: Maximum tokens to generate
            enable_analysis: Whether to use GPT-4 analysis and constraint checking
            
        Returns:
            Dictionary with completion, violations, and summary
        """
        if not self.initialized:
            return {"error": "Gateway not initialized"}
        
        try:
            # Step 1: Generate Code
            print("🔄 Step 1: Generating code completion...")
            completion = self.completion_engine.generate_completion(prompt, max_tokens)
            
            if not completion:
                return {"error": "Failed to generate completion"}
            
            # Step 2: Analyze with Constraint Debugger
            print("🔍 Step 2: Analyzing code with constraint debugger...")
            violations = []
            if enable_analysis and self.constraint_debugger:
                violations = self.constraint_debugger.analyze_code(completion)
                # Convert ConstraintViolation objects to dictionaries
                violations = [
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
            
            # Step 3: Summarize Violations with GPT-4
            print("📝 Step 3: Summarizing violations with GPT-4...")
            summary = ""
            if enable_analysis and self.analysis_engine and violations:
                summary = self.analysis_engine.summarize_violations(violations)
            elif not violations:
                summary = "✅ No constraint violations found. Code follows all defined rules."
            
            # Construct Response
            result = {
                "completion": completion,
                "constraint_violations": violations,
                "summary": summary,
                "metadata": {
                    "model": "Qwen2.5-Coder-7B",
                    "analysis_enabled": enable_analysis,
                    "timestamp": time.time(),
                    "violations_count": len(violations),
                    "components_used": [
                        "HiLDeCompletionEngine",
                        "ConstraintDebugger", 
                        "GPT4AnalysisEngine"
                    ]
                }
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
                "constraint_debugger": "ready" if self.constraint_debugger else "not_initialized",
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
    """Main HiLDe completion endpoint with Generate → Analyze → Summarize workflow"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        prompt = data.get('prompt', '')
        max_tokens = data.get('max_tokens', 100)
        enable_analysis = data.get('enable_analysis', True)
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Validate parameters
        max_tokens = min(max_tokens, 200)  # Cap at 200 tokens for T4
        
        print(f"🎯 Processing request: '{prompt[:50]}...'")
        
        # Generate completion with new workflow
        result = gateway.generate_completion(prompt, max_tokens, enable_analysis)
        
        if "error" in result:
            return jsonify(result), 500
        
        print(f"✅ Request completed: {result['metadata']['violations_count']} violations found")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(gateway.get_health_status())

@app.route('/demo', methods=['GET'])
def demo():
    """Demo endpoint with sample completion showing new workflow"""
    sample_prompt = "def hash_password(password):"
    
    try:
        result = gateway.generate_completion(sample_prompt, 50, True)
        
        return jsonify({
            'prompt': sample_prompt,
            'workflow': 'Generate → Analyze → Summarize',
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
    """Test endpoint for quick validation of new workflow"""
    data = request.get_json() or {}
    test_prompt = data.get('prompt', 'def test_function():')
    
    try:
        result = gateway.generate_completion(test_prompt, 30, True)
        
        return jsonify({
            'test_prompt': test_prompt,
            'success': 'error' not in result,
            'completion_length': len(result.get('completion', '')),
            'violations_count': len(result.get('constraint_violations', [])),
            'has_summary': bool(result.get('summary', '')),
            'workflow': 'Generate → Analyze → Summarize',
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
    """Test completion with new Generate → Analyze → Summarize workflow"""
    import requests
    
    try:
        response = requests.post('http://localhost:5000/hilde/completion', 
                               json={
                                   'prompt': prompt,
                                   'max_tokens': 80,
                                   'enable_analysis': True
                               })
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"🎯 Results for: '{prompt}'")
            print(f"📝 Completion: {result['completion']}")
            print(f"🔍 Constraint violations: {len(result['constraint_violations'])} found")
            print(f"📋 Summary: {result['summary']}")
            
            # Show violations if any
            if result['constraint_violations']:
                print(f"\n🚨 Violations Details:")
                for i, violation in enumerate(result['constraint_violations'], 1):
                    severity_emoji = "🔴" if violation['severity'] == "error" else "🟡" if violation['severity'] == "warning" else "🔵"
                    print(f"  {i}. {severity_emoji} {violation['rule']} (Line {violation['line']}): {violation['explanation']}")
            
            return result
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_multiple_prompts():
    """Test multiple prompts with new workflow"""
    test_prompts = [
        "def hash_password(password):",
        "global_config = {'api_key': 'secret'}",
        "def process_user_input():",
        "def very_long_function():",
        "def good_function():"
    ]
    
    print("🧪 Testing multiple prompts with Generate → Analyze → Summarize workflow:")
    print("=" * 70)
    
    for prompt in test_prompts:
        test_completion(prompt)
        print("\n" + "-" * 40 + "\n")

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