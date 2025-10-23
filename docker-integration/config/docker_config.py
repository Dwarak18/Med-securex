"""
Environment Configuration for Docker Integration
Centralized configuration for all services - updated based on docker-compose.yml
"""

import os
import logging

# ============================================================================
# SERVICE URLs - Docker Environment (internal service names)
# ============================================================================
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag-service:8000")
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:9000")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DATABASE_CONFIG = {
    "host": POSTGRES_HOST,
    "port": int(POSTGRES_PORT),
    "database": os.getenv("POSTGRES_DB", "cybersecurity"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "password"),
}

# Connection string for SQLAlchemy/asyncpg
DATABASE_URL = f"postgresql+asyncpg://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================
MAX_PAYLOAD_SIZE = int(os.getenv("MAX_PAYLOAD_SIZE", "10240"))  # 10KB default
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# ============================================================================
# RAG SERVICE CONFIGURATION
# ============================================================================
RAG_CONFIDENCE_THRESHOLD = float(os.getenv("RAG_CONFIDENCE_THRESHOLD", "0.7"))
RAG_MAX_RESULTS = int(os.getenv("RAG_MAX_RESULTS", "5"))

# ============================================================================
# EXTERNAL API KEYS (Optional)
# ============================================================================
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")
SECURITYTRAIL_API_KEY = os.getenv("SECURITYTRAIL_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
USE_GEMINI = os.getenv("USE_GEMINI", "false").lower() == "true"

# ============================================================================
# FASTAPI CONFIGURATION
# ============================================================================
API_VERSION = "1.0.0"
API_TITLE = "Med-SecureX API"
API_DESCRIPTION = "Cybersecurity API with AI/ML Payload Detection and Analysis"

# ============================================================================
# CONFIGURATION SUMMARY (For debugging)
# ============================================================================
def print_config():
    """Print configuration summary for debugging"""
    print(f"\n{'='*60}")
    print(f"🔧 Environment Configuration Loaded (Integration-v2.0)")
    print(f"{'='*60}")
    print(f"  RAG Service: {RAG_SERVICE_URL}")
    print(f"  API Gateway: {API_GATEWAY_URL}")
    print(f"  Database: {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}")
    print(f"  Log Level: {LOG_LEVEL}")
    print(f"  Max Payload Size: {MAX_PAYLOAD_SIZE} bytes")
    print(f"  Rate Limit: {RATE_LIMIT_REQUESTS} requests/{RATE_LIMIT_WINDOW}s")
    print(f"  RAG Confidence Threshold: {RAG_CONFIDENCE_THRESHOLD}")
    print(f"  Gemini API: {'Enabled' if USE_GEMINI else 'Disabled'}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    print_config()