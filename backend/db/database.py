from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
 
 
# SQLite database file
DATABASE_URL = "sqlite:///./app.db"

# Required for SQLite
connect_args = {"check_same_thread": False}

# SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base
class Base(DeclarativeBase):
    pass

# FastAPI dependency for DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()