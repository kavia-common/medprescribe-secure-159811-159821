from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ORMBase(BaseModel):
    """Base for Pydantic models configured to read data from ORM objects."""

    model_config = {"from_attributes": True}


# -----------------------------
# Authentication Schemas
# -----------------------------
class Token(ORMBase):
    """JWT bearer token."""
    access_token: str = Field(..., description="Encoded JWT access token")
    token_type: str = Field("bearer", description="Token type, typically 'bearer'")


class TokenData(ORMBase):
    """Data extracted from an access token."""
    sub: Optional[str] = Field(None, description="Subject (e.g., username or user ID)")
    exp: Optional[int] = Field(None, description="Expiration timestamp")


# -----------------------------
# User Schemas
# -----------------------------
class UserBase(ORMBase):
    """Common properties for user models."""
    role: str = Field(..., description="User role: doctor|pharmacist|admin")
    email: EmailStr = Field(..., description="Unique user email")
    username: str = Field(..., description="Unique username")
    solana_wallet: Optional[str] = Field(None, description="Linked Solana wallet address")
    is_active: int = Field(1, description="1 if active; 0 otherwise")


class UserCreate(UserBase):
    """Payload for creating a new user."""
    password: str = Field(..., description="Raw password to be hashed and stored")


class UserRead(UserBase):
    """User data visible to API consumers."""
    id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class UserLogin(ORMBase):
    """Login payload."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


# -----------------------------
# Prescription Schemas
# -----------------------------
class PrescriptionBase(ORMBase):
    """Common fields for prescriptions."""
    code: str = Field(..., description="Unique prescription code")
    patient_name: str = Field(..., description="Patient full name")
    patient_dob: Optional[str] = Field(None, description="Patient date of birth")
    medication_name: str = Field(..., description="Prescribed medication")
    dosage: Optional[str] = Field(None, description="Dosage instructions")
    quantity: Optional[int] = Field(None, description="Quantity to dispense")
    instructions: Optional[str] = Field(None, description="Additional instructions")
    status: str = Field("created", description="created|dispensed|revoked|expired")
    offchain_hash: Optional[str] = Field(None, description="Hash of off-chain data for integrity")


class PrescriptionCreate(PrescriptionBase):
    """Payload to create a prescription."""
    doctor_id: int = Field(..., description="Prescribing doctor's user ID")
    pharmacist_id: Optional[int] = Field(None, description="Assigned pharmacist user ID (optional)")


class PrescriptionRead(PrescriptionBase):
    """Prescription details returned by the API."""
    id: int = Field(..., description="Prescription ID")
    doctor_id: int = Field(..., description="Prescribing doctor's user ID")
    pharmacist_id: Optional[int] = Field(None, description="Assigned pharmacist user ID")
    issued_at: Optional[datetime] = Field(None, description="Issue timestamp")
    dispensed_at: Optional[datetime] = Field(None, description="Dispensed timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last modification timestamp")


class PrescriptionStatusUpdate(ORMBase):
    """Payload to update prescription status."""
    status: str = Field(..., description="New status for prescription")
    pharmacist_id: Optional[int] = Field(None, description="Pharmacist performing the action (optional)")


# -----------------------------
# Verification Log Schemas
# -----------------------------
class VerificationLogCreate(ORMBase):
    """Payload to record a verification attempt."""
    prescription_id: int = Field(..., description="ID of the prescription being verified")
    verifier_user_id: Optional[int] = Field(None, description="User ID of verifier if known")
    method: str = Field(..., description="Verification method: 'code' or 'qr'")
    success: int = Field(0, description="1 if successful; 0 otherwise")
    reason: Optional[str] = Field(None, description="Failure reason if any")
    ip_address: Optional[str] = Field(None, description="Request IPv4/IPv6 address")
    user_agent: Optional[str] = Field(None, description="Client user agent")


class VerificationLogRead(VerificationLogCreate):
    """Verification log entry returned by the API."""
    id: int = Field(..., description="Log entry ID")
    created_at: datetime = Field(..., description="Creation timestamp")


# -----------------------------
# Transaction Schemas
# -----------------------------
class TransactionCreate(ORMBase):
    """Payload to create a blockchain transaction record."""
    prescription_id: int = Field(..., description="Related prescription ID")
    tx_signature: str = Field(..., description="Unique blockchain transaction signature")
    network: str = Field(..., description="Network (devnet, testnet, mainnet)")
    status: str = Field(..., description="Transaction status (submitted, confirmed, failed)")
    slot: Optional[int] = Field(None, description="Blockchain slot number")
    error: Optional[str] = Field(None, description="Error message if failed")


class TransactionRead(TransactionCreate):
    """Transaction record returned by the API."""
    id: int = Field(..., description="Transaction ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    confirmed_at: Optional[datetime] = Field(None, description="Confirmation timestamp")
