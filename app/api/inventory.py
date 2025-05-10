from fastapi import APIRouter, Form, Depends, Request, Body, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import crud, database
from datetime import date
from pydantic import BaseModel
import pandas as pd
import os
import tempfile
from typing import List, Optional


class QuantityUpdate(BaseModel):
    quantity: int


class ItemUpdate(BaseModel):
    item_name: str
    hsn_code: str
    purchase_price_per_unit: float
    margin: float
    gst_rate: float
    quantity: int
    unit_of_measurement: str
    supplier_name: str


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/inventory/stock")
def add_stock_item(
    request: Request = None,
    date: date = Form(...),
    item_name: str = Form(...),
    hsn_code: str = Form(...),
    gst_rate: float = Form(...),
    purchase_price_per_unit: float = Form(...),
    margin: float = Form(...),
    quantity: int = Form(...),
    unit_of_measurement: str = Form(...),
    supplier_name: str = Form(...),
    supplier_gst_number: str = Form(...),
    db: Session = Depends(database.get_db),
):
    """Add a new item to inventory

    This endpoint now returns JSON instead of HTML to work with our table component
    """
    try:
        # Generate a unique item code
        item_code = crud.generate_item_code(db)

        # Create the item in the database
        new_item = crud.create_item(
            db=db,
            item_data={
                "item_code": item_code,
                "date": date,
                "item_name": item_name,
                "hsn_code": hsn_code,
                "gst_rate": gst_rate,
                "purchase_price_per_unit": purchase_price_per_unit,
                "margin": margin,
                "quantity": quantity,
                "unit_of_measurement": unit_of_measurement,
                "supplier_name": supplier_name,
                "supplier_gst_number": supplier_gst_number
            }
        )

        # Return success response with the new item data
        return {
            "success": True,
            "message": f"Item {item_name} added successfully with code {item_code}",
            "item": {
                "item_code": item_code,
                "date": date.isoformat(),
                "item_name": item_name,
                "hsn_code": hsn_code,
                "gst_rate": gst_rate,
                "purchase_price_per_unit": purchase_price_per_unit,
                "margin": margin,
                "quantity": quantity,
                "unit_of_measurement": unit_of_measurement,
                "supplier_name": supplier_name,
                "supplier_gst_number": supplier_gst_number
            }
        }
    except Exception as e:
        # Log the error
        print(f"Error adding item to inventory: {e}")

        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error adding item to inventory: {str(e)}"
            }
        )


@router.get("/inventory/items", response_class=HTMLResponse)
def get_all_items(request: Request, db: Session = Depends(database.get_db)):
    items = crud.get_all_items(db)
    return templates.TemplateResponse("index.html", {"request": request, "items": items})


@router.get("/inventory/item/{item_code}")
def get_item(item_code: str, db: Session = Depends(database.get_db)):
    item = crud.get_item(db, item_code)
    if not item:
        return {"error": "Item not found"}
    return item


@router.get("/inventory/search")
def search_items(query: str, db: Session = Depends(database.get_db)):
    """Search for items by item code or name across the entire inventory"""
    try:
        # Search in the database for items matching the query
        items = crud.search_items(db, query)

        # Convert items to a list of dictionaries for JSON response
        items_list = []
        for item in items:
            items_list.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "hsn_code": item.hsn_code,
                "gst_rate": item.gst_rate,
                "purchase_price_per_unit": item.purchase_price_per_unit,
                "margin": item.margin,
                "quantity": item.quantity,
                "unit_of_measurement": item.unit_of_measurement,
                "supplier_name": item.supplier_name,
                "supplier_gst_number": item.supplier_gst_number
            })

        return {"success": True, "items": items_list, "count": len(items_list)}
    except Exception as e:
        print(f"Error searching items: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error searching items: {str(e)}"}
        )


@router.get("/inventory/export-excel")
def export_inventory_excel(db: Session = Depends(database.get_db)):
    """Export inventory to Excel"""
    from fastapi.responses import FileResponse
    from app.core.excel_generator import export_inventory_to_excel

    try:
        # Get all items
        items = crud.get_all_items(db)

        # Generate Excel file
        filename, file_path = export_inventory_to_excel(items)

        # Return the Excel file
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error exporting inventory to Excel: {e}")
        print(f"Error details: {error_details}")
        return {"error": f"Error exporting inventory to Excel: {str(e)}"}


@router.post("/inventory/update-quantity/{item_code}")
def update_quantity(item_code: str, update_data: QuantityUpdate, db: Session = Depends(database.get_db)):
    try:
        item = crud.update_item_quantity(db, item_code, update_data.quantity, is_absolute=True)
        if not item:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Item not found"}
            )
        return {"success": True, "item_code": item_code, "new_quantity": update_data.quantity}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


@router.post("/inventory/update-item/{item_code}")
def update_item(item_code: str, update_data: ItemUpdate, db: Session = Depends(database.get_db)):
    try:
        item = crud.update_item(db, item_code, update_data.dict())
        if not item:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Item not found"}
            )
        return {"success": True, "item_code": item_code}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

