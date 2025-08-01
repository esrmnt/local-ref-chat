@echo off
REM Quick start script for Reference Chat (Windows)
REM This script starts both backend and frontend services

echo.
echo 🚀 Starting Reference Chat...

REM Check if virtual environment exists
if not exist venv (
    echo ❌ Virtual environment not found. Please run setup-dev.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if Ollama is running
echo.
echo 🤖 Checking Ollama service...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Ollama is not running. Please start Ollama manually with: ollama serve
    echo    Then run this script again.
    pause
    exit /b 1
)

REM Check if required model is available
echo.
echo 🔍 Checking for required model...
ollama list | findstr "llama3" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📥 Pulling llama3 model...
    ollama pull llama3
)

echo ✅ Ollama is ready

REM Create necessary directories
if not exist docs mkdir docs
if not exist logs mkdir logs

REM Start backend in a new window
echo.
echo 🔧 Starting backend API server...
start "Reference Chat Backend" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to start
echo ⏳ Waiting for backend to start...
timeout /t 8 /nobreak >nul

REM Check if backend is ready
echo 🔍 Checking backend status...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Backend may still be starting. Please wait a moment and check http://localhost:8000/health
)

REM Start frontend in a new window
echo.
echo 🎨 Starting frontend UI...
start "Reference Chat Frontend" cmd /k "streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501"

echo.
echo 🎉 Reference Chat is starting!
echo ================================
echo 📊 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo 🎨 Frontend UI: http://localhost:8501
echo.
echo Backend and frontend are running in separate windows.
echo Close those windows to stop the services.
echo.
pause
