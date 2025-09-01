
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.params import Depends

from database import create_connection
from dependencies import get_current_user
from models import UserProfileUpdate


router = APIRouter()

@router.get("/read")
def read_profile(current_user:dict = Depends(get_current_user)):
    user_id = current_user["id"]
    connection = create_connection()
   
    
    cursor = connection.cursor(dictionary=True)
   # cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    #user = cursor.fetchone()
    #if not user:
        #cursor.close()
        #connection.close()
       # raise HTTPException(status_code=404, detail="User not found")
    
    cursor.execute("SELECT age_group, language_preference FROM profiles WHERE user_id = %s", (user_id,))
    profile = cursor.fetchone()
    cursor.close()
    connection.close()


    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile



@router.put("/update")
def update_profile(profile_update: UserProfileUpdate, current_user:dict=Depends(get_current_user)):
    user_id = current_user["id"]
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    #cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
   # user = cursor.fetchone()
    #if not user:
      #  cursor.close()
       # connection.close()
       # raise HTTPException(status_code=404, detail="User not found")
    
    cursor.execute("SELECT * FROM profiles WHERE user_id = %s", (user_id,))
    exists = cursor.fetchone()
    if exists:
        cursor.execute("UPDATE profiles SET age_group = %s, language_preference = %s WHERE user_id = %s",
            (profile_update.age_group, profile_update.language_preference, user_id))
    else:
        cursor.execute("INSERT INTO profiles (user_id, age_group, language_preference) VALUES (%s, %s, %s)",
            (user_id, profile_update.age_group, profile_update.language_preference))
    connection.commit()
    cursor.close()
    connection.close()
    return {"msg": "Profile updated successfully"}