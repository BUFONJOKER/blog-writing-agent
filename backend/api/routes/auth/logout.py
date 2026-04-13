from fastapi import APIRouter, Response
from api.schema.auth_states import LogoutRequest
router = APIRouter()

@router.post("/logout")
async def logout(response: Response):
    # You can implement your logout logic here, such as invalidating the user's session or token
    response.delete_cookies("access_token")
    # Implement your logout logic here
    return {"message": "Logout successful"}
