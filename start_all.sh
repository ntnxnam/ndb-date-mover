#!/bin/bash
# Start Both Backend and Frontend Servers
# Note: Use ./restart.sh or ./uber.sh restart to run tests first

echo "🚀 Starting JIRA Connection Application..."
echo ""

cd "$(dirname "$0")"

# Make scripts executable
chmod +x start_backend.sh start_frontend.sh

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend in background
echo "📡 Starting backend server..."
./start_backend.sh &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend in background
echo "🎨 Starting frontend server..."
./start_frontend.sh &
FRONTEND_PID=$!

echo ""
echo "✅ Both servers are running!"
echo ""
echo "🌐 Frontend: http://localhost:6291"
echo "📡 Backend:  http://localhost:8473"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait

