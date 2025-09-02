#!/usr/bin/env python3
"""
HILDE Demo Script
Demonstrates the key features of the HILDE system
"""

import requests
import json
import time

def demo_hilde_completion():
    """Demonstrate HILDE completion with alternatives"""
    print("🎯 HILDE Completion Demo")
    print("=" * 50)
    
    # Test prompt that should trigger security alternatives
    test_prompts = [
        "def hash_password(password):",
        "def generate_token():",
        "def validate_input(user_input):"
    ]
    
    for prompt in test_prompts:
        print(f"\n📝 Prompt: {prompt}")
        print("-" * 30)
        
        try:
            response = requests.post(
                "http://localhost:8000/hilde/completion",
                json={
                    "prompt": prompt,
                    "max_tokens": 50,
                    "temperature": 0.1,
                    "top_k": 5,
                    "enable_analysis": True
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Completion: {data.get('completion', 'N/A')}")
                print(f"🔍 Highlighted positions: {data.get('highlighted_positions', [])}")
                
                # Show alternatives for highlighted positions
                for pos in data.get('highlighted_positions', []):
                    if pos < len(data.get('top_k_tokens', [])):
                        alternatives = data['top_k_tokens'][pos]
                        print(f"   Position {pos} alternatives:")
                        for i, alt in enumerate(alternatives[:3]):  # Show top 3
                            marker = "🟢" if i == 0 else "🔵"
                            analysis = alt.get('analysis', {})
                            print(f"     {marker} {alt['token']} ({(alt['probability']*100):.1f}%)")
                            if analysis:
                                print(f"        Category: {analysis.get('category', 'N/A')}")
                                print(f"        Importance: {(analysis.get('importance_score', 0)*100):.0f}%")
                                print(f"        Summary: {analysis.get('explanation_summary', 'N/A')}")
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(1)  # Brief pause between requests

def demo_security_analysis():
    """Demonstrate security analysis capabilities"""
    print("\n🔒 Security Analysis Demo")
    print("=" * 50)
    
    # Sample vulnerable code
    vulnerable_code = """
import hashlib
import random

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def generate_token():
    return random.randint(1, 1000)

def validate_input(user_input):
    return eval(user_input)
"""
    
    print("📝 Sample vulnerable code:")
    print(vulnerable_code)
    
    try:
        # This would normally be called by the security integration service
        print("�� Security analysis would identify:")
        print("   ❌ Weak hashing algorithm (MD5)")
        print("   ❌ Predictable random number generation")
        print("   ❌ Code injection vulnerability (eval)")
        print("   ✅ Input validation function exists")
        
    except Exception as e:
        print(f"❌ Security analysis failed: {e}")

def demo_user_interaction():
    """Demonstrate user interaction tracking"""
    print("\n📊 User Interaction Demo")
    print("=" * 50)
    
    print("🎯 Simulating user interactions:")
    
    interactions = [
        {
            "action": "Token highlighted",
            "token": "sha256",
            "entropy": 0.8,
            "category": "Significant"
        },
        {
            "action": "Alternative selected",
            "token": "scrypt",
            "entropy": 0.8,
            "category": "Significant"
        },
        {
            "action": "Completion accepted",
            "token": "scrypt",
            "entropy": 0.8,
            "category": "Significant"
        }
    ]
    
    for i, interaction in enumerate(interactions, 1):
        print(f"   {i}. {interaction['action']}: {interaction['token']}")
        print(f"      Entropy: {interaction['entropy']:.1f}")
        print(f"      Category: {interaction['category']}")
    
    print("\n📈 Analytics would show:")
    print("   - 3 interactions recorded")
    print("   - 1 alternative selected (33% selection rate)")
    print("   - Average entropy: 0.8")
    print("   - Security improvement: MD5 → scrypt")

def main():
    """Run the HILDE demo"""
    print("🚀 HILDE System Demo")
    print("=" * 60)
    print("This demo showcases the key features of the HILDE system:")
    print("1. Intelligent code completion with alternatives")
    print("2. Security-aware decision highlighting")
    print("3. User interaction tracking and analytics")
    print("=" * 60)
    
    # Check if services are running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ HILDE services are running")
            print()
            
            demo_hilde_completion()
            demo_security_analysis()
            demo_user_interaction()
            
        else:
            print("❌ HILDE services are not responding")
            print("   Please start the services first: ./start_hilde.sh")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to HILDE services")
        print("   Please start the services first: ./start_hilde.sh")
        print("   Or check if they're running on the expected ports")
    
    print("\n" + "=" * 60)
    print("🎉 Demo complete!")
    print("📚 For more information, see README.md")
    print("🧪 Run tests with: python test_hilde.py")

if __name__ == "__main__":
    main()
