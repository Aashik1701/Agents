from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)  # daily, weekly, monthly, custom, anomaly
    
    # Report content
    content = Column(JSON, nullable=False)  # Report data and structure
    summary = Column(Text)
    
    # Generation details
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Time range
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    
    # Delivery
    is_scheduled = Column(Boolean, default=False)
    schedule_config = Column(JSON)  # Cron-like scheduling
    recipients = Column(JSON)  # Email list
    
    # Files
    file_path = Column(String)  # Path to generated PDF/CSV
    file_size = Column(Integer)
    
    # Status
    is_published = Column(Boolean, default=False)
    status = Column(String, default="draft")  # draft, generating, ready, sent, failed
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    created_by_user = relationship("User", back_populates="reports")
