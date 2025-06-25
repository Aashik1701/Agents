# Basic Setup Example

This example demonstrates how to get started with EMS Agent in just a few minutes. You'll learn how to install, configure, and submit your first energy data.

## What You'll Learn

- How to install and configure EMS Agent
- How to submit energy consumption data via API
- How to query and retrieve data
- How to view results in the web interface
- Basic data validation and error handling

## Prerequisites

- Python 3.9 or higher
- MongoDB (local or Atlas)
- Basic understanding of REST APIs

## Quick Start (5 Minutes)

### Step 1: Environment Setup

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd EMS_Agent/examples/01_basic_setup/

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configuration

```bash
# Copy environment template
cp ../../.env.example .env

# Edit configuration (minimal setup)
cat > .env << 'EOF'
# Basic Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=EMS_Example
ENVIRONMENT=development
DEBUG=true

# Disable services we don't need for this example
MICROSERVICES_MODE=false
EOF
```

### Step 3: Start EMS Agent

```bash
# Start MongoDB (if not running)
# Option 1: Local MongoDB
sudo systemctl start mongod

# Option 2: Docker MongoDB
docker run -d --name mongodb -p 27017:27017 mongo:7

# Start EMS Agent
cd ../../
python app.py
```

### Step 4: Run the Example

```bash
# In a new terminal, go to the example directory
cd examples/01_basic_setup/

# Run the basic example
python basic_example.py
```

You should see output like:
```
INFO - Starting Basic EMS Agent Example
INFO - Submitting sample energy data...
INFO - ✓ Data submitted successfully: DATA_001
INFO - Querying submitted data...
INFO - ✓ Found 1 records for meter METER_001
INFO - Example completed successfully!
```

## Detailed Walkthrough

### Understanding the Code

Let's examine the `basic_example.py` file:

```python
"""
Basic EMS Agent Example
=====================

This example demonstrates:
1. Connecting to the EMS Agent API
2. Submitting energy consumption data
3. Querying the submitted data
4. Basic error handling
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

class EMSBasicExample:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "EMS-Agent-Example/1.0"
        })
    
    def check_api_health(self) -> bool:
        """Check if the EMS Agent API is running and healthy."""
        try:
            response = self.session.get(f"{self.api_base_url}/health")
            response.raise_for_status()
            
            health_data = response.json()
            print(f"✓ API Health: {health_data.get('status', 'unknown')}")
            return health_data.get('status') == 'healthy'
            
        except requests.exceptions.RequestException as e:
            print(f"✗ API Health Check Failed: {e}")
            print("Make sure EMS Agent is running on http://localhost:8000")
            return False
    
    def submit_energy_data(self, meter_id: str, consumption: float, 
                          timestamp: datetime = None) -> str:
        """Submit energy consumption data to EMS Agent."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Prepare data payload
        data = {
            "meter_id": meter_id,
            "timestamp": timestamp.isoformat() + "Z",
            "energy_consumption": consumption,
            "power_factor": 0.85,  # Example power factor
            "voltage": 240.0,      # Example voltage
            "current": consumption / 240.0,  # Calculated current
            "location": "Building A - Floor 1",
            "meter_type": "smart_meter"
        }
        
        try:
            response = self.session.post(
                f"{self.api_base_url}/api/v1/data/upload",
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            data_id = result.get('data_id', 'unknown')
            print(f"✓ Data submitted successfully: {data_id}")
            return data_id
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to submit data: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response: {e.response.text}")
            raise
    
    def query_meter_data(self, meter_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Query energy data for a specific meter."""
        try:
            params = {
                "meter_id": meter_id,
                "limit": limit,
                "sort": "-timestamp"  # Most recent first
            }
            
            response = self.session.get(
                f"{self.api_base_url}/api/v1/data/query",
                params=params
            )
            response.raise_for_status()
            
            result = response.json()
            data = result.get('data', [])
            print(f"✓ Found {len(data)} records for meter {meter_id}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to query data: {e}")
            raise
    
    def get_analytics_summary(self, meter_id: str = None) -> Dict[str, Any]:
        """Get analytics summary for energy consumption."""
        try:
            params = {}
            if meter_id:
                params["meter_id"] = meter_id
            
            response = self.session.get(
                f"{self.api_base_url}/api/v1/analytics/summary",
                params=params
            )
            response.raise_for_status()
            
            summary = response.json()
            print(f"✓ Analytics summary retrieved")
            
            return summary
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to get analytics: {e}")
            return {}

def main():
    """Run the basic example."""
    print("=" * 50)
    print("🔋 EMS Agent - Basic Setup Example")
    print("=" * 50)
    
    # Initialize example
    example = EMSBasicExample()
    
    # Step 1: Check API health
    print("\n1. Checking API Health...")
    if not example.check_api_health():
        print("Please start EMS Agent first: python app.py")
        return
    
    # Step 2: Submit sample data
    print("\n2. Submitting Sample Energy Data...")
    
    sample_data = [
        {"meter_id": "METER_001", "consumption": 150.5, "time_offset": 0},
        {"meter_id": "METER_001", "consumption": 148.2, "time_offset": -1},
        {"meter_id": "METER_001", "consumption": 152.1, "time_offset": -2},
        {"meter_id": "METER_002", "consumption": 89.7, "time_offset": 0},
        {"meter_id": "METER_002", "consumption": 91.3, "time_offset": -1},
    ]
    
    data_ids = []
    for data_point in sample_data:
        timestamp = datetime.utcnow() + timedelta(hours=data_point["time_offset"])
        data_id = example.submit_energy_data(
            meter_id=data_point["meter_id"],
            consumption=data_point["consumption"],
            timestamp=timestamp
        )
        data_ids.append(data_id)
        time.sleep(0.1)  # Small delay between submissions
    
    # Step 3: Query the submitted data
    print("\n3. Querying Submitted Data...")
    
    for meter_id in ["METER_001", "METER_002"]:
        data = example.query_meter_data(meter_id, limit=5)
        
        if data:
            print(f"\n   Recent data for {meter_id}:")
            for record in data[:3]:  # Show first 3 records
                timestamp = record.get('timestamp', 'unknown')
                consumption = record.get('energy_consumption', 0)
                print(f"   - {timestamp}: {consumption} kWh")
    
    # Step 4: Get analytics summary
    print("\n4. Getting Analytics Summary...")
    
    summary = example.get_analytics_summary()
    if summary:
        print(f"   Total Meters: {summary.get('total_meters', 'N/A')}")
        print(f"   Total Records: {summary.get('total_records', 'N/A')}")
        print(f"   Average Consumption: {summary.get('average_consumption', 'N/A')} kWh")
    
    # Step 5: Display web interface information
    print("\n5. Web Interface Access...")
    print("   🌐 Open your browser and visit:")
    print("   📊 Dashboard: http://localhost:8000")
    print("   📖 API Docs: http://localhost:8000/docs")
    print("   💬 Chat Interface: http://localhost:8000/chat")
    
    print("\n" + "=" * 50)
    print("✅ Basic example completed successfully!")
    print("=" * 50)
    
    # Optional: Interactive mode
    print("\n🎯 Try these commands manually:")
    print("   curl http://localhost:8000/health")
    print("   curl http://localhost:8000/api/v1/data/query?meter_id=METER_001")

if __name__ == "__main__":
    main()
```

### Sample Data Structure

The example uses this data structure for energy consumption:

```json
{
  "meter_id": "METER_001",
  "timestamp": "2024-01-01T12:00:00Z",
  "energy_consumption": 150.5,
  "power_factor": 0.85,
  "voltage": 240.0,
  "current": 0.627,
  "location": "Building A - Floor 1",
  "meter_type": "smart_meter"
}
```

