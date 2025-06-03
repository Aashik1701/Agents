from typing import Dict, List, Any, Optional
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import structlog
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models import SensorData, Equipment, Anomaly
from app.services.websocket_manager import websocket_manager

logger = structlog.get_logger()


class AnomalyDetector:
    """Real-time anomaly detection service"""
    
    def __init__(self):
        self.running = False
        self.detection_task = None
        self.thresholds = {
            "voltage_spike": {"threshold": 1.1, "baseline_multiplier": True},
            "voltage_drop": {"threshold": 0.9, "baseline_multiplier": True},
            "zero_current": {"threshold": 0.1, "duration_minutes": 5},
            "high_temperature": {"threshold": 80.0, "unit": "celsius"},
            "low_power_factor": {"threshold": 0.8, "duration_minutes": 10},
            "frequency_deviation": {"threshold": 2.0, "nominal": 50.0}  # ±2Hz from 50Hz
        }
    
    async def initialize(self):
        """Initialize anomaly detection service"""
        logger.info("Initializing anomaly detector")
        self.running = True
        self.detection_task = asyncio.create_task(self._detection_loop())
        logger.info("Anomaly detector initialized")
    
    async def cleanup(self):
        """Cleanup anomaly detection service"""
        self.running = False
        if self.detection_task:
            self.detection_task.cancel()
            try:
                await self.detection_task
            except asyncio.CancelledError:
                pass
        logger.info("Anomaly detector cleanup completed")
    
    async def _detection_loop(self):
        """Main detection loop that runs continuously"""
        while self.running:
            try:
                await self._run_detection_cycle()
                await asyncio.sleep(30)  # Run every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in detection loop", error=str(e))
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _run_detection_cycle(self):
        """Run a single detection cycle"""
        logger.debug("Running anomaly detection cycle")
        
        async with async_session_maker() as session:
            # Get recent sensor data (last 10 minutes)
            cutoff_time = datetime.now() - timedelta(minutes=10)
            
            query = select(SensorData).where(
                SensorData.timestamp >= cutoff_time
            ).order_by(SensorData.timestamp.desc())
            
            result = await session.execute(query)
            recent_data = result.scalars().all()
            
            if not recent_data:
                return
            
            # Group data by equipment
            equipment_data = {}
            for data_point in recent_data:
                if data_point.equipment_id not in equipment_data:
                    equipment_data[data_point.equipment_id] = []
                equipment_data[data_point.equipment_id].append(data_point)
            
            # Run detection algorithms for each equipment
            for equipment_id, data_points in equipment_data.items():
                await self._detect_equipment_anomalies(session, equipment_id, data_points)
    
    async def _detect_equipment_anomalies(self, session: AsyncSession, equipment_id: int, data_points: List[SensorData]):
        """Detect anomalies for a specific equipment"""
        if not data_points:
            return
        
        # Get equipment info
        equipment = await session.get(Equipment, equipment_id)
        if not equipment:
            return
        
        # Sort data points by timestamp
        data_points.sort(key=lambda x: x.timestamp)
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([
            {
                'timestamp': dp.timestamp,
                'voltage': dp.voltage,
                'current': dp.current,
                'power': dp.power,
                'power_factor': dp.power_factor,
                'frequency': dp.frequency,
                'temperature': dp.temperature
            }
            for dp in data_points
        ])
        
        if df.empty:
            return
        
        anomalies = []
        
        # 1. Zero Current Detection
        zero_current_anomaly = await self._detect_zero_current(df, equipment)
        if zero_current_anomaly:
            anomalies.append(zero_current_anomaly)
        
        # 2. Voltage Spike/Drop Detection
        voltage_anomalies = await self._detect_voltage_anomalies(df, equipment)
        anomalies.extend(voltage_anomalies)
        
        # 3. High Temperature Detection
        temp_anomaly = await self._detect_high_temperature(df, equipment)
        if temp_anomaly:
            anomalies.append(temp_anomaly)
        
        # 4. Low Power Factor Detection
        pf_anomaly = await self._detect_low_power_factor(df, equipment)
        if pf_anomaly:
            anomalies.append(pf_anomaly)
        
        # 5. Frequency Deviation Detection
        freq_anomaly = await self._detect_frequency_deviation(df, equipment)
        if freq_anomaly:
            anomalies.append(freq_anomaly)
        
        # Save anomalies to database and send alerts
        for anomaly_data in anomalies:
            await self._save_and_alert_anomaly(session, anomaly_data)
    
    async def _detect_zero_current(self, df: pd.DataFrame, equipment: Equipment) -> Optional[Dict[str, Any]]:
        """Detect zero current anomaly"""
        if df['current'].isna().all():
            return None
        
        # Check if current has been near zero for extended period
        threshold = self.thresholds["zero_current"]["threshold"]
        duration_minutes = self.thresholds["zero_current"]["duration_minutes"]
        
        zero_current_points = df[df['current'] <= threshold]
        
        if len(zero_current_points) >= 3:  # At least 3 data points showing zero current
            latest_timestamp = df['timestamp'].max()
            earliest_zero = zero_current_points['timestamp'].min()
            
            duration = (latest_timestamp - earliest_zero).total_seconds() / 60
            
            if duration >= duration_minutes:
                return {
                    "equipment_id": equipment.id,
                    "type": "zero_current",
                    "severity": "high",
                    "description": f"Equipment {equipment.equipment_id} showing zero current for {duration:.1f} minutes",
                    "detected_at": latest_timestamp,
                    "measured_value": float(df['current'].iloc[-1]),
                    "expected_value": equipment.rated_current or 10.0,
                    "threshold_value": threshold,
                    "context_data": {
                        "duration_minutes": duration,
                        "equipment_name": equipment.name,
                        "equipment_type": equipment.type
                    }
                }
        
        return None
    
    async def _detect_voltage_anomalies(self, df: pd.DataFrame, equipment: Equipment) -> List[Dict[str, Any]]:
        """Detect voltage spikes and drops"""
        anomalies = []
        
        if df['voltage'].isna().all():
            return anomalies
        
        # Calculate baseline voltage (median of recent readings)
        baseline_voltage = df['voltage'].median()
        rated_voltage = equipment.rated_voltage or baseline_voltage or 230.0
        
        # Detect spikes (>10% above rated)
        spike_threshold = rated_voltage * self.thresholds["voltage_spike"]["threshold"]
        voltage_spikes = df[df['voltage'] > spike_threshold]
        
        if not voltage_spikes.empty:
            max_spike = voltage_spikes['voltage'].max()
            spike_time = voltage_spikes.loc[voltage_spikes['voltage'].idxmax(), 'timestamp']
            
            anomalies.append({
                "equipment_id": equipment.id,
                "type": "voltage_spike",
                "severity": "high" if max_spike > rated_voltage * 1.2 else "medium",
                "description": f"Voltage spike detected on {equipment.equipment_id}: {max_spike:.1f}V",
                "detected_at": spike_time,
                "measured_value": float(max_spike),
                "expected_value": rated_voltage,
                "threshold_value": spike_threshold,
                "context_data": {
                    "baseline_voltage": baseline_voltage,
                    "equipment_name": equipment.name
                }
            })
        
        # Detect drops (<10% below rated)
        drop_threshold = rated_voltage * self.thresholds["voltage_drop"]["threshold"]
        voltage_drops = df[df['voltage'] < drop_threshold]
        
        if not voltage_drops.empty:
            min_drop = voltage_drops['voltage'].min()
            drop_time = voltage_drops.loc[voltage_drops['voltage'].idxmin(), 'timestamp']
            
            anomalies.append({
                "equipment_id": equipment.id,
                "type": "voltage_drop",
                "severity": "medium",
                "description": f"Voltage drop detected on {equipment.equipment_id}: {min_drop:.1f}V",
                "detected_at": drop_time,
                "measured_value": float(min_drop),
                "expected_value": rated_voltage,
                "threshold_value": drop_threshold,
                "context_data": {
                    "baseline_voltage": baseline_voltage,
                    "equipment_name": equipment.name
                }
            })
        
        return anomalies
    
    async def _detect_high_temperature(self, df: pd.DataFrame, equipment: Equipment) -> Optional[Dict[str, Any]]:
        """Detect high temperature anomaly"""
        if df['temperature'].isna().all():
            return None
        
        threshold = self.thresholds["high_temperature"]["threshold"]
        high_temp_points = df[df['temperature'] > threshold]
        
        if not high_temp_points.empty:
            max_temp = high_temp_points['temperature'].max()
            temp_time = high_temp_points.loc[high_temp_points['temperature'].idxmax(), 'timestamp']
            
            severity = "critical" if max_temp > 90 else "high" if max_temp > 85 else "medium"
            
            return {
                "equipment_id": equipment.id,
                "type": "high_temperature",
                "severity": severity,
                "description": f"High temperature detected on {equipment.equipment_id}: {max_temp:.1f}°C",
                "detected_at": temp_time,
                "measured_value": float(max_temp),
                "expected_value": 70.0,  # Normal operating temperature
                "threshold_value": threshold,
                "context_data": {
                    "equipment_name": equipment.name,
                    "equipment_type": equipment.type
                }
            }
        
        return None
    
    async def _detect_low_power_factor(self, df: pd.DataFrame, equipment: Equipment) -> Optional[Dict[str, Any]]:
        """Detect low power factor anomaly"""
        if df['power_factor'].isna().all():
            return None
        
        threshold = self.thresholds["low_power_factor"]["threshold"]
        low_pf_points = df[df['power_factor'] < threshold]
        
        if len(low_pf_points) >= 3:  # Consistent low power factor
            avg_pf = low_pf_points['power_factor'].mean()
            latest_time = low_pf_points['timestamp'].max()
            
            return {
                "equipment_id": equipment.id,
                "type": "low_power_factor",
                "severity": "medium",
                "description": f"Low power factor detected on {equipment.equipment_id}: {avg_pf:.2f}",
                "detected_at": latest_time,
                "measured_value": float(avg_pf),
                "expected_value": 0.95,
                "threshold_value": threshold,
                "context_data": {
                    "equipment_name": equipment.name,
                    "efficiency_impact": "Reduced efficiency, higher energy costs"
                }
            }
        
        return None
    
    async def _detect_frequency_deviation(self, df: pd.DataFrame, equipment: Equipment) -> Optional[Dict[str, Any]]:
        """Detect frequency deviation anomaly"""
        if df['frequency'].isna().all():
            return None
        
        nominal_frequency = self.thresholds["frequency_deviation"]["nominal"]
        threshold = self.thresholds["frequency_deviation"]["threshold"]
        
        # Check for frequency outside normal range
        freq_deviations = df[
            (df['frequency'] < nominal_frequency - threshold) |
            (df['frequency'] > nominal_frequency + threshold)
        ]
        
        if not freq_deviations.empty:
            latest_freq = freq_deviations['frequency'].iloc[-1]
            deviation_time = freq_deviations['timestamp'].iloc[-1]
            deviation = abs(latest_freq - nominal_frequency)
            
            return {
                "equipment_id": equipment.id,
                "type": "frequency_deviation",
                "severity": "medium" if deviation < 5 else "high",
                "description": f"Frequency deviation on {equipment.equipment_id}: {latest_freq:.1f}Hz (±{deviation:.1f}Hz)",
                "detected_at": deviation_time,
                "measured_value": float(latest_freq),
                "expected_value": nominal_frequency,
                "threshold_value": threshold,
                "context_data": {
                    "equipment_name": equipment.name,
                    "deviation": deviation
                }
            }
        
        return None
    
    async def _save_and_alert_anomaly(self, session: AsyncSession, anomaly_data: Dict[str, Any]):
        """Save anomaly to database and send alert"""
        try:
            # Check if similar anomaly already exists (avoid duplicates)
            existing_query = select(Anomaly).where(
                and_(
                    Anomaly.equipment_id == anomaly_data["equipment_id"],
                    Anomaly.type == anomaly_data["type"],
                    Anomaly.detected_at >= datetime.now() - timedelta(hours=1),
                    Anomaly.is_resolved == False
                )
            )
            
            result = await session.execute(existing_query)
            existing_anomaly = result.scalar_one_or_none()
            
            if existing_anomaly:
                # Update existing anomaly
                existing_anomaly.detected_at = anomaly_data["detected_at"]
                existing_anomaly.measured_value = anomaly_data["measured_value"]
                existing_anomaly.context_data = anomaly_data["context_data"]
            else:
                # Create new anomaly
                new_anomaly = Anomaly(**anomaly_data)
                session.add(new_anomaly)
            
            await session.commit()
            
            # Send WebSocket alert
            await websocket_manager.send_anomaly_alert(anomaly_data)
            
            logger.info(
                "Anomaly detected and saved",
                equipment_id=anomaly_data["equipment_id"],
                type=anomaly_data["type"],
                severity=anomaly_data["severity"]
            )
            
        except Exception as e:
            logger.error("Error saving anomaly", error=str(e))
            await session.rollback()
    
    async def get_anomaly_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of anomalies in the last N hours"""
        async with async_session_maker() as session:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            query = select(Anomaly).where(
                Anomaly.detected_at >= cutoff_time
            )
            
            result = await session.execute(query)
            anomalies = result.scalars().all()
            
            # Group by type and severity
            summary = {
                "total_count": len(anomalies),
                "by_type": {},
                "by_severity": {},
                "unresolved_count": 0,
                "recent_anomalies": []
            }
            
            for anomaly in anomalies:
                # Count by type
                if anomaly.type not in summary["by_type"]:
                    summary["by_type"][anomaly.type] = 0
                summary["by_type"][anomaly.type] += 1
                
                # Count by severity
                if anomaly.severity not in summary["by_severity"]:
                    summary["by_severity"][anomaly.severity] = 0
                summary["by_severity"][anomaly.severity] += 1
                
                # Count unresolved
                if not anomaly.is_resolved:
                    summary["unresolved_count"] += 1
                
                # Add to recent list (last 10)
                if len(summary["recent_anomalies"]) < 10:
                    summary["recent_anomalies"].append({
                        "id": anomaly.id,
                        "type": anomaly.type,
                        "severity": anomaly.severity,
                        "description": anomaly.description,
                        "detected_at": anomaly.detected_at.isoformat(),
                        "is_resolved": anomaly.is_resolved
                    })
            
            return summary


# Global instance
anomaly_detector = AnomalyDetector()
