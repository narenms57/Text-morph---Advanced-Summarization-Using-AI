from fastapi import Depends, HTTPException

from auth import get_user_by_email, verify_token
from authBearer import JWTBearer



def get_current_user(token :str = Depends(JWTBearer())):
    email = verify_token(token)
    if email is None:
        raise HTTPException(status_code=403, detail="Invalid token or expired token.")
    user = get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user