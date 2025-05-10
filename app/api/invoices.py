from fastapi import APIRouter, Depends, Form, Request, Body, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import os
import json

from app.db import crud, database, models
from app.core.pdf_generator import generate_pdf_invoice
from app.schemas.invoice import InvoiceCreate, Invoice, PaymentCreate

router = APIRouter(tags=["Invoices"])
templates = Jinja2Templates(directory="templates")


@router.get("/invoices", response_class=HTMLResponse)
async def invoices_page(
    request: Request,
    payment_status: Optional[str] = None,
    invoice_type: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """Get invoices page with optional filtering"""
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
            "invoices": invoices,
            "current_payment_status": payment_status or "all",
            "current_invoice_type": invoice_type or "all"
        }
    )


@router.get("/invoice/{invoice_id}", response_class=HTMLResponse)
async def invoice_page(request: Request, invoice_id: str, db: Session = Depends(database.get_db)):
    """Get a single invoice page"""
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

    return templates.TemplateResponse("invoice.html", {"request": request, "invoice": invoice})


@router.get("/invoices/export-excel")
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


@router.post("/invoices/payment/{invoice_id}")
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


@router.delete("/invoices/delete/{invoice_id}")
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


@router.get("/invoices/view/{invoice_id}")
async def view_invoice_pdf(invoice_id: str, db: Session = Depends(database.get_db)):
    """View an invoice PDF in the browser"""
    try:
        # Get invoice from database
        invoice = crud.get_invoice(db, invoice_id)
        if not invoice:
            return JSONResponse(status_code=404, content={"error": "Invoice not found"})

        # Get PDF path
        pdf_path = invoice.get("pdf_path", f"invoices/{invoice_id}.pdf")

        # Check if PDF exists and has valid size
        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) < 1000:
            print(f"PDF file missing or too small: {pdf_path}")

            # Generate the PDF
            print(f"Generating PDF for invoice {invoice_id}")
            pdf_path = generate_pdf_invoice(invoice)

            # Check again if PDF exists and has valid size
            if not os.path.exists(pdf_path):
                return JSONResponse(status_code=404, content={"error": "Invoice PDF not found and could not be generated"})
            elif os.path.getsize(pdf_path) < 1000:
                return JSONResponse(status_code=500, content={"error": "Generated PDF file is too small and may be corrupted"})

        # Serve the file for viewing in the browser (inline)
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"Invoice_{invoice_id}.pdf",
            headers={"Content-Disposition": f"inline; filename=Invoice_{invoice_id}.pdf"}
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error viewing PDF: {e}")
        print(f"Error details: {error_details}")
        return JSONResponse(status_code=500, content={"error": f"Error viewing PDF: {str(e)}", "details": error_details})


@router.get("/invoices/download/{invoice_id}")
async def download_invoice_pdf(invoice_id: str, db: Session = Depends(database.get_db)):
    """Download an invoice PDF to the user's device"""
    try:
        # Get invoice from database
        invoice = crud.get_invoice(db, invoice_id)
        if not invoice:
            return JSONResponse(status_code=404, content={"error": "Invoice not found"})

        # Get PDF path
        pdf_path = invoice.get("pdf_path", f"invoices/{invoice_id}.pdf")

        # Check if PDF exists and has valid size
        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) < 1000:
            print(f"PDF file missing or too small: {pdf_path}")

            # Generate the PDF
            print(f"Generating PDF for invoice {invoice_id}")
            pdf_path = generate_pdf_invoice(invoice)

            # Check again if PDF exists and has valid size
            if not os.path.exists(pdf_path):
                return JSONResponse(status_code=404, content={"error": "Invoice PDF not found and could not be generated"})
            elif os.path.getsize(pdf_path) < 1000:
                return JSONResponse(status_code=500, content={"error": "Generated PDF file is too small and may be corrupted"})

        # Serve the file for download (attachment)
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"Invoice_{invoice_id}.pdf",
            headers={"Content-Disposition": f"attachment; filename=Invoice_{invoice_id}.pdf"}
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error downloading PDF: {e}")
        print(f"Error details: {error_details}")
        return JSONResponse(status_code=500, content={"error": f"Error downloading PDF: {str(e)}", "details": error_details})


@router.post("/invoices/update/{invoice_id}")
async def update_invoice_api(
    invoice_id: str,
    invoice_data: dict = Body(...),
    db: Session = Depends(database.get_db)
):
    """Update an invoice"""
    try:
        # Get invoice from database
        invoice_obj = db.query(models.Invoice).filter(models.Invoice.invoice_number == invoice_id).first()
        if not invoice_obj:
            return JSONResponse(status_code=404, content={"success": False, "message": "Invoice not found"})

        # Convert date string to Python date object
        if "date" in invoice_data and isinstance(invoice_data["date"], str):
            try:
                from datetime import datetime
                invoice_data["date"] = datetime.strptime(invoice_data["date"], "%Y-%m-%d").date()
            except ValueError as e:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": f"Invalid date format: {e}"}
                )
        
        # Update invoice attributes
        for key, value in invoice_data.items():
            if hasattr(invoice_obj, key):
                setattr(invoice_obj, key, value)
        
        db.commit()
        
        # Regenerate PDF with updated information
        invoice = crud.get_invoice(db, invoice_id)
        generate_pdf_invoice(invoice)
        
        return JSONResponse(content={"success": True, "message": "Invoice updated successfully"})
    except Exception as e:
        print(f"Error updating invoice: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )
