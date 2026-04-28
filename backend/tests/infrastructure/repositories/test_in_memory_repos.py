import pytest
import datetime
from uuid import uuid4
from unittest.mock import MagicMock

# יבוא של כל הרפוזיטורים 
from src.infrastructure.repositories.in_memory_home_repository import InMemoryHomeRepository
from src.infrastructure.repositories.in_memory_user_repository import InMemoryUserRepository
from src.infrastructure.repositories.in_memory_shopping_list_repository import InMemoryShoppingListRepository
from src.infrastructure.repositories.in_memory_receipt_repository import InMemoryReceiptRepository
from src.infrastructure.repositories.in_memory_product_repository import InMemoryProductRepository
from src.domain.enums import LocationType, ExpirationType

# ==========================================
# 1. Test InMemoryHomeRepository
# ==========================================

@pytest.mark.asyncio
class TestInMemoryHomeRepository:
    async def test_home_crud(self):
        repo = InMemoryHomeRepository()
        home = MagicMock()
        h_id = uuid4()
        home.get_id.return_value = h_id
        home.get_join_code.return_value = "CODE123"
        home.get_name.return_value = "My Home"
        home.is_member.return_value = True

        # Save & Get
        await repo.save(home)
        assert await repo.get_by_id(h_id) == home
        assert await repo.get_by_id(uuid4()) is None

        # Get by join code & name
        assert await repo.get_by_join_code("CODE123") == home
        assert await repo.get_by_join_code("WRONG") is None
        assert await repo.get_by_name("My Home") == home
        assert await repo.get_by_name("Wrong") is None

        # Get by user & batch
        assert len(await repo.get_homes_by_user_id(uuid4())) == 1
        assert len(await repo.get_homes_batch(limit=1)) == 1

        # Update & Delete
        await repo.update(home) # Overwrites
        await repo.delete(h_id)
        assert await repo.get_by_id(h_id) is None
        # Delete non-existent (should not crash)
        await repo.delete(h_id)


# ==========================================
# 2. Test InMemoryUserRepository
# ==========================================

@pytest.mark.asyncio
class TestInMemoryUserRepository:
    async def test_user_crud(self):
        repo = InMemoryUserRepository()
        user = MagicMock()
        u_id = uuid4()
        user.id = u_id
        user.email = "test@test.com"
        user.name = "John"

        # Save & Get
        await repo.save(user)
        assert await repo.get_by_id(u_id) == user
        assert await repo.get_by_id(uuid4()) is None
        assert await repo.get_by_email("test@test.com") == user
        assert await repo.get_by_email("wrong@test.com") is None

        # Get names
        names = await repo.get_names_by_ids([u_id, uuid4()])
        assert names[u_id] == "John"

        # Update push token
        updated = await repo.update_push_token(u_id, "new_token")
        user.update_push_token.assert_called_with("new_token")
        assert updated == user
        assert await repo.update_push_token(uuid4(), "token") is None


# ==========================================
# 3. Test InMemoryShoppingListRepository
# ==========================================

@pytest.mark.asyncio
class TestInMemoryShoppingListRepository:
    async def test_shopping_list_crud(self):
        repo = InMemoryShoppingListRepository()
        s_list = MagicMock()
        l_id = uuid4()
        h_id = uuid4()
        s_list.id = l_id
        s_list.home_id = h_id

        await repo.save(s_list)
        assert await repo.get_by_id(l_id) == s_list
        assert len(await repo.get_all_by_home(h_id)) == 1
        assert len(await repo.get_all_by_home(uuid4())) == 0

        await repo.delete(l_id)
        assert await repo.get_by_id(l_id) is None
        # Delete non-existent
        await repo.delete(l_id)


# ==========================================
# 4. Test InMemoryReceiptRepository
# ==========================================

@pytest.mark.asyncio
class TestInMemoryReceiptRepository:
    async def test_receipt_crud(self):
        repo = InMemoryReceiptRepository()
        receipt1 = MagicMock()
        receipt2 = MagicMock()
        h_id = uuid4()
        receipt1.home_id = h_id
        receipt2.home_id = h_id

        await repo.save(receipt1)
        await repo.save(receipt2)

        res = await repo.get_by_home(h_id, limit=1)
        # Should be reversed, so receipt2 comes first
        assert len(res) == 1
        assert res[0] == receipt2


