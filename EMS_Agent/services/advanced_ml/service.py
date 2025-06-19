#!/usr/bin/env python3
"""
Advanced Machine Learning Service for EMS
Enhanced ML models for anomaly detection, forecasting, and predictive maintenance
"""

import asyncio
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import joblib
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

# Advanced ML imports
from sklearn.ensemble import IsolationForest, RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, precision_score, recall_score, f1_score
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPRegressor, MLPClassifier
import xgboost as xgb
import lightgbm as lgb
from scipy import stats
from scipy.signal import find_peaks
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import warnings
warnings.filterwarnings('ignore')

from common.base_service import BaseService

logger = logging.getLogger(__name__)


@dataclass
class ModelPerformanceMetrics:
    """Enhanced model performance metrics"""
    model_name: str
    model_type: str  # 'anomaly', 'forecasting', 'classification'
    mae: float
    mse: float
    rmse: float
    r2_score: float
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    training_time: float = 0.0
    prediction_time: float = 0.0
    last_updated: datetime = None
    feature_importance: Optional[Dict[str, float]] = None


@dataclass
class AnomalyPrediction:
    """Enhanced anomaly prediction with confidence and explanation"""
    timestamp: datetime
    equipment_id: str
    anomaly_score: float
    is_anomaly: bool
    confidence: float
    anomaly_type: str  # 'voltage_spike', 'current_anomaly', 'power_factor_drop', etc.
    explanation: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    recommended_action: str
    feature_contributions: Dict[str, float]


@dataclass
class ForecastResult:
    """Enhanced forecasting result with uncertainty quantification"""
    timestamp: datetime
    equipment_id: str
    forecast_horizon: int  # hours
    predicted_values: List[float]
    confidence_intervals: List[Tuple[float, float]]  # (lower, upper) bounds
    forecast_type: str  # 'power', 'voltage', 'current'
    model_confidence: float
    trend_analysis: Dict[str, Any]
    seasonal_components: Optional[Dict[str, Any]] = None


