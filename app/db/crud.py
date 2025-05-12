from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from app.db import models
from sqlalchemy.sql import func
from app.core.auth import get_password_hash


def generate_item_code(db: Session) -> str:
    """Generate a unique item code with format SUN001, SUN002, etc.

    This function finds the highest existing item code and increments it by 1.
    It uses 3 digits to allow for up to 999 unique codes.
    """
    try:
        # Get the last item by item_code in descending order
        last_item = db.query(models.InventoryItem).order_by(
            models.InventoryItem.item_code.desc()
        ).first()

        if last_item and last_item.item_code.startswith("SUN"):
            # Extract the numeric part after "SUN"
            numeric_part = ''.join(filter(str.isdigit, last_item.item_code))
            if numeric_part:
                number = int(numeric_part) + 1
            else:
                number = 1
        else:
            number = 1

        # Use 3 digits (zfill(3)) to allow for up to 999 items
        return f"SUN{str(number).zfill(3)}"
    except Exception as e:
        print(f"Error generating item code: {e}")
        # Fallback to a timestamp-based code if there's an error
        import time
        timestamp = int(time.time()) % 10000  # Last 4 digits of timestamp
        return f"SUN{timestamp}"


def generate_service_code(db: Session) -> str:
    try:
        last_service = db.query(models.Service).order_by(
            models.Service.service_code.desc()
        ).first()
        if last_service and last_service.service_code.startswith("SRV"):
            number = int(last_service.service_code[3:]) + 1
        else:
            number = 1
        return f"SRV{str(number).zfill(3)}"
    except Exception as e:
        print(f"Error generating service code: {e}")
        # Fallback to a default number if there's an error
        return f"SRV001"


def generate_customer_code(db: Session) -> str:
    """Generate a unique customer code with format CUST001, CUST002, etc."""
    try:
        last_customer = db.query(models.Customer).order_by(
            models.Customer.customer_code.desc()
        ).first()
        if last_customer and last_customer.customer_code.startswith("CUST"):
            number = int(last_customer.customer_code[4:]) + 1
        else:
            number = 1
        return f"CUST{str(number).zfill(3)}"
    except Exception as e:
        print(f"Error generating customer code: {e}")
        # Fallback to a default number if there's an error
        return f"CUST001"


def create_item(db: Session, item_data: dict):
    item = models.InventoryItem(**item_data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_all_items(db: Session, skip: int = 0, limit: int = 100):
    """Get all items from the inventory"""
    return db.query(models.InventoryItem).offset(skip).limit(limit).all()


def get_items_count(db: Session):
    """Get the total count of items in the inventory"""
    return db.query(models.InventoryItem).count()


def get_item(db: Session, item_code: str):
    """Get a specific item by its code"""
    return db.query(models.InventoryItem).filter(models.InventoryItem.item_code == item_code).first()


def search_items(db: Session, query: str):
    """Search for items by item code or name

    This function searches across the entire inventory, not just the current page.
    It uses case-insensitive LIKE queries to find partial matches in both item_code and item_name.

    Args:
        db: Database session
        query: Search query string

    Returns:
        List of items matching the search criteria
    """
    from sqlalchemy import or_

    # Convert query to lowercase for case-insensitive search
    search_term = f"%{query}%"

    # Search in both item_code and item_name columns
    items = db.query(models.InventoryItem).filter(
        or_(
            models.InventoryItem.item_code.ilike(search_term),
            models.InventoryItem.item_name.ilike(search_term),
            models.InventoryItem.supplier_name.ilike(search_term)
        )
    ).all()

    return items


def update_item(db: Session, item_code: str, item_data: dict):
    """Update an existing item in the inventory

    Args:
        db: Database session
        item_code: The item code to update
        item_data: Dictionary containing the updated item data

    Returns:
        The updated item if successful, None if the item was not found
    """
    item = get_item(db, item_code)
    if not item:
        return None

    try:
        # Update the item attributes
        for key, value in item_data.items():
            if hasattr(item, key):
                setattr(item, key, value)

        # Commit the changes
        db.commit()
        db.refresh(item)
        return item
    except Exception as e:
        # If there's an error, rollback the transaction
        db.rollback()
        print(f"Error updating item {item_code}: {e}")
        raise


def update_item_quantity(db: Session, item_code: str, quantity_change: int, is_absolute: bool = False):
    """Update the quantity of an item in inventory

    Args:
        db: Database session
        item_code: The item code to update
        quantity_change: The amount to change the quantity by, or the new quantity if is_absolute is True
        is_absolute: If True, set the quantity to quantity_change instead of adding it

    Returns:
        The updated item, or None if the item was not found
    """
    item = get_item(db, item_code)
    if not item:
        return None

    if is_absolute:
        item.quantity = quantity_change
    else:
        item.quantity += quantity_change

    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item_code: str, item_data: dict):
    """Update an item in the inventory

    Args:
        db: Database session
        item_code: The item code to update
        item_data: Dictionary containing the updated item data

    Returns:
        The updated item, or None if the item was not found
    """
    item = get_item(db, item_code)
    if not item:
        return None

    # Update the item attributes
    for key, value in item_data.items():
        if hasattr(item, key):
            setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item_code: str):
    """Delete an item from the inventory

    Args:
        db: Database session
        item_code: The item code to delete

    Returns:
        True if the item was deleted, False if the item was not found
    """
    item = get_item(db, item_code)
    if not item:
        return False

    try:
        # Delete the item
        db.delete(item)
        # Ensure the transaction is committed
        db.commit()
        # Flush the session to ensure changes are applied immediately
        db.flush()
        print(f"Item {item_code} successfully deleted from database")
        return True
    except Exception as e:
        # If there's an error, rollback the transaction
        db.rollback()
        print(f"Error deleting item {item_code}: {e}")
        return False


