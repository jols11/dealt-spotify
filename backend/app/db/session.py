from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.models import entities  # noqa: F401

settings = get_settings()
connect_args = {"check_same_thread": False} if settings.resolved_database_url.startswith("sqlite") else {}
engine = create_engine(settings.resolved_database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    if settings.resolved_database_url.startswith("sqlite"):
        db_path = Path(settings.resolved_database_url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
