from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class EmailConnectionTest(BaseModel):
    email: Optional[EmailStr] = None
    email_password: Optional[str] = None
    imap_server: str = Field(default="imap.mail.ru", description="IMAP server address")
    imap_port: int = Field(default=993, description="IMAP server port")


class EmailConnectionResponse(BaseModel):
    success: bool
    message: str
    email: Optional[str] = None
    details: Optional[str] = None


class EmailAttachment(BaseModel):
    filename: str
    content_type: str
    size: int


class EmailMessage(BaseModel):
    uid: str
    subject: str
    from_address: str
    to_addresses: List[str]
    date: Optional[datetime] = None
    body_plain: Optional[str] = None
    body_html: Optional[str] = None
    has_attachments: bool = False
    attachments: List[EmailAttachment] = []
    is_read: bool = False


class EmailFetchRequest(BaseModel):
    folder: str = Field(default="INBOX", description="Папка почты, из которой получаем email'ы")
    limit: int = Field(default=50, ge=1, le=100, description="Минимальное и максимальное количество писем")
    search_criteria: Optional[str] = Field(default="ALL", description="IMAP критерия поиска(например, 'НЕПРОСМОТРЕННЫЕ', 'ВСЕ', 'ОТ example@mail.com')")
    include_body: bool = Field(default=True, description="Включить тело письма в ответе")


class EmailFetchResponse(BaseModel):
    success: bool
    message: str
    total_count: int
    emails: List[EmailMessage] = []


class EmailFolderInfo(BaseModel):
    name: str
    message_count: Optional[int] = None


class EmailFoldersResponse(BaseModel):
    success: bool
    folders: List[EmailFolderInfo] = []

