from uuid import UUID

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, Security

from src.infrastructure.app_container import AppContainer

# 1. הגדרת הסכימה החדשה
security_scheme = HTTPBearer()

async def get_current_user_id(
    auth: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> UUID:
    """
    Dependency שמאמת טוקן מול Supabase.
    """
    # 2. חילוץ הטוקן הנקי (ה-Bearer כבר יורד אוטומטית)
    token = auth.credentials
    
    auth_provider = AppContainer.get_auth_provider()
    user_id = auth_provider.verify_token(token)
    
    if user_id is None:
        raise HTTPException(
            detail="Invalid or expired token",
        )
        
    return user_id