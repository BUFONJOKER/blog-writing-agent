from fastapi import APIRouter, Response
from api.schema.auth_states import LogoutRequest

router = APIRouter()


@router.post("/logout")
async def logout(response: Response):
    """Clear the access token cookie to end the user's authenticated session.

    Args:
        response: FastAPI response object used to delete the auth cookie.

    Returns:
        dict: A success message confirming logout.
    """
    response.delete_cookies("access_token")
    return {"message": "Logout successful"}
