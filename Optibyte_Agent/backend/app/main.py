from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import structlog

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.api.router import api_router
from app.services.websocket_manager import websocket_manager
from app.services.ai_agent import ai_agent
from app.services.anomaly_detector import anomaly_detector


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    setup_logging()
    logger = structlog.get_logger()
    
    logger.info("Starting Optibyte AI Agent", version=settings.APP_VERSION)
    
    # Initialize database
    await init_db()
    
    # Initialize AI services
    await ai_agent.initialize()
    await anomaly_detector.initialize()
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    await ai_agent.cleanup()
    await anomaly_detector.cleanup()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Agent for Optibyte Energy Management System",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.optibyte.com"]
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Optibyte AI Agent API",
        "version": settings.APP_VERSION,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "services": {
            "database": "connected",
            "redis": "connected",
            "ai_agent": "ready",
            "anomaly_detector": "ready"
        }
    }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process message through AI agent
            response = await ai_agent.process_message(
                message=data.get("message"),
                user_id=data.get("user_id"),
                session_id=client_id
            )
            
            # Send response back to client
            await websocket_manager.send_personal_message(response, client_id)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
    except Exception as e:
        logger = structlog.get_logger()
        logger.error("WebSocket error", error=str(e), client_id=client_id)
        await websocket_manager.send_personal_message(
            {"type": "error", "message": "An error occurred processing your request"},
            client_id
        )
