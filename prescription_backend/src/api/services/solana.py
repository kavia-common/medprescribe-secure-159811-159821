from __future__ import annotations

from datetime import datetime, timezone

from src.api.utils.ids import generate_nonce


# PUBLIC_INTERFACE
def create_sign_message(address: str, nonce: str | None = None) -> dict:
    """Create a signable message for Solana wallet authentication (stub).

    This function returns a message and nonce that a client can sign with their Solana wallet.
    It does not perform any blockchain interaction and is intended as a stub for integration.

    Args:
        address: The Solana wallet address the user wants to authenticate with.
        nonce: Optional nonce. If not provided, a new nonce is generated.

    Returns:
        Dict with 'address', 'nonce', and 'message' fields.
    """
    if not nonce:
        nonce = generate_nonce()
    ts = datetime.now(timezone.utc).isoformat()
    message_lines = [
        "MedPrescribe Authentication",
        f"Address: {address}",
        f"Nonce: {nonce}",
        f"Timestamp: {ts}",
        "By signing this message you prove ownership of the address.",
    ]
    message = "\n".join(message_lines)
    return {"address": address, "nonce": nonce, "message": message}


# PUBLIC_INTERFACE
def verify_signature(signature: str, message: str, address: str) -> bool:
    """Verify a Solana signature for a message (stub).

    WARNING:
        This is a stubbed verifier and ALWAYS returns True as long as inputs are non-empty.
        Replace this with a real Solana signature verification when integrating a wallet library.

    Args:
        signature: The signature provided by the client.
        message: The original message that was signed.
        address: The signer's wallet address.

    Returns:
        True if the signature is considered valid (stubbed); False otherwise.
    """
    return bool(signature and message and address)
