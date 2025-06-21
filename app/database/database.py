# app/database/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base
import os
from google.cloud.sql.connector import Connector

# Cloud SQL Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "tradesage-mvp")
REGION = os.getenv("REGION", "us-central1")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "agentic-db")
DATABASE_NAME = os.getenv("DATABASE_NAME", "tradesage_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def create_cloud_sql_engine():
    """Create engine for Cloud SQL PostgreSQL"""
    connector = Connector()
    
    def getconn():
        return connector.connect(
            f"{PROJECT_ID}:{REGION}:{INSTANCE_NAME}",
            "pg8000",
            user=DB_USER,
            password=DB_PASSWORD,
            db=DATABASE_NAME
        )
    
    # Create engine with Cloud SQL connector
    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False  # Set to True for SQL debugging
    )
    
    return engine, connector

# Connect to database
if DB_PASSWORD:
    print("🐘 Connecting to Cloud SQL PostgreSQL...")
    engine, connector = create_cloud_sql_engine()
    print("✅ Cloud SQL connection established")

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables in the database."""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise

def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def close_connections():
    """Close database connections (important for Cloud SQL)"""
    if connector:
        connector.close()

# Initialize database on module import
create_tables()
