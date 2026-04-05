import os
from typing import Optional
from uuid import UUID
from supabase import create_client, Client
from src.authentication.auth_provider import IAuthProvider
from src.infrastructure.logger import app_logger
 
class SupabaseAuthProvider(IAuthProvider):
    def __init__(self):
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            app_logger.error("Supabase credentials missing in environment variables")
            raise ValueError("Supabase configuration missing")
            
        self.supabase: Client = create_client(url, key)

    def create_token(self, user_id: UUID) -> str:
        app_logger.warning(f"create_token called for user {user_id}. Tokens are managed by Supabase client-side.")
        return ""

    def verify_token(self, token: str) -> Optional[UUID]:
        try:
            # The token is usually passed as a Bearer token. 
            # If the string contains "Bearer ", we strip it.
            clean_token = token.replace("Bearer ", "") if "Bearer " in token else token
            
            user_response = self.supabase.auth.get_user(clean_token)
            user_id_str = user_response.user.id
            
            return UUID(user_id_str)
        except Exception as e:
            app_logger.error(f"Supabase JWT Verification failed: {str(e)}")
            return None