#!/usr/bin/env python3
"""
Database Inspector Script

This script examines SQLite database files and provides information about:
- Tables in each database
- Schema (column structure) for each table
- Sample data from each table

Usage:
    python db_inspector.py

The script will examine both app.db and db/sunmax.db by default.
"""

import os
import sqlite3
import sys

# Define database paths
DB_FILES = {
    "app.db": "app.db",
    "sunmax.db": os.path.join("db", "sunmax.db")
}

def check_db_exists(db_path):
    """Check if the database file exists."""
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    return True

def get_db_size(db_path):
    """Get the size of the database file in KB."""
    return os.path.getsize(db_path) / 1024

def get_tables(conn):
    """Get a list of all tables in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    return [table[0] for table in tables]

def get_table_schema(conn, table_name):
    """Get the schema (column structure) for a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return columns

def get_table_row_count(conn, table_name):
    """Get the number of rows in a table."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    return count

def get_sample_data(conn, table_name, limit=5):
    """Get a sample of data from a table."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()

        # Get column names
        column_names = [description[0] for description in cursor.description]

        return column_names, rows
    except sqlite3.Error as e:
        print(f"Error getting sample data from {table_name}: {e}")
        return [], []

def print_table(data, headers=None, column_widths=None):
    """Print data in a table format without using the tabulate package."""
    if not data:
        return

    # Determine column widths if not provided
    if not column_widths:
        if headers:
            # Initialize with header widths
            column_widths = [len(str(h)) for h in headers]
        else:
            # Initialize with zeros
            column_widths = [0] * len(data[0])

        # Find the maximum width needed for each column
        for row in data:
            for i, cell in enumerate(row):
                column_widths[i] = max(column_widths[i], len(str(cell)))

    # Print headers if provided
    if headers:
        header_row = " | ".join(str(h).ljust(column_widths[i]) for i, h in enumerate(headers))
        print(header_row)
        print("-" * len(header_row))

    # Print data rows
    for row in data:
        print(" | ".join(str(cell).ljust(column_widths[i]) for i, cell in enumerate(row)))

def inspect_database(db_path, db_name):
    """Inspect a database and print information about it."""
    if not check_db_exists(db_path):
        return

    print(f"\n{'=' * 80}")
    print(f"DATABASE: {db_name} ({db_path})")
    print(f"Size: {get_db_size(db_path):.2f} KB")
    print(f"{'=' * 80}")

    try:
        conn = sqlite3.connect(db_path)
        tables = get_tables(conn)

        if not tables:
            print("No tables found in this database.")
            conn.close()
            return

        print(f"Found {len(tables)} tables:")

        for table_name in tables:
            row_count = get_table_row_count(conn, table_name)
            print(f"\n{'-' * 80}")
            print(f"TABLE: {table_name} ({row_count} rows)")
            print(f"{'-' * 80}")

            # Print schema
            schema = get_table_schema(conn, table_name)
            schema_data = [(col[0], col[1], col[2], "PRIMARY KEY" if col[5] else "", "NOT NULL" if col[3] else "")
                          for col in schema]
            print("\nSchema:")
            print_table(schema_data, headers=["ID", "Name", "Type", "PK", "NN"])

            # Print sample data
            if row_count > 0:
                column_names, rows = get_sample_data(conn, table_name)
                if rows:
                    print(f"\nSample data (up to 5 rows):")
                    print_table(rows, headers=column_names)
            else:
                print("\nNo data in this table.")

        conn.close()

    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")

def main():
    """Main function to inspect all databases."""
    try:
        # Inspect each database
        for db_name, db_path in DB_FILES.items():
            inspect_database(db_path, db_name)

        print("\nDatabase inspection complete.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
