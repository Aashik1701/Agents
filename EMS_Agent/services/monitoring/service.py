#!/usr/bin/env python3
"""
Production-grade Monitoring Service for EMS
Comprehensive monitoring, metrics collection, alerting, observability, and SLA tracking
"""

import asyncio
import json
import logging
import time
import psutil
import statistics
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from collections import deque, defaultdict
import threading
import socket
import yaml
import aiofiles
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
import httpx
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST

from common.base_service import BaseService

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Enhanced metric data point with metadata"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    unit: str
    metric_type: str  # 'counter', 'gauge', 'histogram', 'summary'
    help_text: str = ""
    
    def to_prometheus_format(self) -> str:
        """Convert to Prometheus format"""
        labels_str = ','.join([f'{k}="{v}"' for k, v in self.labels.items()])
        if labels_str:
            return f'{self.name}{{{labels_str}}} {self.value} {int(self.timestamp.timestamp() * 1000)}'
        return f'{self.name} {self.value} {int(self.timestamp.timestamp() * 1000)}'


@dataclass
class Alert:
    """Enhanced alert definition with escalation"""
    alert_id: str
    name: str
    description: str
    severity: str  # critical, warning, info
    condition: str
    threshold: float
    comparison: str  # '>', '<', '>=', '<=', '==', '!='
    duration: int  # seconds - how long condition must be true
    evaluation_interval: int  # seconds
    is_active: bool
    created_at: datetime
    updated_at: datetime
    escalation_rules: List[Dict[str, Any]] = field(default_factory=list)
    notification_channels: List[str] = field(default_factory=list)
    runbook_url: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class AlertInstance:
    """Active alert instance"""
    instance_id: str
    alert_id: str
    fired_at: datetime
    resolved_at: Optional[datetime]
    current_value: float
    threshold: float
    labels: Dict[str, str]
    annotations: Dict[str, str]
    escalation_level: int = 0
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


@dataclass
class ServiceHealth:
    """Service health status"""
    service_name: str
    status: str  # 'healthy', 'degraded', 'unhealthy', 'unknown'
    last_check: datetime
    response_time: float
    error_count: int
    uptime_percentage: float
    endpoint: str
    version: str
    dependencies: List[str] = field(default_factory=list)
    custom_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class SLAMetrics:
    """SLA tracking metrics"""
    service_name: str
    sla_type: str  # 'availability', 'response_time', 'error_rate'
    target: float  # Target SLA (e.g., 99.9% availability)
    current: float  # Current SLA
    period: str  # 'daily', 'weekly', 'monthly'
    window_start: datetime
    window_end: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float


