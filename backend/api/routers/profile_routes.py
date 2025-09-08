# backend/api/routers/profile_routes.py
from fastapi import APIRouter, Depends, HTTPException
from backend.api.database import create_connection
from backend.api.models import UserProfileUpdate
from backend.api.dependencies import get_current_user


router = APIRouter()

@router.get("/read")
def read_profile(current_user: dict = Depends(get_current_user)):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT age_group, language_preference FROM profiles WHERE user_id = %s",
        (current_user["id"],)
    )
    profile = cursor.fetchone()
    cursor.close()
    connection.close()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.put("/update")
def update_profile(profile_update: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM profiles WHERE user_id = %s", (current_user["id"],))
    exists = cursor.fetchone()
    if exists:
        cursor.execute(
            "UPDATE profiles SET age_group = %s, language_preference = %s WHERE user_id = %s",
            (profile_update.age_group, profile_update.language_preference, current_user["id"])
        )
    else:
        cursor.execute(
            "INSERT INTO profiles (user_id, age_group, language_preference) VALUES (%s, %s, %s)",
            (current_user["id"], profile_update.age_group, profile_update.language_preference)
        )
    connection.commit()
    cursor.close()
    connection.close()
    return {"msg": "Profile updated successfully"}