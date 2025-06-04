from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, text
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User
from app.models.equipment import Equipment
from app.models.sensor_data import SensorData
from app.models.anomaly import Anomaly
from app.schemas.dashboard import (
    DashboardMetrics,
    ChartRequest,
    ChartResponse
)
from app.schemas.equipment import EquipmentStatus
from app.schemas.anomaly import AnomalyStatus, AnomalySeverity
from app.utils.auth import get_current_user
from app.services.chart_generator import chart_generator

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive dashboard metrics"""
    
    # Get total and active equipment count
    total_equipment_result = await db.execute(
        select(func.count(Equipment.id))
    )
    total_equipment = total_equipment_result.scalar() or 0
    
    active_equipment_result = await db.execute(
        select(func.count(Equipment.id)).where(
            Equipment.status == EquipmentStatus.ONLINE
        )
    )
    active_equipment = active_equipment_result.scalar() or 0
    
    # Calculate today's and this month's energy consumption
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    energy_today_result = await db.execute(
        select(func.coalesce(func.sum(SensorData.energy_consumption), 0)).where(
            SensorData.timestamp >= today_start
        )
    )
    total_energy_today = float(energy_today_result.scalar() or 0)
    
    energy_month_result = await db.execute(
        select(func.coalesce(func.sum(SensorData.energy_consumption), 0)).where(
            SensorData.timestamp >= month_start
        )
    )
    total_energy_month = float(energy_month_result.scalar() or 0)
    
    # Calculate average efficiency (placeholder calculation)
    efficiency_result = await db.execute(
        select(func.avg(SensorData.power_factor * 100)).where(
            SensorData.timestamp >= today_start
        )
    )
    average_efficiency = float(efficiency_result.scalar() or 85.0)
    
    # Get active anomalies count
    active_anomalies_result = await db.execute(
        select(func.count(Anomaly.id)).where(
            Anomaly.status == AnomalyStatus.OPEN
        )
    )
    active_anomalies = active_anomalies_result.scalar() or 0
    
    # Calculate cost savings (placeholder calculation - $0.15 per kWh)
    cost_per_kwh = 0.15
    # Assume 10% savings from optimization
    cost_savings_month = total_energy_month * cost_per_kwh * 0.10
    
    # Get top energy consumers
    top_consumers_result = await db.execute(
        select(
            Equipment.name,
            Equipment.id,
            func.sum(SensorData.energy_consumption).label('total_energy')
        ).join(
            SensorData, Equipment.id == SensorData.equipment_id
        ).where(
            SensorData.timestamp >= today_start
        ).group_by(
            Equipment.id, Equipment.name
        ).order_by(
            desc('total_energy')
        ).limit(5)
    )
    top_consumers = [
        {
            "name": row.name,
            "id": row.id,
            "energy": float(row.total_energy or 0)
        }
        for row in top_consumers_result
    ]
    
    # Get recent anomalies
    recent_anomalies_result = await db.execute(
        select(
            Anomaly.id,
            Anomaly.anomaly_type,
            Anomaly.severity,
            Anomaly.detected_at,
            Equipment.name.label('equipment_name')
        ).join(
            Equipment, Anomaly.equipment_id == Equipment.id
        ).order_by(
            desc(Anomaly.detected_at)
        ).limit(5)
    )
    recent_anomalies = [
        {
            "id": row.id,
            "type": str(row.anomaly_type),
            "severity": str(row.severity),
            "detected_at": row.detected_at.isoformat(),
            "equipment_name": row.equipment_name
        }
        for row in recent_anomalies_result
    ]
    
    # Get 24-hour energy trend (hourly aggregation)
    trend_start = datetime.now() - timedelta(hours=24)
    energy_trend_result = await db.execute(
        select(
            func.date_trunc('hour', SensorData.timestamp).label('hour'),
            func.sum(SensorData.energy_consumption).label('energy')
        ).where(
            SensorData.timestamp >= trend_start
        ).group_by(
            func.date_trunc('hour', SensorData.timestamp)
        ).order_by('hour')
    )
    energy_trend_24h = [
        {
            "time": row.hour.isoformat(),
            "energy": float(row.energy or 0)
        }
        for row in energy_trend_result
    ]
    
    return DashboardMetrics(
        total_equipment=total_equipment,
        active_equipment=active_equipment,
        total_energy_today=total_energy_today,
        total_energy_month=total_energy_month,
        average_efficiency=average_efficiency,
        active_anomalies=active_anomalies,
        cost_savings_month=cost_savings_month,
        top_consumers=top_consumers,
        recent_anomalies=recent_anomalies,
        energy_trend_24h=energy_trend_24h
    )


@router.get("/equipment-summary")
async def get_equipment_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get equipment summary with real-time status"""
    
    # Get equipment with latest sensor data
    subquery = select(
        SensorData.equipment_id,
        func.max(SensorData.timestamp).label('latest_timestamp')
    ).group_by(SensorData.equipment_id).subquery()
    
    query = select(
        Equipment.id,
        Equipment.name,
        Equipment.equipment_type,
        Equipment.status,
        Equipment.location,
        SensorData.active_power,
        SensorData.temperature,
        SensorData.timestamp
    ).outerjoin(
        subquery, Equipment.id == subquery.c.equipment_id
    ).outerjoin(
        SensorData,
        and_(
            SensorData.equipment_id == Equipment.id,
            SensorData.timestamp == subquery.c.latest_timestamp
        )
    ).order_by(Equipment.name)
    
    result = await db.execute(query)
    equipment_summary = []
    
    for row in result:
        equipment_summary.append({
            "id": row.id,
            "name": row.name,
            "type": str(row.equipment_type),
            "status": str(row.status),
            "location": row.location,
            "current_power": float(row.active_power) if row.active_power else None,
            "temperature": float(row.temperature) if row.temperature else None,
            "last_update": row.timestamp.isoformat() if row.timestamp else None
        })
    
    return {"equipment": equipment_summary}


