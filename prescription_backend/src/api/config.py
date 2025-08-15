import os
from typing import List, Optional

from dotenv import load_dotenv

# Load variables from a .env file if present. The orchestrator will set actual env values.
load_dotenv()


class Settings:
    """Runtime configuration for the backend API loaded from environment variables.

    Environment variables:
        - APP_NAME: Optional app display name.
        - API_DESCRIPTION: Optional description for API docs.
        - API_VERSION: Semantic version string for the API.
        - SQLITE_DB: Absolute or relative path to the SQLite database file (required in real deployments).
        - SECRET_KEY: Secret used to sign JWTs (required in real deployments).
        - ACCESS_TOKEN_EXPIRE_MINUTES: Token expiry in minutes (default 60).
        - JWT_ALGORITHM: Algorithm for JWT signing (default HS256).
        - CORS_ORIGINS: Comma-separated list of allowed origins for CORS. If not provided, sensible defaults
                        are used to allow local dev (http://localhost:3000) and the Kavia preview host.
        - CORS_ORIGIN_REGEX: Optional regex pattern for allowed origins (e.g., to allow preview hosts).
                             If provided, this will be passed to CORSMiddleware's allow_origin_regex.
    """

    APP_NAME: str = os.getenv("APP_NAME", "MedPrescribe Backend")
    API_DESCRIPTION: str = os.getenv(
        "API_DESCRIPTION",
        "Backend API for creating and verifying medical prescriptions with Solana integration.",
    )
    VERSION: str = os.getenv("API_VERSION", "0.1.0")

    # Path to SQLite database file. If not set, default to a local file named 'myapp.db'
    SQLITE_DB: str = os.path.abspath(os.getenv("SQLITE_DB", os.path.join(os.getcwd(), "myapp.db")))

    # Security configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME_IN_ENV")  # For development only; override in env.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # CORS configuration
    # If CORS_ORIGINS is not set, default to common frontend dev/preview origins.
    _cors_origins: str = os.getenv(
        "CORS_ORIGINS",
        ",".join(
            [
                # Local dev
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                # Known preview host (from work item context)
                "https://vscode-internal-22919-beta.beta01.cloud.kavia.ai:3000",
            ]
        ),
    )
    _cors_origin_regex: Optional[str] = os.getenv(
        "CORS_ORIGIN_REGEX",
        # Allow localhost/127.* with optional ports AND any *.cloud.kavia.ai host (with optional port),
        # which covers preview URLs such as https://<subdomain>.cloud.kavia.ai:3000
        r"^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$|^https:\/\/[a-z0-9\-\.]+\.cloud\.kavia\.ai(:\d+)?$",
    )

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Return the list of allowed CORS origins derived from CORS_ORIGINS env or defaults."""
        # Support "*" or CSV values
        if self._cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self._cors_origins.split(",") if o.strip()]

    @property
    def CORS_ORIGIN_REGEX(self) -> Optional[str]:
        """Return an optional regex used by CORSMiddleware to match allowed origins."""
        value = (self._cors_origin_regex or "").strip()
        return value or None


_settings: "Settings | None" = None


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Return a singleton Settings instance loaded from environment variables."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
