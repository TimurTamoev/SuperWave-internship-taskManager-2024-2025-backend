from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class SentEmailResponse(BaseModel):
    id: int
    user_id: int
    attachment_id: Optional[int] = None
    to_email: str
    subject: str
    body: str
    original_email_uid: Optional[str] = None
    original_email_subject: Optional[str] = None
    success: bool
    smtp_response: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: datetime
    response_template_id: Optional[int] = None

    class Config:
        from_attributes = True


class SentEmailStats(BaseModel):
    total_sent: int
    successful: int
    failed: int
    recent_emails: list[SentEmailResponse]

