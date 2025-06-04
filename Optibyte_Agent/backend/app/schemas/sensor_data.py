from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class SensorDataBase(BaseModel):
    """Base sensor data schema"""
    equipment_id: int
    voltage_a: Optional[Decimal] = None
    voltage_b: Optional[Decimal] = None
    voltage_c: Optional[Decimal] = None
    current_a: Optional[Decimal] = None
    current_b: Optional[Decimal] = None
    current_c: Optional[Decimal] = None
    power_factor: Optional[Decimal] = None
    frequency: Optional[Decimal] = None
    active_power: Optional[Decimal] = None
    reactive_power: Optional[Decimal] = None
    apparent_power: Optional[Decimal] = None
    temperature: Optional[Decimal] = None
    humidity: Optional[Decimal] = None
    vibration_x: Optional[Decimal] = None
    vibration_y: Optional[Decimal] = None
    vibration_z: Optional[Decimal] = None


class SensorDataCreate(SensorDataBase):
    """Sensor data creation schema"""
    pass


class SensorDataResponse(SensorDataBase):
    """Sensor data response schema"""
    id: int
    timestamp: datetime
    energy_consumption: Optional[Decimal] = None

    class Config:
        from_attributes = True


class SensorDataQuery(BaseModel):
    """Sensor data query parameters"""
    equipment_ids: Optional[List[int]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: Optional[int] = 1000
    offset: Optional[int] = 0


class SensorDataStats(BaseModel):
    """Sensor data statistics"""
    equipment_id: int
    avg_power: Optional[Decimal] = None
    max_power: Optional[Decimal] = None
    min_power: Optional[Decimal] = None
    total_energy: Optional[Decimal] = None
    avg_temperature: Optional[Decimal] = None
    max_temperature: Optional[Decimal] = None
    avg_power_factor: Optional[Decimal] = None
    uptime_hours: Optional[Decimal] = None
    efficiency_score: Optional[Decimal] = None
