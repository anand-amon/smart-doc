from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

# Use SQLite locally, Postgres on Cloud Run
ENV = os.getenv("ENV", "dev")

if ENV == "dev":
    # Local development
    DATABASE_URL = "sqlite:///./smartdoc.db"
    connect_args = {"check_same_thread": False}
else:
    # Production / staging (Postgres via Cloud SQL)
    DATABASE_URL = os.getenv("DATABASE_URL")
    connect_args = {}

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for ORM models
class Base(DeclarativeBase):
    pass

# FastAPI dependency
def get_db():
    """Yields a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
