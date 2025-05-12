import sqlite3
import os
from datetime import datetime

# Define database path
DB_FOLDER = "db"
DB_PATH = os.path.join(DB_FOLDER, "sunmax.db")


def create_customers_table():
    """Create the customers and customer_payments tables if they don't exist"""
    try:
        # Ensure the database folder exists
        os.makedirs(DB_FOLDER, exist_ok=True)

        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the customers table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
        if not cursor.fetchone():
            print("Creating customers table...")
            # Create the customers table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_code TEXT UNIQUE NOT NULL,
                date DATE NOT NULL,
                customer_name TEXT NOT NULL,
                phone_no TEXT NOT NULL,
                address TEXT,
                product_description TEXT,
                payment_method TEXT,
                payment_status TEXT DEFAULT 'Unpaid',
                total_amount REAL NOT NULL,
                amount_paid REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

        # Check if the customer_payments table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customer_payments'")
        if not cursor.fetchone():
            print("Creating customer_payments table...")
            # Create the customer_payments table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
            """)

        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        print("Customers tables created successfully")
    except Exception as e:
        print(f"Error creating customers tables: {e}")


if __name__ == "__main__":
    create_customers_table()
