# Getting Started with EMS Agent

This guide will help you quickly set up and start using the EMS Agent (Energy Management System).

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [Initial Configuration](#initial-configuration)
4. [First Run](#first-run)
5. [Basic Usage](#basic-usage)
6. [Next Steps](#next-steps)

## System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows 10+
- **Python**: 3.9 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB free space
- **Network**: Internet connection for dependencies and MongoDB Atlas

### Recommended Setup
- **OS**: Ubuntu 20.04+ or macOS 12+
- **Python**: 3.11+
- **RAM**: 16GB for production workloads
- **Storage**: 50GB+ for data storage
- **CPU**: 4+ cores for optimal performance

## Installation Methods

### Method 1: Docker Deployment (Recommended)

This is the fastest way to get started with all services running.

```bash
# 1. Clone the repository
git clone <repository-url>
cd EMS_Agent

# 2. Copy and configure environment variables
cp .env.example .env
# Edit .env with your MongoDB URI and other settings

# 3. Deploy with Docker
chmod +x deploy.sh
./deploy.sh

# 4. Verify installation
curl http://localhost:8000/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "gateway": "healthy",
    "data_ingestion": "healthy",
    "analytics": "healthy"
  }
}
```

### Method 2: Development Setup

For development and customization:

```bash
# 1. Clone and enter directory
git clone <repository-url>
cd EMS_Agent

# 2. Run development setup script
chmod +x start_dev.sh
./start_dev.sh

# Follow the interactive prompts to choose:
# - Python environment setup
# - MongoDB configuration
# - Service deployment mode
```

### Method 3: Manual Installation

For full control over the installation:

```bash
# 1. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export MONGODB_URI="your-mongodb-connection-string"
export MICROSERVICES_MODE=false  # Start with legacy mode

# 4. Run the application
python app.py
```

## Initial Configuration

### 1. Database Setup

**Option A: MongoDB Atlas (Recommended)**
1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a new cluster
3. Get your connection string
4. Add it to your `.env` file:
   ```bash
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   ```

**Option B: Local MongoDB**
```bash
# Install MongoDB locally
# macOS
brew install mongodb-community

# Ubuntu
sudo apt-get install mongodb

# Start MongoDB
sudo systemctl start mongod

# Use local connection
MONGODB_URI=mongodb://localhost:27017/
```

### 2. Environment Configuration

Edit your `.env` file with essential settings:

```bash
# Required Settings
MONGODB_URI=your-mongodb-connection-string
MONGODB_DATABASE=EMS_Database

# Optional but Recommended
GEMINI_API_KEY=your-gemini-api-key  # For AI features
ENVIRONMENT=development
DEBUG=true
```

### 3. Service Configuration

Choose your deployment mode:

**Legacy Mode** (Single application):
```bash
MICROSERVICES_MODE=false
```

**Microservices Mode** (Distributed services):
```bash
MICROSERVICES_MODE=true
```

## First Run

### 1. Start the Application

**Docker Method:**
```bash
./deploy.sh
```

**Development Method:**
```bash
./start_dev.sh
```

**Manual Method:**
```bash
python app.py
```

### 2. Verify Installation

Check that all services are running:

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Main interface
open http://localhost:8000
```

### 3. Load Sample Data

```bash
# Run the sample data loader
python data_loader.py --sample

# Or use the API
curl -X POST http://localhost:8000/api/v1/data/load-sample
```

## Basic Usage

### 1. Web Interface

Open your browser and go to `http://localhost:8000`

- **Dashboard**: View energy consumption overview
- **Analytics**: Explore energy patterns and anomalies
- **Chat Interface**: Ask questions about your energy data
- **Data Upload**: Import your energy meter data

### 2. API Usage

**Upload Energy Data:**
```bash
curl -X POST http://localhost:8000/api/v1/data/upload \
  -H "Content-Type: application/json" \
  -d '{
    "meter_id": "METER_001",
    "timestamp": "2024-01-01T12:00:00Z",
    "energy_consumption": 150.5,
    "power_factor": 0.85
  }'
```

**Query Energy Data:**
```bash
curl "http://localhost:8000/api/v1/data/query?meter_id=METER_001&limit=10"
```

**Get Analytics:**
```bash
curl "http://localhost:8000/api/v1/analytics/summary?period=daily"
```

### 3. Chat Interface

Use natural language queries:
- "What's my energy consumption today?"
- "Show me anomalies in the last week"
- "Compare consumption between meters"
- "Predict next month's energy usage"

## Next Steps

### 1. Data Integration

- **Import your energy meter data** using the web interface or API
- **Set up automated data collection** from your energy meters
- **Configure data validation rules** for your specific use case

### 2. Customize Analytics

- **Configure anomaly detection thresholds** in the Analytics service
- **Set up custom alerts** for your energy consumption patterns
- **Create custom dashboards** for your specific metrics

### 3. Production Deployment

- **Scale services** using Kubernetes (see [DEPLOYMENT.md](docs/DEPLOYMENT.md))
- **Set up monitoring** with Prometheus and Grafana
- **Configure backups** for your data
- **Implement security measures** (SSL, authentication, etc.)

### 4. Advanced Features

- **Machine Learning Models**: Train custom models for your data
- **Integration APIs**: Connect with other energy management systems
- **Real-time Streaming**: Set up live data feeds
- **Mobile Access**: Configure mobile-friendly interfaces

## Troubleshooting

### Common Issues

**Connection Errors:**
```bash
# Check MongoDB connection
python -c "from pymongo import MongoClient; print(MongoClient('your-uri').admin.command('ping'))"

# Check Redis connection (if using microservices)
redis-cli ping
```

**Port Conflicts:**
```bash
# Check what's running on default ports
lsof -i :8000  # API Gateway
lsof -i :8001  # Data Ingestion
lsof -i :8002  # Analytics
```

**Permission Issues:**
```bash
# Make scripts executable
chmod +x deploy.sh start_dev.sh

# Fix Python path issues
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Getting Help

1. **Check the logs**: Look at the console output for error messages
2. **Review documentation**: Check [docs/](docs/) folder for detailed guides
3. **Verify configuration**: Ensure your `.env` file has correct values
4. **Test components**: Use the health check endpoints to isolate issues

### Support Resources

- **API Documentation**: `http://localhost:8000/docs`
- **Deployment Guide**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **API Reference**: [docs/API.md](docs/API.md)
- **Configuration Guide**: [README.md](README.md#configuration)

---

**Congratulations!** 🎉 You now have EMS Agent running. Start by uploading some energy data and exploring the analytics features.
