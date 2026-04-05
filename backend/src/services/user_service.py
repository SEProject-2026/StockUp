from uuid import UUID
from src.domain.user.user import User
from src.repositories.user_repository import IUserRepository
from src.infrastructure.logger import app_logger

class UserService:

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
    
    
    async def register(self, email: str, user_id: UUID, name: str) -> User:
        """
        Synchronizes a Supabase authenticated user with the local database.
        """
        app_logger.debug(f"Starting local registration/sync for user_id: {user_id}, email: {email}")
        
        # 1. Check if user already exists by ID (Primary Key)
        # This prevents duplicate local profiles for the same Supabase user
        existing_user = await self.user_repo.get_by_id(user_id)
        if existing_user:
            app_logger.info(f"User {user_id} already exists locally. Returning existing profile.")
            return existing_user

        normalized_email = email.strip().lower()
        # 2. Check if email is already taken by a different user_id
        # (Safety check in case of email changes or existing manual accounts)
        if await self.user_repo.get_by_email(normalized_email):
            app_logger.warning(f"Registration failed: Email {normalized_email} is already associated with another account")
            raise ValueError("Email already exists in the system")

        # 3. Create the new User entity linked to the Supabase UUID
        # Note: hashed_password is removed from the constructor as discussed
        user = User(
            id=user_id, 
            email=normalized_email, 
            name=name
        )
        
        # 4. Save to our local PostgreSQL
        await self.user_repo.save(user)
        
        app_logger.info(f"User profile synced successfully: {normalized_email} (ID: {user_id})")
        
        return user


    async def logout(self, user_id: UUID) -> bool:
        app_logger.info(f"User {user_id} logged out")
        return True
    
    async def update_name(self, user_id: UUID, new_name: str) -> User:
        app_logger.debug(f"Starting name update for user {user_id}")

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            app_logger.warning(f"Name update failed: User not found with ID {user_id}")
            raise ValueError("User not found")

        user.update_name(new_name) 
        await self.user_repo.save(user)
        
        app_logger.info(f"User {user_id} successfully updated their name to: '{new_name}'")
        return user

    async def update_push_token(self, user_id: UUID, new_push_token: str) -> User:
        app_logger.debug(f"Starting push token update for user {user_id}")

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            app_logger.warning(f"Push token update failed: User not found with ID {user_id}")
            raise ValueError("User not found")

        user.update_push_token(new_push_token) 
        await self.user_repo.update_push_token(user_id, new_push_token)
        
        app_logger.info(f"User {user_id} successfully updated their push token")
        return user