#!/usr/bin/env python3
"""
HILDE Logging and Analytics Service
Tracks user interactions and provides insights
"""

import json
import time
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class UserInteraction:
    timestamp: datetime
    action_type: str  # 'token_highlighted', 'alternative_selected', 'completion_accepted'
    token_position: int
    original_token: str
    alternative_token: Optional[str]
    decision_time_ms: Optional[int]
    entropy_score: float
    importance_score: Optional[float]
    category: Optional[str]
    language: str
    file_extension: str

@dataclass
class SecurityMetrics:
    timestamp: datetime
    vulnerabilities_found: int
    vulnerabilities_fixed: int
    security_scan_time_ms: int
    language: str

class HILDELoggingService:
    def __init__(self, db_path: str = "logs/hilde_analytics.db"):
        self.db_path = db_path
        self.ensure_db_directory()
        self.init_database()
    
    def ensure_db_directory(self):
        """Ensure the database directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create user interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action_type TEXT NOT NULL,
                token_position INTEGER,
                original_token TEXT,
                alternative_token TEXT,
                decision_time_ms INTEGER,
                entropy_score REAL,
                importance_score REAL,
                category TEXT,
                language TEXT,
                file_extension TEXT
            )
        ''')
        
        # Create security metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                vulnerabilities_found INTEGER,
                vulnerabilities_fixed INTEGER,
                security_scan_time_ms INTEGER,
                language TEXT
            )
        ''')
        
        # Create completion metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS completion_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                completion_length INTEGER,
                alternatives_provided INTEGER,
                user_selected_alternative BOOLEAN,
                language TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_user_interaction(self, interaction: UserInteraction):
        """Log a user interaction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_interactions 
            (timestamp, action_type, token_position, original_token, alternative_token,
             decision_time_ms, entropy_score, importance_score, category, language, file_extension)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            interaction.timestamp.isoformat(),
            interaction.action_type,
            interaction.token_position,
            interaction.original_token,
            interaction.alternative_token,
            interaction.decision_time_ms,
            interaction.entropy_score,
            interaction.importance_score,
            interaction.category,
            interaction.language,
            interaction.file_extension
        ))
        
        conn.commit()
        conn.close()
    
    def log_security_metrics(self, metrics: SecurityMetrics):
        """Log security-related metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_metrics 
            (timestamp, vulnerabilities_found, vulnerabilities_fixed, security_scan_time_ms, language)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            metrics.timestamp.isoformat(),
            metrics.vulnerabilities_found,
            metrics.vulnerabilities_fixed,
            metrics.security_scan_time_ms,
            metrics.language
        ))
        
        conn.commit()
        conn.close()
    
    def get_user_behavior_insights(self) -> Dict[str, Any]:
        """Get insights about user behavior"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get total interactions
        cursor.execute('SELECT COUNT(*) FROM user_interactions')
        total_interactions = cursor.fetchone()[0]
        
        # Get alternative selection rate
        cursor.execute('''
            SELECT 
                COUNT(*) as total_alternatives,
                SUM(CASE WHEN alternative_token IS NOT NULL THEN 1 ELSE 0 END) as selected_alternatives
            FROM user_interactions 
            WHERE action_type = 'alternative_selected'
        ''')
        alt_result = cursor.fetchone()
        alternative_selection_rate = 0.0
        if alt_result and alt_result[0] > 0:
            alternative_selection_rate = alt_result[1] / alt_result[0]
        
        # Get average decision time
        cursor.execute('''
            SELECT AVG(decision_time_ms) 
            FROM user_interactions 
            WHERE decision_time_ms IS NOT NULL
        ''')
        avg_decision_time = cursor.fetchone()[0] or 0
        
        # Get entropy distribution
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN entropy_score < 0.3 THEN 'low'
                    WHEN entropy_score < 0.7 THEN 'medium'
                    ELSE 'high'
                END as entropy_level,
                COUNT(*) as count
            FROM user_interactions 
            GROUP BY entropy_level
        ''')
        entropy_distribution = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_interactions': total_interactions,
            'alternative_selection_rate': alternative_selection_rate,
            'average_decision_time_ms': avg_decision_time,
            'entropy_distribution': entropy_distribution
        }
    
    def get_security_insights(self) -> Dict[str, Any]:
        """Get insights about security improvements"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get vulnerability trends
        cursor.execute('''
            SELECT 
                DATE(timestamp) as date,
                SUM(vulnerabilities_found) as found,
                SUM(vulnerabilities_fixed) as fixed
            FROM security_metrics 
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
        ''')
        vulnerability_trends = cursor.fetchall()
        
        # Get total security metrics
        cursor.execute('''
            SELECT 
                SUM(vulnerabilities_found) as total_found,
                SUM(vulnerabilities_fixed) as total_fixed,
                AVG(security_scan_time_ms) as avg_scan_time
            FROM security_metrics
        ''')
        total_metrics = cursor.fetchone()
        
        conn.close()
        
        return {
            'vulnerability_trends': vulnerability_trends,
            'total_vulnerabilities_found': total_metrics[0] or 0,
            'total_vulnerabilities_fixed': total_metrics[1] or 0,
            'average_scan_time_ms': total_metrics[2] or 0
        }
    
    def export_analytics_report(self, output_path: str = "logs/hilde_analytics_report.json"):
        """Export comprehensive analytics report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'user_behavior': self.get_user_behavior_insights(),
            'security_insights': self.get_security_insights(),
            'recommendations': self._generate_recommendations()
        }
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_path
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analytics"""
        recommendations = []
        
        # Get basic insights
        user_insights = self.get_user_behavior_insights()
        security_insights = self.get_security_insights()
        
        # User behavior recommendations
        if user_insights['alternative_selection_rate'] < 0.3:
            recommendations.append("Consider highlighting more critical decisions to increase user engagement")
        
        if user_insights['average_decision_time_ms'] > 60000:  # > 1 minute
            recommendations.append("Users are taking long to make decisions - consider simplifying the interface")
        
        # Security recommendations
        if security_insights['total_vulnerabilities_found'] > 0:
            recommendations.append("Continue monitoring security improvements and user adoption of secure alternatives")
        
        if not recommendations:
            recommendations.append("System is performing well - continue current practices")
        
        return recommendations

# Example usage
if __name__ == "__main__":
    logging_service = HILDELoggingService()
    
    # Log some sample interactions
    sample_interaction = UserInteraction(
        timestamp=datetime.now(),
        action_type='alternative_selected',
        token_position=25,
        original_token='sha256',
        alternative_token='scrypt',
        decision_time_ms=2500,
        entropy_score=0.8,
        importance_score=0.9,
        category='Significant',
        language='python',
        file_extension='.py'
    )
    
    logging_service.log_user_interaction(sample_interaction)
    
    # Generate and export report
    report_path = logging_service.export_analytics_report()
    print(f"Analytics report exported to: {report_path}")
    
    # Display insights
    insights = logging_service.get_user_behavior_insights()
    print(f"User behavior insights: {insights}")
