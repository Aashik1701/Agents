# API Reference - EMS Agent

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

All API requests require authentication using one of the following methods:

### API Key Authentication
```http
Authorization: Bearer YOUR_API_KEY
```

### JWT Token Authentication
```http
Authorization: Bearer YOUR_JWT_TOKEN
```

## Response Format

All responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "data": {},
  "timestamp": "2025-06-25T10:30:00Z",
  "processing_time": "150ms"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid equipment ID format",
    "details": {}
  },
  "timestamp": "2025-06-25T10:30:00Z"
}
```

## HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

---

## System Endpoints

### Health Check
Get system health status.

```http
GET /health
```

**Response:**
```json
{
  "gateway": "healthy",
  "overall_status": "healthy",
  "services": {
    "data_ingestion": {
      "service": "data_ingestion",
      "status": "healthy",
      "uptime_seconds": 3600,
      "last_health_check": "2025-06-25T10:29:30Z"
    },
    "analytics": {
      "service": "analytics", 
      "status": "healthy",
      "uptime_seconds": 3598,
      "last_health_check": "2025-06-25T10:29:28Z"
    }
  },
  "circuit_breaker": {
    "data_ingestion": {
      "state": "closed",
      "failures": 0,
      "last_failure": null
    }
  },
  "timestamp": "2025-06-25T10:30:00Z"
}
```

### List Services
Get information about all available services.

```http
GET /services
```

**Response:**
```json
{
  "services": [
    {
      "name": "data_ingestion",
      "instances": 2,
      "status": "available"
    },
    {
      "name": "analytics",
      "instances": 1,
      "status": "available"
    }
  ]
}
```

### Dashboard Data
Get aggregated dashboard data from all services.

```http
GET /api/v1/dashboard
```

**Response:**
```json
{
  "data_ingestion": {
    "total_records": 125000,
    "total_errors": 45,
    "recent_ingestions": [
      {
        "type": "excel_ingestion",
        "status": "completed",
        "processed_count": 5000,
        "start_time": "2025-06-25T09:00:00Z"
      }
    ]
  },
  "analytics": {
    "anomalies_detected_24h": 12,
    "predictions_generated_24h": 48,
    "models": {
      "anomaly_detector": {
        "loaded": true,
        "type": "IsolationForest"
      }
    }
  },
  "service_health": {
    "data_ingestion": { "status": "healthy" },
    "analytics": { "status": "healthy" }
  },
  "timestamp": "2025-06-25T10:30:00Z"
}
```

---

## Data Ingestion Endpoints

### Excel File Ingestion
Upload and process Excel files containing energy meter data.

```http
POST /api/v1/data/ingest/excel
```

**Request Body:**
```json
{
  "file_path": "EMS_Energy_Meter_Data.xlsx"
}
```

**Response:**
```json
{
  "message": "Excel file processing started",
  "file_path": "EMS_Energy_Meter_Data.xlsx",
  "task_id": "task_12345"
}
```

### Real-time Data Ingestion
Ingest individual data points in real-time.

```http
POST /api/v1/data/ingest/realtime
```

**Request Body:**
```json
{
  "equipment_id": "IKC0073",
  "timestamp": "2025-06-25T10:30:00Z",
  "voltage": 220.5,
  "current": 15.2,
  "power_factor": 0.89,
  "temperature": 25.3,
  "cfm": 850
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "record_id": "60d1f8c9e123456789abcdef"
  }
}
```

### Data Validation
Validate data format without ingesting.

```http
POST /api/v1/data/validate
```

**Request Body:**
```json
{
  "data": [
    {
      "equipment_id": "IKC0073",
      "timestamp": "2025-06-25T10:30:00Z",
      "voltage": 220.5,
      "current": 15.2,
      "power_factor": 0.89
    }
  ]
}
```

**Response:**
```json
{
  "validation_results": [
    {
      "index": 0,
      "status": "valid",
      "record": {
        "equipment_id": "IKC0073",
        "timestamp": "2025-06-25T10:30:00Z",
        "voltage": 220.5,
        "current": 15.2,
        "power_factor": 0.89
      }
    }
  ]
}
```

### Ingestion Statistics
Get data ingestion statistics and metrics.

```http
GET /api/v1/data/stats
```

**Response:**
```json
{
  "total_records": 125000,
  "total_errors": 45,
  "recent_ingestions": [
    {
      "type": "excel_ingestion",
      "status": "completed",
      "processed_count": 5000,
      "error_count": 2,
      "start_time": "2025-06-25T09:00:00Z"
    }
  ],
  "timestamp": "2025-06-25T10:30:00Z"
}
```

---

## Analytics Endpoints

### Anomaly Detection
Detect anomalies in energy consumption data.

```http
POST /api/v1/analytics/anomalies
```

**Request Body:**
```json
{
  "equipment_ids": ["IKC0073", "IKC0076"],
  "time_range": {
    "start": "2025-06-24T00:00:00Z",
    "end": "2025-06-25T00:00:00Z"
  }
}
```

**Response:**
```json
{
  "anomalies": [
    {
      "equipment_id": "IKC0073",
      "timestamp": "2025-06-24T14:30:00Z",
      "detected_at": "2025-06-24T14:31:00Z",
      "anomaly_score": -0.45,
      "severity": "high",
      "type": "statistical_anomaly",
      "features": {
        "voltage": 245.2,
        "current": 25.8,
        "power_factor": 0.65
      }
    }
  ]
}
```

### Energy Consumption Prediction
Generate energy consumption predictions.

```http
POST /api/v1/analytics/predict
```

**Request Body:**
```json
{
  "equipment_id": "IKC0073",
  "hours": 24
}
```

**Response:**
```json
{
  "predictions": {
    "equipment_id": "IKC0073",
    "predictions": [
      {
        "timestamp": "2025-06-25T11:00:00Z",
        "predicted_power": 3350.5,
        "confidence": 0.85
      },
      {
        "timestamp": "2025-06-25T12:00:00Z",
        "predicted_power": 3420.2,
        "confidence": 0.87
      }
    ],
    "generated_at": "2025-06-25T10:30:00Z"
  }
}
```

### Analytics Summary
Get analytics overview and model status.

```http
GET /api/v1/analytics/summary
```

**Response:**
```json
{
  "anomalies_detected_24h": 12,
  "predictions_generated_24h": 48,
  "models": {
    "anomaly_detector": {
      "loaded": true,
      "type": "IsolationForest"
    }
  },
  "status": "active",
  "timestamp": "2025-06-25T10:30:00Z"
}
```

### Model Training
Retrain machine learning models.

```http
POST /api/v1/analytics/train
```

**Response:**
```json
{
  "message": "Model training started",
  "estimated_completion": "2025-06-25T11:00:00Z"
}
```

---

## Query Processing Endpoints

### Natural Language Query
Process natural language queries about energy data.

```http
POST /api/v1/query
```

**Request Body:**
```json
{
  "query": "Show me the average power consumption for IKC0073 today",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "type": "ai_response",
  "message": "The average power consumption for equipment IKC0073 today is 3,245.6 kW. This represents a 5% increase compared to yesterday.",
  "intent": "data_query",
  "data": {
    "equipment_id": "IKC0073",
    "date": "2025-06-25",
    "average_power": 3245.6,
    "comparison": {
      "yesterday": 3092.1,
      "change_percent": 5.0
    }
  },
  "charts": [
    {
      "type": "line_chart",
      "title": "Power Consumption - IKC0073",
      "data": [...],
      "config": {...}
    }
  ],
  "processing_time": "145ms",
  "timestamp": "2025-06-25T10:30:00Z"
}
```

### Query History
Get user's query history.

```http
GET /api/v1/query/history?user_id={user_id}&limit=10
```

**Query Parameters:**
- `user_id` (required): User identifier
- `limit` (optional): Number of queries to return (default: 10)
- `offset` (optional): Offset for pagination (default: 0)

**Response:**
```json
{
  "queries": [
    {
      "id": "query_123",
      "query": "Show power consumption trends",
      "timestamp": "2025-06-25T10:25:00Z",
      "processing_time": "120ms",
      "intent": "data_query"
    }
  ],
  "total": 25,
  "limit": 10,
  "offset": 0
}
```

### Batch Query Processing
Process multiple queries in batch.

```http
POST /api/v1/query/batch
```

**Request Body:**
```json
{
  "queries": [
    {
      "id": "q1",
      "query": "Average power consumption today",
      "user_id": "user123"
    },
    {
      "id": "q2", 
      "query": "Anomalies in the last hour",
      "user_id": "user123"
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "query_id": "q1",
      "success": true,
      "response": {...}
    },
    {
      "query_id": "q2",
      "success": true,
      "response": {...}
    }
  ],
  "processing_time": "320ms"
}
```

---

## Notification Endpoints

### Send Notification
Send notifications to users or systems.

```http
POST /api/v1/notifications/send
```

**Request Body:**
```json
{
  "type": "anomaly_alert",
  "recipient": "admin@company.com",
  "subject": "Energy Anomaly Detected",
  "message": "Anomaly detected in equipment IKC0073",
  "priority": "high",
  "data": {
    "equipment_id": "IKC0073",
    "anomaly_score": -0.45,
    "timestamp": "2025-06-25T10:30:00Z"
  }
}
```

**Response:**
```json
{
  "notification_id": "notif_12345",
  "status": "sent",
  "timestamp": "2025-06-25T10:30:00Z"
}
```

### Get Notifications
Retrieve notifications for a user.

```http
GET /api/v1/notifications?user_id={user_id}&status=unread&limit=20
```

**Query Parameters:**
- `user_id` (optional): Filter by user
- `status` (optional): Filter by status (read, unread, all)
- `type` (optional): Filter by notification type
- `limit` (optional): Number of notifications to return
- `offset` (optional): Offset for pagination

**Response:**
```json
{
  "notifications": [
    {
      "id": "notif_123",
      "type": "anomaly_alert",
      "subject": "Energy Anomaly Detected",
      "message": "Anomaly detected in equipment IKC0073",
      "priority": "high",
      "status": "unread",
      "created_at": "2025-06-25T10:30:00Z",
      "data": {
        "equipment_id": "IKC0073",
        "anomaly_score": -0.45
      }
    }
  ],
  "total": 5,
  "unread": 3
}
```

### Mark Notification as Read
Mark a notification as read.

```http
PUT /api/v1/notifications/{notification_id}/read
```

**Response:**
```json
{
  "notification_id": "notif_123",
  "status": "read",
  "read_at": "2025-06-25T10:35:00Z"
}
```

---

## Data Schemas

### Equipment Data Point
```json
{
  "equipment_id": "string",       // Required: Equipment identifier (e.g., "IKC0073")
  "timestamp": "datetime",        // Required: ISO 8601 timestamp
  "voltage": "number",           // Required: Voltage in volts
  "current": "number",           // Required: Current in amperes
  "power_factor": "number",      // Required: Power factor (0-1)
  "temperature": "number",       // Optional: Temperature in Celsius
  "cfm": "number",              // Optional: Air flow in CFM
  "frequency": "number",         // Optional: Frequency in Hz
  "power": "number"             // Optional: Power in watts
}
```

### Time Range
```json
{
  "start": "datetime",          // ISO 8601 start timestamp
  "end": "datetime"            // ISO 8601 end timestamp
}
```

### Anomaly
```json
{
  "equipment_id": "string",
  "timestamp": "datetime",
  "detected_at": "datetime",
  "anomaly_score": "number",     // Negative values indicate anomalies
  "severity": "string",          // "low", "medium", "high", "critical"
  "type": "string",             // "statistical_anomaly", "threshold_breach", etc.
  "features": "object",         // Values that triggered the anomaly
  "confidence": "number"        // Confidence score (0-1)
}
```

### Prediction
```json
{
  "timestamp": "datetime",
  "predicted_power": "number",
  "confidence": "number",       // Prediction confidence (0-1)
  "lower_bound": "number",      // Optional: Lower confidence interval
  "upper_bound": "number"       // Optional: Upper confidence interval
}
```

---

## Error Codes

### Data Ingestion Errors
- `INVALID_FILE_FORMAT`: Excel file format is invalid
- `MISSING_REQUIRED_COLUMNS`: Required columns missing from data
- `DATA_VALIDATION_FAILED`: Data validation failed
- `DUPLICATE_RECORDS`: Duplicate records detected
- `FILE_NOT_FOUND`: Specified file does not exist

### Analytics Errors
- `MODEL_NOT_LOADED`: ML model is not loaded
- `INSUFFICIENT_DATA`: Not enough data for analysis
- `INVALID_TIME_RANGE`: Invalid time range specified
- `EQUIPMENT_NOT_FOUND`: Equipment ID not found in database
- `PREDICTION_FAILED`: Prediction generation failed

### Query Processing Errors
- `QUERY_PARSING_FAILED`: Could not parse natural language query
- `INVALID_QUERY_SYNTAX`: Query syntax is invalid
- `QUERY_TIMEOUT`: Query execution timed out
- `UNSUPPORTED_QUERY_TYPE`: Query type not supported

### Notification Errors
- `INVALID_RECIPIENT`: Recipient address is invalid
- `NOTIFICATION_SEND_FAILED`: Failed to send notification
- `TEMPLATE_NOT_FOUND`: Notification template not found
- `RATE_LIMIT_EXCEEDED`: Notification rate limit exceeded

---

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Default Limit**: 100 requests per minute per IP
- **Authenticated Users**: 1000 requests per minute
- **Premium Users**: 10000 requests per minute

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

When rate limit is exceeded:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "retry_after": 60
  }
}
```

