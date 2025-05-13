from sqlalchemy import Column, String, Integer, Float, Date, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime


class InventoryItem(Base):
    __tablename__ = "inventory"

    item_code = Column(String, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    item_name = Column(String, nullable=False)
    hsn_code = Column(String, nullable=False)
    gst_rate = Column(Float, nullable=False)
    purchase_price_per_unit = Column(Float)
    margin = Column(Float, default=20.0)  # Default margin of 20%
    quantity = Column(Integer, nullable=False)
    unit_of_measurement = Column(String, default="No.s")  # Default unit is No.s (Numbers)
    supplier_name = Column(String)
    supplier_gst_number = Column(String)


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, index=True, nullable=False)
    date = Column(Date, nullable=False)
    customer_name = Column(String, nullable=False)
    customer_address = Column(String)
    customer_phone = Column(String)
    customer_email = Column(String)
    customer_gst = Column(String)
    payment_method = Column(String)
    subtotal = Column(Float, nullable=False)
    total_gst = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0)  # Amount paid so far
    payment_status = Column(String, default="Unpaid")  # Unpaid, Partially Paid, Fully Paid
    invoice_type = Column(String, default="product")  # "product" or "service"
    pdf_path = Column(String)

    # Relationship with invoice items and payments
    items = relationship("InvoiceItem", back_populates="invoice")
    payments = relationship("Payment", back_populates="invoice")
    services = relationship("Service", back_populates="invoice")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    item_code = Column(String, nullable=False)
    item_name = Column(String, nullable=False)
    hsn_code = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    discounted_subtotal = Column(Float, nullable=False)
    gst_rate = Column(Float, nullable=False)
    gst_amount = Column(Float, nullable=False)
    total = Column(Float, nullable=False)

    # Relationship with invoice
    invoice = relationship("Invoice", back_populates="items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    payment_date = Column(DateTime, default=datetime.now)
    amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)
    notes = Column(String)

    # Relationship with invoice
    invoice = relationship("Invoice", back_populates="payments")


class SalesCounter(Base):
    __tablename__ = "sales_counter"

    id = Column(Integer, primary_key=True, index=True)
    total_sales = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    service_code = Column(String, unique=True, index=True, nullable=False)
    date = Column(Date, nullable=False, default=datetime.now().date())
    service_name = Column(String, nullable=False)
    employee_name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    gst_rate = Column(Float, default=18.0)
    payment_method = Column(String)
    payment_status = Column(String, default="Unpaid")  # Unpaid, Partially Paid, Fully Paid
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    pdf_path = Column(String)

    # Relationship with invoice
    invoice = relationship("Invoice", back_populates="services")


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    quote_number = Column(String, unique=True, index=True, nullable=False)
    date = Column(Date, nullable=False, default=datetime.now().date())
    customer_name = Column(String, nullable=False)
    customer_address = Column(String)
    customer_phone = Column(String)
    customer_email = Column(String)
    subtotal = Column(Float, nullable=False)
    total_gst = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    asked_about = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    pdf_path = Column(String)

    # Relationship with quotation items
    items = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")


class QuotationItem(Base):
    __tablename__ = "quotation_items"

    id = Column(Integer, primary_key=True, index=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=False)
    item_code = Column(String, nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    gst_rate = Column(Float, nullable=False)
    gst_amount = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    item_type = Column(String, nullable=False)  # "product" or "service"

    # Relationship with quotation
    quotation = relationship("Quotation", back_populates="items")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String)
    role = Column(String, nullable=False, default="employee")  # "top_user", "admin" or "employee"
    first_login = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)


class Enquiry(Base):
    __tablename__ = "enquiries"

    id = Column(Integer, primary_key=True, index=True)
    enquiry_number = Column(String, unique=True, index=True, nullable=False)
    date = Column(Date, nullable=False, default=datetime.now().date())
    customer_name = Column(String, nullable=False)
    phone_no = Column(String, nullable=False)
    address = Column(String)
    requirements = Column(Text)
    quotation_given = Column(Boolean, default=False)
    quotation_amount = Column(Float, nullable=True)
    quotation_file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String, unique=True, index=True, nullable=False)
    date = Column(Date, nullable=False, default=datetime.now().date())
    customer_name = Column(String, nullable=False)
    phone_no = Column(String, nullable=False)
    address = Column(String)
    product_description = Column(Text)
    payment_method = Column(String)
    payment_status = Column(String, default="Unpaid")  # Unpaid, Partially Paid, Fully Paid
    total_amount = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship with customer payments
    payments = relationship("CustomerPayment", back_populates="customer", cascade="all, delete-orphan")


class CustomerPayment(Base):
    __tablename__ = "customer_payments"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    payment_date = Column(DateTime, default=datetime.now)
    amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)
    notes = Column(String)

    # Relationship with customer
    customer = relationship("Customer", back_populates="payments")
