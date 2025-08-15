#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

import httpx


DEFAULT_BASE_URL = "https://vscode-internal-22919-beta.beta01.cloud.kavia.ai:3001"


@dataclass
class EndpointResult:
    ok: bool
    status: Optional[int] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class SmokeTestReport:
    base_url: str
    health: EndpointResult
    login_doctor: EndpointResult
    login_pharmacist: EndpointResult
    me_doctor: EndpointResult
    code_generate: EndpointResult
    create_prescription: EndpointResult
    list_prescriptions: EndpointResult
    public_verify: EndpointResult
    pharmacist_verify: EndpointResult

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)


def _bearer(token: Optional[str]) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test for MedPrescribe backend")
    parser.add_argument("--base-url", default=os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL), help="Backend base URL")
    parser.add_argument("--timeout", type=float, default=float(os.getenv("BACKEND_TIMEOUT", "15")), help="Request timeout seconds")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification")
    parser.add_argument("--username-doctor", default=os.getenv("SMOKE_DOCTOR_USER", "drdev"))
    parser.add_argument("--password-doctor", default=os.getenv("SMOKE_DOCTOR_PASS", "doctor123"))
    parser.add_argument("--username-pharm", default=os.getenv("SMOKE_PHARM_USER", "pharmdev"))
    parser.add_argument("--password-pharm", default=os.getenv("SMOKE_PHARM_PASS", "pharmacist123"))
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    timeout = httpx.Timeout(args.timeout)
    verify_opt = not args.insecure

    report = SmokeTestReport(
        base_url=base,
        health=EndpointResult(ok=False),
        login_doctor=EndpointResult(ok=False),
        login_pharmacist=EndpointResult(ok=False),
        me_doctor=EndpointResult(ok=False),
        code_generate=EndpointResult(ok=False),
        create_prescription=EndpointResult(ok=False),
        list_prescriptions=EndpointResult(ok=False),
        public_verify=EndpointResult(ok=False),
        pharmacist_verify=EndpointResult(ok=False),
    )

    try:
        with httpx.Client(base_url=base, timeout=timeout, verify=verify_opt) as client:
            # Health
            try:
                r = client.get("/")
                report.health.status = r.status_code
                if r.status_code == 200 and r.json().get("message") == "Healthy":
                    report.health.ok = True
                    report.health.details = r.json()
                else:
                    report.health.error = f"Unexpected response: {r.text}"
            except Exception as e:
                report.health.error = str(e)

            # Login doctor
            doctor_token: Optional[str] = None
            try:
                r = client.post("/auth/login", json={"username": args.username_doctor, "password": args.password_doctor})
                report.login_doctor.status = r.status_code
                if r.status_code == 200:
                    data = r.json()
                    doctor_token = data.get("access_token")
                    report.login_doctor.ok = bool(doctor_token)
                    report.login_doctor.details = {"token_type": data.get("token_type")}
                    if not doctor_token:
                        report.login_doctor.error = "No access_token in response"
                else:
                    report.login_doctor.error = f"{r.status_code}: {r.text}"
            except Exception as e:
                report.login_doctor.error = str(e)

            # Login pharmacist
            pharm_token: Optional[str] = None
            try:
                r = client.post("/auth/login", json={"username": args.username_pharm, "password": args.password_pharm})
                report.login_pharmacist.status = r.status_code
                if r.status_code == 200:
                    data = r.json()
                    pharm_token = data.get("access_token")
                    report.login_pharmacist.ok = bool(pharm_token)
                    report.login_pharmacist.details = {"token_type": data.get("token_type")}
                    if not pharm_token:
                        report.login_pharmacist.error = "No access_token in response"
                else:
                    report.login_pharmacist.error = f"{r.status_code}: {r.text}"
            except Exception as e:
                report.login_pharmacist.error = str(e)

            # Me (doctor) - get user id
            doctor_id: Optional[int] = None
            try:
                r = client.get("/auth/me", headers=_bearer(doctor_token))
                report.me_doctor.status = r.status_code
                if r.status_code == 200:
                    me = r.json()
                    doctor_id = me.get("id")
                    report.me_doctor.ok = doctor_id is not None
                    report.me_doctor.details = {"id": doctor_id, "username": me.get("username"), "role": me.get("role")}
                    if doctor_id is None:
                        report.me_doctor.error = "Missing id in /auth/me"
                else:
                    report.me_doctor.error = f"{r.status_code}: {r.text}"
            except Exception as e:
                report.me_doctor.error = str(e)

            # Generate code (no auth required)
            code: Optional[str] = None
            try:
                r = client.get("/prescriptions/code", params={"length": 8})
                report.code_generate.status = r.status_code
                if r.status_code == 200:
                    code = r.json().get("code")
                    report.code_generate.ok = bool(code)
                    report.code_generate.details = {"code": code}
                    if not code:
                        report.code_generate.error = "No code in response"
                else:
                    report.code_generate.error = f"{r.status_code}: {r.text}"
            except Exception as e:
                report.code_generate.error = str(e)

            # Create prescription (doctor)
            pres_id: Optional[int] = None
            try:
                payload = {
                    "code": code or "CODE1234",
                    "patient_name": "John Doe",
                    "patient_dob": "1990-01-01",
                    "medication_name": "Atorvastatin",
                    "dosage": "10mg once daily",
                    "quantity": 30,
                    "instructions": "Take with dinner",
                    "status": "created",
                    "offchain_hash": None,
                    # If doctor_id is None (e.g., login failed), fall back to 1 to attempt creation anyway.
                    "doctor_id": doctor_id or 1,
                    "pharmacist_id": None,
                }
                r = client.post("/prescriptions", headers=_bearer(doctor_token), json=payload)
                report.create_prescription.status = r.status_code
                if r.status_code in (200, 201):
                    pres = r.json()
                    pres_id = pres.get("id")
                    report.create_prescription.ok = pres_id is not None
                    report.create_prescription.details = {"id": pres_id, "code": pres.get("code")}
                    if pres_id is None:
                        report.create_prescription.error = "No id in created prescription"
                else:
                    report.create_prescription.error = f"{r.status_code}: {r.text}"
            except Exception as e:
                report.create_prescription.error = str(e)

            # List prescriptions (doctor)
            try:
                r = client.get("/prescriptions", headers=_bearer(doctor_token))
                report.list_prescriptions.status = r.status_code
                if r.status_code == 200:
                    rows = r.json()
                    report.list_prescriptions.ok = isinstance(rows, list)
                    # provide a small summary
                    first = rows[0] if rows else None
                    report.list_prescriptions.details = {
                        "count": len(rows),
                        "first_id": first.get("id") if isinstance(first, dict) else None,
                    }
                else:
                    report.list_prescriptions.error = f"{r.status_code}: {r.text}"
            except Exception as e:
                report.list_prescriptions.error = str(e)

            # Public verify by code
            try:
                # If creation failed, try verifying last generated code anyway.
                verify_code = (report.create_prescription.details or {}).get("code") or code
                r = client.get(f"/verify/code/{verify_code}")
                report.public_verify.status = r.status_code
                if r.status_code == 200:
                    data = r.json()
                    report.public_verify.ok = data.get("code") == verify_code
                    report.public_verify.details = {"id": data.get("id"), "status": data.get("status")}
                    if not report.public_verify.ok:
                        report.public_verify.error = "Returned code mismatch"
                else:
                    report.public_verify.error = f"{r.status_code}: {r.text}"
            except Exception as e:
                report.public_verify.error = str(e)

            # Pharmacist verify by code
            try:
                verify_code = (report.create_prescription.details or {}).get("code") or code
                r = client.post(f"/verify/code/{verify_code}", headers=_bearer(pharm_token))
                report.pharmacist_verify.status = r.status_code
                if r.status_code == 200:
                    data = r.json()
                    report.pharmacist_verify.ok = data.get("code") == verify_code
                    report.pharmacist_verify.details = {"id": data.get("id"), "status": data.get("status")}
                    if not report.pharmacist_verify.ok:
                        report.pharmacist_verify.error = "Returned code mismatch"
                else:
                    report.pharmacist_verify.error = f"{r.status_code}: {r.text}"
            except Exception as e:
                report.pharmacist_verify.error = str(e)

    except Exception as e:
        # Global failure (e.g., DNS or TLS)
        report.health.error = f"Client init error: {e}"

    print(report.to_json())
    # Exit non-zero if anything critical failed
    critical = [
        report.health.ok,
        report.login_doctor.ok,
        report.login_pharmacist.ok,
        report.me_doctor.ok,
        report.code_generate.ok,
        report.create_prescription.ok,
        report.list_prescriptions.ok,
        report.public_verify.ok,
        report.pharmacist_verify.ok,
    ]
    return 0 if all(critical) else 1


if __name__ == "__main__":
    sys.exit(main())