---

## Pagination

Endpoints that return lists support pagination:

### Request Parameters
- `limit`: Number of items per page (default: 20, max: 100)
- `offset`: Number of items to skip (default: 0)
- `sort`: Sort field (default: varies by endpoint)
- `order`: Sort order - "asc" or "desc" (default: "desc")

### Response Format
```json
{
  "data": [...],
  "pagination": {
    "total": 1000,
    "limit": 20,
    "offset": 0,
    "pages": 50,
    "current_page": 1,
    "has_next": true,
    "has_prev": false,
    "next_url": "/api/v1/endpoint?limit=20&offset=20",
    "prev_url": null
  }
}
```

---

## WebSocket API

For real-time updates, the system provides WebSocket endpoints:

### Connection
```javascript
ws://localhost:8000/ws/{user_id}
```

### Message Types

#### Subscribe to Real-time Data
```json
{
  "type": "subscribe",
  "channel": "equipment_data",
  "equipment_ids": ["IKC0073", "IKC0076"]
}
```

#### Subscribe to Anomaly Alerts
```json
{
  "type": "subscribe", 
  "channel": "anomaly_alerts",
  "severity": ["high", "critical"]
}
```

#### Real-time Data Message
```json
{
  "type": "equipment_data",
  "equipment_id": "IKC0073",
  "timestamp": "2025-06-25T10:30:00Z",
  "data": {
    "voltage": 220.5,
    "current": 15.2,
    "power_factor": 0.89
  }
}
```

