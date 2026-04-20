from fastapi import APIRouter, Request, HTTPException, Response, status, Depends
import logging
from api.schema.auth_states import UpdatePasswordRequest
from api.utils.password_hashing import verify_password, hash_password
from api.utils.auth import get_current_user

# Rename the import to avoid collision
from db.crud.user_data import get_user, update_password as update_password_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.put("/update_password")
async def change_user_password(
    request: Request,
    payload: UpdatePasswordRequest,
    current_user_email: str = Depends(get_current_user),
):
    """Verify the current password and persist a replacement password hash.

    Args:
        request: FastAPI request used to access shared application resources.
        payload: Password change request containing current and new passwords.

    Returns:
        dict: A success message with the user's email address.

    Raises:
        HTTPException: If authentication fails or the database update fails.
    """
    email = current_user_email
    password = payload.password
    new_password = payload.new_password

    resources = request.app.state.resources
    pool = resources.pool

    # 1. Fetch User
    user = await get_user(pool, email=email)
    if not user:
        # Use 401 for auth failures
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # 2. Verify Old Password
    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # 3. Hash and Update
    new_password_hashed = hash_password(new_password)

    try:
        await update_password_db(pool, email=email, hashed_password=new_password_hashed)
    except Exception as exc:
        logger.exception("Failed to update password", exc_info=exc)
        raise HTTPException(
            status_code=500, detail="Unable to update the password right now."
        )

    return {"message": "Password updated successfully", "email": email}
