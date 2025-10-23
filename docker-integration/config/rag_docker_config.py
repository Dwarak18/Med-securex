"""
Updated RAG Service Configuration for Docker
Add this to your rag_service.py file to support Docker environment
Uses Qdrant vector database for enhanced performance

USAGE GUIDE:
1. Copy the get_qdrant_config() function to your rag_service.py
2. Update the RAGPipelineConfig initialization to use: config.vector_db_path = get_qdrant_config()
3. Add the health check endpoint to your FastAPI app
"""

import os
import logging
from typing import Optional

# Docker Environment Configuration for Qdrant
def get_qdrant_config() -> str:
    """
    Get Qdrant configuration for Docker environment
    Returns the Qdrant connection URL based on environment variables
    
    Environment Variables:
        QDRANT_HOST: Hostname or IP of Qdrant service (default: localhost)
        QDRANT_PORT: Port of Qdrant service (default: 6333)
    """
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = os.getenv("QDRANT_PORT", "6333")
    
    if qdrant_host != "localhost":
        # Running in Docker, use internal service name
        return f"http://{qdrant_host}:{qdrant_port}"
    else:
        # Running locally, use localhost
        return f"http://localhost:{qdrant_port}"


# REFERENCE ONLY - Copy this pattern to your rag_service.py
# def init_rag_pipeline():
#     """Initialize the RAG pipeline with Qdrant vector database"""
#     global rag_pipeline
#     try:
#         from rag_pipeline.main_pipeline import RAGPipelineOrchestrator, RAGPipelineConfig
#         
#         config = RAGPipelineConfig()
#         config.vector_db_path = get_qdrant_config()  # Use this line!
#         
#         rag_pipeline = RAGPipelineOrchestrator(config)
#         logging.info(f"RAG Pipeline initialized with Qdrant at {config.vector_db_path}")
#         return rag_pipeline
#     except Exception as e:
#         logging.warning(f"Failed to initialize RAG Pipeline: {e}")
#         return None


# REFERENCE ONLY - Health check endpoint pattern for FastAPI
# @app.get("/health")
# async def health_check():
#     return {
#         "status": "healthy",
#         "service": "rag-service",
#         "version": "1.0.0",
#         "vector_db": "qdrant",
#         "qdrant_url": get_qdrant_config()
#     }