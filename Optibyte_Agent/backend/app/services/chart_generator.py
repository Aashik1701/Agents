from typing import Dict, List, Any, Optional
import base64
import io
import json
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import pandas as pd
import structlog

logger = structlog.get_logger()


class ChartGenerator:
    """Service for generating charts and visualizations"""
    
    def __init__(self):
        # Configure matplotlib for non-interactive backend
        plt.switch_backend('Agg')
        
        # Default color schemes
        self.colors = {
            "primary": "#2563eb",
            "secondary": "#64748b", 
            "success": "#059669",
            "warning": "#d97706",
            "danger": "#dc2626",
            "info": "#0891b2"
        }
    
    async def generate_charts_for_data(self, data: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Generate appropriate charts based on data and query"""
        if not data:
            return []
        
        charts = []
        
        # Determine chart types based on query keywords
        query_lower = query.lower()
        
        # Time series charts
        if any(keyword in query_lower for keyword in ["trend", "over time", "history", "past"]):
            time_chart = await self.create_time_series_chart(data)
            if time_chart:
                charts.append(time_chart)
        
        # Power consumption charts
        if any(keyword in query_lower for keyword in ["power", "consumption", "energy"]):
            power_chart = await self.create_power_consumption_chart(data)
            if power_chart:
                charts.append(power_chart)
        
        # Power factor charts
        if "power factor" in query_lower or "pf" in query_lower:
            pf_chart = await self.create_power_factor_chart(data)
            if pf_chart:
                charts.append(pf_chart)
        
        # Temperature charts
        if "temperature" in query_lower or "temp" in query_lower:
            temp_chart = await self.create_temperature_chart(data)
            if temp_chart:
                charts.append(temp_chart)
        
        # If no specific charts requested, create a general overview
        if not charts:
            overview_chart = await self.create_overview_chart(data)
            if overview_chart:
                charts.append(overview_chart)
        
        return charts
    
    async def create_time_series_chart(self, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a time series chart showing multiple metrics"""
        if not data:
            return None
        
        try:
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Create subplots for different metrics
            fig = go.Figure()
            
            # Add power trace
            if 'power' in df.columns and df['power'].notna().any():
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['power'],
                    mode='lines',
                    name='Power (kW)',
                    line=dict(color=self.colors["primary"]),
                    yaxis='y'
                ))
            
            # Add current trace (secondary y-axis)
            if 'current' in df.columns and df['current'].notna().any():
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['current'],
                    mode='lines',
                    name='Current (A)',
                    line=dict(color=self.colors["secondary"]),
                    yaxis='y2'
                ))
            
            # Update layout
            fig.update_layout(
                title='Energy Metrics Over Time',
                xaxis_title='Time',
                yaxis=dict(title='Power (kW)', side='left'),
                yaxis2=dict(title='Current (A)', side='right', overlaying='y'),
                height=400,
                showlegend=True,
                hovermode='x unified'
            )
            
            return {
                "type": "time_series",
                "title": "Energy Metrics Over Time",
                "data": json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)),
                "description": "Time series showing power and current trends"
            }
            
        except Exception as e:
            logger.error("Error creating time series chart", error=str(e))
            return None
    
    async def create_power_consumption_chart(self, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a power consumption chart"""
        if not data:
            return None
        
        try:
            df = pd.DataFrame(data)
            
            # Group by equipment and sum power
            if 'equipment_id' in df.columns and 'power' in df.columns:
                power_by_equipment = df.groupby('equipment_id')['power'].mean().sort_values(ascending=False)
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=power_by_equipment.index,
                        y=power_by_equipment.values,
                        marker_color=self.colors["primary"],
                        text=[f'{val:.1f} kW' for val in power_by_equipment.values],
                        textposition='auto'
                    )
                ])
                
                fig.update_layout(
                    title='Average Power Consumption by Equipment',
                    xaxis_title='Equipment ID',
                    yaxis_title='Average Power (kW)',
                    height=400,
                    showlegend=False
                )
                
                return {
                    "type": "bar_chart",
                    "title": "Power Consumption by Equipment",
                    "data": json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)),
                    "description": "Average power consumption for each equipment"
                }
        
        except Exception as e:
            logger.error("Error creating power consumption chart", error=str(e))
            return None
    
    async def create_power_factor_chart(self, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a power factor chart"""
        if not data:
            return None
        
        try:
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            if 'power_factor' in df.columns and df['power_factor'].notna().any():
                fig = go.Figure()
                
                # Add power factor line
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['power_factor'],
                    mode='lines+markers',
                    name='Power Factor',
                    line=dict(color=self.colors["success"]),
                    marker=dict(size=4)
                ))
                
                # Add ideal power factor reference line
                fig.add_hline(
                    y=0.9, 
                    line_dash="dash", 
                    line_color=self.colors["warning"],
                    annotation_text="Ideal PF (0.9+)"
                )
                
                fig.update_layout(
                    title='Power Factor Trend',
                    xaxis_title='Time',
                    yaxis_title='Power Factor',
                    yaxis=dict(range=[0, 1]),
                    height=400,
                    showlegend=True
                )
                
                return {
                    "type": "line_chart",
                    "title": "Power Factor Trend",
                    "data": json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)),
                    "description": "Power factor trend with ideal reference line"
                }
        
        except Exception as e:
            logger.error("Error creating power factor chart", error=str(e))
            return None
    
    async def create_temperature_chart(self, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a temperature monitoring chart"""
        if not data:
            return None
        
        try:
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            if 'temperature' in df.columns and df['temperature'].notna().any():
                fig = go.Figure()
                
                # Add temperature line
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['temperature'],
                    mode='lines+markers',
                    name='Temperature',
                    line=dict(color=self.colors["danger"]),
                    marker=dict(size=4),
                    fill='tonexty'
                ))
                
                # Add warning threshold
                fig.add_hline(
                    y=80, 
                    line_dash="dash", 
                    line_color=self.colors["warning"],
                    annotation_text="Warning Threshold (80°C)"
                )
                
                # Add critical threshold
                fig.add_hline(
                    y=90, 
                    line_dash="dash", 
                    line_color=self.colors["danger"],
                    annotation_text="Critical Threshold (90°C)"
                )
                
                fig.update_layout(
                    title='Temperature Monitoring',
                    xaxis_title='Time',
                    yaxis_title='Temperature (°C)',
                    height=400,
                    showlegend=True
                )
                
                return {
                    "type": "temperature_chart",
                    "title": "Temperature Monitoring",
                    "data": json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)),
                    "description": "Temperature trend with warning and critical thresholds"
                }
        
        except Exception as e:
            logger.error("Error creating temperature chart", error=str(e))
            return None
    
    async def create_overview_chart(self, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create an overview chart with key metrics"""
        if not data:
            return None
        
        try:
            df = pd.DataFrame(data)
            
            # Create a dashboard-style chart with multiple metrics
            fig = go.Figure()
            
            # If we have equipment breakdown, show it
            if 'equipment_id' in df.columns:
                # Count data points per equipment
                equipment_counts = df['equipment_id'].value_counts()
                
                fig = go.Figure(data=[
                    go.Pie(
                        labels=equipment_counts.index,
                        values=equipment_counts.values,
                        hole=0.4,
                        textinfo='label+percent',
                        textposition='outside'
                    )
                ])
                
                fig.update_layout(
                    title='Data Distribution by Equipment',
                    height=400,
                    showlegend=True
                )
                
                return {
                    "type": "pie_chart",
                    "title": "Data Distribution by Equipment",
                    "data": json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)),
                    "description": "Distribution of sensor readings across equipment"
                }
        
        except Exception as e:
            logger.error("Error creating overview chart", error=str(e))
            return None
    
    async def generate_comparison_charts(self, comparison_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate charts for equipment comparison"""
        charts = []
        
        try:
            metrics = comparison_data.get("metrics", {})
            
            # Average Power Comparison
            if "average_power" in metrics:
                power_data = metrics["average_power"]
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=list(power_data.keys()),
                        y=list(power_data.values()),
                        marker_color=self.colors["primary"],
                        text=[f'{val:.1f} kW' for val in power_data.values()],
                        textposition='auto'
                    )
                ])
                
                fig.update_layout(
                    title='Average Power Comparison',
                    xaxis_title='Equipment ID',
                    yaxis_title='Average Power (kW)',
                    height=400
                )
                
                charts.append({
                    "type": "comparison_bar",
                    "title": "Average Power Comparison",
                    "data": json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)),
                    "description": "Comparison of average power consumption"
                })
            
            # Power Factor Comparison
            if "power_factor" in metrics:
                pf_data = metrics["power_factor"]
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=list(pf_data.keys()),
                        y=list(pf_data.values()),
                        marker_color=[
                            self.colors["success"] if val >= 0.9 
                            else self.colors["warning"] if val >= 0.8 
                            else self.colors["danger"] 
                            for val in pf_data.values()
                        ],
                        text=[f'{val:.2f}' for val in pf_data.values()],
                        textposition='auto'
                    )
                ])
                
                fig.add_hline(
                    y=0.9, 
                    line_dash="dash", 
                    line_color=self.colors["success"],
                    annotation_text="Target PF (0.9)"
                )
                
                fig.update_layout(
                    title='Power Factor Comparison',
                    xaxis_title='Equipment ID',
                    yaxis_title='Power Factor',
                    yaxis=dict(range=[0, 1]),
                    height=400
                )
                
                charts.append({
                    "type": "comparison_bar",
                    "title": "Power Factor Comparison",
                    "data": json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)),
                    "description": "Comparison of power factor efficiency"
                })
            
            # Efficiency Comparison
            if "efficiency" in metrics and any(metrics["efficiency"].values()):
                eff_data = {k: v for k, v in metrics["efficiency"].items() if v is not None}
                
                if eff_data:
                    fig = go.Figure(data=[
                        go.Bar(
                            x=list(eff_data.keys()),
                            y=list(eff_data.values()),
                            marker_color=self.colors["info"],
                            text=[f'{val:.1f}%' for val in eff_data.values()],
                            textposition='auto'
                        )
                    ])
                    
                    fig.update_layout(
                        title='Efficiency Comparison',
                        xaxis_title='Equipment ID',
                        yaxis_title='Efficiency (%)',
                        height=400
                    )
                    
                    charts.append({
                        "type": "comparison_bar",
                        "title": "Efficiency Comparison",
                        "data": json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)),
                        "description": "Comparison of equipment efficiency"
                    })
        
        except Exception as e:
            logger.error("Error generating comparison charts", error=str(e))
        
        return charts
    
    async def create_anomaly_chart(self, anomalies: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a chart showing anomaly distribution"""
        if not anomalies:
            return None
        
        try:
            df = pd.DataFrame(anomalies)
            
            # Count anomalies by type
            anomaly_counts = df['type'].value_counts()
            
            # Color mapping for different severities
            colors = []
            for anomaly_type in anomaly_counts.index:
                type_anomalies = df[df['type'] == anomaly_type]
                if any(type_anomalies['severity'] == 'critical'):
                    colors.append(self.colors["danger"])
                elif any(type_anomalies['severity'] == 'high'):
                    colors.append(self.colors["warning"])
                else:
                    colors.append(self.colors["info"])
            
            fig = go.Figure(data=[
                go.Bar(
                    x=anomaly_counts.index,
                    y=anomaly_counts.values,
                    marker_color=colors,
                    text=anomaly_counts.values,
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title='Anomaly Distribution by Type',
                xaxis_title='Anomaly Type',
                yaxis_title='Count',
                height=400
            )
            
            return {
                "type": "anomaly_chart",
                "title": "Anomaly Distribution",
                "data": json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)),
                "description": "Distribution of detected anomalies by type"
            }
        
        except Exception as e:
            logger.error("Error creating anomaly chart", error=str(e))
            return None


# Global instance
chart_generator = ChartGenerator()
