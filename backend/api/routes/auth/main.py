from fastapi import APIRouter, Request, HTTPException
from api.routes.auth.login import router as login_router
from api.routes.auth.logout import router as logout_router
from api.routes.auth.register import router as register_router
from api.routes.auth.update_password import router as update_password_router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

auth_router.include_router(login_router)
auth_router.include_router(logout_router)
auth_router.include_router(register_router)
auth_router.include_router(update_password_router)