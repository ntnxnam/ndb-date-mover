#!/bin/bash
# Start Frontend Server

echo "🚀 Starting JIRA Connection Frontend Server..."
echo ""

cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3."
    exit 1
fi

# Start the frontend server
# Using unusual port 6291 to avoid conflicts
echo "🌐 Frontend server starting on http://localhost:6291"
echo "   Make sure the backend server is running on http://localhost:8473"
echo ""
python3 frontend/server.py

