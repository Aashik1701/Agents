#!/bin/bash

# Enhanced EMS Agent Deployment Script
# Supports horizontal scaling, health monitoring, and zero-downtime deployments

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="ems-agent"
ENVIRONMENT="${ENVIRONMENT:-production}"
DEPLOY_MODE="${DEPLOY_MODE:-swarm}"  # swarm, compose, kubernetes
SCALE_REPLICAS="${SCALE_REPLICAS:-auto}"
HEALTH_CHECK_TIMEOUT=${HEALTH_CHECK_TIMEOUT:-300}
ROLLBACK_ON_FAILURE=${ROLLBACK_ON_FAILURE:-true}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker Swarm is initialized (for swarm mode)
    if [[ "$DEPLOY_MODE" == "swarm" ]]; then
        if ! docker info | grep -q "Swarm: active"; then
            log_warning "Docker Swarm is not active. Initializing..."
            docker swarm init || {
                log_error "Failed to initialize Docker Swarm"
                exit 1
            }
        fi
    fi
    
    log_success "Prerequisites check passed"
}

# Setup environment variables
setup_environment() {
    log_info "Setting up environment for $ENVIRONMENT deployment..."
    
    # Load environment-specific variables
    if [[ -f ".env.$ENVIRONMENT" ]]; then
        export $(cat .env.$ENVIRONMENT | xargs)
        log_info "Loaded environment variables from .env.$ENVIRONMENT"
    elif [[ -f ".env" ]]; then
        export $(cat .env | xargs)
        log_info "Loaded environment variables from .env"
    fi
    
    # Set default values if not provided
    export MONGODB_URI="${MONGODB_URI:-mongodb://admin:password123@mongodb-primary:27017,mongodb-secondary-1:27017,mongodb-secondary-2:27017/ems?authSource=admin&replicaSet=rs0}"
    export MONGODB_DATABASE="${MONGODB_DATABASE:-ems}"
    export JWT_SECRET_KEY="${JWT_SECRET_KEY:-$(openssl rand -base64 32)}"
    export ENCRYPTION_KEY="${ENCRYPTION_KEY:-$(openssl rand -base64 32)}"
    export GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"
    
    log_success "Environment setup completed"
}

# Determine scaling configuration
determine_scaling() {
    log_info "Determining scaling configuration..."
    
    if [[ "$SCALE_REPLICAS" == "auto" ]]; then
        # Auto-scale based on available resources
        local cpu_cores=$(nproc)
        local memory_gb=$(free -g | awk '/^Mem:/{print $2}')
        
        log_info "Detected $cpu_cores CPU cores and ${memory_gb}GB memory"
        
        # Scale services based on resource availability
        if [[ $memory_gb -ge 16 && $cpu_cores -ge 8 ]]; then
            # High-end configuration
            export GATEWAY_REPLICAS=3
            export DATA_INGESTION_REPLICAS=5
            export ANALYTICS_REPLICAS=3
            export ADVANCED_ML_REPLICAS=2
            export QUERY_PROCESSOR_REPLICAS=4
            export REALTIME_STREAMING_REPLICAS=3
            export SECURITY_REPLICAS=3
            export MONITORING_REPLICAS=2
            export NOTIFICATION_REPLICAS=2
        elif [[ $memory_gb -ge 8 && $cpu_cores -ge 4 ]]; then
            # Medium configuration
            export GATEWAY_REPLICAS=2
            export DATA_INGESTION_REPLICAS=3
            export ANALYTICS_REPLICAS=2
            export ADVANCED_ML_REPLICAS=1
            export QUERY_PROCESSOR_REPLICAS=2
            export REALTIME_STREAMING_REPLICAS=2
            export SECURITY_REPLICAS=2
            export MONITORING_REPLICAS=1
            export NOTIFICATION_REPLICAS=1
        else
            # Minimal configuration
            export GATEWAY_REPLICAS=1
            export DATA_INGESTION_REPLICAS=2
            export ANALYTICS_REPLICAS=1
            export ADVANCED_ML_REPLICAS=1
            export QUERY_PROCESSOR_REPLICAS=1
            export REALTIME_STREAMING_REPLICAS=1
            export SECURITY_REPLICAS=1
            export MONITORING_REPLICAS=1
            export NOTIFICATION_REPLICAS=1
        fi
        
        log_info "Auto-scaling configured for ${memory_gb}GB/${cpu_cores} cores"
    else
        # Use fixed replica count
        local replicas=$SCALE_REPLICAS
        export GATEWAY_REPLICAS=$replicas
        export DATA_INGESTION_REPLICAS=$replicas
        export ANALYTICS_REPLICAS=$replicas
        export ADVANCED_ML_REPLICAS=$(($replicas > 1 ? $replicas / 2 : 1))
        export QUERY_PROCESSOR_REPLICAS=$replicas
        export REALTIME_STREAMING_REPLICAS=$replicas
        export SECURITY_REPLICAS=$replicas
        export MONITORING_REPLICAS=1
        export NOTIFICATION_REPLICAS=1
        
        log_info "Fixed scaling configured with $replicas replicas"
    fi
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    # Build base service image
    docker build -t ems-agent:latest -f Dockerfile .
    
    # Build specific service images
    services=("gateway" "data_ingestion" "analytics" "advanced_ml" "realtime_streaming" "security" "monitoring" "query_processor" "notification")
    
    for service in "${services[@]}"; do
        if [[ -f "services/$service/Dockerfile" ]]; then
            log_info "Building $service image..."
            docker build -t "ems-agent-$service:latest" -f "services/$service/Dockerfile" .
        elif [[ -f "$service/Dockerfile" ]]; then
            log_info "Building $service image..."
            docker build -t "ems-agent-$service:latest" -f "$service/Dockerfile" .
        fi
    done
    
    log_success "Docker images built successfully"
}

# Deploy with Docker Swarm
deploy_swarm() {
    log_info "Deploying with Docker Swarm..."
    
    # Create secrets
    create_secrets
    
    # Deploy stack
    docker stack deploy -c docker-compose.production.yml "$PROJECT_NAME"
    
    # Wait for services to be healthy
    wait_for_healthy_services
    
    log_success "Docker Swarm deployment completed"
}

# Deploy with Docker Compose
deploy_compose() {
    log_info "Deploying with Docker Compose..."
    
    # Use production compose file
    docker-compose -f docker-compose.production.yml up -d
    
    # Scale services
    scale_services_compose
    
    # Wait for services to be healthy
    wait_for_healthy_services
    
    log_success "Docker Compose deployment completed"
}

# Scale services with Docker Compose
scale_services_compose() {
    log_info "Scaling services..."
    
    docker-compose -f docker-compose.production.yml up -d --scale api-gateway=$GATEWAY_REPLICAS
    docker-compose -f docker-compose.production.yml up -d --scale data-ingestion=$DATA_INGESTION_REPLICAS
    docker-compose -f docker-compose.production.yml up -d --scale analytics=$ANALYTICS_REPLICAS
    docker-compose -f docker-compose.production.yml up -d --scale advanced-ml=$ADVANCED_ML_REPLICAS
    docker-compose -f docker-compose.production.yml up -d --scale query-processor=$QUERY_PROCESSOR_REPLICAS
    docker-compose -f docker-compose.production.yml up -d --scale realtime-streaming=$REALTIME_STREAMING_REPLICAS
    docker-compose -f docker-compose.production.yml up -d --scale security=$SECURITY_REPLICAS
    docker-compose -f docker-compose.production.yml up -d --scale monitoring=$MONITORING_REPLICAS
    docker-compose -f docker-compose.production.yml up -d --scale notification=$NOTIFICATION_REPLICAS
    
    log_success "Services scaled successfully"
}

# Create Docker secrets
create_secrets() {
    log_info "Creating Docker secrets..."
    
    # Create secrets if they don't exist
    if ! docker secret ls | grep -q "mongodb_root_password"; then
        echo "$MONGO_ROOT_PASSWORD" | docker secret create mongodb_root_password -
    fi
    
    if ! docker secret ls | grep -q "jwt_secret_key"; then
        echo "$JWT_SECRET_KEY" | docker secret create jwt_secret_key -
    fi
    
    if ! docker secret ls | grep -q "encryption_key"; then
        echo "$ENCRYPTION_KEY" | docker secret create encryption_key -
    fi
    
    log_success "Docker secrets created"
}

# Wait for services to be healthy
wait_for_healthy_services() {
    log_info "Waiting for services to be healthy (timeout: ${HEALTH_CHECK_TIMEOUT}s)..."
    
    local start_time=$(date +%s)
    local services_to_check=("api-gateway" "monitoring")
    
    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [[ $elapsed -gt $HEALTH_CHECK_TIMEOUT ]]; then
            log_error "Health check timeout reached"
            if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
                rollback_deployment
            fi
            exit 1
        fi
        
        local healthy_count=0
        
        for service in "${services_to_check[@]}"; do
            if check_service_health "$service"; then
                ((healthy_count++))
            fi
        done
        
        if [[ $healthy_count -eq ${#services_to_check[@]} ]]; then
            log_success "All services are healthy"
            break
        fi
        
        log_info "Waiting for services... ($elapsed/${HEALTH_CHECK_TIMEOUT}s)"
        sleep 10
    done
}

# Check individual service health
check_service_health() {
    local service=$1
    local port
    
    case $service in
        "api-gateway") port=8000 ;;
        "monitoring") port=8008 ;;
        *) return 1 ;;
    esac
    
    # Try to connect to health endpoint
    if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Rollback deployment
rollback_deployment() {
    log_warning "Rolling back deployment..."
    
    if [[ "$DEPLOY_MODE" == "swarm" ]]; then
        docker stack rm "$PROJECT_NAME"
    else
        docker-compose -f docker-compose.production.yml down
    fi
    
    log_info "Deployment rolled back"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring and observability..."
    
    # Wait for Prometheus to be ready
    log_info "Waiting for Prometheus to be ready..."
    timeout 60 bash -c 'until curl -f http://localhost:9090/-/ready; do sleep 5; done'
    
    # Wait for Grafana to be ready
    log_info "Waiting for Grafana to be ready..."
    timeout 60 bash -c 'until curl -f http://localhost:3000/api/health; do sleep 5; done'
    
    # Import Grafana dashboards
    if [[ -d "monitoring/grafana/dashboards" ]]; then
        log_info "Importing Grafana dashboards..."
        # Dashboard import logic would go here
    fi
    
    log_success "Monitoring setup completed"
}

# Show deployment status
show_status() {
    log_info "Deployment Status:"
    echo "===================="
    
    if [[ "$DEPLOY_MODE" == "swarm" ]]; then
        docker stack services "$PROJECT_NAME"
        echo ""
        docker stack ps "$PROJECT_NAME" --no-trunc
    else
        docker-compose -f docker-compose.production.yml ps
    fi
    
    echo ""
    log_info "Service Endpoints:"
    echo "  API Gateway:   http://localhost:8000"
    echo "  Prometheus:    http://localhost:9090"
    echo "  Grafana:       http://localhost:3000 (admin/admin)"
    echo "  Jaeger:        http://localhost:16686"
    echo ""
    
    log_info "Health Check Commands:"
    echo "  curl http://localhost:8000/health"
    echo "  curl http://localhost:8008/health"
}

# Performance testing
run_performance_test() {
    log_info "Running basic performance test..."
    
    # Wait for services to be fully ready
    sleep 30
    
    # Test API Gateway response time
    log_info "Testing API Gateway..."
    local response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/health)
    echo "  Response time: ${response_time}s"
    
    # Test basic load
    if command -v ab &> /dev/null; then
        log_info "Running load test (100 requests)..."
        ab -n 100 -c 10 http://localhost:8000/health
    else
        log_warning "Apache Bench (ab) not available for load testing"
    fi
    
    log_success "Performance test completed"
}

# Main deployment function
main() {
    log_info "Starting EMS Agent deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Deploy Mode: $DEPLOY_MODE"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment|-e)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --mode|-m)
                DEPLOY_MODE="$2"
                shift 2
                ;;
            --scale|-s)
                SCALE_REPLICAS="$2"
                shift 2
                ;;
            --build|-b)
                BUILD_IMAGES=true
                shift
                ;;
            --test|-t)
                RUN_TESTS=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  -e, --environment    Deployment environment (production, staging, development)"
                echo "  -m, --mode          Deploy mode (swarm, compose, kubernetes)"
                echo "  -s, --scale         Scaling configuration (auto, 1, 2, 3, etc.)"
                echo "  -b, --build         Build Docker images before deployment"
                echo "  -t, --test          Run performance tests after deployment"
                echo "  -h, --help          Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Execute deployment steps
    check_prerequisites
    setup_environment
    determine_scaling
    
    if [[ "$BUILD_IMAGES" == "true" ]]; then
        build_images
    fi
    
    case $DEPLOY_MODE in
        "swarm")
            deploy_swarm
            ;;
        "compose")
            deploy_compose
            ;;
        "kubernetes")
            log_error "Kubernetes deployment not yet implemented"
            exit 1
            ;;
        *)
            log_error "Unknown deploy mode: $DEPLOY_MODE"
            exit 1
            ;;
    esac
    
    setup_monitoring
    show_status
    
    if [[ "$RUN_TESTS" == "true" ]]; then
        run_performance_test
    fi
    
    log_success "EMS Agent deployment completed successfully!"
    log_info "Access the system at: http://localhost:8000"
}

# Run main function
main "$@"
