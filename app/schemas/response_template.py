from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ResponseTemplateBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Заголовок шаблона ответа")
    body: str = Field(..., min_length=1, max_length=2000, description="Текст ответа")
    send_response: bool = Field(default=False, description="Отправлять ли ответ автоматически")


class ResponseTemplateCreate(ResponseTemplateBase):
    pass


class ResponseTemplateUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Заголовок шаблона ответа")
    body: Optional[str] = Field(None, min_length=1, max_length=2000, description="Текст ответа")
    send_response: Optional[bool] = Field(None, description="Отправлять ли ответ автоматически")


class ResponseTemplateResponse(ResponseTemplateBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmailResponseAttachmentCreate(BaseModel):
    email_uid: str = Field(..., description="UID письма из IMAP")
    response_template_id: int = Field(..., description="ID шаблона ответа")
    email_subject: Optional[str] = Field(None, description="Тема письма (опционально)")
    email_from: Optional[str] = Field(None, description="От кого письмо (опционально)")
    notes: Optional[str] = Field(None, description="Дополнительные заметки (опционально)")


class EmailResponseAttachmentResponse(BaseModel):
    id: int
    user_id: int
    email_uid: str
    email_subject: Optional[str] = None
    email_from: Optional[str] = None
    response_template_id: int
    attached_at: datetime
    notes: Optional[str] = None
    
    response_template: Optional[ResponseTemplateResponse] = None

    class Config:
        from_attributes = True


class EmailWithAttachedResponse(BaseModel):
    email_uid: str
    email_subject: Optional[str] = None
    email_from: Optional[str] = None
    attachment_id: int
    attached_at: datetime
    notes: Optional[str] = None
    response_template: ResponseTemplateResponse

