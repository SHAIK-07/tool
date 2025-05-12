#!/usr/bin/env python3
"""
Direct Database Cleaning Script

This script uses direct SQL commands to clean the database tables.
It's designed to work even when there are locking issues.

Usage:
    python direct_clean_db.py
"""

import os
import sqlite3
import shutil
from datetime import datetime

# Define database path
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
        
        # Simple file copy
        shutil.copy2(DB_PATH, backup_path)
        
        print(f"Backup created at: {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

def get_table_info():
    """Get information about all tables in the database."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [table[0] for table in cursor.fetchall()]
        
        # Get row counts for each table
        table_info = []
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                table_info.append((table, row_count))
            except:
                table_info.append((table, "Error"))
        
        # Close connection
        conn.close()
        
        return table_info
    except Exception as e:
        print(f"Error getting table info: {e}")
        return []

def clean_database_direct():
    """Clean the database using direct SQL commands."""
    try:
        # Create a new empty database
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_db_path = os.path.join(DB_FOLDER, f"temp_{timestamp}.db")
        
        # Connect to the original database to get schema
        conn_orig = sqlite3.connect(DB_PATH)
        cursor_orig = conn_orig.cursor()
        
        # Get all table creation SQL
        cursor_orig.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        table_schemas = cursor_orig.fetchall()
        
        # Get all index creation SQL
        cursor_orig.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        index_schemas = cursor_orig.fetchall()
        
        # Get all view creation SQL
        cursor_orig.execute("SELECT name, sql FROM sqlite_master WHERE type='view'")
        view_schemas = cursor_orig.fetchall()
        
        # Get all trigger creation SQL
        cursor_orig.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'")
        trigger_schemas = cursor_orig.fetchall()
        
        # Close original connection
        conn_orig.close()
        
        # Create new database with same schema but no data
        conn_new = sqlite3.connect(temp_db_path)
        cursor_new = conn_new.cursor()
        
        # Create tables
        for table_name, table_sql in table_schemas:
            if table_sql:
                cursor_new.execute(table_sql)
                print(f"Created table: {table_name}")
        
        # Create indexes
        for index_name, index_sql in index_schemas:
            if index_sql:
                cursor_new.execute(index_sql)
                print(f"Created index: {index_name}")
        
        # Create views
        for view_name, view_sql in view_schemas:
            if view_sql:
                cursor_new.execute(view_sql)
                print(f"Created view: {view_name}")
        
        # Create triggers
        for trigger_name, trigger_sql in trigger_schemas:
            if trigger_sql:
                cursor_new.execute(trigger_sql)
                print(f"Created trigger: {trigger_name}")
        
        # Commit changes and close connection
        conn_new.commit()
        conn_new.close()
        
        # Backup original database
        create_backup()
        
        # Replace original database with new empty one
        os.remove(DB_PATH)
        shutil.move(temp_db_path, DB_PATH)
        
        print("\nDatabase has been completely reset with the same schema but no data.")
        return True
    except Exception as e:
        print(f"Error during direct database cleaning: {e}")
        return False

def main():
    """Main function to clean the database."""
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"Database file not found: {DB_PATH}")
        return
    
    # Get table info
    table_info = get_table_info()
    if not table_info:
        print("No tables found in the database.")
        return
    
    # Show tables to be cleaned
    print("\nThe following tables will be cleaned:")
    for table, row_count in table_info:
        print(f"  - {table}: {row_count} rows")
    
    # Ask for confirmation
    confirmation = input("\nWARNING: This will delete ALL data from these tables. Are you sure? (yes/no): ")
    if confirmation.lower() != "yes":
        print("Operation cancelled.")
        return
    
    # Clean database directly
    print("\nCleaning database...")
    if clean_database_direct():
        print("\nDatabase cleaning completed successfully.")
    else:
        print("\nDatabase cleaning failed.")
    
    print("\nIMPORTANT: Restart your application to ensure changes take effect.")

if __name__ == "__main__":
    main()
