from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String, unique=True, index=True, nullable=False)  # e.g., IKC0073
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # compressor, pump, motor, etc.
    location = Column(String)
    description = Column(Text)
    
    # Specifications
    rated_power = Column(Float)  # kW
    rated_voltage = Column(Float)  # V
    rated_current = Column(Float)  # A
    rated_frequency = Column(Float)  # Hz
    
    # Status
    is_active = Column(Boolean, default=True)
    maintenance_schedule = Column(JSON)  # Flexible maintenance data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sensor_data = relationship("SensorData", back_populates="equipment")
    anomalies = relationship("Anomaly", back_populates="equipment")