def create_invoice(db: Session, invoice_data: dict):
    """Create a new invoice"""
    # Use provided invoice number or generate one
    invoice_number = invoice_data.get("invoice_number") or generate_invoice_number(db)

    # Create invoice
    invoice = models.Invoice(
        invoice_number=invoice_number,
        date=invoice_data.get("date", datetime.now().date()),
        customer_name=invoice_data.get("customer_name", ""),
        customer_address=invoice_data.get("customer_address", ""),
        customer_phone=invoice_data.get("customer_phone", ""),
        customer_email=invoice_data.get("customer_email", ""),
        customer_gst=invoice_data.get("customer_gst", ""),
        payment_method=invoice_data.get("payment_method", ""),
        subtotal=invoice_data.get("subtotal", 0),
        total_gst=invoice_data.get("total_gst", 0),
        total_amount=invoice_data.get("total_amount", 0),
        amount_paid=invoice_data.get("amount_paid", 0),
        payment_status=invoice_data.get("payment_status", "Unpaid"),
        invoice_type=invoice_data.get("invoice_type", "product"),
        pdf_path=invoice_data.get("pdf_path", "")
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # Create invoice items
    for item_data in invoice_data.get("items", []):
        invoice_item = models.InvoiceItem(
            invoice_id=invoice.id,
            item_code=item_data.get("item_code", ""),
            item_name=item_data.get("item_name", ""),
            hsn_code=item_data.get("hsn_code", ""),
            quantity=item_data.get("quantity", 0),
            price=item_data.get("price", 0),
            discount_percent=item_data.get("discount_percent", 0),
            discount_amount=item_data.get("discount_amount", 0),
            discounted_subtotal=item_data.get("discounted_subtotal", 0),
            gst_rate=item_data.get("gst_rate", 0),
            gst_amount=item_data.get("gst_amount", 0),
            total=item_data.get("total", 0)
        )
        db.add(invoice_item)

        # Stock is already reserved when added to cart, so we don't need to update it again
        # Just log the item for record-keeping
        print(f"Recording invoice item: {item_data.get('item_name')} x {item_data.get('quantity')}")

    db.commit()
    return invoice


def generate_invoice_number(db: Session) -> str:
    """Generate a unique invoice number starting from INV01"""
    # Get the last invoice
    last_invoice = db.query(models.Invoice).order_by(desc(models.Invoice.id)).first()

    if last_invoice and last_invoice.invoice_number.startswith("INV"):
        # Try to extract the sequence number
        try:
            # Extract numeric part after "INV"
            numeric_part = ''.join(filter(str.isdigit, last_invoice.invoice_number))
            if numeric_part:
                seq_num = int(numeric_part) + 1
            else:
                seq_num = 1
        except ValueError:
            # If we can't parse the number, start from 1
            seq_num = 1
    else:
        seq_num = 1

    return f"INV{seq_num:02d}"


def get_all_invoices(db: Session, skip: int = 0, limit: int = 100):
    """Get all invoices with pagination"""
    invoices = db.query(models.Invoice).order_by(models.Invoice.date.desc()).offset(skip).limit(limit).all()

    result = []
    for invoice in invoices:
        # Convert to dict for template
        invoice_dict = {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "date": invoice.date,
            "customer_name": invoice.customer_name,
            "customer_address": invoice.customer_address,
            "customer_phone": invoice.customer_phone,
            "customer_email": invoice.customer_email,
            "customer_gst": invoice.customer_gst,
            "payment_method": invoice.payment_method,
            "payment_status": invoice.payment_status,
            "amount_paid": invoice.amount_paid,
            "subtotal": invoice.subtotal,
            "total_gst": invoice.total_gst,
            "total_amount": invoice.total_amount,
            "invoice_type": invoice.invoice_type if hasattr(invoice, "invoice_type") else "product",
            "pdf_path": invoice.pdf_path
        }
        result.append(invoice_dict)

    return result

def get_invoice(db: Session, invoice_number: str):
    """Get an invoice by its number"""
    invoice = db.query(models.Invoice).filter(
        models.Invoice.invoice_number == invoice_number
    ).first()

    if not invoice:
        return None

    # Get invoice items
    invoice_items = db.query(models.InvoiceItem).filter(
        models.InvoiceItem.invoice_id == invoice.id
    ).all()

    # Convert to dict for template
    invoice_dict = {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "date": invoice.date,
        "customer_name": invoice.customer_name,
        "customer_address": invoice.customer_address,
        "customer_phone": invoice.customer_phone,
        "customer_email": invoice.customer_email,
        "customer_gst": invoice.customer_gst,
        "payment_method": invoice.payment_method,
        "payment_status": invoice.payment_status,
        "amount_paid": invoice.amount_paid,
        "subtotal": invoice.subtotal,
        "total_gst": invoice.total_gst,
        "total_amount": invoice.total_amount,
        "invoice_type": invoice.invoice_type if hasattr(invoice, "invoice_type") else "product",
        "pdf_path": invoice.pdf_path,
        "invoice_items": []  # Renamed to avoid conflict with the built-in items() method
    }

    # If this is a service invoice, get the service details
    if hasattr(invoice, "invoice_type") and invoice.invoice_type == "service":
        try:
            # Get the service record
            service = db.query(models.Service).filter(
                models.Service.invoice_id == invoice.id
            ).first()

            if service:
                invoice_dict["service_name"] = service.service_name
                invoice_dict["service_description"] = service.description
                invoice_dict["employee_name"] = service.employee_name
        except Exception as e:
            print(f"Error getting service details: {e}")

    for item in invoice_items:
        invoice_dict["invoice_items"].append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "hsn_code": item.hsn_code,
            "quantity": item.quantity,
            "price": item.price,
            "discount_percent": item.discount_percent,
            "discount_amount": item.discount_amount,
            "discounted_subtotal": item.discounted_subtotal,
            "gst_rate": item.gst_rate,
            "gst_amount": item.gst_amount,
            "total": item.total
        })

    return invoice_dict

