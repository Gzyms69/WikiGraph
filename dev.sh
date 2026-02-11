#!/bin/bash

# WikiGraph Development Control Script
# Usage: ./dev.sh [start|stop|restart|status] [target]

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKEND_PORT=8000
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
PYTHON_BIN="python3"

# Determine Python Binary (venv priority)
if [ -f "$PROJECT_ROOT/venv/bin/python3" ]; then
    PYTHON_BIN="$PROJECT_ROOT/venv/bin/python3"
fi

function manage_containers() {
    PYTHONPATH="$PROJECT_ROOT" "$PYTHON_BIN" "$PROJECT_ROOT/tools/ops/manage_containers.py" "$@"
}

function start_backend() {
    echo -e "${BLUE}🚀 Starting Backend (FastAPI)...${NC}"
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        echo -e "${GREEN}✅ Backend is already running (PID: $(pgrep -f "uvicorn app.main:app")).${NC}"
    else
        # Use venv uvicorn if available
        UVICORN_BIN="uvicorn"
        if [ -f "$PROJECT_ROOT/venv/bin/uvicorn" ]; then
            UVICORN_BIN="$PROJECT_ROOT/venv/bin/uvicorn"
        fi
        
        nohup "$UVICORN_BIN" app.main:app --host 0.0.0.0 --port $BACKEND_PORT > "$BACKEND_LOG" 2>&1 &
        local pid=$!
        echo -e "${GREEN}✅ Backend started (PID: $pid). Logs: $BACKEND_LOG${NC}"
        
        # Health Check Loop
        echo -n "   Waiting for API to be healthy..."
        for i in {1..10}; do
            if curl -s "http://localhost:$BACKEND_PORT/api/v1/health" | grep -q "status"; then
                echo -e " ${GREEN}OK${NC}"
                return
            fi
            echo -n "."
            sleep 1
        done
        echo -e " ${YELLOW}Backend started but health check timed out. Check logs.${NC}"
    fi
}

function start_frontend() {
    echo -e "${BLUE}🚀 Starting Frontend (Next.js)...${NC}"
    
    # Check for node_modules
    if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
        echo -e "${YELLOW}📦 node_modules not found. Installing dependencies...${NC}"
        cd "$PROJECT_ROOT/frontend" && npm install
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ npm install failed. Frontend cannot start.${NC}"
            return 1
        fi
        cd "$PROJECT_ROOT"
    fi

    if pgrep -f "next-server" > /dev/null || pgrep -f "next dev" > /dev/null; then
        echo -e "${GREEN}✅ Frontend is already running.${NC}"
    else
        # CRITICAL: Enforce memory limit to prevent system crash (OOM)
        # 2GB limit is sufficient for dev; crash happened at 32GB+ due to infinite build loop.
        export NODE_OPTIONS="--max-old-space-size=2048"
        
        cd "$PROJECT_ROOT/frontend" && nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
        local pid=$!
        echo -e "${GREEN}✅ Frontend started (PID: $pid). Logs: $FRONTEND_LOG${NC}"
        
        # Health Check
        echo -n "   Waiting for Frontend to be ready..."
        for i in {1..30}; do
            if curl -s "http://localhost:3000" > /dev/null; then
                echo -e " ${GREEN}OK${NC}"
                return
            fi
            # Check if process died immediately
            if ! kill -0 $pid 2>/dev/null; then
                 echo -e "\n${RED}❌ Frontend process died immediately. Check logs.${NC}"
                 tail -n 10 "$FRONTEND_LOG"
                 return 1
            fi
            echo -n "."
            sleep 1
        done
        echo -e " ${YELLOW}Frontend started but health check timed out. Check logs.${NC}"
    fi
}

function stop_backend() {
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        pkill -f "uvicorn app.main:app"
        echo -e "${GREEN}✅ Backend stopped.${NC}"
    else
        echo -e "${YELLOW}Backend was not running.${NC}"
    fi
}

function stop_frontend() {
    # Kill Next.js development server
    if pgrep -f "next-server" > /dev/null || pgrep -f "next dev" > /dev/null || pgrep -f "next start" > /dev/null; then
         echo -e "${BLUE}🛑 Stopping Frontend...${NC}"
         pkill -f "next-server"
         pkill -f "next dev"
         pkill -f "next start"
         echo -e "${GREEN}✅ Frontend stopped.${NC}"
    else
         echo -e "${YELLOW}Frontend was not running.${NC}"
    fi
}

function stop_pipelines() {
    # Kill any running ingestion pipelines
    if pgrep -f "core/pipeline" > /dev/null; then
        echo -e "${BLUE}🛑 Stopping Pipeline Scripts...${NC}"
        pkill -f "core/pipeline"
        echo -e "${GREEN}✅ Pipeline scripts stopped.${NC}"
    fi
}

CMD=$1
ARG=$2

case "$CMD" in
    start)
        if [ -z "$ARG" ]; then
            echo "Usage: ./dev.sh start {pl|de|es|backend|frontend|all}"
            exit 1
        fi
        
        if [ "$ARG" == "backend" ]; then
            start_backend
        elif [ "$ARG" == "frontend" ]; then
            start_frontend
        elif [ "$ARG" == "all" ]; then
            manage_containers start all
            start_backend
            start_frontend
        else
            manage_containers start "$ARG"
        fi
        ;;
        
    stop)
        if [ -z "$ARG" ]; then
            echo "Usage: ./dev.sh stop {pl|de|es|backend|frontend|all}"
            exit 1
        fi
        
        if [ "$ARG" == "backend" ]; then
            stop_backend
        elif [ "$ARG" == "frontend" ]; then
            stop_frontend
        elif [ "$ARG" == "all" ]; then
            manage_containers stop all
            stop_backend
            stop_frontend
            stop_pipelines
        else
            manage_containers stop "$ARG"
        fi
        ;;
        
    restart)
        if [ -z "$ARG" ]; then
             echo "Usage: ./dev.sh restart {pl|de|es|backend|frontend}"
             exit 1
        fi
        
        if [ "$ARG" == "backend" ]; then
            stop_backend
            sleep 1
            start_backend
        elif [ "$ARG" == "frontend" ]; then
            stop_frontend
            sleep 1
            start_frontend
        else
            manage_containers restart "$ARG"
        fi
        ;;
        
    status)
        manage_containers status
        echo -e "\n${BLUE}=== Backend Status ===${NC}"
        if pgrep -f "uvicorn app.main:app" > /dev/null; then
            echo -e "${GREEN}Running${NC} (PID: $(pgrep -f "uvicorn app.main:app"))"
        else
            echo -e "${RED}Stopped${NC}"
        fi
        
        echo -e "\n${BLUE}=== Frontend Status ===${NC}"
        if pgrep -f "next dev" > /dev/null || pgrep -f "next start" > /dev/null || pgrep -f "next-server" > /dev/null; then
             echo -e "${GREEN}Running${NC}"
        else
             echo -e "${RED}Stopped${NC}"
        fi
        ;;
        
    *)
        echo "Usage: ./dev.sh {start|stop|restart|status} [target]"
        exit 1
        ;; 
esac
