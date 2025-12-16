#app/security.py

"""API security helpers (API key authentication)."""

import os

from fastapi import Header, HTTPException, status


def require_api_key(x_api_key: str | None = Header(None)) -> bool:
    """Require a valid API key via the `X-API-Key` header.

    The expected key is read from environment variable `API_KEY`.
    Raises HTTP 401 if missing or invalid.
    """
    expected = os.getenv("API_KEY")
    if expected is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is not configured on the server.",
        )

    if not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )

    return True
