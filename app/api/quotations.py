from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.db.database import get_db
from app.db import models
from app.core.auth import get_current_user_from_cookie

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Create quotations directory if it doesn't exist
os.makedirs("quotations", exist_ok=True)


@router.get("/quotations")
async def get_quotations(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all quotations."""
    # Get current user from cookie
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login?next=/quotations", status_code=303)

    # Get all quotations from database
    quotations = db.query(models.Quotation).order_by(models.Quotation.created_at.desc()).all()

    return templates.TemplateResponse(
        "quotations.html",
        {"request": request, "quotations": quotations, "user": current_user}
    )


@router.get("/quotation/{quote_id}")
async def get_quotation(
    request: Request,
    quote_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific quotation."""
    try:
        # Get current user from cookie
        current_user = await get_current_user_from_cookie(request, db)
        if not current_user:
            return RedirectResponse(url=f"/login?next=/quotation/{quote_id}", status_code=303)

        # Get quotation from database
        quotation = db.query(models.Quotation).filter(models.Quotation.id == quote_id).first()
        if not quotation:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error_message": "Quotation not found", "user": current_user},
                status_code=404
            )

        # Get quotation items
        items = db.query(models.QuotationItem).filter(models.QuotationItem.quotation_id == quote_id).all()

        # Calculate the valid until date (30 days from issue)
        from datetime import timedelta

        return templates.TemplateResponse(
            "quotation_details.html",
            {
                "request": request,
                "quotation": quotation,
                "items": items,
                "user": current_user,
                "timedelta": timedelta  # Pass timedelta to the template
            }
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error viewing quotation: {e}")
        print(f"Error details: {error_details}")

        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": f"Error viewing quotation: {str(e)}",
                "user": current_user if 'current_user' in locals() else None
            },
            status_code=500
        )


@router.get("/quote-cart")
async def quote_cart_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """Render the quote cart page."""
    # Get current user from cookie
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login?next=/quote-cart", status_code=303)

    return templates.TemplateResponse(
        "quote_cart.html",
        {"request": request, "user": current_user}
    )

@router.get("/quote-checkout")
async def quote_checkout_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """Render the quote checkout page."""
    # Get current user from cookie
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login?next=/quote-checkout", status_code=303)

    return templates.TemplateResponse(
        "quote_checkout.html",
        {"request": request, "user": current_user}
    )


