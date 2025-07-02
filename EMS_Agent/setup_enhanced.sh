#!/bin/bash
# Enhanced EMS Agent Setup and Validation Script

set -e

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

# Main setup function
main() {
    echo "🚀 EMS Agent Enhanced Setup & Validation"
    echo "========================================"
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root is not recommended for security reasons"
        read -p "Continue anyway? (y/N): " continue_root
        if [[ ! "$continue_root" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # System requirements check
    check_system_requirements
    
    # Environment setup
    setup_environment
    
    # Security validation
    validate_security_configuration
    
    # Dependencies installation
    install_dependencies
    
    # Service validation
    validate_services
    
    # Final recommendations
    display_final_recommendations
}

# Check system requirements
check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 9) else 1)'; then
            log_success "Python $PYTHON_VERSION is supported"
        else
            log_error "Python 3.9+ is required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Docker
    if command -v docker &> /dev/null; then
        log_success "Docker is installed"
    else
        log_warning "Docker is not installed - required for microservices mode"
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        log_success "Docker Compose is installed"
    else
        log_warning "Docker Compose is not installed - required for microservices mode"
    fi
    
    # Check available memory
    if [[ -f /proc/meminfo ]]; then
        MEMORY_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        MEMORY_GB=$((MEMORY_KB / 1024 / 1024))
        if [[ $MEMORY_GB -lt 4 ]]; then
            log_warning "Low memory detected ($MEMORY_GB GB). Recommend at least 4GB for optimal performance"
        else
            log_success "Adequate memory available ($MEMORY_GB GB)"
        fi
    fi
    
    # Check disk space
    DISK_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if [[ $DISK_SPACE -lt 10 ]]; then
        log_warning "Low disk space ($DISK_SPACE GB available). Recommend at least 10GB"
    else
        log_success "Adequate disk space available ($DISK_SPACE GB)"
    fi
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    # Create environment file if it doesn't exist
    if [[ ! -f .env ]]; then
        if [[ -f .env.example ]]; then
            log_info "Creating .env from .env.example"
            cp .env.example .env
        elif [[ -f .env.security ]]; then
            log_info "Creating .env from .env.security template"
            cp .env.security .env
        else
            log_warning "No environment template found, creating minimal .env"
            cat > .env << 'EOF'
# Basic EMS Agent Configuration
ENVIRONMENT=development
MICROSERVICES_MODE=true
DEBUG=false

# Database
MONGODB_URI=mongodb://localhost:27017/ems
MONGODB_DATABASE=ems

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Security (CHANGE THESE IN PRODUCTION!)
JWT_SECRET_KEY=$(openssl rand -base64 32)
ENCRYPTION_KEY=$(openssl rand -base64 32)
ADMIN_PASSWORD=change-this-password

# Services
API_GATEWAY_PORT=8000
DATA_INGESTION_PORT=8001
ANALYTICS_PORT=8002
QUERY_PROCESSOR_PORT=8003
NOTIFICATION_PORT=8004
EOF
        fi
        log_success "Environment file created"
    else
        log_info "Environment file already exists"
    fi
    
    # Generate secure secrets if using defaults
    if grep -q "openssl rand -base64 32" .env; then
        log_info "Generating secure secrets..."
        JWT_SECRET=$(openssl rand -base64 32)
        ENCRYPTION_KEY=$(openssl rand -base64 32)
        sed -i.bak "s/\$(openssl rand -base64 32)/$JWT_SECRET/" .env
        sed -i.bak "s/\$(openssl rand -base64 32)/$ENCRYPTION_KEY/" .env
        rm .env.bak
        log_success "Secure secrets generated"
    fi
    
    # Load environment variables
    if [[ -f .env ]]; then
        export $(grep -v '^#' .env | xargs)
    fi
}

# Validate security configuration
validate_security_configuration() {
    log_info "Validating security configuration..."
    
    if [[ -f validate_security.py ]]; then
        if python3 validate_security.py; then
            log_success "Security configuration validation passed"
        else
            log_error "Security configuration validation failed"
            log_warning "Please review and fix security issues before proceeding"
            read -p "Continue anyway? (y/N): " continue_security
            if [[ ! "$continue_security" =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        log_warning "Security validation script not found"
    fi
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d venv ]]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
        log_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [[ -f requirements.txt ]]; then
        log_info "Installing Python dependencies..."
        pip install -r requirements.txt
        log_success "Python dependencies installed"
    else
        log_error "requirements.txt not found"
        exit 1
    fi
    
    # Install additional security tools
    log_info "Installing security tools..."
    pip install safety bandit
    log_success "Security tools installed"
}

