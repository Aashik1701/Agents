from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class SensorData(Base):
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Electrical measurements
    voltage = Column(Float)  # V
    current = Column(Float)  # A
    power = Column(Float)    # kW
    power_factor = Column(Float)
    frequency = Column(Float)  # Hz
    energy = Column(Float)   # kWh
    
    # Environmental measurements
    temperature = Column(Float)  # °C
    humidity = Column(Float)     # %
    pressure = Column(Float)     # Pa
    vibration = Column(Float)    # mm/s
    
    # Air flow measurements
    cfm = Column(Float)          # Cubic feet per minute
    air_flow = Column(Float)     # m³/min
    dew_point = Column(Float)    # °C
    
    # Calculated metrics
    efficiency = Column(Float)   # %
    carbon_footprint = Column(Float)  # kg CO2
    cost = Column(Float)         # Currency units
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    equipment = relationship("Equipment", back_populates="sensor_data")
    
    # Indexes for time-series queries
    __table_args__ = (
        Index('idx_equipment_timestamp', 'equipment_id', 'timestamp'),
        Index('idx_timestamp_desc', 'timestamp', postgresql_using='btree'),
    )
