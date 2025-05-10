from fastapi import APIRouter, Depends, Form, Request, Body, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import json

from app.db import crud, database, models
from app.schemas.sale import SaleCreate, Sale, SaleItem

router = APIRouter(tags=["Sales"])
templates = Jinja2Templates(directory="templates")


@router.post("/checkout")
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
    """Process checkout and create invoice"""
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

        # Determine invoice type based on items
        has_products = any(item.get("item_type", "product") == "product" for item in items)
        has_services = any(item.get("item_type", "product") == "service" for item in items)

        if has_products and has_services:
            invoice_type = "combination"
        elif has_services:
            invoice_type = "service"
        else:
            invoice_type = "product"

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
            "pdf_path": pdf_path,
            "invoice_type": invoice_type
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

            # Determine item type
            item_type = item.get("item_type", "product")

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
                "total": item_total,
                "item_type": item_type
            })

        # Save invoice to database
        invoice = crud.create_invoice(db, invoice_data)

        # Generate PDF invoice
        from app.core.pdf_generator import generate_pdf_invoice
        generate_pdf_invoice(invoice)

        # Update sales counter
        crud.update_sales_counter(db, total)

        return {"success": True, "invoice_id": invoice.invoice_number}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/reserve-stock")
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


@router.post("/release-stock")
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
