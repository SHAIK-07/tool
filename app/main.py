# app/main.py

from fastapi import FastAPI, Request, Depends, Form, File, UploadFile, Body, Cookie, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import os
import json
import signal
import subprocess
import atexit
import sqlite3
from typing import Optional, Union
import uuid
from jose import JWTError, jwt

# Import for database queries
from sqlalchemy import func, desc
from io import BytesIO

# Import core modules
from app.core.pdf_generator import generate_pdf_invoice, generate_pdf_quotation
from app.core.excel_generator import export_invoices_to_excel

from app.api import inventory  # Import inventory route module
from app.api import auth  # Import authentication routes
from app.api import services  # Import services routes
from app.api import invoices  # Import invoices routes
from app.api import sales  # Import sales routes
from app.api import db_management  # Import database management routes
from app.api import quotations  # Import quotations routes
from app.api import enquiries  # Import enquiries routes
from app.api import customers  # Import customers routes
from app.db import crud, database, models
from app.db.migrate import run_migrations
from app.core.auth import get_current_user_from_cookie

# Helper function to get current user from cookie is defined below after app initialization

# Define database constants
DB_FOLDER = "db"  # Database folder
DB_PATH = os.path.join(DB_FOLDER, "sunmax.db")  # Local database path

# Ensure the database folder exists
os.makedirs(DB_FOLDER, exist_ok=True)

# Initialize database directly without cloud storage
print("Using local database")

# Initialize the database - this will create tables if they don't exist
database.init_db()

# Create the enquiries table
from app.db.create_enquiries_table import create_enquiries_table
create_enquiries_table()

# Create the customers table
from app.db.create_customers_table import create_customers_table
create_customers_table()

# Create invoices directory if it doesn't exist
os.makedirs("invoices", exist_ok=True)
# We'll call this after the app is initialized

# Simple SIGTERM handler
def handle_sigterm(*args):
    """Handle SIGTERM signal by shutting down gracefully."""
    print("Received SIGTERM signal, shutting down...")
    exit(0)

# Register the SIGTERM handler
signal.signal(signal.SIGTERM, handle_sigterm)

# Also register an exit handler
def exit_handler():
    """Handle normal exit."""
    print("Application exiting normally...")

# Register the exit handler
atexit.register(exit_handler)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key="sunmax_session_secret_key_2023_please_change_in_production",
    max_age=3600  # 1 hour
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create invoices directory if it doesn't exist
os.makedirs("invoices", exist_ok=True)

# Create quotations directory if it doesn't exist
os.makedirs("quotations", exist_ok=True)

# Mount invoices directory as static files
app.mount("/invoice-files", StaticFiles(directory="invoices"), name="invoices")

# Mount quotations directory as static files
app.mount("/quotation-files", StaticFiles(directory="quotations"), name="quotations")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(inventory.router, prefix="/api", tags=["Inventory"])
app.include_router(auth.router)
app.include_router(services.router, tags=["Services"])
app.include_router(invoices.router, prefix="/api", tags=["Invoices"])
app.include_router(sales.router, prefix="/api", tags=["Sales"])
app.include_router(quotations.router, tags=["Quotations"])
app.include_router(enquiries.router, tags=["Enquiries"])
app.include_router(customers.router, tags=["Customers"])

@app.delete("/api/services/delete/{service_id}")
async def delete_service_api(service_id: int, db: Session = Depends(database.get_db)):
    """Delete a service directly via API"""
    try:
        print(f"Attempting to delete service with ID: {service_id}")

        # Check if the service exists
        service = crud.get_service(db, service_id)
        if not service:
            print(f"Service with ID {service_id} not found")
            return JSONResponse(status_code=404, content={"success": False, "message": "Service not found"})

        # Delete the service
        result = crud.delete_service(db, service_id)

        if result:
            print(f"Service with ID {service_id} deleted successfully")
            return JSONResponse(content={"success": True, "message": "Service deleted successfully"})
        else:
            print(f"Failed to delete service with ID {service_id}")
            return JSONResponse(status_code=500, content={"success": False, "message": "Failed to delete service"})
    except Exception as e:
        print(f"Error deleting service: {e}")
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

# Include the database management router
app.include_router(db_management.router, prefix="/api", tags=["Database"])

# No need to backup database on startup anymore


# Helper function to get current user from cookie is now imported from app.core.auth

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(database.get_db)):
    # Get current user from cookie
    user = await get_current_user_from_cookie(request, db=db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Get items from database
    items = crud.get_all_items(db)

    # Get services from database
    services = crud.get_all_services(db)

    # Get sales statistics
    sales_stats = crud.get_sales_stats(db)

    # Calculate total inventory count
    total_inventory = sum(item.quantity for item in items)

    # Calculate unique categories count
    categories = set()
    for item in items:
        if hasattr(item, 'category') and item.category:
            categories.add(item.category)

    # If no categories are found, try to extract from item names
    if not categories:
        for item in items:
            # Extract first word as category (simplified approach)
            if hasattr(item, 'item_name') and item.item_name:
                category = item.item_name.split()[0] if item.item_name.split() else ""
                if category:
                    categories.add(category)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "items": items,
        "services": services,
        "sales_stats": sales_stats,
        "total_inventory": total_inventory,
        "categories": len(categories),
        "categories_list": list(categories)
    })

