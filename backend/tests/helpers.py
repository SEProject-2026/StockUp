from datetime import date, timedelta
from uuid import UUID, uuid4
from src.domain.enums import LocationType
from tests.factories import create_product_entity, create_user_entity, create_home_entity

class ServiceTestHelpers:
    """Helper methods to setup complex scenarios for Service testing."""

    @staticmethod
    def setup_mock_user(mock_user_repo, **kwargs):
        """Creates a user and configures the mock repo to return it."""
        user = create_user_entity(**kwargs)
        mock_user_repo.get_by_id.return_value = user
        mock_user_repo.get_by_email.return_value = user
        return user

    @staticmethod
    def setup_home_with_admin(mock_home_repo, mock_user_repo, **kwargs):
        """
        Scenario: A home exists with an assigned admin.
        Returns: (admin_user, home_entity)
        """
        # 1. Create the admin user
        admin = create_user_entity()
        mock_user_repo.get_by_id.return_value = admin
        
        # 2. Create the home and set admin
        home = create_home_entity(admin_user_id=admin.id, **kwargs)
        mock_home_repo.get_by_id.return_value = home
        
        return admin, home

    @staticmethod
    def setup_home_with_member(mock_home_repo, mock_user_repo):
        """
        Scenario: A home exists with an admin AND a regular member.
        Returns: (admin_user, member_user, home_entity)
        """
        admin, home = ServiceTestHelpers.setup_home_with_admin(mock_home_repo, mock_user_repo)
        
        # Create and add a member
        member = create_user_entity(email="member@test.com")
        home.add_member(member.id)
        
        # We need to decide what get_by_id returns if called twice. 
        # Usually, Side Effects are better for multiple different returns:
        mock_user_repo.get_by_id.side_effect = [admin, member]
        
        return admin, member, home
    
    @staticmethod
    def setup_mock_product(mock_product_repo, home_id: UUID, name: str = "Milk", quantity: int = 5):
        """
        Creates a product entity, populates it using domain methods, 
        and configures the repository mock to return it.
        """
        # 1. Create the entity shell
        product = create_product_entity(home_id=home_id, name=name)
        
        # 2. Use the domain method to add the initial stock
        product.add_item(quantity=quantity, location=LocationType.OTHER)
        
        # 3. Configure repo mocks
        mock_product_repo.get_by_id.return_value = product
        mock_product_repo.get_by_original_name.return_value = product
        
        # Return the product and the specific item batch created
        return product, product.items[0]
    
    @staticmethod
    def setup_diverse_inventory(mock_product_repo, home_id: UUID):
        """
        Creates a realistic home inventory with various locations and expiration states.
        Returns a dictionary of created products for easy assertion.
        """
        today = date.today()

        # 1. Fresh Milk in Fridge (Expiring in 7 days)
        milk = create_product_entity(home_id=home_id, name="Milk", barcode="111")
        milk.add_item(quantity=2, location=LocationType.FRIDGE, expiration_date=today + timedelta(days=7))
        
        # 2. Old Eggs in Fridge (Expired 2 days ago)
        eggs = create_product_entity(home_id=home_id, name="Eggs", barcode="222")
        eggs.add_item(quantity=12, location=LocationType.FRIDGE, expiration_date=today - timedelta(days=2))
        
        # 3. Pasta in Pantry (No expiration, 5 units)
        pasta = create_product_entity(home_id=home_id, name="Pasta", barcode="333")
        pasta.add_item(quantity=5, location=LocationType.PANTRY)

        # 4. Meat in Freezer (Expiring tomorrow - Warning zone)
        meat = create_product_entity(home_id=home_id, name="Ground Beef", barcode="444")
        meat.add_item(quantity=1, location=LocationType.FREEZER, expiration_date=today + timedelta(days=1))

        inventory = [milk, eggs, pasta, meat]
        mock_product_repo.list_all_by_home.return_value = inventory
        
        return {
            "milk": milk,
            "eggs": eggs,
            "pasta": pasta,
            "meat": meat,
            "all": inventory
        }
    
    @staticmethod
    def setup_search_scenario(mock_product_repo, mock_catalog_provider, home_id: UUID):
        """
        Sets up a scenario for testing local and external searches.
        """
        # Local Inventory
        milk = create_product_entity(home_id=home_id, name="Milk", nickname="White Gold")
        bread = create_product_entity(home_id=home_id, name="Whole Wheat Bread")
        
        # External Catalog Items
        from src.repositories.catalog_provider import CatalogItem
        ext_milk = CatalogItem(barcode="111", name="Organic Milk", location=LocationType.FRIDGE)
        ext_cheese = CatalogItem(barcode="222", name="Cheddar Cheese", location=LocationType.FRIDGE)

        # Configure Mocks
        mock_product_repo.search_by_name.return_value = [milk]
        mock_catalog_provider.search_items_by_name.return_value = [ext_milk, ext_cheese]
        mock_catalog_provider.get_item_by_barcode.return_value = ext_milk

        return {"local": [milk, bread], "external": [ext_milk, ext_cheese]}
    
class ApiTestHelpers:
    """Helper methods for API-level integration testing."""

    @staticmethod
    def auth_headers(token: str = "mocked_token"):
        """Returns standard authorization headers."""
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def register_user(client, user_id: UUID, email: str, name: str):
        """Helper to register a user via the API endpoint."""
        payload = {
            "user_id": str(user_id),
            "email": email,
            "name": name
        }
        return client.post("/auth/register", json=payload)

    @staticmethod
    def update_user_name(client, name: str, token: str = "mocked"):
        """Helper to update user name via the protected API endpoint."""
        return client.put(
            "/auth/update_name", 
            json={"name": name}, 
            headers=ApiTestHelpers.auth_headers(token)
        )
