"""
Real-time Data Streaming Service for EMS Agent

This service implements real-time data ingestion, processing, and streaming
capabilities using WebSockets, MQTT, and Redis for high-performance data flow.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor

import redis
import websockets
import paho.mqtt.client as mqtt
from prometheus_client import Counter, Histogram, Gauge
import pandas as pd
import numpy as np
from scipy import stats

from common.base_service import BaseService


# Metrics
STREAM_MESSAGES_TOTAL = Counter('stream_messages_total', 'Total streaming messages', ['type', 'source'])
STREAM_PROCESSING_TIME = Histogram('stream_processing_seconds', 'Stream processing time')
ACTIVE_CONNECTIONS = Gauge('active_connections_total', 'Active streaming connections', ['type'])
DATA_THROUGHPUT = Gauge('data_throughput_bytes_per_second', 'Data throughput', ['direction'])


@dataclass
class StreamMessage:
    """Standard message format for streaming data."""
    timestamp: float
    device_id: str
    metric_type: str
    value: float
    unit: str
    quality: str = "good"
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamMessage':
        return cls(**data)


class StreamBuffer:
    """High-performance circular buffer for streaming data."""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.RLock()
        self.total_messages = 0
        self.last_flush = time.time()
    
    def add(self, message: StreamMessage):
        with self.lock:
            self.buffer.append(message)
            self.total_messages += 1
            STREAM_MESSAGES_TOTAL.labels(type=message.metric_type, source=message.device_id).inc()
    
    def get_recent(self, seconds: int = 60) -> List[StreamMessage]:
        """Get messages from the last N seconds."""
        cutoff = time.time() - seconds
        with self.lock:
            return [msg for msg in self.buffer if msg.timestamp >= cutoff]
    
    def flush_old(self, max_age_seconds: int = 3600):
        """Remove messages older than max_age_seconds."""
        cutoff = time.time() - max_age_seconds
        with self.lock:
            while self.buffer and self.buffer[0].timestamp < cutoff:
                self.buffer.popleft()


class RealTimeAnalyzer:
    """Real-time data analysis and anomaly detection."""
    
    def __init__(self):
        self.metric_stats = defaultdict(lambda: {
            'values': deque(maxlen=1000),
            'mean': 0.0,
            'std': 0.0,
            'last_update': time.time()
        })
        self.anomaly_threshold = 3.0  # Z-score threshold
    
    def analyze_message(self, message: StreamMessage) -> Dict[str, Any]:
        """Analyze a single message for anomalies and patterns."""
        metric_key = f"{message.device_id}:{message.metric_type}"
        stats_data = self.metric_stats[metric_key]
        
        # Update rolling statistics
        stats_data['values'].append(message.value)
        if len(stats_data['values']) >= 10:
            values = list(stats_data['values'])
            stats_data['mean'] = np.mean(values)
            stats_data['std'] = np.std(values)
        
        # Anomaly detection
        is_anomaly = False
        anomaly_score = 0.0
        
        if stats_data['std'] > 0:
            z_score = abs((message.value - stats_data['mean']) / stats_data['std'])
            anomaly_score = z_score
            is_anomaly = z_score > self.anomaly_threshold
        
        # Trend analysis
        trend = "stable"
        if len(stats_data['values']) >= 20:
            recent_values = list(stats_data['values'])[-20:]
            slope, _, r_value, _, _ = stats.linregress(range(len(recent_values)), recent_values)
            if abs(r_value) > 0.7:  # Strong correlation
                trend = "increasing" if slope > 0 else "decreasing"
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': anomaly_score,
            'trend': trend,
            'mean': stats_data['mean'],
            'std': stats_data['std'],
            'analysis_timestamp': time.time()
        }


class WebSocketStreamer:
    """WebSocket streaming server for real-time data."""
    
    def __init__(self, port: int = 8765):
        self.port = port
        self.connections = set()
        self.subscriptions = defaultdict(set)  # topic -> connections
        self.server = None
    
    async def register_connection(self, websocket, path):
        """Register a new WebSocket connection."""
        self.connections.add(websocket)
        ACTIVE_CONNECTIONS.labels(type='websocket').set(len(self.connections))
        
        try:
            await websocket.wait_closed()
        finally:
            self.connections.remove(websocket)
            # Remove from all subscriptions
            for topic_connections in self.subscriptions.values():
                topic_connections.discard(websocket)
            ACTIVE_CONNECTIONS.labels(type='websocket').set(len(self.connections))
    
    async def subscribe(self, websocket, topic: str):
        """Subscribe a connection to a specific topic."""
        self.subscriptions[topic].add(websocket)
    
    async def unsubscribe(self, websocket, topic: str):
        """Unsubscribe a connection from a topic."""
        self.subscriptions[topic].discard(websocket)
    
    async def broadcast(self, message: Dict[str, Any], topic: str = "all"):
        """Broadcast message to all subscribers of a topic."""
        if not self.connections:
            return
        
        message_str = json.dumps(message)
        connections_to_notify = (
            self.subscriptions[topic] if topic != "all" 
            else self.connections
        )
        
        if connections_to_notify:
            await asyncio.gather(
                *[conn.send(message_str) for conn in connections_to_notify],
                return_exceptions=True
            )
    
    async def start_server(self):
        """Start the WebSocket server."""
        self.server = await websockets.serve(
            self.register_connection, 
            "localhost", 
            self.port
        )
        logging.info(f"WebSocket server started on port {self.port}")


class MQTTStreamer:
    """MQTT client for IoT device data streaming."""
    
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.message_handlers = {}
        self.connected = False
        
        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            self.connected = True
            logging.info("Connected to MQTT broker")
            # Subscribe to all EMS topics
            client.subscribe("ems/+/+")  # ems/device_id/metric_type
        else:
            logging.error(f"Failed to connect to MQTT broker: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection."""
        self.connected = False
        logging.warning("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        try:
            topic_parts = msg.topic.split('/')
            if len(topic_parts) >= 3 and topic_parts[0] == 'ems':
                device_id = topic_parts[1]
                metric_type = topic_parts[2]
                
                # Parse message payload
                payload = json.loads(msg.payload.decode())
                
                # Create stream message
                stream_msg = StreamMessage(
                    timestamp=payload.get('timestamp', time.time()),
                    device_id=device_id,
                    metric_type=metric_type,
                    value=float(payload['value']),
                    unit=payload.get('unit', ''),
                    quality=payload.get('quality', 'good'),
                    metadata=payload.get('metadata', {})
                )
                
                # Route to handlers
                for handler in self.message_handlers.values():
                    handler(stream_msg)
                
        except Exception as e:
            logging.error(f"Error processing MQTT message: {e}")
    
    def add_message_handler(self, name: str, handler: Callable[[StreamMessage], None]):
        """Add a message handler."""
        self.message_handlers[name] = handler
    
    def remove_message_handler(self, name: str):
        """Remove a message handler."""
        self.message_handlers.pop(name, None)
    
    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            logging.error(f"Failed to connect to MQTT broker: {e}")
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
    
    def publish_data(self, device_id: str, metric_type: str, data: Dict[str, Any]):
        """Publish data to MQTT topic."""
        if self.connected:
            topic = f"ems/{device_id}/{metric_type}"
            payload = json.dumps(data)
            self.client.publish(topic, payload)


class StreamingService(BaseService):
    """Main streaming service orchestrating all real-time components."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("streaming", config)
        
        # Configuration
        self.redis_url = config.get('redis_url', 'redis://localhost:6379')
        self.mqtt_broker = config.get('mqtt_broker', 'localhost')
        self.websocket_port = config.get('websocket_port', 8765)
        self.buffer_size = config.get('buffer_size', 10000)
        
        # Components
        self.redis_client = None
        self.stream_buffer = StreamBuffer(self.buffer_size)
        self.analyzer = RealTimeAnalyzer()
        self.websocket_streamer = WebSocketStreamer(self.websocket_port)
        self.mqtt_streamer = MQTTStreamer(self.mqtt_broker)
        
        # Background tasks
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running = False
        
        # Performance tracking
        self.last_throughput_check = time.time()
        self.bytes_processed = 0
    
    async def initialize(self):
        """Initialize the streaming service."""
        try:
            # Connect to Redis
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self._test_redis_connection()
            
            # Setup MQTT handlers
            self.mqtt_streamer.add_message_handler('buffer', self._handle_mqtt_message)
            self.mqtt_streamer.add_message_handler('analyzer', self._handle_mqtt_analysis)
            
            # Connect to MQTT
            self.mqtt_streamer.connect()
            
            # Start WebSocket server
            await self.websocket_streamer.start_server()
            
            self.running = True
            logging.info("Streaming service initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize streaming service: {e}")
            raise
    
    async def _test_redis_connection(self):
        """Test Redis connection."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self.redis_client.ping
            )
        except Exception as e:
            logging.error(f"Redis connection failed: {e}")
            raise
    
    def _handle_mqtt_message(self, message: StreamMessage):
        """Handle incoming MQTT messages."""
        with STREAM_PROCESSING_TIME.time():
            # Add to buffer
            self.stream_buffer.add(message)
            
            # Store in Redis for persistence
            self._store_in_redis(message)
            
            # Update throughput metrics
            self._update_throughput_metrics(message)
    
    def _handle_mqtt_analysis(self, message: StreamMessage):
        """Handle real-time analysis of messages."""
        try:
            # Perform analysis
            analysis = self.analyzer.analyze_message(message)
            
            # Create enriched message
            enriched_data = {
                'message': message.to_dict(),
                'analysis': analysis,
                'timestamp': time.time()
            }
            
            # Broadcast via WebSocket
            asyncio.create_task(
                self.websocket_streamer.broadcast(
                    enriched_data, 
                    topic=f"{message.device_id}:{message.metric_type}"
                )
            )
            
            # Store analysis if anomaly detected
            if analysis['is_anomaly']:
                self._store_anomaly(message, analysis)
                
        except Exception as e:
            logging.error(f"Error in real-time analysis: {e}")
    
    def _store_in_redis(self, message: StreamMessage):
        """Store message in Redis for fast retrieval."""
        try:
            # Store latest value per device/metric
            key = f"latest:{message.device_id}:{message.metric_type}"
            self.redis_client.setex(key, 3600, json.dumps(message.to_dict()))
            
            # Store in time series
            ts_key = f"ts:{message.device_id}:{message.metric_type}"
            self.redis_client.zadd(ts_key, {json.dumps(message.to_dict()): message.timestamp})
            
            # Keep only last 24 hours
            cutoff = time.time() - 86400
            self.redis_client.zremrangebyscore(ts_key, 0, cutoff)
            
        except Exception as e:
            logging.error(f"Error storing in Redis: {e}")
    
    def _store_anomaly(self, message: StreamMessage, analysis: Dict[str, Any]):
        """Store anomaly information for alerting."""
        try:
            anomaly_data = {
                'message': message.to_dict(),
                'analysis': analysis,
                'stored_at': time.time()
            }
            
            # Store in Redis anomaly stream
            self.redis_client.lpush('anomalies', json.dumps(anomaly_data))
            
            # Keep only last 1000 anomalies
            self.redis_client.ltrim('anomalies', 0, 999)
            
        except Exception as e:
            logging.error(f"Error storing anomaly: {e}")
    
    def _update_throughput_metrics(self, message: StreamMessage):
        """Update throughput performance metrics."""
        self.bytes_processed += len(json.dumps(message.to_dict()).encode())
        
        # Update metrics every 10 seconds
        now = time.time()
        if now - self.last_throughput_check >= 10:
            throughput = self.bytes_processed / (now - self.last_throughput_check)
            DATA_THROUGHPUT.labels(direction='inbound').set(throughput)
            
            self.bytes_processed = 0
            self.last_throughput_check = now
    
    async def get_real_time_data(self, device_id: str = None, metric_type: str = None, 
                                 last_seconds: int = 60) -> List[Dict[str, Any]]:
        """Get real-time data from buffer."""
        messages = self.stream_buffer.get_recent(last_seconds)
        
        # Filter if criteria provided
        if device_id:
            messages = [m for m in messages if m.device_id == device_id]
        if metric_type:
            messages = [m for m in messages if m.metric_type == metric_type]
        
        return [msg.to_dict() for msg in messages]
    
    async def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Get real-time status of a specific device."""
        try:
            # Get latest values for all metrics
            pattern = f"latest:{device_id}:*"
            keys = self.redis_client.keys(pattern)
            
            status = {'device_id': device_id, 'metrics': {}, 'last_seen': None}
            
            for key in keys:
                data = json.loads(self.redis_client.get(key))
                metric_type = key.split(':')[-1]
                status['metrics'][metric_type] = data
                
                # Track last seen timestamp
                if not status['last_seen'] or data['timestamp'] > status['last_seen']:
                    status['last_seen'] = data['timestamp']
            
            return status
            
        except Exception as e:
            logging.error(f"Error getting device status: {e}")
            return {'device_id': device_id, 'error': str(e)}
    
    async def get_anomalies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent anomalies."""
        try:
            anomaly_data = self.redis_client.lrange('anomalies', 0, limit - 1)
            return [json.loads(data) for data in anomaly_data]
        except Exception as e:
            logging.error(f"Error getting anomalies: {e}")
            return []
    
    async def simulate_data_stream(self, duration_seconds: int = 60):
        """Simulate real-time data for testing purposes."""
        import random
        
        devices = ['meter_001', 'meter_002', 'meter_003', 'hvac_001', 'lighting_001']
        metrics = ['power_consumption', 'voltage', 'current', 'temperature', 'humidity']
        
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds and self.running:
            for device in devices:
                for metric in metrics:
                    # Generate realistic data with occasional anomalies
                    base_value = {'power_consumption': 1000, 'voltage': 230, 'current': 4.3, 
                                'temperature': 22, 'humidity': 45}.get(metric, 100)
                    
                    # 5% chance of anomaly
                    if random.random() < 0.05:
                        value = base_value * random.uniform(0.1, 3.0)  # Anomalous value
                    else:
                        value = base_value * random.uniform(0.8, 1.2)  # Normal variation
                    
                    message = StreamMessage(
                        timestamp=time.time(),
                        device_id=device,
                        metric_type=metric,
                        value=round(value, 2),
                        unit={'power_consumption': 'W', 'voltage': 'V', 'current': 'A', 
                             'temperature': 'C', 'humidity': '%'}.get(metric, ''),
                        metadata={'simulated': True}
                    )
                    
                    # Process through handlers
                    self._handle_mqtt_message(message)
                    self._handle_mqtt_analysis(message)
            
            await asyncio.sleep(1)  # Send data every second
    
    async def shutdown(self):
        """Shutdown the streaming service."""
        self.running = False
        
        # Disconnect MQTT
        self.mqtt_streamer.disconnect()
        
        # Close WebSocket server
        if self.websocket_streamer.server:
            self.websocket_streamer.server.close()
            await self.websocket_streamer.server.wait_closed()
        
        # Close Redis connection
        if self.redis_client:
            self.redis_client.close()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logging.info("Streaming service shutdown complete")


