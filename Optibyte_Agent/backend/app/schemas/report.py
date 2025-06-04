from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ReportType(str, Enum):
    """Report type enumeration"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Report format enumeration"""
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CSV = "csv"


class ReportStatus(str, Enum):
    """Report status enumeration"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportBase(BaseModel):
    """Base report schema"""
    name: str
    report_type: ReportType
    format: ReportFormat = ReportFormat.PDF
    equipment_ids: Optional[List[int]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    parameters: Optional[Dict[str, Any]] = None


class ReportCreate(ReportBase):
    """Report creation schema"""
    pass


class ReportResponse(ReportBase):
    """Report response schema"""
    id: int
    status: ReportStatus
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    generated_by: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportQuery(BaseModel):
    """Report query parameters"""
    report_type: Optional[ReportType] = None
    status: Optional[ReportStatus] = None
    generated_by: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: Optional[int] = 50
    offset: Optional[int] = 0
