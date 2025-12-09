from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from jose import jwt, JWTError
from authentication.auth_provider import IAuthProvider

#settings will be moved to config file later
SECRET_KEY = "MY_SUPER_SECRET_KEY"
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60 * 24 

class JwtAuthProvider(IAuthProvider):
    def create_token(self, user_id: UUID) -> str:
        #creation of the token payload
        payload = {
            "sub": str(user_id),  # sub = the subject of the token, the user ID
            "exp": datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
        }
        # create signature and return the token
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> Optional[UUID]:
        try:
            #decode the token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id_str = payload.get("sub")
            
            if user_id_str is None:
                return None
                
            return UUID(user_id_str)
            
        except JWTError:
            # invalid token(invalid signature, expired)
            return None