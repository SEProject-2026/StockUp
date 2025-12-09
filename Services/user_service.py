from uuid import UUID
from typing import List, Optional, Dict
from datetime import date

from Authentication.password_encoder import PasswordEncoder
from Domain import user
from Domain.user import User
from Repositories.user_repository import IUserRepository

class UserService:
    """
    Manages user lifecycle and authentication (independent of specific homes).
    """
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
    
    async def register(self, email: str, password: str, name: str) -> Dict:
        """
        Registers a new user to the system.
        Input: Registration details.
        Output: Created user object (or success message).
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if '@' not in email:
            raise ValueError("Invalid email address")
        if await self.user_repo.get_by_email(email):
            raise ValueError("Email already registered")
        hashed_password = PasswordEncoder.encode(password)

        user=User(email=email, password=password, name=name)
        user_dict = {
            "email": user.email,
            "password": user.password,
            "name": user.name
        }
        created_user = await self.user_repo.add(user_dict)
        return created_user

        

    async def login(self, email: str, password: str) -> Dict:
        """
        Authenticates a user.
        Input: Email and password.
        Output: Access Token (JWT) and basic user info.
        """
        user = await self.user_repo.get_by_email(email)
        if not user or not PasswordEncoder.validate(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        # For simplicity, returning user info directly. In real scenario, generate JWT token.
        return {
            "user_id": user['id'],
            "email": user['email'],
            "name": user['name']
        }

    async def logout(self, user_id: UUID) -> bool:
        return True