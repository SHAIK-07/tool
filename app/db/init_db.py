"""
Database initialization script.
This script creates all the necessary tables in the database.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, engine
from app.db import models

def init_db():
    """Initialize the database by creating all tables."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    init_db()
