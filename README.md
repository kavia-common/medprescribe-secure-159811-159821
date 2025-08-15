# medprescribe-secure-159811-159821

Backend: FastAPI (prescription_backend)
Database: SQLite
Frontend: Next.js (in a separate container)

Quick start (backend)
1) Create an environment file
   - Copy prescription_backend/.env.example to prescription_backend/.env
   - Set values for:
     - SQLITE_DB: path to your SQLite file (e.g., ./data/medprescribe.db)
     - SECRET_KEY: a strong random string for JWT signing
     - (Optional) CORS_ORIGINS and/or CORS_ORIGIN_REGEX to control allowed frontend origins

2) Install dependencies (handled by CI/automation in most cases)
   - See prescription_backend/requirements.txt

3) Run the backend (example)
   - uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   - Swagger UI at: http://localhost:8000/docs

CORS configuration
- The backend enables CORS via FastAPI’s CORSMiddleware.
- Defaults allow common local and preview origins:
  - http://localhost:3000
  - http://127.0.0.1:3000
  - https://vscode-internal-22919-beta.beta01.cloud.kavia.ai:3000
- You can configure:
  - CORS_ORIGINS: CSV of exact origins (e.g., http://localhost:3000,https://preview.example.com:3000)
  - CORS_ORIGIN_REGEX: Regex to match dynamic preview hosts (defaults to allow *.cloud.kavia.ai and localhost)

Environment variables (backend)
- SQLITE_DB: Path to the SQLite database file. Required in real deployments.
- SECRET_KEY: Secret for JWT signing. Required in real deployments.
- ACCESS_TOKEN_EXPIRE_MINUTES: Token expiry in minutes (default 60).
- JWT_ALGORITHM: Algorithm for JWT signing (default HS256).
- CORS_ORIGINS: CSV list of allowed CORS origins (overrides defaults).
- CORS_ORIGIN_REGEX: Regex for allowed origins (useful for previews).

Frontend API base URL (Next.js)
- In the frontend container, set:
  - NEXT_PUBLIC_API_BASE to the base URL of this backend.
  - Examples:
    - NEXT_PUBLIC_API_BASE="http://localhost:8000"
    - NEXT_PUBLIC_API_BASE="https://vscode-internal-22919-beta.beta01.cloud.kavia.ai:3001"
- Frontend code should call APIs using this base URL:
  - fetch(`${process.env.NEXT_PUBLIC_API_BASE}/auth/login`, { ... })

Notes
- The SQLite database container is represented by a file path specified via SQLITE_DB.
- Do not hardcode secrets/paths in code; always use environment variables.
- See prescription_backend/src/api for API modules, routers, and models.
