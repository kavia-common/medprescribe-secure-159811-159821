from .auth import router as auth_router
from .prescriptions import router as prescriptions_router
from .verify import router as verify_router

__all__ = ["auth_router", "prescriptions_router", "verify_router"]
