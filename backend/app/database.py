# backend/app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

# Use environment variable if present, otherwise default to SQLite for easy local dev.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(os.path.dirname(__file__), '..', 'dev.db')}")

# For SQLite we need this connect_args; for Postgres it will be ignored by create_engine
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create tables (idempotent)."""
    Base.metadata.create_all(bind=engine)


# Dependency for FastAPI routes
def get_db():
    """Yield a new SQLAlchemy session, and ensure it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
