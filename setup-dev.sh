#!/bin/bash

# Development setup script for Reference Chat
# This script helps set up the development environment

set -e  # Exit on any error

echo "🚀 Setting up Reference Chat development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
print_status "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    print_error "Python is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
print_status "Found Python $PYTHON_VERSION"

# Check if Python version is 3.8+
if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_error "Python 3.8+ is required. Please upgrade Python and try again."
    exit 1
fi

# Create virtual environment
print_status "Creating virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    print_status "Virtual environment created successfully"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Install development dependencies if they exist
if [ -f "requirements-dev.txt" ]; then
    print_status "Installing development dependencies..."
    pip install -r requirements-dev.txt
else
    print_status "Installing common development tools..."
    pip install pytest pytest-asyncio black flake8 mypy
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    print_warning "Please review and update .env file with your preferences"
else
    print_warning ".env file already exists"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p docs logs

# Download NLTK data
print_status "Downloading NLTK data..."
$PYTHON_CMD -c "
import nltk
try:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    print('NLTK data downloaded successfully')
except Exception as e:
    print(f'Warning: Failed to download NLTK data: {e}')
"

# Check if Ollama is available
print_status "Checking Ollama availability..."
if command -v ollama &> /dev/null; then
    print_status "Ollama is installed"
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_status "Ollama service is running"
        
        # List available models
        print_status "Available Ollama models:"
        ollama list
    else
        print_warning "Ollama is installed but not running. Start it with: ollama serve"
    fi
else
    print_warning "Ollama is not installed. Please install it from https://ollama.ai/"
    print_warning "After installation, run: ollama pull llama3"
fi

# Run tests to verify setup
print_status "Running tests to verify setup..."
if python -m pytest tests/ -v --tb=short; then
    print_status "✅ All tests passed! Setup completed successfully."
else
    print_warning "⚠️  Some tests failed. The setup is mostly complete, but you may need to troubleshoot."
fi

# Summary
echo ""
echo "📋 Setup Summary:"
echo "=================="
echo "✅ Python environment: Ready"
echo "✅ Dependencies: Installed"
echo "✅ Configuration: Created"
echo "✅ Directories: Created"
echo ""
echo "🚀 Next steps:"
echo "1. Review .env file and adjust settings if needed"
echo "2. Ensure Ollama is installed and running"
echo "3. Pull an Ollama model: ollama pull llama3"
echo "4. Start the backend: python -m uvicorn backend.main:app --reload"
echo "5. Start the frontend: streamlit run frontend/app.py"
echo ""
echo "📚 Documentation: http://localhost:8000/docs (when backend is running)"
echo "🎨 Frontend: http://localhost:8501 (when frontend is running)"
echo ""
print_status "Development environment setup complete! 🎉"
