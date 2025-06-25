# Examples

This directory contains practical examples demonstrating how to use the EMS Agent in various scenarios. Each example includes complete code, configuration, and detailed explanations.

## Quick Reference

| Example | Description | Difficulty | Technologies |
|---------|-------------|------------|-------------|
| [Basic Setup](#basic-setup) | Simple installation and first data submission | Beginner | Python, MongoDB |
| [Data Integration](#data-integration) | Connecting real energy meters | Intermediate | MQTT, APIs |
| [Custom Analytics](#custom-analytics) | Building custom energy analysis models | Advanced | Python, ML |
| [Dashboard Creation](#dashboard-creation) | Creating custom visualization dashboards | Intermediate | Grafana, APIs |
| [Multi-Tenant Setup](#multi-tenant-setup) | Configuring for multiple organizations | Advanced | Docker, Kubernetes |

## Examples Overview

### [01_basic_setup/](01_basic_setup/)
**Get started with EMS Agent in 5 minutes**

Learn how to:
- Install and configure EMS Agent
- Submit your first energy data
- Query data through the API
- View results in the web interface

```bash
cd examples/01_basic_setup/
python setup_example.py
```

### [02_data_integration/](02_data_integration/)
**Connect real energy meters and data sources**

Examples include:
- MQTT broker integration
- CSV file import automation
- REST API data pulling
- Real-time data streaming

```bash
cd examples/02_data_integration/
docker-compose up -d
python mqtt_integration.py
```

### [03_custom_analytics/](03_custom_analytics/)
**Build advanced analytics and machine learning models**

Covers:
- Custom anomaly detection algorithms
- Energy consumption forecasting
- Demand response optimization
- Cost analysis models

```bash
cd examples/03_custom_analytics/
pip install -r requirements.txt
python custom_ml_model.py
```

### [04_dashboard_creation/](04_dashboard_creation/)
**Create beautiful energy dashboards**

Learn to:
- Design custom Grafana dashboards
- Build web-based visualizations
- Create mobile-friendly interfaces
- Export reports automatically

```bash
cd examples/04_dashboard_creation/
./setup_dashboard.sh
```

### [05_multi_tenant_setup/](05_multi_tenant_setup/)
**Deploy for multiple organizations**

Implementation of:
- Multi-tenant architecture
- Organization-level data isolation
- Custom branding per tenant
- Scalable deployment patterns

```bash
cd examples/05_multi_tenant_setup/
kubectl apply -f kubernetes/
```

### [06_integration_patterns/](06_integration_patterns/)
**Common integration scenarios**

Examples for:
- Third-party system integration
- API gateway patterns
- Event-driven architecture
- Microservices communication

### [07_advanced_deployment/](07_advanced_deployment/)
**Production deployment scenarios**

Covers:
- High availability setup
- Load balancing configuration
- Backup and disaster recovery
- Performance optimization

### [08_security_examples/](08_security_examples/)
**Security implementation examples**

Demonstrates:
- JWT authentication setup
- Role-based access control
- API security best practices
- Data encryption examples

### [09_monitoring_alerting/](09_monitoring_alerting/)
**Comprehensive monitoring setup**

Includes:
- Prometheus metrics configuration
- Grafana dashboard templates
- Alert rule examples
- Log aggregation setup

### [10_mobile_integration/](10_mobile_integration/)
**Mobile application integration**

Shows how to:
- Build mobile APIs
- Implement offline sync
- Create push notifications
- Optimize for mobile networks

## Getting Started with Examples

### Prerequisites

Before running the examples, ensure you have:

```bash
# Basic requirements
python3.9+
docker
docker-compose

# Optional for advanced examples
kubectl
helm
node.js (for frontend examples)
```

### Common Setup

Most examples share common setup steps:

```bash
# 1. Clone the repository
git clone <repository-url>
cd EMS_Agent/examples

# 2. Set up Python environment
python3 -m venv venv
source venv/bin/activate

# 3. Install common dependencies
pip install -r ../requirements.txt

# 4. Copy environment template
cp ../.env.example .env
# Edit .env with your settings

# 5. Start common services
docker-compose -f ../docker-compose.yml up -d mongodb redis
```

### Running Examples

Each example directory contains:

```
example_directory/
├── README.md           # Detailed instructions
├── setup.py           # Automated setup script
├── config/            # Configuration files
├── src/               # Source code
├── data/              # Sample data files
├── docker-compose.yml # Docker setup (if needed)
└── requirements.txt   # Additional dependencies
```

To run any example:

```bash
cd example_directory/
python setup.py        # Automated setup
# or
./run_example.sh       # Manual setup
```

## Sample Data

All examples use consistent sample data located in `sample_data/`:

- **`meters.json`**: Sample meter configurations
- **`energy_data.csv`**: Historical energy consumption data
- **`weather_data.json`**: Weather data for correlation analysis
- **`events.json`**: Sample events and anomalies

## Environment Configuration

Examples use environment variables that can be configured in `.env`:

```bash
# Database Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=EMS_Examples

# API Configuration
API_BASE_URL=http://localhost:8000
API_KEY=your-example-api-key

# Example-specific settings
EXAMPLE_MQTT_BROKER=localhost:1883
EXAMPLE_WEATHER_API_KEY=your-weather-api-key
```

## Code Style and Conventions

All examples follow these conventions:

```python
# Standard example structure
"""
Example: [Example Name]
Description: [What this example demonstrates]
Requirements: [What you need to run this]
Usage: python example_name.py
"""

import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any

# Configure logging for examples
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExampleRunner:
    """Base class for example runners."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info(f"Initializing {self.__class__.__name__}")
    
    async def run(self):
        """Main example execution method."""
        try:
            await self.setup()
            await self.execute()
            await self.cleanup()
        except Exception as e:
            logger.error(f"Example failed: {e}")
            raise
    
    async def setup(self):
        """Setup resources for the example."""
        logger.info("Setting up example resources...")
    
    async def execute(self):
        """Execute the main example logic."""
        logger.info("Executing example...")
    
    async def cleanup(self):
        """Clean up resources after example."""
        logger.info("Cleaning up example resources...")

if __name__ == "__main__":
    # Example configuration
    config = {
        "api_url": os.getenv("API_BASE_URL", "http://localhost:8000"),
        "database_uri": os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    }
    
    # Run the example
    example = ExampleRunner(config)
    asyncio.run(example.run())
```

## Testing Examples

Each example includes tests to verify functionality:

```bash
# Run tests for specific example
cd examples/01_basic_setup/
python -m pytest tests/

# Run all example tests
cd examples/
python -m pytest */tests/

# Run with coverage
python -m pytest --cov=. --cov-report=html
```

## Contributing Examples

We welcome contributions of new examples! To contribute:

1. **Create Example Directory**: Follow the standard structure
2. **Write Clear Documentation**: Include detailed README with prerequisites
3. **Add Tests**: Ensure your example works reliably
4. **Update This Index**: Add your example to the table above

### Example Template

Use this template for new examples:

```bash
# Create new example directory
mkdir examples/XX_your_example_name/
cd examples/XX_your_example_name/

# Create standard files
touch README.md setup.py requirements.txt
mkdir src/ config/ tests/ data/

# Follow the existing example patterns
```

## Troubleshooting Examples

### Common Issues

1. **Service Connection Errors**
   ```bash
   # Check if services are running
   docker-compose ps
   
   # Check service logs
   docker-compose logs service-name
   ```

2. **Database Connection Issues**
   ```bash
   # Verify MongoDB connection
   python -c "from pymongo import MongoClient; print(MongoClient().admin.command('ping'))"
   ```

3. **Missing Dependencies**
   ```bash
   # Install all dependencies
   pip install -r requirements.txt -r ../requirements.txt
   ```

4. **Port Conflicts**
   ```bash
   # Check what's using ports
   netstat -tulpn | grep :8000
   
   # Use different ports
   export API_GATEWAY_PORT=8080
   ```

### Getting Help

- **Check Example README**: Each example has detailed instructions
- **Review Logs**: Enable debug logging with `export LOG_LEVEL=DEBUG`
- **Ask Questions**: Use GitHub Discussions for example-related questions
- **Report Issues**: Create GitHub issues for bugs in examples

## External Resources

### Related Projects
- **EMS Dashboard Templates**: [link to dashboard repository]
- **Energy Data Simulators**: [link to simulator tools]
- **Integration Libraries**: [link to client libraries]

### Learning Resources
- **Energy Management Fundamentals**: [educational links]
- **Time Series Analysis**: [tutorial links]
- **IoT Data Integration**: [best practices]

### Community Examples
- **User-Contributed Examples**: [community repository]
- **Industry Use Cases**: [case study collection]
- **Best Practices**: [community wiki]

---

Start with the [Basic Setup](01_basic_setup/) example to get familiar with EMS Agent, then explore more advanced scenarios based on your specific use case!