@app.get("/stock", response_class=HTMLResponse)
async def stock_page(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=10, le=500),
    db: Session = Depends(database.get_db)
):
    # Get current user from cookie
    user = await get_current_user_from_cookie(request, db=db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Get total count of items
    total_items = crud.get_items_count(db)

    # Calculate total pages
    total_pages = (total_items + limit - 1) // limit

    # Ensure page is valid
    if page > total_pages and total_pages > 0:
        page = total_pages

    # Calculate offset
    offset = (page - 1) * limit

    # Get items for current page
    items = crud.get_all_items(db, skip=offset, limit=limit)

    return templates.TemplateResponse(
        "stock.html",
        {
            "request": request,
            "user": user,
            "items": items,
            "today": datetime.now().date(),
            "current_page": page,
            "total_pages": total_pages,
            "total_items": total_items,
            "limit": limit
        }
    )

@app.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request, db: Session = Depends(database.get_db)):
    # Get current user from cookie
    user = await get_current_user_from_cookie(request, db=db)

    # Cart data will be handled by JavaScript
    # We're just providing the template here
    # The actual cart items will be loaded from localStorage in JavaScript
    return templates.TemplateResponse("cart.html", {"request": request, "user": user})

@app.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request, db: Session = Depends(database.get_db)):
    # Get current user from cookie
    user = await get_current_user_from_cookie(request, db=db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url="/login?next=/checkout", status_code=303)

    # Checkout page will be populated with cart data from localStorage
    return templates.TemplateResponse("checkout.html", {"request": request, "user": user})

@app.get("/invoices", response_class=HTMLResponse)
async def invoices_page(
    request: Request,
    payment_status: Optional[str] = None,
    invoice_type: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    # Get current user from cookie
    user = await get_current_user_from_cookie(request, db=db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url="/login?next=/invoices", status_code=303)

    # Get all invoices from database
    invoices = crud.get_all_invoices(db)

    # Filter by payment status if provided
    if payment_status and payment_status != "all":
        invoices = [inv for inv in invoices if inv["payment_status"] == payment_status]

    # Filter by invoice type if provided
    if invoice_type and invoice_type != "all":
        invoices = [inv for inv in invoices if inv.get("invoice_type", "product") == invoice_type]

    return templates.TemplateResponse(
        "invoices.html",
        {
            "request": request,
            "user": user,
            "invoices": invoices,
            "current_payment_status": payment_status or "all",
            "current_invoice_type": invoice_type or "all"
        }
    )

@app.get("/api/invoices/export-excel")
async def export_invoices_excel(
    payment_status: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """Export invoices to Excel file with detailed information for GST filing"""
    try:
        # Get all invoices from database
        invoices = crud.get_all_invoices(db)

        # Filter by payment status if provided
        if payment_status and payment_status != "all":
            invoices = [inv for inv in invoices if inv["payment_status"] == payment_status]

        # Use the excel_generator module to create the Excel file
        from app.core.excel_generator import export_invoices_to_excel
        filename, file_path = export_invoices_to_excel(invoices, db, payment_status)

        # Return the Excel file
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename
        )
    except Exception as e:
        print(f"Error exporting invoices to Excel: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/invoice/{invoice_id}", response_class=HTMLResponse)
async def invoice_page(request: Request, invoice_id: str, db: Session = Depends(database.get_db)):
    # Get current user from cookie
    user = await get_current_user_from_cookie(request, db=db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url=f"/login?next=/invoice/{invoice_id}", status_code=303)

    # Check if invoice_id is a number (database ID) or a string (invoice number)
    try:
        # Try to convert to int - if it works, it's a database ID
        invoice_id_int = int(invoice_id)

        # Get invoice by ID
        invoice_obj = db.query(models.Invoice).filter(models.Invoice.id == invoice_id_int).first()
        if not invoice_obj:
            return {"error": "Invoice not found"}

        # Get invoice by invoice number
        invoice = crud.get_invoice(db, invoice_obj.invoice_number)
    except ValueError:
        # If conversion fails, treat as invoice number
        invoice = crud.get_invoice(db, invoice_id)

    if not invoice:
        return {"error": "Invoice not found"}

    return templates.TemplateResponse("invoice.html", {"request": request, "user": user, "invoice": invoice})

# Authentication and user management routes
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: Optional[str] = None, db: Session = Depends(database.get_db)):
    # Check if user is already logged in
    user = await get_current_user_from_cookie(request, db=db)
    if user:
        # If already logged in, redirect to home or next page
        return RedirectResponse(url=next or "/", status_code=303)

    # Check for password changed cookie
    password_changed = request.cookies.get("password_changed")
    success_message = None

    if password_changed:
        success_message = "Password changed successfully. Please log in with your new password."
        # Create a response that will clear the cookie
        response = templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "next": next,
                "success": success_message
            }
        )
        response.delete_cookie(key="password_changed")
        return response

    return templates.TemplateResponse("login.html", {"request": request, "next": next})


