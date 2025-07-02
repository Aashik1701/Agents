#!/usr/bin/env python3
"""
Notification Service for EMS
Intelligent alerting and notification system with multiple delivery channels
"""

import asyncio
import json
import logging
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import redis.asyncio as redis
from pymongo import MongoClient
import paho.mqtt.client as mqtt
import websockets
import json

from common.base_service import BaseService
from common.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    WEBSOCKET = "websocket"
    MQTT = "mqtt"
    PUSH = "push"


class NotificationStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class NotificationRule:
    """Notification rule configuration"""
    rule_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    channels: List[str]
    recipients: List[str]
    priority: str
    enabled: bool = True
    rate_limit: Optional[Dict[str, Any]] = None
    template: Optional[str] = None


@dataclass
class Notification:
    """Notification object"""
    notification_id: str
    rule_id: Optional[str]
    title: str
    message: str
    priority: str
    channels: List[str]
    recipients: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    status: str = NotificationStatus.PENDING.value
    delivery_attempts: int = 0
    last_attempt: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None


class EmailNotificationChannel:
    """Email notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.sender_email = config.get('sender_email', self.username)
        self.sender_name = config.get('sender_name', 'EMS Alert System')
    
    async def send(self, notification: Notification) -> bool:
        """Send email notification"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['Subject'] = f"[{notification.priority.upper()}] {notification.title}"
            
            # HTML email template
            html_content = self._create_html_email(notification)
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send to all recipients
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                
                for recipient in notification.recipients:
                    msg['To'] = recipient
                    server.sendmail(self.sender_email, recipient, msg.as_string())
                    del msg['To']
            
            logger.info(f"Email sent successfully to {len(notification.recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False
    
    def _create_html_email(self, notification: Notification) -> str:
        """Create HTML email content"""
        priority_colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        
        color = priority_colors.get(notification.priority, '#6c757d')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>EMS Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">🚨 EMS Alert</h1>
                    <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">Priority: {notification.priority.upper()}</p>
                </div>
                
                <div style="padding: 30px;">
                    <h2 style="color: #333; margin-top: 0;">{notification.title}</h2>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0; line-height: 1.6; color: #555;">{notification.message}</p>
                    </div>
                    
                    <div style="margin: 20px 0;">
                        <h3 style="color: #333; margin-bottom: 10px;">Alert Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">Time:</td>
                                <td style="padding: 8px; border-bottom: 1px solid #eee; color: #333;">{notification.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">Alert ID:</td>
                                <td style="padding: 8px; border-bottom: 1px solid #eee; color: #333;">{notification.notification_id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">System:</td>
                                <td style="padding: 8px; border-bottom: 1px solid #eee; color: #333;">Energy Management System</td>
                            </tr>
                        </table>
                    </div>
                    
                    {"".join([f'<p style="margin: 5px 0; color: #666;"><strong>{k}:</strong> {v}</p>' for k, v in notification.metadata.items() if k not in ['raw_data']])}
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center;">
                        <p style="color: #666; font-size: 12px; margin: 0;">
                            This is an automated alert from the EMS monitoring system.
                            <br>
                            Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html


class WebhookNotificationChannel:
    """Webhook notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        self.webhook_urls = config.get('webhook_urls', [])
        self.timeout = config.get('timeout', 10)
        self.headers = config.get('headers', {'Content-Type': 'application/json'})
    
    async def send(self, notification: Notification) -> bool:
        """Send webhook notification"""
        try:
            payload = {
                'notification_id': notification.notification_id,
                'title': notification.title,
                'message': notification.message,
                'priority': notification.priority,
                'timestamp': notification.created_at.isoformat(),
                'metadata': notification.metadata
            }
            
            success_count = 0
            
            for url in self.webhook_urls:
                try:
                    response = requests.post(
                        url,
                        json=payload,
                        headers=self.headers,
                        timeout=self.timeout
                    )
                    
                    if response.status_code < 400:
                        success_count += 1
                        logger.info(f"Webhook sent successfully to {url}")
                    else:
                        logger.warning(f"Webhook failed for {url}: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"Webhook error for {url}: {e}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Webhook sending failed: {e}")
            return False


class SlackNotificationChannel:
    """Slack notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        self.webhook_url = config.get('webhook_url', '')
        self.channel = config.get('channel', '#alerts')
        self.username = config.get('username', 'EMS Alert Bot')
        self.icon_emoji = config.get('icon_emoji', ':warning:')
    
    async def send(self, notification: Notification) -> bool:
        """Send Slack notification"""
        try:
            if not self.webhook_url:
                logger.warning("Slack webhook URL not configured")
                return False
            
            # Priority emoji mapping
            priority_emoji = {
                'low': ':information_source:',
                'medium': ':warning:',
                'high': ':exclamation:',
                'critical': ':rotating_light:'
            }
            
            emoji = priority_emoji.get(notification.priority, ':warning:')
            
            # Create Slack message
            payload = {
                'channel': self.channel,
                'username': self.username,
                'icon_emoji': self.icon_emoji,
                'attachments': [
                    {
                        'color': self._get_priority_color(notification.priority),
                        'title': f"{emoji} {notification.title}",
                        'text': notification.message,
                        'fields': [
                            {
                                'title': 'Priority',
                                'value': notification.priority.upper(),
                                'short': True
                            },
                            {
                                'title': 'Time',
                                'value': notification.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
                                'short': True
                            },
                            {
                                'title': 'Alert ID',
                                'value': notification.notification_id,
                                'short': True
                            }
                        ],
                        'footer': 'EMS Alert System',
                        'ts': int(notification.created_at.timestamp())
                    }
                ]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Slack notification sent successfully")
                return True
            else:
                logger.error(f"Slack notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return False
    
    def _get_priority_color(self, priority: str) -> str:
        """Get color for priority"""
        colors = {
            'low': 'good',
            'medium': 'warning',
            'high': 'danger',
            'critical': '#ff0000'
        }
        return colors.get(priority, '#cccccc')


class WebSocketNotificationChannel:
    """WebSocket notification channel for real-time alerts"""
    
    def __init__(self, config: Dict[str, Any]):
        self.connections = set()
        self.redis_client = None
    
    async def initialize(self, redis_client):
        """Initialize WebSocket channel"""
        self.redis_client = redis_client
    
    async def add_connection(self, websocket):
        """Add WebSocket connection"""
        self.connections.add(websocket)
        logger.info(f"WebSocket connection added. Total: {len(self.connections)}")
    
    async def remove_connection(self, websocket):
        """Remove WebSocket connection"""
        self.connections.discard(websocket)
        logger.info(f"WebSocket connection removed. Total: {len(self.connections)}")
    
    async def send(self, notification: Notification) -> bool:
        """Send WebSocket notification to all connected clients"""
        if not self.connections:
            return True  # No connections, but not an error
        
        try:
            message = {
                'type': 'notification',
                'data': {
                    'id': notification.notification_id,
                    'title': notification.title,
                    'message': notification.message,
                    'priority': notification.priority,
                    'timestamp': notification.created_at.isoformat(),
                    'metadata': notification.metadata
                }
            }
            
            # Send to all connected clients
            disconnected = set()
            
            for websocket in self.connections.copy():
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket client: {e}")
                    disconnected.add(websocket)
            
            # Remove disconnected clients
            for websocket in disconnected:
                self.connections.discard(websocket)
            
            logger.info(f"WebSocket notification sent to {len(self.connections)} clients")
            return True
            
        except Exception as e:
            logger.error(f"WebSocket notification failed: {e}")
            return False


class NotificationService(BaseService):
    """Notification service for intelligent alerting"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("notification", config)
        self.collections = {}
        self.channels = {}
        self.rules = {}
        self.rate_limiter = {}
        self.app = self._create_fastapi_app()
        
        # Initialize notification channels
        self._initialize_channels()
    
    async def initialize(self):
        """Initialize notification service"""
        await super().initialize()
        
        # Initialize database collections
        if self.db_client:
            db = self.db_client[self.config['mongodb']['database']]
            self.collections = {
                'notifications': db.ems_notifications,
                'notification_rules': db.ems_notification_rules,
                'notification_history': db.ems_notification_history,
                'notification_templates': db.ems_notification_templates
            }
        
        # Initialize WebSocket channel with Redis
        if hasattr(self, 'redis_client') and self.redis_client:
            await self.channels['websocket'].initialize(self.redis_client)
        
        # Load notification rules
        await self._load_notification_rules()
        
        # Start background tasks
        asyncio.create_task(self._process_notification_queue())
        asyncio.create_task(self._cleanup_old_notifications())
        
        logger.info("Notification Service initialized")
    
    def _initialize_channels(self):
        """Initialize notification channels"""
        notification_config = self.config.get('notification', {})
        
        # Email channel
        email_config = notification_config.get('email', {})
        if email_config.get('enabled', False):
            self.channels['email'] = EmailNotificationChannel(email_config)
        
        # Webhook channel
        webhook_config = notification_config.get('webhook', {})
        if webhook_config.get('enabled', False):
            self.channels['webhook'] = WebhookNotificationChannel(webhook_config)
        
        # Slack channel
        slack_config = notification_config.get('slack', {})
        if slack_config.get('enabled', False):
            self.channels['slack'] = SlackNotificationChannel(slack_config)
        
        # WebSocket channel (always enabled)
        self.channels['websocket'] = WebSocketNotificationChannel({})
        
        logger.info(f"Initialized {len(self.channels)} notification channels")
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title="EMS Notification Service",
            description="Intelligent alerting and notification system",
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
            """Health check endpoint"""
            return self.get_health_status()
        
        @app.post("/send")
        async def send_notification(request: Dict[str, Any]):
            """Send a notification"""
            try:
                notification_data = {
                    'title': request.get('title', ''),
                    'message': request.get('message', ''),
                    'priority': request.get('priority', 'medium'),
                    'channels': request.get('channels', ['websocket']),
                    'recipients': request.get('recipients', []),
                    'metadata': request.get('metadata', {}),
                    'rule_id': request.get('rule_id')
                }
                
                notification_id = await self.send_notification(notification_data)
                return {"success": True, "notification_id": notification_id}
                
            except Exception as e:
                logger.error(f"Send notification error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @app.get("/notifications")
        async def get_notifications(
            status: str = None,
            priority: str = None,
            limit: int = 50,
            offset: int = 0
        ):
            """Get notifications with filtering"""
            try:
                notifications = await self.get_notifications_list(status, priority, limit, offset)
                return {"notifications": notifications}
                
            except Exception as e:
                logger.error(f"Get notifications error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.put("/notifications/{notification_id}/read")
        async def mark_notification_read(notification_id: str):
            """Mark notification as read"""
            try:
                success = await self.mark_notification_read(notification_id)
                return {"success": success}
                
            except Exception as e:
                logger.error(f"Mark read error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/rules")
        async def get_notification_rules():
            """Get notification rules"""
            try:
                rules = await self.get_notification_rules()
                return {"rules": rules}
                
            except Exception as e:
                logger.error(f"Get rules error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/rules")
        async def create_notification_rule(request: Dict[str, Any]):
            """Create notification rule"""
            try:
                rule_id = await self.create_notification_rule(request)
                return {"success": True, "rule_id": rule_id}
                
            except Exception as e:
                logger.error(f"Create rule error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @app.websocket("/ws")
        async def websocket_endpoint(websocket):
            """WebSocket endpoint for real-time notifications"""
            await websocket.accept()
            await self.channels['websocket'].add_connection(websocket)
            
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
            except Exception as e:
                logger.info(f"WebSocket connection closed: {e}")
            finally:
                await self.channels['websocket'].remove_connection(websocket)
    
    async def send_notification(self, notification_data: Dict[str, Any]) -> str:
        """Send a notification through specified channels"""
        
        # Create notification object
        notification = Notification(
            notification_id=f"notif_{int(datetime.now().timestamp())}_{hash(str(notification_data)) % 10000}",
            rule_id=notification_data.get('rule_id'),
            title=notification_data['title'],
            message=notification_data['message'],
            priority=notification_data.get('priority', 'medium'),
            channels=notification_data.get('channels', ['websocket']),
            recipients=notification_data.get('recipients', []),
            metadata=notification_data.get('metadata', {}),
            created_at=datetime.now()
        )
        
        # Check rate limiting
        if not await self._check_rate_limit(notification):
            logger.warning(f"Rate limit exceeded for notification: {notification.notification_id}")
            return notification.notification_id
        
        # Store notification in database
        await self._store_notification(notification)
        
        # Add to processing queue
        if self.redis_client:
            await self.redis_client.lpush('notification_queue', json.dumps(asdict(notification), default=str))
        else:
            # Process immediately if no Redis
            await self._process_notification(notification)
        
        return notification.notification_id
    
    async def _process_notification_queue(self):
        """Process notification queue in background"""
        while True:
            try:
                if not self.redis_client:
                    await asyncio.sleep(5)
                    continue
                
                # Get notification from queue
                queued_item = await self.redis_client.brpop('notification_queue', timeout=5)
                
                if queued_item:
                    notification_data = json.loads(queued_item[1])
                    
                    # Convert back to Notification object
                    notification_data['created_at'] = datetime.fromisoformat(notification_data['created_at'])
                    if notification_data.get('scheduled_at'):
                        notification_data['scheduled_at'] = datetime.fromisoformat(notification_data['scheduled_at'])
                    if notification_data.get('last_attempt'):
                        notification_data['last_attempt'] = datetime.fromisoformat(notification_data['last_attempt'])
                    if notification_data.get('delivered_at'):
                        notification_data['delivered_at'] = datetime.fromisoformat(notification_data['delivered_at'])
                    
                    notification = Notification(**notification_data)
                    
                    # Process notification
                    await self._process_notification(notification)
                
            except Exception as e:
                logger.error(f"Error processing notification queue: {e}")
                await asyncio.sleep(5)
    
    async def _process_notification(self, notification: Notification):
        """Process a single notification"""
        try:
            notification.delivery_attempts += 1
            notification.last_attempt = datetime.now()
            
            success_channels = []
            failed_channels = []
            
            # Send through each channel
            for channel_name in notification.channels:
                if channel_name in self.channels:
                    try:
                        success = await self.channels[channel_name].send(notification)
                        if success:
                            success_channels.append(channel_name)
                        else:
                            failed_channels.append(channel_name)
                    except Exception as e:
                        logger.error(f"Channel {channel_name} failed: {e}")
                        failed_channels.append(channel_name)
                else:
                    logger.warning(f"Unknown notification channel: {channel_name}")
                    failed_channels.append(channel_name)
            
            # Update notification status
            if success_channels:
                notification.status = NotificationStatus.DELIVERED.value
                notification.delivered_at = datetime.now()
                logger.info(f"Notification {notification.notification_id} delivered via {success_channels}")
            else:
                notification.status = NotificationStatus.FAILED.value
                notification.error_message = f"Failed channels: {failed_channels}"
                logger.error(f"Notification {notification.notification_id} failed on all channels")
            
            # Update in database
            await self._update_notification_status(notification)
            
            # Retry logic for failed notifications
            if failed_channels and notification.delivery_attempts < 3:
                retry_delay = min(300, 60 * notification.delivery_attempts)  # Max 5 minutes
                
                if self.redis_client:
                    # Schedule retry
                    retry_notification = notification
                    retry_notification.channels = failed_channels
                    retry_notification.status = NotificationStatus.RETRY.value
                    
                    await asyncio.sleep(retry_delay)
                    await self.redis_client.lpush('notification_queue', json.dumps(asdict(retry_notification), default=str))
        
        except Exception as e:
            logger.error(f"Error processing notification {notification.notification_id}: {e}")
    
    async def _check_rate_limit(self, notification: Notification) -> bool:
        """Check if notification is within rate limits"""
        try:
            if not notification.rule_id or not self.redis_client:
                return True
            
            rule = self.rules.get(notification.rule_id)
            if not rule or not rule.rate_limit:
                return True
            
            rate_limit = rule.rate_limit
            limit_key = f"rate_limit:{notification.rule_id}"
            
            # Get current count
            current_count = await self.redis_client.get(limit_key)
            current_count = int(current_count) if current_count else 0
            
            # Check limit
            max_count = rate_limit.get('max_count', 10)
            time_window = rate_limit.get('time_window_seconds', 3600)
            
            if current_count >= max_count:
                return False
            
            # Increment counter
            await self.redis_client.incr(limit_key)
            await self.redis_client.expire(limit_key, time_window)
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow on error
    
    async def _store_notification(self, notification: Notification):
        """Store notification in database"""
        try:
            notification_doc = asdict(notification)
            await asyncio.to_thread(
                self.collections['notifications'].insert_one,
                notification_doc
            )
        except Exception as e:
            logger.error(f"Failed to store notification: {e}")
    
    async def _update_notification_status(self, notification: Notification):
        """Update notification status in database"""
        try:
            await asyncio.to_thread(
                self.collections['notifications'].update_one,
                {'notification_id': notification.notification_id},
                {
                    '$set': {
                        'status': notification.status,
                        'delivery_attempts': notification.delivery_attempts,
                        'last_attempt': notification.last_attempt,
                        'delivered_at': notification.delivered_at,
                        'error_message': notification.error_message
                    }
                }
            )
        except Exception as e:
            logger.error(f"Failed to update notification status: {e}")
    
    async def _load_notification_rules(self):
        """Load notification rules from database"""
        try:
            rules_cursor = self.collections['notification_rules'].find({'enabled': True})
            
            for rule_doc in rules_cursor:
                rule = NotificationRule(
                    rule_id=rule_doc['rule_id'],
                    name=rule_doc['name'],
                    description=rule_doc['description'],
                    conditions=rule_doc['conditions'],
                    channels=rule_doc['channels'],
                    recipients=rule_doc['recipients'],
                    priority=rule_doc['priority'],
                    enabled=rule_doc['enabled'],
                    rate_limit=rule_doc.get('rate_limit'),
                    template=rule_doc.get('template')
                )
                
                self.rules[rule.rule_id] = rule
            
            logger.info(f"Loaded {len(self.rules)} notification rules")
            
        except Exception as e:
            logger.error(f"Failed to load notification rules: {e}")
    
    async def get_notifications_list(
        self, 
        status: str = None, 
        priority: str = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get list of notifications with filtering"""
        try:
            query_filter = {}
            
            if status:
                query_filter['status'] = status
            if priority:
                query_filter['priority'] = priority
            
            notifications_cursor = self.collections['notifications'].find(query_filter)\
                .sort('created_at', -1)\
                .skip(offset)\
                .limit(limit)
            
            notifications = []
            for doc in notifications_cursor:
                doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
                notifications.append(doc)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return []
    
    async def mark_notification_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        try:
            result = await asyncio.to_thread(
                self.collections['notifications'].update_one,
                {'notification_id': notification_id},
                {'$set': {'read_at': datetime.now()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    async def get_notification_rules(self) -> List[Dict[str, Any]]:
        """Get notification rules"""
        try:
            rules_cursor = self.collections['notification_rules'].find()
            
            rules = []
            for doc in rules_cursor:
                doc['_id'] = str(doc['_id'])
                rules.append(doc)
            
            return rules
            
        except Exception as e:
            logger.error(f"Error getting notification rules: {e}")
            return []
    
    async def create_notification_rule(self, rule_data: Dict[str, Any]) -> str:
        """Create a new notification rule"""
        try:
            rule_id = f"rule_{int(datetime.now().timestamp())}_{hash(str(rule_data)) % 10000}"
            
            rule_doc = {
                'rule_id': rule_id,
                'name': rule_data['name'],
                'description': rule_data.get('description', ''),
                'conditions': rule_data['conditions'],
                'channels': rule_data['channels'],
                'recipients': rule_data['recipients'],
                'priority': rule_data.get('priority', 'medium'),
                'enabled': rule_data.get('enabled', True),
                'rate_limit': rule_data.get('rate_limit'),
                'template': rule_data.get('template'),
                'created_at': datetime.now()
            }
            
            await asyncio.to_thread(
                self.collections['notification_rules'].insert_one,
                rule_doc
            )
            
            # Add to in-memory rules
            rule = NotificationRule(**{k: v for k, v in rule_doc.items() if k != '_id' and k != 'created_at'})
            self.rules[rule_id] = rule
            
            logger.info(f"Created notification rule: {rule_id}")
            return rule_id
            
        except Exception as e:
            logger.error(f"Error creating notification rule: {e}")
            raise
    
    async def _cleanup_old_notifications(self):
        """Clean up old notifications periodically"""
        while True:
            try:
                # Clean up notifications older than 30 days
                cutoff_date = datetime.now() - timedelta(days=30)
                
                result = await asyncio.to_thread(
                    self.collections['notifications'].delete_many,
                    {'created_at': {'$lt': cutoff_date}}
                )
                
                if result.deleted_count > 0:
                    logger.info(f"Cleaned up {result.deleted_count} old notifications")
                
                # Sleep for 24 hours
                await asyncio.sleep(24 * 3600)
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour on error
    
    async def health_check(self):
        """Service-specific health check"""
        # Test notification channels
        test_channels = 0
        working_channels = 0
        
        for channel_name, channel in self.channels.items():
            test_channels += 1
            try:
                # Simple test - just check if channel exists and is configured
                if hasattr(channel, 'send'):
                    working_channels += 1
            except Exception as e:
                logger.warning(f"Channel {channel_name} health check failed: {e}")
        
        if working_channels == 0:
            raise Exception("No notification channels available")
        
        logger.info(f"Health check: {working_channels}/{test_channels} channels available")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service-specific requests"""
        request_type = request_data.get('type')
        
        if request_type == 'send_notification':
            notification_id = await self.send_notification(request_data['notification_data'])
            return {'notification_id': notification_id}
        elif request_type == 'get_notifications':
            notifications = await self.get_notifications_list(
                request_data.get('status'),
                request_data.get('priority'),
                request_data.get('limit', 50),
                request_data.get('offset', 0)
            )
            return {'notifications': notifications}
        else:
            raise ValueError(f"Unknown request type: {request_type}")


def create_notification_service():
    """Factory function to create notification service"""
    config_manager = ConfigManager()
    config = config_manager.get_config()
    return NotificationService(config)


async def run_service():
    """Run the notification service"""
    service = create_notification_service()
    await service.initialize()
    await service.run()


if __name__ == "__main__":
    asyncio.run(run_service())
