from src.infrastructure.repositories.in_memory_user_repository import InMemoryUserRepository
from src.services.user_service import UserService
from src.infrastructure.auth.jwt_auth_provider import JwtAuthProvider

from src.services.stock_service import StockService
from src.infrastructure.repositories.in_memory_home_repository import InMemoryHomeRepository
from src.infrastructure.repositories.in_memory_product_repository import InMemoryProductRepository
from src.infrastructure.repositories.in_memory_catalog_repository import InMemoryCatalogRepository

class AppContainer:
    """
    Dependency Injection Container.
    The main factory that creates and wires the application components.
    """

    # Singleton instances
    _user_repo_instance = None
    _auth_provider_instance = None
    _user_service_instance = None
    _home_repo_instance = None
    _product_repo_instance = None
    _catalog_repo_instance = None
    _stock_service_instance = None

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
    
    @staticmethod
    def get_home_repository():
        """Creates (if needed) and returns the Home Repository"""
        if AppContainer._home_repo_instance is None:
            AppContainer._home_repo_instance = InMemoryHomeRepository()
        return AppContainer._home_repo_instance
    @staticmethod
    def get_product_repository():
        """Creates (if needed) and returns the Product Repository"""
        if AppContainer._product_repo_instance is None:
            AppContainer._product_repo_instance = InMemoryProductRepository()
        return AppContainer._product_repo_instance
    @staticmethod
    def get_catalog_repository():
        """Creates (if needed) and returns the Catalog Repository"""
        if AppContainer._catalog_repo_instance is None:
            AppContainer._catalog_repo_instance = InMemoryCatalogRepository()
        return AppContainer._catalog_repo_instance
    @staticmethod
    def get_stock_service():
        """
        Creates the StockService and injects dependencies.
        """
        if AppContainer._stock_service_instance is None:
            home_repo = AppContainer.get_home_repository()
            product_repo = AppContainer.get_product_repository()
            catalog_repo = AppContainer.get_catalog_repository()
            
            # Injection happens here
            AppContainer._stock_service_instance = StockService(
                home_repository=home_repo,
                product_repository=product_repo,
                catalog_repository=catalog_repo
            )
            
        return AppContainer._stock_service_instance