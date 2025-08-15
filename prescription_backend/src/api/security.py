from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.api.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


# PUBLIC_INTERFACE
def get_password_hash(password: str) -> str:
    """Return a secure hash for a password using bcrypt."""
    return pwd_context.hash(password)


# PUBLIC_INTERFACE
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a raw password against its hashed value."""
    return pwd_context.verify(plain_password, hashed_password)


# PUBLIC_INTERFACE
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token embedding the provided data.

    Args:
        data: Claims to encode into the JWT payload (e.g., {'sub': 'username'}).
        expires_delta: Optional timedelta for token expiration. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta is not None else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# PUBLIC_INTERFACE
def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token.

    Raises:
        JWTError: If the token is invalid or expired.

    Returns:
        The decoded token payload as a dictionary.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise e


# PUBLIC_INTERFACE
def is_admin(role: str) -> bool:
    """Return True if the role corresponds to an admin user."""
    return role == "admin"


# PUBLIC_INTERFACE
def is_doctor(role: str) -> bool:
    """Return True if the role corresponds to a doctor user."""
    return role == "doctor"


# PUBLIC_INTERFACE
def is_pharmacist(role: str) -> bool:
    """Return True if the role corresponds to a pharmacist user."""
    return role == "pharmacist"
