#!/usr/bin/env python3
"""
API Gateway for EMS Microservices
Provides load balancing, service discovery, and unified API interface
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import httpx
import uvicorn
import redis.asyncio as redis
import websockets
from contextlib import asynccontextmanager
import websockets

from common.base_service import LoadBalancer
from common.config_manager import ConfigManager

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


class CircuitBreakerGateway:
    """Circuit breaker for gateway requests"""
    
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.service_states = {}  # service_name -> {failures, last_failure, state}
    
    async def call_service(self, service_name: str, func, *args, **kwargs):
        """Call service with circuit breaker protection"""
        service_state = self.service_states.get(service_name, {
            'failures': 0,
            'last_failure': None,
            'state': 'closed'
        })
        
        # Check if circuit is open
        if service_state['state'] == 'open':
            if self._should_attempt_reset(service_state):
                service_state['state'] = 'half-open'
            else:
                raise HTTPException(
                    status_code=503,
                    detail=f"Service {service_name} is currently unavailable"
                )
        
        try:
            result = await func(*args, **kwargs)
            
            # Reset on success
            if service_state['state'] == 'half-open':
                service_state['failures'] = 0
                service_state['state'] = 'closed'
            
            self.service_states[service_name] = service_state
            return result
            
        except Exception as e:
            service_state['failures'] += 1
            service_state['last_failure'] = datetime.now()
            
            if service_state['failures'] >= self.failure_threshold:
                service_state['state'] = 'open'
            
            self.service_states[service_name] = service_state
            raise e
    
    def _should_attempt_reset(self, service_state: Dict) -> bool:
        """Check if circuit should attempt reset"""
        if not service_state['last_failure']:
            return False
        
        time_since_failure = (datetime.now() - service_state['last_failure']).total_seconds()
        return time_since_failure > self.recovery_timeout
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        return {
            service: {
                'state': state['state'],
                'failures': state['failures'],
                'last_failure': state['last_failure'].isoformat() if state['last_failure'] else None
            }
            for service, state in self.service_states.items()
        }


class APIGateway:
    """API Gateway for EMS microservices"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = None
        self.load_balancer = None
        self.circuit_breaker = CircuitBreakerGateway()
        self.app = self._create_fastapi_app()
        
        # Service configuration
        self.services = {
            'data_ingestion': {
                'default_port': 8001,
                'health_endpoint': '/health',
                'timeout': 30
            },
            'analytics': {
                'default_port': 8002,
                'health_endpoint': '/health',
                'timeout': 60
            },
            'query_processor': {
                'default_port': 8003,
                'health_endpoint': '/health',
                'timeout': 30
            },
            'notification': {
                'default_port': 8004,
                'health_endpoint': '/health',
                'timeout': 10
            },
            'realtime_streaming': {
                'default_port': 8005,
                'health_endpoint': '/health',
                'timeout': 10
            },
            'advanced_ml': {
                'default_port': 8006,
                'health_endpoint': '/health',
                'timeout': 10
            },
            'security': {
                'default_port': 8007,
                'health_endpoint': '/health',
                'timeout': 10
            },
            'monitoring': {
                'default_port': 8008,
                'health_endpoint': '/health',
                'timeout': 10
            }
        }
    
    async def initialize(self):
        """Initialize API Gateway"""
        try:
            # Initialize Redis for service discovery
            redis_config = self.config.get('redis', {})
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0)
            )
            
            # Initialize load balancer
            self.load_balancer = LoadBalancer(self.redis_client)
            
            # Start health check monitoring
            asyncio.create_task(self._monitor_services())
            
            logger.info("API Gateway initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize API Gateway: {e}")
            raise
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            await self.initialize()
            yield
            # Shutdown
            if self.redis_client:
                await self.redis_client.close()
        
        app = FastAPI(
            title="EMS API Gateway",
            description="Unified API Gateway for EMS Microservices",
            version="1.0.0",
            lifespan=lifespan
        )
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add middleware for request logging and metrics
        self._add_middleware(app)
        
        # Add routes
        self._add_routes(app)
        
        return app
    
    def _add_middleware(self, app: FastAPI):
        """Add middleware for logging and metrics"""
        
        @app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = datetime.now()
            
            # Log request
            logger.info(f"Request: {request.method} {request.url}")
            
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log response
            logger.info(f"Response: {response.status_code} - {process_time:.2f}ms")
            
            return response
        
        @app.middleware("http")
        async def rate_limiting(request: Request, call_next):
            """Simple rate limiting middleware"""
            if self.redis_client:
                client_ip = request.client.host
                key = f"rate_limit:{client_ip}"
                
                # Get current request count
                current_count = await self.redis_client.get(key)
                
                if current_count and int(current_count) > 100:  # 100 requests per minute
                    return JSONResponse(
                        status_code=429,
                        content={"error": "Rate limit exceeded"}
                    )
                
                # Increment counter
                await self.redis_client.incr(key)
                await self.redis_client.expire(key, 60)  # 1 minute window
            
            return await call_next(request)
    
    def _add_routes(self, app: FastAPI):
        """Add gateway routes"""
        
        @app.get("/health")
        async def gateway_health():
            """Gateway health check"""
            service_statuses = await self._check_all_services_health()
            
            overall_status = "healthy" if all(
                status.get('status') == 'healthy' 
                for status in service_statuses.values()
            ) else "degraded"
            
            return {
                "gateway": "healthy",
                "overall_status": overall_status,
                "services": service_statuses,
                "circuit_breaker": self.circuit_breaker.get_service_status(),
                "timestamp": datetime.now().isoformat()
            }
        
        @app.get("/services")
        async def list_services():
            """List all available services"""
            service_list = []
            
            for service_name in self.services:
                instances = await self._get_service_instances(service_name)
                service_list.append({
                    "name": service_name,
                    "instances": len(instances),
                    "status": "available" if instances else "unavailable"
                })
            
            return {"services": service_list}
        
        # Data Ingestion Service Routes
        @app.post("/api/v1/data/ingest/excel")
        async def ingest_excel(request: Dict[str, Any]):
            return await self._proxy_request("data_ingestion", "POST", "/ingest/excel", request)
        
        @app.post("/api/v1/data/ingest/realtime")
        async def ingest_realtime(request: Dict[str, Any]):
            return await self._proxy_request("data_ingestion", "POST", "/ingest/realtime", request)
        
        @app.get("/api/v1/data/stats")
        async def data_stats():
            return await self._proxy_request("data_ingestion", "GET", "/stats")
        
        # Analytics Service Routes
        @app.post("/api/v1/analytics/anomalies")
        async def detect_anomalies(request: Dict[str, Any]):
            return await self._proxy_request("analytics", "POST", "/detect_anomalies", request)
        
        @app.post("/api/v1/analytics/predict")
        async def predict(request: Dict[str, Any]):
            return await self._proxy_request("analytics", "POST", "/predict", request)
        
        @app.get("/api/v1/analytics/summary")
        async def analytics_summary():
            return await self._proxy_request("analytics", "GET", "/analytics/summary")
        
        # Query Processor Routes
        @app.post("/api/v1/query")
        async def process_query(request: Dict[str, Any]):
            return await self._proxy_request("query_processor", "POST", "/query", request)
        
        # Real-time Streaming Service Routes
        @app.websocket("/api/v1/realtime/stream")
        async def realtime_stream(websocket):
            """WebSocket endpoint for real-time data streaming"""
            # This would proxy to the realtime streaming service
            await self._proxy_websocket("realtime_streaming", "/stream", websocket)
        
        @app.post("/api/v1/realtime/sensor_data")
        async def add_sensor_data(request: Dict[str, Any]):
            return await self._proxy_request("realtime_streaming", "POST", "/sensor_data", request)
        
        @app.get("/api/v1/realtime/active_alerts")
        async def get_active_alerts():
            return await self._proxy_request("realtime_streaming", "GET", "/active_alerts")
        
        @app.post("/api/v1/realtime/alert_rules")
        async def create_alert_rule(request: Dict[str, Any]):
            return await self._proxy_request("realtime_streaming", "POST", "/alert_rules", request)
        
        # Advanced ML Service Routes
        @app.post("/api/v1/ml/anomaly_detection")
        async def advanced_anomaly_detection(request: Dict[str, Any]):
            return await self._proxy_request("advanced_ml", "POST", "/anomaly_detection", request)
        
        @app.post("/api/v1/ml/forecast")
        async def energy_forecast(request: Dict[str, Any]):
            return await self._proxy_request("advanced_ml", "POST", "/forecast", request)
        
        @app.post("/api/v1/ml/predictive_maintenance")
        async def predictive_maintenance(request: Dict[str, Any]):
            return await self._proxy_request("advanced_ml", "POST", "/predictive_maintenance", request)
        
        @app.get("/api/v1/ml/models")
        async def list_ml_models():
            return await self._proxy_request("advanced_ml", "GET", "/models")
        
        # Security Service Routes
        @app.post("/api/v1/auth/login")
        async def login(request: Dict[str, Any]):
            return await self._proxy_request("security", "POST", "/auth/login", request)
        
        @app.post("/api/v1/auth/register")
        async def register(request: Dict[str, Any]):
            return await self._proxy_request("security", "POST", "/auth/register", request)
        
        @app.post("/api/v1/auth/refresh")
        async def refresh_token(request: Dict[str, Any], token: Optional[str] = Depends(security)):
            return await self._proxy_request("security", "POST", "/auth/refresh", request, token)
        
        @app.get("/api/v1/auth/profile")
        async def get_profile(token: Optional[str] = Depends(security)):
            return await self._proxy_request("security", "GET", "/auth/profile", {}, token)
        
        @app.get("/api/v1/security/audit")
        async def get_audit_logs(token: Optional[str] = Depends(security)):
            return await self._proxy_request("security", "GET", "/audit", {}, token)
        
        # Monitoring Service Routes
        @app.get("/api/v1/monitoring/metrics")
        async def get_metrics():
            return await self._proxy_request("monitoring", "GET", "/metrics")
        
        @app.get("/api/v1/monitoring/prometheus")
        async def prometheus_metrics():
            return await self._proxy_request("monitoring", "GET", "/prometheus")
        
        @app.get("/api/v1/monitoring/health")
        async def system_health():
            return await self._proxy_request("monitoring", "GET", "/health")
        
        @app.get("/api/v1/monitoring/alerts")
        async def get_monitoring_alerts():
            return await self._proxy_request("monitoring", "GET", "/alerts")
        
        @app.post("/api/v1/monitoring/alerts")
        async def create_monitoring_alert(request: Dict[str, Any]):
            return await self._proxy_request("monitoring", "POST", "/alerts", request)
        
        # Notification Service Routes
        @app.post("/api/v1/notifications/send")
        async def send_notification(request: Dict[str, Any]):
            return await self._proxy_request("notification", "POST", "/send", request)
        
        @app.get("/api/v1/notifications")
        async def get_notifications():
            return await self._proxy_request("notification", "GET", "/notifications")
        
        # Aggregated endpoints
        @app.get("/api/v1/dashboard")
        async def dashboard_data():
            """Get aggregated dashboard data from multiple services"""
            try:
                # Fetch data from multiple services concurrently
                tasks = [
                    self._proxy_request("data_ingestion", "GET", "/stats"),
                    self._proxy_request("analytics", "GET", "/analytics/summary"),
                    self._check_all_services_health()
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                data_stats = results[0] if not isinstance(results[0], Exception) else {}
                analytics_summary = results[1] if not isinstance(results[1], Exception) else {}
                service_health = results[2] if not isinstance(results[2], Exception) else {}
                
                return {
                    "data_ingestion": data_stats,
                    "analytics": analytics_summary,
                    "service_health": service_health,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting dashboard data: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _proxy_request(
        self, 
        service_name: str, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Proxy request to microservice with load balancing and circuit breaker"""
        
        async def make_request():
            # Get service instance
            instance = await self._get_service_instances(service_name)
            if not instance:
                raise HTTPException(
                    status_code=503,
                    detail=f"Service {service_name} is not available"
                )
            
            # Make HTTP request
            url = f"http://{instance['host']}:{instance['port']}{endpoint}"
            timeout = self.services[service_name].get('timeout', 30)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url)
                else:
                    raise HTTPException(status_code=405, detail="Method not allowed")
                
                if response.status_code >= 400:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=response.text
                    )
                
                return response.json()
        
        # Use circuit breaker
        return await self.circuit_breaker.call_service(service_name, make_request)
    
    async def _proxy_websocket(self, service_name: str, endpoint: str, websocket):
        """Proxy WebSocket connection to microservice"""
        try:
            # Get service instance
            instance = await self._get_service_instances(service_name)
            if not instance:
                await websocket.close(code=1011, reason="Service unavailable")
                return
            
            # Connect to backend WebSocket
            url = f"ws://{instance['host']}:{instance['port']}{endpoint}"
            
            async with websockets.connect(url) as backend_ws:
                await websocket.accept()
                
                async def forward_to_backend():
                    async for message in websocket.iter_text():
                        await backend_ws.send(message)
                
                async def forward_to_client():
                    async for message in backend_ws:
                        await websocket.send_text(message)
                
                # Run both directions concurrently
                await asyncio.gather(
                    forward_to_backend(),
                    forward_to_client(),
                    return_exceptions=True
                )
        
        except Exception as e:
            logger.error(f"WebSocket proxy error: {e}")
            if not websocket.client_state.disconnected:
                await websocket.close(code=1011, reason="Proxy error")

    async def _get_service_instances(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get available service instance using load balancer"""
        if self.load_balancer:
            return await self.load_balancer.get_service_instance(service_name)
        
        # Fallback to default configuration
        service_config = self.services.get(service_name)
        if service_config:
            return {
                'host': 'localhost',
                'port': service_config['default_port']
            }
        
        return None
    
    async def _check_all_services_health(self) -> Dict[str, Any]:
        """Check health of all services"""
        health_results = {}
        
        for service_name in self.services:
            try:
                result = await self._proxy_request(
                    service_name, 
                    "GET", 
                    self.services[service_name]['health_endpoint']
                )
                health_results[service_name] = result
                
            except Exception as e:
                health_results[service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_results
    
    async def _monitor_services(self):
        """Monitor service health periodically"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                health_results = await self._check_all_services_health()
                
                # Log unhealthy services
                for service_name, health in health_results.items():
                    if health.get('status') != 'healthy':
                        logger.warning(f"Service {service_name} is unhealthy: {health}")
                
                # Store health status in Redis
                if self.redis_client:
                    await self.redis_client.setex(
                        "gateway_health_check",
                        60,  # 1 minute TTL
                        json.dumps(health_results, default=str)
                    )
                
            except Exception as e:
                logger.error(f"Error in service monitoring: {e}")


def create_api_gateway():
    """Factory function to create API gateway"""
    config_manager = ConfigManager("gateway")
    config = config_manager.get_all_config()
    
    return APIGateway(config)


async def run_gateway():
    """Run the API gateway"""
    gateway = create_api_gateway()
    
    config = uvicorn.Config(
        gateway.app,
        host="0.0.0.0",
        port=gateway.config.get('port', 8000),
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run_gateway())