@app.get("/change-password", response_class=HTMLResponse)
async def change_password_page(request: Request, db: Session = Depends(database.get_db)):
    # Get current user from cookie
    user = await get_current_user_from_cookie(request, db=db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url="/login?next=/change-password", status_code=303)

    return templates.TemplateResponse(
        "change_password.html",
        {
            "request": request,
            "user": user,
            "first_login": user.first_login
        }
    )


@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(database.get_db)):
    # Get current user from cookie
    user = await get_current_user_from_cookie(request, db=db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url="/login?next=/profile", status_code=303)

    return templates.TemplateResponse("profile.html", {"request": request, "user": user})


@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, db: Session = Depends(database.get_db)):
    # Get current user from cookie
    user = await get_current_user_from_cookie(request, db=db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url="/login?next=/users", status_code=303)

    # Check if user is admin or top_user
    if user.role not in ["admin", "top_user"]:
        return RedirectResponse(url="/", status_code=303)

    # Get all users
    users = crud.get_all_users(db)

    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "user": user,
            "users": users
        }
    )

# User management page - only accessible by top_user
@app.get("/user-management", response_class=HTMLResponse)
async def user_management_page(request: Request, db: Session = Depends(database.get_db)):
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db=db)
        print(f"Current user: {user}")

        # Redirect to login if not authenticated
        if not user:
            print("No user found, redirecting to login")
            return RedirectResponse(url="/login?next=/user-management", status_code=303)

        # Check if user is top_user or admin
        if user.role not in ["top_user", "admin"]:
            print(f"User role is {user.role}, not top_user or admin, redirecting to home")
            return RedirectResponse(url="/", status_code=303)

        # Get all users
        users = crud.get_all_users(db)
        print(f"Found {len(users)} users")

        # Get success message from session if it exists
        success_message = request.session.get("success_message", "")

        # Clear the success message from the session after displaying it
        if "success_message" in request.session:
            del request.session["success_message"]

        return templates.TemplateResponse(
            "user_management.html",
            {
                "request": request,
                "user": user,
                "users": users,
                "success_message": success_message
            }
        )
    except Exception as e:
        print(f"Error in user_management_page: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Internal server error: {str(e)}"}
        )

# Add new user page - only accessible by top_user
@app.get("/user-management/add-new-user", response_class=HTMLResponse)
async def add_user_page(request: Request, db: Session = Depends(database.get_db)):
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db=db)
        print(f"Current user: {user}")

        # Redirect to login if not authenticated
        if not user:
            print("No user found, redirecting to login")
            return RedirectResponse(url="/login?next=/user-management/add-new-user", status_code=303)

        # Check if user is top_user or admin
        if user.role not in ["top_user", "admin"]:
            print(f"User role is {user.role}, not top_user or admin, redirecting to home")
            return RedirectResponse(url="/", status_code=303)

        return templates.TemplateResponse(
            "add_user.html",
            {
                "request": request,
                "user": user
            }
        )
    except Exception as e:
        print(f"Error in add_user_page: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Internal server error: {str(e)}"}
        )

# User Management API Endpoints for top_user role
@app.post("/api/users/create")
async def create_user_api(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    role: str = Form("employee"),
    db: Session = Depends(database.get_db)
):
    """Create a new user with a system-generated password"""
    try:
        print(f"Received create user request with data: name={name}, email={email}, phone={phone}, role={role}")

        # Get current user from cookie
        current_user = await get_current_user_from_cookie(request, db=db)
        print(f"Current user: {current_user}")

        if not current_user or current_user.role not in ["top_user", "admin"]:
            print(f"Authorization failed: User is {'not authenticated' if not current_user else f'not authorized (role: {current_user.role})'}")
            return RedirectResponse(url="/login?next=/user-management/add-new-user", status_code=303)

        # Check if email already exists
        existing_user = crud.get_user_by_email(db, email)
        if existing_user:
            print(f"Email {email} already registered to user ID {existing_user.id}")
            return templates.TemplateResponse(
                "add_user.html",
                {
                    "request": request,
                    "user": current_user,
                    "error": "Email already registered"
                },
                status_code=400
            )

        # Check if trying to create a top_user when one already exists
        if role == "top_user":
            existing_top_user = db.query(models.User).filter(models.User.role == "top_user").first()
            if existing_top_user:
                print(f"Attempt to create a second top_user when one already exists (ID: {existing_top_user.id})")
                return templates.TemplateResponse(
                    "add_user.html",
                    {
                        "request": request,
                        "user": current_user,
                        "error": "A top user already exists. Only one top user is allowed."
                    },
                    status_code=400
                )

        # Generate a random password
        import string
        import random
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        generated_password = ''.join(random.choice(characters) for _ in range(10))
        print(f"Generated password for new user: {generated_password}")

        # Create user data
        user_data = {
            "name": name,
            "email": email,
            "password": generated_password,
            "phone": phone,
            "role": role,
            "first_login": True  # Ensure user must change password on first login
        }
        print(f"Creating user with data: {user_data}")

        # Create user
        new_user = crud.create_user(db, user_data)
        print(f"User created successfully: ID={new_user.id}, email={new_user.email}, role={new_user.role}")

        # Add success message to session
        request.session["success_message"] = f"User {name} created successfully with password: {generated_password}"

        # Redirect to user management page
        return RedirectResponse(url="/user-management", status_code=303)
    except Exception as e:
        import traceback
        print(f"Error creating user: {e}")
        traceback.print_exc()
        return templates.TemplateResponse(
            "add_user.html",
            {
                "request": request,
                "user": current_user if 'current_user' in locals() else None,
                "error": f"Error creating user: {str(e)}"
            },
            status_code=500
        )



