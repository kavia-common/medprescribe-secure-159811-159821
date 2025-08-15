from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import get_settings
from src.api.db import init_db
from src.api.routers import auth_router, prescriptions_router, verify_router

settings = get_settings()

# Define OpenAPI tag groups for documentation clarity
openapi_tags = [
    {
        "name": "health",
        "description": "Service health and status endpoints.",
    },
    {
        "name": "auth",
        "description": "Authentication and token utilities.",
    },
    {
        "name": "users",
        "description": "User management endpoints.",
    },
    {
        "name": "prescriptions",
        "description": "Prescription creation and verification endpoints.",
    },
    {
        "name": "blockchain",
        "description": "Solana transaction and status endpoints.",
    },
]

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.API_DESCRIPTION,
    version=settings.VERSION,
    openapi_tags=openapi_tags,
)

# CORS setup - allows configuration via env (CORS_ORIGINS as comma separated list) or defaults to "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """
    FastAPI startup event handler.

    Initializes the database by creating tables for SQLAlchemy models if they do not exist.
    This ensures the backend can run even if the DB file is new (uses SQLITE_DB env var or defaults).
    """
    init_db()


# PUBLIC_INTERFACE
@app.get("/", tags=["health"], summary="Health Check", operation_id="health_check")
def health_check():
    """Return backend health status.

    Returns:
        JSON object with a message confirming the API is healthy.
    """
    return {"message": "Healthy"}


# Include application routers
app.include_router(auth_router)
app.include_router(prescriptions_router)
app.include_router(verify_router)
