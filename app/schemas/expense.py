from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List


class ExpensePaymentBase(BaseModel):
    amount: float
    payment_method: str
    notes: Optional[str] = None
    payment_date: datetime = Field(default_factory=datetime.now)


class ExpensePaymentCreate(ExpensePaymentBase):
    pass


class ExpensePayment(ExpensePaymentBase):
    id: int
    expense_id: int

    class Config:
        from_attributes = True


class ExpenseCreate(BaseModel):
    date: date
    expense_code: Optional[str] = None  # Will be auto-generated if not provided
    expense_type: str
    vendor_name: str
    vendor_gst: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_phone: Optional[str] = None
    description: Optional[str] = None
    amount: float
    gst_rate: float = 0.0
    gst_amount: float = 0.0
    total_amount: float
    amount_paid: float = 0.0
    payment_method: str
    payment_status: str = "Paid"
    category: Optional[str] = None
    receipt_path: Optional[str] = None
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    date: Optional[date] = None
    expense_type: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_gst: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_phone: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    gst_rate: Optional[float] = None
    gst_amount: Optional[float] = None
    total_amount: Optional[float] = None
    amount_paid: Optional[float] = None
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    category: Optional[str] = None
    receipt_path: Optional[str] = None
    notes: Optional[str] = None


class Expense(ExpenseCreate):
    id: int
    expense_code: str
    created_at: datetime
    updated_at: datetime
    payments: List[ExpensePayment] = []

    class Config:
        from_attributes = True  # Updated from orm_mode=True for Pydantic V2
