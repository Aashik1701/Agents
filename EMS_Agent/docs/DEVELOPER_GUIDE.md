# Developer Guide

Welcome to the EMS Agent development guide. This document provides comprehensive information for developers who want to contribute to, extend, or customize the EMS Agent.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Architecture Deep Dive](#architecture-deep-dive)
4. [Adding New Services](#adding-new-services)
5. [Testing Guide](#testing-guide)
6. [Code Style and Standards](#code-style-and-standards)
7. [Debugging and Troubleshooting](#debugging-and-troubleshooting)
8. [Performance Optimization](#performance-optimization)
9. [Contributing Guidelines](#contributing-guidelines)

## Development Environment Setup

### Prerequisites

```bash
# Install Python 3.9+
python3 --version

# Install development tools
pip install --upgrade pip setuptools wheel

# Install Docker for local services
docker --version
docker-compose --version

# Install Git for version control
git --version
```

### Development Setup

```bash
# Clone and setup development environment
git clone <repository-url>
cd EMS_Agent

# Create development environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Copy development configuration
cp .env.example .env
# Edit .env for development settings
```

### Development Configuration

Configure your `.env` for development:

```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
MICROSERVICES_MODE=true

# Use local services for development
MONGODB_URI=mongodb://localhost:27017/
REDIS_HOST=localhost

# Enable development features
ENABLE_DEBUG_TOOLBAR=true
ENABLE_PROFILING=true
MOCK_EXTERNAL_SERVICES=true
```

### IDE Setup

**VS Code Configuration:**

Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

## Project Structure

```
EMS_Agent/
├── app.py                      # Main application entry point
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── docker-compose.yml          # Service orchestration
├── .env.example               # Environment configuration template
├── deploy.sh                  # Production deployment script
├── start_dev.sh              # Development startup script
├── pyproject.toml            # Python project configuration
├── pytest.ini               # Test configuration
├── .pre-commit-config.yaml   # Git hooks configuration
│
├── common/                   # Shared utilities and base classes
│   ├── __init__.py
│   ├── base_service.py      # Base service class with common functionality
│   └── config_manager.py    # Configuration management
│
├── config/                  # Environment-specific configurations
│   ├── development.yaml     # Development settings
│   ├── production.yaml      # Production settings
│   └── testing.yaml         # Test environment settings
│
├── gateway/                 # API Gateway implementation
│   ├── __init__.py
│   ├── api_gateway.py      # Main gateway application
│   ├── middleware.py       # Custom middleware
│   └── routes.py           # Route definitions
│
├── services/               # Microservices implementations
│   ├── data_ingestion/     # Data ingestion service
│   │   ├── __init__.py
│   │   ├── service.py      # Main service implementation
│   │   ├── models.py       # Data models
│   │   ├── processors.py   # Data processing logic
│   │   └── validators.py   # Data validation
│   │
│   ├── analytics/          # Analytics and ML service
│   │   ├── __init__.py
│   │   ├── service.py      # Main service implementation
│   │   ├── models.py       # ML models
│   │   ├── anomaly_detection.py
│   │   └── predictive_analytics.py
│   │
│   ├── query_processor/    # Query processing service
│   │   ├── __init__.py
│   │   ├── service.py      # Main service implementation
│   │   ├── nlp_processor.py
│   │   └── query_engine.py
│   │
│   └── notification/       # Notification service
│       ├── __init__.py
│       ├── service.py      # Main service implementation
│       ├── email_sender.py
│       ├── sms_sender.py
│       └── slack_sender.py
│
├── monitoring/             # Monitoring and observability
│   ├── prometheus.yml      # Prometheus configuration
│   ├── grafana_dashboards.py
│   └── dashboards/         # Grafana dashboard definitions
│
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Test configuration
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/               # End-to-end tests
│
├── docs/                   # Documentation
│   ├── API.md              # API reference
│   ├── DEPLOYMENT.md       # Deployment guide
│   ├── GETTING_STARTED.md  # Quick start guide
│   └── DEVELOPER_GUIDE.md  # This file
│
├── scripts/               # Utility scripts
│   ├── setup_db.py       # Database initialization
│   ├── load_sample_data.py
│   └── health_check.py
│
└── static/               # Static web assets
    ├── css/
    ├── js/
    └── templates/
```

## Architecture Deep Dive

### Service Communication

Services communicate through:

1. **HTTP REST APIs**: Primary communication method
2. **Redis Pub/Sub**: For real-time events and notifications
3. **Database Shared State**: For persistent data sharing

### Base Service Architecture

All services inherit from `BaseService` which provides:

```python
class BaseService:
    def __init__(self, service_name: str, config: dict):
        self.service_name = service_name
        self.config = config
        self.circuit_breaker = CircuitBreaker()
        self.metrics = PrometheusMetrics()
        self.health_checker = HealthChecker()
        
    async def start(self):
        """Service startup logic"""
        await self.register_service()
        await self.setup_health_checks()
        await self.start_metrics_server()
        
    async def register_service(self):
        """Register with service discovery"""
        
    @circuit_breaker.protect
    @retry(max_attempts=3)
    async def call_service(self, service_name: str, endpoint: str):
        """Make inter-service calls with resilience"""
```

### Configuration Management

```python
from common.config_manager import ConfigManager

# Load configuration for a service
config = ConfigManager.get_service_config('analytics')

# Access configuration values
db_config = config.database
api_config = config.api
ml_config = config.machine_learning
```

### Circuit Breaker Pattern

```python
from common.base_service import circuit_breaker

@circuit_breaker.protect
async def external_api_call():
    """This call is protected by circuit breaker"""
    response = await http_client.get("external-service")
    return response
```

## Adding New Services

### 1. Create Service Structure

```bash
mkdir services/new_service
cd services/new_service
touch __init__.py service.py models.py
```

### 2. Implement Service Class

```python
# services/new_service/service.py
from fastapi import FastAPI
from common.base_service import BaseService
from common.config_manager import ConfigManager

class NewService(BaseService):
    def __init__(self):
        config = ConfigManager.get_service_config('new_service')
        super().__init__('new_service', config)
        
        self.app = FastAPI(
            title="New Service",
            version="1.0.0"
        )
        
        # Add routes
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.get("/")
        async def root():
            return {"service": "new_service", "status": "running"}
            
        @self.app.get("/health")
        async def health():
            return await self.health_check()

if __name__ == "__main__":
    import uvicorn
    service = NewService()
    uvicorn.run(
        service.app,
        host="0.0.0.0",
        port=service.config.port
    )
```

### 3. Add Configuration

```yaml
# config/development.yaml
services:
  new_service:
    port: 8005
    database:
      connection_pool_size: 10
    api:
      timeout: 30
```

### 4. Update Docker Compose

```yaml
# docker-compose.yml
services:
  new-service:
    build:
      context: .
      dockerfile: Dockerfile.service
    ports:
      - "8005:8005"
    environment:
      - SERVICE_NAME=new_service
    depends_on:
      - mongodb
      - redis
```

### 5. Register with Gateway

```python
# gateway/api_gateway.py
async def setup_service_routes():
    services = {
        "new_service": "http://new-service:8005"
    }
    
    @app.api_route("/api/v1/new/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def proxy_new_service(request: Request, path: str):
        return await proxy_request(request, "new_service", f"/{path}")
```

## Testing Guide

### Test Structure

```
tests/
├── conftest.py              # Shared test configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_base_service.py
│   ├── test_config_manager.py
│   └── services/
│       ├── test_analytics.py
│       └── test_data_ingestion.py
├── integration/             # Integration tests (services + DB)
│   ├── test_api_gateway.py
│   └── test_service_communication.py
└── e2e/                    # End-to-end tests (full system)
    ├── test_data_flow.py
    └── test_user_scenarios.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest tests/e2e/           # End-to-end tests only

# Run with coverage
pytest --cov=. --cov-report=html

# Run tests in parallel
pytest -n auto

# Run specific test file
pytest tests/unit/test_analytics.py

# Run with debugging
pytest -s -vv tests/unit/test_analytics.py::test_anomaly_detection
```

### Writing Tests

**Unit Test Example:**

```python
# tests/unit/services/test_analytics.py
import pytest
from unittest.mock import Mock, patch
from services.analytics.service import AnalyticsService

class TestAnalyticsService:
    @pytest.fixture
    def analytics_service(self):
        config = {"database": {"uri": "mock://localhost"}}
        return AnalyticsService(config)
    
    @pytest.mark.asyncio
    async def test_anomaly_detection(self, analytics_service):
        # Mock data
        sample_data = [
            {"timestamp": "2024-01-01", "consumption": 100},
            {"timestamp": "2024-01-02", "consumption": 500}  # Anomaly
        ]
        
        # Test anomaly detection
        anomalies = await analytics_service.detect_anomalies(sample_data)
        
        assert len(anomalies) == 1
        assert anomalies[0]["timestamp"] == "2024-01-02"
```

**Integration Test Example:**

```python
# tests/integration/test_api_gateway.py
import pytest
import httpx
from fastapi.testclient import TestClient
from gateway.api_gateway import app

class TestAPIGateway:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_service_proxy(self, client):
        # Test that gateway properly forwards requests
        response = client.get("/api/v1/data/summary")
        assert response.status_code in [200, 503]  # 503 if service down
```

### Test Configuration

```python
# conftest.py
import pytest
import asyncio
from unittest.mock import Mock

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_database():
    """Mock database for testing"""
    db = Mock()
    db.find.return_value = []
    db.insert_one.return_value = Mock(inserted_id="mock_id")
    return db

@pytest.fixture(autouse=True)
def mock_external_services():
    """Automatically mock external services in tests"""
    with patch('services.analytics.external_api_call') as mock:
        mock.return_value = {"status": "success"}
        yield mock
```

## Code Style and Standards

### Python Code Style

We follow PEP 8 with some modifications:

```python
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        args: [--line-length=88]
        
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]
        
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]
```

### Code Formatting

```bash
# Format code automatically
black .
isort .

# Check code style
flake8 .
mypy .
```

### Documentation Standards

**Function Documentation:**

```python
def analyze_energy_consumption(
    data: List[Dict[str, Any]], 
    timeframe: str = "daily"
) -> Dict[str, float]:
    """
    Analyze energy consumption patterns in the provided data.
    
    Args:
        data: List of energy consumption records
        timeframe: Analysis timeframe ('hourly', 'daily', 'monthly')
        
    Returns:
        Dictionary containing analysis results with keys:
        - average_consumption: Average consumption value
        - peak_consumption: Maximum consumption value
        - anomaly_count: Number of detected anomalies
        
    Raises:
        ValueError: If timeframe is not supported
        DataError: If data format is invalid
        
    Example:
        >>> data = [{"timestamp": "2024-01-01", "consumption": 100}]
        >>> result = analyze_energy_consumption(data, "daily")
        >>> print(result["average_consumption"])
        100.0
    """
```

**Class Documentation:**

```python
class EnergyAnalyzer:
    """
    Advanced energy consumption analyzer with ML capabilities.
    
    This class provides methods for analyzing energy consumption patterns,
    detecting anomalies, and generating predictive insights.
    
    Attributes:
        model: Trained machine learning model
        threshold: Anomaly detection threshold
        
    Example:
        >>> analyzer = EnergyAnalyzer(threshold=0.8)
        >>> analyzer.load_model("models/energy_model.pkl")
        >>> anomalies = analyzer.detect_anomalies(data)
    """
```

### Error Handling Standards

```python
# Custom exceptions
class EnergyDataError(Exception):
    """Raised when energy data is invalid or corrupted."""
    pass

class ServiceUnavailableError(Exception):
    """Raised when a required service is unavailable."""
    pass

# Error handling in services
async def process_energy_data(data: dict) -> dict:
    try:
        validated_data = validate_energy_data(data)
        result = await analyze_data(validated_data)
        return result
    except ValidationError as e:
        logger.error(f"Data validation failed: {e}")
        raise EnergyDataError(f"Invalid data format: {e}")
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing data: {e}")
        raise EnergyDataError(f"Processing failed: {e}")
```

## Debugging and Troubleshooting

### Logging Configuration

```python
# Enable detailed logging for development
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug.log')
    ]
)

# Service-specific loggers
logger = logging.getLogger(__name__)
```

### Debug Mode

```bash
# Run with debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG
python app.py

# Enable profiling
export ENABLE_PROFILING=true
```

### Common Debugging Scenarios

**Service Communication Issues:**

```python
# Debug service discovery
from common.base_service import ServiceRegistry

registry = ServiceRegistry()
services = await registry.get_all_services()
print("Available services:", services)

# Test service connectivity
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get("http://analytics-service:8002/health")
    print("Analytics service health:", response.json())
```

**Database Connection Issues:**

```python
# Test MongoDB connection
from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGODB_URI"))
try:
    client.admin.command('ping')
    print("MongoDB connection successful")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
```

**Memory and Performance Issues:**

```python
# Enable memory profiling
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Your function code
    pass

# Enable performance profiling
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# Your code here
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative').print_stats(10)
```

## Performance Optimization

### Database Optimization

```python
# Indexing for better query performance
async def setup_database_indexes():
    """Setup database indexes for optimal performance"""
    db = get_database()
    
    # Index on frequently queried fields
    await db.energy_data.create_index([
        ("meter_id", 1),
        ("timestamp", -1)
    ])
    
    # Compound indexes for complex queries
    await db.energy_data.create_index([
        ("meter_id", 1),
        ("timestamp", -1),
        ("consumption", 1)
    ])
    
    # Text index for search functionality
    await db.energy_data.create_index([
        ("description", "text"),
        ("location", "text")
    ])
```

### Caching Strategy

```python
from functools import lru_cache
import redis

# In-memory caching
@lru_cache(maxsize=1000)
def get_meter_configuration(meter_id: str):
    """Cache meter configurations in memory"""
    return fetch_meter_config_from_db(meter_id)

# Redis caching
class CacheService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT", 6379))
        )
    
    async def get_or_set(self, key: str, fetch_func, ttl: int = 300):
        """Get from cache or set if not exists"""
        cached_value = self.redis_client.get(key)
        if cached_value:
            return json.loads(cached_value)
        
        value = await fetch_func()
        self.redis_client.setex(key, ttl, json.dumps(value))
        return value
```

### Async Programming Best Practices

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Use async/await for I/O operations
async def fetch_multiple_meters(meter_ids: List[str]):
    """Fetch data for multiple meters concurrently"""
    tasks = [fetch_meter_data(meter_id) for meter_id in meter_ids]
    results = await asyncio.gather(*tasks)
    return results

# Use thread pool for CPU-intensive tasks
executor = ThreadPoolExecutor(max_workers=4)

async def cpu_intensive_analysis(data):
    """Run CPU-intensive analysis in thread pool"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor, 
        perform_complex_analysis, 
        data
    )
    return result
```

### Batch Processing

```python
async def process_data_in_batches(data: List[dict], batch_size: int = 1000):
    """Process large datasets in batches to avoid memory issues"""
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        try:
            await process_batch(batch)
            await asyncio.sleep(0.1)  # Brief pause to prevent overwhelming
        except Exception as e:
            logger.error(f"Batch processing failed for batch {i//batch_size}: {e}")
            # Implement retry logic or error recovery
```

## Contributing Guidelines

### Git Workflow

```bash
# 1. Create feature branch
git checkout -b feature/new-analytics-algorithm

# 2. Make changes and commit
git add .
git commit -m "Add anomaly detection using isolation forest"

# 3. Push and create pull request
git push origin feature/new-analytics-algorithm
```

### Pull Request Process

1. **Code Review Checklist:**
   - [ ] Code follows style guidelines
   - [ ] Tests are included and passing
   - [ ] Documentation is updated
   - [ ] No security vulnerabilities
   - [ ] Performance impact considered

2. **Required Approvals:**
   - At least one code review approval
   - All CI/CD checks passing
   - No merge conflicts

### Commit Message Convention

```bash
# Format: type(scope): description
feat(analytics): add isolation forest anomaly detection
fix(gateway): resolve circuit breaker timeout issue
docs(api): update authentication documentation
test(integration): add service communication tests
refactor(data-ingestion): improve batch processing efficiency
```

### Release Process

```bash
# 1. Create release branch
git checkout -b release/v1.2.0

# 2. Update version numbers
# Update version in setup.py, __init__.py, etc.

# 3. Update CHANGELOG.md
# Document new features, fixes, and breaking changes

# 4. Create release tag
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0
```

---

This developer guide provides the foundation for working with the EMS Agent codebase. For specific implementation details, refer to the inline code documentation and the other guides in the `docs/` directory.
