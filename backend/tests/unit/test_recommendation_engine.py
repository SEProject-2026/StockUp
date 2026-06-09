import pytest
import math
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from src.domain.recommendation.engine import RecommendationEngine, StoreType, EngineMetadata, EngineContext
from src.domain.receipt.receipt import ReceiptDTO, ReceiptItemDTO

# --- Helper Mock Classes ---

class MockLocation:
    def __init__(self, name):
        self.name = name

class MockInventoryItem:
    def __init__(self, quantity, location_name):
        self.quantity = quantity
        self.location = MockLocation(location_name)

class MockProduct:
    def __init__(self, barcode, original_name, items=None, nickname=None):
        self.barcode = barcode
        self.original_name = original_name
        self.items = items or []
        self.nickname = nickname

# --- Test Fixtures ---

@pytest.fixture
def mock_repos():
    product_repo = AsyncMock()
    receipt_repo = AsyncMock()
    return product_repo, receipt_repo

@pytest.fixture
def engine(mock_repos):
    p_repo, r_repo = mock_repos
    return RecommendationEngine(p_repo, r_repo)

# --- Unit Tests for Internal Helpers ---

def test_get_generic_name(engine):
    """Verify noun extraction from diverse Hebrew strings."""
    # Simple cases
    assert engine._get_generic_name("חלב") == "חלב"
    assert engine._get_generic_name("לחם") == "לחם"
    
    # Brand stripping
    assert engine._get_generic_name("חלב תנובה") == "חלב"
    assert engine._get_generic_name("גבינה שטראוס") == "גבינה"
    
    # Two-word nouns
    assert engine._get_generic_name("נייר טואלט") == "נייר טואלט"
    assert engine._get_generic_name("שמן זית") == "שמן זית"
    assert engine._get_generic_name("גבינה לבנה") == "גבינה לבנה"
    
    # Base categories keeping descriptor
    assert engine._get_generic_name("מיץ תפוזים") == "מיץ תפוזים"
    assert engine._get_generic_name("יוגורט תות") == "יוגורט תות"
    
    # Cleaning punctuation
    assert engine._get_generic_name("חלב!") == "חלב"
    assert engine._get_generic_name("לחם, פרוס") == "לחם"

def test_classify_receipt_store_type(engine):
    """Verify store classification based on chain and items."""
    # Chain name based - using lowercase as per keywords in engine
    r_pharm = ReceiptDTO(id=uuid4(), home_id=uuid4(), user_id=uuid4(), chain="super-pharm", items=[])
    assert engine._classify_receipt_store_type(r_pharm, {}) == StoreType.PHARMACY
    
    r_grocery = ReceiptDTO(id=uuid4(), home_id=uuid4(), user_id=uuid4(), chain="רמי לוי", items=[])
    assert engine._classify_receipt_store_type(r_grocery, {}) == StoreType.GROCERY
    
    # Keyword based
    r_hint_p = ReceiptDTO(id=uuid4(), home_id=uuid4(), user_id=uuid4(), items=[
        ReceiptItemDTO(name="אקמול", barcode="bc1", quantity=1)
    ])
    assert engine._classify_receipt_store_type(r_hint_p, {}) == StoreType.PHARMACY
    
    r_hint_g = ReceiptDTO(id=uuid4(), home_id=uuid4(), user_id=uuid4(), items=[
        ReceiptItemDTO(name="עגבניה", barcode="bc2", quantity=1)
    ])
    assert engine._classify_receipt_store_type(r_hint_g, {}) == StoreType.GROCERY
    
    # Location fallback
    r_loc = ReceiptDTO(id=uuid4(), home_id=uuid4(), user_id=uuid4(), items=[
        ReceiptItemDTO(name="פריט", barcode="bc_f", quantity=1)
    ])
    assert engine._classify_receipt_store_type(r_loc, {"bc_f": "FRIDGE"}) == StoreType.GROCERY

def test_fuzzy_match_products(engine):
    """Verify attribute-aware fuzzy matching."""
    name_to_bc = {
        "חלב תנובה 3%": "bc_reg",
        "חלב סויה": "bc_soy",
        "לחם פרוס": "bc_bread",
        "גבינה לבנה": "bc_cheese"
    }
    
    # Direct match
    assert "bc_reg" in engine._fuzzy_match_products("חלב תנובה", name_to_bc)
    
    # Attribute guard: "Soy" search should not match "Regular"
    assert "bc_reg" not in engine._fuzzy_match_products("חלב סויה", name_to_bc)
    assert "bc_soy" in engine._fuzzy_match_products("חלב סויה", name_to_bc)
    
    # Clean text match
    assert "bc_cheese" in engine._fuzzy_match_products("גבינה לבנה!", name_to_bc)

