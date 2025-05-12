#!/usr/bin/env python3
"""
Migration Script: Move enquiries table from app.db to sunmax.db

This script will:
1. Check if the enquiries table exists in both databases
2. Compare the schema of both tables
3. Copy any data from app.db to sunmax.db
4. Verify the migration was successful

Usage:
    python migrate_enquiries.py
"""

import os
import sqlite3
import sys

# Define database paths
APP_DB_PATH = "app.db"
SUNMAX_DB_PATH = os.path.join("db", "sunmax.db")

def check_db_exists(db_path):
    """Check if the database file exists."""
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    return True

def get_table_schema(conn, table_name):
    """Get the schema (column structure) for a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return columns

def table_exists(conn, table_name):
    """Check if a table exists in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def get_table_data(conn, table_name):
    """Get all data from a table."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    return cursor.fetchall()

def get_column_names(conn, table_name):
    """Get column names for a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return [col[1] for col in columns]

def create_table_from_schema(conn, table_name, schema):
    """Create a table based on schema from another database."""
    cursor = conn.cursor()
    
    # Generate CREATE TABLE statement
    columns = []
    for col in schema:
        col_id, col_name, col_type, not_null, default_val, is_pk = col
        column_def = f"{col_name} {col_type}"
        
        if is_pk:
            column_def += " PRIMARY KEY"
        if not_null:
            column_def += " NOT NULL"
        if default_val is not None:
            column_def += f" DEFAULT {default_val}"
            
        columns.append(column_def)
    
    create_stmt = f"CREATE TABLE {table_name} (\n    " + ",\n    ".join(columns) + "\n)"
    print(f"Creating table with statement:\n{create_stmt}")
    
    cursor.execute(create_stmt)
    conn.commit()

def migrate_data(source_conn, dest_conn, table_name):
    """Migrate data from source to destination database."""
    # Get data from source
    data = get_table_data(source_conn, table_name)
    if not data:
        print(f"No data found in {table_name} table in source database.")
        return 0
    
    # Get column names
    source_columns = get_column_names(source_conn, table_name)
    dest_columns = get_column_names(dest_conn, table_name)
    
    # Find common columns
    common_columns = [col for col in source_columns if col in dest_columns]
    if not common_columns:
        print("No common columns found between source and destination tables.")
        return 0
    
    # Generate placeholders for the INSERT statement
    placeholders = ", ".join(["?" for _ in common_columns])
    
    # Generate INSERT statement
    insert_stmt = f"INSERT INTO {table_name} ({', '.join(common_columns)}) VALUES ({placeholders})"
    
    # Insert data
    cursor = dest_conn.cursor()
    rows_inserted = 0
    
    for row in data:
        # Extract values for common columns
        values = [row[source_columns.index(col)] for col in common_columns]
        try:
            cursor.execute(insert_stmt, values)
            rows_inserted += 1
        except sqlite3.Error as e:
            print(f"Error inserting row: {e}")
    
    dest_conn.commit()
    return rows_inserted

def main():
    """Main function to migrate the enquiries table."""
    # Check if both databases exist
    if not check_db_exists(APP_DB_PATH) or not check_db_exists(SUNMAX_DB_PATH):
        print("Migration aborted: One or both database files not found.")
        return
    
    try:
        # Connect to both databases
        app_conn = sqlite3.connect(APP_DB_PATH)
        sunmax_conn = sqlite3.connect(SUNMAX_DB_PATH)
        
        # Check if enquiries table exists in app.db
        if not table_exists(app_conn, "enquiries"):
            print("Migration aborted: enquiries table not found in app.db")
            return
        
        # Get schema from app.db
        app_schema = get_table_schema(app_conn, "enquiries")
        print(f"Found enquiries table in app.db with {len(app_schema)} columns")
        
        # Check if enquiries table exists in sunmax.db
        if table_exists(sunmax_conn, "enquiries"):
            # Compare schemas
            sunmax_schema = get_table_schema(sunmax_conn, "enquiries")
            print(f"Found existing enquiries table in sunmax.db with {len(sunmax_schema)} columns")
            
            # Check if we need to drop and recreate the table
            app_columns = [col[1] for col in app_schema]
            sunmax_columns = [col[1] for col in sunmax_schema]
            
            if set(app_columns) != set(sunmax_columns):
                print("Warning: Schema mismatch between app.db and sunmax.db")
                print(f"app.db columns: {app_columns}")
                print(f"sunmax.db columns: {sunmax_columns}")
                
                response = input("Do you want to drop and recreate the enquiries table in sunmax.db? (y/n): ")
                if response.lower() == 'y':
                    sunmax_conn.execute("DROP TABLE enquiries")
                    create_table_from_schema(sunmax_conn, "enquiries", app_schema)
                    print("Table recreated in sunmax.db")
                else:
                    print("Using existing table structure in sunmax.db")
        else:
            # Create the table in sunmax.db
            create_table_from_schema(sunmax_conn, "enquiries", app_schema)
            print("Created enquiries table in sunmax.db")
        
        # Migrate data
        rows_inserted = migrate_data(app_conn, sunmax_conn, "enquiries")
        print(f"Migrated {rows_inserted} rows from app.db to sunmax.db")
        
        # Close connections
        app_conn.close()
        sunmax_conn.close()
        
        print("\nMigration completed successfully.")
        print("You can now update your code to use sunmax.db and delete app.db")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
