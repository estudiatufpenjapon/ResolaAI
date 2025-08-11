from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Create database engine
# Engine handles connection pool and database communication
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recreate connections every 5 minutes
    echo=False           # Set to True for SQL query debugging
)

# Create session factory
# Sessions handle individual database transactions
SessionLocal = sessionmaker(
    autocommit=False,    # Manual transaction control
    autoflush=False,     # Manual flush control
    bind=engine          # Bind to our database engine
)

# Base class for all database models
# All SQLAlchemy models will inherit from this
Base = declarative_base()

# Dependency function for FastAPI
# Provides database session to API endpoints
def get_db():
    """
    Database session dependency for FastAPI endpoints
    Automatically closes session after request
    """
    db = SessionLocal()
    try:
        yield db  # Provide session to endpoint
    finally:
        db.close()  # Always close session