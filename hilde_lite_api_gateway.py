#!/usr/bin/env python3
"""
HiLDe-Lite API Gateway - Streamlined Version
Flask server that orchestrates the Generate → Analyze → Summarize workflow
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import time
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
    status = {
        "status": "healthy" if gateway.initialized else "unhealthy",
        "initialized": gateway.initialized,
        "timestamp": time.time()
    }
    
    if gateway.initialized:
        status.update({
            "completion_engine": "ready",
            "analysis_engine": "ready" if gateway.analysis_engine.api_key else "no_api_key",
            "constraint_debugger": "ready" if gateway.constraint_debugger else "not_initialized"
        })
    
    return jsonify(status)

def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask server"""
    print(f"🌐 Starting HiLDe-Lite server on {host}:{port}")
    print(f"📡 Health check: http://{host}:{port}/health")
    print(f"🔧 Main endpoint: POST http://{host}:{port}/hilde/completion")
    
    app.run(host=host, port=port, debug=debug, use_reloader=False)

if __name__ == "__main__":
    run_server()