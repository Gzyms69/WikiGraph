# WikiGraph Development Control Script
# Usage: ./dev.sh [start|stop|restart|status|links] [target]

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
RUN_DIR="$PROJECT_ROOT/.run"
mkdir -p "$LOG_DIR" "$RUN_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKEND_PORT=8000
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
PYTHON_BIN="python3"

# Determine Python Binary (venv priority)
if [ -f "$PROJECT_ROOT/venv/bin/python3" ]; then
    PYTHON_BIN="$PROJECT_ROOT/venv/bin/python3"
fi

function manage_containers() {
    PYTHONPATH="$PROJECT_ROOT" "$PYTHON_BIN" "$PROJECT_ROOT/tools/ops/manage_containers.py" "$@"
}

function stop_process_by_file() {
    local pid_file=$1
    local name=$2
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${BLUE}🛑 Stopping $name (PID: $pid)...${NC}"
            # Kill the process group to ensure children are gone
            kill -TERM -$pid 2>/dev/null || kill -TERM $pid 2>/dev/null
            
            # Wait and check
            for i in {1..5}; do
                if ! kill -0 $pid 2>/dev/null; then
                    echo -e "${GREEN}✅ $name stopped.${NC}"
                    rm "$pid_file"
                    return 0
                fi
                sleep 1
            done
            
            echo -e "${YELLOW}⚠️ $name did not stop gracefully. Forcing...${NC}"
            kill -KILL -$pid 2>/dev/null || kill -KILL $pid 2>/dev/null
            sleep 1
        fi
        rm "$pid_file"
        echo -e "${GREEN}✅ $name stopped.${NC}"
    else
        # Fallback to pgrep if PID file is missing
        local pattern=$3
        if [ ! -z "$pattern" ] && pgrep -f "$pattern" > /dev/null; then
            echo -e "${BLUE}🛑 Stopping $name (via pgrep)...${NC}"
            pkill -f "$pattern"
            echo -e "${GREEN}✅ $name stopped.${NC}"
        fi
    fi
}

function start_backend() {
    echo -e "${BLUE}🚀 Starting Backend (FastAPI)...${NC}"
    if [ -f "$BACKEND_PID_FILE" ] && kill -0 $(cat "$BACKEND_PID_FILE") 2>/dev/null; then
        echo -e "${GREEN}✅ Backend is already running (PID: $(cat "$BACKEND_PID_FILE")).${NC}"
    else
        UVICORN_BIN="uvicorn"
        [ -f "$PROJECT_ROOT/venv/bin/uvicorn" ] && UVICORN_BIN="$PROJECT_ROOT/venv/bin/uvicorn"
        
        # Start in a new process group to allow killing children
        setsid "$UVICORN_BIN" app.main:app --host 0.0.0.0 --port $BACKEND_PORT > "$BACKEND_LOG" 2>&1 &
        local pid=$!
        echo $pid > "$BACKEND_PID_FILE"
        echo -e "${GREEN}✅ Backend started (PID: $pid). Logs: $BACKEND_LOG${NC}"
        
        # Health Check
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
    
    if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
        echo -e "${YELLOW}📦 node_modules not found. Installing...${NC}"
        (cd "$PROJECT_ROOT/frontend" && npm install)
    fi

    if [ -f "$FRONTEND_PID_FILE" ] && kill -0 $(cat "$FRONTEND_PID_FILE") 2>/dev/null; then
        echo -e "${GREEN}✅ Frontend is already running.${NC}"
    else
        export NODE_OPTIONS="--max-old-space-size=2048"
        cd "$PROJECT_ROOT/frontend"
        setsid npm run dev > "$FRONTEND_LOG" 2>&1 &
        local pid=$!
        echo $pid > "$FRONTEND_PID_FILE"
        cd "$PROJECT_ROOT"
        echo -e "${GREEN}✅ Frontend started (PID: $pid). Logs: $FRONTEND_LOG${NC}"
        
        # Health Check
        echo -n "   Waiting for Frontend..."
        for i in {1..30}; do
            if curl -s "http://localhost:3000" > /dev/null; then
                echo -e " ${GREEN}OK${NC}"
                return
            fi
            if ! kill -0 $pid 2>/dev/null; then
                 echo -e "\n${RED}❌ Frontend process died immediately.${NC}"
                 tail -n 10 "$FRONTEND_LOG"
                 return 1
            fi
            echo -n "."
            sleep 1
        done
        echo -e " ${YELLOW}Frontend timeout. Check logs.${NC}"
    fi
}

