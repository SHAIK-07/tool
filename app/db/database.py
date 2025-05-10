from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from app.core.config import IN_GCP

# Ensure db directory exists
DB_FOLDER = "db"
os.makedirs(DB_FOLDER, exist_ok=True)

# Use SQLite for local development
SQLITE_DATABASE_URL = f"sqlite:///./db/sunmax.db"

# Create engine with SQLite
engine = create_engine(
    SQLITE_DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,  # Helps with connection drops
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# Dependency for DB session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database tables
def init_db():
    """Initialize the database by creating all tables."""
    # Import models here to avoid circular imports
    # We need to import models to ensure they are registered with the Base
    import app.db.models  # noqa
    from sqlalchemy import inspect

    try:
        # Simply create tables if they don't exist
        # This is a safe operation that won't affect existing data
        Base.metadata.create_all(bind=engine, checkfirst=True)

        # Check if we have tables (only log in debug mode)
        if os.environ.get('DEBUG', '').lower() in ('true', '1', 't'):
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            if tables:
                print(f"Database initialized with {len(tables)} tables: {', '.join(tables)}")
            else:
                print("No tables found in database. Tables have been created.")

    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        print("Application may not function correctly without a database.")
