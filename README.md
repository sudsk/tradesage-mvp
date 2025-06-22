# TradeSage AI - Complete Deployment Guide

A comprehensive guide for developing, testing, and deploying TradeSage AI system locally and on Google Cloud.

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Architecture Overview](#-architecture-overview)
- [Repository Structure](#-repository-structure)
- [Database Setup](#-database-setup)
- [Local Development](#-local-development)
- [Local Testing](#-local-testing)
- [Cloud Deployment](#-cloud-deployment)
- [Monitoring & Management](#-monitoring--management)
- [Troubleshooting](#-troubleshooting)

## 🚀 Quick Start

### Prerequisites

- **Python 3.10-3.12** installed
- **Node.js 16+** and npm installed
- **Google Cloud CLI** installed and configured
- **Google Cloud Project** with billing enabled
- **Docker** (for Cloud Run deployments)

### Environment Setup

```bash
# Clone your repository
git clone <your-repo-url>
cd tradesage-ai

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

## 🏗️ Architecture Overview

```
TradeSage AI System
├── Backend (Python/FastAPI with ADK)
│   ├── Local Development: app/adk/main.py
│   ├── Cloud Deployment Option 1: Cloud Run (Recommended)
│   ├── Cloud Deployment Option 2: Agent Engine
│   └── Core Logic: orchestrator.py + 6 specialized agents
└── Frontend (React/Next.js)
    ├── Local Development: npm run dev
    ├── Cloud Deployment: Cloud Run
    └── UI Components: TradingDashboard with enhanced features
```

## 📁 Repository Structure

```
tradesage-ai/
├── Dockerfile                    # Cloud Run deployment configuration
├── .dockerignore                 # Docker build exclusions
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── .gitignore                    # Git exclusions
├── README.md                     # This file
├── main_agent.py                 # Agent Engine entry point (optional)
├── quick_deploy.sh               # Quick Cloud Run deployment script
├── service.yaml                  # Cloud Run service configuration
├── app/
│   ├── __init__.py
│   ├── adk/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI application entry point
│   │   ├── orchestrator.py       # Multi-agent orchestrator
│   │   ├── agents/               # Specialized agents
│   │   │   ├── __init__.py
│   │   │   ├── hypothesis_agent.py
│   │   │   ├── context_agent.py
│   │   │   ├── research_agent.py
│   │   │   ├── contradiction_agent.py
│   │   │   ├── synthesis_agent.py
│   │   │   └── alert_agent.py
│   │   ├── tools.py              # ADK tools and utilities
│   │   └── response_handler.py   # Response processing
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py           # Database connection and setup
│   │   ├── models.py             # SQLAlchemy models
│   │   └── crud.py               # Database operations
│   ├── services/
│   │   ├── __init__.py
│   │   ├── market_data_service.py
│   │   └── hybrid_rag_service.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── market_data_tool.py
│   │   └── news_data_tool.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── text_processor.py
│   └── config/
│       ├── __init__.py
│       └── adk_config.py
├── frontend/                     # React/Next.js frontend
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── Dockerfile               # Frontend Cloud Run deployment
├── scripts/
│   ├── __init__.py
│   ├── init_cloudsql_tables.py
│   ├── init_cloudsql_demo.py
│   └── manage_db.py
└── deployment/                   # Deployment utilities
    ├── deploy_to_agent_engine.py # Agent Engine deployment (optional)
    ├── manage_agent.py           # Agent management utilities
    └── setup_agent_engine.sh     # Agent Engine setup (optional)
```

## 🗃️ Database Setup

TradeSage uses **Cloud SQL PostgreSQL** for all environments (local development and cloud deployment). This ensures consistency across environments and leverages advanced PostgreSQL features.

### Cloud SQL Setup

```bash
# 1. Create Cloud SQL instance
export PROJECT_ID="tradesage-mvp"
export REGION="us-central1"
export DB_PASSWORD="your-secure-password"

gcloud sql instances create tradesage-db \
  --database-version=POSTGRES_13 \
  --tier=db-f1-micro \
  --region=$REGION

# 2. Create database
gcloud sql databases create tradesage \
  --instance=tradesage-db

# 3. Create user
gcloud sql users create tradesage-user \
  --instance=tradesage-db \
  --password=$DB_PASSWORD

# 4. Initialize tables and extensions
python scripts/init_cloudsql_tables.py

# 5. Add demo data (optional)
python scripts/init_cloudsql_demo.py
```

### Environment Configuration

Update your `.env` file with database settings:

```bash
# Cloud SQL PostgreSQL Configuration
PROJECT_ID=tradesage-mvp
REGION=us-central1
INSTANCE_NAME=tradesage-db
DATABASE_NAME=tradesage
DB_USER=tradesage-user
DB_PASSWORD=your-secure-password

# API Keys (optional for basic functionality)
ALPHA_VANTAGE_API_KEY=your-api-key
FMP_API_KEY=your-fmp-key

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=tradesage-mvp
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=True
```

**Note:** Cloud SQL is used for both local development and cloud deployment to ensure environment consistency.

## 💻 Local Development

### Backend Setup

```bash
# 1. Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies from unified requirements
pip install -r requirements.txt

# 3. Set up environment variables (after database setup)
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GOOGLE_GENAI_USE_VERTEXAI="True"
export ALPHA_VANTAGE_API_KEY="your-api-key"
export FMP_API_KEY="your-fmp-key"

# Database should already be configured from Database Setup section above

# 4. Start the backend server
python app/adk/main.py
```

The backend will be available at `http://localhost:8080`

### Frontend Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Set up environment variables
echo "REACT_APP_API_URL=http://localhost:8080" > .env.local

# 4. Start the development server
npm start
```

The frontend will be available at `http://localhost:3000`

## 🧪 Local Testing

### Full System Test

```bash
# 1. Start backend (in terminal 1)
cd tradesage-ai
source venv/bin/activate
python app/adk/main.py &
echo "Backend started on http://localhost:8080"

# 2. Start frontend (in terminal 2)
cd tradesage-ai/frontend
npm start &
echo "Frontend started on http://localhost:3000"

# 3. Test the integration
# Open browser to http://localhost:3000
# Submit a hypothesis: "Apple will reach $220 by Q2 2025"
```

### Backend API Testing

```bash
# Test health endpoint
curl http://localhost:8080/health

# Test hypothesis analysis
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d '{"hypothesis": "Tesla will reach $300 by end of 2025", "mode": "analyze"}'

# Test dashboard data
curl http://localhost:8080/dashboard
```

### Frontend Testing

```bash
# Run tests
cd frontend
npm test

# Run linting
npm run lint

# Build for production (test)
npm run build
npm run start  # Test production build locally
```

## ☁️ Cloud Deployment

### Backend: Cloud Run Deployment (Recommended)

Cloud Run provides a serverless, fully managed platform that's ideal for the TradeSage AI backend with automatic scaling and pay-per-use pricing.

#### Quick Cloud Run Deployment

```bash
# 1. Set up environment variables
export PROJECT_ID="tradesage-mvp"
export REGION="us-central1"

# 2. Set up gcloud
gcloud config set project $PROJECT_ID

# 3. Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com

# 4. Quick deployment using the provided script
chmod +x quick_deploy.sh
./quick_deploy.sh
```

#### Manual Cloud Run Deployment

```bash
# 1. Build the container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/tradesage-ai .

# 2. Deploy to Cloud Run with environment variables
gcloud run deploy tradesage-ai \
  --image gcr.io/$PROJECT_ID/tradesage-ai \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 900 \
  --set-env-vars "PROJECT_ID=$PROJECT_ID,REGION=$REGION,DB_PASSWORD=your-db-password,INSTANCE_NAME=tradesage-db,DATABASE_NAME=tradesage,DB_USER=tradesage-user,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,GOOGLE_GENAI_USE_VERTEXAI=True,ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key,FMP_API_KEY=your-fmp-key"

# 3. Get the service URL
SERVICE_URL=$(gcloud run services describe tradesage-ai --region $REGION --format 'value(status.url)')
echo "🔗 Service URL: $SERVICE_URL"
```

#### Setting Environment Variables in Cloud Run

You can set environment variables using YAML configuration:

```bash
# Create service.yaml with environment variables
cat > service.yaml << 'EOF'
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: tradesage-ai
spec:
  template:
    spec:
      containers:
      - image: gcr.io/tradesage-mvp/tradesage-ai
        ports:
        - containerPort: 8080
        env:
        - name: PROJECT_ID
          value: tradesage-mvp
        - name: REGION
          value: us-central1
        - name: DB_PASSWORD
          value: your-secure-password
        - name: INSTANCE_NAME
          value: tradesage-db
        - name: DATABASE_NAME
          value: tradesage
        - name: DB_USER
          value: tradesage-user
        - name: GOOGLE_CLOUD_PROJECT
          value: tradesage-mvp
        - name: GOOGLE_CLOUD_LOCATION
          value: us-central1
        - name: GOOGLE_GENAI_USE_VERTEXAI
          value: "True"
        - name: ALPHA_VANTAGE_API_KEY
          value: your-alpha-vantage-key
        - name: FMP_API_KEY
          value: your-fmp-key
        resources:
          limits:
            memory: 4Gi
            cpu: 2
EOF

# Apply the configuration
gcloud run services replace service.yaml --region $REGION
```

### Backend: Agent Engine Deployment (Alternative)

For advanced use cases requiring the Agent Engine platform:

```bash
# 1. Set up Google Cloud environment
export PROJECT_ID="tradesage-mvp"
export REGION="us-central1"  
export STAGING_BUCKET="gs://tradesage-staging"

# 2. Run setup script
chmod +x deployment/setup_agent_engine.sh
./deployment/setup_agent_engine.sh

# 3. Deploy to Agent Engine
python deployment/deploy_to_agent_engine.py

# 4. Test deployed agent
python deployment/manage_agent.py test -m "Apple will reach $220 by Q2 2025"
```

### Frontend: Cloud Run Deployment

Create `frontend/Dockerfile`:

```dockerfile
# Frontend Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Clean install dependencies (fix sync issues)
RUN npm install

# Copy source code
COPY . .

# Build the React app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

Create `frontend/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    server {
        listen 8080;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # More specific API proxy configuration
        location ^~ /api/ {
            proxy_pass YOUR-BACKEND-URL/;
            proxy_set_header Host YOUR-BACKEND-URL-HOSTNAME;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Accept application/json;
            proxy_redirect off;
        }

        # React app (all other routes)
        location / {
            try_files $uri $uri/ /index.html;
        }
    }
}
```

Deploy frontend to Cloud Run:

```bash
# 1. Build and deploy
cd frontend

# 2. Set environment variables
export PROJECT_ID="tradesage-mvp"
export SERVICE_NAME="tradesage-frontend"
export REGION="us-central1"

# 3. Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1

# 4. Get the service URL
gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)'
```

## 📊 Monitoring & Management

### Cloud Run Backend Monitoring

```bash
# View service status
gcloud run services describe tradesage-ai --region $REGION

# View logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=tradesage-ai" \
  --limit 50 \
  --format="table(timestamp,severity,textPayload)"

# Monitor performance metrics
gcloud run services describe tradesage-ai \
  --region $REGION \
  --format="yaml(status.traffic,status.url)"

# Update service configuration
gcloud run services update tradesage-ai \
  --region $REGION \
  --memory 8Gi \
  --cpu 4
```

### Google Cloud Console

1. **Cloud Run**: https://console.cloud.google.com/run
2. **Cloud SQL**: https://console.cloud.google.com/sql
3. **Monitoring**: https://console.cloud.google.com/monitoring
4. **Logs**: https://console.cloud.google.com/logs

## 🛠️ Development Workflow

### Daily Development

```bash
# 1. Start local environment
cd tradesage-ai
source venv/bin/activate
python app/adk/main.py &

cd frontend
npm start &

# 2. Make changes
# Edit files in your IDE

# 3. Test changes
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d '{"hypothesis": "Test hypothesis"}'

# 4. Run tests
python -m pytest tests/
cd frontend && npm test
```

### Cloud Deployment Workflow

```bash
# 1. Test locally
python -m pytest tests/
cd frontend && npm test

# 2. Update version
git add .
git commit -m "feat: new feature"
git push

# 3. Deploy backend to Cloud Run
./quick_deploy.sh

# 4. Deploy frontend to Cloud Run
cd frontend && gcloud builds submit --tag gcr.io/$PROJECT_ID/tradesage-frontend
```

## 🔧 Troubleshooting

### Common Local Issues

**❌ Backend not starting:**
```bash
# Check Python version
python --version  # Should be 3.10-3.12

# Check dependencies
pip install -r requirements.txt

# Check environment variables
echo $GOOGLE_CLOUD_PROJECT

# Check logs
python app/adk/main.py  # Run without & to see logs
```

**❌ Database connection issues:**
```bash
# Check Cloud SQL instance status
gcloud sql instances describe tradesage-db

# Test connection with cloud sql proxy
cloud_sql_proxy -instances=$PROJECT_ID:$REGION:tradesage-db=tcp:5432

# Test connection
psql -h localhost -U tradesage-user -d tradesage
```

### Common Cloud Run Issues

**❌ Container fails to start:**
```bash
# Check container logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=tradesage-ai" --limit=50

# Check environment variables
gcloud run services describe tradesage-ai --region $REGION --format="value(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)"

# Test container locally
docker build -t tradesage-test .
docker run -p 8080:8080 -e PROJECT_ID=tradesage-mvp tradesage-test
```

**❌ Service not responding:**
```bash
# Check service status
gcloud run services describe tradesage-ai --region $REGION

# Increase timeout and resources
gcloud run services update tradesage-ai \
  --region $REGION \
  --timeout 900 \
  --memory 4Gi \
  --cpu 2
```

**❌ Environment variables not set:**
```bash
# Update environment variables using YAML
gcloud run services replace service.yaml --region $REGION

# Or update individual variables
gcloud run services update tradesage-ai \
  --region $REGION \
  --set-env-vars PROJECT_ID=tradesage-mvp,DB_PASSWORD=your-password
```

### Performance Issues

**🐌 Slow Cloud Run responses:**
```bash
# Check Cloud Run metrics
gcloud run services describe tradesage-ai --region $REGION

# Increase resources
gcloud run services update tradesage-ai \
  --memory 8Gi \
  --cpu 4 \
  --region $REGION

# Enable CPU always allocated
gcloud run services update tradesage-ai \
  --region $REGION \
  --cpu-throttling
```

## 📚 Additional Resources

### Documentation
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Agent Development Kit](https://google.github.io/adk-docs/)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Container Registry](https://cloud.google.com/container-registry/docs)

### Sample Commands Reference

```bash
# Quick start local development
source venv/bin/activate && python app/adk/main.py & cd frontend && npm start &

# Quick deploy backend to Cloud Run
./quick_deploy.sh

# Quick health check
curl https://your-cloud-run-url/health

# Quick logs check
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=tradesage-ai" --limit 10
```

### Cost Optimization

- **Cloud Run**: Pay per request, scales to zero when not in use
- **Cloud SQL**: Consider smaller instance for development (db-f1-micro)
- **Container Registry**: Clean up old images regularly
- **Logs**: Set retention policies to manage storage costs

---

**🎉 Your TradeSage AI system is now ready for both local development and cloud deployment with Cloud Run!**

For support, check the troubleshooting section or refer to the Google Cloud documentation links above.
