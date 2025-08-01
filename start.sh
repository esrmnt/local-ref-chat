#!/bin/bash

# Quick start script for Reference Chat
# This script starts both backend and frontend services

set -e

echo "🚀 Starting Reference Chat..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup-dev.sh first."
    exit 1
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Check if Ollama is running
echo "🤖 Checking Ollama service..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running. Starting Ollama..."
    if command -v ollama &> /dev/null; then
        echo "Starting Ollama in background..."
        ollama serve &
        sleep 5
    else
        echo "❌ Ollama is not installed. Please install it from https://ollama.ai/"
        exit 1
    fi
fi

# Check if required model is available
echo "🔍 Checking for required model..."
if ! ollama list | grep -q "llama3"; then
    echo "📥 Pulling llama3 model..."
    ollama pull llama3
fi

echo "✅ Ollama is ready"

# Create necessary directories
mkdir -p docs logs

# Function to cleanup background processes
cleanup() {
    echo "🛑 Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start backend
echo "🔧 Starting backend API server..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is ready
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ Backend failed to start"
        cleanup
        exit 1
    fi
    sleep 2
done

# Start frontend
echo "🎨 Starting frontend UI..."
streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501 &
FRONTEND_PID=$!

echo ""
echo "🎉 Reference Chat is running!"
echo "================================"
echo "📊 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🎨 Frontend UI: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user to stop
wait
