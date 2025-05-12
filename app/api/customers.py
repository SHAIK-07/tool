from fastapi import APIRouter, Depends, Form, Request, Body, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, date
import json
import os
import traceback
from sqlalchemy import or_

from app.db import crud, database, models
from app.schemas import customer as customer_schemas
from app.core.auth import get_current_user_from_cookie
from app.core.pdf_generator import generate_pdf_customer_details



router = APIRouter(tags=["Customers"])
templates = Jinja2Templates(directory="templates")


@router.get("/customers", response_class=HTMLResponse)
async def get_customers_page(
    request: Request,
    message: str = None,
    error: str = None,
    page: int = 1,
    limit: int = 50,
    search: str = None,
    status: str = None,
    db: Session = Depends(database.get_db)
):
    """Display the customers page with a list of all customers and the form to add new customers"""
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db)

        # Redirect to login if not authenticated
        if not user:
            return RedirectResponse(url="/login?next=/customers", status_code=303)

        # Calculate offset based on page and limit
        offset = (page - 1) * limit

        # Build query with filters
        query = db.query(models.Customer)

        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    models.Customer.customer_name.ilike(search_term),
                    models.Customer.phone_no.ilike(search_term),
                    models.Customer.customer_code.ilike(search_term)
                )
            )

        # Apply status filter if provided
        if status and status != "all":
            query = query.filter(models.Customer.payment_status == status)

        # Get total count for pagination
        total_customers = query.count()

        # Apply pagination
        customers = query.order_by(models.Customer.date.desc()).offset(offset).limit(limit).all()

        # Convert to dictionary format
        customers_list = []
        for customer in customers:
            customers_list.append({
                "id": customer.id,
                "customer_code": customer.customer_code,
                "date": customer.date,
                "customer_name": customer.customer_name,
                "phone_no": customer.phone_no,
                "address": customer.address,
                "product_description": customer.product_description,
                "payment_method": customer.payment_method,
                "payment_status": customer.payment_status,
                "total_amount": customer.total_amount,
                "amount_paid": customer.amount_paid
            })

        # Calculate pagination values
        total_pages = (total_customers + limit - 1) // limit  # Ceiling division
        if total_pages == 0:
            total_pages = 1  # At least one page even if empty

        # Get today's date for the form
        today = datetime.now().date().isoformat()

        return templates.TemplateResponse(
            "customers.html",
            {
                "request": request,
                "customers": customers_list,
                "message": message,
                "error": error,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "total_customers": total_customers,
                "today": today,
                "user": user,
                "search_query": search or "",
                "current_status": status or "all"
            }
        )
    except Exception as e:
        print(f"Error displaying customers page: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse(
            "customers.html",
            {
                "request": request,
                "error": f"Error loading customers: {str(e)}",
                "customers": [],
                "page": 1,
                "limit": limit,
                "total_pages": 1,
                "total_customers": 0,
                "today": datetime.now().date().isoformat(),
                "user": user if 'user' in locals() else None,
                "search_query": search or "",
                "current_status": status or "all"
            }
        )


@router.post("/customer/new", response_class=HTMLResponse)
async def create_new_customer(
    request: Request,
    date: str = Form(...),
    customer_name: str = Form(...),
    phone_no: str = Form(...),
    address: str = Form(None),
    product_description: str = Form(None),
    payment_method: str = Form(None),
    payment_status: str = Form("Unpaid"),
    total_amount: float = Form(...),
    amount_paid: float = Form(0.0),
    db: Session = Depends(database.get_db),
):
    """Create a new customer record"""
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db)

        # Redirect to login if not authenticated
        if not user:
            return RedirectResponse(url="/login?next=/customers", status_code=303)

        # Validate customer name
        if not customer_name or len(customer_name.strip()) == 0:
            return RedirectResponse(url="/customers?error=Customer+name+is+required", status_code=303)

        # Validate phone number
        if not phone_no or len(phone_no.strip()) == 0:
            return RedirectResponse(url="/customers?error=Phone+number+is+required", status_code=303)

        # Parse date
        try:
            customer_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return RedirectResponse(url="/customers?error=Invalid+date+format.+Please+use+YYYY-MM-DD", status_code=303)

        # Parse numeric values
        try:
            total_amount_value = float(total_amount)
            if total_amount_value <= 0:
                return RedirectResponse(url="/customers?error=Total+amount+must+be+greater+than+zero", status_code=303)
        except ValueError:
            return RedirectResponse(url="/customers?error=Invalid+total+amount+value", status_code=303)

        try:
            amount_paid_value = float(amount_paid)
            if amount_paid_value < 0:
                return RedirectResponse(url="/customers?error=Amount+paid+cannot+be+negative", status_code=303)
            if amount_paid_value > total_amount_value:
                amount_paid_value = total_amount_value  # Auto-correct amount paid
        except ValueError:
            return RedirectResponse(url="/customers?error=Invalid+amount+paid+value", status_code=303)

        # Set payment status based on amount paid
        if amount_paid_value >= total_amount_value:
            payment_status = "Fully Paid"
        elif amount_paid_value > 0:
            payment_status = "Partially Paid"
        else:
            payment_status = "Unpaid"

        # Create customer data dictionary
        customer_data = {
            "date": customer_date,
            "customer_name": customer_name,
            "phone_no": phone_no,
            "address": address,
            "product_description": product_description,
            "payment_method": payment_method,
            "payment_status": payment_status,
            "total_amount": total_amount_value,
            "amount_paid": amount_paid_value
        }

        # Create customer record
        customer = crud.create_customer(db, customer_data)

        # Redirect to customers page with success message
        return RedirectResponse(url="/customers?message=Customer+created+successfully", status_code=303)
    except Exception as e:
        print(f"Error creating customer: {e}")
        import traceback
        traceback.print_exc()

        # Provide a more user-friendly error message
        error_message = str(e)
        if "UNIQUE constraint failed" in error_message and "customer_code" in error_message:
            error_message = "A customer with this code already exists. Please try again."
        elif "not a valid date" in error_message.lower():
            error_message = "Invalid date format. Please use YYYY-MM-DD."

        return RedirectResponse(url=f"/customers?error=Error+creating+customer:+{error_message}", status_code=303)


