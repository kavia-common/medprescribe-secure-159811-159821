import os
from typing import List

from dotenv import load_dotenv

# Load variables from a .env file if present. The orchestrator will set actual env values.
load_dotenv()


class Settings:
    """Runtime configuration for the backend API loaded from environment variables."""

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

    # CORS - comma separated list, defaults to "*"
    _cors_origins: str = os.getenv("CORS_ORIGINS", "*")

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Return the list of allowed CORS origins."""
        # Support "*" or CSV values
        if self._cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self._cors_origins.split(",") if o.strip()]


_settings: Settings | None = None


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Return a singleton Settings instance loaded from environment variables."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
