from fastapi import APIRouter, Form, Depends, Request, Body, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import crud, database, models
from app.core.auth import get_current_user_from_cookie
from datetime import date, datetime
from pydantic import BaseModel
import pandas as pd
import os
import tempfile
from typing import List, Optional


class ExpenseUpdate(BaseModel):
    date: str
    expense_type: str
    vendor_name: str
    vendor_gst: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_phone: Optional[str] = None
    description: Optional[str] = None
    amount: float
    gst_rate: float
    payment_method: str
    payment_status: str
    category: Optional[str] = None
    notes: Optional[str] = None


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/expenses", response_class=HTMLResponse)
async def expenses_page(
    request: Request,
    expense_type: Optional[str] = None,
    category: Optional[str] = None,
    payment_status: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """Expenses management page"""
    # Get current user from cookie
    user = await get_current_user_from_cookie(request, db=db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url="/login?next=/expenses", status_code=303)

    # Get all expenses from database
    expenses = crud.get_all_expenses(db, limit=1000)

    # Apply filters if provided
    if expense_type and expense_type != "all":
        expenses = [exp for exp in expenses if exp.expense_type == expense_type]

    if category and category != "all":
        expenses = [exp for exp in expenses if exp.category == category]

    if payment_status and payment_status != "all":
        expenses = [exp for exp in expenses if exp.payment_status == payment_status]

    # Get expense statistics
    expense_stats = crud.get_expense_stats(db)

    # Get unique expense types and categories for filters
    all_expenses = crud.get_all_expenses(db, limit=10000)
    expense_types = list(set([exp.expense_type for exp in all_expenses if exp.expense_type]))
    categories = list(set([exp.category for exp in all_expenses if exp.category]))

    return templates.TemplateResponse(
        "expenses.html",
        {
            "request": request,
            "user": user,
            "expenses": expenses,
            "expense_stats": expense_stats,
            "expense_types": expense_types,
            "categories": categories,
            "current_expense_type": expense_type or "all",
            "current_category": category or "all",
            "current_payment_status": payment_status or "all",
            "today": datetime.now().date()
        }
    )


@router.get("/expense/{expense_id}", response_class=HTMLResponse)
async def expense_details_page(
    expense_id: int,
    request: Request,
    db: Session = Depends(database.get_db)
):
    """Expense details page"""
    # Get current user from cookie
    user = await get_current_user_from_cookie(request, db=db)

    # Redirect to login if not authenticated
    if not user:
        return RedirectResponse(url="/login?next=/expense/" + str(expense_id), status_code=303)

    # Get expense details with payments
    expense = crud.get_expense_with_payments(db, expense_id)
    if not expense:
        return RedirectResponse(url="/expenses", status_code=303)

    # Get payment history
    payments = crud.get_expense_payments(db, expense_id)

    return templates.TemplateResponse(
        "expense_details.html",
        {
            "request": request,
            "user": user,
            "expense": expense,
            "payments": payments
        }
    )


@router.get("/api/expenses/export-excel")
async def export_expenses_excel(
    request: Request,
    expense_type: Optional[str] = None,
    payment_status: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """Export expenses to CSV file"""
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db=db)

        if not user:
            return JSONResponse(status_code=401, content={"success": False, "message": "Authentication required"})

        # Get all expenses
        expenses = crud.get_all_expenses(db, limit=10000)

        # Apply filters if provided
        if expense_type and expense_type != "all":
            expenses = [exp for exp in expenses if exp.expense_type == expense_type]

        if payment_status and payment_status != "all":
            expenses = [exp for exp in expenses if exp.payment_status == payment_status]

        # Create CSV content
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Expense Code", "Date", "Expense Type", "Name", "GST Number",
            "Description", "Amount", "GST Rate (%)", "GST Amount", "Total Amount",
            "Payment Method", "Payment Status"
        ])

        # Write data
        for expense in expenses:
            writer.writerow([
                expense.expense_code,
                expense.date.strftime("%Y-%m-%d"),
                expense.expense_type,
                expense.vendor_name,
                expense.vendor_gst or "",
                expense.description or "",
                expense.amount,
                expense.gst_rate,
                expense.gst_amount,
                expense.total_amount,
                expense.payment_method,
                expense.payment_status
            ])

        # Generate filename
        filter_suffix = ""
        if expense_type and expense_type != "all":
            filter_suffix += f"_{expense_type}"
        if payment_status and payment_status != "all":
            filter_suffix += f"_{payment_status}"

        filename = f"expenses_export{filter_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Create response
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print(f"Error exporting expenses to CSV: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/api/expenses/create")
async def create_expense_api(
    request: Request,
    date: date = Form(...),
    expense_type: str = Form(...),
    vendor_name: str = Form(...),
    vendor_gst: str = Form(""),
    description: str = Form(""),
    amount: float = Form(...),
    gst_rate: float = Form(0.0),
    amount_paid: float = Form(0.0),
    payment_method: str = Form(...),
    payment_status: str = Form("Paid"),
    db: Session = Depends(database.get_db)
):
    """Create a new expense record"""
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db=db)

        # Redirect to login if not authenticated
        if not user:
            return JSONResponse(status_code=401, content={"success": False, "message": "Authentication required"})

        # Create expense data dictionary
        expense_data = {
            "date": date,
            "expense_type": expense_type,
            "vendor_name": vendor_name,
            "vendor_gst": vendor_gst,
            "description": description,
            "amount": amount,
            "gst_rate": gst_rate,
            "amount_paid": amount_paid,
            "payment_method": payment_method,
            "payment_status": payment_status
        }

        # Create expense record
        expense = crud.create_expense(db, expense_data)

        return JSONResponse(content={
            "success": True,
            "message": "Expense created successfully",
            "expense_code": expense.expense_code
        })
    except Exception as e:
        print(f"Error creating expense: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


@router.get("/api/expenses/{expense_id}")
async def get_expense_api(
    expense_id: int,
    request: Request,
    db: Session = Depends(database.get_db)
):
    """Get a specific expense by ID"""
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db=db)

        if not user:
            return JSONResponse(status_code=401, content={"success": False, "message": "Authentication required"})

        # Get expense
        expense = crud.get_expense(db, expense_id)
        if not expense:
            return JSONResponse(status_code=404, content={"success": False, "message": "Expense not found"})

        # Return expense data
        return {
            "id": expense.id,
            "expense_code": expense.expense_code,
            "date": expense.date.strftime("%Y-%m-%d"),
            "expense_type": expense.expense_type,
            "vendor_name": expense.vendor_name,
            "vendor_gst": expense.vendor_gst,
            "description": expense.description,
            "amount": expense.amount,
            "gst_rate": expense.gst_rate,
            "gst_amount": expense.gst_amount,
            "total_amount": expense.total_amount,
            "payment_method": expense.payment_method,
            "payment_status": expense.payment_status
        }
    except Exception as e:
        print(f"Error getting expense: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


@router.post("/api/expenses/{expense_id}/update")
async def update_expense_api(
    expense_id: int,
    request: Request,
    date: str = Form(...),
    expense_type: str = Form(...),
    vendor_name: str = Form(...),
    vendor_gst: str = Form(""),
    description: str = Form(""),
    amount: float = Form(...),
    gst_rate: float = Form(0.0),
    amount_paid: float = Form(0.0),
    payment_method: str = Form(...),
    payment_status: str = Form("Paid"),
    db: Session = Depends(database.get_db)
):
    """Update an expense record"""
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db=db)

        if not user:
            return JSONResponse(status_code=401, content={"success": False, "message": "Authentication required"})

        # Convert date string to date object
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return JSONResponse(status_code=400, content={"success": False, "message": "Invalid date format"})

        # Create update data
        expense_data = {
            "date": date_obj,
            "expense_type": expense_type,
            "vendor_name": vendor_name,
            "vendor_gst": vendor_gst,
            "description": description,
            "amount": amount,
            "gst_rate": gst_rate,
            "amount_paid": amount_paid,
            "payment_method": payment_method,
            "payment_status": payment_status
        }

        # Update expense
        expense = crud.update_expense(db, expense_id, expense_data)
        if not expense:
            return JSONResponse(status_code=404, content={"success": False, "message": "Expense not found"})

        return JSONResponse(content={"success": True, "message": "Expense updated successfully"})
    except Exception as e:
        print(f"Error updating expense: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


@router.delete("/api/expenses/{expense_id}")
async def delete_expense_api(
    expense_id: int,
    request: Request,
    db: Session = Depends(database.get_db)
):
    """Delete an expense record"""
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db=db)

        if not user:
            return JSONResponse(status_code=401, content={"success": False, "message": "Authentication required"})

        # Delete expense
        result = crud.delete_expense(db, expense_id)
        if not result:
            return JSONResponse(status_code=404, content={"success": False, "message": "Expense not found"})

        return JSONResponse(content={"success": True, "message": "Expense deleted successfully"})
    except Exception as e:
        print(f"Error deleting expense: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


@router.get("/api/expenses/search")
async def search_expenses_api(
    query: str,
    request: Request,
    db: Session = Depends(database.get_db)
):
    """Search expenses"""
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db=db)

        if not user:
            return JSONResponse(status_code=401, content={"success": False, "message": "Authentication required"})

        # Search expenses
        expenses = crud.search_expenses(db, query)

        # Convert to list of dictionaries
        expenses_list = []
        for expense in expenses:
            expenses_list.append({
                "id": expense.id,
                "expense_code": expense.expense_code,
                "date": expense.date.strftime("%Y-%m-%d"),
                "expense_type": expense.expense_type,
                "vendor_name": expense.vendor_name,
                "description": expense.description,
                "amount": expense.amount,
                "gst_rate": expense.gst_rate,
                "total_amount": expense.total_amount,
                "payment_method": expense.payment_method,
                "payment_status": expense.payment_status
            })

        return {"expenses": expenses_list}
    except Exception as e:
        print(f"Error searching expenses: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


@router.post("/expense/{expense_id}/payment", response_class=JSONResponse)
async def add_expense_payment(
    request: Request,
    expense_id: int,
    db: Session = Depends(database.get_db)
):
    """Add a payment to an expense record"""
    try:
        # Get current user from cookie
        user = await get_current_user_from_cookie(request, db=db)

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
            import json
            body = json.loads(body_str)
        except json.JSONDecodeError as e:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"Invalid JSON: {str(e)}"}
            )

        # Validate required fields
        if "amount" not in body or "payment_method" not in body:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Amount and payment method are required"}
            )

        # Parse payment date
        payment_date = datetime.now()
        if "payment_date" in body and body["payment_date"]:
            try:
                payment_date = datetime.fromisoformat(body["payment_date"].replace('Z', '+00:00'))
            except ValueError:
                # If parsing fails, use current datetime
                payment_date = datetime.now()

        # Create payment data
        payment_data = {
            "amount": float(body["amount"]),
            "payment_method": body["payment_method"],
            "notes": body.get("notes", ""),
            "payment_date": payment_date
        }

        # Add payment
        payment = crud.add_expense_payment(db, expense_id, payment_data)
        if not payment:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Expense not found"}
            )

        # Get updated expense
        expense = crud.get_expense_with_payments(db, expense_id)

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
                "expense": {
                    "amount_paid": expense.amount_paid,
                    "payment_status": expense.payment_status,
                    "total_amount": expense.total_amount,
                    "remaining_amount": expense.remaining_amount
                }
            }
        )
    except Exception as e:
        print(f"Error adding payment to expense: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error adding payment: {str(e)}"}
        )


