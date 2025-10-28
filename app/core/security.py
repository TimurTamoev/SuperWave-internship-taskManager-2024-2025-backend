from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import hashlib
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create a Fernet cipher from the encryption key
def _get_fernet() -> Fernet:
    """Generate a Fernet cipher from the encryption key"""
    # Ensure the key is 32 bytes
    key = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def encrypt_email_password(plain_password: str) -> str:
    """Encrypt email password for secure storage"""
    if not plain_password:
        return None
    fernet = _get_fernet()
    encrypted = fernet.encrypt(plain_password.encode())
    return encrypted.decode()


def decrypt_email_password(encrypted_password: str) -> Optional[str]:
    """Decrypt email password for use"""
    if not encrypted_password:
        return None
    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception:
        return None