@app.post("/api/users/update/{user_id}")
async def update_user_api(
    user_id: int,
    request: Request,
    name: str = Form(None),
    email: str = Form(None),
    phone: str = Form(None),
    role: str = Form(None),
    db: Session = Depends(database.get_db)
):
    """Update a user"""
    try:
        print(f"Received update user request for ID {user_id} with data: name={name}, email={email}, phone={phone}, role={role}")

        # Get current user from cookie
        current_user = await get_current_user_from_cookie(request, db=db)
        print(f"Current user: {current_user}")

        if not current_user or current_user.role not in ["top_user", "admin"]:
            print(f"Authorization failed: User is {'not authenticated' if not current_user else f'not authorized (role: {current_user.role})'}")
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Not authorized. Admin or Top user privileges required."}
            )

        # Check if user exists
        user = crud.get_user(db, user_id)
        if not user:
            print(f"User with ID {user_id} not found")
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "User not found"}
            )
        print(f"Found user to update: ID={user.id}, name={user.name}, email={user.email}, role={user.role}")

        # Check if email already exists (if email is being updated)
        if email and email != user.email:
            existing_user = crud.get_user_by_email(db, email)
            if existing_user:
                print(f"Email {email} already registered to another user (ID: {existing_user.id})")
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": "Email already registered to another user"}
                )

        # Create update data
        update_data = {}
        if name:
            update_data["name"] = name
        if email:
            update_data["email"] = email
        if phone is not None:  # Allow empty string
            update_data["phone"] = phone
        if role:
            update_data["role"] = role

        print(f"Updating user with data: {update_data}")

        # Update user
        updated_user = crud.update_user(db, user_id, update_data)
        print(f"User updated successfully: ID={updated_user.id}, name={updated_user.name}, email={updated_user.email}, role={updated_user.role}")

        return JSONResponse(
            content={
                "success": True,
                "message": "User updated successfully",
                "user": {
                    "id": updated_user.id,
                    "name": updated_user.name,
                    "email": updated_user.email,
                    "phone": updated_user.phone,
                    "role": updated_user.role
                }
            }
        )
    except Exception as e:
        import traceback
        print(f"Error updating user: {e}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error updating user: {str(e)}"}
        )

@app.post("/api/users/delete/{user_id}")
async def delete_user_api(
    user_id: int,
    request: Request,
    db: Session = Depends(database.get_db)
):
    """Delete a user"""
    try:
        # Get current user from cookie
        current_user = await get_current_user_from_cookie(request, db=db)
        if not current_user or current_user.role not in ["top_user", "admin"]:
            print(f"Authorization failed: User is {'not authenticated' if not current_user else f'not authorized (role: {current_user.role})'}")
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Not authorized. Admin or Top user privileges required."}
            )

        # Prevent deleting yourself
        if current_user.id == user_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Cannot delete your own account"}
            )

        # Check if user exists
        user = crud.get_user(db, user_id)
        if not user:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "User not found"}
            )

        # Delete user
        result = crud.delete_user(db, user_id)
        if not result:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Failed to delete user"}
            )

        return JSONResponse(
            content={
                "success": True,
                "message": "User deleted successfully"
            }
        )
    except Exception as e:
        print(f"Error deleting user: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error deleting user: {str(e)}"}
        )

@app.get("/api/users/{user_id}")
async def get_user_api(
    user_id: int,
    request: Request,
    db: Session = Depends(database.get_db)
):
    """Get a single user by ID"""
    try:
        print(f"Fetching user with ID: {user_id}")

        # Get current user from cookie
        current_user = await get_current_user_from_cookie(request, db=db)
        print(f"Current user: {current_user}")

        if not current_user or current_user.role not in ["top_user", "admin"]:
            print(f"Authorization failed: User is {'not authenticated' if not current_user else f'not authorized (role: {current_user.role})'}")
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Not authorized. Admin or Top user privileges required."}
            )

        # Get user
        user = crud.get_user(db, user_id)
        if not user:
            print(f"User with ID {user_id} not found")
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "User not found"}
            )

        print(f"Found user: ID={user.id}, name={user.name}, email={user.email}, role={user.role}")

        # Return user data
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "created_at": user.created_at,
            "last_login": user.last_login
        }
    except Exception as e:
        import traceback
        print(f"Error getting user: {e}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error getting user: {str(e)}"}
        )