# ==========================================
# 5. Test InMemoryProductRepository
# ==========================================

# Dummy classes to survive copy.deepcopy() inside filter_products
class DummyItem:
    def __init__(self, location, expiration_date=None):
        self.location = location
        self.expiration_date = expiration_date

class DummyProduct:
    def __init__(self, p_id, h_id, name, nickname, items):
        self.id = p_id
        self.home_id = h_id
        self.original_name = name
        self.nickname = nickname
        self.items = items
        self._items = items

@pytest.mark.asyncio
class TestInMemoryProductRepository:
    async def test_product_crud_and_search(self):
        repo = InMemoryProductRepository()
        h_id = uuid4()
        p_id = uuid4()
        product = DummyProduct(p_id, h_id, "Milk", "Soy", [DummyItem(LocationType.FRIDGE)])

        # Save & Get
        await repo.save(product)
        assert await repo.get_by_id(p_id) == product
        assert await repo.get_by_original_name(h_id, "Milk") == product
        assert await repo.get_by_original_name(h_id, "Wrong") is None

        # Search By Name
        assert len(await repo.search_by_name(h_id, "milk")) == 1
        assert len(await repo.search_by_name(h_id, "soy")) == 1
        assert len(await repo.search_by_name(h_id, "bread")) == 0
        assert len(await repo.search_by_name(uuid4(), "milk")) == 0 # wrong home

        # Location
        assert len(await repo.get_by_location(h_id, LocationType.FRIDGE)) == 1
        assert len(await repo.get_by_location(h_id, LocationType.PANTRY)) == 0

        # Save All & List
        p2 = DummyProduct(uuid4(), h_id, "Bread", None, [])
        await repo.save_all([p2])
        assert len(await repo.list_all_by_home(h_id)) == 2

        # Update
        product.original_name = "Oat Milk"
        await repo.update(product)
        assert (await repo.get_by_id(p_id)).original_name == "Oat Milk"
        with pytest.raises(KeyError):
            await repo.update(DummyProduct(uuid4(), h_id, "", "", []))

        # Delete & Clear
        await repo.delete(p_id)
        assert await repo.get_by_id(p_id) is None
        with pytest.raises(KeyError):
            await repo.delete(p_id)
        
        await repo.clear()
        assert len(await repo.list_all_by_home(h_id)) == 0

    async def test_filter_products(self):
        repo = InMemoryProductRepository()
        h_id = uuid4()
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)
        next_week = today + datetime.timedelta(days=7)

        i_expired = DummyItem(LocationType.FRIDGE, yesterday)
        i_soon = DummyItem(LocationType.PANTRY, tomorrow)
        i_fresh = DummyItem(LocationType.FRIDGE, next_week)
        
        p = DummyProduct(uuid4(), h_id, "Cheese", None, [i_expired, i_soon, i_fresh])
        await repo.save(p)

        # 1. Filter by Text
        res = await repo.filter_products(h_id, query_text="cheese")
        assert len(res) == 1
        res = await repo.filter_products(h_id, query_text="wrong")
        assert len(res) == 0

        # 2. Filter by Location
        res = await repo.filter_products(h_id, location=LocationType.FRIDGE)
        assert len(res[0]._items) == 2 # expired & fresh are in fridge
        
        # 3. Filter by Expiration (EXPIRED)
        res = await repo.filter_products(h_id, expiration_type=ExpirationType.EXPIRED)
        assert len(res[0]._items) == 1
        assert res[0]._items[0] == i_expired

        # 4. Filter by Expiration (GOING_TO_EXPIRE) - warning_days=3
        res = await repo.filter_products(h_id, expiration_type=ExpirationType.GOING_TO_EXPIRE, warning_days=3)
        assert len(res[0]._items) == 1
        assert res[0]._items[0] == i_soon

        # 5. Filter by Expiration (FRESH) - warning_days=3
        res = await repo.filter_products(h_id, expiration_type=ExpirationType.FRESH, warning_days=3)
        assert len(res[0]._items) == 1
        assert res[0]._items[0] == i_fresh

        # 6. Combo (Location + Expiration) yielding empty items -> product omitted
        res = await repo.filter_products(h_id, location=LocationType.PANTRY, expiration_type=ExpirationType.EXPIRED)
        assert len(res) == 0