#!/usr/bin/env python3
"""
Database Cleaning Script

This script cleans all data from the database tables while preserving the table structure.
Use this before deployment to ensure a clean database without test data.

Usage:
    python clean_database.py

The script will ask for confirmation before deleting any data.
"""

import os
import sqlite3
import sys
from datetime import datetime

# Define database paths
DB_FOLDER = "db"
DB_PATH = os.path.join(DB_FOLDER, "sunmax.db")
BACKUP_FOLDER = os.path.join(DB_FOLDER, "backups")

def create_backup():
    """Create a backup of the database before cleaning."""
    try:
        # Ensure backup directory exists
        os.makedirs(BACKUP_FOLDER, exist_ok=True)
        
        # Create a timestamp for the backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_FOLDER, f"sunmax_backup_{timestamp}.db")
        
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        
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

def get_all_tables():
    """Get a list of all tables in the database."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [table[0] for table in cursor.fetchall()]
        
        # Close connection
        conn.close()
        
        return tables
    except Exception as e:
        print(f"Error getting tables: {e}")
        return []

def clean_table(table_name):
    """Clean all data from a table."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Delete all data from the table
        cursor.execute(f"DELETE FROM {table_name}")
        
        # Reset auto-increment counters
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
        
        # Commit changes
        conn.commit()
        
        # Get number of rows deleted
        rows_deleted = cursor.rowcount
        
        # Close connection
        conn.close()
        
        return rows_deleted
    except Exception as e:
        print(f"Error cleaning table {table_name}: {e}")
        return 0

def main():
    """Main function to clean the database."""
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"Database file not found: {DB_PATH}")
        return
    
    # Get all tables
    tables = get_all_tables()
    if not tables:
        print("No tables found in the database.")
        return
    
    # Show tables to be cleaned
    print("\nThe following tables will be cleaned:")
    for table in tables:
        print(f"  - {table}")
    
    # Ask for confirmation
    confirmation = input("\nWARNING: This will delete ALL data from these tables. Are you sure? (yes/no): ")
    if confirmation.lower() != "yes":
        print("Operation cancelled.")
        return
    
    # Create a backup
    print("\nCreating backup before cleaning...")
    if not create_backup():
        second_confirmation = input("Backup failed. Continue anyway? (yes/no): ")
        if second_confirmation.lower() != "yes":
            print("Operation cancelled.")
            return
    
    # Clean each table
    print("\nCleaning tables...")
    total_rows_deleted = 0
    for table in tables:
        rows_deleted = clean_table(table)
        total_rows_deleted += rows_deleted
        print(f"  - {table}: {rows_deleted} rows deleted")
    
    print(f"\nDatabase cleaning completed. Total rows deleted: {total_rows_deleted}")
    print("The database structure has been preserved.")

if __name__ == "__main__":
    main()
