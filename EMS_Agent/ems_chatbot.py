"""
EMS Agent Chatbot - Intelligent Energy Management System Chatbot

This chatbot interface provides natural language conversation capabilities
with comprehensive MongoDB data analysis for energy management.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import re
import numpy as np
from pymongo import MongoClient
from pymongo.server_api import ServerApi

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

# Import existing EMS components
from ems_search import EMSQueryEngine
from config import MONGODB_URI, MONGODB_DATABASE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EMSChatbotAI:
    """Intelligent EMS Chatbot with MongoDB Data Analysis"""
    
    def __init__(self):
        self.query_engine = EMSQueryEngine()
        self.client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        self.db = self.client[MONGODB_DATABASE]
        self.conversation_history = []
        
        # Enhanced patterns for better question understanding
        self.patterns = {
            'greetings': [
                r'(hi|hello|hey|good morning|good afternoon|good evening)',
                r'(how are you|what\'s up|how\'s it going)'
            ],
            'system_status': [
                r'(system status|health|operational|running|working)',
                r'(is everything okay|all systems|status check)'
            ],
            'energy_analysis': [
                r'(energy consumption|power usage|electricity usage)',
                r'(how much energy|energy costs|power costs)',
                r'(energy efficiency|power efficiency|consumption patterns)'
            ],
            'voltage_analysis': [
                r'(voltage|voltage levels|voltage readings)',
                r'(voltage stability|voltage quality|voltage problems)',
                r'(electrical quality|grid quality)'
            ],
            'current_analysis': [
                r'(current|current readings|amperage)',
                r'(current levels|electrical current|load current)'
            ],
            'power_factor': [
                r'(power factor|reactive power|apparent power)',
                r'(pf|power quality|electrical efficiency)'
            ],
            'anomalies': [
                r'(anomalies|anomaly|problems|issues|alerts)',
                r'(anything wrong|abnormal|unusual|spikes|outliers)'
            ],
            'trends': [
                r'(trends|trending|patterns|changes over time)',
                r'(increasing|decreasing|improving|getting worse)'
            ],
            'latest_data': [
                r'(latest|recent|current|newest|last)',
                r'(what\'s the latest|show me recent|current readings)'
            ],
            'historical_data': [
                r'(historical|history|past|previous|earlier)',
                r'(what happened|show me data from|historical trends)'
            ],
            'predictions': [
                r'(predict|forecast|future|what will happen)',
                r'(prediction|forecasting|estimate|project)'
            ],
            'recommendations': [
                r'(recommend|suggestion|advice|what should|optimize)',
                r'(how to improve|best practices|optimization)'
            ],
            'costs': [
                r'(cost|costs|money|billing|bill|expenses)',
                r'(how much|price|financial|savings)'
            ],
            'equipment': [
                r'(equipment|devices|meters|sensors|hardware)',
                r'(device status|equipment health|meter readings)'
            ],
            'comprehensive': [
                r'(comprehensive|complete|full|detailed|everything)',
                r'(full report|complete analysis|detailed summary)'
            ]
        }
        
        # Response templates for different contexts
        self.templates = {
            'greeting': [
                "👋 Hello! I'm your EMS Agent assistant. I can help you analyze energy data, check system status, and provide insights about your energy consumption. What would you like to know?",
                "🔋 Hi there! I'm here to help with your Energy Management System. I can analyze data from MongoDB and answer questions about power consumption, efficiency, and system health. How can I assist you today?",
                "⚡ Welcome to the EMS Agent! I can provide real-time analysis of your energy data, detect anomalies, and help optimize your power usage. What information do you need?"
            ],
            'acknowledgment': [
                "Let me analyze the energy data for you...",
                "Checking the MongoDB database for the latest information...",
                "Analyzing your energy consumption patterns...",
                "Gathering insights from the system data..."
            ]
        }
    
    async def analyze_question_intent(self, question: str) -> Dict[str, Any]:
        """Analyze user question to understand intent and extract parameters"""
        question_lower = question.lower()
        
        intents = []
        confidence_scores = {}
        
        # Check each pattern category
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    intents.append(intent)
                    confidence_scores[intent] = confidence_scores.get(intent, 0) + 1
        
        # Determine primary intent
        primary_intent = max(confidence_scores.keys(), key=lambda k: confidence_scores[k]) if confidence_scores else 'general'
        
        # Extract specific parameters
        parameters = {}
        
        # Time-based parameters
        if re.search(r'(today|daily)', question_lower):
            parameters['timeframe'] = 'today'
        elif re.search(r'(hourly|hour)', question_lower):
            parameters['timeframe'] = 'hourly'
        elif re.search(r'(weekly|week)', question_lower):
            parameters['timeframe'] = 'weekly'
        elif re.search(r'(monthly|month)', question_lower):
            parameters['timeframe'] = 'monthly'
        
        # Specific metric parameters
        if re.search(r'(average|avg|mean)', question_lower):
            parameters['metric_type'] = 'average'
        elif re.search(r'(maximum|max|peak|highest)', question_lower):
            parameters['metric_type'] = 'maximum'
        elif re.search(r'(minimum|min|lowest)', question_lower):
            parameters['metric_type'] = 'minimum'
        elif re.search(r'(total|sum)', question_lower):
            parameters['metric_type'] = 'total'
        
        # Device-specific parameters
        device_match = re.search(r'(meter|device|sensor|equipment)\s*(\w+)', question_lower)
        if device_match:
            parameters['device'] = device_match.group(2)
        
        return {
            'primary_intent': primary_intent,
            'all_intents': list(set(intents)),
            'confidence_scores': confidence_scores,
            'parameters': parameters,
            'original_question': question
        }
    
    async def get_comprehensive_energy_analysis(self) -> Dict[str, Any]:
        """Get comprehensive energy analysis from MongoDB"""
        try:
            collection = self.db["ems_raw_data"]
            cursor = collection.find().sort("timestamp", -1).limit(100)
            data = list(cursor)
            
            if not data:
                return {"error": "No energy data available"}
            
            # Power analysis
            power_values = []
            voltage_values = []
            current_values = []
            pf_values = []
            
            for doc in data:
                # Handle different field name variations
                power = (doc.get("active_power_(kw)") or 
                        doc.get("Active Power (W)") or 
                        doc.get("power_consumption") or 0)
                if power and power > 0:
                    power_values.append(float(power))
                
                voltage = (doc.get("voltage_(v)") or 
                          doc.get("Voltage (V)") or 
                          doc.get("voltage") or 0)
                if voltage and voltage > 0:
                    voltage_values.append(float(voltage))
                
                current = (doc.get("current_(a)") or 
                          doc.get("Current (A)") or 
                          doc.get("current") or 0)
                if current and current > 0:
                    current_values.append(float(current))
                
                pf = (doc.get("power_factor") or 
                     doc.get("Power Factor") or 1.0)
                if pf and 0 < pf <= 1:
                    pf_values.append(float(pf))
            
            # Calculate statistics
            analysis = {
                'power_analysis': {
                    'avg_power': np.mean(power_values) if power_values else 0,
                    'max_power': np.max(power_values) if power_values else 0,
                    'min_power': np.min(power_values) if power_values else 0,
                    'total_energy': sum(power_values) * 0.001 if power_values else 0,  # Convert to kWh
                    'readings_count': len(power_values)
                },
                'voltage_analysis': {
                    'avg_voltage': np.mean(voltage_values) if voltage_values else 0,
                    'max_voltage': np.max(voltage_values) if voltage_values else 0,
                    'min_voltage': np.min(voltage_values) if voltage_values else 0,
                    'voltage_stability': np.std(voltage_values) if voltage_values else 0,
                    'readings_count': len(voltage_values)
                },
                'current_analysis': {
                    'avg_current': np.mean(current_values) if current_values else 0,
                    'max_current': np.max(current_values) if current_values else 0,
                    'min_current': np.min(current_values) if current_values else 0,
                    'current_variation': np.std(current_values) if current_values else 0,
                    'readings_count': len(current_values)
                },
                'power_factor_analysis': {
                    'avg_power_factor': np.mean(pf_values) if pf_values else 1.0,
                    'min_power_factor': np.min(pf_values) if pf_values else 1.0,
                    'power_quality': 'Excellent' if np.mean(pf_values) > 0.95 else 'Good' if np.mean(pf_values) > 0.85 else 'Poor' if pf_values else 'Unknown',
                    'readings_count': len(pf_values)
                },
                'efficiency_metrics': {
                    'load_factor': (np.mean(power_values) / np.max(power_values)) if power_values and np.max(power_values) > 0 else 0,
                    'energy_intensity': np.mean(power_values) if power_values else 0,
                    'peak_demand': np.max(power_values) if power_values else 0
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def detect_anomalies_advanced(self) -> Dict[str, Any]:
        """Advanced anomaly detection using statistical methods"""
        try:
            collection = self.db["ems_raw_data"]
            cursor = collection.find().sort("timestamp", -1).limit(200)
            data = list(cursor)
            
            if len(data) < 10:
                return {"anomalies": [], "count": 0, "analysis": "Insufficient data for anomaly detection"}
            
            anomalies = []
            
            # Extract values for analysis
            power_values = [doc.get("active_power_(kw)", 0) for doc in data]
            voltage_values = [doc.get("voltage_(v)", 230) for doc in data]
            current_values = [doc.get("current_(a)", 0) for doc in data]
            
            # Statistical anomaly detection (Z-score method)
            def detect_outliers(values, threshold=2.5):
                if len(values) < 3:
                    return []
                mean_val = np.mean(values)
                std_val = np.std(values)
                if std_val == 0:
                    return []
                z_scores = [(x - mean_val) / std_val for x in values]
                return [i for i, z in enumerate(z_scores) if abs(z) > threshold]
            
            # Detect power anomalies
            power_anomalies = detect_outliers(power_values)
            for idx in power_anomalies:
                anomalies.append({
                    'type': 'power_anomaly',
                    'value': power_values[idx],
                    'severity': 'high' if abs(power_values[idx] - np.mean(power_values)) > 2 * np.std(power_values) else 'medium',
                    'description': f"Unusual power consumption: {power_values[idx]:.2f} kW",
                    'timestamp': data[idx].get('timestamp', 'Unknown'),
                    'z_score': abs((power_values[idx] - np.mean(power_values)) / np.std(power_values))
                })
            
            # Detect voltage anomalies
            voltage_anomalies = detect_outliers(voltage_values)
            for idx in voltage_anomalies:
                anomalies.append({
                    'type': 'voltage_anomaly',
                    'value': voltage_values[idx],
                    'severity': 'high' if voltage_values[idx] < 200 or voltage_values[idx] > 250 else 'medium',
                    'description': f"Voltage deviation: {voltage_values[idx]:.1f}V",
                    'timestamp': data[idx].get('timestamp', 'Unknown'),
                    'z_score': abs((voltage_values[idx] - np.mean(voltage_values)) / np.std(voltage_values))
                })
            
            # Detect current anomalies
            current_anomalies = detect_outliers(current_values)
            for idx in current_anomalies:
                anomalies.append({
                    'type': 'current_anomaly',
                    'value': current_values[idx],
                    'severity': 'high' if current_values[idx] > 20 else 'medium',
                    'description': f"Current spike: {current_values[idx]:.2f}A",
                    'timestamp': data[idx].get('timestamp', 'Unknown'),
                    'z_score': abs((current_values[idx] - np.mean(current_values)) / np.std(current_values))
                })
            
            # Sort by severity and z-score
            anomalies.sort(key=lambda x: (-x.get('z_score', 0), x.get('severity') == 'high'))
            
            return {
                'anomalies': anomalies[:10],  # Return top 10
                'count': len(anomalies),
                'analysis': f"Detected {len(anomalies)} anomalies in {len(data)} readings",
                'summary': {
                    'high_severity': len([a for a in anomalies if a.get('severity') == 'high']),
                    'medium_severity': len([a for a in anomalies if a.get('severity') == 'medium']),
                    'power_anomalies': len([a for a in anomalies if a.get('type') == 'power_anomaly']),
                    'voltage_anomalies': len([a for a in anomalies if a.get('type') == 'voltage_anomaly']),
                    'current_anomalies': len([a for a in anomalies if a.get('type') == 'current_anomaly'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {"anomalies": [], "count": 0, "analysis": f"Anomaly detection failed: {str(e)}"}
    
    async def generate_intelligent_response(self, question: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate intelligent response based on question intent and MongoDB data"""
        
        primary_intent = intent_analysis['primary_intent']
        parameters = intent_analysis['parameters']
        
        try:
            # Handle different types of questions
            if primary_intent == 'greetings':
                import random
                return random.choice(self.templates['greeting'])
            
            elif primary_intent == 'system_status':
                # Use existing query engine
                result = self.query_engine.search("system status")
                system_info = result.get('answer', '')
                
                # Add real-time MongoDB analysis
                analysis = await self.get_comprehensive_energy_analysis()
                if 'error' not in analysis:
                    power_data = analysis['power_analysis']
                    voltage_data = analysis['voltage_analysis']
                    
                    enhanced_response = f"""🔋 **EMS SYSTEM STATUS**

{system_info}

📊 **REAL-TIME ANALYSIS:**
• Power Consumption: {power_data['avg_power']:.2f} kW (Average), {power_data['max_power']:.2f} kW (Peak)
• Voltage Stability: {voltage_data['avg_voltage']:.1f}V ± {voltage_data['voltage_stability']:.1f}V
• Total Energy: {power_data['total_energy']:.2f} kWh
• Data Points: {power_data['readings_count']} recent readings analyzed

✅ All systems operational and data analysis capabilities are functioning normally."""
                    return enhanced_response
                else:
                    return f"{system_info}\n\n⚠️ Note: {analysis['error']}"
            
            elif primary_intent == 'energy_analysis':
                analysis = await self.get_comprehensive_energy_analysis()
                if 'error' in analysis:
                    return f"❌ Unable to analyze energy data: {analysis['error']}"
                
                power_data = analysis['power_analysis']
                efficiency_data = analysis['efficiency_metrics']
                
                # Calculate costs (assuming $0.12/kWh)
                cost_per_kwh = 0.12
                total_cost = power_data['total_energy'] * cost_per_kwh
                daily_cost = total_cost / 7  # Assuming weekly data
                
                response = f"""⚡ **ENERGY CONSUMPTION ANALYSIS**

📈 **POWER CONSUMPTION:**
• Average Power: {power_data['avg_power']:.2f} kW
• Peak Demand: {power_data['max_power']:.2f} kW
• Minimum Load: {power_data['min_power']:.2f} kW
• Total Energy: {power_data['total_energy']:.2f} kWh

💰 **COST ANALYSIS:**
• Estimated Total Cost: ${total_cost:.2f}
• Daily Average: ${daily_cost:.2f}
• Rate: ${cost_per_kwh}/kWh

📊 **EFFICIENCY METRICS:**
• Load Factor: {efficiency_data['load_factor']:.1%}
• Energy Intensity: {efficiency_data['energy_intensity']:.2f} kW
• Peak Demand: {efficiency_data['peak_demand']:.2f} kW

💡 **INSIGHTS:**
• {'High efficiency - well-balanced load' if efficiency_data['load_factor'] > 0.7 else 'Moderate efficiency - consider load balancing' if efficiency_data['load_factor'] > 0.5 else 'Low efficiency - significant optimization potential'}
• Based on {power_data['readings_count']} data points"""
                
                return response
            
            elif primary_intent == 'voltage_analysis':
                analysis = await self.get_comprehensive_energy_analysis()
                if 'error' in analysis:
                    return f"❌ Unable to analyze voltage data: {analysis['error']}"
                
                voltage_data = analysis['voltage_analysis']
                
                # Voltage quality assessment
                avg_v = voltage_data['avg_voltage']
                stability = voltage_data['voltage_stability']
                
                if 220 <= avg_v <= 240 and stability < 2:
                    quality = "🟢 Excellent"
                elif 210 <= avg_v <= 250 and stability < 5:
                    quality = "🟡 Good"
                else:
                    quality = "🔴 Poor"
                
                response = f"""⚡ **VOLTAGE ANALYSIS**

📊 **VOLTAGE STATISTICS:**
• Average Voltage: {avg_v:.1f}V
• Maximum Voltage: {voltage_data['max_voltage']:.1f}V
• Minimum Voltage: {voltage_data['min_voltage']:.1f}V
• Voltage Stability: ±{stability:.1f}V

🔍 **QUALITY ASSESSMENT:**
• Grid Quality: {quality}
• Voltage Range: {voltage_data['max_voltage'] - voltage_data['min_voltage']:.1f}V
• Standard Deviation: {stability:.2f}V

💡 **ANALYSIS:**
• {'Voltage levels are within optimal range (220-240V)' if 220 <= avg_v <= 240 else 'Voltage levels need attention - outside optimal range'}
• {'Low voltage variation indicates stable supply' if stability < 3 else 'High voltage variation may indicate supply issues'}
• Based on {voltage_data['readings_count']} measurements"""
                
                return response
            
            elif primary_intent == 'anomalies':
                anomaly_data = await self.detect_anomalies_advanced()
                
                if anomaly_data['count'] == 0:
                    return """✅ **NO ANOMALIES DETECTED**

🔍 **ANOMALY ANALYSIS:**
• All energy parameters are within normal ranges
• No unusual spikes or deviations detected
• System operating normally

📊 **ANALYSIS STATUS:**
• Statistical analysis completed
• Monitoring continues for real-time detection
• All readings appear consistent and stable"""
                
                summary = anomaly_data['summary']
                anomalies = anomaly_data['anomalies'][:5]  # Top 5
                
                response = f"""🚨 **ANOMALY DETECTION REPORT**

📊 **SUMMARY:**
• Total Anomalies: {anomaly_data['count']}
• High Severity: {summary['high_severity']}
• Medium Severity: {summary['medium_severity']}

🔍 **BREAKDOWN:**
• Power Anomalies: {summary['power_anomalies']}
• Voltage Anomalies: {summary['voltage_anomalies']}
• Current Anomalies: {summary['current_anomalies']}

⚠️ **TOP ANOMALIES:**"""
                
                for i, anomaly in enumerate(anomalies, 1):
                    severity_icon = "🔴" if anomaly['severity'] == 'high' else "🟡"
                    response += f"\n{i}. {severity_icon} {anomaly['description']} (Score: {anomaly.get('z_score', 0):.1f})"
                
                response += f"\n\n💡 **RECOMMENDATION:**\n• {'Immediate investigation required for high-severity anomalies' if summary['high_severity'] > 0 else 'Monitor medium-severity anomalies and investigate patterns'}"
                
                return response
            
            elif primary_intent == 'trends':
                # Use existing trend analysis
                result = self.query_engine.search("trends")
                trend_info = result.get('answer', '')
                
                # Add enhanced analysis
                analysis = await self.get_comprehensive_energy_analysis()
                if 'error' not in analysis:
                    power_data = analysis['power_analysis']
                    response = f"""📈 **ENERGY TRENDS ANALYSIS**

{trend_info}

🔍 **ADDITIONAL INSIGHTS:**
• Load Factor: {analysis['efficiency_metrics']['load_factor']:.1%}
• Peak-to-Average Ratio: {power_data['max_power']/power_data['avg_power']:.1f}
• Energy Variation: {'Low' if power_data['max_power']/power_data['avg_power'] < 1.5 else 'Moderate' if power_data['max_power']/power_data['avg_power'] < 2.0 else 'High'}

💡 **TREND INSIGHTS:**
• {'Stable consumption pattern' if power_data['max_power']/power_data['avg_power'] < 1.5 else 'Variable consumption - consider load scheduling'}"""
                    return response
                else:
                    return trend_info
            
            elif primary_intent == 'latest_data':
                result = self.query_engine.search("latest readings")
                latest_info = result.get('answer', '')
                
                # Add real-time enhancement
                analysis = await self.get_comprehensive_energy_analysis()
                if 'error' not in analysis:
                    power_data = analysis['power_analysis']
                    voltage_data = analysis['voltage_analysis']
                    current_data = analysis['current_analysis']
                    pf_data = analysis['power_factor_analysis']
                    
                    enhanced_response = f"""{latest_info}

📊 **CURRENT SYSTEM METRICS:**
• Power: {power_data['avg_power']:.2f} kW (Average from {power_data['readings_count']} readings)
• Voltage: {voltage_data['avg_voltage']:.1f}V ± {voltage_data['voltage_stability']:.1f}V
• Current: {current_data['avg_current']:.2f}A
• Power Factor: {pf_data['avg_power_factor']:.3f} ({pf_data['power_quality']})

🕐 **Data Freshness:** Analysis based on {power_data['readings_count']} recent readings"""
                    return enhanced_response
                else:
                    return latest_info
            
            elif primary_intent == 'comprehensive':
                # Generate full comprehensive report
                analysis = await self.get_comprehensive_energy_analysis()
                anomalies = await self.detect_anomalies_advanced()
                
                if 'error' in analysis:
                    return f"❌ Unable to generate comprehensive report: {analysis['error']}"
                
                power_data = analysis['power_analysis']
                voltage_data = analysis['voltage_analysis']
                current_data = analysis['current_analysis']
                pf_data = analysis['power_factor_analysis']
                efficiency_data = analysis['efficiency_metrics']
                
                response = f"""📋 **COMPREHENSIVE ENERGY MANAGEMENT REPORT**
{'='*60}

⚡ **POWER CONSUMPTION ANALYSIS:**
• Average Power: {power_data['avg_power']:.2f} kW
• Peak Demand: {power_data['max_power']:.2f} kW
• Total Energy: {power_data['total_energy']:.2f} kWh
• Load Factor: {efficiency_data['load_factor']:.1%}

🔌 **ELECTRICAL QUALITY:**
• Voltage: {voltage_data['avg_voltage']:.1f}V (Range: {voltage_data['min_voltage']:.1f}-{voltage_data['max_voltage']:.1f}V)
• Current: {current_data['avg_current']:.2f}A (Max: {current_data['max_current']:.2f}A)
• Power Factor: {pf_data['avg_power_factor']:.3f} ({pf_data['power_quality']})
• Voltage Stability: ±{voltage_data['voltage_stability']:.1f}V

📊 **EFFICIENCY METRICS:**
• System Efficiency: {efficiency_data['load_factor']*100:.1f}%
• Peak-to-Average Ratio: {power_data['max_power']/power_data['avg_power']:.2f}
• Energy Intensity: {efficiency_data['energy_intensity']:.2f} kW

🚨 **ANOMALY STATUS:**
• Total Anomalies: {anomalies['count']}
• High Severity: {anomalies['summary']['high_severity'] if 'summary' in anomalies else 0}
• Status: {'⚠️ Requires attention' if anomalies['count'] > 5 else '✅ Normal operation'}

💰 **COST ESTIMATION:**
• Estimated Daily Cost: ${power_data['total_energy']*0.12/7:.2f}
• Monthly Projection: ${power_data['total_energy']*0.12*30/7:.2f}

💡 **RECOMMENDATIONS:**
• {'Excellent system performance - continue monitoring' if efficiency_data['load_factor'] > 0.7 and pf_data['avg_power_factor'] > 0.9 else 'Consider power factor correction' if pf_data['avg_power_factor'] < 0.85 else 'Implement load balancing strategies'}
• {'Voltage quality is optimal' if 220 <= voltage_data['avg_voltage'] <= 240 else 'Check voltage regulation systems'}

📈 **DATA QUALITY:**
• Power Readings: {power_data['readings_count']} data points
• Voltage Readings: {voltage_data['readings_count']} data points
• Analysis Confidence: {'High' if power_data['readings_count'] > 50 else 'Medium' if power_data['readings_count'] > 20 else 'Low'}

🕐 **Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
                
                return response
            
            elif primary_intent == 'costs':
                analysis = await self.get_comprehensive_energy_analysis()
                if 'error' in analysis:
                    return f"❌ Unable to analyze costs: {analysis['error']}"
                
                power_data = analysis['power_analysis']
                
                # Cost calculations
                rate_per_kwh = 0.12
                total_cost = power_data['total_energy'] * rate_per_kwh
                daily_avg = total_cost / 7
                monthly_projection = daily_avg * 30
                
                # Peak demand charges (typical utility structure)
                peak_demand_charge = power_data['max_power'] * 15  # $15/kW
                
                response = f"""💰 **ENERGY COST ANALYSIS**

