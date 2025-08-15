#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

# Ensure src imports resolve by setting PYTHONPATH to the backend container root
here = Path(__file__).resolve()
container_root = here.parents[2]  # .../prescription_backend
os.environ.setdefault("PYTHONPATH", str(container_root))

from src.api.generate_openapi import generate_and_write_openapi  # type: ignore  # noqa: E402


def main() -> int:
    out_path = generate_and_write_openapi()
    print(f"OpenAPI regenerated at: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
