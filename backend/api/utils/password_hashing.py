import hashlib
import bcrypt


def _prepare_password(password: str) -> bytes:
    """Normalize user input into fixed-length bytes for bcrypt.

    Args:
        password: Plain-text password provided by the user.

    Returns:
        bytes: SHA-256 digest bytes used as bcrypt input.
    """
    if not isinstance(password, str):
        raise TypeError("password must be a string")
    return hashlib.sha256(password.encode("utf-8")).digest()


def hash_password(password: str):
    """Hash a password for secure storage.

    Args:
        password: Plain-text password provided by the user.

    Returns:
        str: Bcrypt hash string safe to persist in the database.
    """
    prepared_pw = _prepare_password(password)
    return bcrypt.hashpw(prepared_pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str):
    """Verify user-provided password against a stored hash.

    Args:
        plain_password: Plain-text password provided during authentication.
        hashed_password: Previously stored bcrypt hash string.

    Returns:
        bool: True when credentials are valid, otherwise False.
    """
    prepared_pw = _prepare_password(plain_password)
    try:
        return bcrypt.checkpw(prepared_pw, hashed_password.encode("utf-8"))
    except ValueError:
        return False
