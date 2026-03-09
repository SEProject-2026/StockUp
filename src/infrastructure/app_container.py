from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

# --- Services ---
from src.services.user_service import UserService
from src.services.stock_service import StockService
from src.services.management_service import ManagementService

# --- Auth ---
from src.infrastructure.auth.jwt_auth_provider import JwtAuthProvider

# --- Repositories (DB Implementation) ---
from src.infrastructure.repositories.db_user_repository import DbUserRepository
from src.infrastructure.repositories.db_home_repository import DbHomeRepository
from src.infrastructure.repositories.db_product_repository import DbProductRepository

# --- Repositories (In-Memory for Tests) ---
from src.infrastructure.repositories.in_memory_user_repository import InMemoryUserRepository
from src.infrastructure.repositories.in_memory_home_repository import InMemoryHomeRepository
from src.infrastructure.repositories.in_memory_product_repository import InMemoryProductRepository

# --- Catalog ---
from src.infrastructure.repositories.csv_catalog_provider import CsvCatalogProvider
from src.infrastructure.repositories.db_catalog_provider import DbCatalogProvider

class AppContainer:
    """
    Dependency Injection Container.
    Supports both Database injection (Production) and In-Memory fallback (Testing).
    """

    # Singleton instances (for Tests or Stateless components)
    _user_service_instance = None
    _stock_service_instance = None
    _management_service_instance = None
    _auth_provider_instance = None
    _catalog_provider_instance = None

    @staticmethod
    def get_auth_provider():
        if AppContainer._auth_provider_instance is None:
            AppContainer._auth_provider_instance = JwtAuthProvider()
        return AppContainer._auth_provider_instance

    @staticmethod
    def get_catalog_provider(db: Optional[Session] = None):
        """
        Returns a Catalog Provider.
        - If 'db' is provided: Returns DbCatalogProvider.
        - If 'db' is None: Returns CsvCatalogProvider.
        """
        if AppContainer._catalog_provider_instance is not None:
            return AppContainer._catalog_provider_instance
        # 1. Production (Database)
        #if db:
         #   _catalog_provider_instance= DbCatalogProvider(db)

        # 2. Testing/Fallback (CSV)
        if AppContainer._catalog_provider_instance is None:
            project_root = Path(__file__).resolve().parents[2]
            csv_path = project_root / "src" / "data" / "master_db.csv"

            if not csv_path.exists():
                alt = project_root / "data" / "master_db.csv"
                if alt.exists():
                    csv_path = alt

            AppContainer._catalog_provider_instance = CsvCatalogProvider(str(csv_path))

        return AppContainer._catalog_provider_instance

    @staticmethod
    def get_user_service(db: Optional[Session] = None) -> UserService:
        """
        Returns a UserService.
        - If 'db' is provided: Returns a new instance connected to the DB (Production).
        - If 'db' is None: Returns a singleton instance with InMemory repository (Testing).
        """
        auth = AppContainer.get_auth_provider()

        # Production (DB)
        if db:
            repo = DbUserRepository(db)
            return UserService(user_repo=repo, auth_provider=auth)

        # Testing (In-Memory)
        if AppContainer._user_service_instance is None:
            repo = InMemoryUserRepository()
            AppContainer._user_service_instance = UserService(user_repo=repo, auth_provider=auth)
        
        return AppContainer._user_service_instance

    @staticmethod
    def get_stock_service(db: Optional[Session] = None) -> StockService:
        catalog = AppContainer.get_catalog_provider(db)

        # Production (DB)
        if db:
            return StockService(
                home_repository=DbHomeRepository(db),
                product_repository=DbProductRepository(db),
                catalog_provider=catalog
            )

        # Testing (In-Memory)
        if AppContainer._stock_service_instance is None:
            AppContainer._stock_service_instance = StockService(
                home_repository=InMemoryHomeRepository(),
                product_repository=InMemoryProductRepository(),
                catalog_provider=catalog
            )
        
        return AppContainer._stock_service_instance

    @staticmethod
    def get_management_service(db: Optional[Session] = None) -> ManagementService:
        # Production (DB)
        if db:
            return ManagementService(home_repository=DbHomeRepository(db), user_repository=DbUserRepository(db))
        
        # Testing (In-Memory)
        if AppContainer._management_service_instance is None:
            AppContainer._management_service_instance = ManagementService(
                home_repository=InMemoryHomeRepository(),
                user_repository=InMemoryUserRepository()
            )
            
        return AppContainer._management_service_instance