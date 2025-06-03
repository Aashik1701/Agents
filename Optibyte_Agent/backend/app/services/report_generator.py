from typing import Dict, List, Any, Optional
import io
import json
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import structlog
from weasyprint import HTML, CSS
from jinja2 import Template
import pandas as pd

from app.core.config import settings
from app.models import Report
from app.services.data_service import data_service
from app.services.chart_generator import chart_generator
from app.core.database import async_session_maker

logger = structlog.get_logger()


class ReportGenerator:
    """Service for generating various types of reports"""
    
    def __init__(self):
        self.report_templates = {
            "daily": self._get_daily_template(),
            "weekly": self._get_weekly_template(),
            "monthly": self._get_monthly_template(),
            "anomaly": self._get_anomaly_template(),
            "custom": self._get_custom_template()
        }
    
    async def generate_report(
        self, 
        report_type: str, 
        time_range: Dict[str, datetime], 
        user_id: str,
        equipment_ids: List[str] = None
    ) -> Dict[str, Any]:
        """Generate a report based on type and parameters"""
        
        try:
            # Collect data based on report type
            report_data = await self._collect_report_data(report_type, time_range, equipment_ids)
            
            # Generate charts
            charts = await self._generate_report_charts(report_data, report_type)
            
            # Create report content
            report_content = {
                "type": report_type,
                "generated_at": datetime.now().isoformat(),
                "time_range": {
                    "start": time_range["start"].isoformat(),
                    "end": time_range["end"].isoformat()
                },
                "data": report_data,
                "charts": charts,
                "summary": await self._generate_summary(report_data, report_type)
            }
            
            # Generate PDF
            pdf_path = await self._generate_pdf_report(report_content, report_type)
            
            # Save report to database
            report_record = await self._save_report_to_db(
                report_content, 
                pdf_path, 
                user_id, 
                time_range
            )
            
            return {
                "id": report_record.id,
                "type": report_type,
                "title": report_record.title,
                "generated_at": report_record.generated_at.isoformat(),
                "file_path": pdf_path,
                "summary": report_content["summary"],
                "charts": charts,
                "download_url": f"/api/v1/reports/{report_record.id}/download"
            }
            
        except Exception as e:
            logger.error("Error generating report", error=str(e), report_type=report_type)
            raise
    
    async def _collect_report_data(
        self, 
        report_type: str, 
        time_range: Dict[str, datetime], 
        equipment_ids: List[str] = None
    ) -> Dict[str, Any]:
        """Collect data for the report"""
        
        data = {}
        
        # Get sensor data
        sensor_data = await data_service.get_sensor_data(equipment_ids, time_range)
        data["sensor_data"] = sensor_data
        
        # Get energy summary
        energy_summary = await data_service.get_energy_summary(time_range)
        data["energy_summary"] = energy_summary
        
        # Get equipment status
        equipment_status = await data_service.get_equipment_status(equipment_ids)
        data["equipment_status"] = equipment_status
        
        # Get anomalies
        hours = int((time_range["end"] - time_range["start"]).total_seconds() / 3600)
        anomalies = await data_service.get_recent_anomalies(hours)
        data["anomalies"] = anomalies
        
        # Additional data based on report type
        if report_type == "weekly" or report_type == "monthly":
            # Get peak usage analysis
            days = 7 if report_type == "weekly" else 30
            peak_analysis = await data_service.get_peak_usage_analysis(days)
            data["peak_analysis"] = peak_analysis
        
        return data
    
    async def _generate_report_charts(self, report_data: Dict[str, Any], report_type: str) -> List[Dict[str, Any]]:
        """Generate charts for the report"""
        charts = []
        
        try:
            sensor_data = report_data.get("sensor_data", [])
            
            if sensor_data:
                # Time series chart
                time_chart = await chart_generator.create_time_series_chart(sensor_data)
                if time_chart:
                    charts.append(time_chart)
                
                # Power consumption chart
                power_chart = await chart_generator.create_power_consumption_chart(sensor_data)
                if power_chart:
                    charts.append(power_chart)
                
                # Power factor chart
                pf_chart = await chart_generator.create_power_factor_chart(sensor_data)
                if pf_chart:
                    charts.append(pf_chart)
            
            # Anomaly chart
            anomalies = report_data.get("anomalies", [])
            if anomalies:
                anomaly_chart = await chart_generator.create_anomaly_chart(anomalies)
                if anomaly_chart:
                    charts.append(anomaly_chart)
        
        except Exception as e:
            logger.error("Error generating report charts", error=str(e))
        
        return charts
    
    async def _generate_summary(self, report_data: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Generate executive summary for the report"""
        
        summary = {
            "total_energy": 0,
            "total_cost": 0,
            "total_carbon": 0,
            "equipment_count": 0,
            "anomaly_count": 0,
            "critical_anomalies": 0,
            "key_insights": [],
            "recommendations": []
        }
        
        try:
            # Energy summary
            energy_summary = report_data.get("energy_summary", {})
            summary["total_energy"] = energy_summary.get("total_energy", 0)
            summary["total_cost"] = energy_summary.get("total_cost", 0)
            summary["total_carbon"] = energy_summary.get("total_carbon", 0)
            
            # Equipment count
            equipment_status = report_data.get("equipment_status", {})
            summary["equipment_count"] = len(equipment_status)
            
            # Anomaly statistics
            anomalies = report_data.get("anomalies", [])
            summary["anomaly_count"] = len(anomalies)
            summary["critical_anomalies"] = len([a for a in anomalies if a.get("severity") == "critical"])
            
            # Generate insights
            summary["key_insights"] = self._generate_insights(report_data)
            
            # Generate recommendations
            summary["recommendations"] = self._generate_recommendations(report_data)
        
        except Exception as e:
            logger.error("Error generating summary", error=str(e))
        
        return summary
    
    def _generate_insights(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate key insights from the data"""
        insights = []
        
        try:
            # Energy insights
            energy_summary = report_data.get("energy_summary", {})
            if energy_summary.get("total_energy", 0) > 0:
                insights.append(f"Total energy consumption: {energy_summary['total_energy']:.1f} kWh")
            
            # Equipment insights
            equipment_breakdown = energy_summary.get("equipment_breakdown", {})
            if equipment_breakdown:
                top_consumer = max(equipment_breakdown.items(), key=lambda x: x[1].get("energy", 0))
                insights.append(f"Highest energy consumer: {top_consumer[0]} ({top_consumer[1].get('energy', 0):.1f} kWh)")
            
            # Anomaly insights
            anomalies = report_data.get("anomalies", [])
            if anomalies:
                anomaly_types = {}
                for anomaly in anomalies:
                    anomaly_type = anomaly.get("type", "unknown")
                    anomaly_types[anomaly_type] = anomaly_types.get(anomaly_type, 0) + 1
                
                most_common = max(anomaly_types.items(), key=lambda x: x[1])
                insights.append(f"Most common anomaly: {most_common[0]} ({most_common[1]} occurrences)")
            
            # Peak usage insights
            peak_analysis = report_data.get("peak_analysis", {})
            if peak_analysis.get("peak_hours"):
                peak_hours = peak_analysis["peak_hours"]
                insights.append(f"Peak usage hours: {', '.join(map(str, peak_hours))}")
        
        except Exception as e:
            logger.error("Error generating insights", error=str(e))
        
        return insights
    
    def _generate_recommendations(self, report_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate recommendations based on the data"""
        recommendations = []
        
        try:
            # Anomaly-based recommendations
            anomalies = report_data.get("anomalies", [])
            critical_anomalies = [a for a in anomalies if a.get("severity") == "critical"]
            
            if critical_anomalies:
                recommendations.append({
                    "type": "urgent",
                    "title": "Address Critical Anomalies",
                    "description": f"There are {len(critical_anomalies)} critical anomalies requiring immediate attention."
                })
            
            # Power factor recommendations
            sensor_data = report_data.get("sensor_data", [])
            if sensor_data:
                low_pf_data = [d for d in sensor_data if d.get("power_factor") and d["power_factor"] < 0.8]
                if low_pf_data:
                    recommendations.append({
                        "type": "efficiency",
                        "title": "Improve Power Factor",
                        "description": "Some equipment shows low power factor. Consider power factor correction to improve efficiency."
                    })
            
            # Peak usage recommendations
            peak_analysis = report_data.get("peak_analysis", {})
            if peak_analysis.get("recommendations"):
                for rec in peak_analysis["recommendations"]:
                    recommendations.append({
                        "type": "optimization",
                        "title": rec.get("type", "Load Optimization"),
                        "description": rec.get("description", "")
                    })
        
        except Exception as e:
            logger.error("Error generating recommendations", error=str(e))
        
        return recommendations
    
    async def _generate_pdf_report(self, report_content: Dict[str, Any], report_type: str) -> str:
        """Generate PDF report from content"""
        
        try:
            # Get template
            template_str = self.report_templates.get(report_type, self.report_templates["custom"])
            template = Template(template_str)
            
            # Render HTML
            html_content = template.render(report=report_content)
            
            # Create temporary file for PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                # Generate PDF
                HTML(string=html_content).write_pdf(
                    temp_file.name,
                    stylesheets=[CSS(string=self._get_pdf_styles())]
                )
                
                return temp_file.name
        
        except Exception as e:
            logger.error("Error generating PDF", error=str(e))
            raise
    
    async def _save_report_to_db(
        self, 
        content: Dict[str, Any], 
        pdf_path: str, 
        user_id: str, 
        time_range: Dict[str, datetime]
    ) -> Report:
        """Save report record to database"""
        
        async with async_session_maker() as session:
            report = Report(
                title=f"{content['type'].title()} Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                type=content["type"],
                content=content,
                summary=content.get("summary", {}).get("key_insights", []),
                created_by=int(user_id),
                start_date=time_range["start"],
                end_date=time_range["end"],
                file_path=pdf_path,
                status="ready"
            )
            
            session.add(report)
            await session.commit()
            await session.refresh(report)
            
            return report
    
    def _get_daily_template(self) -> str:
        """Get daily report template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Daily Energy Report</title>
            <meta charset="utf-8">
        </head>
        <body>
            <div class="header">
                <h1>Optibyte Daily Energy Report</h1>
                <p>Generated: {{ report.generated_at }}</p>
                <p>Period: {{ report.time_range.start }} to {{ report.time_range.end }}</p>
            </div>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <div class="metrics">
                    <div class="metric">
                        <h3>Total Energy</h3>
                        <p>{{ "%.1f"|format(report.summary.total_energy) }} kWh</p>
                    </div>
                    <div class="metric">
                        <h3>Total Cost</h3>
                        <p>${{ "%.2f"|format(report.summary.total_cost) }}</p>
                    </div>
                    <div class="metric">
                        <h3>Carbon Footprint</h3>
                        <p>{{ "%.1f"|format(report.summary.total_carbon) }} kg CO₂</p>
                    </div>
                    <div class="metric">
                        <h3>Anomalies</h3>
                        <p>{{ report.summary.anomaly_count }}</p>
                    </div>
                </div>
            </div>
            
            <div class="insights">
                <h2>Key Insights</h2>
                <ul>
                {% for insight in report.summary.key_insights %}
                    <li>{{ insight }}</li>
                {% endfor %}
                </ul>
            </div>
            
            <div class="recommendations">
                <h2>Recommendations</h2>
                {% for rec in report.summary.recommendations %}
                <div class="recommendation {{ rec.type }}">
                    <h3>{{ rec.title }}</h3>
                    <p>{{ rec.description }}</p>
                </div>
                {% endfor %}
            </div>
            
            <div class="equipment">
                <h2>Equipment Status</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Equipment ID</th>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Energy (kWh)</th>
                        </tr>
                    </thead>
                    <tbody>
                    {% for id, eq in report.data.equipment_status.items() %}
                        <tr>
                            <td>{{ id }}</td>
                            <td>{{ eq.name }}</td>
                            <td class="status {{ eq.status }}">{{ eq.status }}</td>
                            <td>{{ "%.1f"|format(report.data.energy_summary.equipment_breakdown[id].energy or 0) }}</td>
                        </tr>
                    {% endfor %}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
    
    def _get_weekly_template(self) -> str:
        """Get weekly report template"""
        return self._get_daily_template().replace("Daily", "Weekly")
    
    def _get_monthly_template(self) -> str:
        """Get monthly report template"""
        return self._get_daily_template().replace("Daily", "Monthly")
    
    def _get_anomaly_template(self) -> str:
        """Get anomaly report template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Anomaly Report</title>
            <meta charset="utf-8">
        </head>
        <body>
            <div class="header">
                <h1>Optibyte Anomaly Report</h1>
                <p>Generated: {{ report.generated_at }}</p>
                <p>Period: {{ report.time_range.start }} to {{ report.time_range.end }}</p>
            </div>
            
            <div class="summary">
                <h2>Anomaly Summary</h2>
                <p>Total anomalies detected: {{ report.summary.anomaly_count }}</p>
                <p>Critical anomalies: {{ report.summary.critical_anomalies }}</p>
            </div>
            
            <div class="anomalies">
                <h2>Detected Anomalies</h2>
                {% for anomaly in report.data.anomalies %}
                <div class="anomaly {{ anomaly.severity }}">
                    <h3>{{ anomaly.type }} - {{ anomaly.equipment_id }}</h3>
                    <p><strong>Severity:</strong> {{ anomaly.severity }}</p>
                    <p><strong>Description:</strong> {{ anomaly.description }}</p>
                    <p><strong>Detected:</strong> {{ anomaly.detected_at }}</p>
                    <p><strong>Status:</strong> {{ "Resolved" if anomaly.is_resolved else "Active" }}</p>
                </div>
                {% endfor %}
            </div>
        </body>
        </html>
        """
    
    def _get_custom_template(self) -> str:
        """Get custom report template"""
        return self._get_daily_template().replace("Daily", "Custom")
    
    def _get_pdf_styles(self) -> str:
        """Get CSS styles for PDF"""
        return """
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            color: #333;
        }
        
        .header {
            border-bottom: 2px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #2563eb;
            margin: 0;
        }
        
        .metrics {
            display: flex;
            justify-content: space-between;
            margin: 20px 0;
        }
        
        .metric {
            text-align: center;
            padding: 15px;
            background-color: #f8fafc;
            border-radius: 8px;
            min-width: 120px;
        }
        
        .metric h3 {
            margin: 0 0 10px 0;
            color: #64748b;
            font-size: 14px;
        }
        
        .metric p {
            margin: 0;
            font-size: 24px;
            font-weight: bold;
            color: #1e293b;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        
        th {
            background-color: #f1f5f9;
            font-weight: bold;
        }
        
        .status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .status.online { background-color: #dcfce7; color: #166534; }
        .status.warning { background-color: #fef3c7; color: #92400e; }
        .status.critical { background-color: #fecaca; color: #991b1b; }
        .status.offline { background-color: #f1f5f9; color: #64748b; }
        
        .recommendation {
            margin: 15px 0;
            padding: 15px;
            border-left: 4px solid #64748b;
            background-color: #f8fafc;
        }
        
        .recommendation.urgent {
            border-left-color: #dc2626;
            background-color: #fef2f2;
        }
        
        .recommendation.efficiency {
            border-left-color: #059669;
            background-color: #f0fdf4;
        }
        
        .anomaly {
            margin: 15px 0;
            padding: 15px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
        }
        
        .anomaly.critical {
            border-color: #dc2626;
            background-color: #fef2f2;
        }
        
        .anomaly.high {
            border-color: #d97706;
            background-color: #fffbeb;
        }
        """


# Global instance
report_generator = ReportGenerator()