@pytest.mark.asyncio
async def test_infer_shopping_context(engine):
    """Verify context inference from cart items."""
    metadata = EngineMetadata()
    metadata.name_to_bc = {"אקמול": "bc_p", "חלב": "bc_g"}
    metadata.bc_to_cat = {"bc_p": "אקמול", "bc_g": "חלב"}
    
    receipts = [
        ReceiptDTO(id=uuid4(), home_id=uuid4(), user_id=uuid4(), chain="be", items=[
            ReceiptItemDTO(name="אקמול", barcode="bc_p", quantity=1)
        ])
    ]
    
    # Cart has pharmacy item
    ctx = engine._infer_shopping_context(["אקמול"], receipts, metadata)
    assert StoreType.PHARMACY in ctx.active_store_types
    assert "אקמול" in ctx.mapped_cart_categories
    
    # Cart has grocery item
    ctx = engine._infer_shopping_context(["חלב"], receipts, metadata)
    assert "חלב" in ctx.mapped_cart_categories

# --- Orchestration Tests ---

@pytest.mark.asyncio
async def test_get_recommendations_staples_threshold(engine, mock_repos):
    """Test that staples require 10 receipts as per new requirement."""
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    
    # Scenario: Item bought 9 times (less than 10)
    receipts_9 = [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), chain="רמי לוי", items=[
            ReceiptItemDTO(name="לחם", barcode="bc1", quantity=1)
        ]) for _ in range(9)
    ]
    r_repo.get_by_home.return_value = receipts_9
    p_repo.list_all_by_home.return_value = [MockProduct("bc1", "לחם", [MockInventoryItem(0, "PANTRY")])]
    
    res = await engine.get_recommendations_for_home(home_id, ["חלב"])
    assert not any(r['name'] == "לחם" for r in res)
    
    # Scenario: Item bought 10 times
    receipts_10 = [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), chain="רמי לוי", items=[
            ReceiptItemDTO(name="לחם", barcode="bc1", quantity=1)
        ]) for _ in range(10)
    ]
    r_repo.get_by_home.return_value = receipts_10
    
    res = await engine.get_recommendations_for_home(home_id, ["חלב"])
    assert any(r['name'] == "לחם" for r in res)

@pytest.mark.asyncio
async def test_pairing_no_location_bonus(engine, mock_repos):
    """Verify that location bonus is removed (scores should be identical if frequencies match)."""
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    
    receipts = [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), chain="רמי לוי", items=[
            ReceiptItemDTO(name="לחם", barcode="bc_bread", quantity=1),
            ReceiptItemDTO(name="גבינה", barcode="bc_cheese", quantity=1),
            ReceiptItemDTO(name="חמאה", barcode="bc_butter", quantity=1)
        ]) for _ in range(5)
    ]
    r_repo.get_by_home.return_value = receipts
    
    prods = [
        MockProduct("bc_bread", "לחם", [MockInventoryItem(1, "PANTRY")]),
        MockProduct("bc_cheese", "גבינה", [MockInventoryItem(0, "PANTRY")]), # SAME LOCATION as bread
        MockProduct("bc_butter", "חמאה", [MockInventoryItem(0, "FRIDGE")]), # DIFFERENT LOCATION
    ]
    p_repo.list_all_by_home.return_value = prods
    
    res = await engine.get_recommendations_for_home(home_id, ["לחם"])
    
    cheese_score = next(r['score'] for r in res if r['barcode'] == "bc_cheese")
    butter_score = next(r['score'] for r in res if r['barcode'] == "bc_butter")
    
    # Scores should be equal because they have same frequency and location bonus is gone
    assert cheese_score == butter_score

