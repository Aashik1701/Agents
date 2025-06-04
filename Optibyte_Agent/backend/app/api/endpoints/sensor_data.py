from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, text
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User
from app.models.sensor_data import SensorData
from app.models.equipment import Equipment
from app.schemas.sensor_data import (
    SensorDataCreate,
    SensorDataResponse,
    SensorDataQuery,
    SensorDataStats
)
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[SensorDataResponse])
async def get_sensor_data(
    equipment_ids: Optional[List[int]] = Query(None),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(1000, le=10000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get sensor data with filtering"""
    query = select(SensorData)
    
    # Apply filters
    conditions = []
    if equipment_ids:
        conditions.append(SensorData.equipment_id.in_(equipment_ids))
    if start_time:
        conditions.append(SensorData.timestamp >= start_time)
    if end_time:
        conditions.append(SensorData.timestamp <= end_time)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(desc(SensorData.timestamp)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    sensor_data = result.scalars().all()
    
    return sensor_data


@router.get("/latest", response_model=List[SensorDataResponse])
async def get_latest_sensor_data(
    equipment_ids: Optional[List[int]] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get latest sensor data for each equipment"""
    if equipment_ids:
        # Get latest data for specific equipment
        subquery = select(
            SensorData.equipment_id,
            func.max(SensorData.timestamp).label('max_timestamp')
        ).where(
            SensorData.equipment_id.in_(equipment_ids)
        ).group_by(SensorData.equipment_id).subquery()
        
        query = select(SensorData).join(
            subquery,
            and_(
                SensorData.equipment_id == subquery.c.equipment_id,
                SensorData.timestamp == subquery.c.max_timestamp
            )
        )
    else:
        # Get latest data for all equipment
        subquery = select(
            SensorData.equipment_id,
            func.max(SensorData.timestamp).label('max_timestamp')
        ).group_by(SensorData.equipment_id).subquery()
        
        query = select(SensorData).join(
            subquery,
            and_(
                SensorData.equipment_id == subquery.c.equipment_id,
                SensorData.timestamp == subquery.c.max_timestamp
            )
        )
    
    result = await db.execute(query)
    latest_data = result.scalars().all()
    
    return latest_data


@router.get("/stats", response_model=List[SensorDataStats])
async def get_sensor_data_stats(
    equipment_ids: Optional[List[int]] = Query(None),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get sensor data statistics"""
    # Default to last 24 hours if no time range specified
    if not start_time:
        start_time = datetime.now() - timedelta(days=1)
    if not end_time:
        end_time = datetime.now()
    
    conditions = [
        SensorData.timestamp >= start_time,
        SensorData.timestamp <= end_time
    ]
    
    if equipment_ids:
        conditions.append(SensorData.equipment_id.in_(equipment_ids))
    
    # Calculate statistics using SQL aggregation
    stats_query = select(
        SensorData.equipment_id,
        func.avg(SensorData.active_power).label('avg_power'),
        func.max(SensorData.active_power).label('max_power'),
        func.min(SensorData.active_power).label('min_power'),
        func.sum(SensorData.energy_consumption).label('total_energy'),
        func.avg(SensorData.temperature).label('avg_temperature'),
        func.max(SensorData.temperature).label('max_temperature'),
        func.avg(SensorData.power_factor).label('avg_power_factor'),
        func.count(SensorData.id).label('data_points')
    ).where(and_(*conditions)).group_by(SensorData.equipment_id)
    
    result = await db.execute(stats_query)
    stats_data = result.all()
    
    # Convert to response format
    stats_list = []
    for stat in stats_data:
        # Calculate uptime hours (assuming 1 data point per minute)
        uptime_hours = (stat.data_points / 60.0) if stat.data_points else 0
        
        # Calculate efficiency score (placeholder logic)
        efficiency_score = 85.0  # Implement actual efficiency calculation
        
        stats_list.append(SensorDataStats(
            equipment_id=stat.equipment_id,
            avg_power=stat.avg_power,
            max_power=stat.max_power,
            min_power=stat.min_power,
            total_energy=stat.total_energy,
            avg_temperature=stat.avg_temperature,
            max_temperature=stat.max_temperature,
            avg_power_factor=stat.avg_power_factor,
            uptime_hours=uptime_hours,
            efficiency_score=efficiency_score
        ))
    
    return stats_list


@router.get("/aggregated")
async def get_aggregated_data(
    equipment_ids: Optional[List[int]] = Query(None),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    interval: str = Query("hour", regex="^(minute|hour|day)$"),
    metrics: List[str] = Query(["active_power", "energy_consumption"]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated sensor data by time intervals"""
    # Default to last 24 hours if no time range specified
    if not start_time:
        start_time = datetime.now() - timedelta(days=1)
    if not end_time:
        end_time = datetime.now()
    
    # Define time bucket based on interval
    time_bucket_sql = {
        "minute": "date_trunc('minute', timestamp)",
        "hour": "date_trunc('hour', timestamp)",
        "day": "date_trunc('day', timestamp)"
    }
    
    if interval not in time_bucket_sql:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid interval. Must be 'minute', 'hour', or 'day'"
        )
    
    # Build dynamic aggregation query
    select_fields = [text(f"{time_bucket_sql[interval]} as time_bucket")]
    
    if equipment_ids:
        select_fields.append(SensorData.equipment_id)
    
    # Add metric aggregations
    metric_mapping = {
        "active_power": func.avg(SensorData.active_power).label('avg_active_power'),
        "energy_consumption": func.sum(SensorData.energy_consumption).label('sum_energy_consumption'),
        "temperature": func.avg(SensorData.temperature).label('avg_temperature'),
        "power_factor": func.avg(SensorData.power_factor).label('avg_power_factor'),
        "voltage_a": func.avg(SensorData.voltage_a).label('avg_voltage_a'),
        "current_a": func.avg(SensorData.current_a).label('avg_current_a')
    }
    
    for metric in metrics:
        if metric in metric_mapping:
            select_fields.append(metric_mapping[metric])
    
    query = select(*select_fields).where(
        and_(
            SensorData.timestamp >= start_time,
            SensorData.timestamp <= end_time,
            SensorData.equipment_id.in_(equipment_ids) if equipment_ids else True
        )
    )
    
    # Group by time bucket and equipment_id if specified
    group_by_fields = [text(time_bucket_sql[interval])]
    if equipment_ids:
        group_by_fields.append(SensorData.equipment_id)
    
    query = query.group_by(*group_by_fields).order_by(text(time_bucket_sql[interval]))
    
    result = await db.execute(query)
    aggregated_data = [dict(row._mapping) for row in result]
    
    return {
        "data": aggregated_data,
        "interval": interval,
        "start_time": start_time,
        "end_time": end_time,
        "metrics": metrics
    }


@router.post("/", response_model=SensorDataResponse)
async def create_sensor_data(
    sensor_data: SensorDataCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new sensor data entry"""
    # Verify equipment exists
    equipment_result = await db.execute(
        select(Equipment).where(Equipment.id == sensor_data.equipment_id)
    )
    equipment = equipment_result.scalar_one_or_none()
    
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )
    
    # Calculate energy consumption if power is provided
    energy_consumption = None
    if sensor_data.active_power:
        # Assume 1-minute interval for energy calculation (power * time_hours)
        energy_consumption = sensor_data.active_power * (1/60)  # kWh for 1 minute
    
    # Create sensor data entry
    new_sensor_data = SensorData(
        **sensor_data.dict(),
        energy_consumption=energy_consumption
    )
    
    db.add(new_sensor_data)
    await db.commit()
    await db.refresh(new_sensor_data)
    
    return new_sensor_data


@router.post("/batch", response_model=List[SensorDataResponse])
async def create_sensor_data_batch(
    sensor_data_list: List[SensorDataCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create multiple sensor data entries in batch"""
    # Verify all equipment exists
    equipment_ids = list(set(data.equipment_id for data in sensor_data_list))
    equipment_result = await db.execute(
        select(Equipment.id).where(Equipment.id.in_(equipment_ids))
    )
    existing_equipment_ids = set(row[0] for row in equipment_result)
    
    # Check for invalid equipment IDs
    invalid_ids = set(equipment_ids) - existing_equipment_ids
    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment not found: {list(invalid_ids)}"
        )
    
    # Create sensor data entries
    new_entries = []
    for sensor_data in sensor_data_list:
        # Calculate energy consumption
        energy_consumption = None
        if sensor_data.active_power:
            energy_consumption = sensor_data.active_power * (1/60)  # kWh for 1 minute
        
        new_entry = SensorData(
            **sensor_data.dict(),
            energy_consumption=energy_consumption
        )
        new_entries.append(new_entry)
    
    db.add_all(new_entries)
    await db.commit()
    
    # Refresh all entries
    for entry in new_entries:
        await db.refresh(entry)
    
    return new_entries
