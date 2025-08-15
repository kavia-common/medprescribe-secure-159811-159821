# medprescribe-secure-159811-159821

Backend: FastAPI (prescription_backend)
Database: SQLite
Frontend: Next.js (in a separate container)

Overview

This FastAPI service exposes REST endpoints for authentication, prescription creation and listing, public verification by code, and pharmacist verification. It connects to a SQLite database via an environment variable and is CORS-enabled for local development and preview hosts.

Quick start (backend)

1) Create an environment file (.env) or export env vars
   - Required in real deployments:
     - SQLITE_DB: path to your SQLite file, e.g. /abs/path/to/prescription_database/myapp.db
     - SECRET_KEY: a strong random string for JWT signing
   - Optional (with sensible defaults):
     - ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, CORS_ORIGINS, CORS_ORIGIN_REGEX, APP_NAME, API_DESCRIPTION, API_VERSION

   Example .env:
   APP_NAME="MedPrescribe Backend"
   API_DESCRIPTION="Backend API for creating and verifying medical prescriptions with Solana integration."
   API_VERSION="0.1.0"

   # IMPORTANT: Point to the DB initialized by prescription_database/init_db.py to get seeded users
   SQLITE_DB="/absolute/path/to/medprescribe-secure-159811-159820/prescription_database/myapp.db"

   # Replace with a strong secret in real deployments
   SECRET_KEY="dev-secret-change-me"

   ACCESS_TOKEN_EXPIRE_MINUTES="60"
   JWT_ALGORITHM="HS256"

   # Either an explicit CSV allow-list and/or a regex for previews
   CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,https://vscode-internal-22919-beta.beta01.cloud.kavia.ai:3000"
   CORS_ORIGIN_REGEX="^https?:\\/\\/(localhost|127\\.0\\.0\\.1)(:\\d+)?$|^https:\\/\\/[a-z0-9\\-\\.]+\\.cloud\\.kavia\\.ai(:\\d+)?$"

2) Install dependencies
   - See prescription_backend/requirements.txt
   - Example with pip:
     - python3 -m venv .venv && source .venv/bin/activate
     - pip install -r prescription_backend/requirements.txt

3) Run the backend
   - uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   - OpenAPI/Swagger UI: http://localhost:8000/docs
   - Health check: http://localhost:8000/

CORS configuration

- The backend enables CORS via FastAPI’s CORSMiddleware using values derived from environment variables.
- Defaults allow common local and preview origins:
  - http://localhost:3000
  - http://127.0.0.1:3000
  - https://vscode-internal-22919-beta.beta01.cloud.kavia.ai:3000
- You can configure:
  - CORS_ORIGINS: comma-separated list of exact origins (e.g., http://localhost:3000,https://preview.example.com:3000)
  - CORS_ORIGIN_REGEX: regex to match dynamic preview hosts (defaults to allow *.cloud.kavia.ai and localhost)

Environment variables (backend)

- SQLITE_DB: Absolute or relative path to the SQLite database file. If you want seeded users, ensure it points to the DB file created by the database container’s init_db.py.
- SECRET_KEY: Secret for JWT signing. Replace the development default for any real deployment.
- ACCESS_TOKEN_EXPIRE_MINUTES: Token expiry in minutes (default 60).
- JWT_ALGORITHM: Algorithm for JWT signing (default HS256).
- CORS_ORIGINS: CSV of allowed CORS origins (overrides defaults).
- CORS_ORIGIN_REGEX: Regex for allowed origins (useful for previews).
- APP_NAME, API_DESCRIPTION, API_VERSION: Optional metadata shown in OpenAPI.

Frontend API base URL (Next.js)

- In the frontend container, set:
  - NEXT_PUBLIC_BACKEND_URL to the base URL of this backend.
  - Examples:
    - NEXT_PUBLIC_BACKEND_URL="http://localhost:8000"
    - NEXT_PUBLIC_BACKEND_URL="https://vscode-internal-22919-beta.beta01.cloud.kavia.ai:3001"
- Frontend code calls APIs using this base URL:
  - fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/auth/login`, { ... })

Seeded accounts (development)

The database initializer seeds two users:

- Doctor
  - username: drdev
  - email: doctor@example.com
  - password: doctor123
- Pharmacist
  - username: pharmdev
  - email: pharmacist@example.com
  - password: pharmacist123

Make sure the backend’s SQLITE_DB points to the database file initialized in the database container to use these credentials.

API walkthrough

- Health
  - GET / → {"message": "Healthy"}

- Auth
  - POST /auth/login → returns Token { access_token, token_type }
    - Body: { "username": "drdev", "password": "doctor123" }
  - GET /auth/me → returns UserRead for the current bearer token
  - GET /auth/solana/message?address=... → returns a message + nonce to sign (stub)
  - POST /auth/solana/verify → verifies signature (stub)

- Prescriptions (bearer token required except code generation may be guarded by role in the future)
  - GET /prescriptions/code?length=8 → returns { code }
  - POST /prescriptions → create a new prescription (doctor or admin)
    - Example body:
      {
        "code": "ABCD1234",
        "patient_name": "John Doe",
        "patient_dob": "1990-01-01",
        "medication_name": "Atorvastatin",
        "dosage": "10mg once daily",
        "quantity": 30,
        "instructions": "Take with dinner",
        "status": "created",
        "offchain_hash": null,
        "doctor_id": 1,
        "pharmacist_id": null
      }
  - GET /prescriptions → list prescriptions (doctors see their own; pharmacists see assigned; admins see all)
  - GET /prescriptions/{id} → get by ID (role-restricted)
  - GET /prescriptions/{id}/qr → returns a simple payload string to render a QR

- Verify
  - GET /verify/code/{code} → public verify by code; returns details if status permits
  - POST /verify/code/{code} → pharmacist-only verify by code

Typical usage flows

- Doctor flow:
  1) Login with drdev/doctor123
  2) Generate a code via GET /prescriptions/code
  3) Create a prescription via POST /prescriptions (doctor_id will be your user ID)
  4) Share the code (and optionally QR) with the patient/pharmacist

- Pharmacist flow:
  1) Login with pharmdev/pharmacist123
  2) Verify a code via POST /verify/code/{code}
  3) If UI permits, update prescription status via PATCH /prescriptions/{id}/status with { "status": "dispensed" }

Notes

- SQLAlchemy models are defined in src/api/models.py and tables are created on startup if missing.
- To use seeded credentials, always run the DB initializer in the database container and point SQLITE_DB to that file.
- The service uses JWT bearer tokens signed with SECRET_KEY. Replace defaults for real deployments.
