from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from src.api.config import Settings, get_settings
from src.api.db import SessionLocal


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session for request handling and ensure it is closed afterwards."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# PUBLIC_INTERFACE
def get_config() -> Settings:
    """Provide the current application settings (useful for dependency injection in routes)."""
    return get_settings()
