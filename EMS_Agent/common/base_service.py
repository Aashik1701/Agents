#!/usr/bin/env python3
"""
Base Service Class for EMS Microservices
Provides common functionality for all services including health checks, 
circuit breakers, retry mechanisms, and graceful degradation.
"""

import asyncio
import logging
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import aiohttp
import redis.asyncio as redis
from pymongo import MongoClient
from pymongo.server_api import ServerApi

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 3


@dataclass
class RetryConfig:
    """Retry mechanism configuration"""
    max_attempts: int = 3
    backoff_factor: float = 2.0
    initial_delay: float = 1.0


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time > self.config.recovery_timeout
    
    async def _on_success(self):
        """Handle successful execution"""
        if self.state == "half-open":
            self.failure_count = 0
            self.state = "closed"
    
    async def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = "open"


class RetryMechanism:
    """Retry mechanism with exponential backoff"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    async def execute(self, func: Callable, *args, **kwargs):
        """Execute function with retry mechanism"""
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.config.max_attempts - 1:
                    break
                
                delay = self.config.initial_delay * (self.config.backoff_factor ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
        
        raise last_exception


class BaseService(ABC):
    """Base class for all EMS microservices"""
    
    def __init__(self, service_name: str, config: Dict[str, Any]):
        self.service_name = service_name
        self.config = config
        self.status = ServiceStatus.STARTING
        self.start_time = datetime.now()
        self.last_health_check = None
        
        # Initialize components
        self.circuit_breaker = CircuitBreaker(
            CircuitBreakerConfig(**config.get('circuit_breaker', {}))
        )
        self.retry_mechanism = RetryMechanism(
            RetryConfig(**config.get('retry', {}))
        )
        
        # Database and cache connections
        self.db_client = None
        self.redis_client = None
        
        # Service registry for inter-service communication
        self.service_registry = {}
        
        logger.info(f"Initializing {service_name} service")
    
    async def initialize(self):
        """Initialize service dependencies"""
        try:
            await self._setup_database()
            await self._setup_cache()
            await self._register_service()
            await self._setup_health_checks()
            
            self.status = ServiceStatus.HEALTHY
            logger.info(f"{self.service_name} service initialized successfully")
            
        except Exception as e:
            self.status = ServiceStatus.UNHEALTHY
            logger.error(f"Failed to initialize {self.service_name}: {e}")
            raise
    
    async def shutdown(self):
        """Graceful shutdown of service"""
        self.status = ServiceStatus.STOPPING
        
        try:
            await self._deregister_service()
            await self._cleanup_connections()
            logger.info(f"{self.service_name} service shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during {self.service_name} shutdown: {e}")
    
    async def _setup_database(self):
        """Setup database connection with connection pooling"""
        if 'mongodb' in self.config:
            mongodb_config = self.config['mongodb']
            self.db_client = MongoClient(
                mongodb_config['uri'],
                server_api=ServerApi('1'),
                maxPoolSize=mongodb_config.get('max_pool_size', 10),
                minPoolSize=mongodb_config.get('min_pool_size', 5),
                serverSelectionTimeoutMS=mongodb_config.get('timeout', 5000)
            )
            
            # Test connection
            await self.circuit_breaker.call(self._test_database_connection)
    
    async def _setup_cache(self):
        """Setup Redis cache connection"""
        if 'redis' in self.config:
            redis_config = self.config['redis']
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                max_connections=redis_config.get('max_connections', 10)
            )
            
            # Test connection
            await self.redis_client.ping()
    
    async def _test_database_connection(self):
        """Test database connection"""
        if self.db_client:
            self.db_client.admin.command('ping')
    
    async def _register_service(self):
        """Register service in service registry"""
        if 'service_registry' in self.config:
            registry_config = self.config['service_registry']
            service_info = {
                'name': self.service_name,
                'host': registry_config.get('host', 'localhost'),
                'port': registry_config.get('port'),
                'health_endpoint': f"/health",
                'status': self.status.value,
                'start_time': self.start_time.isoformat(),
                'version': self.config.get('version', '1.0.0')
            }
            
            # Register with service discovery (e.g., Consul, etcd, or Redis)
            if self.redis_client:
                await self.redis_client.setex(
                    f"services:{self.service_name}",
                    30,  # TTL in seconds
                    json.dumps(service_info)
                )
    
    async def _deregister_service(self):
        """Deregister service from service registry"""
        if self.redis_client:
            await self.redis_client.delete(f"services:{self.service_name}")
    
    async def _setup_health_checks(self):
        """Setup periodic health checks"""
        asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self):
        """Periodic health check loop"""
        while self.status != ServiceStatus.STOPPING:
            try:
                await self._perform_health_check()
                await asyncio.sleep(30)  # Health check every 30 seconds
            except Exception as e:
                logger.error(f"Health check failed for {self.service_name}: {e}")
                await asyncio.sleep(10)  # Retry after 10 seconds on failure
    
    async def _perform_health_check(self):
        """Perform health check"""
        try:
            # Check database connection
            if self.db_client:
                await self.circuit_breaker.call(self._test_database_connection)
            
            # Check cache connection
            if self.redis_client:
                await self.redis_client.ping()
            
            # Service-specific health checks
            await self.health_check()
            
            self.last_health_check = datetime.now()
            
            # Update service registry
            await self._register_service()
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.status = ServiceStatus.DEGRADED
            raise
    
    async def _cleanup_connections(self):
        """Cleanup database and cache connections"""
        if self.db_client:
            self.db_client.close()
        
        if self.redis_client:
            await self.redis_client.close()
    
    async def call_service(self, service_name: str, endpoint: str, data: Dict[str, Any] = None):
        """Call another service with circuit breaker and retry"""
        return await self.circuit_breaker.call(
            self.retry_mechanism.execute,
            self._make_service_call,
            service_name,
            endpoint,
            data
        )
    
    async def _make_service_call(self, service_name: str, endpoint: str, data: Dict[str, Any] = None):
        """Make HTTP call to another service"""
        # Get service info from registry
        if self.redis_client:
            service_info_str = await self.redis_client.get(f"services:{service_name}")
            if not service_info_str:
                raise Exception(f"Service {service_name} not found in registry")
            
            service_info = json.loads(service_info_str)
            url = f"http://{service_info['host']}:{service_info['port']}{endpoint}"
            
            async with aiohttp.ClientSession() as session:
                if data:
                    async with session.post(url, json=data) as response:
                        return await response.json()
                else:
                    async with session.get(url) as response:
                        return await response.json()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        uptime = datetime.now() - self.start_time
        
        return {
            'service': self.service_name,
            'status': self.status.value,
            'uptime_seconds': int(uptime.total_seconds()),
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'circuit_breaker_state': self.circuit_breaker.state,
            'circuit_breaker_failures': self.circuit_breaker.failure_count,
            'timestamp': datetime.now().isoformat()
        }
    
    @abstractmethod
    async def health_check(self):
        """Service-specific health check implementation"""
        pass
    
    @abstractmethod
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service-specific requests"""
        pass


class LoadBalancer:
    """Simple round-robin load balancer for service instances"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.service_instances = {}
        self.current_index = {}
    
    async def get_service_instance(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get next available service instance using round-robin"""
        # Get all instances of the service
        pattern = f"services:{service_name}:*"
        keys = await self.redis_client.keys(pattern)
        
        if not keys:
            return None
        
        # Update current index for round-robin
        if service_name not in self.current_index:
            self.current_index[service_name] = 0
        
        # Get instance info
        key = keys[self.current_index[service_name]]
        instance_info_str = await self.redis_client.get(key)
        
        if instance_info_str:
            # Move to next instance for next request
            self.current_index[service_name] = (
                self.current_index[service_name] + 1
            ) % len(keys)
            
            return json.loads(instance_info_str)
        
        return None