def delete_invoice(db: Session, invoice_number: str):
    """Delete an invoice by its number"""
    # Get the invoice
    invoice = db.query(models.Invoice).filter(
        models.Invoice.invoice_number == invoice_number
    ).first()

    if not invoice:
        return False

    # Get invoice items
    invoice_items = db.query(models.InvoiceItem).filter(
        models.InvoiceItem.invoice_id == invoice.id
    ).all()

    # Delete invoice items
    for item in invoice_items:
        db.delete(item)

    # We don't need to store the invoice amount anymore since we're calculating totals directly

    # Delete the invoice
    db.delete(invoice)
    db.commit()

    # Check if this was the last invoice
    remaining_invoices = db.query(models.Invoice).count()
    if remaining_invoices == 0:
        # Reset the sales counter
        counter = get_sales_counter(db)
        counter.total_sales = 0
        counter.total_revenue = 0.0
        counter.last_updated = datetime.now()
        db.commit()

    return True


def get_sales_counter(db: Session):
    """Get the sales counter or create it if it doesn't exist"""
    counter = db.query(models.SalesCounter).first()
    if not counter:
        counter = models.SalesCounter(total_sales=0, total_revenue=0.0)
        db.add(counter)
        db.commit()
        db.refresh(counter)
    return counter


# Service CRUD operations
def create_service(db: Session, service_data: dict):
    """Create a new service record"""
    try:
        # Generate service code if not provided
        if "service_code" not in service_data:
            service_data["service_code"] = generate_service_code(db)

        # Create service record
        service = models.Service(**service_data)
        db.add(service)
        db.commit()
        db.refresh(service)
        return service
    except Exception as e:
        db.rollback()
        print(f"Error creating service: {e}")
        raise


