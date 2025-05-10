from pydantic import BaseModel
from datetime import date
from typing import Optional


class ItemCreate(BaseModel):
    date: date
    item_name: str
    hsn_code: str
    gst_rate: float
    purchase_price_per_unit: Optional[float] = 0.0
    quantity: int
    unit_of_measurement: Optional[str] = "No.s"
    supplier_name: Optional[str] = None
    supplier_gst_number: Optional[str] = None


class Item(ItemCreate):
    item_code: str

    class Config:
        from_attributes = True  # Updated from orm_mode=True for Pydantic V2
