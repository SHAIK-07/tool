"""
Ensure Top User Script

This script ensures that the top user account (contactsunmax@gmail.com) always exists in the database.
It's designed to be called during application startup to guarantee the top user is always available.
"""

from sqlalchemy.orm import Session
from app.db import models, crud
from app.core.auth import get_password_hash

# Top user credentials - DO NOT CHANGE
TOP_USER_EMAIL = "contactsunmax@gmail.com"
TOP_USER_PASSWORD = "Sunmax@123"
TOP_USER_NAME = "Sunmax Administrator"
TOP_USER_ROLE = "top_user"

def ensure_top_user_exists(db: Session) -> bool:
    """
    Check if the top user exists, and create it if it doesn't.
    
    Args:
        db: Database session
        
    Returns:
        bool: True if the top user exists or was created, False if there was an error
    """
    try:
        # Check if top user exists
        top_user = crud.get_user_by_email(db, TOP_USER_EMAIL)
        
        if top_user:
            # Top user exists, nothing to do
            return True
        
        # Top user doesn't exist, create it
        print(f"Creating top user account: {TOP_USER_EMAIL}")
        
        # Create user data
        user_data = {
            "email": TOP_USER_EMAIL,
            "password": TOP_USER_PASSWORD,
            "name": TOP_USER_NAME,
            "role": TOP_USER_ROLE,
            "first_login": False  # Don't require password change
        }
        
        # Create the user
        crud.create_user(db, user_data)
        
        print(f"Top user account created successfully")
        return True
    except Exception as e:
        print(f"Error ensuring top user exists: {e}")
        return False
