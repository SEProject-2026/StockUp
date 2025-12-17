from src.infrastructure.repositories_in_memory.in_memory_user_repository import InMemoryUserRepository
from src.services.user_service import UserService
from src.infrastructure.auth.jwt_auth_provider import JwtAuthProvider

class AppContainer:
    """
    Dependency Injection Container.
    The main factory that creates and wires the application components.
    """

    # Singleton instances
    _user_repo_instance = None
    _auth_provider_instance = None
    _user_service_instance = None

    @staticmethod
    def get_user_repository():
        """Creates (if needed) and returns the User Repository"""
        if AppContainer._user_repo_instance is None:
            AppContainer._user_repo_instance = InMemoryUserRepository()
        return AppContainer._user_repo_instance

    @staticmethod
    def get_auth_provider():
        """Creates (if needed) and returns the Auth Provider"""
        if AppContainer._auth_provider_instance is None:
            # In production, get secret from env variables
            AppContainer._auth_provider_instance = JwtAuthProvider()
        return AppContainer._auth_provider_instance

    @staticmethod
    def get_user_service():
        """
        Creates the UserService and injects dependencies.
        """
        if AppContainer._user_service_instance is None:
            repo = AppContainer.get_user_repository()
            auth = AppContainer.get_auth_provider()
            
            # Injection happens here
            AppContainer._user_service_instance = UserService(user_repo=repo, auth_provider=auth)
            
        return AppContainer._user_service_instance