import difflib
import math
import string
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple
from collections import defaultdict, Counter
from uuid import UUID
from enum import Enum
from dataclasses import dataclass, field
from src.domain.receipt.receipt import ReceiptDTO
from src.repositories.i_product_repository import IProductRepository
from src.repositories.i_receipt_repository import IReceiptRepository

class StoreType(str, Enum):
    GROCERY = "GROCERY"
    PHARMACY = "PHARMACY"
    HOUSEHOLD = "HOUSEHOLD"
    UNKNOWN = "UNKNOWN"

# Lists for Attribute-Aware Matching
COMMON_BRANDS = {
    "תנובה", "טרה", "שטראוס", "אסם", "עלית", "מולר", "גד", "יולו", "יטבתה",
    "וילי פוד", "שופרסל", "רמי לוי", "יוניליוור", "אסם-נסטלה", "סנו", "פילסברי", 
    "ניקול", "סוגת", "מאסטר שף", "טבעול", "זוגלובק", "מעדנות", "פריגת", "יכין",
    "קולגייט", "אורל בי", "פנטן", "הד אנד שולדרס", "קלינקה", "סוד", "פרסיל"
}

DISTINCTIVE_ATTRIBUTES = {
    # Types & Diet
    "סויה", "שקדים", "אורז", "שיבולת", "טבעוני", "צמחי", "נטול", "דיאט", "דל", "אורגני", "ללא", "מרוכז", "עמיד",
    "ללא סוכר", "ללא גלוטן", "מופחת שומן", "דל שומן", "מלא", "כוסמין", "שיפון", "תופח", "ביו", "פרוביוטי",
    # Preparation
    "קפוא", "מצונן", "טרי", "מיובש", "טחון", "קלוי", "כבוש", "מעושן", "מבושל", "ארוז", "שלם", "חתוך", "קלוף", "פרוס", "מפורק", "אפוי",
    # Flavors/Additives
    "וניל", "שוקולד", "תות", "לימון", "קוקוס", "דבש", "במילוי", "מילוי", "חריף", "מתוק", "מלוח", "בשמן", "במים",
    "פיקנטי", "פטריות", "זיתים", "בוטנים", "אגוזי", "קרמל", "מייפל", "קינמון", "פוסילי", "פנה", "ספגטי",
    # Textures/Categories
    "מריר", "מריחה", "ממרח", "יוגורט", "מעדן", "גבינה", "לחמניה", "חלב", "משקה", "אגוז", "פקאן", "קשיו", "פיסטוק",
    "ניקוי", "כביסה", "כלים", "רחצה", "טיפוח",
    # Kosher & Quality
    "חלבי", "בשרי", "פרווה", "מוכשר", "מהדרין", "בד''ץ", "כשר", "פרמיום", "פרימיום"
}

@dataclass
class EngineMetadata:
    """Internal container for barcode mapping and inventory metadata."""
    name_to_bc: Dict[str, str] = field(default_factory=dict)
    bc_to_name: Dict[str, str] = field(default_factory=dict)
    bc_to_loc: Dict[str, str] = field(default_factory=dict)
    bc_to_stock: Dict[str, float] = field(default_factory=dict)
    bc_to_cat: Dict[str, str] = field(default_factory=dict)
    cat_to_bcs: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))

@dataclass
class EngineContext:
    """Internal container for the detected context of the current shopping list."""
    active_store_types: Set[StoreType] = field(default_factory=set)
    mapped_cart_barcodes: Set[str] = field(default_factory=set)
    mapped_cart_categories: Set[str] = field(default_factory=set)

