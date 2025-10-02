#!/bin/bash

# Start the AI Pre-Deployment Assistant UI
# This script activates the virtual environment and starts the Streamlit UI

set -e

echo "🤖 Starting AI Pre-Deployment Assistant UI..."
echo ""

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    cd backend
    python -m venv venv
    cd ..
fi

# Activate virtual environment
source backend/venv/bin/activate

# Check if requirements are installed
echo "Checking dependencies..."
if ! python -c "import streamlit" &> /dev/null; then
    echo "⚠️  Dependencies not found. Installing from requirements.txt..."
    pip install -r backend/requirements.txt
    echo "✅ Dependencies installed"
    echo ""
fi

# Check if FastAPI backend is running
echo "Checking if FastAPI backend is running..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Warning: FastAPI backend is not running on http://localhost:8000"
    echo "Please start it in another terminal: ./run_api.sh"
    echo ""
fi

# Start Streamlit
echo "Starting Streamlit UI on http://localhost:8501..."
echo ""

# Disable Streamlit's email collection prompt on first run
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

streamlit run ui/app.py --server.headless true
