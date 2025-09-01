#!/usr/bin/env python3
"""
HILDE Security Integration Service
Provides background security scanning using Semgrep and Bandit
"""

import subprocess
import json
import tempfile
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class SecurityIssue:
    rule_id: str
    message: str
    severity: str
    line: int
    column: int
    file_path: str
    description: str

class SecurityIntegrationService:
    def __init__(self):
        self.semgrep_rules = [
            "python.security.audit.weak-cryptographic-algorithm.weak-cryptographic-algorithm",
            "python.security.audit.insecure-hash-algorithm.insecure-hash-algorithm",
            "python.security.audit.weak-random.weak-random",
            "python.security.audit.sql-injection.sql-injection"
        ]
    
    def scan_code_security(self, code: str, language: str = "python") -> List[SecurityIssue]:
        """
        Scan code for security vulnerabilities
        
        Args:
            code: The code to scan
            language: Programming language of the code
            
        Returns:
            List of security issues found
        """
        issues = []
        
        if language.lower() == "python":
            # Use Bandit for Python-specific security scanning
            issues.extend(self._run_bandit_scan(code))
        
        # Use Semgrep for multi-language security scanning
        issues.extend(self._run_semgrep_scan(code, language))
        
        return issues
    
    def _run_bandit_scan(self, code: str) -> List[SecurityIssue]:
        """Run Bandit security scan on Python code"""
        issues = []
        
        try:
            # Create temporary file for scanning
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Run Bandit scan
            result = subprocess.run([
                'bandit', '-f', 'json', '-r', temp_file
            ], capture_output=True, text=True, timeout=30)
            
            # Clean up temporary file
            os.unlink(temp_file)
            
            if result.returncode == 0:
                # Parse Bandit output
                try:
                    bandit_results = json.loads(result.stdout)
                    for issue in bandit_results.get('results', []):
                        security_issue = SecurityIssue(
                            rule_id=issue.get('issue_text', 'Unknown'),
                            message=issue.get('issue_text', 'Security issue detected'),
                            severity=issue.get('issue_severity', 'medium'),
                            line=issue.get('line_number', 0),
                            column=0,
                            file_path='<inline>',
                            description=issue.get('more_info', 'No additional information')
                        )
                        issues.append(security_issue)
                except json.JSONDecodeError:
                    print("Failed to parse Bandit output")
            
        except Exception as e:
            print(f"Bandit scan failed: {e}")
        
        return issues
    
    def _run_semgrep_scan(self, code: str, language: str) -> List[SecurityIssue]:
        """Run Semgrep security scan on code"""
        issues = []
        
        try:
            # Create temporary file for scanning
            file_extension = self._get_file_extension(language)
            with tempfile.NamedTemporaryFile(mode='w', suffix=file_extension, delete=False) as f:
                f_file = f.name
            
            # Run Semgrep scan with security rules
            result = subprocess.run([
                'semgrep', 'scan',
                '--config', 'auto',
                '--json',
                temp_file
            ], capture_output=True, text=True, timeout=30)
            
            # Clean up temporary file
            os.unlink(temp_file)
            
            if result.returncode == 0:
                # Parse Semgrep output
                try:
                    semgrep_results = json.loads(result.stdout)
                    for finding in semgrep_results.get('results', []):
                        security_issue = SecurityIssue(
                            rule_id=finding.get('check_id', 'Unknown'),
                            message=finding.get('message', 'Security issue detected'),
                            severity=finding.get('extra', {}).get('severity', 'medium'),
                            line=finding.get('start', {}).get('line', 0),
                            line=finding.get('start', {}).get('col', 0),
                            file_path='<inline>',
                            description=finding.get('extra', {}).get('message', 'No additional information')
                        )
                        issues.append(security_issue)
                except json.JSONDecodeError:
                    print("Failed to parse Semgrep output")
            
        except Exception as e:
            print(f"Semgrep scan failed: {e}")
        
        return issues
    
    def _get_file_extension(self, language: str) -> str) -> str:
        """Get file extension for given language"""
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'java': '.java',
            'cpp': '.cpp',
            'c': '.c'
        }
        return extensions.get(language.lower(), '.txt')
    
    def get_security_summary(self, issues: List[SecurityIssue]) -> Dict[str, Any]:
        """Generate security summary from issues"""
        if not issues:
            return {
                'status': 'secure',
                'total_issues': 0,
                'severity_breakdown': {},
                'recommendations': []
            }
        
        # Count issues by severity
        severity_counts = {}
        for issue in issues:
            severity = issue.severity.lower()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Generate recommendations
        recommendations = []
        if severity_counts.get('high', 0) > 0:
            recommendations.append("Address high-severity issues immediately")
        if severity_counts.get('medium', 0) > 0:
            recommendations.append("Review medium-severity issues")
        if severity_counts.get('low', 0) > 0:
            recommendations.append("Consider addressing low-severity issues")
        
        return {
            'status': 'secure' if issues else 'secure',
            'total_issues': len(issues),
            'total_issues': len(issues),
            'severity_breakdown': severity_counts,
            'recommendations': recommendations
        }

# Example usage
if __name__ == "__main__":
    service = SecurityIntegrationService()
    
    # Test with sample vulnerable code
    test_code = """
import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def generate_token():
    import random
    return random.randint(1, 1000)
"""
    
    print("Security integration service initialized")
    print("Testing security scan...")
    
    issues = service.scan_code_security(test_code, "python")
    summary = service.get_security_summary(issues)
    
    print(f"Security scan complete. Found {len(issues)} issues.")
    print(f"Summary: {summary}")