@router.get("/customer/{customer_id}", response_class=HTMLResponse)
async def get_customer_details_page(
    request: Request,
    customer_id: int,
    message: str = None,
    error: str = None,
    db: Session = Depends(database.get_db)
):
    """Display the customer details page"""
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db)

        # Redirect to login if not authenticated
        if not user:
            return RedirectResponse(url=f"/login?next=/customer/{customer_id}", status_code=303)

        # Get customer details
        customer = crud.get_customer(db, customer_id)
        if not customer:
            return RedirectResponse(url="/customers?error=Customer+not+found", status_code=303)

        # Get customer payments
        payments = crud.get_customer_payments(db, customer_id)

        return templates.TemplateResponse(
            "customer_details.html",
            {
                "request": request,
                "customer": customer,
                "payments": payments,
                "message": message,
                "error": error,
                "user": user
            }
        )
    except Exception as e:
        print(f"Error displaying customer details: {e}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(url=f"/customers?error=Error+loading+customer+details:+{str(e)}", status_code=303)


@router.post("/customer/{customer_id}/update", response_class=JSONResponse)
async def update_customer(
    request: Request,
    customer_id: int,
    db: Session = Depends(database.get_db)
):
    """Update a customer record"""
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db)

        # Check if user is authenticated
        if not user:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Authentication required"}
            )

        # Get request body as raw data
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        print(f"Raw request body: {body_str}")

        # Parse JSON
        try:
            body = json.loads(body_str)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"Invalid JSON: {str(e)}"}
            )

        print(f"Parsed body: {body}")

        # Create a clean update dictionary with only the fields we need
        update_data = {}

        # Handle date field
        if "date" in body and body["date"]:
            try:
                update_data["date"] = datetime.strptime(body["date"], "%Y-%m-%d").date()
            except ValueError:
                return JSONResponse(
                    status_code=422,
                    content={"success": False, "message": "Invalid date format. Use YYYY-MM-DD"}
                )

        # Copy string fields directly
        for field in ["customer_name", "phone_no", "address", "product_description", "payment_method", "payment_status"]:
            if field in body:
                update_data[field] = body[field]

        # Handle numeric fields
        if "total_amount" in body:
            try:
                update_data["total_amount"] = float(body["total_amount"])
            except (ValueError, TypeError):
                return JSONResponse(
                    status_code=422,
                    content={"success": False, "message": "Invalid total_amount value"}
                )

        if "amount_paid" in body:
            try:
                update_data["amount_paid"] = float(body["amount_paid"])
            except (ValueError, TypeError):
                return JSONResponse(
                    status_code=422,
                    content={"success": False, "message": "Invalid amount_paid value"}
                )

        print(f"Processed update data: {update_data}")

        # Update customer
        updated_customer = crud.update_customer(db, customer_id, update_data)
        if not updated_customer:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Customer not found"}
            )

        return JSONResponse(
            content={"success": True, "message": "Customer updated successfully"}
        )
    except Exception as e:
        print(f"Error updating customer: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error updating customer: {str(e)}"}
        )


