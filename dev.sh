#!/bin/bash

# WikiGraph Development Control Script
# Usage: ./dev.sh [start|stop|status|restart]

FRONTEND_PORT=3000
BACKEND_PORT=8000
NEO4J_PORT=7687

# Text Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function check_neo4j() {
    if docker ps | grep -q "neo4j"; then
        return 0
    else
        return 1
    fi
}

function start() {
    echo -e "${BLUE}🚀 Starting WikiGraph Lab Environment...${NC}"

    # 1. Start Neo4j if not running
    if ! check_neo4j; then
        echo -e "${YELLOW}📦 Starting Neo4j Container...${NC}"
        ./start_services.sh
        sleep 5
    else
        echo -e "${GREEN}✅ Neo4j is already running.${NC}"
    fi

    # 2. Start Backend API
    if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}✅ Backend API is already running on port $BACKEND_PORT.${NC}"
    else
        echo -e "${YELLOW}🧠 Starting FastAPI Backend...${NC}"
        nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > logs/api_dev.log 2>&1 &
        echo $! > .backend.pid
    fi

    # 3. Start Frontend
    if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}✅ Frontend is already running on port $FRONTEND_PORT.${NC}"
    else
        echo -e "${YELLOW}🌌 Starting Next.js Frontend...${NC}"
        cd frontend && nohup npm run dev -- -p $FRONTEND_PORT > ../logs/frontend_dev.log 2>&1 &
        echo $! > ../.frontend.pid
        cd ..
    fi

    echo -e "${GREEN}==================================================${NC}"
    echo -e "${GREEN}✨ Environment Ready!${NC}"
    echo -e "🔗 Frontend: ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "🔗 API Docs: ${BLUE}http://localhost:$BACKEND_PORT/docs${NC}"
    echo -e "${GREEN}==================================================${NC}"
    echo -e "Logs are available in the ${YELLOW}logs/${NC} directory."
}

function stop() {
    echo -e "${RED}🛑 Stopping WikiGraph Lab...${NC}"
    
    # Stop Frontend
    if [ -f .frontend.pid ]; then
        PID=$(cat .frontend.pid)
        kill $PID 2>/dev/null || true
        rm .frontend.pid
        echo -e "Frontend stopped."
    fi
    # Also kill by port just in case
    fuser -k $FRONTEND_PORT/tcp 2>/dev/null || true

    # Stop Backend
    if [ -f .backend.pid ]; then
        PID=$(cat .backend.pid)
        kill $PID 2>/dev/null || true
        rm .backend.pid
        echo -e "Backend stopped."
    fi
    fuser -k $BACKEND_PORT/tcp 2>/dev/null || true

    echo -e "${GREEN}All local processes stopped.${NC}"
    echo -e "${YELLOW}Note: Neo4j Docker container is still running. Use 'docker stop neo4j' if you want to kill it too.${NC}"
}

function status() {
    echo -e "${BLUE}📊 System Status:${NC}"
    
    if check_neo4j; then
        echo -e "Neo4j:    ${GREEN}RUNNING${NC}"
    else
        echo -e "Neo4j:    ${RED}STOPPED${NC}"
    fi

    if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null ; then
        echo -e "Backend:  ${GREEN}RUNNING${NC} (Port $BACKEND_PORT)"
    else
        echo -e "Backend:  ${RED}STOPPED${NC}"
    fi

    if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null ; then
        echo -e "Frontend: ${GREEN}RUNNING${NC} (Port $FRONTEND_PORT)"
    else
        echo -e "Frontend: ${RED}STOPPED${NC}"
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    restart)
        stop
        start
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
esac
