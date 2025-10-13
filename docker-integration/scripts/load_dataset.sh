#!/bin/bash

# Dataset loading script for Docker integration
echo "Loading cybersecurity dataset from multiple CSV files..."

# Check if datasets directory exists
if [ ! -d "/app/dataset" ]; then
    echo "Error: Dataset directory not found at /app/dataset/"
    exit 1
fi

# Check if we have CSV files
CSV_COUNT=$(find /app/dataset -name "*.csv" -type f | wc -l)
if [ "$CSV_COUNT" -eq 0 ]; then
    echo "Error: No CSV files found in /app/dataset/"
    exit 1
fi

echo "Found $CSV_COUNT CSV files in dataset directory"

# Wait for Qdrant to be ready
echo "Waiting for Qdrant to be ready..."
until curl -f http://${QDRANT_HOST:-qdrant}:${QDRANT_PORT:-6333}/health > /dev/null 2>&1; do
    echo "Waiting for Qdrant..."
    sleep 5
done

# Wait for PostgreSQL to be ready  
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h ${POSTGRES_HOST:-postgres} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres} > /dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 5
done

echo "All services are ready."
echo "Dataset with $CSV_COUNT files will be automatically processed when RAG service starts."
echo "CSV files available:"
ls -1 /app/dataset/*.csv | head -10