class PrometheusMetrics:
    """Prometheus metrics collector"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # System metrics
        self.cpu_usage = Gauge('ems_cpu_usage_percent', 'CPU usage percentage', registry=self.registry)
        self.memory_usage = Gauge('ems_memory_usage_percent', 'Memory usage percentage', registry=self.registry)
        self.disk_usage = Gauge('ems_disk_usage_percent', 'Disk usage percentage', registry=self.registry)
        
        # Service metrics
        self.http_requests_total = Counter(
            'ems_http_requests_total', 
            'Total HTTP requests', 
            ['service', 'method', 'status_code'], 
            registry=self.registry
        )
        self.http_request_duration = Histogram(
            'ems_http_request_duration_seconds', 
            'HTTP request duration', 
            ['service', 'method'], 
            registry=self.registry
        )
        
        # Database metrics
        self.db_connections = Gauge('ems_db_connections', 'Database connections', ['database'], registry=self.registry)
        self.db_query_duration = Histogram(
            'ems_db_query_duration_seconds', 
            'Database query duration', 
            ['database', 'operation'], 
            registry=self.registry
        )
        
        # Business metrics
        self.energy_readings_total = Counter(
            'ems_energy_readings_total', 
            'Total energy readings processed', 
            ['equipment_id'], 
            registry=self.registry
        )
        self.anomalies_detected_total = Counter(
            'ems_anomalies_detected_total', 
            'Total anomalies detected', 
            ['equipment_id', 'severity'], 
            registry=self.registry
        )
        
        # Service health metrics
        self.service_up = Gauge('ems_service_up', 'Service availability', ['service'], registry=self.registry)
        self.service_response_time = Gauge(
            'ems_service_response_time_seconds', 
            'Service response time', 
            ['service'], 
            registry=self.registry
        )
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        return generate_latest(self.registry).decode('utf-8')


class AlertManager:
    """Advanced alert management with escalation"""
    
    def __init__(self, redis_client, notification_service_url: str = None):
        self.redis = redis_client
        self.notification_service_url = notification_service_url
        self.active_alerts: Dict[str, AlertInstance] = {}
        self.alert_history = deque(maxlen=10000)
        self.escalation_timers: Dict[str, asyncio.Task] = {}
    
    async def evaluate_alert(self, alert: Alert, current_value: float, labels: Dict[str, str] = None) -> bool:
        """Evaluate alert condition"""
        labels = labels or {}
        
        try:
            # Evaluate condition
            triggered = self._evaluate_condition(alert.condition, current_value, alert.threshold, alert.comparison)
            
            alert_key = f"{alert.alert_id}_{hash(str(sorted(labels.items())))}"
            
            if triggered:
                if alert_key not in self.active_alerts:
                    # New alert
                    instance = AlertInstance(
                        instance_id=alert_key,
                        alert_id=alert.alert_id,
                        fired_at=datetime.now(),
                        resolved_at=None,
                        current_value=current_value,
                        threshold=alert.threshold,
                        labels=labels,
                        annotations={
                            'description': alert.description,
                            'runbook_url': alert.runbook_url or '',
                            'severity': alert.severity
                        }
                    )
                    
                    self.active_alerts[alert_key] = instance
                    await self._fire_alert(alert, instance)
                    
                    # Start escalation timer if rules exist
                    if alert.escalation_rules:
                        self.escalation_timers[alert_key] = asyncio.create_task(
                            self._handle_escalation(alert, instance)
                        )
                
                else:
                    # Update existing alert
                    self.active_alerts[alert_key].current_value = current_value
            
            else:
                if alert_key in self.active_alerts:
                    # Resolve alert
                    instance = self.active_alerts[alert_key]
                    instance.resolved_at = datetime.now()
                    
                    await self._resolve_alert(alert, instance)
                    
                    # Cancel escalation timer
                    if alert_key in self.escalation_timers:
                        self.escalation_timers[alert_key].cancel()
                        del self.escalation_timers[alert_key]
                    
                    # Move to history
                    self.alert_history.append(instance)
                    del self.active_alerts[alert_key]
            
            return triggered
            
        except Exception as e:
            logger.error(f"Error evaluating alert {alert.alert_id}: {e}")
            return False
    
    def _evaluate_condition(self, condition: str, value: float, threshold: float, comparison: str) -> bool:
        """Evaluate alert condition"""
        if comparison == '>':
            return value > threshold
        elif comparison == '<':
            return value < threshold
        elif comparison == '>=':
            return value >= threshold
        elif comparison == '<=':
            return value <= threshold
        elif comparison == '==':
            return value == threshold
        elif comparison == '!=':
            return value != threshold
        else:
            return False
    
    async def _fire_alert(self, alert: Alert, instance: AlertInstance):
        """Fire alert notification"""
        try:
            # Send notification
            if self.notification_service_url:
                notification_data = {
                    'alert_id': alert.alert_id,
                    'severity': alert.severity,
                    'title': alert.name,
                    'message': alert.description,
                    'current_value': instance.current_value,
                    'threshold': instance.threshold,
                    'labels': instance.labels,
                    'channels': alert.notification_channels
                }
                
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{self.notification_service_url}/send",
                        json=notification_data,
                        timeout=10
                    )
            
            # Store in Redis for external consumption
            if self.redis:
                await self.redis.lpush(
                    'ems_alerts_fired',
                    json.dumps(asdict(instance), default=str)
                )
                await self.redis.ltrim('ems_alerts_fired', 0, 999)  # Keep last 1000 alerts
            
            logger.warning(f"Alert fired: {alert.name} - {instance.current_value} {alert.comparison} {alert.threshold}")
            
        except Exception as e:
            logger.error(f"Error firing alert: {e}")
    
    async def _resolve_alert(self, alert: Alert, instance: AlertInstance):
        """Resolve alert notification"""
        try:
            # Send resolution notification
            if self.notification_service_url:
                notification_data = {
                    'alert_id': alert.alert_id,
                    'severity': 'info',
                    'title': f"RESOLVED: {alert.name}",
                    'message': f"Alert has been resolved. Duration: {instance.resolved_at - instance.fired_at}",
                    'labels': instance.labels,
                    'channels': alert.notification_channels
                }
                
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{self.notification_service_url}/send",
                        json=notification_data,
                        timeout=10
                    )
            
            logger.info(f"Alert resolved: {alert.name}")
            
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
    
    async def _handle_escalation(self, alert: Alert, instance: AlertInstance):
        """Handle alert escalation"""
        try:
            for rule in alert.escalation_rules:
                # Wait for escalation delay
                await asyncio.sleep(rule.get('delay_minutes', 15) * 60)
                
                # Check if alert is still active and not acknowledged
                if (instance.instance_id in self.active_alerts and 
                    not self.active_alerts[instance.instance_id].acknowledged):
                    
                    instance.escalation_level += 1
                    
                    # Send escalation notification
                    if self.notification_service_url:
                        notification_data = {
                            'alert_id': alert.alert_id,
                            'severity': 'critical',
                            'title': f"ESCALATED: {alert.name}",
                            'message': f"Alert escalated to level {instance.escalation_level}",
                            'escalation_level': instance.escalation_level,
                            'channels': rule.get('channels', alert.notification_channels)
                        }
                        
                        async with httpx.AsyncClient() as client:
                            await client.post(
                                f"{self.notification_service_url}/send",
                                json=notification_data,
                                timeout=10
                            )
                    
                    logger.critical(f"Alert escalated: {alert.name} - Level {instance.escalation_level}")
                else:
                    break  # Alert resolved or acknowledged
                    
        except asyncio.CancelledError:
            pass  # Escalation cancelled (alert resolved)
        except Exception as e:
            logger.error(f"Error in alert escalation: {e}")


class HealthChecker:
    """Advanced health checking with dependency tracking"""
    
    def __init__(self):
        self.services: Dict[str, ServiceHealth] = {}
        self.check_interval = 30  # seconds
        self.timeout = 10  # seconds
    
    async def register_service(self, service_name: str, endpoint: str, dependencies: List[str] = None):
        """Register a service for health checking"""
        self.services[service_name] = ServiceHealth(
            service_name=service_name,
            status='unknown',
            last_check=datetime.now(),
            response_time=0.0,
            error_count=0,
            uptime_percentage=100.0,
            endpoint=endpoint,
            version='unknown',
            dependencies=dependencies or []
        )
    
    async def check_service_health(self, service_name: str) -> ServiceHealth:
        """Check health of a specific service"""
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} not registered")
        
        service = self.services[service_name]
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(service.endpoint)
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    service.status = 'healthy'
                    service.error_count = 0
                    
                    # Parse health response for additional metrics
                    try:
                        health_data = response.json()
                        service.version = health_data.get('version', 'unknown')
                        service.custom_metrics = health_data.get('metrics', {})
                    except:
                        pass
                        
                else:
                    service.status = 'degraded'
                    service.error_count += 1
                
                service.response_time = response_time
                service.last_check = datetime.now()
                
        except Exception as e:
            service.status = 'unhealthy'
            service.error_count += 1
            service.response_time = time.time() - start_time
            service.last_check = datetime.now()
            
            logger.error(f"Health check failed for {service_name}: {e}")
        
        return service
    
    async def check_all_services(self) -> Dict[str, ServiceHealth]:
        """Check health of all registered services"""
        results = {}
        
        tasks = []
        for service_name in self.services:
            tasks.append(self.check_service_health(service_name))
        
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in health checks: {e}")
        
        for service_name, service in self.services.items():
            results[service_name] = service
        
        return results


class SLATracker:
    """SLA tracking and reporting"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.sla_targets = {
            'availability': 99.9,  # 99.9%
            'response_time': 2.0,  # 2 seconds
            'error_rate': 1.0      # 1%
        }
    
    async def record_request(self, service_name: str, response_time: float, success: bool):
        """Record a request for SLA tracking"""
        timestamp = datetime.now()
        
        # Store request data
        request_data = {
            'service': service_name,
            'response_time': response_time,
            'success': success,
            'timestamp': timestamp.isoformat()
        }
        
        # Store in Redis with TTL
        await self.redis.lpush(f'sla_requests:{service_name}', json.dumps(request_data))
        await self.redis.expire(f'sla_requests:{service_name}', 30 * 24 * 3600)  # 30 days
    
    async def calculate_sla_metrics(self, service_name: str, period: str = 'daily') -> SLAMetrics:
        """Calculate SLA metrics for a service"""
        now = datetime.now()
        
        if period == 'daily':
            window_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'weekly':
            window_start = now - timedelta(days=7)
        elif period == 'monthly':
            window_start = now - timedelta(days=30)
        else:
            window_start = now - timedelta(hours=1)
        
        # Get request data from Redis
        request_data = await self.redis.lrange(f'sla_requests:{service_name}', 0, -1)
        
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        for data in request_data:
            try:
                request = json.loads(data)
                request_time = datetime.fromisoformat(request['timestamp'])
                
                if request_time >= window_start:
                    total_requests += 1
                    if request['success']:
                        successful_requests += 1
                        response_times.append(request['response_time'])
                    else:
                        failed_requests += 1
            except:
                continue
        
        # Calculate metrics
        availability = (successful_requests / total_requests * 100) if total_requests > 0 else 100
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0
        p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else 0
        
        return SLAMetrics(
            service_name=service_name,
            sla_type='overall',
            target=self.sla_targets['availability'],
            current=availability,
            period=period,
            window_start=window_start,
            window_end=now,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time
        )


