#!/usr/bin/env python3
"""
Service Launcher for EMS Microservices
Dynamically starts the appropriate service based on SERVICE_TYPE environment variable
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Service factory functions
SERVICE_FACTORIES = {
    'data_ingestion': lambda: __import__('services.data_ingestion.service', fromlist=['create_data_ingestion_service']).create_data_ingestion_service(),
    'analytics': lambda: __import__('services.analytics.service', fromlist=['create_analytics_service']).create_analytics_service(),
    'query_processor': lambda: __import__('services.query_processor.service', fromlist=['create_query_processor_service']).create_query_processor_service(),
    'notification': lambda: __import__('services.notification.service', fromlist=['create_notification_service']).create_notification_service(),
    'realtime_streaming': lambda: __import__('services.streaming.service', fromlist=['create_streaming_service']).create_streaming_service(),
    'advanced_ml': lambda: __import__('services.advanced_ml.service', fromlist=['create_advanced_ml_service']).create_advanced_ml_service(),
    'security': lambda: __import__('services.security.service', fromlist=['create_security_service']).create_security_service(),
    'monitoring': lambda: __import__('services.monitoring.service', fromlist=['create_monitoring_service']).create_monitoring_service(),
    'gateway': lambda: __import__('gateway.api_gateway', fromlist=['create_api_gateway']).create_api_gateway()
}

async def run_service(service_type: str):
    """Run the specified service"""
    if service_type not in SERVICE_FACTORIES:
        logger.error(f"Unknown service type: {service_type}")
        logger.info(f"Available services: {list(SERVICE_FACTORIES.keys())}")
        sys.exit(1)

    try:
        logger.info(f"Starting {service_type} service...")
        
        # Create service instance
        service = SERVICE_FACTORIES[service_type]()
        
        # Initialize service
        await service.initialize()
        
        # Special handling for gateway
        if service_type == 'gateway':
            from gateway.api_gateway import run_gateway
            await run_gateway()
        else:
            # Start the service server
            import uvicorn
            port = int(os.getenv('SERVICE_PORT', get_default_port(service_type)))
            
            logger.info(f"Starting {service_type} on port {port}")
            
            # Enhanced uvicorn configuration for production
            config = uvicorn.Config(
                app=service.app,
                host="0.0.0.0",
                port=port,
                log_level=os.getenv('LOG_LEVEL', 'info').lower(),
                reload=False,
                workers=1,  # Single worker for now, can be increased
                access_log=True,
                use_colors=True,
                server_header=False,  # Security: hide server info
                date_header=False     # Security: hide date header
            )
            server = uvicorn.Server(config)
            
            # Graceful shutdown handler
            import signal
            def signal_handler(signum, frame):
                logger.info(f"Received shutdown signal for {service_type}")
                server.should_exit = True
            
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            
            await server.serve()
            
    except ImportError as e:
        logger.error(f"Failed to import {service_type} service: {e}")
        logger.error("Make sure all dependencies are installed")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start {service_type} service: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def get_default_port(service_type: str) -> int:
    """Get default port for service type"""
    port_mapping = {
        'gateway': 8000,
        'data_ingestion': 8001,
        'analytics': 8002,
        'query_processor': 8003,
        'notification': 8004,
        'realtime_streaming': 8005,
        'advanced_ml': 8006,
        'security': 8007,
        'monitoring': 8008
    }
    return port_mapping.get(service_type, 8000)

def main():
    """Main entry point"""
    # Set microservices mode
    os.environ['MICROSERVICES_MODE'] = 'true'
    
    # Get service type from environment
    service_type = os.getenv('SERVICE_TYPE', os.getenv('SERVICE_NAME', 'gateway'))
    
    if not service_type:
        logger.error("SERVICE_TYPE or SERVICE_NAME environment variable must be set")
        logger.info("Example: export SERVICE_TYPE=analytics")
        sys.exit(1)
    
    # Run the service
    try:
        asyncio.run(run_service(service_type))
    except KeyboardInterrupt:
        logger.info(f"Shutting down {service_type} service...")
    except Exception as e:
        logger.error(f"Service crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
