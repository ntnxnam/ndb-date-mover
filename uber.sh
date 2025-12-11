#!/bin/bash
# Uber Script: Complete Control for JIRA Connection App
# Usage: ./uber.sh [start|stop|restart|status]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

BACKEND_PORT=8473
FRONTEND_PORT=6291

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if servers are running
check_status() {
    echo -e "${BLUE}📊 Server Status:${NC}"
    echo ""
    
    BACKEND_PIDS=$(lsof -ti:$BACKEND_PORT 2>/dev/null)
    if [ -n "$BACKEND_PIDS" ]; then
        echo -e "   ${GREEN}✅ Backend${NC}  - Running on port $BACKEND_PORT (PID: $BACKEND_PIDS)"
    else
        echo -e "   ${RED}❌ Backend${NC}  - Not running on port $BACKEND_PORT"
    fi
    
    FRONTEND_PIDS=$(lsof -ti:$FRONTEND_PORT 2>/dev/null)
    if [ -n "$FRONTEND_PIDS" ]; then
        echo -e "   ${GREEN}✅ Frontend${NC} - Running on port $FRONTEND_PORT (PID: $FRONTEND_PIDS)"
    else
        echo -e "   ${RED}❌ Frontend${NC} - Not running on port $FRONTEND_PORT"
    fi
    echo ""
}

# Function to stop servers
stop_servers() {
    echo -e "${YELLOW}🛑 Stopping servers...${NC}"
    echo ""
    ./kill_servers.sh
}

# Function to start servers
start_servers() {
    echo -e "${GREEN}🚀 Starting servers...${NC}"
    echo ""
    ./start_all.sh
}

# Function to start with tests
start_with_tests() {
    echo -e "${BLUE}🧪 Starting with tests and self-healing...${NC}"
    echo ""
    ./start_with_tests.sh
}

# Function to restart servers
restart_servers() {
    echo -e "${BLUE}🔄 Restarting servers...${NC}"
    echo ""
    
    # Step 1: Run tests
    echo -e "${YELLOW}Step 1: Running tests...${NC}"
    if ./run_tests.sh; then
        echo -e "${GREEN}✅ Tests passed!${NC}"
    else
        echo -e "${YELLOW}⚠️  Tests failed, but continuing with restart...${NC}"
        echo ""
    fi
    
    # Step 2: Stop servers
    stop_servers
    sleep 2
    
    # Step 3: Start servers
    start_servers
}

# Main script logic
case "${1:-}" in
    start)
        start_servers
        ;;
    stop)
        stop_servers
        ;;
    restart)
        restart_servers
        ;;
    status)
        check_status
        ;;
    test)
        start_with_tests
        ;;
    *)
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BLUE}  JIRA Connection App - Control Script${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo "Usage: ./uber.sh [command]"
        echo ""
        echo "Commands:"
        echo -e "  ${GREEN}start${NC}       - Start backend and frontend servers"
        echo -e "  ${RED}stop${NC}        - Stop all running servers"
        echo -e "  ${BLUE}restart${NC}     - Stop and start servers (recommended)"
        echo -e "  ${BLUE}test${NC}        - Run tests and start servers with self-healing"
        echo -e "  ${YELLOW}status${NC}      - Check server status"
        echo ""
        check_status
        echo "Examples:"
        echo "  ./uber.sh test       # Run tests and start (recommended)"
        echo "  ./uber.sh restart    # Kill and restart everything"
        echo "  ./uber.sh stop       # Stop all servers"
        echo "  ./uber.sh start      # Start servers"
        echo "  ./uber.sh status     # Check what's running"
        echo ""
        ;;
esac

