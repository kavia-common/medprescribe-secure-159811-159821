# OpenAPI Regeneration and Smoke Test

This document explains how to regenerate the OpenAPI spec and perform a basic smoke test against a running backend.

## Prerequisites
- Python 3.10+
- Virtual environment with backend requirements installed:
  - python3 -m venv .venv && source .venv/bin/activate
  - pip install -r prescription_backend/requirements.txt

## Regenerate OpenAPI

Option A: Use the helper script
- source .venv/bin/activate
- PYTHONPATH=medprescribe-secure-159811-159821/prescription_backend \\
  python medprescribe-secure-159811-159821/prescription_backend/src/api/generate_openapi.py

Option B: Use the utility runner
- source .venv/bin/activate
- python medprescribe-secure-159811-159821/prescription_backend/utils/regenerate_openAPI.py

The OpenAPI file is written to:
- medprescribe-secure-159811-159821/prescription_backend/interfaces/openapi.json

## Smoke Test

Run the smoke test against the running backend (default URL is the preview instance):

- source .venv/bin/activate
- python medprescribe-secure-159811-159821/prescription_backend/utils/smoke_test_backend.py \\
    --base-url https://vscode-internal-22919-beta.beta01.cloud.kavia.ai:3001

Options:
- --insecure: skip TLS verification if needed
- Override default credentials via env:
  - SMOKE_DOCTOR_USER, SMOKE_DOCTOR_PASS
  - SMOKE_PHARM_USER, SMOKE_PHARM_PASS
- Override via flags:
  - --username-doctor, --password-doctor, --username-pharm, --password-pharm

The script prints a JSON report; it returns exit code 0 if all checks pass, otherwise 1.

Endpoints exercised:
- GET / (health)
- POST /auth/login (doctor and pharmacist)
- GET /auth/me (doctor)
- GET /prescriptions/code
- POST /prescriptions (doctor)
- GET /prescriptions (doctor)
- GET /verify/code/{code} (public)
- POST /verify/code/{code} (pharmacist)
