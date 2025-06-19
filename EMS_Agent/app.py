#!/usr/bin/env python3
"""
EMS (Energy Management System) Main Application
Modernized with microservices architecture support and backwards compatibility
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import requests
import json

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Check if running in microservices mode
MICROSERVICES_MODE = os.getenv('MICROSERVICES_MODE', 'false').lower() == 'true'

# Service URLs configuration
SERVICE_URLS = {
    'analytics': os.getenv('ANALYTICS_SERVICE_URL', 'http://localhost:8001'),
    'advanced_ml': os.getenv('ADVANCED_ML_SERVICE_URL', 'http://localhost:8002'),
    'monitoring': os.getenv('MONITORING_SERVICE_URL', 'http://localhost:8003'),
    'data_ingestion': os.getenv('DATA_INGESTION_SERVICE_URL', 'http://localhost:8004'),
}

class ServiceIntegrator:
    """Helper class to integrate with microservices"""
    
    def __init__(self):
        self.available_services = self._check_service_availability()
        
    def _check_service_availability(self) -> Dict[str, bool]:
        """Check which services are available"""
        available = {}
        for service_name, url in SERVICE_URLS.items():
            try:
                response = requests.get(f"{url}/health", timeout=2)
                available[service_name] = response.status_code == 200
            except:
                available[service_name] = False
        return available
    
    def get_analytics(self, query_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get analytics from analytics service"""
        if not self.available_services.get('analytics', False):
            return None
        
        try:
            response = requests.post(
                f"{SERVICE_URLS['analytics']}/analyze",
                json={'type': query_type, 'data': data},
                timeout=10
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logging.error(f"Analytics service error: {e}")
            return None
    
    def get_ml_prediction(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get ML predictions from advanced ML service"""
        if not self.available_services.get('advanced_ml', False):
            return None
        
        try:
            response = requests.post(
                f"{SERVICE_URLS['advanced_ml']}/predict",
                json=data,
                timeout=15
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logging.error(f"ML service error: {e}")
            return None
    
    def get_anomalies(self) -> Optional[Dict[str, Any]]:
        """Get anomaly detection results"""
        if not self.available_services.get('advanced_ml', False):
            return None
        
        try:
            response = requests.get(
                f"{SERVICE_URLS['advanced_ml']}/anomalies",
                timeout=10
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logging.error(f"Anomaly detection service error: {e}")
            return None

# Global service integrator
service_integrator = ServiceIntegrator()

if MICROSERVICES_MODE:
    # Import microservices components
    from gateway.api_gateway import create_api_gateway, run_gateway
    from services.data_ingestion.service import create_data_ingestion_service
    from services.analytics.service import create_analytics_service
    
    logger = logging.getLogger(__name__)
    
    async def run_microservices():
        """Run all microservices"""
        logger.info("Starting EMS in microservices mode...")
        
        # This would typically be handled by docker-compose
        # For development, we can run a single service based on environment variable
        service_type = os.getenv('SERVICE_TYPE', 'gateway')
        
        if service_type == 'gateway':
            await run_gateway()
        elif service_type == 'data_ingestion':
            service = create_data_ingestion_service()
            await service.initialize()
            # Run service
        elif service_type == 'analytics':
            service = create_analytics_service()
            await service.initialize()
            # Run service
        else:
            logger.error(f"Unknown service type: {service_type}")
            sys.exit(1)
    
    def main():
        """Main entry point for microservices mode"""
        asyncio.run(run_microservices())

else:
    # Legacy monolithic mode for backwards compatibility
    from flask import Flask, render_template, request, jsonify
    import traceback
    from ems_search import EMSQueryEngine
    from data_loader import EMSDataLoader
    from config import MONGODB_URI, MONGODB_DATABASE

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Initialize Flask app
    app = Flask(__name__)

    # Global variables for EMS components
    query_engine = None
    data_loader = None

    def initialize_ems():
        """Initialize EMS components (legacy mode)"""
        global query_engine, data_loader
        
        try:
            logger.info("Initializing EMS Query Engine...")
            query_engine = EMSQueryEngine()
            
            logger.info("Initializing EMS Data Loader...")
            data_loader = EMSDataLoader()
            
            logger.info("EMS components initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize EMS components: {e}")
            logger.error(traceback.format_exc())
            return False

    # Flask routes (legacy mode)
    @app.route('/')
    def index():
        """Main dashboard page"""
        return render_template('index.html')

    @app.route('/api/query', methods=['POST'])
    def process_query():
        """Process user queries about energy data"""
        try:
            data = request.get_json()
            user_query = data.get('query', '').strip()
            
            if not user_query:
                return jsonify({
                    'success': False,
                    'error': 'No query provided'
                }), 400
            
            logger.info(f"Processing query: {user_query}")
            
            # Process the query using the EMS search engine
            if query_engine:
                response = query_engine.process_query(user_query)
                
                # Integrate with analytics and ML services for enhanced processing
                analytics_result = service_integrator.get_analytics('query_analysis', {'query': user_query})
                ml_prediction = service_integrator.get_ml_prediction({'query': user_query})
                anomalies = service_integrator.get_anomalies()
            else:
                response = "EMS system not initialized. Please try again later."
                analytics_result = None
                ml_prediction = None
                anomalies = None
            
            return jsonify({
                'success': True,
                'query': user_query,
                'response': response,
                'analytics': analytics_result,
                'ml_prediction': ml_prediction,
                'anomalies': anomalies,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/status')
    def get_status():
        """Get system status and database statistics"""
        try:
            # Get database statistics
            if query_engine:
                db_stats = query_engine.get_system_stats()
            else:
                db_stats = {'error': 'Query engine not initialized'}
            
            return jsonify({
                'status': 'online',
                'system': 'EMS Agent (Legacy Mode)',
                'database': MONGODB_DATABASE,
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'query_engine': query_engine is not None,
                    'data_loader': data_loader is not None
                },
                'database_stats': db_stats,
                'mode': 'monolithic'
            })
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500

    # ... rest of existing routes ...
    @app.route('/api/load_data', methods=['POST'])
    def load_data():
        """Load Excel data into MongoDB"""
        try:
            # For now, use the default Excel file path
            excel_file_path = 'EMS_Energy_Meter_Data.xlsx'
            
            if not os.path.exists(excel_file_path):
                return jsonify({
                    'success': False,
                    'error': f'Excel file not found: {excel_file_path}'
                }), 400
            
            logger.info(f"Loading data from {excel_file_path}")
            
            # Load and process data
            if data_loader:
                result = data_loader.load_and_process_all(excel_file_path)
            else:
                result = {
                    'success': False,
                    'error': 'Data loader not initialized'
                }
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/data_summary')
    def get_data_summary():
        """Get data summary and statistics"""
        try:
            if query_engine:
                summary = query_engine.get_data_summary()
            else:
                summary = {'error': 'Query engine not initialized'}
            
            return jsonify({
                'success': True,
                'summary': summary
            })
            
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'EMS Agent (Legacy Mode)',
            'mode': 'monolithic'
        })

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({
            'error': 'Endpoint not found',
            'status': 404
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        return jsonify({
            'error': 'Internal server error',
            'status': 500
        }), 500

    def main():
        """Main entry point for legacy mode"""
        print("=" * 60)
        print("🔋 EMS (Energy Management System) AI Agent")
        print("=" * 60)
        print(f"🏛️  Database: {MONGODB_DATABASE}")
        print("🌐 Starting Flask server (Legacy Mode)...")
        print("💡 To use microservices mode, set MICROSERVICES_MODE=true")
        print("=" * 60)
        
        # Initialize EMS components
        if initialize_ems():
            print("✅ EMS components initialized successfully!")
            print("🚀 Server starting on http://localhost:5004")
            print("\n📊 Available endpoints:")
            print("   • GET  /              - Main dashboard")
            print("   • POST /api/query     - Process EMS queries")
            print("   • GET  /api/status    - System status")
            print("   • POST /api/load_data - Load Excel data")
            print("   • GET  /api/data_summary - Data summary")
            print("   • GET  /health        - Health check")
            print("=" * 60)
            
            # Run the Flask app
            app.run(
                host='0.0.0.0',
                port=5004,
                debug=True,
                use_reloader=False  # Disable reloader to prevent double initialization
            )
        else:
            print("❌ Failed to initialize EMS components. Exiting...")
            sys.exit(1)

if __name__ == '__main__':
    main()
