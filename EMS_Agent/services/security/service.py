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
