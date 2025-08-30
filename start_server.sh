#!/bin/bash

# Backtest API Server Startup Script

echo "Starting Backtest API Server..."

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p data
mkdir -p files

# Check if database needs initialization
echo "Checking database..."
if [ ! -f "backtest.db" ]; then
    echo "Database will be created on first run..."
fi

# Start the server
echo "Starting FastAPI server on http://localhost:8000"
echo "API Documentation will be available at http://localhost:8000/docs"
echo "Press Ctrl+C to stop the server"

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
