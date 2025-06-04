from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database and create tables"""
    try:
        async with engine.begin() as conn:
            # Enable TimescaleDB extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
            
            # Import all models to ensure they are registered
            from app.models import (
                user, equipment, sensor_data, 
                chat_session, anomaly, report
            )
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
            # Create hypertables for time-series data
            await conn.execute(text("""
                SELECT create_hypertable('sensor_data', 'timestamp', 
                    if_not_exists => TRUE);
            """))
            
            await conn.execute(text("""
                SELECT create_hypertable('anomalies', 'detected_at', 
                    if_not_exists => TRUE);
            """))
            
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
