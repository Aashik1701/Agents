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


class DashboardMetrics(BaseModel):
    """Dashboard metrics response"""
    total_equipment: int
    active_equipment: int
    total_energy_today: float
    total_energy_month: float
    average_efficiency: float
    active_anomalies: int
    cost_savings_month: float
    top_consumers: List[Dict[str, Any]]
    recent_anomalies: List[Dict[str, Any]]
    energy_trend_24h: List[Dict[str, Any]]


class ChartRequest(BaseModel):
    """Chart generation request"""
    chart_type: str  # line, bar, pie, scatter, heatmap
    equipment_ids: Optional[List[int]] = None
    metrics: List[str]  # power, energy, temperature, etc.
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    aggregation: Optional[str] = "hour"  # minute, hour, day, week
    title: Optional[str] = None


class ChartResponse(BaseModel):
    """Chart generation response"""
    chart_data: Dict[str, Any]
    chart_config: Dict[str, Any]
    metadata: Dict[str, Any]