@pytest.mark.asyncio
async def test_context_filtering_pharmacy(engine, mock_repos):
    """Test that grocery staples are filtered out during a pharmacy trip."""
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    
    # History has Milk (Grocery) and Vitamins (Pharmacy) as staples (10+ buys)
    # Using a pharmacy chain for the receipts to guarantee PHARMACY classification
    receipts = [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), chain="be", items=[
            ReceiptItemDTO(name="חלב", barcode="bc_milk", quantity=1),
            ReceiptItemDTO(name="ויטמין", barcode="bc_vit", quantity=1)
        ]) for _ in range(12)
    ]
    r_repo.get_by_home.return_value = receipts
    
    p_repo.list_all_by_home.return_value = [
        MockProduct("bc_milk", "חלב", [MockInventoryItem(0, "FRIDGE")]),
        MockProduct("bc_vit", "ויטמין", [MockInventoryItem(0, "OTHER")])
    ]
    
    # Act: Search with "אקמול" (Pharmacy signal)
    res = await engine.get_recommendations_for_home(home_id, ["אקמול"])
    
    names = [r['name'] for r in res]
    assert "ויטמין" in names
    assert "חלב" not in names

@pytest.mark.asyncio
async def test_diversity_and_limit(engine, mock_repos):
    """Test diversity filter and max_results."""
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    
    # 15 different items bought together with Milk
    items = [ReceiptItemDTO(name=f"Item{i}", barcode=f"bc{i}", quantity=1) for i in range(15)]
    receipts = [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), items=[
            ReceiptItemDTO(name="חלב", barcode="bc_milk", quantity=1),
            it
        ]) for it in items for _ in range(2) 
    ]
    r_repo.get_by_home.return_value = receipts
    
    p_repo.list_all_by_home.return_value = [MockProduct(f"bc{i}", f"Item{i}", [MockInventoryItem(0, "PANTRY")]) for i in range(15)] + [MockProduct("bc_milk", "חלב", [MockInventoryItem(1, "FRIDGE")])]
    
    # Request only 5 results
    res = await engine.get_recommendations_for_home(home_id, ["חלב"], max_results=5)
    
    assert len(res) <= 5
    # Since they all come from the same source (Milk), diversity filter limits to 3 per source
    assert len(res) == 3 

@pytest.mark.asyncio
async def test_stock_awareness_staple(engine, mock_repos):
    """Test that staples in stock are NOT recommended."""
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    
    receipts = [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), items=[
            ReceiptItemDTO(name="לחם", barcode="bc1", quantity=1)
        ]) for _ in range(15)
    ]
    r_repo.get_by_home.return_value = receipts
    
    # Bread is IN STOCK (quantity=1)
    p_repo.list_all_by_home.return_value = [MockProduct("bc1", "לחם", [MockInventoryItem(1, "PANTRY")])]
    
    res = await engine.get_recommendations_for_home(home_id, ["חלב"])
    assert not any(r['name'] == "לחם" for r in res)

@pytest.mark.asyncio
async def test_empty_state_handling(engine, mock_repos):
    """Test empty results when no data matches."""
    p_repo, r_repo = mock_repos
    r_repo.get_by_home.return_value = []
    p_repo.list_all_by_home.return_value = []
    
    res = await engine.get_recommendations_for_home(uuid4(), ["חלב"])
    assert res == []

@pytest.mark.asyncio
async def test_staple_priority_over_pairing(engine, mock_repos):
    """
    Verify that if a product is both a staple and a strong pairing candidate,
    it appears with the 'staple' reason and score 100, not as a pairing.
    """
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    
    # 1. Bread is a staple (bought 15 times)
    # 2. Bread is ALWAYS bought with Milk (strong pairing)
    receipts = [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), items=[
            ReceiptItemDTO(name="חלב", barcode="bc_milk", quantity=1),
            ReceiptItemDTO(name="לחם", barcode="bc_bread", quantity=1)
        ]) for _ in range(15)
    ]
    r_repo.get_by_home.return_value = receipts
    
    p_repo.list_all_by_home.return_value = [
        MockProduct("bc_milk", "חלב", [MockInventoryItem(1, "FRIDGE")]),
        MockProduct("bc_bread", "לחם", [MockInventoryItem(0, "PANTRY")])
    ]
    
    res = await engine.get_recommendations_for_home(home_id, ["חלב"])
    
    # Bread matches both tiers.
    bread_recs = [r for r in res if r['barcode'] == "bc_bread"]
    
    # Should appear exactly once
    assert len(bread_recs) == 1
    # Should have the staple reason and score
    assert bread_recs[0]['type'] == 'staple'
    assert bread_recs[0]['score'] == 100.0