def get_all_services(db: Session, skip: int = 0, limit: int = 100):
    """Get all services"""
    return db.query(models.Service).order_by(models.Service.date.desc()).offset(skip).limit(limit).all()


def get_service(db: Session, service_id: int):
    """Get a specific service by ID"""
    return db.query(models.Service).filter(models.Service.id == service_id).first()


def get_service_by_code(db: Session, service_code: str):
    """Get a specific service by service code"""
    return db.query(models.Service).filter(models.Service.service_code == service_code).first()


def get_next_service_id(db: Session) -> int:
    """Get the next service ID for generating service codes"""
    last_service = db.query(models.Service).order_by(models.Service.id.desc()).first()
    if last_service:
        return last_service.id + 1
    else:
        return 1


def update_service(db: Session, service_id: int, service_data: dict):
    """Update a service record"""
    try:
        service = get_service(db, service_id)
        if not service:
            return None

        # Update service attributes
        for key, value in service_data.items():
            if hasattr(service, key):
                setattr(service, key, value)

        db.commit()
        db.refresh(service)
        return service
    except Exception as e:
        db.rollback()
        print(f"Error updating service: {e}")
        raise


def delete_service(db: Session, service_id: int):
    """Delete a service record"""
    service = get_service(db, service_id)
    if not service:
        return False

    try:
        db.delete(service)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error deleting service {service_id}: {e}")
        return False


def search_services(db: Session, query: str):
    """Search for services by service code or name

    This function searches across all services, looking for matches in service_code and service_name.
    It uses case-insensitive LIKE queries to find partial matches.

    Args:
        db: Database session
        query: Search query string

    Returns:
        List of services matching the search criteria
    """
    from sqlalchemy import or_

    # Convert query to lowercase for case-insensitive search
    search_term = f"%{query}%"

    # Search in both service_code and service_name columns
    services = db.query(models.Service).filter(
        or_(
            models.Service.service_code.ilike(search_term),
            models.Service.service_name.ilike(search_term),
            models.Service.employee_name.ilike(search_term)
        )
    ).all()

    return services


def update_sales_counter(db: Session, order_amount: float):
    """Update the sales counter with a new sale"""
    counter = get_sales_counter(db)
    counter.total_sales += 1
    counter.total_revenue += order_amount
    counter.last_updated = datetime.now()
    db.commit()
    db.refresh(counter)
    return counter


