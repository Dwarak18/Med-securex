#!/usr/bin/env python3
"""
Test script for the RAG service integration
"""
import asyncio
import httpx
import json
import sys
import time

# Test payloads
TEST_PAYLOADS = [
    {
        "name": "XSS Attack",
        "payload": "<script>alert('XSS')</script>",
        "expected": "malicious"
    },
    {
        "name": "SQL Injection",
        "payload": "' OR '1'='1",
        "expected": "malicious"
    },
    {
        "name": "Command Injection",
        "payload": "nc -l -p 4444 -e /bin/bash",
        "expected": "malicious"
    },
    {
        "name": "Path Traversal",
        "payload": "../../../etc/passwd",
        "expected": "malicious"
    },
    {
        "name": "Benign Request",
        "payload": "SELECT name FROM users WHERE id = 1",
        "expected": "benign"
    }
]

async def test_rag_service(base_url="http://localhost:8000"):
    """Test the RAG service endpoints"""
    print(f"🧪 Testing RAG Service at {base_url}")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        # Test health check
        try:
            print("📡 Testing health endpoint...")
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check passed")
                print(f"   - Service: {health_data.get('service')}")
                print(f"   - Version: {health_data.get('version')}")
                print(f"   - PostgreSQL: {'Available' if health_data.get('postgres_available') else 'Unavailable'}")
                print(f"   - MongoDB: {'Available' if health_data.get('mongodb_available') else 'Unavailable'}")
                print(f"   - RAG Pipeline: {'Available' if health_data.get('rag_pipeline_available') else 'Unavailable'}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
        
        print()
        
        # Test payload analysis
        print("🔍 Testing payload analysis...")
        for test_case in TEST_PAYLOADS:
            try:
                payload_data = {
                    "payload": test_case["payload"],
                    "source_ip": "127.0.0.1",
                    "user_agent": "Test Client"
                }
                
                print(f"Testing: {test_case['name']}")
                start_time = time.time()
                
                response = await client.post(f"{base_url}/check_payload", json=payload_data)
                response_time = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    result = response.json()
                    verdict = result.get("verdict", "unknown")
                    confidence = result.get("confidence_score", 0.0)
                    method = result.get("analysis_method", "unknown")
                    
                    status = "✅" if verdict == test_case["expected"] else "⚠️"
                    print(f"  {status} Verdict: {verdict} (confidence: {confidence:.2f})")
                    print(f"     Method: {method}, Time: {response_time}ms")
                    
                    if result.get("threat_details"):
                        threat = result["threat_details"]
                        if threat.get("attack_type"):
                            print(f"     Attack Type: {threat['attack_type']}")
                        if threat.get("severity"):
                            print(f"     Severity: {threat['severity']}")
                else:
                    print(f"  ❌ Request failed: {response.status_code}")
                    print(f"     Response: {response.text}")
                
            except Exception as e:
                print(f"  ❌ Error testing {test_case['name']}: {e}")
            
            print()
        
        # Test statistics endpoints if available
        print("📊 Testing statistics endpoints...")
        try:
            response = await client.get(f"{base_url}/recent_payloads?limit=5")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    payloads = data.get("data", [])
                    print(f"✅ Recent payloads: {len(payloads)} entries")
                else:
                    print(f"⚠️ Recent payloads: {data.get('status')}")
            else:
                print(f"❌ Recent payloads failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Recent payloads error: {e}")
        
        try:
            response = await client.get(f"{base_url}/attack_statistics?hours=24")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    stats = data.get("data", {})
                    print(f"✅ Attack statistics retrieved")
                    if stats.get("total_stats"):
                        total = stats["total_stats"]
                        print(f"   - Total payloads: {total.get('total_payloads', 0)}")
                        print(f"   - Malicious: {total.get('malicious_count', 0)}")
                        print(f"   - Benign: {total.get('benign_count', 0)}")
                else:
                    print(f"⚠️ Attack statistics: {data.get('status')}")
            else:
                print(f"❌ Attack statistics failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Attack statistics error: {e}")
    
    print("\n🎯 Test completed!")
    return True

async def test_api_gateway(base_url="http://localhost:9000"):
    """Test the API Gateway integration"""
    print(f"\n🌐 Testing API Gateway at {base_url}")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        # Test malicious payload through gateway
        try:
            print("🔍 Testing malicious payload through gateway...")
            
            # Send a malicious payload that should be blocked
            response = await client.post(f"{base_url}/test", 
                                       json={"data": "<script>alert('XSS')</script>"})
            
            if response.status_code == 403:
                print("✅ Malicious payload correctly blocked by gateway")
                result = response.json()
                print(f"   Block reason: {result.get('detail', 'Unknown')}")
            else:
                print(f"⚠️ Unexpected response: {response.status_code}")
                print(f"   Response: {response.text}")
            
        except Exception as e:
            print(f"❌ Gateway test error: {e}")

if __name__ == "__main__":
    rag_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    gateway_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:9000"
    
    print("🚀 Starting RAG Service Integration Tests")
    print("=" * 60)
    
    # Test RAG service
    asyncio.run(test_rag_service(rag_url))
    
    # Test API Gateway integration
    asyncio.run(test_api_gateway(gateway_url))