"""
Database setup and configuration
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager

# Database configuration
DATABASE_URL = "sqlite+aiosqlite:///./sitewatch.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """Initialize database and create tables"""
    # Import models here to avoid circular imports
    from models import Base as ModelsBase
    async with engine.begin() as conn:
        await conn.run_sync(ModelsBase.metadata.create_all)

@asynccontextmanager
async def get_db():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 