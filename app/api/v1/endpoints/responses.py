from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.response_template import ResponseTemplate, EmailResponseAttachment
from app.schemas.response_template import (
    ResponseTemplateCreate,
    ResponseTemplateUpdate,
    ResponseTemplateResponse,
    EmailResponseAttachmentCreate,
    EmailResponseAttachmentResponse,
    EmailWithAttachedResponse,
)

router = APIRouter()


@router.post(
    "/response/create",
    summary="Создать шаблон ответа",
    tags=["Response Templates"],
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
    summary="Получить все шаблоны ответов текущего пользователя",
    tags=["Response Templates"],
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
        .filter(ResponseTemplate.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return templates


@router.get(
    "/response/{template_id}",
    summary="Получить шаблон ответа по ID",
    tags=["Response Templates"],
    response_model=ResponseTemplateResponse,
)
async def get_response_template(
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
    
    return template


@router.put(
    "/response/{template_id}",
    summary="Обновить шаблон ответа",
    tags=["Response Templates"],
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
    tags=["Response Templates"],
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
    summary="Прикрепить шаблон ответа к письму",
    tags=["Response Templates", "Email Attachments"],
    response_model=EmailResponseAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def attach_response_to_email(
    attachment_data: EmailResponseAttachmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = (
        db.query(ResponseTemplate)
        .filter(
            ResponseTemplate.id == attachment_data.response_template_id,
            ResponseTemplate.user_id == current_user.id
        )
        .first()
    )
    
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
    
    # Создать связь
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
    
    return attachment


@router.get(
    "/response/attachments/email/{email_uid}",
    summary="Получить все ответы, прикрепленные к письму",
    tags=["Response Templates", "Email Attachments"],
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
    summary="Получить все письма с прикрепленным шаблоном",
    tags=["Response Templates", "Email Attachments"],
    response_model=List[EmailWithAttachedResponse],
)
async def get_template_attachments(
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
    tags=["Response Templates", "Email Attachments"],
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
    tags=["Response Templates", "Email Attachments"],
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