def add_payment(db: Session, invoice_number: str, payment_data: dict):
    """Add a payment to an invoice and update its payment status

    Args:
        db: Database session
        invoice_number: The invoice number to add payment to
        payment_data: Dictionary containing payment details (amount, method, notes)

    Returns:
        The updated invoice, or None if the invoice was not found
    """
    # Get the invoice
    invoice = db.query(models.Invoice).filter(
        models.Invoice.invoice_number == invoice_number
    ).first()

    if not invoice:
        return None

    # Create payment record
    payment = models.Payment(
        invoice_id=invoice.id,
        payment_date=payment_data.get("payment_date", datetime.now()),
        amount=payment_data.get("amount", 0),
        payment_method=payment_data.get("payment_method", "Cash"),
        notes=payment_data.get("notes", "")
    )

    db.add(payment)

    # Update invoice payment status
    invoice.amount_paid += payment.amount

    # Round to 2 decimal places to avoid floating point issues
    invoice.amount_paid = round(invoice.amount_paid, 2)

    # Determine payment status
    if invoice.amount_paid >= invoice.total_amount:
        invoice.payment_status = "Fully Paid"
        # Ensure amount_paid doesn't exceed total_amount due to rounding
        invoice.amount_paid = invoice.total_amount
    elif invoice.amount_paid > 0:
        invoice.payment_status = "Partially Paid"
    else:
        invoice.payment_status = "Unpaid"

    db.commit()
    db.refresh(invoice)

    return invoice


def get_sales_stats(db: Session):
    """Get sales statistics"""
    # Get the counter for last_updated timestamp
    counter = get_sales_counter(db)

    # Count the total number of invoices (sales)
    total_sales = db.query(models.Invoice).count()

    # Calculate the total revenue from all invoices
    total_revenue = db.query(func.sum(models.Invoice.total_amount)).scalar() or 0.0

    # Get total number of products sold
    total_products_sold = db.query(func.sum(models.InvoiceItem.quantity)).scalar() or 0

    # Get most popular product
    most_popular_product = db.query(
        models.InvoiceItem.item_name,
        func.sum(models.InvoiceItem.quantity).label('total_quantity')
    ).group_by(
        models.InvoiceItem.item_name
    ).order_by(
        desc('total_quantity')
    ).first()

    # Calculate total inventory investment (purchase price * quantity)
    total_inventory_investment = db.query(
        func.sum(models.InventoryItem.purchase_price_per_unit * models.InventoryItem.quantity)
    ).scalar() or 0.0

    # Calculate total profit (revenue - cost)
    # First, get the cost of goods sold
    invoice_items = db.query(models.InvoiceItem).all()
    cost_of_goods_sold = 0.0

    for item in invoice_items:
        # Get the purchase price of the item
        inventory_item = db.query(models.InventoryItem).filter(
            models.InventoryItem.item_code == item.item_code
        ).first()

        if inventory_item:
            item_cost = inventory_item.purchase_price_per_unit * item.quantity
            cost_of_goods_sold += item_cost

    # Calculate profit
    total_profit = total_revenue - cost_of_goods_sold
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

    # Get top buyers (customers with highest total purchases)
    top_buyers = db.query(
        models.Invoice.customer_name,
        func.sum(models.Invoice.total_amount).label('total_spent')
    ).group_by(
        models.Invoice.customer_name
    ).order_by(
        desc('total_spent')
    ).limit(5).all()

    # Get top sellers (products with highest revenue)
    top_sellers = db.query(
        models.InvoiceItem.item_name,
        func.sum(models.InvoiceItem.total).label('total_revenue')
    ).group_by(
        models.InvoiceItem.item_name
    ).order_by(
        desc('total_revenue')
    ).limit(5).all()

    # Update the counter to match the actual data
    if counter.total_sales != total_sales or counter.total_revenue != total_revenue:
        counter.total_sales = total_sales
        counter.total_revenue = total_revenue
        counter.last_updated = datetime.now()
        db.commit()
        db.refresh(counter)

    return {
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "total_products_sold": total_products_sold,
        "most_popular_product": most_popular_product[0] if most_popular_product else None,
        "most_popular_quantity": most_popular_product[1] if most_popular_product else 0,
        "last_updated": counter.last_updated,
        "total_inventory_investment": round(total_inventory_investment, 2),
        "cost_of_goods_sold": round(cost_of_goods_sold, 2),
        "total_profit": round(total_profit, 2),
        "profit_margin": round(profit_margin, 2),
        "top_buyers": [{"name": buyer[0], "amount": round(buyer[1], 2)} for buyer in top_buyers],
        "top_sellers": [{"name": seller[0], "revenue": round(seller[1], 2)} for seller in top_sellers]
    }


