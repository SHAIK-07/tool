"""
Simplified database migration script.

This script is now a simple wrapper around the database initialization process.
For more complex migrations, use the setup_database.py script.
"""

from app.db.database import Base, engine

def run_migrations():
    """
    Run database migrations.

    This is now a simplified function that just ensures tables exist.
    For more complex migrations, use the setup_database.py script.
    """
    print("Running database migrations...")

    # Simply create tables if they don't exist
    # This is a safe operation that won't affect existing data
    Base.metadata.create_all(bind=engine, checkfirst=True)

    print("Database migrations completed.")
    print("Note: For schema changes, use the setup_database.py script.")

if __name__ == "__main__":
    run_migrations()