class MonitoringService(BaseService):
    """Production-grade monitoring service"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("monitoring", config)
        
        # Initialize components
        self.prometheus_metrics = PrometheusMetrics()
        self.alert_manager = None
        self.health_checker = HealthChecker()
        self.sla_tracker = None
        
        # Configuration
        self.collection_interval = config.get('collection_interval', 30)
        self.retention_days = config.get('retention_days', 30)
        self.notification_service_url = config.get('notification_service_url')
        
        # Collections
        self.collections = {}
        
        # Alerts configuration
        self.alerts: Dict[str, Alert] = {}
        self._load_default_alerts()
        
        # FastAPI app
        self.app = self._create_fastapi_app()
    
    async def initialize(self):
        """Initialize monitoring service"""
        await super().initialize()
        
        # Initialize database collections
        if self.db_client:
            db = self.db_client[self.config['mongodb']['database']]
            self.collections = {
                'metrics': db.ems_metrics,
                'alerts': db.ems_alerts,
                'alert_history': db.ems_alert_history,
                'service_health': db.ems_service_health,
                'sla_metrics': db.ems_sla_metrics
            }
        
        # Initialize Redis-dependent components
        if self.redis_client:
            self.alert_manager = AlertManager(self.redis_client, self.notification_service_url)
            self.sla_tracker = SLATracker(self.redis_client)
        
        # Register EMS services for health checking
        await self._register_ems_services()
        
        # Start background tasks
        asyncio.create_task(self._collect_metrics_loop())
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._alert_evaluation_loop())
        asyncio.create_task(self._cleanup_old_data_loop())
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title="EMS Monitoring Service",
            description="Production-grade monitoring and observability service",
            version="1.0.0"
        )
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add routes
        self._add_routes(app)
        
        return app
    
    def _add_routes(self, app: FastAPI):
        """Add monitoring service routes"""
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "metrics_collected": len(self.prometheus_metrics.registry._collector_to_names),
                "active_alerts": len(self.alert_manager.active_alerts) if self.alert_manager else 0,
                "monitored_services": len(self.health_checker.services)
            }
        
        @app.get("/metrics", response_class=PlainTextResponse)
        async def get_prometheus_metrics():
            """Prometheus metrics endpoint"""
            return self.prometheus_metrics.get_metrics()
        
        @app.get("/alerts")
        async def get_active_alerts():
            """Get all active alerts"""
            if not self.alert_manager:
                return {"active_alerts": []}
            
            return {
                "active_alerts": [asdict(alert) for alert in self.alert_manager.active_alerts.values()],
                "total_active": len(self.alert_manager.active_alerts)
            }
        
        @app.post("/alerts/{alert_id}/acknowledge")
        async def acknowledge_alert(alert_id: str, acknowledgment: Dict[str, Any]):
            """Acknowledge an alert"""
            if not self.alert_manager:
                raise HTTPException(status_code=503, detail="Alert manager not available")
            
            acknowledged_by = acknowledgment.get('acknowledged_by', 'unknown')
            
            for instance in self.alert_manager.active_alerts.values():
                if instance.alert_id == alert_id:
                    instance.acknowledged = True
                    instance.acknowledged_by = acknowledged_by
                    instance.acknowledged_at = datetime.now()
                    
                    # Cancel escalation
                    if instance.instance_id in self.alert_manager.escalation_timers:
                        self.alert_manager.escalation_timers[instance.instance_id].cancel()
                        del self.alert_manager.escalation_timers[instance.instance_id]
                    
                    return {"message": f"Alert {alert_id} acknowledged by {acknowledged_by}"}
            
            raise HTTPException(status_code=404, detail="Alert not found")
        
        @app.get("/services/health")
        async def get_services_health():
            """Get health status of all services"""
            health_results = await self.health_checker.check_all_services()
            return {
                "services": {name: asdict(health) for name, health in health_results.items()},
                "summary": {
                    "total": len(health_results),
                    "healthy": len([h for h in health_results.values() if h.status == 'healthy']),
                    "degraded": len([h for h in health_results.values() if h.status == 'degraded']),
                    "unhealthy": len([h for h in health_results.values() if h.status == 'unhealthy'])
                }
            }
        
        @app.get("/sla/{service_name}")
        async def get_sla_metrics(service_name: str, period: str = 'daily'):
            """Get SLA metrics for a service"""
            if not self.sla_tracker:
                raise HTTPException(status_code=503, detail="SLA tracker not available")
            
            sla_metrics = await self.sla_tracker.calculate_sla_metrics(service_name, period)
            return asdict(sla_metrics)
        
        @app.get("/dashboard")
        async def get_monitoring_dashboard():
            """Get comprehensive monitoring dashboard data"""
            # Get system metrics
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            # Get service health
            health_results = await self.health_checker.check_all_services()
            
            # Get active alerts
            active_alerts = []
            if self.alert_manager:
                active_alerts = [asdict(alert) for alert in self.alert_manager.active_alerts.values()]
            
            return {
                "system_metrics": {
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory_percent,
                    "disk_usage": disk_percent,
                    "timestamp": datetime.now().isoformat()
                },
                "service_health": {
                    "services": {name: asdict(health) for name, health in health_results.items()},
                    "summary": {
                        "total": len(health_results),
                        "healthy": len([h for h in health_results.values() if h.status == 'healthy']),
                        "issues": len([h for h in health_results.values() if h.status != 'healthy'])
                    }
                },
                "alerts": {
                    "active": active_alerts,
                    "count": len(active_alerts),
                    "critical": len([a for a in active_alerts if a.get('annotations', {}).get('severity') == 'critical'])
                },
                "timestamp": datetime.now().isoformat()
            }
    
    async def _register_ems_services(self):
        """Register EMS services for health monitoring"""
        service_endpoints = {
            'data_ingestion': 'http://localhost:8001/health',
            'analytics': 'http://localhost:8002/health',
            'query_processor': 'http://localhost:8003/health',
            'notification': 'http://localhost:8004/health',
            'realtime_streaming': 'http://localhost:8005/health',
            'advanced_ml': 'http://localhost:8006/health',
            'security': 'http://localhost:8007/health',
            'api_gateway': 'http://localhost:8000/health'
        }
        
        for service_name, endpoint in service_endpoints.items():
            await self.health_checker.register_service(service_name, endpoint)
    
    def _load_default_alerts(self):
        """Load default alerts configuration"""
        try:
            default_alerts = [
                {
                    "alert_id": "high_cpu_usage",
                    "name": "High CPU Usage",
                    "description": "CPU usage is above 80%",
                    "severity": "warning",
                    "condition": "cpu_usage > 80",
                    "threshold": 80.0,
                    "comparison": ">",
                    "duration": 300,
                    "evaluation_interval": 60,
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "escalation_rules": [],
                    "notification_channels": ["email", "slack"],
                    "runbook_url": "http://runbooks.example.com/high_cpu_usage",
                    "tags": {"team": "infra", "service": "all"}
                },
                {
                    "alert_id": "service_down",
                    "name": "Service Down",
                    "description": "A critical service is down",
                    "severity": "critical",
                    "condition": "service_health == 'unhealthy'",
                    "threshold": 1.0,
                    "comparison": "==",
                    "duration": 60,
                    "evaluation_interval": 30,
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "escalation_rules": [
                        {"level": 1, "delay_minutes": 5, "channels": ["pagerduty"]},
                        {"level": 2, "delay_minutes": 10, "channels": ["email"]}
                    ],
                    "notification_channels": ["email", "pagerduty"],
                    "runbook_url": "http://runbooks.example.com/service_down",
                    "tags": {"team": "ops", "service": "critical"}
                }
            ]
            
            for alert_config in default_alerts:
                alert = Alert(**alert_config)
                self.alerts[alert.alert_id] = alert
            
            logger.info("Loaded default alerts")
        
        except Exception as e:
            logger.error(f"Error loading default alerts: {e}")
    
    async def _collect_metrics_loop(self):
        """Metrics collection loop"""
        while True:
            try:
                await asyncio.sleep(self.collection_interval)
                
                # Collect system metrics
                cpu_usage = psutil.cpu_percent()
                memory_usage = psutil.virtual_memory().percent
                disk_usage = psutil.disk_usage('/').percent
                
                # Update Prometheus metrics
                self.prometheus_metrics.cpu_usage.set(cpu_usage)
                self.prometheus_metrics.memory_usage.set(memory_usage)
                self.prometheus_metrics.disk_usage.set(disk_usage)
                
                # Collect application metrics
                for service_name, health in self.health_checker.services.items():
                    self.prometheus_metrics.service_up.labels(service=service_name).set(
                        1 if health.status == "healthy" else 0
                    )
                    self.prometheus_metrics.service_response_time.labels(service=service_name).set(
                        health.response_time
                    )
                
                # Collect custom metrics from Redis
                await self._collect_custom_metrics()
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
    
    async def _collect_custom_metrics(self):
        """Collect custom metrics from Redis"""
        try:
            if not self.redis_client:
                return
            
            # Get all metric keys
            metric_keys = await self.redis_client.keys("metric:*")
            
            for key in metric_keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                parts = key_str.split(':')
                
                if len(parts) >= 3:
                    try:
                        metric_name = parts[1]
                        timestamp = int(parts[2])
                        
                        # Get metric value
                        value = await self.redis_client.get(key)
                        if value is not None:
                            value = float(value)
                            
                            # Update Prometheus metric
                            self.prometheus_metrics.registry.get_sample_value(metric_name, labels={"host": socket.gethostname()})
                            self.prometheus_metrics.registry.get_sample_value(metric_name, labels={"host": socket.gethostname()}).set(value)
                    except Exception as e:
                        logger.error(f"Error processing metric key {key_str}: {e}")
        
        except Exception as e:
            logger.error(f"Error collecting custom metrics: {e}")
    
    async def _health_check_loop(self):
        """Health check loop"""
        while True:
            try:
                await asyncio.sleep(self.health_checker.check_interval)
                
                # Check health of all registered services
                await self.health_checker.check_all_services()
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    async def _alert_evaluation_loop(self):
        """Alert evaluation loop"""
        while True:
            try:
                await asyncio.sleep(30)  # Evaluate alerts every 30 seconds
                
                # Get recent metrics
                recent_metrics = self.prometheus_metrics.get_metrics()
                
                # Evaluate alerts
                if self.alert_manager:
                    for alert in self.alerts.values():
                        # Get relevant metrics for alert
                        metrics = [
                            m for m in recent_metrics 
                            if m.name == alert.condition.split(' ')[0]
                        ]
                        
                        if metrics:
                            # Use latest metric value for evaluation
                            latest_metric = max(metrics, key=lambda m: m.timestamp)
                            await self.alert_manager.evaluate_alert(alert, latest_metric.value)
            
            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}")
    
    async def _cleanup_old_data_loop(self):
        """Cleanup old data loop"""
        while True:
            try:
                await asyncio.sleep(3600)  # Cleanup every hour
                
                # Cleanup old metrics data
                if self.collections.get('metrics'):
                    cutoff_time = datetime.now() - timedelta(days=self.retention_days)
                    await self.collections['metrics'].delete_many({"timestamp": {"$lt": cutoff_time}})
                
                # Cleanup old alert history
                if self.collections.get('alert_history'):
                    cutoff_time = datetime.now() - timedelta(days=self.retention_days)
                    await self.collections['alert_history'].delete_many({"fired_at": {"$lt": cutoff_time}})
                
                # Cleanup old SLA metrics
                if self.collections.get('sla_metrics'):
                    cutoff_time = datetime.now() - timedelta(days=self.retention_days)
                    await self.collections['sla_metrics'].delete_many({"window_end": {"$lt": cutoff_time}})
                
                logger.info("Old data cleanup completed")
            
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def health_check(self):
        """Service-specific health check"""
        try:
            # Check Redis connection
            if self.redis_client:
                await self.redis_client.ping()
                redis_healthy = True
            else:
                redis_healthy = False
            
            # Check metrics collection
            recent_metrics_count = len(self.prometheus_metrics.registry._collector_to_names)
            
            # Check alert manager
            active_alerts_count = len(self.alert_manager.active_alerts()) if self.alert_manager else 0
            
            return {
                "status": "healthy",
                "redis_connected": redis_healthy,
                "recent_metrics_count": recent_metrics_count,
                "active_alerts_count": active_alerts_count,
                "monitored_services": len(self.health_checker.services),
                "service": self.service_name
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise Exception(f"Monitoring service unhealthy: {e}")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service-specific requests"""
        request_type = request_data.get('type')
        
        if request_type == 'get_service_status':
            service_name = request_data.get('service_name')
            if service_name in self.health_checker.services:
                return {"status": asdict(self.health_checker.services[service_name])}
            else:
                return {"status": None, "error": "Service not found"}
        
        elif request_type == 'get_metrics_summary':
            recent_metrics = self.prometheus_metrics.get_metrics(
                since=datetime.now() - timedelta(hours=1)
            )
            return {
                "total_metrics": len(recent_metrics),
                "unique_metric_names": len(set(m.name for m in recent_metrics)),
                "time_range": "1 hour"
            }
        
        else:
            raise ValueError(f"Unknown request type: {request_type}")


def create_monitoring_service(config: Dict[str, Any] = None) -> MonitoringService:
    """Factory function to create monitoring service"""
    if config is None:
        from common.config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.get_service_config("monitoring")
    
    return MonitoringService(config)


if __name__ == "__main__":
    import uvicorn
    
    service = create_monitoring_service()
    
    # Run the service
    uvicorn.run(
        service.app,
        host="0.0.0.0",
        port=8008,
        log_level="info"
    )
