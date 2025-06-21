#!/bin/bash
# setup_agent_engine.sh - Setup script for Agent Engine deployment

echo "🚀 TradeSage AI - Agent Engine Setup"
echo "====================================="

# Check if required environment variables are set
if [ -z "$PROJECT_ID" ]; then
    echo "❌ PROJECT_ID environment variable not set"
    echo "Please run: export PROJECT_ID=your-project-id"
    exit 1
fi

if [ -z "$STAGING_BUCKET" ]; then
    echo "❌ STAGING_BUCKET environment variable not set" 
    echo "Please run: export STAGING_BUCKET=gs://your-bucket-name"
    exit 1
fi

echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Region: ${REGION:-us-central1}"
echo "   Staging Bucket: $STAGING_BUCKET"
echo ""

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
gcloud services enable storage.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID

# Create staging bucket if it doesn't exist
echo "🪣 Checking staging bucket..."
BUCKET_NAME=$(echo $STAGING_BUCKET | sed 's/gs:\/\///')
if ! gsutil ls $STAGING_BUCKET > /dev/null 2>&1; then
    echo "Creating staging bucket: $STAGING_BUCKET"
    gsutil mb -p $PROJECT_ID $STAGING_BUCKET
    echo "✅ Staging bucket created"
else
    echo "✅ Staging bucket exists"
fi

# Set up authentication
echo "🔐 Setting up authentication..."
gcloud auth application-default login --project=$PROJECT_ID

# Install required Python packages
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install google-cloud-aiplatform[adk,agent_engines]
pip install google-adk>=1.0.0

# Create deployment environment file
echo "📝 Creating deployment environment..."
cat > deploy.env << EOF
export PROJECT_ID=$PROJECT_ID
export REGION=${REGION:-us-central1}
export STAGING_BUCKET=$STAGING_BUCKET
export GOOGLE_CLOUD_PROJECT=$PROJECT_ID
export GOOGLE_CLOUD_LOCATION=${REGION:-us-central1}
EOF

echo "✅ Setup complete!"
echo ""
echo "💡 Next steps:"
echo "1. Source the environment: source deploy.env"
echo "2. Run deployment: python deploy_to_agent_engine.py"
echo ""
echo "🔗 Useful links:"
echo "   - Agent Engine Console: https://console.cloud.google.com/vertex-ai/agent-engine"
echo "   - Project Console: https://console.cloud.google.com/home/dashboard?project=$PROJECT_ID"
