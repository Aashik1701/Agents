from fastapi import APIRouter
from app.api.endpoints import auth, dashboard, equipment, sensor_data, anomalies, reports, chat

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(equipment.router, prefix="/equipment", tags=["equipment"])
api_router.include_router(sensor_data.router, prefix="/sensor-data", tags=["sensor-data"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
