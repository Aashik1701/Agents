from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class EquipmentType(str, Enum):
    """Equipment type enumeration"""
    COMPRESSOR = "compressor"
    MOTOR = "motor"
    HVAC = "hvac"
    PUMP = "pump"
    OTHER = "other"


class EquipmentStatus(str, Enum):
    """Equipment status enumeration"""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class EquipmentBase(BaseModel):
    """Base equipment schema"""
    name: str
    equipment_type: EquipmentType
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    rated_power: Optional[Decimal] = None
    rated_voltage: Optional[Decimal] = None
    rated_current: Optional[Decimal] = None
    rated_frequency: Optional[Decimal] = None
    installation_date: Optional[datetime] = None
    description: Optional[str] = None


class EquipmentCreate(EquipmentBase):
    """Equipment creation schema"""
    pass


class EquipmentUpdate(BaseModel):
    """Equipment update schema"""
    name: Optional[str] = None
    equipment_type: Optional[EquipmentType] = None
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    rated_power: Optional[Decimal] = None
    rated_voltage: Optional[Decimal] = None
    rated_current: Optional[Decimal] = None
    rated_frequency: Optional[Decimal] = None
    installation_date: Optional[datetime] = None
    description: Optional[str] = None
    status: Optional[EquipmentStatus] = None


class EquipmentResponse(EquipmentBase):
    """Equipment response schema"""
    id: int
    status: EquipmentStatus
    last_maintenance: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EquipmentWithStats(EquipmentResponse):
    """Equipment with statistics"""
    current_power: Optional[Decimal] = None
    energy_today: Optional[Decimal] = None
    uptime_percentage: Optional[Decimal] = None
    efficiency_score: Optional[Decimal] = None
    last_data_timestamp: Optional[datetime] = None


class EquipmentQuery(BaseModel):
    """Equipment query parameters"""
    equipment_type: Optional[EquipmentType] = None
    status: Optional[EquipmentStatus] = None
    location: Optional[str] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0
