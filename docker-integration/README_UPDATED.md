# Docker Integration for Cybersecurity RAG System

This directory contains the complete Docker integration setup for the cybersecurity threat intelligence RAG (Retrieval-Augmented Generation) system.

## Overview

The system consists of:
- **Qdrant Vector Database**: For storing and retrieving vector embeddings
- **PostgreSQL Database**: For structured data storage
- **RAG Service**: AI/ML service for threat analysis using the new dataset structure
- **API Gateway**: Entry point for security payload inspection
- **Nginx**: Reverse proxy (optional)

## New Dataset Structure

The system now uses **24 individual CSV files** instead of a single master dataset:

### Dataset Files (in `../datasets/` directory):
- `brute_force.csv`
- `command_injection.csv` 
- `cross_site_scripting.csv`
- `deserialization.csv`
- `directory_traversal.csv`
- `empty_null.csv`
- `file_inclusion.csv`
- `generic_payload.csv`
- `generic_payload_generic.csv`
- `healthcare_idor.csv`
- `healthcare_path_traversal.csv`
- `healthcare_sql_injection.csv`
- `healthcare_xss.csv`
- `http_protocol_attack.csv`
- `idor.csv`
- `normal_query.csv`
- `open_redirect.csv`
- `path_traversal.csv`
- `race_condition.csv`
- `sql_injection.csv`
- `ssrf.csv`
- `ssti.csv`
- `xss.csv`
- `xxe.csv`

### CSV Format
Each CSV file contains columns:
- `Payload`: The actual attack payload
- `Signature`: Attack signature identifier  
- `AttackType`: Type of attack
- `Severity`: Critical, High, Medium, Low
- `MITRE`: MITRE ATT&CK technique ID
- `Label`: Malicious/Legit classification
- `Description`: Human-readable description

## Vector Database

**Changed from ChromaDB to Qdrant:**
- Uses Qdrant vector database for better performance
- Persistent storage with Docker volumes
- Configurable connection via environment variables

## Quick Start

1. **Build and start all services:**
```bash
cd docker-integration
docker-compose up --build
```

2. **Check service health:**
```bash
# Qdrant health
curl http://localhost:6333/health

# PostgreSQL health  
docker-compose exec postgres pg_isready -U postgres

# RAG service health
curl http://localhost:8000/health

# API Gateway health
curl http://localhost:9000/health
```

3. **Load dataset:**
The dataset is automatically loaded when the RAG service starts. Monitor logs:
```bash
docker-compose logs -f rag-service
```

## Configuration

### Environment Variables

**Qdrant Configuration:**
- `QDRANT_HOST`: Qdrant server host (default: qdrant)
- `QDRANT_PORT`: Qdrant server port (default: 6333)

**PostgreSQL Configuration:**
- `POSTGRES_HOST`: PostgreSQL host (default: postgres)
- `POSTGRES_PORT`: PostgreSQL port (default: 5432)
- `POSTGRES_DB`: Database name (default: cybersecurity)
- `POSTGRES_USER`: Database user (default: postgres)
- `POSTGRES_PASSWORD`: Database password (default: password)

### Volume Mounts

- `../datasets:/app/datasets` - 24 CSV dataset files
- `../../dataset:/app/dataset` - Legacy dataset backup
- `qdrant_vectors:/app/cybersecurity_vectordb` - Vector embeddings
- `postgres_data:/var/lib/postgresql/data` - PostgreSQL data

## API Endpoints

### RAG Service (Port 8000)
- `GET /health` - Health check
- `POST /analyze_payload` - Analyze security payload
- `GET /stats` - Service statistics
- `POST /query` - Query threat intelligence

### API Gateway (Port 9000)  
- `GET /health` - Health check
- `POST /validate` - Validate incoming requests
- `POST /scan` - Security scan endpoint

## Development

### Adding New Attack Types
1. Create new CSV file in `../datasets/` with the standard format
2. Restart the RAG service to reload datasets:
```bash
docker-compose restart rag-service
```

### Rebuilding Vector Database
```bash
# Force rebuild with new data
docker-compose down
docker volume rm docker-integration_qdrant_vectors
docker-compose up --build
```

### Logs
```bash
# View all logs
docker-compose logs

# Follow specific service
docker-compose logs -f rag-service
docker-compose logs -f api-gateway
```

## Troubleshooting

### Common Issues

1. **Dataset not loading:**
   - Check if `../datasets/` directory exists with 24 CSV files
   - Verify CSV format matches expected columns
   - Check RAG service logs: `docker-compose logs rag-service`

2. **Qdrant connection failed:**
   - Wait for Qdrant to be fully ready (can take 30-60 seconds)
   - Check Qdrant logs: `docker-compose logs qdrant`
   - Verify port 6333 is not used by other services

3. **PostgreSQL issues:**
   - Check PostgreSQL logs: `docker-compose logs postgres`
   - Verify init.sql is mounted correctly
   - Ensure port 5432 is available

### Performance Tuning

1. **Increase Qdrant memory:**
```yaml
qdrant:
  deploy:
    resources:
      limits:
        memory: 2G
```

2. **PostgreSQL optimization:**
```yaml
postgres:
  environment:
    - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
    - POSTGRES_MAX_CONNECTIONS=200
```

## Security Considerations

- Change default PostgreSQL password in production
- Use secrets management for sensitive data
- Enable TLS/SSL for external connections
- Implement proper network segmentation

## Monitoring

Monitor service health:
```bash
# Check all container status
docker-compose ps

# Monitor resource usage
docker stats

# Check vector database stats
curl http://localhost:6333/metrics
```