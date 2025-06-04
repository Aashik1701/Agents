from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime, timedelta
import os

from app.core.database import get_db
from app.models.user import User
from app.models.report import Report
from app.schemas.report import (
    ReportCreate,
    ReportResponse,
    ReportQuery,
    ReportStatus,
    ReportType,
    ReportFormat
)
from app.utils.auth import get_current_user
from app.services.report_generator import report_generator

router = APIRouter()


@router.get("/", response_model=List[ReportResponse])
async def get_reports(
    report_type: Optional[ReportType] = None,
    status: Optional[ReportStatus] = None,
    generated_by: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get reports with filtering"""
    query = select(Report)
    
    # Apply filters
    conditions = []
    if report_type:
        conditions.append(Report.report_type == report_type)
    if status:
        conditions.append(Report.status == status)
    if generated_by:
        conditions.append(Report.generated_by == generated_by)
    if start_date:
        conditions.append(Report.created_at >= start_date)
    if end_date:
        conditions.append(Report.created_at <= end_date)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(desc(Report.created_at)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    reports = result.scalars().all()
    
    return reports


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific report by ID"""
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return report


@router.post("/", response_model=ReportResponse)
async def create_report(
    report_data: ReportCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create and generate new report"""
    
    # Set default date range if not provided
    if not report_data.start_date or not report_data.end_date:
        end_date = datetime.now()
        if report_data.report_type == ReportType.DAILY:
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif report_data.report_type == ReportType.WEEKLY:
            start_date = end_date - timedelta(days=7)
        elif report_data.report_type == ReportType.MONTHLY:
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif report_data.report_type == ReportType.QUARTERLY:
            # Get first day of quarter
            quarter_start_month = ((end_date.month - 1) // 3) * 3 + 1
            start_date = end_date.replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif report_data.report_type == ReportType.ANNUAL:
            start_date = end_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # CUSTOM
            if not report_data.start_date or not report_data.end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Start date and end date are required for custom reports"
                )
            start_date = report_data.start_date
            end_date = report_data.end_date
        
        # Update the report data with calculated dates
        if not report_data.start_date:
            report_data.start_date = start_date
        if not report_data.end_date:
            report_data.end_date = end_date
    
    # Create report record
    report = Report(
        name=report_data.name,
        report_type=report_data.report_type,
        format=report_data.format,
        equipment_ids=report_data.equipment_ids,
        start_date=report_data.start_date,
        end_date=report_data.end_date,
        parameters=report_data.parameters or {},
        generated_by=current_user.id,
        status=ReportStatus.PENDING
    )
    
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # Generate report in background
    background_tasks.add_task(generate_report_task, report.id, db)
    
    return report


async def generate_report_task(report_id: int, db: AsyncSession):
    """Background task to generate report"""
    try:
        # Get report from database
        result = await db.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            return
        
        # Update status to generating
        report.status = ReportStatus.GENERATING
        await db.commit()
        
        # Generate report using report service
        report_result = await report_generator.generate_report(
            report_type=report.report_type,
            equipment_ids=report.equipment_ids,
            start_date=report.start_date,
            end_date=report.end_date,
            format=report.format,
            parameters=report.parameters
        )
        
        # Update report with results
        report.status = ReportStatus.COMPLETED
        report.file_path = report_result.get("file_path")
        report.file_size = report_result.get("file_size")
        report.completed_at = datetime.utcnow()
        
        await db.commit()
        
    except Exception as e:
        # Update report with error
        if report:
            report.status = ReportStatus.FAILED
            report.error_message = str(e)
            await db.commit()


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download generated report file"""
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report is not ready for download. Status: {report.status}"
        )
    
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found"
        )
    
    # Determine content type based on format
    content_types = {
        ReportFormat.PDF: "application/pdf",
        ReportFormat.HTML: "text/html",
        ReportFormat.JSON: "application/json",
        ReportFormat.CSV: "text/csv"
    }
    
    return FileResponse(
        path=report.file_path,
        media_type=content_types.get(report.format, "application/octet-stream"),
        filename=f"{report.name}.{report.format.value}"
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete report and its file"""
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Delete file if it exists
    if report.file_path and os.path.exists(report.file_path):
        try:
            os.remove(report.file_path)
        except OSError:
            pass  # File might be in use or already deleted
    
    # Delete report record
    await db.delete(report)
    await db.commit()
    
    return {"message": "Report deleted successfully"}


@router.post("/templates")
async def get_report_templates(
    current_user: User = Depends(get_current_user)
):
    """Get available report templates"""
    templates = [
        {
            "name": "Daily Energy Summary",
            "type": "daily",
            "description": "Daily energy consumption and efficiency report",
            "parameters": {
                "include_charts": True,
                "include_anomalies": True,
                "include_recommendations": True
            }
        },
        {
            "name": "Weekly Equipment Performance",
            "type": "weekly",
            "description": "Weekly equipment performance and maintenance report",
            "parameters": {
                "include_maintenance_alerts": True,
                "include_efficiency_trends": True,
                "include_cost_analysis": True
            }
        },
        {
            "name": "Monthly Cost Analysis",
            "type": "monthly",
            "description": "Monthly energy cost and savings analysis",
            "parameters": {
                "include_cost_breakdown": True,
                "include_savings_opportunities": True,
                "include_benchmarking": True
            }
        },
        {
            "name": "Quarterly Sustainability Report",
            "type": "quarterly",
            "description": "Quarterly sustainability and carbon footprint report",
            "parameters": {
                "include_carbon_metrics": True,
                "include_sustainability_goals": True,
                "include_green_initiatives": True
            }
        },
        {
            "name": "Annual Comprehensive Report",
            "type": "annual",
            "description": "Annual comprehensive energy management report",
            "parameters": {
                "include_all_metrics": True,
                "include_year_over_year": True,
                "include_strategic_recommendations": True
            }
        }
    ]
    
    return {"templates": templates}


@router.post("/{report_id}/regenerate")
async def regenerate_report(
    report_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate an existing report"""
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Reset report status
    report.status = ReportStatus.PENDING
    report.error_message = None
    report.completed_at = None
    
    # Delete old file if it exists
    if report.file_path and os.path.exists(report.file_path):
        try:
            os.remove(report.file_path)
        except OSError:
            pass
    
    report.file_path = None
    report.file_size = None
    
    await db.commit()
    
    # Generate report in background
    background_tasks.add_task(generate_report_task, report.id, db)
    
    return {"message": "Report regeneration started", "report": report}


@router.get("/status/{report_id}")
async def get_report_status(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get report generation status"""
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return {
        "report_id": report.id,
        "status": report.status,
        "progress": 100 if report.status == ReportStatus.COMPLETED else 
                  50 if report.status == ReportStatus.GENERATING else 0,
        "error_message": report.error_message,
        "completed_at": report.completed_at,
        "file_ready": report.status == ReportStatus.COMPLETED and report.file_path is not None
    }
