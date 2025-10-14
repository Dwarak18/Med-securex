#!/bin/bash

# AI/ML RAG Service Startup Script
set -e

echo "🚀 Starting AI/ML RAG Service..."

# Check if we're in the right directory
if [ ! -f "rag_service.py" ]; then
    echo "❌ Error: rag_service.py not found. Make sure you're in the aiml_part directory."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p /app/logs /app/models /app/models/tmp
chmod -R 755 /app/models /app/logs

# Check if datasets directory exists
if [ ! -d "/app/datasets" ]; then
    echo "❌ Warning: Datasets directory not found at /app/datasets"
    echo "   Model training will be skipped."
else
    echo "📊 Found datasets directory with $(ls -1 /app/datasets/*.csv 2>/dev/null | wc -l) CSV files"
fi

# Check if models exist, if not, train them
if [ ! -f "/app/models/attack_model.joblib" ] || [ ! -f "/app/models/network_model.joblib" ]; then
    if [ -d "/app/datasets" ] && [ "$(ls -1 /app/datasets/*.csv 2>/dev/null | wc -l)" -gt 0 ]; then
        echo "🎯 Models not found. Training models from datasets..."
        python train_models.py
        
        # Check if training was successful
        if [ -f "/app/models/attack_model.joblib" ] && [ -f "/app/models/network_model.joblib" ]; then
            echo "✅ Model training completed successfully!"
        else
            echo "❌ Model training failed. Continuing without trained models."
        fi
    else
        echo "⚠️  No datasets found. Skipping model training."
    fi
else
    echo "✅ Pre-trained models found. Skipping training."
fi

# Wait for PostgreSQL to be ready
echo "🗄️  Waiting for PostgreSQL connection..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if python -c "
import asyncio
import asyncpg
import sys
import os
sys.path.insert(0, '/app/../API-gateway')

async def test_postgres():
    try:
        conn = await asyncpg.connect('postgresql://postgres:password@postgres:5432/cybersecurity')
        await conn.close()
        return True
    except:
        return False

result = asyncio.run(test_postgres())
sys.exit(0 if result else 1)
"; then
        echo "✅ PostgreSQL connection established!"
        break
    else
        echo "⏳ Attempt $attempt/$max_attempts: PostgreSQL not ready, waiting 2 seconds..."
        sleep 2
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ PostgreSQL connection failed after $max_attempts attempts. Starting service anyway..."
fi

# Check if .env file exists for Gemini API key
if [ -f "/app/.env" ]; then
    echo "🔑 Found .env file for API keys"
else
    echo "⚠️  No .env file found. Make sure GEMINI_API_KEY is set via environment variables."
fi

# Start the RAG service
echo "🔥 Starting RAG service..."
exec uvicorn rag_service:app --host 0.0.0.0 --port 8000 --reload --log-level info