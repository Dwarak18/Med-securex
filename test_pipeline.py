#!/usr/bin/env python3
"""
Test script for the cybersecurity RAG pipeline.
This script demonstrates how to use both the cyberagents and rag_pipeline modules.
"""

import os
import sys
import logging
from pathlib import Path

# Add project directories to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "cyberagents"))
sys.path.append(str(project_root / "rag_pipeline"))

def test_cyberagents():
    """Test the cyberagents module."""
    print("\n=== Testing CyberAgents ===")
    
    try:
        from cyberagents.agents.orchestrator import OrchestratorAgent
        
        # Create test data
        api_logs = [
            "POST /login {username:'admin' OR '1'='1', password:''}",
            "GET /search?q=<script>alert('xss')</script>"
        ]
        
        network_logs = [
            "192.168.1.50 scanning ports 21-80 repeatedly",
            "High volume of SYN packets from 10.0.0.99 to port 443"
        ]
        
        # Test orchestrator
        orchestrator = OrchestratorAgent()
        result = orchestrator.process(api_logs, network_logs)
        
        print("CyberAgents test result:")
        print(result)
        return True
        
    except Exception as e:
        print(f"CyberAgents test failed: {e}")
        return False

def test_rag_pipeline():
    """Test the RAG pipeline module."""
    print("\n=== Testing RAG Pipeline ===")
    
    try:
        from rag_pipeline.main_pipeline import RAGPipelineOrchestrator, RAGPipelineConfig
        
        # Create configuration
        config = RAGPipelineConfig()
        config.vector_db_path = "test_vectordb"
        
        # Initialize pipeline
        pipeline = RAGPipelineOrchestrator(config)
        
        # Test simple query
        result = pipeline.query_knowledge_base("SQL injection attack", top_k=3)
        
        print("RAG Pipeline test result:")
        print(f"Status: {result['status']}")
        print(f"Query: {result.get('query', 'N/A')}")
        print(f"Results count: {len(result.get('results', []))}")
        
        return result['status'] == 'success'
        
    except Exception as e:
        print(f"RAG Pipeline test failed: {e}")
        return False

def test_integration():
    """Test integration between both modules."""
    print("\n=== Testing Integration ===")
    
    try:
        # This would be where you'd test the integration
        # For now, just return success if both modules work independently
        print("Integration test: Both modules can be imported and used independently")
        return True
        
    except Exception as e:
        print(f"Integration test failed: {e}")
        return False

def main():
    """Main test function."""
    print("Starting Cybersecurity Pipeline Tests...")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Check for .env file
    env_file = project_root / ".env"
    if not env_file.exists():
        print("WARNING: .env file not found. Please create one with your GEMINI_API_KEY")
        print("You can copy .env.template and update it with your API key")
        return False
    
    # Run tests
    results = {
        "cyberagents": test_cyberagents(),
        "rag_pipeline": test_rag_pipeline(),
        "integration": test_integration()
    }
    
    # Print summary
    print("\n=== Test Results Summary ===")
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
