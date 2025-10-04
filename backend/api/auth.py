# backend/api/auth.py
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import JWTError, jwt
from backend.api.database import create_connection
from backend.api.authBearer import JWTBearer

# Load environment variables
load_dotenv()  # Must be called before using os.getenv()

# Environment variables with fallback defaults
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# ---------------- Authentication / JWT Functions ----------------

def create_access_token(data: dict):
    """
    Create a JWT access token with expiration
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """
    Verify JWT token and return the user email if valid
    """
    if not isinstance(token, str):
        raise ValueError(f"Expected token as str, got {type(token)}")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return None
        return email
    except JWTError:
        return None

# ---------------- User Utilities ----------------

def get_user_by_email(email: str):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, email ,role FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user  # {"id": ..., "email": ...}