@router.post("/customer/{customer_id}/payment", response_class=JSONResponse)
async def add_payment(
    request: Request,
    customer_id: int,
    payment_data: customer_schemas.CustomerPaymentCreate,
    db: Session = Depends(database.get_db)
):
    """Add a payment to a customer record"""
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db)

        # Check if user is authenticated
        if not user:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Authentication required"}
            )

        # Add payment
        payment = crud.add_customer_payment(db, customer_id, payment_data.dict())
        if not payment:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Customer not found"}
            )

        # Get updated customer
        customer = crud.get_customer(db, customer_id)

        return JSONResponse(
            content={
                "success": True,
                "message": "Payment added successfully",
                "payment": {
                    "id": payment.id,
                    "amount": payment.amount,
                    "payment_method": payment.payment_method,
                    "payment_date": payment.payment_date.isoformat(),
                    "notes": payment.notes
                },
                "customer": {
                    "amount_paid": customer.amount_paid,
                    "payment_status": customer.payment_status,
                    "total_amount": customer.total_amount,
                    "remaining_amount": customer.total_amount - customer.amount_paid
                }
            }
        )
    except Exception as e:
        print(f"Error adding payment: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error adding payment: {str(e)}"}
        )


@router.get("/api/customers/export-excel")
async def export_customers_excel(
    search: str = None,
    status: str = None,
    db: Session = Depends(database.get_db)
):
    """Export customers to Excel file"""
    try:
        # Get all customers from database
        customers = crud.get_all_customers(db)

        # Filter by search query if provided
        if search:
            search = search.lower()
            customers = [c for c in customers if (
                search in c.customer_name.lower() or
                search in c.phone_no.lower() or
                search in c.customer_code.lower()
            )]

        # Filter by payment status if provided
        if status and status != "all":
            customers = [c for c in customers if c.payment_status == status]

        # Use the excel_generator module to create the Excel file
        from app.core.excel_generator import export_customers_to_excel
        filename, file_path = export_customers_to_excel(customers, status)

        # Return the Excel file
        from fastapi.responses import FileResponse
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename
        )
    except Exception as e:
        print(f"Error exporting customers to Excel: {e}")
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.delete("/api/customers/{customer_id}")
async def delete_customer_api(
    customer_id: int,
    db: Session = Depends(database.get_db)
):
    """Delete a customer record via API"""
    try:
        # Get the customer
        customer = crud.get_customer(db, customer_id)

        if not customer:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Customer not found"}
            )

        # Use the crud function to delete the customer
        result = crud.delete_customer(db, customer_id)

        if result:
            return JSONResponse(
                content={"success": True, "message": "Customer deleted successfully"}
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Failed to delete customer"}
            )
    except Exception as e:
        print(f"Error deleting customer: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error deleting customer: {str(e)}"}
        )


@router.post("/customer/{customer_id}/delete")
async def delete_customer_post(
    request: Request,
    customer_id: int,
    db: Session = Depends(database.get_db)
):
    """Delete a customer record via POST request"""
    try:
        print(f"Received POST request to delete customer ID: {customer_id}")

        # Get the customer
        customer = crud.get_customer(db, customer_id)

        if not customer:
            print(f"Customer ID {customer_id} not found")
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Customer not found"}
            )

        print(f"Found customer: {customer.customer_name} (ID: {customer_id})")

        # Use the crud function to delete the customer
        result = crud.delete_customer(db, customer_id)

        if result:
            print(f"Successfully deleted customer ID: {customer_id}")
            return JSONResponse(
                content={"success": True, "message": "Customer deleted successfully"}
            )
        else:
            print(f"Failed to delete customer ID: {customer_id}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Failed to delete customer"}
            )
    except Exception as e:
        print(f"Error deleting customer: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error deleting customer: {str(e)}"}
        )




from app.core.pdf_generator import generate_pdf_customer_details

# Add these new endpoints

@router.get("/customer-pdf/{customer_id}")
async def view_customer_pdf(
    customer_id: int,
    db: Session = Depends(database.get_db)
):
    """View a customer details PDF in the browser"""
    try:
        # Get customer from database
        customer = crud.get_customer(db, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Get customer payments
        payments = crud.get_customer_payments(db, customer_id)

        # Convert customer model to dictionary
        customer_data = {
            "id": customer.id,
            "customer_code": customer.customer_code,
            "date": customer.date,
            "customer_name": customer.customer_name,
            "phone_no": customer.phone_no,
            "address": customer.address,
            "product_description": customer.product_description,
            "payment_method": customer.payment_method,
            "payment_status": customer.payment_status,
            "total_amount": customer.total_amount,
            "amount_paid": customer.amount_paid,
            "created_at": customer.created_at,
            "updated_at": customer.updated_at
        }

        # Add payments to customer data
        customer_data["payments"] = payments

        # Set PDF path
        pdf_path = f"customers/{customer_id}.pdf"

        # Always regenerate the PDF to ensure it has the latest data
        print(f"Generating PDF for customer {customer_id}")
        pdf_path = generate_pdf_customer_details(customer_data)

        # Check if PDF exists and has valid size
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="Customer PDF could not be generated")
        elif os.path.getsize(pdf_path) < 1000:
            raise HTTPException(status_code=500, detail="Generated PDF file is too small and may be corrupted")

        # Serve the file for viewing in the browser (inline)
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"Customer_{customer_id}.pdf",
            headers={"Content-Disposition": f"inline; filename=Customer_{customer_id}.pdf"}
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error viewing customer PDF: {e}")
        print(f"Error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error viewing PDF: {str(e)}")


