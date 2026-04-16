"""
Gestión de conexión a la base de datos SQL para KICKDEX.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.data.models import Base

# Usamos SQLite para desarrollo, configurable a Postgres via env var
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kickdex.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Crea las tablas en la base de datos."""
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """Generador de sesión para FastAPI / Scripts."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