# User CRUD operations

def create_user(db: Session, user_data: dict):
    """Create a new user with hashed password"""
    # Hash the password
    hashed_password = get_password_hash(user_data["password"])

    # Create user with hashed password
    user = models.User(
        email=user_data["email"],
        password=hashed_password,
        name=user_data["name"],
        phone=user_data.get("phone"),
        role=user_data.get("role", "employee"),
        first_login=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int):
    """Get a user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    """Get a user by email"""
    return db.query(models.User).filter(models.User.email == email).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    """Get all users with pagination"""
    return db.query(models.User).offset(skip).limit(limit).all()


def update_user(db: Session, user_id: int, user_data: dict):
    """Update user information"""
    user = get_user(db, user_id)
    if not user:
        return None

    # Update user attributes
    for key, value in user_data.items():
        if key == "password" and value:
            # Hash the password if it's being updated
            setattr(user, key, get_password_hash(value))
        elif hasattr(user, key) and key != "password":
            # Don't update password field directly
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


def update_password(db: Session, user_id: int, new_password: str):
    """Update user password and set first_login to False"""
    user = get_user(db, user_id)
    if not user:
        return None

    user.password = get_password_hash(new_password)
    user.first_login = False
    user.last_login = datetime.now()

    db.commit()
    db.refresh(user)
    return user


def update_last_login(db: Session, user_id: int):
    """Update user's last login timestamp"""
    user = get_user(db, user_id)
    if not user:
        return None

    user.last_login = datetime.now()
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int):
    """Delete a user"""
    user = get_user(db, user_id)
    if not user:
        return False

    db.delete(user)
    db.commit()
    return True


# Enquiry CRUD operations

def generate_enquiry_number(db: Session) -> str:
    """Generate a unique enquiry number with format ENQ001, ENQ002, etc."""
    try:
        # Get the last enquiry by enquiry_number in descending order
        last_enquiry = db.query(models.Enquiry).order_by(
            models.Enquiry.enquiry_number.desc()
        ).first()

        if last_enquiry and last_enquiry.enquiry_number.startswith("ENQ"):
            # Extract the numeric part after "ENQ"
            numeric_part = ''.join(filter(str.isdigit, last_enquiry.enquiry_number))
            if numeric_part:
                number = int(numeric_part) + 1
            else:
                number = 1
        else:
            number = 1

        # Use 3 digits (zfill(3)) to allow for up to 999 enquiries
        return f"ENQ{str(number).zfill(3)}"
    except Exception as e:
        print(f"Error generating enquiry number: {e}")
        # Fallback to a timestamp-based code if there's an error
        import time
        timestamp = int(time.time()) % 10000  # Last 4 digits of timestamp
        return f"ENQ{timestamp}"


def create_enquiry(db: Session, enquiry_data: dict):
    """Create a new enquiry record"""
    try:
        # Generate enquiry number if not provided
        if "enquiry_number" not in enquiry_data:
            enquiry_data["enquiry_number"] = generate_enquiry_number(db)

        # Create enquiry record
        enquiry = models.Enquiry(**enquiry_data)
        db.add(enquiry)
        db.commit()
        db.refresh(enquiry)
        return enquiry
    except Exception as e:
        db.rollback()
        print(f"Error creating enquiry: {e}")
        raise


def get_all_enquiries(db: Session, skip: int = 0, limit: int = 100):
    """Get all enquiries with pagination"""
    return db.query(models.Enquiry).order_by(models.Enquiry.date.desc()).offset(skip).limit(limit).all()


def get_enquiry(db: Session, enquiry_id: int):
    """Get a specific enquiry by ID"""
    return db.query(models.Enquiry).filter(models.Enquiry.id == enquiry_id).first()


def get_enquiry_by_number(db: Session, enquiry_number: str):
    """Get a specific enquiry by enquiry number"""
    return db.query(models.Enquiry).filter(models.Enquiry.enquiry_number == enquiry_number).first()


