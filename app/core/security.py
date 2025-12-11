"""
HeinerCast Security Module
JWT, Password Hashing, and Encryption
"""
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet

from app.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== Password Functions ====================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


# ==================== JWT Functions ====================

def create_access_token(
    user_id: UUID,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create an access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.access_token_expire_hours)
    
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(
    user_id: UUID,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a refresh token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        from app.core.exceptions import TokenExpiredError
        raise TokenExpiredError()
    except jwt.InvalidTokenError:
        from app.core.exceptions import InvalidTokenError
        raise InvalidTokenError()


def verify_access_token(token: str) -> dict:
    """Verify an access token and return payload"""
    payload = decode_token(token)
    if payload.get("type") != "access":
        from app.core.exceptions import InvalidTokenError
        raise InvalidTokenError()
    return payload


def verify_refresh_token(token: str) -> dict:
    """Verify a refresh token and return payload"""
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        from app.core.exceptions import InvalidTokenError
        raise InvalidTokenError()
    return payload


# ==================== API Key Functions ====================

def generate_api_key() -> Tuple[str, str]:
    """
    Generate a new API key.
    Returns tuple of (plain_key, hashed_key)
    """
    plain_key = "hc_" + secrets.token_urlsafe(32)
    hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()
    return plain_key, hashed_key


def hash_api_key(plain_key: str) -> str:
    """Hash an API key for storage"""
    return hashlib.sha256(plain_key.encode()).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    return hashlib.sha256(plain_key.encode()).hexdigest() == hashed_key


# ==================== Encryption Functions ====================

def _get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption"""
    # Ensure key is exactly 32 bytes, then base64 encode
    key_bytes = settings.encryption_key.encode()[:32].ljust(32, b'\0')
    key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(key)


def encrypt_api_key(plain_key: str) -> str:
    """Encrypt an API key for secure storage"""
    if not plain_key:
        return ""
    f = _get_fernet()
    encrypted = f.encrypt(plain_key.encode())
    return encrypted.decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key"""
    if not encrypted_key:
        return ""
    f = _get_fernet()
    decrypted = f.decrypt(encrypted_key.encode())
    return decrypted.decode()


# ==================== Sanitization Functions ====================

def sanitize_text(text: str) -> str:
    """Remove potentially dangerous characters from text"""
    if not text:
        return ""
    # Remove HTML tags and script content
    import re
    # Remove script tags and content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove null bytes
    text = text.replace('\x00', '')
    return text.strip()


def sanitize_filename(filename: str) -> str:
    """Create a safe filename"""
    if not filename:
        return "unnamed"
    import re
    # Keep only alphanumeric, dots, hyphens, and underscores
    safe = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # Limit length
    return safe[:255]


# ==================== Token Generation ====================

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)
