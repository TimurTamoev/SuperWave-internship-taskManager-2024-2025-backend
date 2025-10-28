"""
Скрипт для создания пользователя-админа, которому доступна возможность управления пользователями.
Использование:
    python create_superuser.py
"""

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from app.core.database import Base

Base.metadata.create_all(bind=engine)


def create_superuser():
    db: Session = SessionLocal()

    try:
        existing_superuser = db.query(User).filter(User.is_superuser == True).first()
        if existing_superuser:
            print(f"Админ уже существует: {existing_superuser.username}")
            response = input("Хотите ли вы создать нового админа? (y/n): ")
            if response.lower() != "y":
                print("Aborted.")
                return

        print("\nСоздание аккаунта админа\n")

        email = input("Адрес электронной почты: ").strip()
        if not email:
            print("Адрес электронной почты обязателен.")
            return

        username = input("Имя Пользователя: ").strip()
        if not username:
            print("Имя пользователя обязательно.")
            return

        full_name = input("Полное имя(необязательно): ").strip() or None

        password = input("Пароль (минимальная величина - 8 символов): ").strip()
        if len(password) < 8:
            print("Пароль должен содержать минимум 8 символов.")
            return

        password_confirm = input("Введите пароль еще раз: ").strip()
        if password != password_confirm:
            print("Пароли не совпадают")
            return

        existing_user = (
            db.query(User)
            .filter((User.email == email) | (User.username == username))
            .first()
        )

        if existing_user:
            print(f"\nПользователь с таким email уже существует.")
            return

        # Create superuser
        hashed_password = get_password_hash(password)
        superuser = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True,
        )

        db.add(superuser)
        db.commit()
        db.refresh(superuser)

        print("\n" + "=" * 50)
        print("✅ Superuser created successfully!")
        print("=" * 50)
        print(f"ID: {superuser.id}")
        print(f"Email: {superuser.email}")
        print(f"Username: {superuser.username}")
        print(f"Full Name: {superuser.full_name or 'N/A'}")
        print(f"Is Active: {superuser.is_active}")
        print(f"Is Superuser: {superuser.is_superuser}")
        print("=" * 50)
        print("\n🎉 You can now login with these credentials!")

    except Exception as e:
        print(f"\n❌ Error creating superuser: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_superuser()
