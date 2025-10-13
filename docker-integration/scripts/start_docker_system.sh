#!/bin/bash

echo "🚀 Starting Enhanced Cybersecurity System with Cyber Agents..."

# Navigate to docker integration directory
cd "$(dirname "$0")/.."

# Build and start all services
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
services=("postgres:5432" "rag-service:8000" "api-gateway:9000" "nginx:8080")

for service in "${services[@]}"; do
    name=${service%:*}
    port=${service#*:}
    
    if [ "$name" = "postgres" ]; then
        # Special check for PostgreSQL
        if docker-compose exec postgres pg_isready -U postgres -d cybersecurity > /dev/null 2>&1; then
            echo "✅ PostgreSQL is healthy"
        else
            echo "❌ PostgreSQL is not responding"
        fi
    elif curl -s http://localhost:$port/health > /dev/null 2>&1 || curl -s http://localhost:$port/stats > /dev/null 2>&1; then
        echo "✅ $name is healthy"
    else
        echo "❌ $name is not responding"
    fi
done

echo ""
echo "🎉 Enhanced Security System is ready!"
echo "📊 Service URLs:"
echo "  - Frontend (Nginx): http://localhost:8080"
echo "  - API Gateway: http://localhost:9000"
echo "  - RAG Service: http://localhost:8000 (internal)"
echo "  - PostgreSQL: localhost:5432"
echo ""
echo "🤖 Cyber Agents Features:"
echo "  - Attack Agent: Payload vector analysis"
echo "  - Network Agent: IP reputation & monitoring"
echo "  - Investigation Agent: MITRE ATT&CK mapping"
echo ""
echo "📋 Management Commands:"
echo "  - View logs: docker-compose logs -f [service-name]"
echo "  - Stop system: ./stop_docker_system.sh"
echo "  - Test system: ./test_docker_system.sh"
echo ""
echo "🧪 Quick test:"
echo '  curl -X POST http://localhost:9000/test -H "Content-Type: application/json" -d '"'"'{"test": "SELECT * FROM users"}'"'"