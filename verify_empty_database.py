#!/usr/bin/env python3
"""
Verify Empty Database Script

This script checks if all tables in both database files (app.db and sunmax.db) are empty.
Use this after running the force_clean_database.py script to verify that all data has been removed.

Usage:
    python verify_empty_database.py
"""

import os
import sqlite3
import sys

# Define database paths
DB_FOLDER = "db"
SUNMAX_DB_PATH = os.path.join(DB_FOLDER, "sunmax.db")
APP_DB_PATH = "app.db"  # Root directory app.db

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

def check_table_empty(db_path, table_name):
    """Check if a table is empty."""
    if not os.path.exists(db_path):
        return True
        
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Close connection
        conn.close()
        
        return row_count == 0
    except Exception as e:
        print(f"Error checking table {table_name} in {db_path}: {e}")
        return False

def verify_database(db_path, db_name):
    """Verify all tables in a database are empty."""
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return True
        
    # Get all tables
    tables = get_all_tables(db_path)
    if not tables:
        print(f"No tables found in {db_path}.")
        return True
    
    # Check each table
    print(f"\nVerifying tables in {db_name}:")
    all_empty = True
    for table in tables:
        is_empty = check_table_empty(db_path, table)
        status = "EMPTY" if is_empty else "NOT EMPTY"
        print(f"  - {table}: {status}")
        if not is_empty:
            all_empty = False
    
    return all_empty

def main():
    """Main function to verify both databases are empty."""
    print("=== VERIFY EMPTY DATABASE TOOL ===")
    print("This tool checks if all tables in both app.db and sunmax.db databases are empty.")
    
    all_empty = True
    
    # Verify sunmax.db
    if os.path.exists(SUNMAX_DB_PATH):
        sunmax_empty = verify_database(SUNMAX_DB_PATH, "sunmax.db")
        all_empty = all_empty and sunmax_empty
    else:
        print(f"\nDatabase file not found: {SUNMAX_DB_PATH}")
    
    # Verify app.db
    if os.path.exists(APP_DB_PATH):
        app_empty = verify_database(APP_DB_PATH, "app.db")
        all_empty = all_empty and app_empty
    else:
        print(f"\nDatabase file not found: {APP_DB_PATH}")
    
    if all_empty:
        print("\nVERIFICATION SUCCESSFUL: All tables in all databases are empty.")
    else:
        print("\nVERIFICATION FAILED: Some tables still contain data.")
        print("You may need to run force_clean_database.py again or check for other issues.")

if __name__ == "__main__":
    main()
