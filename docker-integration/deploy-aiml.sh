#!/bin/bash

# AI/ML Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 AI/ML RAG Service Deployment Script${NC}"
echo -e "${BLUE}=====================================${NC}"

# Change to the docker-integration directory
cd "$(dirname "$0")"
SCRIPT_DIR=$(pwd)
echo -e "${BLUE}📁 Working directory: $SCRIPT_DIR${NC}"

# Check if .env file exists
ENV_FILE="../aiml_part/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  Warning: No .env file found at $ENV_FILE${NC}"
    echo -e "${YELLOW}   Please create one with your GEMINI_API_KEY if you want to use Gemini AI${NC}"
    echo ""
    echo "Example .env file content:"
    echo "GEMINI_API_KEY=your_api_key_here"
    echo "USE_GEMINI=true"
    echo "MODEL_NAME=gemini-2.0-flash"
    echo ""
fi

# Check if datasets exist
DATASETS_DIR="../datasets"
if [ ! -d "$DATASETS_DIR" ]; then
    echo -e "${RED}❌ Error: Datasets directory not found at $DATASETS_DIR${NC}"
    echo -e "${RED}   Please ensure the datasets directory exists with CSV files${NC}"
    exit 1
fi

CSV_COUNT=$(ls -1 "$DATASETS_DIR"/*.csv 2>/dev/null | wc -l)
echo -e "${GREEN}📊 Found $CSV_COUNT CSV files in datasets directory${NC}"

if [ "$CSV_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ Error: No CSV files found in datasets directory${NC}"
    exit 1
fi

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  up       - Start the AI/ML services"
    echo "  down     - Stop the AI/ML services"
    echo "  restart  - Restart the AI/ML services"
    echo "  logs     - Show service logs"
    echo "  status   - Show service status"
    echo "  clean    - Clean up containers and volumes"
    echo "  build    - Rebuild the containers"
    echo ""
}

# Parse command line arguments
COMMAND=${1:-up}

case $COMMAND in
    "up")
        echo -e "${GREEN}🚀 Starting AI/ML services...${NC}"
        docker-compose -f docker-compose-aiml.yml up -d
        echo ""
        echo -e "${GREEN}✅ Services started!${NC}"
        echo -e "${BLUE}🌐 RAG Service: http://localhost:8000${NC}"
        echo -e "${BLUE}📊 Health Check: http://localhost:8000/health${NC}"
        echo -e "${BLUE}📈 Stats: http://localhost:8000/stats${NC}"
        echo ""
        echo -e "${YELLOW}📋 To view logs: $0 logs${NC}"
        echo -e "${YELLOW}📋 To check status: $0 status${NC}"
        ;;
    "down")
        echo -e "${YELLOW}🛑 Stopping AI/ML services...${NC}"
        docker-compose -f docker-compose-aiml.yml down
        echo -e "${GREEN}✅ Services stopped!${NC}"
        ;;
    "restart")
        echo -e "${YELLOW}🔄 Restarting AI/ML services...${NC}"
        docker-compose -f docker-compose-aiml.yml down
        docker-compose -f docker-compose-aiml.yml up -d
        echo -e "${GREEN}✅ Services restarted!${NC}"
        ;;
    "logs")
        echo -e "${BLUE}📋 Showing service logs...${NC}"
        docker-compose -f docker-compose-aiml.yml logs -f
        ;;
    "status")
        echo -e "${BLUE}📊 Service Status:${NC}"
        docker-compose -f docker-compose-aiml.yml ps
        echo ""
        echo -e "${BLUE}🏥 Health Checks:${NC}"
        echo "RAG Service: $(curl -s http://localhost:8000/health >/dev/null && echo -e "${GREEN}✅ Healthy${NC}" || echo -e "${RED}❌ Unhealthy${NC}")"
        echo "PostgreSQL: $(docker-compose -f docker-compose-aiml.yml exec postgres pg_isready -U postgres >/dev/null 2>&1 && echo -e "${GREEN}✅ Ready${NC}" || echo -e "${RED}❌ Not Ready${NC}")"
        ;;
    "clean")
        echo -e "${RED}🧹 Cleaning up containers and volumes...${NC}"
        docker-compose -f docker-compose-aiml.yml down -v
        docker system prune -f
        echo -e "${GREEN}✅ Cleanup completed!${NC}"
        ;;
    "build")
        echo -e "${BLUE}🔨 Rebuilding containers...${NC}"
        docker-compose -f docker-compose-aiml.yml build --no-cache
        echo -e "${GREEN}✅ Build completed!${NC}"
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac