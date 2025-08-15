from __future__ import annotations

import json
import os
from pathlib import Path

from src.api.main import app


def _resolve_interfaces_dir() -> Path:
    """Return the absolute path to the 'interfaces' directory at the container root."""
    # __file__ -> .../prescription_backend/src/api/generate_openapi.py
    # parents[0] -> .../src/api
    # parents[1] -> .../src
    # parents[2] -> .../prescription_backend
    container_root = Path(__file__).resolve().parents[2]
    return container_root / "interfaces"


# PUBLIC_INTERFACE
def generate_and_write_openapi(output_path: str | os.PathLike | None = None) -> str:
    """Generate the OpenAPI schema from the FastAPI app and write it to openapi.json.

    Args:
        output_path: Optional absolute or relative path to the output file. If not provided,
            the file will be written to '<container_root>/interfaces/openapi.json'.

    Returns:
        The absolute path to the written OpenAPI JSON file.
    """
    openapi_schema = app.openapi()

    if output_path is None:
        output_dir = _resolve_interfaces_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "openapi.json"
    else:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)

    return str(output_file.resolve())


if __name__ == "__main__":
    path = generate_and_write_openapi()
    print(f"OpenAPI schema written to: {path}")
