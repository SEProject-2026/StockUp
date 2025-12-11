from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from infrastructure.app_container import AppContainer

# 1. Define the OAuth2 Scheme
# This tells FastAPI to look for a "Bearer" token in the Authorization header.
# The 'tokenUrl' parameter is used by Swagger UI to know where to send login requests.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> UUID:
    """
    Dependency function that acts as a Security Guard.
    It validates the Bearer token and extracts the User ID.
    If validation fails, it raises a 401 Unauthorized error.
    """
    
    # 2. Get the Auth Provider from our central container
    auth_provider = AppContainer.get_auth_provider()
    
    # 3. Verify the token using the provider logic
    user_id = auth_provider.verify_token(token)
    
    # 4. Fail Fast: If token is invalid/expired
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 5. Return the ID (so the controller can use it)
    return user_id