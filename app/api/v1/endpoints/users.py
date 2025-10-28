from turtle import title
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.dependencies import get_current_user, get_current_active_superuser
from app.core.security import get_password_hash, encrypt_email_password, decrypt_email_password
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()

"""
Пока не уверен начсет этого эндпоинта тк в процессе разработки переосмыслил иерархию пользователей. 
@router.get(
    "/user/get/me",
    summary="Получить информацию о текущем пользователе. Доступ возможен только для админа",
    tags=["Команды админа"],
    response_model=UserResponse,
)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
"""


@router.get(
    "/user/get/all",
    summary="Получить информацию о всех пользователях. Доступно только для админа",
    tags=["Команды админа"],
    response_model=List[UserResponse],
)
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_active_superuser),
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users


"""
Только админ может создавать пользователей и проводить какие-либо манипуляции с ними. 
Ввиду специфики назначения сервиса.
"""


@router.get(
    "/user/get/{user_id}",
    summary="Получиить информацию по его id. Доступно только для админа",
    tags=["Команды админа"],
    response_model=UserResponse,
)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_active_superuser),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.patch(
    "/user/deactivate/{user_id}",
    summary="Деактивировать пользователя по его id",
    tags=["Команды админа"],
    response_model=UserResponse,
)
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_active_superuser),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.id == current_superuser.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself"
        )

    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.patch(
    "/user/activate/{user_id}",
    summary="Активировать пользователя по его id",
    tags=["Команды админа"],
    response_model=UserResponse,
)
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_active_superuser),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


@router.patch(
    "/user/update/{user_id}",
    summary="Изменить информацию о пользователе",
    tags=["Команды админа"],
    response_model=UserResponse,
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_active_superuser),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user_data.email and user_data.email != user.email:
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        user.email = user_data.email

    if user_data.username and user_data.username != user.username:
        existing = db.query(User).filter(User.username == user_data.username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )
        user.username = user_data.username

    if user_data.full_name is not None:
        user.full_name = user_data.full_name

    if user_data.password:
        user.hashed_password = get_password_hash(user_data.password)
    
    if user_data.email_password is not None:
        user.email_password = encrypt_email_password(user_data.email_password) if user_data.email_password else None

    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    if user_data.is_superuser is not None:
        user.is_superuser = user_data.is_superuser

    db.commit()
    db.refresh(user)
    return user


@router.delete(
    "/user/delete/{user_id}",
    summary="Удалить пользвателя по его id",
    tags=["Команды админа"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_active_superuser),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.id == current_superuser.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself"
        )

    db.delete(user)
    db.commit()
    return None
