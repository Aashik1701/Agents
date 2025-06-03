from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Anomaly(Base):
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    
    # Anomaly details
    type = Column(String, nullable=False)  # voltage_spike, zero_current, high_temperature, etc.
    severity = Column(String, default="medium")  # low, medium, high, critical
    description = Column(Text, nullable=False)
    
    # Detection details
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True)
    detection_method = Column(String)  # rule_based, ml_model, threshold
    confidence_score = Column(Float)  # 0.0 to 1.0
    
    # Values
    measured_value = Column(Float)
    expected_value = Column(Float)
    threshold_value = Column(Float)
    deviation_percentage = Column(Float)
    
    # Status
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    
    # Additional data
    context_data = Column(JSON)  # Related sensor readings, conditions
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    equipment = relationship("Equipment", back_populates="anomalies")
