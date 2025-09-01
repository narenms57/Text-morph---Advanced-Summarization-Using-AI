

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from auth import create_access_token, get_user_by_email
from database import create_connection, update_user_password
from models import PasswordResetRequest, UpdatePasswordRequest, UserCreate, UserLogin
from passhash import hash_password, verify_password
from fastapi import status


router = APIRouter()

@router.post("/register")
def register(user: UserCreate):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed.")
    
    cursor = connection.cursor()
    
    # Check if email or username already exist
    cursor.execute("SELECT id FROM users WHERE email = %s OR username = %s", (user.email, user.username))
    if cursor.fetchone():
        cursor.close()
        connection.close()
        raise HTTPException(status_code=400, detail="Email or username already exists.")
    
    hashed_password = hash_password(user.password)
    #insert inot users
    cursor.execute(
        "INSERT INTO users (username, email, hashed_password, language_preference) VALUES (%s, %s, %s, %s)",
        (user.username, user.email, hashed_password, user.language_preference)
    )
    connection.commit()

    #id
    user_id = cursor.lastrowid
    #insert into profiles
    cursor.execute(
        "INSERT INTO profiles (user_id,age_group, language_preference) VALUES (%s, %s, %s)",
        (user_id,None, user.language_preference)
    )
    connection.commit()

    cursor.close()
    connection.close()
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"msg": "User registered successfully"})


@router.post("/login")
def login(user:UserLogin):
        connection = create_connection()
        if not connection:
            raise HTTPException(status_code=500, detail="DB connection failed.")
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (user.email,))
        db_user = cursor.fetchone()
        cursor.close()
        connection.close()

        if not db_user:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        if not verify_password(user.password, db_user["hashed_password"]):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        #create jwt token
        access_token = create_access_token(data={"sub": db_user["email"]})
        return {"access_token": access_token, "token_type": "bearer"}

@router.post("/reset-password")
async def request_reset_password(request: PasswordResetRequest):
    user = get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=400, detail="Email does not exist.")
    return {"msg": "Email exists, you can now reset your password."}

@router.post("/update-password")
async def update_password(request: UpdatePasswordRequest):
    user = get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=400, detail="Email not found.")
    hashed = hash_password(request.new_password)
    success = update_user_password(request.email, hashed)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password.")
    return {"msg": "Password updated successfully"}