@app.post("/api/users/reset-password/{user_id}")
async def reset_password_api(
    user_id: int,
    request: Request,
    db: Session = Depends(database.get_db)
):
    """Reset a user's password and set first_login flag to true"""
    try:
        # Get current user from cookie
        current_user = await get_current_user_from_cookie(request, db=db)
        if not current_user or current_user.role not in ["top_user", "admin"]:
            print(f"Authorization failed: User is {'not authenticated' if not current_user else f'not authorized (role: {current_user.role})'}")
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Not authorized. Admin or Top user privileges required."}
            )

        # Check if user exists
        user = crud.get_user(db, user_id)
        if not user:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "User not found"}
            )

        # Generate a new random password
        import string
        import random
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        generated_password = ''.join(random.choice(characters) for _ in range(10))

        # Hash the password
        from app.core.auth import get_password_hash
        hashed_password = get_password_hash(generated_password)

        # Update user with new password and set first_login to True
        user.password = hashed_password
        user.first_login = True
        db.commit()
        db.refresh(user)

        return JSONResponse(
            content={
                "success": True,
                "message": "Password reset successfully",
                "generated_password": generated_password
            }
        )
    except Exception as e:
        print(f"Error resetting password: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error resetting password: {str(e)}"}
        )


@app.get("/insights", response_class=HTMLResponse)
async def insights_page(request: Request, db: Session = Depends(database.get_db)):
    # Get current user from cookie
    user = await get_current_user_from_cookie(request, db=db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url="/login?next=/insights", status_code=303)

    # Check if user is admin or top_user
    if user.role not in ["admin", "top_user"]:
        return RedirectResponse(url="/", status_code=303)

    # Get items from database
    items = crud.get_all_items(db)

    # Get sales statistics
    sales_stats = crud.get_sales_stats(db)

    # Calculate total inventory count
    total_inventory = sum(item.quantity for item in items)

    # Calculate unique categories and organize items by category
    categories = set()
    category_items = {}
    category_values = {}

    for item in items:
        category = None
        if hasattr(item, 'category') and item.category:
            category = item.category
        else:
            # Extract first word as category (simplified approach)
            if hasattr(item, 'item_name') and item.item_name:
                category = item.item_name.split()[0] if item.item_name.split() else "Other"

        if category:
            categories.add(category)

            # Add to category items count
            if category not in category_items:
                category_items[category] = 0
            category_items[category] += 1

            # Add to category value (quantity * purchase price)
            if category not in category_values:
                category_values[category] = 0
            category_values[category] += item.quantity * item.purchase_price_per_unit

    # Get low stock items (quantity < 5)
    low_stock_items = [item for item in items if item.quantity < 5]

    # Get all invoices for sales trend data
    all_invoices = crud.get_all_invoices(db, limit=1000)  # Get more invoices for better data

    # Prepare monthly sales data
    import calendar
    from datetime import datetime

    # Initialize monthly sales data with zeros
    current_year = datetime.now().year
    monthly_sales = {month: 0 for month in range(1, 13)}

    # Populate with actual data
    for invoice in all_invoices:
        if isinstance(invoice['date'], str):
            try:
                date = datetime.strptime(invoice['date'], '%Y-%m-%d')
            except ValueError:
                continue
        else:
            date = invoice['date']

        if date.year == current_year:
            monthly_sales[date.month] += invoice['total_amount']

    # Convert to list format for the chart
    sales_trend_data = [round(monthly_sales[month], 2) for month in range(1, 13)]
    sales_trend_labels = list(calendar.month_name)[1:]  # Get month names

    # Get payment method distribution
    payment_methods = {}
    for invoice in all_invoices:
        method = invoice['payment_method']
        if method not in payment_methods:
            payment_methods[method] = 0
        payment_methods[method] += invoice['total_amount']

    # Convert to lists for the chart
    payment_method_labels = list(payment_methods.keys())
    payment_method_data = [round(payment_methods[method], 2) for method in payment_method_labels]

    # Prepare category distribution data
    category_distribution_labels = list(category_items.keys())
    category_distribution_data = [category_items[category] for category in category_distribution_labels]

    # Prepare inventory value distribution data
    inventory_value_labels = list(category_values.keys())
    inventory_value_data = [round(category_values[category], 2) for category in inventory_value_labels]

    return templates.TemplateResponse(
        "insights.html",
        {
            "request": request,
            "user": user,
            "items": items,
            "sales_stats": sales_stats,
            "total_inventory": total_inventory,
            "categories": len(categories),
            "low_stock_items": low_stock_items,
            "low_stock_count": len(low_stock_items),
            # Chart data
            "sales_trend_labels": sales_trend_labels,
            "sales_trend_data": sales_trend_data,
            "category_distribution_labels": category_distribution_labels,
            "category_distribution_data": category_distribution_data,
            "payment_method_labels": payment_method_labels,
            "payment_method_data": payment_method_data,
            "inventory_value_labels": inventory_value_labels,
            "inventory_value_data": inventory_value_data
        }
    )


