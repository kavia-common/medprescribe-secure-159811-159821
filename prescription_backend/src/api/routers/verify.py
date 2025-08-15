from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.api.models import Prescription, VerificationLog, User
from src.api.schemas import PrescriptionRead
from src.api.security import is_pharmacist

from .auth import get_current_user

router = APIRouter(prefix="/verify", tags=["prescriptions"])


def _log_verification(
    db: Session,
    prescription: Optional[Prescription],
    method: str,
    success: int,
    request: Request,
    verifier_user_id: Optional[int] = None,
    reason: Optional[str] = None,
) -> None:
    """Create a verification log entry."""
    ip = request.client.host if request and request.client else None
    ua = request.headers.get("user-agent") if request else None
    log = VerificationLog(
        prescription_id=prescription.id if prescription else 0,
        verifier_user_id=verifier_user_id,
        method=method,
        success=success,
        reason=reason,
        ip_address=ip,
        user_agent=ua,
    )
    db.add(log)
    db.commit()


# PUBLIC_INTERFACE
@router.get(
    "/code/{code}",
    response_model=PrescriptionRead,
    summary="Public verify by code",
    description="Public endpoint to verify a prescription by its code. Returns prescription details if verifiable.",
)
def public_verify_by_code(code: str, request: Request, db: Session = Depends(get_db)) -> PrescriptionRead:
    """Public verification by code. Returns details if found and not revoked/expired."""
    pres: Optional[Prescription] = db.query(Prescription).filter(Prescription.code == code).first()
    if not pres:
        _log_verification(db, None, "code", 0, request, reason="not_found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")

    valid = pres.status in {"created", "dispensed"}
    _log_verification(db, pres, "code", 1 if valid else 0, request, reason=None if valid else f"invalid_status:{pres.status}")

    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Prescription not verifiable (status={pres.status})")

    return PrescriptionRead.model_validate(pres)


# PUBLIC_INTERFACE
@router.post(
    "/code/{code}",
    response_model=PrescriptionRead,
    summary="Pharmacist verify by code",
    description="Pharmacist-only endpoint to verify and confirm a prescription by code.",
)
def pharmacist_verify_by_code(
    code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PrescriptionRead:
    """Pharmacist verification by code with logging."""
    if not is_pharmacist(current_user.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only pharmacists can confirm verification")

    pres: Optional[Prescription] = db.query(Prescription).filter(Prescription.code == code).first()
    if not pres:
        _log_verification(db, None, "code", 0, request, verifier_user_id=current_user.id, reason="not_found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")

    valid = pres.status in {"created", "dispensed"}
    _log_verification(
        db,
        pres,
        "code",
        1 if valid else 0,
        request,
        verifier_user_id=current_user.id,
        reason=None if valid else f"invalid_status:{pres.status}",
    )

    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Prescription not verifiable (status={pres.status})")

    return PrescriptionRead.model_validate(pres)
