from fastapi import APIRouter, Request, HTTPException, Response  # Added Response
from api.schema.auth_states import LoginRequest
from api.utils.password_hashing import verify_password
from db.crud.user_data import get_user
from api.utils.access_token import create_access_token

router = APIRouter()


@router.post("/login")
async def login(request: Request, payload: LoginRequest, response: Response):
    """Authenticate a user and issue a JWT access token cookie.

    Args:
        request: FastAPI request used to access shared application resources.
        payload: Login credentials containing email and password.
        response: Mutable HTTP response used to set the auth cookie.

    Returns:
        dict: A success message with the authenticated email address.

    Raises:
        HTTPException: If the credentials are invalid or the user is missing.
    """
    email = payload.email
    password = payload.password

    # Access your database pool from app state
    resources = request.app.state.resources
    pool = resources.pool

    # 1. Fetch User
    user = await get_user(pool, user_id=email)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 2. Verify Credentials
    hashed_password = user["hashed_password"]
    is_valid = verify_password(password, hashed_password)

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 3. Create JWT
    access_token = create_access_token(data={"sub": email})

    # 4. Set HttpOnly Cookie for Security
    response.set_cookie(
        key="access_token",
        value=access_token,  # We store just the raw token string
        httponly=True,  # JS cannot read this
        max_age=6000,  # 100 minutes in seconds
        expires=6000,  # For older browsers
        samesite="lax",  # CSRF protection
        secure=False,  # Change to True in production with HTTPS!
    )

    return {"message": "Login successful", "email": email}
