from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: str = "employee"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    id: int
    role: str
    first_login: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True  # Updated from orm_mode=True for Pydantic V2


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