# Validate services
validate_services() {
    log_info "Validating service configuration..."
    
    # Check if all required service files exist
    REQUIRED_SERVICES=(
        "services/data_ingestion/service.py"
        "services/analytics/service.py"
        "services/query_processor/service.py"
        "services/notification/service.py"
        "services/monitoring/service.py"
        "services/security/service.py"
        "gateway/api_gateway.py"
    )
    
    MISSING_SERVICES=()
    for service in "${REQUIRED_SERVICES[@]}"; do
        if [[ ! -f "$service" ]]; then
            MISSING_SERVICES+=("$service")
        fi
    done
    
    if [[ ${#MISSING_SERVICES[@]} -eq 0 ]]; then
        log_success "All required services are present"
    else
        log_error "Missing services:"
        for service in "${MISSING_SERVICES[@]}"; do
            echo "  - $service"
        done
        exit 1
    fi
    
    # Check service launcher
    if [[ -f service_launcher.py ]]; then
        log_success "Service launcher is present"
    else
        log_error "Service launcher (service_launcher.py) not found"
        exit 1
    fi
    
    # Check Docker files
    if [[ -f Dockerfile.service ]] && [[ -f Dockerfile.gateway ]]; then
        log_success "Docker configuration files are present"
    else
        log_warning "Docker configuration files are missing"
    fi
    
    # Check Docker Compose files
    if [[ -f docker-compose.yml ]] && [[ -f docker-compose.production.yml ]]; then
        log_success "Docker Compose configuration files are present"
    else
        log_warning "Docker Compose configuration files are missing"
    fi
}

# Security vulnerability scan
run_security_scan() {
    log_info "Running security vulnerability scan..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Check for known vulnerabilities in dependencies
    if command -v safety &> /dev/null; then
        log_info "Scanning for vulnerable dependencies..."
        if safety check; then
            log_success "No known vulnerabilities found in dependencies"
        else
            log_warning "Vulnerabilities found in dependencies - please update"
        fi
    fi
    
    # Static code analysis for security issues
    if command -v bandit &> /dev/null; then
        log_info "Running static security analysis..."
        if bandit -r . -f json -o security-report.json; then
            log_success "Static security analysis completed"
        else
            log_warning "Security issues found - check security-report.json"
        fi
    fi
}

# Display final recommendations
display_final_recommendations() {
    log_success "Setup completed successfully!"
    
    echo ""
    echo "🔧 NEXT STEPS:"
    echo "============="
    echo "1. Review and customize your .env file"
    echo "2. Update default passwords and secrets"
    echo "3. Configure your MongoDB connection"
    echo "4. Choose deployment mode:"
    echo ""
    echo "   Development (Legacy):"
    echo "   $ ./start_dev.sh"
    echo ""
    echo "   Microservices (Docker):"
    echo "   $ ./deploy.sh"
    echo ""
    echo "   Production:"
    echo "   $ ./deploy_enhanced.sh"
    echo ""
    echo "🔒 SECURITY RECOMMENDATIONS:"
    echo "============================"
    echo "• Change all default passwords"
    echo "• Enable HTTPS in production"
    echo "• Configure IP whitelisting"
    echo "• Enable audit logging"
    echo "• Set up monitoring and alerting"
    echo "• Regular security updates"
    echo ""
    echo "📚 DOCUMENTATION:"
    echo "=================="
    echo "• API Reference: docs/API.md"
    echo "• Security Guide: docs/SECURITY.md"
    echo "• Deployment Guide: docs/DEPLOYMENT.md"
    echo "• Troubleshooting: docs/TROUBLESHOOTING.md"
    echo ""
    echo "🚀 Ready to start your EMS Agent!"
}

# Run security scan if requested
if [[ "$1" == "--security-scan" ]]; then
    run_security_scan
    exit 0
fi

# Run main setup
main
