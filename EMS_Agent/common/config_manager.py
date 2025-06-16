#!/usr/bin/env python3
"""
Configuration management for EMS microservices
Handles environment-based configuration, service discovery, and feature flags.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration"""
    uri: str
    database: str
    max_pool_size: int = 10
    min_pool_size: int = 5
    timeout: int = 5000


@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    max_connections: int = 10


@dataclass
class ServiceRegistryConfig:
    """Service registry configuration"""
    host: str = "localhost"
    port: int
    health_check_interval: int = 30


class ConfigManager:
    """Configuration manager for microservices"""
    
    def __init__(self, service_name: str, config_path: Optional[str] = None):
        self.service_name = service_name
        self.config_path = config_path or self._get_default_config_path()
        self.config = {}
        self._load_configuration()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        env = os.getenv('ENVIRONMENT', 'development')
        return f"config/{env}.yaml"
    
    def _load_configuration(self):
        """Load configuration from file and environment variables"""
        # Load from file
        if Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    self.config = yaml.safe_load(f)
                else:
                    self.config = json.load(f)
        
        # Override with environment variables
        self._load_environment_variables()
        
        # Service-specific configuration
        self.config = self.config.get(self.service_name, self.config)
    
    def _load_environment_variables(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'MONGODB_URI': ['mongodb', 'uri'],
            'MONGODB_DATABASE': ['mongodb', 'database'],
            'REDIS_HOST': ['redis', 'host'],
            'REDIS_PORT': ['redis', 'port'],
            'SERVICE_PORT': ['service_registry', 'port'],
            'LOG_LEVEL': ['logging', 'level'],
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_config(config_path, value)
    
    def _set_nested_config(self, path: list, value: str):
        """Set nested configuration value"""
        current = self.config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert value to appropriate type
        if value.isdigit():
            value = int(value)
        elif value.lower() in ['true', 'false']:
            value = value.lower() == 'true'
        
        current[path[-1]] = value
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        db_config = self.config.get('mongodb', {})
        return DatabaseConfig(
            uri=db_config.get('uri', 'mongodb://localhost:27017'),
            database=db_config.get('database', 'ems_database'),
            max_pool_size=db_config.get('max_pool_size', 10),
            min_pool_size=db_config.get('min_pool_size', 5),
            timeout=db_config.get('timeout', 5000)
        )
    
    def get_redis_config(self) -> RedisConfig:
        """Get Redis configuration"""
        redis_config = self.config.get('redis', {})
        return RedisConfig(
            host=redis_config.get('host', 'localhost'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 0),
            max_connections=redis_config.get('max_connections', 10)
        )
    
    def get_service_registry_config(self) -> ServiceRegistryConfig:
        """Get service registry configuration"""
        registry_config = self.config.get('service_registry', {})
        return ServiceRegistryConfig(
            host=registry_config.get('host', 'localhost'),
            port=registry_config.get('port', 8000),
            health_check_interval=registry_config.get('health_check_interval', 30)
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        current = self.config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self.config.copy()
