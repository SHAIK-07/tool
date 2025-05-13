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
import math
import shutil
import tempfile
import zipfile
from datetime import datetime
from typing import Dict
from jose import JWTError, jwt

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form, Path
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.core.auth import SECRET_KEY, ALGORITHM

# Create a router
router = APIRouter(tags=["Database Management"])

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

def get_folder_info() -> Dict:
    """Get information about document storage folders."""
    # Define folders to check
    folders_to_check = [
        {"name": "customers", "description": "Customer PDF documents"},
        {"name": "invoices", "description": "Invoice PDF documents"},
        {"name": "quotations", "description": "Quotation PDF documents"},
        {"name": "exports", "description": "Exported Excel files"},
        {"name": "services", "description": "Service PDF documents"}
    ]

    total_file_count = 0
    total_size_bytes = 0
    folder_info = []

    for folder_data in folders_to_check:
        folder_name = folder_data["name"]
        folder_path = folder_name  # Assuming folders are in the root directory

        # Initialize folder stats
        stats = {
            "name": folder_name,
            "description": folder_data["description"],
            "file_count": 0,
            "total_size": "0 KB",
            "last_modified": "Never",
            "size_bytes": 0
        }

        # Check if folder exists
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            files = []
            last_modified_timestamp = 0

            # Walk through the folder and all subfolders
            for root, _, filenames in os.walk(folder_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)

                    # Skip hidden files and temporary files
                    if filename.startswith('.') or filename.endswith('~'):
                        continue

                    try:
                        # Get file stats
                        file_stats = os.stat(file_path)
                        file_size = file_stats.st_size
                        file_modified = file_stats.st_mtime

                        # Update folder stats
                        stats["file_count"] += 1
                        stats["size_bytes"] += file_size

                        # Track the most recently modified file
                        if file_modified > last_modified_timestamp:
                            last_modified_timestamp = file_modified
                    except Exception as e:
                        print(f"Error getting stats for {file_path}: {e}")

            # Format the total size
            stats["total_size"] = format_file_size(stats["size_bytes"])

            # Format the last modified date if files were found
            if last_modified_timestamp > 0:
                stats["last_modified"] = datetime.fromtimestamp(last_modified_timestamp).strftime("%Y-%m-%d %H:%M:%S")

            # Update totals
            total_file_count += stats["file_count"]
            total_size_bytes += stats["size_bytes"]

        folder_info.append(stats)

    return {
        "folders": folder_info,
        "total_file_count": total_file_count,
        "total_storage_size": format_file_size(total_size_bytes)
    }

def format_file_size(size_bytes):
    """Format file size from bytes to human-readable format."""
    if size_bytes == 0:
        return "0 B"

    size_names = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)

    return f"{s} {size_names[i]}"

# Cloud info function removed as we're not using cloud storage

