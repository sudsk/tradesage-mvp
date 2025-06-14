#!/bin/bash
# scripts/deploy_adk.sh

echo "🚀 Deploying TradeSage AI - ADK Version"

# Build and deploy
docker-compose -f docker-compose.adk.yml up --build -d tradesage-adk

echo "✅ ADK version deployed on port 8001"
echo "📊 LangGraph version available on port 8000"
echo "🔗 Test ADK: curl http://localhost:8001/health"
echo "🔗 Test LangGraph: curl http://localhost:8000/health"