@router.post("/api/create-quotation")
async def create_quotation(
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new quotation."""
    # Get current user from cookie
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Parse request body
    data = await request.json()

    # Generate unique quote number (QN001, QN002, etc.)
    # Get the last quote number
    last_quote = db.query(models.Quotation).order_by(models.Quotation.id.desc()).first()

    if last_quote and (last_quote.quote_number.startswith("QN") or last_quote.quote_number.startswith("QT")):
        # Extract the sequence number and increment
        try:
            # Extract numeric part after prefix
            numeric_part = ''.join(filter(str.isdigit, last_quote.quote_number))
            if numeric_part:
                seq_num = int(numeric_part) + 1
            else:
                seq_num = 1
        except ValueError:
            # If we can't parse the number, start from 1
            seq_num = 1
    else:
        # Start with 1
        seq_num = 1

    quote_number = f"QN{seq_num:03d}"

    # Create new quotation
    new_quotation = models.Quotation(
        quote_number=quote_number,
        date=datetime.now().date(),
        customer_name=data["customer"]["name"],
        customer_phone=data["customer"]["phone"],
        customer_email=data["customer"].get("email", ""),
        customer_address=data["customer"].get("address", ""),
        subtotal=data["totals"]["subtotal"],
        total_gst=data["totals"]["gst"],
        total_amount=data["totals"]["total"],
        asked_about=data.get("askedAbout", "")
    )

    db.add(new_quotation)
    db.commit()
    db.refresh(new_quotation)

    # Add quotation items
    for item in data["items"]:
        new_item = models.QuotationItem(
            quotation_id=new_quotation.id,
            item_code=item["code"],
            item_name=item["name"],
            quantity=item["quantity"],
            price=item["price"],
            gst_rate=item["gstRate"],
            gst_amount=item["price"] * item["quantity"] * (item["gstRate"] / 100),
            total=item["price"] * item["quantity"] * (1 + item["gstRate"] / 100),
            item_type=item["type"]
        )
        db.add(new_item)

    db.commit()

    return {"success": True, "quote_number": quote_number, "id": new_quotation.id}


@router.get("/api/quotations")
async def api_get_quotations(
    db: Session = Depends(get_db)
):
    """Get all quotations as JSON."""
    quotations = db.query(models.Quotation).order_by(models.Quotation.created_at.desc()).all()

    result = []
    for q in quotations:
        result.append({
            "id": q.id,
            "quote_number": q.quote_number,
            "date": q.date.isoformat(),
            "customer_name": q.customer_name,
            "customer_phone": q.customer_phone,
            "total_amount": q.total_amount,
            "asked_about": q.asked_about,
            "created_at": q.created_at.isoformat()
        })

    return result


@router.get("/api/quotation/{quote_id}")
async def api_get_quotation(
    quote_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific quotation as JSON."""
    try:
        quotation = db.query(models.Quotation).filter(models.Quotation.id == quote_id).first()
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")

        items = db.query(models.QuotationItem).filter(models.QuotationItem.quotation_id == quote_id).all()

        items_data = []
        for item in items:
            items_data.append({
                "id": item.id,
                "item_code": item.item_code,
                "item_name": item.item_name,
                "quantity": item.quantity,
                "price": item.price,
                "gst_rate": item.gst_rate,
                "gst_amount": item.gst_amount,
                "total": item.total,
                "item_type": item.item_type
            })

        return {
            "id": quotation.id,
            "quote_number": quotation.quote_number,
            "date": quotation.date.isoformat(),
            "customer_name": quotation.customer_name,
            "customer_phone": quotation.customer_phone,
            "customer_email": quotation.customer_email,
            "customer_address": quotation.customer_address,
            "asked_about": quotation.asked_about,
            "subtotal": quotation.subtotal,
            "total_gst": quotation.total_gst,
            "total_amount": quotation.total_amount,
            "pdf_path": quotation.pdf_path,
            "created_at": quotation.created_at.isoformat(),
            "items": items_data
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error getting quotation API: {e}")
        print(f"Error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error getting quotation: {str(e)}")


@router.post("/api/generate-quotation-pdf/{quote_id}")
async def generate_quotation_pdf(
    quote_id: int,
    db: Session = Depends(get_db)
):
    """Generate a PDF for a quotation."""
    try:
        # Get quotation from database
        quotation = db.query(models.Quotation).filter(models.Quotation.id == quote_id).first()
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")

        # Get quotation items
        items = db.query(models.QuotationItem).filter(models.QuotationItem.quotation_id == quote_id).all()

        # Prepare data for PDF generation
        quotation_data = {
            "id": quotation.id,
            "quote_number": quotation.quote_number,
            "date": quotation.date,
            "customer_name": quotation.customer_name,
            "customer_phone": quotation.customer_phone,
            "customer_email": quotation.customer_email,
            "customer_address": quotation.customer_address,
            "asked_about": quotation.asked_about,
            "subtotal": quotation.subtotal,
            "total_gst": quotation.total_gst,
            "total_amount": quotation.total_amount,
            "items": [
                {
                    "item_name": item.item_name,
                    "item_type": item.item_type,
                    "quantity": item.quantity,
                    "price": item.price,
                    "gst_rate": item.gst_rate,
                    "gst_amount": item.gst_amount,
                    "total": item.total
                } for item in items
            ]
        }

        # Generate PDF
        from app.utils.pdf_generator import generate_pdf_quotation
        pdf_path = generate_pdf_quotation(quotation_data)

        # Update quotation with PDF path
        quotation.pdf_path = pdf_path
        db.commit()

        return {"success": True, "pdf_path": pdf_path}
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating quotation PDF: {e}")
        print(f"Error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")


@router.post("/api/convert-quotation-to-invoice/{quote_id}")
async def convert_quotation_to_invoice(
    quote_id: int,
    db: Session = Depends(get_db)
):
    """Convert a quotation to an invoice."""
    try:
        # Get quotation from database
        quotation = db.query(models.Quotation).filter(models.Quotation.id == quote_id).first()
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")

        # Get quotation items
        items = db.query(models.QuotationItem).filter(models.QuotationItem.quotation_id == quote_id).all()

        # Import necessary modules
        from app.db import crud
        from datetime import datetime

        # Generate invoice number
        invoice_number = crud.generate_invoice_number(db)

        # Calculate invoice values
        subtotal = quotation.subtotal
        total_discount = 0  # No discount in quotation
        discounted_subtotal = subtotal - total_discount
        total_gst = quotation.total_gst
        total_amount = quotation.total_amount

        # Prepare invoice data
        invoice_data = {
            "invoice_number": invoice_number,
            "date": datetime.now().date(),
            "customer_name": quotation.customer_name,
            "customer_address": quotation.customer_address or "",
            "customer_phone": quotation.customer_phone or "",
            "customer_email": quotation.customer_email or "",
            "customer_gst": "",  # Default empty GST
            "payment_method": "Cash",  # Default payment method
            "payment_status": "Unpaid",  # Default payment status
            "amount_paid": 0,  # Default amount paid
            "subtotal": subtotal,
            "total_discount": total_discount,
            "discounted_subtotal": discounted_subtotal,
            "total_gst": total_gst,
            "total_amount": total_amount,
            "invoice_type": "product",  # Default invoice type
            "items": [
                {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "hsn_code": "N/A",  # Default HSN code
                    "quantity": item.quantity,
                    "price": item.price,
                    "discount_percent": 0,  # No discount
                    "discount_amount": 0,  # No discount
                    "discounted_subtotal": item.price * item.quantity,
                    "gst_rate": item.gst_rate,
                    "gst_amount": item.gst_amount,
                    "total": item.total,
                    "item_type": item.item_type
                } for item in items
            ]
        }

        # Create invoice
        invoice = crud.create_invoice(db, invoice_data)

        # Generate PDF for the invoice
        from app.utils.pdf_generator import generate_pdf_invoice
        generate_pdf_invoice(invoice)

        return {"success": True, "invoice_id": invoice.invoice_number}
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error converting quotation to invoice: {e}")
        print(f"Error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error converting to invoice: {str(e)}")


@router.get("/api/quotations/export-excel")
async def export_quotations_excel(
    db: Session = Depends(get_db)
):
    """Export quotations to Excel file."""
    try:
        from fastapi.responses import FileResponse
        from app.core.excel_generator import export_quotations_to_excel

        # Get all quotations from database
        quotations = db.query(models.Quotation).order_by(models.Quotation.created_at.desc()).all()

        # Generate Excel file
        filename, file_path = export_quotations_to_excel(quotations)

        # Return the Excel file
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error exporting quotations to Excel: {e}")
        print(f"Error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error exporting to Excel: {str(e)}")


@router.get("/quotation-pdf/{quote_number}")
async def view_quotation_pdf(
    quote_number: str,
    db: Session = Depends(get_db)
):
    """View a quotation PDF in the browser."""
    try:
        # Get quotation from database
        quotation = db.query(models.Quotation).filter(models.Quotation.quote_number == quote_number).first()
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")

        # Check if PDF exists
        if not quotation.pdf_path or not os.path.exists(quotation.pdf_path):
            # Generate PDF if it doesn't exist
            from app.utils.pdf_generator import generate_pdf_quotation

            # Get quotation items
            items = db.query(models.QuotationItem).filter(models.QuotationItem.quotation_id == quotation.id).all()

            # Prepare quotation data for PDF generation
            quotation_data = {
                "id": quotation.id,
                "quote_number": quotation.quote_number,
                "date": quotation.date,
                "customer_name": quotation.customer_name,
                "customer_phone": quotation.customer_phone,
                "customer_email": quotation.customer_email,
                "customer_address": quotation.customer_address,
                "asked_about": quotation.asked_about,
                "subtotal": quotation.subtotal,
                "total_gst": quotation.total_gst,
                "total_amount": quotation.total_amount,
                "items": [
                    {
                        "item_name": item.item_name,
                        "quantity": item.quantity,
                        "price": item.price,
                        "gst_rate": item.gst_rate,
                        "gst_amount": item.gst_amount,
                        "total": item.total
                    } for item in items
                ]
            }

            # Generate PDF
            pdf_path = generate_pdf_quotation(quotation_data)

            # Update quotation with PDF path
            quotation.pdf_path = pdf_path
            db.commit()

        # Return PDF file for viewing in the browser (inline)
        return FileResponse(
            path=quotation.pdf_path,
            filename=f"Quotation_{quote_number}.pdf",
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=Quotation_{quote_number}.pdf"}
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error viewing quotation PDF: {e}")
        print(f"Error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error viewing PDF: {str(e)}")


@router.get("/download-quotation-pdf/{quote_number}")
async def download_quotation_pdf(
    quote_number: str,
    db: Session = Depends(get_db)
):
    """Download a quotation PDF."""
    try:
        # Get quotation from database
        quotation = db.query(models.Quotation).filter(models.Quotation.quote_number == quote_number).first()
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")

        # Check if PDF exists
        if not quotation.pdf_path or not os.path.exists(quotation.pdf_path):
            # Generate PDF if it doesn't exist
            from app.utils.pdf_generator import generate_pdf_quotation

            # Get quotation items
            items = db.query(models.QuotationItem).filter(models.QuotationItem.quotation_id == quotation.id).all()

            # Prepare quotation data for PDF generation
            quotation_data = {
                "id": quotation.id,
                "quote_number": quotation.quote_number,
                "date": quotation.date,
                "customer_name": quotation.customer_name,
                "customer_phone": quotation.customer_phone,
                "customer_email": quotation.customer_email,
                "customer_address": quotation.customer_address,
                "asked_about": quotation.asked_about,
                "subtotal": quotation.subtotal,
                "total_gst": quotation.total_gst,
                "total_amount": quotation.total_amount,
                "items": [
                    {
                        "item_name": item.item_name,
                        "quantity": item.quantity,
                        "price": item.price,
                        "gst_rate": item.gst_rate,
                        "gst_amount": item.gst_amount,
                        "total": item.total
                    } for item in items
                ]
            }

            # Generate PDF
            pdf_path = generate_pdf_quotation(quotation_data)

            # Update quotation with PDF path
            quotation.pdf_path = pdf_path
            db.commit()

        # Return PDF file as attachment
        return FileResponse(
            path=quotation.pdf_path,
            filename=f"Quotation_{quote_number}.pdf",
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Quotation_{quote_number}.pdf"}
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error downloading quotation PDF: {e}")
        print(f"Error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error downloading PDF: {str(e)}")


@router.delete("/api/quotations/delete/{quote_number}")
async def delete_quotation(
    quote_number: str,
    db: Session = Depends(get_db)
):
    """Delete a quotation."""
    try:
        # Get quotation from database
        quotation = db.query(models.Quotation).filter(models.Quotation.quote_number == quote_number).first()
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")

        # Delete the PDF file if it exists
        if quotation.pdf_path and os.path.exists(quotation.pdf_path):
            try:
                os.remove(quotation.pdf_path)
            except Exception as e:
                print(f"Error deleting PDF file: {e}")

        # Delete quotation items
        db.query(models.QuotationItem).filter(models.QuotationItem.quotation_id == quotation.id).delete()

        # Delete the quotation
        db.delete(quotation)
        db.commit()

        return {"status": "success", "message": "Quotation deleted successfully"}
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error deleting quotation: {e}")
        print(f"Error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error deleting quotation: {str(e)}")