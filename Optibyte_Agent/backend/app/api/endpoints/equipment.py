from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User
from app.models.equipment import Equipment
from app.models.sensor_data import SensorData
from app.schemas.equipment import (
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentResponse,
    EquipmentWithStats,
    EquipmentQuery,
    EquipmentStatus,
    EquipmentType
)
from app.utils.auth import get_current_user
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/", response_model=List[EquipmentResponse])
async def get_equipment_list(
    equipment_type: Optional[EquipmentType] = None,
    status: Optional[EquipmentStatus] = None,
    location: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of equipment with optional filtering"""
    query = select(Equipment)
    
    # Apply filters
    conditions = []
    if equipment_type:
        conditions.append(Equipment.equipment_type == equipment_type)
    if status:
        conditions.append(Equipment.status == status)
    if location:
        conditions.append(Equipment.location.ilike(f"%{location}%"))
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.offset(offset).limit(limit).order_by(Equipment.name)
    
    result = await db.execute(query)
    equipment_list = result.scalars().all()
    
    return equipment_list


@router.get("/with-stats", response_model=List[EquipmentWithStats])
async def get_equipment_with_stats(
    equipment_type: Optional[EquipmentType] = None,
    status: Optional[EquipmentStatus] = None,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get equipment list with real-time statistics"""
    # Base equipment query
    query = select(Equipment)
    
    conditions = []
    if equipment_type:
        conditions.append(Equipment.equipment_type == equipment_type)
    if status:
        conditions.append(Equipment.status == status)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.offset(offset).limit(limit).order_by(Equipment.name)
    
    result = await db.execute(query)
    equipment_list = result.scalars().all()
    
    # Get statistics for each equipment
    equipment_with_stats = []
    for equipment in equipment_list:
        # Get latest sensor data
        latest_data_query = select(SensorData).where(
            SensorData.equipment_id == equipment.id
        ).order_by(desc(SensorData.timestamp)).limit(1)
        
        latest_result = await db.execute(latest_data_query)
        latest_data = latest_result.scalar_one_or_none()
        
        # Calculate today's energy consumption
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        energy_query = select(func.sum(SensorData.energy_consumption)).where(
            and_(
                SensorData.equipment_id == equipment.id,
                SensorData.timestamp >= today_start
            )
        )
        energy_result = await db.execute(energy_query)
        energy_today = energy_result.scalar() or 0
        
        # Calculate uptime percentage (last 24 hours)
        day_ago = datetime.now() - timedelta(days=1)
        total_points_query = select(func.count(SensorData.id)).where(
            and_(
                SensorData.equipment_id == equipment.id,
                SensorData.timestamp >= day_ago
            )
        )
        total_points_result = await db.execute(total_points_query)
        total_points = total_points_result.scalar() or 0
        
        # Assume 1 data point per minute for 24 hours = 1440 points
        expected_points = 24 * 60
        uptime_percentage = (total_points / expected_points * 100) if expected_points > 0 else 0
        uptime_percentage = min(uptime_percentage, 100)  # Cap at 100%
        
        # Create equipment with stats
        equipment_stats = EquipmentWithStats(
            **equipment.__dict__,
            current_power=latest_data.active_power if latest_data else None,
            energy_today=energy_today,
            uptime_percentage=uptime_percentage,
            efficiency_score=85.0,  # Placeholder - implement actual calculation
            last_data_timestamp=latest_data.timestamp if latest_data else None
        )
        
        equipment_with_stats.append(equipment_stats)
    
    return equipment_with_stats


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific equipment by ID"""
    result = await db.execute(
        select(Equipment).where(Equipment.id == equipment_id)
    )
    equipment = result.scalar_one_or_none()
    
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )
    
    return equipment


@router.post("/", response_model=EquipmentResponse)
async def create_equipment(
    equipment_data: EquipmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new equipment"""
    # Check if equipment name already exists
    result = await db.execute(
        select(Equipment).where(Equipment.name == equipment_data.name)
    )
    existing_equipment = result.scalar_one_or_none()
    
    if existing_equipment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Equipment with this name already exists"
        )
    
    equipment = Equipment(**equipment_data.dict())
    db.add(equipment)
    await db.commit()
    await db.refresh(equipment)
    
    return equipment


@router.put("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: int,
    equipment_data: EquipmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update equipment"""
    result = await db.execute(
        select(Equipment).where(Equipment.id == equipment_id)
    )
    equipment = result.scalar_one_or_none()
    
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )
    
    # Update fields
    update_data = equipment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(equipment, field, value)
    
    equipment.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(equipment)
    
    return equipment


@router.delete("/{equipment_id}")
async def delete_equipment(
    equipment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete equipment"""
    result = await db.execute(
        select(Equipment).where(Equipment.id == equipment_id)
    )
    equipment = result.scalar_one_or_none()
    
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )
    
    await db.delete(equipment)
    await db.commit()
    
    return {"message": "Equipment deleted successfully"}


@router.post("/{equipment_id}/maintenance")
async def schedule_maintenance(
    equipment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Schedule maintenance for equipment"""
    result = await db.execute(
        select(Equipment).where(Equipment.id == equipment_id)
    )
    equipment = result.scalar_one_or_none()
    
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )
    
    equipment.status = EquipmentStatus.MAINTENANCE
    equipment.last_maintenance = datetime.utcnow()
    equipment.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(equipment)
    
    return {"message": "Equipment scheduled for maintenance", "equipment": equipment}
