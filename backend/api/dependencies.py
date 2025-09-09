from backend.api.auth import get_user_by_email, verify_token
from backend.api.authBearer import JWTBearer
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(JWTBearer())):
    token_str = credentials.credentials  # Extract the raw token string
    email = verify_token(token_str)
    if email is None:
        raise HTTPException(status_code=403, detail="Invalid token or expired token.")
    user = get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
