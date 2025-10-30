from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.response_template import ResponseTemplate, EmailResponseAttachment
from app.models.sent_email import SentEmail
from app.schemas.response_template import (
    ResponseTemplateCreate,
    ResponseTemplateUpdate,
    ResponseTemplateResponse,
    EmailResponseAttachmentCreate,
    EmailResponseAttachmentResponse,
    EmailWithAttachedResponse,
)
from app.schemas.sent_email import SentEmailResponse, SentEmailStats
from app.services.smtp_service import SMTPService

router = APIRouter()


@router.post(
    "/response/create",
    summary="Создать шаблон ответа",
    tags=["Шаблоны ответов"],
    response_model=ResponseTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_response_template(
    template_data: ResponseTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_template = ResponseTemplate(
        user_id=current_user.id,
        title=template_data.title,
        body=template_data.body,
        send_response=template_data.send_response,
    )
    
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    
    return new_template


@router.get(
    "/response/all",
    summary="Получить все шаблоны ответов (доступны всем пользователям)",
    tags=["Шаблоны ответов"],
    response_model=List[ResponseTemplateResponse],
)
async def get_all_response_templates(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    templates = (
        db.query(ResponseTemplate)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return templates


@router.get(
    "/response/{template_id}",
    summary="Получить шаблон ответа по ID (доступен всем)",
    tags=["Шаблоны ответов"],
    response_model=ResponseTemplateResponse,
)
async def get_response_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(ResponseTemplate).filter(ResponseTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон ответа не найден",
        )
    
    return template


@router.put(
    "/response/{template_id}",
    summary="Обновить шаблон ответа",
    tags=["Шаблоны ответов"],
    response_model=ResponseTemplateResponse,
)
async def update_response_template(
    template_id: int,
    template_data: ResponseTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = (
        db.query(ResponseTemplate)
        .filter(
            ResponseTemplate.id == template_id,
            ResponseTemplate.user_id == current_user.id
        )
        .first()
    )
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон ответа не найден",
        )
    
    if template_data.title is not None:
        template.title = template_data.title
    
    if template_data.body is not None:
        template.body = template_data.body
    
    if template_data.send_response is not None:
        template.send_response = template_data.send_response
    
    db.commit()
    db.refresh(template)
    
    return template


@router.delete(
    "/response/{template_id}",
    summary="Удалить шаблон ответа",
    tags=["Шаблоны ответов"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_response_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = (
        db.query(ResponseTemplate)
        .filter(
            ResponseTemplate.id == template_id,
            ResponseTemplate.user_id == current_user.id
        )
        .first()
    )
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон ответа не найден",
        )
    
    db.delete(template)
    db.commit()
    
    return None


@router.post(
    "/response/attach",
    summary="Прикрепить шаблон ответа к письму (автоотправка если send_response=True)",
    tags=["Шаблоны ответов", "Прикрепление ответа к письму"],
    response_model=EmailResponseAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def attach_response_to_email(
    attachment_data: EmailResponseAttachmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(ResponseTemplate).filter(
        ResponseTemplate.id == attachment_data.response_template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон ответа не найден",
        )
    
    existing = (
        db.query(EmailResponseAttachment)
        .filter(
            EmailResponseAttachment.user_id == current_user.id,
            EmailResponseAttachment.email_uid == attachment_data.email_uid,
            EmailResponseAttachment.response_template_id == attachment_data.response_template_id
        )
        .first()
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Этот шаблон уже прикреплен к данному письму",
        )
    
    attachment = EmailResponseAttachment(
        user_id=current_user.id,
        email_uid=attachment_data.email_uid,
        email_subject=attachment_data.email_subject,
        email_from=attachment_data.email_from,
        response_template_id=attachment_data.response_template_id,
        notes=attachment_data.notes,
    )
    
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    
    # Если send_response=True, автоматически отправить email
    if template.send_response:
        # Получить email получателя
        recipient_email = attachment_data.email_from
        
        if not recipient_email:
            # Если email_from не указан, создать запись об ошибке
            sent_email = SentEmail(
                user_id=current_user.id,
                attachment_id=attachment.id,
                to_email="unknown",
                subject=template.title,
                body=template.body,
                original_email_uid=attachment_data.email_uid,
                original_email_subject=attachment_data.email_subject,
                success=False,
                error_message="Email отправителя не указан (email_from отсутствует)",
                response_template_id=template.id
            )
            db.add(sent_email)
            db.commit()
        else:
            # Отправить email через SMTP
            smtp_service = SMTPService()
            success, message = smtp_service.send_email(
                to_email=recipient_email,
                subject=template.title,
                body=template.body,
                reply_to_subject=attachment_data.email_subject,
                is_html=False
            )
            
            # Сохранить запись об отправке
            sent_email = SentEmail(
                user_id=current_user.id,
                attachment_id=attachment.id,
                to_email=recipient_email,
                subject=template.title if not attachment_data.email_subject else f"Re: {attachment_data.email_subject}",
                body=template.body,
                original_email_uid=attachment_data.email_uid,
                original_email_subject=attachment_data.email_subject,
                success=success,
                smtp_response=message if success else None,
                error_message=None if success else message,
                response_template_id=template.id
            )
            
            db.add(sent_email)
            db.commit()
    
    return attachment


@router.get(
    "/response/attachments/email/{email_uid}",
    summary="Получить все ответы, прикрепленные к письму",
    tags=["Шаблоны ответов", "Прикрепление ответа к письму"],
    response_model=List[EmailResponseAttachmentResponse],
)
async def get_email_attachments(
    email_uid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    attachments = (
        db.query(EmailResponseAttachment)
        .filter(
            EmailResponseAttachment.user_id == current_user.id,
            EmailResponseAttachment.email_uid == email_uid
        )
        .all()
    )
    
    return attachments


@router.get(
    "/response/attachments/template/{template_id}",
    summary="Получить все письма текущего пользователя с прикрепленным шаблоном",
    tags=["Шаблоны ответов", "Прикрепление ответа к письму"],
    response_model=List[EmailWithAttachedResponse],
)
async def get_template_attachments(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(ResponseTemplate).filter(ResponseTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон ответа не найден",
        )
    
    attachments = (
        db.query(EmailResponseAttachment)
        .filter(
            EmailResponseAttachment.user_id == current_user.id,
            EmailResponseAttachment.response_template_id == template_id
        )
        .all()
    )
    
    result = []
    for attachment in attachments:
        result.append(EmailWithAttachedResponse(
            email_uid=attachment.email_uid,
            email_subject=attachment.email_subject,
            email_from=attachment.email_from,
            attachment_id=attachment.id,
            attached_at=attachment.attached_at,
            notes=attachment.notes,
            response_template=template,
        ))
    
    return result


@router.delete(
    "/response/attachment/{attachment_id}",
    summary="Удалить связь между письмом и шаблоном ответа",
    tags=["Шаблоны ответов", "Прикрепление ответа к письму"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_email_attachment(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    attachment = (
        db.query(EmailResponseAttachment)
        .filter(
            EmailResponseAttachment.id == attachment_id,
            EmailResponseAttachment.user_id == current_user.id
        )
        .first()
    )
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Связь не найдена",
        )
    
    db.delete(attachment)
    db.commit()
    
    return None


@router.get(
    "/response/attachments/all",
    summary="Получить все связи письмо-ответ текущего пользователя",
    tags=["Шаблоны ответов", "Прикрепление ответа к письму"],
    response_model=List[EmailResponseAttachmentResponse],
)
async def get_all_attachments(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    attachments = (
        db.query(EmailResponseAttachment)
        .filter(EmailResponseAttachment.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return attachments


@router.get(
    "/sent-emails/all",
    summary="Получить историю всех отправленных email текущего пользователя",
    tags=["Отправленные Email"],
    response_model=List[SentEmailResponse],
)
async def get_sent_emails(
    skip: int = 0,
    limit: int = 100,
    success_only: bool = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(SentEmail).filter(SentEmail.user_id == current_user.id)
    
    if success_only is not None:
        query = query.filter(SentEmail.success == success_only)
    
    sent_emails = query.order_by(SentEmail.sent_at.desc()).offset(skip).limit(limit).all()
    
    return sent_emails


@router.get(
    "/sent-emails/stats",
    summary="Получить статистику отправленных email",
    tags=["Отправленные Email"],
    response_model=SentEmailStats,
)
async def get_sent_emails_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total_sent = db.query(SentEmail).filter(SentEmail.user_id == current_user.id).count()
    
    successful = db.query(SentEmail).filter(
        SentEmail.user_id == current_user.id,
        SentEmail.success == True
    ).count()
    
    failed = db.query(SentEmail).filter(
        SentEmail.user_id == current_user.id,
        SentEmail.success == False
    ).count()
    
    recent_emails = (
        db.query(SentEmail)
        .filter(SentEmail.user_id == current_user.id)
        .order_by(SentEmail.sent_at.desc())
        .limit(10)
        .all()
    )
    
    return SentEmailStats(
        total_sent=total_sent,
        successful=successful,
        failed=failed,
        recent_emails=recent_emails
    )


@router.get(
    "/sent-emails/{sent_email_id}",
    summary="Получить детали конкретного отправленного email",
    tags=["Отправленные Email"],
    response_model=SentEmailResponse,
)
async def get_sent_email(
    sent_email_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sent_email = (
        db.query(SentEmail)
        .filter(
            SentEmail.id == sent_email_id,
            SentEmail.user_id == current_user.id
        )
        .first()
    )
    
    if not sent_email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отправленный email не найден",
        )
    
    return sent_email


@router.post(
    "/smtp/test",
    summary="Проверить SMTP подключение",
    tags=["SMTP"],
)
async def test_smtp_connection(
    current_user: User = Depends(get_current_user),
):
    smtp_service = SMTPService()
    success, message = smtp_service.test_connection()
    
    return {
        "success": success,
        "message": message
    }

