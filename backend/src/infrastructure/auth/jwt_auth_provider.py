from datetime import datetime, timedelta, timezone
import os
from typing import Optional
from uuid import UUID
from jose import jwt, JWTError
from backend.src.authentication.auth_provider import IAuthProvider
from backend.src.infrastructure.logger import app_logger
from dotenv import load_dotenv


load_dotenv()


SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-test-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRES_IN", "60")) 
class JwtAuthProvider(IAuthProvider):
    def create_token(self, user_id: UUID) -> str:
        #creation of the token payload
        payload = {
            "sub": str(user_id),  # sub = the subject of the token, the user ID
            "exp": datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
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
            
        except Exception as e:
            # invalid token(invalid signature, expired)
            app_logger.error(f"JWT Verification failed: {str(e)}")
            return None