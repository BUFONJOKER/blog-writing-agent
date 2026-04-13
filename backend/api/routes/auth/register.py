from fastapi import APIRouter, Request, HTTPException
from api.schema.auth_states import RegisterRequest
from backend.api.utils.password_hashing import hash_password
from backend.db.crud.user_data import create_user, get_user, update_password

router = APIRouter()

@router.post("/register")
async def register(request: Request, payload: RegisterRequest):
    # Implement your registration logic here
    resources = request.app.state.resources
    pool = resources.pool
    name = payload.name
    email = payload.email
    password = payload.password
    password = hash_password(password)

    await create_user(pool, user_id=name, email=email, hashed_password=password)

    user = await get_user(pool, user_id=name)
    if not user:
        raise HTTPException(status_code=404, detail="User not found after creation")

    return {"message": "Registration successful"}