#!/bin/bash
# setup_and_run.sh - Script to set up the database and run TradeSage

set -e

echo "🚀 Setting up TradeSage with SQLite database..."

# Create necessary directories
mkdir -p app/database

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Initialize the database with sample data
echo "🗃️ Initializing database with sample data..."
python scripts/init_db.py

# Start the backend server
echo "🚀 Starting backend server..."
python -m app.main_with_db &
BACKEND_PID=$!

# Wait a moment for the backend to start
sleep 3

# Check if backend is running
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend server is running on http://localhost:8000"
else
    echo "❌ Backend server failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start the frontend (if available)
if [ -d "frontend" ]; then
    echo "🚀 Starting frontend..."
    cd frontend
    npm install
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    echo "✅ Frontend started on http://localhost:3000"
fi

echo "
🎉 TradeSage is now running!

📊 Dashboard: http://localhost:3000
🔧 API: http://localhost:8000
📚 API Docs: http://localhost:8000/docs

Key endpoints:
- GET /dashboard - Get all hypotheses
- GET /hypothesis/{id} - Get hypothesis details
- POST /process - Process new hypothesis
- GET /alerts - Get unread alerts

To stop the servers:
- Press Ctrl+C or run: kill $BACKEND_PID"

if [ -n "${FRONTEND_PID:-}" ]; then
    echo "  For frontend: kill $FRONTEND_PID"
fi

# Keep the script running
wait