def update_enquiry(db: Session, enquiry_id: int, enquiry_data: dict):
    """Update an enquiry record"""
    try:
        enquiry = get_enquiry(db, enquiry_id)
        if not enquiry:
            return None

        # Update enquiry attributes
        for key, value in enquiry_data.items():
            if hasattr(enquiry, key):
                setattr(enquiry, key, value)

        db.commit()
        db.refresh(enquiry)
        return enquiry
    except Exception as e:
        db.rollback()
        print(f"Error updating enquiry: {e}")
        raise


def delete_enquiry(db: Session, enquiry_id: int):
    """Delete an enquiry record"""
    enquiry = get_enquiry(db, enquiry_id)
    if not enquiry:
        return False

    try:
        db.delete(enquiry)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error deleting enquiry {enquiry_id}: {e}")
        return False


# Customer CRUD operations
def create_customer(db: Session, customer_data: dict):
    """Create a new customer record"""
    try:
        # Generate a unique customer code
        customer_code = generate_customer_code(db)
        
        # Create customer object
        customer = models.Customer(
            customer_code=customer_code,
            date=customer_data.get("date", datetime.now().date()),
            customer_name=customer_data.get("customer_name", ""),
            phone_no=customer_data.get("phone_no", ""),
            address=customer_data.get("address", ""),
            product_description=customer_data.get("product_description", ""),
            payment_method=customer_data.get("payment_method", ""),
            payment_status=customer_data.get("payment_status", "Unpaid"),
            total_amount=customer_data.get("total_amount", 0),
            amount_paid=customer_data.get("amount_paid", 0),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(customer)
        db.commit()
        db.refresh(customer)
        
        # If there's an initial payment, create a payment record
        initial_amount = customer_data.get("amount_paid", 0)
        if initial_amount > 0:
            payment = models.CustomerPayment(
                customer_id=customer.id,
                payment_date=datetime.now(),
                amount=initial_amount,
                payment_method=customer_data.get("payment_method", "Cash"),
                notes="Initial payment"
            )
            db.add(payment)
            db.commit()
        
        return customer
    except Exception as e:
        db.rollback()
        print(f"Error creating customer: {e}")
        raise


def get_all_customers(db: Session, skip: int = 0, limit: int = 100):
    """Get all customers with pagination"""
    return db.query(models.Customer).order_by(models.Customer.date.desc()).offset(skip).limit(limit).all()


def get_customer(db: Session, customer_id: int):
    """Get a specific customer by ID"""
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()


def get_customer_by_code(db: Session, customer_code: str):
    """Get a specific customer by customer code"""
    return db.query(models.Customer).filter(models.Customer.customer_code == customer_code).first()


def update_customer(db: Session, customer_id: int, customer_data: dict):
    """Update a customer record"""
    try:
        customer = get_customer(db, customer_id)
        if not customer:
            return None

        # Update customer attributes
        for key, value in customer_data.items():
            if hasattr(customer, key):
                setattr(customer, key, value)

        # Update the updated_at timestamp
        customer.updated_at = datetime.now()

        db.commit()
        db.refresh(customer)
        return customer
    except Exception as e:
        db.rollback()
        print(f"Error updating customer: {e}")
        raise


def delete_customer(db: Session, customer_id: int):
    """Delete a customer record"""
    customer = get_customer(db, customer_id)
    if not customer:
        return False

    try:
        # Delete all customer payments first
        db.query(models.CustomerPayment).filter(
            models.CustomerPayment.customer_id == customer_id
        ).delete()

        # Delete the customer
        db.delete(customer)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error deleting customer {customer_id}: {e}")
        return False


def add_customer_payment(db: Session, customer_id: int, payment_data: dict):
    """Add a payment to a customer record"""
    try:
        customer = get_customer(db, customer_id)
        if not customer:
            return None

        # Create payment record
        payment = models.CustomerPayment(
            customer_id=customer_id,
            payment_date=payment_data.get("payment_date", datetime.now()),
            amount=payment_data.get("amount", 0),
            payment_method=payment_data.get("payment_method", ""),
            notes=payment_data.get("notes", "")
        )
        db.add(payment)

        # Update customer's amount_paid
        customer.amount_paid += payment_data.get("amount", 0)

        # Update payment status based on amount paid
        if customer.amount_paid >= customer.total_amount:
            customer.payment_status = "Fully Paid"
        elif customer.amount_paid > 0:
            customer.payment_status = "Partially Paid"
        else:
            customer.payment_status = "Unpaid"

        # Update the updated_at timestamp
        customer.updated_at = datetime.now()

        db.commit()
        db.refresh(payment)
        return payment
    except Exception as e:
        db.rollback()
        print(f"Error adding payment to customer {customer_id}: {e}")
        raise


def get_customer_payments(db: Session, customer_id: int):
    """Get all payments for a specific customer"""
    return db.query(models.CustomerPayment).filter(
        models.CustomerPayment.customer_id == customer_id
    ).order_by(models.CustomerPayment.payment_date.desc()).all()


def search_customers(db: Session, query: str):
    """Search for customers by name, code, or phone number"""
    from sqlalchemy import or_

    search_term = f"%{query}%"

    customers = db.query(models.Customer).filter(
        or_(
            models.Customer.customer_code.ilike(search_term),
            models.Customer.customer_name.ilike(search_term),
            models.Customer.phone_no.ilike(search_term)
        )
    ).all()

    return customers


def search_enquiries(db: Session, query: str):
    """Search for enquiries by customer name, phone number, or enquiry number

    Args:
        db: Database session
        query: Search query string

    Returns:
        List of enquiries matching the search criteria
    """
    from sqlalchemy import or_

    # Convert query to lowercase for case-insensitive search
    search_term = f"%{query}%"

    # Search in relevant columns
    enquiries = db.query(models.Enquiry).filter(
        or_(
            models.Enquiry.enquiry_number.ilike(search_term),
            models.Enquiry.customer_name.ilike(search_term),
            models.Enquiry.phone_no.ilike(search_term),
            models.Enquiry.requirements.ilike(search_term)
        )
    ).all()

    return enquiries

def get_paginated_enquiries(db: Session, limit: int = 50, offset: int = 0):
    """Get paginated enquiries ordered by date descending"""
    return db.query(models.Enquiry).order_by(models.Enquiry.date.desc()).offset(offset).limit(limit).all()

def get_total_enquiries_count(db: Session):
    """Get total count of enquiries for pagination"""
    return db.query(models.Enquiry).count()

def get_filtered_enquiries(db: Session, filters: dict, limit: int = 50, offset: int = 0):
    """Get filtered and paginated enquiries"""
    query = db.query(models.Enquiry)

    if "customer_name" in filters and filters["customer_name"]:
        query = query.filter(models.Enquiry.customer_name.ilike(f"%{filters['customer_name']}%"))

    if "date_from" in filters and filters["date_from"]:
        query = query.filter(models.Enquiry.date >= filters["date_from"])

    if "date_to" in filters and filters["date_to"]:
        query = query.filter(models.Enquiry.date <= filters["date_to"])

    if "quotation_given" in filters:
        query = query.filter(models.Enquiry.quotation_given == filters["quotation_given"])

    return query.order_by(models.Enquiry.date.desc()).offset(offset).limit(limit).all()

def get_filtered_enquiries_count(db: Session, filters: dict):
    """Get count of filtered enquiries"""
    query = db.query(models.Enquiry)

    if "customer_name" in filters and filters["customer_name"]:
        query = query.filter(models.Enquiry.customer_name.ilike(f"%{filters['customer_name']}%"))

    if "date_from" in filters and filters["date_from"]:
        query = query.filter(models.Enquiry.date >= filters["date_from"])

    if "date_to" in filters and filters["date_to"]:
        query = query.filter(models.Enquiry.date <= filters["date_to"])

    if "quotation_given" in filters:
        query = query.filter(models.Enquiry.quotation_given == filters["quotation_given"])

    return query.count()



def get_customer(db: Session, customer_id: int):
    """Get a customer by ID"""
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        return None
    return customer


def get_customer_payments(db: Session, customer_id: int):
    """Get all payments for a specific customer"""
    return db.query(models.CustomerPayment).filter(
        models.CustomerPayment.customer_id == customer_id
    ).order_by(models.CustomerPayment.payment_date.desc()).all()