@app.post("/api/checkout")
async def process_checkout(
    buyer_name: str = Form(...),
    buyer_gst: str = Form(""),  # Optional field
    buyer_address: str = Form(...),
    buyer_phone: str = Form(...),
    buyer_email: str = Form(""),  # Optional field
    invoice_date: str = Form(...),  # Added invoice date field
    payment_method: str = Form(...),
    payment_status: str = Form(...),  # Fully Paid, Partially Paid, Unpaid
    amount_paid: str = Form(None),  # Optional, will be set based on payment_status
    cart_items: str = Form(...),
    db: Session = Depends(database.get_db)
):
    try:
        # Parse cart items
        items = json.loads(cart_items)

        # Calculate totals with discounts
        subtotal = sum(item["price"] * item["quantity"] for item in items)

        # Calculate total discount
        total_discount = sum(
            (item["price"] * item["quantity"]) * ((item.get("discount", 0) or 0) / 100)
            for item in items
        )

        # Calculate discounted subtotal
        discounted_subtotal = subtotal - total_discount

        # Calculate GST amount on discounted subtotal and round to 2 decimal places
        gst_amount = sum(
            round(
                ((item["price"] * item["quantity"]) -
                 ((item["price"] * item["quantity"]) * ((item.get("discount", 0) or 0) / 100))) *
                (item["gst_rate"] / 100),
                2
            )
            for item in items
        )

        total = discounted_subtotal + gst_amount

        # Round all values to 2 decimal places
        subtotal = round(subtotal, 2)
        total_discount = round(total_discount, 2)
        discounted_subtotal = round(discounted_subtotal, 2)
        gst_amount = round(gst_amount, 2)
        total = round(total, 2)

        # Handle amount paid based on payment status
        if payment_status == "Fully Paid":
            amount_paid_value = total
        elif payment_status == "Unpaid":
            amount_paid_value = 0.0
        else:  # Partially Paid
            # Convert amount_paid to float, default to 0 if empty or invalid
            try:
                amount_paid_value = float(amount_paid) if amount_paid else 0.0
                amount_paid_value = round(amount_paid_value, 2)

                # Validate amount paid is not greater than total
                if amount_paid_value > total:
                    amount_paid_value = total
                    payment_status = "Fully Paid"
                elif amount_paid_value <= 0:
                    amount_paid_value = 0.0
                    payment_status = "Unpaid"
            except ValueError:
                amount_paid_value = 0.0
                payment_status = "Unpaid"

        # Generate invoice number
        invoice_number = crud.generate_invoice_number(db)

        # Set PDF path
        pdf_path = f"invoices/{invoice_number}.pdf"

        # Parse the invoice date from the form
        try:
            # Convert string date to datetime object
            invoice_date_obj = datetime.strptime(invoice_date, '%Y-%m-%d')
        except ValueError:
            # If date parsing fails, use current date
            invoice_date_obj = datetime.now()

        # Create invoice data
        invoice_data = {
            "invoice_number": invoice_number,
            "date": invoice_date_obj,  # Use the parsed date
            "customer_name": buyer_name,
            "customer_gst": buyer_gst,
            "customer_address": buyer_address,
            "customer_phone": buyer_phone,
            "customer_email": buyer_email,
            "payment_method": payment_method,
            "payment_status": payment_status,
            "amount_paid": amount_paid_value,
            "items": [],
            "subtotal": subtotal,
            "total_discount": total_discount,
            "discounted_subtotal": discounted_subtotal,
            "total_gst": gst_amount,
            "total_amount": total,
            "pdf_path": pdf_path
        }

        # Add items to invoice
        for item in items:
            item_subtotal = item["price"] * item["quantity"]

            # Get discount percentage (default to 0 if not present)
            discount_percent = item.get("discount", 0) or 0

            # Calculate discount amount
            discount_amount = round(item_subtotal * (discount_percent / 100), 2)

            # Calculate discounted subtotal
            discounted_subtotal = item_subtotal - discount_amount

            # Round GST amount to 2 decimal places (calculated on discounted amount)
            item_gst = round(discounted_subtotal * (item["gst_rate"] / 100), 2)

            # Calculate total with GST
            item_total = round(discounted_subtotal + item_gst, 2)

            # Get item details from database
            db_item = crud.get_item(db, item["id"])
            hsn_code = db_item.hsn_code if db_item else "N/A"

            invoice_data["items"].append({
                "item_code": item["id"],
                "item_name": item["item_name"],
                "hsn_code": hsn_code,
                "price": round(item["price"], 2),
                "quantity": item["quantity"],
                "discount_percent": discount_percent,
                "discount_amount": discount_amount,
                "discounted_subtotal": discounted_subtotal,
                "gst_rate": item["gst_rate"],
                "gst_amount": item_gst,
                "total": item_total
            })

            # Stock is already reserved when added to cart, so we don't need to update it again
            # Just verify that the item exists
            if not db_item:
                print(f"Warning: Item {item['id']} not found in database")

        # Save invoice to database
        invoice = crud.create_invoice(db, invoice_data)

        # Generate PDF invoice
        generate_pdf_invoice(invoice)

        # Update sales counter
        crud.update_sales_counter(db, total)

        return {"success": True, "invoice_id": invoice.invoice_number}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/invoices/view/{invoice_id}")