@router.post("/chart", response_model=ChartResponse)
async def generate_chart(
    chart_request: ChartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate chart data based on request parameters"""
    
    try:
        chart_data = await chart_generator.generate_chart(
            chart_type=chart_request.chart_type,
            equipment_ids=chart_request.equipment_ids,
            metrics=chart_request.metrics,
            start_time=chart_request.start_time,
            end_time=chart_request.end_time,
            aggregation=chart_request.aggregation,
            title=chart_request.title
        )
        
        return ChartResponse(
            chart_data=chart_data["data"],
            chart_config=chart_data["layout"],
            metadata=chart_data["metadata"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chart generation failed: {str(e)}"
        )


@router.get("/energy-overview")
async def get_energy_overview(
    period: str = Query("day", regex="^(hour|day|week|month)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get energy consumption overview for different time periods"""
    
    # Define time ranges
    now = datetime.now()
    time_ranges = {
        "hour": now - timedelta(hours=1),
        "day": now - timedelta(days=1),
        "week": now - timedelta(weeks=1),
        "month": now - timedelta(days=30)
    }
    
    start_time = time_ranges.get(period, time_ranges["day"])
    
    # Get total energy consumption
    total_energy_result = await db.execute(
        select(func.coalesce(func.sum(SensorData.energy_consumption), 0)).where(
            SensorData.timestamp >= start_time
        )
    )
    total_energy = float(total_energy_result.scalar() or 0)
    
    # Get energy by equipment type
    energy_by_type_result = await db.execute(
        select(
            Equipment.equipment_type,
            func.sum(SensorData.energy_consumption).label('total_energy')
        ).join(
            SensorData, Equipment.id == SensorData.equipment_id
        ).where(
            SensorData.timestamp >= start_time
        ).group_by(
            Equipment.equipment_type
        )
    )
    energy_by_type = {
        str(row.equipment_type): float(row.total_energy or 0)
        for row in energy_by_type_result
    }
    
    # Get hourly breakdown for the period
    if period == "hour":
        time_trunc = "minute"
        trunc_interval = 5  # 5-minute intervals
    elif period == "day":
        time_trunc = "hour"
        trunc_interval = 1
    elif period == "week":
        time_trunc = "day"
        trunc_interval = 1
    else:  # month
        time_trunc = "day"
        trunc_interval = 1
    
    hourly_breakdown_result = await db.execute(
        select(
            func.date_trunc(time_trunc, SensorData.timestamp).label('time_bucket'),
            func.sum(SensorData.energy_consumption).label('energy')
        ).where(
            SensorData.timestamp >= start_time
        ).group_by(
            func.date_trunc(time_trunc, SensorData.timestamp)
        ).order_by('time_bucket')
    )
    
    hourly_breakdown = [
        {
            "time": row.time_bucket.isoformat(),
            "energy": float(row.energy or 0)
        }
        for row in hourly_breakdown_result
    ]
    
    # Calculate efficiency metrics
    avg_power_factor_result = await db.execute(
        select(func.avg(SensorData.power_factor)).where(
            SensorData.timestamp >= start_time
        )
    )
    avg_power_factor = float(avg_power_factor_result.scalar() or 0.85)
    
    return {
        "period": period,
        "start_time": start_time.isoformat(),
        "end_time": now.isoformat(),
        "total_energy": total_energy,
        "energy_by_type": energy_by_type,
        "hourly_breakdown": hourly_breakdown,
        "average_power_factor": avg_power_factor,
        "estimated_cost": total_energy * 0.15,  # $0.15 per kWh
        "carbon_footprint": total_energy * 0.5  # 0.5 kg CO2 per kWh
    }


@router.get("/alerts")
async def get_dashboard_alerts(
    limit: int = Query(10, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recent alerts for dashboard"""
    
    # Get recent critical anomalies
    recent_anomalies_result = await db.execute(
        select(
            Anomaly.id,
            Anomaly.anomaly_type,
            Anomaly.severity,
            Anomaly.description,
            Anomaly.detected_at,
            Equipment.name.label('equipment_name')
        ).join(
            Equipment, Anomaly.equipment_id == Equipment.id
        ).where(
            Anomaly.status == AnomalyStatus.OPEN
        ).order_by(
            Anomaly.severity.desc(),
            desc(Anomaly.detected_at)
        ).limit(limit)
    )
    
    alerts = []
    for row in recent_anomalies_result:
        alert_type = "critical" if row.severity == AnomalySeverity.CRITICAL else "warning"
        alerts.append({
            "id": row.id,
            "type": alert_type,
            "title": f"{row.anomaly_type.replace('_', ' ').title()} - {row.equipment_name}",
            "message": row.description,
            "timestamp": row.detected_at.isoformat(),
            "equipment_name": row.equipment_name,
            "severity": str(row.severity)
        })
    
    # Add system alerts (placeholder)
    if len(alerts) < limit:
        system_alerts = [
            {
                "id": "sys_1",
                "type": "info",
                "title": "System Health Check",
                "message": "All systems operating normally",
                "timestamp": datetime.now().isoformat(),
                "equipment_name": "System",
                "severity": "low"
            }
        ]
        alerts.extend(system_alerts[:limit - len(alerts)])
    
    return {"alerts": alerts}
