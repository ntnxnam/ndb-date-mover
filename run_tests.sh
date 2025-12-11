#!/bin/bash
# Run Tests Before Starting Application

echo "🧪 Running tests..."
echo ""

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if pytest is available
if ! python3 -m pytest --version > /dev/null 2>&1; then
    echo "⚠️  pytest not found. Installing dependencies..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    pip install -q pytest pytest-cov pytest-mock 2>/dev/null || true
fi

# Run tests with pytest
if python3 -m pytest tests/ -v --tb=short 2>&1; then
    echo ""
    echo "✅ All tests passed!"
    return 0 2>/dev/null || exit 0
else
    TEST_EXIT_CODE=$?
    echo ""
    echo "❌ Tests failed! Exit code: $TEST_EXIT_CODE"
    echo "   Please fix issues before starting the application."
    return $TEST_EXIT_CODE 2>/dev/null || exit $TEST_EXIT_CODE
fi

