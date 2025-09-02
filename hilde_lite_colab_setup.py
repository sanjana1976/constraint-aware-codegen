#!/usr/bin/env python3
"""
HiLDe-Lite Colab Setup Script
Complete setup and demo for Google Colab T4 GPU
"""

import subprocess
import sys
import os
import time

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    packages = [
        "transformers>=4.35.0",
        "accelerate>=0.20.0", 
        "torch>=2.0.0",
        "flask>=2.3.0",
        "flask-cors>=4.0.0",
        "openai>=1.3.0",
        "requests>=2.31.0",
        "numpy>=1.24.0"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("✅ Dependencies installed!")

def check_gpu():
    """Check GPU availability and memory"""
    try:
        import torch
        print(f"🔍 GPU Check:")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"  GPU: {torch.cuda.get_device_name(0)}")
            print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            return True
        else:
            print("  ⚠️ No GPU available - will use CPU (slower)")
            return False
    except ImportError:
        print("❌ PyTorch not installed")
        return False

def setup_environment():
    """Setup environment variables and paths"""
    print("🔧 Setting up environment...")
    
    # Set environment variables for better performance
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    os.environ['TRANSFORMERS_CACHE'] = '/content/cache'
    
    # Create cache directory
    os.makedirs('/content/cache', exist_ok=True)
    
    print("✅ Environment configured!")

def create_demo_notebook():
    """Create a demo notebook cell"""
    demo_code = '''
# HiLDe-Lite Demo
# Run this cell to test the system

import requests
import json

def test_hilde_lite(prompt="def hash_password(password):"):
    """Test HiLDe-Lite with a given prompt"""
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
            for pos in result['highlighted_positions'][:2]:
                if pos < len(result['token_alternatives']):
                    alts = result['token_alternatives'][pos]
                    print(f"\\n📍 Position {pos} (entropy: {result['entropy_scores'][pos]:.3f}):")
                    for j, alt in enumerate(alts[:3]):
                        marker = "🟢" if j == 0 else "🔵"
                        analysis = alt.get('analysis', {})
                        print(f"  {marker} '{alt['token']}' (prob: {alt['probability']:.3f})")
                        if analysis and analysis.get('explanation') != 'Analysis unavailable':
                            print(f"     💡 {analysis.get('explanation', 'N/A')}")
            
            return result
        else:
            print(f"❌ Request failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Test with different prompts
test_prompts = [
    "def hash_password(password):",
    "def connect_database():",
    "def process_payment(amount, card_number):",
    "def validate_email(email):",
    "def generate_api_key():"
]

print("🧪 Testing HiLDe-Lite with multiple prompts:")
print("=" * 50)

for prompt in test_prompts:
    test_hilde_lite(prompt)
    print("\\n" + "-" * 30 + "\\n")
'''
    
    with open('/content/hilde_lite_demo.py', 'w') as f:
        f.write(demo_code)
    
    print("✅ Demo script created at /content/hilde_lite_demo.py")

def main():
    """Main setup function"""
    print("🚀 HiLDe-Lite Colab Setup")
    print("=" * 40)
    
    # Step 1: Install dependencies
    install_dependencies()
    
    # Step 2: Check GPU
    gpu_available = check_gpu()
    
    # Step 3: Setup environment
    setup_environment()
    
    # Step 4: Create demo
    create_demo_notebook()
    
    print("\n" + "=" * 40)
    print("✅ Setup complete!")
    print("\n📝 Next steps:")
    print("1. Set your OpenAI API key: os.environ['OPENAI_API_KEY'] = 'your-key'")
    print("2. Run the main gateway: python hilde_lite_api_gateway.py")
    print("3. Test with: python /content/hilde_lite_demo.py")
    print("\n🔗 API Endpoints:")
    print("  - Health: http://localhost:5000/health")
    print("  - Demo: http://localhost:5000/demo")
    print("  - Main: POST http://localhost:5000/hilde/completion")
    
    if not gpu_available:
        print("\n⚠️ Warning: No GPU detected. Performance will be limited.")

if __name__ == "__main__":
    main()