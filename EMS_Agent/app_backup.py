#!/usr/bin/env python3
"""
EMS (Energy Management System) AI Agent
A Flask-based web application for analyzing energy meter data and providing intelligent insights.
"""

from flask import Flask, render_template, request, jsonify
        print("🚀 Server starting on http://localhost:5003")
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
            port=5003,
            debug=True,
            use_reloader=False  # Disable reloader to prevent double initialization
        )om datetime import datetime
import traceback
import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ems_search import EMSQueryEngine
from data_loader import EMSDataLoader
from config import MONGODB_URI, MONGODB_DATABASE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'ems_agent_secret_key_2025'

# Initialize EMS components
query_engine = None
data_loader = None

def initialize_ems():
    """Initialize the EMS query engine and data loader"""
    global query_engine, data_loader
    
    try:
        logger.info("Initializing EMS Query Engine...")
        query_engine = EMSQueryEngine()
        
        logger.info("Initializing EMS Data Loader...")
        data_loader = EMSDataLoader()
        
        logger.info("EMS components initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize EMS components: {str(e)}")
        logger.error(traceback.format_exc())
        return False

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def api_query():
    """Handle EMS queries via API"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'error': 'No query provided',
                'success': False
            }), 400
        
        user_query = data['query'].strip()
        if not user_query:
            return jsonify({
                'error': 'Empty query provided',
                'success': False
            }), 400
        
        logger.info(f"Processing query: {user_query}")
        
        # Get response from EMS query engine
        response = query_engine.process_query(user_query)
        
        return jsonify({
            'query': user_query,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'success': False
        }), 500

@app.route('/api/status')
def api_status():
    """Get system status and statistics"""
    try:
        status = {
            'system': 'EMS Agent',
            'status': 'online',
            'timestamp': datetime.now().isoformat(),
            'database': MONGODB_DATABASE,
            'components': {
                'query_engine': query_engine is not None,
                'data_loader': data_loader is not None
            }
        }
        
        # Get database statistics if available
        if query_engine:
            try:
                stats = query_engine.get_system_stats()
                status['database_stats'] = stats
            except Exception as e:
                logger.warning(f"Could not get database stats: {str(e)}")
                status['database_stats'] = {'error': 'Stats unavailable'}
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({
            'error': f'Status check failed: {str(e)}',
            'success': False
        }), 500

@app.route('/api/load_data', methods=['POST'])
def api_load_data():
    """Load and process Excel data into MongoDB"""
    try:
        logger.info("Starting data loading process...")
        
        # Check if Excel file exists
        excel_file = 'EMS_Energy_Meter_Data.xlsx'
        if not os.path.exists(excel_file):
            return jsonify({
                'error': f'Excel file {excel_file} not found',
                'success': False
            }), 404
        
        # Load and process data
        result = data_loader.load_and_process_all(excel_file)
        
        if result['success']:
            logger.info("Data loading completed successfully")
            return jsonify({
                'message': 'Data loaded successfully',
                'stats': result['stats'],
                'collections_created': result.get('collections', []),
                'success': True
            })
        else:
            logger.error(f"Data loading failed: {result.get('error', 'Unknown error')}")
            return jsonify({
                'error': result.get('error', 'Data loading failed'),
                'success': False
            }), 500
            
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Data loading error: {str(e)}',
            'success': False
        }), 500

@app.route('/api/data_summary')
def api_data_summary():
    """Get summary of available data"""
    try:
        if not query_engine:
            return jsonify({
                'error': 'Query engine not initialized',
                'success': False
            }), 500
        
        summary = query_engine.get_data_summary()
        return jsonify({
            'summary': summary,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error getting data summary: {str(e)}")
        return jsonify({
            'error': f'Could not get data summary: {str(e)}',
            'success': False
        }), 500

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'EMS Agent'
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'success': False
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'success': False
    }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🔋 EMS (Energy Management System) AI Agent")
    print("=" * 60)
    print(f"🏛️  Database: {MONGODB_DATABASE}")
    print(f"🌐 Starting Flask server...")
    print("=" * 60)
    
    # Initialize EMS components
    if initialize_ems():
        print("✅ EMS components initialized successfully!")
        print("🚀 Server starting on http://localhost:5002")
        print("\n📊 Available endpoints:")
        print("   • GET  /              - Main dashboard")
        print("   • POST /api/query     - Process EMS queries")
        print("   • GET  /api/status    - System status")
        print("   • POST /api/load_data - Load Excel data")
        print("   • GET  /api/data_summary - Data summary")
        print("   • GET  /health        - Health check")
        print("=" * 60)
        
        # Start Flask app
        app.run(
            host='0.0.0.0',
            port=5002,
            debug=True,
            use_reloader=False  # Disable reloader to prevent double initialization
        )
    else:
        print("❌ Failed to initialize EMS components. Exiting...")
        sys.exit(1)
