from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ResponseTemplate(Base):
    __tablename__ = "response_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    send_response = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="response_templates")


class EmailResponseAttachment(Base):
    __tablename__ = "email_response_attachments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email_uid = Column(String, nullable=False, index=True) 
    email_subject = Column(String, nullable=True)
    email_from = Column(String, nullable=True)
    response_template_id = Column(Integer, ForeignKey("response_templates.id", ondelete="CASCADE"), nullable=False)
    attached_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)

    user = relationship("User", backref="email_attachments")
    response_template = relationship("ResponseTemplate", backref="email_attachments")