💵 **CURRENT COSTS:**
• Total Energy Cost: ${total_cost:.2f}
• Daily Average: ${daily_avg:.2f}
• Monthly Projection: ${monthly_projection:.2f}

⚡ **DEMAND CHARGES:**
• Peak Demand: {power_data['max_power']:.2f} kW
• Demand Charge: ${peak_demand_charge:.2f}
• Total Monthly Est.: ${monthly_projection + peak_demand_charge:.2f}

📊 **COST BREAKDOWN:**
• Energy Charges: ${monthly_projection:.2f}/month
• Demand Charges: ${peak_demand_charge:.2f}/month
• Rate: ${rate_per_kwh}/kWh

💡 **SAVINGS OPPORTUNITIES:**
• {'Peak shaving could save $' + str(power_data['max_power']*0.2*15) + '/month' if power_data['max_power'] > power_data['avg_power']*1.5 else 'Current demand profile is efficient'}
• {'Power factor improvement needed' if analysis['power_factor_analysis']['avg_power_factor'] < 0.85 else 'Good power factor - no reactive power penalties'}

📈 **EFFICIENCY IMPACT:**
• Load Factor: {analysis['efficiency_metrics']['load_factor']:.1%}
• Potential Savings: ${'%.2f' % (daily_avg * 0.15 if analysis['efficiency_metrics']['load_factor'] < 0.6 else daily_avg * 0.05)}/day with optimization"""
                
                return response
            
            else:
                # General question - use existing query engine
                result = self.query_engine.search(question)
                base_answer = result.get('answer', 'I can help you analyze energy data. Try asking about system status, energy consumption, anomalies, or trends.')
                
                # Try to enhance with real-time data
                try:
                    analysis = await self.get_comprehensive_energy_analysis()
                    if 'error' not in analysis:
                        power_data = analysis['power_analysis']
                        enhanced_answer = f"""{base_answer}

