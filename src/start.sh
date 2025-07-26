#!/bin/bash

# SiteWatch Full-Stack Startup Script

echo "🚀 Starting SiteWatch Full-Stack Application"
echo "=============================================="

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: OPENAI_API_KEY environment variable not set."
    echo "   Some AI features will be limited without an OpenAI API key."
    echo "   To enable full functionality, set your OpenAI API key:"
    echo "   export OPENAI_API_KEY='your-api-key-here'"
    echo ""
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is required but not installed."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Start backend
echo "🔧 Starting backend..."
cd backend

# Install Python dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

echo "🚀 Starting backend server on http://localhost:8081"
# Use absolute path to python in venv to ensure it uses the right environment
# Redirect output to log files for debugging
./venv/bin/python run.py > backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment and check if backend started successfully
sleep 3
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend started successfully (PID: $BACKEND_PID)"
else
    echo "❌ Backend failed to start. Check backend.log for errors."
    cat backend.log
fi

cd ..

# Start frontend
echo "🔧 Starting frontend..."
cd frontend

# Install npm dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

echo "🚀 Starting frontend server on http://localhost:3000"
npm start > frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait a moment and check if frontend started successfully
sleep 5
if ps -p $FRONTEND_PID > /dev/null; then
    echo "✅ Frontend started successfully (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend failed to start. Check frontend.log for errors."
    cat frontend.log | tail -20
fi

cd ..

echo ""
echo "🎉 SiteWatch is starting up!"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8081"
echo "   API Docs: http://localhost:8081/docs"
echo ""
echo "💬 Try asking: 'Monitor AI startup job postings'"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait 