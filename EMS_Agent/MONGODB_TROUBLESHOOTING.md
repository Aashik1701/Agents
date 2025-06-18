# MongoDB Troubleshooting Guide
**EMS Agent - Energy Management System**

## Quick Diagnostics

### 🏃‍♂️ Quick Health Check
```bash
# Run the automated health check
python mongodb_health_check.py
```

### 🔧 Common Issues & Solutions

#### 1. Connection Timeout
**Symptoms:** "ServerSelectionTimeoutError" or "Connection timeout"
**Solutions:**
```bash
# Check internet connectivity
ping cluster20526.g4udhpz.mongodb.net

# Verify credentials in config.py
# Check if MongoDB Atlas allows your IP address
```

#### 2. Authentication Failed
**Symptoms:** "Authentication failed" or "Invalid credentials"
**Solutions:**
- Verify username/password in `config.py`
- Check if user has database permissions
- Ensure database name is correct

#### 3. SSL Certificate Issues
**Symptoms:** "SSL certificate verify failed"
**Solutions:**
```bash
# Update certificates
pip install --upgrade certifi

# Check system time (certificates are time-sensitive)
date
```

#### 4. Import Errors
**Symptoms:** "ModuleNotFoundError: No module named 'pymongo'"
**Solutions:**
```bash
# Install dependencies
pip install -r requirements.txt

# Or install PyMongo specifically
pip install 'pymongo[srv]>=4.6.0'
```

### 🔍 Step-by-Step Diagnosis

#### Step 1: Basic Connection Test
```python
from pymongo import MongoClient
from config import MONGODB_URI

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ Connection successful")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

#### Step 2: Check Configuration
```python
from config import MONGODB_URI, MONGODB_DATABASE
print(f"URI: {MONGODB_URI[:50]}...")
print(f"Database: {MONGODB_DATABASE}")
```

#### Step 3: Test Collections
```python
from pymongo import MongoClient
from config import MONGODB_URI, MONGODB_DATABASE

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DATABASE]
collections = db.list_collection_names()
print(f"Collections: {collections}")

for coll in collections:
    count = db[coll].estimated_document_count()
    print(f"{coll}: {count} documents")
```

### 🛠️ Environment Setup

#### Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Environment Variables (Recommended)
Create `.env` file:
```env
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
MONGODB_CLUSTER=your_cluster.mongodb.net
MONGODB_DATABASE=EMS_Database
```

Update `config.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
# ... rest of config
```

### 📊 Performance Optimization

#### Connection Pooling
```python
client = MongoClient(
    MONGODB_URI,
    server_api=ServerApi('1'),
    maxPoolSize=50,
    minPoolSize=10,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000
)
```

#### Indexing Recommendations
```javascript
// In MongoDB shell or Compass
db.ems_raw_data.createIndex({"timestamp": 1})
db.ems_raw_data.createIndex({"timestamp": 1, "voltage": 1})
db.ems_hourly_aggregates.createIndex({"timestamp": 1})
db.ems_daily_aggregates.createIndex({"timestamp": 1})
```

### 🚨 Emergency Procedures

#### 1. Connection Recovery
```python
def test_and_recover_connection():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            return client
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
    raise Exception("Could not establish connection after retries")
```

#### 2. Fallback to Local MongoDB
```python
# In config.py, add fallback logic
try:
    # Test Atlas connection
    test_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
    test_client.admin.command('ping')
    test_client.close()
    ACTIVE_URI = MONGODB_URI
except:
    print("⚠️ Atlas unavailable, falling back to local MongoDB")
    ACTIVE_URI = LOCAL_MONGODB_URI
```

### 📞 Support Contacts

#### MongoDB Atlas Support
- **Documentation:** https://docs.mongodb.com/atlas/
- **Support:** https://support.mongodb.com/
- **Status Page:** https://status.mongodb.com/

#### EMS Agent Support
- **Repository:** Contact system administrator
- **Logs:** Check `server.log` for detailed error messages
- **Health Check:** Run `python mongodb_health_check.py`

### 📝 Logging & Monitoring

#### Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('pymongo').setLevel(logging.DEBUG)
```

#### Monitor Connection Pool
```python
client = MongoClient(MONGODB_URI)
# Check pool statistics
pool_stats = client.nodes
print(f"Active connections: {len(pool_stats)}")
```

### 🔄 Maintenance Tasks

#### Daily Health Checks
```bash
# Add to crontab for daily checks
0 9 * * * /path/to/venv/bin/python /path/to/mongodb_health_check.py >> /var/log/ems_health.log 2>&1
```

#### Weekly Data Validation
```python
# Check data integrity
def validate_data_integrity():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]
    
    # Check for missing timestamps
    missing_timestamps = db.ems_raw_data.count_documents({"timestamp": None})
    print(f"Missing timestamps: {missing_timestamps}")
    
    # Check for future dates
    from datetime import datetime
    future_docs = db.ems_raw_data.count_documents({"timestamp": {"$gt": datetime.now()}})
    print(f"Future-dated documents: {future_docs}")
```

---

**Last Updated:** June 18, 2025  
**Next Review:** Monthly  
**Version:** 1.0