@pytest.mark.asyncio
async def test_cart_category_filtering_for_pairings(engine, mock_repos):
    """
    Verify that if the user has one brand of milk in cart, 
    the engine doesn't recommend another brand of milk as a pairing.
    """
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    
    # History: Milk and Cereal bought together
    receipts = [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), items=[
            ReceiptItemDTO(name="חלב תנובה", barcode="bc_tnuva", quantity=1),
            ReceiptItemDTO(name="ברנפלקס", barcode="bc_cereal", quantity=1)
        ]) for _ in range(5)
    ]
    r_repo.get_by_home.return_value = receipts
    
    # Cart has "Tara Milk" (different barcode, same generic 'חלב')
    # Inventory doesn't have Tnuva Milk.
    p_repo.list_all_by_home.return_value = [
        MockProduct("bc_tnuva", "חלב תנובה", [MockInventoryItem(0, "FRIDGE")]),
        MockProduct("bc_cereal", "ברנפלקס", [MockInventoryItem(1, "PANTRY")])
    ]
    
    # Act: Search with "חלב טרה" in cart
    res = await engine.get_recommendations_for_home(home_id, ["חלב טרה"])
    
    # Should NOT recommend Tnuva Milk because category 'חלב' is satisfied
    assert not any(r['barcode'] == "bc_tnuva" for r in res)

@pytest.mark.asyncio
async def test_no_duplicate_recommendations(engine, mock_repos):
    """Verify that the final list contains unique barcodes and names."""
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    
    receipts = [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), items=[
            ReceiptItemDTO(name="חלב", barcode="bc_milk", quantity=1),
            ReceiptItemDTO(name="ביצים", barcode="bc_eggs", quantity=1)
        ]) for _ in range(12)
    ]
    r_repo.get_by_home.return_value = receipts
    p_repo.list_all_by_home.return_value = [
        MockProduct("bc_milk", "חלב", [MockInventoryItem(1, "FRIDGE")]),
        MockProduct("bc_eggs", "ביצים", [MockInventoryItem(0, "FRIDGE")])
    ]
    
    res = await engine.get_recommendations_for_home(home_id, ["חלב"])
    
    barcodes = [r['barcode'] for r in res]
    assert len(barcodes) == len(set(barcodes))
    
    names = [r['name'] for r in res]
    assert len(names) == len(set(names))

@pytest.mark.asyncio
async def test_cross_source_diversity_limit(engine, mock_repos):
    """Verify that the 3-per-source diversity limit applies correctly."""
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    
    # 5 items. To be staples, each must appear in >= 50% of receipts.
    # We'll create 20 receipts, and each item stays in 15 of them (75% frequency).
    items = [f"Staple{i}" for i in range(5)]
    receipts = []
    for _ in range(20):
        # Each receipt contains all 5 items
        receipt_items = [ReceiptItemDTO(name=name, barcode=f"bc{i}", quantity=1) for i, name in enumerate(items)]
        receipts.append(ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), items=receipt_items))
    
    r_repo.get_by_home.return_value = receipts
    p_repo.list_all_by_home.return_value = [
        MockProduct(f"bc{i}", f"Staple{i}", [MockInventoryItem(0, "PANTRY")]) for i in range(5)
    ]
    
    res = await engine.get_recommendations_for_home(home_id, ["חלב"])
    
    # Diversity filter limits 'staple' source to 3
    staple_recs = [r for r in res if r['type'] == 'staple']
    assert len(staple_recs) == 3

@pytest.mark.asyncio
async def test_attribute_strict_guard(engine, mock_repos):
    """
    Verify that distinctive attributes (Soy vs Dairy) prevent incorrect pairings.
    """
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    
    # History: Milk bought with Cookies. 
    # But one is Soy Milk, and one is Dairy Cookies.
    receipts = [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), items=[
            ReceiptItemDTO(name="חלב סויה", barcode="bc_soy", quantity=1),
            ReceiptItemDTO(name="עוגיות חלביות", barcode="bc_dairy_cookies", quantity=1)
        ]) for _ in range(5)
    ]
    r_repo.get_by_home.return_value = receipts
    p_repo.list_all_by_home.return_value = [
        MockProduct("bc_soy", "חלב סויה", [MockInventoryItem(0, "FRIDGE")]),
        MockProduct("bc_dairy_cookies", "עוגיות חלביות", [MockInventoryItem(0, "PANTRY")])
    ]
    
    # Act: Search with "חלב" in cart (Regular milk)
    res = await engine.get_recommendations_for_home(home_id, ["חלב"])
    
    # Should NOT recommend Soy items or items paired specifically with Soy
    # because the generic 'חלב' search doesn't have the 'סויה' attribute.
    # The attribute-aware matcher skips products if they have attributes NOT in search.
    assert not any("סויה" in r['name'] for r in res)

