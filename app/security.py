import os

from fastapi import Depends, Header, HTTPException, status


def require_api_key(x_api_key: str | None = Header(None)) -> bool:
    """FastAPI dependency to require a valid API key via X-API-Key header.

    Reads the expected key from environment variable `API_KEY` and compares it
    to the provided header value. Raises HTTP 401 on missing or invalid key.
    """
    expected = os.getenv("API_KEY")
    if expected is None:
        # If API_KEY is not set in the environment, treat as misconfiguration
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