async def view_invoice_pdf(invoice_id: str, db: Session = Depends(database.get_db)):
    try:
        # Get invoice from database
        invoice = crud.get_invoice(db, invoice_id)
        if not invoice:
            return JSONResponse(status_code=404, content={"error": "Invoice not found"})

        # Get PDF path
        pdf_path = invoice.get("pdf_path", f"invoices/{invoice_id}.pdf")
        filename = os.path.basename(pdf_path)

        # Check if PDF exists and has valid size
        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) < 1000:  # Check if file is too small
            print(f"PDF file missing or too small: {pdf_path}, size: {os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0} bytes")

            # Try to regenerate the PDF
            from app.core.pdf_generator import generate_pdf_invoice
            print(f"Regenerating PDF for invoice {invoice_id}")
            generate_pdf_invoice(invoice)

            # Check again if PDF exists and has valid size
            if not os.path.exists(pdf_path):
                return JSONResponse(status_code=404, content={"error": "Invoice PDF not found and could not be generated"})
            elif os.path.getsize(pdf_path) < 1000:
                return JSONResponse(status_code=500, content={"error": "Generated PDF file is too small and may be corrupted"})

        # Use the mounted static directory to serve the file
        return RedirectResponse(url=f"/invoice-files/{filename}", status_code=303)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error viewing PDF: {e}")
        print(f"Error details: {error_details}")
        return JSONResponse(status_code=500, content={"error": f"Error viewing PDF: {str(e)}", "details": error_details})

@app.get("/api/invoices/download/{invoice_id}")
async def download_invoice_pdf(invoice_id: str, db: Session = Depends(database.get_db)):
    try:
        # Get invoice from database
        invoice = crud.get_invoice(db, invoice_id)
        if not invoice:
            return JSONResponse(status_code=404, content={"error": "Invoice not found"})

        # Get PDF path
        pdf_path = invoice.get("pdf_path", f"invoices/{invoice_id}.pdf")
        filename = os.path.basename(pdf_path)

        # Check if PDF exists and has valid size
        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) < 1000:  # Check if file is too small
            print(f"PDF file missing or too small: {pdf_path}, size: {os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0} bytes")

            # Try to regenerate the PDF
            from app.core.pdf_generator import generate_pdf_invoice
            print(f"Regenerating PDF for invoice {invoice_id}")
            generate_pdf_invoice(invoice)

            # Check again if PDF exists and has valid size
            if not os.path.exists(pdf_path):
                return JSONResponse(status_code=404, content={"error": "Invoice PDF not found and could not be generated"})
            elif os.path.getsize(pdf_path) < 1000:
                return JSONResponse(status_code=500, content={"error": "Generated PDF file is too small and may be corrupted"})

        # For download, we'll still use FileResponse to set the content-disposition header
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"Invoice_{invoice_id}.pdf"
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error downloading PDF: {e}")
        print(f"Error details: {error_details}")
        return JSONResponse(status_code=500, content={"error": f"Error downloading PDF: {str(e)}", "details": error_details})

@app.post("/api/reserve-stock")
async def reserve_stock(
    request: Request,
    data: dict = Body(...),
    db: Session = Depends(database.get_db)
):
    """Temporarily reserve stock for an item"""
    try:
        item_code = data.get("item_code")
        quantity = data.get("quantity", 1)

        if not item_code:
            return JSONResponse(status_code=400, content={"success": False, "message": "Item code is required"})

        # Get the item from the database
        item = crud.get_item(db, item_code)
        if not item:
            return JSONResponse(status_code=404, content={"success": False, "message": "Item not found"})

        # Check if there's enough stock
        if item.quantity < quantity:
            return JSONResponse(status_code=400, content={
                "success": False,
                "message": f"Not enough stock. Only {item.quantity} units available."
            })

        # Temporarily reduce the stock
        result = crud.update_item_quantity(db, item_code, -quantity)
        if result:
            # Return the updated quantity in the response
            return JSONResponse(content={
                "success": True,
                "message": "Stock reserved successfully",
                "new_quantity": result.quantity
            })
        else:
            return JSONResponse(status_code=500, content={"success": False, "message": "Failed to reserve stock"})
    except Exception as e:
        print(f"Error reserving stock: {e}")
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

@app.post("/api/release-stock")
async def release_stock(
    data: dict = Body(...),
    db: Session = Depends(database.get_db)
):
    """Release reserved stock for an item"""
    try:
        item_code = data.get("item_code")
        quantity = data.get("quantity", 1)

        if not item_code:
            return JSONResponse(status_code=400, content={"success": False, "message": "Item code is required"})

        # Get the item from the database
        item = crud.get_item(db, item_code)
        if not item:
            return JSONResponse(status_code=404, content={"success": False, "message": "Item not found"})

        # Return the stock
        result = crud.update_item_quantity(db, item_code, quantity)
        if result:
            # Return the updated quantity in the response
            return JSONResponse(content={
                "success": True,
                "message": "Stock released successfully",
                "new_quantity": result.quantity
            })
        else:
            return JSONResponse(status_code=500, content={"success": False, "message": "Failed to release stock"})
    except Exception as e:
        print(f"Error releasing stock: {e}")
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

@app.post("/api/invoices/payment/{invoice_id}")
async def add_payment_to_invoice(
    invoice_id: str,
    amount: float = Form(...),
    payment_method: str = Form(...),
    notes: str = Form(""),
    db: Session = Depends(database.get_db)
):
    """Add a payment to an existing invoice"""
    try:
        # Create payment data
        payment_data = {
            "amount": amount,
            "payment_method": payment_method,
            "notes": notes,
            "payment_date": datetime.now()
        }

        # Add payment to invoice
        invoice = crud.add_payment(db, invoice_id, payment_data)

        if not invoice:
            return JSONResponse(status_code=404, content={"success": False, "message": "Invoice not found"})

        # Regenerate the PDF with updated payment information
        invoice_data = crud.get_invoice(db, invoice_id)
        generate_pdf_invoice(invoice_data)

        return JSONResponse(content={
            "success": True,
            "message": "Payment added successfully",
            "invoice_id": invoice_id,
            "payment_status": invoice.payment_status,
            "amount_paid": invoice.amount_paid,
            "balance_due": round(invoice.total_amount - invoice.amount_paid, 2)
        })
    except Exception as e:
        print(f"Error adding payment: {e}")
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})


