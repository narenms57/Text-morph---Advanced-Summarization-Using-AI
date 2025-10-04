from typing_extensions import Optional
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username:str
    email: EmailStr
    password: str
    language_preference: str = "English" 
    role: str = "user"  # Default role is 'user'


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdate(BaseModel):
    #username: Optional[str]
    age_group: Optional[str]
    language_preference: Optional[str]

class PasswordResetRequest(BaseModel):
    email: EmailStr

class UpdatePasswordRequest(BaseModel):
    email: EmailStr
    new_password: str

