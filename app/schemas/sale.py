from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SaleItem(BaseModel):
    item_code: str
    item_name: str
    price: float
    quantity: int
    discount_percent: float = 0
    gst_rate: float
    total: float
    item_type: str = "product"  # product, service, or combination


class SaleCreate(BaseModel):
    date: datetime
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    payment_method: str
    items: List[SaleItem]
    subtotal: float
    total_discount: float
    total_gst: float
    total_amount: float
    invoice_id: Optional[int] = None


class Sale(SaleCreate):
    id: int
    sale_number: str

    class Config:
        from_attributes = True  # Updated from orm_mode=True for Pydantic V2
