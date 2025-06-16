#!/bin/bash
# Development startup script for EMS

echo "🔧 EMS Development Environment Setup"
echo "===================================="

# Set development environment
export ENVIRONMENT=development
export MICROSERVICES_MODE=false

# Check Python environment
echo "🐍 Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Start Redis if not running (for development)
if ! pgrep redis-server > /dev/null; then
    echo "🚀 Starting Redis server..."
    if command -v redis-server &> /dev/null; then
        redis-server --daemonize yes
    else
        echo "⚠️  Redis not found. Install Redis or use Docker:"
        echo "   brew install redis  # on macOS"
        echo "   sudo apt install redis-server  # on Ubuntu"
        echo "   docker run -d -p 6379:6379 redis:alpine"
    fi
fi

# Choice of mode
echo ""
echo "🚀 Choose startup mode:"
echo "1) Legacy monolithic mode (default)"
echo "2) Microservices mode (gateway only)"
echo "3) Microservices mode (all services)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    2)
        export MICROSERVICES_MODE=true
        export SERVICE_TYPE=gateway
        echo "🌐 Starting API Gateway..."
        python app.py
        ;;
    3)
        echo "🐳 Starting all microservices with Docker..."
        ./deploy.sh
        ;;
    *)
        echo "🏢 Starting in legacy monolithic mode..."
        python app.py
        ;;
esac
