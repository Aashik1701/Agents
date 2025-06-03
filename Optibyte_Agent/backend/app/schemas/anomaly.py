from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class AnomalyType(str, Enum):
    """Anomaly type enumeration"""
    VOLTAGE_SPIKE = "voltage_spike"
    VOLTAGE_DROP = "voltage_drop"
    ZERO_CURRENT = "zero_current"
    HIGH_TEMPERATURE = "high_temperature"
    LOW_POWER_FACTOR = "low_power_factor"
    FREQUENCY_DEVIATION = "frequency_deviation"
    HIGH_VIBRATION = "high_vibration"
    POWER_OUTAGE = "power_outage"
    EFFICIENCY_DROP = "efficiency_drop"


class AnomalySeverity(str, Enum):
    """Anomaly severity enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyStatus(str, Enum):
    """Anomaly status enumeration"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class AnomalyBase(BaseModel):
    """Base anomaly schema"""
    equipment_id: int
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    description: str
    value: Optional[Decimal] = None
    threshold: Optional[Decimal] = None
    confidence: Optional[Decimal] = None


class AnomalyCreate(AnomalyBase):
    """Anomaly creation schema"""
    pass


class AnomalyUpdate(BaseModel):
    """Anomaly update schema"""
    status: Optional[AnomalyStatus] = None
    notes: Optional[str] = None
    resolved_by: Optional[int] = None


class AnomalyResponse(AnomalyBase):
    """Anomaly response schema"""
    id: int
    status: AnomalyStatus
    notes: Optional[str] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    detected_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnomalyQuery(BaseModel):
    """Anomaly query parameters"""
    equipment_ids: Optional[List[int]] = None
    anomaly_types: Optional[List[AnomalyType]] = None
    severities: Optional[List[AnomalySeverity]] = None
    statuses: Optional[List[AnomalyStatus]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0


class AnomalyStats(BaseModel):
    """Anomaly statistics"""
    total_anomalies: int
    open_anomalies: int
    resolved_anomalies: int
    critical_anomalies: int
    by_type: dict
    by_severity: dict
    by_equipment: dict
    trend_24h: int
    trend_7d: int
