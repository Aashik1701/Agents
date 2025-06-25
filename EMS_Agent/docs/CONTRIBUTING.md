# Contributing to EMS Agent

Thank you for your interest in contributing to the EMS Agent project! This guide will help you get started with contributing code, documentation, bug reports, and feature requests.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Contribution Types](#contribution-types)
5. [Coding Standards](#coding-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Documentation Guidelines](#documentation-guidelines)
8. [Pull Request Process](#pull-request-process)
9. [Community and Support](#community-and-support)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of:
- Experience level
- Gender identity and expression
- Sexual orientation
- Disability
- Personal appearance
- Body size
- Race
- Ethnicity
- Age
- Religion
- Nationality

### Expected Behavior

- Be respectful and inclusive in all interactions
- Provide constructive feedback and criticism
- Focus on what is best for the community and project
- Show empathy towards other community members
- Accept responsibility for mistakes and learn from them

### Unacceptable Behavior

- Harassment, trolling, or discriminatory language
- Personal attacks or political discussions
- Publishing private information without permission
- Any conduct that would be considered inappropriate in a professional setting

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.9+** installed
- **Git** for version control
- **Docker & Docker Compose** for local development
- Basic understanding of **FastAPI**, **MongoDB**, and **microservices**

### Development Setup

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/ems-agent.git
   cd ems-agent
   ```

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   
   # Install pre-commit hooks
   pre-commit install
   ```

3. **Configure Environment**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env with your development settings
   # At minimum, set MONGODB_URI for your test database
   ```

4. **Start Development Services**
   ```bash
   # Start with Docker Compose
   docker-compose up -d mongodb redis
   
   # Or use the development script
   ./start_dev.sh
   ```

5. **Verify Setup**
   ```bash
   # Run health check
   python -c "from app import app; print('Setup successful!')"
   
   # Run tests
   pytest tests/unit/
   ```

## Development Workflow

### Branching Strategy

We use **Git Flow** with the following branch structure:

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features or enhancements
- `bugfix/*`: Bug fixes
- `hotfix/*`: Critical production fixes
- `release/*`: Release preparation

### Workflow Steps

1. **Create Feature Branch**
   ```bash
   # Ensure you're on develop branch
   git checkout develop
   git pull origin develop
   
   # Create feature branch
   git checkout -b feature/add-energy-forecasting
   ```

2. **Make Changes**
   ```bash
   # Make your changes, following coding standards
   # Add tests for new functionality
   # Update documentation if needed
   ```

3. **Test Your Changes**
   ```bash
   # Run all tests
   pytest
   
   # Run linting
   flake8 .
   black --check .
   
   # Run type checking
   mypy .
   
   # Test integration
   ./scripts/integration_test.sh
   ```

4. **Commit Changes**
   ```bash
   # Stage changes
   git add .
   
   # Commit with descriptive message
   git commit -m "feat(analytics): add energy consumption forecasting model
   
   - Implement LSTM-based forecasting model
   - Add API endpoint for predictions
   - Include model training pipeline
   - Add comprehensive tests
   
   Closes #123"
   ```

5. **Push and Create Pull Request**
   ```bash
   # Push to your fork
   git push origin feature/add-energy-forecasting
   
   # Create pull request on GitHub
   ```

## Contribution Types

### 🐛 Bug Reports

When reporting bugs, please include:

```markdown
**Bug Description**
A clear description of the bug and what you expected to happen.

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python Version: [e.g., 3.9.7]
- EMS Agent Version: [e.g., 1.2.0]
- Docker Version: [if applicable]

**Error Logs**
```
Paste relevant error logs here
```

**Additional Context**
Any other information that might be helpful.
```

### ✨ Feature Requests

For feature requests, please provide:

```markdown
**Feature Description**
A clear description of the feature and why it would be useful.

**Use Case**
Describe the problem this feature would solve.

**Proposed Solution**
Your ideas on how this could be implemented.

**Alternatives Considered**
Any alternative solutions you've considered.

**Additional Context**
Mockups, examples, or references to similar implementations.
```

### 📚 Documentation Improvements

Documentation contributions are always welcome:

- Fix typos or improve clarity
- Add missing documentation
- Create tutorials or guides
- Translate documentation
- Update outdated information

### 🔧 Code Contributions

Areas where code contributions are especially valuable:

- **New Analytics Models**: Machine learning algorithms for energy analysis
- **Data Connectors**: Integration with energy meter APIs
- **Performance Optimizations**: Database queries, caching, async processing
- **Security Enhancements**: Authentication, encryption, vulnerability fixes
- **Testing**: Unit tests, integration tests, performance tests
- **Monitoring**: Metrics, alerts, dashboards

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

```python
# Use Black for formatting (line length: 88)
# Import organization with isort
# Type hints for all functions

from typing import List, Dict, Optional, Union
import asyncio
from datetime import datetime

async def process_energy_data(
    meter_id: str,
    data: List[Dict[str, Union[float, str]]],
    options: Optional[Dict[str, bool]] = None
) -> Dict[str, float]:
    """
    Process energy consumption data for a specific meter.
    
    Args:
        meter_id: Unique identifier for the energy meter
        data: List of energy consumption records
        options: Optional processing configuration
        
    Returns:
        Dictionary containing processed metrics
        
    Raises:
        ValueError: If meter_id is invalid
        DataProcessingError: If data processing fails
    """
    if not meter_id or not isinstance(meter_id, str):
        raise ValueError("Invalid meter_id provided")
    
    # Your implementation here
    return {"average": 100.0, "peak": 150.0}
```

### Code Organization

```python
# File structure within modules
"""
Module docstring describing the module's purpose.
"""

# Standard library imports
import os
import json
from datetime import datetime
from typing import List, Dict, Optional

# Third-party imports
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException

# Local imports
from common.base_service import BaseService
from common.config_manager import ConfigManager
from .models import EnergyData, ProcessingResult

# Constants (ALL_CAPS)
DEFAULT_TIMEOUT = 30
MAX_BATCH_SIZE = 1000

# Classes
class EnergyProcessor(BaseService):
    """Energy data processor with validation and analytics."""
    pass

# Functions
async def process_batch(data: List[Dict]) -> ProcessingResult:
    """Process a batch of energy data."""
    pass

# Main execution
if __name__ == "__main__":
    # Module-level execution code
    pass
```

### API Design Standards

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["energy-data"])

class EnergyDataRequest(BaseModel):
    """Request model for energy data submission."""
    meter_id: str
    timestamp: datetime
    consumption: float
    
    class Config:
        schema_extra = {
            "example": {
                "meter_id": "METER_001",
                "timestamp": "2024-01-01T12:00:00Z",
                "consumption": 150.5
            }
        }

class EnergyDataResponse(BaseModel):
    """Response model for energy data operations."""
    success: bool
    message: str
    data_id: Optional[str] = None

@router.post(
    "/data",
    response_model=EnergyDataResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit energy consumption data",
    description="Submit energy consumption data for processing and storage."
)
async def submit_energy_data(
    request: EnergyDataRequest,
    current_user: str = Depends(get_current_user)
) -> EnergyDataResponse:
    """Submit energy consumption data."""
    try:
        # Validate and process data
        data_id = await process_energy_data(request.dict())
        
        return EnergyDataResponse(
            success=True,
            message="Data submitted successfully",
            data_id=data_id
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

### Error Handling Standards

```python
# Custom exceptions
class EMSError(Exception):
    """Base exception for EMS Agent."""
    pass

class DataValidationError(EMSError):
    """Raised when data validation fails."""
    pass

class ServiceUnavailableError(EMSError):
    """Raised when a required service is unavailable."""
    pass

# Error handling in functions
async def validate_energy_data(data: dict) -> dict:
    """Validate energy consumption data."""
    try:
        # Validation logic
        validated_data = perform_validation(data)
        return validated_data
    except KeyError as e:
        raise DataValidationError(f"Missing required field: {e}")
    except ValueError as e:
        raise DataValidationError(f"Invalid data format: {e}")
    except Exception as e:
        logger.exception(f"Unexpected validation error: {e}")
        raise DataValidationError(f"Validation failed: {e}")

# Error handling in API endpoints
@app.exception_handler(DataValidationError)
async def validation_error_handler(request: Request, exc: DataValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "validation_error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

## Testing Guidelines

### Test Structure

```
tests/
├── conftest.py                 # Shared test configuration
├── unit/                       # Fast, isolated tests
│   ├── test_data_validation.py
│   ├── test_analytics_models.py
│   └── services/
│       ├── test_data_ingestion.py
│       └── test_analytics.py
├── integration/                # Service integration tests
│   ├── test_api_endpoints.py
│   └── test_database_operations.py
└── e2e/                       # End-to-end system tests
    ├── test_complete_workflow.py
    └── test_user_scenarios.py
```

### Writing Tests

```python
# Unit test example
import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.analytics.anomaly_detection import AnomalyDetector

class TestAnomalyDetector:
    """Test suite for anomaly detection functionality."""
    
    @pytest.fixture
    def detector(self):
        """Create anomaly detector instance for testing."""
        config = {"threshold": 0.8, "window_size": 24}
        return AnomalyDetector(config)
    
    @pytest.fixture
    def sample_data(self):
        """Sample energy consumption data for testing."""
        return [
            {"timestamp": "2024-01-01T00:00:00Z", "consumption": 100},
            {"timestamp": "2024-01-01T01:00:00Z", "consumption": 105},
            {"timestamp": "2024-01-01T02:00:00Z", "consumption": 500},  # Anomaly
        ]
    
    def test_detect_anomalies_with_normal_data(self, detector):
        """Test anomaly detection with normal consumption data."""
        normal_data = [
            {"consumption": 100}, {"consumption": 105}, {"consumption": 98}
        ]
        
        anomalies = detector.detect_anomalies(normal_data)
        
        assert len(anomalies) == 0
    
    def test_detect_anomalies_with_outliers(self, detector, sample_data):
        """Test anomaly detection with outlier values."""
        anomalies = detector.detect_anomalies(sample_data)
        
        assert len(anomalies) == 1
        assert anomalies[0]["consumption"] == 500
    
    @pytest.mark.asyncio
    async def test_async_anomaly_detection(self, detector):
        """Test asynchronous anomaly detection."""
        with patch.object(detector, 'fetch_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [{"consumption": 100}]
            
            result = await detector.detect_anomalies_async("METER_001")
            
            mock_fetch.assert_called_once_with("METER_001")
            assert isinstance(result, list)
    
    @pytest.mark.parametrize("threshold,expected_count", [
        (0.5, 2),
        (0.8, 1),
        (0.9, 0),
    ])
    def test_threshold_sensitivity(self, sample_data, threshold, expected_count):
        """Test anomaly detection with different thresholds."""
        detector = AnomalyDetector({"threshold": threshold})
        anomalies = detector.detect_anomalies(sample_data)
        assert len(anomalies) == expected_count

# Integration test example
class TestEnergyDataAPI:
    """Integration tests for energy data API endpoints."""
    
    @pytest.fixture
    async def client(self):
        """Create test client for API testing."""
        from app import app
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_submit_valid_energy_data(self, client):
        """Test submitting valid energy consumption data."""
        data = {
            "meter_id": "TEST_METER",
            "timestamp": "2024-01-01T12:00:00Z",
            "consumption": 150.5
        }
        
        response = await client.post("/api/v1/data", json=data)
        
        assert response.status_code == 201
        assert response.json()["success"] is True
        assert "data_id" in response.json()
    
    @pytest.mark.asyncio
    async def test_submit_invalid_energy_data(self, client):
        """Test submitting invalid energy consumption data."""
        data = {
            "meter_id": "",  # Invalid empty meter_id
            "timestamp": "invalid-date",
            "consumption": -100  # Invalid negative consumption
        }
        
        response = await client.post("/api/v1/data", json=data)
        
        assert response.status_code == 400
        assert "validation_error" in response.json()["error"]
```

### Test Configuration

```python
# conftest.py
import pytest
import asyncio
from unittest.mock import Mock
import tempfile
import os

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_database():
    """Mock database for testing."""
    db = Mock()
    db.energy_data = Mock()
    db.energy_data.find = Mock(return_value=Mock(to_list=AsyncMock(return_value=[])))
    db.energy_data.insert_one = AsyncMock(return_value=Mock(inserted_id="test_id"))
    return db

@pytest.fixture
def temp_config_file():
    """Create temporary configuration file for testing."""
    config_content = """
    database:
      uri: "mongodb://test:27017"
      name: "test_db"
    services:
      analytics:
        threshold: 0.8
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()
        yield f.name
    
    os.unlink(f.name)

@pytest.fixture(autouse=True)
def mock_external_services():
    """Automatically mock external services in tests."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value = Mock(status_code=200, json=lambda: {"status": "ok"})
        yield mock_get
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest tests/e2e/                    # End-to-end tests only

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run tests in parallel
pytest -n auto

# Run specific test file or function
pytest tests/unit/test_analytics.py
pytest tests/unit/test_analytics.py::TestAnomalyDetector::test_detect_anomalies

# Run tests with specific markers
pytest -m "slow"                     # Run slow tests
pytest -m "not slow"                 # Skip slow tests

# Run tests with verbose output
pytest -v -s

# Generate test report
pytest --html=reports/report.html --self-contained-html
```

## Documentation Guidelines

### Documentation Types

1. **Code Documentation**
   - Docstrings for all public functions and classes
   - Inline comments for complex logic
   - Type hints for all parameters and return values

2. **API Documentation**
   - OpenAPI/Swagger documentation (auto-generated)
   - Request/response examples
   - Error code descriptions

3. **User Documentation**
   - Getting started guides
   - Configuration instructions
   - Troubleshooting guides

4. **Developer Documentation**
   - Architecture overviews
   - Development setup
   - Contribution guidelines

### Writing Guidelines

```python
def calculate_energy_efficiency(
    consumption_data: List[Dict[str, float]],
    baseline_period: int = 30,
    efficiency_threshold: float = 0.8
) -> Dict[str, Union[float, bool]]:
    """
    Calculate energy efficiency metrics for consumption data.
    
    This function analyzes energy consumption patterns over a specified
    baseline period and calculates efficiency metrics including variance,
    trend analysis, and efficiency rating.
    
    Args:
        consumption_data: List of consumption records with 'timestamp' 
            and 'consumption' keys. Must contain at least 7 days of data.
        baseline_period: Number of days to use for baseline calculation.
            Must be between 7 and 365 days. Defaults to 30.
        efficiency_threshold: Threshold for determining efficiency rating
            (0.0 to 1.0). Values above threshold are considered efficient.
            Defaults to 0.8.
    
    Returns:
        Dictionary containing:
        - 'efficiency_score': Float between 0.0 and 1.0
        - 'is_efficient': Boolean indicating if above threshold
        - 'baseline_average': Average consumption during baseline period
        - 'current_average': Current period average consumption
        - 'improvement_percentage': Percentage improvement from baseline
    
    Raises:
        ValueError: If consumption_data is empty or contains invalid data
        ValueError: If baseline_period is outside valid range
        ValueError: If efficiency_threshold is not between 0.0 and 1.0
    
    Example:
        >>> data = [
        ...     {"timestamp": "2024-01-01", "consumption": 100},
        ...     {"timestamp": "2024-01-02", "consumption": 95}
        ... ]
        >>> result = calculate_energy_efficiency(data, baseline_period=7)
        >>> print(f"Efficiency: {result['efficiency_score']:.2f}")
        Efficiency: 0.95
        
    Note:
        This function requires at least 7 days of data for meaningful
        analysis. For shorter periods, consider using daily efficiency
        calculation methods.
        
    See Also:
        calculate_daily_efficiency: For single-day efficiency calculation
        analyze_consumption_trends: For trend analysis without efficiency rating
    """
```

### Markdown Documentation

```markdown
# Feature Name

Brief description of what this feature does and why it's useful.

## Overview

More detailed explanation of the feature, its benefits, and use cases.

## Quick Start

```bash
# Minimal example to get started
curl -X POST http://localhost:8000/api/v1/feature \
  -H "Content-Type: application/json" \
  -d '{"example": "data"}'
```

## Configuration

### Required Settings

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `feature_enabled` | Enable/disable feature | `false` | `true` |
| `timeout` | Request timeout in seconds | `30` | `60` |

### Optional Settings

Additional configuration options...

## API Reference

### POST /api/v1/feature

Submit data for processing.

**Request Body:**
```json
{
  "data": "string",
  "options": {
    "validate": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": "processed_data",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Error Responses:**
- `400`: Invalid request data
- `429`: Rate limit exceeded
- `500`: Internal server error

## Examples

### Basic Usage

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/feature",
    json={"data": "example"}
)
result = response.json()
```

### Advanced Usage

More complex examples...

## Troubleshooting

Common issues and solutions...

## See Also

- [Related Feature](link)
- [Configuration Guide](link)
```

## Pull Request Process

### Before Submitting

1. **Ensure your changes are complete:**
   - Code follows style guidelines
   - Tests are included and passing
   - Documentation is updated
   - No breaking changes (or clearly documented)

2. **Run the full test suite:**
   ```bash
   # Linting and formatting
   black .
   isort .
   flake8 .
   
   # Type checking
   mypy .
   
   # Tests
   pytest --cov=.
   
   # Integration tests
   ./scripts/integration_test.sh
   ```

3. **Update documentation:**
   - Update relevant markdown files
   - Add docstrings to new functions
   - Update API documentation if needed

### Pull Request Template

```markdown
## Description

Brief description of changes and motivation.

Fixes #(issue number)

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring (no functional changes)

## Changes Made

- List key changes
- Include any new dependencies
- Mention configuration changes

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Added tests for new functionality

## Screenshots (if applicable)

Include screenshots for UI changes.

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Additional Notes

Any additional information or context.
```

### Review Process

1. **Automated Checks:**
   - All CI/CD pipeline checks must pass
   - Code coverage must not decrease significantly
   - No security vulnerabilities introduced

2. **Manual Review:**
   - At least one maintainer approval required
   - Code quality and design review
   - Documentation completeness check

3. **Final Steps:**
   - Squash commits if needed
   - Update changelog
   - Merge to develop branch

## Community and Support

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community discussions
- **Discord/Slack**: Real-time chat (if available)
- **Email**: Direct contact for security issues

### Getting Help

1. **Check existing documentation** in the `docs/` folder
2. **Search existing issues** on GitHub
3. **Ask in discussions** for general questions
4. **Create a new issue** for bugs or feature requests

### Mentorship

New contributors are welcome! If you're new to the project:

- Look for issues labeled `good first issue`
- Ask questions in discussions
- Request mentorship from experienced contributors
- Start with documentation improvements

### Recognition

Contributors are recognized through:

- **Contributors file**: Listed in CONTRIBUTORS.md
- **Release notes**: Mentioned in significant releases
- **GitHub insights**: Contribution graphs and statistics
- **Community highlights**: Featured in project updates

## Release Process

### Version Numbering

We use **Semantic Versioning** (semver):

- `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Schedule

- **Major releases**: Every 6-12 months
- **Minor releases**: Every 1-2 months
- **Patch releases**: As needed for critical fixes

### Contributing to Releases

- **Feature freeze**: 2 weeks before major releases
- **Release candidates**: Test upcoming releases
- **Documentation updates**: Must be completed before release

---

Thank you for contributing to EMS Agent! Your efforts help make energy management more efficient and accessible for everyone. 🌱⚡
