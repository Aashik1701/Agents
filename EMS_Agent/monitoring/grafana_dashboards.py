"""
Grafana Dashboard Configuration for EMS Agent

This file contains the JSON configuration for comprehensive Grafana dashboards
that visualize all aspects of the EMS Agent system.
"""

GRAFANA_DASHBOARDS = {
    "ems_system_overview": {
        "dashboard": {
            "id": None,
            "title": "EMS Agent - System Overview",
            "tags": ["ems", "monitoring", "overview"],
            "style": "dark",
            "timezone": "browser",
            "refresh": "5s",
            "time": {
                "from": "now-1h",
                "to": "now"
            },
            "panels": [
                {
                    "id": 1,
                    "title": "System Health Score",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "ems_system_health_score",
                            "legendFormat": "Health Score"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "min": 0,
                            "max": 100,
                            "unit": "percent",
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": 0},
                                    {"color": "yellow", "value": 70},
                                    {"color": "green", "value": 90}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                },
                {
                    "id": 2,
                    "title": "Active Devices",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "count(rate(stream_messages_total[5m]) > 0)",
                            "legendFormat": "Active Devices"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
                },
                {
                    "id": 3,
                    "title": "Data Throughput",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "rate(stream_messages_total[1m])",
                            "legendFormat": "Messages/sec - {{type}}"
                        },
                        {
                            "expr": "data_throughput_bytes_per_second",
                            "legendFormat": "Bytes/sec - {{direction}}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                },
                {
                    "id": 4,
                    "title": "Anomaly Detection Rate",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "rate(anomalies_detected_total[5m])",
                            "legendFormat": "Anomalies/min"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                },
                {
                    "id": 5,
                    "title": "Service Response Times",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                            "legendFormat": "95th percentile"
                        },
                        {
                            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
                            "legendFormat": "50th percentile"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                }
            ]
        }
    },
    
    "ems_energy_analytics": {
        "dashboard": {
            "id": None,
            "title": "EMS Agent - Energy Analytics",
            "tags": ["ems", "energy", "analytics"],
            "style": "dark",
            "timezone": "browser",
            "refresh": "30s",
            "time": {
                "from": "now-24h",
                "to": "now"
            },
            "panels": [
                {
                    "id": 1,
                    "title": "Total Energy Consumption",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "sum(energy_consumption_total)",
                            "legendFormat": "Total kWh"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "kwatth",
                            "decimals": 2
                        }
                    },
                    "gridPos": {"h": 8, "w": 8, "x": 0, "y": 0}
                },
                {
                    "id": 2,
                    "title": "Peak Demand",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "max_over_time(power_demand_watts[24h])",
                            "legendFormat": "Peak kW"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "kwatt",
                            "decimals": 2
                        }
                    },
                    "gridPos": {"h": 8, "w": 8, "x": 8, "y": 0}
                },
                {
                    "id": 3,
                    "title": "Energy Efficiency Score",
                    "type": "gauge",
                    "targets": [
                        {
                            "expr": "energy_efficiency_score",
                            "legendFormat": "Efficiency %"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "min": 0,
                            "max": 100,
                            "unit": "percent",
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": 0},
                                    {"color": "yellow", "value": 60},
                                    {"color": "green", "value": 80}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 8, "x": 16, "y": 0}
                },
                {
                    "id": 4,
                    "title": "Power Consumption by Device",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "power_consumption_watts",
                            "legendFormat": "{{device_id}}"
                        }
                    ],
                    "gridPos": {"h": 12, "w": 12, "x": 0, "y": 8}
                },
                {
                    "id": 5,
                    "title": "Energy Cost Analysis",
                    "type": "table",
                    "targets": [
                        {
                            "expr": "energy_cost_total",
                            "legendFormat": "Cost",
                            "format": "table"
                        }
                    ],
                    "gridPos": {"h": 12, "w": 12, "x": 12, "y": 8}
                }
            ]
        }
    },
    
    "ems_security_monitoring": {
        "dashboard": {
            "id": None,
            "title": "EMS Agent - Security Monitoring",
            "tags": ["ems", "security", "monitoring"],
            "style": "dark",
            "timezone": "browser",
            "refresh": "10s",
            "time": {
                "from": "now-1h",
                "to": "now"
            },
            "panels": [
                {
                    "id": 1,
                    "title": "Authentication Attempts",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "rate(auth_attempts_total[5m])",
                            "legendFormat": "{{status}} - {{method}}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                },
                {
                    "id": 2,
                    "title": "Security Alerts",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "sum(rate(security_alerts_total[5m]))",
                            "legendFormat": "Alerts/min"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": 0},
                                    {"color": "yellow", "value": 1},
                                    {"color": "red", "value": 5}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0}
                },
                {
                    "id": 3,
                    "title": "Failed Login Attempts",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "sum(rate(auth_attempts_total{status=\"failed\"}[5m]))",
                            "legendFormat": "Failed/min"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
                },
                {
                    "id": 4,
                    "title": "Rate Limiting Events",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "rate(rate_limit_exceeded_total[1m])",
                            "legendFormat": "Rate Limits/min"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
                }
            ]
        }
    }
}


def create_grafana_dashboard_config():
    """Create Grafana dashboard configuration files."""
    import json
    import os
    
    # Create dashboard directory
    dashboard_dir = "/Users/aashik/Documents/Sustainabyte/agent/EMS_Agent/monitoring/dashboards"
    os.makedirs(dashboard_dir, exist_ok=True)
    
    # Write each dashboard to a separate file
    for name, config in GRAFANA_DASHBOARDS.items():
        file_path = os.path.join(dashboard_dir, f"{name}.json")
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Created dashboard config: {file_path}")


if __name__ == "__main__":
    create_grafana_dashboard_config()
