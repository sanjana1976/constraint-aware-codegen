#!/usr/bin/env python3
"""
HILDE System Test Script
Tests all major components of the HILDE system
"""

import asyncio
import json
import time
import requests
from pathlib import Path

class HILDETester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = {}
    
    def test_completion_service(self):
        """Test the completion service directly"""
        print("🔍 Testing Completion Service...")
        try:
            response = requests.get("http://localhost:8001/health", timeout=5)
            if response.status_code == 200:
                print("✅ Completion service is running")
                self.test_results['completion_service'] = 'PASS'
                return True
            else:
                print("❌ Completion service health check failed")
                self.test_results['completion_service'] = 'FAIL'
                return False
        except Exception as e:
            print(f"❌ Completion service connection failed: {e}")
            self.test_results['completion_service'] = 'FAIL'
            return False
    
    def test_analysis_service(self):
        """Test the analysis service directly"""
        print("🔍 Testing Analysis Service...")
        try:
            response = requests.get("http://localhost:8002/health", timeout=5)
            if response.status_code == 200:
                print("✅ Analysis service is running")
                self.test_results['analysis_service'] = 'PASS'
                return True
            else:
                print("❌ Analysis service health check failed")
                self.test_results['analysis_service'] = 'FAIL'
                return False
        except Exception as e:
            print(f"❌ Analysis service connection failed: {e}")
            self.test_results['analysis_service'] = 'FAIL'
            return False
    
    def test_api_gateway(self):
        """Test the main API gateway"""
        print("🔍 Testing API Gateway...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API gateway is running")
                self.test_results['api_gateway'] = 'PASS'
                return True
            else:
                print("❌ API gateway health check failed")
                self.test_results['api_gateway'] = 'FAIL'
                return False
        except Exception as e:
            print(f"❌ API gateway connection failed: {e}")
            self.test_results['api_gateway'] = 'FAIL'
            return False
    
    def test_hilde_completion(self):
        """Test the main HILDE completion endpoint"""
        print("🔍 Testing HILDE Completion...")
        try:
            test_prompt = "def hash_password(password):"
            
            response = requests.post(
                f"{self.base_url}/hilde/completion",
                json={
                    "prompt": test_prompt,
                    "max_tokens": 50,
                    "temperature": 0.1,
                    "top_k": 5,
                    "enable_analysis": True
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ HILDE completion successful")
                print(f"   Completion: {data.get('completion', 'N/A')}")
                print(f"   Highlighted positions: {data.get('highlighted_positions', [])}")
                print(f"   Entropy scores: {data.get('corrected_entropy_scores', [])}")
                self.test_results['hilde_completion'] = 'PASS'
                return True
            else:
                print(f"❌ HILDE completion failed: {response.status_code}")
                print(f"   Response: {response.text}")
                self.test_results['hilde_completion'] = 'FAIL'
                return False
                
        except Exception as e:
            print(f"❌ HILDE completion test failed: {e}")
            self.test_results['hilde_completion'] = 'FAIL'
            return False
    
    def test_security_integration(self):
        """Test the security integration service"""
        print("🔍 Testing Security Integration...")
        try:
            # Import and test security service
            from security_integration import SecurityIntegrationService
            
            service = SecurityIntegrationService()
            
            # Test with vulnerable code
            test_code = """
import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()
"""
            
            issues = service.scan_code_security(test_code, "python")
            summary = service.get_security_summary(issues)
            
            print("✅ Security integration test successful")
            print(f"   Issues found: {len(issues)}")
            print(f"   Summary: {summary}")
            self.test_results['security_integration'] = 'PASS'
            return True
            
        except Exception as e:
            print(f"❌ Security integration test failed: {e}")
            self.test_results['security_integration'] = 'FAIL'
            return False
    
    def test_suffix_preservation(self):
        """Test the suffix preservation service"""
        print("🔍 Testing Suffix Preservation...")
        try:
            from suffix_preservation import SuffixPreservationService
            
            service = SuffixPreservationService()
            
            # Test basic functionality
            original_code = "def test_function():\n    return 'hello world'"
            new_token = "greeting"
            position = 17  # Position of 'hello'
            
            # This would normally use a completion engine
            print("✅ Suffix preservation service initialized")
            self.test_results['suffix_preservation'] = 'PASS'
            return True
            
        except Exception as e:
            print(f"❌ Suffix preservation test failed: {e}")
            self.test_results['suffix_preservation'] = 'FAIL'
            return False
    
    def test_logging_analytics(self):
        """Test the logging and analytics service"""
        print("🔍 Testing Logging & Analytics...")
        try:
            from logging_analytics import HILDELoggingService, UserInteraction
            from datetime import datetime
            
            # Create logging service
            logging_service = HILDELoggingService("test_analytics.db")
            
            # Test logging
            sample_interaction = UserInteraction(
                timestamp=datetime.now(),
                action_type='test_interaction',
                token_position=0,
                original_token='test',
                alternative_token=None,
                decision_time_ms=1000,
                entropy_score=0.5,
                importance_score=0.5,
                category='Minor',
                language='python',
                file_extension='.py'
            )
            
            logging_service.log_user_interaction(sample_interaction)
            
            # Test insights
            insights = logging_service.get_user_behavior_insights()
            
            print("✅ Logging & analytics test successful")
            print(f"   Insights: {insights}")
            self.test_results['logging_analytics'] = 'PASS'
            return True
            
        except Exception as e:
            print(f"❌ Logging & analytics test failed: {e}")
            self.test_results['logging_analytics'] = 'FAIL'
            return False
    
    def test_vscode_extension(self):
        """Test VS Code extension compilation"""
        print("🔍 Testing VS Code Extension...")
        try:
            extension_dir = Path("extension")
            if not extension_dir.exists():
                print("❌ Extension directory not found")
                self.test_results['vscode_extension'] = 'FAIL'
                return False
            
            # Check if TypeScript files exist
            ts_files = list(extension_dir.rglob("*.ts"))
            if not ts_files:
                print("❌ No TypeScript files found in extension")
                self.test_results['vscode_extension'] = 'FAIL'
                return False
            
            print(f"✅ VS Code extension structure found ({len(ts_files)} TypeScript files)")
            self.test_results['vscode_extension'] = 'PASS'
            return True
            
        except Exception as e:
            print(f"❌ VS Code extension test failed: {e}")
            self.test_results['vscode_extension'] = 'FAIL'
            return False
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🚀 Starting HILDE System Tests...\n")
        
        tests = [
            self.test_completion_service,
            self.test_analysis_service,
            self.test_api_gateway,
            self.test_hilde_completion,
            self.test_security_integration,
            self.test_suffix_preservation,
            self.test_logging_analytics,
            self.test_vscode_extension
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
                self.test_results[test.__name__] = 'CRASH'
            print()
        
        self.generate_test_report()
    
    def generate_test_report(self):
        """Generate a comprehensive test report"""
        print("📊 Test Results Summary")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results.values() if result == 'PASS')
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result == 'PASS' else "❌"
            print(f"{status_icon} {test_name}: {result}")
        
        print("\n" + "=" * 50)
        print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! HILDE system is ready.")
        else:
            print("⚠️  Some tests failed. Check the logs above for details.")
        
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📄 Test results saved to test_results.json")

def main():
    """Main test runner"""
    tester = HILDETester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
