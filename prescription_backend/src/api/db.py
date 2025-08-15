from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.api.config import get_settings

settings = get_settings()

# Build SQLAlchemy database URI from SQLITE_DB path
DATABASE_URL = f"sqlite:///{settings.SQLITE_DB}"

# For SQLite, check_same_thread must be False for use in multi-threaded FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)

# Factory for DB sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


# PUBLIC_INTERFACE
def init_db() -> None:
    """Create database tables for all SQLAlchemy models if they do not already exist."""
    # Import models so that SQLAlchemy sees them before creating tables
    from src.api import models  # noqa: F401  # pylint: disable=unused-import

    Base.metadata.create_all(bind=engine)
