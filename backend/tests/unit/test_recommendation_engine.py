import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from src.domain.recommendation.engine import RecommendationEngine, StoreType
from src.domain.receipt.receipt import ReceiptDTO, ReceiptItemDTO

# --- Helper Mock Classes ---

class MockLocation:
    def __init__(self, name):
        self.name = name

class MockItem:
    def __init__(self, quantity, location_name):
        self.quantity = quantity
        self.location = MockLocation(location_name)

class MockProduct:
    def __init__(self, barcode, original_name, items=None, nickname=None):
        self.barcode = barcode
        self.original_name = original_name
        self.items = items or []
        self.nickname = nickname

# --- Test Suite ---

@pytest.fixture
def mock_repos():
    product_repo = AsyncMock()
    receipt_repo = AsyncMock()
    return product_repo, receipt_repo

@pytest.fixture
def engine(mock_repos):
    p_repo, r_repo = mock_repos
    return RecommendationEngine(p_repo, r_repo)

@pytest.mark.asyncio
async def test_get_recommendations_empty_cart(engine):
    """Should return empty list if cart is empty."""
    res = await engine.get_recommendations_for_home(uuid4(), [])
    assert res == []

@pytest.mark.asyncio
async def test_get_recommendations_no_history(engine, mock_repos):
    """Should return empty list if no history exists."""
    p_repo, r_repo = mock_repos
    r_repo.get_by_home.return_value = []
    p_repo.list_all_by_home.return_value = []
    
    res = await engine.get_recommendations_for_home(uuid4(), ["Milk"])
    assert res == []

@pytest.mark.asyncio
async def test_staple_recommendation_logic(engine, mock_repos):
    """Test that frequently bought items (staples) are suggested correctly."""
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    user_id = uuid4()
    
    # 3 receipts with Bread (bc1)
    receipts = [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=user_id, chain="Rami Levi", items=[
            ReceiptItemDTO(name="לחם", barcode="bc1", quantity=1)
        ]) for _ in range(3)
    ]
    r_repo.get_by_home.return_value = receipts
    
    # Bread is out of stock (quantity=0)
    mock_product = MockProduct("bc1", "לחם", [MockItem(0, "PANTRY")])
    p_repo.list_all_by_home.return_value = [mock_product]
    
    # Act: Search for something else (e.g. Milk)
    res = await engine.get_recommendations_for_home(home_id, ["חלב"])
    
    # Assert: Bread should be suggested as a staple
    names = [r['name'] for r in res]
    assert "לחם" in names
    assert any(r['type'] == 'staple' for r in res)

@pytest.mark.asyncio
async def test_pairing_synergy_boost_out_of_stock(engine, mock_repos):
    """Test synergy boost: Cheese is suggested when Bread+Milk are in cart AND it is out of stock."""
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    user_id = uuid4()
    
    receipts = [
        *[ReceiptDTO(id=uuid4(), home_id=home_id, user_id=user_id, chain="Rami Levi", items=[
            ReceiptItemDTO(name="לחם", barcode="bc_bread", quantity=1),
            ReceiptItemDTO(name="גבינה", barcode="bc_cheese", quantity=1)
        ]) for _ in range(3)],
        *[ReceiptDTO(id=uuid4(), home_id=home_id, user_id=user_id, chain="Rami Levi", items=[
            ReceiptItemDTO(name="חלב", barcode="bc_milk", quantity=1),
            ReceiptItemDTO(name="גבינה", barcode="bc_cheese", quantity=1)
        ]) for _ in range(3)],
    ]
    r_repo.get_by_home.return_value = receipts
    
    prods = [
        MockProduct("bc_bread", "לחם", [MockItem(1, "PANTRY")]),
        MockProduct("bc_milk", "חלב", [MockItem(1, "FRIDGE")]),
        MockProduct("bc_cheese", "גבינה", [MockItem(0, "FRIDGE")]), # OUT OF STOCK
    ]
    p_repo.list_all_by_home.return_value = prods
    
    res = await engine.get_recommendations_for_home(home_id, ["לחם", "חלב"])
    
    names = [r['name'] for r in res]
    assert "גבינה" in names

@pytest.mark.asyncio
async def test_pairing_synergy_boost_in_stock(engine, mock_repos):
    """Test synergy boost suppression: Cheese is NOT suggested when it is already in stock."""
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    user_id = uuid4()
    
    receipts = [
        *[ReceiptDTO(id=uuid4(), home_id=home_id, user_id=user_id, chain="Rami Levi", items=[
            ReceiptItemDTO(name="לחם", barcode="bc_bread", quantity=1),
            ReceiptItemDTO(name="גבינה", barcode="bc_cheese", quantity=1)
        ]) for _ in range(3)],
    ]
    r_repo.get_by_home.return_value = receipts
    
    prods = [
        MockProduct("bc_bread", "לחם", [MockItem(1, "PANTRY")]),
        MockProduct("bc_cheese", "גבינה", [MockItem(2, "FRIDGE")]), # IN STOCK (quantity=2)
    ]
    p_repo.list_all_by_home.return_value = prods
    
    res = await engine.get_recommendations_for_home(home_id, ["לחם"])
    
    names = [r['name'] for r in res]
    assert "גבינה" not in names

@pytest.mark.asyncio
async def test_attribute_aware_staple_filtering(engine, mock_repos):
    """Test that searching for 'Soy' doesn't suggest 'Regular' milk if they differ by attributes."""
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    user_id = uuid4()
    
    receipts = [
        *[ReceiptDTO(id=uuid4(), home_id=home_id, user_id=user_id, chain="Rami Levi", items=[
            ReceiptItemDTO(name="חלב תנובה", barcode="bc_reg", quantity=1)
        ]) for _ in range(4)]
    ]
    r_repo.get_by_home.return_value = receipts
    
    prods = [
        MockProduct("bc_reg", "חלב תנובה", [MockItem(0, "FRIDGE")]),
        MockProduct("bc_soy", "חלב סויה", [MockItem(1, "FRIDGE")]),
    ]
    p_repo.list_all_by_home.return_value = prods
    
    # Act: Search for "חלב סויה"
    res = await engine.get_recommendations_for_home(home_id, ["חלב סויה"])
    
    names = [r['name'] for r in res]
    assert "חלב תנובה" not in names

@pytest.mark.asyncio
async def test_mixed_store_context_priority(engine, mock_repos):
    """Test that Pharmacy signal overrides Grocery when both are present."""
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    user_id = uuid4()
    
    receipts = [
        *[ReceiptDTO(id=uuid4(), home_id=home_id, user_id=user_id, chain="Be", items=[
            ReceiptItemDTO(name="ויטמין", barcode="bc_vit", quantity=1)
        ]) for _ in range(3)],
        *[ReceiptDTO(id=uuid4(), home_id=home_id, user_id=user_id, chain="Rami Levi", items=[
            ReceiptItemDTO(name="לחם", barcode="bc_bread", quantity=1)
        ]) for _ in range(3)],
    ]
    r_repo.get_by_home.return_value = receipts
    
    prods = [
        MockProduct("bc_vit", "ויטמין", [MockItem(0, "OTHER")]),
        MockProduct("bc_bread", "לחם", [MockItem(0, "PANTRY")]),
    ]
    p_repo.list_all_by_home.return_value = prods
    
    # Act: Cart has BOTH a Grocery item (Milk) and a Pharmacy item (Acamol)
    res = await engine.get_recommendations_for_home(home_id, ["חלב", "אקמול"])
    
    names = [r['name'] for r in res]
    assert "ויטמין" in names
    assert "לחם" not in names

if __name__ == "__main__":
    pass
