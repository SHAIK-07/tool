#!/usr/bin/env python3
"""
Clean Database for Deployment Script

This script:
1. Attempts to stop any running instances of the application
2. Cleans the database while preserving or recreating an admin user
3. Verifies the database is properly cleaned

Usage:
    python clean_for_deployment.py
"""

import os
import sqlite3
import time
import shutil
import hashlib
import secrets
from datetime import datetime

# Define database path
DB_FOLDER = "db"
DB_PATH = os.path.join(DB_FOLDER, "sunmax.db")
BACKUP_FOLDER = os.path.join(DB_FOLDER, "backups")

# Default admin credentials - using the top user account
DEFAULT_ADMIN_USERNAME = "contactsunmax@gmail.com"
DEFAULT_ADMIN_PASSWORD = "Sunmax@123"

def stop_application():
    """Attempt to stop any running instances of the application."""
    print("Attempting to stop any running application instances...")

    try:
        # Ask user to manually close the application
        input("Please close any running instances of the application and press Enter to continue...")

        # Wait a moment for processes to fully terminate
        time.sleep(2)

        return True
    except Exception as e:
        print(f"Error stopping application: {e}")
        print("Please manually stop any running instances of the application.")
        input("Press Enter to continue...")
        return True

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

def backup_admin_user():
    """Backup the top user account if it exists."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("Users table not found. No top user account to backup.")
            conn.close()
            return None

        # Get top user
        cursor.execute("SELECT * FROM users WHERE email = ? LIMIT 1", (DEFAULT_ADMIN_USERNAME,))
        top_user = cursor.fetchone()

        # Close connection
        conn.close()

        if top_user:
            print(f"Found top user account: {top_user[1]}")
            return top_user
        else:
            print("No top user account found.")
            return None
    except Exception as e:
        print(f"Error backing up top user account: {e}")
        return None

def clean_table(table_name, preserve_admin=False):
    """Clean all data from a table, optionally preserving top user account."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get row count before deletion
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]

        # Special handling for users table
        if table_name == 'users' and preserve_admin:
            # Delete all users except the top user
            cursor.execute("DELETE FROM users WHERE email != ?", (DEFAULT_ADMIN_USERNAME,))
            deleted_count = cursor.rowcount
            print(f"  - Preserved top user account, deleted {deleted_count} other users")
        else:
            # Delete all data from the table
            cursor.execute(f"DELETE FROM {table_name}")
            deleted_count = row_count

        # Reset auto-increment counters for tables other than users
        if table_name != 'users' or not preserve_admin:
            try:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
            except:
                pass

        # Commit changes
        conn.commit()

        # Close connection
        conn.close()

        return deleted_count
    except Exception as e:
        print(f"Error cleaning table {table_name}: {e}")
        return 0

