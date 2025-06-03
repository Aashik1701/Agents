from typing import Dict, List, Any, Optional
from fastapi import WebSocket
import json
import structlog

logger = structlog.get_logger()


class WebSocketManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> client_id
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info("WebSocket connected", client_id=client_id)
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove user session mapping
        for user_id, session_client_id in list(self.user_sessions.items()):
            if session_client_id == client_id:
                del self.user_sessions[user_id]
                break
        
        logger.info("WebSocket disconnected", client_id=client_id)
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error("Failed to send message", client_id=client_id, error=str(e))
                self.disconnect(client_id)
    
    async def send_to_user(self, message: Dict[str, Any], user_id: str):
        """Send a message to a user (if they have an active connection)"""
        if user_id in self.user_sessions:
            client_id = self.user_sessions[user_id]
            await self.send_personal_message(message, client_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error("Failed to broadcast to client", client_id=client_id, error=str(e))
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def send_anomaly_alert(self, anomaly_data: Dict[str, Any]):
        """Send anomaly alert to all admin users"""
        alert_message = {
            "type": "anomaly_alert",
            "data": anomaly_data,
            "timestamp": anomaly_data.get("detected_at"),
            "severity": anomaly_data.get("severity", "medium")
        }
        
        # For now, broadcast to all users
        # In production, filter by user roles
        await self.broadcast(alert_message)
    
    async def send_recommendation(self, recommendation: Dict[str, Any], user_id: Optional[str] = None):
        """Send optimization recommendation"""
        message = {
            "type": "recommendation",
            "data": recommendation,
            "timestamp": recommendation.get("created_at")
        }
        
        if user_id:
            await self.send_to_user(message, user_id)
        else:
            await self.broadcast(message)
    
    def get_active_connections_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_connected_users(self) -> List[str]:
        """Get list of connected user IDs"""
        return list(self.user_sessions.keys())


# Global instance
websocket_manager = WebSocketManager()
