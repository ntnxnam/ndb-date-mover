#!/bin/bash
# Start Backend Server

echo "🚀 Starting JIRA Connection Backend Server..."
echo ""

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.dependencies_installed" ]; then
    echo "📥 Installing dependencies..."
    pip install -q -r requirements.txt
    touch venv/.dependencies_installed
fi

# Change to backend directory for running the app
cd backend

# Check for .env file (in project root)
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Please create .env file in the project root with JIRA_URL and JIRA_PAT_TOKEN"
    echo ""
fi

# Start the backend server
# Using unusual port 8473 to avoid conflicts
echo "🌐 Backend API server starting on http://localhost:8473"
echo "   Health check: http://localhost:8473/health"
echo ""
python3 app.py

