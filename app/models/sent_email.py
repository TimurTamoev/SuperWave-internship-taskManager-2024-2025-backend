from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SentEmail(Base):
    """История отправленных email ответов"""
    __tablename__ = "sent_emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    attachment_id = Column(Integer, ForeignKey("email_response_attachments.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Данные отправленного email
    to_email = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    
    # Данные исходного письма
    original_email_uid = Column(String, nullable=True, index=True)
    original_email_subject = Column(String, nullable=True)
    
    # Статус отправки
    success = Column(Boolean, nullable=False, default=False)
    smtp_response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Метаданные
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    response_template_id = Column(Integer, ForeignKey("response_templates.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user = relationship("User", backref="sent_emails")
    attachment = relationship("EmailResponseAttachment", backref="sent_emails")
    response_template = relationship("ResponseTemplate", backref="sent_emails")

