#!/bin/bash
# Start Application with Tests and Self-Healing

echo "🚀 Starting JIRA Connection Application with Tests..."
echo ""

cd "$(dirname "$0")"

# Step 1: Run tests
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Running tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ! ./run_tests.sh; then
    echo ""
    echo "⚠️  Tests failed, but continuing anyway..."
    echo "   Fix test issues before deploying to production."
    echo ""
    read -p "Press Enter to continue or Ctrl+C to abort..."
fi

# Step 2: Kill existing servers
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Stopping existing servers..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
./kill_servers.sh

# Step 3: Start servers with self-healing
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Starting servers with self-healing..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
./start_all.sh