@pytest.mark.asyncio
async def test_staple_brand_preference(engine, mock_repos):
    """
    Verify that the most frequently bought brand in a category is chosen as the staple.
    """
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    
    # History: Tnuva Milk (15 times) vs Tara Milk (2 times)
    receipts = [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), items=[
            ReceiptItemDTO(name="חלב תנובה", barcode="bc_tnuva", quantity=1)
        ]) for _ in range(15)
    ] + [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), items=[
            ReceiptItemDTO(name="חלב טרה", barcode="bc_tara", quantity=1)
        ]) for _ in range(2)
    ]
    r_repo.get_by_home.return_value = receipts
    
    p_repo.list_all_by_home.return_value = [
        MockProduct("bc_tnuva", "חלב תנובה", [MockInventoryItem(0, "FRIDGE")]),
        MockProduct("bc_tara", "חלב טרה", [MockInventoryItem(0, "FRIDGE")])
    ]
    
    res = await engine.get_recommendations_for_home(home_id, ["לחם"])
    
    # Should recommend Tnuva because it's the more dominant brand in the 'חלב' staple category
    assert any(r['barcode'] == "bc_tnuva" for r in res)
    assert not any(r['barcode'] == "bc_tara" for r in res)

@pytest.mark.asyncio
async def test_joint_probability_bonus(engine, mock_repos):
    """
    Verify that multiple items in cart boost results that are related to ALL of them.
    """
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    
    # History: 
    # Milk + Bread (5 times)
    # Eggs + Bread (5 times)
    # Extra 20 receipts with just Milk (Total = 30, Bread frequency = 10/30 = 33% < 50%)
    receipts = [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), items=[
            ReceiptItemDTO(name="חלב", barcode="bc_milk", quantity=1),
            ReceiptItemDTO(name="לחם", barcode="bc_bread", quantity=1)
        ]) for _ in range(5)
    ] + [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), items=[
            ReceiptItemDTO(name="ביצים", barcode="bc_eggs", quantity=1),
            ReceiptItemDTO(name="לחם", barcode="bc_bread", quantity=1)
        ]) for _ in range(5)
    ] + [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), items=[
            ReceiptItemDTO(name="חלב", barcode="bc_milk", quantity=1)
        ]) for _ in range(20)
    ]
    r_repo.get_by_home.return_value = receipts
    p_repo.list_all_by_home.return_value = [
        MockProduct("bc_milk", "חלב", [MockInventoryItem(1, "FRIDGE")]),
        MockProduct("bc_eggs", "ביצים", [MockInventoryItem(1, "FRIDGE")]),
        MockProduct("bc_bread", "לחם", [MockInventoryItem(0, "PANTRY")])
    ]
    
    # Scenario A: Only Milk in cart
    res_single = await engine.get_recommendations_for_home(home_id, ["חלב"])
    score_single = next(r['score'] for r in res_single if r['barcode'] == "bc_bread")
    
    # Scenario B: Both Milk and Eggs in cart
    res_both = await engine.get_recommendations_for_home(home_id, ["חלב", "ביצים"])
    score_both = next(r['score'] for r in res_both if r['barcode'] == "bc_bread")
    
    # Scoring: score = total_count * idf. 
    # With one source, total_count = 5. With two sources, total_count = 10.
    assert score_both > score_single

@pytest.mark.asyncio
async def test_minimum_co_occurrence_threshold(engine, mock_repos):
    """
    Verify that items bought together only ONCE (noise) are not recommended.
    """
    p_repo, r_repo = mock_repos
    home_id = uuid4()
    
    # History: Milk and "Weird Item" bought together only ONCE
    receipts = [
        ReceiptDTO(id=uuid4(), home_id=home_id, user_id=uuid4(), items=[
            ReceiptItemDTO(name="חלב", barcode="bc_milk", quantity=1),
            ReceiptItemDTO(name="משהו מוזר", barcode="bc_weird", quantity=1)
        ])
    ]
    r_repo.get_by_home.return_value = receipts
    p_repo.list_all_by_home.return_value = [
        MockProduct("bc_milk", "חלב", [MockInventoryItem(1, "FRIDGE")]),
        MockProduct("bc_weird", "משהו מוזר", [MockInventoryItem(0, "OTHER")])
    ]
    
    res = await engine.get_recommendations_for_home(home_id, ["חלב"])
    
    # Should be empty because total_count < 2 items is considered noise in Tier 2
    assert not any(r['barcode'] == "bc_weird" for r in res)

if __name__ == "__main__":
    pass
