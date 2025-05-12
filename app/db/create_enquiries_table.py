"""
Script to create the enquiries table in the database.
"""

import sqlite3
import os
from datetime import datetime

# Define database path
DB_FOLDER = "db"
DB_PATH = os.path.join(DB_FOLDER, "sunmax.db")

def create_enquiries_table():
    """Create the enquiries table if it doesn't exist."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='enquiries'")
        if cursor.fetchone():
            print("Enquiries table already exists.")
            
            # Check if the table has the required columns
            cursor.execute("PRAGMA table_info(enquiries)")
            columns = [column[1] for column in cursor.fetchall()]
            
            required_columns = [
                "id", "enquiry_number", "date", "customer_name", "phone_no", 
                "address", "requirements", "quotation_given", "quotation_amount",
                "created_at", "updated_at"
            ]
            
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"Missing columns in enquiries table: {missing_columns}")
                print("Recreating the table...")
                
                # Rename the existing table
                cursor.execute("ALTER TABLE enquiries RENAME TO enquiries_old")
                
                # Create the new table with all required columns
                create_table_sql = """
                CREATE TABLE enquiries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    enquiry_number TEXT UNIQUE NOT NULL,
                    date DATE NOT NULL,
                    customer_name TEXT NOT NULL,
                    phone_no TEXT NOT NULL,
                    address TEXT,
                    requirements TEXT,
                    quotation_given BOOLEAN DEFAULT 0,
                    quotation_amount REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                cursor.execute(create_table_sql)
                
                # Copy data from old table to new table (only for columns that exist in both)
                common_columns = [col for col in columns if col in required_columns]
                if common_columns:
                    columns_str = ", ".join(common_columns)
                    cursor.execute(f"INSERT INTO enquiries ({columns_str}) SELECT {columns_str} FROM enquiries_old")
                
                # Drop the old table
                cursor.execute("DROP TABLE enquiries_old")
                
                print("Table recreated successfully.")
            else:
                print("Enquiries table has all required columns.")
        else:
            print("Creating enquiries table...")
            
            # Create the table
            create_table_sql = """
            CREATE TABLE enquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enquiry_number TEXT UNIQUE NOT NULL,
                date DATE NOT NULL,
                customer_name TEXT NOT NULL,
                phone_no TEXT NOT NULL,
                address TEXT,
                requirements TEXT,
                quotation_given BOOLEAN DEFAULT 0,
                quotation_amount REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_sql)
            print("Enquiries table created successfully.")

        # Commit the changes
        conn.commit()
        
        # Close the connection
        conn.close()
        
        print("Enquiries table setup completed.")
        return True
    except Exception as e:
        print(f"Error creating enquiries table: {e}")
        return False

if __name__ == "__main__":
    create_enquiries_table()
