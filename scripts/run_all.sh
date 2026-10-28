#!/usr/bin/env bash
set -e

# AO-03 Root Cause Evidence Engine: Unified Startup Script
echo "=================================================="
echo " Starting AO-03 Root Cause Evidence Engine"
echo "=================================================="

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

# Load telemetry to MongoDB if running
echo "Checking telemetry data in MongoDB..."
.venv/bin/python scripts/load_to_mongo.py || echo "MongoDB not available; continuing in JSONL file mode."

# Start backend Django REST API
echo "Starting backend API server on http://localhost:8000 ..."
.venv/bin/uvicorn config.asgi:application --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!

# Trap signals to terminate child processes
cleanup() {
    echo "Stopping servers..."
    kill "$BACKEND_PID" 2>/dev/null || true
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Start frontend if node_modules exists
if [ -d "frontend" ]; then
    echo "Starting React Vite frontend on http://localhost:5173 ..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    npm run dev &
    FRONTEND_PID=$!
    cd ..
fi

echo ""
echo "AO-03 Engine running!"
echo "Backend API:  http://localhost:8000 (endpoints: /health, /scenarios, /analyze/{id}, /evaluate)"
echo "Frontend UI:  http://localhost:5173"
echo "Press Ctrl+C to stop."
echo ""

wait
