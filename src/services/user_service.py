from uuid import UUID
from typing import Dict
from authentication.auth_provider import IAuthProvider
from authentication.password_encoder import PasswordEncoder
from domain.user import User
from repositories.user_repository import IUserRepository

class UserService:

    def __init__(self, user_repo: IUserRepository, auth_provider: IAuthProvider):
        self.user_repo = user_repo
        self.auth_provider = auth_provider
    
    async def register(self, email: str, password: str, name: str) -> Dict:
        """
        Registers a new user to the system.
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if '@' not in email:
            raise ValueError("Invalid email address")
        if await self.user_repo.get_by_email(email):
            raise ValueError("User with this email already exists") 

        hashed_password = PasswordEncoder.encode(password)

        # Create user entity
        user = User(email=email, hashed_password=hashed_password, name=name)
        
        # Save to DB
        await self.user_repo.save(user)
        
        return {
            "status": "success",
            "data": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }

    async def login(self, email: str, password: str) -> Dict:
        """
        Authenticates a user.
        """
        user = await self.user_repo.get_by_email(email)
        
        # Validate password
        if not user or not PasswordEncoder.validate(password, user.hashed_password):
            raise ValueError("Invalid email or password")
            
        # Generate token
        token = self.auth_provider.create_token(user.id)
        
        return {
            "status": "success",
            "access_token": token,
            "data": {
                "user_id": user.id,
                "email": user.email,
                "name": user.name
            }
        }

    async def logout(self, user_id: UUID) -> bool:
        return True
    
    async def update_name(self, user_id: UUID, new_name: str) -> Dict:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.update_name(new_name) 

        await self.user_repo.save(user)

        return {
            "status": "success",
            "data": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }

    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> Dict:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if not PasswordEncoder.validate(current_password, user.hashed_password):
            raise ValueError("Incorrect current password")

        if len(new_password) < 8:
            raise ValueError("New password is too short")

        new_hashed_pw = PasswordEncoder.encode(new_password)

        user.change_password(new_hashed_pw)
    
        await self.user_repo.save(user)

        return {
            "status": "success",
            "message": "Password changed successfully"
        }