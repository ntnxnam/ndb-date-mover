#!/bin/bash
# Kill Backend and Frontend Servers

echo "🛑 Stopping JIRA Connection servers..."
echo ""

BACKEND_PORT=8473
FRONTEND_PORT=6291

# Find and kill processes on backend port
BACKEND_PIDS=$(lsof -ti:$BACKEND_PORT 2>/dev/null)
if [ -n "$BACKEND_PIDS" ]; then
    echo "📡 Killing backend server on port $BACKEND_PORT (PIDs: $BACKEND_PIDS)..."
    kill -9 $BACKEND_PIDS 2>/dev/null
    echo "   ✅ Backend server stopped"
else
    echo "   ℹ️  No process found on port $BACKEND_PORT"
fi

# Find and kill processes on frontend port
FRONTEND_PIDS=$(lsof -ti:$FRONTEND_PORT 2>/dev/null)
if [ -n "$FRONTEND_PIDS" ]; then
    echo "🎨 Killing frontend server on port $FRONTEND_PORT (PIDs: $FRONTEND_PIDS)..."
    kill -9 $FRONTEND_PIDS 2>/dev/null
    echo "   ✅ Frontend server stopped"
else
    echo "   ℹ️  No process found on port $FRONTEND_PORT"
fi

# Wait a moment for processes to fully terminate
sleep 1

# Verify ports are free
if lsof -ti:$BACKEND_PORT,$FRONTEND_PORT 2>/dev/null | grep -q .; then
    echo ""
    echo "⚠️  Warning: Some processes may still be running"
    lsof -ti:$BACKEND_PORT,$FRONTEND_PORT 2>/dev/null | xargs kill -9 2>/dev/null
    sleep 1
fi

echo ""
echo "✅ All servers stopped. Ports $BACKEND_PORT and $FRONTEND_PORT are now free."

