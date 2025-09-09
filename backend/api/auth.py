from datetime import datetime, timedelta
from fastapi import HTTPException
from fastapi.params import Depends
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
from database import create_connection

from authBearer import JWTBearer
load_dotenv()  # Load environment variables from .env file

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow()+ timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email:str = payload.get("sub")
        if not email:
            return None
        return email
    except JWTError:
        return None
    

def get_user_by_email(email: str):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("Select id , username, email, language_preference from users where email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user