from typing import List, Dict, Optional
from uuid import UUID
from src.domain.recommendation.engine import RecommendationEngine

class RecommendationService:
    """
    Mediator service for shopping recommendations.
    Provides a thin entry point to the RecommendationEngine.
    """
    def __init__(self, engine: RecommendationEngine):
        self._engine = engine

    async def get_recommendations(
        self, 
        home_id: UUID, 
        current_shopping_list_items: List[str], 
        max_results: int = 10
    ) -> List[Dict[str, str]]:
        """Simply delegates to the underlying domain engine."""
        return await self._engine.get_recommendations_for_home(
            home_id=home_id,
            current_cart_items=current_shopping_list_items,
            max_results=max_results
        )
