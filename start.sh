#!/bin/bash

# TokenWise Startup Script

echo "🚀 Starting TokenWise API..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env and add your OPENAI_API_KEY"
    exit 1
fi

# Check if OPENAI_API_KEY is set
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "❌ Error: OPENAI_API_KEY not configured in .env"
    echo "📝 Please edit .env and add your OpenAI API key"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create necessary directories
mkdir -p chroma_db

# Start the server
echo "✨ Starting TokenWise API on http://localhost:8000"
echo "📖 API docs available at http://localhost:8000/docs"
echo ""
python main.py

