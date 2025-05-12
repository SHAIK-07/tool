#!/usr/bin/env python3
"""
Ensure Admin User Script

This script ensures that the top user account (contactsunmax@gmail.com) always exists in the database.
It's designed to be called during container startup to guarantee the top user is always available.
"""

import os
import sys
import sqlite3
from passlib.context import CryptContext

# Top user credentials - DO NOT CHANGE
TOP_USER_EMAIL = "contactsunmax@gmail.com"
TOP_USER_PASSWORD = "Sunmax@123"
TOP_USER_NAME = "Sunmax Administrator"
TOP_USER_ROLE = "top_user"

# Database path
DB_FOLDER = "db"
DB_PATH = os.path.join(DB_FOLDER, "sunmax.db")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    """Generate a password hash."""
    return pwd_context.hash(password)

def ensure_top_user_exists():
    """Check if the top user exists, and create it if it doesn't."""
    try:
        # Ensure database directory exists
        os.makedirs(DB_FOLDER, exist_ok=True)
        
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
        
        # Check if top user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (TOP_USER_EMAIL,))
        if cursor.fetchone():
            print(f"Top user account already exists: {TOP_USER_EMAIL}")
        else:
            # Create top user
            print(f"Creating top user account: {TOP_USER_EMAIL}")
            
            # Generate password hash
            hashed_password = get_password_hash(TOP_USER_PASSWORD)
            
            # Insert top user
            cursor.execute("""
            INSERT INTO users (email, password, name, role, first_login)
            VALUES (?, ?, ?, ?, ?)
            """, (TOP_USER_EMAIL, hashed_password, TOP_USER_NAME, TOP_USER_ROLE, 0))
            
            print(f"Top user account created successfully")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error ensuring top user exists: {e}")
        return False

if __name__ == "__main__":
    if ensure_top_user_exists():
        print("Top user check completed successfully")
        sys.exit(0)
    else:
        print("Failed to ensure top user exists")
        sys.exit(1)
