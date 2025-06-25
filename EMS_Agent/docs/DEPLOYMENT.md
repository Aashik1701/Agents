# Deployment Guide - EMS Agent

This guide covers various deployment scenarios for the EMS Agent, from development setups to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Configuration](#configuration)
7. [Security Considerations](#security-considerations)
8. [Monitoring Setup](#monitoring-setup)
9. [Backup and Recovery](#backup-and-recovery)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 20 GB available space
- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2

#### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Storage**: 50+ GB SSD
- **OS**: Linux (Ubuntu 22.04 LTS)

### Software Dependencies

#### Required
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.9+ (for development)
- **Git**: Latest version

#### Optional
- **Kubernetes**: 1.24+ (for K8s deployment)
- **Helm**: 3.0+ (for K8s package management)
- **kubectl**: Latest version

### External Services

#### Required
- **MongoDB Atlas** or **MongoDB Server**: 5.0+
- **Internet Connection**: For downloading dependencies

#### Optional
- **Redis**: 6.0+ (for caching and service discovery)
- **SMTP Server**: For email notifications
- **SSL Certificate**: For HTTPS in production

---

## Development Deployment

### Quick Start

The fastest way to get EMS Agent running for development:

```bash
# Clone repository
git clone <repository-url>
cd EMS_Agent

# Quick development setup
./start_dev.sh
```

This script will:
1. Create Python virtual environment
2. Install dependencies
3. Start Redis (if available)
4. Prompt for deployment mode selection

### Manual Development Setup

#### 1. Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configuration

Create environment configuration:

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Example `.env` for development:
```bash
# Environment
ENVIRONMENT=development
MICROSERVICES_MODE=false
DEBUG=true
LOG_LEVEL=INFO

# Database
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=EMS_Database_Dev

# Redis (optional for development)
REDIS_HOST=localhost
REDIS_PORT=6379

# Security
JWT_SECRET_KEY=dev-secret-key-change-in-production
API_KEY=dev-api-key
```

#### 3. Start Services

**Option A: Legacy Monolithic Mode (Default)**
```bash
export MICROSERVICES_MODE=false
python app.py
```

**Option B: Microservices Mode with Docker**
```bash
# Start infrastructure services
docker-compose up -d redis

# Start individual services
export MICROSERVICES_MODE=true
export SERVICE_TYPE=gateway
python app.py
```

**Option C: Full Microservices with Docker**
```bash
docker-compose up -d
```

### Development URLs

Once deployed, access the system at:

- **Main Application**: http://localhost:5004 (legacy mode)
- **API Gateway**: http://localhost:8000 (microservices mode)
- **Data Ingestion**: http://localhost:8001
- **Analytics**: http://localhost:8002
- **API Documentation**: http://localhost:8000/docs
- **Redis**: localhost:6379

---

## Production Deployment

### Prerequisites for Production

1. **Domain and SSL Certificate**
2. **Production MongoDB Atlas cluster**
3. **Email/SMS service for notifications**
4. **Monitoring infrastructure**
5. **Backup solution**

### Production Environment Setup

#### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Reboot to apply changes
sudo reboot
```

#### 2. Application Deployment

```bash
# Clone repository
git clone <repository-url>
cd EMS_Agent

# Create production environment file
cp .env.example .env.production
```

Edit `.env.production`:
```bash
# Environment
ENVIRONMENT=production
MICROSERVICES_MODE=true
DEBUG=false
LOG_LEVEL=WARNING

# Database
MONGODB_URI=mongodb+srv://prod_user:secure_password@prod-cluster.mongodb.net/
MONGODB_DATABASE=EMS_Database_Prod

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Security
JWT_SECRET_KEY=super-secure-jwt-secret-256-bit-key
API_KEY=production-api-key-secure
ADMIN_PASSWORD=secure-admin-password

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/ems-agent.crt
SSL_KEY_PATH=/etc/ssl/private/ems-agent.key

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_PASSWORD=secure-grafana-password
SENTRY_DSN=https://your-sentry-dsn

# Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notifications@yourcompany.com
SMTP_PASSWORD=app-specific-password
```

#### 3. SSL Certificate Setup

**Option A: Let's Encrypt (Recommended)**
```bash
# Install Certbot
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /etc/ssl/certs/ems-agent.crt
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /etc/ssl/private/ems-agent.key
```

**Option B: Self-signed (Development/Testing)**
```bash
# Generate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/ems-agent.key \
  -out /etc/ssl/certs/ems-agent.crt
```

#### 4. Deploy with Production Configuration

```bash
# Set environment
export ENVIRONMENT=production

# Deploy with production compose file
docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d

# Verify deployment
curl -k https://your-domain.com/health
```

### Production Optimization

#### 1. Resource Allocation

Edit `docker-compose.production.yml`:
```yaml
version: '3.8'
services:
  data-ingestion:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  analytics:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'

  gateway:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first
```

#### 2. Load Balancer Configuration

Create `nginx/nginx.conf`:
```nginx
upstream ems_gateway {
    least_conn;
    server gateway:8000 max_fails=3 fail_timeout=30s;
    server gateway:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/ems-agent.crt;
    ssl_certificate_key /etc/ssl/private/ems-agent.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://ems_gateway;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Health check
        proxy_next_upstream error timeout http_500 http_502 http_503;
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://ems_gateway;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3.0+ (optional)

### 1. Create Namespace

```bash
kubectl create namespace ems-agent
kubectl config set-context --current --namespace=ems-agent
```

### 2. Create Secrets

```bash
# Database secret
kubectl create secret generic mongodb-secret \
  --from-literal=uri='mongodb+srv://user:pass@cluster.mongodb.net/' \
  --from-literal=database='EMS_Database'

# Application secrets
kubectl create secret generic ems-secrets \
  --from-literal=jwt-secret='your-jwt-secret' \
  --from-literal=api-key='your-api-key' \
  --from-literal=admin-password='admin-password'

# SSL certificates
kubectl create secret tls ems-tls \
  --cert=/path/to/tls.crt \
  --key=/path/to/tls.key
```

### 3. Create ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ems-config
data:
  ENVIRONMENT: "production"
  MICROSERVICES_MODE: "true"
  LOG_LEVEL: "INFO"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  PROMETHEUS_ENABLED: "true"
```

```bash
kubectl apply -f k8s/configmap.yaml
```

### 4. Deploy Redis

```yaml
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

### 5. Deploy EMS Services

```yaml
# k8s/ems-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ems-gateway
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ems-gateway
  template:
    metadata:
      labels:
        app: ems-gateway
    spec:
      containers:
      - name: gateway
        image: ems-agent/gateway:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: ems-config
        - secretRef:
            name: ems-secrets
        - secretRef:
            name: mongodb-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ems-gateway-service
spec:
  selector:
    app: ems-gateway
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ems-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: ems-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ems-gateway-service
            port:
              number: 8000
```

### 6. Deploy All Services

```bash
# Apply all configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
kubectl get services
kubectl get ingress

# Check logs
kubectl logs -f deployment/ems-gateway
```

### 7. Auto-scaling Configuration

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ems-gateway-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ems-gateway
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Cloud Deployment

### AWS Deployment

#### 1. ECS with Fargate

```json
{
  "family": "ems-agent",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "ems-gateway",
      "image": "your-account.dkr.ecr.region.amazonaws.com/ems-agent:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "MONGODB_URI",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:ems/mongodb"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ems-agent",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### 2. Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name ems-agent-alb \
  --subnets subnet-12345 subnet-67890 \
  --security-groups sg-12345

# Create target group
aws elbv2 create-target-group \
  --name ems-agent-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-12345 \
  --target-type ip \
  --health-check-path /health
```

### Google Cloud Platform

#### 1. Cloud Run Deployment

```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ems-agent
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 100
      containers:
      - image: gcr.io/PROJECT_ID/ems-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: production
        - name: MONGODB_URI
          valueFrom:
            secretKeyRef:
              name: mongodb-secret
              key: uri
        resources:
          limits:
            cpu: "2"
            memory: "2Gi"
```

```bash
# Deploy to Cloud Run
gcloud run services replace cloudrun.yaml --region=us-central1
```

### Azure Deployment

#### 1. Azure Container Instances

```json
{
  "apiVersion": "2021-07-01",
  "type": "Microsoft.ContainerInstance/containerGroups",
  "name": "ems-agent",
  "location": "East US",
  "properties": {
    "containers": [
      {
        "name": "ems-gateway",
        "properties": {
          "image": "yourregistry.azurecr.io/ems-agent:latest",
          "ports": [
            {
              "port": 8000,
              "protocol": "TCP"
            }
          ],
          "environmentVariables": [
            {
              "name": "ENVIRONMENT",
              "value": "production"
            }
          ],
          "resources": {
            "requests": {
              "cpu": 1,
              "memoryInGB": 2
            }
          }
        }
      }
    ],
    "osType": "Linux",
    "ipAddress": {
      "type": "Public",
      "ports": [
        {
          "port": 8000,
          "protocol": "TCP"
        }
      ]
    }
  }
}
```

---

## Security Considerations

### 1. Environment Variables and Secrets

**Never commit secrets to version control:**

```bash
# Use environment-specific files
.env.development
.env.staging  
.env.production

# Add to .gitignore
echo ".env*" >> .gitignore
echo "!.env.example" >> .gitignore
```

**Use secret management services:**
- **AWS**: Secrets Manager
- **GCP**: Secret Manager
- **Azure**: Key Vault
- **Kubernetes**: Secrets

### 2. Network Security

**Docker Network Isolation:**
```yaml
# docker-compose.yml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

services:
  gateway:
    networks:
      - frontend
      - backend
  
  analytics:
    networks:
      - backend  # Only internal access
```

**Firewall Configuration:**
```bash
# Ubuntu UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 3. SSL/TLS Configuration

**Strong SSL Configuration:**
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 4. Database Security

**MongoDB Security:**
```javascript
// Create application user with limited permissions
use EMS_Database
db.createUser({
  user: "ems_app",
  pwd: "secure_password",
  roles: [
    { role: "readWrite", db: "EMS_Database" }
  ]
})

// Enable authentication
// In mongod.conf:
// security:
//   authorization: enabled
```

### 5. API Security

**Rate Limiting:**
```python
# In gateway configuration
rate_limit:
  requests_per_minute: 100
  burst: 20
  
# IP-based blocking
blocked_ips:
  - "192.168.1.100"
  - "10.0.0.50"
```

**API Key Management:**
```python
# Rotate API keys regularly
API_KEY_ROTATION_DAYS=30

# Use different keys per environment
DEV_API_KEY=dev-key-12345
PROD_API_KEY=prod-key-67890
```

---

## Monitoring Setup

### 1. Prometheus Configuration

Create `monitoring/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ems-services'
    static_configs:
      - targets: 
        - 'gateway:8000'
        - 'data-ingestion:8001'
        - 'analytics:8002'
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 2. Grafana Dashboards

Create `monitoring/grafana/dashboards/ems-overview.json`:
```json
{
  "dashboard": {
    "title": "EMS Agent Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph", 
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "{{service}}"
          }
        ]
      }
    ]
  }
}
```

### 3. Alerting Rules

Create `monitoring/rules/ems-alerts.yml`:
```yaml
groups:
  - name: ems.rules
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.service }}"

      - alert: DatabaseConnectionFailed
        expr: mongodb_up == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Database connection failed"
```

---

## Backup and Recovery

### 1. Database Backup

**MongoDB Atlas (Managed):**
- Enable automatic backups in Atlas console
- Configure backup retention policy
- Set up cross-region backups for DR

**Self-hosted MongoDB:**
```bash
#!/bin/bash
# backup-mongodb.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mongodb"
DB_NAME="EMS_Database"

# Create backup
mongodump --uri="$MONGODB_URI" --db=$DB_NAME --out=$BACKUP_DIR/$DATE

# Compress backup
tar -czf $BACKUP_DIR/ems_backup_$DATE.tar.gz -C $BACKUP_DIR $DATE

# Remove uncompressed backup
rm -rf $BACKUP_DIR/$DATE

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "ems_backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed: ems_backup_$DATE.tar.gz"
```

### 2. Application Configuration Backup

```bash
#!/bin/bash
# backup-config.sh

BACKUP_DIR="/backups/config"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR/$DATE

# Backup configuration files
cp -r config/ $BACKUP_DIR/$DATE/
cp docker-compose*.yml $BACKUP_DIR/$DATE/
cp .env.production $BACKUP_DIR/$DATE/

# Backup Kubernetes manifests
if [ -d "k8s/" ]; then
    cp -r k8s/ $BACKUP_DIR/$DATE/
fi

# Create archive
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz -C $BACKUP_DIR $DATE

# Cleanup
rm -rf $BACKUP_DIR/$DATE

echo "Configuration backup completed: config_backup_$DATE.tar.gz"
```

### 3. Disaster Recovery Plan

**Recovery Time Objective (RTO):** 30 minutes
**Recovery Point Objective (RPO):** 1 hour

**Recovery Steps:**

1. **Assess Impact:**
   ```bash
   # Check service status
   curl -f https://your-domain.com/health || echo "Service down"
   
   # Check database connectivity
   mongosh "$MONGODB_URI" --eval "db.adminCommand('ping')"
   ```

2. **Restore Database:**
   ```bash
   # Restore from backup
   mongorestore --uri="$MONGODB_URI" --db=EMS_Database /path/to/backup
   ```

3. **Redeploy Application:**
   ```bash
   # Pull latest images
   docker-compose pull
   
   # Restart services
   docker-compose up -d
   
   # Verify health
   curl -f https://your-domain.com/health
   ```

---

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

**Check logs:**
```bash
docker-compose logs service-name
```

**Common causes:**
- Database connection issues
- Port conflicts
- Missing environment variables
- Insufficient permissions

**Solutions:**
```bash
# Check port usage
netstat -tlnp | grep :8000

# Check environment variables
docker-compose config

# Check file permissions
ls -la config/
```

#### 2. Database Connection Issues

**Test connectivity:**
```bash
# From container
docker-compose exec gateway python -c "
from pymongo import MongoClient
client = MongoClient('$MONGODB_URI')
print(client.admin.command('ping'))
"

# Network connectivity
telnet cluster.mongodb.net 27017
```

**Common solutions:**
- Verify connection string
- Check firewall rules
- Validate credentials
- Ensure database exists

#### 3. High Memory Usage

**Monitor resource usage:**
```bash
# Check container stats
docker stats

# Check system resources
free -h
df -h
```

**Optimization steps:**
```bash
# Increase container limits
# In docker-compose.yml:
services:
  analytics:
    deploy:
      resources:
        limits:
          memory: 4G

# Clean up unused resources
docker system prune -f
```

#### 4. SSL Certificate Issues

**Check certificate:**
```bash
# Verify certificate
openssl x509 -in /etc/ssl/certs/ems-agent.crt -text -noout

# Check expiration
openssl x509 -in /etc/ssl/certs/ems-agent.crt -checkend 86400
```

**Renew Let's Encrypt:**
```bash
sudo certbot renew --dry-run
sudo certbot renew
sudo docker-compose restart nginx
```

### Performance Tuning

#### 1. Database Optimization

**MongoDB Indexes:**
```javascript
// Create compound indexes
db.ems_raw_data.createIndex({ "equipment_id": 1, "timestamp": 1 })
db.ems_raw_data.createIndex({ "timestamp": 1 })
db.ems_anomalies.createIndex({ "detected_at": 1 })

// Check index usage
db.ems_raw_data.explain("executionStats").find({"equipment_id": "IKC0073"})
```

**Connection Pooling:**
```yaml
# Increase pool sizes for production
mongodb:
  max_pool_size: 50
  min_pool_size: 10
```

#### 2. Application Optimization

**Async Processing:**
```python
# Use async operations
async def process_batch(data):
    tasks = [process_record(record) for record in data]
    results = await asyncio.gather(*tasks)
    return results
```

**Caching:**
```python
# Implement Redis caching
@cache(expire=300)  # 5 minutes
async def get_equipment_metadata(equipment_id):
    return await database.find_one({"_id": equipment_id})
```

#### 3. Load Balancing

**Nginx Optimization:**
```nginx
# Increase worker processes
worker_processes auto;
worker_connections 1024;

# Enable keep-alive
upstream ems_gateway {
    keepalive 32;
    server gateway:8000;
}

# Gzip compression
gzip on;
gzip_types text/plain application/json;
```

### Monitoring and Alerts

**Health Check Script:**
```bash
#!/bin/bash
# health-check.sh

SERVICES=("gateway:8000" "data-ingestion:8001" "analytics:8002")

for service in "${SERVICES[@]}"; do
    if curl -f --max-time 5 "http://$service/health" > /dev/null 2>&1; then
        echo "✓ $service is healthy"
    else
        echo "✗ $service is unhealthy"
        # Send alert
        curl -X POST "https://hooks.slack.com/..." \
             -d "{\"text\": \"🚨 $service is down!\"}"
    fi
done
```

**Log Analysis:**
```bash
# Find errors in logs
docker-compose logs | grep -i error

# Monitor real-time logs
docker-compose logs -f --tail=100

# Analyze specific service
docker-compose logs analytics | grep "anomaly detected"
```

This deployment guide provides comprehensive instructions for deploying EMS Agent across different environments and platforms. Choose the deployment method that best fits your infrastructure and requirements.
