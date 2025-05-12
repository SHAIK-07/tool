#!/usr/bin/env python3
"""
Prepare Database for Deployment Script

This script:
1. Cleans all data from the database tables EXCEPT the top user account
2. Ensures the top user account exists with the correct credentials
3. Verifies the database is properly prepared for deployment

Usage:
    python prepare_db_for_deployment.py
"""

import os
import sqlite3
import time
import shutil
import hashlib
import secrets
from datetime import datetime
from passlib.context import CryptContext

# Define database path
DB_FOLDER = "db"
DB_PATH = os.path.join(DB_FOLDER, "sunmax.db")
BACKUP_FOLDER = os.path.join(DB_FOLDER, "backups")

# Top user credentials - DO NOT CHANGE
TOP_USER_EMAIL = "contactsunmax@gmail.com"
TOP_USER_PASSWORD = "Sunmax@123"
TOP_USER_NAME = "Sunmax Administrator"
TOP_USER_ROLE = "top_user"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    """Generate a password hash."""
    return pwd_context.hash(password)

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

def backup_top_user():
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
        cursor.execute("SELECT * FROM users WHERE email = ? LIMIT 1", (TOP_USER_EMAIL,))
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

def clean_table(table_name, preserve_top_user=False):
    """Clean all data from a table, optionally preserving top user account."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get row count before deletion
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Special handling for users table
        if table_name == 'users' and preserve_top_user:
            # Delete all users except the top user
            cursor.execute("DELETE FROM users WHERE email != ?", (TOP_USER_EMAIL,))
            deleted_count = cursor.rowcount
            print(f"  - Preserved top user account, deleted {deleted_count} other users")
        else:
            # Delete all data from the table
            cursor.execute(f"DELETE FROM {table_name}")
            deleted_count = row_count
        
        # Reset auto-increment counters for tables other than users
        if table_name != 'users' or not preserve_top_user:
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

def create_top_user():
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
        cursor.execute("SELECT id FROM users WHERE email = ?", (TOP_USER_EMAIL,))
        if cursor.fetchone():
            print("Top user account already exists. Updating it...")
            
            # Update top user with fresh password and role
            hashed_password = get_password_hash(TOP_USER_PASSWORD)
            cursor.execute("""
            UPDATE users SET 
                password = ?, 
                name = ?, 
                role = ?, 
                first_login = 0
            WHERE email = ?
            """, (hashed_password, TOP_USER_NAME, TOP_USER_ROLE, TOP_USER_EMAIL))
        else:
            # Create top user
            print("Creating top user account...")
            
            # Generate password hash
            hashed_password = get_password_hash(TOP_USER_PASSWORD)
            
            # Insert top user
            cursor.execute("""
            INSERT INTO users (email, password, name, role, first_login)
            VALUES (?, ?, ?, ?, ?)
            """, (TOP_USER_EMAIL, hashed_password, TOP_USER_NAME, TOP_USER_ROLE, 0))
        
        # Commit changes
        conn.commit()
        
        # Close connection
        conn.close()
        
        print(f"\nTop user account ready:")
        print(f"  Email: {TOP_USER_EMAIL}")
        print(f"  Password: {TOP_USER_PASSWORD}")
        print(f"  Role: {TOP_USER_ROLE}")
        
        return True
    except Exception as e:
        print(f"Error creating/updating top user account: {e}")
        return False

def verify_top_user():
    """Verify that the top user exists and has the correct role."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if top user exists
        cursor.execute("SELECT id, email, role FROM users WHERE email = ?", (TOP_USER_EMAIL,))
        user = cursor.fetchone()
        
        # Close connection
        conn.close()
        
        if user:
            print(f"\nTop user verification successful:")
            print(f"  ID: {user[0]}")
            print(f"  Email: {user[1]}")
            print(f"  Role: {user[2]}")
            return True
        else:
            print(f"\nTop user verification failed: User not found")
            return False
    except Exception as e:
        print(f"Error verifying top user: {e}")
        return False

def main():
    """Main function to prepare the database for deployment."""
    print("=== PREPARE DATABASE FOR DEPLOYMENT ===")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"Database file not found: {DB_PATH}")
        return
    
    # Stop the application
    stop_application()
    
    # Get all tables
    tables = get_all_tables()
    if not tables:
        print("No tables found in the database.")
        return
    
    # Show tables to be cleaned
    print("\nThe following tables will be cleaned (preserving top user account):")
    for table in tables:
        print(f"  - {table}")
    
    # Ask for confirmation
    confirmation = input("\nWARNING: This will delete ALL data except the top user. Are you sure? (yes/no): ")
    if confirmation.lower() != "yes":
        print("Operation cancelled.")
        return
    
    # Create a backup
    print("\nCreating backup before cleaning...")
    create_backup()
    
    # Backup top user
    top_user = backup_top_user()
    has_top_user = top_user is not None
    
    # Clean each table
    print("\nCleaning tables...")
    total_rows_deleted = 0
    for table in tables:
        # Preserve top user in users table
        preserve_top_user = (table == 'users' and has_top_user)
        rows_deleted = clean_table(table, preserve_top_user)
        total_rows_deleted += rows_deleted
        print(f"  - {table}: {rows_deleted} rows deleted")
    
    # Create or update top user
    print("\nEnsuring top user account exists...")
    create_top_user()
    
    # Verify top user
    print("\nVerifying top user account...")
    if verify_top_user():
        print("\nDatabase preparation completed successfully.")
        print("The database is now ready for deployment with only the top user account.")
    else:
        print("\nWARNING: Top user verification failed.")
        print("Please check the database manually before deployment.")
    
    print(f"\nTotal rows deleted: {total_rows_deleted}")
    print("\nTop user account credentials:")
    print(f"  Email: {TOP_USER_EMAIL}")
    print(f"  Password: {TOP_USER_PASSWORD}")
    print(f"  Role: {TOP_USER_ROLE}")

if __name__ == "__main__":
    main()
