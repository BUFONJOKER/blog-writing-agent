from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from api.config import JWT_SECRET_KEY

SECRET_KEY = JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 100


def create_access_token(data: dict):
    """Create a signed JWT access token with an expiration timestamp.

    Args:
        data: Token claims to encode, such as the subject email or user id.

    Returns:
        str: Encoded JWT access token string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    """Decode and validate a JWT access token.

    Args:
        token: Raw JWT access token string received from the client.

    Returns:
        dict | None: Decoded token payload when valid, otherwise None.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # Returns the dictionary of user data
    except JWTError:
        return None  # Token is invalid or expired
