#!/usr/bin/env python3
"""
Advanced EMS Data Search Engine
Intelligent query processing for Energy Management System data
"""

import re
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import MONGODB_URI, MONGODB_DATABASE

class EMSQueryEngine:
    def __init__(self):
        """Initialize EMS Query Engine"""
        self.client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        self.db = self.client[MONGODB_DATABASE]
        
        # Collections
        self.collections = {
            'raw_data': self.db.ems_raw_data,
            'hourly_aggregates': self.db.ems_hourly_aggregates,
            'daily_aggregates': self.db.ems_daily_aggregates,
            'anomalies': self.db.ems_anomalies,
            'predictions': self.db.ems_predictions
        }
        
        # Query patterns for different types of queries
        self.query_patterns = {
            # Status queries
            r'status|health|connection': self.get_system_status,
            r'anomal|spike|fluctuat|abnormal': self.get_anomalies,
            r'latest|current|now|real.?time': self.get_latest_readings,
            
            # Statistical queries
            r'average|mean|avg': self.get_averages,
            r'maximum|max|peak|highest': self.get_maximum,
            r'minimum|min|lowest': self.get_minimum,
            r'trend|pattern|change': self.get_trends,
            
            # Energy metrics
            r'voltage|volt': self.get_voltage_info,
            r'current|amp|ampere': self.get_current_info,
            r'power.*factor|pf': self.get_power_factor_info,
            r'energy|consumption|usage': self.get_energy_info,
            
            # Time-based queries
            r'today|daily': self.get_today_summary,
            r'hour|hourly': self.get_hourly_data,
            r'report|summary': self.get_comprehensive_report,
        }
    
    def search(self, user_query):
        """Main search method that processes user queries"""
        try:
            query_lower = user_query.lower()
            
            # Try to match query patterns
            for pattern, handler in self.query_patterns.items():
                if re.search(pattern, query_lower):
                    result = handler(user_query)
                    return {
                        'answer': result,
                        'method': handler.__name__,
                        'confidence': 0.85,
                        'query': user_query
                    }
            
            # Default response for unmatched queries
            return {
                'answer': self.get_default_response(user_query),
                'method': 'default_response',
                'confidence': 0.5,
                'query': user_query
            }
            
        except Exception as e:
            return {
                'answer': f"Sorry, I encountered an error processing your query: {str(e)}",
                'method': 'error_handler',
                'confidence': 0.0,
                'query': user_query
            }
    
    def get_system_status(self, query):
        """Get system connection and data status"""
        try:
            # Test connection
            self.client.admin.command('ping')
            
            stats = self.get_system_stats()
            total_records = stats.get('total_records', 0)
            
            if total_records > 0:
                return f"✅ EMS System Status: Connected and operational with {total_records:,} total records across {stats.get('total_collections', 0)} collections."
            else:
                return "⚠️ EMS System Status: Connected but no data available. Please load energy data first."
                
        except Exception as e:
            return f"❌ EMS System Status: Connection failed - {str(e)}"
    
    def get_anomalies(self, query):
        """Get information about anomalies and spikes"""
        try:
            anomaly_collection = self.collections['anomalies']
            anomaly_count = anomaly_collection.count_documents({})
            
            if anomaly_count == 0:
                return "✅ No anomalies detected in the current dataset. All energy readings appear normal."
            
            # Get recent anomalies
            recent_anomalies = list(anomaly_collection.find().sort('timestamp', -1).limit(5))
            
            response = f"⚠️ Found {anomaly_count} anomalies in the energy data.\n\nRecent anomalies:\n"
            
            for i, anomaly in enumerate(recent_anomalies, 1):
                response += f"{i}. {anomaly.get('description', 'Anomaly detected')} - {anomaly.get('parameter', 'Unknown parameter')}: {anomaly.get('value', 'N/A')}\n"
            
            return response
            
        except Exception as e:
            return f"Error retrieving anomaly data: {str(e)}"
    
    def get_latest_readings(self, query):
        """Get the most recent sensor readings"""
        try:
            raw_data = self.collections['raw_data']
            latest = raw_data.find().sort('timestamp', -1).limit(1)
            latest_doc = next(latest, None)
            
            if not latest_doc:
                return "No recent readings available. Please ensure energy data is loaded."
            
            response = "📊 Latest Energy Readings:\n"
            response += f"🕐 Timestamp: {latest_doc.get('timestamp', 'Unknown')}\n"
            response += f"⚡ Voltage: {latest_doc.get('Voltage (V)', 'N/A')} V\n"
            response += f"🔌 Current: {latest_doc.get('Current (A)', 'N/A')} A\n"
            response += f"📈 Power Factor: {latest_doc.get('Power Factor', 'N/A')}\n"
            response += f"💡 Active Power: {latest_doc.get('Active Power (W)', 'N/A')} W\n"
            
            return response
            
        except Exception as e:
            return f"Error retrieving latest readings: {str(e)}"
    
    def get_averages(self, query):
        """Get average values for energy parameters"""
        try:
            raw_data = self.collections['raw_data']
            
            # Use aggregation pipeline to calculate averages
            pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'avg_voltage': {'$avg': '$Voltage (V)'},
                        'avg_current': {'$avg': '$Current (A)'},
                        'avg_power_factor': {'$avg': '$Power Factor'},
                        'avg_active_power': {'$avg': '$Active Power (W)'},
                        'count': {'$sum': 1}
                    }
                }
            ]
            
            result = list(raw_data.aggregate(pipeline))
            
            if not result:
                return "No data available for calculating averages."
            
            avg_data = result[0]
            
            response = f"📊 Average Energy Parameters (based on {avg_data.get('count', 0)} readings):\n"
            response += f"⚡ Average Voltage: {avg_data.get('avg_voltage', 0):.2f} V\n"
            response += f"🔌 Average Current: {avg_data.get('avg_current', 0):.2f} A\n"
            response += f"📈 Average Power Factor: {avg_data.get('avg_power_factor', 0):.3f}\n"
            response += f"💡 Average Active Power: {avg_data.get('avg_active_power', 0):.2f} W\n"
            
            return response
            
        except Exception as e:
            return f"Error calculating averages: {str(e)}"
    
    def get_today_summary(self, query):
        """Get summary of today's energy data"""
        try:
            # For demo purposes, get overall summary since we don't have real-time data
            stats = self.get_system_stats()
            summary = self.get_data_summary()
            
            response = "📅 Energy System Summary:\n"
            response += f"📊 Total Records: {stats.get('total_records', 0):,}\n"
            response += f"⚠️ Anomalies Detected: {summary.get('anomaly_count', 0)}\n"
            
            latest = summary.get('latest_readings', {})
            if latest:
                response += f"\n🔍 Latest Reading:\n"
                response += f"⚡ Voltage: {latest.get('voltage', 'N/A')} V\n"
                response += f"🔌 Current: {latest.get('current', 'N/A')} A\n"
                response += f"📈 Power Factor: {latest.get('power_factor', 'N/A')}\n"
            
            return response
            
        except Exception as e:
            return f"Error generating today's summary: {str(e)}"
    
    def get_comprehensive_report(self, query):
        """Generate a comprehensive energy report"""
        try:
            stats = self.get_system_stats()
            summary = self.get_data_summary()
            
            response = "📋 Comprehensive Energy Management Report\n"
            response += "=" * 50 + "\n"
            
            # System Status
            response += f"🔌 System Status: {stats.get('status', 'Unknown')}\n"
            response += f"📊 Total Records: {stats.get('total_records', 0):,}\n"
            response += f"📂 Active Collections: {stats.get('total_collections', 0)}\n"
            
            # Data Summary
            data_range = summary.get('data_range', {})
            if data_range:
                response += f"\n📅 Data Range:\n"
                response += f"   Start: {data_range.get('start', 'Unknown')}\n"
                response += f"   End: {data_range.get('end', 'Unknown')}\n"
            
            # Anomalies
            anomaly_count = summary.get('anomaly_count', 0)
            response += f"\n⚠️ Anomalies: {anomaly_count} detected\n"
            
            # Latest readings
            latest = summary.get('latest_readings', {})
            if latest:
                response += f"\n🔍 Latest Readings:\n"
                response += f"   Voltage: {latest.get('voltage', 'N/A')} V\n"
                response += f"   Current: {latest.get('current', 'N/A')} A\n"
                response += f"   Power Factor: {latest.get('power_factor', 'N/A')}\n"
            
            return response
            
        except Exception as e:
            return f"Error generating comprehensive report: {str(e)}"
    
    def get_default_response(self, query):
        """Default response for unmatched queries"""
        return f"I understand you're asking about '{query}'. I can help you with energy management queries like:\n" \
               "• System status and health\n" \
               "• Latest energy readings\n" \
               "• Average voltage, current, and power factor\n" \
               "• Anomaly detection and alerts\n" \
               "• Energy consumption reports\n" \
               "• Trend analysis\n\n" \
               "Try asking something like 'What's the system status?' or 'Show me latest readings'."
    
    def get_voltage_info(self, query):
        """Get voltage-specific information"""
        return self.get_parameter_info('Voltage (V)', 'voltage', 'V')
    
    def get_current_info(self, query):
        """Get current-specific information"""
        return self.get_parameter_info('Current (A)', 'current', 'A')
    
    def get_power_factor_info(self, query):
        """Get power factor information"""
        return self.get_parameter_info('Power Factor', 'power factor', '')
    
    def get_parameter_info(self, field_name, display_name, unit):
        """Generic method to get parameter information"""
        try:
            raw_data = self.collections['raw_data']
            
            pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'avg': {'$avg': f'${field_name}'},
                        'min': {'$min': f'${field_name}'},
                        'max': {'$max': f'${field_name}'},
                        'count': {'$sum': 1}
                    }
                }
            ]
            
            result = list(raw_data.aggregate(pipeline))
            
            if not result:
                return f"No {display_name} data available."
            
            data = result[0]
            
            response = f"⚡ {display_name.title()} Analysis:\n"
            response += f"📊 Average: {data.get('avg', 0):.2f} {unit}\n"
            response += f"📈 Maximum: {data.get('max', 0):.2f} {unit}\n"
            response += f"📉 Minimum: {data.get('min', 0):.2f} {unit}\n"
            response += f"📋 Total Readings: {data.get('count', 0):,}\n"
            
            return response
            
        except Exception as e:
            return f"Error retrieving {display_name} information: {str(e)}"
    
    def get_maximum(self, query):
        """Get maximum values"""
        return self.get_extremes('max')
    
    def get_minimum(self, query):
        """Get minimum values"""
        return self.get_extremes('min')
    
    def get_extremes(self, extreme_type):
        """Get maximum or minimum values for all parameters"""
        try:
            raw_data = self.collections['raw_data']
            
            operation = '$max' if extreme_type == 'max' else '$min'
            title = 'Maximum' if extreme_type == 'max' else 'Minimum'
            
            pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'voltage': {operation: '$Voltage (V)'},
                        'current': {operation: '$Current (A)'},
                        'power_factor': {operation: '$Power Factor'},
                        'active_power': {operation: '$Active Power (W)'}
                    }
                }
            ]
            
            result = list(raw_data.aggregate(pipeline))
            
            if not result:
                return f"No data available for {title.lower()} calculations."
            
            data = result[0]
            
            response = f"📊 {title} Energy Values:\n"
            response += f"⚡ Voltage: {data.get('voltage', 0):.2f} V\n"
            response += f"🔌 Current: {data.get('current', 0):.2f} A\n"
            response += f"📈 Power Factor: {data.get('power_factor', 0):.3f}\n"
            response += f"💡 Active Power: {data.get('active_power', 0):.2f} W\n"
            
            return response
            
        except Exception as e:
            return f"Error calculating {title.lower()} values: {str(e)}"
    
    def get_trends(self, query):
        """Get trend analysis"""
        try:
            # Simple trend analysis using recent vs older data
            raw_data = self.collections['raw_data']
            total_count = raw_data.count_documents({})
            
            if total_count < 10:
                return "Insufficient data for trend analysis. Need at least 10 readings."
            
            # Get first and last 10% of data for comparison
            sample_size = max(5, total_count // 10)
            
            # Recent data
            recent_pipeline = [
                {'$sort': {'timestamp': -1}},
                {'$limit': sample_size},
                {
                    '$group': {
                        '_id': None,
                        'avg_voltage': {'$avg': '$Voltage (V)'},
                        'avg_current': {'$avg': '$Current (A)'},
                        'avg_power_factor': {'$avg': '$Power Factor'}
                    }
                }
            ]
            
            # Older data
            older_pipeline = [
                {'$sort': {'timestamp': 1}},
                {'$limit': sample_size},
                {
                    '$group': {
                        '_id': None,
                        'avg_voltage': {'$avg': '$Voltage (V)'},
                        'avg_current': {'$avg': '$Current (A)'},
                        'avg_power_factor': {'$avg': '$Power Factor'}
                    }
                }
            ]
            
            recent_result = list(raw_data.aggregate(recent_pipeline))
            older_result = list(raw_data.aggregate(older_pipeline))
            
            if not recent_result or not older_result:
                return "Unable to calculate trends due to insufficient data."
            
            recent = recent_result[0]
            older = older_result[0]
            
            response = "📈 Energy Parameter Trends:\n"
            
            # Calculate trends
            voltage_trend = recent.get('avg_voltage', 0) - older.get('avg_voltage', 0)
            current_trend = recent.get('avg_current', 0) - older.get('avg_current', 0)
            pf_trend = recent.get('avg_power_factor', 0) - older.get('avg_power_factor', 0)
            
            response += f"⚡ Voltage: {'↗️ Increasing' if voltage_trend > 0.1 else '↘️ Decreasing' if voltage_trend < -0.1 else '➡️ Stable'} ({voltage_trend:+.2f} V)\n"
            response += f"🔌 Current: {'↗️ Increasing' if current_trend > 0.1 else '↘️ Decreasing' if current_trend < -0.1 else '➡️ Stable'} ({current_trend:+.2f} A)\n"
            response += f"📈 Power Factor: {'↗️ Improving' if pf_trend > 0.01 else '↘️ Declining' if pf_trend < -0.01 else '➡️ Stable'} ({pf_trend:+.3f})\n"
            
            return response
            
        except Exception as e:
            return f"Error calculating trends: {str(e)}"
    
    def get_energy_info(self, query):
        """Get energy consumption information"""
        try:
            raw_data = self.collections['raw_data']
            
            pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'total_active_power': {'$sum': '$Active Power (W)'},
                        'avg_active_power': {'$avg': '$Active Power (W)'},
                        'max_active_power': {'$max': '$Active Power (W)'},
                        'count': {'$sum': 1}
                    }
                }
            ]
            
            result = list(raw_data.aggregate(pipeline))
            
            if not result:
                return "No energy consumption data available."
            
            data = result[0]
            
            # Estimate energy consumption (simplified calculation)
            total_power = data.get('total_active_power', 0)
            avg_power = data.get('avg_active_power', 0)
            max_power = data.get('max_active_power', 0)
            reading_count = data.get('count', 0)
            
            # Assuming readings are taken every hour for energy calculation
            estimated_energy_wh = total_power / reading_count if reading_count > 0 else 0
            estimated_energy_kwh = estimated_energy_wh / 1000
            
            response = "⚡ Energy Consumption Analysis:\n"
            response += f"💡 Average Power: {avg_power:.2f} W\n"
            response += f"📈 Peak Power: {max_power:.2f} W\n"
            response += f"🔋 Estimated Energy: {estimated_energy_kwh:.2f} kWh\n"
            response += f"📊 Based on {reading_count:,} readings\n"
            
            return response
            
        except Exception as e:
            return f"Error calculating energy consumption: {str(e)}"
    
    def get_hourly_data(self, query):
        """Get hourly aggregated data"""
        try:
            hourly_collection = self.collections['hourly_aggregates']
            hourly_count = hourly_collection.count_documents({})
            
            if hourly_count == 0:
                return "No hourly aggregated data available. Please ensure data processing is complete."
            
            # Get recent hourly data
            recent_hourly = list(hourly_collection.find().sort('timestamp', -1).limit(5))
            
            response = f"📊 Hourly Energy Data (showing {len(recent_hourly)} recent entries):\n"
            
            for i, entry in enumerate(recent_hourly, 1):
                timestamp = entry.get('timestamp', 'Unknown')
                avg_voltage = entry.get('avg_voltage', 'N/A')
                avg_current = entry.get('avg_current', 'N/A')
                avg_power = entry.get('avg_active_power', 'N/A')
                
                response += f"{i}. {timestamp}: V={avg_voltage}V, I={avg_current}A, P={avg_power}W\n"
            
            return response
            
        except Exception as e:
            return f"Error retrieving hourly data: {str(e)}"
    
    def get_system_stats(self):
        """Get system statistics for Flask app - collection counts, total records"""
        try:
            stats = {
                'total_collections': 0,
                'total_records': 0,
                'collections': {}
            }
            
            for name, collection in self.collections.items():
                count = collection.count_documents({})
                stats['collections'][name] = count
                stats['total_records'] += count
                if count > 0:
                    stats['total_collections'] += 1
            
            stats['status'] = 'Connected' if stats['total_records'] > 0 else 'No Data'
            return stats
            
        except Exception as e:
            return {
                'total_collections': 0,
                'total_records': 0,
                'collections': {},
                'status': f'Error: {str(e)}'
            }
    
    def get_data_summary(self):
        """Get comprehensive data summary - ranges, latest data, anomaly counts"""
        try:
            summary = {
                'data_range': {},
                'latest_readings': {},
                'anomaly_count': 0,
                'total_records': 0
            }
            
            # Get data range from raw data
            raw_data = self.collections['raw_data']
            total_count = raw_data.count_documents({})
            summary['total_records'] = total_count
            
            if total_count > 0:
                # Get latest reading
                latest = raw_data.find().sort('timestamp', -1).limit(1)
                latest_doc = next(latest, None)
                if latest_doc:
                    summary['latest_readings'] = {
                        'timestamp': latest_doc.get('timestamp', 'Unknown'),
                        'voltage': latest_doc.get('Voltage (V)', 0),
                        'current': latest_doc.get('Current (A)', 0),
                        'power_factor': latest_doc.get('Power Factor', 0)
                    }
                
                # Get data range
                first = raw_data.find().sort('timestamp', 1).limit(1)
                first_doc = next(first, None)
                if first_doc and latest_doc:
                    summary['data_range'] = {
                        'start': first_doc.get('timestamp', 'Unknown'),
                        'end': latest_doc.get('timestamp', 'Unknown')
                    }
            
            # Get anomaly count
            anomaly_count = self.collections['anomalies'].count_documents({})
            summary['anomaly_count'] = anomaly_count
            
            return summary
            
        except Exception as e:
            return {
                'data_range': {},
                'latest_readings': {},
                'anomaly_count': 0,
                'total_records': 0,
                'error': str(e)
            }
    
    def process_query(self, user_query):
        """Alias for search method - returns string response for Flask"""
        result = self.search(user_query)
        return result.get('answer', 'Sorry, I could not process your query.')
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()

# Test the query engine
if __name__ == "__main__":
    engine = EMSQueryEngine()
    
    test_queries = [
        "What is the system status?",
        "Show me the latest readings",
        "What's the average voltage?",
        "Are there any anomalies?",
        "Give me a comprehensive report",
        "Show me energy trends",
        "What's the maximum current?",
        "Tell me about power factor"
    ]
    
    print("🧪 Testing EMS Query Engine")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        result = engine.search(query)
        print(f"   Answer: {result.get('answer', 'No answer')[:100]}...")
        print(f"   Method: {result.get('method', 'unknown')}")
        print(f"   Confidence: {result.get('confidence', 0):.0%}")
    
    engine.close()
