@echo off
REM Backtest API Server Startup Script for Windows

echo Starting Backtest API Server...

REM Check if virtual environment exists, if not create it
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Create necessary directories
if not exist "data" mkdir data
if not exist "files" mkdir files

REM Check if database needs initialization
echo Checking database...
if not exist "backtest.db" (
    echo Database will be created on first run...
)

REM Start the server
echo Starting FastAPI server on http://localhost:8000
echo API Documentation will be available at http://localhost:8000/docs
echo Press Ctrl+C to stop the server

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
