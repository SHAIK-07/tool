"""
Database Management API for Sunmax Application

This module provides endpoints for database management operations:
- View database information
- Download the current database
- Upload a database
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict
from jose import JWTError, jwt

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.core.auth import SECRET_KEY, ALGORITHM

# Create a router
router = APIRouter()

# Set up templates
templates = Jinja2Templates(directory="templates")

# Helper function to get current user from cookie
async def get_current_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db)
):
    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]

        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None

        # Get the user from database
        user = crud.get_user_by_email(db, email)
        return user
    except JWTError:
        return None
    except Exception as e:
        print(f"Error getting user from cookie: {e}")
        return None

# Constants
DB_FOLDER = "db"  # Database folder
DB_PATH = os.path.join(DB_FOLDER, "sunmax.db")  # Local database path

# Ensure the database folder exists
os.makedirs(DB_FOLDER, exist_ok=True)

def get_db_info() -> Dict:
    """Get information about the local database."""
    result = {
        "db_size": "Not found",
        "last_modified": "Not found",
        "table_count": 0,
        "table_data": {}
    }

    if not os.path.exists(DB_PATH):
        return result

    # Get file size and last modified time
    file_stats = os.stat(DB_PATH)
    result["db_size"] = f"{file_stats.st_size / 1024:.2f} KB"
    result["last_modified"] = datetime.fromtimestamp(file_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    # Get table information
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        result["table_count"] = len(table_names)

        # Get row counts for each table
        for table in table_names:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            result["table_data"][table] = count

        conn.close()
    except Exception as e:
        print(f"Error getting database info: {e}")

    return result

# Cloud info function removed as we're not using cloud storage

@router.get("/database-management")
async def database_management(request: Request, db: Session = Depends(get_db)):
    """
    Database management page.
    This endpoint is protected and only accessible to top_user.
    """
    # Get current user from cookie
    current_user = await get_current_user_from_cookie(request, db)

    # Redirect to login if not authenticated
    if not current_user:
        return RedirectResponse(url="/login?next=/api/database-management", status_code=303)

    # Check if the user is a top_user (only top_user can access this page)
    if current_user.role != "top_user":
        return RedirectResponse(url="/", status_code=303)

    # Get database information
    db_info = get_db_info()

    # Create context
    context = {
        "request": request,
        "user": current_user,  # Use "user" instead of "current_user" to match base.html
        **db_info
    }

    return templates.TemplateResponse("database_management.html", context)

@router.get("/download-database")
async def download_database(request: Request, db: Session = Depends(get_db)):
    """
    Download the current database file.
    This endpoint is protected and only accessible to admin users.
    """
    # Get current user from cookie
    current_user = await get_current_user_from_cookie(request, db)

    # Redirect to login if not authenticated
    if not current_user:
        return RedirectResponse(url="/login?next=/api/download-database", status_code=303)

    # Check if the user is a top_user
    if current_user.role != "top_user":
        return RedirectResponse(url="/", status_code=303)

    # Check if the file exists
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Database file not found")

    # Return the file as a download
    return FileResponse(
        path=DB_PATH,
        filename="sunmax.db",
        media_type="application/octet-stream"
    )

# Remove the download-cloud-database endpoint as we're not using Cloud Storage anymore

@router.post("/upload-database")
async def upload_database(
    request: Request,
    database_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a database file and save locally."""
    # Authentication checks...
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user or current_user.role != "top_user":
        return RedirectResponse(url="/login?next=/api/database-management", status_code=303)

    try:
        # Save uploaded file to local filesystem
        content = await database_file.read()
        with open(DB_PATH, "wb") as db_file:
            db_file.write(content)

        print(f"Database uploaded successfully to {DB_PATH}")
        return RedirectResponse(url="/api/database-management", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading database: {str(e)}")

# Remove the sync-database and backup-database endpoints as we're not using Cloud Storage anymore

