from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User
from app.models.anomaly import Anomaly
from app.models.equipment import Equipment
from app.schemas.anomaly import (
    AnomalyCreate,
    AnomalyUpdate,
    AnomalyResponse,
    AnomalyQuery,
    AnomalyStats,
    AnomalyType,
    AnomalySeverity,
    AnomalyStatus
)
from app.utils.auth import get_current_user
from app.services.anomaly_detector import anomaly_detector

router = APIRouter()


@router.get("/", response_model=List[AnomalyResponse])
async def get_anomalies(
    equipment_ids: Optional[List[int]] = Query(None),
    anomaly_types: Optional[List[AnomalyType]] = Query(None),
    severities: Optional[List[AnomalySeverity]] = Query(None),
    statuses: Optional[List[AnomalyStatus]] = Query(None),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get anomalies with filtering"""
    query = select(Anomaly)
    
    # Apply filters
    conditions = []
    if equipment_ids:
        conditions.append(Anomaly.equipment_id.in_(equipment_ids))
    if anomaly_types:
        conditions.append(Anomaly.anomaly_type.in_(anomaly_types))
    if severities:
        conditions.append(Anomaly.severity.in_(severities))
    if statuses:
        conditions.append(Anomaly.status.in_(statuses))
    if start_time:
        conditions.append(Anomaly.detected_at >= start_time)
    if end_time:
        conditions.append(Anomaly.detected_at <= end_time)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(desc(Anomaly.detected_at)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    anomalies = result.scalars().all()
    
    return anomalies


@router.get("/stats", response_model=AnomalyStats)
async def get_anomaly_stats(
    equipment_ids: Optional[List[int]] = Query(None),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get anomaly statistics"""
    # Default to last 30 days if no time range specified
    if not start_time:
        start_time = datetime.now() - timedelta(days=30)
    if not end_time:
        end_time = datetime.now()
    
    conditions = [
        Anomaly.detected_at >= start_time,
        Anomaly.detected_at <= end_time
    ]
    
    if equipment_ids:
        conditions.append(Anomaly.equipment_id.in_(equipment_ids))
    
    base_query = select(Anomaly).where(and_(*conditions))
    
    # Total anomalies
    total_result = await db.execute(
        select(func.count(Anomaly.id)).where(and_(*conditions))
    )
    total_anomalies = total_result.scalar() or 0
    
    # Open anomalies
    open_result = await db.execute(
        select(func.count(Anomaly.id)).where(
            and_(Anomaly.status == AnomalyStatus.OPEN, *conditions)
        )
    )
    open_anomalies = open_result.scalar() or 0
    
    # Resolved anomalies
    resolved_result = await db.execute(
        select(func.count(Anomaly.id)).where(
            and_(Anomaly.status == AnomalyStatus.RESOLVED, *conditions)
        )
    )
    resolved_anomalies = resolved_result.scalar() or 0
    
    # Critical anomalies
    critical_result = await db.execute(
        select(func.count(Anomaly.id)).where(
            and_(Anomaly.severity == AnomalySeverity.CRITICAL, *conditions)
        )
    )
    critical_anomalies = critical_result.scalar() or 0
    
    # By type
    type_result = await db.execute(
        select(Anomaly.anomaly_type, func.count(Anomaly.id)).where(
            and_(*conditions)
        ).group_by(Anomaly.anomaly_type)
    )
    by_type = {str(row[0]): row[1] for row in type_result}
    
    # By severity
    severity_result = await db.execute(
        select(Anomaly.severity, func.count(Anomaly.id)).where(
            and_(*conditions)
        ).group_by(Anomaly.severity)
    )
    by_severity = {str(row[0]): row[1] for row in severity_result}
    
    # By equipment
    equipment_result = await db.execute(
        select(Anomaly.equipment_id, func.count(Anomaly.id)).where(
            and_(*conditions)
        ).group_by(Anomaly.equipment_id)
    )
    by_equipment = {str(row[0]): row[1] for row in equipment_result}
    
    # Trend calculations
    day_ago = datetime.now() - timedelta(days=1)
    week_ago = datetime.now() - timedelta(days=7)
    
    trend_24h_result = await db.execute(
        select(func.count(Anomaly.id)).where(
            and_(Anomaly.detected_at >= day_ago, *conditions)
        )
    )
    trend_24h = trend_24h_result.scalar() or 0
    
    trend_7d_result = await db.execute(
        select(func.count(Anomaly.id)).where(
            and_(Anomaly.detected_at >= week_ago, *conditions)
        )
    )
    trend_7d = trend_7d_result.scalar() or 0
    
    return AnomalyStats(
        total_anomalies=total_anomalies,
        open_anomalies=open_anomalies,
        resolved_anomalies=resolved_anomalies,
        critical_anomalies=critical_anomalies,
        by_type=by_type,
        by_severity=by_severity,
        by_equipment=by_equipment,
        trend_24h=trend_24h,
        trend_7d=trend_7d
    )


@router.get("/recent", response_model=List[AnomalyResponse])
async def get_recent_anomalies(
    limit: int = Query(10, le=50),
    severity: Optional[AnomalySeverity] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recent anomalies"""
    query = select(Anomaly)
    
    conditions = []
    if severity:
        conditions.append(Anomaly.severity == severity)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(desc(Anomaly.detected_at)).limit(limit)
    
    result = await db.execute(query)
    recent_anomalies = result.scalars().all()
    
    return recent_anomalies


@router.get("/{anomaly_id}", response_model=AnomalyResponse)
async def get_anomaly(
    anomaly_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific anomaly by ID"""
    result = await db.execute(
        select(Anomaly).where(Anomaly.id == anomaly_id)
    )
    anomaly = result.scalar_one_or_none()
    
    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anomaly not found"
        )
    
    return anomaly


@router.post("/", response_model=AnomalyResponse)
async def create_anomaly(
    anomaly_data: AnomalyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new anomaly (manual reporting)"""
    # Verify equipment exists
    equipment_result = await db.execute(
        select(Equipment).where(Equipment.id == anomaly_data.equipment_id)
    )
    equipment = equipment_result.scalar_one_or_none()
    
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )
    
    anomaly = Anomaly(
        **anomaly_data.dict(),
        detected_at=datetime.utcnow()
    )
    
    db.add(anomaly)
    await db.commit()
    await db.refresh(anomaly)
    
    return anomaly


@router.put("/{anomaly_id}", response_model=AnomalyResponse)
async def update_anomaly(
    anomaly_id: int,
    anomaly_data: AnomalyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update anomaly (acknowledge, resolve, add notes)"""
    result = await db.execute(
        select(Anomaly).where(Anomaly.id == anomaly_id)
    )
    anomaly = result.scalar_one_or_none()
    
    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anomaly not found"
        )
    
    # Update fields
    update_data = anomaly_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(anomaly, field, value)
    
    # Set resolved timestamp if status is resolved
    if anomaly_data.status == AnomalyStatus.RESOLVED:
        anomaly.resolved_at = datetime.utcnow()
        anomaly.resolved_by = current_user.id
    
    anomaly.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(anomaly)
    
    return anomaly


@router.post("/{anomaly_id}/acknowledge")
async def acknowledge_anomaly(
    anomaly_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an anomaly"""
    result = await db.execute(
        select(Anomaly).where(Anomaly.id == anomaly_id)
    )
    anomaly = result.scalar_one_or_none()
    
    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anomaly not found"
        )
    
    anomaly.status = AnomalyStatus.ACKNOWLEDGED
    anomaly.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(anomaly)
    
    return {"message": "Anomaly acknowledged", "anomaly": anomaly}


@router.post("/{anomaly_id}/resolve")
async def resolve_anomaly(
    anomaly_id: int,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resolve an anomaly"""
    result = await db.execute(
        select(Anomaly).where(Anomaly.id == anomaly_id)
    )
    anomaly = result.scalar_one_or_none()
    
    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anomaly not found"
        )
    
    anomaly.status = AnomalyStatus.RESOLVED
    anomaly.resolved_at = datetime.utcnow()
    anomaly.resolved_by = current_user.id
    if notes:
        anomaly.notes = notes
    anomaly.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(anomaly)
    
    return {"message": "Anomaly resolved", "anomaly": anomaly}


@router.post("/detect")
async def trigger_anomaly_detection(
    equipment_ids: Optional[List[int]] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger anomaly detection"""
    try:
        # Trigger anomaly detection for specified equipment or all equipment
        detected_anomalies = await anomaly_detector.detect_anomalies(equipment_ids)
        
        return {
            "message": "Anomaly detection completed",
            "detected_count": len(detected_anomalies),
            "anomalies": detected_anomalies
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection failed: {str(e)}"
        )
