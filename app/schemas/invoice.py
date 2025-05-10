from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class InvoiceItem(BaseModel):
    item_code: str
    item_name: str
    hsn_code: str = "N/A"
    price: float
    quantity: int
    discount_percent: float = 0
    discount_amount: float = 0
    discounted_subtotal: float
    gst_rate: float
    gst_amount: float
    total: float
    item_type: str = "product"  # product, service, or combination


class InvoiceCreate(BaseModel):
    invoice_number: str
    date: datetime
    customer_name: str
    customer_gst: Optional[str] = None
    customer_address: str
    customer_phone: str
    customer_email: Optional[str] = None
    payment_method: str
    payment_status: str
    amount_paid: float
    items: List[InvoiceItem]
    subtotal: float
    total_discount: float
    discounted_subtotal: float
    total_gst: float
    total_amount: float
    pdf_path: Optional[str] = None
    invoice_type: str = "product"


class Invoice(InvoiceCreate):
    id: int

    class Config:
        from_attributes = True  # Updated from orm_mode=True for Pydantic V2


class PaymentCreate(BaseModel):
    amount: float
    payment_method: str
    notes: Optional[str] = None
    payment_date: datetime = Field(default_factory=datetime.now)
