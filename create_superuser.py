"""
Script to create the first superuser for the application.
Run this once to bootstrap your application with an admin account.

Usage:
    python create_superuser.py
"""
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from app.core.database import Base

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


def create_superuser():
    """Create a superuser account"""
    db: Session = SessionLocal()
    
    try:
        # Check if any superuser already exists
        existing_superuser = db.query(User).filter(User.is_superuser == True).first()
        if existing_superuser:
            print(f"⚠️  Superuser already exists: {existing_superuser.username}")
            response = input("Do you want to create another superuser? (y/n): ")
            if response.lower() != 'y':
                print("Aborted.")
                return
        
        print("\n🔐 Creating Superuser Account\n")
        print("=" * 50)
        
        # Get user input
        email = input("Email: ").strip()
        if not email:
            print("❌ Email is required!")
            return
        
        username = input("Username: ").strip()
        if not username:
            print("❌ Username is required!")
            return
        
        full_name = input("Full Name (optional): ").strip() or None
        
        password = input("Password (min 8 characters): ").strip()
        if len(password) < 8:
            print("❌ Password must be at least 8 characters!")
            return
        
        password_confirm = input("Confirm Password: ").strip()
        if password != password_confirm:
            print("❌ Passwords do not match!")
            return
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            print(f"\n❌ User with this email or username already exists!")
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

