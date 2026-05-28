from pathlib import Path
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

# --- Services ---
from src.infrastructure.scanner.receipt_scanner import ReceiptScanner
from src.infrastructure.repositories.db_shopping_list_repository import DbShoppingListRepository
from src.infrastructure.repositories.in_memory_shopping_list_repository import InMemoryShoppingListRepository
from src.services.shopping_list_service import ShoppingListService
from src.services.user_service import UserService
from src.services.stock_service import StockService
from src.services.management_service import ManagementService
from src.services.recommendation_service import RecommendationService
from src.domain.recommendation.engine import RecommendationEngine

# --- Auth ---
from src.infrastructure.auth.supabase_auth_provider import SupabaseAuthProvider

# --- Repositories (DB Implementation) ---
from src.infrastructure.repositories.db_user_repository import DbUserRepository
from src.infrastructure.repositories.db_home_repository import DbHomeRepository
from src.infrastructure.repositories.db_product_repository import DbProductRepository
from src.infrastructure.repositories.db_receipt_repository import DbReceiptRepository

# --- Repositories (In-Memory for Tests) ---
from src.infrastructure.repositories.in_memory_user_repository import InMemoryUserRepository
from src.infrastructure.repositories.in_memory_home_repository import InMemoryHomeRepository
from src.infrastructure.repositories.in_memory_product_repository import InMemoryProductRepository
from src.infrastructure.repositories.in_memory_receipt_repository import InMemoryReceiptRepository

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
    _shopping_list_service_instance = None
    _recommendation_service_instance = None
    _receipt_scanner_instance = None

    @staticmethod
    def get_auth_provider():
        if AppContainer._auth_provider_instance is None:
            #AppContainer._auth_provider_instance = JwtAuthProvider()
            AppContainer._auth_provider_instance = SupabaseAuthProvider()
        return AppContainer._auth_provider_instance
    
    @staticmethod
    def get_receipt_scanner():
        if AppContainer._receipt_scanner_instance is None:
                AppContainer._receipt_scanner_instance = ReceiptScanner()
        return AppContainer._receipt_scanner_instance

    @staticmethod
    def get_catalog_provider(db: Optional[AsyncSession] = None):
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
    def get_user_service(db: Optional[AsyncSession] = None) -> UserService:
        """
        Returns a UserService.
        - If 'db' is provided: Returns a new instance connected to the DB (Production).
        - If 'db' is None: Returns a singleton instance with InMemory repository (Testing).
        """

        # Production (DB)
        if db:
            repo = DbUserRepository(db)
            return UserService(user_repo=repo)

        # Testing (In-Memory)
        if AppContainer._user_service_instance is None:
            repo = InMemoryUserRepository()
            AppContainer._user_service_instance = UserService(user_repo=repo)
        
        return AppContainer._user_service_instance

    @staticmethod
    def get_stock_service(db: Optional[AsyncSession] = None) -> StockService:
        catalog = AppContainer.get_catalog_provider(db)
        scanner = AppContainer.get_receipt_scanner()

        # Production (DB)
        if db:
            return StockService(
                home_repository=DbHomeRepository(db),
                product_repository=DbProductRepository(db),
                catalog_provider=catalog,
                user_repository=DbUserRepository(db),
                receipt_repository=DbReceiptRepository(db),
                receipt_scanner=scanner
            )

        # Testing (In-Memory)
        if AppContainer._stock_service_instance is None:
            AppContainer._stock_service_instance = StockService(
                home_repository=InMemoryHomeRepository(),
                product_repository=InMemoryProductRepository(),
                catalog_provider=catalog,
                user_repository=InMemoryUserRepository(),
                receipt_repository=InMemoryReceiptRepository(),
                receipt_scanner=scanner
            )
        
        return AppContainer._stock_service_instance

    @staticmethod
    def get_management_service(db: Optional[AsyncSession] = None) -> ManagementService:
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
    
    @staticmethod
    def get_shopping_list_service(db: Optional[AsyncSession] = None):
        # Production (DB)
        if db:
            return ShoppingListService(shopping_repo=DbShoppingListRepository(db))
        
        # Testing (In-Memory)
        if AppContainer._shopping_list_service_instance is None:
            AppContainer._shopping_list_service_instance = ShoppingListService(
                shopping_repo=InMemoryShoppingListRepository()
            )
            
        return AppContainer._shopping_list_service_instance

    @staticmethod
    def get_recommendation_engine(db: Optional[AsyncSession] = None):
        if db:
            return RecommendationEngine(
                product_repository=DbProductRepository(db),
                receipt_repository=DbReceiptRepository(db)
            )
        return RecommendationEngine(
            product_repository=InMemoryProductRepository(),
            receipt_repository=InMemoryReceiptRepository()
        )

    @staticmethod
    def get_recommendation_service(db: Optional[AsyncSession] = None):
        engine = AppContainer.get_recommendation_engine(db)
        # Production (DB)
        if db:
            return RecommendationService(engine=engine)
        
        # Testing (In-Memory)
        if AppContainer._recommendation_service_instance is None:
            AppContainer._recommendation_service_instance = RecommendationService(engine=engine)
            
        return AppContainer._recommendation_service_instance