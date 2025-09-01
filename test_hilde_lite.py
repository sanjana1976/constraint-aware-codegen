#!/usr/bin/env python3
"""
HiLDe-Lite Test Script
Comprehensive testing for the HiLDe-Lite system
"""

import requests
import time
import json
from typing import Dict, Any

class HiLDeLiteTester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_results = {}
    
    def test_health(self) -> bool:
        """Test health endpoint"""
        print("🔍 Testing health endpoint...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed")
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   GPU Available: {data.get('gpu_available', False)}")
                print(f"   Memory Usage: {data.get('memory_usage', {}).get('gpu_memory_used', 'N/A')}")
                self.test_results['health'] = 'PASS'
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                self.test_results['health'] = 'FAIL'
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            self.test_results['health'] = 'ERROR'
            return False
    
    def test_demo(self) -> bool:
        """Test demo endpoint"""
        print("\n🎯 Testing demo endpoint...")
        try:
            response = requests.get(f"{self.base_url}/demo", timeout=30)
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                print(f"✅ Demo test passed")
                print(f"   Prompt: {data.get('prompt', 'N/A')}")
                print(f"   Completion: {result.get('completion', 'N/A')[:50]}...")
                print(f"   Alternatives: {len(result.get('token_alternatives', []))}")
                print(f"   Highlighted: {len(result.get('highlighted_positions', []))}")
                self.test_results['demo'] = 'PASS'
                return True
            else:
                print(f"❌ Demo test failed: {response.status_code}")
                self.test_results['demo'] = 'FAIL'
                return False
        except Exception as e:
            print(f"❌ Demo test error: {e}")
            self.test_results['demo'] = 'ERROR'
            return False
    
    def test_completion(self, prompt: str = "def hash_password(password):") -> bool:
        """Test main completion endpoint"""
        print(f"\n📝 Testing completion endpoint with: '{prompt}'")
        try:
            response = requests.post(
                f"{self.base_url}/hilde/completion",
                json={
                    'prompt': prompt,
                    'max_tokens': 50,
                    'top_k': 5,
                    'enable_analysis': True
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Completion test passed")
                print(f"   Completion: {data.get('completion', 'N/A')[:50]}...")
                print(f"   Token alternatives: {len(data.get('token_alternatives', []))}")
                print(f"   Entropy scores: {len(data.get('entropy_scores', []))}")
                print(f"   Highlighted positions: {data.get('highlighted_positions', [])}")
                
                # Check if analysis is working
                has_analysis = any(
                    alt.get('analysis') for alt_group in data.get('token_alternatives', [])
                    for alt in alt_group
                )
                print(f"   GPT-4 Analysis: {'✅ Working' if has_analysis else '❌ Not working'}")
                
                self.test_results['completion'] = 'PASS'
                return True
            else:
                print(f"❌ Completion test failed: {response.status_code}")
                print(f"   Response: {response.text}")
                self.test_results['completion'] = 'FAIL'
                return False
        except Exception as e:
            print(f"❌ Completion test error: {e}")
            self.test_results['completion'] = 'ERROR'
            return False
    
    def test_multiple_prompts(self) -> bool:
        """Test with multiple different prompts"""
        print(f"\n🧪 Testing multiple prompts...")
        
        test_prompts = [
            "def hash_password(password):",
            "def connect_database():",
            "def process_payment(amount, card_number):",
            "def validate_email(email):",
            "def generate_api_key():"
        ]
        
        passed = 0
        total = len(test_prompts)
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n   Test {i}/{total}: '{prompt}'")
            try:
                response = requests.post(
                    f"{self.base_url}/hilde/completion",
                    json={
                        'prompt': prompt,
                        'max_tokens': 40,
                        'top_k': 3,
                        'enable_analysis': True
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    completion = data.get('completion', '')
                    highlighted = len(data.get('highlighted_positions', []))
                    print(f"   ✅ Success: '{completion[:30]}...' ({highlighted} highlights)")
                    passed += 1
                else:
                    print(f"   ❌ Failed: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        success_rate = passed / total
        print(f"\n📊 Multiple prompts test: {passed}/{total} passed ({success_rate:.1%})")
        
        if success_rate >= 0.8:
            self.test_results['multiple_prompts'] = 'PASS'
            return True
        else:
            self.test_results['multiple_prompts'] = 'FAIL'
            return False
    
    def test_memory_management(self) -> bool:
        """Test memory management endpoints"""
        print(f"\n💾 Testing memory management...")
        
        try:
            # Test memory usage endpoint
            response = requests.get(f"{self.base_url}/memory", timeout=10)
            if response.status_code == 200:
                memory_data = response.json()
                print(f"✅ Memory usage retrieved")
                for key, value in memory_data.items():
                    print(f"   {key}: {value}")
            else:
                print(f"❌ Memory usage failed: {response.status_code}")
                return False
            
            # Test cache clearing
            response = requests.post(f"{self.base_url}/clear_cache", timeout=10)
            if response.status_code == 200:
                print(f"✅ Cache cleared successfully")
                self.test_results['memory_management'] = 'PASS'
                return True
            else:
                print(f"❌ Cache clear failed: {response.status_code}")
                self.test_results['memory_management'] = 'FAIL'
                return False
                
        except Exception as e:
            print(f"❌ Memory management error: {e}")
            self.test_results['memory_management'] = 'ERROR'
            return False
    
    def test_performance(self) -> bool:
        """Test performance with timing"""
        print(f"\n⏱️ Testing performance...")
        
        test_prompt = "def calculate_sum(a, b):"
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/hilde/completion",
                json={
                    'prompt': test_prompt,
                    'max_tokens': 30,
                    'top_k': 3,
                    'enable_analysis': True
                },
                timeout=60
            )
            end_time = time.time()
            
            if response.status_code == 200:
                duration = end_time - start_time
                print(f"✅ Performance test passed")
                print(f"   Response time: {duration:.2f} seconds")
                print(f"   Status: {'Fast' if duration < 10 else 'Slow' if duration < 30 else 'Very Slow'}")
                
                if duration < 30:
                    self.test_results['performance'] = 'PASS'
                    return True
                else:
                    self.test_results['performance'] = 'SLOW'
                    return False
            else:
                print(f"❌ Performance test failed: {response.status_code}")
                self.test_results['performance'] = 'FAIL'
                return False
                
        except Exception as e:
            print(f"❌ Performance test error: {e}")
            self.test_results['performance'] = 'ERROR'
            return False
    
    def run_all_tests(self) -> Dict[str, str]:
        """Run all tests and return results"""
        print("🚀 HiLDe-Lite Test Suite")
        print("=" * 50)
        
        tests = [
            self.test_health,
            self.test_demo,
            self.test_completion,
            self.test_multiple_prompts,
            self.test_memory_management,
            self.test_performance
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
                self.test_results[test.__name__] = 'CRASH'
        
        return self.test_results
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results.values() if result == 'PASS')
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result == 'PASS' else "⚠️" if result == 'SLOW' else "❌"
            print(f"{status_icon} {test_name}: {result}")
        
        print("\n" + "=" * 50)
        print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! HiLDe-Lite is working perfectly.")
        elif passed >= total * 0.8:
            print("✅ Most tests passed. HiLDe-Lite is working well.")
        else:
            print("⚠️ Some tests failed. Check the logs above for details.")
        
        # Save results
        with open('test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📄 Test results saved to test_results.json")

def main():
    """Main test runner"""
    tester = HiLDeLiteTester()
    tester.run_all_tests()
    tester.generate_report()

if __name__ == "__main__":
    main()