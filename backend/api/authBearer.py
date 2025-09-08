from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class JWTBearer(HTTPBearer):
    def _init_(self, auto_error:bool = True):
        super(JWTBearer, self)._init_(auto_error=auto_error)

    async def _call_(self, request:Request):
        credentials : HTTPAuthorizationCredentials = await super(JWTBearer, self)._call_(request)
        if credentials:
            if credentials.scheme != "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")
        
    def verify_jwt(self, jwtoken: str) -> bool:
        from auth import verify_token
        try:
            payload = verify_token(jwtoken)
            return payload is not None
        except:
            return False