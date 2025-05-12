from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


class CustomerPaymentBase(BaseModel):
    amount: float
    payment_method: str
    notes: Optional[str] = None
    payment_date: datetime = Field(default_factory=datetime.now)


class CustomerPaymentCreate(CustomerPaymentBase):
    pass


class CustomerPayment(CustomerPaymentBase):
    id: int
    customer_id: int

    class Config:
        from_attributes = True


class CustomerBase(BaseModel):
    customer_name: str
    phone_no: str
    address: Optional[str] = None
    product_description: Optional[str] = None
    payment_method: Optional[str] = None
    payment_status: str = "Unpaid"
    total_amount: float
    amount_paid: float = 0.0


class CustomerCreate(CustomerBase):
    date: Optional[date] = None


class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = None
    phone_no: Optional[str] = None
    address: Optional[str] = None
    product_description: Optional[str] = None
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    total_amount: Optional[float] = None
    amount_paid: Optional[float] = None
    date: Optional[date] = None


class Customer(CustomerBase):
    id: int
    customer_code: str
    date: date
    created_at: datetime
    updated_at: datetime
    payments: List[CustomerPayment] = []

    class Config:
        from_attributes = True