class RecommendationEngine:
    """
    Domain Service for generating shopping recommendations.
    Handles data analysis, pattern recognition, and store-context awareness.
    """
    def __init__(self, product_repository: IProductRepository, receipt_repository: IReceiptRepository):
        self._product_repository = product_repository
        self._receipt_repository = receipt_repository

    async def get_recommendations_for_home(
        self, 
        home_id: UUID, 
        current_cart_items: List[str],
        max_results: int = 10
    ) -> List[Dict]:
        """
        Main entry point for recommendation logic. 
        Orchestrates data fetching, context inference, and multi-tier suggestion generation.
        """
        if not current_cart_items:
            return []

        # 1. Fetch Raw Data
        all_receipts, home_products = await self._fetch_raw_data(home_id)
        if not all_receipts: return []

        # 2. Prepare Metadata & Context
        metadata = self._prepare_metadata(all_receipts, home_products)
        context = self._infer_shopping_context(current_cart_items, all_receipts, metadata)
        
        # 3. Filter Data by Context
        relevant_receipts = self._filter_receipts_by_context(all_receipts, context, metadata)
        if not relevant_receipts: return []

        # 4. Generate Suggestions (Tiered)
        staple_recommendations = self._generate_tier1_staples(relevant_receipts, metadata, context)
        pairing_recommendations = self._generate_tier2_pairings(relevant_receipts, metadata, context, current_cart_items)

        # 5. Filter & Sort Final Results
        all_candidates = staple_recommendations + pairing_recommendations
        if not all_candidates:
            return []
        return self._diversity_filter(all_candidates, max_results)

    async def _fetch_raw_data(self, home_id: UUID) -> Tuple[List[ReceiptDTO], List]:
        """Fetch receipts (last 30 days) and current household products."""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        all_receipts = await self._receipt_repository.get_by_home(home_id, limit=200, since=thirty_days_ago)
        home_products = await self._product_repository.list_all_by_home(home_id)
        return all_receipts, home_products

    def _prepare_metadata(self, receipts: List[ReceiptDTO], products: List) -> EngineMetadata:
        """Enrich metadata and map barcodes to names, locations, stocks, and categories."""
        meta = EngineMetadata()
        
        # Populate from inventory
        for p in products:
            if not p.barcode: continue
            meta.name_to_bc[p.original_name ] = p.barcode
            meta.bc_to_name[p.barcode] = p.nickname or p.original_name
            if p.nickname: meta.name_to_bc[p.nickname ] = p.barcode
            
            if p.items:
                # Point: ensure p.items[0].location is an Enum before accessing .name
                loc = p.items[0].location
                if hasattr(loc, 'name'):
                    meta.bc_to_loc[p.barcode] = loc.name
                else:
                    meta.bc_to_loc[p.barcode] = str(loc)
                meta.bc_to_stock[p.barcode] = sum(item.quantity for item in p.items)

        # Populate from receipt history
        for r in receipts:
            for item in r.items:
                if not item.barcode: continue
                meta.name_to_bc[item.name ] = item.barcode
                if item.barcode not in meta.bc_to_name:
                    meta.bc_to_name[item.barcode] = item.name

        # Map to Generic Categories
        for bc, name in meta.bc_to_name.items():
            cat = self._get_generic_name(name)
            meta.bc_to_cat[bc] = cat
            meta.cat_to_bcs[cat].append(bc)
            # Point 1: Map Generic Names to barcodes too for robust matching
            if cat not in meta.name_to_bc:
                meta.name_to_bc[cat] = bc
            
        return meta

    def _infer_shopping_context(self, cart_items: List[str], receipts: List[ReceiptDTO], metadata: EngineMetadata) -> EngineContext:
        """Detect the active store type (Pharmacy/Grocery) from current cart items."""
        ctx = EngineContext()
        pharmacy_keywords = {
            "אקמול", "אדוויל", "חיתול", "מגבונים", "תרופה", "ויטמין", "משחת שיניים", "מברשת שיניים",
            "קרם", "טיטול", "מוצץ", "בקבוק", "סימילאק", "מטרנה", "נורופן", "בפנטן"
        }

        for item_text in cart_items:            
            item_lower = item_text 
            # 1. Direct Keyword Check
            if any(kw in item_lower for kw in pharmacy_keywords):
                ctx.active_store_types.add(StoreType.PHARMACY)
            
            # 2. Historical Match Context
            matches = self._fuzzy_match_products(item_lower, metadata.name_to_bc)
            for bc in matches:
                cat = metadata.bc_to_cat.get(bc)
                if cat:
                    ctx.mapped_cart_categories.add(cat)
                    # Point 4: Robust Pairings - Expand category to include ALL its member barcodes.
                    # This ensures that if the user adds "Milk", we find items bought with ANY milk brand.
                    for member_bc in metadata.cat_to_bcs.get(cat, []):
                        ctx.mapped_cart_barcodes.add(member_bc)
                else:
                    ctx.mapped_cart_barcodes.add(bc)
                
                # Check which historical receipts contained this item to infer store type
                for r in receipts:
                    if any(i.barcode == bc for i in r.items):
                        ctx.active_store_types.add(self._classify_receipt_store_type(r, metadata.bc_to_loc))

        # Cleanup Signals: discard UNKNOWN if we have concrete signals
        if len(ctx.active_store_types) > 1:
            ctx.active_store_types.discard(StoreType.UNKNOWN)
            if StoreType.PHARMACY in ctx.active_store_types:
                ctx.active_store_types.discard(StoreType.GROCERY) # Pharmacy trip is very specific
                
        return ctx

    def _filter_receipts_by_context(self, receipts: List[ReceiptDTO], ctx: EngineContext, metadata: EngineMetadata) -> List[ReceiptDTO]:
        """Filter the historical dataset to match the current shopping context."""
        if not ctx.active_store_types: return receipts
        
        # Priority: Strict store type matching (Pharmacy signal overrides Generic)
        target_type = StoreType.PHARMACY if StoreType.PHARMACY in ctx.active_store_types else StoreType.GROCERY
        return [r for r in receipts if self._classify_receipt_store_type(r, metadata.bc_to_loc) == target_type]

    def _generate_tier1_staples(self, receipts: List[ReceiptDTO], metadata: EngineMetadata, ctx: EngineContext) -> List[Dict]:
        """Recommend frequently purchased categories that are currently missing/out of stock."""
        if not receipts: return []
        
        # Point 2: Infer current target context to filter staples
        target_context = StoreType.PHARMACY if StoreType.PHARMACY in ctx.active_store_types else StoreType.GROCERY
        
        cat_freq = self._calculate_category_frequencies(receipts)
        total_receipts = len(receipts)
        
        # Identify Staples (>50% freq AND >=10 purchases)
        staple_cats = {c for c, count in cat_freq.items() if (count/total_receipts) >= 0.5 and count >= 10}
        
        # Calculate Category Stock
        cat_stock = defaultdict(float)
        for bc, stock in metadata.bc_to_stock.items():
            cat = metadata.bc_to_cat.get(bc)
            if cat: cat_stock[cat] += stock
            
        recommendations = []
        for cat in staple_cats:
            # Point 2: Only suggest staples that match the current context (Pharmacy vs Grocery)
            cat_type = self._get_cat_store_type(cat, metadata)
            # If we are strictly in a Pharmacy context, don't suggest Grocery staples.
            if cat_type != target_context and StoreType.PHARMACY in ctx.active_store_types:
                continue

            if cat not in ctx.mapped_cart_categories and cat_stock.get(cat, 0) <= 0:
                # Use the first barcode in the category as representative
                if cat in metadata.cat_to_bcs:
                    best_bc = metadata.cat_to_bcs[cat][0]
                    recommendations.append({
                        # Use the specific product name for better recognition, or capitalize generic
                        'name': metadata.bc_to_name.get(best_bc, cat.capitalize()),
                        'barcode': best_bc,
                        'reason': "נראה שזה מוצר קבוע אצלכם",
                        'type': 'staple', 
                        'score': 100.0
                    })
        return recommendations

    def _get_cat_store_type(self, cat: str, metadata: EngineMetadata) -> StoreType:
        """Helper to classify a category by its representative product location or keywords."""
        pharmacy_keywords = {
            "אקמול", "אדוויל", "חיתול", "מגבונים", "תרופה", "ויטמין", "משחת שיניים", "מברשת שיניים",
            "סימילאק", "מטרנה", "טיטול", "מוצץ", "בקבוק", "נורופן", "בפנטן"
        }
        if any(kw in cat for kw in pharmacy_keywords): return StoreType.PHARMACY
        
        # Check location of associated barcodes from inventory metadata
        for bc in metadata.cat_to_bcs.get(cat, []):
            loc = metadata.bc_to_loc.get(bc, "")
            if loc in ["FRIDGE", "FREEZER", "PANTRY"]: return StoreType.GROCERY
            
        # Fallback to keyword matching for grocery common nouns
        grocery_keywords = {"חלב", "לחם", "ביצים", "גבינה", "יוגורט", "עגבניה", "מלפפון"}
        if any(kw in cat for kw in grocery_keywords): return StoreType.GROCERY
        
        return StoreType.GROCERY # Default to grocery

    def _generate_tier2_pairings(self, receipts: List[ReceiptDTO], metadata: EngineMetadata, ctx: EngineContext, cart_items: List[str]) -> List[Dict]:
        """Recommend items frequently co-purchased with current cart items."""
        if not ctx.mapped_cart_barcodes or not receipts: return []
        
        co_occurrence = defaultdict(lambda: defaultdict(int))
        for r in receipts:
            rb_codes = {i.barcode for i in r.items if i.barcode}
            sources = rb_codes.intersection(ctx.mapped_cart_barcodes)
            if sources:
                for s_bc in sources:
                    for t_bc in rb_codes:
                        target_cat = metadata.bc_to_cat.get(t_bc)
                        # Suggest pairings that are NOT in cart
                        if t_bc not in ctx.mapped_cart_barcodes:
                            co_occurrence[t_bc][s_bc] += 1

        # Calculate Category Stock
        cat_stock = defaultdict(float)
        for bc, stock in metadata.bc_to_stock.items():
            cat = metadata.bc_to_cat.get(bc)
            if cat: cat_stock[cat] += stock
            
        total_receipts = len(receipts)
        cat_freq = self._calculate_category_frequencies(receipts)

        # Collect by generic group to avoid redundant pairings (e.g., 2 types of milk)
        grouped_targets = defaultdict(list)
        for t_bc in co_occurrence.keys():
            generic = metadata.bc_to_cat.get(t_bc)
            if generic: grouped_targets[generic].append(t_bc)
            
        recommendations = []
        for generic, bcs in grouped_targets.items():
            # Point 5: Stock-Aware Pairings - Do not suggest items already in stock (quantity > 0)
            if cat_stock.get(generic, 0) > 0:
                continue

            agg_sources = defaultdict(int)
            for bc in bcs:
                for src, count in co_occurrence[bc].items(): agg_sources[src] += count
            
            total_count = sum(agg_sources.values())
            if total_count < 2: continue
            
            best_target = max(bcs, key=lambda b: sum(co_occurrence[b].values()))
            best_source = max(agg_sources.items(), key=lambda x: x[1])[0]
            
            # TF-IDF Score
            target_f = cat_freq.get(generic, 1)
            idf = math.log10((total_receipts + 1) / (target_f + 0.5)) + 0.5
            score = float(total_count) * idf
            
            recommendations.append({
                'barcode': best_target,
                'source_barcode': best_source,
                'name': metadata.bc_to_name.get(best_target, generic.capitalize()),
                'reason': f"נקנה בדרך כלל עם {self._get_source_text(best_source, cart_items, metadata.name_to_bc)}",
                'type': 'pairing',
                'score': score
            })
        return recommendations

    def _classify_receipt_store_type(self, receipt: ReceiptDTO, bc_to_loc: Dict[str, str]) -> StoreType:
        """Heuristic to determine if a receipt is from a Supermarket, Pharmacy, etc."""
        chain = (receipt.chain or "").lower()
        if any(kw in chain for kw in ["pharm", "be", "pharmacy", "סופר פארם", "ניו פארם"]):
            return StoreType.PHARMACY
        
        grocery_chains = {
            "RAMI LEVI", "SHUFERSAL", "YOHANANOF", "VICTORY", "STOPSHOP", "TIV TAAM", 
            "רמי לוי", "שופרסל", "יוחננוף", "ויקטורי", "טיב טעם", "חצי חינם", "מחסני השוק"
        }
        if any(kw in chain for kw in grocery_chains):
            return StoreType.GROCERY
        
        pharmacy_keywords = {"אקמול", "אדוויל", "חיתול", "מגבונים", "תרופה", "ויטמין", "סימילאק", "נורופן"}
        grocery_keywords = {"מלפפון", "עגבניה", "חלב", "ביצים", "גבינה", "יוגורט","לחם","בשר","עוף","דג"}
        
        p_hint = any(any(kw in (i.name or "") for kw in pharmacy_keywords) for i in receipt.items)
        g_hint = any(any(kw in (i.name or "")  for kw in grocery_keywords) for i in receipt.items)
        
        if p_hint: return StoreType.PHARMACY
        if g_hint: return StoreType.GROCERY
        
        # Location fallback
        loc_counts = Counter(bc_to_loc.get(i.barcode, "OTHER") for i in receipt.items)
        if loc_counts["FRIDGE"] > 0 or loc_counts["FREEZER"] > 0: return StoreType.GROCERY
        if loc_counts["PANTRY"] > 1: return StoreType.GROCERY
        if loc_counts["CLEANING"] > 1: return StoreType.HOUSEHOLD
        return StoreType.UNKNOWN

    def _get_generic_name(self, name: str) -> str:
        """Extracts the core product noun for grouping, avoiding over-aggressive cleaning."""
        clean = name 
        # Strip brand names
        for brand in COMMON_BRANDS: clean = clean.replace(brand , "").strip()
        # Strip punctuation
        clean = "".join(c for c in clean if c not in string.punctuation)
        
        two_word_nouns = [
            "נייר טואלט", "שמן זית", "תפוח אדמה", "גבינה צהובה", "גבינה לבנה", "גבינת שמנת",
            "מרכך כביסה", "אבקת כביסה", "נוזל כביסה", "סבון כלים", "משחת שיניים", "מברשת שיניים",
            "מגבונים לחים", "נייר סופג", "שמן קנולה", "מיץ תפוזים", "מעדן חלב", "רסק עגבניות",
            "שימורי תירס", "חטיף תפוחי אדמה", "שמנת לבישול", "שמנת מתוקה", "שמנת חמוצה",
            "מיץ ענבים", "מיץ תפוחים", "יוגורט תות", "יוגורט וניל", "מעדן שוקולד"
        ]
        for noun in two_word_nouns:
            if clean.startswith(noun): return noun
                
        words = clean.split()
        if not words: return name.strip()
        
        # Point 3: Prevent "Axe" cleaning for common base categories (allows tracking "Grape Juice" vs "Apple Juice")
        base_categories = {"מיץ", "יוגורט", "מעדן", "גבינה", "שמנת", "לחם", "יין", "שוקולד"}
        if words[0] in base_categories and len(words) > 1:
            # If the second word is not a brand or a generic adjective, keep it as part of the category
            if words[1] not in DISTINCTIVE_ATTRIBUTES:
                return f"{words[0]} {words[1]}"
                
        return words[0]

    def _fuzzy_match_products(self, text: str, name_to_bc: Dict[str, str]) -> List[str]:
        """Attribute-Aware Fuzzy Matching with symmetric cleaning for robust recognition."""
        text = text.strip()
        if not text: return []
        
        # Symmetric cleaning for the search text
        clean_text = "".join(c for c in text if c not in string.punctuation)
        for brand in COMMON_BRANDS: clean_text = clean_text.replace(brand, "").strip()
        
        search_tokens = set(text.split())
        search_attrs = {a for a in DISTINCTIVE_ATTRIBUTES if a in text}
        matches = []
        
        for name, barcode in name_to_bc.items():
            name_lower = name 
            # Attribute Guard: skip if product has distinctive trait NOT in search
            prod_attrs = {a for a in DISTINCTIVE_ATTRIBUTES if a in name_lower}
            if prod_attrs - search_attrs: continue
            
            # Start-match check (stripping brands)
            clean_name = "".join(c for c in name_lower if c not in string.punctuation)
            for brand in COMMON_BRANDS: clean_name = clean_name.replace(brand , "").strip()
            
            if clean_name.startswith(clean_text) or (clean_text and clean_name == clean_text):
                matches.append((barcode, 100))
            elif any(t in name_lower for t in search_tokens):
                matches.append((barcode, 50))
        
        # Return only top-tier matches
        if not matches:
            # Note: We must clean the keys here too if we want difflib to be accurate
            fuzzy = difflib.get_close_matches(text, list(name_to_bc.keys()), n=1, cutoff=0.9)
            if fuzzy: return [name_to_bc[f] for f in fuzzy]
            return []
            
        max_s = max(m[1] for m in matches)
        if max_s < 100: return [] # Strictly enforce 100 as per user request
        return list(set(m[0] for m in matches if m[1] == max_s))

    def _get_source_text(self, source_barcode: str, cart_items: List[str], name_to_bc: Dict[str, str]) -> str:
        for text in cart_items:
            if source_barcode in self._fuzzy_match_products(text, name_to_bc): return text
        return "פריט ברשימה"

    def _calculate_category_frequencies(self, receipts: List[ReceiptDTO]) -> Dict[str, int]:
        freq = defaultdict(int)
        for r in receipts:
            seen_cats = {self._get_generic_name(i.name or "") for i in r.items}
            for c in seen_cats: freq[c] += 1
        return freq

    def _diversity_filter(self, candidates: List[Dict], max_results: int) -> List[Dict]:
        """Limit results and ensure variety of source products."""
        source_counts = defaultdict(int)
        filtered = []
        seen_targets = set()
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        for item in candidates:
            src = item.get('source_barcode', 'staple')
            target = item['barcode']
            if source_counts[src] < 3 and target not in seen_targets:
                filtered.append(item)
                source_counts[src] += 1
                seen_targets.add(target)
            if len(filtered) >= max_results: break
        return filtered
