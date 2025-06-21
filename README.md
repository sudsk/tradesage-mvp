# TradeSage AI - Complete Deployment Guide

A comprehensive guide for developing, testing, and deploying TradeSage AI system locally and on Google Cloud.

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Architecture Overview](#-architecture-overview)
- [Database Setup](#-database-setup)
- [Local Development](#-local-development)
- [Local Testing](#-local-testing)
- [Cloud Deployment](#-cloud-deployment)
- [Monitoring & Management](#-monitoring--management)
- [Troubleshooting](#-troubleshooting)

## 🚀 Quick Start

### Prerequisites

- **Python 3.9-3.12** installed
- **Node.js 16+** and npm installed
- **Google Cloud CLI** installed and configured
- **Google Cloud Project** with billing enabled
- **Docker** (optional, for containerized deployments)

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
├── Backend (Python/FastAPI)
│   ├── Local Development: app/adk/main.py
│   ├── Cloud Deployment: Agent Engine via main_agent.py
│   └── Core Logic: orchestrator.py + 6 specialized agents
└── Frontend (React/Next.js)
    ├── Local Development: npm run dev
    ├── Cloud Deployment: Cloud Run
    └── UI Components: TradingDashboard with enhanced features
```

## 📁 File Structure

```
your-project/
├── deploy_to_agent_engine.py     # Main deployment script
├── manage_agent.py               # Management utilities
├── setup_agent_engine.sh         # Initial setup
├── requirements.txt              # Unified dependencies
├── deploy.env                    # Environment variables
├── deployment_info.json          # Deployment details (auto-generated)
├── main_agent.py                 # ← Agent Engine entry point (root level)
└── app/
    └── adk/
        ├── orchestrator.py        # Your orchestrator
        └── agents/                # Your agent files
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
export NEWS_API_KEY="your-news-api-key"

# Database should already be configured from Database Setup section above

# 4. Start the backend server
python app/adk/main.py &
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Set up environment variables
echo "REACT_APP_API_URL=http://localhost:8000" > .env.local

# 4. Start the development server
npm start &
```

The frontend will be available at `http://localhost:3000`

## 🧪 Local Testing

### Full System Test

```bash
# 1. Start backend (in terminal 1)
cd tradesage-ai
source venv/bin/activate
python app/adk/main.py &
echo "Backend started on http://localhost:8000"

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
curl http://localhost:8000/health

# Test hypothesis analysis
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"hypothesis": "Tesla will reach $300 by end of 2025", "mode": "analyze"}'

# Test with streaming
curl -X POST http://localhost:8000/api/analyze/stream \
  -H "Content-Type: application/json" \
  -d '{"hypothesis": "Bitcoin will reach $100k by 2025"}'
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

### Integration Testing

```bash
# Test complete workflow
cd tradesage-ai

# Run backend tests
python -m pytest tests/ -v

# Run end-to-end tests (if configured)
cd frontend
npm run test:e2e
```

## ☁️ Cloud Deployment

### Backend: Agent Engine Deployment

```bash
# 1. Set up Google Cloud environment
export PROJECT_ID="tradesage-mvp"
export REGION="us-central1"  
export STAGING_BUCKET="gs://tradesage-staging"

# 2. Run setup script
chmod +x setup_agent_engine.sh
./setup_agent_engine.sh

# 3. Deploy to Agent Engine
source deploy.env
python deploy_to_agent_engine.py

# 4. Test deployed agent
python manage_agent.py test -m "Apple will reach $220 by Q2 2025"
```

### Frontend: Cloud Run Deployment

Create `frontend/Dockerfile`:

```dockerfile
# Frontend Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 8080
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

        location / {
            try_files $uri $uri/ /index.html;
        }

        location /api {
            proxy_pass https://YOUR_AGENT_ENGINE_URL;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
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

### Backend Monitoring

```bash
# Check Agent Engine status
python manage_agent.py info

# View logs
gcloud logging read "resource.type=gce_instance AND resource.labels.instance_name:tradesage" \
  --limit 50 \
  --format="table(timestamp,severity,textPayload)"

# Performance metrics
gcloud monitoring metrics list --filter="tradesage"
```

### Frontend Monitoring

```bash
# Cloud Run logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=tradesage-frontend" \
  --limit 50

# Performance metrics
gcloud run services describe tradesage-frontend \
  --region $REGION \
  --format="yaml(status.traffic,status.url)"
```

### Google Cloud Console

1. **Agent Engine**: https://console.cloud.google.com/vertex-ai/agent-engine
2. **Cloud Run**: https://console.cloud.google.com/run
3. **Cloud SQL**: https://console.cloud.google.com/sql
4. **Monitoring**: https://console.cloud.google.com/monitoring

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
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"hypothesis": "Test hypothesis"}'

# 4. Run tests
python -m pytest tests/
cd frontend && npm test
```

### Deployment Workflow

```bash
# 1. Test locally
python -m pytest tests/
cd frontend && npm test

# 2. Update version
git add .
git commit -m "feat: new feature"
git push

# 3. Deploy to cloud
python deploy_to_agent_engine.py
cd frontend && gcloud builds submit --tag gcr.io/$PROJECT_ID/tradesage-frontend
```

## 🔧 Troubleshooting

### Common Local Issues

**❌ Backend not starting:**
```bash
# Check Python version
python --version  # Should be 3.9-3.12

# Check dependencies
pip install -r requirements.txt

# Check environment variables
echo $GOOGLE_CLOUD_PROJECT

# Check logs
python app/adk/main.py  # Run without & to see logs
```

**❌ Frontend not connecting:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check environment variables
cat frontend/.env.local

# Check CORS settings in backend
```

**❌ Database connection issues:**
```bash
# Check Cloud SQL proxy
cloud_sql_proxy -instances=$PROJECT_ID:$REGION:tradesage-db=tcp:5432

# Test connection
psql -h localhost -U tradesage-user -d tradesage
```

### Common Cloud Issues

**❌ Agent Engine deployment fails:**
```bash
# Check APIs are enabled
gcloud services list --enabled | grep aiplatform

# Check staging bucket permissions
gsutil ls $STAGING_BUCKET

# Check deployment logs
python deploy_to_agent_engine.py 2>&1 | tee deploy.log
```

**❌ Cloud Run deployment fails:**
```bash
# Check Docker build
docker build -t test-image frontend/

# Check Cloud Build permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/run.developer"

# Check service logs
gcloud run services logs read tradesage-frontend --region $REGION
```

### Performance Issues

**🐌 Slow Agent Engine responses:**
```bash
# Check Agent Engine metrics
python manage_agent.py info

# Monitor request latency
gcloud monitoring metrics list --filter="agent_engine"

# Scale up if needed (automatic with Agent Engine)
```

**🐌 Slow frontend loading:**
```bash
# Check Cloud Run metrics
gcloud run services describe tradesage-frontend --region $REGION

# Increase resources
gcloud run services update tradesage-frontend \
  --memory 2Gi \
  --cpu 2 \
  --region $REGION
```

## 📚 Additional Resources

### Documentation
- [Agent Development Kit](https://google.github.io/adk-docs/)
- [Agent Engine](https://cloud.google.com/vertex-ai/docs/agent-engine)
- [Cloud Run](https://cloud.google.com/run/docs)
- [Cloud SQL](https://cloud.google.com/sql/docs)

### Sample Commands Reference

```bash
# Quick start local development
source venv/bin/activate && python app/adk/main.py & cd frontend && npm start &

# Quick deploy to cloud
python deploy_to_agent_engine.py && cd frontend && gcloud builds submit --tag gcr.io/$PROJECT_ID/tradesage-frontend

# Quick health check
curl http://localhost:8000/health && python manage_agent.py test

# Quick logs check
gcloud logs read "resource.type=cloud_run_revision" --limit 10
```

### Cost Optimization

- **Agent Engine**: Pay per request, scales to zero
- **Cloud Run**: Pay per request, scales to zero
- **Cloud SQL**: Consider smaller instance for development
- **Storage**: Use lifecycle policies for staging bucket

---

**🎉 Your TradeSage AI system is now ready for both local development and cloud deployment!**

For support, check the troubleshooting section or refer to the Google Cloud documentation links above.
