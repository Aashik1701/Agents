#!/usr/bin/env python3
"""
Analytics Service for EMS
Handles data analysis, anomaly detection, and predictive analytics
"""

import asyncio
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

from common.base_service import BaseService
from common.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class AnalyticsService(BaseService):
    """Analytics service for EMS data processing and anomaly detection"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("analytics", config)
        self.collections = {}
        self.models = {}
        self.scalers = {}
        self.app = self._create_fastapi_app()
        
        # Analytics configuration
        self.anomaly_threshold = config.get('anomaly_threshold', 0.1)
        self.prediction_window = config.get('prediction_window', 24)  # hours
        
    async def initialize(self):
        """Initialize analytics service"""
        await super().initialize()
        
        # Initialize database collections
        if self.db_client:
            db = self.db_client[self.config['mongodb']['database']]
            self.collections = {
                'raw_data': db.ems_raw_data,
                'processed_data': db.ems_processed_data,
                'anomalies': db.ems_anomalies,
                'predictions': db.ems_predictions,
                'analytics_models': db.ems_analytics_models
            }
        
        # Load or train ML models
        await self._initialize_models()
        
        # Start background analytics tasks
        asyncio.create_task(self._run_periodic_analytics())
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title="EMS Analytics Service",
            description="Analytics and anomaly detection service for EMS",
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
            return self.get_health_status()
        
        @app.post("/analyze/new_data")
        async def analyze_new_data(data: Dict[str, Any]):
            """Analyze newly ingested data"""
            background_tasks = BackgroundTasks()
            background_tasks.add_task(self.process_new_data, data)
            return {"message": "Analytics processing started", "data": data}
        
        @app.post("/detect_anomalies")
        async def detect_anomalies(request: Dict[str, Any]):
            """Detect anomalies in data"""
            equipment_ids = request.get('equipment_ids', [])
            time_range = request.get('time_range', {})
            
            result = await self.detect_anomalies_for_equipment(equipment_ids, time_range)
            return {"anomalies": result}
        
        @app.post("/predict")
        async def predict_energy_consumption(request: Dict[str, Any]):
            """Predict energy consumption"""
            equipment_id = request.get('equipment_id')
            prediction_hours = request.get('hours', 24)
            
            result = await self.predict_consumption(equipment_id, prediction_hours)
            return {"predictions": result}
        
        @app.get("/analytics/summary")
        async def get_analytics_summary():
            """Get analytics summary"""
            return await self.get_analytics_summary()
        
        @app.post("/train_models")
        async def train_models(background_tasks: BackgroundTasks):
            """Retrain ML models"""
            background_tasks.add_task(self._train_all_models)
            return {"message": "Model training started"}
    
    async def _initialize_models(self):
        """Initialize or load ML models"""
        try:
            # Try to load existing models from database
            await self._load_models_from_database()
            
            # If no models exist, train new ones
            if not self.models:
                await self._train_all_models()
                
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            # Create default models
            await self._create_default_models()
    
    async def _load_models_from_database(self):
        """Load trained models from database"""
        try:
            models_data = await asyncio.to_thread(
                self.collections['analytics_models'].find,
                {'active': True}
            )
            
            for model_doc in models_data:
                model_name = model_doc['name']
                model_data = model_doc['model_data']
                
                # Deserialize model (in production, use proper model storage)
                self.models[model_name] = joblib.loads(model_data)
                
                if 'scaler_data' in model_doc:
                    self.scalers[model_name] = joblib.loads(model_doc['scaler_data'])
            
            logger.info(f"Loaded {len(self.models)} models from database")
            
        except Exception as e:
            logger.error(f"Error loading models from database: {e}")
    
    async def _create_default_models(self):
        """Create default ML models"""
        # Anomaly detection model
        self.models['anomaly_detector'] = IsolationForest(
            contamination=self.anomaly_threshold,
            random_state=42
        )
        
        # Scaler for anomaly detection
        self.scalers['anomaly_detector'] = StandardScaler()
        
        logger.info("Created default models")
    
    async def _train_all_models(self):
        """Train all ML models"""
        try:
            logger.info("Starting model training...")
            
            # Get training data
            training_data = await self._get_training_data()
            
            if training_data.empty:
                logger.warning("No training data available")
                return
            
            # Train anomaly detection model
            await self._train_anomaly_model(training_data)
            
            # Save models to database
            await self._save_models_to_database()
            
            logger.info("Model training completed")
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
    
    async def _get_training_data(self) -> pd.DataFrame:
        """Get data for model training"""
        try:
            # Get data from last 30 days
            start_date = datetime.now() - timedelta(days=30)
            
            query = {
                'timestamp': {'$gte': start_date},
                'quality_score': {'$gte': 0.8}  # Use only high-quality data
            }
            
            cursor = self.collections['raw_data'].find(query)
            data = await asyncio.to_thread(list, cursor)
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            # Select features for training
            feature_columns = ['voltage', 'current', 'power_factor', 'temperature', 'cfm']
            df = df[feature_columns + ['equipment_id', 'timestamp']].dropna()
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return pd.DataFrame()
    
    async def _train_anomaly_model(self, data: pd.DataFrame):
        """Train anomaly detection model"""
        try:
            # Prepare features
            feature_columns = ['voltage', 'current', 'power_factor', 'temperature', 'cfm']
            X = data[feature_columns]
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train model
            model = IsolationForest(
                contamination=self.anomaly_threshold,
                random_state=42,
                n_estimators=100
            )
            model.fit(X_scaled)
            
            # Store model and scaler
            self.models['anomaly_detector'] = model
            self.scalers['anomaly_detector'] = scaler
            
            logger.info("Anomaly detection model trained successfully")
            
        except Exception as e:
            logger.error(f"Error training anomaly model: {e}")
    
    async def _save_models_to_database(self):
        """Save trained models to database"""
        try:
            for model_name, model in self.models.items():
                # Serialize model
                model_data = joblib.dumps(model)
                scaler_data = joblib.dumps(self.scalers.get(model_name))
                
                model_doc = {
                    'name': model_name,
                    'model_data': model_data,
                    'scaler_data': scaler_data,
                    'trained_at': datetime.now(),
                    'active': True,
                    'version': '1.0'
                }
                
                # Deactivate old models
                await asyncio.to_thread(
                    self.collections['analytics_models'].update_many,
                    {'name': model_name},
                    {'$set': {'active': False}}
                )
                
                # Insert new model
                await asyncio.to_thread(
                    self.collections['analytics_models'].insert_one,
                    model_doc
                )
            
            logger.info("Models saved to database")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    async def _run_periodic_analytics(self):
        """Run periodic analytics tasks"""
        while True:
            try:
                # Run every 10 minutes
                await asyncio.sleep(600)
                
                # Detect anomalies in recent data
                await self._detect_recent_anomalies()
                
                # Generate predictions
                await self._generate_predictions()
                
                # Update analytics cache
                await self._update_analytics_cache()
                
            except Exception as e:
                logger.error(f"Error in periodic analytics: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _detect_recent_anomalies(self):
        """Detect anomalies in recent data"""
        try:
            # Get data from last hour
            start_time = datetime.now() - timedelta(hours=1)
            
            query = {
                'timestamp': {'$gte': start_time},
                'quality_score': {'$gte': 0.7}
            }
            
            cursor = self.collections['raw_data'].find(query)
            recent_data = await asyncio.to_thread(list, cursor)
            
            if not recent_data:
                return
            
            df = pd.DataFrame(recent_data)
            anomalies = await self._detect_anomalies_in_data(df)
            
            # Store anomalies
            if anomalies:
                await asyncio.to_thread(
                    self.collections['anomalies'].insert_many,
                    anomalies
                )
                
                # Publish anomaly alerts
                for anomaly in anomalies:
                    await self._publish_anomaly_alert(anomaly)
            
        except Exception as e:
            logger.error(f"Error detecting recent anomalies: {e}")
    
    async def _detect_anomalies_in_data(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies in given data"""
        anomalies = []
        
        if 'anomaly_detector' not in self.models:
            return anomalies
        
        try:
            model = self.models['anomaly_detector']
            scaler = self.scalers['anomaly_detector']
            
            feature_columns = ['voltage', 'current', 'power_factor', 'temperature', 'cfm']
            
            # Prepare features
            features_df = data[feature_columns].dropna()
            if features_df.empty:
                return anomalies
            
            # Scale features
            X_scaled = scaler.transform(features_df)
            
            # Predict anomalies
            predictions = model.predict(X_scaled)
            anomaly_scores = model.decision_function(X_scaled)
            
            # Create anomaly records
            for idx, (prediction, score) in enumerate(zip(predictions, anomaly_scores)):
                if prediction == -1:  # Anomaly detected
                    original_idx = features_df.index[idx]
                    record = data.iloc[original_idx]
                    
                    anomaly = {
                        'equipment_id': record['equipment_id'],
                        'timestamp': record['timestamp'],
                        'anomaly_score': float(score),
                        'detected_at': datetime.now(),
                        'type': 'statistical_anomaly',
                        'severity': self._calculate_anomaly_severity(score),
                        'original_record_id': record.get('_id'),
                        'features': record[feature_columns].to_dict()
                    }
                    
                    anomalies.append(anomaly)
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
        
        return anomalies
    
    def _calculate_anomaly_severity(self, score: float) -> str:
        """Calculate anomaly severity based on score"""
        if score < -0.5:
            return 'critical'
        elif score < -0.3:
            return 'high'
        elif score < -0.1:
            return 'medium'
        else:
            return 'low'
    
    async def _publish_anomaly_alert(self, anomaly: Dict[str, Any]):
        """Publish anomaly alert to notification service"""
        try:
            if self.redis_client:
                alert_data = {
                    'type': 'anomaly_alert',
                    'equipment_id': anomaly['equipment_id'],
                    'severity': anomaly['severity'],
                    'timestamp': anomaly['timestamp'].isoformat(),
                    'message': f"Anomaly detected in equipment {anomaly['equipment_id']}"
                }
                
                await self.redis_client.publish('alerts', json.dumps(alert_data))
            
            # Also call notification service directly
            await self.call_service(
                'notification',
                '/send_alert',
                {'alert': anomaly}
            )
            
        except Exception as e:
            logger.error(f"Error publishing anomaly alert: {e}")
    
    async def detect_anomalies_for_equipment(
        self, 
        equipment_ids: List[str], 
        time_range: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies for specific equipment and time range"""
        try:
            # Build query
            query = {}
            
            if equipment_ids:
                query['equipment_id'] = {'$in': equipment_ids}
            
            if time_range:
                if 'start' in time_range:
                    query.setdefault('timestamp', {})['$gte'] = pd.to_datetime(time_range['start'])
                if 'end' in time_range:
                    query.setdefault('timestamp', {})['$lte'] = pd.to_datetime(time_range['end'])
            
            # Get data
            cursor = self.collections['raw_data'].find(query)
            data = await asyncio.to_thread(list, cursor)
            
            if not data:
                return []
            
            df = pd.DataFrame(data)
            anomalies = await self._detect_anomalies_in_data(df)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies for equipment: {e}")
            return []
    
    async def predict_consumption(self, equipment_id: str, hours: int) -> Dict[str, Any]:
        """Predict energy consumption for equipment"""
        try:
            # Get historical data for the equipment
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)  # Use last 7 days for prediction
            
            query = {
                'equipment_id': equipment_id,
                'timestamp': {'$gte': start_time, '$lte': end_time}
            }
            
            cursor = self.collections['raw_data'].find(query).sort('timestamp', 1)
            data = await asyncio.to_thread(list, cursor)
            
            if len(data) < 10:  # Need minimum data points
                return {
                    'error': 'Insufficient historical data for prediction',
                    'equipment_id': equipment_id
                }
            
            df = pd.DataFrame(data)
            
            # Simple prediction based on recent trends
            # In production, use more sophisticated time series models
            recent_data = df.tail(24)  # Last 24 records
            avg_power = recent_data['voltage'].mean() * recent_data['current'].mean()
            
            # Generate predictions for next hours
            predictions = []
            base_time = datetime.now()
            
            for i in range(hours):
                pred_time = base_time + timedelta(hours=i)
                
                # Simple seasonal adjustment (peak hours vs off-peak)
                hour = pred_time.hour
                seasonal_factor = 1.2 if 8 <= hour <= 18 else 0.8
                
                predicted_power = avg_power * seasonal_factor
                
                predictions.append({
                    'timestamp': pred_time.isoformat(),
                    'predicted_power': float(predicted_power),
                    'confidence': 0.75  # Static confidence for now
                })
            
            # Store predictions in database
            prediction_doc = {
                'equipment_id': equipment_id,
                'generated_at': datetime.now(),
                'prediction_horizon_hours': hours,
                'predictions': predictions,
                'model_version': '1.0'
            }
            
            await asyncio.to_thread(
                self.collections['predictions'].insert_one,
                prediction_doc
            )
            
            return {
                'equipment_id': equipment_id,
                'predictions': predictions,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting consumption: {e}")
            return {'error': str(e), 'equipment_id': equipment_id}
    
    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        try:
            # Get anomaly counts
            anomaly_count = await asyncio.to_thread(
                self.collections['anomalies'].count_documents,
                {'detected_at': {'$gte': datetime.now() - timedelta(days=1)}}
            )
            
            # Get prediction counts
            prediction_count = await asyncio.to_thread(
                self.collections['predictions'].count_documents,
                {'generated_at': {'$gte': datetime.now() - timedelta(days=1)}}
            )
            
            # Get model information
            model_info = {}
            for model_name in self.models:
                model_info[model_name] = {
                    'loaded': True,
                    'type': type(self.models[model_name]).__name__
                }
            
            return {
                'anomalies_detected_24h': anomaly_count,
                'predictions_generated_24h': prediction_count,
                'models': model_info,
                'status': 'active',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return {'error': str(e)}
    
    async def process_new_data(self, data: Dict[str, Any]):
        """Process newly ingested data"""
        try:
            # This could trigger real-time analytics
            logger.info(f"Processing new data: {data}")
            
            # Run anomaly detection on new data if enough records
            if data.get('count', 0) > 100:
                await self._detect_recent_anomalies()
            
        except Exception as e:
            logger.error(f"Error processing new data: {e}")
    
    async def _generate_predictions(self):
        """Generate predictions for all active equipment"""
        try:
            # Get list of active equipment
            pipeline = [
                {'$group': {'_id': '$equipment_id', 'last_seen': {'$max': '$timestamp'}}},
                {'$match': {'last_seen': {'$gte': datetime.now() - timedelta(hours=2)}}}
            ]
            
            active_equipment = await asyncio.to_thread(
                list,
                self.collections['raw_data'].aggregate(pipeline)
            )
            
            # Generate predictions for each equipment
            for equipment in active_equipment:
                equipment_id = equipment['_id']
                await self.predict_consumption(equipment_id, 24)
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
    
    async def _update_analytics_cache(self):
        """Update analytics cache with summary data"""
        try:
            if not self.redis_client:
                return
            
            summary = await self.get_analytics_summary()
            await self.redis_client.setex(
                'analytics_summary',
                300,  # 5 minutes TTL
                json.dumps(summary, default=str)
            )
            
        except Exception as e:
            logger.error(f"Error updating analytics cache: {e}")
    
    async def health_check(self):
        """Service-specific health check"""
        # Check if models are loaded
        if not self.models:
            raise Exception("No ML models loaded")
        
        # Test model prediction
        test_data = np.array([[220, 5, 0.9, 25, 100]])  # Sample data
        if 'anomaly_detector' in self.models and 'anomaly_detector' in self.scalers:
            scaler = self.scalers['anomaly_detector']
            model = self.models['anomaly_detector']
            
            test_scaled = scaler.transform(test_data)
            model.predict(test_scaled)
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service-specific requests"""
        request_type = request_data.get('type')
        
        if request_type == 'detect_anomalies':
            return await self.detect_anomalies_for_equipment(
                request_data.get('equipment_ids', []),
                request_data.get('time_range', {})
            )
        elif request_type == 'predict':
            return await self.predict_consumption(
                request_data['equipment_id'],
                request_data.get('hours', 24)
            )
        elif request_type == 'summary':
            return await self.get_analytics_summary()
        else:
            raise ValueError(f"Unknown request type: {request_type}")


def create_analytics_service():
    """Factory function to create analytics service"""
    config_manager = ConfigManager("analytics")
    config = config_manager.get_all_config()
    
    return AnalyticsService(config)


async def run_service():
    """Run the analytics service"""
    service = create_analytics_service()
    await service.initialize()
    
    config = uvicorn.Config(
        service.app,
        host="0.0.0.0",
        port=service.config.get('port', 8002),
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    finally:
        await service.shutdown()


if __name__ == "__main__":
    asyncio.run(run_service())
