from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.api.models import Prescription, User
from src.api.schemas import (
    PrescriptionCreate,
    PrescriptionRead,
    PrescriptionStatusUpdate,
)
from src.api.security import is_admin, is_doctor, is_pharmacist
from src.api.utils.ids import build_qr_payload, generate_prescription_code

from .auth import get_current_user

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])


# PUBLIC_INTERFACE
@router.get(
    "/code",
    summary="Generate a unique prescription code",
    description="Generate a new unique prescription code that is not used in the database.",
)
def generate_code(db: Session = Depends(get_db), length: int = Query(default=8, ge=6, le=16)) -> dict:
    """Generate a unique prescription code not present in the database."""
    attempt = 0
    while True:
        code = generate_prescription_code(length=length)
        exists = db.query(Prescription.id).filter(Prescription.code == code).first()
        if not exists:
            return {"code": code}
        attempt += 1
        if attempt > 20:
            raise HTTPException(status_code=500, detail="Failed to generate a unique code")


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=PrescriptionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create prescription",
    description="Create a new prescription (doctor or admin only).",
)
def create_prescription(
    payload: PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PrescriptionRead:
    """Create a new prescription. Only doctors and admins can create."""
    if not (is_doctor(current_user.role) or is_admin(current_user.role)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only doctors or admins can create prescriptions")

    # Ensure unique code
    exists = db.query(Prescription.id).filter(Prescription.code == payload.code).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prescription code already exists")

    # Force doctor_id to be the current user if they are a doctor
    doctor_id = current_user.id if is_doctor(current_user.role) else payload.doctor_id

    pres = Prescription(
        code=payload.code,
        doctor_id=doctor_id,
        pharmacist_id=payload.pharmacist_id,
        patient_name=payload.patient_name,
        patient_dob=payload.patient_dob,
        medication_name=payload.medication_name,
        dosage=payload.dosage,
        quantity=payload.quantity,
        instructions=payload.instructions,
        status=payload.status or "created",
        offchain_hash=payload.offchain_hash,
        issued_at=datetime.now(timezone.utc),
    )
    db.add(pres)
    db.commit()
    db.refresh(pres)
    return PrescriptionRead.model_validate(pres)


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=List[PrescriptionRead],
    summary="List prescriptions",
    description="List prescriptions for the current user. Doctors see their own; pharmacists see assigned; admins see all.",
)
def list_prescriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: Optional[str] = Query(default=None, description="Filter by status"),
    doctor_id: Optional[int] = Query(default=None, description="Admin-only: filter by doctor_id"),
    pharmacist_id: Optional[int] = Query(default=None, description="Admin-only: filter by pharmacist_id"),
) -> List[PrescriptionRead]:
    """List prescriptions with role-aware filtering."""
    query = db.query(Prescription)
    if is_admin(current_user.role):
        if doctor_id is not None:
            query = query.filter(Prescription.doctor_id == doctor_id)
        if pharmacist_id is not None:
            query = query.filter(Prescription.pharmacist_id == pharmacist_id)
    elif is_doctor(current_user.role):
        query = query.filter(Prescription.doctor_id == current_user.id)
    elif is_pharmacist(current_user.role):
        query = query.filter(Prescription.pharmacist_id == current_user.id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized role")

    if status_filter:
        query = query.filter(Prescription.status == status_filter)

    rows = query.order_by(Prescription.created_at.desc()).all()
    return [PrescriptionRead.model_validate(r) for r in rows]


# PUBLIC_INTERFACE
@router.get(
    "/{prescription_id}",
    response_model=PrescriptionRead,
    summary="Get prescription by ID",
    description="Return prescription details if visible to the current user.",
)
def get_prescription(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PrescriptionRead:
    """Return prescription details with role-based access."""
    pres: Optional[Prescription] = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")

    if is_admin(current_user.role) or pres.doctor_id == current_user.id or pres.pharmacist_id == current_user.id:
        return PrescriptionRead.model_validate(pres)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view this prescription")


# PUBLIC_INTERFACE
@router.get(
    "/{prescription_id}/qr",
    summary="Get QR payload for prescription",
    description="Return a QR payload string that encodes the prescription code.",
)
def get_qr_payload(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return a simple QR payload for the prescription code."""
    pres: Optional[Prescription] = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")

    if not (is_admin(current_user.role) or pres.doctor_id == current_user.id or pres.pharmacist_id == current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    return {"code": pres.code, "payload": build_qr_payload(pres.code), "format": "text/uri"}


# PUBLIC_INTERFACE
@router.patch(
    "/{prescription_id}/status",
    response_model=PrescriptionRead,
    summary="Update prescription status",
    description="Update the prescription status (pharmacist: 'dispensed'; doctor/admin: 'revoked' or 'expired').",
)
def update_status(
    prescription_id: int,
    payload: PrescriptionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PrescriptionRead:
    """Update prescription status with role-based rules."""
    pres: Optional[Prescription] = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")

    new_status = payload.status.lower().strip()

    if new_status == "dispensed":
        if not is_pharmacist(current_user.role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only pharmacists can mark as dispensed")
        pres.status = "dispensed"
        pres.pharmacist_id = payload.pharmacist_id or current_user.id
        pres.dispensed_at = datetime.now(timezone.utc)
    elif new_status in {"revoked", "expired"}:
        if not (is_doctor(current_user.role) or is_admin(current_user.role)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only doctors/admin can revoke/expire")
        pres.status = new_status
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported status")

    pres.updated_at = datetime.now(timezone.utc)
    db.add(pres)
    db.commit()
    db.refresh(pres)
    return PrescriptionRead.model_validate(pres)
