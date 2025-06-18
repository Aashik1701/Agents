#!/usr/bin/env python3
"""
Real-time Data Streaming Service for EMS
Handles real-time sensor data ingestion, WebSocket connections, and streaming analytics
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
import logging
from dataclasses import dataclass, asdict
import numpy as np

from common.base_service import BaseService

logger = logging.getLogger(__name__)


@dataclass
class SensorReading:
    """Real-time sensor reading data structure"""
    sensor_id: str
    timestamp: datetime
    voltage: float
    current: float
    power_factor: float
    active_power: float
    reactive_power: float
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    location: Optional[str] = None


@dataclass
class StreamingAlert:
    """Real-time alert data structure"""
    alert_id: str
    timestamp: datetime
    sensor_id: str
    alert_type: str
    severity: str
    message: str
    value: float
    threshold: float


class WebSocketConnectionManager:
    """Manages WebSocket connections for real-time data streaming"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()
        logger.info(f"WebSocket client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            del self.client_subscriptions[client_id]
            logger.info(f"WebSocket client {client_id} disconnected")
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict, sensor_ids: Set[str] = None):
        """Broadcast message to all subscribed clients"""
        for client_id, websocket in list(self.active_connections.items()):
            try:
                # Check if client is subscribed to any of the sensor IDs
                if sensor_ids:
                    client_subs = self.client_subscriptions.get(client_id, set())
                    if not (sensor_ids & client_subs):
                        continue
                
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_id}: {e}")
                self.disconnect(client_id)
    
    def subscribe_client(self, client_id: str, sensor_ids: List[str]):
        """Subscribe client to specific sensor data"""
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].update(sensor_ids)