📊 **Current System Summary:**
• Power: {power_data['avg_power']:.2f} kW (Average), {power_data['max_power']:.2f} kW (Peak)
• Energy: {power_data['total_energy']:.2f} kWh total
• Efficiency: {analysis['efficiency_metrics']['load_factor']:.1%} load factor

💡 **Ask me about:** energy costs, anomalies, trends, voltage analysis, system optimization, or comprehensive reports!"""
                        return enhanced_answer
                except:
                    pass
                
                return base_answer
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"❌ I encountered an error while analyzing your question: {str(e)}. Please try rephrasing your question or ask about system status, energy consumption, anomalies, or trends."
    
    async def process_chat_message(self, message: str) -> Dict[str, Any]:
        """Process chat message and return response with metadata"""
        start_time = time.time()
        
        # Analyze the question
        intent_analysis = await self.analyze_question_intent(message)
        
        # Generate response
        response = await self.generate_intelligent_response(message, intent_analysis)
        
        # Add to conversation history
        conversation_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_message': message,
            'bot_response': response,
            'intent_analysis': intent_analysis,
            'processing_time': time.time() - start_time
        }
        
        self.conversation_history.append(conversation_entry)
        
        # Keep only last 50 conversations
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
        
        return {
            'response': response,
            'intent': intent_analysis['primary_intent'],
            'confidence': max(intent_analysis['confidence_scores'].values()) if intent_analysis['confidence_scores'] else 0,
            'processing_time': conversation_entry['processing_time'],
            'timestamp': conversation_entry['timestamp']
        }


class EMSChatbotApp:
    """FastAPI application for EMS Chatbot"""
    
    def __init__(self):
        self.app = self._create_app()
        self.chatbot = EMSChatbotAI()
        self.active_connections = set()
    
    def _create_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title="EMS Agent Chatbot",
            description="Intelligent Energy Management System Chatbot with MongoDB Data Analysis",
            version="1.0.0"
        )
        
        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.get("/", response_class=HTMLResponse)
        async def chatbot_interface():
            """EMS Chatbot Interface"""
            return self._create_chatbot_html()
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "EMS Chatbot",
                "timestamp": datetime.now().isoformat(),
                "active_connections": len(self.active_connections)
            }
        
        @app.websocket("/chat")
        async def chat_websocket(websocket: WebSocket):
            """WebSocket endpoint for chat"""
            await websocket.accept()
            self.active_connections.add(websocket)
            
            try:
                # Send welcome message
                welcome_response = await self.chatbot.process_chat_message("hello")
                await websocket.send_json({
                    'type': 'bot_message',
                    'message': welcome_response['response'],
                    'intent': welcome_response['intent'],
                    'timestamp': welcome_response['timestamp']
                })
                
                while True:
                    # Receive message from client
                    data = await websocket.receive_json()
                    user_message = data.get('message', '')
                    
                    if user_message.strip():
                        # Process the message
                        response_data = await self.chatbot.process_chat_message(user_message)
                        
                        # Send response
                        await websocket.send_json({
                            'type': 'bot_message',
                            'message': response_data['response'],
                            'intent': response_data['intent'],
                            'confidence': response_data['confidence'],
                            'processing_time': response_data['processing_time'],
                            'timestamp': response_data['timestamp']
                        })
                    
            except WebSocketDisconnect:
                self.active_connections.discard(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_json({
                    'type': 'error',
                    'message': 'Sorry, I encountered an error. Please try again.'
                })
                self.active_connections.discard(websocket)
        
        return app
    
    def _create_chatbot_html(self) -> str:
        """Create chatbot interface HTML"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>EMS Agent Chatbot - Intelligent Energy Management Assistant</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }
                
                .chat-container {
                    width: 90%;
                    max-width: 800px;
                    height: 90vh;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                }
                
                .chat-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    position: relative;
                }
                
                .chat-header h1 {
                    margin: 0;
                    font-size: 1.8em;
                    font-weight: 600;
                }
                
                .chat-header p {
                    margin: 5px 0 0 0;
                    opacity: 0.9;
                    font-size: 0.95em;
                }
                
                .status-indicator {
                    position: absolute;
                    top: 15px;
                    right: 20px;
                    width: 12px;
                    height: 12px;
                    background: #4ade80;
                    border-radius: 50%;
                    animation: pulse 2s infinite;
                }
                
                @keyframes pulse {
                    0% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); }
                    70% { box-shadow: 0 0 0 10px rgba(74, 222, 128, 0); }
                    100% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
                }
                
                .chat-messages {
                    flex: 1;
                    padding: 20px;
                    overflow-y: auto;
                    background: #f8fafc;
                }
                
                .message {
                    margin-bottom: 20px;
                    animation: fadeIn 0.3s ease-in;
                }
                
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                .message.user {
                    display: flex;
                    justify-content: flex-end;
                }
                
                .message.bot {
                    display: flex;
                    justify-content: flex-start;
                }
                
                .message-content {
                    max-width: 70%;
                    padding: 15px 20px;
                    border-radius: 18px;
                    position: relative;
                    word-wrap: break-word;
                }
                
                .message.user .message-content {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-bottom-right-radius: 4px;
                }
                
                .message.bot .message-content {
                    background: white;
                    color: #1f2937;
                    border: 1px solid #e5e7eb;
                    border-bottom-left-radius: 4px;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                }
                
                .message-meta {
                    font-size: 0.75em;
                    color: #6b7280;
                    margin-top: 5px;
                    text-align: right;
                }
                
                .message.bot .message-meta {
                    text-align: left;
                }
                
                .bot-avatar {
                    width: 32px;
                    height: 32px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 10px;
                    margin-top: 5px;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    flex-shrink: 0;
                }
                
                .chat-input-container {
                    padding: 20px;
                    background: white;
                    border-top: 1px solid #e5e7eb;
                }
                
                .chat-input-form {
                    display: flex;
                    gap: 10px;
                }
                
                .chat-input {
                    flex: 1;
                    padding: 15px 20px;
                    border: 1px solid #d1d5db;
                    border-radius: 25px;
                    font-size: 16px;
                    outline: none;
                    transition: border-color 0.2s;
                }
                
                .chat-input:focus {
                    border-color: #667eea;
                    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                }
                
                .send-button {
                    width: 50px;
                    height: 50px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: transform 0.2s;
                    font-size: 18px;
                }
                
                .send-button:hover {
                    transform: scale(1.05);
                }
                
                .send-button:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                    transform: none;
                }
                
                .typing-indicator {
                    display: none;
                    align-items: center;
                    margin-bottom: 15px;
                }
                
                .typing-indicator .bot-avatar {
                    margin-bottom: 0;
                }
                
                .typing-dots {
                    background: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 18px;
                    padding: 15px 20px;
                    margin-left: 10px;
                }
                
                .typing-dots span {
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    background: #9ca3af;
                    border-radius: 50%;
                    margin-right: 5px;
                    animation: typing 1.4s infinite;
                }
                
                .typing-dots span:nth-child(1) { animation-delay: 0s; }
                .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
                .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
                
                @keyframes typing {
                    0%, 80%, 100% { transform: scale(1); opacity: 0.5; }
                    40% { transform: scale(1.2); opacity: 1; }
                }
                
                .suggestions {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    margin-bottom: 15px;
                }
                
                .suggestion-chip {
                    background: #f3f4f6;
                    border: 1px solid #d1d5db;
                    border-radius: 20px;
                    padding: 8px 16px;
                    font-size: 14px;
                    cursor: pointer;
                    transition: all 0.2s;
                    color: #374151;
                }
                
                .suggestion-chip:hover {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-color: transparent;
                }
                
                /* Mobile responsiveness */
                @media (max-width: 768px) {
                    .chat-container {
                        width: 100%;
                        height: 100vh;
                        border-radius: 0;
                    }
                    
                    .message-content {
                        max-width: 85%;
                    }
                    
                    .chat-header h1 {
                        font-size: 1.5em;
                    }
                }
                
                /* Code formatting */
                .message-content pre {
                    background: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 6px;
                    padding: 12px;
                    margin: 10px 0;
                    overflow-x: auto;
                    font-family: 'Monaco', 'Consolas', monospace;
                    font-size: 14px;
                }
                
                .message-content code {
                    background: #f1f3f4;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-family: 'Monaco', 'Consolas', monospace;
                    font-size: 14px;
                }
                
                /* Lists and formatting */
                .message-content ul, .message-content ol {
                    margin: 10px 0;
                    padding-left: 20px;
                }
                
                .message-content li {
                    margin: 5px 0;
                }
                
                .message-content h3, .message-content h4 {
                    margin: 15px 0 10px 0;
                    color: #1f2937;
                }
                
                .message-content strong {
                    font-weight: 600;
                }
            </style>
        </head>
        <body>
            <div class="chat-container">
                <div class="chat-header">
                    <div class="status-indicator" id="statusIndicator"></div>
                    <h1>🔋 EMS Agent Assistant</h1>
                    <p>Intelligent Energy Management System with MongoDB Analysis</p>
                </div>
                
                <div class="chat-messages" id="chatMessages">
                    <div class="suggestions">
                        <div class="suggestion-chip" onclick="sendSuggestion('What is the current system status?')">📊 System Status</div>
                        <div class="suggestion-chip" onclick="sendSuggestion('Analyze my energy consumption')">⚡ Energy Analysis</div>
                        <div class="suggestion-chip" onclick="sendSuggestion('Show me any anomalies')">🚨 Check Anomalies</div>
                        <div class="suggestion-chip" onclick="sendSuggestion('What are the energy trends?')">📈 View Trends</div>
                        <div class="suggestion-chip" onclick="sendSuggestion('Generate a comprehensive report')">📋 Full Report</div>
                        <div class="suggestion-chip" onclick="sendSuggestion('Analyze voltage quality')">⚡ Voltage Analysis</div>
                    </div>
                    
                    <div class="typing-indicator" id="typingIndicator">
                        <div class="bot-avatar">🤖</div>
                        <div class="typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
                
                <div class="chat-input-container">
                    <form class="chat-input-form" id="chatForm">
                        <input 
                            type="text" 
                            class="chat-input" 
                            id="messageInput" 
                            placeholder="Ask me about energy consumption, system status, anomalies, trends, or any energy-related question..."
                            autocomplete="off"
                        >
                        <button type="submit" class="send-button" id="sendButton">
                            ➤
                        </button>
                    </form>
                </div>
            </div>
            
            <script>
                let ws = null;
                let isConnected = false;
                
                const chatMessages = document.getElementById('chatMessages');
                const messageInput = document.getElementById('messageInput');
                const sendButton = document.getElementById('sendButton');
                const chatForm = document.getElementById('chatForm');
                const typingIndicator = document.getElementById('typingIndicator');
                const statusIndicator = document.getElementById('statusIndicator');
                
                function connectWebSocket() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/chat`;
                    
                    ws = new WebSocket(wsUrl);
                    
                    ws.onopen = function() {
                        console.log('Connected to EMS Chatbot');
                        isConnected = true;
                        statusIndicator.style.background = '#4ade80';
                        sendButton.disabled = false;
                    };
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        
                        if (data.type === 'bot_message') {
                            hideTypingIndicator();
                            addBotMessage(data.message, data.intent, data.processing_time);
                        } else if (data.type === 'error') {
                            hideTypingIndicator();
                            addBotMessage('❌ ' + data.message, 'error');
                        }
                    };
                    
                    ws.onclose = function() {
                        console.log('Disconnected from EMS Chatbot');
                        isConnected = false;
                        statusIndicator.style.background = '#ef4444';
                        sendButton.disabled = true;
                        
                        // Attempt to reconnect after 3 seconds
                        setTimeout(connectWebSocket, 3000);
                    };
                    
                    ws.onerror = function(error) {
                        console.error('WebSocket error:', error);
                        isConnected = false;
                        statusIndicator.style.background = '#ef4444';
                    };
                }
                
                function sendMessage(message) {
                    if (!isConnected || !message.trim()) return;
                    
                    addUserMessage(message);
                    showTypingIndicator();
                    
                    ws.send(JSON.stringify({
                        message: message.trim()
                    }));
                    
                    messageInput.value = '';
                    messageInput.focus();
                }
                
                function addUserMessage(message) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message user';
                    messageDiv.innerHTML = `
                        <div class="message-content">
                            ${escapeHtml(message)}
                            <div class="message-meta">${getCurrentTime()}</div>
                        </div>
                    `;
                    
                    chatMessages.insertBefore(messageDiv, typingIndicator);
                    scrollToBottom();
                }
                
                function addBotMessage(message, intent, processingTime) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message bot';
                    
                    const formattedMessage = formatBotMessage(message);
                    const intentBadge = intent ? `<span style="background: #e5e7eb; padding: 2px 8px; border-radius: 12px; font-size: 11px; color: #6b7280; margin-right: 8px;">${intent}</span>` : '';
                    const timingInfo = processingTime ? ` • ${processingTime.toFixed(2)}s` : '';
                    
                    messageDiv.innerHTML = `
                        <div class="bot-avatar">🤖</div>
                        <div class="message-content">
                            ${formattedMessage}
                            <div class="message-meta">
                                ${intentBadge}${getCurrentTime()}${timingInfo}
                            </div>
                        </div>
                    `;
                    
                    chatMessages.insertBefore(messageDiv, typingIndicator);
                    scrollToBottom();
                }
                
                function formatBotMessage(message) {
                    // Convert markdown-style formatting to HTML
                    return message
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\*(.*?)\*/g, '<em>$1</em>')
                        .replace(/`(.*?)`/g, '<code>$1</code>')
                        .replace(/\n/g, '<br>')
                        .replace(/#{1,6} (.*?)$/gm, '<h4>$1</h4>')
                        .replace(/• (.*?)$/gm, '• $1')
                        .replace(/(\d+\.) (.*?)$/gm, '$1 $2');
                }
                
                function showTypingIndicator() {
                    typingIndicator.style.display = 'flex';
                    scrollToBottom();
                }
                
                function hideTypingIndicator() {
                    typingIndicator.style.display = 'none';
                }
                
                function scrollToBottom() {
                    setTimeout(() => {
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    }, 100);
                }
                
                function getCurrentTime() {
                    return new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                }
                
                function escapeHtml(text) {
                    const div = document.createElement('div');
                    div.textContent = text;
                    return div.innerHTML;
                }
                
                function sendSuggestion(suggestion) {
                    if (isConnected) {
                        sendMessage(suggestion);
                    }
                }
                
                // Event listeners
                chatForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    sendMessage(messageInput.value);
                });
                
                messageInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage(messageInput.value);
                    }
                });
                
                // Initialize connection
                connectWebSocket();
                
                // Focus input on load
                messageInput.focus();
            </script>
        </body>
        </html>
        """
    
    def run(self, host: str = "127.0.0.1", port: int = 8091):
        """Run the EMS Chatbot application"""
        print(f"🤖 Starting EMS Agent Chatbot on {host}:{port}")
        print(f"🌐 Access the chatbot at: http://{host}:{port}")
        print(f"💬 The chatbot can analyze MongoDB data and answer energy-related questions")
        
        uvicorn.run(self.app, host=host, port=port, log_level="info")


def main():
    """Main entry point for EMS Chatbot"""
    import argparse
    
    parser = argparse.ArgumentParser(description="EMS Agent Chatbot - Intelligent Energy Management Assistant")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8091, help="Port to bind to")
    
    args = parser.parse_args()
    
    chatbot_app = EMSChatbotApp()
    chatbot_app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
