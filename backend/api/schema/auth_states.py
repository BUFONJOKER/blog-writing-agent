from pydantic import BaseModel, Field

class RegisterRequest(BaseModel):
    name: str = Field(..., example="John Doe", description="The full name of the user")
    email: str = Field(..., example="user@example.com", description="The email address of the user")
    password: str = Field(..., example="password123", description="The password for the user account")

class LoginRequest(BaseModel):
    email: str = Field(..., example="user@example.com", description="The email address of the user")
    password: str = Field(..., example="password123", description="The password for the user account")

class LogoutRequest(BaseModel):
    user_id: str = Field(..., example="12345", description="The unique identifier of the user")

class UpdatePasswordRequest(BaseModel):
    email: str = Field(..., example="user@example.com", description="The email address of the user")
    password: str = Field(..., example="password123", description="The current password for the user account")
    new_password: str = Field(..., example="newpassword123", description="The new password for the user account")