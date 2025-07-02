#!/usr/bin/env python3
"""
Enhanced Predictive Maintenance Service for EMS
Advanced ML models for equipment failure prediction, maintenance scheduling, and reliability analysis
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dataclasses import dataclass, asdict
import joblib
from pathlib import Path

# Advanced ML imports
from sklearn.ensemble import IsolationForest, RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
from sklearn.neural_network import MLPClassifier
import xgboost as xgb

# TensorFlow for deep learning
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logging.warning("TensorFlow not available. Install with: pip install tensorflow")

from common.base_service import BaseService

logger = logging.getLogger(__name__)


@dataclass
class MaintenanceAlert:
    """Maintenance alert data structure"""
    alert_id: str
    equipment_id: str
    alert_type: str
    severity: str
    failure_probability: float
    predicted_failure_date: Optional[datetime]
    recommended_actions: List[str]
    confidence: float
    created_at: datetime
    status: str = "active"


@dataclass
class EquipmentHealth:
    """Equipment health status"""
    equipment_id: str
    health_score: float
    degradation_rate: float
    remaining_useful_life: Optional[int]  # days
    maintenance_priority: str
    last_maintenance: Optional[datetime]
    next_maintenance: Optional[datetime]
    failure_modes: List[Dict[str, Any]]


@dataclass
class MaintenanceRecommendation:
    """Maintenance recommendation"""
    equipment_id: str
    maintenance_type: str
    priority: str
    estimated_cost: float
    estimated_duration: int  # hours
    required_resources: List[str]
    scheduling_window: Dict[str, datetime]
    cost_benefit_analysis: Dict[str, float]


class FailurePredictionModel:
    """Advanced failure prediction using multiple ML models"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.model_performance = {}
        
        # Initialize models
        self.models['random_forest'] = RandomForestRegressor(
            n_estimators=100, 
            max_depth=10, 
            random_state=42
        )
        self.models['xgboost'] = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        self.models['gradient_boosting'] = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        # Initialize scalers
        for model_name in self.models.keys():
            self.scalers[model_name] = StandardScaler()
    
    def prepare_features(self, sensor_data: List[Dict[str, Any]]) -> np.ndarray:
        """Prepare features for failure prediction"""
        if not sensor_data:
            return np.array([])
        
        df = pd.DataFrame(sensor_data)
        features = []
        
        # Statistical features
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if col in df.columns:
                values = df[col].dropna()
                if len(values) > 0:
                    features.extend([
                        values.mean(),
                        values.std(),
                        values.min(),
                        values.max(),
                        values.quantile(0.25),
                        values.quantile(0.75)
                    ])
        
        # Time-based features
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Trend features
            for col in numeric_columns:
                if col in df.columns and len(df[col].dropna()) > 1:
                    trend = np.polyfit(range(len(df)), df[col].fillna(0), 1)[0]
                    features.append(trend)
        
        # Vibration analysis features (if available)
        if 'vibration' in df.columns:
            vibration = df['vibration'].dropna()
            if len(vibration) > 0:
                # FFT features for frequency analysis
                fft = np.fft.fft(vibration.values)
                features.extend([
                    np.mean(np.abs(fft)),
                    np.std(np.abs(fft)),
                    np.max(np.abs(fft))
                ])
        
        # Temperature degradation features
        if 'temperature' in df.columns:
            temp = df['temperature'].dropna()
            if len(temp) > 0:
                # High temperature exposure
                high_temp_exposure = (temp > 60).sum() / len(temp)
                features.append(high_temp_exposure)
        
        return np.array(features).reshape(1, -1) if features else np.array([])
    
    def train_models(self, training_data: List[Dict[str, Any]], failure_labels: List[int]):
        """Train failure prediction models"""
        if not training_data or len(training_data) != len(failure_labels):
            logger.warning("Insufficient training data for failure prediction")
            return
        
        # Prepare features for all samples
        X = []
        for sample in training_data:
            features = self.prepare_features([sample])
            if features.size > 0:
                X.append(features.flatten())
        
        if not X:
            logger.warning("No valid features extracted from training data")
            return
        
        X = np.array(X)
        y = np.array(failure_labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train each model
        for model_name, model in self.models.items():
            try:
                # Scale features
                X_train_scaled = self.scalers[model_name].fit_transform(X_train)
                X_test_scaled = self.scalers[model_name].transform(X_test)
                
                # Train model
                if model_name == 'gradient_boosting':
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
                else:
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    y_pred_proba = y_pred  # For regression models
                
                # Calculate performance metrics
                if model_name == 'gradient_boosting':
                    self.model_performance[model_name] = {
                        'precision': precision_score(y_test, y_pred),
                        'recall': recall_score(y_test, y_pred),
                        'f1': f1_score(y_test, y_pred),
                        'auc': roc_auc_score(y_test, y_pred_proba)
                    }
                else:
                    self.model_performance[model_name] = {
                        'mse': np.mean((y_test - y_pred) ** 2),
                        'mae': np.mean(np.abs(y_test - y_pred)),
                        'r2': 1 - np.sum((y_test - y_pred) ** 2) / np.sum((y_test - np.mean(y_test)) ** 2)
                    }
                
                # Feature importance
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance[model_name] = model.feature_importances_
                
                logger.info(f"Trained {model_name} model successfully")
                
            except Exception as e:
                logger.error(f"Error training {model_name} model: {e}")
    
    def predict_failure(self, sensor_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Predict failure probability using ensemble of models"""
        features = self.prepare_features(sensor_data)
        
        if features.size == 0:
            return {"ensemble_probability": 0.0, "confidence": 0.0}
        
        predictions = {}
        
        for model_name, model in self.models.items():
            try:
                # Scale features
                features_scaled = self.scalers[model_name].transform(features)
                
                # Predict
                if model_name == 'gradient_boosting':
                    prediction = model.predict_proba(features_scaled)[0, 1]
                else:
                    prediction = max(0, min(1, model.predict(features_scaled)[0]))
                
                predictions[model_name] = prediction
                
            except Exception as e:
                logger.error(f"Error predicting with {model_name}: {e}")
                predictions[model_name] = 0.0
        
        # Ensemble prediction (weighted average)
        weights = {'random_forest': 0.3, 'xgboost': 0.4, 'gradient_boosting': 0.3}
        ensemble_pred = sum(predictions[name] * weights.get(name, 1/len(predictions)) 
                           for name in predictions) / sum(weights.values())
        
        # Calculate confidence based on agreement between models
        pred_values = list(predictions.values())
        confidence = 1.0 - (np.std(pred_values) if len(pred_values) > 1 else 0.0)
        
        return {
            "ensemble_probability": ensemble_pred,
            "individual_predictions": predictions,
            "confidence": confidence
        }


class MaintenanceScheduler:
    """Intelligent maintenance scheduling and optimization"""
    
    def __init__(self):
        self.maintenance_history = []
        self.equipment_profiles = {}
        self.resource_availability = {}
    
    def analyze_equipment_health(self, 
                               equipment_id: str,
                               sensor_data: List[Dict[str, Any]],
                               failure_prediction: Dict[str, float]) -> EquipmentHealth:
        """Analyze overall equipment health"""
        
        # Calculate health score (0-100)
        failure_prob = failure_prediction.get("ensemble_probability", 0.0)
        health_score = max(0, 100 - (failure_prob * 100))
        
        # Estimate degradation rate
        degradation_rate = self._calculate_degradation_rate(equipment_id, sensor_data)
        
        # Estimate remaining useful life
        remaining_life = self._estimate_remaining_life(health_score, degradation_rate)
        
        # Determine maintenance priority
        priority = (
            "critical" if failure_prob > 0.8 else
            "high" if failure_prob > 0.6 else
            "medium" if failure_prob > 0.4 else
            "low"
        )
        
        # Identify potential failure modes
        failure_modes = self._identify_failure_modes(sensor_data, failure_prediction)
        
        return EquipmentHealth(
            equipment_id=equipment_id,
            health_score=health_score,
            degradation_rate=degradation_rate,
            remaining_useful_life=remaining_life,
            maintenance_priority=priority,
            last_maintenance=self._get_last_maintenance(equipment_id),
            next_maintenance=self._calculate_next_maintenance(equipment_id, remaining_life),
            failure_modes=failure_modes
        )
    
    def generate_maintenance_recommendation(self, 
                                         equipment_health: EquipmentHealth) -> MaintenanceRecommendation:
        """Generate intelligent maintenance recommendations"""
        
        equipment_id = equipment_health.equipment_id
        
        # Determine maintenance type
        if equipment_health.maintenance_priority == "critical":
            maintenance_type = "emergency"
            estimated_cost = 5000.0
            estimated_duration = 8
        elif equipment_health.maintenance_priority == "high":
            maintenance_type = "preventive"
            estimated_cost = 2000.0
            estimated_duration = 4
        else:
            maintenance_type = "routine"
            estimated_cost = 500.0
            estimated_duration = 2
        
        # Calculate scheduling window
        if equipment_health.remaining_useful_life:
            days_ahead = max(1, equipment_health.remaining_useful_life - 7)
            start_date = datetime.now() + timedelta(days=days_ahead)
            end_date = start_date + timedelta(days=7)
        else:
            start_date = datetime.now()
            end_date = start_date + timedelta(days=1)
        
        # Required resources
        resources = self._determine_required_resources(maintenance_type, equipment_health.failure_modes)
        
        # Cost-benefit analysis
        cost_benefit = self._calculate_cost_benefit(equipment_health, estimated_cost)
        
        return MaintenanceRecommendation(
            equipment_id=equipment_id,
            maintenance_type=maintenance_type,
            priority=equipment_health.maintenance_priority,
            estimated_cost=estimated_cost,
            estimated_duration=estimated_duration,
            required_resources=resources,
            scheduling_window={
                "start": start_date,
                "end": end_date
            },
            cost_benefit_analysis=cost_benefit
        )
    
    def _calculate_degradation_rate(self, equipment_id: str, sensor_data: List[Dict[str, Any]]) -> float:
        """Calculate equipment degradation rate"""
        if not sensor_data:
            return 0.0
        
        df = pd.DataFrame(sensor_data)
        if 'timestamp' in df.columns and len(df) > 1:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate trends in key metrics
            degradation_indicators = []
            
            for metric in ['efficiency', 'vibration', 'temperature']:
                if metric in df.columns:
                    values = df[metric].dropna()
                    if len(values) > 1:
                        # Calculate slope (degradation)
                        x = np.arange(len(values))
                        slope = np.polyfit(x, values, 1)[0]
                        
                        # Normalize based on metric type
                        if metric == 'efficiency':
                            degradation_indicators.append(-slope)  # Negative slope is bad
                        else:
                            degradation_indicators.append(abs(slope))  # Increasing trend is bad
            
            return np.mean(degradation_indicators) if degradation_indicators else 0.0
        
        return 0.0
    
    def _estimate_remaining_life(self, health_score: float, degradation_rate: float) -> Optional[int]:
        """Estimate remaining useful life in days"""
        if degradation_rate <= 0:
            return None
        
        # Simple linear model: days = (health_score - threshold) / degradation_rate
        failure_threshold = 20  # Health score below which failure is likely
        if health_score <= failure_threshold:
            return 0
        
        remaining_days = (health_score - failure_threshold) / max(degradation_rate, 0.1)
        return max(1, int(remaining_days))
    
    def _identify_failure_modes(self, 
                              sensor_data: List[Dict[str, Any]], 
                              failure_prediction: Dict[str, float]) -> List[Dict[str, Any]]:
        """Identify potential failure modes"""
        failure_modes = []
        
        if not sensor_data:
            return failure_modes
        
        df = pd.DataFrame(sensor_data)
        
        # Temperature-related failures
        if 'temperature' in df.columns:
            avg_temp = df['temperature'].mean()
            if avg_temp > 60:
                failure_modes.append({
                    "mode": "thermal_degradation",
                    "probability": min(1.0, (avg_temp - 60) / 20),
                    "description": "High operating temperature causing component degradation"
                })
        
        # Vibration-related failures
        if 'vibration' in df.columns:
            avg_vibration = df['vibration'].mean()
            if avg_vibration > 5.0:  # Assuming 5.0 is high
                failure_modes.append({
                    "mode": "mechanical_wear",
                    "probability": min(1.0, (avg_vibration - 5.0) / 10),
                    "description": "Excessive vibration indicating mechanical wear"
                })
        
        # Electrical failures
        if 'voltage' in df.columns:
            voltage_std = df['voltage'].std()
            if voltage_std > 10:  # High voltage variation
                failure_modes.append({
                    "mode": "electrical_instability",
                    "probability": min(1.0, voltage_std / 20),
                    "description": "Voltage instability affecting equipment operation"
                })
        
        return failure_modes
    
    def _get_last_maintenance(self, equipment_id: str) -> Optional[datetime]:
        """Get last maintenance date for equipment"""
        # This would typically query a maintenance database
        # For now, return a simulated date
        return datetime.now() - timedelta(days=30)
    
    def _calculate_next_maintenance(self, equipment_id: str, remaining_life: Optional[int]) -> Optional[datetime]:
        """Calculate next maintenance date"""
        if remaining_life is None:
            return datetime.now() + timedelta(days=90)  # Standard interval
        
        # Schedule maintenance before predicted failure
        buffer_days = max(7, remaining_life // 4)
        return datetime.now() + timedelta(days=remaining_life - buffer_days)
    
    def _determine_required_resources(self, 
                                    maintenance_type: str, 
                                    failure_modes: List[Dict[str, Any]]) -> List[str]:
        """Determine required resources for maintenance"""
        resources = ["maintenance_technician"]
        
        if maintenance_type == "emergency":
            resources.extend(["spare_parts", "emergency_tools", "electrical_engineer"])
        
        # Add specific resources based on failure modes
        for mode in failure_modes:
            if mode["mode"] == "thermal_degradation":
                resources.append("cooling_specialist")
            elif mode["mode"] == "mechanical_wear":
                resources.append("mechanical_engineer")
            elif mode["mode"] == "electrical_instability":
                resources.append("electrical_engineer")
        
        return list(set(resources))  # Remove duplicates
    
    def _calculate_cost_benefit(self, 
                              equipment_health: EquipmentHealth, 
                              maintenance_cost: float) -> Dict[str, float]:
        """Calculate cost-benefit analysis for maintenance"""
        
        # Estimate cost of failure
        failure_cost = {
            "critical": 50000.0,
            "high": 20000.0,
            "medium": 5000.0,
            "low": 1000.0
        }.get(equipment_health.maintenance_priority, 5000.0)
        
        # Calculate potential savings
        potential_savings = failure_cost - maintenance_cost
        
        # ROI calculation
        roi = (potential_savings / maintenance_cost) * 100 if maintenance_cost > 0 else 0
        
        return {
            "maintenance_cost": maintenance_cost,
            "potential_failure_cost": failure_cost,
            "potential_savings": potential_savings,
            "roi_percentage": roi,
            "payback_period_days": 30  # Simplified calculation
        }


class PredictiveMaintenanceService(BaseService):
    """Enhanced Predictive Maintenance Service"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("predictive_maintenance", config)
        self.app = self._create_fastapi_app()
        self.failure_model = FailurePredictionModel()
        self.scheduler = MaintenanceScheduler()
        self.active_alerts = {}
        
    async def initialize(self):
        """Initialize predictive maintenance service"""
        await super().initialize()
        
        # Load pre-trained models if available
        await self._load_models()
        
        # Start background monitoring
        asyncio.create_task(self._background_monitoring())
        
        logger.info("Predictive maintenance service initialized")
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title="EMS Predictive Maintenance Service",
            description="Advanced predictive maintenance with ML/AI",
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
            return await self.health_check()
        
        @app.post("/predict_failure")
        async def predict_failure(request: Dict[str, Any]):
            """Predict equipment failure probability"""
            try:
                equipment_id = request.get("equipment_id")
                sensor_data = request.get("sensor_data", [])
                
                # Predict failure
                prediction = self.failure_model.predict_failure(sensor_data)
                
                # Analyze equipment health
                health = self.scheduler.analyze_equipment_health(
                    equipment_id, sensor_data, prediction
                )
                
                return {
                    "equipment_id": equipment_id,
                    "failure_prediction": prediction,
                    "equipment_health": asdict(health),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Failure prediction error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/maintenance_recommendation")
        async def get_maintenance_recommendation(request: Dict[str, Any]):
            """Get maintenance recommendations"""
            try:
                equipment_id = request.get("equipment_id")
                sensor_data = request.get("sensor_data", [])
                
                # Get failure prediction and health analysis
                prediction = self.failure_model.predict_failure(sensor_data)
                health = self.scheduler.analyze_equipment_health(
                    equipment_id, sensor_data, prediction
                )
                
                # Generate recommendation
                recommendation = self.scheduler.generate_maintenance_recommendation(health)
                
                return {
                    "equipment_id": equipment_id,
                    "recommendation": asdict(recommendation),
                    "equipment_health": asdict(health)
                }
                
            except Exception as e:
                logger.error(f"Maintenance recommendation error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/train_models")
        async def train_failure_models(request: Dict[str, Any]):
            """Train failure prediction models with new data"""
            try:
                training_data = request.get("training_data", [])
                failure_labels = request.get("failure_labels", [])
                
                # Train models
                self.failure_model.train_models(training_data, failure_labels)
                
                # Save models
                await self._save_models()
                
                return {
                    "status": "success",
                    "models_trained": len(self.failure_model.models),
                    "performance": self.failure_model.model_performance
                }
                
            except Exception as e:
                logger.error(f"Model training error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/alerts/active")
        async def get_active_alerts():
            """Get active maintenance alerts"""
            try:
                return {
                    "active_alerts": [asdict(alert) for alert in self.active_alerts.values()],
                    "total_count": len(self.active_alerts)
                }
                
            except Exception as e:
                logger.error(f"Error getting active alerts: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _load_models(self):
        """Load pre-trained models"""
        models_dir = Path("models/predictive_maintenance")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        for model_name in self.failure_model.models.keys():
            model_path = models_dir / f"{model_name}.joblib"
            scaler_path = models_dir / f"{model_name}_scaler.joblib"
            
            if model_path.exists() and scaler_path.exists():
                try:
                    self.failure_model.models[model_name] = joblib.load(model_path)
                    self.failure_model.scalers[model_name] = joblib.load(scaler_path)
                    logger.info(f"Loaded {model_name} model")
                except Exception as e:
                    logger.error(f"Error loading {model_name} model: {e}")
    
    async def _save_models(self):
        """Save trained models"""
        models_dir = Path("models/predictive_maintenance")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        for model_name, model in self.failure_model.models.items():
            try:
                model_path = models_dir / f"{model_name}.joblib"
                scaler_path = models_dir / f"{model_name}_scaler.joblib"
                
                joblib.dump(model, model_path)
                joblib.dump(self.failure_model.scalers[model_name], scaler_path)
                logger.info(f"Saved {model_name} model")
            except Exception as e:
                logger.error(f"Error saving {model_name} model: {e}")
    
    async def _background_monitoring(self):
        """Background task for continuous monitoring"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # This would typically pull data from the database
                # and check for equipment that needs attention
                logger.debug("Background monitoring check completed")
                
            except Exception as e:
                logger.error(f"Background monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def health_check(self):
        """Service-specific health check"""
        try:
            return {
                "status": "healthy",
                "service": self.service_name,
                "models_loaded": len([m for m in self.failure_model.models.values() if m is not None]),
                "active_alerts": len(self.active_alerts),
                "tensorflow_available": TENSORFLOW_AVAILABLE
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise Exception(f"Predictive maintenance service unhealthy: {e}")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service-specific requests"""
        request_type = request_data.get('type')
        
        if request_type == 'predict_failure':
            return await self.predict_failure(request_data)
        elif request_type == 'maintenance_recommendation':
            return await self.get_maintenance_recommendation(request_data)
        else:
            raise ValueError(f"Unknown request type: {request_type}")


def create_predictive_maintenance_service(config: Dict[str, Any] = None) -> PredictiveMaintenanceService:
    """Create and configure predictive maintenance service"""
    if config is None:
        config = {
            "model_update_interval": 3600,  # 1 hour
            "alert_threshold": 0.7,
            "monitoring_interval": 300  # 5 minutes
        }
    
    return PredictiveMaintenanceService(config)


# Example usage
if __name__ == "__main__":
    import uvicorn
    
    service = create_predictive_maintenance_service()
    uvicorn.run(service.app, host="0.0.0.0", port=8011)
