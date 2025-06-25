# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the EMS Agent system.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Service-Specific Troubleshooting](#service-specific-troubleshooting)
4. [Database Issues](#database-issues)
5. [Performance Problems](#performance-problems)
6. [Security Issues](#security-issues)
7. [Deployment Issues](#deployment-issues)
8. [Monitoring and Debugging](#monitoring-and-debugging)
9. [FAQ](#frequently-asked-questions)

## Quick Diagnostics

### System Health Check

Run this comprehensive health check to identify issues:

```bash
#!/bin/bash
# health_check.sh - Quick system diagnostics

echo "=== EMS Agent Health Check ==="
echo "Timestamp: $(date)"
echo

# Check if services are running
echo "1. Service Status:"
if command -v docker &> /dev/null; then
    echo "Docker services:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "Checking Python processes:"
    ps aux | grep -E "(app\.py|uvicorn)" | grep -v grep
fi
echo

# Check ports
echo "2. Port Status:"
for port in 8000 8001 8002 8003 8004 27017 6379; do
    if nc -z localhost $port 2>/dev/null; then
        echo "✓ Port $port: Open"
    else
        echo "✗ Port $port: Closed"
    fi
done
echo

# Check API endpoints
echo "3. API Health:"
for endpoint in "http://localhost:8000/health" "http://localhost:8001/health" "http://localhost:8002/health"; do
    if curl -s "$endpoint" &>/dev/null; then
        status=$(curl -s "$endpoint" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null)
        echo "✓ $endpoint: $status"
    else
        echo "✗ $endpoint: Unreachable"
    fi
done
echo

# Check database connectivity
echo "4. Database Connectivity:"
python3 -c "
import os
from pymongo import MongoClient
try:
    client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'), serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✓ MongoDB: Connected')
except Exception as e:
    print(f'✗ MongoDB: {e}')
" 2>/dev/null
echo

# Check Redis connectivity
echo "5. Redis Connectivity:"
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &>/dev/null; then
        echo "✓ Redis: Connected"
    else
        echo "✗ Redis: Not responding"
    fi
else
    echo "? Redis CLI not available"
fi
echo

# Check disk space
echo "6. Disk Space:"
df -h | grep -E "(/$|/var)" | while read line; do
    usage=$(echo $line | awk '{print $5}' | sed 's/%//')
    if [ $usage -gt 80 ]; then
        echo "⚠ $line (Warning: >80%)"
    else
        echo "✓ $line"
    fi
done
echo

# Check memory usage
echo "7. Memory Usage:"
free -h | grep "Mem:" | awk '{printf "Used: %s/%s (%.1f%%)\n", $3, $2, ($3/$2)*100}'
echo

echo "=== Health Check Complete ==="
```

### Quick Fix Commands

```bash
# Restart all services
docker-compose down && docker-compose up -d

# Clear Redis cache
redis-cli FLUSHALL

# Restart individual service
docker-compose restart data-ingestion

# Check logs for errors
docker-compose logs --tail=50 api-gateway

# Reset database indexes
python3 scripts/reset_indexes.py
```

## Common Issues

### 1. Service Won't Start

**Symptoms:**
- Service fails to start
- Port binding errors
- Import errors

**Diagnosis:**
```bash
# Check specific service logs
docker-compose logs service-name

# Check port conflicts
netstat -tulpn | grep :8000

# Check Python path issues
python3 -c "import sys; print('\n'.join(sys.path))"
```

**Solutions:**

**Port Already in Use:**
```bash
# Find process using port
sudo lsof -i :8000

# Kill process using port
sudo kill -9 $(sudo lsof -t -i:8000)

# Or use different port
export API_GATEWAY_PORT=8080
```

**Missing Dependencies:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check for conflicting versions
pip list | grep -E "(fastapi|uvicorn|motor)"
```

**Permission Issues:**
```bash
# Fix file permissions
chmod +x deploy.sh start_dev.sh

# Fix directory permissions
sudo chown -R $USER:$USER ./EMS_Agent
```

### 2. Database Connection Issues

**Symptoms:**
- "No route to host" errors
- Authentication failures
- Timeout errors

**Diagnosis:**
```bash
# Test MongoDB connection
python3 -c "
from pymongo import MongoClient
import os
try:
    client = MongoClient(os.getenv('MONGODB_URI'))
    print('Connection successful')
    print('Databases:', client.list_database_names())
except Exception as e:
    print(f'Connection failed: {e}')
"
```

**Solutions:**

**Connection String Issues:**
```bash
# Check environment variables
echo $MONGODB_URI

# For MongoDB Atlas, ensure:
# 1. IP is whitelisted (0.0.0.0/0 for development)
# 2. Username/password are correct
# 3. Database name exists

# Example correct format:
export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/database_name"
```

**Local MongoDB Issues:**
```bash
# Start MongoDB service
sudo systemctl start mongod

# Check MongoDB status
sudo systemctl status mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

**Network Issues:**
```bash
# Test network connectivity
ping cluster.mongodb.net

# Test port connectivity
telnet cluster.mongodb.net 27017
```

### 3. API Gateway Issues

**Symptoms:**
- 502 Bad Gateway errors
- Service discovery failures
- Load balancing issues

**Diagnosis:**
```bash
# Check gateway logs
docker-compose logs api-gateway

# Test direct service access
curl http://localhost:8001/health

# Check service registry
redis-cli KEYS "service:*"
```

**Solutions:**

**Service Discovery Issues:**
```python
# Debug service registration
import redis
r = redis.Redis(host='localhost', port=6379)
services = r.keys('service:*')
for service in services:
    print(f"{service}: {r.get(service)}")
```

**Load Balancer Issues:**
```bash
# Reset Redis service registry
redis-cli DEL "service:data_ingestion"
redis-cli DEL "service:analytics"

# Restart services to re-register
docker-compose restart data-ingestion analytics
```

## Service-Specific Troubleshooting

### Data Ingestion Service

**Common Issues:**

1. **Data Validation Errors:**
```bash
# Check validation logs
docker-compose logs data-ingestion | grep "ValidationError"

# Test with sample data
curl -X POST http://localhost:8001/validate \
  -H "Content-Type: application/json" \
  -d '{"meter_id": "TEST", "timestamp": "2024-01-01T12:00:00Z", "consumption": 100}'
```

2. **Batch Processing Issues:**
```bash
# Check batch processing status
curl http://localhost:8001/batch/status

# Clear stuck batches
curl -X POST http://localhost:8001/batch/clear
```

3. **Memory Issues with Large Files:**
```python
# Adjust batch size in configuration
# config/development.yaml
services:
  data_ingestion:
    batch_size: 500  # Reduce from default 1000
    max_file_size: 10MB  # Limit file size
```

### Analytics Service

**Common Issues:**

1. **Model Loading Failures:**
```bash
# Check model files
ls -la models/

# Test model loading
python3 -c "
from services.analytics.models import load_anomaly_model
try:
    model = load_anomaly_model()
    print('Model loaded successfully')
except Exception as e:
    print(f'Model loading failed: {e}')
"
```

2. **Memory Issues with ML Operations:**
```bash
# Monitor memory usage
docker stats analytics-service

# Adjust memory limits
# docker-compose.yml
services:
  analytics:
    mem_limit: 2g
    environment:
      - ML_BATCH_SIZE=100
```

3. **Slow Analytics Performance:**
```python
# Enable profiling
import cProfile
import pstats

def profile_analytics():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your analytics code here
    result = perform_analysis(data)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative').print_stats(10)
```

### Query Processor Service

**Common Issues:**

1. **NLP Processing Errors:**
```bash
# Check for missing NLP models
python3 -c "
import spacy
try:
    nlp = spacy.load('en_core_web_sm')
    print('NLP model loaded successfully')
except OSError:
    print('NLP model not found. Install with: python -m spacy download en_core_web_sm')
"
```

2. **Query Timeout Issues:**
```yaml
# Increase timeout in configuration
services:
  query_processor:
    timeout: 60  # seconds
    max_query_complexity: 10
```

## Database Issues

### MongoDB Performance Issues

**Diagnosis:**
```javascript
// Connect to MongoDB shell
mongo

// Check slow queries
db.setProfilingLevel(2, { slowms: 100 })
db.system.profile.find().sort({ts: -1}).limit(5)

// Check index usage
db.energy_data.find({meter_id: "METER_001"}).explain("executionStats")

// Check collection stats
db.energy_data.stats()
```

**Solutions:**

1. **Missing Indexes:**
```python
# Create performance indexes
async def create_performance_indexes():
    db = get_database()
    
    # Compound index for common queries
    await db.energy_data.create_index([
        ("meter_id", 1),
        ("timestamp", -1)
    ])
    
    # Index for analytics queries
    await db.energy_data.create_index([
        ("timestamp", -1),
        ("consumption", 1)
    ])
    
    print("Performance indexes created")
```

2. **Large Collection Issues:**
```javascript
// Enable sharding for large collections
sh.enableSharding("EMS_Database")
sh.shardCollection("EMS_Database.energy_data", {"meter_id": 1, "timestamp": 1})
```

3. **Memory Issues:**
```yaml
# Increase MongoDB memory (in MongoDB config)
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4
```

### Data Corruption Issues

**Diagnosis:**
```bash
# Check database integrity
mongod --dbpath /data/db --repair

# Validate collections
mongo --eval "db.energy_data.validate({full: true})"
```

**Solutions:**
```bash
# Backup before repair
mongodump --out /backup/before_repair

# Repair database
mongod --repair

# Restore from backup if needed
mongorestore /backup/last_good_backup
```

## Performance Problems

### High CPU Usage

**Diagnosis:**
```bash
# Check CPU usage by container
docker stats

# Profile Python application
python3 -m cProfile -o profile.stats app.py
python3 -c "
import pstats
stats = pstats.Stats('profile.stats')
stats.sort_stats('cumulative').print_stats(10)
"
```

**Solutions:**

1. **Optimize Database Queries:**
```python
# Use aggregation pipeline instead of multiple queries
pipeline = [
    {"$match": {"meter_id": meter_id, "timestamp": {"$gte": start_date}}},
    {"$group": {"_id": None, "avg_consumption": {"$avg": "$consumption"}}},
    {"$project": {"_id": 0, "average": "$avg_consumption"}}
]
result = await db.energy_data.aggregate(pipeline).to_list(1)
```

2. **Implement Caching:**
```python
import redis
from functools import wraps

def cache_result(expiry=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Calculate and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expiry, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### High Memory Usage

**Diagnosis:**
```bash
# Check memory usage
free -h
docker stats

# Python memory profiling
pip install memory-profiler
python3 -m memory_profiler app.py
```

**Solutions:**

1. **Optimize Data Processing:**
```python
# Process data in chunks instead of loading all at once
async def process_large_dataset(query):
    batch_size = 1000
    skip = 0
    
    while True:
        batch = await db.energy_data.find(query).skip(skip).limit(batch_size).to_list(batch_size)
        if not batch:
            break
            
        # Process batch
        await process_batch(batch)
        skip += batch_size
        
        # Force garbage collection
        import gc
        gc.collect()
```

2. **Use Generators:**
```python
def generate_data_chunks(data, chunk_size=1000):
    """Generate data in chunks to reduce memory usage"""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

# Usage
for chunk in generate_data_chunks(large_dataset):
    process_chunk(chunk)
```

### Network Latency Issues

**Diagnosis:**
```bash
# Test network latency between services
docker exec api-gateway ping data-ingestion

# Check DNS resolution
nslookup data-ingestion

# Test HTTP latency
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8001/health"
```

**Solutions:**

1. **Connection Pooling:**
```python
import httpx

# Use connection pooling for HTTP requests
async with httpx.AsyncClient(
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    timeout=httpx.Timeout(10.0)
) as client:
    response = await client.get("http://service/endpoint")
```

2. **Database Connection Pooling:**
```python
from motor.motor_asyncio import AsyncIOMotorClient

# Configure connection pool
client = AsyncIOMotorClient(
    mongodb_uri,
    maxPoolSize=50,
    minPoolSize=10,
    serverSelectionTimeoutMS=5000
)
```

## Security Issues

### Authentication Failures

**Diagnosis:**
```bash
# Check authentication logs
grep "authentication" /var/log/ems/security.log

# Test JWT token
python3 -c "
import jwt
token = 'your-jwt-token'
secret = 'your-secret'
try:
    payload = jwt.decode(token, secret, algorithms=['HS256'])
    print('Token valid:', payload)
except jwt.ExpiredSignatureError:
    print('Token expired')
except jwt.InvalidTokenError:
    print('Token invalid')
"
```

**Solutions:**

1. **Token Refresh Issues:**
```python
# Implement automatic token refresh
async def refresh_token_if_needed(token):
    try:
        # Decode without verification to check expiry
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = payload.get('exp', 0)
        
        # Refresh if expires in next 5 minutes
        if exp - time.time() < 300:
            return await get_new_token()
        return token
    except:
        return await get_new_token()
```

### Rate Limiting Issues

**Diagnosis:**
```bash
# Check rate limiting logs
redis-cli KEYS "rate_limit:*"

# Check current limits
redis-cli GET "rate_limit:ip:192.168.1.100"
```

**Solutions:**
```bash
# Clear rate limits for debugging
redis-cli DEL "rate_limit:ip:192.168.1.100"

# Adjust rate limits temporarily
redis-cli SET "rate_limit:ip:192.168.1.100" 0 EX 3600
```

## Deployment Issues

### Docker Issues

**Common Problems:**

1. **Build Failures:**
```bash
# Clean build cache
docker system prune -a

# Build with verbose output
docker-compose build --no-cache --progress=plain

# Check Dockerfile syntax
docker run --rm -i hadolint/hadolint < Dockerfile
```

2. **Container Communication:**
```bash
# Check Docker networks
docker network ls
docker network inspect ems_agent_default

# Test container-to-container communication
docker exec api-gateway ping data-ingestion
```

3. **Volume Mount Issues:**
```bash
# Check volume permissions
ls -la ./data/

# Fix permissions
sudo chown -R $(id -u):$(id -g) ./data/
```

### Environment Configuration

**Common Issues:**

1. **Missing Environment Variables:**
```bash
# Check all environment variables
docker-compose exec api-gateway printenv | grep -E "(MONGODB|REDIS|JWT)"

# Set missing variables
echo "MISSING_VAR=value" >> .env
docker-compose up -d
```

2. **Configuration File Issues:**
```yaml
# Validate YAML syntax
python3 -c "
import yaml
with open('config/development.yaml') as f:
    config = yaml.safe_load(f)
    print('YAML is valid')
"
```

## Monitoring and Debugging

### Logging Best Practices

```python
import logging
import sys

# Configure comprehensive logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/var/log/ems/app.log'),
            logging.handlers.RotatingFileHandler(
                '/var/log/ems/app.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )

# Use structured logging
import json

def log_structured(level, event, **kwargs):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        **kwargs
    }
    getattr(logging, level)(json.dumps(log_entry))

# Usage
log_structured("info", "data_processed", meter_id="METER_001", count=1500)
```

### Debug Mode

```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Enable SQL query logging (if using SQL)
export DB_ECHO=true

# Enable request/response logging
export HTTP_DEBUG=true
```

### Health Monitoring

```python
class HealthMonitor:
    def __init__(self):
        self.checks = {}
    
    async def add_check(self, name: str, check_func):
        """Add a health check"""
        self.checks[name] = check_func
    
    async def get_health_status(self):
        """Get overall health status"""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                result = await check_func()
                results[name] = {"status": "healthy", "details": result}
            except Exception as e:
                results[name] = {"status": "unhealthy", "error": str(e)}
                overall_healthy = False
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "checks": results,
            "timestamp": datetime.utcnow().isoformat()
        }

# Usage
health_monitor = HealthMonitor()

async def check_database():
    client = get_database_client()
    await client.admin.command('ping')
    return "Database connection OK"

await health_monitor.add_check("database", check_database)
```

## Frequently Asked Questions

### Q: Why is my service taking so long to start?

**A:** Check the following:
1. Database connection timeout (increase `serverSelectionTimeoutMS`)
2. Large model loading (implement lazy loading)
3. Network connectivity issues
4. Resource constraints (CPU/memory)

### Q: How do I scale individual services?

**A:** Use Docker Compose scaling:
```bash
# Scale specific service
docker-compose up -d --scale analytics=3

# Check scaled instances
docker-compose ps
```

### Q: How do I backup and restore data?

**A:** For MongoDB:
```bash
# Backup
mongodump --uri="$MONGODB_URI" --out=/backup/$(date +%Y%m%d_%H%M%S)

# Restore
mongorestore --uri="$MONGODB_URI" /backup/20240101_120000
```

### Q: How do I update the system safely?

**A:** Follow this process:
```bash
# 1. Backup data
./scripts/backup.sh

# 2. Test in staging
export ENVIRONMENT=staging
./deploy.sh

# 3. Deploy to production
export ENVIRONMENT=production
./deploy.sh

# 4. Verify deployment
./scripts/health_check.sh
```

### Q: How do I debug intermittent issues?

**A:** 
1. Enable detailed logging
2. Use correlation IDs for request tracing
3. Implement metrics collection
4. Set up alerting for anomalies

```python
# Request correlation ID middleware
import uuid

@app.middleware("http")
async def add_correlation_id_middleware(request: Request, call_next):
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response
```

---

For additional support, check the system logs, enable debug mode, and review the specific service documentation.
