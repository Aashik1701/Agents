from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import structlog
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import async_session_maker
from app.models import SensorData, Equipment, Anomaly, User

logger = structlog.get_logger()


class DataService:
    """Service for accessing and processing sensor data"""
    
    async def get_sensor_data(
        self, 
        equipment_ids: List[str] = None, 
        time_range: Dict[str, datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get sensor data for specified equipment and time range"""
        
        async with async_session_maker() as session:
            query = select(SensorData).options(selectinload(SensorData.equipment))
            
            # Apply equipment filter
            if equipment_ids:
                # Get equipment IDs from equipment_id strings
                equipment_query = select(Equipment).where(
                    Equipment.equipment_id.in_(equipment_ids)
                )
                result = await session.execute(equipment_query)
                equipment_records = result.scalars().all()
                equipment_db_ids = [eq.id for eq in equipment_records]
                
                if equipment_db_ids:
                    query = query.where(SensorData.equipment_id.in_(equipment_db_ids))
                else:
                    return []  # No matching equipment found
            
            # Apply time range filter
            if time_range:
                if 'start' in time_range:
                    query = query.where(SensorData.timestamp >= time_range['start'])
                if 'end' in time_range:
                    query = query.where(SensorData.timestamp <= time_range['end'])
            
            # Order by timestamp and limit results
            query = query.order_by(desc(SensorData.timestamp)).limit(limit)
            
            result = await session.execute(query)
            sensor_data = result.scalars().all()
            
            # Convert to dict format
            data_list = []
            for data in sensor_data:
                data_dict = {
                    "id": data.id,
                    "equipment_id": data.equipment.equipment_id if data.equipment else None,
                    "equipment_name": data.equipment.name if data.equipment else None,
                    "timestamp": data.timestamp.isoformat(),
                    "voltage": data.voltage,
                    "current": data.current,
                    "power": data.power,
                    "power_factor": data.power_factor,
                    "frequency": data.frequency,
                    "energy": data.energy,
                    "temperature": data.temperature,
                    "humidity": data.humidity,
                    "pressure": data.pressure,
                    "vibration": data.vibration,
                    "cfm": data.cfm,
                    "air_flow": data.air_flow,
                    "dew_point": data.dew_point,
                    "efficiency": data.efficiency,
                    "carbon_footprint": data.carbon_footprint,
                    "cost": data.cost
                }
                data_list.append(data_dict)
            
            return data_list
    
    async def get_equipment_status(self, equipment_ids: List[str] = None) -> Dict[str, Any]:
        """Get current status of specified equipment"""
        
        async with async_session_maker() as session:
            query = select(Equipment)
            
            if equipment_ids:
                query = query.where(Equipment.equipment_id.in_(equipment_ids))
            
            result = await session.execute(query)
            equipment_list = result.scalars().all()
            
            status_data = {}
            
            for equipment in equipment_list:
                # Get latest sensor reading
                latest_query = select(SensorData).where(
                    SensorData.equipment_id == equipment.id
                ).order_by(desc(SensorData.timestamp)).limit(1)
                
                latest_result = await session.execute(latest_query)
                latest_data = latest_result.scalar_one_or_none()
                
                # Get recent anomalies
                anomaly_query = select(Anomaly).where(
                    and_(
                        Anomaly.equipment_id == equipment.id,
                        Anomaly.detected_at >= datetime.now() - timedelta(hours=24),
                        Anomaly.is_resolved == False
                    )
                ).order_by(desc(Anomaly.detected_at))
                
                anomaly_result = await session.execute(anomaly_query)
                active_anomalies = anomaly_result.scalars().all()
                
                # Determine overall status
                if active_anomalies:
                    critical_anomalies = [a for a in active_anomalies if a.severity == "critical"]
                    high_anomalies = [a for a in active_anomalies if a.severity == "high"]
                    
                    if critical_anomalies:
                        status = "critical"
                    elif high_anomalies:
                        status = "warning"
                    else:
                        status = "caution"
                elif latest_data and latest_data.timestamp > datetime.now() - timedelta(minutes=30):
                    status = "online"
                else:
                    status = "offline"
                
                status_data[equipment.equipment_id] = {
                    "id": equipment.id,
                    "name": equipment.name,
                    "type": equipment.type,
                    "status": status,
                    "last_seen": latest_data.timestamp.isoformat() if latest_data else None,
                    "current_readings": {
                        "voltage": latest_data.voltage if latest_data else None,
                        "current": latest_data.current if latest_data else None,
                        "power": latest_data.power if latest_data else None,
                        "power_factor": latest_data.power_factor if latest_data else None,
                        "temperature": latest_data.temperature if latest_data else None,
                    } if latest_data else None,
                    "active_anomalies": [
                        {
                            "id": anomaly.id,
                            "type": anomaly.type,
                            "severity": anomaly.severity,
                            "description": anomaly.description,
                            "detected_at": anomaly.detected_at.isoformat()
                        }
                        for anomaly in active_anomalies
                    ]
                }
            
            return status_data
    
    async def get_recent_anomalies(self, hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent anomalies"""
        
        async with async_session_maker() as session:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            query = select(Anomaly).options(
                selectinload(Anomaly.equipment)
            ).where(
                Anomaly.detected_at >= cutoff_time
            ).order_by(desc(Anomaly.detected_at)).limit(limit)
            
            result = await session.execute(query)
            anomalies = result.scalars().all()
            
            anomaly_list = []
            for anomaly in anomalies:
                anomaly_dict = {
                    "id": anomaly.id,
                    "equipment_id": anomaly.equipment.equipment_id if anomaly.equipment else None,
                    "equipment_name": anomaly.equipment.name if anomaly.equipment else None,
                    "type": anomaly.type,
                    "severity": anomaly.severity,
                    "description": anomaly.description,
                    "detected_at": anomaly.detected_at.isoformat(),
                    "measured_value": anomaly.measured_value,
                    "expected_value": anomaly.expected_value,
                    "threshold_value": anomaly.threshold_value,
                    "is_resolved": anomaly.is_resolved,
                    "resolved_at": anomaly.resolved_at.isoformat() if anomaly.resolved_at else None,
                    "context_data": anomaly.context_data
                }
                anomaly_list.append(anomaly_dict)
            
            return anomaly_list
    
    async def get_comparison_data(
        self, 
        equipment_ids: List[str], 
        time_range: Dict[str, datetime] = None
    ) -> Dict[str, Any]:
        """Get data for comparing multiple equipment"""
        
        comparison_data = {
            "equipment": {},
            "metrics": {
                "energy_consumption": {},
                "efficiency": {},
                "power_factor": {},
                "average_power": {},
                "operating_hours": {}
            },
            "time_range": time_range
        }
        
        for equipment_id in equipment_ids:
            data = await self.get_sensor_data([equipment_id], time_range)
            
            if data:
                # Calculate metrics
                power_values = [d["power"] for d in data if d["power"] is not None]
                pf_values = [d["power_factor"] for d in data if d["power_factor"] is not None]
                efficiency_values = [d["efficiency"] for d in data if d["efficiency"] is not None]
                energy_values = [d["energy"] for d in data if d["energy"] is not None]
                
                comparison_data["equipment"][equipment_id] = {
                    "data_points": len(data),
                    "latest_reading": data[0] if data else None
                }
                
                if power_values:
                    comparison_data["metrics"]["average_power"][equipment_id] = sum(power_values) / len(power_values)
                
                if pf_values:
                    comparison_data["metrics"]["power_factor"][equipment_id] = sum(pf_values) / len(pf_values)
                
                if efficiency_values:
                    comparison_data["metrics"]["efficiency"][equipment_id] = sum(efficiency_values) / len(efficiency_values)
                
                if energy_values:
                    comparison_data["metrics"]["energy_consumption"][equipment_id] = max(energy_values) - min(energy_values)
                
                # Calculate operating hours (assuming data points every 5 minutes)
                comparison_data["metrics"]["operating_hours"][equipment_id] = len(data) * 5 / 60
        
        return comparison_data
    
    async def get_energy_summary(self, time_range: Dict[str, datetime] = None) -> Dict[str, Any]:
        """Get energy consumption summary"""
        
        if not time_range:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            time_range = {"start": start_time, "end": end_time}
        
        async with async_session_maker() as session:
            # Get all equipment
            equipment_query = select(Equipment).where(Equipment.is_active == True)
            equipment_result = await session.execute(equipment_query)
            equipment_list = equipment_result.scalars().all()
            
            summary = {
                "total_energy": 0.0,
                "total_cost": 0.0,
                "total_carbon": 0.0,
                "equipment_breakdown": {},
                "time_range": {
                    "start": time_range["start"].isoformat(),
                    "end": time_range["end"].isoformat()
                }
            }
            
            for equipment in equipment_list:
                # Get energy data for this equipment
                data_query = select(SensorData).where(
                    and_(
                        SensorData.equipment_id == equipment.id,
                        SensorData.timestamp >= time_range["start"],
                        SensorData.timestamp <= time_range["end"]
                    )
                ).order_by(SensorData.timestamp)
                
                data_result = await session.execute(data_query)
                data_points = data_result.scalars().all()
                
                if data_points:
                    energy_values = [d.energy for d in data_points if d.energy is not None]
                    cost_values = [d.cost for d in data_points if d.cost is not None]
                    carbon_values = [d.carbon_footprint for d in data_points if d.carbon_footprint is not None]
                    
                    equipment_energy = max(energy_values) - min(energy_values) if energy_values else 0
                    equipment_cost = sum(cost_values) if cost_values else 0
                    equipment_carbon = sum(carbon_values) if carbon_values else 0
                    
                    summary["equipment_breakdown"][equipment.equipment_id] = {
                        "name": equipment.name,
                        "type": equipment.type,
                        "energy": equipment_energy,
                        "cost": equipment_cost,
                        "carbon": equipment_carbon
                    }
                    
                    summary["total_energy"] += equipment_energy
                    summary["total_cost"] += equipment_cost
                    summary["total_carbon"] += equipment_carbon
            
            return summary
    
    async def get_peak_usage_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Analyze peak usage patterns"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        async with async_session_maker() as session:
            # Get power data grouped by hour
            query = select(
                func.extract('hour', SensorData.timestamp).label('hour'),
                func.avg(SensorData.power).label('avg_power'),
                func.max(SensorData.power).label('max_power'),
                func.count(SensorData.id).label('count')
            ).where(
                and_(
                    SensorData.timestamp >= start_time,
                    SensorData.power.is_not(None)
                )
            ).group_by(
                func.extract('hour', SensorData.timestamp)
            ).order_by('hour')
            
            result = await session.execute(query)
            hourly_data = result.all()
            
            peak_analysis = {
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "days": days
                },
                "hourly_averages": {},
                "peak_hours": [],
                "off_peak_hours": [],
                "recommendations": []
            }
            
            if hourly_data:
                # Process hourly data
                power_by_hour = {}
                for row in hourly_data:
                    hour = int(row.hour)
                    avg_power = float(row.avg_power)
                    max_power = float(row.max_power)
                    
                    peak_analysis["hourly_averages"][hour] = {
                        "average_power": avg_power,
                        "peak_power": max_power,
                        "data_points": row.count
                    }
                    power_by_hour[hour] = avg_power
                
                # Identify peak and off-peak hours
                avg_power_overall = sum(power_by_hour.values()) / len(power_by_hour)
                
                for hour, power in power_by_hour.items():
                    if power > avg_power_overall * 1.2:  # 20% above average
                        peak_analysis["peak_hours"].append(hour)
                    elif power < avg_power_overall * 0.8:  # 20% below average
                        peak_analysis["off_peak_hours"].append(hour)
                
                # Generate recommendations
                if peak_analysis["peak_hours"] and peak_analysis["off_peak_hours"]:
                    peak_analysis["recommendations"].append({
                        "type": "load_shifting",
                        "description": f"Consider shifting non-critical loads from peak hours ({peak_analysis['peak_hours']}) to off-peak hours ({peak_analysis['off_peak_hours']}) to reduce energy costs.",
                        "potential_savings": "10-15%"
                    })
            
            return peak_analysis


# Global instance
data_service = DataService()