@router.get("/download-customer-pdf/{customer_id}")
async def download_customer_pdf(
    customer_id: int,
    db: Session = Depends(database.get_db)
):
    """Download a customer details PDF"""
    try:
        # Get customer from database
        customer = crud.get_customer(db, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Get customer payments
        payments = crud.get_customer_payments(db, customer_id)

        # Convert customer model to dictionary
        customer_data = {
            "id": customer.id,
            "customer_code": customer.customer_code,
            "date": customer.date,
            "customer_name": customer.customer_name,
            "phone_no": customer.phone_no,
            "address": customer.address,
            "product_description": customer.product_description,
            "payment_method": customer.payment_method,
            "payment_status": customer.payment_status,
            "total_amount": customer.total_amount,
            "amount_paid": customer.amount_paid,
            "created_at": customer.created_at,
            "updated_at": customer.updated_at
        }

        # Add payments to customer data
        customer_data["payments"] = payments

        # Set PDF path
        pdf_path = f"customers/{customer_id}.pdf"

        # Always regenerate the PDF to ensure it has the latest data
        print(f"Generating PDF for customer {customer_id}")
        pdf_path = generate_pdf_customer_details(customer_data)

        # Check if PDF exists and has valid size
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="Customer PDF could not be generated")
        elif os.path.getsize(pdf_path) < 1000:
            raise HTTPException(status_code=500, detail="Generated PDF file is too small and may be corrupted")

        # Serve the file for download (attachment)
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"Customer_{customer_id}.pdf",
            headers={"Content-Disposition": f"attachment; filename=Customer_{customer_id}.pdf"}
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error downloading customer PDF: {e}")
        print(f"Error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error downloading PDF: {str(e)}")


@router.post("/customers/{customer_id}/update-payment", response_class=JSONResponse)
async def update_customer_payment(
    request: Request,
    customer_id: int,
    db: Session = Depends(database.get_db)
):
    """Update customer payment details"""
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db)

        # Check if user is authenticated
        if not user:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Authentication required"}
            )

        # Get request body
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        
        try:
            body = json.loads(body_str)
        except json.JSONDecodeError as e:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"Invalid JSON: {str(e)}"}
            )

        # Create update data dictionary
        update_data = {}
        
        # Handle numeric fields
        if "total_amount" in body:
            try:
                update_data["total_amount"] = float(body["total_amount"])
                if update_data["total_amount"] < 0:
                    return JSONResponse(
                        status_code=422,
                        content={"success": False, "message": "Total amount cannot be negative"}
                    )
            except (ValueError, TypeError):
                return JSONResponse(
                    status_code=422,
                    content={"success": False, "message": "Invalid total amount value"}
                )

        if "amount_paid" in body:
            try:
                update_data["amount_paid"] = float(body["amount_paid"])
                if update_data["amount_paid"] < 0:
                    return JSONResponse(
                        status_code=422,
                        content={"success": False, "message": "Amount paid cannot be negative"}
                    )
            except (ValueError, TypeError):
                return JSONResponse(
                    status_code=422,
                    content={"success": False, "message": "Invalid amount paid value"}
                )

        # Handle payment status
        if "payment_status" in body:
            update_data["payment_status"] = body["payment_status"]
            
        # Validate payment status based on amounts if both are provided
        if "total_amount" in update_data and "amount_paid" in update_data:
            total = update_data["total_amount"]
            paid = update_data["amount_paid"]
            
            # Auto-correct amount paid if it exceeds total
            if paid > total:
                update_data["amount_paid"] = total
                paid = total
                
            # Set payment status based on amount paid
            if paid <= 0:
                update_data["payment_status"] = "Unpaid"
            elif paid >= total:
                update_data["payment_status"] = "Fully Paid"
            else:
                update_data["payment_status"] = "Partially Paid"

        # Update customer
        updated_customer = crud.update_customer(db, customer_id, update_data)
        if not updated_customer:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Customer not found"}
            )

        return JSONResponse(
            content={
                "success": True, 
                "message": "Payment details updated successfully",
                "customer": {
                    "id": updated_customer.id,
                    "total_amount": updated_customer.total_amount,
                    "amount_paid": updated_customer.amount_paid,
                    "payment_status": updated_customer.payment_status
                }
            }
        )
    except Exception as e:
        print(f"Error updating customer payment: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error updating payment: {str(e)}"}
        )