@app.delete("/api/invoices/delete/{invoice_id}")
async def delete_invoice_api(invoice_id: str, db: Session = Depends(database.get_db)):
    """Delete an invoice"""
    try:
        # Get invoice from database
        invoice = crud.get_invoice(db, invoice_id)
        if not invoice:
            return JSONResponse(status_code=404, content={"error": "Invoice not found"})

        # Delete the PDF file if it exists
        pdf_path = f"invoices/{invoice_id}.pdf"
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception as e:
                print(f"Error deleting PDF file: {e}")

        # Delete the invoice from the database
        result = crud.delete_invoice(db, invoice_id)
        if result:
            return JSONResponse(content={"status": "success", "message": "Invoice deleted successfully"})
        else:
            return JSONResponse(status_code=404, content={"error": "Invoice not found in database"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Error deleting invoice: {str(e)}"})


@app.delete("/api/enquiries/delete/{enquiry_id}")
async def delete_enquiry_api(enquiry_id: int, db: Session = Depends(database.get_db)):
    """Delete an enquiry directly via API"""
    try:
        print(f"Attempting to delete enquiry with ID: {enquiry_id}")

        # Check if the enquiry exists
        enquiry = crud.get_enquiry(db, enquiry_id)
        if not enquiry:
            print(f"Enquiry with ID {enquiry_id} not found")
            return JSONResponse(status_code=404, content={"success": False, "message": "Enquiry not found"})

        # Delete the enquiry
        result = crud.delete_enquiry(db, enquiry_id)
        if result:
            print(f"Enquiry with ID {enquiry_id} deleted successfully")
            return JSONResponse(content={"success": True, "message": "Enquiry deleted successfully"})
        else:
            print(f"Failed to delete enquiry with ID {enquiry_id}")
            return JSONResponse(status_code=500, content={"success": False, "message": "Failed to delete enquiry"})
    except Exception as e:
        print(f"Error deleting enquiry: {e}")
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})


@app.delete("/api/inventory/delete/{item_code}")
async def delete_inventory_item(item_code: str, db: Session = Depends(database.get_db)):
    """Delete an inventory item directly"""
    try:
        print(f"Attempting to delete inventory item: {item_code}")

        # Check if the item exists before attempting to delete
        item = crud.get_item(db, item_code)
        if not item:
            print(f"Item {item_code} not found in database")
            return JSONResponse(status_code=404, content={"success": False, "message": "Item not found"})

        print(f"Item {item_code} found in database, proceeding with deletion")

        # Delete the item from the database
        result = crud.delete_item(db, item_code)

        # Verify the item was actually deleted
        if result:
            # Double-check that the item is no longer in the database
            verification = crud.get_item(db, item_code)
            if verification:
                print(f"WARNING: Item {item_code} still exists in database after deletion")
                return JSONResponse(status_code=500, content={"success": False, "message": "Item deletion failed - item still exists"})

            print(f"Item {item_code} successfully deleted and verified")
            return JSONResponse(content={"success": True, "message": f"Item {item_code} deleted successfully"})
        else:
            print(f"Item {item_code} deletion failed")
            return JSONResponse(status_code=500, content={"success": False, "message": "Item deletion failed"})
    except Exception as e:
        print(f"Error deleting inventory item: {e}")
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

@app.post("/customer/{customer_id}/delete")
async def delete_customer_route(
    request: Request,
    customer_id: int,
    db: Session = Depends(database.get_db)
):
    """Delete a customer record"""
    try:
        print(f"[MAIN.PY] Received request to delete customer ID: {customer_id}")
        
        # Get current user from cookie
        from app.core.auth import get_current_user_from_cookie
        user = await get_current_user_from_cookie(request, db)
        
        # Check if user is authenticated
        if not user:
            print(f"[MAIN.PY] User not authenticated")
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Authentication required"}
            )
        
        print(f"[MAIN.PY] User authenticated: {user.username}")
        
        # Get the customer
        from app.db import crud
        customer = crud.get_customer(db, customer_id)
        
        if not customer:
            print(f"[MAIN.PY] Customer ID {customer_id} not found")
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Customer not found"}
            )
        
        print(f"[MAIN.PY] Found customer: {customer.customer_name} (ID: {customer_id})")
        
        # Use the crud function to delete the customer
        result = crud.delete_customer(db, customer_id)
        
        if result:
            print(f"[MAIN.PY] Successfully deleted customer ID: {customer_id}")
            return JSONResponse(
                content={"success": True, "message": "Customer deleted successfully"}
            )
        else:
            print(f"[MAIN.PY] Failed to delete customer ID: {customer_id}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Failed to delete customer"}
            )
    except Exception as e:
        print(f"[MAIN.PY] Error deleting customer: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error deleting customer: {str(e)}"}
        )



