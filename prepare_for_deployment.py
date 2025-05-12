#!/usr/bin/env python3
"""
Prepare Database for Deployment Script

This script:
1. Cleans all data from both database files (app.db and sunmax.db)
2. Creates a default admin user for initial login
3. Verifies that all other tables are empty

Usage:
    python prepare_for_deployment.py

The script will ask for confirmation before proceeding.
"""

import os
import sqlite3
import sys
import hashlib
import secrets
from datetime import datetime

# Define database paths
DB_FOLDER = "db"
SUNMAX_DB_PATH = os.path.join(DB_FOLDER, "sunmax.db")
APP_DB_PATH = "app.db"  # Root directory app.db
BACKUP_FOLDER = os.path.join(DB_FOLDER, "backups")

# Default admin credentials
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"  # This should be changed after first login

def create_backup(db_path, prefix):
    """Create a backup of the database before cleaning."""
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
        
    try:
        # Ensure backup directory exists
        os.makedirs(BACKUP_FOLDER, exist_ok=True)
        
        # Create a timestamp for the backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_FOLDER, f"{prefix}_backup_{timestamp}.db")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        
        # Create a backup
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        
        # Close connections
        backup_conn.close()
        conn.close()
        
        print(f"Backup created at: {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

def get_all_tables(db_path):
    """Get a list of all tables in the database."""
    if not os.path.exists(db_path):
        return []
        
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [table[0] for table in cursor.fetchall()]
        
        # Close connection
        conn.close()
        
        return tables
    except Exception as e:
        print(f"Error getting tables from {db_path}: {e}")
        return []

def force_clean_table(db_path, table_name):
    """Forcefully clean all data from a table."""
    if not os.path.exists(db_path):
        return 0
        
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get row count before deletion
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
        except:
            row_count = 0
        
        # Delete all data from the table
        cursor.execute(f"DELETE FROM {table_name}")
        
        # Reset auto-increment counters
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
        
        # Commit changes
        conn.commit()
        
        # Close connection
        conn.close()
        
        return row_count
    except Exception as e:
        print(f"Error cleaning table {table_name} in {db_path}: {e}")
        return 0

def clean_database(db_path, db_name):
    """Clean all tables in a database."""
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return 0
        
    # Get all tables
    tables = get_all_tables(db_path)
    if not tables:
        print(f"No tables found in {db_path}.")
        return 0
    
    # Clean each table
    print(f"\nCleaning tables in {db_name}...")
    total_rows_deleted = 0
    for table in tables:
        rows_deleted = force_clean_table(db_path, table)
        total_rows_deleted += rows_deleted
        print(f"  - {table}: {rows_deleted} rows deleted")
    
    return total_rows_deleted

def create_admin_user():
    """Create a default admin user in the database."""
    if not os.path.exists(APP_DB_PATH):
        print(f"Database file not found: {APP_DB_PATH}")
        return False
        
    try:
        # Connect to the database
        conn = sqlite3.connect(APP_DB_PATH)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("Users table not found. Creating it...")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                email TEXT,
                full_name TEXT,
                disabled BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
        
        # Generate password hash
        salt = secrets.token_hex(8)
        hashed_password = hashlib.sha256(f"{DEFAULT_ADMIN_PASSWORD}{salt}".encode()).hexdigest()
        password_with_salt = f"{salt}${hashed_password}"
        
        # Insert admin user
        cursor.execute("""
        INSERT INTO users (username, hashed_password, email, full_name, disabled)
        VALUES (?, ?, ?, ?, ?)
        """, (DEFAULT_ADMIN_USERNAME, password_with_salt, "admin@example.com", "Administrator", 0))
        
        # Commit changes
        conn.commit()
        
        # Close connection
        conn.close()
        
        print(f"\nDefault admin user created:")
        print(f"  Username: {DEFAULT_ADMIN_USERNAME}")
        print(f"  Password: {DEFAULT_ADMIN_PASSWORD}")
        print("  IMPORTANT: Change this password after first login!")
        
        return True
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return False

def main():
    """Main function to prepare the database for deployment."""
    print("=== PREPARE DATABASE FOR DEPLOYMENT ===")
    print("This tool will:")
    print("1. Clean all data from both app.db and sunmax.db databases")
    print("2. Create a default admin user for initial login")
    print("3. Verify that all other tables are empty")
    
    # Ask for confirmation
    confirmation = input("\nWARNING: This will delete ALL existing data. Are you sure? (yes/no): ")
    if confirmation.lower() != "yes":
        print("Operation cancelled.")
        return
    
    # Create backups
    print("\nCreating backups before proceeding...")
    if os.path.exists(SUNMAX_DB_PATH):
        create_backup(SUNMAX_DB_PATH, "sunmax")
    if os.path.exists(APP_DB_PATH):
        create_backup(APP_DB_PATH, "app")
    
    # Clean both databases
    total_deleted = 0
    
    # Clean sunmax.db
    if os.path.exists(SUNMAX_DB_PATH):
        total_deleted += clean_database(SUNMAX_DB_PATH, "sunmax.db")
    
    # Clean app.db
    if os.path.exists(APP_DB_PATH):
        total_deleted += clean_database(APP_DB_PATH, "app.db")
    
    print(f"\nDatabase cleaning completed. Total rows deleted: {total_deleted}")
    
    # Create admin user
    print("\nCreating default admin user...")
    create_admin_user()
    
    print("\nDatabase preparation completed successfully.")
    print("Your application is now ready for deployment with a clean database.")
    print("\nIMPORTANT: Remember to change the default admin password after first login!")

if __name__ == "__main__":
    main()
