#!/usr/bin/env python3
"""
Query Processor Service for EMS
Natural language query processing and data retrieval
"""

import asyncio
import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
import numpy as np
from pymongo import MongoClient
import openai
from transformers import pipeline, AutoTokenizer, AutoModel
import torch

from common.base_service import BaseService
from common.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class QueryIntent:
    """Query intent classification"""
    POWER_ANALYSIS = "power_analysis"
    TREND_ANALYSIS = "trend_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    COST_ANALYSIS = "cost_analysis"
    EFFICIENCY_ANALYSIS = "efficiency_analysis"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    PREDICTIVE_ANALYSIS = "predictive_analysis"
    SYSTEM_STATUS = "system_status"


class NLPQueryProcessor:
    """Natural Language Processing for query understanding"""
    
    def __init__(self):
        self.intent_patterns = {
            QueryIntent.POWER_ANALYSIS: [
                r'power\s+(consumption|usage|demand)',
                r'energy\s+(consumption|usage)',
                r'(current|active|reactive)\s+power',
                r'load\s+(analysis|profile)',
                r'(kw|kilowatt|watt)\s*(h|hour)?'
            ],
            QueryIntent.TREND_ANALYSIS: [
                r'trend\s+(analysis|pattern)',
                r'(historical|past|previous)\s+data',
                r'over\s+time',
                r'(daily|weekly|monthly|yearly)\s+pattern',
                r'time\s+series'
            ],
            QueryIntent.ANOMALY_DETECTION: [
                r'anomal(y|ies)',
                r'unusual\s+(pattern|behavior)',
                r'(detect|find|identify)\s+(issues|problems)',
                r'out\s+of\s+(normal|range)',
                r'abnormal\s+(reading|value)'
            ],
            QueryIntent.COST_ANALYSIS: [
                r'cost\s+(analysis|breakdown)',
                r'(energy|electricity)\s+bill',
                r'(dollar|money|\$|expense)',
                r'tariff\s+rate',
                r'demand\s+charge'
            ],
            QueryIntent.EFFICIENCY_ANALYSIS: [
                r'efficiency\s+(analysis|rating)',
                r'power\s+factor',
                r'(optimize|optimization)',
                r'performance\s+(metric|indicator)',
                r'energy\s+saving'
            ],
            QueryIntent.COMPARATIVE_ANALYSIS: [
                r'compar(e|ison)',
                r'(vs|versus|against)',
                r'(difference|delta)',
                r'(before|after)',
                r'(better|worse|improved)'
            ],
            QueryIntent.PREDICTIVE_ANALYSIS: [
                r'predict(ion|ive)',
                r'forecast(ing)?',
                r'(future|next|upcoming)',
                r'(will|would|might)\s+be',
                r'expect(ed|ation)'
            ],
            QueryIntent.SYSTEM_STATUS: [
                r'system\s+(status|health)',
                r'(current|real\s*time)\s+status',
                r'(online|offline|running)',
                r'health\s+check',
                r'operational\s+status'
            ]
        }
        
        # Initialize transformer model for more sophisticated NLP
        try:
            self.tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')
            self.model = AutoModel.from_pretrained('distilbert-base-uncased')
            self.nlp_available = True
        except Exception as e:
            logger.warning(f"Advanced NLP model not available: {e}")
            self.nlp_available = False
    
    def classify_intent(self, query: str) -> str:
        """Classify query intent using pattern matching"""
        query_lower = query.lower()
        
        # Score each intent
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query_lower))
                score += matches
            intent_scores[intent] = score
        
        # Return highest scoring intent
        if intent_scores and max(intent_scores.values()) > 0:
            return max(intent_scores, key=intent_scores.get)
        
        return QueryIntent.POWER_ANALYSIS  # Default intent
    
    def extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from query (time ranges, equipment IDs, etc.)"""
        entities = {
            'time_range': None,
            'equipment_ids': [],
            'metrics': [],
            'aggregation': None,
            'filters': {}
        }
        
        query_lower = query.lower()
        
        # Extract time ranges
        time_patterns = {
            'today': timedelta(days=1),
            'yesterday': timedelta(days=1),
            'last week': timedelta(days=7),
            'last month': timedelta(days=30),
            'last year': timedelta(days=365),
            'this week': timedelta(days=7),
            'this month': timedelta(days=30),
            'this year': timedelta(days=365)
        }
        
        for time_expr, delta in time_patterns.items():
            if time_expr in query_lower:
                entities['time_range'] = {
                    'start': datetime.now() - delta,
                    'end': datetime.now(),
                    'expression': time_expr
                }
                break
        
        # Extract equipment IDs (pattern: IKC followed by numbers)
        equipment_pattern = r'IKC\w*\d+'
        equipment_matches = re.findall(equipment_pattern, query, re.IGNORECASE)
        entities['equipment_ids'] = list(set(equipment_matches))
        
        # Extract metrics
        metric_keywords = {
            'power': ['power', 'watt', 'kw', 'kilowatt'],
            'voltage': ['voltage', 'volt', 'v'],
            'current': ['current', 'amp', 'ampere', 'a'],
            'frequency': ['frequency', 'hz', 'hertz'],
            'power_factor': ['power factor', 'pf'],
            'energy': ['energy', 'kwh', 'kilowatt-hour']
        }
        
        for metric, keywords in metric_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                entities['metrics'].append(metric)
        
        # Extract aggregation type
        aggregation_patterns = {
            'average': ['average', 'avg', 'mean'],
            'maximum': ['maximum', 'max', 'peak', 'highest'],
            'minimum': ['minimum', 'min', 'lowest'],
            'sum': ['total', 'sum', 'cumulative'],
            'count': ['count', 'number of']
        }
        
        for agg_type, keywords in aggregation_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                entities['aggregation'] = agg_type
                break
        
        return entities


class QueryProcessorService(BaseService):
    """Query processor service for natural language queries"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("query_processor", config)
        self.nlp_processor = NLPQueryProcessor()
        self.query_history = []
        self.collections = {}
        self.app = self._create_fastapi_app()
    
    async def initialize(self):
        """Initialize query processor service"""
        await super().initialize()
        
        # Initialize database collections
        if self.db_client:
            db = self.db_client[self.config['mongodb']['database']]
            self.collections = {
                'raw_data': db.ems_raw_data,
                'processed_data': db.ems_processed_data,
                'query_history': db.ems_query_history,
                'query_cache': db.ems_query_cache
            }
        
        logger.info("Query Processor Service initialized")
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title="EMS Query Processor Service",
            description="Natural language query processing for energy data",
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
        
        @app.post("/query")
        async def process_query(request: Dict[str, Any]):
            """Process natural language query"""
            try:
                query = request.get('query', '')
                user_id = request.get('user_id', 'anonymous')
                context = request.get('context', {})
                
                result = await self.process_natural_language_query(query, user_id, context)
                return {"success": True, "result": result}
                
            except Exception as e:
                logger.error(f"Query processing error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @app.get("/query/history")
        async def get_query_history(user_id: str = None, limit: int = 10):
            """Get query history"""
            try:
                history = await self.get_user_query_history(user_id, limit)
                return {"history": history}
                
            except Exception as e:
                logger.error(f"Error getting query history: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/query/batch")
        async def process_batch_queries(request: Dict[str, Any]):
            """Process multiple queries in batch"""
            try:
                queries = request.get('queries', [])
                user_id = request.get('user_id', 'anonymous')
                
                results = []
                for query in queries:
                    try:
                        result = await self.process_natural_language_query(query, user_id)
                        results.append({"query": query, "success": True, "result": result})
                    except Exception as e:
                        results.append({"query": query, "success": False, "error": str(e)})
                
                return {"batch_results": results}
                
            except Exception as e:
                logger.error(f"Batch query processing error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @app.get("/query/suggestions")
        async def get_query_suggestions():
            """Get query suggestions based on common patterns"""
            suggestions = [
                "What is the current power consumption?",
                "Show me today's energy usage trends",
                "Are there any anomalies in the system?",
                "What's the average power consumption this month?",
                "Show me the cost breakdown for last week",
                "How is the power factor performance?",
                "Compare this month vs last month energy usage",
                "Predict tomorrow's energy consumption",
                "What equipment is using the most power?",
                "Show me system health status"
            ]
            return {"suggestions": suggestions}
    
    async def process_natural_language_query(
        self, 
        query: str, 
        user_id: str = 'anonymous',
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process natural language query and return structured results"""
        
        # Check cache first
        cached_result = await self._check_query_cache(query)
        if cached_result:
            return cached_result
        
        # Classify intent and extract entities
        intent = self.nlp_processor.classify_intent(query)
        entities = self.nlp_processor.extract_entities(query)
        
        # Log query
        await self._log_query(query, user_id, intent, entities)
        
        # Process based on intent
        if intent == QueryIntent.POWER_ANALYSIS:
            result = await self._process_power_analysis_query(entities)
        elif intent == QueryIntent.TREND_ANALYSIS:
            result = await self._process_trend_analysis_query(entities)
        elif intent == QueryIntent.ANOMALY_DETECTION:
            result = await self._process_anomaly_detection_query(entities)
        elif intent == QueryIntent.COST_ANALYSIS:
            result = await self._process_cost_analysis_query(entities)
        elif intent == QueryIntent.EFFICIENCY_ANALYSIS:
            result = await self._process_efficiency_analysis_query(entities)
        elif intent == QueryIntent.COMPARATIVE_ANALYSIS:
            result = await self._process_comparative_analysis_query(entities)
        elif intent == QueryIntent.PREDICTIVE_ANALYSIS:
            result = await self._process_predictive_analysis_query(entities)
        elif intent == QueryIntent.SYSTEM_STATUS:
            result = await self._process_system_status_query(entities)
        else:
            result = await self._process_general_query(entities)
        
        # Add metadata
        result.update({
            'query': query,
            'intent': intent,
            'entities': entities,
            'timestamp': datetime.now().isoformat(),
            'processing_time_ms': result.get('processing_time_ms', 0)
        })
        
        # Cache result
        await self._cache_query_result(query, result)
        
        return result
    
    async def _process_power_analysis_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Process power analysis queries"""
        start_time = datetime.now()
        
        # Build query filter
        query_filter = {}
        if entities['time_range']:
            query_filter['timestamp'] = {
                '$gte': entities['time_range']['start'],
                '$lte': entities['time_range']['end']
            }
        else:
            # Default to last 24 hours
            query_filter['timestamp'] = {
                '$gte': datetime.now() - timedelta(hours=24),
                '$lte': datetime.now()
            }
        
        if entities['equipment_ids']:
            query_filter['equipment_id'] = {'$in': entities['equipment_ids']}
        
        # Get data from database
        data_cursor = self.collections['raw_data'].find(query_filter)
        data = list(data_cursor)
        
        if not data:
            return {
                'message': 'No data found for the specified criteria',
                'data_points': 0,
                'processing_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(data)
        
        # Calculate power metrics
        power_metrics = {}
        
        if 'active_power_kw' in df.columns:
            power_metrics['current_power_kw'] = df['active_power_kw'].iloc[-1] if len(df) > 0 else 0
            power_metrics['average_power_kw'] = df['active_power_kw'].mean()
            power_metrics['max_power_kw'] = df['active_power_kw'].max()
            power_metrics['min_power_kw'] = df['active_power_kw'].min()
            power_metrics['total_energy_kwh'] = df['active_power_kw'].sum() * (len(df) / 3600)  # Approximate
        
        if 'reactive_power_kvar' in df.columns:
            power_metrics['reactive_power_kvar'] = {
                'current': df['reactive_power_kvar'].iloc[-1] if len(df) > 0 else 0,
                'average': df['reactive_power_kvar'].mean(),
                'max': df['reactive_power_kvar'].max(),
                'min': df['reactive_power_kvar'].min()
            }
        
        if 'power_factor' in df.columns:
            power_metrics['power_factor'] = {
                'current': df['power_factor'].iloc[-1] if len(df) > 0 else 0,
                'average': df['power_factor'].mean(),
                'min': df['power_factor'].min()
            }
        
        # Time series data for charts
        time_series = []
        if len(df) > 0:
            df_sorted = df.sort_values('timestamp')
            time_series = [
                {
                    'timestamp': row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp']),
                    'power_kw': row.get('active_power_kw', 0),
                    'equipment_id': row.get('equipment_id', 'unknown')
                }
                for _, row in df_sorted.iterrows()
            ]
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            'analysis_type': 'power_analysis',
            'power_metrics': power_metrics,
            'time_series': time_series[-100:],  # Limit to last 100 points for performance
            'data_points': len(data),
            'time_range': entities.get('time_range', {}),
            'equipment_count': len(entities.get('equipment_ids', [])) or len(df['equipment_id'].unique()) if 'equipment_id' in df.columns else 1,
            'processing_time_ms': processing_time,
            'summary': self._generate_power_analysis_summary(power_metrics)
        }
    
    async def _process_trend_analysis_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Process trend analysis queries"""
        start_time = datetime.now()
        
        # Get historical data for trend analysis
        query_filter = {}
        
        # Default to last 30 days for trend analysis
        if not entities['time_range']:
            entities['time_range'] = {
                'start': datetime.now() - timedelta(days=30),
                'end': datetime.now()
            }
        
        query_filter['timestamp'] = {
            '$gte': entities['time_range']['start'],
            '$lte': entities['time_range']['end']
        }
        
        if entities['equipment_ids']:
            query_filter['equipment_id'] = {'$in': entities['equipment_ids']}
        
        # Get data and perform trend analysis
        data_cursor = self.collections['raw_data'].find(query_filter)
        data = list(data_cursor)
        
        if not data:
            return {
                'message': 'No data found for trend analysis',
                'processing_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Group by day for daily trends
        daily_trends = []
        if 'active_power_kw' in df.columns:
            daily_df = df.groupby(df['timestamp'].dt.date).agg({
                'active_power_kw': ['mean', 'max', 'min', 'sum'],
                'equipment_id': 'count'
            }).reset_index()
            
            daily_trends = [
                {
                    'date': str(row['timestamp']),
                    'avg_power_kw': row[('active_power_kw', 'mean')],
                    'max_power_kw': row[('active_power_kw', 'max')],
                    'min_power_kw': row[('active_power_kw', 'min')],
                    'total_energy_kwh': row[('active_power_kw', 'sum')] / 24,  # Approximate
                    'data_points': row[('equipment_id', 'count')]
                }
                for _, row in daily_df.iterrows()
            ]
        
        # Calculate trend direction
        trend_direction = 'stable'
        if len(daily_trends) >= 7:  # Need at least a week of data
            recent_avg = np.mean([t['avg_power_kw'] for t in daily_trends[-7:]])
            earlier_avg = np.mean([t['avg_power_kw'] for t in daily_trends[:7]])
            
            change_percent = ((recent_avg - earlier_avg) / earlier_avg) * 100
            
            if change_percent > 5:
                trend_direction = 'increasing'
            elif change_percent < -5:
                trend_direction = 'decreasing'
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            'analysis_type': 'trend_analysis',
            'daily_trends': daily_trends,
            'trend_direction': trend_direction,
            'trend_summary': self._generate_trend_summary(daily_trends, trend_direction),
            'data_points': len(data),
            'time_range': entities['time_range'],
            'processing_time_ms': processing_time
        }
    
    async def _process_anomaly_detection_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Process anomaly detection queries"""
        # This would integrate with the Analytics service for ML-based anomaly detection
        start_time = datetime.now()
        
        # For now, implement simple statistical anomaly detection
        query_filter = {}
        if entities['time_range']:
            query_filter['timestamp'] = {
                '$gte': entities['time_range']['start'],
                '$lte': entities['time_range']['end']
            }
        else:
            # Default to last 7 days
            query_filter['timestamp'] = {
                '$gte': datetime.now() - timedelta(days=7),
                '$lte': datetime.now()
            }
        
        data_cursor = self.collections['raw_data'].find(query_filter)
        data = list(data_cursor)
        
        if len(data) < 10:
            return {
                'message': 'Insufficient data for anomaly detection',
                'processing_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
        
        df = pd.DataFrame(data)
        anomalies = []
        
        # Simple statistical anomaly detection using z-score
        if 'active_power_kw' in df.columns:
            mean_power = df['active_power_kw'].mean()
            std_power = df['active_power_kw'].std()
            
            # Find values more than 2 standard deviations from mean
            anomaly_mask = np.abs((df['active_power_kw'] - mean_power) / std_power) > 2
            anomaly_data = df[anomaly_mask]
            
            for _, row in anomaly_data.iterrows():
                anomalies.append({
                    'timestamp': row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp']),
                    'equipment_id': row.get('equipment_id', 'unknown'),
                    'power_kw': row['active_power_kw'],
                    'deviation_from_mean': abs(row['active_power_kw'] - mean_power),
                    'severity': 'high' if abs(row['active_power_kw'] - mean_power) > 3 * std_power else 'medium'
                })
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            'analysis_type': 'anomaly_detection',
            'anomalies_found': len(anomalies),
            'anomalies': anomalies[:20],  # Limit to 20 most recent
            'summary': f"Found {len(anomalies)} anomalies in the specified time period",
            'data_points': len(data),
            'processing_time_ms': processing_time
        }
    
    async def _process_cost_analysis_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Process cost analysis queries"""
        start_time = datetime.now()
        
        # Default rate structure (this should come from configuration)
        energy_rate = 0.12  # $/kWh
        demand_rate = 15.0  # $/kW
        
        query_filter = {}
        if entities['time_range']:
            query_filter['timestamp'] = {
                '$gte': entities['time_range']['start'],
                '$lte': entities['time_range']['end']
            }
        else:
            # Default to current month
            now = datetime.now()
            query_filter['timestamp'] = {
                '$gte': datetime(now.year, now.month, 1),
                '$lte': now
            }
        
        data_cursor = self.collections['raw_data'].find(query_filter)
        data = list(data_cursor)
        
        if not data:
            return {
                'message': 'No data found for cost analysis',
                'processing_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
        
        df = pd.DataFrame(data)
        
        # Calculate energy consumption and costs
        cost_breakdown = {}
        
        if 'active_power_kw' in df.columns:
            total_energy_kwh = df['active_power_kw'].sum() * (len(df) / 3600)  # Approximate
            max_demand_kw = df['active_power_kw'].max()
            
            energy_cost = total_energy_kwh * energy_rate
            demand_cost = max_demand_kw * demand_rate
            total_cost = energy_cost + demand_cost
            
            cost_breakdown = {
                'total_cost': round(total_cost, 2),
                'energy_cost': round(energy_cost, 2),
                'demand_cost': round(demand_cost, 2),
                'total_energy_kwh': round(total_energy_kwh, 2),
                'max_demand_kw': round(max_demand_kw, 2),
                'average_rate_per_kwh': round(total_cost / total_energy_kwh, 4) if total_energy_kwh > 0 else 0
            }
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            'analysis_type': 'cost_analysis',
            'cost_breakdown': cost_breakdown,
            'rate_structure': {
                'energy_rate_per_kwh': energy_rate,
                'demand_rate_per_kw': demand_rate
            },
            'summary': f"Total estimated cost: ${cost_breakdown.get('total_cost', 0):.2f}",
            'data_points': len(data),
            'processing_time_ms': processing_time
        }
    
    async def _process_efficiency_analysis_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Process efficiency analysis queries"""
        start_time = datetime.now()
        
        query_filter = {}
        if entities['time_range']:
            query_filter['timestamp'] = {
                '$gte': entities['time_range']['start'],
                '$lte': entities['time_range']['end']
            }
        else:
            # Default to last 24 hours
            query_filter['timestamp'] = {
                '$gte': datetime.now() - timedelta(hours=24),
                '$lte': datetime.now()
            }
        
        data_cursor = self.collections['raw_data'].find(query_filter)
        data = list(data_cursor)
        
        if not data:
            return {
                'message': 'No data found for efficiency analysis',
                'processing_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
        
        df = pd.DataFrame(data)
        
        efficiency_metrics = {}
        
        # Calculate power factor efficiency
        if 'power_factor' in df.columns:
            avg_pf = df['power_factor'].mean()
            min_pf = df['power_factor'].min()
            
            # Efficiency rating based on power factor
            if avg_pf >= 0.95:
                pf_rating = 'excellent'
            elif avg_pf >= 0.90:
                pf_rating = 'good'
            elif avg_pf >= 0.85:
                pf_rating = 'fair'
            else:
                pf_rating = 'poor'
            
            efficiency_metrics['power_factor'] = {
                'average': round(avg_pf, 3),
                'minimum': round(min_pf, 3),
                'rating': pf_rating,
                'improvement_potential': max(0, round((0.95 - avg_pf) * 100, 1))
            }
        
        # Calculate load factor
        if 'active_power_kw' in df.columns:
            avg_load = df['active_power_kw'].mean()
            max_load = df['active_power_kw'].max()
            load_factor = avg_load / max_load if max_load > 0 else 0
            
            efficiency_metrics['load_factor'] = {
                'value': round(load_factor, 3),
                'rating': 'excellent' if load_factor >= 0.8 else 'good' if load_factor >= 0.6 else 'fair' if load_factor >= 0.4 else 'poor'
            }
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            'analysis_type': 'efficiency_analysis',
            'efficiency_metrics': efficiency_metrics,
            'recommendations': self._generate_efficiency_recommendations(efficiency_metrics),
            'summary': f"Overall efficiency rating: {self._calculate_overall_efficiency_rating(efficiency_metrics)}",
            'data_points': len(data),
            'processing_time_ms': processing_time
        }
    
    async def _process_comparative_analysis_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Process comparative analysis queries"""
        # This would compare different time periods or equipment
        return {
            'analysis_type': 'comparative_analysis',
            'message': 'Comparative analysis feature coming soon',
            'processing_time_ms': 10
        }
    
    async def _process_predictive_analysis_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Process predictive analysis queries"""
        # This would integrate with ML models for prediction
        return {
            'analysis_type': 'predictive_analysis',
            'message': 'Predictive analysis feature coming soon',
            'processing_time_ms': 10
        }
    
    async def _process_system_status_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Process system status queries"""
        start_time = datetime.now()
        
        # Get recent data to determine system status
        recent_time = datetime.now() - timedelta(minutes=5)
        query_filter = {'timestamp': {'$gte': recent_time}}
        
        recent_data = list(self.collections['raw_data'].find(query_filter))
        
        system_status = {
            'overall_status': 'online' if recent_data else 'offline',
            'last_update': max([d['timestamp'] for d in recent_data]).isoformat() if recent_data else 'unknown',
            'active_equipment': len(set([d.get('equipment_id') for d in recent_data])) if recent_data else 0,
            'data_points_last_hour': len(recent_data)
        }
        
        if recent_data:
            df = pd.DataFrame(recent_data)
            if 'active_power_kw' in df.columns:
                system_status['current_total_power_kw'] = round(df['active_power_kw'].sum(), 2)
                system_status['average_power_kw'] = round(df['active_power_kw'].mean(), 2)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            'analysis_type': 'system_status',
            'system_status': system_status,
            'summary': f"System is {system_status['overall_status']} with {system_status['active_equipment']} active equipment",
            'processing_time_ms': processing_time
        }
    
    async def _process_general_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Process general queries that don't fit specific categories"""
        return {
            'analysis_type': 'general',
            'message': 'I understand you want information about your energy data. Could you be more specific about what you\'d like to know?',
            'suggestions': [
                'Try asking about power consumption, trends, costs, or system status',
                'You can specify time ranges like "today", "last week", or "this month"',
                'Ask about specific equipment by mentioning equipment IDs'
            ],
            'processing_time_ms': 5
        }
    
    def _generate_power_analysis_summary(self, metrics: Dict[str, Any]) -> str:
        """Generate human-readable summary of power analysis"""
        if not metrics:
            return "No power data available for analysis"
        
        current_power = metrics.get('current_power_kw', 0)
        avg_power = metrics.get('average_power_kw', 0)
        max_power = metrics.get('max_power_kw', 0)
        
        summary_parts = []
        
        if current_power > 0:
            summary_parts.append(f"Current power consumption is {current_power:.1f} kW")
        
        if avg_power > 0:
            summary_parts.append(f"average consumption is {avg_power:.1f} kW")
        
        if max_power > 0:
            summary_parts.append(f"peak demand reached {max_power:.1f} kW")
        
        return ". ".join(summary_parts) if summary_parts else "Power analysis completed"
    
    def _generate_trend_summary(self, trends: List[Dict], direction: str) -> str:
        """Generate summary of trend analysis"""
        if not trends:
            return "No trend data available"
        
        if direction == 'increasing':
            return "Energy consumption is showing an increasing trend over the analyzed period"
        elif direction == 'decreasing':
            return "Energy consumption is showing a decreasing trend over the analyzed period"
        else:
            return "Energy consumption is relatively stable over the analyzed period"
    
    def _generate_efficiency_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate efficiency improvement recommendations"""
        recommendations = []
        
        pf_metrics = metrics.get('power_factor', {})
        if pf_metrics and pf_metrics.get('average', 1) < 0.9:
            recommendations.append("Consider installing power factor correction equipment to improve efficiency")
        
        load_metrics = metrics.get('load_factor', {})
        if load_metrics and load_metrics.get('value', 1) < 0.6:
            recommendations.append("Load factor is low - consider load scheduling to improve equipment utilization")
        
        if not recommendations:
            recommendations.append("System efficiency appears to be operating within acceptable parameters")
        
        return recommendations
    
    def _calculate_overall_efficiency_rating(self, metrics: Dict[str, Any]) -> str:
        """Calculate overall efficiency rating"""
        scores = []
        
        pf_metrics = metrics.get('power_factor', {})
        if pf_metrics:
            pf_rating = pf_metrics.get('rating', 'unknown')
            rating_scores = {'excellent': 4, 'good': 3, 'fair': 2, 'poor': 1}
            scores.append(rating_scores.get(pf_rating, 2))
        
        load_metrics = metrics.get('load_factor', {})
        if load_metrics:
            lf_rating = load_metrics.get('rating', 'unknown')
            rating_scores = {'excellent': 4, 'good': 3, 'fair': 2, 'poor': 1}
            scores.append(rating_scores.get(lf_rating, 2))
        
        if not scores:
            return 'unknown'
        
        avg_score = sum(scores) / len(scores)
        if avg_score >= 3.5:
            return 'excellent'
        elif avg_score >= 2.5:
            return 'good'
        elif avg_score >= 1.5:
            return 'fair'
        else:
            return 'poor'
    
    async def _check_query_cache(self, query: str) -> Optional[Dict[str, Any]]:
        """Check if query result is cached"""
        try:
            query_hash = hash(query.lower().strip())
            cached = self.collections['query_cache'].find_one({
                'query_hash': query_hash,
                'expiry': {'$gt': datetime.now()}
            })
            
            if cached:
                return cached.get('result')
            
        except Exception as e:
            logger.error(f"Cache check error: {e}")
        
        return None
    
    async def _cache_query_result(self, query: str, result: Dict[str, Any]):
        """Cache query result for future use"""
        try:
            query_hash = hash(query.lower().strip())
            cache_entry = {
                'query_hash': query_hash,
                'query': query,
                'result': result,
                'cached_at': datetime.now(),
                'expiry': datetime.now() + timedelta(hours=1)  # Cache for 1 hour
            }
            
            # Use upsert to replace existing cache entry
            self.collections['query_cache'].replace_one(
                {'query_hash': query_hash},
                cache_entry,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Cache save error: {e}")
    
    async def _log_query(self, query: str, user_id: str, intent: str, entities: Dict[str, Any]):
        """Log query for analytics and improvement"""
        try:
            log_entry = {
                'query': query,
                'user_id': user_id,
                'intent': intent,
                'entities': entities,
                'timestamp': datetime.now()
            }
            
            self.collections['query_history'].insert_one(log_entry)
            
        except Exception as e:
            logger.error(f"Query logging error: {e}")
    
    async def get_user_query_history(self, user_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user query history"""
        try:
            query_filter = {}
            if user_id:
                query_filter['user_id'] = user_id
            
            history_cursor = self.collections['query_history'].find(
                query_filter
            ).sort('timestamp', -1).limit(limit)
            
            history = []
            for entry in history_cursor:
                history.append({
                    'query': entry['query'],
                    'intent': entry['intent'],
                    'timestamp': entry['timestamp'].isoformat()
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting query history: {e}")
            return []
    
    async def health_check(self):
        """Service-specific health check"""
        # Test NLP processor
        test_query = "What is the current power consumption?"
        intent = self.nlp_processor.classify_intent(test_query)
        
        if not intent:
            raise Exception("NLP processor not working")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service-specific requests"""
        request_type = request_data.get('type')
        
        if request_type == 'process_query':
            return await self.process_natural_language_query(
                request_data['query'],
                request_data.get('user_id', 'anonymous'),
                request_data.get('context', {})
            )
        elif request_type == 'get_history':
            history = await self.get_user_query_history(
                request_data.get('user_id'),
                request_data.get('limit', 10)
            )
            return {'history': history}
        else:
            raise ValueError(f"Unknown request type: {request_type}")


def create_query_processor_service():
    """Factory function to create query processor service"""
    config_manager = ConfigManager()
    config = config_manager.get_config()
    return QueryProcessorService(config)


async def run_service():
    """Run the query processor service"""
    service = create_query_processor_service()
    await service.initialize()
    await service.run()


if __name__ == "__main__":
    asyncio.run(run_service())
