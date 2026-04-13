from fastapi import Request, HTTPException, status
from backend.api.utils.access_token import (
    decode_access_token,
)  # Your existing decode logic


async def get_current_user(request: Request):
    """Resolve the current authenticated user from the access token cookie.

    Args:
        request: Incoming FastAPI request containing the auth cookie.

    Returns:
        str: The authenticated user's subject value from the JWT payload.

    Raises:
        HTTPException: If the cookie is missing or the token is invalid.
    """
    # 1. Grab the token from the cookie
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please login.",
        )

    # 2. Decode and validate
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid token.",
        )

    # 3. Return the user identifier (email/id) stored in the token
    return payload.get("sub")
