from passlib.context import CryptContext

# Setup the hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    """Hash a plain-text password for secure database storage.

    Args:
        password: Plain-text password provided by the user.

    Returns:
        str: Bcrypt-hashed password string ready to persist in the database.
    """
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """Verify a plain-text password against a stored password hash.

    Args:
        plain_password: Plain-text password supplied during login or update.
        hashed_password: Stored bcrypt hash fetched from the database.

    Returns:
        bool: True when the password matches the stored hash, otherwise False.
    """
    return pwd_context.verify(plain_password, hashed_password)
