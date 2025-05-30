#!/bin/bash
# scripts/setup_cloudsql.sh

set -e

# Configuration
PROJECT_ID="tradesage-mvp"
REGION="us-central1"
INSTANCE_NAME="agentic-db"
DATABASE_NAME="tradesage_db"
DB_USER="postgres"

echo "🐘 Setting up Cloud SQL for TradeSage..."
echo "=================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is required but not installed"
    echo "Please install gcloud CLI first: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set the project
echo "📋 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Check if Cloud SQL instance exists
echo "🔍 Checking if Cloud SQL instance exists..."
if gcloud sql instances describe $INSTANCE_NAME --project=$PROJECT_ID 2>/dev/null; then
    echo "✅ Cloud SQL instance '$INSTANCE_NAME' already exists"
else
    echo "🚀 Creating Cloud SQL instance '$INSTANCE_NAME'..."
    
    # Create the Cloud SQL instance
    gcloud sql instances create $INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase \
        --backup \
        --backup-start-time=03:00 \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=04 \
        --maintenance-release-channel=production \
        --deletion-protection
    
    echo "✅ Cloud SQL instance created successfully"
fi

# Set the postgres user password
echo "🔑 Setting postgres user password..."
read -s -p "Enter password for postgres user: " DB_PASSWORD
echo

gcloud sql users set-password $DB_USER \
    --instance=$INSTANCE_NAME \
    --password=$DB_PASSWORD

echo "✅ Password set for postgres user"

# Create the database
echo "📊 Creating database '$DATABASE_NAME'..."
if gcloud sql databases describe $DATABASE_NAME --instance=$INSTANCE_NAME 2>/dev/null; then
    echo "✅ Database '$DATABASE_NAME' already exists"
else
    gcloud sql databases create $DATABASE_NAME \
        --instance=$INSTANCE_NAME
    echo "✅ Database '$DATABASE_NAME' created"
fi

# Enable vector extension (for RAG)
echo "🔌 Enabling pgvector extension..."
gcloud sql instances patch $INSTANCE_NAME \
    --database-flags=cloudsql.enable_pgvector=on

echo "⚠️ Instance restart required for pgvector extension..."
read -p "Restart instance now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gcloud sql instances restart $INSTANCE_NAME
    echo "✅ Instance restarted"
else
    echo "⚠️ Please restart the instance manually to enable pgvector"
fi

# Get connection info
echo ""
echo "🔗 Connection Information:"
echo "=================================="
echo "Instance Connection Name: $PROJECT_ID:$REGION:$INSTANCE_NAME"
echo "Database Name: $DATABASE_NAME"
echo "Username: $DB_USER"
echo "Password: [Set above]"
echo ""

# Create environment variables
echo "📝 Environment Variables:"
echo "=================================="
echo "USE_CLOUD_SQL=true"
echo "PROJECT_ID=$PROJECT_ID"
echo "REGION=$REGION"
echo "INSTANCE_NAME=$INSTANCE_NAME"
echo "DATABASE_NAME=$DATABASE_NAME"
echo "DB_USER=$DB_USER"
echo "DB_PASSWORD=$DB_PASSWORD"
echo ""

# Test connection (optional)
echo "🧪 Testing connection..."
if command -v psql &> /dev/null; then
    echo "Testing with psql..."
    # This requires Cloud SQL Proxy or proper network setup
    echo "Note: Direct connection test requires Cloud SQL Proxy"
    echo "Run: cloud_sql_proxy -instances=$PROJECT_ID:$REGION:$INSTANCE_NAME=tcp:5432"
else
    echo "psql not installed, skipping connection test"
fi

echo ""
echo "🎉 Cloud SQL setup complete!"
echo "Next steps:"
echo "1. Set the environment variables above in your .env file"
echo "2. Run: python scripts/init_cloudsql_tables.py"
echo "3. Run: python scripts/migrate_data.py (if migrating from SQLite)"
