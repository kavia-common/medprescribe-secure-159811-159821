from __future__ import annotations

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_config
from src.api.models import User
from src.api.schemas import Token, UserLogin, UserRead
from src.api.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from src.api.services.solana import create_sign_message, verify_signature

router = APIRouter(prefix="/auth", tags=["auth"])


# PUBLIC_INTERFACE
def _extract_token_from_header(authorization: Optional[str]) -> str:
    """Extract a bearer token from the Authorization header."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header format")
    return parts[1]


# PUBLIC_INTERFACE
def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
) -> User:
    """Resolve current user from JWT bearer token.

    Raises:
        401 if token is invalid or user not found.
    """
    token = _extract_token_from_header(authorization)
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token (no subject)")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


# PUBLIC_INTERFACE
@router.post(
    "/login",
    response_model=Token,
    summary="User login",
    description="Authenticate a user (doctor or pharmacist) and return a JWT bearer token.",
)
def login(data: UserLogin, db: Session = Depends(get_db), settings=Depends(get_config)) -> Token:
    """Authenticate with username/password and return a JWT token."""
    user: Optional[User] = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    token_claims = {"sub": str(user.id), "username": user.username, "role": user.role}
    access_token = create_access_token(token_claims, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return Token(access_token=access_token, token_type="bearer")


# PUBLIC_INTERFACE
@router.get(
    "/me",
    response_model=UserRead,
    summary="Current user",
    description="Return the current authenticated user's profile.",
)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return the current authenticated user."""
    return UserRead.model_validate(current_user)


# PUBLIC_INTERFACE
@router.get(
    "/solana/message",
    summary="Get Solana sign message (stub)",
    description="Return a message and nonce for a wallet to sign for authentication (stubbed).",
    tags=["blockchain", "auth"],
)
def solana_message(address: str) -> dict:
    """Return a signable message and nonce for a given Solana address."""
    return create_sign_message(address)


# PUBLIC_INTERFACE
@router.post(
    "/solana/verify",
    summary="Verify Solana signature (stub)",
    description="Accept a signature for a message and return a boolean indicating verification (stubbed).",
    tags=["blockchain", "auth"],
)
def solana_verify(payload: dict) -> dict:
    """Verify a Solana signature for a provided message (stub)."""
    address = payload.get("address")
    message = payload.get("message")
    signature = payload.get("signature")
    ok = verify_signature(signature=signature, message=message, address=address)
    return {"verified": ok}