@router.get("/database-management", response_class=HTMLResponse)
async def database_management(request: Request, db: Session = Depends(get_db)):
    """Database management page."""
    # Get current user from cookie
    current_user = await get_current_user_from_cookie(request, db)

    # Redirect to login if not authenticated
    if not current_user:
        return RedirectResponse(url="/login?next=/database-management", status_code=303)

    # Check if user is top_user
    if current_user.role != "top_user":
        return RedirectResponse(url="/", status_code=303)

    # Get database information
    db_info = get_db_info()

    # Get folder information
    folder_info = get_folder_info()

    # Add browse links to folder info
    for folder in folder_info["folders"]:
        folder["browse_link"] = f"/browse-folder/{folder['name']}"

    return templates.TemplateResponse(
        "database_management.html",
        {
            "request": request,
            "user": current_user,  # Pass the current user to the template
            "db_size": db_info["db_size"],
            "last_modified": db_info["last_modified"],
            "table_count": db_info["table_count"],
            "table_data": db_info["table_data"],
            "storage_folders": folder_info["folders"],
            "total_storage_size": folder_info["total_storage_size"],
            "total_file_count": folder_info["total_file_count"]
        }
    )

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
        return RedirectResponse(url="/login?next=/database-management", status_code=303)

    try:
        # Save uploaded file to local filesystem
        content = await database_file.read()
        with open(DB_PATH, "wb") as db_file:
            db_file.write(content)

        print(f"Database uploaded successfully to {DB_PATH}")
        return RedirectResponse(url="/database-management", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading database: {str(e)}")

# Remove the sync-database and backup-database endpoints as we're not using Cloud Storage anymore

@router.get("/browse-folder/{folder_name}")
async def browse_folder(
    request: Request,
    folder_name: str,
    db: Session = Depends(get_db)
):
    """Browse files in a specific folder."""
    # Get current user from cookie
    current_user = await get_current_user_from_cookie(request, db)

    # Redirect to login if not authenticated
    if not current_user:
        return RedirectResponse(url="/login?next=/browse-folder/" + folder_name, status_code=303)

    # Check if user is top_user
    if current_user.role != "top_user":
        return RedirectResponse(url="/", status_code=303)

    # Validate folder name to prevent directory traversal attacks
    valid_folders = ["customers", "invoices", "quotations", "exports", "services"]
    if folder_name not in valid_folders:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_path = folder_name  # Assuming folders are in the root directory

    # Check if folder exists
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        os.makedirs(folder_path, exist_ok=True)

    # Get all files in the folder and subfolders
    files = []
    for root, _, filenames in os.walk(folder_path):
        for filename in filenames:
            # Skip hidden files and temporary files
            if filename.startswith('.') or filename.endswith('~'):
                continue

            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, folder_path)

            try:
                # Get file stats
                file_stats = os.stat(file_path)

                # Get file extension
                _, ext = os.path.splitext(filename)
                ext = ext.lower()[1:] if ext else ""

                files.append({
                    "name": filename,
                    "path": relative_path,
                    "size": format_file_size(file_stats.st_size),
                    "size_bytes": file_stats.st_size,
                    "modified": datetime.fromtimestamp(file_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "modified_timestamp": file_stats.st_mtime,
                    "type": ext.upper() if ext else "Unknown"
                })
            except Exception as e:
                print(f"Error getting stats for {file_path}: {e}")

    # Sort files by modified date (newest first)
    files.sort(key=lambda x: x["modified_timestamp"], reverse=True)

    return templates.TemplateResponse(
        "folder_browser.html",
        {
            "request": request,
            "user": current_user,  # Pass the current user to the template
            "folder_name": folder_name,
            "files": files,
            "file_count": len(files)
        }
    )

@router.get("/download-folder/{folder_name}")
async def download_folder(
    request: Request,
    folder_name: str,
    db: Session = Depends(get_db)
):
    """Download all files in a folder as a ZIP archive."""
    # Get current user from cookie
    current_user = await get_current_user_from_cookie(request, db)

    # Check if user is authenticated and has top_user role
    if not current_user or current_user.role != "top_user":
        return RedirectResponse(url="/login", status_code=303)

    # Validate folder name to prevent directory traversal attacks
    valid_folders = ["customers", "invoices", "quotations", "exports", "services"]
    if folder_name not in valid_folders:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_path = folder_name  # Assuming folders are in the root directory

    # Check if folder exists
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        raise HTTPException(status_code=404, detail="Folder not found")

    # Create a temporary file for the ZIP archive
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
        temp_path = temp_file.name

    try:
        # Create a ZIP archive
        with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the folder and add all files
            for root, _, files in os.walk(folder_path):
                for file in files:
                    # Skip hidden files and temporary files
                    if file.startswith('.') or file.endswith('~'):
                        continue

                    file_path = os.path.join(root, file)
                    # Add file to ZIP with relative path
                    zipf.write(file_path, os.path.relpath(file_path, folder_path))

        # Return the ZIP file
        return FileResponse(
            path=temp_path,
            filename=f"{folder_name}_files.zip",
            media_type="application/zip",
            background=shutil.rmtree(temp_path, ignore_errors=True)
        )
    except Exception as e:
        # Clean up the temporary file in case of error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"Error creating ZIP archive: {str(e)}")

@router.get("/view-file/{folder_name}/{file_path:path}")
async def view_file(
    request: Request,
    folder_name: str,
    file_path: str,
    db: Session = Depends(get_db)
):
    """View a file from a folder."""
    # Get current user from cookie
    current_user = await get_current_user_from_cookie(request, db)

    # Check if user is authenticated and has top_user role
    if not current_user or current_user.role != "top_user":
        return RedirectResponse(url="/login", status_code=303)

    # Validate folder name to prevent directory traversal attacks
    valid_folders = ["customers", "invoices", "quotations", "exports", "services"]
    if folder_name not in valid_folders:
        raise HTTPException(status_code=404, detail="Folder not found")

    # Construct the full file path
    full_path = os.path.join(folder_name, file_path)

    # Check if file exists
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    # Set content type based on file extension
    content_type = "application/octet-stream"  # Default
    if ext == ".pdf":
        content_type = "application/pdf"
    elif ext in [".xlsx", ".xls"]:
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    # Return the file for viewing
    return FileResponse(
        path=full_path,
        media_type=content_type,
        filename=os.path.basename(file_path)
    )

@router.get("/download-file/{folder_name}/{file_path:path}")
async def download_file(
    request: Request,
    folder_name: str,
    file_path: str,
    db: Session = Depends(get_db)
):
    """Download a file from a folder."""
    # Get current user from cookie
    current_user = await get_current_user_from_cookie(request, db)

    # Check if user is authenticated and has top_user role
    if not current_user or current_user.role != "top_user":
        return RedirectResponse(url="/login", status_code=303)

    # Validate folder name to prevent directory traversal attacks
    valid_folders = ["customers", "invoices", "quotations", "exports", "services"]
    if folder_name not in valid_folders:
        raise HTTPException(status_code=404, detail="Folder not found")

    # Construct the full file path
    full_path = os.path.join(folder_name, file_path)

    # Check if file exists
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Return the file for download
    return FileResponse(
        path=full_path,
        filename=os.path.basename(file_path),
        media_type="application/octet-stream"
    )

@router.delete("/delete-all-files/{folder_name}")
async def delete_all_files(
    request: Request,
    folder_name: str,
    db: Session = Depends(get_db)
):
    """Delete all files in a folder."""
    # Get current user from cookie
    current_user = await get_current_user_from_cookie(request, db)

    # Check if user is authenticated and has top_user role
    if not current_user or current_user.role != "top_user":
        raise HTTPException(status_code=403, detail="Not authorized")

    # Validate folder name to prevent directory traversal attacks
    valid_folders = ["customers", "invoices", "quotations", "exports", "services"]
    if folder_name not in valid_folders:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_path = folder_name  # Assuming folders are in the root directory

    # Check if folder exists
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        raise HTTPException(status_code=404, detail="Folder not found")

    try:
        # Count files before deletion
        file_count = 0
        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                # Skip hidden files and temporary files
                if filename.startswith('.') or filename.endswith('~'):
                    continue
                file_count += 1

        # Delete all files in the folder
        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                # Skip hidden files and temporary files
                if filename.startswith('.') or filename.endswith('~'):
                    continue

                file_path = os.path.join(root, filename)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

        return {"success": True, "message": f"Successfully deleted {file_count} files from {folder_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting files: {str(e)}")

@router.delete("/clear-table/{table_name}")
async def clear_table(
    request: Request,
    table_name: str,
    db: Session = Depends(get_db)
):
    """Clear all records from a table, preserving top user in users table."""
    # Get current user from cookie
    current_user = await get_current_user_from_cookie(request, db)

    # Check if user is authenticated and has top_user role
    if not current_user or current_user.role != "top_user":
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get row count before deletion
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]

        # Special handling for users table
        if table_name == 'users':
            # Delete all users except the top user
            cursor.execute("DELETE FROM users WHERE role != 'top_user'")
            deleted_count = cursor.rowcount
        else:
            # Delete all data from the table
            cursor.execute(f"DELETE FROM {table_name}")
            deleted_count = row_count

        # Reset auto-increment counters for tables other than users
        if table_name != 'users':
            try:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
            except:
                pass

        # Commit changes
        conn.commit()

        # Close connection
        conn.close()

        return {"success": True, "message": f"Successfully deleted {deleted_count} records from {table_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing table: {str(e)}")

@router.delete("/delete-file/{folder_name}/{file_path:path}")
async def delete_file(
    request: Request,
    folder_name: str,
    file_path: str,
    db: Session = Depends(get_db)
):
    """Delete a file from a folder."""
    # Get current user from cookie
    current_user = await get_current_user_from_cookie(request, db)

    # Check if user is authenticated and has top_user role
    if not current_user or current_user.role != "top_user":
        raise HTTPException(status_code=403, detail="Not authorized")

    # Validate folder name to prevent directory traversal attacks
    valid_folders = ["customers", "invoices", "quotations", "exports", "services"]
    if folder_name not in valid_folders:
        raise HTTPException(status_code=404, detail="Folder not found")

    # Construct the full file path
    full_path = os.path.join(folder_name, file_path)

    # Check if file exists
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Delete the file
        os.remove(full_path)
        return {"success": True, "message": f"File {file_path} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")