class RealTimeStreamingService(BaseService):
    """Real-time data streaming service for EMS"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("realtime_streaming", config)
        self.app = self._create_fastapi_app()
        self.connection_manager = WebSocketConnectionManager()
        self.redis_client = None
        self.stream_processors = {}
        self.alert_thresholds = {
            'voltage_high': 240.0,
            'voltage_low': 210.0,
            'current_high': 20.0,
            'power_factor_low': 0.85,
            'temperature_high': 60.0
        }
    
    async def initialize(self):
        """Initialize real-time streaming service"""
        await super().initialize()
        
        # Initialize Redis for real-time data streaming
        redis_config = self.config.get('redis', {})
        self.redis_client = redis.Redis(
            host=redis_config.get('host', 'localhost'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 1)  # Use different DB for streaming
        )
        
        # Start background tasks
        asyncio.create_task(self._process_sensor_stream())
        asyncio.create_task(self._cleanup_old_data())
        
        logger.info("Real-time streaming service initialized")
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title="EMS Real-time Streaming Service",
            description="Real-time data streaming and WebSocket service for EMS",
            version="1.0.0"
        )
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._add_routes(app)
        return app
    
    def _add_routes(self, app: FastAPI):
        """Add FastAPI routes"""
        
        @app.get("/health")
        async def health_check():
            return await self.health_check()
        
        @app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            """WebSocket endpoint for real-time data streaming"""
            await self.connection_manager.connect(websocket, client_id)
            try:
                while True:
                    # Receive subscription requests
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get('type') == 'subscribe':
                        sensor_ids = message.get('sensor_ids', [])
                        self.connection_manager.subscribe_client(client_id, sensor_ids)
                        await self.connection_manager.send_personal_message({
                            'type': 'subscription_confirmed',
                            'sensor_ids': sensor_ids
                        }, client_id)
                    
            except WebSocketDisconnect:
                self.connection_manager.disconnect(client_id)
        
        @app.post("/stream/sensor_data")
        async def ingest_sensor_data(reading: dict, background_tasks: BackgroundTasks):
            """Ingest real-time sensor data"""
            try:
                # Validate and process sensor reading
                sensor_reading = SensorReading(
                    sensor_id=reading['sensor_id'],
                    timestamp=datetime.fromisoformat(reading.get('timestamp', datetime.now().isoformat())),
                    voltage=float(reading['voltage']),
                    current=float(reading['current']),
                    power_factor=float(reading['power_factor']),
                    active_power=float(reading['active_power']),
                    reactive_power=float(reading['reactive_power']),
                    temperature=reading.get('temperature'),
                    humidity=reading.get('humidity'),
                    location=reading.get('location')
                )
                
                # Process in background
                background_tasks.add_task(self._process_sensor_reading, sensor_reading)
                
                return {"status": "accepted", "sensor_id": sensor_reading.sensor_id}
                
            except Exception as e:
                logger.error(f"Error processing sensor data: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @app.get("/stream/sensors/{sensor_id}/latest")
        async def get_latest_reading(sensor_id: str):
            """Get latest reading for a sensor"""
            try:
                data = await self.redis_client.get(f"sensor:{sensor_id}:latest")
                if data:
                    return json.loads(data)
                else:
                    raise HTTPException(status_code=404, detail="Sensor not found")
            except Exception as e:
                logger.error(f"Error retrieving sensor data: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/stream/sensors/{sensor_id}/history")
        async def get_sensor_history(sensor_id: str, hours: int = 1):
            """Get sensor history for specified hours"""
            try:
                # Get data from Redis stream
                stream_key = f"sensor:{sensor_id}:stream"
                since = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)
                
                messages = await self.redis_client.xrange(stream_key, min=since)
                
                history = []
                for msg_id, fields in messages:
                    data = {k.decode(): v.decode() for k, v in fields.items()}
                    history.append(data)
                
                return {"sensor_id": sensor_id, "history": history}
                
            except Exception as e:
                logger.error(f"Error retrieving sensor history: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/stream/alerts/active")
        async def get_active_alerts():
            """Get currently active alerts"""
            try:
                alert_keys = await self.redis_client.keys("alert:active:*")
                alerts = []
                
                for key in alert_keys:
                    alert_data = await self.redis_client.get(key)
                    if alert_data:
                        alerts.append(json.loads(alert_data))
                
                return {"active_alerts": alerts}
                
            except Exception as e:
                logger.error(f"Error retrieving active alerts: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _process_sensor_reading(self, reading: SensorReading):
        """Process individual sensor reading"""
        try:
            # Store in Redis stream for real-time access
            stream_key = f"sensor:{reading.sensor_id}:stream"
            await self.redis_client.xadd(stream_key, asdict(reading))
            
            # Store latest reading
            await self.redis_client.set(
                f"sensor:{reading.sensor_id}:latest",
                json.dumps(asdict(reading), default=str),
                ex=3600  # Expire after 1 hour
            )
            
            # Check for alerts
            alerts = await self._check_for_alerts(reading)
            
            # Broadcast to WebSocket clients
            await self.connection_manager.broadcast({
                'type': 'sensor_reading',
                'data': asdict(reading)
            }, {reading.sensor_id})
            
            # Broadcast alerts
            for alert in alerts:
                await self.connection_manager.broadcast({
                    'type': 'alert',
                    'data': asdict(alert)
                }, {alert.sensor_id})
            
            # Store in MongoDB for long-term analysis
            await self._store_in_mongodb(reading)
            
        except Exception as e:
            logger.error(f"Error processing sensor reading: {e}")
    
    async def _check_for_alerts(self, reading: SensorReading) -> List[StreamingAlert]:
        """Check sensor reading for alert conditions"""
        alerts = []
        
        try:
            # Voltage alerts
            if reading.voltage > self.alert_thresholds['voltage_high']:
                alerts.append(StreamingAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=reading.timestamp,
                    sensor_id=reading.sensor_id,
                    alert_type='voltage_high',
                    severity='warning',
                    message=f"High voltage detected: {reading.voltage}V",
                    value=reading.voltage,
                    threshold=self.alert_thresholds['voltage_high']
                ))
            
            elif reading.voltage < self.alert_thresholds['voltage_low']:
                alerts.append(StreamingAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=reading.timestamp,
                    sensor_id=reading.sensor_id,
                    alert_type='voltage_low',
                    severity='warning',
                    message=f"Low voltage detected: {reading.voltage}V",
                    value=reading.voltage,
                    threshold=self.alert_thresholds['voltage_low']
                ))
            
            # Current alerts
            if reading.current > self.alert_thresholds['current_high']:
                alerts.append(StreamingAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=reading.timestamp,
                    sensor_id=reading.sensor_id,
                    alert_type='current_high',
                    severity='critical',
                    message=f"High current detected: {reading.current}A",
                    value=reading.current,
                    threshold=self.alert_thresholds['current_high']
                ))
            
            # Power factor alerts
            if reading.power_factor < self.alert_thresholds['power_factor_low']:
                alerts.append(StreamingAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=reading.timestamp,
                    sensor_id=reading.sensor_id,
                    alert_type='power_factor_low',
                    severity='warning',
                    message=f"Low power factor: {reading.power_factor}",
                    value=reading.power_factor,
                    threshold=self.alert_thresholds['power_factor_low']
                ))
            
            # Temperature alerts (if available)
            if reading.temperature and reading.temperature > self.alert_thresholds['temperature_high']:
                alerts.append(StreamingAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=reading.timestamp,
                    sensor_id=reading.sensor_id,
                    alert_type='temperature_high',
                    severity='critical',
                    message=f"High temperature: {reading.temperature}°C",
                    value=reading.temperature,
                    threshold=self.alert_thresholds['temperature_high']
                ))
            
            # Store active alerts in Redis
            for alert in alerts:
                await self.redis_client.set(
                    f"alert:active:{alert.alert_id}",
                    json.dumps(asdict(alert), default=str),
                    ex=3600  # Auto-expire after 1 hour
                )
            
        except Exception as e:
            logger.error(f"Error checking for alerts: {e}")
        
        return alerts
    
    async def _store_in_mongodb(self, reading: SensorReading):
        """Store reading in MongoDB for long-term analysis"""
        try:
            if self.db_client:
                db = self.db_client[self.config['mongodb']['database']]
                collection = db.ems_realtime_data
                
                document = asdict(reading)
                document['ingestion_time'] = datetime.now()
                
                # Insert in thread pool to avoid blocking
                await asyncio.to_thread(collection.insert_one, document)
                
        except Exception as e:
            logger.error(f"Error storing in MongoDB: {e}")
    
    async def _process_sensor_stream(self):
        """Background task to process sensor data streams"""
        while True:
            try:
                # Process any queued sensor data
                await asyncio.sleep(1)  # Process every second
                
                # Here you could add additional stream processing logic
                # such as aggregating data, detecting patterns, etc.
                
            except Exception as e:
                logger.error(f"Error in stream processing: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_old_data(self):
        """Background task to clean up old streaming data"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Clean up old stream data (keep last 24 hours)
                cutoff = int((datetime.now() - timedelta(hours=24)).timestamp() * 1000)
                
                # Get all sensor stream keys
                stream_keys = await self.redis_client.keys("sensor:*:stream")
                
                for key in stream_keys:
                    await self.redis_client.xtrim(key, minid=cutoff)
                
                logger.info("Cleaned up old streaming data")
                
            except Exception as e:
                logger.error(f"Error cleaning up old data: {e}")
    
    async def health_check(self):
        """Service-specific health check"""
        try:
            # Check Redis connection
            await self.redis_client.ping()
            
            # Check WebSocket connections
            active_connections = len(self.connection_manager.active_connections)
            
            return {
                "status": "healthy",
                "active_websocket_connections": active_connections,
                "redis_connected": True,
                "service": self.service_name
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise Exception(f"Real-time streaming service unhealthy: {e}")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service-specific requests"""
        request_type = request_data.get('type')
        
        if request_type == 'get_active_sensors':
            # Get list of active sensors
            sensor_keys = await self.redis_client.keys("sensor:*:latest")
            sensors = [key.decode().split(':')[1] for key in sensor_keys]
            return {"active_sensors": sensors}
        
        elif request_type == 'get_connection_stats':
            return {
                "active_connections": len(self.connection_manager.active_connections),
                "subscriptions": dict(self.connection_manager.client_subscriptions)
            }
        
        else:
            raise ValueError(f"Unknown request type: {request_type}")


def create_realtime_streaming_service(config: Dict[str, Any] = None) -> RealTimeStreamingService:
    """Factory function to create real-time streaming service"""
    if config is None:
        from common.config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.get_service_config("realtime_streaming")
    
    return RealTimeStreamingService(config)


if __name__ == "__main__":
    import uvicorn
    
    service = create_realtime_streaming_service()
    
    # Run the service
    uvicorn.run(
        service.app,
        host="0.0.0.0",
        port=8005,
        log_level="info"
    )
