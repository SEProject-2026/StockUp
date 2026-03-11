from uuid import UUID
from typing import Tuple
from src.authentication.auth_provider import IAuthProvider
from src.authentication.password_encoder import PasswordEncoder
from src.domain.user import User
from src.repositories.user_repository import IUserRepository
from src.infrastructure.logger import app_logger

class UserService:

    def __init__(self, user_repo: IUserRepository, auth_provider: IAuthProvider):
        self.user_repo = user_repo
        self.auth_provider = auth_provider
    
    async def register(self, email: str, password: str, confirm_password: str, name: str) -> User:
        """
        Registers a new user to the system.
        """
        app_logger.debug(f"Starting registration process for email: {email}")
        
        if await self.user_repo.get_by_email(email):
            app_logger.warning(f"Registration failed: Email already exists ({email})")
            raise ValueError("User with this email already exists") 
            
        if password != confirm_password:
            app_logger.warning(f"Registration failed: Passwords do not match for email ({email})")
            raise ValueError("Passwords do not match")

        # Encoding is a CPU-intensive operation, good place for a DEBUG log
        app_logger.debug(f"Encoding password for new user ({email})")
        hashed_password = PasswordEncoder.encode(password)

        user = User(email=email, hashed_password=hashed_password, name=name)
        
        await self.user_repo.save(user)
        app_logger.info(f"User registered successfully with email: {email}")
        
        return user

    async def login(self, email: str, password: str) -> Tuple[User, str]: #[User,token]
        """
        Authenticates a user.
        """
        app_logger.debug(f"Starting login process for email: {email}")

        user = await self.user_repo.get_by_email(email)
        
        # Validate password
        if not user or not PasswordEncoder.validate(password, user.hashed_password):
            app_logger.warning(f"Login failed: Invalid credentials for email ({email})")
            raise ValueError("Invalid email or password")
            
        app_logger.debug(f"Credentials validated. Generating token for user ID: {user.id}")
        token = self.auth_provider.create_token(user.id)
        
        app_logger.info(f"User logged in successfully with email: {email}")
        return user, token

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

    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> None:
        app_logger.debug(f"Starting password change process for user {user_id}")
        
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            app_logger.warning(f"Password change failed: User not found with ID {user_id}")
            raise ValueError("User not found")

        if not PasswordEncoder.validate(current_password, user.hashed_password):
            app_logger.warning(f"Password change failed: Incorrect current password provided by user {user_id}")
            raise ValueError("Incorrect current password")
        
        
        app_logger.debug(f"Encoding new password for user {user_id}")
        new_hashed_pw = PasswordEncoder.encode(new_password)

        user.change_password(new_hashed_pw)
        
        await self.user_repo.save(user)
        app_logger.info(f"User {user_id} successfully changed their password")

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