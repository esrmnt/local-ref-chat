@echo off
REM Development setup script for Reference Chat (Windows)
REM This script helps set up the development environment on Windows

echo.
echo 🚀 Setting up Reference Chat development environment...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH. Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

echo ✅ Python is available
python --version

REM Create virtual environment
echo.
echo 📦 Creating virtual environment...
if not exist venv (
    python -m venv venv
    echo ✅ Virtual environment created successfully
) else (
    echo ⚠️  Virtual environment already exists
)

REM Activate virtual environment
echo.
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo 📈 Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo 📥 Installing Python dependencies...
pip install -r requirements.txt

REM Install development tools
echo.
echo 🛠️  Installing development tools...
pip install pytest pytest-asyncio black flake8 mypy

REM Create .env file if it doesn't exist
echo.
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please review and update .env file with your preferences
) else (
    echo ⚠️  .env file already exists
)

REM Create necessary directories
echo.
echo 📁 Creating necessary directories...
if not exist docs mkdir docs
if not exist logs mkdir logs

REM Download NLTK data
echo.
echo 📚 Downloading NLTK data...
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True); print('NLTK data downloaded successfully')"

REM Check if Ollama is available
echo.
echo 🤖 Checking Ollama availability...
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama is installed
    
    REM Check if Ollama is running
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Ollama service is running
        echo.
        echo 📋 Available Ollama models:
        ollama list
    ) else (
        echo ⚠️  Ollama is installed but not running. Start it with: ollama serve
    )
) else (
    echo ⚠️  Ollama is not installed. Please install it from https://ollama.ai/
    echo    After installation, run: ollama pull llama3
)

REM Run tests to verify setup
echo.
echo 🧪 Running tests to verify setup...
python -m pytest tests/ -v --tb=short
if %errorlevel% equ 0 (
    echo ✅ All tests passed! Setup completed successfully.
) else (
    echo ⚠️  Some tests failed. The setup is mostly complete, but you may need to troubleshoot.
)

REM Summary
echo.
echo 📋 Setup Summary:
echo ==================
echo ✅ Python environment: Ready
echo ✅ Dependencies: Installed
echo ✅ Configuration: Created
echo ✅ Directories: Created
echo.
echo 🚀 Next steps:
echo 1. Review .env file and adjust settings if needed
echo 2. Ensure Ollama is installed and running
echo 3. Pull an Ollama model: ollama pull llama3
echo 4. Start the backend: python -m uvicorn backend.main:app --reload
echo 5. Start the frontend: streamlit run frontend/app.py
echo.
echo 📚 Documentation: http://localhost:8000/docs (when backend is running)
echo 🎨 Frontend: http://localhost:8501 (when frontend is running)
echo.
echo ✅ Development environment setup complete! 🎉
echo.
pause
