from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.core.security import decrypt_email_password
from app.services.email_service import EmailService
from app.schemas.email import (
    EmailConnectionTest,
    EmailConnectionResponse,
    EmailFetchRequest,
    EmailFetchResponse,
    EmailFoldersResponse,
)

router = APIRouter()


@router.post(
    "/email/test/connection",
    summary="Проверить подключение к почтовому серверу",
    tags=["Email"],
    response_model=EmailConnectionResponse,
)
async def test_email_connection(
    connection_data: Optional[EmailConnectionTest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if connection_data and connection_data.email and connection_data.email_password:
        email_address = connection_data.email
        email_password = connection_data.email_password
    else:
        if not current_user.email_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="К профилю пользователя не привязана почта. Пожалуйста проверьте данные профиля.",
            )
        
        email_address = current_user.email
        email_password = decrypt_email_password(current_user.email_password)
        if not email_password:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка в расшифровывании пароля.",
            )
    
    imap_server = connection_data.imap_server if connection_data else "imap.mail.ru"
    imap_port = connection_data.imap_port if connection_data else 993
    
    try:
        email_service = EmailService(
            email_address=email_address,
            password=email_password,
            imap_server=imap_server,
            imap_port=imap_port,
        )
        
        success, message, details = email_service.test_connection()
        
        return EmailConnectionResponse(
            success=success,
            message=message,
            email=email_address,
            details=details,
        )
    except Exception as e:
        return EmailConnectionResponse(
            success=False,
            message=f"Неожиданная ошибка: {str(e)}",
            email=email_address,
        )


@router.post(
    "/fetch",
    summary="Получить письма из почтового ящика",
    tags=["Email"],
    response_model=EmailFetchResponse,
)
async def fetch_emails(
    fetch_request: EmailFetchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.email_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="В профиле отсутствует пароль. Проверьте данные аккаунта.",
        )
    
    email_password = decrypt_email_password(current_user.email_password)
    if not email_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка в расшифровке пароля для почты",
        )
    
    try:
        email_service = EmailService(
            email_address=current_user.email,
            password=email_password,
            imap_server="imap.mail.ru",
            imap_port=993,
        )
        
        success, message = email_service.connect()
        if not success:
            return EmailFetchResponse(
                success=False,
                message=message,
                total_count=0,
                emails=[],
            )
        
        try:
            emails = email_service.fetch_emails(
                folder=fetch_request.folder,
                limit=fetch_request.limit,
                search_criteria=fetch_request.search_criteria,
                include_body=fetch_request.include_body,
            )
            
            return EmailFetchResponse(
                success=True,
                message=f"Успешно получены {len(emails)} emails",
                total_count=len(emails),
                emails=emails,
            )
        finally:
            email_service.disconnect()
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении email'ов: {str(e)}",
        )


@router.get(
    "/email/folders",
    summary="Получить список папок в почтовом ящике",
    tags=["Email"],
    response_model=EmailFoldersResponse,
)
async def get_email_folders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.email_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="В профиле отсутствует пароль от почты. Пожалуйста проверьте свой аккаунт.",
        )
    
    email_password = decrypt_email_password(current_user.email_password)
    if not email_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка в расшифровке пароля.",
        )
    
    try:
        email_service = EmailService(
            email_address=current_user.email,
            password=email_password,
            imap_server="imap.mail.ru",
            imap_port=993,
        )
        
        success, message = email_service.connect()
        if not success:
            return EmailFoldersResponse(
                success=False,
                folders=[],
            )
        
        try:
            folders = email_service.list_folders()
            return EmailFoldersResponse(
                success=True,
                folders=folders,
            )
        finally:
            email_service.disconnect()
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения папок: {str(e)}",
        )


@router.get(
    "/email/me",
    summary="Получить информацию о настроенной почте текущего пользователя",
    tags=["Email"],
)
async def get_my_email_info(
    current_user: User = Depends(get_current_user),
):
    has_email_password = current_user.email_password is not None
    
    return {
        "email": current_user.email,
        "has_email_password": has_email_password,
        "email_configured": has_email_password,
    }

