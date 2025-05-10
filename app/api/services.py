from fastapi import APIRouter, Depends, Request, Form, Body, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db import crud, database, models
from app.core.pdf_generator import generate_pdf_invoice
from datetime import date, datetime
import sqlite3
import os
import pandas as pd
import tempfile

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Function to ensure the services table exists
def ensure_services_table_exists():
    """Check if the services table exists and create it if it doesn't"""
    try:
        # Connect to the SQLite database
        DB_FOLDER = "db"  # Database folder
        db_path = os.path.join(os.getcwd(), DB_FOLDER, "sunmax.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the services table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='services'")
        if not cursor.fetchone():
            print("Creating services table...")
            # Create the services table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_code TEXT UNIQUE NOT NULL,
                date DATE NOT NULL,
                service_name TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                gst_rate REAL DEFAULT 18.0,
                payment_method TEXT,
                payment_status TEXT DEFAULT 'Unpaid',
                invoice_id INTEGER,
                pdf_path TEXT,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id)
            )
            """)
            conn.commit()
            print("Services table created successfully.")
        else:
            # Check if required columns exist
            cursor.execute("PRAGMA table_info(services)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]

            # Check for missing columns
            missing_columns = []
            if "service_code" not in column_names:
                missing_columns.append("service_code")
            if "service_name" not in column_names:
                missing_columns.append("service_name")
            if "price" not in column_names:
                missing_columns.append("price")
            if "gst_rate" not in column_names:
                missing_columns.append("gst_rate")

            # If service_code column doesn't exist, recreate the table (major schema change)
            if "service_code" not in column_names or "service_name" not in column_names:
                print("Recreating services table with correct schema...")

                # Check if services_old table exists and drop it if it does
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='services_old'")
                if cursor.fetchone():
                    cursor.execute("DROP TABLE services_old")
                    conn.commit()
                    print("Dropped existing services_old table")

                # Rename the old table
                cursor.execute("ALTER TABLE services RENAME TO services_old")

                # Create the new table with correct schema
                cursor.execute("""
                CREATE TABLE services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_code TEXT UNIQUE NOT NULL,
                    date DATE NOT NULL,
                    service_name TEXT NOT NULL,
                    employee_name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    gst_rate REAL DEFAULT 18.0,
                    payment_method TEXT,
                    payment_status TEXT DEFAULT 'Unpaid',
                    invoice_id INTEGER,
                    pdf_path TEXT,
                    FOREIGN KEY (invoice_id) REFERENCES invoices (id)
                )
                """)

                # Try to copy data from old table if possible
                try:
                    cursor.execute("""
                    INSERT INTO services (id, date, employee_name, description,
                                         payment_method, payment_status, invoice_id, pdf_path)
                    SELECT id, date, employee_name, description,
                           payment_method, payment_status, invoice_id, pdf_path
                    FROM services_old
                    """)

                    # Update service_code and service_name for existing records
                    cursor.execute("SELECT id FROM services")
                    service_ids = cursor.fetchall()
                    for i, (service_id,) in enumerate(service_ids):
                        service_code = f"SRV{str(i+1).zfill(3)}"
                        service_name = f"Service {i+1}"
                        price = 0.0
                        cursor.execute("UPDATE services SET service_code = ?, service_name = ?, price = ? WHERE id = ?",
                                      (service_code, service_name, price, service_id))
                except Exception as e:
                    print(f"Error copying data from old table: {e}")

                conn.commit()
                print("Services table recreated successfully.")
            # If only some columns are missing, add them as new columns
            else:
                if "price" not in column_names:
                    print("Adding price column to services table...")
                    cursor.execute("ALTER TABLE services ADD COLUMN price REAL DEFAULT 0")
                    # Try to copy total_amount to price if it exists
                    if "total_amount" in column_names:
                        cursor.execute("UPDATE services SET price = total_amount")
                    conn.commit()
                    print("Added price column to services table")

                if "gst_rate" not in column_names:
                    print("Adding gst_rate column to services table...")
                    cursor.execute("ALTER TABLE services ADD COLUMN gst_rate REAL DEFAULT 18.0")
                    conn.commit()
                    print("Added gst_rate column to services table")

        # Close the connection
        conn.close()
    except Exception as e:
        print(f"Error ensuring services table exists: {e}")

# Ensure the services table exists when the module is loaded
ensure_services_table_exists()

@router.get("/services/export-excel")
async def export_services_excel(db: Session = Depends(database.get_db)):
    """Export services to Excel"""
    from fastapi.responses import FileResponse
    from app.core.excel_generator import export_services_to_excel

    try:
        # Get all services
        services = crud.get_all_services(db)

        # Generate Excel file
        filename, file_path = export_services_to_excel(services)

        # Return the Excel file
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error exporting services to Excel: {e}")
        print(f"Error details: {error_details}")
        return JSONResponse(status_code=500, content={"error": f"Error exporting services to Excel: {str(e)}"})


@router.post("/api/services/import-excel")
async def import_services_excel(file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    """Import services from Excel"""
    try:
        # Create a temporary file to store the uploaded file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write the uploaded file content to the temporary file
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Read the Excel or CSV file
        try:
            file_extension = file.filename.split('.')[-1].lower()
            if file_extension == 'csv':
                df = pd.read_csv(temp_file_path)
            else:
                df = pd.read_excel(temp_file_path)
        except Exception as e:
            os.unlink(temp_file_path)  # Delete the temp file
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"Error reading file: {str(e)}"}
            )

        # Delete the temporary file
        os.unlink(temp_file_path)

        # Check if required columns exist
        required_columns = ['service_name', 'employee_name', 'price', 'date']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"Missing required columns: {', '.join(missing_columns)}",
                    "required_columns": required_columns
                }
            )

        # Process the data and create service records
        success_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                # Convert date string to date object if it's a string
                service_date = row['date']
                if isinstance(service_date, str):
                    try:
                        service_date = datetime.strptime(service_date, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            service_date = datetime.strptime(service_date, '%d-%m-%Y').date()
                        except ValueError:
                            errors.append(f"Row {index+1}: Invalid date format. Use YYYY-MM-DD or DD-MM-YYYY.")
                            continue

                # Create service data dictionary
                service_data = {
                    "service_name": str(row['service_name']),
                    "employee_name": str(row['employee_name']),
                    "description": str(row.get('description', '')),
                    "price": float(row['price']),
                    "date": service_date,
                    "gst_rate": float(row.get('gst_rate', 18.0)),
                    "payment_method": str(row.get('payment_method', '')),
                    "payment_status": str(row.get('payment_status', 'Unpaid'))
                }

                # Generate a unique service code
                service_count = db.query(models.Service).count()
                service_data["service_code"] = f"SRV{str(service_count + 1).zfill(3)}"

                # Create service record
                service = crud.create_service(db, service_data)
                success_count += 1
            except Exception as e:
                errors.append(f"Row {index+1}: {str(e)}")

        # Return response
        if success_count > 0:
            return JSONResponse(
                content={
                    "success": True,
                    "message": f"Successfully imported {success_count} services",
                    "errors": errors
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "No services were imported",
                    "errors": errors
                }
            )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error importing services from Excel: {e}")
        print(f"Error details: {error_details}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error importing services: {str(e)}"}
        )


@router.get("/services", response_class=HTMLResponse)
async def get_services_page(
    request: Request,
    message: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """Render the services listing page"""
    # Get current user from cookie
    from app.main import get_current_user_from_cookie

    user = await get_current_user_from_cookie(request, db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url="/login?next=/services", status_code=303)

    # Get all services
    services = crud.get_all_services(db)

    return templates.TemplateResponse(
        "services.html",
        {
            "request": request,
            "user": user,
            "services": services,
            "today": date.today(),
            "message": message,
            "error": error
        }
    )

@router.get("/service-cards", response_class=HTMLResponse)
async def get_service_cards_page(
    request: Request,
    message: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """Render the service cards page"""
    # Get current user from cookie
    from app.main import get_current_user_from_cookie

    user = await get_current_user_from_cookie(request, db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url="/login?next=/service-cards", status_code=303)

    # Get all services
    services = crud.get_all_services(db)

    return templates.TemplateResponse(
        "service_cards.html",
        {
            "request": request,
            "user": user,
            "services": services,
            "today": date.today(),
            "message": message,
            "error": error
        }
    )

@router.get("/api/services/item/{service_id}")
async def get_service_details(service_id: int, db: Session = Depends(database.get_db)):
    """Get service details for modal display"""
    try:
        print(f"Fetching service details for ID: {service_id}, Type: {type(service_id)}")

        # Get service by ID
        service = crud.get_service(db, service_id)
        if not service:
            print(f"Service not found with ID: {service_id}")
            return JSONResponse(status_code=404, content={"error": "Service not found"})

        print(f"Service found: {service.service_name}, ID: {service.id}")
        return service
    except Exception as e:
        print(f"Error fetching service details: {e}")
        return JSONResponse(status_code=500, content={"error": f"Error fetching service details: {str(e)}"})


@router.get("/api/services/search")
async def search_services(q: str, db: Session = Depends(database.get_db)):
    """Search for services by service code or name"""
    try:
        print(f"Searching services with query: {q}")

        # Search for services
        services = crud.search_services(db, q)

        # Convert services to a list of dictionaries for JSON response
        services_list = []
        for service in services:
            services_list.append({
                "id": service.id,
                "service_code": service.service_code,
                "service_name": service.service_name,
                "employee_name": service.employee_name,
                "description": service.description,
                "price": service.price,
                "date": service.date.strftime("%d-%m-%Y") if hasattr(service.date, "strftime") else service.date,
                "gst_rate": service.gst_rate,
                "payment_method": service.payment_method,
                "payment_status": service.payment_status
            })

        print(f"Found {len(services_list)} services matching the query")
        return services_list
    except Exception as e:
        print(f"Error searching services: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Error searching services: {str(e)}"})


@router.get("/api/services/{service_id}")
async def get_service_by_id(service_id: int, db: Session = Depends(database.get_db)):
    """Get service details by ID"""
    try:
        print(f"Fetching service with ID: {service_id}")

        # Get service by ID
        service = crud.get_service(db, service_id)
        if not service:
            print(f"Service not found with ID: {service_id}")
            return JSONResponse(status_code=404, content={"error": "Service not found"})

        # Convert service to dictionary for JSON response
        service_dict = {
            "id": service.id,
            "service_code": service.service_code,
            "service_name": service.service_name,
            "employee_name": service.employee_name,
            "description": service.description,
            "price": service.price,
            "date": service.date.strftime("%Y-%m-%d") if hasattr(service.date, "strftime") else service.date,
            "gst_rate": service.gst_rate,
            "payment_method": service.payment_method,
            "payment_status": service.payment_status
        }

        print(f"Service found: {service.service_name}, ID: {service.id}")
        return service_dict
    except Exception as e:
        print(f"Error fetching service: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Error fetching service: {str(e)}"})


@router.get("/service/{service_id}/edit", response_class=HTMLResponse)
async def get_edit_service_page(
    request: Request,
    service_id: int,
    db: Session = Depends(database.get_db)
):
    """Render the edit service form page"""
    # Get current user from cookie
    from app.main import get_current_user_from_cookie

    user = await get_current_user_from_cookie(request, db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url=f"/login?next=/service/{service_id}/edit", status_code=303)

    # Get service by ID
    service = crud.get_service(db, service_id)
    if not service:
        return RedirectResponse(url="/services", status_code=303)

    return templates.TemplateResponse(
        "service_form_simple.html",
        {
            "request": request,
            "user": user,
            "service": service,
            "edit_mode": True
        }
    )

@router.post("/service/{service_id}/edit", response_class=HTMLResponse)
async def update_service(
    request: Request,
    service_id: int,
    date: date = Form(...),
    service_name: str = Form(...),
    employee_name: str = Form(...),
    description: str = Form(None),
    price: float = Form(...),
    gst_rate: float = Form(18.0),
    payment_method: str = Form(None),
    payment_status: str = Form("Unpaid"),
    db: Session = Depends(database.get_db)
):
    """Update a service record"""
    try:
        # Get current user from cookie
        from app.main import get_current_user_from_cookie

        user = await get_current_user_from_cookie(request, db)

        # Redirect to login if not authenticated
        if not user:
            return RedirectResponse(url=f"/login?next=/service/{service_id}/edit", status_code=303)

        # Create service data dictionary
        service_data = {
            "date": date,
            "service_name": service_name,
            "employee_name": employee_name,
            "description": description,
            "price": price,
            "gst_rate": gst_rate,
            "payment_method": payment_method,
            "payment_status": payment_status
        }

        # Update service record
        service = crud.update_service(db, service_id, service_data)
        if not service:
            return templates.TemplateResponse(
                "service_form_simple.html",
                {
                    "request": request,
                    "user": user,
                    "service": service_data,
                    "edit_mode": True,
                    "error": "Service not found"
                },
                status_code=404
            )

        # If service has an invoice, update it too
        if service.invoice_id:
            invoice_data = {
                "date": service.date,
                "payment_method": service.payment_method,
                "payment_status": service.payment_status,
                "total_amount": service.price,
                "subtotal": service.price
            }

            # Get invoice by ID
            invoice = db.query(models.Invoice).filter(models.Invoice.id == service.invoice_id).first()
            if invoice:
                # Update invoice attributes
                for key, value in invoice_data.items():
                    if hasattr(invoice, key):
                        setattr(invoice, key, value)

                db.commit()

                # Regenerate PDF
                generate_pdf_invoice(invoice)

        # Redirect to services page with success message
        return RedirectResponse(url="/services?message=Service+updated+successfully", status_code=303)
    except Exception as e:
        print(f"Error updating service: {e}")
        # Return to the form with an error message
        return templates.TemplateResponse(
            "service_form_simple.html",
            {
                "request": request,
                "user": user if 'user' in locals() else None,
                "service": service_data if 'service_data' in locals() else {},
                "edit_mode": True,
                "error": f"Error updating service: {str(e)}"
            },
            status_code=500
        )

@router.post("/api/services/{service_id}/update")
async def api_update_service(
    service_id: int,
    date: str = Form(...),
    service_name: str = Form(...),
    employee_name: str = Form(...),
    description: str = Form(None),
    price: float = Form(...),
    gst_rate: float = Form(18.0),
    payment_method: str = Form(None),
    payment_status: str = Form("Unpaid"),
    db: Session = Depends(database.get_db)
):
    """API endpoint to update a service record"""
    try:
        # Convert date string to date object
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return {"success": False, "message": "Invalid date format"}

        # Create service data dictionary
        service_data = {
            "date": date_obj,
            "service_name": service_name,
            "employee_name": employee_name,
            "description": description,
            "price": price,
            "gst_rate": gst_rate,
            "payment_method": payment_method,
            "payment_status": payment_status
        }

        # Update service record
        service = crud.update_service(db, service_id, service_data)
        if not service:
            return {"success": False, "message": "Service not found"}

        # If service has an invoice, update it too
        if service.invoice_id:
            invoice_data = {
                "date": service.date,
                "payment_method": service.payment_method,
                "payment_status": service.payment_status,
                "total_amount": service.price,
                "subtotal": service.price
            }

            # Get invoice by ID
            invoice = db.query(models.Invoice).filter(models.Invoice.id == service.invoice_id).first()
            if invoice:
                # Update invoice attributes
                for key, value in invoice_data.items():
                    if hasattr(invoice, key):
                        setattr(invoice, key, value)

                db.commit()

                # Regenerate PDF
                generate_pdf_invoice(invoice)

        return {"success": True, "message": "Service updated successfully"}
    except Exception as e:
        print(f"Error updating service via API: {e}")
        return {"success": False, "message": f"Error updating service: {str(e)}"}

@router.get("/service/{service_id}/delete")
async def delete_service(
    request: Request,
    service_id: int,
    db: Session = Depends(database.get_db)
):
    """Delete a service record"""
    # Get current user from cookie
    from app.main import get_current_user_from_cookie

    user = await get_current_user_from_cookie(request, db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url="/login?next=/services", status_code=303)

    # Delete service
    result = crud.delete_service(db, service_id)

    # Redirect to services page with message
    if result:
        return RedirectResponse(url="/services?message=Service+deleted+successfully", status_code=303)
    else:
        return RedirectResponse(url="/services?error=Error+deleting+service", status_code=303)

@router.post("/service/{service_id}/update")
async def update_service(
    service_id: int,
    service_data: dict = Body(...),
    db: Session = Depends(database.get_db)
):
    """Update a service record"""
    try:
        # Get service by ID
        service = crud.get_service(db, service_id)
        if not service:
            return JSONResponse(status_code=404, content={"success": False, "message": "Service not found"})

        # Convert date string to Python date object
        if "date" in service_data and isinstance(service_data["date"], str):
            try:
                from datetime import datetime
                service_data["date"] = datetime.strptime(service_data["date"], "%Y-%m-%d").date()
            except ValueError as e:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": f"Invalid date format: {e}"}
                )

        # Update service record
        updated_service = crud.update_service(db, service_id, service_data)

        # If service has an invoice, update it too
        if updated_service.invoice_id:
            invoice_data = {
                "date": updated_service.date,
                "payment_method": updated_service.payment_method,
                "payment_status": updated_service.payment_status,
                "total_amount": updated_service.price,
                "subtotal": updated_service.price
            }

            # Get invoice by ID
            invoice = db.query(models.Invoice).filter(models.Invoice.id == updated_service.invoice_id).first()
            if invoice:
                # Update invoice attributes
                for key, value in invoice_data.items():
                    if hasattr(invoice, key):
                        setattr(invoice, key, value)

                db.commit()

        return JSONResponse(content={"success": True, "message": "Service updated successfully"})
    except Exception as e:
        print(f"Error updating service: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


@router.delete("/service/{service_id}/delete")
async def delete_service(
    service_id: int,
    db: Session = Depends(database.get_db)
):
    """Delete a service record"""
    try:
        # Get service by ID
        service = crud.get_service(db, service_id)
        if not service:
            return JSONResponse(status_code=404, content={"success": False, "message": "Service not found"})

        # Delete the service
        result = crud.delete_service(db, service_id)
        if result:
            return JSONResponse(content={"success": True, "message": "Service deleted successfully"})
        else:
            return JSONResponse(status_code=500, content={"success": False, "message": "Failed to delete service"})
    except Exception as e:
        print(f"Error deleting service: {e}")
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})


@router.get("/service/{service_id}/generate-invoice")
async def generate_service_invoice(
    request: Request,
    service_id: int,
    db: Session = Depends(database.get_db)
):
    """Generate an invoice for a service record"""
    try:
        # Get current user from cookie
        from app.main import get_current_user_from_cookie

        user = await get_current_user_from_cookie(request, db)

        # Redirect to login if not authenticated
        if not user:
            return RedirectResponse(url="/login?next=/services", status_code=303)

        # Get service by ID
        service = crud.get_service(db, service_id)
        if not service:
            return RedirectResponse(url="/services?error=Service+not+found", status_code=303)

        # Check if service already has an invoice
        if service.invoice_id:
            return RedirectResponse(url=f"/invoice/{service.invoice_id}", status_code=303)

        # Calculate GST amount
        gst_amount = service.price * (service.gst_rate / 100)
        total_amount = service.price + gst_amount

        # Create invoice data
        invoice_data = {
            "invoice_number": f"INV-{service.service_code}",
            "date": service.date,
            "customer_name": "Service Customer",  # Default customer name
            "customer_address": "",
            "customer_phone": "",
            "customer_email": "",
            "customer_gst": "",
            "payment_method": service.payment_method,
            "payment_status": service.payment_status,
            "subtotal": service.price,
            "total_discount": 0,
            "discounted_subtotal": service.price,
            "total_gst": gst_amount,
            "total_amount": total_amount,
            "amount_paid": 0,
            "invoice_type": "service",
            "pdf_path": f"invoices/service-{service.service_code}.pdf",
            "items": [{
                "item_code": service.service_code,
                "item_name": service.service_name,
                "hsn_code": "SAC",  # Service Accounting Code
                "price": service.price,
                "quantity": 1,
                "discount_percent": 0,
                "discount_amount": 0,
                "discounted_subtotal": service.price,
                "gst_rate": service.gst_rate,
                "gst_amount": gst_amount,
                "total": total_amount,
                "item_type": "service"
            }]
        }

        # Create invoice
        invoice = crud.create_invoice(db, invoice_data)

        # Update service with invoice ID
        crud.update_service(db, service.id, {"invoice_id": invoice.id})

        # Generate PDF
        generate_pdf_invoice(invoice)

        # Redirect to invoice page
        return RedirectResponse(url=f"/invoice/{invoice.id}?message=Invoice+generated+successfully", status_code=303)
    except Exception as e:
        print(f"Error generating invoice: {e}")
        return RedirectResponse(url="/services?error=Error+generating+invoice:+{str(e)}", status_code=303)


@router.get("/service/new", response_class=HTMLResponse)
async def get_new_service_page(request: Request, db: Session = Depends(database.get_db)):
    """Render the new service form page"""
    # Get current user from cookie
    from app.main import get_current_user_from_cookie

    user = await get_current_user_from_cookie(request, db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url="/login?next=/service/new", status_code=303)

    return templates.TemplateResponse(
        "service_form_simple.html",
        {
            "request": request,
            "user": user,
            "today": date.today(),
            "edit_mode": False,
            "service": {}
        }
    )


@router.post("/service/new", response_class=HTMLResponse)
async def create_new_service(
    request: Request,
    date: date = Form(...),
    service_name: str = Form(...),
    employee_name: str = Form(...),
    description: str = Form(None),
    price: float = Form(...),
    gst_rate: float = Form(18.0),
    payment_method: str = Form(None),
    payment_status: str = Form("Unpaid"),
    db: Session = Depends(database.get_db),
):
    """Create a new service record"""
    try:
        # Get current user from cookie
        from app.main import get_current_user_from_cookie

        user = await get_current_user_from_cookie(request, db)

        # Redirect to login if not authenticated
        if not user:
            return RedirectResponse(url="/login?next=/service/new", status_code=303)

        # Generate service code
        service_code = f"SRV{str(crud.get_next_service_id(db)).zfill(3)}"

        # Create service data dictionary
        service_data = {
            "date": date,
            "service_code": service_code,
            "service_name": service_name,
            "employee_name": employee_name,
            "description": description,
            "price": price,
            "gst_rate": gst_rate,
            "payment_method": payment_method,
            "payment_status": payment_status
        }

        # Create service record
        service = crud.create_service(db, service_data)

        # Redirect to services page with success message
        return RedirectResponse(url="/services?message=Service+created+successfully", status_code=303)
    except Exception as e:
        print(f"Error creating service: {e}")

        # Return to the form with an error message
        return templates.TemplateResponse(
            "service_form_simple.html",
            {
                "request": request,
                "user": user if 'user' in locals() else None,
                "today": date.today(),
                "edit_mode": False,
                "service": {
                    "service_name": service_name if 'service_name' in locals() else "",
                    "employee_name": employee_name if 'employee_name' in locals() else "",
                    "description": description if 'description' in locals() else "",
                    "price": price if 'price' in locals() else 0,
                    "gst_rate": gst_rate if 'gst_rate' in locals() else 18.0
                },
                "error": f"Error creating service: {str(e)}"
            },
            status_code=500
        )




