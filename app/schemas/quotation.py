from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date


class QuotationItemBase(BaseModel):
    item_code: str
    item_name: str
    quantity: int
    price: float
    gst_rate: float
    gst_amount: float
    total: float
    item_type: str  # "product" or "service"


class QuotationItemCreate(QuotationItemBase):
    pass


class QuotationItem(QuotationItemBase):
    id: int
    quotation_id: int

    class Config:
        from_attributes = True


class QuotationBase(BaseModel):
    customer_name: str
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    subtotal: float
    total_gst: float
    total_amount: float
    asked_about: Optional[str] = None


class QuotationCreate(QuotationBase):
    quote_date: date = datetime.now().date()
    items: List[QuotationItemCreate]


class Quotation(QuotationBase):
    id: int
    quote_number: str
    date: date
    created_at: datetime
    pdf_path: Optional[str] = None
    items: List[QuotationItem] = []

    class Config:
        from_attributes = True
