#!/usr/bin/env python3
"""
Check Top User Script

This script checks if the top user account (contactsunmax@gmail.com) exists in the database.
Use this to verify that the top user is present before performing operations.
"""

import os
import sys
import sqlite3

# Top user email
TOP_USER_EMAIL = "contactsunmax@gmail.com"

# Database path
DB_FOLDER = "db"
DB_PATH = os.path.join(DB_FOLDER, "sunmax.db")

def check_top_user_exists():
    """Check if the top user exists in the database."""
    try:
        # Check if database file exists
        if not os.path.exists(DB_PATH):
            print(f"Database file not found: {DB_PATH}")
            return False
        
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("Users table not found in the database.")
            conn.close()
            return False
        
        # Check if top user exists
        cursor.execute("SELECT id, email, role FROM users WHERE email = ?", (TOP_USER_EMAIL,))
        user = cursor.fetchone()
        
        # Close connection
        conn.close()
        
        if user:
            print(f"Top user account found:")
            print(f"  ID: {user[0]}")
            print(f"  Email: {user[1]}")
            print(f"  Role: {user[2]}")
            return True
        else:
            print(f"Top user account not found: {TOP_USER_EMAIL}")
            return False
    except Exception as e:
        print(f"Error checking top user: {e}")
        return False

if __name__ == "__main__":
    if check_top_user_exists():
        print("Top user check completed successfully")
        sys.exit(0)
    else:
        print("Top user not found in the database")
        sys.exit(1)