def create_admin_user():
    """Create the top user account in the database."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("Users table not found. Creating it...")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                phone TEXT,
                role TEXT NOT NULL DEFAULT 'employee',
                first_login BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
            """)

        # Check if top user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (DEFAULT_ADMIN_USERNAME,))
        if cursor.fetchone():
            print("Top user account already exists. Skipping creation.")
            conn.close()
            return True

        # Generate password hash using passlib's bcrypt
        try:
            # Try to import passlib for proper password hashing
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed_password = pwd_context.hash(DEFAULT_ADMIN_PASSWORD)
        except ImportError:
            # Try to use bcrypt directly if passlib is not available
            try:
                import bcrypt
                hashed_password = bcrypt.hashpw(DEFAULT_ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
            except ImportError:
                # Fallback to simple hashing if neither is available
                print("Warning: bcrypt not available, using simple hashing")
                salt = secrets.token_hex(8)
                hashed_password = hashlib.sha256(f"{DEFAULT_ADMIN_PASSWORD}{salt}".encode()).hexdigest()
                hashed_password = f"{salt}${hashed_password}"

        # Insert top user with role 'top_user'
        cursor.execute("""
        INSERT INTO users (email, password, name, role, first_login)
        VALUES (?, ?, ?, ?, ?)
        """, (DEFAULT_ADMIN_USERNAME, hashed_password, "Sunmax Administrator", "top_user", 0))

        # Commit changes
        conn.commit()

        # Close connection
        conn.close()

        print(f"\nTop user account created:")
        print(f"  Email: {DEFAULT_ADMIN_USERNAME}")
        print(f"  Password: {DEFAULT_ADMIN_PASSWORD}")
        print(f"  Role: top_user")

        return True
    except Exception as e:
        print(f"Error creating top user account: {e}")
        return False

def verify_table_empty(table_name, check_admin=False):
    """Verify that a table is empty (or has only top user for users table)."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if table_name == 'users' and check_admin:
            # For users table, check that only top user exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE email != ?", (DEFAULT_ADMIN_USERNAME,))
            row_count = cursor.fetchone()[0]

            # Check that top user exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", (DEFAULT_ADMIN_USERNAME,))
            admin_count = cursor.fetchone()[0]

            conn.close()
            return row_count == 0 and admin_count > 0
        else:
            # For other tables, check they're completely empty
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            conn.close()
            return row_count == 0
    except Exception as e:
        print(f"Error verifying table {table_name}: {e}")
        return False

def main():
    """Main function to clean the database for deployment."""
    print("=== CLEAN DATABASE FOR DEPLOYMENT ===")

    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"Database file not found: {DB_PATH}")
        return

    # Stop the application
    if not stop_application():
        print("Failed to stop the application. Database cleaning may not work correctly.")
        confirmation = input("Continue anyway? (yes/no): ")
        if confirmation.lower() != "yes":
            print("Operation cancelled.")
            return

    # Get all tables
    tables = get_all_tables()
    if not tables:
        print("No tables found in the database.")
        return

    # Show tables to be cleaned
    print("\nThe following tables will be cleaned (preserving admin user):")
    for table in tables:
        print(f"  - {table}")

    # Ask for confirmation
    confirmation = input("\nWARNING: This will delete ALL data except the admin user. Are you sure? (yes/no): ")
    if confirmation.lower() != "yes":
        print("Operation cancelled.")
        return

    # Create a backup
    print("\nCreating backup before cleaning...")
    create_backup()

    # Backup admin user
    admin_user = backup_admin_user()
    has_admin = admin_user is not None

    # Clean each table
    print("\nCleaning tables...")
    total_rows_deleted = 0
    for table in tables:
        # Preserve admin user in users table
        preserve_admin = (table == 'users' and has_admin)
        rows_deleted = clean_table(table, preserve_admin)
        total_rows_deleted += rows_deleted
        print(f"  - {table}: {rows_deleted} rows deleted")

    # Create admin user if it doesn't exist
    if not has_admin:
        print("\nCreating admin user...")
        create_admin_user()

    # Verify tables are empty (except for admin user in users table)
    print("\nVerifying tables are clean...")
    all_clean = True
    for table in tables:
        check_admin = (table == 'users')
        is_clean = verify_table_empty(table, check_admin)

        if table == 'users':
            status = "CLEAN (admin only)" if is_clean else "NOT CLEAN"
        else:
            status = "EMPTY" if is_clean else "NOT EMPTY"

        print(f"  - {table}: {status}")
        if not is_clean:
            all_clean = False

    if all_clean:
        print("\nDatabase cleaning completed successfully.")
        print("All tables are empty except for the top user account in the users table.")
    else:
        print("\nWARNING: Some tables may not be completely clean.")
        print("You may need to manually clean these tables or try again.")

    print(f"\nTotal rows deleted: {total_rows_deleted}")
    print("\nTop user account credentials:")
    print(f"  Email: {DEFAULT_ADMIN_USERNAME}")
    print(f"  Password: {DEFAULT_ADMIN_PASSWORD}")
    print("  Role: top_user")

if __name__ == "__main__":
    main()