@router.post("/inventory/update-item")
def update_item_form(
    item_code: str = Form(...),
    item_name: str = Form(...),
    hsn_code: str = Form(...),
    purchase_price_per_unit: float = Form(...),
    margin: float = Form(...),
    gst_rate: float = Form(...),
    quantity: int = Form(...),
    unit_of_measurement: str = Form(...),
    supplier_name: str = Form(...),
    supplier_gst_number: str = Form(...),
    db: Session = Depends(database.get_db)
):
    """Update an item using form data"""
    try:
        # Create a dictionary with the item data
        item_data = {
            "item_name": item_name,
            "hsn_code": hsn_code,
            "purchase_price_per_unit": purchase_price_per_unit,
            "margin": margin,
            "gst_rate": gst_rate,
            "quantity": quantity,
            "unit_of_measurement": unit_of_measurement,
            "supplier_name": supplier_name,
            "supplier_gst_number": supplier_gst_number
        }

        # Update the item
        item = crud.update_item(db, item_code, item_data)
        if not item:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Item not found"}
            )

        return JSONResponse(
            content={"success": True, "item_code": item_code, "message": "Item updated successfully"}
        )
    except Exception as e:
        print(f"Error updating item: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


@router.delete("/inventory/delete-item/{item_code}")
def delete_item(item_code: str, db: Session = Depends(database.get_db)):
    try:
        success = crud.delete_item(db, item_code)
        if not success:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Item not found"}
            )
        return {"success": True, "message": f"Item {item_code} deleted successfully"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


@router.post("/inventory/import-excel")
async def import_inventory_from_excel(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    """Import inventory items from Excel file"""
    try:
        # Create a temporary file to store the uploaded Excel
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
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

        # Check if the Excel has the required columns
        required_columns = [
            "item_name", "hsn_code", "purchase_price_per_unit",
            "margin", "gst_rate", "quantity", "unit_of_measurement",
            "supplier_name", "supplier_gst_number"
        ]

        # item_code is optional but can be included for updating existing items
        optional_columns = ["item_code"]

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

        # Process each row in the Excel file
        success_count = 0
        update_count = 0
        error_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                # Create item data dictionary with explicit date formatting
                today = date.today()
                item_data = {
                    "date": today,  # Ensure date is properly set
                    "item_name": row["item_name"],
                    "hsn_code": row["hsn_code"],
                    "gst_rate": float(row["gst_rate"]),
                    "purchase_price_per_unit": float(row["purchase_price_per_unit"]),
                    "margin": float(row["margin"]),
                    "quantity": int(row["quantity"]),
                    "unit_of_measurement": row["unit_of_measurement"],
                    "supplier_name": row["supplier_name"],
                    "supplier_gst_number": row["supplier_gst_number"]
                }

                # Check if item_code is provided in the Excel file and is not empty
                has_item_code = "item_code" in row and row["item_code"] and str(row["item_code"]).strip()

                if has_item_code:
                    # Convert to string and clean up
                    item_code = str(row["item_code"]).strip()

                    # Check if this item already exists
                    existing_item = crud.get_item(db, item_code)

                    if existing_item:
                        try:
                            # Update existing item
                            crud.update_item(db=db, item_code=item_code, item_data=item_data)
                            # Explicitly commit after each successful update
                            db.commit()
                            update_count += 1
                        except Exception as e:
                            db.rollback()
                            error_count += 1
                            errors.append(f"Row {index+2}: Error updating item: {str(e)}")
                    else:
                        try:
                            # Create new item with provided code
                            item_data["item_code"] = item_code
                            crud.create_item(db=db, item_data=item_data)
                            # Explicitly commit after each successful item creation
                            db.commit()
                            success_count += 1
                        except Exception as e:
                            db.rollback()
                            error_count += 1
                            errors.append(f"Row {index+2}: Error creating item with provided code: {str(e)}")
                else:
                    # Generate a new unique item code for this item
                    try:
                        item_code = crud.generate_item_code(db)

                        # Add the generated code to the item data
                        item_data["item_code"] = item_code

                        # Create the item in the database
                        crud.create_item(db=db, item_data=item_data)

                        # Explicitly commit after each successful item creation
                        db.commit()
                        success_count += 1

                        print(f"Created new item with generated code: {item_code}")
                    except Exception as e:
                        db.rollback()
                        error_count += 1
                        errors.append(f"Row {index+2}: Error creating item with generated code: {str(e)}")
            except Exception as e:
                # Rollback the transaction to prevent cascading errors
                db.rollback()
                error_count += 1
                errors.append(f"Row {index+2}: {str(e)}")

        # Get the total count of items in the inventory
        try:
            # Make sure we have a fresh session
            db.rollback()
            # Use get_items_count instead of get_all_items to get the actual total count
            items_count = crud.get_items_count(db)
        except Exception as e:
            print(f"Error getting items count: {e}")
            items_count = 0

        # Format errors to be more user-friendly
        formatted_errors = []
        if errors:
            # Limit to first 5 errors to avoid overwhelming the user
            for i, error in enumerate(errors[:5]):
                formatted_errors.append(error)

            # If there are more errors, add a summary
            if len(errors) > 5:
                formatted_errors.append(f"... and {len(errors) - 5} more errors")

        # Return the results with the updated items list
        return {
            "success": True,
            "message": f"Imported {success_count} new items and updated {update_count} existing items successfully. {error_count} items failed.",
            "errors": formatted_errors if formatted_errors else None,
            "items_count": items_count
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error importing inventory from Excel: {e}")
        print(f"Error details: {error_details}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error importing inventory: {str(e)}"}
        )