#### Anomaly Alert Message
```json
{
  "type": "anomaly_alert",
  "equipment_id": "IKC0073",
  "severity": "high",
  "timestamp": "2025-06-25T10:30:00Z",
  "anomaly_score": -0.45
}
```

---

## SDKs and Client Libraries

### Python SDK
```python
from ems_client import EMSClient

client = EMSClient(base_url="http://localhost:8000", api_key="your-key")

# Ingest data
result = client.data.ingest_realtime({
    "equipment_id": "IKC0073",
    "voltage": 220.5,
    "current": 15.2
})

# Detect anomalies
anomalies = client.analytics.detect_anomalies(
    equipment_ids=["IKC0073"],
    time_range={"start": "2025-06-24T00:00:00Z", "end": "2025-06-25T00:00:00Z"}
)

# Process query
response = client.query.process("Show me power consumption for IKC0073 today")
```

### JavaScript SDK
```javascript
import { EMSClient } from 'ems-client-js';

const client = new EMSClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-key'
});

// Ingest data
const result = await client.data.ingestRealtime({
  equipment_id: 'IKC0073',
  voltage: 220.5,
  current: 15.2
});

// Detect anomalies
const anomalies = await client.analytics.detectAnomalies({
  equipment_ids: ['IKC0073'],
  time_range: {
    start: '2025-06-24T00:00:00Z',
    end: '2025-06-25T00:00:00Z'
  }
});
```

---

This API reference provides comprehensive documentation for all EMS Agent endpoints. For interactive API exploration, visit the auto-generated documentation at `/docs` when running the system.
