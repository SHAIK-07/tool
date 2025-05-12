#!/usr/bin/env python3
"""
Force Clean Database Script

This script forcefully cleans all data from both database files (app.db and sunmax.db).
It uses both SQLAlchemy and direct SQLite commands to ensure thorough cleaning.

Usage:
    python force_clean_database.py

The script will ask for confirmation before deleting any data.
"""

import os
import sqlite3
import sys
from datetime import datetime

# Define database paths
DB_FOLDER = "db"
SUNMAX_DB_PATH = os.path.join(DB_FOLDER, "sunmax.db")
APP_DB_PATH = "app.db"  # Root directory app.db
BACKUP_FOLDER = os.path.join(DB_FOLDER, "backups")

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
        
        # Vacuum the database to reclaim space
        cursor.execute("VACUUM")
        
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
    
    # Show tables to be cleaned
    print(f"\nThe following tables will be cleaned in {db_name}:")
    for table in tables:
        print(f"  - {table}")
    
    # Create a backup
    print(f"\nCreating backup of {db_name} before cleaning...")
    create_backup(db_path, db_name.replace('.', '_'))
    
    # Clean each table
    print(f"\nCleaning tables in {db_name}...")
    total_rows_deleted = 0
    for table in tables:
        rows_deleted = force_clean_table(db_path, table)
        total_rows_deleted += rows_deleted
        print(f"  - {table}: {rows_deleted} rows deleted")
    
    return total_rows_deleted

def main():
    """Main function to clean both databases."""
    print("=== FORCE CLEAN DATABASE TOOL ===")
    print("This tool will delete ALL data from both app.db and sunmax.db databases.")
    print("The database structure will be preserved, but ALL DATA WILL BE LOST.")
    
    # Ask for confirmation
    confirmation = input("\nWARNING: This is irreversible. Are you sure you want to proceed? (yes/no): ")
    if confirmation.lower() != "yes":
        print("Operation cancelled.")
        return
    
    # Second confirmation
    second_confirmation = input("Type 'CONFIRM' to proceed with database cleaning: ")
    if second_confirmation != "CONFIRM":
        print("Operation cancelled.")
        return
    
    # Clean both databases
    total_deleted = 0
    
    # Clean sunmax.db
    if os.path.exists(SUNMAX_DB_PATH):
        total_deleted += clean_database(SUNMAX_DB_PATH, "sunmax.db")
    else:
        print(f"\nDatabase file not found: {SUNMAX_DB_PATH}")
    
    # Clean app.db
    if os.path.exists(APP_DB_PATH):
        total_deleted += clean_database(APP_DB_PATH, "app.db")
    else:
        print(f"\nDatabase file not found: {APP_DB_PATH}")
    
    print(f"\nDatabase cleaning completed. Total rows deleted across all databases: {total_deleted}")
    print("The database structures have been preserved.")
    print("\nIMPORTANT: Restart your application to ensure changes take effect.")

if __name__ == "__main__":
    main()
