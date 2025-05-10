from pydantic import BaseModel
from datetime import date
from typing import Optional


class ServiceCreate(BaseModel):
    date: date
    service_code: Optional[str] = None  # Will be auto-generated if not provided
    service_name: str
    employee_name: str
    description: Optional[str] = None
    price: float
    gst_rate: float = 18.0  # Default GST rate for services
    payment_method: Optional[str] = None
    payment_status: Optional[str] = "Unpaid"


class ServiceUpdate(BaseModel):
    date: Optional[date] = None
    service_name: Optional[str] = None
    employee_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    gst_rate: Optional[float] = None
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None


class Service(ServiceCreate):
    id: int
    service_code: str
    invoice_id: Optional[int] = None
    pdf_path: Optional[str] = None

    class Config:
        from_attributes = True  # Updated from orm_mode=True for Pydantic V2