# FastAPI integration
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/streaming", tags=["streaming"])

# Global streaming service instance
streaming_service: Optional[StreamingService] = None


async def get_streaming_service() -> StreamingService:
    """Get or create streaming service instance."""
    global streaming_service
    if not streaming_service:
        config = {
            'redis_url': 'redis://localhost:6379',
            'mqtt_broker': 'localhost',
            'websocket_port': 8765,
            'buffer_size': 10000
        }
        streaming_service = StreamingService(config)
        await streaming_service.initialize()
    return streaming_service


@router.get("/status")
async def get_streaming_status():
    """Get streaming service status."""
    service = await get_streaming_service()
    return {
        "status": "running" if service.running else "stopped",
        "buffer_size": len(service.stream_buffer.buffer),
        "total_messages": service.stream_buffer.total_messages,
        "active_connections": len(service.websocket_streamer.connections)
    }


@router.get("/data/real-time")
async def get_real_time_data(device_id: str = None, metric_type: str = None, 
                           last_seconds: int = 60):
    """Get real-time data from the stream buffer."""
    service = await get_streaming_service()
    return await service.get_real_time_data(device_id, metric_type, last_seconds)


@router.get("/device/{device_id}/status")
async def get_device_status(device_id: str):
    """Get real-time status of a specific device."""
    service = await get_streaming_service()
    return await service.get_device_status(device_id)


