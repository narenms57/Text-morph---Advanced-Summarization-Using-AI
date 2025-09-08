from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Import routers
from backend.api.routers.auth_routes import router as auth_router
from backend.api.routers.profile_routes import router as profile_router
from backend.paraphrasing.router import router as paraphrasing_router

app = FastAPI()
app = FastAPI(title="Text Morph API")

app.include_router(paraphrasing_router)
# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(profile_router, prefix="/profile", tags=["profile"])
# Mount the paraphrasing router
app.include_router(paraphrasing_router, prefix="/paraphrasing", tags=["paraphrasing"])

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Backend is running!"}

security = HTTPBearer()

@app.get("/verify")
def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    from backend.api.auth import verify_token
    email = verify_token(token)
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"email": email}

