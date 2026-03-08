from uuid import UUID
from typing import Dict, Tuple
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
        app_logger.debug(f"Registering user with email: {email} and name: {name}")
        if await self.user_repo.get_by_email(email):
            app_logger.warning(f"Registration attempt with existing email: {email}")
            raise ValueError("User with this email already exists") 
        if password != confirm_password:
            app_logger.warning(f"Password mismatch during registration for email: {email}")
            raise ValueError("Passwords do not match")

        app_logger.debug(f"Encoding password for user with email: {email}")
        hashed_password = PasswordEncoder.encode(password)

        # Create user entity
        user = User(email=email, hashed_password=hashed_password, name=name)
        
        # Save to DB
        app_logger.debug(f"Saving new user to the database with email: {email} and name: {name}")
        await self.user_repo.save(user)
        app_logger.info(f"User registered successfully with email: {email} and name: {name}")
        
        return user

    async def login(self, email: str, password: str) -> Tuple[User, str]: #[User,token]
        """
        Authenticates a user.
        """
        app_logger.debug(f"Attempting to log in user with email: {email}")

        app_logger.debug(f"Retrieving user from database with email: {email}")
        user = await self.user_repo.get_by_email(email)
        
        # Validate password
        if not user or not PasswordEncoder.validate(password, user.hashed_password):
            app_logger.warning(f"Login failed for email: {email}")
            raise ValueError("Invalid email or password")
            
        # Generate token
        app_logger.debug(f"Generating authentication token for user with email: {email}")
        token = self.auth_provider.create_token(user.id)
        
        app_logger.info(f"User logged in successfully with email: {email}")
        return user, token

    async def logout(self, user_id: UUID) -> bool:
        return True
    
    async def update_name(self, user_id: UUID, new_name: str) -> User:
        app_logger.debug(f"Updating name for user {user_id} to: {new_name}")

        app_logger.debug(f"Retrieving user from database with ID: {user_id}")
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            app_logger.warning(f"User not found with ID: {user_id} for name update")
            raise ValueError("User not found")

        user.update_name(new_name) 
        app_logger.debug(f"Saving updated user to the database with ID: {user_id} and new name: {new_name}")
        await self.user_repo.save(user)
        app_logger.info(f"User {user_id} updated their name successfully to: {new_name}")

        return user

    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> None:
        app_logger.debug(f"Attempting to change password for user {user_id}")
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            app_logger.warning(f"User not found with ID: {user_id} for password change")
            raise ValueError("User not found")

        if not PasswordEncoder.validate(current_password, user.hashed_password):
            app_logger.warning(f"Invalid current password for user {user_id}")
            raise ValueError("Incorrect current password")
        
        app_logger.debug(f"Encoding new password for user {user_id}")
        new_hashed_pw = PasswordEncoder.encode(new_password)

        user.change_password(new_hashed_pw)
        app_logger.debug(f"Saving updated user to the database with ID: {user_id}")
        await self.user_repo.save(user)
        app_logger.info(f"User {user_id} changed their password successfully")
        