import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from .constants import ALGORITHM
from .config import settings


# --------------------
# Password hashing with bcrypt
# --------------------
def hash_password(password: str) -> str:
    """Hash password using bcrypt and return as string"""
    # Generate salt and hash the password
    salt = bcrypt.gensalt(rounds=12)  # You can increase rounds for more security
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')     # Store as string in database


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


# --------------------
# JWT token (unchanged)
# --------------------
def create_token(data: dict, token_expiry_in_min):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=token_expiry_in_min)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)