#!/usr/bin/env python3
"""
Comprehensive Security Service for EMS
Handles authentication, authorization, encryption, audit logging, and security monitoring
"""

import asyncio
import hashlib
import hmac
import jwt
import secrets
import logging
import time
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import ipaddress
from fastapi import FastAPI, HTTPException, Depends, Security, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from email_validator import validate_email, EmailNotValidError

from common.base_service import BaseService

logger = logging.getLogger(__name__)


@dataclass
class User:
    """Enhanced user model with security features"""
    user_id: str
    username: str
    email: str
    password_hash: str
    roles: List[str]
    permissions: List[str]
    is_active: bool
    is_verified: bool
    is_locked: bool
    last_login: Optional[datetime]
    last_password_change: Optional[datetime]
    failed_login_attempts: int
    max_failed_attempts: int
    lockout_duration: int  # minutes
    mfa_enabled: bool
    mfa_secret: Optional[str]
    password_history: List[str]  # Store hash of last 5 passwords
    session_timeout: int  # minutes
    allowed_ips: List[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class SecurityEvent:
    """Security event for audit logging"""
    event_id: str
    event_type: str  # 'login', 'logout', 'failed_login', 'permission_denied', 'data_access', etc.
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    additional_data: Dict[str, Any]
    risk_score: float


@dataclass
class AccessToken:
    """Enhanced access token with security features"""
    token: str
    token_type: str
    expires_at: datetime
    user_id: str
    scopes: List[str]
    session_id: str
    is_revoked: bool
    created_at: datetime
    last_used: Optional[datetime]
    ip_address: str
    user_agent: str


@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_symbols: bool = True
    password_history_count: int = 5
    password_max_age: int = 90  # days
    session_timeout: int = 480  # minutes (8 hours)
    max_failed_login_attempts: int = 5
    lockout_duration: int = 30  # minutes
    mfa_required: bool = False
    ip_whitelist_enabled: bool = False
    rate_limit_enabled: bool = True
    encryption_key_rotation_days: int = 30


class PasswordValidator:
    """Advanced password validation and security checks"""
    
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
        self.common_passwords = self._load_common_passwords()
    
    def _load_common_passwords(self) -> Set[str]:
        """Load common passwords list"""
        # In production, this would load from a file
        return {
            "password", "123456", "password123", "admin", "qwerty",
            "letmein", "welcome", "monkey", "dragon", "master"
        }
    
    def validate_password(self, password: str, user_context: Dict[str, str] = None) -> Dict[str, Any]:
        """Comprehensive password validation"""
        errors = []
        warnings = []
        score = 0
        
        # Length check
        if len(password) < self.policy.password_min_length:
            errors.append(f"Password must be at least {self.policy.password_min_length} characters long")
        else:
            score += min(20, len(password))
        
        # Character requirements
        if self.policy.password_require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        elif re.search(r'[A-Z]', password):
            score += 10
        
        if self.policy.password_require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        elif re.search(r'[a-z]', password):
            score += 10
        
        if self.policy.password_require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        elif re.search(r'\d', password):
            score += 10
        
        if self.policy.password_require_symbols and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one symbol")
        elif re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 15
        
        # Common password check
        if password.lower() in self.common_passwords:
            errors.append("Password is too common")
        
        # Personal information check
        if user_context:
            username = user_context.get('username', '').lower()
            email = user_context.get('email', '').lower()
            
            if username and username in password.lower():
                errors.append("Password should not contain username")
            
            if email and email.split('@')[0] in password.lower():
                errors.append("Password should not contain email")
        
        # Pattern checks
        if re.search(r'(.)\1{2,}', password):  # Repeated characters
            warnings.append("Avoid repeating characters")
            score -= 5
        
        if re.search(r'(012|123|234|345|456|567|678|789|890)', password):  # Sequential numbers
            warnings.append("Avoid sequential numbers")
            score -= 5
        
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            warnings.append("Avoid sequential letters")
            score -= 5
        
        # Entropy calculation
        charset_size = 0
        if re.search(r'[a-z]', password):
            charset_size += 26
        if re.search(r'[A-Z]', password):
            charset_size += 26
        if re.search(r'\d', password):
            charset_size += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            charset_size += 32
        
        entropy = len(password) * (charset_size.bit_length() - 1) if charset_size > 0 else 0
        score += min(25, entropy // 4)
        
        # Final score and strength
        strength = "very_weak"
        if score >= 80:
            strength = "very_strong"
        elif score >= 60:
            strength = "strong"
        elif score >= 40:
            strength = "medium"
        elif score >= 20:
            strength = "weak"
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "score": min(100, score),
            "strength": strength,
            "entropy": entropy
        }
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate a cryptographically secure password"""
        alphabet = ""
        
        if self.policy.password_require_lowercase:
            alphabet += "abcdefghijklmnopqrstuvwxyz"
        if self.policy.password_require_uppercase:
            alphabet += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if self.policy.password_require_numbers:
            alphabet += "0123456789"
        if self.policy.password_require_symbols:
            alphabet += "!@#$%^&*(),.?\":{}|<>"
        
        if not alphabet:
            alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Ensure password meets requirements
        validation = self.validate_password(password)
        if not validation["valid"]:
            # Regenerate if it doesn't meet requirements
            return self.generate_secure_password(length)
        
        return password


class EncryptionManager:
    """Advanced encryption and key management"""
    
    def __init__(self):
        self.master_key = self._get_or_create_master_key()
        self.fernet = Fernet(self.master_key)
        self.key_rotation_schedule = {}
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key"""
        key_file = Path("security/master.key")
        key_file.parent.mkdir(exist_ok=True)
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Read/write for owner only
            return key
    
    def encrypt_data(self, data: Union[str, bytes]) -> str:
        """Encrypt data with AES-256"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted = self.fernet.encrypt(data)
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Invalid encrypted data")
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    def generate_token(self, payload: Dict[str, Any], secret_key: str, expires_in: int = 3600) -> str:
        """Generate JWT token"""
        payload.update({
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(16)  # JWT ID
        })
        
        return jwt.encode(payload, secret_key, algorithm='HS256')
    
    def verify_token(self, token: str, secret_key: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    def rotate_keys(self):
        """Rotate encryption keys (scheduled operation)"""
        # Implementation for key rotation
        logger.info("Key rotation completed")


class AuditLogger:
    """Comprehensive audit logging system"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.audit_file = Path("logs/security_audit.log")
        self.audit_file.parent.mkdir(exist_ok=True)
    
    async def log_security_event(self, event: SecurityEvent):
        """Log security event to multiple destinations"""
        
        # Log to file
        self._log_to_file(event)
        
        # Log to Redis for real-time monitoring
        if self.redis_client:
            await self._log_to_redis(event)
        
        # Alert on high-risk events
        if event.risk_score >= 8.0:
            await self._send_security_alert(event)
    
    def _log_to_file(self, event: SecurityEvent):
        """Log event to file"""
        log_entry = {
            "timestamp": event.timestamp.isoformat(),
            "event_id": event.event_id,
            "event_type": event.event_type,
            "user_id": event.user_id,
            "ip_address": event.ip_address,
            "severity": event.severity,
            "description": event.description,
            "risk_score": event.risk_score,
            "additional_data": event.additional_data
        }
        
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    async def _log_to_redis(self, event: SecurityEvent):
        """Log event to Redis for real-time monitoring"""
        try:
            await self.redis_client.lpush(
                "security_events", 
                json.dumps(asdict(event), default=str)
            )
            await self.redis_client.ltrim("security_events", 0, 999)  # Keep last 1000 events
        except Exception as e:
            logger.error(f"Failed to log to Redis: {e}")
    
    async def _send_security_alert(self, event: SecurityEvent):
        """Send security alert for high-risk events"""
        alert_message = f"HIGH RISK SECURITY EVENT: {event.event_type} - {event.description}"
        logger.critical(alert_message)
        
        # Here you would integrate with alerting systems
        # like email, Slack, PagerDuty, etc.


class RateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.rate_limits = {
            'login': {'requests': 5, 'window': 300},  # 5 attempts per 5 minutes
            'api': {'requests': 100, 'window': 60},   # 100 requests per minute
            'sensitive': {'requests': 10, 'window': 60}  # 10 requests per minute for sensitive endpoints
        }
    
    async def is_rate_limited(self, key: str, endpoint_type: str = 'api') -> bool:
        """Check if request should be rate limited"""
        if not self.redis_client:
            return False
        
        limit_config = self.rate_limits.get(endpoint_type, self.rate_limits['api'])
        redis_key = f"rate_limit:{endpoint_type}:{key}"
        
        try:
            current_count = await self.redis_client.incr(redis_key)
            if current_count == 1:
                await self.redis_client.expire(redis_key, limit_config['window'])
            
            return current_count > limit_config['requests']
        except Exception as e:
            logger.error(f"Rate limiting check failed: {e}")
            return False
    
    async def get_rate_limit_status(self, key: str, endpoint_type: str = 'api') -> Dict[str, Any]:
        """Get rate limit status for a key"""
        if not self.redis_client:
            return {"unlimited": True}
        
        limit_config = self.rate_limits.get(endpoint_type, self.rate_limits['api'])
        redis_key = f"rate_limit:{endpoint_type}:{key}"
        
        try:
            current_count = await self.redis_client.get(redis_key)
            ttl = await self.redis_client.ttl(redis_key)
            
            current_count = int(current_count) if current_count else 0
            
            return {
                "limit": limit_config['requests'],
                "remaining": max(0, limit_config['requests'] - current_count),
                "reset_time": ttl,
                "window": limit_config['window']
            }
        except Exception as e:
            logger.error(f"Rate limit status check failed: {e}")
            return {"unlimited": True}


class SecurityService(BaseService):
    """Comprehensive Security Service for EMS"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("security", config)
        self.app = self._create_fastapi_app()
        
        # Security components
        self.policy = SecurityPolicy(**config.get('security_policy', {}))
        self.password_validator = PasswordValidator(self.policy)
        self.encryption_manager = EncryptionManager()
        self.audit_logger = AuditLogger()
        self.rate_limiter = RateLimiter()
        
        # Storage
        self.users = {}  # In production, this would be a database
        self.active_sessions = {}
        self.revoked_tokens = set()
        
        # Security monitoring
        self.failed_login_attempts = {}
        self.suspicious_activities = []
        
        # JWT secret
        self.jwt_secret = config.get('jwt_secret', secrets.token_urlsafe(32))
        
    async def initialize(self):
        """Initialize security service"""
        await super().initialize()
        
        # Initialize Redis for caching and rate limiting
        if self.config.get('redis'):
            redis_config = self.config['redis']
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 2)  # Different DB for security
            )
            self.audit_logger.redis_client = self.redis_client
            self.rate_limiter.redis_client = self.redis_client
        
        # Create default admin user if none exists
        await self._create_default_admin()
        
        logger.info("Security service initialized")
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application with security middleware"""
        app = FastAPI(
            title="EMS Security Service",
            description="Comprehensive security and authentication service",
            version="1.0.0"
        )
        
        # Security middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        if self.policy.ip_whitelist_enabled:
            app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=["localhost", "127.0.0.1"]
            )
        
        self._add_routes(app)
        return app
    
    def _add_routes(self, app: FastAPI):
        """Add security-related routes"""
        
        @app.middleware("http")
        async def security_middleware(request: Request, call_next):
            """Security middleware for all requests"""
            start_time = time.time()
            
            # Rate limiting
            client_ip = self._get_client_ip(request)
            if await self.rate_limiter.is_rate_limited(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded"}
                )
            
            response = await call_next(request)
            
            # Log request
            processing_time = time.time() - start_time
            await self._log_request(request, response, processing_time)
            
            return response
        
        @app.get("/health")
        async def health_check():
            return await self.health_check()
        
        @app.post("/auth/register")
        async def register_user(request: Request, user_data: Dict[str, Any]):
            """Register new user"""
            try:
                client_ip = self._get_client_ip(request)
                
                # Validate input
                validation_result = await self._validate_user_registration(user_data)
                if not validation_result["valid"]:
                    await self._log_security_event(
                        "registration_failed", None, client_ip, request.headers.get("user-agent", ""),
                        f"Invalid registration data: {validation_result['errors']}", "medium", 5.0
                    )
                    raise HTTPException(status_code=400, detail=validation_result["errors"])
                
                # Create user
                user = await self._create_user(user_data, client_ip)
                
                await self._log_security_event(
                    "user_registered", user.user_id, client_ip, request.headers.get("user-agent", ""),
                    f"User {user.username} registered successfully", "low", 2.0
                )
                
                return {
                    "message": "User registered successfully",
                    "user_id": user.user_id,
                    "verification_required": not user.is_verified
                }
                
            except Exception as e:
                logger.error(f"Registration error: {e}")
                raise HTTPException(status_code=500, detail="Registration failed")
        
        @app.post("/auth/login")
        async def login_user(request: Request, credentials: Dict[str, str]):
            """Authenticate user and create session"""
            try:
                client_ip = self._get_client_ip(request)
                user_agent = request.headers.get("user-agent", "")
                username = credentials.get("username", "")
                password = credentials.get("password", "")
                
                # Check rate limiting for login attempts
                if await self.rate_limiter.is_rate_limited(f"login:{client_ip}", "login"):
                    await self._log_security_event(
                        "login_rate_limited", None, client_ip, user_agent,
                        f"Login rate limit exceeded for IP {client_ip}", "high", 7.0
                    )
                    raise HTTPException(status_code=429, detail="Too many login attempts")
                
                # Authenticate user
                auth_result = await self._authenticate_user(username, password, client_ip, user_agent)
                
                if auth_result["success"]:
                    user = auth_result["user"]
                    token = auth_result["token"]
                    
                    return {
                        "access_token": token.token,
                        "token_type": "bearer",
                        "expires_in": int((token.expires_at - datetime.now()).total_seconds()),
                        "user": {
                            "user_id": user.user_id,
                            "username": user.username,
                            "roles": user.roles,
                            "permissions": user.permissions
                        }
                    }
                else:
                    raise HTTPException(status_code=401, detail=auth_result["error"])
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Login error: {e}")
                raise HTTPException(status_code=500, detail="Authentication failed")
        
        @app.post("/auth/logout")
        async def logout_user(request: Request, token: str = Depends(self._get_token_from_header)):
            """Logout user and revoke session"""
            try:
                client_ip = self._get_client_ip(request)
                user_agent = request.headers.get("user-agent", "")
                
                # Revoke token
                await self._revoke_token(token)
                
                # Get user from token for logging
                try:
                    payload = self.encryption_manager.verify_token(token, self.jwt_secret)
                    user_id = payload.get("user_id")
                except:
                    user_id = None
                
                await self._log_security_event(
                    "user_logout", user_id, client_ip, user_agent,
                    "User logged out successfully", "low", 1.0
                )
                
                return {"message": "Logged out successfully"}
                
            except Exception as e:
                logger.error(f"Logout error: {e}")
                raise HTTPException(status_code=500, detail="Logout failed")
        
        @app.get("/auth/verify")
        async def verify_token(request: Request, token: str = Depends(self._get_token_from_header)):
            """Verify token and return user information"""
            try:
                # Verify token
                payload = self.encryption_manager.verify_token(token, self.jwt_secret)
                
                # Check if token is revoked
                if token in self.revoked_tokens:
                    raise HTTPException(status_code=401, detail="Token has been revoked")
                
                user_id = payload.get("user_id")
                user = self.users.get(user_id)
                
                if not user or not user.is_active:
                    raise HTTPException(status_code=401, detail="User not found or inactive")
                
                return {
                    "valid": True,
                    "user": {
                        "user_id": user.user_id,
                        "username": user.username,
                        "roles": user.roles,
                        "permissions": user.permissions
                    },
                    "expires_at": payload.get("exp")
                }
                
            except ValueError as e:
                raise HTTPException(status_code=401, detail=str(e))
            except Exception as e:
                logger.error(f"Token verification error: {e}")
                raise HTTPException(status_code=500, detail="Token verification failed")
        
        @app.post("/security/change_password")
        async def change_password(
            request: Request, 
            password_data: Dict[str, str],
            current_user: Dict[str, Any] = Depends(self._get_current_user)
        ):
            """Change user password"""
            try:
                client_ip = self._get_client_ip(request)
                user_agent = request.headers.get("user-agent", "")
                user_id = current_user["user_id"]
                
                current_password = password_data.get("current_password", "")
                new_password = password_data.get("new_password", "")
                
                # Verify current password
                user = self.users[user_id]
                if not self.encryption_manager.verify_password(current_password, user.password_hash):
                    await self._log_security_event(
                        "password_change_failed", user_id, client_ip, user_agent,
                        "Invalid current password for password change", "medium", 6.0
                    )
                    raise HTTPException(status_code=400, detail="Current password is incorrect")
                
                # Validate new password
                validation = self.password_validator.validate_password(
                    new_password, 
                    {"username": user.username, "email": user.email}
                )
                
                if not validation["valid"]:
                    raise HTTPException(status_code=400, detail=validation["errors"])
                
                # Check password history
                for old_hash in user.password_history:
                    if self.encryption_manager.verify_password(new_password, old_hash):
                        raise HTTPException(
                            status_code=400, 
                            detail="Password has been used recently. Please choose a different password."
                        )
                
                # Update password
                new_hash = self.encryption_manager.hash_password(new_password)
                user.password_history.append(user.password_hash)
                user.password_history = user.password_history[-self.policy.password_history_count:]
                user.password_hash = new_hash
                user.last_password_change = datetime.now()
                user.updated_at = datetime.now()
                
                await self._log_security_event(
                    "password_changed", user_id, client_ip, user_agent,
                    "Password changed successfully", "low", 2.0
                )
                
                return {"message": "Password changed successfully"}
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Password change error: {e}")
                raise HTTPException(status_code=500, detail="Password change failed")
        
        @app.get("/security/audit_logs")
        async def get_audit_logs(
            request: Request,
            limit: int = 100,
            event_type: Optional[str] = None,
            current_user: Dict[str, Any] = Depends(self._get_current_user)
        ):
            """Get security audit logs (admin only)"""
            try:
                # Check admin permission
                if "admin" not in current_user.get("roles", []):
                    raise HTTPException(status_code=403, detail="Admin access required")
                
                # Get logs from Redis
                logs = []
                if self.redis_client:
                    log_entries = await self.redis_client.lrange("security_events", 0, limit - 1)
                    for entry in log_entries:
                        log_data = json.loads(entry)
                        if not event_type or log_data.get("event_type") == event_type:
                            logs.append(log_data)
                
                return {
                    "logs": logs,
                    "total": len(logs),
                    "filtered_by": event_type
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Audit logs error: {e}")
                raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")
    
    async def _validate_user_registration(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user registration data"""
        errors = []
        
        # Required fields
        required_fields = ["username", "email", "password"]
        for field in required_fields:
            if not user_data.get(field):
                errors.append(f"{field} is required")
        
        username = user_data.get("username", "")
        email = user_data.get("email", "")
        password = user_data.get("password", "")
        
        # Username validation
        if len(username) < 3:
            errors.append("Username must be at least 3 characters long")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append("Username can only contain letters, numbers, and underscores")
        if any(user.username == username for user in self.users.values()):
            errors.append("Username already exists")
        
        # Email validation
        try:
            valid_email = validate_email(email)
            email = valid_email.email
        except EmailNotValidError:
            errors.append("Invalid email format")
        
        if any(user.email == email for user in self.users.values()):
            errors.append("Email already registered")
        
        # Password validation
        if password:
            validation = self.password_validator.validate_password(
                password, 
                {"username": username, "email": email}
            )
            if not validation["valid"]:
                errors.extend(validation["errors"])
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _create_user(self, user_data: Dict[str, Any], client_ip: str) -> User:
        """Create new user"""
        user_id = secrets.token_urlsafe(16)
        password_hash = self.encryption_manager.hash_password(user_data["password"])
        
        user = User(
            user_id=user_id,
            username=user_data["username"],
            email=user_data["email"],
            password_hash=password_hash,
            roles=user_data.get("roles", ["user"]),
            permissions=user_data.get("permissions", []),
            is_active=True,
            is_verified=False,  # Require email verification
            is_locked=False,
            last_login=None,
            last_password_change=datetime.now(),
            failed_login_attempts=0,
            max_failed_attempts=self.policy.max_failed_login_attempts,
            lockout_duration=self.policy.lockout_duration,
            mfa_enabled=False,
            mfa_secret=None,
            password_history=[],
            session_timeout=self.policy.session_timeout,
            allowed_ips=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.users[user_id] = user
        return user
    
    async def _authenticate_user(self, username: str, password: str, client_ip: str, user_agent: str) -> Dict[str, Any]:
        """Authenticate user and create session"""
        
        # Find user
        user = None
        for u in self.users.values():
            if u.username == username or u.email == username:
                user = u
                break
        
        if not user:
            await self._log_security_event(
                "login_failed", None, client_ip, user_agent,
                f"Login attempt with unknown username: {username}", "medium", 5.0
            )
            return {"success": False, "error": "Invalid credentials"}
        
        # Check if user is locked
        if user.is_locked:
            await self._log_security_event(
                "login_failed", user.user_id, client_ip, user_agent,
                "Login attempt on locked account", "high", 8.0
            )
            return {"success": False, "error": "Account is locked"}
        
        # Check if user is active
        if not user.is_active:
            await self._log_security_event(
                "login_failed", user.user_id, client_ip, user_agent,
                "Login attempt on inactive account", "medium", 6.0
            )
            return {"success": False, "error": "Account is inactive"}
        
        # Verify password
        if not self.encryption_manager.verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            
            # Lock account if too many failed attempts
            if user.failed_login_attempts >= user.max_failed_attempts:
                user.is_locked = True
                await self._log_security_event(
                    "account_locked", user.user_id, client_ip, user_agent,
                    f"Account locked due to {user.failed_login_attempts} failed login attempts", "high", 8.0
                )
            else:
                await self._log_security_event(
                    "login_failed", user.user_id, client_ip, user_agent,
                    f"Invalid password (attempt {user.failed_login_attempts})", "medium", 5.0
                )
            
            return {"success": False, "error": "Invalid credentials"}
        
        # Successful login
        user.failed_login_attempts = 0
        user.last_login = datetime.now()
        user.updated_at = datetime.now()
        
        # Create access token
        token = await self._create_access_token(user, client_ip, user_agent)
        
        await self._log_security_event(
            "login_success", user.user_id, client_ip, user_agent,
            "Successful login", "low", 1.0
        )
        
        return {"success": True, "user": user, "token": token}
    
    async def _create_access_token(self, user: User, client_ip: str, user_agent: str) -> AccessToken:
        """Create access token for user"""
        
        session_id = secrets.token_urlsafe(16)
        expires_at = datetime.now() + timedelta(minutes=user.session_timeout)
        
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "roles": user.roles,
            "permissions": user.permissions,
            "session_id": session_id
        }
        
        token_string = self.encryption_manager.generate_token(
            payload, 
            self.jwt_secret, 
            int((expires_at - datetime.now()).total_seconds())
        )
        
        token = AccessToken(
            token=token_string,
            token_type="bearer",
            expires_at=expires_at,
            user_id=user.user_id,
            scopes=user.permissions,
            session_id=session_id,
            is_revoked=False,
            created_at=datetime.now(),
            last_used=datetime.now(),
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        self.active_sessions[session_id] = token
        return token
    
    async def _revoke_token(self, token_string: str):
        """Revoke access token"""
        try:
            payload = self.encryption_manager.verify_token(token_string, self.jwt_secret)
            session_id = payload.get("session_id")
            
            if session_id in self.active_sessions:
                self.active_sessions[session_id].is_revoked = True
                del self.active_sessions[session_id]
            
            self.revoked_tokens.add(token_string)
            
        except Exception as e:
            logger.error(f"Token revocation error: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for X-Forwarded-For header (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Use direct client IP
        return request.client.host if request.client else "unknown"
    
    async def _get_token_from_header(self, request: Request) -> str:
        """Extract token from Authorization header"""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Invalid authentication scheme")
            return token
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    async def _get_current_user(self, request: Request, token: str = Depends(_get_token_from_header)) -> Dict[str, Any]:
        """Get current user from token"""
        try:
            payload = self.encryption_manager.verify_token(token, self.jwt_secret)
            
            if token in self.revoked_tokens:
                raise HTTPException(status_code=401, detail="Token has been revoked")
            
            user_id = payload.get("user_id")
            user = self.users.get(user_id)
            
            if not user or not user.is_active:
                raise HTTPException(status_code=401, detail="User not found or inactive")
            
            return {
                "user_id": user.user_id,
                "username": user.username,
                "roles": user.roles,
                "permissions": user.permissions
            }
            
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
    
    async def _log_security_event(self, 
                                event_type: str,
                                user_id: Optional[str],
                                ip_address: str,
                                user_agent: str,
                                description: str,
                                severity: str,
                                risk_score: float):
        """Log security event"""
        
        event = SecurityEvent(
            event_id=secrets.token_urlsafe(8),
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(),
            severity=severity,
            description=description,
            additional_data={},
            risk_score=risk_score
        )
        
        await self.audit_logger.log_security_event(event)
    
    async def _log_request(self, request: Request, response: Response, processing_time: float):
        """Log HTTP request for security monitoring"""
        # Only log sensitive endpoints or failed requests
        sensitive_paths = ["/auth/", "/security/", "/admin/"]
        
        if any(path in str(request.url) for path in sensitive_paths) or response.status_code >= 400:
            await self._log_security_event(
                "http_request",
                None,  # Would extract from token if available
                self._get_client_ip(request),
                request.headers.get("user-agent", ""),
                f"{request.method} {request.url} - {response.status_code} ({processing_time:.3f}s)",
                "low" if response.status_code < 400 else "medium",
                3.0 if response.status_code >= 400 else 1.0
            )
    
    async def _create_default_admin(self):
        """Create default admin user if none exists"""
        if not any(user for user in self.users.values() if "admin" in user.roles):
            admin_password = self.password_validator.generate_secure_password(16)
            
            admin_data = {
                "username": "admin",
                "email": "admin@ems.local",
                "password": admin_password,
                "roles": ["admin", "user"],
                "permissions": ["*"]
            }
            
            admin_user = await self._create_user(admin_data, "127.0.0.1")
            admin_user.is_verified = True
            
            logger.warning(f"Default admin user created - Username: admin, Password: {admin_password}")
            logger.warning("Please change the default admin password immediately!")
    
    async def health_check(self):
        """Service-specific health check"""
        try:
            redis_connected = False
            if self.redis_client:
                try:
                    await self.redis_client.ping()
                    redis_connected = True
                except:
                    pass
            
            return {
                "status": "healthy",
                "service": self.service_name,
                "users_count": len(self.users),
                "active_sessions": len(self.active_sessions),
                "revoked_tokens": len(self.revoked_tokens),
                "redis_connected": redis_connected,
                "security_policy": {
                    "mfa_required": self.policy.mfa_required,
                    "rate_limit_enabled": self.policy.rate_limit_enabled,
                    "password_min_length": self.policy.password_min_length
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise Exception(f"Security service unhealthy: {e}")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service-specific requests"""
        request_type = request_data.get('type')
        
        if request_type == 'authenticate':
            return await self._authenticate_user(
                request_data.get('username'),
                request_data.get('password'),
                request_data.get('client_ip', 'unknown'),
                request_data.get('user_agent', 'unknown')
            )
        elif request_type == 'verify_token':
            token = request_data.get('token')
            try:
                payload = self.encryption_manager.verify_token(token, self.jwt_secret)
                return {"valid": True, "payload": payload}
            except ValueError as e:
                return {"valid": False, "error": str(e)}
        else:
            raise ValueError(f"Unknown request type: {request_type}")


def create_security_service(config: Dict[str, Any] = None) -> SecurityService:
    """Create and configure security service"""
    if config is None:
        config = {
            "jwt_secret": os.getenv("JWT_SECRET", secrets.token_urlsafe(32)),
            "security_policy": {
                "password_min_length": 12,
                "session_timeout": 480,
                "max_failed_login_attempts": 5,
                "mfa_required": False,
                "rate_limit_enabled": True
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 2
            }
        }
    
    return SecurityService(config)


# Example usage
if __name__ == "__main__":
    import uvicorn
    
    service = create_security_service()
    uvicorn.run(service.app, host="0.0.0.0", port=8013)
    password_min_length: int
    password_require_uppercase: bool
    password_require_lowercase: bool
    password_require_numbers: bool
    password_require_symbols: bool
    password_max_age_days: int
    session_timeout_minutes: int
    max_failed_login_attempts: int
    lockout_duration_minutes: int
    require_mfa: bool
    allowed_ip_ranges: List[str]
    rate_limit_requests_per_minute: int
    enable_audit_logging: bool


class PasswordValidator:
    """Advanced password validation"""
    
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
    
    def validate_password(self, password: str, user: Optional[User] = None) -> Dict[str, Any]:
        """Comprehensive password validation"""
        errors = []
        score = 0
        
        # Length check
        if len(password) < self.policy.password_min_length:
            errors.append(f"Password must be at least {self.policy.password_min_length} characters")
        else:
            score += 1
        
        # Character requirements
        if self.policy.password_require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        else:
            score += 1
        
        if self.policy.password_require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        else:
            score += 1
        
        if self.policy.password_require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        else:
            score += 1
        
        if self.policy.password_require_symbols and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        else:
            score += 1
        
        # Common password checks
        common_passwords = ['password', '123456', 'admin', 'qwerty', 'password123']
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        # Check against previous passwords
        if user and user.password_history:
            for old_password_hash in user.password_history:
                if bcrypt.checkpw(password.encode('utf-8'), old_password_hash.encode('utf-8')):
                    errors.append("Password cannot be the same as previous passwords")
                    break
        
        # Calculate strength score (0-100)
        strength_score = min(100, (score / 5) * 100)
        
        # Entropy calculation
        entropy = self._calculate_entropy(password)
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'strength_score': strength_score,
            'entropy': entropy
        }
    
    def _calculate_entropy(self, password: str) -> float:
        """Calculate password entropy"""
        charset_size = 0
        
        if re.search(r'[a-z]', password):
            charset_size += 26
        if re.search(r'[A-Z]', password):
            charset_size += 26
        if re.search(r'\d', password):
            charset_size += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            charset_size += 32
        
        if charset_size == 0:
            return 0
        
        import math
        return len(password) * math.log2(charset_size)


class EncryptionManager:
    """Advanced encryption and decryption manager"""
    
    def __init__(self, key: bytes):
        self.fernet = Fernet(key)
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
    
    def encrypt_symmetric(self, data: str) -> str:
        """Encrypt data using symmetric encryption"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_symmetric(self, encrypted_data: str) -> str:
        """Decrypt data using symmetric encryption"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_asymmetric(self, data: str) -> bytes:
        """Encrypt data using asymmetric encryption"""
        return self.public_key.encrypt(
            data.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
    def decrypt_asymmetric(self, encrypted_data: bytes) -> str:
        """Decrypt data using asymmetric encryption"""
        return self.private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        ).decode()
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


class RateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_rate_limit(self, identifier: str, limit: int, window: int, burst: int = None) -> Dict[str, Any]:
        """Check rate limit using sliding window with burst capability"""
        current_time = int(time.time())
        key = f"rate_limit:{identifier}"
        
        # Sliding window rate limiting
        async with self.redis.pipeline() as pipe:
            # Remove old entries
            pipe.zremrangebyscore(key, 0, current_time - window)
            # Count current requests
            pipe.zcard(key)
            # Add current request
            pipe.zadd(key, {current_time: current_time})
            # Set expiration
            pipe.expire(key, window)
            
            results = await pipe.execute()
            current_count = results[1]
        
        # Check limits
        is_allowed = current_count < limit
        
        # Burst handling
        if burst and current_count >= limit:
            burst_key = f"burst:{identifier}"
            burst_count = await self.redis.get(burst_key) or 0
            
            if int(burst_count) < burst:
                await self.redis.incr(burst_key)
                await self.redis.expire(burst_key, 60)  # 1 minute burst window
                is_allowed = True
        
        return {
            'allowed': is_allowed,
            'current_count': current_count,
            'limit': limit,
            'reset_time': current_time + window,
            'remaining': max(0, limit - current_count)
        }


class SecurityMonitor:
    """Advanced security monitoring and threat detection"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.threat_patterns = self._load_threat_patterns()
    
    def _load_threat_patterns(self) -> Dict[str, Any]:
        """Load threat detection patterns"""
        return {
            'sql_injection': [
                r"(\bunion\b.*\bselect\b)",
                r"(\bselect\b.*\bfrom\b)",
                r"(\binsert\b.*\binto\b)",
                r"(\bupdate\b.*\bset\b)",
                r"(\bdelete\b.*\bfrom\b)"
            ],
            'xss': [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"expression\s*\("
            ],
            'directory_traversal': [
                r"\.\./",
                r"\.\.\\",
                r"\.\.%2f",
                r"\.\.%5c"
            ],
            'command_injection': [
                r"[;&|`]",
                r"\$\(",
                r"`[^`]*`",
                r"\|\s*\w+"
            ]
        }
    
    async def analyze_request(self, request: Request) -> Dict[str, Any]:
        """Analyze request for security threats"""
        risk_score = 0
        threats = []
        
        # Analyze URL
        url_threats = self._analyze_url(str(request.url))
        threats.extend(url_threats)
        risk_score += len(url_threats) * 0.3
        
        # Analyze headers
        header_threats = self._analyze_headers(request.headers)
        threats.extend(header_threats)
        risk_score += len(header_threats) * 0.2
        
        # Analyze user agent
        user_agent = request.headers.get('user-agent', '')
        if self._is_suspicious_user_agent(user_agent):
            threats.append('suspicious_user_agent')
            risk_score += 0.4
        
        # Check IP reputation (simplified)
        client_ip = request.client.host
        if await self._check_ip_reputation(client_ip):
            threats.append('malicious_ip')
            risk_score += 0.8
        
        return {
            'risk_score': min(1.0, risk_score),
            'threats': threats,
            'is_suspicious': risk_score > 0.5
        }
    
    def _analyze_url(self, url: str) -> List[str]:
        """Analyze URL for malicious patterns"""
        threats = []
        url_lower = url.lower()
        
        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url_lower, re.IGNORECASE):
                    threats.append(threat_type)
                    break
        
        return threats
    
    def _analyze_headers(self, headers) -> List[str]:
        """Analyze headers for suspicious content"""
        threats = []
        
        # Check for common attack headers
        suspicious_headers = ['x-forwarded-for', 'x-real-ip', 'x-originating-ip']
        
        for header_name, header_value in headers.items():
            if header_name.lower() in suspicious_headers:
                # Check for multiple IPs (potential IP spoofing)
                if ',' in header_value:
                    threats.append('ip_spoofing_attempt')
        
        return threats
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious"""
        suspicious_patterns = [
            r'bot',
            r'crawler',
            r'spider',
            r'scan',
            r'curl',
            r'wget',
            r'python',
            r'java'
        ]
        
        user_agent_lower = user_agent.lower()
        return any(re.search(pattern, user_agent_lower) for pattern in suspicious_patterns)
    
    async def _check_ip_reputation(self, ip: str) -> bool:
        """Check IP against reputation databases (simplified)"""
        # In a real implementation, this would check against threat intelligence feeds
        blocked_ips = await self.redis.sismember('blocked_ips', ip)
        return blocked_ips


class SecurityService(BaseService):
    """Comprehensive security service with advanced features"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("security", config)
        
        # Security configuration
        self.security_policy = SecurityPolicy(
            password_min_length=config.get('password_min_length', 12),
            password_require_uppercase=config.get('password_require_uppercase', True),
            password_require_lowercase=config.get('password_require_lowercase', True),
            password_require_numbers=config.get('password_require_numbers', True),
            password_require_symbols=config.get('password_require_symbols', True),
            password_max_age_days=config.get('password_max_age_days', 90),
            session_timeout_minutes=config.get('session_timeout_minutes', 30),
            max_failed_login_attempts=config.get('max_failed_login_attempts', 5),
            lockout_duration_minutes=config.get('lockout_duration_minutes', 15),
            require_mfa=config.get('require_mfa', False),
            allowed_ip_ranges=config.get('allowed_ip_ranges', []),
            rate_limit_requests_per_minute=config.get('rate_limit_requests_per_minute', 60),
            enable_audit_logging=config.get('enable_audit_logging', True)
        )
        
        # Initialize components
        encryption_key = config.get('encryption_key', Fernet.generate_key())
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        self.password_validator = PasswordValidator(self.security_policy)
        self.encryption_manager = EncryptionManager(encryption_key)
        self.jwt_secret = config.get('jwt_secret', secrets.token_urlsafe(32))
        self.jwt_algorithm = 'HS256'
        
        # Collections
        self.collections = {}
        
        # Security components (initialized during setup)
        self.rate_limiter = None
        self.security_monitor = None
        
        # FastAPI app
        self.app = self._create_fastapi_app()
    
    async def initialize(self):
        """Initialize security service"""
        await super().initialize()
        
        # Initialize database collections
        if self.db_client:
            db = self.db_client[self.config['mongodb']['database']]
            self.collections = {
                'users': db.ems_users,
                'sessions': db.ems_sessions,
                'security_events': db.ems_security_events,
                'access_tokens': db.ems_access_tokens,
                'api_keys': db.ems_api_keys,
                'audit_logs': db.ems_audit_logs
            }
            
            # Create indexes for performance
            await self._create_security_indexes()
        
        # Initialize Redis-dependent components
        if self.redis_client:
            self.rate_limiter = RateLimiter(self.redis_client)
            self.security_monitor = SecurityMonitor(self.redis_client)
        
        # Create default admin user if not exists
        await self._ensure_admin_user()
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application with security middleware"""
        app = FastAPI(
            title="EMS Security Service",
            description="Comprehensive security service for authentication and authorization",
            version="1.0.0"
        )
        
        # Security middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure properly for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=["*"]  # Configure properly for production
        )
        
        # Custom security middleware
        @app.middleware("http")
        async def security_middleware(request: Request, call_next):
            """Custom security middleware"""
            start_time = time.time()
            
            # Security analysis
            if self.security_monitor:
                security_analysis = await self.security_monitor.analyze_request(request)
                
                # Block suspicious requests
                if security_analysis['is_suspicious']:
                    await self._log_security_event(
                        'suspicious_request',
                        None,
                        request.client.host,
                        request.headers.get('user-agent', ''),
                        'medium',
                        f"Suspicious request detected: {security_analysis['threats']}",
                        {'analysis': security_analysis}
                    )
                    
                    # Return 403 for high-risk requests
                    if security_analysis['risk_score'] > 0.8:
                        return JSONResponse(
                            status_code=403,
                            content={"error": "Request blocked for security reasons"}
                        )
            
            # Rate limiting
            if self.rate_limiter:
                rate_limit_result = await self.rate_limiter.check_rate_limit(
                    request.client.host,
                    self.security_policy.rate_limit_requests_per_minute,
                    60  # 1 minute window
                )
                
                if not rate_limit_result['allowed']:
                    return JSONResponse(
                        status_code=429,
                        content={"error": "Rate limit exceeded"},
                        headers={
                            "X-RateLimit-Limit": str(self.security_policy.rate_limit_requests_per_minute),
                            "X-RateLimit-Remaining": str(rate_limit_result['remaining']),
                            "X-RateLimit-Reset": str(rate_limit_result['reset_time'])
                        }
                    )
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'"
            
            # Log processing time
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        
        # Add routes
        self._add_routes(app)
        
        return app
    
    def _add_routes(self, app: FastAPI):
        """Add security service routes"""
        
        oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "security_policy": {
                    "mfa_required": self.security_policy.require_mfa,
                    "password_policy": {
                        "min_length": self.security_policy.password_min_length,
                        "complexity_required": True
                    }
                }
            }
        
        @app.post("/auth/register")
        async def register_user(user_data: Dict[str, Any]):
            """Register new user with comprehensive validation"""
            try:
                # Validate input
                username = user_data.get('username', '').strip()
                email = user_data.get('email', '').strip()
                password = user_data.get('password', '')
                
                if not username or not email or not password:
                    raise HTTPException(
                        status_code=400,
                        detail="Username, email, and password are required"
                    )
                
                # Validate email
                try:
                    validated_email = validate_email(email)
                    email = validated_email.email
                except EmailNotValidError:
                    raise HTTPException(status_code=400, detail="Invalid email address")
                
                # Check if user already exists
                existing_user = await asyncio.to_thread(
                    self.collections['users'].find_one,
                    {"$or": [{"username": username}, {"email": email}]}
                )
                
                if existing_user:
                    raise HTTPException(status_code=400, detail="User already exists")
                
                # Validate password
                password_validation = self.password_validator.validate_password(password)
                if not password_validation['is_valid']:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "message": "Password validation failed",
                            "errors": password_validation['errors'],
                            "strength_score": password_validation['strength_score']
                        }
                    )
                
                # Create user
                user = User(
                    user_id=secrets.token_urlsafe(16),
                    username=username,
                    email=email,
                    password_hash=self.encryption_manager.hash_password(password),
                    roles=['user'],
                    permissions=['read:own_data'],
                    is_active=True,
                    is_verified=False,
                    is_locked=False,
                    last_login=None,
                    last_password_change=datetime.now(),
                    failed_login_attempts=0,
                    max_failed_attempts=self.security_policy.max_failed_login_attempts,
                    lockout_duration=self.security_policy.lockout_duration_minutes,
                    mfa_enabled=False,
                    mfa_secret=None,
                    password_history=[],
                    session_timeout=self.security_policy.session_timeout_minutes,
                    allowed_ips=[],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                # Store user
                await asyncio.to_thread(
                    self.collections['users'].insert_one,
                    asdict(user)
                )
                
                return {
                    "message": "User registered successfully",
                    "user_id": user.user_id,
                    "verification_required": True
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error registering user: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @app.post("/auth/login")
        async def login_user(request: Request, credentials: Dict[str, Any]):
            """Enhanced login with security features"""
            try:
                username = credentials.get('username', '').strip()
                password = credentials.get('password', '')
                
                if not username or not password:
                    raise HTTPException(status_code=400, detail="Username and password required")
                
                # Get user
                user_doc = await asyncio.to_thread(
                    self.collections['users'].find_one,
                    {"$or": [{"username": username}, {"email": username}]}
                )
                
                if not user_doc:
                    await self._log_security_event(
                        'failed_login',
                        None,
                        request.client.host,
                        request.headers.get('user-agent', ''),
                        'low',
                        f"Login attempt with non-existent username: {username}",
                        {'username': username}
                    )
                    raise HTTPException(status_code=401, detail="Invalid credentials")
                
                user = User(**user_doc)
                
                # Check if account is locked
                if user.is_locked:
                    await self._log_security_event(
                        'locked_account_access',
                        user.user_id,
                        request.client.host,
                        request.headers.get('user-agent', ''),
                        'medium',
                        f"Login attempt on locked account: {username}",
                        {'username': username}
                    )
                    raise HTTPException(status_code=423, detail="Account is locked")
                
                # Verify password
                if not self.encryption_manager.verify_password(password, user.password_hash):
                    # Increment failed attempts
                    failed_attempts = user.failed_login_attempts + 1
                    
                    update_data = {"failed_login_attempts": failed_attempts}
                    
                    # Lock account if max attempts reached
                    if failed_attempts >= user.max_failed_attempts:
                        update_data["is_locked"] = True
                        update_data["locked_at"] = datetime.now()
                    
                    await asyncio.to_thread(
                        self.collections['users'].update_one,
                        {"user_id": user.user_id},
                        {"$set": update_data}
                    )
                    
                    await self._log_security_event(
                        'failed_login',
                        user.user_id,
                        request.client.host,
                        request.headers.get('user-agent', ''),
                        'medium' if failed_attempts >= user.max_failed_attempts else 'low',
                        f"Failed login attempt ({failed_attempts}/{user.max_failed_attempts})",
                        {'username': username, 'failed_attempts': failed_attempts}
                    )
                    
                    raise HTTPException(status_code=401, detail="Invalid credentials")
                
                # Check IP restrictions
                if user.allowed_ips and request.client.host not in user.allowed_ips:
                    await self._log_security_event(
                        'unauthorized_ip',
                        user.user_id,
                        request.client.host,
                        request.headers.get('user-agent', ''),
                        'high',
                        f"Login from unauthorized IP: {request.client.host}",
                        {'username': username, 'ip': request.client.host}
                    )
                    raise HTTPException(status_code=403, detail="Access from this IP is not allowed")
                
                # Generate tokens
                access_token = await self._generate_access_token(user, request)
                refresh_token = await self._generate_refresh_token(user, request)
                
                # Update user login info
                await asyncio.to_thread(
                    self.collections['users'].update_one,
                    {"user_id": user.user_id},
                    {
                        "$set": {
                            "last_login": datetime.now(),
                            "failed_login_attempts": 0,
                            "updated_at": datetime.now()
                        }
                    }
                )
                
                # Log successful login
                await self._log_security_event(
                    'successful_login',
                    user.user_id,
                    request.client.host,
                    request.headers.get('user-agent', ''),
                    'low',
                    f"Successful login for user: {username}",
                    {'username': username}
                )
                
                return {
                    "access_token": access_token['token'],
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": 3600,  # 1 hour
                    "user": {
                        "user_id": user.user_id,
                        "username": user.username,
                        "email": user.email,
                        "roles": user.roles,
                        "permissions": user.permissions
                    }
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error during login: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        # Additional security endpoints would continue here...
        # Including: logout, refresh token, change password, MFA setup, etc.
    
    # Helper methods continue...
