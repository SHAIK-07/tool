import sqlite3
import os
from pathlib import Path

def migrate_database():
    """
    Add the quotation_file_path column to the enquiries table if it doesn't exist.
    """
    # Find the SQLite database file
    db_path = Path("db/sunmax.db")
    if not db_path.exists():
        print(f"Database file not found at {db_path}")
        return False

    print(f"Found database at {db_path}")

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the column already exists
        cursor.execute("PRAGMA table_info(enquiries)")
        columns = [column[1] for column in cursor.fetchall()]

        if "quotation_file_path" not in columns:
            print("Adding quotation_file_path column to enquiries table...")
            # Add the new column
            cursor.execute("ALTER TABLE enquiries ADD COLUMN quotation_file_path TEXT")
            conn.commit()
            print("Column added successfully!")
        else:
            print("Column quotation_file_path already exists in enquiries table.")

        conn.close()
        return True
    except Exception as e:
        print(f"Error migrating database: {e}")
        return False

if __name__ == "__main__":
    if migrate_database():
        print("Database migration completed successfully.")
    else:
        print("Database migration failed.")
