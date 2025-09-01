
from fastapi import FastAPI
from routers.auth_routes import router as auth_router
from routers.profile_routes import router as profile_router


app= FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(profile_router, prefix="/profile", tags=["profile"])

#security = HTTPBearer()






"""
@app.get("/verify")
def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    from auth import verify_token
    email = verify_token(token)
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"email": email}
"""