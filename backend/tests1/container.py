import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from fastapi.testclient import TestClient
from src.main import app
from src.infrastructure.db.database import get_db, Base 

# In-Memory Repos
from src.infrastructure.repositories.in_memory_user_repository import InMemoryUserRepository
from src.infrastructure.repositories.in_memory_product_repository import InMemoryProductRepository
from src.infrastructure.repositories.in_memory_home_repository import InMemoryHomeRepository
from src.infrastructure.repositories.in_memory_shopping_list_repository import InMemoryShoppingListRepository

# DB Repos
from src.infrastructure.repositories.db_user_repository import DbUserRepository
from src.infrastructure.repositories.db_product_repository import DbProductRepository
from src.infrastructure.repositories.db_home_repository import DbHomeRepository
from src.infrastructure.repositories.db_shopping_list_repository import DbShoppingListRepository

# Services & Auth
from src.services.user_service import UserService
from src.services.stock_service import StockService
from src.services.management_service import ManagementService
from src.services.shopping_list_service import ShoppingListService
from src.infrastructure.auth.jwt_auth_provider import JwtAuthProvider

# Route Dependencies
from src.api.routes.auth_routes import get_user_service
from src.api.routes.stock_routes import get_stock_service
from src.api.routes.management_routes import get_management_service
from src.api.routes.shopping_routes import get_shopping_list_service

load_dotenv()


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

class MockCatalogProvider:
    async def get_item_by_barcode(self, barcode, chain_name=None):
        return None
    async def search_items_by_name(self, query):
        return []
    
class MockSupabaseAuthProvider:
    """
    A fake Auth Provider for tests that doesn't 
    touch the real Supabase API.
    """
    def verify_token(self, token: str):
        # In tests, we often override this logic anyway, 
        # so returning None or a dummy value is safe.
        return None

class TestingContainer:

    def __init__(self):
        self.auth_provider = MockSupabaseAuthProvider()
        self.catalog_provider = MockCatalogProvider()
        self.client = TestClient(app)
        
        self.active_mode = "memory"
        self.db_session = None
        self.engine = None
        
        # Start in memory mode by default
        self._configure_memory_mode()

    def _configure_services_and_overrides(self):
        """Reloads services with current repositories."""
        self.user_service = UserService(user_repo=self.user_repo, auth_provider=self.auth_provider)
        self.stock_service = StockService(home_repository=self.home_repo, product_repository=self.stock_repo, catalog_provider=self.catalog_provider, user_repository=self.user_repo)
        self.management_service = ManagementService(home_repository=self.home_repo,user_repository=self.user_repo)
        self.shopping_list_service = ShoppingListService(shopping_repo=self.shopping_list_repo)

        app.dependency_overrides[get_user_service] = lambda: self.user_service
        app.dependency_overrides[get_stock_service] = lambda: self.stock_service
        app.dependency_overrides[get_management_service] = lambda: self.management_service
        app.dependency_overrides[get_shopping_list_service] = lambda: self.shopping_list_service

    def _close_db_resources(self):
        """Force close session and dispose engine to prevent locks."""
        if self.db_session:
            try:
                self.db_session.close()
            except Exception:
                pass
        
        if self.engine:
            self.engine.dispose()

    def _configure_memory_mode(self):
        self._close_db_resources()

        self.user_repo = InMemoryUserRepository()
        self.stock_repo = InMemoryProductRepository()
        self.home_repo = InMemoryHomeRepository()
        self.shopping_list_repo = InMemoryShoppingListRepository()
        
        app.dependency_overrides[get_db] = lambda: None
        self._configure_services_and_overrides()

    def _configure_db_mode(self):
        self._close_db_resources()

        # CRITICAL: poolclass=NullPool
        # This prevents SQLAlchemy from keeping idle connections open, 
        # which causes deadlocks when we try to TRUNCATE tables during tests.
        self.engine = create_engine(TEST_DATABASE_URL, poolclass=NullPool)
        
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create schema if not exists
        Base.metadata.create_all(bind=self.engine)
        
        self.db_session = self.TestingSessionLocal()
        
        self.user_repo = DbUserRepository(self.db_session)
        self.stock_repo = DbProductRepository(self.db_session)
        self.home_repo = DbHomeRepository(self.db_session)
        self.shopping_list_repo = DbShoppingListRepository(self.db_session)

        app.dependency_overrides[get_db] = lambda: self.db_session
        self._configure_services_and_overrides()

    # --- Public Methods ---

    def activate_db_mode(self):
        if self.active_mode != "db":
            self.active_mode = "db"
            self._configure_db_mode()

    def activate_memory_mode(self):
        if self.active_mode != "memory":
            self.active_mode = "memory"
            self._configure_memory_mode()

    def reset_state(self):
        if self.active_mode == "db":
            # 1. Close the previous session to release any transaction locks
            if self.db_session:
                self.db_session.close()

            # 2. Create a temporary session for cleanup
            cleanup_session = self.TestingSessionLocal()
            
            try:
                # 3. TRUNCATE ... CASCADE
                cleanup_session.execute(text("""
                TRUNCATE TABLE products, product_items, homes, users, shopping_lists 
                RESTART IDENTITY CASCADE;
                """))
                cleanup_session.commit()
            except Exception as e:
                print(f"DB Cleanup Failed: {e}")
                cleanup_session.rollback()
                raise e  # CRITICAL: Fail fast if we can't clean the DB!
            finally:
                cleanup_session.close()

            # 4. Create a NEW session for the next test
            self.db_session = self.TestingSessionLocal()
            
            # 5. RECREATE repositories cleanly with the fresh session
            self.user_repo = DbUserRepository(self.db_session)
            self.stock_repo = DbProductRepository(self.db_session)
            self.home_repo = DbHomeRepository(self.db_session)
            self.shopping_list_repo = DbShoppingListRepository(self.db_session)
            # 6. Update FastAPI Override and Services
            app.dependency_overrides[get_db] = lambda: self.db_session
            self._configure_services_and_overrides()

        else:
            # Memory Cleanup
            self.user_repo.users.clear()
            self.stock_repo._products_db.clear()
            self.home_repo._storage.clear()
            self.shopping_list_repo._lists.clear()

testing_container = TestingContainer()