

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Database URLs
ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./chatboost.db"
SYNC_DATABASE_URL = "sqlite:///./chatboost.db"

# Create async engine
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,  # Set to False in production
    future=True
)

# Create sync engine
sync_engine = create_engine(
    SYNC_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Create async session maker
async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create sync session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Base class for all models
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_async_session() -> AsyncSession:
    """
    Dependency to get async database session.
    
    Yields:
        AsyncSession: Database session for async operations
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session() -> SessionLocal:
    """
    Dependency to get sync database session.
    
    Yields:
        Session: Database session for sync operations
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db():
    """
    Dependency to get sync database session for FastAPI.
    
    Yields:
        Session: Database session for sync operations
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """
    Initialize database tables.
    Call this function on application startup.
    """
    async with async_engine.begin() as conn:
        # Import models here to ensure they are registered with Base
        from ..models.auth import User
        from ..models.bot_builder import Bot, BotFlow, BotNode, Template
        await conn.run_sync(Base.metadata.create_all)