@router.get("/anomalies")
async def get_anomalies(limit: int = 100):
    """Get recent anomalies detected in the stream."""
    service = await get_streaming_service()
    return await service.get_anomalies(limit)


@router.post("/simulate")
async def start_simulation(duration_seconds: int = 60):
    """Start data simulation for testing."""
    service = await get_streaming_service()
    # Run simulation in background
    asyncio.create_task(service.simulate_data_stream(duration_seconds))
    return {"message": f"Started data simulation for {duration_seconds} seconds"}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming."""
    await websocket.accept()
    service = await get_streaming_service()
    
    # Add to WebSocket connections
    service.websocket_streamer.connections.add(websocket)
    
    try:
        while True:
            # Wait for client messages (subscription requests)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('action') == 'subscribe':
                topic = message.get('topic', 'all')
                await service.websocket_streamer.subscribe(websocket, topic)
                await websocket.send_text(json.dumps({
                    'type': 'subscription_confirmed',
                    'topic': topic
                }))
            
            elif message.get('action') == 'unsubscribe':
                topic = message.get('topic', 'all')
                await service.websocket_streamer.unsubscribe(websocket, topic)
                
    except WebSocketDisconnect:
        pass
    finally:
        service.websocket_streamer.connections.discard(websocket)
        # Remove from all subscriptions
        for topic_connections in service.websocket_streamer.subscriptions.values():
            topic_connections.discard(websocket)


# HTML page for testing WebSocket streaming
@router.get("/demo", response_class=HTMLResponse)
async def streaming_demo():
    """Demo page for real-time streaming."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>EMS Real-time Streaming Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
            .metric-card { border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: #f9f9f9; }
            .anomaly { background-color: #ffe6e6; border-color: #ff9999; }
            .controls { margin: 20px 0; }
            button { padding: 10px 20px; margin: 5px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            #status { padding: 10px; margin: 10px 0; border-radius: 4px; }
            .connected { background: #d4edda; color: #155724; }
            .disconnected { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>EMS Real-time Streaming Demo</h1>
            
            <div id="status" class="disconnected">Disconnected</div>
            
            <div class="controls">
                <button onclick="connect()">Connect</button>
                <button onclick="disconnect()">Disconnect</button>
                <button onclick="startSimulation()">Start Simulation</button>
                <button onclick="clearMetrics()">Clear</button>
            </div>
            
            <div id="metrics" class="metrics"></div>
        </div>
        
        <script>
            let ws = null;
            let metrics = {};
            
            function connect() {
                ws = new WebSocket('ws://localhost:8000/streaming/ws');
                
                ws.onopen = function() {
                    document.getElementById('status').textContent = 'Connected';
                    document.getElementById('status').className = 'connected';
                    
                    // Subscribe to all topics
                    ws.send(JSON.stringify({action: 'subscribe', topic: 'all'}));
                };
                
                ws.onclose = function() {
                    document.getElementById('status').textContent = 'Disconnected';
                    document.getElementById('status').className = 'disconnected';
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'subscription_confirmed') {
                        console.log('Subscribed to topic:', data.topic);
                        return;
                    }
                    
                    if (data.message && data.analysis) {
                        updateMetric(data.message, data.analysis);
                    }
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }
            
            function startSimulation() {
                fetch('/streaming/simulate', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => console.log('Simulation started:', data));
            }
            
            function updateMetric(message, analysis) {
                const key = message.device_id + ':' + message.metric_type;
                metrics[key] = {message, analysis, updated: Date.now()};
                renderMetrics();
            }
            
            function renderMetrics() {
                const container = document.getElementById('metrics');
                container.innerHTML = '';
                
                Object.entries(metrics).forEach(([key, data]) => {
                    const {message, analysis} = data;
                    const card = document.createElement('div');
                    card.className = 'metric-card' + (analysis.is_anomaly ? ' anomaly' : '');
                    
                    card.innerHTML = `
                        <h3>${message.device_id} - ${message.metric_type}</h3>
                        <p><strong>Value:</strong> ${message.value} ${message.unit}</p>
                        <p><strong>Quality:</strong> ${message.quality}</p>
                        <p><strong>Timestamp:</strong> ${new Date(message.timestamp * 1000).toLocaleTimeString()}</p>
                        <hr>
                        <p><strong>Anomaly:</strong> ${analysis.is_anomaly ? 'YES' : 'No'}</p>
                        <p><strong>Score:</strong> ${analysis.anomaly_score.toFixed(2)}</p>
                        <p><strong>Trend:</strong> ${analysis.trend}</p>
                        <p><strong>Mean:</strong> ${analysis.mean.toFixed(2)}</p>
                        <p><strong>Std Dev:</strong> ${analysis.std.toFixed(2)}</p>
                    `;
                    
                    container.appendChild(card);
                });
            }
            
            function clearMetrics() {
                metrics = {};
                renderMetrics();
            }
            
            // Auto-connect on page load
            window.onload = connect;
        </script>
    </body>
    </html>
    """
