from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    email_password: Optional[str] = Field(None, description="User's email password for inbox access")


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    email_password: Optional[str] = Field(None, description="User's email password for inbox access")
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    email_password: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    @model_validator(mode='after')
    def decrypt_email_password_field(self):
        """Decrypt email password when returning user data"""
        if self.email_password:
            from app.core.security import decrypt_email_password
            self.email_password = decrypt_email_password(self.email_password)
        return self

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
