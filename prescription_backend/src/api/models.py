from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.api.db import Base

USER_ROLES = ("doctor", "pharmacist", "admin")
PRESCRIPTION_STATUS = ("created", "dispensed", "revoked", "expired")


class User(Base):
    """User account model for doctors, pharmacists, and admins."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="ux_users_email"),
        UniqueConstraint("username", name="ux_users_username"),
        CheckConstraint(f"role IN {USER_ROLES}", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role: Mapped[str] = mapped_column(String, nullable=False, default="doctor")
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    solana_wallet: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    prescriptions_prescribed: Mapped[List["Prescription"]] = relationship(
        "Prescription",
        foreign_keys="Prescription.doctor_id",
        back_populates="doctor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    prescriptions_dispensed: Mapped[List["Prescription"]] = relationship(
        "Prescription",
        foreign_keys="Prescription.pharmacist_id",
        back_populates="pharmacist",
    )
    verifications: Mapped[List["VerificationLog"]] = relationship(
        "VerificationLog", foreign_keys="VerificationLog.verifier_user_id", back_populates="verifier"
    )


class Prescription(Base):
    """Prescription model representing a prescribing event by a doctor."""

    __tablename__ = "prescriptions"
    __table_args__ = (
        UniqueConstraint("code", name="ux_prescriptions_code"),
        CheckConstraint(f"status IN {PRESCRIPTION_STATUS}", name="ck_prescriptions_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    pharmacist_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    patient_name: Mapped[str] = mapped_column(String, nullable=False)
    patient_dob: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    medication_name: Mapped[str] = mapped_column(String, nullable=False)
    dosage: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="created")
    offchain_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    dispensed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    doctor: Mapped["User"] = relationship(
        "User", foreign_keys=[doctor_id], back_populates="prescriptions_prescribed"
    )
    pharmacist: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[pharmacist_id], back_populates="prescriptions_dispensed"
    )
    verification_logs: Mapped[List["VerificationLog"]] = relationship(
        "VerificationLog", back_populates="prescription", cascade="all, delete-orphan", passive_deletes=True
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="prescription", cascade="all, delete-orphan", passive_deletes=True
    )


class VerificationLog(Base):
    """Verification attempt log for prescriptions."""

    __tablename__ = "verification_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prescription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    verifier_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    method: Mapped[str] = mapped_column(String, nullable=False)
    success: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    prescription: Mapped["Prescription"] = relationship("Prescription", back_populates="verification_logs")
    verifier: Mapped[Optional["User"]] = relationship("User", back_populates="verifications")


class Transaction(Base):
    """Blockchain transaction metadata (e.g., Solana)."""

    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("tx_signature", name="ux_transactions_signature"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prescription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tx_signature: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    network: Mapped[str] = mapped_column(String, nullable=False)  # devnet, testnet, mainnet
    status: Mapped[str] = mapped_column(String, nullable=False)  # submitted, confirmed, failed
    slot: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    prescription: Mapped["Prescription"] = relationship("Prescription", back_populates="transactions")
