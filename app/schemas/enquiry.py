from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class EnquiryBase(BaseModel):
    customer_name: str
    phone_no: str
    address: Optional[str] = None
    requirements: Optional[str] = None
    quotation_given: bool = False
    quotation_amount: Optional[float] = None
    quotation_file_path: Optional[str] = None


class EnquiryCreate(EnquiryBase):
    date: Optional[date] = None


class EnquiryUpdate(BaseModel):
    customer_name: Optional[str] = None
    phone_no: Optional[str] = None
    address: Optional[str] = None
    requirements: Optional[str] = None
    quotation_given: Optional[bool] = None
    quotation_amount: Optional[float] = None
    quotation_file_path: Optional[str] = None


class Enquiry(EnquiryBase):
    id: int
    enquiry_number: str
    date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Updated from orm_mode=True for Pydantic V2


