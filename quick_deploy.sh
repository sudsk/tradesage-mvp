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
    --set-env-vars "PROJECT_ID=$PROJECT_ID,REGION=$REGION,DB_PASSWORD=$DB_PASSWORD,INSTANCE_NAME=$INSTANCE_NAME,DATABASE_NAME=$DATABASE_NAME,DB_USER=$DB_USER,ALPHA_VANTAGE_API_KEY=$ALPHA_VANTAGE_API_KEY,FMP_API_KEY=$FMP_API_KEY,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,GOOGLE_GENAI_USE_VERTEXAI=True"

echo "✅ Done! Getting URL..."
gcloud run services describe tradesage-ai --region $REGION --format 'value(status.url)'
