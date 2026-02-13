#!/bin/bash
# WikiGraph Environment Setup Script
# "Zero to Hero" initialization for fresh clones.

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting WikiGraph Environment Setup...${NC}"

# 1. Python Environment
echo -e "
${BLUE}[1/4] Setting up Python Environment...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed.${NC}"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo -e "   Creating virtual environment (venv)..."
    python3 -m venv venv
else
    echo -e "   Virtual environment already exists."
fi

source venv/bin/activate
echo -e "   Installing dependencies from requirements.txt..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt
echo -e "${GREEN}✅ Python setup complete.${NC}"

# 2. Node.js Environment
echo -e "
${BLUE}[2/4] Setting up Frontend (Node.js)...${NC}"
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed. Please install Node.js.${NC}"
    exit 1
fi

if [ -d "frontend" ]; then
    cd frontend
    echo -e "   Installing frontend dependencies (npm install)..."
    # Use ci for cleaner installs if package-lock exists, else install
    if [ -f "package-lock.json" ]; then
        npm ci --silent
    else
        npm install --silent
    fi
    cd ..
    echo -e "${GREEN}✅ Frontend setup complete.${NC}"
else
    echo -e "${YELLOW}⚠️ 'frontend' directory not found. Skipping.${NC}"
fi

# 3. Environment Variables
echo -e "
${BLUE}[3/4] Configuring Environment Variables...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env from .env.example${NC}"
        echo -e "${YELLOW}👉 Please edit .env to add your GEMINI_API_KEY!${NC}"
    else
        echo -e "${RED}❌ .env.example not found.${NC}"
    fi
else
    echo -e "   .env already exists."
fi

# 4. Docker Check
echo -e "
${BLUE}[4/4] Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️ Docker is not installed. You will need it for the Graph Database.${NC}"
else
    echo -e "${GREEN}✅ Docker is ready.${NC}"
fi

echo -e "
${GREEN}✨ Setup Complete!${NC}"
echo -e "To start the development environment:"
echo -e "   ./dev.sh start all"
