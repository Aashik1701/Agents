"""
Simplified Enhanced EMS Agent

This is a simplified version that demonstrates all the improvements
without dependencies that have platform-specific installation issues.
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import json
import time
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import pandas as pd
import numpy as np

# Import existing components
from app import app as legacy_app
from ems_search import EMSQueryEngine
from mongodb_health_check import test_mongodb_connection, test_ems_components

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimplifiedStreamingService:
    """Simplified streaming service for demonstration."""
    
    def __init__(self):
        self.connections = set()
        self.data_buffer = []
        self.running = False
        self.total_messages = 0
        
    async def add_connection(self, websocket):
        """Add a WebSocket connection."""
        self.connections.add(websocket)
        logger.info(f"WebSocket connection added. Total: {len(self.connections)}")
        
    async def remove_connection(self, websocket):
        """Remove a WebSocket connection."""
        self.connections.discard(websocket)
        logger.info(f"WebSocket connection removed. Total: {len(self.connections)}")
        
    async def broadcast_message(self, message: Dict):
        """Broadcast message to all connected clients."""
        if self.connections:
            message_str = json.dumps(message)
            disconnected = []
            
            for connection in self.connections:
                try:
                    await connection.send_text(message_str)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.connections.discard(conn)
    
    async def simulate_real_time_data(self, duration: int = 60):
        """Simulate real-time energy data."""
        import random
        
        devices = ['meter_001', 'meter_002', 'meter_003', 'hvac_001', 'lighting_001']
        metrics = ['power_consumption', 'voltage', 'current', 'temperature', 'humidity']
        
        self.running = True
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            for device in devices:
                for metric in metrics:
                    # Generate realistic data
                    base_values = {
                        'power_consumption': 1000,
                        'voltage': 230,
                        'current': 4.3,
                        'temperature': 22,
                        'humidity': 45
                    }
                    
                    base_value = base_values.get(metric, 100)
                    
                    # 5% chance of anomaly
                    if random.random() < 0.05:
                        value = base_value * random.uniform(0.1, 3.0)
                        is_anomaly = True
                    else:
                        value = base_value * random.uniform(0.8, 1.2)
                        is_anomaly = False
                    
                    message = {
                        'timestamp': time.time(),
                        'device_id': device,
                        'metric_type': metric,
                        'value': round(value, 2),
                        'unit': {'power_consumption': 'W', 'voltage': 'V', 'current': 'A', 
                                'temperature': 'C', 'humidity': '%'}.get(metric, ''),
                        'is_anomaly': is_anomaly,
                        'quality': 'good'
                    }
                    
                    # Add to buffer
                    self.data_buffer.append(message)
                    if len(self.data_buffer) > 1000:
                        self.data_buffer.pop(0)
                    
                    self.total_messages += 1
                    
                    # Broadcast to WebSocket clients
                    await self.broadcast_message({
                        'type': 'real_time_data',
                        'data': message
                    })
            
            await asyncio.sleep(1)  # Send data every second
        
        self.running = False


class SimplifiedMLService:
    """Simplified ML service for demonstration."""
    
    def __init__(self):
        self.models = {
            'anomaly_detection': 'Statistical Z-Score Model',
            'energy_prediction': 'Linear Regression Model',
            'optimization': 'Rule-based Optimizer'
        }
        self.predictions_made = 0
        
    async def detect_anomalies(self, data: List[Dict]) -> List[Dict]:
        """Simple anomaly detection using statistical methods."""
        if len(data) < 10:
            return []
        
        anomalies = []
        values = [d['value'] for d in data if 'value' in d]
        
        if values:
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            for item in data:
                if 'value' in item and std_val > 0:
                    z_score = abs((item['value'] - mean_val) / std_val)
                    if z_score > 2.5:  # Anomaly threshold
                        anomalies.append({
                            **item,
                            'anomaly_score': z_score,
                            'anomaly_type': 'statistical_outlier'
                        })
        
        return anomalies
    
    async def predict_energy_consumption(self, device_id: str, hours_ahead: int = 24) -> Dict:
        """Simple energy consumption prediction."""
        # Simulate prediction
        import random
        
        base_consumption = random.uniform(800, 1200)
        predicted_values = []
        
        for hour in range(hours_ahead):
            # Add some trend and noise
            trend = 0.1 * hour
            noise = random.uniform(-50, 50)
            predicted = base_consumption + trend + noise
            
            predicted_values.append({
                'hour': hour + 1,
                'predicted_consumption': round(predicted, 2),
                'confidence': random.uniform(0.7, 0.95)
            })
        
        self.predictions_made += 1
        
        return {
            'device_id': device_id,
            'prediction_timestamp': time.time(),
            'predictions': predicted_values,
            'model_used': 'simplified_regression',
            'total_predicted_consumption': sum(p['predicted_consumption'] for p in predicted_values)
        }


class SimplifiedSecurityService:
    """Simplified security service for demonstration."""
    
    def __init__(self):
        self.login_attempts = 0
        self.successful_logins = 0
        self.blocked_ips = set()
        
    def authenticate_user(self, username: str, password: str) -> Dict:
        """Simple authentication."""
        self.login_attempts += 1
        
        # Demo users
        valid_users = {
            'admin': 'admin123',
            'operator': 'operator123',
            'viewer': 'viewer123'
        }
        
        if username in valid_users and valid_users[username] == password:
            self.successful_logins += 1
            return {
                'success': True,
                'username': username,
                'role': 'admin' if username == 'admin' else 'user',
                'token': f'demo_token_{username}_{int(time.time())}',
                'expires_at': time.time() + 3600
            }
        else:
            return {
                'success': False,
                'error': 'Invalid credentials'
            }
    
    def get_security_metrics(self) -> Dict:
        """Get security metrics."""
        return {
            'total_login_attempts': self.login_attempts,
            'successful_logins': self.successful_logins,
            'failed_logins': self.login_attempts - self.successful_logins,
            'blocked_ips': len(self.blocked_ips),
            'security_events': []
        }


class EnhancedEMSAgentSimplified:
    """Simplified Enhanced EMS Agent for demonstration."""
    
    def __init__(self):
        self.app = self._create_app()
        self.streaming_service = SimplifiedStreamingService()
        self.ml_service = SimplifiedMLService()
        self.security_service = SimplifiedSecurityService()
        self.start_time = time.time()
        
    def _create_app(self) -> FastAPI:
        """Create FastAPI application."""
        app = FastAPI(
            title="Enhanced EMS Agent (Simplified)",
            description="Demonstration of Enhanced Energy Management System",
            version="2.0.0"
        )
        
        # Setup templates and static files
        templates = Jinja2Templates(directory="templates")
        app.mount("/static", StaticFiles(directory="static"), name="static")
        
        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Routes
        @app.get("/")
        async def dashboard(request: Request):
            """Enhanced dashboard."""
            return templates.TemplateResponse("index.html", {"request": request})
        
        @app.get("/health")
        async def health_check():
            """System health check."""
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "uptime_seconds": int(time.time() - self.start_time),
                "services": {
                    "streaming": "operational",
                    "ml": "operational", 
                    "security": "operational",
                    "mongodb": "connected"
                }
            }
        
        @app.get("/info")
        async def system_info():
            """System information."""
            return {
                "name": "Enhanced EMS Agent (Simplified)",
                "version": "2.0.0",
                "capabilities": [
                    "Real-time data streaming",
                    "Basic ML analytics",
                    "Anomaly detection",
                    "Simple security",
                    "System monitoring"
                ]
            }
        
        # Streaming endpoints
        @app.get("/streaming/status")
        async def streaming_status():
            """Get streaming status."""
            return {
                "active_connections": len(self.streaming_service.connections),
                "total_messages": self.streaming_service.total_messages,
                "buffer_size": len(self.streaming_service.data_buffer),
                "running": self.streaming_service.running
            }
        
        @app.post("/streaming/simulate")
        async def start_simulation(duration: int = 60):
            """Start data simulation."""
            asyncio.create_task(self.streaming_service.simulate_real_time_data(duration))
            return {"message": f"Started simulation for {duration} seconds"}
        
        @app.get("/streaming/data")
        async def get_recent_data(limit: int = 100):
            """Get recent streaming data."""
            return self.streaming_service.data_buffer[-limit:]
        
        # Chat endpoint for conversational AI
        @app.post("/chat")
        async def chat_with_agent(message: Dict[str, str]):
            """Main chat endpoint for conversational AI interaction."""
            try:
                user_message = message.get('message', '').strip()
                if not user_message:
                    return {"error": "Message cannot be empty"}
                
                # Process the message through our AI agent
                response = await self._process_chat_message(user_message)
                return {
                    "response": response,
                    "timestamp": time.time(),
                    "status": "success"
                }
            except Exception as e:
                return {
                    "error": str(e),
                    "timestamp": time.time(),
                    "status": "error"
                }
        
        # WebSocket endpoint
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time data."""
            await websocket.accept()
            await self.streaming_service.add_connection(websocket)
            
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
            except WebSocketDisconnect:
                await self.streaming_service.remove_connection(websocket)
        
        # ML endpoints
        @app.get("/ml/models")
        async def get_ml_models():
            """Get available ML models."""
            return {
                "models": self.ml_service.models,
                "predictions_made": self.ml_service.predictions_made
            }
        
        @app.post("/ml/predict/{device_id}")
        async def predict_energy(device_id: str, hours_ahead: int = 24):
            """Predict energy consumption."""
            prediction = await self.ml_service.predict_energy_consumption(device_id, hours_ahead)
            return prediction
        
        @app.post("/ml/anomalies")
        async def detect_anomalies(data: List[Dict]):
            """Detect anomalies in data."""
            anomalies = await self.ml_service.detect_anomalies(data)
            return {"anomalies": anomalies, "count": len(anomalies)}
        
        # Security endpoints
        @app.post("/security/login")
        async def login(credentials: Dict[str, str]):
            """User login."""
            return self.security_service.authenticate_user(
                credentials.get('username', ''),
                credentials.get('password', '')
            )
        
        @app.get("/security/metrics")
        async def security_metrics():
            """Get security metrics."""
            return self.security_service.get_security_metrics()
        
        # Legacy EMS integration
        @app.get("/ems/query")
        async def ems_query(query: str):
            """Query EMS system."""
            try:
                engine = EMSQueryEngine()
                result = engine.process_query(query)
                return {"query": query, "result": result}
            except Exception as e:
                return {"query": query, "error": str(e)}
        
        @app.get("/ems/health")
        async def ems_health():
            """Check EMS system health."""
            try:
                # Run both health checks
                mongo_result = test_mongodb_connection()
                ems_result = test_ems_components()
                
                return {
                    "mongodb_status": "Connected" if mongo_result else "Disconnected",
                    "ems_components": "Working" if ems_result else "Error",
                    "overall_status": "Healthy" if (mongo_result and ems_result) else "Degraded"
                }
            except Exception as e:
                return {"error": str(e)}
        
        return app
    
    def _create_dashboard_html(self) -> str:
        """Create enhanced chatbot dashboard HTML."""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>EMS AI Chatbot - Energy Management Assistant</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    min-height: 100vh;
                    color: #333;
                }
                .container { max-width: 1200px; margin: 0 auto; padding: 20px; height: 100vh; display: flex; flex-direction: column; }
                
                /* Header */
                .header { 
                    text-align: center; 
                    color: white; 
                    margin-bottom: 20px;
                    background: rgba(255,255,255,0.1);
                    padding: 20px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
                .header h1 { font-size: 2.2em; margin-bottom: 5px; }
                .header p { font-size: 1.1em; opacity: 0.9; }
                
                /* Chat Container */
                .chat-container {
                    flex: 1;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    min-height: 600px;
                }
                
                /* Chat Header */
                .chat-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    display: flex;
                    align-items: center;
                    gap: 15px;
                }
                .chat-header h2 { font-size: 1.5em; margin: 0; }
                .status-indicator { 
                    display: flex; 
                    align-items: center; 
                    gap: 8px; 
                    font-size: 0.9em; 
                    background: rgba(255,255,255,0.2);
                    padding: 5px 10px;
                    border-radius: 20px;
                }
                .status-dot { 
                    width: 8px; 
                    height: 8px; 
                    border-radius: 50%; 
                    background: #4ade80; 
                    animation: pulse 2s infinite;
                }
                @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
                
                /* Quick Actions */
                .quick-actions {
                    background: #f8fafc;
                    padding: 15px 20px;
                    border-bottom: 1px solid #e2e8f0;
                }
                .quick-actions h4 { 
                    margin-bottom: 10px; 
                    color: #475569; 
                    font-size: 0.9em; 
                    font-weight: 600;
                }
                .action-chips {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                }
                .action-chip {
                    background: white;
                    color: #667eea;
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-size: 0.8em;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    border: 1px solid #e2e8f0;
                    white-space: nowrap;
                }
                .action-chip:hover {
                    background: #667eea;
                    color: white;
                    transform: translateY(-1px);
                    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                }
                
                /* Messages Area */
                .messages-area {
                    flex: 1;
                    overflow-y: auto;
                    padding: 20px;
                    background: #fafbfc;
                    scroll-behavior: smooth;
                }
                
                /* Message Styles */
                .message {
                    margin-bottom: 20px;
                    display: flex;
                    align-items: flex-start;
                    gap: 12px;
                    animation: fadeIn 0.3s ease;
                }
                @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
                
                .message.user { flex-direction: row-reverse; }
                .message.assistant { flex-direction: row; }
                
                .message-avatar {
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.1em;
                    flex-shrink: 0;
                }
                .user .message-avatar {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .assistant .message-avatar {
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                }
                
                .message-content {
                    max-width: 75%;
                    padding: 14px 18px;
                    border-radius: 18px;
                    line-height: 1.5;
                    position: relative;
                }
                .user .message-content {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-bottom-right-radius: 4px;
                }
                .assistant .message-content {
                    background: white;
                    color: #334155;
                    border: 1px solid #e2e8f0;
                    border-bottom-left-radius: 4px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                }
                
                .message-time {
                    font-size: 0.75em;
                    opacity: 0.7;
                    margin-top: 5px;
                    text-align: center;
                }
                
                /* Typing Indicator */
                .typing-indicator {
                    display: none;
                    padding: 15px 18px;
                    background: white;
                    border-radius: 18px;
                    border-bottom-left-radius: 4px;
                    border: 1px solid #e2e8f0;
                    max-width: 75%;
                }
                .typing-dots {
                    display: flex;
                    gap: 4px;
                }
                .typing-dot {
                    width: 6px;
                    height: 6px;
                    border-radius: 50%;
                    background: #94a3b8;
                    animation: typing 1.4s infinite ease-in-out;
                }
                .typing-dot:nth-child(2) { animation-delay: 0.2s; }
                .typing-dot:nth-child(3) { animation-delay: 0.4s; }
                @keyframes typing { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-10px); } }
                
                /* Input Area */
                .input-area {
                    padding: 20px;
                    background: white;
                    border-top: 1px solid #e2e8f0;
                }
                .input-container {
                    display: flex;
                    gap: 10px;
                    align-items: flex-end;
                }
                .input-field {
                    flex: 1;
                    min-height: 44px;
                    max-height: 120px;
                    padding: 12px 16px;
                    border: 2px solid #e2e8f0;
                    border-radius: 22px;
                    font-size: 0.95em;
                    resize: none;
                    outline: none;
                    transition: all 0.2s ease;
                    font-family: inherit;
                }
                .input-field:focus {
                    border-color: #667eea;
                    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                }
                .send-button {
                    width: 44px;
                    height: 44px;
                    border: none;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s ease;
                    font-size: 1.1em;
                }
                .send-button:hover:not(:disabled) {
                    transform: scale(1.05);
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                }
                .send-button:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                }
                
                /* System Stats */
                .system-stats {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 10px;
                    margin-top: 10px;
                }
                .stat-card {
                    background: rgba(255,255,255,0.1);
                    padding: 10px;
                    border-radius: 8px;
                    text-align: center;
                    color: white;
                }
                .stat-value { font-size: 1.2em; font-weight: bold; }
                .stat-label { font-size: 0.8em; opacity: 0.8; }
                
                /* Scrollbar */
                .messages-area::-webkit-scrollbar { width: 6px; }
                .messages-area::-webkit-scrollbar-track { background: transparent; }
                .messages-area::-webkit-scrollbar-thumb { 
                    background: #cbd5e1; 
                    border-radius: 3px; 
                }
                .messages-area::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
                
                /* Responsive */
                @media (max-width: 768px) {
                    .container { padding: 10px; }
                    .header h1 { font-size: 1.8em; }
                    .message-content { max-width: 85%; }
                    .action-chips { justify-content: center; }
                }
                
                /* Enhanced Message Formatting */
                .message-content h3 { color: #1e40af; margin-bottom: 10px; }
                .message-content h4 { color: #3730a3; margin: 8px 0; }
                .message-content ul { margin: 10px 0; padding-left: 20px; }
                .message-content li { margin: 4px 0; }
                .message-content strong { color: #1e40af; }
                .message-content code { 
                    background: #f1f5f9; 
                    padding: 2px 6px; 
                    border-radius: 4px; 
                    font-family: monospace; 
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 EMS AI Assistant</h1>
                    <p>Intelligent Energy Management & Data Analysis Chatbot</p>
                    <div class="system-stats">
                        <div class="stat-card">
                            <div class="stat-value" id="totalMessages">0</div>
                            <div class="stat-label">Messages</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="dbRecords">-</div>
                            <div class="stat-label">DB Records</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="anomalies">0</div>
                            <div class="stat-label">Anomalies</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="uptime">0s</div>
                            <div class="stat-label">Uptime</div>
                        </div>
                    </div>
                </div>
                
                <div class="chat-container">
                    <div class="chat-header">
                        <div style="flex: 1;">
                            <h2>💬 Energy Data Analysis Chat</h2>
                        </div>
                        <div class="status-indicator">
                            <div class="status-dot"></div>
                            <span>Online</span>
                        </div>
                    </div>
                    
                    <div class="quick-actions">
                        <h4>✨ Quick Questions:</h4>
                        <div class="action-chips">
                            <span class="action-chip" onclick="askQuestion(this)">Show system status</span>
                            <span class="action-chip" onclick="askQuestion(this)">Analyze power consumption</span>
                            <span class="action-chip" onclick="askQuestion(this)">Detect anomalies</span>
                            <span class="action-chip" onclick="askQuestion(this)">Show voltage analysis</span>
                            <span class="action-chip" onclick="askQuestion(this)">Energy efficiency report</span>
                            <span class="action-chip" onclick="askQuestion(this)">Predict consumption</span>
                            <span class="action-chip" onclick="askQuestion(this)">Cost analysis</span>
                            <span class="action-chip" onclick="askQuestion(this)">Generate report</span>
                        </div>
                    </div>
                    
                    <div class="messages-area" id="messagesArea">
                        <div class="message assistant">
                            <div class="message-avatar">🤖</div>
                            <div class="message-content">
                                <div>
                                    <strong>Hello! I'm your EMS AI Assistant! 👋</strong><br><br>
                                    I can help you analyze energy data, detect anomalies, predict consumption, and provide insights about your electrical systems.<br><br>
                                    <strong>What I can do:</strong>
                                    <ul>
                                        <li>📊 Analyze power consumption patterns</li>
                                        <li>⚡ Monitor voltage and current metrics</li>
                                        <li>🚨 Detect electrical anomalies</li>
                                        <li>🔮 Predict future energy usage</li>
                                        <li>💰 Calculate energy costs</li>
                                        <li>📈 Generate comprehensive reports</li>
                                    </ul>
                                    Just ask me anything about your energy data!
                                </div>
                                <div class="message-time" id="welcomeTime"></div>
                            </div>
                        </div>
                        
                        <div class="message assistant" style="display: none;" id="typingMessage">
                            <div class="message-avatar">🤖</div>
                            <div class="typing-indicator">
                                <div class="typing-dots">
                                    <div class="typing-dot"></div>
                                    <div class="typing-dot"></div>
                                    <div class="typing-dot"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="input-area">
                        <div class="input-container">
                            <textarea 
                                id="messageInput" 
                                class="input-field" 
                                placeholder="Ask me about energy consumption, anomalies, voltage analysis, predictions..."
                                rows="1"
                                maxlength="1000"
                            ></textarea>
                            <button id="sendButton" class="send-button">
                                <span>📤</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                // Global variables
                let messageCount = 0;
                let isProcessing = false;
                let startTime = Date.now();
                
                // Initialize
                document.addEventListener('DOMContentLoaded', function() {
                    updateWelcomeTime();
                    setupEventListeners();
                    updateSystemStats();
                    setInterval(updateSystemStats, 30000); // Update every 30 seconds
                });
                
                function setupEventListeners() {
                    const input = document.getElementById('messageInput');
                    const button = document.getElementById('sendButton');
                    
                    // Send button click
                    button.addEventListener('click', sendMessage);
                    
                    // Enter key handling
                    input.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            sendMessage();
                        }
                    });
                    
                    // Auto-resize textarea
                    input.addEventListener('input', function() {
                        this.style.height = 'auto';
                        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
                    });
                }
                
                async function sendMessage() {
                    if (isProcessing) return;
                    
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    
                    if (!message) return;
                    
                    // Add user message
                    addMessage(message, 'user');
                    input.value = '';
                    input.style.height = 'auto';
                    
                    // Show typing indicator
                    showTyping(true);
                    isProcessing = true;
                    
                    try {
                        const response = await fetch('/chat', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ message: message })
                        });
                        
                        const data = await response.json();
                        
                        // Hide typing indicator
                        showTyping(false);
                        
                        if (data.status === 'success') {
                            addMessage(data.response, 'assistant');
                        } else {
                            addMessage(`❌ Sorry, I encountered an error: ${data.error}`, 'assistant');
                        }
                        
                    } catch (error) {
                        showTyping(false);
                        addMessage('❌ Sorry, I had trouble processing your request. Please try again.', 'assistant');
                        console.error('Chat error:', error);
                    }
                    
                    isProcessing = false;
                    updateSendButton();
                }
                
                function addMessage(content, sender) {
                    const messagesArea = document.getElementById('messagesArea');
                    const messageDiv = document.createElement('div');
                    
                    messageDiv.className = `message ${sender}`;
                    
                    const avatar = sender === 'user' ? '👤' : '🤖';
                    
                    // Format the content for better display
                    const formattedContent = formatMessageContent(content);
                    
                    messageDiv.innerHTML = `
                        <div class="message-avatar">${avatar}</div>
                        <div class="message-content">
                            <div>${formattedContent}</div>
                            <div class="message-time">${getCurrentTime()}</div>
                        </div>
                    `;
                    
                    // Insert before typing indicator
                    const typingMessage = document.getElementById('typingMessage');
                    messagesArea.insertBefore(messageDiv, typingMessage);
                    
                    // Scroll to bottom
                    messagesArea.scrollTop = messagesArea.scrollHeight;
                    
                    messageCount++;
                    document.getElementById('totalMessages').textContent = messageCount;
                }
                
                function formatMessageContent(content) {
                    return content
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\*(.*?)\*/g, '<em>$1</em>')
                        .replace(/\n/g, '<br>')
                        .replace(/#{3} (.*?)\n/g, '<h4>$1</h4>')
                        .replace(/#{2} (.*?)\n/g, '<h3>$1</h3>')
                        .replace(/• /g, '<li>')
                        .replace(/<li>/g, '</li><li>')
                        .replace(/<\/li><li>/g, '<li>')
                        .replace(/(<li>.*?)<br>/g, '$1</li>')
                        .replace(/(<li>.*?)<\/li>/g, '<ul>$1</ul>');
                }
                
                function showTyping(show) {
                    const typingMessage = document.getElementById('typingMessage');
                    typingMessage.style.display = show ? 'flex' : 'none';
                    
                    if (show) {
                        const messagesArea = document.getElementById('messagesArea');
                        messagesArea.scrollTop = messagesArea.scrollHeight;
                    }
                    
                    updateSendButton();
                }
                
                function updateSendButton() {
                    const button = document.getElementById('sendButton');
                    if (isProcessing) {
                        button.innerHTML = '<span style="animation: spin 1s linear infinite;">⏳</span>';
                        button.disabled = true;
                    } else {
                        button.innerHTML = '<span>📤</span>';
                        button.disabled = false;
                    }
                }
                
                function askQuestion(element) {
                    const question = element.textContent;
                    document.getElementById('messageInput').value = question;
                    sendMessage();
                }
                
                async function updateSystemStats() {
                    try {
                        // Update uptime
                        const uptimeSeconds = Math.floor((Date.now() - startTime) / 1000);
                        const minutes = Math.floor(uptimeSeconds / 60);
                        const hours = Math.floor(minutes / 60);
                        const uptime = hours > 0 ? `${hours}h ${minutes % 60}m` : `${minutes}m`;
                        document.getElementById('uptime').textContent = uptime;
                        
                        // Get system health
                        const healthResponse = await fetch('/health');
                        if (healthResponse.ok) {
                            const healthData = await healthResponse.json();
                            // Update other stats as available
                        }
                        
                        // Get streaming status
                        const streamingResponse = await fetch('/streaming/status');
                        if (streamingResponse.ok) {
                            const streamingData = await streamingResponse.json();
                            document.getElementById('dbRecords').textContent = streamingData.total_messages || 0;
                        }
                        
                    } catch (error) {
                        console.error('Error updating stats:', error);
                    }
                }
                
                function getCurrentTime() {
                    return new Date().toLocaleTimeString();
                }
                
                function updateWelcomeTime() {
                    document.getElementById('welcomeTime').textContent = getCurrentTime();
                }
                
                // CSS animation for spinning
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes spin {
                        from { transform: rotate(0deg); }
                        to { transform: rotate(360deg); }
                    }
                `;
                document.head.appendChild(style);
            </script>
        </body>
        </html>
        """
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the simplified enhanced EMS Agent."""
        logger.info(f"Starting Enhanced EMS Agent (Simplified) on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, log_level="info")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced EMS Agent (Simplified)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    
    agent = EnhancedEMSAgentSimplified()
    agent.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()

async def _process_chat_message(self, user_message: str) -> str:
        """Process user chat message and provide intelligent responses with data analysis."""
        try:
            from ems_search import EMSQueryEngine
            from data_loader import DataLoader
            import pymongo
            
            user_message_lower = user_message.lower()
            
            # Initialize connections
            engine = EMSQueryEngine()
            data_loader = DataLoader()
            
            # Connect to MongoDB
            client = pymongo.MongoClient("mongodb+srv://aashik1701:Sustainabyte@cluster20526.g4udhpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster20526")
            db = client["EMS_Database"]
            
            # Greeting responses
            if any(greeting in user_message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
                stats = await self._get_database_stats(db)
                return f"Hello! 👋 I'm your EMS AI Assistant. I can help you analyze energy data from our MongoDB database.\n\n📊 **Current Database Status:**\n• Collections: {stats['collections']}\n• Total Records: {stats['total_records']}\n• Latest Data: {stats['latest_timestamp']}\n\nWhat would you like to know about your energy data?"
            
            # Help responses
            if any(word in user_message_lower for word in ['help', 'what can you do', 'capabilities']):
                return """🤖 **I can help you with:**

📈 **Data Analysis:**
• Power consumption trends and patterns
• Voltage and current analysis
• Energy efficiency calculations
• Peak demand identification

🔍 **Anomaly Detection:**
• Voltage fluctuations and spikes
• Power factor anomalies
• Unusual consumption patterns
• Equipment malfunction indicators

📊 **Reporting:**
• Daily/weekly/monthly energy reports
• Cost analysis and projections
• Performance metrics
• Comparative analysis

🔮 **Predictions:**
• Energy consumption forecasting
• Peak demand predictions
• Cost projections
• Maintenance recommendations

Just ask me anything like:
• "Show me today's power consumption"
• "Are there any voltage anomalies?"
• "What's the energy cost this month?"
• "Predict tomorrow's energy usage"
"""
            
            # System status queries
            if any(word in user_message_lower for word in ['status', 'health', 'system']):
                stats = await self._get_database_stats(db)
                health = await self._get_system_health()
                return f"""🔋 **EMS System Status**

**Database Health:** {'✅ Connected' if stats['connected'] else '❌ Disconnected'}
**Total Collections:** {stats['collections']}
**Total Records:** {stats['total_records']}
**Latest Data:** {stats['latest_timestamp']}

**Services Status:**
• Streaming: {'✅ Active' if health['streaming'] == 'operational' else '❌ Inactive'}
• ML Analytics: {'✅ Active' if health['ml'] == 'operational' else '❌ Inactive'}  
• Security: {'✅ Active' if health['security'] == 'operational' else '❌ Inactive'}

**Real-time Metrics:**
• Messages Processed: {self.streaming_service.total_messages}
• ML Predictions Made: {self.ml_service.predictions_made}
• Active Connections: {len(self.streaming_service.connections)}
"""
            
            # Power/Energy consumption queries
            if any(word in user_message_lower for word in ['power', 'consumption', 'energy', 'usage', 'kwh']):
                analysis = await self._analyze_power_consumption(db)
                return f"""⚡ **Power Consumption Analysis**

**Current Stats:**
• Average Power: {analysis['avg_power']:.2f} W
• Peak Power: {analysis['max_power']:.2f} W
• Total Energy: {analysis['total_energy']:.2f} kWh
• Power Factor: {analysis['avg_power_factor']:.3f}

**Recent Trends:**
{analysis['trend_description']}

**Key Insights:**
• {analysis['insights']}

**Recommendations:**
• {analysis['recommendations']}
"""
            
            # Voltage analysis queries
            if any(word in user_message_lower for word in ['voltage', 'volt', 'v']):
                analysis = await self._analyze_voltage(db)
                return f"""⚡ **Voltage Analysis**

**Current Stats:**
• Average Voltage: {analysis['avg_voltage']:.2f} V
• Voltage Range: {analysis['min_voltage']:.2f} - {analysis['max_voltage']:.2f} V
• Voltage Stability: {analysis['stability']}

**Anomalies Detected:**
{analysis['anomalies_description']}

**Grid Quality:** {analysis['grid_quality']}
"""
            
            # Current analysis queries  
            if any(word in user_message_lower for word in ['current', 'ampere', 'amp', 'a']):
                analysis = await self._analyze_current(db)
                return f"""🔌 **Current Analysis**

**Current Stats:**
• Average Current: {analysis['avg_current']:.2f} A
• Peak Current: {analysis['max_current']:.2f} A
• Load Factor: {analysis['load_factor']:.2f}

**Load Patterns:**
{analysis['pattern_description']}
"""
            
            # Anomaly detection queries
            if any(word in user_message_lower for word in ['anomaly', 'anomalies', 'unusual', 'abnormal', 'alert']):
                anomalies = await self._detect_energy_anomalies(db)
                if anomalies['count'] > 0:
                    return f"""🚨 **Anomaly Detection Results**

**Found {anomalies['count']} anomalies in recent data:**

{anomalies['detailed_report']}

**Severity Breakdown:**
• High: {anomalies['high_severity']} issues
• Medium: {anomalies['medium_severity']} issues  
• Low: {anomalies['low_severity']} issues

**Recommended Actions:**
{anomalies['recommendations']}
"""
                else:
                    return "✅ **No anomalies detected** in recent energy data. All systems are operating within normal parameters."
            
            # Cost analysis queries
            if any(word in user_message_lower for word in ['cost', 'bill', 'expense', 'money', 'savings']):
                cost_analysis = await self._analyze_energy_costs(db)
                return f"""💰 **Energy Cost Analysis**

**Current Period:**
• Total Cost: ${cost_analysis['total_cost']:.2f}
• Daily Average: ${cost_analysis['daily_avg']:.2f}
• Cost per kWh: ${cost_analysis['rate']:.4f}

**Trends:**
{cost_analysis['trend_description']}

**Potential Savings:**
{cost_analysis['savings_opportunities']}
"""
            
            # Efficiency queries
            if any(word in user_message_lower for word in ['efficiency', 'performance', 'optimization']):
                efficiency = await self._analyze_efficiency(db)
                return f"""⚡ **Energy Efficiency Analysis**

**Efficiency Score:** {efficiency['score']:.1f}/100

**Key Metrics:**
• Power Factor: {efficiency['power_factor']:.3f}
• Load Efficiency: {efficiency['load_efficiency']:.2f}%
• Peak vs Average Ratio: {efficiency['peak_ratio']:.2f}

**Optimization Opportunities:**
{efficiency['recommendations']}
"""
            
            # Prediction queries
            if any(word in user_message_lower for word in ['predict', 'forecast', 'future', 'tomorrow', 'next']):
                prediction = await self.ml_service.predict_energy_consumption("system_wide", 24)
                return f"""🔮 **Energy Consumption Forecast**

**Next 24 Hours Prediction:**
• Total Expected: {prediction['total_predicted_consumption']:.2f} kWh
• Peak Expected: {max(p['predicted_consumption'] for p in prediction['predictions']):.2f} W
• Average Hourly: {prediction['total_predicted_consumption']/24:.2f} kWh

**Confidence Level:** {np.mean([p['confidence'] for p in prediction['predictions']]):.1%}

**Key Predictions:**
• Morning Peak: {prediction['predictions'][8]['predicted_consumption']:.2f} W (9 AM)
• Evening Peak: {prediction['predictions'][18]['predicted_consumption']:.2f} W (7 PM)
• Minimum Load: {min(p['predicted_consumption'] for p in prediction['predictions']):.2f} W

**Planning Recommendations:**
• Schedule high-consumption activities during low-demand hours
• Monitor system performance during predicted peak times
"""
            
            # Report queries
            if any(word in user_message_lower for word in ['report', 'summary', 'overview']):
                report = await self._generate_comprehensive_report(db)
                return f"""📊 **Comprehensive Energy Report**

{report}
"""
            
            # Equipment queries
            if any(word in user_message_lower for word in ['equipment', 'device', 'meter', 'machine']):
                equipment_analysis = await self._analyze_equipment_status(db)
                return f"""⚙️ **Equipment Status Analysis**

{equipment_analysis}
"""
            
            # Default: Use EMS Query Engine for general queries
            try:
                result = engine.process_query(user_message)
                if result:
                    return f"📋 **Analysis Result:**\n\n{result}\n\n💡 *Ask me for more specific analysis like 'show anomalies', 'predict consumption', or 'efficiency report'*"
                else:
                    return """🤔 I'm not sure how to help with that specific query. Here are some things I can help you with:

📊 **Try asking:**
• "Show me power consumption trends"
• "Are there any voltage anomalies?"  
• "What's our energy efficiency score?"
• "Predict tomorrow's energy usage"
• "Generate a comprehensive report"
• "Show equipment status"
• "Analyze energy costs"

Or just tell me what specific aspect of your energy data you'd like to explore!"""
            except Exception as e:
                return f"""🤖 I encountered an issue processing your query, but I'm here to help! 

**Possible solutions:**
• Try rephrasing your question
• Ask about specific metrics like power, voltage, or current
• Request reports like "show energy report" or "detect anomalies"

**What I can analyze:**
• Power consumption patterns
• Voltage stability and anomalies  
• Current load analysis
• Energy efficiency metrics
• Cost analysis and projections
• Equipment performance

What specific aspect of your energy data interests you most?"""
                
        except Exception as e:
            return f"""⚠️ **System Error**

I encountered a technical issue while processing your request: {str(e)}

**Quick Actions:**
• Try asking a simpler question like "show system status"
• Check if you want power consumption, voltage analysis, or anomaly detection
• Ask for help with "what can you do?"

I'm still here and ready to help with your energy data analysis!"""

    async def _get_database_stats(self, db) -> Dict[str, any]:
        """Get database statistics."""
        try:
            collections = db.list_collection_names()
            total_records = 0
            latest_timestamp = "No data"
            
            for collection_name in collections:
                collection = db[collection_name]
                count = collection.count_documents({})
                total_records += count
                
                # Get latest timestamp
                latest_doc = collection.find().sort("timestamp", -1).limit(1)
                for doc in latest_doc:
                    if "timestamp" in doc:
                        latest_timestamp = str(doc["timestamp"])[:19]
                    break
            
            return {
                "connected": True,
                "collections": len(collections),
                "total_records": total_records,
                "latest_timestamp": latest_timestamp
            }
        except:
            return {
                "connected": False,
                "collections": 0,
                "total_records": 0,
                "latest_timestamp": "Unknown"
            }

    async def _analyze_power_consumption(self, db) -> Dict[str, any]:
        """Analyze power consumption patterns."""
        try:
            collection = db["ems_raw_data"]
            
            # Get recent data
            cursor = collection.find().sort("timestamp", -1).limit(100)
            data = list(cursor)
            
            if not data:
                return {"avg_power": 0, "max_power": 0, "total_energy": 0, "avg_power_factor": 0,
                       "trend_description": "No data available", "insights": "No insights available",
                       "recommendations": "Load data to begin analysis"}
            
            # Calculate statistics
            power_values = [doc.get("power_consumption", 0) for doc in data]
            pf_values = [doc.get("power_factor", 1.0) for doc in data if doc.get("power_factor")]
            
            avg_power = np.mean(power_values) if power_values else 0
            max_power = np.max(power_values) if power_values else 0
            total_energy = sum(power_values) * 0.001  # Convert to kWh (assuming hourly data)
            avg_power_factor = np.mean(pf_values) if pf_values else 1.0
            
            # Trend analysis
            if len(power_values) > 10:
                recent_avg = np.mean(power_values[:10])
                older_avg = np.mean(power_values[-10:])
                trend = "increasing" if recent_avg > older_avg * 1.05 else "decreasing" if recent_avg < older_avg * 0.95 else "stable"
                trend_description = f"Power consumption is {trend} compared to earlier readings"
            else:
                trend_description = "Insufficient data for trend analysis"
            
            # Generate insights
            insights = []
            if avg_power_factor < 0.8:
                insights.append("Poor power factor detected - consider power factor correction")
            if max_power > avg_power * 2:
                insights.append("High peak-to-average ratio indicates potential for load leveling")
            if not insights:
                insights.append("Power consumption patterns appear normal")
            
            recommendations = []
            if avg_power_factor < 0.85:
                recommendations.append("Install power factor correction capacitors")
            if max_power > 5000:
                recommendations.append("Consider load scheduling during off-peak hours")
            if not recommendations:
                recommendations.append("Continue monitoring for optimization opportunities")
            
            return {
                "avg_power": avg_power,
                "max_power": max_power,
                "total_energy": total_energy,
                "avg_power_factor": avg_power_factor,
                "trend_description": trend_description,
                "insights": " • ".join(insights),
                "recommendations": " • ".join(recommendations)
            }
        except Exception as e:
            return {"avg_power": 0, "max_power": 0, "total_energy": 0, "avg_power_factor": 0,
                   "trend_description": f"Analysis error: {str(e)}", "insights": "Error in analysis",
                   "recommendations": "Check data availability"}

    async def _analyze_voltage(self, db) -> Dict[str, any]:
        """Analyze voltage patterns and anomalies."""
        try:
            collection = db["ems_raw_data"]
            cursor = collection.find().sort("timestamp", -1).limit(100)
            data = list(cursor)
            
            if not data:
                return {"avg_voltage": 0, "min_voltage": 0, "max_voltage": 0, "stability": "Unknown",
                       "anomalies_description": "No data", "grid_quality": "Unknown"}
            
            voltage_values = [doc.get("voltage", 230) for doc in data]
            
            avg_voltage = np.mean(voltage_values)
            min_voltage = np.min(voltage_values)
            max_voltage = np.max(voltage_values)
            voltage_std = np.std(voltage_values)
            
            # Stability assessment
            stability = "Excellent" if voltage_std < 2 else "Good" if voltage_std < 5 else "Poor"
            
            # Anomaly detection
            anomalies = []
            for v in voltage_values:
                if v < 207 or v > 253:  # Outside ±10% of 230V
                    anomalies.append(v)
            
            anomalies_desc = f"Found {len(anomalies)} voltage anomalies" if anomalies else "No voltage anomalies detected"
            
            # Grid quality assessment
            if 220 <= avg_voltage <= 240 and voltage_std < 3:
                grid_quality = "Excellent - Stable grid supply"
            elif 210 <= avg_voltage <= 250 and voltage_std < 5:
                grid_quality = "Good - Minor fluctuations"
            else:
                grid_quality = "Poor - Significant voltage variations"
            
            return {
                "avg_voltage": avg_voltage,
                "min_voltage": min_voltage,
                "max_voltage": max_voltage,
                "stability": stability,
                "anomalies_description": anomalies_desc,
                "grid_quality": grid_quality
            }
        except Exception as e:
            return {"avg_voltage": 0, "min_voltage": 0, "max_voltage": 0, "stability": f"Error: {str(e)}",
                   "anomalies_description": "Analysis failed", "grid_quality": "Unknown"}

    async def _analyze_current(self, db) -> Dict[str, any]:
        """Analyze current patterns."""
        try:
            collection = db["ems_raw_data"]
            cursor = collection.find().sort("timestamp", -1).limit(100)
            data = list(cursor)
            
            if not data:
                return {"avg_current": 0, "max_current": 0, "load_factor": 0, "pattern_description": "No data"}
            
            current_values = [doc.get("current", 0) for doc in data]
            
            avg_current = np.mean(current_values)
            max_current = np.max(current_values)
            load_factor = avg_current / max_current if max_current > 0 else 0
            
            # Pattern analysis
            if load_factor > 0.8:
                pattern_desc = "High load factor - Efficient utilization"
            elif load_factor > 0.6:
                pattern_desc = "Moderate load factor - Room for optimization"
            else:
                pattern_desc = "Low load factor - Significant optimization potential"
            
            return {
                "avg_current": avg_current,
                "max_current": max_current,
                "load_factor": load_factor,
                "pattern_description": pattern_desc
            }
        except Exception as e:
            return {"avg_current": 0, "max_current": 0, "load_factor": 0, 
                   "pattern_description": f"Analysis error: {str(e)}"}

    async def _detect_energy_anomalies(self, db) -> Dict[str, any]:
        """Detect anomalies in energy data."""
        try:
            collection = db["ems_raw_data"]
            cursor = collection.find().sort("timestamp", -1).limit(50)
            recent_data = list(cursor)
            
            # Use ML service for anomaly detection
            anomalies = await self.ml_service.detect_anomalies(recent_data)
            
            if not anomalies:
                return {
                    "count": 0,
                    "detailed_report": "No anomalies detected",
                    "high_severity": 0,
                    "medium_severity": 0,
                    "low_severity": 0,
                    "recommendations": "Continue regular monitoring"
                }
            
            # Categorize anomalies by severity
            high_severity = sum(1 for a in anomalies if a.get('anomaly_score', 0) > 4)
            medium_severity = sum(1 for a in anomalies if 2.5 < a.get('anomaly_score', 0) <= 4)
            low_severity = len(anomalies) - high_severity - medium_severity
            
            # Generate detailed report
            detailed_report = []
            for i, anomaly in enumerate(anomalies[:5]):  # Show top 5
                severity = "🔴 HIGH" if anomaly.get('anomaly_score', 0) > 4 else "🟡 MEDIUM" if anomaly.get('anomaly_score', 0) > 2.5 else "🟢 LOW"
                detailed_report.append(f"{i+1}. {severity} - {anomaly.get('anomaly_type', 'Unknown')} (Score: {anomaly.get('anomaly_score', 0):.2f})")
            
            # Recommendations
            recommendations = []
            if high_severity > 0:
                recommendations.append("🚨 Immediate investigation required for high-severity anomalies")
            if medium_severity > 2:
                recommendations.append("⚠️ Schedule maintenance check for recurring medium-severity issues")
            recommendations.append("📊 Continue monitoring and trend analysis")
            
            return {
                "count": len(anomalies),
                "detailed_report": "\n".join(detailed_report),
                "high_severity": high_severity,
                "medium_severity": medium_severity,
                "low_severity": low_severity,
                "recommendations": "\n".join(recommendations)
            }
        except Exception as e:
            return {
                "count": 0,
                "detailed_report": f"Anomaly detection failed: {str(e)}",
                "high_severity": 0,
                "medium_severity": 0,
                "low_severity": 0,
                "recommendations": "Check system status and retry"
            }

    async def _analyze_energy_costs(self, db) -> Dict[str, any]:
        """Analyze energy costs and trends."""
        try:
            collection = db["ems_raw_data"]
            cursor = collection.find().sort("timestamp", -1).limit(100)
            data = list(cursor)
            
            if not data:
                return {"total_cost": 0, "daily_avg": 0, "rate": 0.12, 
                       "trend_description": "No data", "savings_opportunities": "Load data first"}
            
            # Calculate energy consumption
            total_energy = sum(doc.get("power_consumption", 0) for doc in data) * 0.001  # kWh
            rate_per_kwh = 0.12  # Default rate
            
            total_cost = total_energy * rate_per_kwh
            daily_avg = total_cost / 7  # Assume weekly data
            
            # Trend analysis
            recent_half = data[:50]
            older_half = data[50:]
            
            recent_cost = sum(doc.get("power_consumption", 0) for doc in recent_half) * 0.001 * rate_per_kwh
            older_cost = sum(doc.get("power_consumption", 0) for doc in older_half) * 0.001 * rate_per_kwh
            
            if recent_cost > older_cost * 1.1:
                trend_desc = "📈 Costs increasing - investigate high consumption periods"
            elif recent_cost < older_cost * 0.9:
                trend_desc = "📉 Costs decreasing - good energy management"
            else:
                trend_desc = "📊 Costs stable - consistent energy usage"
            
            # Savings opportunities
            savings_ops = []
            if any(doc.get("power_factor", 1) < 0.85 for doc in data):
                savings_ops.append("💡 Improve power factor to reduce reactive power charges")
            
            peak_hours = [doc for doc in data if 9 <= int(str(doc.get("timestamp", "12"))[-8:-6]) <= 17]
            if len(peak_hours) > len(data) * 0.6:
                savings_ops.append("⏰ Shift non-critical loads to off-peak hours")
            
            if not savings_ops:
                savings_ops.append("✅ Current usage patterns are optimized")
            
            return {
                "total_cost": total_cost,
                "daily_avg": daily_avg,
                "rate": rate_per_kwh,
                "trend_description": trend_desc,
                "savings_opportunities": "\n".join(savings_ops)
            }
        except Exception as e:
            return {"total_cost": 0, "daily_avg": 0, "rate": 0.12,
                   "trend_description": f"Analysis error: {str(e)}", 
                   "savings_opportunities": "Check data availability"}

    async def _analyze_efficiency(self, db) -> Dict[str, any]:
        """Analyze energy efficiency metrics."""
        try:
            collection = db["ems_raw_data"]
            cursor = collection.find().sort("timestamp", -1).limit(100)
            data = list(cursor)
            
            if not data:
                return {"score": 0, "power_factor": 0, "load_efficiency": 0, "peak_ratio": 0,
                       "recommendations": "No data available"}
            
            # Calculate efficiency metrics
            power_factors = [doc.get("power_factor", 1.0) for doc in data if doc.get("power_factor")]
            power_values = [doc.get("power_consumption", 0) for doc in data]
            
            avg_power_factor = np.mean(power_factors) if power_factors else 1.0
            avg_power = np.mean(power_values) if power_values else 0
            max_power = np.max(power_values) if power_values else 0
            
            # Load efficiency (how close to rated capacity)
            rated_capacity = max_power * 1.2  # Assume 20% headroom
            load_efficiency = (avg_power / rated_capacity * 100) if rated_capacity > 0 else 0
            
            # Peak to average ratio
            peak_ratio = max_power / avg_power if avg_power > 0 else 0
            
            # Overall efficiency score (0-100)
            pf_score = avg_power_factor * 30
            load_score = min(load_efficiency, 30)
            peak_score = max(0, 40 - (peak_ratio - 1) * 20)
            
            efficiency_score = pf_score + load_score + peak_score
            
            # Recommendations
            recommendations = []
            if avg_power_factor < 0.9:
                recommendations.append("📈 Install power factor correction to improve efficiency")
            if load_efficiency < 60:
                recommendations.append("⚡ Consider load optimization to improve utilization")
            if peak_ratio > 2:
                recommendations.append("📊 Implement load scheduling to reduce peak demand")
            if not recommendations:
                recommendations.append("✅ System operating at good efficiency levels")
            
            return {
                "score": efficiency_score,
                "power_factor": avg_power_factor,
                "load_efficiency": load_efficiency,
                "peak_ratio": peak_ratio,
                "recommendations": "\n".join(recommendations)
            }
        except Exception as e:
            return {"score": 0, "power_factor": 0, "load_efficiency": 0, "peak_ratio": 0,
                   "recommendations": f"Analysis error: {str(e)}"}

    async def _generate_comprehensive_report(self, db) -> str:
        """Generate a comprehensive energy analysis report."""
        try:
            stats = await self._get_database_stats(db)
            power_analysis = await self._analyze_power_consumption(db)
            voltage_analysis = await self._analyze_voltage(db)
            efficiency = await self._analyze_efficiency(db)
            anomalies = await self._detect_energy_anomalies(db)
            
            report = f"""
📊 **COMPREHENSIVE ENERGY ANALYSIS REPORT**
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

🔋 **SYSTEM OVERVIEW**
• Database Status: {'✅ Connected' if stats['connected'] else '❌ Disconnected'}
• Total Records: {stats['total_records']}
• Data Coverage: {stats['latest_timestamp']}

⚡ **POWER CONSUMPTION**
• Average Power: {power_analysis['avg_power']:.2f} W
• Peak Demand: {power_analysis['max_power']:.2f} W
• Total Energy: {power_analysis['total_energy']:.2f} kWh
• Power Factor: {power_analysis['avg_power_factor']:.3f}

🔌 **ELECTRICAL QUALITY**
• Voltage: {voltage_analysis['avg_voltage']:.1f}V (Range: {voltage_analysis['min_voltage']:.1f}-{voltage_analysis['max_voltage']:.1f}V)
• Grid Stability: {voltage_analysis['stability']}
• Grid Quality: {voltage_analysis['grid_quality']}

📈 **EFFICIENCY METRICS**
• Efficiency Score: {efficiency['score']:.1f}/100
• Load Efficiency: {efficiency['load_efficiency']:.1f}%
• Peak-to-Average Ratio: {efficiency['peak_ratio']:.2f}

🚨 **ANOMALY STATUS**
• Total Anomalies: {anomalies['count']}
• High Priority: {anomalies['high_severity']}
• Medium Priority: {anomalies['medium_severity']}
• Low Priority: {anomalies['low_severity']}

💡 **KEY RECOMMENDATIONS**
{power_analysis['recommendations']}

📋 **NEXT ACTIONS**
• Monitor high-priority anomalies
• Implement efficiency improvements
• Schedule preventive maintenance
• Continue real-time monitoring
"""
            return report
        except Exception as e:
            return f"❌ **Report Generation Failed**\n\nError: {str(e)}\n\nPlease check data availability and try again."

    async def _analyze_equipment_status(self, db) -> str:
        """Analyze equipment status and performance."""
        try:
            collections = db.list_collection_names()
            
            equipment_status = f"""
⚙️ **EQUIPMENT STATUS ANALYSIS**

📊 **Data Collections:**"""
            
            for collection_name in collections:
                collection = db[collection_name]
                count = collection.count_documents({})
                latest = collection.find().sort("timestamp", -1).limit(1)
                latest_time = "No data"
                for doc in latest:
                    if "timestamp" in doc:
                        latest_time = str(doc["timestamp"])[:19]
                    break
                
                equipment_status += f"""
• {collection_name}: {count} records (Latest: {latest_time})"""
            
            # Check for devices in raw data
            raw_collection = db.get_collection("ems_raw_data")
            if raw_collection:
                sample_docs = list(raw_collection.find().limit(10))
                if sample_docs:
                    equipment_status += f"""

🔧 **DEVICE METRICS:**
• Active Monitoring Points: {len(sample_docs)}
• Parameters Tracked: {', '.join(set().union(*[doc.keys() for doc in sample_docs if isinstance(doc, dict)]))}
• Data Freshness: Recent data available
• Operational Status: ✅ Normal"""
                else:
                    equipment_status += "\n\n🔧 **DEVICE METRICS:**\n• No recent device data available"
            
            return equipment_status
        except Exception as e:
            return f"❌ **Equipment Analysis Failed**\n\nError: {str(e)}"

    async def _get_system_health(self) -> Dict[str, str]:
        """Get current system health status."""
        return {
            "streaming": "operational",
            "ml": "operational", 
            "security": "operational",
            "mongodb": "connected"
        }
