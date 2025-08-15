from __future__ import annotations

import secrets
import string
from typing import Final


# Character set excludes easily-confused characters
ALPHABET: Final[str] = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


# PUBLIC_INTERFACE
def generate_prescription_code(length: int = 8) -> str:
    """Generate a random, human-friendly prescription code.

    Args:
        length: The length of the code to generate (default: 8).

    Returns:
        An uppercase alphanumeric code suitable for human entry.
    """
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


# PUBLIC_INTERFACE
def generate_nonce(length: int = 24) -> str:
    """Generate a random nonce string.

    Args:
        length: The length of the nonce to generate (default: 24).

    Returns:
        A random nonce string made of URL-safe characters.
    """
    # Use URL-safe alphabet for nonces
    urlsafe = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(urlsafe) for _ in range(length))


# PUBLIC_INTERFACE
def build_qr_payload(code: str) -> str:
    """Build a QR payload string for a prescription code.

    The payload is a simple custom URI scheme that frontends can turn into a QR code image.

    Args:
        code: The unique prescription code.

    Returns:
        A string like: 'medprescribe:{CODE}'
    """
    return f"medprescribe:{code}"