### Understanding API Responses

**Successful Data Submission:**
```json
{
  "success": true,
  "message": "Data submitted successfully",
  "data_id": "507f1f77bcf86cd799439011",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Data Query Response:**
```json
{
  "success": true,
  "data": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "meter_id": "METER_001",
      "timestamp": "2024-01-01T12:00:00Z",
      "energy_consumption": 150.5,
      "power_factor": 0.85,
      "created_at": "2024-01-01T12:01:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

## Advanced Configuration

### Using MongoDB Atlas

Update your `.env` file for MongoDB Atlas:

```bash
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=EMS_Production
```

### Authentication Setup

For production use, enable authentication:

```bash
# Add to .env
JWT_SECRET_KEY=your-super-secret-key
API_KEY_HEADER=X-API-Key

# Get API key from admin
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Custom Validation

Add custom validation to your data:

```python
def validate_energy_data(data: Dict[str, Any]) -> bool:
    """Validate energy data before submission."""
    required_fields = ["meter_id", "timestamp", "energy_consumption"]
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            print(f"Missing required field: {field}")
            return False
    
    # Validate consumption value
    consumption = data.get("energy_consumption", 0)
    if not isinstance(consumption, (int, float)) or consumption < 0:
        print("Invalid energy consumption value")
        return False
    
    # Validate meter ID format
    meter_id = data.get("meter_id", "")
    if not meter_id or len(meter_id) < 3:
        print("Invalid meter ID")
        return False
    
    return True
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Make sure EMS Agent is running
   python ../../app.py
   
   # Check if port 8000 is available
   netstat -tulpn | grep :8000
   ```

2. **Database Connection Errors**
   ```bash
   # Check MongoDB status
   sudo systemctl status mongod
   
   # Or start with Docker
   docker run -d --name mongodb -p 27017:27017 mongo:7
   ```

3. **Import Errors**
   ```bash
   # Install missing dependencies
   pip install requests pymongo motor
   
   # Verify Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/../../"
   ```

4. **Data Validation Errors**
   ```python
   # Check data format
   data = {
       "meter_id": "METER_001",  # Must be non-empty string
       "timestamp": "2024-01-01T12:00:00Z",  # ISO format
       "energy_consumption": 150.5  # Must be positive number
   }
   ```

### Debug Mode

Enable debug logging for more detailed output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export LOG_LEVEL=DEBUG
```

## Next Steps

After completing this basic example:

1. **Try the Data Integration Example** - Learn how to connect real energy meters
2. **Explore the Analytics Example** - Build custom analysis models  
3. **Check the Dashboard Example** - Create visualizations
4. **Review the API Documentation** - Understand all available endpoints

### API Exploration

```bash
# Explore all available endpoints
curl http://localhost:8000/docs

# Try different query parameters
curl "http://localhost:8000/api/v1/data/query?limit=5&sort=-timestamp"

# Get analytics for specific time range
curl "http://localhost:8000/api/v1/analytics/summary?start_date=2024-01-01&end_date=2024-01-02"
```

### Data Formats

EMS Agent supports multiple data formats:

```python
# Minimal format
minimal_data = {
    "meter_id": "METER_001",
    "energy_consumption": 150.5
}

# Detailed format
detailed_data = {
    "meter_id": "METER_001",
    "timestamp": "2024-01-01T12:00:00Z",
    "energy_consumption": 150.5,
    "power_factor": 0.85,
    "voltage": 240.0,
    "current": 0.627,
    "location": "Building A",
    "meter_type": "smart_meter",
    "tags": ["critical", "monitored"]
}
```

## Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Web Dashboard**: http://localhost:8000
- **Project Documentation**: [../../docs/](../../docs/)
- **More Examples**: [../](../)

---

Congratulations! You've successfully set up and used EMS Agent. You're now ready to explore more advanced features and integration patterns.