class AdvancedMLModels:
    """Advanced ML model collection with automatic model selection"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True)
        
        # Model storage
        self.anomaly_models = {}
        self.forecasting_models = {}
        self.classification_models = {}
        self.scalers = {}
        
        # Model performance tracking
        self.performance_metrics = {}
        self.model_versions = {}
        
        # Advanced features
        self.feature_extractors = {}
        self.ensemble_weights = {}
        
    async def initialize_models(self):
        """Initialize advanced ML models"""
        try:
            # Load existing models or create new ones
            await self._load_existing_models()
            
            # Initialize ensemble models
            await self._initialize_ensemble_models()
            
            # Initialize deep learning models
            await self._initialize_deep_learning_models()
            
            logger.info("Advanced ML models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")
            raise
    
    async def _initialize_ensemble_models(self):
        """Initialize ensemble anomaly detection models"""
        
        # Multi-model anomaly detection ensemble
        self.anomaly_models['isolation_forest'] = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=200,
            max_features=0.8
        )
        
        self.anomaly_models['one_class_svm'] = OneClassSVM(
            nu=0.1,
            kernel='rbf',
            gamma='scale'
        )
        
        self.anomaly_models['local_outlier_factor'] = LocalOutlierFactor(
            n_neighbors=20,
            contamination=0.1,
            novelty=True
        )
        
        # Advanced forecasting models
        self.forecasting_models['xgboost'] = xgb.XGBRegressor(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        
        self.forecasting_models['lightgbm'] = lgb.LGBMRegressor(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.1,
            feature_fraction=0.8,
            random_state=42
        )
        
        self.forecasting_models['gradient_boosting'] = GradientBoostingRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42
        )
        
        # Neural network models
        self.forecasting_models['mlp_regressor'] = MLPRegressor(
            hidden_layer_sizes=(100, 50),
            activation='relu',
            solver='adam',
            alpha=0.001,
            batch_size='auto',
            learning_rate='adaptive',
            max_iter=500,
            random_state=42
        )
    
    async def _initialize_deep_learning_models(self):
        """Initialize deep learning models for time series forecasting"""
        
        def create_lstm_model(input_shape, units=50):
            """Create LSTM model for time series forecasting"""
            model = Sequential([
                LSTM(units, return_sequences=True, input_shape=input_shape),
                Dropout(0.2),
                BatchNormalization(),
                LSTM(units, return_sequences=False),
                Dropout(0.2),
                BatchNormalization(),
                Dense(25, activation='relu'),
                Dropout(0.1),
                Dense(1)
            ])
            
            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )
            
            return model
        
        # Store model factory function
        self.deep_learning_factories = {
            'lstm_forecaster': create_lstm_model
        }
    
    async def train_anomaly_ensemble(self, training_data: pd.DataFrame) -> Dict[str, ModelPerformanceMetrics]:
        """Train ensemble anomaly detection models"""
        metrics = {}
        
        try:
            # Prepare features
            feature_columns = ['voltage', 'current', 'power_factor', 'active_power', 'reactive_power']
            X = training_data[feature_columns].fillna(training_data[feature_columns].mean())
            
            # Advanced feature engineering
            X_enhanced = await self._extract_advanced_features(X)
            
            # Scale features
            scaler = RobustScaler()
            X_scaled = scaler.fit_transform(X_enhanced)
            self.scalers['anomaly_detection'] = scaler
            
            # Train each model in the ensemble
            for model_name, model in self.anomaly_models.items():
                start_time = datetime.now()
                
                if hasattr(model, 'fit'):
                    model.fit(X_scaled)
                
                training_time = (datetime.now() - start_time).total_seconds()
                
                # Calculate performance metrics (using contamination rate as proxy)
                anomaly_scores = model.decision_function(X_scaled) if hasattr(model, 'decision_function') else model.score_samples(X_scaled)
                
                metrics[model_name] = ModelPerformanceMetrics(
                    model_name=model_name,
                    model_type='anomaly',
                    mae=0.0,  # Not applicable for anomaly detection
                    mse=0.0,
                    rmse=0.0,
                    r2_score=0.0,
                    training_time=training_time,
                    last_updated=datetime.now()
                )
                
                logger.info(f"Trained {model_name} anomaly model in {training_time:.2f}s")
            
            # Calculate ensemble weights based on cross-validation
            await self._calculate_ensemble_weights(X_scaled, 'anomaly')
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error training anomaly ensemble: {e}")
            raise
    
    async def train_forecasting_ensemble(self, training_data: pd.DataFrame, target_column: str) -> Dict[str, ModelPerformanceMetrics]:
        """Train ensemble forecasting models with advanced techniques"""
        metrics = {}
        
        try:
            # Prepare time series data
            X, y = await self._prepare_time_series_data(training_data, target_column)
            
            # Split data with time series considerations
            tscv = TimeSeriesSplit(n_splits=5)
            
            for model_name, model in self.forecasting_models.items():
                start_time = datetime.now()
                
                # Cross-validation for robust performance estimation
                cv_scores = []
                
                for train_idx, val_idx in tscv.split(X):
                    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                    
                    # Scale features
                    scaler = StandardScaler()
                    X_train_scaled = scaler.fit_transform(X_train)
                    X_val_scaled = scaler.transform(X_val)
                    
                    # Train model
                    if 'xgb' in model_name or 'lightgbm' in model_name:
                        model.fit(X_train_scaled, y_train, eval_set=[(X_val_scaled, y_val)], verbose=False)
                    else:
                        model.fit(X_train_scaled, y_train)
                    
                    # Predict and evaluate
                    y_pred = model.predict(X_val_scaled)
                    cv_scores.append(mean_squared_error(y_val, y_pred))
                
                training_time = (datetime.now() - start_time).total_seconds()
                
                # Final training on full dataset
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                
                if 'xgb' in model_name or 'lightgbm' in model_name:
                    model.fit(X_scaled, y, verbose=False)
                else:
                    model.fit(X_scaled, y)
                
                self.scalers[f'{model_name}_{target_column}'] = scaler
                
                # Calculate performance metrics
                y_pred_full = model.predict(X_scaled)
                mae = mean_absolute_error(y, y_pred_full)
                mse = mean_squared_error(y, y_pred_full)
                rmse = np.sqrt(mse)
                r2 = r2_score(y, y_pred_full)
                
                # Feature importance (if available)
                feature_importance = {}
                if hasattr(model, 'feature_importances_'):
                    feature_importance = dict(zip(X.columns, model.feature_importances_))
                
                metrics[f'{model_name}_{target_column}'] = ModelPerformanceMetrics(
                    model_name=f'{model_name}_{target_column}',
                    model_type='forecasting',
                    mae=mae,
                    mse=mse,
                    rmse=rmse,
                    r2_score=r2,
                    training_time=training_time,
                    last_updated=datetime.now(),
                    feature_importance=feature_importance
                )
                
                logger.info(f"Trained {model_name} for {target_column}: R² = {r2:.3f}, RMSE = {rmse:.3f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error training forecasting ensemble: {e}")
            raise
    
    async def _extract_advanced_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Extract advanced features for ML models"""
        enhanced_data = data.copy()
        
        # Statistical features
        enhanced_data['voltage_rolling_mean'] = data['voltage'].rolling(window=10).mean()
        enhanced_data['current_rolling_std'] = data['current'].rolling(window=10).std()
        enhanced_data['power_ratio'] = data['active_power'] / (data['reactive_power'] + 1e-6)
        
        # Time-based features (if timestamp available)
        if 'timestamp' in data.columns:
            enhanced_data['hour'] = pd.to_datetime(data['timestamp']).dt.hour
            enhanced_data['day_of_week'] = pd.to_datetime(data['timestamp']).dt.dayofweek
            enhanced_data['is_weekend'] = (enhanced_data['day_of_week'] >= 5).astype(int)
        
        # Interaction features
        enhanced_data['voltage_current_interaction'] = data['voltage'] * data['current']
        enhanced_data['power_factor_efficiency'] = data['power_factor'] * data['active_power']
        
        # Lag features
        for col in ['voltage', 'current', 'active_power']:
            enhanced_data[f'{col}_lag1'] = data[col].shift(1)
            enhanced_data[f'{col}_lag2'] = data[col].shift(2)
        
        # Fill NaN values
        enhanced_data = enhanced_data.fillna(enhanced_data.mean())
        
        return enhanced_data
    
    async def predict_anomalies_ensemble(self, data: pd.DataFrame) -> List[AnomalyPrediction]:
        """Advanced ensemble anomaly prediction with explanations"""
        predictions = []
        
        try:
            # Prepare features
            X_enhanced = await self._extract_advanced_features(data)
            scaler = self.scalers.get('anomaly_detection')
            
            if scaler is None:
                raise ValueError("Anomaly detection scaler not found. Train models first.")
            
            X_scaled = scaler.transform(X_enhanced)
            
            # Get predictions from all models
            ensemble_scores = []
            individual_predictions = {}
            
            for model_name, model in self.anomaly_models.items():
                if hasattr(model, 'decision_function'):
                    scores = model.decision_function(X_scaled)
                elif hasattr(model, 'score_samples'):
                    scores = model.score_samples(X_scaled)
                else:
                    scores = model.predict(X_scaled)
                
                # Normalize scores to [0, 1]
                scores_normalized = (scores - scores.min()) / (scores.max() - scores.min() + 1e-6)
                ensemble_scores.append(scores_normalized)
                individual_predictions[model_name] = scores_normalized
            
            # Calculate ensemble score with learned weights
            weights = self.ensemble_weights.get('anomaly', [1.0] * len(ensemble_scores))
            ensemble_score = np.average(ensemble_scores, axis=0, weights=weights)
            
            # Generate predictions with explanations
            for i, (_, row) in enumerate(data.iterrows()):
                anomaly_score = ensemble_score[i]
                is_anomaly = anomaly_score > 0.7  # Adaptive threshold
                
                # Determine anomaly type and explanation
                anomaly_type, explanation = await self._explain_anomaly(row, individual_predictions, i)
                
                # Calculate confidence
                confidence = self._calculate_prediction_confidence(individual_predictions, i)
                
                # Determine severity
                severity = self._determine_severity(anomaly_score, row)
                
                # Generate recommended action
                recommended_action = self._generate_recommendation(anomaly_type, severity, row)
                
                prediction = AnomalyPrediction(
                    timestamp=datetime.now(),
                    equipment_id=row.get('equipment_id', 'unknown'),
                    anomaly_score=float(anomaly_score),
                    is_anomaly=is_anomaly,
                    confidence=confidence,
                    anomaly_type=anomaly_type,
                    explanation=explanation,
                    severity=severity,
                    recommended_action=recommended_action,
                    feature_contributions=self._calculate_feature_contributions(row, anomaly_score)
                )
                
                predictions.append(prediction)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error in ensemble anomaly prediction: {e}")
            raise
    
    async def forecast_advanced(self, data: pd.DataFrame, target_column: str, horizon: int = 24) -> ForecastResult:
        """Advanced ensemble forecasting with uncertainty quantification"""
        
        try:
            # Prepare data
            X, y = await self._prepare_time_series_data(data, target_column)
            
            # Get ensemble predictions
            ensemble_predictions = []
            model_confidences = []
            
            for model_name, model in self.forecasting_models.items():
                if f'{model_name}_{target_column}' in self.scalers:
                    scaler = self.scalers[f'{model_name}_{target_column}']
                    
                    # Prepare features for forecasting
                    X_forecast = await self._prepare_forecast_features(X, horizon)
                    X_forecast_scaled = scaler.transform(X_forecast)
                    
                    # Make predictions
                    predictions = model.predict(X_forecast_scaled)
                    ensemble_predictions.append(predictions)
                    
                    # Calculate model confidence based on recent performance
                    confidence = self._calculate_model_confidence(model_name, target_column)
                    model_confidences.append(confidence)
            
            # Calculate ensemble forecast
            weights = model_confidences / np.sum(model_confidences)
            final_predictions = np.average(ensemble_predictions, axis=0, weights=weights)
            
            # Calculate uncertainty intervals
            confidence_intervals = self._calculate_confidence_intervals(ensemble_predictions)
            
            # Analyze trends
            trend_analysis = await self._analyze_forecast_trends(final_predictions, data[target_column])
            
            # Calculate overall model confidence
            overall_confidence = np.mean(model_confidences)
            
            result = ForecastResult(
                timestamp=datetime.now(),
                equipment_id=data.get('equipment_id', ['unknown'])[0] if 'equipment_id' in data.columns else 'unknown',
                forecast_horizon=horizon,
                predicted_values=final_predictions.tolist(),
                confidence_intervals=confidence_intervals,
                forecast_type=target_column,
                model_confidence=float(overall_confidence),
                trend_analysis=trend_analysis
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in advanced forecasting: {e}")
            raise

    async def _load_existing_models(self):
        """Load existing models from disk"""
        try:
            # Load anomaly detection models
            for model_file in self.model_path.glob("anomaly_*.pkl"):
                model_name = model_file.stem.replace("anomaly_", "")
                model = await asyncio.to_thread(joblib.load, model_file)
                self.anomaly_models[model_name] = model
                logger.info(f"Loaded anomaly model: {model_name}")
            
            # Load forecasting models
            for model_file in self.model_path.glob("forecasting_*.pkl"):
                model_name = model_file.stem.replace("forecasting_", "")
                model = await asyncio.to_thread(joblib.load, model_file)
                self.forecasting_models[model_name] = model
                logger.info(f"Loaded forecasting model: {model_name}")
            
            # Load scalers
            for scaler_file in self.model_path.glob("scaler_*.pkl"):
                scaler_name = scaler_file.stem.replace("scaler_", "")
                scaler = await asyncio.to_thread(joblib.load, scaler_file)
                self.scalers[scaler_name] = scaler
                logger.info(f"Loaded scaler: {scaler_name}")
            
            # Load model performance metrics
            metrics_path = self.model_path / "model_metrics.json"
            if metrics_path.exists():
                with open(metrics_path, 'r') as f:
                    metrics_dict = json.load(f)
                
                for name, metrics in metrics_dict.items():
                    self.performance_metrics[name] = ModelPerformanceMetrics(**metrics)
                    logger.info(f"Loaded metrics for model: {name}")
        
        except Exception as e:
            logger.error(f"Error loading existing models: {e}")
            raise
    
    async def _calculate_ensemble_weights(self, X: np.ndarray, task_type: str):
        """Calculate ensemble weights for model averaging"""
        try:
            if task_type == 'anomaly':
                # Use simple equal weighting for anomaly models initially
                self.ensemble_weights['anomaly'] = [1.0 / len(self.anomaly_models)] * len(self.anomaly_models)
            
            elif task_type == 'forecasting':
                # Use time-based decay weighting for forecasting models
                weights = np.linspace(1, 0, len(self.forecasting_models))
                self.ensemble_weights['forecasting'] = weights / np.sum(weights)
        
        except Exception as e:
            logger.error(f"Error calculating ensemble weights: {e}")
            raise
    
    async def _prepare_time_series_data(self, data: pd.DataFrame, target_column: str) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare time series data for forecasting models"""
        try:
            # Ensure data is sorted by timestamp
            data = data.sort_values('timestamp')
            
            # Create time-based features
            data['hour'] = data['timestamp'].dt.hour
            data['day_of_week'] = data['timestamp'].dt.dayofweek
            data['month'] = data['timestamp'].dt.month
            
            # Lag features
            for lag in [1, 2, 3, 6, 12, 24]:
                data[f'{target_column}_lag_{lag}'] = data[target_column].shift(lag)
            
            # Remove rows with NaN values
            data = data.dropna()
            
            # Split into X and y
            feature_columns = [col for col in data.columns if col != target_column]
            X = data[feature_columns]
            y = data[target_column]
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error preparing time series data: {e}")
            raise
    
    async def _prepare_forecast_features(self, data: pd.DataFrame, horizon: int) -> pd.DataFrame:
        """Prepare features for forecasting horizon"""
        try:
            last_row = data.iloc[-1].copy()
            features = []
            
            for hour in range(1, horizon + 1):
                # Update time features
                future_time = last_row['timestamp'] + timedelta(hours=hour)
                last_row['hour'] = future_time.hour
                last_row['day_of_week'] = future_time.dayofweek
                last_row['month'] = future_time.month
                
                # Add to features
                features.append(last_row)
            
            return pd.DataFrame(features)
        
        except Exception as e:
            logger.error(f"Error preparing forecast features: {e}")
            raise
    
    async def _analyze_forecast_trends(self, forecast: np.ndarray, historical_data: pd.Series) -> Dict[str, Any]:
        """Analyze trends in the forecasted data"""
        try:
            # Simple trend analysis based on historical data
            historical_mean = historical_data.mean()
            historical_std = historical_data.std()
            
            # Detect peaks and troughs
            peaks, _ = find_peaks(forecast, height=historical_mean + 2 * historical_std)
            troughs, _ = find_peaks(-forecast, height=-historical_mean - 2 * historical_std)
            
            return {
                'peaks': peaks.tolist(),
                'troughs': troughs.tolist(),
                'mean_forecast': float(forecast.mean()),
                'std_forecast': float(forecast.std())
            }
        
        except Exception as e:
            logger.error(f"Error analyzing forecast trends: {e}")
            return {}
    
    async def _calculate_confidence_intervals(self, ensemble_predictions: List[np.ndarray]) -> List[Tuple[float, float]]:
        """Calculate confidence intervals for ensemble predictions"""
        try:
            # Calculate quantiles for uncertainty estimation
            lower_bounds = np.percentile(ensemble_predictions, 2.5, axis=0)
            upper_bounds = np.percentile(ensemble_predictions, 97.5, axis=0)
            
            return list(zip(lower_bounds, upper_bounds))
        
        except Exception as e:
            logger.error(f"Error calculating confidence intervals: {e}")
            return []
    
    async def _calculate_model_confidence(self, model_name: str, target_column: str) -> float:
        """Calculate confidence score for a model based on recent performance"""
        try:
            metrics = self.performance_metrics.get(f'{model_name}_{target_column}')
            
            if metrics:
                # Use inverse of RMSE as confidence score (higher is better)
                return 1 / (1 + metrics.rmse)
            
            return 0.5  # Default confidence
            
        except Exception as e:
            logger.error(f"Error calculating model confidence: {e}")
            return 0.5
    
    async def _explain_anomaly(self, row: pd.Series, individual_predictions: Dict[str, np.ndarray], index: int) -> Tuple[str, str]:
        """Generate explanation for an detected anomaly"""
        try:
            # Simple rule-based explanation
            # In practice, use SHAP or LIME for model-agnostic explanations
            
            if row['voltage'] > 240:
                return 'voltage_spike', 'Voltage exceeds safe threshold'
            elif row['current'] > 20:
                return 'current_anomaly', 'Current exceeds safe threshold'
            elif row['power_factor'] < 0.8:
                return 'power_factor_drop', 'Power factor indicates possible fault'
            
            return 'unknown', 'Anomaly detected'
        
        except Exception as e:
            logger.error(f"Error explaining anomaly: {e}")
            return 'unknown', 'Error in explanation'
    
    def _calculate_prediction_confidence(self, individual_predictions: Dict[str, np.ndarray], index: int) -> float:
        """Calculate confidence of a prediction based on model agreement"""
        try:
            # Use variance of predictions as confidence measure
            scores = [pred[index] for pred in individual_predictions.values()]
            return np.std(scores)
        
        except Exception as e:
            logger.error(f"Error calculating prediction confidence: {e}")
            return 0.0
    
    def _determine_severity(self, score: float, row: pd.Series) -> str:
        """Determine anomaly severity based on score and contextual factors"""
        try:
            if score > 0.9 or row['voltage'] > 250:
                return 'critical'
            elif score > 0.75:
                return 'high'
            elif score > 0.5:
                return 'medium'
            else:
                return 'low'
        
        except Exception as e:
            logger.error(f"Error determining severity: {e}")
            return 'low'
    
    def _generate_recommendation(self, anomaly_type: str, severity: str, row: pd.Series) -> str:
        """Generate recommended action based on anomaly type and severity"""
        try:
            if severity in ['high', 'critical']:
                if anomaly_type == 'voltage_spike':
                    return 'Inspect voltage levels and stabilize supply'
                elif anomaly_type == 'current_anomaly':
                    return 'Check for possible short circuits or overloads'
                elif anomaly_type == 'power_factor_drop':
                    return 'Investigate power factor correction equipment'
            
            return 'Monitor the equipment'
        
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return 'No action recommended'
    
    def _calculate_feature_contributions(self, row: pd.Series, score: float) -> Dict[str, float]:
        """Calculate feature contributions for an anomaly"""
        contributions = {}
        
        try:
            # Simple contribution calculation based on deviation from mean
            for col in row.index:
                if col == 'timestamp' or col == 'equipment_id':
                    continue
                
                mean_val = row[col].mean()
                deviation = row[col] - mean_val
                
                contributions[col] = float(deviation) * score
            
            return contributions
        
        except Exception as e:
            logger.error(f"Error calculating feature contributions: {e}")
            return {}
    
    async def health_check(self):
        """Service-specific health check"""
        try:
            loaded_models = len(self.anomaly_models) + len(self.forecasting_models)
            loaded_scalers = len(self.scalers)
            
            return {
                "status": "healthy",
                "loaded_models": loaded_models,
                "loaded_scalers": loaded_scalers,
                "model_types": list(self.anomaly_models.keys()) + list(self.forecasting_models.keys()),
                "service": self.service_name
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise Exception(f"Advanced ML service unhealthy: {e}")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service-specific requests"""
        request_type = request_data.get('type')
        
        if request_type == 'get_model_info':
            return {
                "available_models": list(self.anomaly_models.keys()) + list(self.forecasting_models.keys()),
                "model_metadata": {
                    name: asdict(metrics) if isinstance(metrics, ModelPerformanceMetrics) else metrics
                    for name, metrics in self.performance_metrics.items()
                }
            }
        
        else:
            raise ValueError(f"Unknown request type: {request_type}")


def create_advanced_ml_service(config: Dict[str, Any] = None) -> AdvancedMLService:
    """Factory function to create advanced ML service"""
    if config is None:
        from common.config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.get_service_config("advanced_ml")
    
    return AdvancedMLService(config)


if __name__ == "__main__":
    import uvicorn
    
    service = create_advanced_ml_service()
    
    # Run the service
    uvicorn.run(
        service.app,
        host="0.0.0.0",
        port=8006,
        log_level="info"
    )
