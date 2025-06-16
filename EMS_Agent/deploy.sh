#!/bin/bash
# EMS Microservices Deployment Script

set -e

echo "🚀 Starting EMS Microservices Deployment"
echo "========================================"

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Default values
ENVIRONMENT=${ENVIRONMENT:-development}
MONGODB_URI=${MONGODB_URI:-"mongodb+srv://aashik1701:Sustainabyte@cluster20526.g4udhpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster20526"}
MONGODB_DATABASE=${MONGODB_DATABASE:-"EMS_Database"}

echo "📋 Configuration:"
echo "   Environment: $ENVIRONMENT"
echo "   Database: $MONGODB_DATABASE"
echo ""

# Function to check if service is healthy
check_service_health() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be healthy..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
            echo "✅ $service_name is healthy"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - waiting..."
        sleep 5
        ((attempt++))
    done
    
    echo "❌ $service_name failed to start properly"
    return 1
}

# Stop existing services
echo "🛑 Stopping existing services..."
docker-compose down --remove-orphans

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up -d --build

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check Redis
if ! docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not responding"
    exit 1
fi
echo "✅ Redis is healthy"

# Check individual services
check_service_health "Data Ingestion" 8001
check_service_health "Analytics" 8002
check_service_health "Gateway" 8000

# Run data ingestion if specified
if [ "$1" = "--load-data" ]; then
    echo "📊 Loading sample data..."
    # This would trigger data loading via API
    curl -X POST "http://localhost:8000/api/v1/data/ingest/excel" \
         -H "Content-Type: application/json" \
         -d '{"file_path": "EMS_Energy_Meter_Data.xlsx"}' \
         || echo "⚠️  Data loading failed or no data file found"
fi

echo ""
echo "🎉 EMS Microservices Deployment Complete!"
echo "========================================"
echo ""
echo "📋 Service URLs:"
echo "   🌐 API Gateway:      http://localhost:8000"
echo "   📊 Data Ingestion:   http://localhost:8001"
echo "   🧠 Analytics:        http://localhost:8002"
echo "   💾 Redis:            localhost:6379"
echo ""
echo "📊 Monitoring:"
echo "   📈 Prometheus:       http://localhost:9090"
echo "   📊 Grafana:          http://localhost:3000"
echo ""
echo "🔍 Health Check:"
echo "   curl http://localhost:8000/health"
echo ""
echo "📚 API Documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "🏁 Deployment completed successfully!"
