#!/bin/bash
# quick_deploy.sh

PROJECT_ID=${PROJECT_ID:-"tradesage-mvp"}
REGION=${REGION:-"us-central1"}

echo "🚀 Quick Cloud Run Deploy"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Check if in right directory
if [ ! -d "app/adk" ]; then
    echo "❌ Run from project root with app/adk folder"
    exit 1
fi

# Build and deploy
gcloud config set project $PROJECT_ID
gcloud builds submit --tag gcr.io/$PROJECT_ID/tradesage-ai .
gcloud run deploy tradesage-ai \
    --image gcr.io/$PROJECT_ID/tradesage-ai \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi

echo "✅ Done! Getting URL..."
gcloud run services describe tradesage-ai --region $REGION --format 'value(status.url)'