function stop_pipelines() {
    if pgrep -f "core/pipeline" > /dev/null; then
        echo -e "${BLUE}🛑 Stopping Pipelines...${NC}"
        pkill -f "core/pipeline"
    fi
}

function print_links() {
    echo -e "\n${BLUE}=== 🌐 WikiGraph Service Links ===${NC}"
    
    # 1. Frontend
    if curl -s "http://localhost:3000" > /dev/null; then
        echo -e "${YELLOW}Frontend App:${NC}       ${GREEN}http://localhost:3000${NC}"
    else
        echo -e "${YELLOW}Frontend App:${NC}       ${RED}Not running${NC}"
    fi

    # 2. Backend
    if curl -s "http://localhost:$BACKEND_PORT/api/v1/health" | grep -q "status"; then
        echo -e "${YELLOW}Backend API:${NC}        ${GREEN}http://localhost:$BACKEND_PORT${NC}"
        echo -e "${YELLOW}API Docs:${NC}           ${GREEN}http://localhost:$BACKEND_PORT/docs${NC}"
    else
        echo -e "${YELLOW}Backend API:${NC}        ${RED}Not running${NC}"
    fi

    # 3. Neo4j
    echo -e "${YELLOW}Graph Databases (Neo4j):${NC}"
    local containers=$(docker ps --format "{{.Names}} {{.Ports}}" --filter "name=wikigraph-neo4j")
    if [ -z "$containers" ]; then
        echo -e "  - ${RED}No active Neo4j containers found.${NC}"
    else
        echo "$containers" | while read name ports; do
            lang=${name#wikigraph-neo4j-}
            http_port=$(echo "$ports" | sed -n 's/.*0\.0\.0\.0:\([0-9]*\)->7474.*/\1/p')
            if [ ! -z "$http_port" ]; then
                echo -e "  - Neo4j ($lang):    ${GREEN}http://localhost:$http_port${NC}"
            else
                echo -e "  - Neo4j ($lang):    Running (Port hidden)"
            fi
        done
    fi
    echo -e "${BLUE}==================================${NC}\n"
}

CMD=$1
ARG=$2

case "$CMD" in
    start)
        [ -z "$ARG" ] && echo "Usage: ./dev.sh start {lang|all|backend|frontend}" && exit 1
        
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
            start_backend
            start_frontend
        fi
        print_links
        ;;
        
    stop)
        [ -z "$ARG" ] && echo "Usage: ./dev.sh stop {lang|all|backend|frontend}" && exit 1
        
        if [ "$ARG" == "backend" ]; then
            stop_process_by_file "$BACKEND_PID_FILE" "Backend" "uvicorn app.main:app"
        elif [ "$ARG" == "frontend" ]; then
            stop_process_by_file "$FRONTEND_PID_FILE" "Frontend" "next dev|next-server"
        elif [ "$ARG" == "all" ]; then
            stop_process_by_file "$BACKEND_PID_FILE" "Backend" "uvicorn app.main:app"
            stop_process_by_file "$FRONTEND_PID_FILE" "Frontend" "next dev|next-server"
            stop_pipelines
            manage_containers stop all
            # Final cleanup of any orphaned node/python processes in this context
            pkill -f "next-server|next dev"
            pkill -f "uvicorn app.main:app"
        else
            manage_containers stop "$ARG"
        fi
        ;;
        
    restart)
        [ -z "$ARG" ] && echo "Usage: ./dev.sh restart {lang|backend|frontend}" && exit 1
        "$0" stop "$ARG"
        sleep 1
        "$0" start "$ARG"
        ;;
        
    status)
        manage_containers status
        echo -e "\n${BLUE}=== Backend Status ===${NC}"
        [ -f "$BACKEND_PID_FILE" ] && kill -0 $(cat "$BACKEND_PID_FILE") 2>/dev/null && echo -e "${GREEN}Running${NC}" || echo -e "${RED}Stopped${NC}"
        
        echo -e "\n${BLUE}=== Frontend Status ===${NC}"
        [ -f "$FRONTEND_PID_FILE" ] && kill -0 $(cat "$FRONTEND_PID_FILE") 2>/dev/null && echo -e "${GREEN}Running${NC}" || echo -e "${RED}Stopped${NC}"
        print_links
        ;;

    links)
        print_links
        ;;
        
    *)
        echo "Usage: ./dev.sh {start|stop|restart|status|links} [target]"
        exit 1
        ;; 
esac
